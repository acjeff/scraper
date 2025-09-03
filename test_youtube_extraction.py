#!/usr/bin/env python3
"""
Test script for YouTube extraction functionality
"""

import os
import sys
import csv

# Import the functions from the main scraper
from url_checker_script import init_driver, quit_driver, extract_info, check_url

def test_youtube_extraction():
    """Test YouTube extraction with a sample URL"""
    
    # Test YouTube URL
    test_url = "https://www.youtube.com/watch?v=nzz6RL1K5DM"
    platform = "YouTube"
    
    print(f"Testing YouTube extraction...")
    print(f"URL: {test_url}")
    print(f"Platform: {platform}")
    print("=" * 60)
    
    # Initialize the driver
    init_driver()
    
    try:
        # Get HTML content
        print("Getting page content...")
        html = check_url(test_url)
        
        if html:
            print("✅ Successfully loaded page")
            print(f"HTML length: {len(html)} characters")
            
            # Extract information
            print("\nExtracting information...")
            from url_checker_script import driver
            info = extract_info(html, platform, test_url, driver)
            
            print("\n" + "=" * 60)
            print("EXTRACTION RESULTS:")
            print("=" * 60)
            print(f"Account: '{info['account']}'")
            print(f"Account ID: '{info['account_id']}'")
            print(f"Media Title: '{info['media_title']}'")
            print(f"Media Length: '{info['media_length']}'")
            print("=" * 60)
            
            # Check if we got meaningful results
            if info['account'] or info['account_id'] or info['media_title'] or info['media_length']:
                print("✅ YouTube extraction appears to be working!")
            else:
                print("❌ No information was extracted")
                
        else:
            print("❌ Failed to load page content")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Quit the driver
        quit_driver()

if __name__ == "__main__":
    test_youtube_extraction()
