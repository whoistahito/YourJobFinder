import requests

from credential import GoogleScraperCredential
from scrapers.google_scraper_models import GoogleScrapeResponse
from logger_utils import create_logger
logger = create_logger("Google Scraper")

def scrape_google(title: str, location: str, limit: int = 10) -> GoogleScrapeResponse:
    token = GoogleScraperCredential.get_google_scraper_token()
    url = GoogleScraperCredential.get_google_scraper_url()
    query = f"{title} jobs in {location}"
    payload = {
        "query": query,
        "limit": limit,
    }
    headers = {
        "Authorization": f"Bearer {token}",
    }
    logger.info(f"Scraping for {title}")
    response = requests.post(url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    data = response.json()
    logger.info(f"Found {len(data['jobs'])} jobs")
    return GoogleScrapeResponse.from_json(data)
