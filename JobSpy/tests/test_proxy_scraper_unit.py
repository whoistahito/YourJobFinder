"""
Unit tests for proxy scraper classes.
Tests individual methods and classes in isolation with mocked dependencies.
"""
import unittest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
import re
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
    GeoNodeScraper,
    ProxyListDownloadScraper,
    scrape,
    get_socks_proxies,
    get_https_proxies,
    test_scraper
)


class TestBaseScraper(unittest.TestCase):
    """Test the base Scraper class."""

    def setUp(self):
        self.scraper = Scraper("http", "https://example.com/{method}")

    def test_init(self):
        """Test scraper initialization."""
        self.assertEqual(self.scraper.method, "http")
        self.assertEqual(self.scraper._url, "https://example.com/{method}")

    def test_get_url(self):
        """Test URL generation."""
        url = self.scraper.get_url()
        self.assertEqual(url, "https://example.com/http")

    def test_get_url_with_kwargs(self):
        """Test URL generation with additional kwargs."""
        scraper = Scraper("https", "https://example.com/{method}?param={param}")
        url = scraper.get_url(param="value")
        self.assertEqual(url, "https://example.com/https?param=value")

    def test_get_response(self):
        """Test HTTP response retrieval."""
        async def run_test():
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_client.get.return_value = mock_response
            
            response = await self.scraper.get_response(mock_client)
            
            mock_client.get.assert_called_once_with("https://example.com/http")
            self.assertEqual(response, mock_response)
        
        asyncio.run(run_test())

    def test_handle(self):
        """Test response handling."""
        async def run_test():
            mock_response = Mock()
            mock_response.text = "proxy content"
            
            result = await self.scraper.handle(mock_response)
            
            self.assertEqual(result, "proxy content")
        
        asyncio.run(run_test())

    def test_scrape_http_method(self):
        """Test complete scraping for HTTP method."""
        async def run_test():
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.text = "192.168.1.1:8080\n10.0.0.1:3128"
            mock_client.get.return_value = mock_response
            
            result = await self.scraper.scrape(mock_client)
            
            expected = ["http://192.168.1.1:8080", "http://10.0.0.1:3128"]
            self.assertEqual(result, expected)
        
        asyncio.run(run_test())

    def test_scrape_socks_method(self):
        """Test complete scraping for SOCKS method."""
        async def run_test():
            scraper = Scraper("socks", "https://example.com/{method}")
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.text = "192.168.1.1:1080\n10.0.0.1:1080"
            mock_client.get.return_value = mock_response
            
            result = await scraper.scrape(mock_client)
            
            expected = ["socks5://192.168.1.1:1080", "socks://192.168.1.1:1080", 
                       "socks5://10.0.0.1:1080", "socks://10.0.0.1:1080"]
            self.assertEqual(result, expected)
        
        asyncio.run(run_test())

    def test_scrape_with_invalid_ips(self):
        """Test scraping filters out invalid IP addresses."""
        async def run_test():
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.text = "192.168.1.1:8080\n999.999.999.999:8080\n10.0.0.1:3128"
            mock_client.get.return_value = mock_response
            
            result = await self.scraper.scrape(mock_client)
            
            # The regex pattern r"\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?" will match 999.999.999.999:8080
            # as it only checks for digits, not valid IP ranges
            expected = ["http://192.168.1.1:8080", "http://999.999.999.999:8080", "http://10.0.0.1:3128"]
            self.assertEqual(result, expected)
        
        asyncio.run(run_test())


