#!/usr/bin/env python3
"""
Test script for the improved URL scraper with enhanced Daily Motion handling
"""

import os
import sys

# Import the functions from the main scraper
from url_checker_script import init_driver, quit_driver, process_csv

if __name__ == "__main__":
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the input and output file paths for testing
    input_file = os.path.join(current_dir, "test_improved_dailymotion.csv")
    output_file = os.path.join(current_dir, "test_improved_results.csv")

    print(f"Testing improved extraction with enhanced Daily Motion handling...")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")

    # Initialize the driver
    init_driver()
    
    try:
        # Process the CSV
        process_csv(input_file, output_file)
        print("\n" + "="*60)
        print("IMPROVED EXTRACTION RESULTS:")
        print("="*60)
        
        # Read and display the results
        import csv
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(f"\nPlatform: {row['platform']}")
                print(f"URL: {row['url']}")
                print(f"Account: '{row['account']}'")
                print(f"Account ID: '{row['account_id']}'")
                print(f"Media Title: '{row['media_title']}'")
                print(f"Media Length: '{row['media_length']}'")
                print("-" * 40)
        
        print(f"\nTest completed! Results saved to: {output_file}")
        print("You can examine the detailed results in the output file.")
        
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        # Quit the driver after processing
        quit_driver()
