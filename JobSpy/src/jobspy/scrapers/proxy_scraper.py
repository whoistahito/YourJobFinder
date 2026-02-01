import asyncio
import base64
import re

from bs4 import BeautifulSoup
import httpx
from .utils import create_logger

logger = create_logger("proxy_scraper")

headers_initial = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9",
    "priority": "u=0, i",
    "referer": "https://www.google.com/",
    "sec-ch-prefers-color-scheme": "dark",
    "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    "sec-ch-ua-arch": '"arm"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-form-factors": '"Desktop"',
    "sec-ch-ua-full-version": '"130.0.6723.58"',
    "sec-ch-ua-full-version-list": '"Chromium";v="130.0.6723.58", "Google Chrome";v="130.0.6723.58", "Not?A_Brand";v="99.0.0.0"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"macOS"',
    "sec-ch-ua-platform-version": '"15.0.1"',
    "sec-ch-ua-wow64": "?0",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "x-browser-channel": "stable",
    "x-browser-copyright": "Copyright 2024 Google LLC. All rights reserved.",
    "x-browser-year": "2024",
}


class Scraper:

    def __init__(self, method, _url):
        self.method = method
        self._url = _url

    def get_url(self, **kwargs):
        return self._url.format(**kwargs, method=self.method)

    async def get_response(self, client):
        return await client.get(self.get_url())

    async def handle(self, response):
        return response.text

    async def scrape(self, client):
        response = await self.get_response(client)
        proxies = await self.handle(response)
        pattern = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?")
        prx = re.findall(pattern, proxies)
        all_prx = []
        for i in prx:
            if self.method == "socks":
                all_prx.append(f"{self.method}5://{i}")
            all_prx.append(f"{self.method}://{i}")
        return all_prx


# From spys.me
class SpysMeScraper(Scraper):

    def __init__(self, method):
        super().__init__(method, "https://spys.me/{mode}.txt")

    def get_url(self, **kwargs):
        mode = "proxy" if self.method == "http" else "socks" if self.method == "socks" else "unknown"
        if mode == "unknown":
            raise NotImplementedError
        return super().get_url(mode=mode, **kwargs)


# From proxyscrape.com
class ProxyScrapeScraper(Scraper):

    def __init__(self, method, timeout=10000, country="All"):
        self.timout = timeout
        self.country = country
        super().__init__(method,
                         "https://api.proxyscrape.com/v2/?request=displayproxies&protocol={method}&timeout={timout}&country={country}&ssl=all&anonymity=All")

    def get_url(self, **kwargs):
        return super().get_url(timout=self.timout, country=self.country, **kwargs)


# From geonode.com - A little dirty, grab http(s) and socks but use just for socks
class GeoNodeScraper(Scraper):

    def __init__(self, method, limit="500", page="1", sort_by="lastChecked", sort_type="desc"):
        self.limit = limit
        self.page = page
        self.sort_by = sort_by
        self.sort_type = sort_type
        super().__init__(method,
                         "https://proxylist.geonode.com/api/proxy-list?"
                         "&limit={limit}"
                         "&page={page}"
                         "&sort_by={sort_by}"
                         "&sort_type={sort_type}")

    def get_url(self, **kwargs):
        return super().get_url(limit=self.limit, page=self.page, sort_by=self.sort_by, sort_type=self.sort_type,
                               **kwargs)


# From proxylib.com
class ProxyLibScraper(Scraper):
    def __init__(self, method, limit="200", sort_by="last_checked", sort_order="desc", country_code="",
                 anonymity="Elite"):
        self.limit = limit
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.country_code = country_code
        self.anonymity = anonymity
        super().__init__(method,
                         "https://proxylib.com/free-proxy-list/?limit={limit}&sort_by={sort_by}&sort_order={sort_order}&country_code={country_code}&type={method}&anonymity={anonymity}")

    def get_url(self, **kwargs):
        return super().get_url(limit=self.limit, sort_by=self.sort_by, sort_order=self.sort_order,
                               country_code=self.country_code, anonymity=self.anonymity, **kwargs)

    async def handle(self, response):
                soup = BeautifulSoup(response.text, "html.parser")
                proxies = set()

                # Find all script tags with type="application/ld+json"
                script_tags = soup.find_all("script", type="application/ld+json")

                # Look for the script tag that contains proxy data
                for script_tag in script_tags:
                    if script_tag and '"@type": "ItemList"' in script_tag.string and '"name": "Proxy Server List"' in script_tag.string:
                        try:
                            import json
                            json_data = json.loads(script_tag.string)
                            items = json_data.get("itemListElement", [])

                            for item in items:
                                if "item" in item and "name" in item["item"]:
                                    proxy = item["item"]["name"]
                                    if ":" in proxy:  # Validate proxy format
                                        proxies.add(proxy)
                        except json.JSONDecodeError:
                            pass

                return "\n".join(proxies)
# From proxy-list.download
class ProxyListDownloadScraper(Scraper):

    def __init__(self, method, anon):
        self.anon = anon
        super().__init__(method, "https://www.proxy-list.download/api/v1/get?type={method}&anon={anon}")

    def get_url(self, **kwargs):
        return super().get_url(anon=self.anon, **kwargs)


