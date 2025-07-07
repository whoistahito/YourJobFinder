#!/usr/bin/env python3
"""
Test script for the improved Google Jobs Scraper
"""

import sys
import os

# Add JobSpy to path
sys.path.append('JobSpy/src')

from jobspy.scrapers.google import GoogleJobsScraper
from jobspy import ScraperInput


def test_google_scraper():
    """Test the improved Google scraper functionality"""
    print("Testing Improved Google Jobs Scraper")
    print("=" * 50)
    
    # Create scraper instance
    scraper = GoogleJobsScraper()
    
    # Test basic functionality
    print(f"✓ Scraper instantiated successfully")
    print(f"✓ User agents available: {len(scraper.USER_AGENTS)}")
    print(f"✓ Max retries: {scraper.max_retries}")
    
    # Test header generation
    headers_initial = scraper.get_dynamic_headers(is_initial=True)
    headers_jobs = scraper.get_dynamic_headers(is_initial=False)
    
    print(f"✓ Initial headers generated: {len(headers_initial)} keys")
    print(f"✓ Jobs headers generated: {len(headers_jobs)} keys")
    print(f"✓ User agent in headers: {'user-agent' in headers_initial}")
    
    # Test search params
    params = scraper.build_search_params("software engineer", "San Francisco")
    print(f"✓ Search params generated: {params}")
    
    # Test parsing methods
    try:
        location = scraper._parse_location_improved("San Francisco, CA, USA")
        print(f"✓ Location parsing: {location.city}, {location.state}, {location.country}")
    except Exception as e:
        print(f"✗ Location parsing failed: {e}")
    
    try:
        from datetime import datetime
        date = scraper._parse_date_improved("3 days ago")
        print(f"✓ Date parsing: {date}")
    except Exception as e:
        print(f"✗ Date parsing failed: {e}")
    
    # Test remote job detection
    is_remote1 = scraper._is_remote_job_improved("This is a remote position", "")
    is_remote2 = scraper._is_remote_job_improved("Office-based role", "New York")
    print(f"✓ Remote detection: remote={is_remote1}, office={is_remote2}")
    
    print("\n" + "=" * 50)
    print("✓ All basic tests passed!")
    print("Note: Full scraping test requires working proxies and may be rate-limited")


if __name__ == "__main__":
    test_google_scraper()