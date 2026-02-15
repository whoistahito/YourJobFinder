import time
from typing import Optional

import schedule

from app import app
from db.database_service import UserManager, UserEmailManager
from email_manager import send_email
from html_render import create_job_card, get_html_template, get_welcome_message
from logger import create_logger
from google_scraper_service import scrape_google
from google_scraper_models import GoogleJobPosting

logger = create_logger("main")


def find_jobs(
        search_term: str,
        location: str,
        job_type: Optional[str],
):
    return scrape_google(search_term, location, 10)


def _safe_str(value: Optional[str]) -> str:
    return value or ""


def _job_to_card(job: GoogleJobPosting) -> dict:
    data = job.model_dump()
    job_url = data.get("job_url") or data.get("link") or ""
    return {
        "title": data.get("title") or "",
        "company": data.get("company") or "",
        "location": data.get("location") or "",
        "date_posted": data.get("date_posted"),
        "job_url": job_url,
    }



def notify_jobs(jobs: list[dict], email: str, position: str, location: str) -> list[dict]:
    """
    Send notification email if there are filtered jobs based on refined criteria.
    """
    if jobs:
        sorted_jobs = sorted(
            jobs,
            key=lambda job: _safe_str(job.get("date_posted")),
            reverse=True,
        )

        html_content = ''.join(create_job_card(job) for job in sorted_jobs)
        html_template = get_html_template(html_content, email, position, location)
        send_email(html_template, "Found some job opportunities for you!", email, is_html=True)
        return sorted_jobs

    logger.error("No jobs found based on the criteria.")
    return []


def check_for_new_users():
    """
    Check for new users and send them a confirmation email.
    """
    with app.app_context():
        new_users = UserManager().get_new_users()
        for user in new_users:
            if user.confirmation_token:
                confirm_url = f"https://api.yourjobfinder.website/confirm/{user.confirmation_token}"
                send_email(get_welcome_message(confirm_url), "Welcome to Your Job Finder! Please Confirm Email",
                           user.email, is_html=True)
            UserManager().mark_user_as_not_new(user.email, user.position, user.location)


def notify_users() -> None:
    """
    Notify all registered users based on their preferences by scraping job sites
    and sending them an email with relevant job opportunities.
    """
    with app.app_context():
        users = UserManager().get_confirmed_users()
        for user in users:
            notify_user(user)


def notify_user(user):
    found_jobs = find_jobs(user.position, user.location, user.job_type)
    if not found_jobs.jobs:
        return

    job_cards = []
    for job in found_jobs.jobs:
        job_url = job.link or job.model_dump().get("job_url")
        if not job_url:
            continue
        if UserEmailManager().is_sent(user.email, job_url, user.position, user.location):
            continue
        job_cards.append(_job_to_card(job))

    sent_jobs = notify_jobs(job_cards, user.email, user.position, user.location)
    for job in sent_jobs:
        UserEmailManager().add_sent_email(
            user.email, job["job_url"], user.position, user.location
        )


if __name__ == "__main__":
    schedule.every().day.at("10:45").do(
        lambda: notify_users())

    while True:
        check_for_new_users()

        schedule.run_pending()
        time.sleep(20)
