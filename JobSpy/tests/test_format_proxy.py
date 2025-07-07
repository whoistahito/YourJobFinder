import unittest

from jobspy.scrapers.utils import RotatingProxySession


class TestProxyFormatter(unittest.TestCase):
    def test_http_proxy(self):
        proxy = "http://example.com:8080"
        expected = {"http": "http://example.com:8080", "https": "http://example.com:8080"}
        result = RotatingProxySession.format_proxy(proxy)
        self.assertEqual(result, expected)

    def test_https_proxy(self):
        proxy = "https://example.com:8080"
        expected = {"http": "https://example.com:8080", "https": "https://example.com:8080"}
        result = RotatingProxySession.format_proxy(proxy)
        self.assertEqual(result, expected)

    def test_plain_proxy(self):
        proxy = "example.com:8080"
        expected = {"http": "http://example.com:8080", "https": "http://example.com:8080"}
        result = RotatingProxySession.format_proxy(proxy)
        self.assertEqual(result, expected)

    def test_socks_proxy(self):
        proxy = "socks5://example.com:1080"
        expected = {"http": "socks5://example.com:1080", "https": "socks5://example.com:1080"}
        result = RotatingProxySession.format_proxy(proxy)
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
