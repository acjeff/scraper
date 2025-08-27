# Google Sheets Workflow Setup Guide

This guide will help you set up the complete Google Sheets workflow where the scraper reads URLs from one Google Sheet and writes processed data to another.

## 🔄 **Workflow Overview**

```
Input Google Sheet → Railway Scraper → Output Google Sheet
     (URLs)              (Process)         (Results)
```

### **What happens:**
1. **Input Sheet:** Contains your URLs to process (like your current TestLinks.csv)
2. **Railway Scraper:** Reads URLs from input sheet, processes them, and writes results
3. **Output Sheet:** Contains all processed data with extracted information

## 📋 **Setup Steps**

### **Step 1: Create Input Google Sheet**

1. **Go to [Google Sheets](https://sheets.google.com/)**
2. **Create a new spreadsheet** called "Scraper Input URLs"
3. **Set up the headers** in row 1:
   ```
   A1: platform
   B1: url
   C1: account
   D1: account_id
   E1: media_title
   F1: media_length
   ```
4. **Add your URLs** starting from row 2:
   ```
   A2: YouTube
   B2: https://www.youtube.com/watch?v=example
   C2: (leave empty - will be filled by scraper)
   D2: (leave empty - will be filled by scraper)
   E2: (leave empty - will be filled by scraper)
   F2: (leave empty - will be filled by scraper)
   ```
5. **Copy the spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_INPUT_SPREADSHEET_ID/edit
   ```

### **Step 2: Create Output Google Sheet**

1. **Create another new spreadsheet** called "Scraper Results"
2. **Leave it empty** - the scraper will create the worksheet and headers automatically
3. **Copy the spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_OUTPUT_SPREADSHEET_ID/edit
   ```

### **Step 3: Set Up Google Cloud (if not done already)**

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create a new project** or select existing
3. **Enable APIs:**
   - Go to "APIs & Services" > "Library"
   - Search for and enable:
     - **Google Sheets API**
     - **Google Drive API**

### **Step 4: Create Service Account**

1. **Go to "APIs & Services" > "Credentials"**
2. **Click "Create Credentials" > "Service Account"**
3. **Fill in details:**
   - Name: `railway-scraper-service`
   - Description: `Service account for Railway scraper`
4. **Click "Create and Continue"**
5. **Skip role assignment** (click "Continue")
6. **Click "Done"**

### **Step 5: Download Credentials**

1. **Click on your service account** in the list
2. **Go to "Keys" tab**
3. **Click "Add Key" > "Create new key"**
4. **Choose "JSON" format**
5. **Download the file**
6. **Open the JSON file and copy the ENTIRE contents**

### **Step 6: Share Both Sheets**

1. **Share Input Sheet:**
   - In your input sheet, click "Share"
   - Add your service account email (from JSON file)
   - Give it "Viewer" permissions (it only needs to read)
   - Click "Share"

2. **Share Output Sheet:**
   - In your output sheet, click "Share"
   - Add your service account email (from JSON file)
   - Give it "Editor" permissions (it needs to write)
   - Click "Share"

## 🔧 **Railway Environment Variables**

Set these **3 environment variables** in Railway.app:

### **1. GOOGLE_CREDENTIALS_JSON**
- **Value:** The entire JSON content from Step 5
- **Example:**
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}
```

### **2. GOOGLE_INPUT_SPREADSHEET_ID**
- **Value:** Your input sheet ID from Step 1
- **Example:** `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`

### **3. GOOGLE_OUTPUT_SPREADSHEET_ID**
- **Value:** Your output sheet ID from Step 2
- **Example:** `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`

## 📊 **Input Sheet Format**

Your input sheet should look like this:

| platform | url | account | account_id | media_title | media_length |
|----------|-----|---------|------------|-------------|--------------|
| YouTube | https://www.youtube.com/watch?v=example1 | | | | |
| TikTok | https://www.tiktok.com/@user/video/123 | | | | |
| Soundcloud | https://soundcloud.com/artist/song | | | | |

**Notes:**
- **platform** and **url** columns are required
- **account**, **account_id**, **media_title**, **media_length** can be empty (will be filled by scraper)
- You can add more columns if needed

## 📈 **Output Sheet Format**

The scraper will automatically create an output sheet like this:

| platform | url | account | account_id | media_title | media_length | processed_at |
|----------|-----|---------|------------|-------------|--------------|--------------|
| YouTube | https://www.youtube.com/watch?v=example1 | Channel Name | UC123456 | Video Title | 5:30 | 2024-01-15 10:30:45 |
| TikTok | https://www.tiktok.com/@user/video/123 | @user | 123456789 | Video Description | 0:45 | 2024-01-15 10:31:12 |

## ✅ **Verification Checklist**

- [ ] Input Google Sheet created with URLs
- [ ] Output Google Sheet created (empty)
- [ ] Google Cloud project set up
- [ ] Google Sheets API enabled
- [ ] Google Drive API enabled
- [ ] Service account created
- [ ] JSON credentials downloaded
- [ ] Input sheet shared with service account (Viewer)
- [ ] Output sheet shared with service account (Editor)
- [ ] Railway environment variables set
- [ ] Ready to deploy

## 🚀 **Deployment**

1. **Push your code** to GitHub
2. **Railway will automatically deploy**
3. **Check the logs** for success messages:
   - ✅ `"Connected to input sheet: [Sheet Name]"`
   - ✅ `"Connected to existing output worksheet: Scraped Data"`
4. **Watch your output sheet** - data will appear row by row

## 🔄 **Workflow Benefits**

- ✅ **No local files** - Everything in Google Sheets
- ✅ **Easy to manage** - Add/remove URLs in input sheet
- ✅ **Real-time results** - Watch data appear in output sheet
- ✅ **Resume capability** - Pick up from where it left off
- ✅ **Collaborative** - Multiple people can manage input sheet
- ✅ **Backup friendly** - Google Sheets handles backups

## 🛠️ **Troubleshooting**

### **"Input sheet is empty or has no data rows"**
**Solution:** Make sure your input sheet has headers in row 1 and data starting from row 2

### **"Error connecting to input sheet"**
**Solution:** Ensure input sheet is shared with service account email

### **"403 Forbidden" when writing to output**
**Solution:** Ensure output sheet is shared with service account email with Editor permissions

### **"No URLs found in row"**
**Solution:** Make sure your input sheet has a "url" column with valid URLs

This workflow gives you a complete Google Sheets-based solution for processing your URLs! 🎉
