#!/usr/bin/env python3
"""
Super Memory Efficient Google Sheets Scraper
- Inserts data directly into Google Sheets as it processes each link
- Clears all memory after each link to prevent memory buildup
- Tracks progress via Google Sheets row numbers for easy resume
"""

import os
import sys
import csv
import time
import json
import gc
import requests
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError

# Google Sheets API setup
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class GoogleSheetsScraper:
    def __init__(self, credentials_file, spreadsheet_id, sheet_name="Scraped Data"):
        """
        Initialize the Google Sheets scraper
        
        Args:
            credentials_file: Path to Google service account JSON file
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the worksheet to write to
        """
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.sheet = None
        self.current_row = 2  # Start after header row
        self.headers_written = False
        
        # Initialize Google Sheets connection
        self._init_google_sheets()
        
        # Initialize web driver
        self.driver = None
        
    def _init_google_sheets(self):
        """Initialize Google Sheets connection"""
        try:
            # Load credentials
            creds = Credentials.from_service_account_file(
                self.credentials_file, scopes=SCOPES
            )
            
            # Create client
            client = gspread.authorize(creds)
            
            # Open spreadsheet
            spreadsheet = client.open_by_key(self.spreadsheet_id)
            
            # Get or create worksheet
            try:
                self.sheet = spreadsheet.worksheet(self.sheet_name)
                print(f"✅ Connected to existing worksheet: {self.sheet_name}")
                
                # Get current row count (next row to write to)
                all_values = self.sheet.get_all_values()
                if len(all_values) > 1:  # Has data beyond header
                    self.current_row = len(all_values) + 1
                    print(f"📊 Resuming from row {self.current_row}")
                else:
                    self.current_row = 2
                    print(f"📊 Starting fresh at row {self.current_row}")
                    
            except gspread.WorksheetNotFound:
                # Create new worksheet
                self.sheet = spreadsheet.add_worksheet(
                    title=self.sheet_name, 
                    rows=1000, 
                    cols=10
                )
                print(f"✅ Created new worksheet: {self.sheet_name}")
                self.current_row = 2
                
        except GoogleAuthError as e:
            print(f"❌ Google authentication error: {e}")
            print("Please check your service account credentials file")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error initializing Google Sheets: {e}")
            sys.exit(1)
    
    def _write_headers(self):
        """Write headers to Google Sheets if not already written"""
        if not self.headers_written:
            headers = ['platform', 'url', 'account', 'account_id', 'media_title', 'media_length', 'processed_at']
            self.sheet.update('A1:G1', [headers])
            self.headers_written = True
            print("📋 Headers written to Google Sheets")
    
    def _insert_row(self, data):
        """Insert a single row of data into Google Sheets"""
        try:
            # Ensure headers are written
            self._write_headers()
            
            # Prepare row data
            row_data = [
                data.get('platform', ''),
                data.get('url', ''),
                data.get('account', ''),
                data.get('account_id', ''),
                data.get('media_title', ''),
                data.get('media_length', ''),
                time.strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            # Insert row
            range_name = f'A{self.current_row}:G{self.current_row}'
            self.sheet.update(range_name, [row_data])
            
            print(f"✅ Row {self.current_row}: {data.get('platform', 'Unknown')} - {data.get('url', '')[:50]}...")
            
            # Increment row counter
            self.current_row += 1
            
            return True
            
        except Exception as e:
            print(f"❌ Error inserting row {self.current_row}: {e}")
            return False
    
    def _init_driver(self):
        """Initialize Chrome driver with anti-detection measures"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--memory-pressure-off")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

        # Use system-installed Chrome and ChromeDriver
        print("🔧 Initializing Chrome driver...")
        
        # Use system Chrome binary
        chrome_bin = "/nix/var/nix/profiles/default/bin/chromium"
        if os.path.exists(chrome_bin):
            options.binary_location = chrome_bin
            print(f"Using Chrome binary: {chrome_bin}")
        
        # Use system ChromeDriver
        chromedriver_path = "/nix/var/nix/profiles/default/bin/chromedriver"
        if not os.path.exists(chromedriver_path):
            print("System ChromeDriver not found, falling back to webdriver-manager")
            base_path = ChromeDriverManager().install()
            chromedriver_dir = os.path.dirname(base_path)
            chromedriver_path = os.path.join(chromedriver_dir, "chromedriver")

        self.driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
        self.driver.set_page_load_timeout(120)
        
        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return self.driver
    
    def _check_url(self, url):
        """Check if URL is accessible and return HTML content"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if not self.driver:
                    self._init_driver()
                
                self.driver.get(url)
                time.sleep(2)  # Brief wait for page load
                html = self.driver.page_source
                
                return html
                
            except Exception as e:
                print(f"Error checking URL {url} (attempt {attempt + 1}/{max_retries}): {e}")
                
                # Reset driver on error
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                
                if attempt < max_retries - 1:
                    time.sleep(3)  # Wait before retry
                else:
                    print(f"Failed to process URL {url} after {max_retries} attempts")
                    return None
        
        return None
    
    def _extract_info(self, html, platform, url):
        """Extract information from HTML content"""
        info = {'account': '', 'account_id': '', 'media_title': '', 'media_length': ''}
        
        if not html:
            return info
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            if platform == 'YouTube':
                # YouTube extraction logic
                try:
                    # Extract title from meta tags
                    title_element = soup.find('meta', property='og:title')
                    if title_element:
                        info['media_title'] = title_element.get('content', '')
                    
                    # Extract duration from meta tags
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
    
    def _clear_memory(self):
        """Clear all memory associated with the current link"""
        try:
            # Clear BeautifulSoup objects
            if 'soup' in locals():
                del soup
            
            # Clear HTML content
            if 'html' in locals():
                del html
            
            # Clear extracted info
            if 'info' in locals():
                del info
            
            # Force garbage collection
            gc.collect()
            
        except Exception as e:
            print(f"Warning: Error clearing memory: {e}")
    
    def process_single_url(self, row):
        """Process a single URL and insert directly into Google Sheets"""
        try:
            # Validate row structure
            if not isinstance(row, dict):
                print(f"❌ Invalid row format")
                return False
                
            if not row.get('url'):
                print(f"❌ No URL found in row")
                return False
            
            platform = row.get('platform', 'Unknown')
            url = row['url']
            
            print(f"🔄 Processing: {platform} - {url}")
            
            # Get HTML content
            html = self._check_url(url)
            
            # Extract information
            info = self._extract_info(html, platform, url)
            
            # Update row with extracted info
            for key, value in info.items():
                if key in row:
                    if not row[key]:  # Only fill empty fields
                        row[key] = value
            
            # Insert into Google Sheets
            success = self._insert_row(row)
            
            # Clear all memory immediately after processing
            self._clear_memory()
            
            return success
            
        except Exception as e:
            print(f"❌ Error processing URL: {e}")
            # Still try to insert the original row
            try:
                self._insert_row(row)
            except:
                pass
            return False
    
    def process_csv_file(self, input_file, start_row=None):
        """
        Process CSV file and insert data directly into Google Sheets
        
        Args:
            input_file: Path to CSV file
            start_row: Row number to start from (for resume functionality)
        """
        print(f"🚀 Starting processing of {input_file}")
        
        if start_row:
            print(f"📍 Resuming from row {start_row}")
        
        try:
            with open(input_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            total_rows = len(rows)
            print(f"📊 Total rows to process: {total_rows}")
            
            # Determine start index
            start_index = 0
            if start_row and start_row > 2:  # Account for header row
                start_index = start_row - 2  # Convert to 0-based index
            
            processed_count = 0
            success_count = 0
            
            for i in range(start_index, total_rows):
                row = rows[i]
                processed_count += 1
                
                print(f"\n📈 Progress: {processed_count}/{total_rows} ({(processed_count/total_rows)*100:.1f}%)")
                
                # Process the URL
                if self.process_single_url(row):
                    success_count += 1
                
                # Add delay to avoid overwhelming servers
                time.sleep(5)
                
                # Periodic status update
                if processed_count % 10 == 0:
                    print(f"📊 Status: {success_count}/{processed_count} successful")
            
            print(f"\n✅ Processing complete!")
            print(f"📊 Final stats: {success_count}/{total_rows} successful")
            print(f"📊 Current Google Sheets row: {self.current_row}")
            
        except Exception as e:
            print(f"❌ Error processing CSV file: {e}")
            print(f"📊 Progress saved up to row {self.current_row}")
    
    def get_current_progress(self):
        """Get current progress information"""
        try:
            all_values = self.sheet.get_all_values()
            total_rows = len(all_values)
            
            print(f"📊 Google Sheets Progress:")
            print(f"   Total rows: {total_rows}")
            print(f"   Next row to write: {self.current_row}")
            print(f"   Data rows (excluding header): {total_rows - 1}")
            
            return total_rows
            
        except Exception as e:
            print(f"❌ Error getting progress: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            print("🧹 Cleanup completed")
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")

def main():
    # Configuration
    CREDENTIALS_FILE = "google-credentials.json"  # You need to create this
    SPREADSHEET_ID = "your-spreadsheet-id"  # Replace with your spreadsheet ID
    SHEET_NAME = "Scraped Data"
    INPUT_FILE = "TestLinks.csv"
    
    print("🚀 Super Memory Efficient Google Sheets Scraper")
    print("=" * 50)
    
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Credentials file not found: {CREDENTIALS_FILE}")
        print("\n📋 Setup Instructions:")
        print("1. Go to Google Cloud Console")
        print("2. Create a new project or select existing")
        print("3. Enable Google Sheets API and Google Drive API")
        print("4. Create a Service Account")
        print("5. Download the JSON credentials file")
        print("6. Rename it to 'google-credentials.json'")
        print("7. Share your Google Sheet with the service account email")
        print("8. Update SPREADSHEET_ID in this script")
        return
    
    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return
    
    # Initialize scraper
    scraper = None
    try:
        scraper = GoogleSheetsScraper(CREDENTIALS_FILE, SPREADSHEET_ID, SHEET_NAME)
        
        # Check current progress
        scraper.get_current_progress()
        
        # Process the file
        scraper.process_csv_file(INPUT_FILE)
        
    except KeyboardInterrupt:
        print("\n⏹️ Processing interrupted by user")
        print(f"📊 Progress saved up to row {scraper.current_row if scraper else 'unknown'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"📊 Progress saved up to row {scraper.current_row if scraper else 'unknown'}")
        
    finally:
        if scraper:
            scraper.cleanup()

if __name__ == "__main__":
    main()
