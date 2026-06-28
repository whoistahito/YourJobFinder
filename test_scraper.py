import requests

# GOOGLE_SCRAPER_URL = "http://127.0.0.1:3000/job-search"
# GOOGLE_SCRAPER_TOKEN = "test123"
GOOGLE_SCRAPER_URL = "https://google.yourjobfinder.website/job-search"
GOOGLE_SCRAPER_TOKEN = "changeme"


def scrape_google(title: str, location: str, country: str, limit: int = 10):
    query = f"{title} jobs in {location}"
    payload = {"query": query, "country": country, "limit": limit}
    headers = {"Authorization": f"Bearer {GOOGLE_SCRAPER_TOKEN}"}

    response = requests.post(GOOGLE_SCRAPER_URL, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    return response.json()["jobs"]


if __name__ == "__main__":
    jobs = scrape_google("Java developer", "Hamburg", "DE", 5)
    for job in jobs:
        print(f"{job['title']} at {job['company']} - {job['location']} -{job['link']} ")
