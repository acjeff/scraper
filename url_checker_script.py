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

        # Get the correct chromedriver path - use the actual executable
        base_path = ChromeDriverManager().install()
        chromedriver_dir = os.path.dirname(base_path)
        chromedriver_path = os.path.join(chromedriver_dir, "chromedriver")
        
        driver = webdriver.Chrome(
            service=Service(chromedriver_path),
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

def extract_info(html, platform, url, driver=None):
    if html:
        soup = BeautifulSoup(html, 'html.parser')
    info = {'account': '', 'account_id': '', 'media_title': '', 'media_length': ''}

    try:
        if platform == 'YouTube':
            if not driver:
                print("Error: Driver is required for YouTube extraction")
                return info
                
            try:    
                # Wait for the page to load
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))  # Wait for the body to load
                )
                
                # Extract media title
                try:
                    title_element = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
                    if title_element:
                        info['media_title'] = title_element.get_attribute('content')
                        print(f"Extracted title from og:title: {info['media_title']}")
                except Exception as e:
                    print(f"Failed to extract title from og:title: {e}")
                    try:
                        title_element = driver.find_element(By.CSS_SELECTOR, 'h1.ytd-video-primary-info-renderer')
                        if title_element:
                            info['media_title'] = title_element.text
                            print(f"Extracted title from h1: {info['media_title']}")
                    except Exception as e2:
                        print(f"Failed to extract title from h1: {e2}")
                        pass
                
                # Extract media length
                try:
                    length_element = driver.find_element(By.CSS_SELECTOR, 'span.ytp-time-duration')
                    if length_element:
                        info['media_length'] = length_element.text
                        print(f"Extracted length from span: {info['media_length']}")
                except Exception as e:
                    print(f"Failed to extract length from span: {e}")
                    try:
                        # Alternative method for length
                        length_element = driver.find_element(By.CSS_SELECTOR, 'meta[itemprop="duration"]')
                        if length_element:
                            duration = length_element.get_attribute('content')
                            print(f"Extracted duration from meta: {duration}")
                            # Convert ISO 8601 duration to readable format
                            if duration.startswith('PT'):
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
                                print(f"Converted duration to: {info['media_length']}")
                    except Exception as e2:
                        print(f"Failed to extract length from meta: {e2}")
                        pass

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
                    # Try to get channel name from page title or other elements
                    try:
                        channel_name_element = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:site_name"]')
                        if channel_name_element:
                            info['account'] = channel_name_element.get_attribute('content')
                        else:
                            info['account'] = "YouTube Channel"
                    except:
                        info['account'] = "YouTube Channel"
                else:
                    print("URL does not point directly to a channel. Proceeding to extract from page metadata...")

                    try:
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
                        info['account'] = channel_name
                        info['account_id'] = channel_id
                        print(f"Set info['account']: {info['account']}")
                    except Exception as e:
                        print(f"Failed to extract channel info from metadata: {e}")
                        # Fallback: try to extract from video page
                        try:
                            # For video pages, try to get channel info from video metadata
                            channel_link = driver.find_element(By.CSS_SELECTOR, 'a[href*="/channel/"]')
                            if channel_link:
                                channel_url = channel_link.get_attribute('href')
                                channel_id = channel_url.split("/channel/")[-1].split("/")[0]
                                info['account_id'] = channel_id
                                
                                # Try to get channel name from the link text
                                channel_name = channel_link.text.strip()
                                if channel_name:
                                    info['account'] = channel_name
                                else:
                                    info['account'] = f"YouTube Channel {channel_id}"
                                print(f"Fallback extraction - Channel: {info['account']}, ID: {info['account_id']}")
                        except Exception as e2:
                            print(f"Fallback extraction also failed: {e2}")
                            info['account'] = "Unknown YouTube Channel"
                            info['account_id'] = "unknown"

            except Exception as e:
                print(f"An error occurred during YouTube extraction: {e}")
                import traceback
                traceback.print_exc()
            
        elif platform == 'Spotify':
            if 'track' in url or 'artist' in url:
                return info
            if not driver:
                print("Error: Driver is required for Spotify extraction")
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
                info['account'] = artist_name
                info['account_id'] = artist_id
                print(f"Set info['account']: {info['account']}")

                # Extract media title and length for Spotify
                if html:
                    try:
                        # Extract title from meta tags
                        title_element = soup.find('meta', property='og:title')
                        if title_element:
                            info['media_title'] = title_element.get('content', '')
                    except:
                        pass
                    
                    try:
                        # Spotify doesn't typically show track length in meta tags
                        # but we can try to extract it from the page content
                        pass
                    except:
                        pass

            except Exception as e:
                print(f"An error occurred: {e}")

        elif platform == 'Apple':
            # Extract media title and length for Apple Music
            if html:
                try:
                    # Extract title from meta tags
                    title_element = soup.find('meta', property='og:title')
                    if title_element:
                        info['media_title'] = title_element.get('content', '')
                except:
                    pass
                
                try:
                    # Extract duration from meta tags
                    duration_element = soup.find('meta', property='music:duration')
                    if duration_element:
                        duration_seconds = int(duration_element.get('content', 0))
                        minutes = duration_seconds // 60
                        seconds = duration_seconds % 60
                        info['media_length'] = f"{minutes}:{seconds:02d}"
                except:
                    pass
                
                try:
                    # Extract artist/account info
                    artist_element = soup.find('meta', property='music:musician')
                    if artist_element:
                        artist_url = artist_element.get('content', '')
                        if artist_url:
                            artist_id = artist_url.split('/')[-1]
                            info['account_id'] = artist_id
                except:
                    pass
                
                try:
                    # Extract artist name from description
                    desc_element = soup.find('meta', property='og:description')
                    if desc_element:
                        description = desc_element.get('content', '')
                        if 'by' in description:
                            artist_name = description.split('by')[-1].split('.')[0].strip()
                            info['account'] = artist_name
                except:
                    pass

        elif platform == 'Soundcloud':
            parts = url.split('/')
            if len(parts) > 4:
                extracted_string = parts[3]
                info['account'] = extracted_string
                print(f"Extracted string: {extracted_string}")
            else:
                print("The URL does not have enough parts to extract the string.")
            
            # Extract media title and length for Soundcloud
            if html:
                try:
                    # Extract title from meta tags
                    title_element = soup.find('meta', property='og:title')
                    if title_element:
                        info['media_title'] = title_element.get('content', '')
                        print(f"Found Soundcloud title from og:title: {info['media_title']}")
                except:
                    pass

                try:
                    # Extract duration from Soundcloud's hydration data
                    scripts = soup.find_all('script')
                    for script in scripts:
                        if script.string and 'window.__sc_hydration' in script.string:
                            try:
                                # Find the sound data in the hydration script
                                start = script.string.find('window.__sc_hydration = ') + len('window.__sc_hydration = ')
                                end = script.string.find(';', start)
                                if end == -1:
                                    end = len(script.string)
                                data_str = script.string[start:end]
                                data = json.loads(data_str)
                                
                                # Look for sound data with duration
                                for item in data:
                                    if item.get('hydratable') == 'sound' and item.get('data'):
                                        sound_data = item['data']
                                        if 'duration' in sound_data:
                                            duration_ms = sound_data['duration']
                                            duration_seconds = duration_ms // 1000
                                            minutes = duration_seconds // 60
                                            seconds = duration_seconds % 60
                                            info['media_length'] = f"{minutes}:{seconds:02d}"
                                            print(f"Found Soundcloud duration from hydration data: {info['media_length']}")
                                            break
                            except:
                                continue
                except:
                    pass

                try:
                    # Fallback: Extract duration from meta tags
                    duration_selectors = [
                        ('meta', {'property': 'music:duration'}),
                        ('meta', {'name': 'duration'}),
                        ('meta', {'property': 'og:video:duration'})
                    ]
                    
                    for tag, attrs in duration_selectors:
                        try:
                            element = soup.find(tag, attrs)
                            if element and element.get('content') and not info['media_length']:
                                duration_text = element.get('content')
                                if duration_text.isdigit():
                                    duration_seconds = int(duration_text)
                                    minutes = duration_seconds // 60
                                    seconds = duration_seconds % 60
                                    info['media_length'] = f"{minutes}:{seconds:02d}"
                                    print(f"Found Soundcloud duration from meta tag: {info['media_length']}")
                                    break
                                elif ':' in duration_text:
                                    info['media_length'] = duration_text
                                    print(f"Found Soundcloud duration from meta tag: {info['media_length']}")
                                    break
                        except:
                            continue
                except:
                    pass
                
        elif platform == 'Facebook':
            if not driver:
                print("Error: Driver is required for Facebook extraction")
                return info
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
            
            # Extract media title and length for Facebook
            if html:
                try:
                    # Extract title from meta tags
                    title_element = soup.find('meta', property='og:title')
                    if title_element:
                        info['media_title'] = title_element.get('content', '')
                except:
                    pass
                
                try:
                    # Extract duration from meta tags
                    duration_element = soup.find('meta', property='video:duration')
                    if duration_element:
                        duration_seconds = int(duration_element.get('content', 0))
                        minutes = duration_seconds // 60
                        seconds = duration_seconds % 60
                        info['media_length'] = f"{minutes}:{seconds:02d}"
                except:
                    pass

        elif platform == 'Daily Motion':
            if not driver:
                print("Error: Driver is required for Daily Motion extraction")
                return info
            # Try Daily Motion's oEmbed API first (most reliable)
            try:
                import requests
                
                # Extract video ID from URL
                video_id = url.split('/')[-1]
                print(f"Extracted Daily Motion video ID: {video_id}")
                
                # Use Daily Motion's oEmbed API
                oembed_url = f"https://www.dailymotion.com/services/oembed?url={url}&format=json"
                print(f"Trying Daily Motion oEmbed API: {oembed_url}")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
                }
                
                response = requests.get(oembed_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    print(f"Daily Motion API success! Found data: {data.get('title', 'No title')}")
                    
                    # Extract account from author_name
                    if 'author_name' in data:
                        info['account'] = data['author_name']
                        print(f"Found Daily Motion account from API: {info['account']}")
                    
                    # Extract media title
                    if 'title' in data:
                        info['media_title'] = data['title']
                        print(f"Found Daily Motion title from API: {info['media_title']}")
                    
                    # Extract duration if available (API doesn't provide duration)
                    # We'll try to get it from the web page as fallback
                    
                else:
                    print(f"Daily Motion API failed: {response.status_code}")
                    # Fall back to web scraping
                    raise Exception("API failed, falling back to web scraping")
                    
            except Exception as e:
                print(f"Daily Motion API approach failed: {e}")
                print("Falling back to web scraping methods...")
                
                # Fallback to web scraping approaches
                success = False
                
                # Approach 1: Try to find channel link with longer wait and different selectors
                if not success:
                    try:
                        # Wait longer and try different selectors
                        selectors = [
                            "a[class*='channelLink']",
                            "a[href*='/channel/']",
                            "a[href*='/user/']",
                            ".channel-name",
                            ".user-name"
                        ]
                        
                        for selector in selectors:
                            try:
                                a_tag = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                )
                                href = a_tag.get_attribute('href')
                                if href:
                                    print(f"Found href with selector '{selector}': {href}")
                                    info['account'] = href.replace("https://www.dailymotion.com/", "").split('/')[0]
                                    success = True
                                    break
                            except:
                                continue
                                
                    except Exception as e:
                        print(f"Web scraping approach 1 failed: {e}")
                
                # Approach 2: Try to extract from meta tags
                if not success and html:
                    try:
                        # Try multiple meta tag approaches
                        meta_selectors = [
                            ('meta', {'property': 'og:site_name'}),
                            ('meta', {'name': 'author'}),
                            ('meta', {'property': 'og:author'}),
                            ('meta', {'name': 'channel'}),
                            ('meta', {'property': 'video:channel'})
                        ]
                        
                        for tag, attrs in meta_selectors:
                            try:
                                element = soup.find(tag, attrs)
                                if element and element.get('content'):
                                    info['account'] = element.get('content')
                                    print(f"Found account from meta tag {tag}: {info['account']}")
                                    success = True
                                    break
                            except:
                                continue
                                
                    except Exception as e:
                        print(f"Web scraping approach 2 failed: {e}")
                
                # Approach 3: Try to extract from page content
                if not success and html:
                    try:
                        # Look for channel/user information in the page content
                        content_selectors = [
                            '.channel-name',
                            '.user-name',
                            '.author-name',
                            '[data-channel]',
                            '[data-user]'
                        ]
                        
                        for selector in content_selectors:
                            try:
                                element = soup.select_one(selector)
                                if element and element.get_text().strip():
                                    info['account'] = element.get_text().strip()
                                    print(f"Found account from content selector '{selector}': {info['account']}")
                                    success = True
                                    break
                            except:
                                continue
                                
                    except Exception as e:
                        print(f"Web scraping approach 3 failed: {e}")
                
                # Approach 4: Fallback to generic Daily Motion
                if not success:
                    try:
                        info['account'] = 'Daily Motion'
                        print("Using fallback account: Daily Motion")
                    except:
                        pass
            
            # Extract media title and length for Daily Motion
            # Note: Title and account are now extracted from the API above
            # This section is mainly for duration extraction and fallbacks
            
            # If we don't have a title from the API, try web scraping
            if not info['media_title'] and html:
                try:
                    # Extract title from multiple meta tag approaches
                    title_selectors = [
                        ('meta', {'property': 'og:title'}),
                        ('meta', {'name': 'title'}),
                        ('meta', {'property': 'twitter:title'}),
                        ('title', {})
                    ]
                    
                    for tag, attrs in title_selectors:
                        try:
                            element = soup.find(tag, attrs)
                            if element:
                                if tag == 'title':
                                    title_text = element.get_text()
                                else:
                                    title_text = element.get('content', '')
                                
                                if title_text and title_text.strip() and title_text.strip() != 'Dailymotion':
                                    info['media_title'] = title_text.strip()
                                    print(f"Found Daily Motion title from web scraping {tag}: {info['media_title']}")
                                    break
                        except:
                            continue
                    
                    # If no good title found, try to extract from page content
                    if not info['media_title'] or info['media_title'] == 'Dailymotion':
                        try:
                            # Look for video title in page content
                            content_selectors = [
                                'h1',
                                '.video-title',
                                '.title',
                                '[data-testid="video-title"]',
                                '[class*="title"]'
                            ]
                            
                            for selector in content_selectors:
                                elements = soup.select(selector)
                                for element in elements:
                                    title_text = element.get_text().strip()
                                    if title_text and title_text != 'Dailymotion' and len(title_text) > 5:
                                        info['media_title'] = title_text
                                        print(f"Found Daily Motion title from content selector '{selector}': {info['media_title']}")
                                        break
                                if info['media_title'] and info['media_title'] != 'Dailymotion':
                                    break
                        except:
                            pass
                except:
                    pass
            
            # Try to extract duration (API doesn't provide duration, so we need web scraping)
            if html:
                try:
                    # Extract duration from multiple meta tag approaches
                    duration_selectors = [
                        ('meta', {'property': 'video:duration'}),
                        ('meta', {'name': 'duration'}),
                        ('meta', {'property': 'og:video:duration'}),
                        ('meta', {'itemprop': 'duration'})
                    ]
                    
                    for tag, attrs in duration_selectors:
                        try:
                            element = soup.find(tag, attrs)
                            if element:
                                duration_text = element.get('content', '')
                                if duration_text:
                                    # Try to parse various duration formats
                                    if duration_text.isdigit():
                                        duration_seconds = int(duration_text)
                                        minutes = duration_seconds // 60
                                        seconds = duration_seconds % 60
                                        info['media_length'] = f"{minutes}:{seconds:02d}"
                                        print(f"Found Daily Motion duration from meta tag: {info['media_length']}")
                                        break
                                    elif ':' in duration_text:
                                        info['media_length'] = duration_text
                                        print(f"Found Daily Motion duration from meta tag: {info['media_length']}")
                                        break
                        except:
                            continue
                    
                    # Try to extract duration from page content
                    if not info['media_length']:
                        try:
                            duration_selectors = [
                                '.video-duration',
                                '.duration',
                                '[class*="duration"]',
                                '[class*="time"]'
                            ]
                            
                            for selector in duration_selectors:
                                elements = soup.select(selector)
                                for element in elements:
                                    duration_text = element.get_text().strip()
                                    if duration_text and ':' in duration_text:
                                        info['media_length'] = duration_text
                                        print(f"Found Daily Motion duration from content: {info['media_length']}")
                                        break
                                if info['media_length']:
                                    break
                        except:
                            pass
                except:
                    pass

        elif platform == 'Apple':
            elements = soup.find_all('a', href=lambda href: href and href.startswith('https://music.apple.com/us/artist/'))
    
            # Extract and print the href and text content
            for element in elements:
                href = element['href']
                info['account'] = href.replace("https://music.apple.com/us/artist/", "").split("/")[0]
                info['account_id'] = href.replace("https://music.apple.com/us/artist/", "").split("/")[1]
            
            # Extract media title and length for Apple Music
            if html:
                try:
                    # Extract title from meta tags
                    title_element = soup.find('meta', property='og:title')
                    if title_element:
                        info['media_title'] = title_element.get('content', '')
                except:
                    pass
                
                try:
                    # Extract duration from meta tags
                    duration_element = soup.find('meta', property='music:duration')
                    if duration_element:
                        duration_seconds = int(duration_element.get('content', 0))
                        minutes = duration_seconds // 60
                        seconds = duration_seconds % 60
                        info['media_length'] = f"{minutes}:{seconds:02d}"
                except:
                    pass
                
        elif platform == 'TikTok':
            parts = url.split('/')
            if len(parts) > 4:
                extracted_string = parts[3]
                info['account'] = extracted_string
                print(f"Extracted string: {extracted_string}")
            else:
                print("The URL does not have enough parts to extract the string.")
            
                        # Extract media title and length for TikTok
            if html:
                try:
                    # Try to extract title from meta tags (priority order)
                    title_selectors = [
                        ('meta', {'property': 'og:title'}),
                        ('meta', {'name': 'title'}),
                        ('meta', {'property': 'twitter:title'})
                    ]
                    
                    for tag, attrs in title_selectors:
                        try:
                            element = soup.find(tag, attrs)
                            if element and element.get('content'):
                                title_text = element.get('content')
                                # Clean up TikTok title (remove "on TikTok" suffix)
                                if title_text.endswith(' on TikTok'):
                                    title_text = title_text[:-10]
                                info['media_title'] = title_text
                                print(f"Found TikTok title from {tag}: {info['media_title']}")
                                break
                        except:
                            continue
                    
                    # Fallback to page title if no meta title found
                    if not info['media_title']:
                        title_element = soup.find('title')
                        if title_element:
                            title_text = title_element.get_text()
                            if title_text and title_text != 'TikTok':
                                # Clean up page title
                                if ' | TikTok' in title_text:
                                    title_text = title_text.split(' | TikTok')[0]
                                info['media_title'] = title_text
                                print(f"Found TikTok title from page title: {info['media_title']}")
                except:
                    pass

                try:
                    # Try to extract video duration from meta tags
                    duration_selectors = [
                        ('meta', {'property': 'video:duration'}),
                        ('meta', {'name': 'duration'}),
                        ('meta', {'property': 'og:video:duration'})
                    ]
                    
                    for tag, attrs in duration_selectors:
                        try:
                            element = soup.find(tag, attrs)
                            if element and element.get('content'):
                                duration_text = element.get('content')
                                if duration_text.isdigit():
                                    duration_seconds = int(duration_text)
                                    minutes = duration_seconds // 60
                                    seconds = duration_seconds % 60
                                    info['media_length'] = f"{minutes}:{seconds:02d}"
                                    print(f"Found TikTok duration: {info['media_length']}")
                                    break
                        except:
                            continue
                except:
                    pass
                
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
                    info['account'] = target_url.replace("https://music.amazon.com/artists/", "").split("/")[1]
                    info['account_id'] = target_url.replace("https://music.amazon.com/artists/", "").split("/")[0]
                else:
                    print("No <script> element contained the desired URL after 20 seconds.")

            except Exception as e:
                print(f"An error occurred: {e}")
                    
        elif platform == 'Daily Motion':
            # Extract media title and length for Daily Motion
            if html:
                try:
                    # Extract title
                    title_element = soup.find('meta', property='og:title')
                    if title_element:
                        info['media_title'] = title_element.get('content', '')
                except:
                    pass
                
                try:
                    # Extract duration
                    duration_element = soup.find('meta', property='video:duration')
                    if duration_element:
                        duration_seconds = int(duration_element.get('content', 0))
                        minutes = duration_seconds // 60
                        seconds = duration_seconds % 60
                        info['media_length'] = f"{minutes}:{seconds:02d}"
                except:
                    pass
                
                try:
                    # Extract account info if available
                    author_element = soup.find('meta', property='og:site_name')
                    if author_element:
                        info['account'] = author_element.get('content', '')
                except:
                    pass
        else:
            title = soup.find('meta', property='og:title')
            info['account'] = title['content'] if title else ''
            
            # Try to extract media title and length for other platforms
            if html:
                try:
                    # Extract title
                    title_element = soup.find('meta', property='og:title')
                    if title_element:
                        info['media_title'] = title_element.get('content', '')
                except:
                    pass
                
                try:
                    # Extract duration
                    duration_element = soup.find('meta', property='video:duration')
                    if duration_element:
                        duration_seconds = int(duration_element.get('content', 0))
                        minutes = duration_seconds // 60
                        seconds = duration_seconds % 60
                        info['media_length'] = f"{minutes}:{seconds:02d}"
                except:
                    pass

        # Add more platform-specific scraping logic here
    except Exception as e:
        print(f"Error extracting info for {platform}: {str(e)}")
    
    print(f"Account: {info}")
    return info

def process_csv(input_file, output_file):
    try:
        with open(input_file, 'r', newline='', encoding='utf-8-sig') as infile, \
             open(output_file, 'w', newline='', encoding='utf-8-sig') as outfile:
            reader = csv.DictReader(infile)
            
            # Ensure all required columns exist, even if they're not in the original CSV
            required_columns = ['platform', 'url', 'account', 'account_id', 'media_title', 'media_length']
            existing_columns = reader.fieldnames or []
            
            # Add missing columns to fieldnames
            fieldnames = existing_columns.copy()
            for col in required_columns:
                if col not in fieldnames:
                    fieldnames.append(col)
            
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                # Ensure all required columns exist in the row
                for col in required_columns:
                    if col not in row:
                        row[col] = ''
                
                if row['url']:
                    print(row)
                    print(f"Processing: {row['url']} {row['platform']}")
                    noWebNeeded = row['platform'] in []  # All platforms need web interaction for media title and length extraction

                    if not noWebNeeded:  # If web interaction is needed
                        html = check_url(row['url'])
                        if html:
                            info = extract_info(html, row['platform'], row['url'], driver)
                    else:  # If no web interaction is needed
                        info = extract_info(None, row['platform'], row['url'], driver)
                        
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