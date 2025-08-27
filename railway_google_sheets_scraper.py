#!/usr/bin/env python3
"""
Railway-Optimized Google Sheets Scraper
Designed for Railway.app deployment with proper environment handling
"""

import os
import sys
import csv
import time
import json
import gc
import requests
import logging
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

# Set up logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('railway_google_sheets.log'),
        logging.StreamHandler()
    ]
)

# Google Sheets API setup
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class RailwayGoogleSheetsScraper:
    def __init__(self, sheet_name="Scraped Data"):
        """
        Initialize the Railway-optimized Google Sheets scraper
        
        Args:
            sheet_name: Name of the worksheet to write to
        """
        self.sheet_name = sheet_name
        self.sheet = None
        self.current_row = 2  # Start after header row
        self.headers_written = False
        
        # Get configuration from environment variables (Railway way)
        self.credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        self.input_spreadsheet_id = os.getenv('GOOGLE_INPUT_SPREADSHEET_ID')
        self.output_spreadsheet_id = os.getenv('GOOGLE_OUTPUT_SPREADSHEET_ID')
        
        if not self.credentials_json:
            logging.error("GOOGLE_CREDENTIALS_JSON environment variable not set")
            sys.exit(1)
            
        if not self.input_spreadsheet_id:
            logging.error("GOOGLE_INPUT_SPREADSHEET_ID environment variable not set")
            sys.exit(1)
            
        if not self.output_spreadsheet_id:
            logging.error("GOOGLE_OUTPUT_SPREADSHEET_ID environment variable not set")
            sys.exit(1)
        
        # Initialize Google Sheets connection
        self._init_google_sheets()
        
        # Initialize web driver
        self.driver = None
        
    def _init_google_sheets(self):
        """Initialize Google Sheets connection using environment variables"""
        try:
            # Parse credentials from JSON string (Railway environment variable)
            import json
            creds_dict = json.loads(self.credentials_json)
            
            # Create credentials from dictionary
            creds = Credentials.from_service_account_info(
                creds_dict, scopes=SCOPES
            )
            
            # Create client
            self.client = gspread.authorize(creds)
            
            # Initialize input and output sheets
            self._init_input_sheet()
            self._init_output_sheet()
                
        except GoogleAuthError as e:
            logging.error(f"❌ Google authentication error: {e}")
            logging.error("Please check your GOOGLE_CREDENTIALS_JSON environment variable")
            sys.exit(1)
        except Exception as e:
            logging.error(f"❌ Error initializing Google Sheets: {e}")
            sys.exit(1)
    
    def _init_input_sheet(self):
        """Initialize connection to input Google Sheet"""
        try:
            # Open input spreadsheet
            input_spreadsheet = self.client.open_by_key(self.input_spreadsheet_id)
            
            # Get the first worksheet (or specify by name if needed)
            self.input_sheet = input_spreadsheet.sheet1
            logging.info(f"✅ Connected to input sheet: {input_spreadsheet.title}")
            
        except Exception as e:
            logging.error(f"❌ Error connecting to input sheet: {e}")
            sys.exit(1)
    
    def _init_output_sheet(self):
        """Initialize connection to output Google Sheet"""
        try:
            # Open output spreadsheet
            output_spreadsheet = self.client.open_by_key(self.output_spreadsheet_id)
            
            # Get or create worksheet
            try:
                self.output_sheet = output_spreadsheet.worksheet(self.sheet_name)
                logging.info(f"✅ Connected to existing output worksheet: {self.sheet_name}")
                
            except gspread.WorksheetNotFound:
                # Create new worksheet
                self.output_sheet = output_spreadsheet.add_worksheet(
                    title=self.sheet_name, 
                    rows=1000, 
                    cols=10
                )
                logging.info(f"✅ Created new output worksheet: {self.sheet_name}")
                
            # Calculate resume position based on output sheet content
            self._calculate_resume_position()
                
        except Exception as e:
            logging.error(f"❌ Error connecting to output sheet: {e}")
            sys.exit(1)
    
    def _calculate_resume_position(self):
        """Calculate where to resume processing based on output sheet content"""
        try:
            all_values = self.output_sheet.get_all_values()
            
            if len(all_values) <= 1:  # Only header or empty
                self.current_row = 2
                self.resume_index = 0
                logging.info(f"📊 Starting fresh - output sheet is empty")
                return
            
            # Count processed rows (excluding header)
            processed_rows = len(all_values) - 1
            self.current_row = len(all_values) + 1
            
            # Get input sheet data to determine total rows
            input_values = self.input_sheet.get_all_values()
            total_input_rows = len(input_values) - 1  # Exclude header
            
            if processed_rows >= total_input_rows:
                logging.info(f"📊 All {total_input_rows} rows already processed!")
                self.resume_index = total_input_rows
                return
            
            # Resume from the next unprocessed row
            self.resume_index = processed_rows
            
            logging.info(f"📊 Resume calculation:")
            logging.info(f"   Output sheet has {processed_rows} processed rows")
            logging.info(f"   Input sheet has {total_input_rows} total rows")
            logging.info(f"   Resuming from input row {self.resume_index + 1} (index {self.resume_index})")
            logging.info(f"   Next output row will be {self.current_row}")
            
        except Exception as e:
            logging.error(f"❌ Error calculating resume position: {e}")
            # Fallback to starting fresh
            self.current_row = 2
            self.resume_index = 0
    
    def _write_headers(self):
        """Write headers to Google Sheets if not already written"""
        if not self.headers_written:
            headers = ['platform', 'url', 'account', 'account_id', 'media_title', 'media_length', 'processed_at']
            self.output_sheet.update('A1:G1', [headers])
            self.headers_written = True
            logging.info("📋 Headers written to output Google Sheet")
    
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
            self.output_sheet.update(range_name, [row_data])
            
            logging.info(f"✅ Row {self.current_row}: {data.get('platform', 'Unknown')} - {data.get('url', '')[:50]}...")
            
            # Increment row counter
            self.current_row += 1
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error inserting row {self.current_row}: {e}")
            return False
    
    def _init_driver(self):
        """Initialize Chrome driver optimized for Railway environment"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
        
        options = Options()
        
        # Railway-optimized Chrome options (memory efficient)
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Save memory
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=512")  # Limit memory usage
        options.add_argument("--single-process")  # Use single process
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        
        # User agent for Railway
        options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
        
        # Anti-detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Use system Chrome/Chromedriver on Railway (installed via Nixpacks)
        chrome_bin = os.getenv('CHROME_BIN', 'chromium')
        chromedriver_path = os.getenv('CHROMEDRIVER_PATH', 'chromedriver')
        
        if os.path.exists(chrome_bin):
            options.binary_location = chrome_bin
            logging.info(f"Using Chrome binary: {chrome_bin}")
        
        if os.path.exists(chromedriver_path):
            logging.info(f"Using system ChromeDriver: {chromedriver_path}")
            service = Service(chromedriver_path)
        else:
            logging.info("System ChromeDriver not found, using webdriver-manager")
            service = Service(ChromeDriverManager().install())

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(30)  # Shorter timeout for Railway
        self.driver.set_script_timeout(15)
        
        # Remove webdriver property
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
                time.sleep(0.5)  # Minimal wait time for Railway
                html = self.driver.page_source
                
                return html
                
            except Exception as e:
                logging.error(f"Error checking URL {url} (attempt {attempt + 1}/{max_retries}): {e}")
                
                # Reset driver on error
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
                else:
                    logging.error(f"Failed to process URL {url} after {max_retries} attempts")
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
                    logging.error(f"Error extracting YouTube info: {e}")
            
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
                    logging.error(f"Error extracting TikTok info: {e}")
            
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
                    logging.error(f"Error extracting Soundcloud info: {e}")
            
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
                    logging.error(f"Error extracting Daily Motion info: {e}")
            
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
                    logging.error(f"Error extracting generic info: {e}")
        
        except Exception as e:
            logging.error(f"Error extracting info for {platform}: {e}")
        
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
            logging.warning(f"Warning: Error clearing memory: {e}")
    
    def process_single_url(self, row):
        """Process a single URL and insert directly into Google Sheets"""
        try:
            # Validate row structure
            if not isinstance(row, dict):
                logging.error(f"❌ Invalid row format")
                return False
                
            if not row.get('url'):
                logging.error(f"❌ No URL found in row")
                return False
            
            platform = row.get('platform', 'Unknown')
            url = row['url']
            
            logging.info(f"🔄 Processing: {platform} - {url}")
            
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
            logging.error(f"❌ Error processing URL: {e}")
            # Still try to insert the original row
            try:
                self._insert_row(row)
            except:
                pass
            return False
    
    def process_google_sheet(self):
        """
        Process Google Sheet and insert data directly into output Google Sheet
        Automatically resumes from where it left off based on output sheet content
        """
        logging.info(f"🚀 Starting processing of input Google Sheet")
        
        try:
            # Get all data from input sheet
            all_values = self.input_sheet.get_all_values()
            
            if len(all_values) < 2:  # Only header or empty
                logging.error("❌ Input sheet is empty or has no data rows")
                return
            
            # Convert to list of dictionaries
            headers = all_values[0]
            rows = []
            for row_values in all_values[1:]:  # Skip header
                # Pad row if it's shorter than headers
                while len(row_values) < len(headers):
                    row_values.append('')
                row_dict = dict(zip(headers, row_values))
                rows.append(row_dict)
            
            total_rows = len(rows)
            
            # Check if all rows are already processed
            if self.resume_index >= total_rows:
                logging.info(f"✅ All {total_rows} rows have already been processed!")
                return
            
            remaining_rows = total_rows - self.resume_index
            logging.info(f"📊 Processing {remaining_rows} remaining rows out of {total_rows} total")
            
            processed_count = 0
            success_count = 0
            
            # Process from resume_index onwards
            for i in range(self.resume_index, total_rows):
                row = rows[i]
                processed_count += 1
                current_progress = i + 1  # 1-based for display
                
                logging.info(f"📈 Progress: {current_progress}/{total_rows} ({(current_progress/total_rows)*100:.1f}%)")
                
                # Process the URL
                if self.process_single_url(row):
                    success_count += 1
                
                # Add delay to avoid overwhelming servers (shorter for Railway)
                time.sleep(3)
                
                # Periodic status update
                if processed_count % 10 == 0:
                    logging.info(f"📊 Status: {success_count}/{processed_count} successful in this session")
            
            logging.info(f"✅ Processing complete!")
            logging.info(f"📊 Final stats: {success_count}/{processed_count} successful in this session")
            logging.info(f"📊 Current output Google Sheets row: {self.current_row}")
            
        except Exception as e:
            logging.error(f"❌ Error processing Google Sheet: {e}")
            logging.info(f"📊 Progress saved up to row {self.current_row}")
    
    def get_current_progress(self):
        """Get current progress information"""
        try:
            # Get input sheet info
            input_values = self.input_sheet.get_all_values()
            input_total_rows = len(input_values)
            input_data_rows = input_total_rows - 1 if input_total_rows > 0 else 0
            
            # Get output sheet info
            output_values = self.output_sheet.get_all_values()
            output_total_rows = len(output_values)
            output_data_rows = output_total_rows - 1 if output_total_rows > 0 else 0
            
            # Calculate remaining rows
            remaining_rows = max(0, input_data_rows - output_data_rows)
            
            logging.info(f"📊 Google Sheets Progress:")
            logging.info(f"   Input sheet: {input_data_rows} data rows")
            logging.info(f"   Output sheet: {output_data_rows} processed rows")
            logging.info(f"   Remaining: {remaining_rows} rows")
            logging.info(f"   Next row to write: {self.current_row}")
            
            if remaining_rows == 0:
                logging.info(f"   ✅ All rows have been processed!")
            else:
                logging.info(f"   🔄 Will resume from input row {output_data_rows + 1}")
            
            return output_total_rows
            
        except Exception as e:
            logging.error(f"❌ Error getting progress: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            logging.info("🧹 Cleanup completed")
        except Exception as e:
            logging.warning(f"Warning: Error during cleanup: {e}")

def main():
    # Configuration for Railway
    SHEET_NAME = "Scraped Data"
    
    logging.info("🚀 Railway-Optimized Google Sheets Scraper")
    logging.info("=" * 50)
    
    # Initialize scraper
    scraper = None
    try:
        scraper = RailwayGoogleSheetsScraper(SHEET_NAME)
        
        # Check current progress and show resume information
        scraper.get_current_progress()
        
        # Process the Google Sheet (automatically resumes from where it left off)
        scraper.process_google_sheet()
        
    except KeyboardInterrupt:
        logging.info("⏹️ Processing interrupted by user")
        logging.info(f"📊 Progress saved - will resume automatically on next run")
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        logging.info(f"📊 Progress saved - will resume automatically on next run")
        
    finally:
        if scraper:
            scraper.cleanup()

if __name__ == "__main__":
    main()
