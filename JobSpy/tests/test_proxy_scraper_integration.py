"""
Integration tests for proxy scraper functionality.
Tests end-to-end functionality with real-like scenarios but controlled environments.
"""
import unittest
from unittest.mock import patch, Mock
import asyncio
import httpx
from jobspy.scrapers.proxy_scraper import (
    get_socks_proxies,
    get_https_proxies,
    test_scraper,
    scrape,
    Scraper,
    GitHubScraper,
    ProxyLibScraper
)


class TestProxyScraperIntegration(unittest.TestCase):
    """Integration tests for proxy scraper functionality."""

    def test_get_socks_proxies_integration(self):
        """Test get_socks_proxies function integration."""
        with patch('jobspy.scrapers.proxy_scraper.scrape') as mock_scrape:
            # Mock a realistic response
            mock_proxies = {
                "socks5://192.168.1.1:1080",
                "socks4://10.0.0.1:1080",
                "socks5://172.16.0.1:1080"
            }
            mock_scrape.return_value = mock_proxies
            
            result = get_socks_proxies()
            
            # Verify correct methods are requested
            mock_scrape.assert_called_once_with(["socks5", "socks4"])
            
            # Verify result is a list
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 3)
            
            # Verify all proxies are included
            result_set = set(result)
            self.assertEqual(result_set, mock_proxies)

    def test_get_https_proxies_integration(self):
        """Test get_https_proxies function integration."""
        with patch('jobspy.scrapers.proxy_scraper.test_scraper') as mock_test_scraper:
            # Mock a realistic response
            mock_proxies = [
                "https://192.168.1.1:8080",
                "https://10.0.0.1:3128",
                "https://172.16.0.1:8080"
            ]
            mock_test_scraper.return_value = mock_proxies
            
            result = get_https_proxies()
            
            # Verify test_scraper is called
            mock_test_scraper.assert_called_once()
            
            # Verify result matches expected
            self.assertEqual(result, mock_proxies)

    async def test_test_scraper_integration(self):
        """Test test_scraper function integration."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.__aenter__ = Mock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = Mock(return_value=None)
            mock_client_class.return_value = mock_client_instance
            
            # Mock ProxyLibScraper
            with patch('jobspy.scrapers.proxy_scraper.ProxyLibScraper') as mock_scraper_class:
                mock_scraper_instance = Mock()
                mock_scraper_instance.scrape = Mock(return_value=["https://1.1.1.1:8080"])
                mock_scraper_class.return_value = mock_scraper_instance
                
                result = await test_scraper()
                
                # Verify ProxyLibScraper is created with correct method
                mock_scraper_class.assert_called_once_with("https")
                
                # Verify scrape is called with client
                mock_scraper_instance.scrape.assert_called_once_with(mock_client_instance)
                
                # Verify result
                self.assertEqual(result, ["https://1.1.1.1:8080"])

    def test_test_scraper_sync_wrapper(self):
        """Test test_scraper synchronous wrapper integration."""
        with patch('jobspy.scrapers.proxy_scraper.test_scraper') as mock_async_test_scraper:
            mock_proxies = ["https://1.1.1.1:8080", "https://2.2.2.2:8080"]
            mock_async_test_scraper.return_value = mock_proxies
            
            result = get_https_proxies()
            
            mock_async_test_scraper.assert_called_once()
            self.assertEqual(result, mock_proxies)


class TestScraperWorkflowIntegration(unittest.TestCase):
    """Test complete scraper workflow integration."""

    async def test_complete_scraper_workflow(self):
        """Test complete workflow from scraper creation to result processing."""
        # Create a real scraper instance
        scraper = Scraper("http", "https://httpbin.org/get")
        
        # Mock the client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "192.168.1.1:8080\n10.0.0.1:3128\ninvalid-data\n172.16.0.1:8080"
        mock_client.get = Mock(return_value=mock_response)
        
        # Test the complete workflow
        result = await scraper.scrape(mock_client)
        
        # Verify URL was called correctly
        mock_client.get.assert_called_once_with("https://httpbin.org/get")
        
        # Verify result processing
        expected = ["http://192.168.1.1:8080", "http://10.0.0.1:3128", "http://172.16.0.1:8080"]
        self.assertEqual(result, expected)

    async def test_github_scraper_workflow(self):
        """Test GitHub scraper complete workflow."""
        scraper = GitHubScraper("https", "https://raw.githubusercontent.com/example/https.txt")
        
        # Mock client and response with GitHub-like data
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = """# Proxy List
https://192.168.1.1:8080
http://10.0.0.1:8080
https://172.16.0.1:8080
socks5://127.0.0.1:1080
https://203.0.113.1:8080"""
        mock_client.get = Mock(return_value=mock_response)
        
        result = await scraper.scrape(mock_client)
        
        # Should only include HTTPS proxies and strip protocol in handle method
        expected_ips = {"192.168.1.1:8080", "172.16.0.1:8080", "203.0.113.1:8080"}
        result_ips = {proxy.replace("https://", "") for proxy in result}
        self.assertEqual(result_ips, expected_ips)

    async def test_proxylib_scraper_workflow(self):
        """Test ProxyLib scraper complete workflow."""
        scraper = ProxyLibScraper("https", limit="100", anonymity="Elite")
        
        # Verify URL generation
        url = scraper.get_url()
        self.assertIn("limit=100", url)
        self.assertIn("anonymity=Elite", url)
        self.assertIn("type=https", url)
        
        # Mock client and response with ProxyLib-like JSON data
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '''<!DOCTYPE html>
<html>
<head>
    <script type="application/ld+json">
    {
        "@type": "ItemList",
        "name": "Proxy Server List",
        "itemListElement": [
            {"item": {"name": "192.168.1.1:8080"}},
            {"item": {"name": "10.0.0.1:3128"}},
            {"item": {"name": "invalid-proxy"}},
            {"item": {"name": "172.16.0.1:8080"}}
        ]
    }
    </script>
</head>
</html>'''
        mock_client.get = Mock(return_value=mock_response)
        
        result = await scraper.scrape(mock_client)
        
        # Should extract valid proxies and add protocol
        expected_ips = {"192.168.1.1:8080", "10.0.0.1:3128", "172.16.0.1:8080"}
        result_ips = {proxy.replace("https://", "") for proxy in result}
        self.assertEqual(result_ips, expected_ips)


