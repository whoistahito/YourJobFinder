"""
Mock tests for proxy scraper HTTP interactions.
Tests behavior with mocked HTTP responses to ensure robust handling of various scenarios.
"""
import unittest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
import httpx
from jobspy.scrapers.proxy_scraper import (
    Scraper,
    GitHubScraper,
    GitHubScraperNoSlash,
    GeneralTableScraper,
    GeneralTableScraper2,
    GeneralDivScraper,
    ProxyLibScraper,
    SpysMeScraper,
    ProxyScrapeScraper,
    scrape
)


class TestScraperHTTPMocking(unittest.TestCase):
    """Test HTTP interactions with mocked responses."""

    def setUp(self):
        self.scraper = Scraper("http", "https://example.com/proxy-list")

    def test_successful_http_request(self):
        """Test successful HTTP request and response handling."""
        async def run_test():
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.text = "192.168.1.1:8080\n10.0.0.1:3128"
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            
            result = await self.scraper.scrape(mock_client)
            
            mock_client.get.assert_called_once_with("https://example.com/proxy-list")
            expected = ["http://192.168.1.1:8080", "http://10.0.0.1:3128"]
            self.assertEqual(result, expected)
        
        asyncio.run(run_test())

    def test_http_request_with_connection_error(self):
        """Test handling of connection errors."""
        async def run_test():
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("Connection failed")
            
            with self.assertRaises(httpx.ConnectError):
                await self.scraper.get_response(mock_client)
        
        asyncio.run(run_test())

    def test_http_request_with_timeout(self):
        """Test handling of timeout errors."""
        async def run_test():
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Request timeout")
            
            with self.assertRaises(httpx.TimeoutException):
                await self.scraper.get_response(mock_client)
        
        asyncio.run(run_test())

    def test_http_request_with_404_response(self):
        """Test handling of 404 responses."""
        async def run_test():
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.text = "Not Found"
            mock_response.status_code = 404
            mock_client.get.return_value = mock_response
            
            # The scraper should still process the response text
            result = await self.scraper.scrape(mock_client)
            
            # No valid IPs in "Not Found" text
            self.assertEqual(result, [])
        
        asyncio.run(run_test())

    def test_http_request_with_empty_response(self):
        """Test handling of empty responses."""
        async def run_test():
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.text = ""
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            
            result = await self.scraper.scrape(mock_client)
            
            self.assertEqual(result, [])
        
        asyncio.run(run_test())


class TestGitHubScraperHTTPMocking(unittest.TestCase):
    """Test GitHubScraper with mocked HTTP responses."""

    def setUp(self):
        self.scraper = GitHubScraper("http", "https://raw.githubusercontent.com/example/proxies.txt")

    async def test_github_response_with_mixed_protocols(self):
        """Test GitHub response containing mixed protocol proxies."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = """http://192.168.1.1:8080
https://10.0.0.1:8080
socks5://127.0.0.1:1080
http://172.16.0.1:3128
ftp://192.168.2.1:21"""
        mock_client.get.return_value = mock_response
        
        result = await self.scraper.scrape(mock_client)
        
        # Should only process HTTP proxies and format them correctly
        expected_ips = {"192.168.1.1:8080", "172.16.0.1:3128"}
        result_ips = {proxy.replace("http://", "") for proxy in result}
        self.assertEqual(result_ips, expected_ips)

    async def test_github_response_with_malformed_data(self):
        """Test GitHub response with malformed proxy data."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = """invalid-proxy-data
http://not-an-ip:8080
http://192.168.1.1:invalid-port
http://192.168.1.1:8080
some random text"""
        mock_client.get.return_value = mock_response
        
        result = await self.scraper.scrape(mock_client)
        
        # Should only extract valid IP:port combinations
        self.assertEqual(result, ["http://192.168.1.1:8080"])

    async def test_github_response_with_no_matching_proxies(self):
        """Test GitHub response with no matching protocol proxies."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = """socks5://192.168.1.1:1080
socks4://10.0.0.1:1080
https://172.16.0.1:8080"""
        mock_client.get.return_value = mock_response
        
        result = await self.scraper.scrape(mock_client)
        
        # No HTTP proxies in the list
        self.assertEqual(result, [])


class TestProxyLibScraperHTTPMocking(unittest.TestCase):
    """Test ProxyLibScraper with mocked HTTP responses."""

    def setUp(self):
        self.scraper = ProxyLibScraper("https")

    async def test_proxylib_valid_json_response(self):
        """Test ProxyLib response with valid JSON-LD data."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = '''<!DOCTYPE html>
<html>
<head>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Proxy Server List",
        "numberOfItems": 2,
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "item": {
                    "@type": "Product",
                    "name": "192.168.1.1:8080"
                }
            },
            {
                "@type": "ListItem",
                "position": 2,
                "item": {
                    "@type": "Product",
                    "name": "10.0.0.1:3128"
                }
            }
        ]
    }
    </script>
</head>
<body></body>
</html>'''
        mock_client.get.return_value = mock_response
        
        result = await self.scraper.scrape(mock_client)
        
        # Should extract both proxies and format them
        expected_ips = {"192.168.1.1:8080", "10.0.0.1:3128"}
        result_ips = {proxy.replace("https://", "") for proxy in result}
        self.assertEqual(result_ips, expected_ips)

    async def test_proxylib_invalid_json_response(self):
        """Test ProxyLib response with invalid JSON data."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = '''<!DOCTYPE html>
