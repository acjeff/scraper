#!/usr/bin/env python3
"""
Railway-Optimized Parallel URL Scraper
Designed for Railway.app deployment with resource constraints
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging

# Set up logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('railway_scraper.log'),
        logging.StreamHandler()
    ]
)

def init_driver():
    """Initialize Chrome driver optimized for Railway environment"""
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
    options.add_argument("--disable-javascript")  # If not needed
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
    
    # Use webdriver-manager for Railway (no system Chrome)
    service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)  # Shorter timeout for Railway
    driver.set_script_timeout(15)
    
    # Remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def check_url(url):
    """Check if URL is accessible and return HTML content"""
    driver = None
    try:
        driver = init_driver()
        logging.info(f"Processing URL: {url}")
        
        driver.get(url)
        time.sleep(0.5)  # Minimal wait time
        
        html = driver.page_source
        return html
        
    except Exception as e:
        logging.error(f"Error checking URL {url}: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def extract_info(html, platform, url):
    """Extract information from HTML content"""
    info = {'account': '', 'account_id': '', 'media_title': '', 'media_length': ''}
    
    if not html:
        return info
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Your existing extraction logic here
        # (Copy from your original parallel_scraper.py)
        
        return info
        
    except Exception as e:
        logging.error(f"Error extracting info from {url}: {e}")
        return info

def process_url(row):
    """Process a single URL and return results"""
    try:
        url = row['URL']
        platform = row.get('Platform', 'Unknown')
        
        # Parse URL to determine platform if not specified
        if platform == 'Unknown':
            domain = urlparse(url).netloc.lower()
            if 'youtube.com' in domain or 'youtu.be' in domain:
                platform = 'YouTube'
            elif 'dailymotion.com' in domain:
                platform = 'Dailymotion'
            elif 'vimeo.com' in domain:
                platform = 'Vimeo'
        
        # Get HTML content
        html = check_url(url)
        
        # Extract information
        info = extract_info(html, platform, url)
        
        # Combine with original row
        result = row.copy()
        result.update(info)
        
        logging.info(f"Successfully processed: {url}")
        return result
        
    except Exception as e:
        logging.error(f"Error processing URL {row.get('URL', 'Unknown')}: {e}")
        return row

def main():
    """Main function optimized for Railway"""
    logging.info("🚂 Starting Railway-Optimized Parallel Scraper...")
    
    # Check if TestLinks.csv exists
    if not os.path.exists('TestLinks.csv'):
        logging.error("❌ TestLinks.csv not found!")
        return
    
    # Create directories
    os.makedirs('chunks', exist_ok=True)
    os.makedirs('processed_chunks', exist_ok=True)
    
    # Your existing main logic here
    # (Copy from your original parallel_scraper.py)
    
    logging.info("✅ Processing complete!")

if __name__ == "__main__":
    main()