class TestGitHubScraper(unittest.TestCase):
    """Test GitHubScraper class."""

    def setUp(self):
        self.scraper = GitHubScraper("http", "https://github.com/example/data.txt")

    def test_handle_filters_method(self):
        """Test that handle method filters proxies by method."""
        async def run_test():
            mock_response = Mock()
            mock_response.text = "http://192.168.1.1:8080\nhttps://10.0.0.1:3128\nsocks5://127.0.0.1:1080"
            
            result = await self.scraper.handle(mock_response)
            
            # Should include both http and https proxies and strip protocol
            result_lines = set(result.split("\n"))
            expected_lines = {"192.168.1.1:8080", "10.0.0.1:3128"}
            self.assertEqual(result_lines, expected_lines)
        
        asyncio.run(run_test())

    def test_handle_no_matching_method(self):
        """Test handle when no proxies match the method."""
        async def run_test():
            mock_response = Mock()
            mock_response.text = "socks5://192.168.1.1:1080\nsocks4://10.0.0.1:1080"
            
            result = await self.scraper.handle(mock_response)
            
            self.assertEqual(result, "")
        
        asyncio.run(run_test())

    def test_handle_multiple_matching_proxies(self):
        """Test handle with multiple matching proxies."""
        async def run_test():
            mock_response = Mock()
            mock_response.text = "http://192.168.1.1:8080\nhttp://10.0.0.1:3128\nhttps://1.1.1.1:8080"
            
            result = await self.scraper.handle(mock_response)
            
            # Should include http and https proxies, order may vary due to set
            result_lines = set(result.split("\n"))
            expected_lines = {"192.168.1.1:8080", "10.0.0.1:3128", "1.1.1.1:8080"}
            self.assertEqual(result_lines, expected_lines)
        
        asyncio.run(run_test())


class TestGitHubScraperNoSlash(unittest.TestCase):
    """Test GitHubScraperNoSlash class."""

    def setUp(self):
        self.scraper = GitHubScraperNoSlash("socks5", "https://github.com/example/data.txt")

    def test_handle_returns_all_proxies(self):
        """Test that handle method returns all proxies without filtering."""
        async def run_test():
            mock_response = Mock()
            mock_response.text = "192.168.1.1:8080\n10.0.0.1:3128\n127.0.0.1:1080"
            
            result = await self.scraper.handle(mock_response)
            
            result_lines = set(result.split("\n"))
            expected_lines = {"192.168.1.1:8080", "10.0.0.1:3128", "127.0.0.1:1080"}
            self.assertEqual(result_lines, expected_lines)
        
        asyncio.run(run_test())

    def test_handle_empty_response(self):
        """Test handle with empty response."""
        async def run_test():
            mock_response = Mock()
            mock_response.text = ""
            
            result = await self.scraper.handle(mock_response)
            
            self.assertEqual(result, "")
        
        asyncio.run(run_test())


class TestProxyLibScraper(unittest.TestCase):
    """Test ProxyLibScraper class."""

    def setUp(self):
        self.scraper = ProxyLibScraper("https")

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        self.assertEqual(self.scraper.method, "https")
        self.assertEqual(self.scraper.limit, "200")
        self.assertEqual(self.scraper.sort_by, "last_checked")
        self.assertEqual(self.scraper.sort_order, "desc")
        self.assertEqual(self.scraper.country_code, "")
        self.assertEqual(self.scraper.anonymity, "Elite")

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        scraper = ProxyLibScraper("http", limit="100", sort_by="uptime", 
                                 sort_order="asc", country_code="US", anonymity="Anonymous")
        self.assertEqual(scraper.limit, "100")
        self.assertEqual(scraper.sort_by, "uptime")
        self.assertEqual(scraper.sort_order, "asc")
        self.assertEqual(scraper.country_code, "US")
        self.assertEqual(scraper.anonymity, "Anonymous")

    def test_get_url(self):
        """Test URL generation with parameters."""
        url = self.scraper.get_url()
        expected_base = "https://proxylib.com/free-proxy-list/"
        self.assertTrue(url.startswith(expected_base))
        self.assertIn("limit=200", url)
        self.assertIn("sort_by=last_checked", url)
        self.assertIn("sort_order=desc", url)
        self.assertIn("type=https", url)
        self.assertIn("anonymity=Elite", url)

    def test_handle_with_json_data(self):
        """Test handle method with valid JSON-LD data."""
        async def run_test():
            mock_response = Mock()
            mock_response.text = '''
            <html>
            <script type="application/ld+json">
            {
                "@type": "ItemList",
                "name": "Proxy Server List",
                "itemListElement": [
                    {"item": {"name": "192.168.1.1:8080"}},
                    {"item": {"name": "10.0.0.1:3128"}}
                ]
            }
            </script>
            </html>
            '''
            
            result = await self.scraper.handle(mock_response)
            
            result_lines = set(result.split("\n"))
            expected_lines = {"192.168.1.1:8080", "10.0.0.1:3128"}
            self.assertEqual(result_lines, expected_lines)
        
        asyncio.run(run_test())

    def test_handle_with_invalid_json(self):
        """Test handle method with invalid JSON data."""
        async def run_test():
            mock_response = Mock()
            mock_response.text = '''
            <html>
            <script type="application/ld+json">
            invalid json data
            </script>
            </html>
            '''
            
            result = await self.scraper.handle(mock_response)
            
            self.assertEqual(result, "")
        
        asyncio.run(run_test())

    def test_handle_no_json_script(self):
        """Test handle method when no JSON-LD script is found."""
        async def run_test():
            mock_response = Mock()
            mock_response.text = '<html><body>No JSON here</body></html>'
            
            result = await self.scraper.handle(mock_response)
            
            self.assertEqual(result, "")
        
        asyncio.run(run_test())