<html>
<head>
    <script type="application/ld+json">
    {
        "@type": "ItemList",
        "name": "Proxy Server List",
        invalid json syntax here...
    }
    </script>
</head>
<body></body>
</html>'''
        mock_client.get.return_value = mock_response
        
        result = await self.scraper.scrape(mock_client)
        
        # Should handle invalid JSON gracefully
        self.assertEqual(result, [])

    async def test_proxylib_no_json_script(self):
        """Test ProxyLib response without JSON-LD script."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = '''<!DOCTYPE html>
<html>
<head>
    <title>Proxy List</title>
</head>
<body>
    <div>Some proxy content but no JSON-LD</div>
</body>
</html>'''
        mock_client.get.return_value = mock_response
        
        result = await self.scraper.scrape(mock_client)
        
        self.assertEqual(result, [])

    async def test_proxylib_multiple_json_scripts(self):
        """Test ProxyLib response with multiple JSON-LD scripts."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = '''<!DOCTYPE html>
<html>
<head>
    <script type="application/ld+json">
    {
        "@type": "Organization",
        "name": "Example Org"
    }
    </script>
    <script type="application/ld+json">
    {
        "@type": "ItemList",
        "name": "Proxy Server List",
        "itemListElement": [
            {"item": {"name": "192.168.1.1:8080"}}
        ]
    }
    </script>
</head>
<body></body>
</html>'''
        mock_client.get.return_value = mock_response
        
        result = await self.scraper.scrape(mock_client)
        
        # Should find the correct JSON-LD script
        self.assertEqual(result, ["https://192.168.1.1:8080"])


class TestGeneralTableScraperHTTPMocking(unittest.TestCase):
    """Test GeneralTableScraper with mocked HTTP responses."""

    def setUp(self):
        self.scraper = GeneralTableScraper("http", "https://example.com/proxy-table")

    async def test_table_scraper_valid_table(self):
        """Test table scraper with valid HTML table."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = '''<!DOCTYPE html>
<html>
<body>
    <table class="table table-striped table-bordered">
        <tr>
            <td>192.168.1.1</td>
            <td>8080</td>
            <td>Elite</td>
        </tr>
        <tr>
            <td>10.0.0.1</td>
            <td>3128</td>
            <td>Anonymous</td>
        </tr>
    </table>
</body>
</html>'''
        mock_client.get.return_value = mock_response
        
        result = await self.scraper.scrape(mock_client)
        
        # Should extract IP:port from first two columns
        expected_ips = {"192.168.1.1:8080", "10.0.0.1:3128"}
        result_ips = {proxy.replace("http://", "") for proxy in result}
        self.assertEqual(result_ips, expected_ips)

    async def test_table_scraper_no_table(self):
        """Test table scraper when no table is found."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = '''<!DOCTYPE html>
<html>
<body>
    <div>No table here</div>
</body>
</html>'''
        mock_client.get.return_value = mock_response
        
        # Should raise AttributeError when trying to find table
        with self.assertRaises(AttributeError):
            await self.scraper.scrape(mock_client)


class TestGeneralDivScraperHTTPMocking(unittest.TestCase):
    """Test GeneralDivScraper with mocked HTTP responses."""

    def setUp(self):
        self.scraper = GeneralDivScraper("http", "https://example.com/proxy-divs")

    async def test_div_scraper_valid_structure(self):
        """Test div scraper with valid div structure."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.text = '''<!DOCTYPE html>
<html>
<body>
    <div class="list">
        <div>
            <div class="td">192.168.1.1</div>
            <div class="td">8080</div>
            <div class="td">Other</div>
        </div>
        <div>
            <div class="td">10.0.0.1</div>
            <div class="td">3128</div>
            <div class="td">Data</div>
        </div>
    </div>
