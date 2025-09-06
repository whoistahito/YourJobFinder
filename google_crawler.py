import csv
import os
import random
import re
import time

from camoufox.sync_api import Camoufox

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}


def is_cloudflare_challenge(page):
    # Check for common Cloudflare challenge indicators
    try:
        title = page.title() or ''
        if 'Just a moment...' in title or 'cloudflare' in title.lower() or 'Attention Required!' in title:
            return True

        # Look for challenge elements
        if page.query_selector('div#cf-challenge') or page.query_selector('div#challenge-stage'):
            return True

        # Look for iframe
        if page.query_selector('iframe[src*="challenges.cloudflare.com"]'):
            return True

    except Exception:
        pass
    return False


def solve_cloudflare_challenge(page, max_wait=30):
    print("Cloudflare challenge detected. Attempting to solve...")

    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            # Wait for the main page to stabilize a bit
            page.wait_for_load_state('domcontentloaded')

            if not is_cloudflare_challenge(page):
                print("Cloudflare challenge resolved.")
                return True

            # Use frame_locator to reliably find the iframe
            iframe_locator = page.frame_locator('iframe[src*="challenges.cloudflare.com"]')

            # Check if the iframe contains the checkbox and click it
            checkbox = iframe_locator.locator('input[type="checkbox"]')
            if checkbox.is_visible():
                print("Found Cloudflare Turnstile/Checkbox, clicking...")
                checkbox.click()
                # Wait for the challenge to be considered solved by observing the page
                page.wait_for_function("!document.querySelector('iframe[src*=\"challenges.cloudflare.com\"]')",
                                       timeout=10000)
                print("Challenge appears to be solved after click.")
                return True

        except Exception as e:
            # This might fail if the iframe or elements are not ready, which is fine, we'll retry
            print(f"Waiting for challenge elements... ({int(time.time() - start_time)}s)")
            pass

        time.sleep(2)

    if is_cloudflare_challenge(page):
        print("Cloudflare challenge not resolved after waiting and trying to solve.")
        return False
    else:
        print("Cloudflare challenge appears to be resolved after waiting.")
        return True


def visit_google_links_with_camoufox(input_csv_path, output_csv_path, html_output_dir, max_links=100):
    # Create the directory for HTML files if it doesn't exist
    os.makedirs(html_output_dir, exist_ok=True)

    # Step 1: Read already processed URLs from the output file to avoid re-scraping
    processed_urls = set()
    try:
        with open(output_csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'job_url' in row:
                    processed_urls.add(row['job_url'])
        if processed_urls:
            print(f"Resuming. Found {len(processed_urls)} already scraped URLs in {output_csv_path}.")
    except FileNotFoundError:
        print(f"Output file {output_csv_path} not found. Starting a new scrape.")

    # Step 2: Read all URLs from the input file
    all_rows = []
    input_fieldnames = []
    try:
        with open(input_csv_path, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            input_fieldnames = reader.fieldnames or ['url']
            all_rows = list(reader)
    except FileNotFoundError:
        print(f"Input file {input_csv_path} not found.")
        return
    except Exception as e:
        print(f"Error reading {input_csv_path}: {e}")
        return

    # Filter for valid URLs that haven't been processed yet
    urls_to_process = [
        row['job_url'] for row in all_rows
        if 'job_url' in row and row['job_url'] not in processed_urls
    ][:max_links]

    if not urls_to_process:
        print("No new URLs to process.")
        return

    print(f"Found {len(urls_to_process)} new URLs to process.")

    newly_processed_urls = set()
    try:
        # Step 3: Scrape new URLs and save HTML content
        with open(output_csv_path, 'a', newline='', encoding='utf-8') as outfile:
            output_fieldnames = list(input_fieldnames) + ['html_file_path']
            writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)

            if outfile.tell() == 0:
                writer.writeheader()

            with Camoufox(humanize=2.0, headless=True) as browser:
                for i, url in enumerate(urls_to_process):
                    print(f"Processing URL {i + 1}/{len(urls_to_process)}: {url}")
                    page = browser.new_page()
                    try:
                        page.goto(url, wait_until='domcontentloaded', timeout=60000)
                        print(f"Visited: {url}")

                        if is_cloudflare_challenge(page):
                            solve_cloudflare_challenge(page, max_wait=30)

                        html_file_path = ''

                        # Check for error indicators before saving
                        page_title = page.title()
                        page_content = page.content()
                        error_keywords = ['error', 'not found', 'job not found', 'listing not found', 'page not found'
                            , "nicht verfügbar", "nicht mehr verfügbar", "nicht gefunden", "seite nicht gefunden",
                                          "abgelaufen", "entfernt", "nicht existiert"]

                        title_lower = page_title.lower()
                        content_lower = page_content.lower()

                        found_error = False
                        for keyword in error_keywords:
                            if keyword in title_lower or keyword in content_lower:
                                print(f"Found error keyword '{keyword}' on page {url}. Skipping save.")
                                found_error = True
                                break

                        if not found_error:
                            try:
                                # Sanitize URL to create a valid filename
                                sanitized_filename = re.sub(r'[<>:"/\\|?*]', '_', url) + '.html'
                                html_file_path = os.path.join(html_output_dir, sanitized_filename)

                                # Save the full HTML content
                                with open(html_file_path, 'w', encoding='utf-8') as f:
                                    f.write(page_content)
                                print(f"Saved HTML to {html_file_path}")

                            except Exception as e:
                                print(f"Could not save page content for {url}: {e}")

                        # Find the original row to write to output
                        original_row = next((row for row in all_rows if row.get('job_url') == url), {})
                        output_row = original_row.copy()
                        output_row['html_file_path'] = html_file_path
                        writer.writerow(output_row)
                        outfile.flush()  # Save progress immediately
                        newly_processed_urls.add(url)

                    except Exception as e:
                        print(f"Failed to process page {url}: {e}")
                    finally:
                        page.close()
                        time.sleep(random.uniform(2, 5))

    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Progress has been saved.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}. Progress has been saved.")
    finally:
        # Step 4: Remove the newly processed URLs from the input file
        if newly_processed_urls:
            print(f"Removing {len(newly_processed_urls)} processed URLs from {input_csv_path}.")

            remaining_rows = [row for row in all_rows if row.get('job_url') not in newly_processed_urls]

            try:
                with open(input_csv_path, 'w', newline='', encoding='utf-8') as infile:
                    writer = csv.DictWriter(infile, fieldnames=input_fieldnames)
                    writer.writeheader()
                    writer.writerows(remaining_rows)
                print(f"{input_csv_path} has been updated.")
            except Exception as e:
                print(f"Error writing updated list to {input_csv_path}: {e}")

    total_processed = len(processed_urls) + len(newly_processed_urls)
    print(f"Finished session. Total URLs processed: {total_processed}")


if __name__ == "__main__":
    visit_google_links_with_camoufox(
        input_csv_path='google_links.csv',
        output_csv_path='google_html_paths.csv',
        html_output_dir='google_html',
        max_links=100
    )
