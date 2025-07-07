"""
jobspy.scrapers.google
~~~~~~~~~~~~~~~~~~~

This module contains routines to scrape Google using improved techniques.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import json
import math
import re
import time
import random
from typing import Tuple, Optional, List, Dict, Any
from urllib.parse import urlencode, quote_plus

import httpx
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError
from urllib3.exceptions import MaxRetryError, ProxyError

from ..proxy_manager import get_proxy_manager
from .constants import headers_jobs, headers_initial, async_param
from .. import Scraper, ScraperInput, Site
from ..utils import (
    create_session,
)
from ..utils import extract_emails_from_text, create_logger, extract_job_type
from ...jobs import (
    JobPost,
    JobResponse,
    Location,
    JobType,
)

logger = create_logger("GoogleImproved")


class GoogleJobsScraper(Scraper):
    """
    Improved Google Jobs Scraper with enhanced reliability and modern techniques.
    """
    
    # Modern user agents for better stealth
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0"
    ]
    
    def __init__(
        self, proxies: list[str] | str | None = None, ca_cert: str | None = None
    ):
        """
        Initializes Google Scraper with improved reliability features
        """
        site = Site(Site.GOOGLE)
        super().__init__(site, proxies=proxies, ca_cert=ca_cert)

        self.response = None
        self.country = None
        self.session = None
        self.scraper_input = None
        self.jobs_per_page = 10
        self.seen_urls = set()
        self.url = "https://www.google.com/search"
        self.jobs_url = "https://www.google.com/async/callback:550"
        self.proxy_manager = get_proxy_manager()
        self.max_retries = 3
        self.retry_delay = 2

    def get_dynamic_headers(self, is_initial: bool = True) -> Dict[str, str]:
        """Generate dynamic headers with random user agent for better stealth."""
        user_agent = random.choice(self.USER_AGENTS)
        
        if is_initial:
            return {
                **headers_initial,
                "user-agent": user_agent,
                "sec-ch-ua": '"Chromium";v="131", "Google Chrome";v="131", "Not?A_Brand";v="99"',
                "sec-ch-ua-full-version": '"131.0.6778.69"',
                "cache-control": "max-age=0",
                "dnt": "1"
            }
        else:
            return {
                **headers_jobs,
                "user-agent": user_agent,
                "sec-ch-ua": '"Chromium";v="131", "Google Chrome";v="131", "Not?A_Brand";v="99"',
                "sec-ch-ua-full-version": '"131.0.6778.69"',
                "x-requested-with": "XMLHttpRequest"
            }

    def build_search_params(self, search_term: str, location: str = None) -> Dict[str, str]:
        """Build optimized search parameters for Google Jobs."""
        query = f"{search_term} jobs"
        if location:
            query += f" in {location}"
            
        return {
            "q": query,
            "udm": "8",  # Jobs search parameter
            "hl": "en",
            "gl": "us",
            "filter": "0",  # No filters initially
            "chips": "date:r_604800",  # Jobs from last week for freshness
        }

    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        """
        Scrapes Google for jobs with improved reliability and error handling.
        :param scraper_input: Information about job search criteria.
        :return: JobResponse containing a list of jobs.
        """
        self.scraper_input = scraper_input
        self.scraper_input.results_wanted = min(900, scraper_input.results_wanted)

        logger.info(f"Starting improved Google Jobs search for: {scraper_input.search_term}")
        
        # Get a working session with proxy
        proxy, response = self.proxy_manager.get_working_proxy(
            'google',
            self.test_proxy_for_google,
            f"{self.scraper_input.search_term} jobs"
        )

        if not response:
            logger.error("Failed to find a working proxy for Google Jobs")
            return JobResponse(jobs=[])

        # Create a session with the working proxy and improved settings
        self.session = create_session(
            proxies=proxy, ca_cert=self.ca_cert, is_tls=True, has_retry=True
        )

        # Extract initial data with improved parsing
        forward_cursor, job_list = self._extract_initial_cursor_and_jobs_improved(response.text)

        if forward_cursor is None:
            logger.warning(
                "Initial cursor not found, try changing your query or there was at most 10 results"
            )
            return JobResponse(jobs=job_list)

        page = 1

        while (
            len(self.seen_urls) < scraper_input.results_wanted + scraper_input.offset
            and forward_cursor
            and page <= 10  # Limit pages to prevent infinite loops
        ):
            logger.info(
                f"Search page: {page} / {min(10, math.ceil(scraper_input.results_wanted / self.jobs_per_page))}"
            )

            # Use improved retry mechanism for pagination
            for retry in range(self.max_retries):
                try:
                    jobs, forward_cursor = self._get_jobs_next_page_improved(forward_cursor)
                    if jobs:
                        job_list.extend(jobs)
                        break
                    elif not forward_cursor:
                        # No more pages available
                        break
                except Exception as e:
                    logger.warning(f"Error on page {page}, retry {retry+1}/{self.max_retries}: {e}")
                    if retry == self.max_retries - 1:
                        logger.error(f"Failed to get jobs on page: {page} after {self.max_retries} retries")
                        forward_cursor = None
                        break
                    
                    # Exponential backoff with jitter
                    delay = self.retry_delay * (2 ** retry) + random.uniform(0, 1)
                    time.sleep(delay)

            if not forward_cursor:
                break

            # Add random delay between pages to be more human-like
            time.sleep(random.uniform(1, 3))
            page += 1

        logger.info(f"Successfully scraped {len(job_list)} jobs from Google")
        
        return JobResponse(
            jobs=job_list[
                scraper_input.offset : scraper_input.offset
                + scraper_input.results_wanted
            ]
        )

    def test_proxy_for_google(self, proxy: Dict[str, str], query: str) -> Optional[httpx.Response]:
        """
        Test if a proxy works with Google search using improved stealth techniques.

        Args:
            proxy: Proxy configuration dictionary
            query: Search query to test

        Returns:
            Response object if successful, None otherwise
        """
        try:
            # Use improved search parameters
            params = self.build_search_params(query)
            
            session = create_session(
                proxies=proxy,
                is_tls=True,  # Use TLS for better security
                ca_cert=None,
                has_retry=False,
                clear_cookies=True,
                delay=random.uniform(1, 2)  # Random delay for stealth
            )

            response = session.get(
                'https://www.google.com/search',
                headers=self.get_dynamic_headers(is_initial=True),
                timeout=25,
                params=params
            )

            if response.status_code == 200:
                # More robust verification
                text_lower = response.text.lower()
                
                # Check for job-related content and avoid CAPTCHA/blocked indicators
                has_jobs = any(indicator in text_lower for indicator in [
                    "jobs", "careers", "employment", "work", "hiring"
                ])
                
                has_blocking_signs = any(sign in text_lower for sign in [
                    "captcha", "unusual traffic", "blocked", "access denied",
                    "robot", "automated queries"
                ])
                
                if has_jobs and not has_blocking_signs and "callback:550" in response.text:
                    logger.debug("Proxy test successful for Google Jobs")
                    return response
                else:
                    logger.debug("Proxy test failed: missing job content or blocking detected")

        except Exception as e:
            if not isinstance(e, (ProxyError, MaxRetryError, ConnectionError)):
                logger.debug(f"Proxy test error: {str(e)}")

        return None

    def _extract_initial_cursor_and_jobs_improved(self, html_text: str) -> Tuple[str, list[JobPost]]:
        """Gets initial cursor and jobs from an HTML response with improved parsing"""
        try:
            # Use BeautifulSoup for more robust HTML parsing
            soup = BeautifulSoup(html_text, 'html.parser')
            
            # Extract cursor using multiple strategies
            data_async_fc = None
            
            # Strategy 1: Look for data-async-fc attribute
            cursor_elements = soup.find_all('div', {'data-async-fc': True})
            if cursor_elements:
                data_async_fc = cursor_elements[0].get('data-async-fc')
            else:
                # Strategy 2: Regex fallback
                pattern_fc = r'data-async-fc="([^"]+)"'
                match_fc = re.search(pattern_fc, html_text)
                data_async_fc = match_fc.group(1) if match_fc else None

            # Extract jobs using improved methods
            jobs_raw = self._find_job_info_initial_page_improved(html_text, soup)
            if not jobs_raw:
                logger.warning("No jobs found on the initial page")
                return None, []

            jobs = []
            for job_raw in jobs_raw:
                job_post = self._parse_job_improved(job_raw)
                if job_post:
                    jobs.append(job_post)

            logger.info(f"Found {len(jobs)} jobs on initial page")
            return data_async_fc, jobs
            
        except Exception as e:
            logger.error(f"Error in improved initial parsing: {e}")
            # Fallback to original method
            return self._extract_initial_cursor_and_jobs(html_text)

    def _extract_initial_cursor_and_jobs(self, html_text: str) -> Tuple[str, list[JobPost]]:
        """Gets initial cursor and jobs from an HTML response"""
        pattern_fc = r'<div jsname="Yust4d"[^>]+data-async-fc="([^"]+)"'
        match_fc = re.search(pattern_fc, html_text)
        data_async_fc = match_fc.group(1) if match_fc else None

        jobs_raw = self._find_job_info_initial_page(html_text)
        if not jobs_raw:
            logger.warning("No jobs found on the initial page")
            return None, []

        jobs = []
        for job_raw in jobs_raw:
            job_post = self._parse_job(job_raw)
            if job_post:
                jobs.append(job_post)

        return data_async_fc, jobs

    def _get_jobs_next_page_improved(self, forward_cursor: str) -> Tuple[list[JobPost], str]:
        """
        Gets jobs from the next page using improved request handling.

        Args:
            forward_cursor: Cursor for the next page of results

        Returns:
            Tuple of (job_posts, next_cursor)
        """
        params = {"fc": [forward_cursor], "fcv": ["3"], "async": [async_param]}

        for retry in range(self.max_retries):
            try:
                response = self.session.get(
                    self.jobs_url,
                    headers=self.get_dynamic_headers(is_initial=False),
                    params=params,
                    timeout=20  # Increased timeout
                )

                if response.status_code == 200:
                    return self._parse_jobs_improved(response.text)
                else:
                    logger.warning(f"Got status code {response.status_code} when fetching next page")

            except Exception as e:
                logger.warning(f"Error fetching next page: {str(e)}")

                # If we've reached the last retry, try with a new proxy
                if retry == self.max_retries - 1:
                    logger.info("Trying with a new proxy...")
                    self.proxy_manager.invalidate_proxy('google')
                    proxy, _ = self.proxy_manager.get_working_proxy(
                        'google',
                        self.test_proxy_for_google,
                        f"{self.scraper_input.search_term} jobs"
                    )

                    if proxy:
                        self.session = create_session(
                            proxies=proxy, ca_cert=self.ca_cert, is_tls=True, has_retry=True
                        )

            # Exponential backoff with jitter
            delay = self.retry_delay * (2 ** retry) + random.uniform(0, 1)
            time.sleep(delay)

        # If we get here, all retries failed
        raise Exception("Failed to get next page of jobs after multiple retries")

    def _get_jobs_next_page(self, forward_cursor: str) -> Tuple[list[JobPost], str]:
        """
        Gets jobs from the next page using the forward cursor.

        Args:
            forward_cursor: Cursor for the next page of results

        Returns:
            Tuple of (job_posts, next_cursor)
        """
        params = {"fc": [forward_cursor], "fcv": ["3"], "async": [async_param]}

        for retry in range(self.max_retries):
            try:
                response = self.session.get(
                    self.jobs_url,
                    headers=headers_jobs,
                    params=params,
                    timeout=15
                )

                if response.status_code == 200:
                    return self._parse_jobs(response.text)

                logger.warning(f"Got status code {response.status_code} when fetching next page")

            except Exception as e:
                logger.warning(f"Error fetching next page: {str(e)}")

                # If we've reached the last retry, try with a new proxy
                if retry == self.max_retries - 1:
                    logger.info("Trying with a new proxy...")
                    self.proxy_manager.invalidate_proxy('google')
                    proxy, _ = self.proxy_manager.get_working_proxy(
                        'google',
                        self.test_proxy_for_google,
                        f"{self.scraper_input.search_term} jobs"
                    )

                    if proxy:
                        self.session = create_session(
                            proxies=proxy, ca_cert=self.ca_cert, is_tls=False, has_retry=True
                        )

            time.sleep(self.retry_delay)

        # If we get here, all retries failed
        raise Exception("Failed to get next page of jobs after multiple retries")

    def _parse_jobs_improved(self, job_data: str) -> Tuple[list[JobPost], str]:
        """
        Parses jobs on a page with improved error handling and data extraction
        """
        try:
            return self._parse_jobs(job_data)
        except Exception as e:
            logger.error(f"Improved parsing failed, trying alternative methods: {e}")
            
            # Try alternative parsing strategies
            jobs = []
            next_cursor = None
            
            try:
                # Strategy 1: Look for JSON data in different patterns
                patterns = [
                    r'\[\[\[.*?\]\]\]',
                    r'"520084652":\s*\[.*?\]',
                    r'AF_initDataCallback.*?\[.*?\]'
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, job_data, re.DOTALL)
                    for match in matches:
                        try:
                            # Try to extract and parse job data
                            match_text = match.group(0)
                            if self._contains_job_data(match_text):
                                extracted_jobs = self._extract_jobs_from_match(match_text)
                                jobs.extend(extracted_jobs)
                        except Exception as parse_error:
                            logger.debug(f"Failed to parse match: {parse_error}")
                            continue
                
                # Extract cursor
                pattern_fc = r'data-async-fc="([^"]+)"'
                match_fc = re.search(pattern_fc, job_data)
                next_cursor = match_fc.group(1) if match_fc else None
                
            except Exception as alt_error:
                logger.error(f"Alternative parsing also failed: {alt_error}")
                
            return jobs, next_cursor

    def _contains_job_data(self, text: str) -> bool:
        """Check if text contains job-related data"""
        job_indicators = ['job', 'title', 'company', 'location', 'description']
        text_lower = text.lower()
        return sum(indicator in text_lower for indicator in job_indicators) >= 2

    def _extract_jobs_from_match(self, match_text: str) -> List[JobPost]:
        """Extract jobs from a regex match"""
        jobs = []
        try:
            # Try to find JSON-like structures
            if match_text.startswith('[[['):
                # Handle array format
                json_data = json.loads(match_text)
                if isinstance(json_data, list) and len(json_data) > 0:
                    for item in json_data[0] if json_data else []:
                        if isinstance(item, list) and len(item) >= 2:
                            job_info = self._find_job_info(item[1] if len(item) > 1 else item)
                            if job_info:
                                job = self._parse_job_improved(job_info)
                                if job:
                                    jobs.append(job)
        except Exception as e:
            logger.debug(f"Error extracting jobs from match: {e}")
            
        return jobs

    def _parse_jobs(self, job_data: str) -> Tuple[list[JobPost], str]:
        """
        Parses jobs on a page with next page cursor
        """
        start_idx = job_data.find("[[[")
        end_idx = job_data.rindex("]]]") + 3

        if start_idx == -1 or end_idx <= 2:
            logger.warning("Invalid job data format received")
            return [], None

        s = job_data[start_idx:end_idx]

        try:
            parsed = json.loads(s)[0]
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse job data: {str(e)}")
            return [], None

        pattern_fc = r'data-async-fc="([^"]+)"'
        match_fc = re.search(pattern_fc, job_data)
        data_async_fc = match_fc.group(1) if match_fc else None

        jobs_on_page = []
        for array in parsed:
            try:
                _, job_data = array
                if not job_data.startswith("[[["):
                    continue

                job_d = json.loads(job_data)
                job_info = self._find_job_info(job_d)

                if not job_info:
                    continue

                job_post = self._parse_job(job_info)
                if job_post:
                    jobs_on_page.append(job_post)

            except Exception as e:
                logger.debug(f"Error parsing job entry: {str(e)}")
                continue

        return jobs_on_page, data_async_fc

    def _parse_job_improved(self, job_info: list) -> Optional[JobPost]:
        """
        Parse job information into a JobPost object with improved data extraction

        Args:
            job_info: Raw job information

        Returns:
            JobPost object or None if invalid/duplicate
        """
        try:
            # Use original parsing as primary method
            job_post = self._parse_job(job_info)
            if job_post:
                return job_post
                
            # If original fails, try improved extraction
            return self._parse_job_alternative(job_info)
            
        except Exception as e:
            logger.debug(f"Error in improved job parsing: {str(e)}")
            return None

    def _parse_job_alternative(self, job_info: list) -> Optional[JobPost]:
        """Alternative job parsing method with more flexible data extraction"""
        try:
            if not isinstance(job_info, list) or len(job_info) < 5:
                return None
                
            # Extract basic info with safe indexing
            title = self._safe_extract(job_info, 0, "Unknown Title")
            company_name = self._safe_extract(job_info, 1, "Unknown Company")
            location_str = self._safe_extract(job_info, 2, "")
            
            # Extract job URL with multiple strategies
            job_url = None
            if len(job_info) > 3 and job_info[3]:
                if isinstance(job_info[3], list) and len(job_info[3]) > 0:
                    if isinstance(job_info[3][0], list) and len(job_info[3][0]) > 0:
                        job_url = job_info[3][0][0]
                    else:
                        job_url = job_info[3][0]
                elif isinstance(job_info[3], str):
                    job_url = job_info[3]

            # Skip if no URL or already seen
            if not job_url or job_url in self.seen_urls:
                return None
            self.seen_urls.add(job_url)

            # Parse location with improved handling
            location = self._parse_location_improved(location_str)

            # Extract date with multiple strategies
            date_posted = None
            for idx in [12, 10, 11, 13, 14]:  # Try multiple potential date indices
                if len(job_info) > idx and job_info[idx]:
                    date_posted = self._parse_date_improved(job_info[idx])
                    if date_posted:
                        break

            # Extract description
            description = ""
            for idx in [19, 15, 16, 17, 18, 20]:  # Try multiple potential description indices
                if len(job_info) > idx and job_info[idx]:
                    desc_candidate = str(job_info[idx])
                    if len(desc_candidate) > len(description):
                        description = desc_candidate

            # Determine if remote
            is_remote = self._is_remote_job_improved(description, location_str)

            # Generate job ID
            job_id = f"google_alt_{abs(hash(job_url))}"

            return JobPost(
                id=job_id,
                title=title,
                company_name=company_name,
                location=location,
                job_url=job_url,
                date_posted=date_posted,
                is_remote=is_remote,
                description=description,
                emails=extract_emails_from_text(description),
                job_type=extract_job_type(description),
            )

        except Exception as e:
            logger.debug(f"Error in alternative job parsing: {str(e)}")
            return None

    def _safe_extract(self, data: list, index: int, default: str = "") -> str:
        """Safely extract string from list with default"""
        try:
            if len(data) > index and data[index] is not None:
                return str(data[index])
        except (IndexError, TypeError):
            pass
        return default

    def _parse_location_improved(self, location_str: str) -> Location:
        """Parse location string with improved handling"""
        if not location_str:
            return Location(city=None, state=None, country=None)

        # Clean the location string
        location_str = location_str.strip()
        
        # Handle common formats
        if "," in location_str:
            parts = [part.strip() for part in location_str.split(",")]
            if len(parts) >= 2:
                city = parts[0] if parts[0] else None
                state = parts[1] if len(parts) > 1 and parts[1] else None
                country = parts[2] if len(parts) > 2 and parts[2] else None
                return Location(city=city, state=state, country=country)
        
        # Single location (could be city, state, or country)
        return Location(city=location_str, state=None, country=None)

    def _parse_date_improved(self, date_input: Any) -> Optional[datetime]:
        """Parse date with improved handling of various formats"""
        if not date_input:
            return None

        date_str = str(date_input).lower()
        
        try:
            # Handle relative dates
            if "day" in date_str or "ago" in date_str:
                # Extract number of days
                numbers = re.findall(r'\d+', date_str)
                if numbers:
                    days_ago = int(numbers[0])
                    return datetime.now() - timedelta(days=days_ago)
            
            # Handle specific keywords
            if any(word in date_str for word in ["today", "now"]):
                return datetime.now()
            elif any(word in date_str for word in ["yesterday"]):
                return datetime.now() - timedelta(days=1)
            elif any(word in date_str for word in ["week"]):
                weeks = re.findall(r'\d+', date_str)
                weeks_ago = int(weeks[0]) if weeks else 1
                return datetime.now() - timedelta(weeks=weeks_ago)
            elif any(word in date_str for word in ["month"]):
                months = re.findall(r'\d+', date_str)
                months_ago = int(months[0]) if months else 1
                return datetime.now() - timedelta(days=months_ago * 30)

        except Exception as e:
            logger.debug(f"Error parsing date '{date_input}': {e}")

        return None

    def _is_remote_job_improved(self, description: str, location: str) -> bool:
        """Improved remote job detection"""
        text = f"{description} {location}".lower()
        
        remote_keywords = [
            "remote", "work from home", "wfh", "telecommute", "virtual",
            "anywhere", "distributed", "home office", "work remotely",
            "location independent", "nomad", "flexible location"
        ]
        
        return any(keyword in text for keyword in remote_keywords)

    def _parse_job(self, job_info: list) -> Optional[JobPost]:
        """
        Parse job information into a JobPost object

        Args:
            job_info: Raw job information

        Returns:
            JobPost object or None if invalid/duplicate
        """
        try:
            job_url = job_info[3][0][0] if job_info[3] and job_info[3][0] else None

            # Skip duplicates
            if not job_url or job_url in self.seen_urls:
                return None

            self.seen_urls.add(job_url)

            title = job_info[0]
            company_name = job_info[1]
            location = city = job_info[2]
            state = country = date_posted = None

            if location and "," in location:
                parts = [part.strip() for part in location.split(",")]
                if len(parts) >= 2:
                    city = parts[0]
                    state = parts[1]
                    country = parts[2] if len(parts) > 2 else None

            days_ago_str = job_info[12]
            if isinstance(days_ago_str, str):
                match = re.search(r"\d+", days_ago_str)
                days_ago = int(match.group()) if match else None
                date_posted = (datetime.now() - timedelta(days=days_ago)).date() if days_ago else None

            description = job_info[19] if len(job_info) > 19 else ""
            is_remote = any(keyword in description.lower() for keyword in ["remote", "wfh", "work from home"])

            return JobPost(
                id=f"go-{job_info[28]}" if len(job_info) > 28 else f"go-{hash(job_url)}",
                title=title,
                company_name=company_name,
                location=Location(
                    city=city,
                    state=state,
                    country=country
                ),
                job_url=job_url,
                date_posted=date_posted,
                is_remote=is_remote,
                description=description,
                emails=extract_emails_from_text(description),
                job_type=extract_job_type(description),
            )

        except Exception as e:
            logger.debug(f"Error parsing job: {str(e)}")
            return None

    @staticmethod
    def _find_job_info(jobs_data: list | dict) -> list | None:
        """Iterates through the JSON data to find the job listings"""
        if isinstance(jobs_data, dict):
            for key, value in jobs_data.items():
                if key == "520084652" and isinstance(value, list):
                    return value
                else:
                    result = GoogleJobsScraper._find_job_info(value)
                    if result:
                        return result
        elif isinstance(jobs_data, list):
            for item in jobs_data:
                result = GoogleJobsScraper._find_job_info(item)
                if result:
                    return result
        return None

    def _find_job_info_initial_page_improved(self, html_text: str, soup: BeautifulSoup = None) -> List[List]:
        """
        Extract job information from the initial page HTML with improved techniques

        Args:
            html_text: HTML content of the initial page
            soup: BeautifulSoup object for the page (optional)

        Returns:
            List of job information arrays
        """
        results = []
        
        try:
            # Strategy 1: Use BeautifulSoup to find structured data
            if soup:
                script_tags = soup.find_all('script')
                for script in script_tags:
                    if script.string and '520084652' in script.string:
                        try:
                            # Look for the job data pattern
                            matches = re.finditer(r'"520084652":\s*(\[.*?\])', script.string, re.DOTALL)
                            for match in matches:
                                try:
                                    job_data = json.loads(match.group(1))
                                    if isinstance(job_data, list):
                                        results.append(job_data)
                                except json.JSONDecodeError:
                                    continue
                        except Exception as e:
                            logger.debug(f"Error processing script tag: {e}")
                            continue
            
            # Strategy 2: Improved regex patterns
            if not results:
                patterns = [
                    rf'520084652":\s*(\[.*?\]\s*])\s*}}\s*]\s*]\s*]\s*]\s*]',
                    rf'"520084652":\s*(\[.*?\])',
                    rf'520084652.*?(\[.*?\])',
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, html_text, re.DOTALL)
                    for match in matches:
                        try:
                            parsed_data = json.loads(match.group(1))
                            if isinstance(parsed_data, list):
                                results.append(parsed_data)
                        except json.JSONDecodeError as e:
                            logger.debug(f"Failed to parse match with pattern: {e}")
                            continue
                    
                    if results:  # If we found results with this pattern, stop trying others
                        break
            
            # Strategy 3: Look for AF_initDataCallback patterns
            if not results:
                af_pattern = r'AF_initDataCallback\(\{[^}]*"520084652"[^}]*\}\);'
                af_matches = re.finditer(af_pattern, html_text, re.DOTALL)
                for match in af_matches:
                    try:
                        # Extract JSON from the callback
                        callback_text = match.group(0)
                        json_match = re.search(r'\{.*\}', callback_text, re.DOTALL)
                        if json_match:
                            callback_data = json.loads(json_match.group(0))
                            # Navigate through the callback structure to find job data
                            job_data = self._extract_from_callback(callback_data)
                            if job_data:
                                results.extend(job_data)
                    except Exception as e:
                        logger.debug(f"Error processing AF_initDataCallback: {e}")
                        continue
            
            # Strategy 4: Fallback to original method
            if not results:
                results = self._find_job_info_initial_page(html_text)
            
            logger.debug(f"Found {len(results)} job entries using improved extraction")
            return results
            
        except Exception as e:
            logger.error(f"Error in improved job info extraction: {e}")
            # Fallback to original method
            return self._find_job_info_initial_page(html_text)

    def _extract_from_callback(self, callback_data: dict) -> List[List]:
        """Extract job data from AF_initDataCallback structure"""
        results = []
        try:
            # Navigate through nested structure to find job arrays
            def find_job_arrays(obj):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key == "520084652" and isinstance(value, list):
                            results.append(value)
                        else:
                            find_job_arrays(value)
                elif isinstance(obj, list):
                    for item in obj:
                        find_job_arrays(item)
            
            find_job_arrays(callback_data)
        except Exception as e:
            logger.debug(f"Error extracting from callback: {e}")
            
        return results

    @staticmethod
    def _find_job_info_initial_page(html_text: str) -> List[List]:
        """
        Extract job information from the initial page HTML

        Args:
            html_text: HTML content of the initial page

        Returns:
            List of job information arrays
        """
        pattern = (
            f'520084652":('
            + r"\[.*?\]\s*])\s*}\s*]\s*]\s*]\s*]\s*]"
        )
        results = []
        matches = re.finditer(pattern, html_text)

        import json

        for match in matches:
            try:
                parsed_data = json.loads(match.group(1))
                results.append(parsed_data)
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse match: {str(e)}")

        return results
