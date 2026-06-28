import time
from datetime import datetime, timezone
from typing import Optional

import schedule

from app import app
from db.database_service import UserManager, UserEmailManager
from email_manager import send_email
from html_render import create_job_card, get_html_template, get_welcome_message
from logger_utils import create_logger
from scrapers.google_scraper_service import scrape_google
from scrapers.google_scraper_models import GoogleJobPosting
from job_matching.job_matching_service import match
from job_matching.job_matching_models import UserProfile
from domain.matched_job import MatchedJob
from infrastructure.job_match_repository import SqlAlchemyJobMatchRepository
from extension import db

logger = create_logger("main")

JOB_MATCH_THRESHOLD = 0.35


def find_jobs(
        search_term: str,
        location: str,
        job_type: Optional[str],
        country_code: Optional[str] = None,
) -> list[GoogleJobPosting]:
    return scrape_google(search_term, location, 10, country_code=country_code).jobs


def _safe_str(value: Optional[str]) -> str:
    return value or ""


def get_user_profile(user) -> Optional[UserProfile]:
    """Convert the SQLAlchemy User relations into a UserProfile Pydantic model."""
    if not (user.skills or user.experiences or user.educations):
        return None

    return UserProfile(
        skills=[s.skill for s in user.skills],
        experiences=[e.experience for e in user.experiences],
        qualifications=[e.education for e in user.educations],
    )

def notify_jobs(
        jobs: list[GoogleJobPosting],
        email: str,
        position: str,
        location: str,
):
    """
    Send notification email if there are filtered jobs based on refined criteria.
    """
    if not jobs:
        raise Exception("No jobs found based on the criteria.")

    sorted_jobs = sorted(
        jobs,
        key=lambda job: _safe_str(job.date_posted),
        reverse=True,
    )

    html_content = ''.join(create_job_card(job) for job in sorted_jobs)
    html_template = get_html_template(html_content, email, position, location)
    send_email(html_template, "Found some job opportunities for you!", email, is_html=True)

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
            if user.is_new and user.is_confirmed:
                try:
                    notify_user(user)
                except Exception as e:
                    logger.exception(f"notify_user failed for {user.email}: {e}")
            UserManager().mark_user_as_not_new(user.email, user.position, user.location)


def notify_users() -> None:
    """
    Notify all registered users based on their preferences by scraping job sites
    and sending them an email with relevant job opportunities.
    """
    with app.app_context():
        users = UserManager().get_confirmed_users()
        for user in users:
            try:
                notify_user(user)
            except Exception as e:
                logger.exception(f"notify_user failed for {user.email}: {e}")


def notify_user(user):
    found_jobs = find_jobs(user.position, user.location, user.job_type, country_code=getattr(user, 'country_code', None))
    if not found_jobs:
        logger.error("No jobs found based on the criteria.")
        return

    user_profile = get_user_profile(user)
    job_match_repo = SqlAlchemyJobMatchRepository(db)

    matched = []  # (job, score_value) — persisted only after the email is sent
    for job in found_jobs:
        job_url = str(job.link)
        if UserEmailManager().is_sent(user.email, job_url, user.position, user.location):
            continue

        # job matching if user has profile and job has description
        score_value = None
        if user_profile and job.description:
            try:
                logger.info(f"Matching: {job.title}")
                score = match(job.description, user_profile)
                if score < JOB_MATCH_THRESHOLD:
                    logger.info(
                        f"Skipping '{job.title}' for {user.email} "
                        f"— match score {score:.2f} < threshold {JOB_MATCH_THRESHOLD}"
                    )
                    continue
                logger.info(
                    f"'{job.title}' passed match filter for {user.email} "
                    f"— score {score:.2f}"
                )
                score_value = int(round(score * 100))
            except Exception as e:
                logger.exception(
                    f"Job matching failed for '{job.title}': {e} — including job anyway"
                )

        matched.append((job, score_value))

    if not matched:
        return

    # Send first; only record (sent-email + dashboard match) once the send succeeds,
    # so a failed send doesn't leave dashboard rows for an email the user never got.
    # ponytail: the two writes below commit per-job, not in one txn — a crash between
    # them can drop a dashboard row (job still marked sent). Wrap in a single txn if
    # that matters; the costly duplicate-on-send-failure case is already gone.
    notify_jobs([job for job, _ in matched], user.email, user.position, user.location)
    for job, score_value in matched:
        UserEmailManager().add_sent_email(
            user.email, str(job.link), user.position, user.location
        )
        job_match_repo.save(MatchedJob(
            id=None, user_id=user.id, title=job.title, company=job.company,
            location=job.location, job_url=str(job.link), date_posted=job.date_posted,
            score=score_value, created_at=datetime.now(timezone.utc),
        ))


if __name__ == "__main__":
    schedule.every().day.at("10:45").do(
        lambda: notify_users())

    while True:
        check_for_new_users()

        schedule.run_pending()
        time.sleep(20)
