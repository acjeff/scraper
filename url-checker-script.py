"""
URL Checker and Scraper Script

Before running this script, make sure to install the required libraries:
    pip install requests beautifulsoup4

Usage:
    python script_name.py

This script processes a CSV file containing URLs, checks each URL,
and attempts to scrape relevant information from the web pages.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from urllib.parse import unquote, urlparse, parse_qs  # Import the required functions
import csv
import time
import json
import os
from bs4 import BeautifulSoup
import time
driver = None  # Initialize globally

def init_driver():
    global driver
    if driver is None:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-web-security")
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")

        # Enable browser logging
        # Enable browser logging
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        driver.set_page_load_timeout(120)

def quit_driver():
    global driver
    if driver is not None:
        driver.quit()
        driver = None

def check_url(url):
    global driver
    try:
        driver.get(url)
        
        # Wait for the body element to ensure the page has loaded
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get the page source
        html = driver.page_source
        return html
    except Exception as e:
        print(f"Error loading {url}: {str(e)}")
        return None

def extract_artist_name(title):
    # Split the string by the '·' character
    parts = title.split('·')
    
    # Check if we have at least 3 parts (before, artist, after)
    if len(parts) >= 3:
        # Return the stripped second part (index 1)
        return parts[1].strip()
    else:
        # Return None or an error message if the format is unexpected
        return None
    
def has_focused_class(tag):
    return tag.name == 'music-text-row' and 'focused' in tag.get('class', [])

def extract_info(html, platform, url):
    if html:
        soup = BeautifulSoup(html, 'html.parser')
    info = {'account': ''}

    try:
        if platform == 'YouTube':
            try:    

                # Wait for the page to load
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))  # Wait for the body to load
                )

                # Get the current URL
                current_url = driver.current_url
                print(f"Current URL: {current_url}")

                # Check if the redirect URL is a consent screen
                if "consent.youtube.com" in current_url:
                    print("Detected YouTube consent screen. Extracting 'continue' URL...")
                    # Extract the `continue` parameter
                    parsed_url = urlparse(current_url)
                    query_params = parse_qs(parsed_url.query)
                    continue_url = query_params.get("continue", [None])[0]

                    if continue_url:
                        print(f"Redirecting to: {continue_url}")
                        driver.get(continue_url)
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                    else:
                        raise Exception("Failed to extract 'continue' URL from consent screen.")

                # After handling consent or if no consent screen, process the page
                redirected_url = driver.current_url
                print(f"Final URL after consent (if applicable): {redirected_url}")

                # Check if the URL contains a channel ID
                if "youtube.com/channel/" in redirected_url:
                    channel_id = redirected_url.split("/channel/")[-1].split("/")[0]
                    print(f"Extracted Channel ID from URL: {channel_id}")
                else:
                    print("URL does not point directly to a channel. Proceeding to extract from page metadata...")

                    # Wait for the <span> with itemprop="author" to be present
                    author_span = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "span[itemprop='author']"))
                    )

                    # Find the <link> elements inside the <span>
                    url_link = author_span.find_element(By.CSS_SELECTOR, "link[itemprop='url']")
                    name_link = author_span.find_element(By.CSS_SELECTOR, "link[itemprop='name']")

                    # Extract the channel ID from the href attribute of the URL link
                    channel_url = url_link.get_attribute("href")
                    channel_id = channel_url.split("/")[-1]  # Extract the last part of the URL
                    print(f"Extracted Channel ID: {channel_id}")

                    # Extract the channel name from the content attribute of the name link
                    channel_name = name_link.get_attribute("content")
                    print(f"Extracted Channel Name: {channel_name}")

                # Set info['account'] to the name and ID separated by a space
                info['account'] = f"{channel_name} {channel_id}"
                print(f"Set info['account']: {info['account']}")

            except Exception as e:
                print(f"An error occurred: {e}")
            
        elif platform == 'Spotify':
            if 'track' in url or 'artist' in url:
                return info
            try:
                # Wait for the <meta> element containing the Spotify artist URL
                artist_meta = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "meta[name='music:musician']"))
                )
                # Extract the content attribute for the artist URL
                artist_url = artist_meta.get_attribute('content')
                artist_id = artist_url.split('/')[-1]  # Extract the artist ID from the URL
                print(f"Extracted Artist ID: {artist_id}")

                # Wait for the <meta> element containing the description
                description_meta = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "meta[name='description']"))
                )
                # Extract the content attribute for the description
                description_content = description_meta.get_attribute('content')

                # Extract the artist name (e.g., "Peppa Pig") from the description
                artist_name = description_content.split('·')[2].strip()  # Split by "·" and get the 3rd element
                print(f"Extracted Artist Name: {artist_name}")

                # Set info['account'] to be the artist name and ID separated by a space
                info['account'] = f"{artist_name} {artist_id}"
                print(f"Set info['account']: {info['account']}")

            except Exception as e:
                print(f"An error occurred: {e}")

        elif platform == 'Soundcloud':
            parts = url.split('/')
            if len(parts) > 4:
                extracted_string = parts[3]
                info['account'] = extracted_string
                print(f"Extracted string: {extracted_string}")
            else:
                print("The URL does not have enough parts to extract the string.")

        elif platform == 'Facebook':
            try:
                # Wait for all <a> elements to be present on the page
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
                )

                # Find all <a> elements on the page
                elements = driver.find_elements(By.TAG_NAME, "a")

                # Loop through the elements and process those with matching href
                for element in elements:
                    href = element.get_attribute('href')  # Get the href attribute

                    if href and href.startswith('https://www.facebook.com/people/'):
                        href = unquote(href)  # Decode the URL
                        info['account'] = href.replace("https://www.facebook.com/people/", "").split('/')[0]
                        print(f"Extracted account: {info['account']}")  # Debugging output

            except Exception as e:
                print(f"An error occurred: {e}")    

        elif platform == 'Daily Motion':
            try:
                # Wait for the <a> element with a class containing 'channelLink' to be present
                a_tag = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[class*='channelLink']"))
                )

                # Check if the 'href' attribute is present
                href = a_tag.get_attribute('href')
                if href:
                    print(f"Found href: {href}")
                    info['account'] = href
                else:
                    print("The <a> tag does not have an href attribute.")

            except Exception as e:
                print(f"Error: {e}")
        elif platform == 'Apple':
            elements = soup.find_all('a', href=lambda href: href and href.startswith('https://music.apple.com/us/artist/'))
    
            # Extract and print the href and text content
            for element in elements:
                href = element['href']
                info['account'] = href.replace("https://music.apple.com/us/artist/", "/")
                
        elif platform == 'TikTok':
            parts = url.split('/')
            if len(parts) > 4:
                extracted_string = parts[3]
                info['account'] = extracted_string
                print(f"Extracted string: {extracted_string}")
            else:
                print("The URL does not have enough parts to extract the string.")
                
        elif platform == 'Amazon':
            
            try:
                print("Starting search for target URL in <script> elements...")

                target_url = None  # To store the URL if found
                start_time = time.time()

                while time.time() - start_time < 20:  # Retry for up to 20 seconds
                    # Get all <script> elements with type="application/ld+json"
                    script_elements = driver.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")

                    print(f"Found {len(script_elements)} <script> elements with type='application/ld+json'.")

                    # Loop through each <script> element
                    for index, script in enumerate(script_elements):
                        try:
                            # Extract the inner JSON content
                            raw_json = script.get_attribute("innerHTML")
                            print(f"Processing <script> element {index + 1}...")

                            # Log the raw JSON for debugging
                            # print(f"Raw JSON content:\n{raw_json}")

                            # Parse the JSON content
                            parsed_json = json.loads(raw_json)
                            # print(f"Parsed JSON content: {json.dumps(parsed_json, indent=4)}")

                            # Check if the JSON contains the desired "url"
                            if "byArtist" in parsed_json and "url" in parsed_json["byArtist"]:
                                target_url = parsed_json["byArtist"]["url"]
                                # print(f"Found target URL: {target_url}")
                                break  # Stop searching once we find the desired URL

                        except json.JSONDecodeError as e:
                            print(f"Skipping <script> element {index + 1}: Invalid JSON. Error: {e}")

                    if target_url:
                        break  # Exit the outer loop if the target URL is found

                    # Wait briefly before retrying
                    print("Target URL not found. Retrying...")
                    time.sleep(1)

                # Handle case where the target URL is not found
                if target_url:
                    print(f"Extracted URL: {target_url}")
                    info['account'] = target_url.replace("https://music.amazon.com/artists/", "")
                else:
                    print("No <script> element contained the desired URL after 20 seconds.")

            except Exception as e:
                print(f"An error occurred: {e}")
                    
        else:
            title = soup.find('meta', property='og:title')
            info['account'] = title['content'] if title else ''

        # Add more platform-specific scraping logic here
    except Exception as e:
        print(f"Error extracting info for {platform}: {str(e)}")
    
    print(f"Account: {info}")
    return info

def process_csv(input_file, output_file):
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
             open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                if row['url']:
                    print(f"Processing: {row['url']}")
                    noWebNeeded = row['platform'] in ['Soundcloud', 'TikTok']  # Simplified the condition

                    if not noWebNeeded:  # If web interaction is needed
                        html = check_url(row['url'])
                        if html:
                            info = extract_info(html, row['platform'], row['url'])
                    else:  # If no web interaction is needed
                        info = extract_info(None, row['platform'], row['url'])
                        
                    for key, value in info.items():
                            if not row[key]:  # Only fill empty fields
                                row[key] = value    
                    time.sleep(1)  # Add a delay to avoid overwhelming the servers
                
                writer.writerow(row)
        
        print("Processing complete. Check the output file.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the input and output file paths
    input_file = os.path.join(current_dir, "TestLinks.csv")
    output_file = os.path.join(current_dir, "UpdatedTestLinks.csv")

    # Initialize the driver
    init_driver()
    
    try:
        # Process the CSV
        process_csv(input_file, output_file)
    finally:
        # Quit the driver after processing
        quit_driver()