</body>
</html>'''
        mock_client.get.return_value = mock_response
        
        result = await self.scraper.scrape(mock_client)
        
        # Should extract IP:port from first two div.td elements
        expected_ips = {"192.168.1.1:8080", "10.0.0.1:3128"}
        result_ips = {proxy.replace("http://", "") for proxy in result}
        self.assertEqual(result_ips, expected_ips)


class TestScrapeFunctionHTTPMocking(unittest.TestCase):
    """Test the main scrape function with mocked scrapers and HTTP responses."""

    @patch('jobspy.scrapers.proxy_scraper.scrapers')
    async def test_scrape_function_with_successful_scrapers(self, mock_scrapers):
        """Test scrape function with multiple successful scrapers."""
        # Create mock scrapers
        mock_scraper1 = Mock()
        mock_scraper1.method = "http"
        mock_scraper1.scrape = AsyncMock(return_value=["http://1.1.1.1:8080", "http://2.2.2.2:8080"])
        
        mock_scraper2 = Mock()
        mock_scraper2.method = "http"
        mock_scraper2.scrape = AsyncMock(return_value=["http://3.3.3.3:8080"])
        
        mock_scraper3 = Mock()
        mock_scraper3.method = "https"  # Different method, should be excluded
        mock_scraper3.scrape = AsyncMock(return_value=["https://4.4.4.4:8080"])
        
        mock_scrapers.__iter__.return_value = [mock_scraper1, mock_scraper2, mock_scraper3]
        
        result = await scrape(["http"])
        
        # Should only include results from HTTP scrapers
        self.assertIsInstance(result, set)
        # Results are combined into a set, so duplicates are removed
        expected_results = {"http://1.1.1.1:8080", "http://2.2.2.2:8080", "http://3.3.3.3:8080"}
        self.assertEqual(result, expected_results)

    @patch('jobspy.scrapers.proxy_scraper.scrapers')
    async def test_scrape_function_with_failing_scrapers(self, mock_scrapers):
        """Test scrape function when some scrapers fail."""
        # Create mock scrapers
        mock_scraper1 = Mock()
        mock_scraper1.method = "http"
        mock_scraper1.scrape = AsyncMock(return_value=["http://1.1.1.1:8080"])
        
        mock_scraper2 = Mock()
        mock_scraper2.method = "http"
        mock_scraper2.scrape = AsyncMock(side_effect=Exception("Network error"))
        
        mock_scraper3 = Mock()
        mock_scraper3.method = "http"
        mock_scraper3.scrape = AsyncMock(return_value=["http://3.3.3.3:8080"])
        
        mock_scrapers.__iter__.return_value = [mock_scraper1, mock_scraper2, mock_scraper3]
        
        result = await scrape(["http"])
        
        # Should include results from successful scrapers only
        self.assertIsInstance(result, set)
        expected_results = {"http://1.1.1.1:8080", "http://3.3.3.3:8080"}
        self.assertEqual(result, expected_results)

    @patch('jobspy.scrapers.proxy_scraper.scrapers')
    async def test_scrape_function_all_scrapers_fail(self, mock_scrapers):
        """Test scrape function when all scrapers fail."""
        # Create mock scrapers that all fail
        mock_scraper1 = Mock()
        mock_scraper1.method = "http"
        mock_scraper1.scrape = AsyncMock(side_effect=Exception("Network error"))
        
        mock_scraper2 = Mock()
        mock_scraper2.method = "http"
        mock_scraper2.scrape = AsyncMock(side_effect=Exception("Timeout"))
        
        mock_scrapers.__iter__.return_value = [mock_scraper1, mock_scraper2]
        
        result = await scrape(["http"])
        
        # Should return empty set when all scrapers fail
        self.assertEqual(result, set())

    @patch('httpx.AsyncClient')
    async def test_scrape_function_client_management(self, mock_client_class):
        """Test that scrape function properly manages HTTP client lifecycle."""
        mock_client_instance = AsyncMock()
        mock_client_class.return_value = mock_client_instance
        
        with patch('jobspy.scrapers.proxy_scraper.scrapers', []):
            with self.assertRaises(ValueError):  # No scrapers for method
                await scrape(["nonexistent"])
        
        # Client should be created and properly closed
        mock_client_class.assert_called_once_with(follow_redirects=True)
        mock_client_instance.aclose.assert_called_once()


class TestHTTPErrorHandling(unittest.TestCase):
    """Test handling of various HTTP errors and edge cases."""

    def setUp(self):
        self.scraper = Scraper("http", "https://example.com/proxy-list")

    async def test_handle_http_status_errors(self):
        """Test handling of various HTTP status codes."""
        status_codes = [400, 401, 403, 404, 500, 502, 503, 504]
        
        for status_code in status_codes:
            with self.subTest(status_code=status_code):
                mock_client = AsyncMock()
                mock_response = Mock()
                mock_response.text = f"Error {status_code}"
                mock_response.status_code = status_code
                mock_client.get.return_value = mock_response
                
                # Scraper should still process the response
                result = await self.scraper.scrape(mock_client)
                
                # No valid IPs in error messages
                self.assertEqual(result, [])

    async def test_handle_network_exceptions(self):
        """Test handling of various network exceptions."""
        exceptions = [
            httpx.ConnectError("Connection failed"),
            httpx.TimeoutException("Request timeout"),
            httpx.HTTPStatusError("HTTP error", request=Mock(), response=Mock()),
            httpx.RequestError("Generic request error")
        ]
        
        for exception in exceptions:
            with self.subTest(exception=type(exception).__name__):
                mock_client = AsyncMock()
                mock_client.get.side_effect = exception
                
                with self.assertRaises(type(exception)):
                    await self.scraper.get_response(mock_client)


if __name__ == '__main__':
    unittest.main()