class GeneralTableScraper2(Scraper):
    async def handle(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        proxies = set()
        # Find the table in the soup.
        table = soup.find("table", attrs={"class": "table"}) or soup.find("tbody")

        if not table:
            return "\n"

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            # Extract IP from either <script> or directly from the cell.
            ip_script = cells[0].find("script")
            if ip_script and 'Base64.decode' in ip_script.string:
                # Decode the IP address if encoded
                encoded_ip = ip_script.string.split('"')[1]
                ip_address = base64.b64decode(encoded_ip).decode('utf-8')
            else:
                # Fallback: direct text in case of non-encoded IP
                ip_address = cells[0].text.strip()

            # Extract the port number
            port = cells[1].text.strip()

            # Form the full proxy string
            proxy = f"{ip_address}:{port}"
            proxies.add(proxy)

        return "\n".join(proxies)


class GeneralTableScraper(Scraper):

    async def handle(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        proxies = set()
        table = soup.find("table", attrs={"class": "table table-striped table-bordered"})
        for row in table.findAll("tr"):
            count = 0
            proxy = ""
            for cell in row.findAll("td"):
                if count == 1:
                    proxy += ":" + cell.text.replace("&nbsp;", "")
                    proxies.add(proxy)
                    break
                proxy += cell.text.replace("&nbsp;", "")
                count += 1
        return "\n".join(proxies)


# For websites using div in html
class GeneralDivScraper(Scraper):

    async def handle(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        proxies = set()
        table = soup.find("div", attrs={"class": "list"})
        for row in table.findAll("div"):
            count = 0
            proxy = ""
            for cell in row.findAll("div", attrs={"class": "td"}):
                if count == 2:
                    break
                proxy += cell.text + ":"
                count += 1
            proxy = proxy.rstrip(":")
            proxies.add(proxy)
        return "\n".join(proxies)


class GitHubScraperNoSlash(Scraper):

    async def handle(self, response):
        tempproxies = response.text.split("\n")
        proxies = set()
        for prxy in tempproxies:
            proxies.add(prxy)

        return "\n".join(proxies)


# For scraping live proxylist from github
class GitHubScraper(Scraper):

    async def handle(self, response):
        tempproxies = response.text.split("\n")
        proxies = set()
        for prxy in tempproxies:
            if self.method in prxy:
                proxies.add(prxy.split("//")[-1])

        return "\n".join(proxies)


scrapers = [
    SpysMeScraper("http"),
    SpysMeScraper("socks"),
    ProxyScrapeScraper("http"),
    ProxyScrapeScraper("socks5"),
    GeoNodeScraper("socks"),
    ProxyLibScraper("https"),
    ProxyListDownloadScraper("https", "elite"),
    ProxyListDownloadScraper("http", "elite"),
    ProxyListDownloadScraper("http", "transparent"),
    ProxyListDownloadScraper("http", "anonymous"),
    GeneralTableScraper("https", "http://sslproxies.org"),
    GeneralTableScraper("https",
                        "https://proxylib.com/free-proxy-list/?limit=200&sort_by=last_checked&sort_order=desc&country_code=&type=&anonymity=Elite"),
    GeneralTableScraper2("socks5", "http://free-proxy.cz/en/proxylist/country/all/socks5/ping/level1"),
    GeneralTableScraper2("https", "http://free-proxy.cz/en/proxylist/country/all/https/ping/level1"),
    GeneralTableScraper("http", "http://free-proxy-list.net"),
    GeneralTableScraper("http", "http://us-proxy.org"),
    GeneralTableScraper("https", "https://proxy-tools.com/proxy/https"),
    GeneralTableScraper("socks", "http://socks-proxy.net"),
    GeneralDivScraper("http", "https://freeproxy.lunaproxy.com/"),
    GitHubScraper("http", "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt"),
    GitHubScraper("socks4", "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt"),
    GitHubScraper("socks5", "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt"),
    GitHubScraper("https",
                  "https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/https/data.txt"),
    GitHubScraper("http", "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt"),
    GitHubScraper("socks5", "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt"),
    GitHubScraper("https", "https://raw.githubusercontent.com/zloi-user/hideip.me/main/https.txt"),
    GitHubScraper("http", "https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt"),
    GitHubScraper("socks4", "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks4.txt"),
    GitHubScraper("socks5", "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks5.txt"),
    GitHubScraperNoSlash("socks5", "https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/main/socks5.txt"),
    GitHubScraperNoSlash("socks4", "https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/main/socks4.txt"),
]


async def scrape(methods):
    proxy_scrapers = [s for s in scrapers if s.method in methods]
    if not proxy_scrapers:
        raise ValueError("Method not supported")
    proxies = []

    tasks = []
    client = httpx.AsyncClient(follow_redirects=True)

    async def scrape_scraper(scraper):
        try:
            proxies.extend(await scraper.scrape(client))
        except Exception:
            pass

    for scraper in proxy_scrapers:
        tasks.append(asyncio.ensure_future(scrape_scraper(scraper)))

    await asyncio.gather(*tasks)
    await client.aclose()

    return set(proxies)


def get_socks_proxies():
    try:
        proxies_set = asyncio.run(scrape(["socks5", "socks4"]))
        return list(proxies_set)
    except Exception as e:
        logger.error(f"Failed to fetch SOCKS proxies: {e}")
        return []

def get_https_proxies():
    try:
        proxies_set = asyncio.run(test_scraper())
        return list(proxies_set)
    except Exception as e:
        logger.error(f"Failed to fetch HTTPS proxies: {e}")
        return []

async def test_scraper():
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            scraper = ProxyLibScraper("https")
            # Scrap the proxies using the SpysMeScraper
            proxies = await scraper.scrape(client)
            return list(proxies)
    except Exception as e:
        logger.error(f"Error in test_scraper: {e}")
        return []
