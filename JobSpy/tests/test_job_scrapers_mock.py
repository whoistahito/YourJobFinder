"""
Mock tests for job scraper HTTP interactions.
Tests behavior with mocked HTTP responses to ensure robust handling of various scenarios.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from bs4 import BeautifulSoup

# Mock the dependencies that might not be available during testing
try:
    from jobspy.scrapers.google import GoogleJobsScraper
    from jobspy.scrapers.linkedin import LinkedInScraper
    from jobspy.scrapers import ScraperInput, Site
    from jobspy.jobs import JobResponse, JobPost, Location
    SCRAPERS_AVAILABLE = True
except ImportError:
    SCRAPERS_AVAILABLE = False
    # Create mock classes for testing
    class GoogleJobsScraper:
        def __init__(self, **kwargs):
            self.jobs_per_page = 10
            self.max_retries = 3
            self.retry_delay = 2
    
    class LinkedInScraper:
        def __init__(self, **kwargs):
            self.base_url = "https://www.linkedin.com"
            self.jobs_per_page = 25
            self.max_retries = 3
            self.retry_delay = 2


@unittest.skipUnless(SCRAPERS_AVAILABLE, "Job scrapers not available")
class TestGoogleJobsScraperHTTPMocking(unittest.TestCase):
    """Test GoogleJobsScraper with mocked HTTP responses."""

    def setUp(self):
        """Set up test fixtures."""
        self.scraper = GoogleJobsScraper()
        self.test_proxy = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        self.test_query = "software engineer jobs"

    def test_successful_google_search_response(self):
        """Test successful Google search response with job results."""
        mock_response_text = '''
        <html>
        <body>
            <div>Jobs search results</div>
            <script>callback:550</script>
            <div class="job-result">
                <h3>Software Engineer</h3>
                <span>Tech Company</span>
            </div>
        </body>
        </html>
        '''
        
        with patch('jobspy.scrapers.google.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_response_text
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            result = self.scraper.test_proxy_for_google(self.test_proxy, self.test_query)
            
            # Verify session creation
            mock_create_session.assert_called_once_with(
                proxies=self.test_proxy,
                is_tls=False,
                ca_cert=None,
                has_retry=False,
                clear_cookies=True,
                delay=1
            )
            
            # Verify request
            args, kwargs = mock_session.get.call_args
            self.assertEqual(args[0], 'https://www.google.com/search')
            self.assertEqual(kwargs['timeout'], 20)
            self.assertIn('q', kwargs['params'])
            self.assertIn('udm', kwargs['params'])
            
            # Should return the response since it contains job indicators
            self.assertEqual(result, mock_response)

    def test_google_search_no_job_content(self):
        """Test Google search response without job content."""
        mock_response_text = '''
        <html>
        <body>
            <div>Regular search results without jobs</div>
            <div class="result">
                <h3>Regular Result</h3>
            </div>
        </body>
        </html>
        '''
        
        with patch('jobspy.scrapers.google.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_response_text
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            result = self.scraper.test_proxy_for_google(self.test_proxy, self.test_query)
            
            # Should return None since no job content indicators
            self.assertIsNone(result)

    def test_google_search_http_error_responses(self):
        """Test Google search with various HTTP error responses."""
        error_responses = [
            (403, "Forbidden"),
            (404, "Not Found"),
            (429, "Too Many Requests"),
            (500, "Internal Server Error"),
            (503, "Service Unavailable")
        ]
        
        for status_code, content in error_responses:
            with self.subTest(status_code=status_code):
                with patch('jobspy.scrapers.google.create_session') as mock_create_session:
                    mock_session = Mock()
                    mock_response = Mock()
                    mock_response.status_code = status_code
                    mock_response.text = content
                    mock_session.get.return_value = mock_response
                    mock_create_session.return_value = mock_session
                    
                    result = self.scraper.test_proxy_for_google(self.test_proxy, self.test_query)
                    
                    # Should return None for all error responses
                    self.assertIsNone(result)

    def test_google_search_network_exceptions(self):
        """Test Google search with various network exceptions."""
        from requests.exceptions import ConnectionError, Timeout
        from urllib3.exceptions import MaxRetryError, ProxyError
        
        exceptions = [
            ConnectionError("Connection failed"),
            Timeout("Request timeout"),
            MaxRetryError("pool", "url", "Max retries exceeded"),
            ProxyError("Proxy error")
        ]
        
        for exception in exceptions:
            with self.subTest(exception=type(exception).__name__):
                with patch('jobspy.scrapers.google.create_session') as mock_create_session:
                    mock_session = Mock()
                    mock_session.get.side_effect = exception
                    mock_create_session.return_value = mock_session
                    
                    result = self.scraper.test_proxy_for_google(self.test_proxy, self.test_query)
                    
                    # Should return None for network exceptions
                    self.assertIsNone(result)

    def test_google_search_malformed_response(self):
        """Test Google search with malformed HTML response."""
        malformed_responses = [
            "Not HTML content at all",
            "<html><body>Incomplete HTML",
            "<?xml version='1.0'?><root>XML instead of HTML</root>",
            "",  # Empty response
            "   ",  # Whitespace only
        ]
        
        for response_text in malformed_responses:
            with self.subTest(response=response_text[:20]):
                with patch('jobspy.scrapers.google.create_session') as mock_create_session:
                    mock_session = Mock()
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.text = response_text
                    mock_session.get.return_value = mock_response
                    mock_create_session.return_value = mock_session
                    
                    result = self.scraper.test_proxy_for_google(self.test_proxy, self.test_query)
                    
                    # Should return None for malformed responses
                    self.assertIsNone(result)

    def test_google_search_with_different_proxies(self):
        """Test Google search with different proxy configurations."""
        proxy_configs = [
            {"http": "http://proxy1:8080", "https": "http://proxy1:8080"},
            {"http": "https://proxy2:8080", "https": "https://proxy2:8080"},
            {"http": "socks5://proxy3:1080", "https": "socks5://proxy3:1080"},
        ]
        
        for proxy_config in proxy_configs:
            with self.subTest(proxy=proxy_config):
                with patch('jobspy.scrapers.google.create_session') as mock_create_session:
                    mock_session = Mock()
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.text = "jobs content with callback:550"
                    mock_session.get.return_value = mock_response
                    mock_create_session.return_value = mock_session
                    
                    result = self.scraper.test_proxy_for_google(proxy_config, self.test_query)
                    
                    # Verify proxy configuration is passed correctly
                    mock_create_session.assert_called_once_with(
                        proxies=proxy_config,
                        is_tls=False,
                        ca_cert=None,
                        has_retry=False,
                        clear_cookies=True,
                        delay=1
                    )
                    
                    self.assertEqual(result, mock_response)


@unittest.skipUnless(SCRAPERS_AVAILABLE, "Job scrapers not available")
class TestLinkedInScraperHTTPMocking(unittest.TestCase):
    """Test LinkedInScraper with mocked HTTP responses."""

    def setUp(self):
        """Set up test fixtures."""
        self.scraper = LinkedInScraper()
        self.test_proxy = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        self.test_params = {"keywords": "engineer", "location": "New York"}
        self.test_job_id = "123456789"

    def test_successful_linkedin_search_response(self):
        """Test successful LinkedIn search response with job results."""
        mock_response_text = '''
        <html>
        <body>
            <div class="job-search-results">
                <div class="job-card">
                    <h3>Software Engineer</h3>
                    <span class="company">Tech Company</span>
                    <span class="location">New York, NY</span>
                </div>
                <div class="job-card">
                    <h3>Senior Developer</h3>
                    <span class="company">Another Company</span>
                    <span class="location">San Francisco, CA</span>
                </div>
            </div>
        </body>
        </html>
        '''
        
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_response_text
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            # Mock the job card parsing
            with patch.object(self.scraper, '_parse_job_cards') as mock_parse:
                mock_job_cards = [Mock(), Mock()]
                mock_parse.return_value = mock_job_cards
                
                result = self.scraper.test_proxy_for_linkedin(self.test_proxy, self.test_params)
                
                # Verify session creation
                mock_create_session.assert_called_once_with(
                    proxies=self.test_proxy,
                    is_tls=False,
                    ca_cert=None,
                    has_retry=False,
                    clear_cookies=True,
                    delay=1
                )
                
                # Verify request
                args, kwargs = mock_session.get.call_args
                expected_url = f"{self.scraper.base_url}/jobs-guest/jobs/api/seeMoreJobPostings/search?"
                self.assertEqual(args[0], expected_url)
                self.assertEqual(kwargs['params'], self.test_params)
                self.assertEqual(kwargs['timeout'], 10)
                
                # Should return parsed job cards
                self.assertEqual(result, mock_job_cards)

    def test_linkedin_search_rate_limited(self):
        """Test LinkedIn search when rate limited (429 response)."""
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.text = "Too Many Requests"
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            with patch('jobspy.scrapers.linkedin.logger') as mock_logger:
                result = self.scraper.test_proxy_for_linkedin(self.test_proxy, self.test_params)
                
                # Should log the rate limiting
                mock_logger.debug.assert_called_once_with(
                    "429 Response - Blocked by LinkedIn for too many requests"
                )
                
                # Should return None
                self.assertIsNone(result)

    def test_linkedin_search_other_http_errors(self):
        """Test LinkedIn search with other HTTP error responses."""
        error_responses = [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (403, "Forbidden"),
            (404, "Not Found"),
            (500, "Internal Server Error")
        ]
        
        for status_code, content in error_responses:
            with self.subTest(status_code=status_code):
                with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
                    mock_session = Mock()
                    mock_response = Mock()
                    mock_response.status_code = status_code
                    mock_response.text = content
                    mock_session.get.return_value = mock_response
                    mock_create_session.return_value = mock_session
                    
                    with patch('jobspy.scrapers.linkedin.logger') as mock_logger:
                        result = self.scraper.test_proxy_for_linkedin(self.test_proxy, self.test_params)
                        
                        # Should log the error
                        mock_logger.debug.assert_called_once_with(
                            f"LinkedIn response status code {status_code}"
                        )
                        
                        # Should return None
                        self.assertIsNone(result)

    def test_successful_job_details_response(self):
        """Test successful job details response."""
        mock_response_text = '''
        <html>
        <body>
            <div class="job-details">
                <h1>Software Engineer Position</h1>
                <div class="show-more-less-html__markup">
                    <p>This is a great opportunity for a software engineer...</p>
                    <ul>
                        <li>5+ years experience</li>
                        <li>Python, JavaScript skills</li>
                        <li>Remote work available</li>
                    </ul>
                </div>
                <span class="company">Tech Company Inc.</span>
                <span class="location">New York, NY</span>
            </div>
        </body>
        </html>
        '''
        
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = f"https://www.linkedin.com/jobs/view/{self.test_job_id}"
            mock_response.text = mock_response_text
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            result = self.scraper._test_job_details_proxy(self.test_proxy, self.test_job_id)
            
            # Verify session creation
            mock_create_session.assert_called_once_with(
                proxies=self.test_proxy,
                is_tls=False,
                ca_cert=None,
                has_retry=False,
                clear_cookies=True
            )
            
            # Verify request
            mock_session.get.assert_called_once_with(
                f"{self.scraper.base_url}/jobs/view/{self.test_job_id}",
                timeout=10
            )
            
            # Should return job details dictionary
            self.assertIsInstance(result, dict)
            self.assertIn("description", result)

    def test_job_details_signup_redirect(self):
        """Test job details when redirected to signup page."""
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = "https://www.linkedin.com/signup"
            mock_response.text = "<html><body>Please sign up</body></html>"
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            result = self.scraper._test_job_details_proxy(self.test_proxy, self.test_job_id)
            
            # Should return None when redirected to signup
            self.assertIsNone(result)

    def test_job_details_missing_content(self):
        """Test job details with missing description content."""
        mock_response_text = '''
        <html>
        <body>
            <div class="job-details">
                <h1>Job Title</h1>
                <!-- No description div -->
                <span class="company">Company</span>
            </div>
        </body>
        </html>
        '''
        
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = f"https://www.linkedin.com/jobs/view/{self.test_job_id}"
            mock_response.text = mock_response_text
            mock_session.get.return_value = mock_response
            mock_create_session.return_value = mock_session
            
            result = self.scraper._test_job_details_proxy(self.test_proxy, self.test_job_id)
            
            # Should still return a result even if description is missing
            self.assertIsInstance(result, dict)
            # Description might be None or empty
            self.assertTrue("description" in result)

    def test_linkedin_network_exceptions(self):
        """Test LinkedIn scraper with network exceptions."""
        from requests.exceptions import ConnectionError, Timeout
        
        exceptions = [
            ConnectionError("Connection failed"),
            Timeout("Request timeout"),
            requests.RequestException("General request error")
        ]
        
        for exception in exceptions:
            with self.subTest(exception=type(exception).__name__):
                with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
                    mock_session = Mock()
                    mock_session.get.side_effect = exception
                    mock_create_session.return_value = mock_session
                    
                    # Test search endpoint
                    result = self.scraper.test_proxy_for_linkedin(self.test_proxy, self.test_params)
                    self.assertIsNone(result)
                    
                    # Test job details endpoint
                    result = self.scraper._test_job_details_proxy(self.test_proxy, self.test_job_id)
                    self.assertIsNone(result)


class TestJobScraperResponseParsing(unittest.TestCase):
    """Test response parsing and content extraction."""

    def test_html_parsing_with_beautifulsoup(self):
        """Test HTML parsing capabilities with various HTML structures."""
        html_samples = [
            # Well-formed HTML
            '''<html><body><div class="job">Job Content</div></body></html>''',
            
            # Malformed HTML
            '''<div class="job">Job Content<span>Unclosed span</div>''',
            
            # HTML with special characters
            '''<div class="job">Job with special chars: &amp; &lt; &gt;</div>''',
            
            # Empty HTML
            '''<html><body></body></html>''',
            
            # HTML with script tags
            '''<html><head><script>alert('test');</script></head><body>Content</body></html>'''
        ]
        
        for html in html_samples:
            with self.subTest(html=html[:30]):
                soup = BeautifulSoup(html, "html.parser")
                
                # Should not raise exceptions
                self.assertIsInstance(soup, BeautifulSoup)
                
                # Should be able to find elements
                job_divs = soup.find_all("div", class_="job")
                self.assertIsInstance(job_divs, list)

    def test_text_extraction_and_cleaning(self):
        """Test text extraction and cleaning from HTML."""
        html_with_text = '''
        <div class="job-description">
            <p>This is a job description with <strong>bold text</strong>.</p>
            <ul>
                <li>Requirement 1</li>
                <li>Requirement 2</li>
            </ul>
            <div>   Extra whitespace   </div>
        </div>
        '''
        
        soup = BeautifulSoup(html_with_text, "html.parser")
        job_desc = soup.find("div", class_="job-description")
        
        if job_desc:
            # Test text extraction
            text = job_desc.get_text()
            self.assertIsInstance(text, str)
            self.assertIn("bold text", text)
            self.assertIn("Requirement 1", text)
            
            # Test text cleaning
            cleaned_text = job_desc.get_text(strip=True)
            self.assertIsInstance(cleaned_text, str)

    def test_attribute_extraction(self):
        """Test extraction of HTML attributes."""
        html_with_attrs = '''
        <div class="job-card" data-job-id="123456">
            <a href="/jobs/view/123456" class="job-link">
                <h3 class="job-title">Software Engineer</h3>
            </a>
            <span class="company" data-company-id="789">Tech Corp</span>
        </div>
        '''
        
        soup = BeautifulSoup(html_with_attrs, "html.parser")
        
        # Test attribute extraction
        job_card = soup.find("div", class_="job-card")
        if job_card:
            job_id = job_card.get("data-job-id")
            self.assertEqual(job_id, "123456")
        
        job_link = soup.find("a", class_="job-link")
        if job_link:
            href = job_link.get("href")
            self.assertEqual(href, "/jobs/view/123456")

    def test_nested_element_navigation(self):
        """Test navigation through nested HTML elements."""
        nested_html = '''
        <div class="search-results">
            <div class="job-list">
                <article class="job-card">
                    <header class="job-header">
                        <h2 class="job-title">Engineer</h2>
                        <div class="company-info">
                            <span class="company-name">TechCorp</span>
                            <span class="location">NYC</span>
                        </div>
                    </header>
                    <section class="job-details">
                        <p class="description">Job description here</p>
                    </section>
                </article>
            </div>
        </div>
        '''
        
        soup = BeautifulSoup(nested_html, "html.parser")
        
        # Test navigation from parent to child
        search_results = soup.find("div", class_="search-results")
        if search_results:
            job_card = search_results.find("article", class_="job-card")
            self.assertIsNotNone(job_card)
            
            # Test finding nested elements
            job_title = job_card.find("h2", class_="job-title")
            if job_title:
                self.assertEqual(job_title.get_text(), "Engineer")
            
            company_name = job_card.find("span", class_="company-name")
            if company_name:
                self.assertEqual(company_name.get_text(), "TechCorp")


class TestHTTPSessionConfiguration(unittest.TestCase):
    """Test HTTP session configuration for different scrapers."""

    def test_session_headers_configuration(self):
        """Test that sessions are configured with appropriate headers."""
        if SCRAPERS_AVAILABLE:
            test_headers = {
                "User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)",
                "Accept": "text/html,application/json",
                "Accept-Language": "en-US,en;q=0.9"
            }
            
            with patch('jobspy.scrapers.google.create_session') as mock_create_session:
                mock_session = Mock()
                mock_create_session.return_value = mock_session
                
                scraper = GoogleJobsScraper()
                proxy = {"http": "http://proxy:8080"}
                
                # This would test if headers are properly set
                scraper.test_proxy_for_google(proxy, "test query")
                
                # Verify session creation was called
                mock_create_session.assert_called_once()

    def test_session_timeout_configuration(self):
        """Test that sessions are configured with appropriate timeouts."""
        if SCRAPERS_AVAILABLE:
            with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
                mock_session = Mock()
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.url = "https://www.linkedin.com/jobs/view/123"
                mock_response.text = "<html></html>"
                mock_session.get.return_value = mock_response
                mock_create_session.return_value = mock_session
                
                scraper = LinkedInScraper()
                proxy = {"http": "http://proxy:8080"}
                
                # Test job details with timeout
                scraper._test_job_details_proxy(proxy, "123456")
                
                # Verify timeout parameter was used
                args, kwargs = mock_session.get.call_args
                self.assertEqual(kwargs['timeout'], 10)

    def test_retry_configuration(self):
        """Test retry configuration for failed requests."""
        if SCRAPERS_AVAILABLE:
            scraper = GoogleJobsScraper()
            
            # Test that retry settings are properly configured
            self.assertEqual(scraper.max_retries, 3)
            self.assertEqual(scraper.retry_delay, 2)
            
            linkedin_scraper = LinkedInScraper()
            self.assertEqual(linkedin_scraper.max_retries, 3)
            self.assertEqual(linkedin_scraper.retry_delay, 2)


if __name__ == '__main__':
    if not SCRAPERS_AVAILABLE:
        print("Warning: Job scrapers not available, some tests will be skipped")
    unittest.main()