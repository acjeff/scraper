#!/usr/bin/env python3
"""
Parallel URL scraper with chunking and resume capability
"""

import os
import sys
import csv
import time
import json
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from urllib.parse import urlparse
import requests
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
# import pandas as pd  # Not needed for this implementation

# Global variables for tracking progress
processed_count = 0
total_count = 0

# Set Railway environment variables if not already set
if not os.environ.get("CHROME_BIN"):
    os.environ["CHROME_BIN"] = "chromium"
if not os.environ.get("CHROMEDRIVER_PATH"):
    os.environ["CHROMEDRIVER_PATH"] = "chromedriver"

def init_driver():
    """Initialize Chrome driver with anti-detection measures"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

    # Prefer system-installed Chromium/Chromedriver (Railway/Nixpacks) and fall back to webdriver_manager
    chrome_bin = os.environ.get("CHROME_BIN") or shutil.which("chromium") or shutil.which("chromium-browser")
    if chrome_bin:
        options.binary_location = chrome_bin
        print(f"Using Chrome binary: {chrome_bin}")

    # Try multiple paths for chromedriver
    chromedriver_path = None
    possible_paths = [
        os.environ.get("CHROMEDRIVER_PATH"),
        shutil.which("chromedriver"),
        "/usr/bin/chromedriver",
        "/nix/var/nix/profiles/default/bin/chromedriver"
    ]
    
    for path in possible_paths:
        if path and os.path.exists(path):
            chromedriver_path = path
            print(f"Found chromedriver at: {chromedriver_path}")
            break
    
    if not chromedriver_path:
        print("ChromeDriver not found in system paths, downloading with webdriver_manager...")
        # Fallback: download with webdriver_manager (useful locally)
        base_path = ChromeDriverManager().install()
        chromedriver_dir = os.path.dirname(base_path)
        chromedriver_path = os.path.join(chromedriver_dir, "chromedriver")
        print(f"Downloaded chromedriver to: {chromedriver_path}")

    driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
    driver.set_page_load_timeout(120)
    
    # Execute script to remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def check_url(url):
    """Check if URL is accessible and return HTML content"""
    try:
        driver = init_driver()
        driver.get(url)
        time.sleep(2)  # Brief wait for page load
        html = driver.page_source
        driver.quit()
        return html
    except Exception as e:
        print(f"Error checking URL {url}: {e}")
        if 'driver' in locals():
            driver.quit()
        return None

def extract_info(html, platform, url):
    """Extract information from HTML content"""
    info = {'account': '', 'account_id': '', 'media_title': '', 'media_length': ''}
    
    if not html:
        return info
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        if platform == 'YouTube':
            # YouTube extraction logic (full implementation)
            try:
                # Extract title from meta tags
                title_element = soup.find('meta', property='og:title')
                if title_element:
                    info['media_title'] = title_element.get('content', '')
                
                # Extract duration from meta tags (multiple methods)
                duration_found = False
                
                # Method 1: Try meta[itemprop="duration"]
                duration_element = soup.find('meta', attrs={'itemprop': 'duration'})
                if duration_element:
                    duration = duration_element.get('content', '')
                    if duration.startswith('PT'):
                        # Convert ISO 8601 duration to readable format
                        duration = duration[2:]
                        hours = 0
                        minutes = 0
                        seconds = 0
                        
                        if 'H' in duration:
                            hours = int(duration.split('H')[0])
                            duration = duration.split('H')[1]
                        if 'M' in duration:
                            minutes = int(duration.split('M')[0])
                            duration = duration.split('M')[1]
                        if 'S' in duration:
                            seconds = int(duration.split('S')[0])
                        
                        if hours > 0:
                            info['media_length'] = f"{hours}:{minutes:02d}:{seconds:02d}"
                        else:
                            info['media_length'] = f"{minutes}:{seconds:02d}"
                        duration_found = True
                
                # Method 2: Try meta[property="video:duration"]
                if not duration_found:
                    duration_element = soup.find('meta', property='video:duration')
                    if duration_element:
                        duration = duration_element.get('content', '')
                        if duration.startswith('PT'):
                            # Convert ISO 8601 duration
                            duration = duration[2:]
                            hours = minutes = seconds = 0
                            if 'H' in duration:
                                hours = int(duration.split('H')[0])
                                duration = duration.split('H')[1]
                            if 'M' in duration:
                                minutes = int(duration.split('M')[0])
                                duration = duration.split('M')[1]
                            if 'S' in duration:
                                seconds = int(duration.split('S')[0])
                            
                            if hours > 0:
                                info['media_length'] = f"{hours}:{minutes:02d}:{seconds:02d}"
                            else:
                                info['media_length'] = f"{minutes}:{seconds:02d}"
                
                # Extract account info from meta tags
                channel_element = soup.find('meta', attrs={'name': 'author'})
                if channel_element:
                    info['account'] = channel_element.get('content', '')
                
                # Try to extract channel ID from various meta tags
                channel_id_selectors = [
                    ('meta', {'name': 'channelId'}),
                    ('meta', {'property': 'og:video:channel'}),
                    ('meta', {'itemprop': 'channelId'})
                ]
                
                for tag, attrs in channel_id_selectors:
                    element = soup.find(tag, attrs)
                    if element and element.get('content'):
                        info['account_id'] = element.get('content')
                        break
                
            except Exception as e:
                print(f"Error extracting YouTube info: {e}")
        
        elif platform == 'TikTok':
            # TikTok extraction logic
            try:
                # Extract account from URL
                if '@' in url:
                    parts = url.split('@')
                    if len(parts) > 1:
                        extracted_string = '@' + parts[1].split('/')[0]
                        info['account'] = extracted_string
                
                # Extract title from meta tags
                title_selectors = [
                    ('meta', {'property': 'og:title'}),
                    ('meta', {'name': 'title'}),
                    ('meta', {'property': 'twitter:title'})
                ]
                
                for tag, attrs in title_selectors:
                    element = soup.find(tag, attrs)
                    if element and element.get('content'):
                        title_text = element.get('content')
                        if title_text.endswith(' on TikTok'):
                            title_text = title_text[:-10]
                        info['media_title'] = title_text
                        break
                
                # Extract duration (limited availability)
                duration_element = soup.find('meta', property='video:duration')
                if duration_element:
                    duration_text = duration_element.get('content', '')
                    if duration_text.isdigit():
                        duration_seconds = int(duration_text)
                        minutes = duration_seconds // 60
                        seconds = duration_seconds % 60
                        info['media_length'] = f"{minutes}:{seconds:02d}"
            except Exception as e:
                print(f"Error extracting TikTok info: {e}")
        
        elif platform == 'Soundcloud':
            # Soundcloud extraction logic
            try:
                # Extract account from URL
                if 'soundcloud.com/' in url:
                    parts = url.split('soundcloud.com/')
                    if len(parts) > 1:
                        extracted_string = parts[1].split('/')[0]
                        info['account'] = extracted_string
                
                # Extract title from meta tags
                title_element = soup.find('meta', property='og:title')
                if title_element:
                    info['media_title'] = title_element.get('content', '')
                
                # Extract duration from hydration data
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'window.__sc_hydration' in script.string:
                        try:
                            start = script.string.find('window.__sc_hydration = ') + len('window.__sc_hydration = ')
                            end = script.string.find(';', start)
                            if end == -1:
                                end = len(script.string)
                            data_str = script.string[start:end]
                            data = json.loads(data_str)
                            
                            for item in data:
                                if item.get('hydratable') == 'sound' and item.get('data'):
                                    sound_data = item['data']
                                    if 'duration' in sound_data:
                                        duration_ms = sound_data['duration']
                                        duration_seconds = duration_ms // 1000
                                        minutes = duration_seconds // 60
                                        seconds = duration_seconds % 60
                                        info['media_length'] = f"{minutes}:{seconds:02d}"
                                        break
                        except:
                            continue
            except Exception as e:
                print(f"Error extracting Soundcloud info: {e}")
        
        elif platform == 'Daily Motion':
            # Daily Motion API extraction
            try:
                import requests
                
                # Extract video ID from URL
                video_id = url.split('/')[-1]
                
                # Use Daily Motion's oEmbed API
                oembed_url = f"https://www.dailymotion.com/services/oembed?url={url}&format=json"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
                }
                
                response = requests.get(oembed_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract account from author_name
                    if 'author_name' in data:
                        info['account'] = data['author_name']
                    
                    # Extract media title
                    if 'title' in data:
                        info['media_title'] = data['title']
                else:
                    # Fallback to web scraping
                    title_element = soup.find('meta', property='og:title')
                    if title_element:
                        info['media_title'] = title_element.get('content', '')
                    info['account'] = 'Daily Motion'
            except Exception as e:
                print(f"Error extracting Daily Motion info: {e}")
        
        else:
            # Generic extraction for other platforms
            try:
                title_element = soup.find('meta', property='og:title')
                if title_element:
                    info['media_title'] = title_element.get('content', '')
                
                # Try to extract account from various meta tags
                account_selectors = [
                    ('meta', {'name': 'author'}),
                    ('meta', {'property': 'og:author'}),
                    ('meta', {'name': 'channel'})
                ]
                
                for tag, attrs in account_selectors:
                    element = soup.find(tag, attrs)
                    if element and element.get('content'):
                        info['account'] = element.get('content')
                        break
            except Exception as e:
                print(f"Error extracting generic info: {e}")
    
    except Exception as e:
        print(f"Error extracting info for {platform}: {e}")
    
    return info

def process_url_batch(batch_data):
    """Process a batch of URLs"""
    batch_id, urls = batch_data
    results = []
    
    print(f"Starting batch {batch_id} with {len(urls)} URLs")
    
    for i, row in enumerate(urls):
        try:
            if row['url']:
                print(f"Batch {batch_id}: Processing {i+1}/{len(urls)} - {row['platform']}: {row['url']}")
                
                # Get HTML content
                html = check_url(row['url'])
                
                # Extract information
                info = extract_info(html, row['platform'], row['url'])
                
                # Update row with extracted info
                for key, value in info.items():
                    if key in row:
                        if not row[key]:  # Only fill empty fields
                            row[key] = value
                
                # Add delay to avoid overwhelming servers
                time.sleep(1)
            
            results.append(row)
            
        except Exception as e:
            print(f"Error processing URL in batch {batch_id}: {e}")
            results.append(row)  # Add original row even if processing failed
    
    print(f"Completed batch {batch_id}")
    return batch_id, results

def split_csv_into_chunks(input_file, chunk_size=100, output_dir="chunks"):
    """Split CSV into smaller chunks"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    chunks = []
    current_chunk = []
    chunk_number = 1
    
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        
        # Ensure all required columns exist
        required_columns = ['platform', 'url', 'account', 'account_id', 'media_title', 'media_length']
        for col in required_columns:
            if col not in header:
                header.append(col)
        
        for row in reader:
            # Ensure all required columns exist in the row
            for col in required_columns:
                if col not in row:
                    row[col] = ''
            current_chunk.append(row)
            
            if len(current_chunk) >= chunk_size:
                # Save chunk
                chunk_file = os.path.join(output_dir, f"chunk_{chunk_number:04d}.csv")
                with open(chunk_file, 'w', newline='', encoding='utf-8-sig') as cf:
                    writer = csv.DictWriter(cf, fieldnames=header)
                    writer.writeheader()
                    writer.writerows(current_chunk)
                
                chunks.append(chunk_file)
                current_chunk = []
                chunk_number += 1
        
        # Save remaining rows
        if current_chunk:
            chunk_file = os.path.join(output_dir, f"chunk_{chunk_number:04d}.csv")
            with open(chunk_file, 'w', newline='', encoding='utf-8-sig') as cf:
                writer = csv.DictWriter(cf, fieldnames=header)
                writer.writeheader()
                writer.writerows(current_chunk)
            
            chunks.append(chunk_file)
    
    return chunks

