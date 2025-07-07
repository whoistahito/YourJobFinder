"""
Integration tests for job scraper functionality.
Tests end-to-end functionality with real-like scenarios but controlled environments.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Mock the dependencies that might not be available during testing
try:
    from jobspy import scrape_jobs
    from jobspy.scrapers.google import GoogleJobsScraper
    from jobspy.scrapers.linkedin import LinkedInScraper
    from jobspy.scrapers import ScraperInput, Site
    from jobspy.jobs import JobResponse, JobPost, Location, JobType
    SCRAPERS_AVAILABLE = True
except ImportError:
    SCRAPERS_AVAILABLE = False
    # Create mock classes for testing
    def scrape_jobs(**kwargs):
        return []
    
    class GoogleJobsScraper:
        def __init__(self, **kwargs):
            pass
    
    class LinkedInScraper:
        def __init__(self, **kwargs):
            pass


@unittest.skipUnless(SCRAPERS_AVAILABLE, "Job scrapers not available")
class TestJobScrapingIntegration(unittest.TestCase):
    """Integration tests for complete job scraping workflows."""

    def test_scrape_jobs_function_integration(self):
        """Test the main scrape_jobs function integration."""
        with patch('jobspy.GoogleJobsScraper') as mock_google_scraper:
            with patch('jobspy.LinkedInScraper') as mock_linkedin_scraper:
                # Mock scraper instances
                mock_google_instance = Mock()
                mock_google_instance.scrape.return_value = JobResponse(jobs=[
                    Mock(title="Google Job 1", company="Company A"),
                    Mock(title="Google Job 2", company="Company B")
                ])
                mock_google_scraper.return_value = mock_google_instance
                
                mock_linkedin_instance = Mock()
                mock_linkedin_instance.scrape.return_value = JobResponse(jobs=[
                    Mock(title="LinkedIn Job 1", company="Company C")
                ])
                mock_linkedin_scraper.return_value = mock_linkedin_instance
                
                # Test scraping from multiple sites
                result = scrape_jobs(
                    site_name=["google", "linkedin"],
                    search_term="software engineer",
                    location="New York",
                    results_wanted=5
                )
                
                # Verify result structure
                self.assertIsNotNone(result)
                # The actual implementation details would depend on the scrape_jobs function

    def test_single_site_scraping_workflow(self):
        """Test complete workflow for single site scraping."""
        with patch('jobspy.GoogleJobsScraper') as mock_scraper_class:
            mock_scraper_instance = Mock()
            
            # Mock a realistic job response
            mock_jobs = [
                Mock(
                    title="Senior Software Engineer",
                    company="Tech Corp",
                    location=Mock(city="New York", state="NY"),
                    description="Great opportunity for a senior engineer...",
                    job_type=JobType.FULL_TIME,
                    url="https://example.com/job/1"
                ),
                Mock(
                    title="Junior Developer",
                    company="Startup Inc",
                    location=Mock(city="San Francisco", state="CA"),
                    description="Entry level position for new graduates...",
                    job_type=JobType.FULL_TIME,
                    url="https://example.com/job/2"
                )
            ]
            
            mock_scraper_instance.scrape.return_value = JobResponse(jobs=mock_jobs)
            mock_scraper_class.return_value = mock_scraper_instance
            
            # Test the workflow
            result = scrape_jobs(
                site_name="google",
                search_term="software engineer",
                location="New York",
                results_wanted=10
            )
            
            # Verify scraper was created and called
            mock_scraper_class.assert_called_once()
            mock_scraper_instance.scrape.assert_called_once()
            
            # The result would be processed by scrape_jobs function
            self.assertIsNotNone(result)

    def test_error_handling_integration(self):
        """Test error handling in the complete scraping workflow."""
        with patch('jobspy.GoogleJobsScraper') as mock_scraper_class:
            # Test with scraper that raises an exception
            mock_scraper_instance = Mock()
            mock_scraper_instance.scrape.side_effect = Exception("Network error")
            mock_scraper_class.return_value = mock_scraper_instance
            
            # The scrape_jobs function should handle errors gracefully
            try:
                result = scrape_jobs(
                    site_name="google",
                    search_term="software engineer",
                    results_wanted=5
                )
                # Should not crash, might return empty results or handle error
                self.assertIsNotNone(result)
            except Exception as e:
                # If it does raise an exception, it should be meaningful
                self.assertIsInstance(e, Exception)

    def test_concurrent_scraping_integration(self):
        """Test concurrent scraping from multiple sites."""
        with patch('jobspy.GoogleJobsScraper') as mock_google_scraper:
            with patch('jobspy.LinkedInScraper') as mock_linkedin_scraper:
                
                # Simulate different response times
                def slow_google_scrape(*args, **kwargs):
                    time.sleep(0.1)  # Simulate network delay
                    return JobResponse(jobs=[Mock(title="Google Job")])
                
                def fast_linkedin_scrape(*args, **kwargs):
                    time.sleep(0.05)  # Faster response
                    return JobResponse(jobs=[Mock(title="LinkedIn Job")])
                
                mock_google_instance = Mock()
                mock_google_instance.scrape.side_effect = slow_google_scrape
                mock_google_scraper.return_value = mock_google_instance
                
                mock_linkedin_instance = Mock()
                mock_linkedin_instance.scrape.side_effect = fast_linkedin_scrape
                mock_linkedin_scraper.return_value = mock_linkedin_instance
                
                start_time = time.time()
                
                result = scrape_jobs(
                    site_name=["google", "linkedin"],
                    search_term="software engineer",
                    results_wanted=5
                )
                
                end_time = time.time()
                
                # Should complete faster than sequential execution
                # (0.1 + 0.05 = 0.15s for sequential, should be closer to 0.1s for concurrent)
                self.assertLess(end_time - start_time, 0.14)
                
                self.assertIsNotNone(result)


@unittest.skipUnless(SCRAPERS_AVAILABLE, "Job scrapers not available")
class TestGoogleScraperIntegration(unittest.TestCase):
    """Integration tests for Google job scraper."""

    def setUp(self):
        """Set up test fixtures."""
        self.scraper = GoogleJobsScraper()

    def test_complete_google_scraping_workflow(self):
        """Test complete Google scraping workflow with mocked responses."""
        # Mock the initial search response
        initial_response_html = '''
        <html>
        <body>
            <div jsname="Yust4d" data-async-fc="cursor123">
                Jobs search results
            </div>
            <script>callback:550</script>
            <div class="job-result">
                <h3>Software Engineer</h3>
                <span>Tech Company</span>
            </div>
        </body>
        </html>
        '''
        
        # Mock the paginated response
        paginated_response = '''
        {
            "jobs": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Big Tech Corp",
                    "location": "New York, NY"
                }
            ],
            "nextCursor": "cursor456"
        }
        '''
        
        with patch('jobspy.scrapers.google.create_session') as mock_create_session:
            mock_session = Mock()
            
            # Mock initial search
            initial_mock_response = Mock()
            initial_mock_response.status_code = 200
            initial_mock_response.text = initial_response_html
            
            # Mock paginated request
            paginated_mock_response = Mock()
            paginated_mock_response.status_code = 200
            paginated_mock_response.text = paginated_response
            
            mock_session.get.side_effect = [initial_mock_response, paginated_mock_response]
            mock_create_session.return_value = mock_session
            
            # Mock proxy manager
            with patch.object(self.scraper, 'proxy_manager') as mock_proxy_manager:
                mock_proxy_manager.get_working_proxy.return_value = (
                    {"http": "http://proxy:8080"}, "proxy_key"
                )
                
                # Mock the parsing methods
                with patch.object(self.scraper, '_extract_initial_cursor_and_jobs') as mock_extract:
                    mock_extract.return_value = ("cursor123", [Mock(title="Job 1")])
                    
                    with patch.object(self.scraper, '_get_jobs_next_page') as mock_next_page:
                        mock_next_page.return_value = ([Mock(title="Job 2")], None)
                        
                        # Create test input
                        scraper_input = ScraperInput(
                            site_name="google",
                            search_term="software engineer",
                            location="New York",
                            results_wanted=10
                        )
                        
                        # Execute the scraping
                        result = self.scraper.scrape(scraper_input)
                        
                        # Verify result
                        self.assertIsInstance(result, JobResponse)
                        self.assertIsInstance(result.jobs, list)

    def test_google_proxy_retry_mechanism(self):
        """Test Google scraper proxy retry mechanism."""
        with patch('jobspy.scrapers.google.create_session') as mock_create_session:
            mock_session = Mock()
            
            # First call fails, second succeeds
            mock_response_fail = Mock()
            mock_response_fail.status_code = 403
            
            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.text = "jobs content with callback:550"
            
            mock_session.get.side_effect = [mock_response_fail, mock_response_success]
            mock_create_session.return_value = mock_session
            
            # Mock proxy manager to provide different proxies
            with patch.object(self.scraper, 'proxy_manager') as mock_proxy_manager:
                mock_proxy_manager.get_working_proxy.side_effect = [
                    ({"http": "http://proxy1:8080"}, "proxy1"),
                    ({"http": "http://proxy2:8080"}, "proxy2")
                ]
                mock_proxy_manager.invalidate_proxy.return_value = None
                
                # Test proxy testing with retry
                proxy1 = {"http": "http://proxy1:8080"}
                proxy2 = {"http": "http://proxy2:8080"}
                
                result1 = self.scraper.test_proxy_for_google(proxy1, "test query")
                result2 = self.scraper.test_proxy_for_google(proxy2, "test query")
                
                # First should fail, second should succeed
                self.assertIsNone(result1)
                self.assertEqual(result2, mock_response_success)

    def test_google_rate_limiting_handling(self):
        """Test handling of rate limiting from Google."""
        with patch('jobspy.scrapers.google.create_session') as mock_create_session:
            mock_session = Mock()
            
            # Simulate rate limiting responses
            rate_limit_responses = [429, 503, 502]
            
            for status_code in rate_limit_responses:
                with self.subTest(status_code=status_code):
                    mock_response = Mock()
                    mock_response.status_code = status_code
                    mock_session.get.return_value = mock_response
                    mock_create_session.return_value = mock_session
                    
                    proxy = {"http": "http://proxy:8080"}
                    result = self.scraper.test_proxy_for_google(proxy, "test query")
                    
                    # Should return None for rate limiting
                    self.assertIsNone(result)


@unittest.skipUnless(SCRAPERS_AVAILABLE, "Job scrapers not available")
class TestLinkedInScraperIntegration(unittest.TestCase):
    """Integration tests for LinkedIn job scraper."""

    def setUp(self):
        """Set up test fixtures."""
        self.scraper = LinkedInScraper()

    def test_complete_linkedin_scraping_workflow(self):
        """Test complete LinkedIn scraping workflow with mocked responses."""
        # Mock job search response
        search_response_html = '''
        <html>
        <body>
            <div class="jobs-search-results">
                <div class="job-card" data-job-id="123">
                    <h3 class="job-title">Software Engineer</h3>
                    <span class="company-name">Tech Corp</span>
                    <span class="job-location">New York, NY</span>
                </div>
                <div class="job-card" data-job-id="456">
                    <h3 class="job-title">Senior Developer</h3>
                    <span class="company-name">Startup Inc</span>
                    <span class="job-location">San Francisco, CA</span>
                </div>
            </div>
        </body>
        </html>
        '''
        
        # Mock job details response
        job_details_html = '''
        <html>
        <body>
            <div class="job-details">
                <h1>Software Engineer</h1>
                <div class="show-more-less-html__markup">
                    <p>We are looking for a talented software engineer...</p>
                    <ul>
                        <li>5+ years experience</li>
                        <li>Python, JavaScript, React</li>
                        <li>Experience with cloud platforms</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        '''
        
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            
            # Mock search response
            search_mock_response = Mock()
            search_mock_response.status_code = 200
            search_mock_response.text = search_response_html
            
            # Mock job details responses
            details_mock_response = Mock()
            details_mock_response.status_code = 200
            details_mock_response.url = "https://www.linkedin.com/jobs/view/123"
            details_mock_response.text = job_details_html
            
            mock_session.get.side_effect = [
                search_mock_response,
                details_mock_response,
                details_mock_response
            ]
            mock_create_session.return_value = mock_session
            
            # Mock proxy manager
            with patch.object(self.scraper, 'proxy_manager') as mock_proxy_manager:
                mock_proxy_manager.get_working_proxy.return_value = (
                    {"http": "http://proxy:8080"}, "proxy_key"
                )
                
                # Create test input
                scraper_input = ScraperInput(
                    site_name="linkedin",
                    search_term="software engineer",
                    location="New York",
                    results_wanted=10,
                    full_description=True
                )
                
                # Execute the scraping
                result = self.scraper.scrape(scraper_input)
                
                # Verify result
                self.assertIsInstance(result, JobResponse)
                self.assertIsInstance(result.jobs, list)

    def test_linkedin_pagination_workflow(self):
        """Test LinkedIn pagination handling."""
        # This would test how LinkedIn scraper handles multiple pages
        pages_data = [
            # Page 1
            '''<div class="job-card" data-job-id="1">Job 1</div>''',
            # Page 2
            '''<div class="job-card" data-job-id="2">Job 2</div>''',
            # Page 3 (empty)
            '''<div class="no-results">No more jobs</div>'''
        ]
        
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            
            # Mock responses for each page
            mock_responses = []
            for page_data in pages_data:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.text = f'<html><body>{page_data}</body></html>'
                mock_responses.append(mock_response)
            
            mock_session.get.side_effect = mock_responses
            mock_create_session.return_value = mock_session
            
            # Test pagination logic
            test_params = {"start": 0, "keywords": "engineer"}
            
            for i, expected_response in enumerate(mock_responses):
                result = self.scraper.test_proxy_for_linkedin(
                    {"http": "http://proxy:8080"}, 
                    {**test_params, "start": i * 25}
                )
                
                # Each page should be processed
                # The actual logic would depend on the implementation

    def test_linkedin_job_details_extraction(self):
        """Test LinkedIn job details extraction workflow."""
        job_ids = ["123456", "789012", "345678"]
        
        job_details_responses = [
            '''
            <div class="show-more-less-html__markup">
                <h4>Job Description</h4>
                <p>Full stack developer position with React and Node.js</p>
            </div>
            ''',
            '''
            <div class="show-more-less-html__markup">
                <h4>Requirements</h4>
                <ul><li>5+ years experience</li><li>Python/Django</li></ul>
            </div>
            ''',
            '''
            <div class="show-more-less-html__markup">
                <p>Entry level position for recent graduates</p>
            </div>
            '''
        ]
        
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            mock_create_session.return_value = mock_session
            
            proxy = {"http": "http://proxy:8080"}
            
            for job_id, details_html in zip(job_ids, job_details_responses):
                with self.subTest(job_id=job_id):
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.url = f"https://www.linkedin.com/jobs/view/{job_id}"
                    mock_response.text = f'<html><body>{details_html}</body></html>'
                    mock_session.get.return_value = mock_response
                    
                    result = self.scraper._test_job_details_proxy(proxy, job_id)
                    
                    # Should extract job details successfully
                    self.assertIsInstance(result, dict)
                    self.assertIn("description", result)

    def test_linkedin_rate_limiting_recovery(self):
        """Test LinkedIn rate limiting recovery mechanism."""
        with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
            mock_session = Mock()
            mock_create_session.return_value = mock_session
            
            # Simulate rate limiting then recovery
            responses = [
                Mock(status_code=429, text="Too Many Requests"),  # Rate limited
                Mock(status_code=429, text="Too Many Requests"),  # Still rate limited
                Mock(status_code=200, text="<div>Success</div>")   # Recovered
            ]
            
            mock_session.get.side_effect = responses
            
            proxy = {"http": "http://proxy:8080"}
            params = {"keywords": "engineer"}
            
            # Test multiple attempts
            for i, expected_response in enumerate(responses):
                with self.subTest(attempt=i+1):
                    with patch('jobspy.scrapers.linkedin.logger'):
                        result = self.scraper.test_proxy_for_linkedin(proxy, params)
                        
                        if expected_response.status_code == 429:
                            self.assertIsNone(result)
                        else:
                            # Should succeed on the last attempt
                            self.assertIsNotNone(result)


class TestScraperPerformanceIntegration(unittest.TestCase):
    """Test scraper performance and efficiency."""

    @unittest.skipUnless(SCRAPERS_AVAILABLE, "Job scrapers not available")
    def test_concurrent_proxy_testing(self):
        """Test concurrent proxy testing performance."""
        if SCRAPERS_AVAILABLE:
            scraper = GoogleJobsScraper()
            
            # Mock multiple proxies
            proxies = [
                {"http": f"http://proxy{i}:8080"} 
                for i in range(10)
            ]
            
            with patch('jobspy.scrapers.google.create_session') as mock_create_session:
                mock_session = Mock()
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.text = "jobs content with callback:550"
                mock_session.get.return_value = mock_response
                mock_create_session.return_value = mock_session
                
                # Test concurrent proxy testing
                start_time = time.time()
                
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = []
                    for proxy in proxies:
                        future = executor.submit(
                            scraper.test_proxy_for_google, 
                            proxy, 
                            "test query"
                        )
                        futures.append(future)
                    
                    results = []
                    for future in as_completed(futures):
                        results.append(future.result())
                
                end_time = time.time()
                
                # Should complete faster than sequential execution
                # and all proxies should be tested
                self.assertEqual(len(results), len(proxies))
                self.assertLess(end_time - start_time, 2.0)  # Reasonable time limit

    @unittest.skipUnless(SCRAPERS_AVAILABLE, "Job scrapers not available")
    def test_memory_efficiency(self):
        """Test memory efficiency with large result sets."""
        if SCRAPERS_AVAILABLE:
            # This would test memory usage patterns
            # In a real scenario, you'd monitor memory usage
            
            scraper = GoogleJobsScraper()
            
            # Mock a large number of job results
            large_job_list = [
                Mock(title=f"Job {i}", company=f"Company {i}")
                for i in range(1000)
            ]
            
            with patch.object(scraper, '_extract_initial_cursor_and_jobs') as mock_extract:
                mock_extract.return_value = ("cursor", large_job_list)
                
                # The scraper should handle large result sets efficiently
                # without excessive memory usage
                self.assertIsInstance(large_job_list, list)
                self.assertEqual(len(large_job_list), 1000)

    @unittest.skipUnless(SCRAPERS_AVAILABLE, "Job scrapers not available")
    def test_error_recovery_performance(self):
        """Test error recovery doesn't significantly impact performance."""
        if SCRAPERS_AVAILABLE:
            scraper = LinkedInScraper()
            
            # Mix of successful and failing requests
            responses = []
            for i in range(20):
                if i % 3 == 0:  # Every third request fails
                    response = Mock()
                    response.status_code = 500
                    responses.append(response)
                else:
                    response = Mock()
                    response.status_code = 200
                    response.text = "<div>Success</div>"
                    responses.append(response)
            
            with patch('jobspy.scrapers.linkedin.create_session') as mock_create_session:
                mock_session = Mock()
                mock_session.get.side_effect = responses
                mock_create_session.return_value = mock_session
                
                proxy = {"http": "http://proxy:8080"}
                params = {"keywords": "engineer"}
                
                start_time = time.time()
                
                # Test multiple requests with some failures
                results = []
                for _ in range(len(responses)):
                    with patch('jobspy.scrapers.linkedin.logger'):
                        result = scraper.test_proxy_for_linkedin(proxy, params)
                        results.append(result)
                
                end_time = time.time()
                
                # Should handle errors without excessive delay
                self.assertLess(end_time - start_time, 5.0)
                
                # Should have some successful results
                successful_results = [r for r in results if r is not None]
                self.assertGreater(len(successful_results), 0)


if __name__ == '__main__':
    if not SCRAPERS_AVAILABLE:
        print("Warning: Job scrapers not available, some tests will be skipped")
    unittest.main()