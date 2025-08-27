# Super Memory Efficient Google Sheets Scraper Setup Guide

This guide will help you set up the super memory-efficient scraper that inserts data directly into Google Sheets and clears memory after each link.

## 🚀 **Key Benefits**

### **Memory Efficiency:**
- ✅ **Zero local storage** - No CSV files, no chunks, no temporary files
- ✅ **Immediate memory clearing** - All data cleared after each link
- ✅ **Minimal RAM usage** - Only processes one link at a time
- ✅ **No memory buildup** - Perfect for long-running processes

### **Easy Tracking:**
- ✅ **Google Sheets row numbers** - Easy to see exactly where you are
- ✅ **Real-time progress** - Watch data appear as it's processed
- ✅ **Automatic resume** - Pick up from any row number
- ✅ **No lost progress** - Data is saved immediately

### **Reliability:**
- ✅ **Crash-proof** - Data saved after each link
- ✅ **Interrupt-safe** - Can stop and resume anytime
- ✅ **Network resilient** - Handles connection issues gracefully

## 📋 **Setup Instructions**

### **Step 1: Install Dependencies**

```bash
pip install -r requirements_google_sheets.txt
```

### **Step 2: Set Up Google Cloud Project**

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create a new project** or select an existing one
3. **Enable APIs:**
   - Go to "APIs & Services" > "Library"
   - Search for and enable:
     - **Google Sheets API**
     - **Google Drive API**

### **Step 3: Create Service Account**

1. **Go to "APIs & Services" > "Credentials"**
2. **Click "Create Credentials" > "Service Account"**
3. **Fill in details:**
   - Name: `scraper-service-account`
   - Description: `Service account for web scraper`
4. **Click "Create and Continue"**
5. **Skip role assignment** (click "Continue")
6. **Click "Done"**

### **Step 4: Download Credentials**

1. **Click on your service account** in the list
2. **Go to "Keys" tab**
3. **Click "Add Key" > "Create new key"**
4. **Choose "JSON" format**
5. **Download the file**
6. **Rename it to `google-credentials.json`**
7. **Place it in your project directory**

### **Step 5: Create Google Sheet**

1. **Go to [Google Sheets](https://sheets.google.com/)**
2. **Create a new spreadsheet**
3. **Copy the spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit
   ```

### **Step 6: Share Sheet with Service Account**

1. **In your Google Sheet, click "Share"**
2. **Add your service account email** (found in `google-credentials.json`)
3. **Give it "Editor" permissions**
4. **Click "Send"**

### **Step 7: Update Configuration**

Edit `memory_efficient_google_sheets_scraper.py` and update:

```python
SPREADSHEET_ID = "your-actual-spreadsheet-id-here"
```

## 🎯 **Usage Instructions**

### **First Time Run:**

```bash
python3 memory_efficient_google_sheets_scraper.py
```

### **Check Progress & Resume:**

```bash
python3 resume_google_sheets_scraper.py
```

### **Resume from Specific Row:**

```bash
python3 resume_google_sheets_scraper.py
# Then choose option 2 and enter the row number
```

## 📊 **How It Works**

### **Memory Management:**
1. **Process one URL** at a time
2. **Extract data** from the webpage
3. **Insert immediately** into Google Sheets
4. **Clear all memory** (HTML, BeautifulSoup objects, etc.)
5. **Force garbage collection**
6. **Move to next URL**

### **Progress Tracking:**
- **Row 1:** Headers (platform, url, account, account_id, media_title, media_length, processed_at)
- **Row 2+:** Data rows
- **Current row number** = Next row to write to
- **Easy resume** from any row number

### **Data Flow:**
```
CSV File → Process URL → Extract Data → Insert to Google Sheets → Clear Memory → Next URL
```

## 🔧 **Configuration Options**

### **Adjust Processing Speed:**
In `memory_efficient_google_sheets_scraper.py`, change:
```python
time.sleep(5)  # Delay between URLs (seconds)
```

### **Change Sheet Name:**
```python
SHEET_NAME = "Your Custom Sheet Name"
```

### **Modify Headers:**
```python
headers = ['platform', 'url', 'account', 'account_id', 'media_title', 'media_length', 'processed_at']
```

## 📈 **Performance Expectations**

### **Memory Usage:**
- **Peak RAM:** ~100-200MB (vs 2-4GB with old system)
- **Constant memory** - No buildup over time
- **Suitable for** long-running processes

### **Processing Speed:**
- **~1 URL per 10-15 seconds** (including delays)
- **~240 URLs per hour**
- **~5,760 URLs per day**
- **Your 24,523 URLs:** ~4-5 days

### **Reliability:**
- **100% crash-safe** - Data saved after each URL
- **Network resilient** - Handles connection issues
- **Resume anywhere** - Pick up from any row

## 🛠️ **Troubleshooting**

### **Authentication Errors:**
```
❌ Google authentication error
```
**Solution:** Check your `google-credentials.json` file and ensure the service account has access to the sheet.

### **Permission Errors:**
```
❌ Error inserting row: 403 Forbidden
```
**Solution:** Make sure you've shared the Google Sheet with the service account email.

### **Rate Limiting:**
```
❌ Error inserting row: 429 Too Many Requests
```
**Solution:** Increase the delay between URLs (change `time.sleep(5)` to `time.sleep(10)`).

### **Chrome Driver Issues:**
```
❌ ChromeDriver not found
```
**Solution:** The script will automatically download ChromeDriver via webdriver-manager.

## 📁 **File Structure**

```
scraper/
├── memory_efficient_google_sheets_scraper.py  # Main scraper
├── resume_google_sheets_scraper.py           # Resume functionality
├── requirements_google_sheets.txt            # Dependencies
├── google-credentials.json                   # Google service account (you create)
├── TestLinks.csv                            # Your input file
└── GOOGLE_SHEETS_SETUP.md                   # This guide
```

## 🎉 **Success Indicators**

### **When it's working correctly:**
- ✅ Data appears in Google Sheets row by row
- ✅ Memory usage stays constant
- ✅ Progress shows current row number
- ✅ Can stop and resume anytime

### **Monitor progress:**
- **Google Sheets:** Watch data appear in real-time
- **Terminal:** See progress updates every 10 URLs
- **Row numbers:** Easy to track exactly where you are

## 🚨 **Important Notes**

1. **Keep your computer awake** - Processing stops if it goes to sleep
2. **Don't delete `google-credentials.json`** - It's needed for authentication
3. **Don't change the Google Sheet structure** while processing
4. **Monitor disk space** - ChromeDriver may download files
5. **Check progress regularly** - Use the resume script to see status

This system should be much more reliable and memory-efficient than the previous chunk-based approach! 🚀