def process_chunk_file(chunk_file, output_dir="processed_chunks"):
    """Process a single chunk file"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    chunk_id = os.path.basename(chunk_file).split('.')[0]
    output_file = os.path.join(output_dir, f"{chunk_id}_processed.csv")
    
    # Check if already processed
    if os.path.exists(output_file):
        print(f"Chunk {chunk_id} already processed, skipping...")
        return output_file
    
    print(f"Processing chunk: {chunk_file}")
    
    # Read chunk
    with open(chunk_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        rows = list(reader)
    
    # Process URLs in parallel within the chunk
    batch_size = 10  # Process 10 URLs at a time
    batches = []
    
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        batches.append((i // batch_size + 1, batch))
    
    processed_rows = []
    
    # Use ProcessPoolExecutor for parallel processing
    with ProcessPoolExecutor(max_workers=4) as executor:
        future_to_batch = {executor.submit(process_url_batch, batch): batch for batch in batches}
        
        for future in as_completed(future_to_batch):
            batch_id, results = future.result()
            processed_rows.extend(results)
            print(f"Completed batch {batch_id} in chunk {chunk_id}")
    
    # Save processed chunk
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(processed_rows)
    
    print(f"Saved processed chunk: {output_file}")
    return output_file

def combine_processed_chunks(processed_chunks, output_file):
    """Combine all processed chunks into final output file"""
    print(f"Combining {len(processed_chunks)} processed chunks...")
    
    all_data = []
    header = None
    
    for chunk_file in sorted(processed_chunks):
        if os.path.exists(chunk_file):
            with open(chunk_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if header is None:
                    header = reader.fieldnames
                
                for row in reader:
                    all_data.append(row)
    
    # Write combined data
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(all_data)
    
    print(f"Combined data saved to: {output_file}")

def main():
    input_file = "TestLinks.csv"  # Use full file
    output_file = "UpdatedTestLinks.csv"
    chunk_size = 100  # Process 100 URLs per chunk
    
    print(f"Starting parallel processing of {input_file}")
    print(f"Chunk size: {chunk_size} URLs")
    
    # Step 1: Split CSV into chunks
    print("\nStep 1: Splitting CSV into chunks...")
    chunks = split_csv_into_chunks(input_file, chunk_size)
    print(f"Created {len(chunks)} chunks")
    
    # Step 2: Process chunks in parallel
    print("\nStep 2: Processing chunks in parallel...")
    processed_chunks = []
    
    # Use ProcessPoolExecutor for chunk processing
    with ProcessPoolExecutor(max_workers=4) as executor:
        future_to_chunk = {executor.submit(process_chunk_file, chunk): chunk for chunk in chunks}
        
        for future in as_completed(future_to_chunk):
            processed_chunk = future.result()
            processed_chunks.append(processed_chunk)
            print(f"Completed processing chunk: {processed_chunk}")
    
    # Step 3: Combine processed chunks
    print("\nStep 3: Combining processed chunks...")
    combine_processed_chunks(processed_chunks, output_file)
    
    print(f"\nProcessing complete! Results saved to: {output_file}")

if __name__ == "__main__":
    main()