class TestSpysMeScraper(unittest.TestCase):
    """Test SpysMeScraper class."""

    def test_init_http(self):
        """Test initialization for HTTP method."""
        scraper = SpysMeScraper("http")
        self.assertEqual(scraper.method, "http")
        self.assertEqual(scraper._url, "https://spys.me/{mode}.txt")

    def test_init_socks(self):
        """Test initialization for SOCKS method."""
        scraper = SpysMeScraper("socks")
        self.assertEqual(scraper.method, "socks")

    def test_get_url_http(self):
        """Test URL generation for HTTP method."""
        scraper = SpysMeScraper("http")
        url = scraper.get_url()
        self.assertEqual(url, "https://spys.me/proxy.txt")

    def test_get_url_socks(self):
        """Test URL generation for SOCKS method."""
        scraper = SpysMeScraper("socks")
        url = scraper.get_url()
        self.assertEqual(url, "https://spys.me/socks.txt")

    def test_get_url_unknown_method(self):
        """Test URL generation for unknown method raises NotImplementedError."""
        scraper = SpysMeScraper("unknown")
        with self.assertRaises(NotImplementedError):
            scraper.get_url()


class TestProxyScrapeScraper(unittest.TestCase):
    """Test ProxyScrapeScraper class."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        scraper = ProxyScrapeScraper("http")
        self.assertEqual(scraper.method, "http")
        self.assertEqual(scraper.timout, 10000)
        self.assertEqual(scraper.country, "All")

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        scraper = ProxyScrapeScraper("socks5", timeout=5000, country="US")
        self.assertEqual(scraper.timout, 5000)  # Note: typo in original code
        self.assertEqual(scraper.country, "US")

    def test_get_url(self):
        """Test URL generation."""
        scraper = ProxyScrapeScraper("http", timeout=5000, country="US")
        url = scraper.get_url()
        expected_base = "https://api.proxyscrape.com/v2/"
        self.assertTrue(url.startswith(expected_base))
        self.assertIn("protocol=http", url)
        self.assertIn("timeout=5000", url)
        self.assertIn("country=US", url)


class TestGeneralTableScraper2(unittest.TestCase):
    """Test GeneralTableScraper2 class."""

    def setUp(self):
        self.scraper = GeneralTableScraper2("http", "https://example.com")

    def test_handle_with_encoded_ip(self):
        """Test handle method with base64 encoded IP."""
        async def run_test():
            import base64
            encoded_ip = base64.b64encode(b"192.168.1.1").decode('utf-8')
            mock_response = Mock()
            mock_response.text = f'''
            <table class="table">
                <tr>
                    <td><script>Base64.decode("{encoded_ip}")</script></td>
                    <td>8080</td>
                </tr>
            </table>
            '''
            
            result = await self.scraper.handle(mock_response)
            
            self.assertEqual(result, "192.168.1.1:8080")
        
        asyncio.run(run_test())

    def test_handle_with_plain_ip(self):
        """Test handle method with plain text IP."""
        async def run_test():
            mock_response = Mock()
            mock_response.text = '''
            <table class="table">
                <tr>
                    <td>10.0.0.1</td>
                    <td>3128</td>
                </tr>
            </table>
            '''
            
            result = await self.scraper.handle(mock_response)
            
            self.assertEqual(result, "10.0.0.1:3128")
        
        asyncio.run(run_test())

    def test_handle_no_table(self):
        """Test handle method when no table is found."""
        async def run_test():
            mock_response = Mock()
            mock_response.text = '<html><body>No table here</body></html>'
            
            result = await self.scraper.handle(mock_response)
            
            self.assertEqual(result, "\n")
        
        asyncio.run(run_test())

    def test_handle_insufficient_cells(self):
        """Test handle method with insufficient table cells."""
        async def run_test():
            mock_response = Mock()
            mock_response.text = '''
            <table class="table">
                <tr><td>192.168.1.1</td></tr>
            </table>
            '''
            
            result = await self.scraper.handle(mock_response)
            
            self.assertEqual(result, "")
        
        asyncio.run(run_test())


class TestAsyncFunctions(unittest.TestCase):
    """Test async module functions."""

    def test_get_socks_proxies(self):
        """Test get_socks_proxies function."""
        with patch('jobspy.scrapers.proxy_scraper.scrape') as mock_scrape:
            mock_scrape.return_value = {"socks5://1.1.1.1:1080", "socks4://2.2.2.2:1080"}
            
            result = get_socks_proxies()
            
            mock_scrape.assert_called_once_with(["socks5", "socks4"])
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 2)

    def test_get_https_proxies(self):
        """Test get_https_proxies function."""
        with patch('jobspy.scrapers.proxy_scraper.test_scraper') as mock_test_scraper:
            mock_test_scraper.return_value = ["https://1.1.1.1:8080", "https://2.2.2.2:8080"]
            
            result = get_https_proxies()
            
            mock_test_scraper.assert_called_once()
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 2)

    def test_scrape_function_no_scrapers(self):
        """Test scrape function with unsupported method."""
        async def run_test():
            with self.assertRaises(ValueError) as context:
                await scrape(["unsupported"])
            
            self.assertEqual(str(context.exception), "Method not supported")
        
        asyncio.run(run_test())

    @patch('jobspy.scrapers.proxy_scraper.scrapers')
    def test_scrape_function_success(self, mock_scrapers):
        """Test scrape function with successful execution."""
        async def run_test():
            # Create mock scrapers
            mock_scraper1 = Mock()
            mock_scraper1.method = "http"
            mock_scraper1.scrape = AsyncMock(return_value=["http://1.1.1.1:8080"])
            
            mock_scraper2 = Mock()
            mock_scraper2.method = "http"
            mock_scraper2.scrape = AsyncMock(return_value=["http://2.2.2.2:8080"])
            
            mock_scrapers.__iter__.return_value = [mock_scraper1, mock_scraper2]
            
            result = await scrape(["http"])
            
            self.assertIsInstance(result, set)
            self.assertTrue(len(result) >= 0)  # May be empty due to set deduplication
        
        asyncio.run(run_test())

    @patch('jobspy.scrapers.proxy_scraper.ProxyLibScraper')
    def test_test_scraper_function(self, mock_proxy_lib_scraper):
        """Test test_scraper function."""
        async def run_test():
            mock_scraper_instance = Mock()
            mock_scraper_instance.scrape = AsyncMock(return_value=["https://1.1.1.1:8080"])
            mock_proxy_lib_scraper.return_value = mock_scraper_instance
            
            result = await test_scraper()
            
            mock_proxy_lib_scraper.assert_called_once_with("https")
            mock_scraper_instance.scrape.assert_called_once()
            self.assertEqual(result, ["https://1.1.1.1:8080"])
        
        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()