class TestConcurrentScrapingIntegration(unittest.TestCase):
    """Test concurrent scraping scenarios."""

    @patch('jobspy.scrapers.proxy_scraper.scrapers')
    async def test_concurrent_scraping_success(self, mock_scrapers):
        """Test concurrent scraping with multiple successful scrapers."""
        # Create mock scrapers with async methods
        async def mock_scrape_1(client):
            await asyncio.sleep(0.01)  # Simulate network delay
            return ["http://1.1.1.1:8080", "http://2.2.2.2:8080"]
        
        async def mock_scrape_2(client):
            await asyncio.sleep(0.02)  # Simulate different network delay
            return ["http://3.3.3.3:8080"]
        
        async def mock_scrape_3(client):
            await asyncio.sleep(0.005)  # Faster response
            return ["http://4.4.4.4:8080", "http://5.5.5.5:8080"]
        
        mock_scraper1 = Mock()
        mock_scraper1.method = "http"
        mock_scraper1.scrape = mock_scrape_1
        
        mock_scraper2 = Mock()
        mock_scraper2.method = "http"
        mock_scraper2.scrape = mock_scrape_2
        
        mock_scraper3 = Mock()
        mock_scraper3.method = "http"
        mock_scraper3.scrape = mock_scrape_3
        
        mock_scrapers.__iter__.return_value = [mock_scraper1, mock_scraper2, mock_scraper3]
        
        start_time = asyncio.get_event_loop().time()
        result = await scrape(["http"])
        end_time = asyncio.get_event_loop().time()
        
        # Should complete in roughly the time of the slowest scraper (0.02s)
        # but not the sum of all times (0.035s)
        self.assertLess(end_time - start_time, 0.05)
        
        # Should include all results
        expected = {"http://1.1.1.1:8080", "http://2.2.2.2:8080", 
                   "http://3.3.3.3:8080", "http://4.4.4.4:8080", "http://5.5.5.5:8080"}
        self.assertEqual(result, expected)

    @patch('jobspy.scrapers.proxy_scraper.scrapers')
    async def test_concurrent_scraping_with_failures(self, mock_scrapers):
        """Test concurrent scraping when some scrapers fail."""
        async def mock_scrape_success(client):
            await asyncio.sleep(0.01)
            return ["http://1.1.1.1:8080"]
        
        async def mock_scrape_failure(client):
            await asyncio.sleep(0.02)
            raise httpx.ConnectError("Connection failed")
        
        async def mock_scrape_timeout(client):
            await asyncio.sleep(0.005)
            raise httpx.TimeoutException("Request timeout")
        
        mock_scraper1 = Mock()
        mock_scraper1.method = "http"
        mock_scraper1.scrape = mock_scrape_success
        
        mock_scraper2 = Mock()
        mock_scraper2.method = "http"
        mock_scraper2.scrape = mock_scrape_failure
        
        mock_scraper3 = Mock()
        mock_scraper3.method = "http"
        mock_scraper3.scrape = mock_scrape_timeout
        
        mock_scrapers.__iter__.return_value = [mock_scraper1, mock_scraper2, mock_scraper3]
        
        # Should not raise exceptions, just return successful results
        result = await scrape(["http"])
        
        # Should only include results from successful scraper
        self.assertEqual(result, {"http://1.1.1.1:8080"})


