#!/usr/bin/env python3
"""
Resume Google Sheets Scraper
- Resume processing from a specific row number
- Check current progress in Google Sheets
- Continue from where it left off
"""

import os
import sys
import csv
from memory_efficient_google_sheets_scraper import GoogleSheetsScraper

def check_progress_and_resume():
    """Check current progress and offer to resume"""
    
    # Configuration
    CREDENTIALS_FILE = "google-credentials.json"
    SPREADSHEET_ID = "your-spreadsheet-id"  # Replace with your spreadsheet ID
    SHEET_NAME = "Scraped Data"
    INPUT_FILE = "TestLinks.csv"
    
    print("📊 Google Sheets Scraper - Progress Check & Resume")
    print("=" * 50)
    
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Credentials file not found: {CREDENTIALS_FILE}")
        print("Please set up Google credentials first")
        return
    
    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return
    
    # Initialize scraper
    scraper = None
    try:
        scraper = GoogleSheetsScraper(CREDENTIALS_FILE, SPREADSHEET_ID, SHEET_NAME)
        
        # Get current progress
        total_sheets_rows = scraper.get_current_progress()
        
        # Count total rows in input file
        with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            input_rows = list(reader)
            total_input_rows = len(input_rows)
        
        print(f"\n📋 Input File Analysis:")
        print(f"   Total rows in {INPUT_FILE}: {total_input_rows}")
        
        # Calculate progress
        if total_sheets_rows > 1:  # Has data beyond header
            processed_rows = total_sheets_rows - 1  # Subtract header
            remaining_rows = total_input_rows - processed_rows
            progress_percent = (processed_rows / total_input_rows) * 100
            
            print(f"\n📈 Progress Summary:")
            print(f"   Processed: {processed_rows}/{total_input_rows} rows")
            print(f"   Remaining: {remaining_rows} rows")
            print(f"   Progress: {progress_percent:.1f}%")
            
            if remaining_rows > 0:
                print(f"\n🔄 Resume Options:")
                print(f"   1. Resume from current position (row {scraper.current_row})")
                print(f"   2. Resume from specific row number")
                print(f"   3. Start over (clear all data)")
                print(f"   4. Just check progress (no processing)")
                
                choice = input("\nEnter your choice (1-4): ").strip()
                
                if choice == "1":
                    print(f"\n🚀 Resuming from row {scraper.current_row}...")
                    scraper.process_csv_file(INPUT_FILE)
                    
                elif choice == "2":
                    try:
                        start_row = int(input("Enter row number to start from: "))
                        if start_row < 2:
                            print("❌ Row number must be 2 or greater (row 1 is header)")
                            return
                        print(f"\n🚀 Resuming from row {start_row}...")
                        scraper.process_csv_file(INPUT_FILE, start_row)
                    except ValueError:
                        print("❌ Invalid row number")
                        return
                        
                elif choice == "3":
                    confirm = input("⚠️ This will clear all data in the Google Sheet. Continue? (y/N): ").strip().lower()
                    if confirm == 'y':
                        print("🗑️ Clearing Google Sheet...")
                        # Clear all data except header
                        scraper.sheet.clear()
                        scraper.headers_written = False
                        scraper.current_row = 2
                        print("✅ Sheet cleared. Starting fresh...")
                        scraper.process_csv_file(INPUT_FILE)
                    else:
                        print("❌ Operation cancelled")
                        
                elif choice == "4":
                    print("✅ Progress check complete")
                    
                else:
                    print("❌ Invalid choice")
            else:
                print("✅ All rows have been processed!")
                
        else:
            print("📊 No data found in Google Sheet. Starting fresh...")
            scraper.process_csv_file(INPUT_FILE)
            
    except KeyboardInterrupt:
        print("\n⏹️ Operation interrupted by user")
        print(f"📊 Progress saved up to row {scraper.current_row if scraper else 'unknown'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"📊 Progress saved up to row {scraper.current_row if scraper else 'unknown'}")
        
    finally:
        if scraper:
            scraper.cleanup()

def main():
    check_progress_and_resume()

if __name__ == "__main__":
    main()
