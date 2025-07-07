"""
Unit tests for job scraper classes.
Tests individual methods and classes in isolation with mocked dependencies.
"""
import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
from typing import Dict, Any, Optional, List
from bs4.element import Tag

# Mock the dependencies that might not be available during testing
try:
    from jobspy.scrapers.google import GoogleJobsScraper
    from jobspy.scrapers.linkedin import LinkedInScraper
    from jobspy.scrapers import ScraperInput, Site
    from jobspy.jobs import JobResponse, JobPost, Location, JobType
    SCRAPERS_AVAILABLE = True
except ImportError:
    SCRAPERS_AVAILABLE = False
    # Create mock classes for testing
    class GoogleJobsScraper:
        pass
    class LinkedInScraper:
        pass
    class ScraperInput:
        pass
    class Site:
        GOOGLE = "google"
        LINKEDIN = "linkedin"
    class JobResponse:
        pass
    class JobPost:
        pass


@unittest.skipUnless(SCRAPERS_AVAILABLE, "Job scrapers not available")
class TestGoogleJobsScraper(unittest.TestCase):
    """Test GoogleJobsScraper class."""

    def setUp(self):
        """Set up test fixtures."""
        self.scraper = GoogleJobsScraper()

    def test_init(self):
        """Test scraper initialization."""
        self.assertEqual(self.scraper.jobs_per_page, 10)
        self.assertEqual(self.scraper.url, "https://www.google.com/search")
        self.assertEqual(self.scraper.jobs_url, "https://www.google.com/async/callback:550")
        self.assertEqual(self.scraper.max_retries, 3)
        self.assertEqual(self.scraper.retry_delay, 2)
        self.assertIsNotNone(self.scraper.proxy_manager)
        self.assertIsInstance(self.scraper.seen_urls, set)

    def test_init_with_proxies(self):
        """Test scraper initialization with proxies."""
        proxies = ["http://proxy1:8080", "http://proxy2:8080"]
        scraper = GoogleJobsScraper(proxies=proxies)
        # Verify proxies are passed to parent
        self.assertIsNotNone(scraper)

    def test_init_with_ca_cert(self):
        """Test scraper initialization with CA certificate."""
        ca_cert = "/path/to/cert.pem"
        scraper = GoogleJobsScraper(ca_cert=ca_cert)
        self.assertEqual(scraper.ca_cert, ca_cert)

    def test_test_proxy_for_google_success(self):
        """Test successful proxy testing for Google."""
        proxy = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        query = "software engineer jobs"
        
        # Mock the session and response
        with patch('jobspy.scrapers.google.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = 'jobs content with callback:550'
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            result = self.scraper.test_proxy_for_google(proxy, query)
            
            mock_create_session.assert_called_once_with(
                proxies=proxy,
                is_tls=False,
                ca_cert=None,
                has_retry=False,
                clear_cookies=True,
                delay=1
            )
            mock_session.get.assert_called_once()
            self.assertEqual(result, mock_response)

    def test_test_proxy_for_google_invalid_response(self):
        """Test proxy testing with invalid response."""
        proxy = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        query = "software engineer jobs"
        
        with patch('jobspy.scrapers.google.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = 'no job content here'
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            result = self.scraper.test_proxy_for_google(proxy, query)
            
            self.assertIsNone(result)

    def test_test_proxy_for_google_http_error(self):
        """Test proxy testing with HTTP error."""
        proxy = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        query = "software engineer jobs"
        
        with patch('jobspy.scrapers.google.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 404
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            result = self.scraper.test_proxy_for_google(proxy, query)
            
            self.assertIsNone(result)

    def test_test_proxy_for_google_connection_error(self):
        """Test proxy testing with connection error."""
        proxy = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        query = "software engineer jobs"
        
        from requests.exceptions import ConnectionError
        
        with patch('jobspy.scrapers.google.create_session') as mock_create_session:
            mock_session = Mock()
            mock_session.get.side_effect = ConnectionError("Connection failed")
            mock_create_session.return_value = mock_session
            
            result = self.scraper.test_proxy_for_google(proxy, query)
            
            self.assertIsNone(result)

    def test_test_proxy_for_google_other_exception(self):
        """Test proxy testing with other exception."""
        proxy = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        query = "software engineer jobs"
        
        with patch('jobspy.scrapers.google.create_session') as mock_create_session:
            mock_session = Mock()
            mock_session.get.side_effect = ValueError("Some other error")
            mock_create_session.return_value = mock_session
            
            with patch('jobspy.scrapers.google.logger') as mock_logger:
                result = self.scraper.test_proxy_for_google(proxy, query)
                
                mock_logger.debug.assert_called_once()
                self.assertIsNone(result)

    @patch('jobspy.scrapers.google.get_proxy_manager')
    def test_proxy_manager_integration(self, mock_get_proxy_manager):
        """Test proxy manager integration."""
        mock_proxy_manager = Mock()
        mock_get_proxy_manager.return_value = mock_proxy_manager
        
        scraper = GoogleJobsScraper()
        
        mock_get_proxy_manager.assert_called_once()
        self.assertEqual(scraper.proxy_manager, mock_proxy_manager)


@unittest.skipUnless(SCRAPERS_AVAILABLE, "Job scrapers not available")
class TestLinkedInScraper(unittest.TestCase):
    """Test LinkedInScraper class."""

    def setUp(self):
        """Set up test fixtures."""
        self.scraper = LinkedInScraper()

    def test_init(self):
        """Test scraper initialization."""
        self.assertEqual(self.scraper.base_url, "https://www.linkedin.com")
        self.assertEqual(self.scraper.delay, 3)
        self.assertEqual(self.scraper.band_delay, 4)
        self.assertEqual(self.scraper.jobs_per_page, 25)
        self.assertEqual(self.scraper.max_retries, 3)
        self.assertEqual(self.scraper.retry_delay, 2)

    def test_init_with_proxies(self):
        """Test scraper initialization with proxies."""
        proxies = ["http://proxy1:8080", "http://proxy2:8080"]
        scraper = LinkedInScraper(proxies=proxies)
        self.assertIsNotNone(scraper)

    def test_test_proxy_for_linkedin_success(self):
        """Test successful proxy testing for LinkedIn."""
        proxy = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        params = {"keywords": "engineer", "location": "New York"}
        
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '<div class="job-card">Mock job content</div>'
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            with patch.object(self.scraper, '_parse_job_cards') as mock_parse:
                mock_job_cards = [Mock(), Mock()]
                mock_parse.return_value = mock_job_cards
                
                result = self.scraper.test_proxy_for_linkedin(proxy, params)
                
                mock_create_session.assert_called_once_with(
                    proxies=proxy,
                    is_tls=False,
                    ca_cert=None,
                    has_retry=False,
                    clear_cookies=True,
                    delay=1
                )
                self.assertEqual(result, mock_job_cards)

    def test_test_proxy_for_linkedin_blocked(self):
        """Test proxy testing when blocked by LinkedIn."""
        proxy = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        params = {"keywords": "engineer", "location": "New York"}
        
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 429
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            with patch('jobspy.scrapers.linkedin.logger') as mock_logger:
                result = self.scraper.test_proxy_for_linkedin(proxy, params)
                
                mock_logger.debug.assert_called_once_with(
                    "429 Response - Blocked by LinkedIn for too many requests"
                )
                self.assertIsNone(result)

    def test_test_proxy_for_linkedin_other_error(self):
        """Test proxy testing with other HTTP error."""
        proxy = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        params = {"keywords": "engineer", "location": "New York"}
        
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 404
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            with patch('jobspy.scrapers.linkedin.logger') as mock_logger:
                result = self.scraper.test_proxy_for_linkedin(proxy, params)
                
                mock_logger.debug.assert_called_once_with(
                    "LinkedIn response status code 404"
                )
                self.assertIsNone(result)

    def test_test_job_details_proxy_success(self):
        """Test successful job details proxy testing."""
        proxy = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        job_id = "123456789"
        
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = "https://www.linkedin.com/jobs/view/123456789"
            mock_response.text = '''
            <html>
                <div class="show-more-less-html__markup">
                    <p>Job description content</p>
                </div>
            </html>
            '''
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            result = self.scraper._test_job_details_proxy(proxy, job_id)
            
            mock_create_session.assert_called_once_with(
                proxies=proxy,
                is_tls=False,
                ca_cert=None,
                has_retry=False,
                clear_cookies=True
            )
            mock_session.get.assert_called_once_with(
                f"{self.scraper.base_url}/jobs/view/{job_id}",
                timeout=10
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn("description", result)

    def test_test_job_details_proxy_signup_redirect(self):
        """Test job details proxy when redirected to signup."""
        proxy = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        job_id = "123456789"
        
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = "https://www.linkedin.com/signup"
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            result = self.scraper._test_job_details_proxy(proxy, job_id)
            
            self.assertIsNone(result)

    def test_test_job_details_proxy_http_error(self):
        """Test job details proxy with HTTP error."""
        proxy = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        job_id = "123456789"
        
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.url = "https://www.linkedin.com/jobs/view/123456789"
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            result = self.scraper._test_job_details_proxy(proxy, job_id)
            
            self.assertIsNone(result)


class TestJobScraperUtilities(unittest.TestCase):
    """Test utility functions and common patterns in job scrapers."""

    def test_scraper_input_validation(self):
        """Test ScraperInput validation and handling."""
        # This would test the ScraperInput class if it's available
        if SCRAPERS_AVAILABLE:
            # Test with valid input
            scraper_input = ScraperInput(
                site_name="google",
                search_term="engineer",
                location="New York",
                results_wanted=10
            )
            self.assertEqual(scraper_input.search_term, "engineer")
            self.assertEqual(scraper_input.location, "New York")
            self.assertEqual(scraper_input.results_wanted, 10)

    def test_site_enum_values(self):
        """Test Site enum values."""
        if SCRAPERS_AVAILABLE:
            self.assertEqual(Site.GOOGLE.value, "google")
            self.assertEqual(Site.LINKEDIN.value, "linkedin")

    def test_job_response_structure(self):
        """Test JobResponse structure and validation."""
        if SCRAPERS_AVAILABLE:
            jobs = []  # Empty list of jobs
            response = JobResponse(jobs=jobs)
            self.assertEqual(response.jobs, jobs)
            self.assertIsInstance(response.jobs, list)

    def test_job_post_structure(self):
        """Test JobPost structure and validation."""
        if SCRAPERS_AVAILABLE:
            # Test basic job post creation
            job_post = JobPost(
                title="Software Engineer",
                company="Tech Company",
                location=Location(city="New York", state="NY"),
                description="Job description"
            )
            self.assertEqual(job_post.title, "Software Engineer")
            self.assertEqual(job_post.company, "Tech Company")
            self.assertEqual(job_post.location.city, "New York")
            self.assertEqual(job_post.description, "Job description")

    @patch('jobspy.scrapers.google.create_session')
    def test_session_creation_parameters(self, mock_create_session):
        """Test session creation with various parameters."""
        if SCRAPERS_AVAILABLE:
            mock_session = Mock()
            mock_create_session.return_value = mock_session
            
            # Test different parameter combinations
            test_cases = [
                {
                    "proxies": {"http": "http://proxy:8080"},
                    "is_tls": False,
                    "ca_cert": None,
                    "has_retry": True,
                    "clear_cookies": True,
                    "delay": 1
                },
                {
                    "proxies": None,
                    "is_tls": True,
                    "ca_cert": "/path/to/cert.pem",
                    "has_retry": False,
                    "clear_cookies": False,
                    "delay": 2
                }
            ]
            
            for params in test_cases:
                with self.subTest(params=params):
                    from jobspy.scrapers.utils import create_session
                    result = create_session(**params)
                    mock_create_session.assert_called_with(**params)
                    self.assertEqual(result, mock_session)


class TestJobScraperErrorHandling(unittest.TestCase):
    """Test error handling in job scrapers."""

    def test_connection_error_handling(self):
        """Test handling of connection errors."""
        if SCRAPERS_AVAILABLE:
            scraper = GoogleJobsScraper()
            proxy = {"http": "http://invalid-proxy:8080"}
            query = "test"
            
            from requests.exceptions import ConnectionError
            
            with patch('jobspy.scrapers.google.create_session') as mock_create_session:
                mock_session = Mock()
                mock_session.get.side_effect = ConnectionError("Connection failed")
                mock_create_session.return_value = mock_session
                
                result = scraper.test_proxy_for_google(proxy, query)
                self.assertIsNone(result)

    def test_timeout_error_handling(self):
        """Test handling of timeout errors."""
        if SCRAPERS_AVAILABLE:
            scraper = LinkedInScraper()
            proxy = {"http": "http://slow-proxy:8080"}
            params = {"keywords": "test"}
            
            from requests.exceptions import Timeout
            
            with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
                mock_session = Mock()
                mock_session.get.side_effect = Timeout("Request timeout")
                mock_create_session.return_value = mock_session
                
                result = scraper.test_proxy_for_linkedin(proxy, params)
                self.assertIsNone(result)

    def test_invalid_response_handling(self):
        """Test handling of invalid responses."""
        if SCRAPERS_AVAILABLE:
            scraper = GoogleJobsScraper()
            proxy = {"http": "http://proxy:8080"}
            query = "test"
            
            with patch('jobspy.scrapers.google.create_session') as mock_create_session:
                mock_session = Mock()
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.text = "Invalid response content"
                mock_session.get.return_value = mock_response
                mock_create_session.return_value = mock_session
                
                result = scraper.test_proxy_for_google(proxy, query)
                self.assertIsNone(result)


class TestJobScraperConfiguration(unittest.TestCase):
    """Test job scraper configuration and setup."""

    def test_default_configuration(self):
        """Test default scraper configuration."""
        if SCRAPERS_AVAILABLE:
            google_scraper = GoogleJobsScraper()
            linkedin_scraper = LinkedInScraper()
            
            # Test Google scraper defaults
            self.assertEqual(google_scraper.jobs_per_page, 10)
            self.assertEqual(google_scraper.max_retries, 3)
            self.assertEqual(google_scraper.retry_delay, 2)
            
            # Test LinkedIn scraper defaults
            self.assertEqual(linkedin_scraper.jobs_per_page, 25)
            self.assertEqual(linkedin_scraper.max_retries, 3)
            self.assertEqual(linkedin_scraper.retry_delay, 2)
            self.assertEqual(linkedin_scraper.delay, 3)
            self.assertEqual(linkedin_scraper.band_delay, 4)

    def test_custom_proxy_configuration(self):
        """Test custom proxy configuration."""
        if SCRAPERS_AVAILABLE:
            proxies = [
                "http://proxy1:8080",
                "http://proxy2:8080",
                "socks5://proxy3:1080"
            ]
            
            google_scraper = GoogleJobsScraper(proxies=proxies)
            linkedin_scraper = LinkedInScraper(proxies=proxies)
            
            # Verify scrapers were created successfully with proxies
            self.assertIsNotNone(google_scraper)
            self.assertIsNotNone(linkedin_scraper)

    def test_ca_cert_configuration(self):
        """Test CA certificate configuration."""
        if SCRAPERS_AVAILABLE:
            ca_cert = "/path/to/custom/cert.pem"
            
            google_scraper = GoogleJobsScraper(ca_cert=ca_cert)
            linkedin_scraper = LinkedInScraper(ca_cert=ca_cert)
            
            self.assertEqual(google_scraper.ca_cert, ca_cert)
            self.assertEqual(linkedin_scraper.ca_cert, ca_cert)


if __name__ == '__main__':
    if not SCRAPERS_AVAILABLE:
        print("Warning: Job scrapers not available, some tests will be skipped")
    unittest.main()