class TestDataValidationIntegration(unittest.TestCase):
    """Test data validation and cleaning integration."""

    async def test_ip_validation_integration(self):
        """Test IP address validation throughout the scraping process."""
        scraper = Scraper("http", "https://example.com")
        
        mock_client = Mock()
        mock_response = Mock()
        # Mix of valid and invalid IP addresses
        mock_response.text = """192.168.1.1:8080
10.0.0.1:3128
999.999.999.999:8080
127.0.0.1:65536
172.16.0.1:8080
0.0.0.0:0
255.255.255.255:65535
192.168.1.1:abc
not-an-ip:8080"""
        mock_client.get = Mock(return_value=mock_response)
        
        result = await scraper.scrape(mock_client)
        
        # Should only include valid IP:port combinations
        expected = [
            "http://192.168.1.1:8080",
            "http://10.0.0.1:3128", 
            "http://172.16.0.1:8080",
            "http://255.255.255.255:65535"
        ]
        self.assertEqual(sorted(result), sorted(expected))

    async def test_protocol_handling_integration(self):
        """Test protocol handling across different scraper types."""
        test_cases = [
            ("http", "192.168.1.1:8080", "http://192.168.1.1:8080"),
            ("https", "10.0.0.1:3128", "https://10.0.0.1:3128"),
            ("socks", "172.16.0.1:1080", ["socks5://172.16.0.1:1080", "socks://172.16.0.1:1080"]),
            ("socks5", "127.0.0.1:1080", "socks5://127.0.0.1:1080")
        ]
        
        for method, proxy_data, expected in test_cases:
            with self.subTest(method=method):
                scraper = Scraper(method, "https://example.com")
                
                mock_client = Mock()
                mock_response = Mock()
                mock_response.text = proxy_data
                mock_client.get = Mock(return_value=mock_response)
                
                result = await scraper.scrape(mock_client)
                
                if isinstance(expected, list):
                    self.assertEqual(sorted(result), sorted(expected))
                else:
                    self.assertEqual(result, [expected])

    async def test_deduplication_integration(self):
        """Test proxy deduplication across multiple sources."""
        # Test the scrape function's deduplication
        with patch('jobspy.scrapers.proxy_scraper.scrapers') as mock_scrapers:
            async def mock_scrape_1(client):
                return ["http://1.1.1.1:8080", "http://2.2.2.2:8080", "http://1.1.1.1:8080"]
            
            async def mock_scrape_2(client):
                return ["http://2.2.2.2:8080", "http://3.3.3.3:8080"]
            
            mock_scraper1 = Mock()
            mock_scraper1.method = "http"
            mock_scraper1.scrape = mock_scrape_1
            
            mock_scraper2 = Mock()
            mock_scraper2.method = "http"
            mock_scraper2.scrape = mock_scrape_2
            
            mock_scrapers.__iter__.return_value = [mock_scraper1, mock_scraper2]
            
            result = await scrape(["http"])
            
            # Should deduplicate across all sources
            expected = {"http://1.1.1.1:8080", "http://2.2.2.2:8080", "http://3.3.3.3:8080"}
            self.assertEqual(result, expected)


class TestErrorRecoveryIntegration(unittest.TestCase):
    """Test error recovery and resilience integration."""

    def test_function_level_error_recovery(self):
        """Test error recovery at the function level."""
        # Test get_socks_proxies with scrape function failure
        with patch('jobspy.scrapers.proxy_scraper.scrape', side_effect=Exception("Network error")):
            with self.assertRaises(Exception):
                get_socks_proxies()
        
        # Test get_https_proxies with test_scraper failure
        with patch('jobspy.scrapers.proxy_scraper.test_scraper', side_effect=Exception("Network error")):
            with self.assertRaises(Exception):
                get_https_proxies()

    @patch('jobspy.scrapers.proxy_scraper.scrapers')
    async def test_partial_failure_recovery(self, mock_scrapers):
        """Test recovery when some scrapers succeed and others fail."""
        async def successful_scraper(client):
            return ["http://success.com:8080"]
        
        async def failing_scraper(client):
            raise Exception("This scraper always fails")
        
        # Mix of successful and failing scrapers
        scrapers_config = [
            ("http", successful_scraper),
            ("http", failing_scraper),
            ("http", successful_scraper),
            ("http", failing_scraper),
            ("http", successful_scraper)
        ]
        
        mock_scrapers_list = []
        for method, scrape_func in scrapers_config:
            mock_scraper = Mock()
            mock_scraper.method = method
            mock_scraper.scrape = scrape_func
            mock_scrapers_list.append(mock_scraper)
        
        mock_scrapers.__iter__.return_value = mock_scrapers_list
        
        result = await scrape(["http"])
        
        # Should get results from successful scrapers only
        self.assertEqual(result, {"http://success.com:8080"})

    async def test_complete_failure_recovery(self):
        """Test behavior when all scrapers fail."""
        with patch('jobspy.scrapers.proxy_scraper.scrapers') as mock_scrapers:
            async def always_fail(client):
                raise Exception("Always fails")
            
            mock_scraper1 = Mock()
            mock_scraper1.method = "http"
            mock_scraper1.scrape = always_fail
            
            mock_scraper2 = Mock()
            mock_scraper2.method = "http"
            mock_scraper2.scrape = always_fail
            
            mock_scrapers.__iter__.return_value = [mock_scraper1, mock_scraper2]
            
            result = await scrape(["http"])
            
            # Should return empty set, not raise exception
            self.assertEqual(result, set())


if __name__ == '__main__':
    unittest.main()