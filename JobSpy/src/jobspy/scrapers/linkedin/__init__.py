"""
jobspy.scrapers.linkedin
~~~~~~~~~~~~~~~~~~~

This module contains routines to scrape LinkedIn.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import math
import random
import time
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse, urlunparse, unquote

from bs4 import BeautifulSoup
from bs4.element import Tag
import regex as re
from requests.exceptions import ConnectionError
from urllib3.exceptions import MaxRetryError, ProxyError

from ..proxy_manager import get_proxy_manager
from .constants import headers
from .. import Scraper, ScraperInput, Site
from ..exceptions import LinkedInException
from ..utils import create_session, remove_attributes, create_logger
from ..utils import (
    extract_emails_from_text,
    get_enum_from_job_type,
    currency_parser,
    markdown_converter,
)
from ...jobs import (
    JobPost,
    Location,
    JobResponse,
    JobType,
    Country,
    Compensation,
    DescriptionFormat,
)

logger = create_logger("LinkedIn")


class LinkedInScraper(Scraper):
    base_url = "https://www.linkedin.com"
    delay = 3
    band_delay = 4
    jobs_per_page = 25
    max_retries = 3
    retry_delay = 2

    def __init__(
        self, proxies: list[str] | str | None = None, ca_cert: str | None = None
    ):
        """
        Initializes LinkedInScraper with the LinkedIn job search url

        Args:
            proxies: Optional list of proxy URLs or a single proxy URL
            ca_cert: Optional path to CA certificate file
        """
        super().__init__(Site.LINKEDIN, proxies=proxies, ca_cert=ca_cert)
        self.session = create_session(
            proxies=self.proxies,
            ca_cert=ca_cert,
            is_tls=False,
            has_retry=True,
            delay=5,
            clear_cookies=True,
        )
        self.session.headers.update(headers)
        self.scraper_input = None
        self.country = "worldwide"
        self.job_url_direct_regex = re.compile(r'(?<=\?url=)[^"]+')
        self.proxy_manager = get_proxy_manager()

    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        """
        Scrapes LinkedIn for jobs with scraper_input criteria

        Args:
            scraper_input: Input parameters for the job search

        Returns:
            JobResponse object containing the scraped job posts
        """
        self.scraper_input = scraper_input
        job_list: list[JobPost] = []
        seen_ids = set()
        start = scraper_input.offset // 10 * 10 if scraper_input.offset else 0
        request_count = 0
        seconds_old = (
            scraper_input.hours_old * 3600 if scraper_input.hours_old else None
        )

        if scraper_input.job_type == JobType.WORKING_STUDENT:
            scraper_input.job_type = None
            scraper_input.search_term += " Werkstudent"

        # Define the search continuation condition
        continue_search = lambda: len(job_list) < scraper_input.results_wanted

        while continue_search():
            request_count += 1
            logger.info(
                f"Search page: {request_count} / {math.ceil(scraper_input.results_wanted / 10)}"
            )

            # Prepare search parameters
            params = {
                "keywords": scraper_input.search_term,
                "location": scraper_input.location,
                "distance": scraper_input.distance,
                "f_WT": 2 if scraper_input.is_remote else None,
                "f_JT": (
                    self.job_type_code(scraper_input.job_type)
                    if scraper_input.job_type
                    else None
                ),
                "pageNum": 0,
                "start": start,
                "f_AL": "true" if scraper_input.easy_apply else None,
                "f_C": (
                    ",".join(map(str, scraper_input.linkedin_company_ids))
                    if scraper_input.linkedin_company_ids
                    else None
                ),
            }

            if seconds_old is not None:
                params["f_TPR"] = f"r{seconds_old}"

            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}

            # Get job cards using the proxy manager
            proxy_result = self.proxy_manager.get_working_proxy(
                'linkedin_search',
                self.test_proxy_for_linkedin,
                params
            )

            # Use proxy result if available, otherwise fallback to direct request
            job_cards = proxy_result[1] if (proxy_result and proxy_result[1]) else self._scrape_without_proxy(params)

            if not job_cards:
                logger.error(f"Failed to scrape LinkedIn for {self.scraper_input.search_term}")
                break


            # Process job cards
            for job_card in job_cards:
                href_tag = job_card.find("a", class_="base-card__full-link")
                if href_tag and "href" in href_tag.attrs:
                    href = href_tag.attrs["href"].split("?")[0]
                    job_id = href.split("-")[-1]

                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    try:
                        fetch_desc = scraper_input.linkedin_fetch_description
                        job_post = self._process_job(job_card, job_id, fetch_desc)
                        if job_post:
                            job_list.append(job_post)
                        if not continue_search():
                            break
                    except Exception as e:
                        logger.debug(f"Error processing job card: {str(e)}")

            # If we need more results, prepare for the next page
            if continue_search():
                time.sleep(random.uniform(self.delay, self.delay + self.band_delay))
                start += len(job_list)

        # Limit results to the requested number
        job_list = job_list[:scraper_input.results_wanted]
        return JobResponse(jobs=job_list)

    def _scrape_without_proxy(self, params: Dict[str, Any]) -> Optional[List[Tag]]:
        """
        Fallback method to scrape LinkedIn without using a proxy

        Args:
            params: Search parameters

        Returns:
            List of job card elements if successful, None otherwise
        """
        logger.warning(f"Proxy manager failed, attempting without proxy for {self.scraper_input.search_term}")
        try:
            response = self.session.get(
                f"{self.base_url}/jobs-guest/jobs/api/seeMoreJobPostings/search?",
                params=params,
                timeout=10
            )

            if response.status_code in range(200, 400):
                soup = BeautifulSoup(response.text, "html.parser")
                job_cards = soup.find_all("div", class_="base-search-card")
                if job_cards:
                    logger.info("Successfully scraped without proxy")
                    return job_cards
            else:
                logger.error(f"Failed to scrape without proxy: status {response.status_code}")
        except Exception as e:
            logger.error(f"Exception when scraping without proxy: {str(e)}")

        return None

    def test_proxy_for_linkedin(self, proxy: Dict[str, str], params: Dict[str, Any]) -> Optional[List[Tag]]:
        """
        Test if a proxy works with LinkedIn job search

        Args:
            proxy: Proxy configuration dictionary
            params: Search parameters to test

        Returns:
            List of job card elements if successful, None otherwise
        """
        try:
            session = create_session(
                proxies=proxy,
                is_tls=False,
                ca_cert=None,
                has_retry=False,
                clear_cookies=True,
                delay=1
            )

            response = session.get(
                f"{self.base_url}/jobs-guest/jobs/api/seeMoreJobPostings/search?",
                params=params,
                timeout=10
            )

            if response.status_code not in range(200, 400):
                if response.status_code == 429:
                    logger.debug(f"429 Response - Blocked by LinkedIn for too many requests")
                else:
                    logger.debug(f"LinkedIn response status code {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("div", class_="base-search-card")

            if job_cards:
                return job_cards

        except Exception as e:
            if not isinstance(e, (ProxyError, MaxRetryError, ConnectionError)):
                logger.debug(f"Proxy test error: {str(e)}")

        return None

    def _process_job(
        self, job_card: Tag, job_id: str, full_descr: bool
    ) -> Optional[JobPost]:
        """
        Process a single job card into a JobPost object

        Args:
            job_card: BeautifulSoup job card element
            job_id: LinkedIn job ID
            full_descr: Whether to fetch full job description

        Returns:
            JobPost object or None if processing fails
        """
        try:
            # Extract salary information
            salary_tag = job_card.find("span", class_="job-search-card__salary-info")
            compensation = None

            if salary_tag:
                salary_text = salary_tag.get_text(separator=" ").strip()
                salary_values = [currency_parser(value) for value in salary_text.split("-")]

                if len(salary_values) >= 2:
                    salary_min = salary_values[0]
                    salary_max = salary_values[1]
                    currency = salary_text[0] if salary_text[0] != "$" else "USD"

                    compensation = Compensation(
                        min_amount=int(salary_min),
                        max_amount=int(salary_max),
                        currency=currency,
                    )

            # Extract job title
            title_tag = job_card.find("span", class_="sr-only")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"

            # Extract company information
            company_tag = job_card.find("h4", class_="base-search-card__subtitle")
            company_a_tag = company_tag.find("a") if company_tag else None

            company_url = ""
            if company_a_tag and company_a_tag.has_attr("href"):
                company_url = urlunparse(urlparse(company_a_tag.get("href"))._replace(query=""))

            company = company_a_tag.get_text(strip=True) if company_a_tag else "N/A"

            # Extract location
            metadata_card = job_card.find("div", class_="base-search-card__metadata")
            location = self._get_location(metadata_card)

            # Extract date posted
            datetime_tag = (
                metadata_card.find("time", class_="job-search-card__listdate")
                if metadata_card
                else None
            )

            date_posted = None
            if datetime_tag and "datetime" in datetime_tag.attrs:
                datetime_str = datetime_tag["datetime"]
                try:
                    date_posted = datetime.strptime(datetime_str, "%Y-%m-%d")
                except ValueError:
                    date_posted = None

            # Get additional job details if requested
            job_details = {}
            if full_descr:
                job_details = self._get_job_details(job_id)

            # Create and return the JobPost object
            return JobPost(
                id=f"li-{job_id}",
                title=title,
                company_name=company,
                company_url=company_url,
                location=location,
                date_posted=date_posted,
                job_url=f"{self.base_url}/jobs/view/{job_id}",
                compensation=compensation,
                job_type=job_details.get("job_type"),
                job_level=job_details.get("job_level", "").lower(),
                company_industry=job_details.get("company_industry"),
                description=job_details.get("description"),
                job_url_direct=job_details.get("job_url_direct"),
                emails=extract_emails_from_text(job_details.get("description")),
                company_logo=job_details.get("company_logo"),
                job_function=job_details.get("job_function"),
            )

        except Exception as e:
            logger.debug(f"Error processing job {job_id}: {str(e)}")
            return None

    def _get_job_details(self, job_id: str) -> dict:
        """
        Retrieves job description and other job details by going to the job page url

        Args:
            job_id: LinkedIn job ID

        Returns:
            Dictionary of job details
        """
        # Try to get job details with retries
        for retry in range(self.max_retries):
            try:
                proxy_result = self.proxy_manager.get_working_proxy(
                    'linkedin_job_details',
                    self._test_job_details_proxy,
                    job_id
                )

                if proxy_result and proxy_result[1]:
                    return proxy_result[1]

            except Exception as e:
                logger.debug(f"Error fetching job details (attempt {retry+1}): {str(e)}")

            time.sleep(self.retry_delay)

        # Return empty dict if all retries failed
        return {}

    def _test_job_details_proxy(self, proxy: Dict[str, str], job_id: str) -> Optional[Dict[str, Any]]:
        """
        Test if a proxy works for fetching job details

        Args:
            proxy: Proxy configuration dictionary
            job_id: LinkedIn job ID

        Returns:
            Dictionary of job details if successful, None otherwise
        """
        try:
            session = create_session(
                proxies=proxy,
                is_tls=False,
                ca_cert=None,
                has_retry=False,
                clear_cookies=True
            )

            response = session.get(f"{self.base_url}/jobs/view/{job_id}", timeout=10)

            if response.status_code != 200 or "linkedin.com/signup" in response.url:
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract description
            div_content = soup.find(
                "div", class_=lambda x: x and "show-more-less-html__markup" in x
            )

            description = None
            if div_content is not None:
                div_content = remove_attributes(div_content)
                description = div_content.prettify(formatter="html")

                if self.scraper_input and self.scraper_input.description_format == DescriptionFormat.MARKDOWN:
                    description = markdown_converter(description)

            # Extract job function
            h3_tag = soup.find(
                "h3", text=lambda text: text and "Job function" in text.strip()
            )

            job_function = None
            if h3_tag:
                job_function_span = h3_tag.find_next(
                    "span", class_="description__job-criteria-text"
                )
                if job_function_span:
                    job_function = job_function_span.text.strip()

            # Extract company logo
            company_logo = None
            logo_image = soup.find("img", {"class": "artdeco-entity-image"})
            if logo_image and logo_image.has_attr("data-delayed-url"):
                company_logo = logo_image.get("data-delayed-url")

            # Return all job details
            return {
                "description": description,
                "job_level": self._parse_job_level(soup),
                "company_industry": self._parse_company_industry(soup),
                "job_type": self._parse_job_type(soup),
                "job_url_direct": self._parse_job_url_direct(soup),
                "company_logo": company_logo,
                "job_function": job_function,
            }

        except Exception as e:
            logger.debug(f"Error testing job details proxy: {str(e)}")
            return None

    def _get_location(self, metadata_card: Optional[Tag]) -> Location:
        """
        Extracts the location data from the job metadata card.

        Args:
            metadata_card: BeautifulSoup element containing location metadata

        Returns:
            Location object
        """
        location = Location(country=Country.from_string(self.country))
        if metadata_card is not None:
            location_tag = metadata_card.find(
                "span", class_="job-search-card__location"
            )
            location_string = location_tag.text.strip() if location_tag else "N/A"
            parts = location_string.split(", ")
            if len(parts) == 2:
                city, state = parts
                location = Location(
                    city=city,
                    state=state,
                    country=Country.from_string(self.country),
                )
            elif len(parts) == 3:
                city, state, country = parts
                country = Country.from_string(country)
                location = Location(city=city, state=state, country=country)
        return location

    @staticmethod
    def _parse_job_type(soup_job_type: BeautifulSoup) -> list[JobType] | None:
        """
        Gets the job type from job page

        Args:
            soup_job_type: BeautifulSoup object of the job page

        Returns:
            List of JobType enum values or None
        """
        h3_tag = soup_job_type.find(
            "h3",
            class_="description__job-criteria-subheader",
            string=lambda text: "Employment type" in text,
        )
        employment_type = None
        if h3_tag:
            employment_type_span = h3_tag.find_next_sibling(
                "span",
                class_="description__job-criteria-text description__job-criteria-text--criteria",
            )
            if employment_type_span:
                employment_type = employment_type_span.get_text(strip=True)
                employment_type = employment_type.lower()
                employment_type = employment_type.replace("-", "")

        return [get_enum_from_job_type(employment_type)] if employment_type else []

    @staticmethod
    def _parse_job_level(soup_job_level: BeautifulSoup) -> str | None:
        """
        Gets the job level from job page

        Args:
            soup_job_level: BeautifulSoup object of the job page

        Returns:
            Job level string or None
        """
        h3_tag = soup_job_level.find(
            "h3",
            class_="description__job-criteria-subheader",
            string=lambda text: "Seniority level" in text,
        )
        job_level = None
        if h3_tag:
            job_level_span = h3_tag.find_next_sibling(
                "span",
                class_="description__job-criteria-text description__job-criteria-text--criteria",
            )
            if job_level_span:
                job_level = job_level_span.get_text(strip=True)

        return job_level

    @staticmethod
    def _parse_company_industry(soup_industry: BeautifulSoup) -> str | None:
        """
        Gets the company industry from job page

        Args:
            soup_industry: BeautifulSoup object of the job page

        Returns:
            Company industry string or None
        """
        h3_tag = soup_industry.find(
            "h3",
            class_="description__job-criteria-subheader",
            string=lambda text: "Industries" in text,
        )
        industry = None
        if h3_tag:
            industry_span = h3_tag.find_next_sibling(
                "span",
                class_="description__job-criteria-text description__job-criteria-text--criteria",
            )
            if industry_span:
                industry = industry_span.get_text(strip=True)

        return industry

    def _parse_job_url_direct(self, soup: BeautifulSoup) -> str | None:
        """
        Gets the job url direct from job page

        Args:
            soup: BeautifulSoup object of the job page

        Returns:
            Direct job URL string or None
        """
        job_url_direct = None
        job_url_direct_content = soup.find("code", id="applyUrl")
        if job_url_direct_content:
            job_url_direct_match = self.job_url_direct_regex.search(
                job_url_direct_content.decode_contents().strip()
            )
            if job_url_direct_match:
                job_url_direct = unquote(job_url_direct_match.group())

        return job_url_direct

    @staticmethod
    def job_type_code(job_type_enum: JobType) -> str:
        """
        Convert JobType enum to LinkedIn's job type code

        Args:
            job_type_enum: JobType enum value

        Returns:
            LinkedIn job type code string
        """
        return {
            JobType.FULL_TIME: "F",
            JobType.PART_TIME: "P",
            JobType.INTERNSHIP: "I",
            JobType.CONTRACT: "C",
            JobType.TEMPORARY: "T",
        }.get(job_type_enum, "")
