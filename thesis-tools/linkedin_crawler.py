import os
import requests
import csv
import time
import re

CSV_PATH = 'verified_linkedin_links_final.csv'
OUTPUT_DIR = 'linkedin_html'

os.makedirs(OUTPUT_DIR, exist_ok=True)

def sanitize_filename(url):
    # Remove protocol and non-alphanumeric characters
    return re.sub(r'[^a-zA-Z0-9]', '_', url)

with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    header = next(reader, None)  # Skip header row
    for idx, row in enumerate(reader):
        if len(row) < 2:
            print(f'Skipping row {idx+1}: not enough columns')
            continue
        url = row[1]
        if not url:
            print(f'Skipping row {idx+1}: empty URL')
            continue
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            safe_name = sanitize_filename(url)
            file_path = os.path.join(OUTPUT_DIR, f'page_{idx}_{safe_name}.html')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            time.sleep(1)  # polite crawling
        except Exception as e:
            print(f'Failed to fetch {url} (row {idx+1}): {e}')
