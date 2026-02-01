"""
jobspy.scrapers.proxy_manager
~~~~~~~~~~~~~~~~~~~

This module provides an optimized proxy management system for JobSpy.
"""

import asyncio
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Dict, Optional, Callable, Any, Tuple
import httpx

from .utils import create_logger
from .proxy_scraper import get_socks_proxies, get_https_proxies

logger = create_logger("ProxyManager")


class ProxyManager:
    """
    A centralized proxy management system that efficiently finds and manages working proxies.
    Features:
    - Proxy caching with expiration
    - Parallel proxy testing
    - Domain-specific proxy pools
    - Automatic proxy rotation and retry
    """

    def __init__(self, cache_duration: int = 1800):
        """
        Initialize the proxy manager.

        Args:
            cache_duration: How long (in seconds) to cache working proxies before re-testing
        """
        self.cache_duration = cache_duration
        self._proxy_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._last_fetch_time = 0
        self._all_proxies = []
        self._min_fetch_interval = 300  # Minimum seconds between proxy list refreshes

    def get_working_proxy(self,
                          domain: str,
                          test_func: Callable[[dict, Any], Optional[Any]],
                          test_args: Any,
                          batch_size: int = 120,
                          max_attempts: int = 3) -> Tuple[Optional[dict], Optional[Any]]:
        """
        Get a working proxy for the specified domain.

        Args:
            domain: The domain to get a proxy for (e.g., 'linkedin', 'google')
            test_func: Function to test if a proxy works with the domain
            test_args: Arguments to pass to the test function
            batch_size: How many proxies to test in parallel
            max_attempts: Maximum number of batches to try before giving up

        Returns:
            Tuple of (working_proxy, test_result) or (None, None) if no working proxy found
        """
        # Check if we have a cached working proxy for this domain
        with self._lock:
            cached = self._proxy_cache.get(domain)
            current_time = time.time()

            if cached and current_time - cached['timestamp'] < self.cache_duration:
                logger.info(f"Using cached proxy for {domain}")
                return cached['proxy'], cached.get('result')

        # Get fresh proxies if needed
        self._ensure_proxies_available()

        # Try to find a working proxy
        for attempt in range(max_attempts):
            logger.info(f"Finding working proxy for {domain} (attempt {attempt + 1}/{max_attempts})")

            # Get a batch of proxies to test
            with self._lock:
                # Shuffle to avoid always testing the same proxies first
                random.shuffle(self._all_proxies)
                batch_start = attempt * batch_size
                batch_end = batch_start + batch_size
                proxy_batch = self._all_proxies[batch_start:batch_end]

                if not proxy_batch:
                    logger.warning(f"No more proxies to test for {domain}")
                    break

            # Test proxies in parallel
            proxy, result = self._test_proxy_batch(proxy_batch, domain, test_func, test_args)

            if proxy:
                # Cache the working proxy
                with self._lock:
                    self._proxy_cache[domain] = {
                        'proxy': proxy,
                        'result': result,
                        'timestamp': time.time()
                    }
                return proxy, result

        logger.error(f"Failed to find working proxy for {domain} after {max_attempts} attempts")
        return None, None

    def _test_proxy_batch(self,
                          proxies: List[dict],
                          domain: str,
                          test_func: Callable[[dict, Any], Optional[Any]],
                          test_args: Any) -> Tuple[Optional[dict], Optional[Any]]:
        """Test a batch of proxies in parallel and return the first working one."""
        logger.info(f"Testing batch of {len(proxies)} proxies for {domain}")

        with ThreadPoolExecutor(max_workers=min(len(proxies), 20)) as executor:
            # Submit all proxy tests
            future_to_proxy = {
                executor.submit(test_func, proxy, test_args): proxy
                for proxy in proxies
            }

            # Process results as they complete
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    result = future.result()
                    if result is not None:
                        logger.info(f"Found working proxy for {domain}")
                        return proxy, result
                except Exception as exc:
                    # Just log at debug level since most proxies will fail
                    logger.debug(f"Proxy test failed: {exc}")

        return None, None

    def _ensure_proxies_available(self):
        """Ensure we have proxies available, fetching new ones if needed."""
        current_time = time.time()

        with self._lock:
            # Only fetch new proxies if we don't have any or if enough time has passed
            if (not self._all_proxies or
                    current_time - self._last_fetch_time > self._min_fetch_interval):

                logger.info("Fetching fresh proxy list")
                try:
                    # Get both SOCKS and HTTPS proxies
                    socks_proxies = get_socks_proxies()
                    https_proxies = get_https_proxies()

                    # Format and combine proxies
                    all_proxies = (
                        [{'http': proxy, 'https': proxy} for proxy in socks_proxies] +
                        [{'http': proxy, 'https': proxy} for proxy in https_proxies]
                    )

                    # Deduplicate while preserving order
                    seen_proxies = set()
                    unique_proxies = []
                    for proxy in all_proxies:
                        proxy_key = (proxy['http'], proxy['https'])
                        if proxy_key not in seen_proxies:
                            seen_proxies.add(proxy_key)
                            unique_proxies.append(proxy)

                    if unique_proxies:
                        self._all_proxies = unique_proxies
                        self._last_fetch_time = current_time
                        logger.info(f"Fetched {len(self._all_proxies)} unique proxies")
                    else:
                        logger.warning("No proxies fetched, keeping existing proxy list if available")
                        if not self._all_proxies:
                            logger.error("No proxies available and failed to fetch new ones")
                except Exception as e:
                    logger.error(f"Error fetching proxies: {e}")
                    if not self._all_proxies:
                        logger.error("No proxies available and failed to fetch new ones")

    def invalidate_proxy(self, domain: str):
        """Mark a cached proxy as invalid, forcing a new one to be found next time."""
        with self._lock:
            if domain in self._proxy_cache:
                logger.info(f"Invalidating cached proxy for {domain}")
                del self._proxy_cache[domain]


# Singleton instance
_proxy_manager = None


def get_proxy_manager() -> ProxyManager:
    """Get the global proxy manager instance."""
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = ProxyManager()
    return _proxy_manager
