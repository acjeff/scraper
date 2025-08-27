# Railway.app Deployment Guide for Google Sheets Scraper

This guide will help you deploy the super memory-efficient Google Sheets scraper on Railway.app.

## 🚀 **Railway-Specific Optimizations**

### **Memory Efficiency:**
- ✅ **Railway-optimized Chrome options** - Minimal memory usage
- ✅ **Single-process mode** - Reduces memory footprint
- ✅ **Disable images/JavaScript** - Saves bandwidth and memory
- ✅ **Shorter timeouts** - Faster processing for Railway environment

### **Environment Variables:**
- ✅ **No file-based credentials** - Uses Railway environment variables
- ✅ **Secure credential handling** - JSON stored as environment variable
- ✅ **Railway-compatible logging** - File and console output

### **Railway Integration:**
- ✅ **Nixpacks builder** - Uses existing Chrome/Chromedriver setup
- ✅ **Automatic restarts** - Railway handles crashes and restarts
- ✅ **Resource optimization** - Designed for Railway's resource constraints

## 📋 **Railway Deployment Steps**

### **Step 1: Prepare Your Repository**

Ensure your repository has these files:
```
scraper/
├── railway_google_sheets_scraper.py    # Main Railway scraper
├── railway.json                        # Railway configuration
├── nixpacks.toml                      # Build configuration
├── requirements_railway.txt           # Python dependencies
├── TestLinks.csv                      # Your input file
└── RAILWAY_DEPLOYMENT.md              # This guide
```

### **Step 2: Set Up Google Cloud Project**

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create a new project** or select existing
3. **Enable APIs:**
   - Go to "APIs & Services" > "Library"
   - Search for and enable:
     - **Google Sheets API**
     - **Google Drive API**

### **Step 3: Create Service Account**

1. **Go to "APIs & Services" > "Credentials"**
2. **Click "Create Credentials" > "Service Account"**
3. **Fill in details:**
   - Name: `railway-scraper-service-account`
   - Description: `Service account for Railway scraper`
4. **Click "Create and Continue"**
5. **Skip role assignment** (click "Continue")
6. **Click "Done"**

### **Step 4: Download and Prepare Credentials**

1. **Click on your service account** in the list
2. **Go to "Keys" tab**
3. **Click "Add Key" > "Create new key"**
4. **Choose "JSON" format**
5. **Download the file**
6. **Open the JSON file** and copy the entire contents
7. **Keep this JSON content** - you'll need it for Railway

### **Step 5: Create Google Sheet**

1. **Go to [Google Sheets](https://sheets.google.com/)**
2. **Create a new spreadsheet**
3. **Copy the spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit
   ```

### **Step 6: Share Sheet with Service Account**

1. **In your Google Sheet, click "Share"**
2. **Add your service account email** (found in the JSON file under `client_email`)
3. **Give it "Editor" permissions**
4. **Click "Send"**

### **Step 7: Deploy to Railway**

1. **Go to [Railway.app](https://railway.app/)**
2. **Create a new project**
3. **Connect your GitHub repository**
4. **Railway will automatically detect the configuration**

### **Step 8: Set Environment Variables**

In your Railway project dashboard:

1. **Go to "Variables" tab**
2. **Add these environment variables:**

   **`GOOGLE_CREDENTIALS_JSON`**
   - Value: Paste the entire JSON content from Step 4
   - Example:
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

   **`GOOGLE_SPREADSHEET_ID`**
   - Value: Your spreadsheet ID from Step 5
   - Example: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`

### **Step 9: Deploy and Monitor**

1. **Railway will automatically deploy** when you push changes
2. **Check the logs** in Railway dashboard
3. **Monitor progress** in your Google Sheet

## 🔧 **Railway Configuration Files**

### **railway.json**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python3 railway_google_sheets_scraper.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 5
  },
  "services": [
    {
      "name": "google-sheets-scraper",
      "startCommand": "python3 railway_google_sheets_scraper.py"
    }
  ]
}
```

### **nixpacks.toml**
```toml
[phases.setup]
nixPkgs = ["chromium", "chromedriver", "python39"]

[variables]
CHROME_BIN = "chromium"
CHROMEDRIVER_PATH = "chromedriver"
PYTHON_VERSION = "3.9"
```

### **requirements_railway.txt**
```
gspread==5.12.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
selenium==4.15.2
webdriver-manager==4.0.1
beautifulsoup4==4.12.2
requests==2.31.0
```

## 📊 **Railway Performance Expectations**

### **Resource Usage:**
- **Memory:** ~200-400MB (optimized for Railway)
- **CPU:** Single-threaded processing
- **Storage:** Minimal (no local files)

### **Processing Speed:**
- **~1 URL per 8-12 seconds** (Railway-optimized)
- **~300 URLs per hour**
- **~7,200 URLs per day**
- **Your 24,523 URLs:** ~3-4 days

### **Reliability:**
- **Automatic restarts** on failure
- **Crash-safe** - Data saved after each URL
- **Network resilient** - Handles Railway network issues

## 🛠️ **Railway-Specific Features**

### **Environment Variable Handling:**
- **No credential files** - Uses Railway environment variables
- **Secure storage** - Credentials stored securely in Railway
- **Easy updates** - Change credentials without redeploying

### **Logging:**
- **File logging** - `railway_google_sheets.log`
- **Console logging** - Visible in Railway dashboard
- **Structured format** - Easy to monitor progress

### **Chrome Optimization:**
- **System Chrome** - Uses Railway's Nixpacks Chrome
- **Memory efficient** - Disabled images, single process
- **Faster timeouts** - Optimized for Railway environment

## 🚨 **Railway Deployment Notes**

### **Important Considerations:**
1. **Environment variables** must be set before deployment
2. **Google Sheet sharing** must be done manually
3. **Railway restarts** will resume from current row
4. **Monitor logs** in Railway dashboard
5. **Check Google Sheet** for real-time progress

### **Troubleshooting:**

**Authentication Errors:**
```
❌ Google authentication error
```
**Solution:** Check `GOOGLE_CREDENTIALS_JSON` environment variable format

**Permission Errors:**
```
❌ Error inserting row: 403 Forbidden
```
**Solution:** Ensure Google Sheet is shared with service account email

**Chrome Driver Issues:**
```
❌ ChromeDriver not found
```
**Solution:** Railway will automatically install via Nixpacks

**Memory Issues:**
```
❌ Out of memory
```
**Solution:** Railway will automatically restart the service

## 🎉 **Success Indicators**

### **When deployed correctly:**
- ✅ **Railway deployment succeeds** without errors
- ✅ **Logs show** "Connected to existing worksheet" or "Created new worksheet"
- ✅ **Data appears** in Google Sheet row by row
- ✅ **Progress updates** in Railway logs every 10 URLs

### **Monitor deployment:**
- **Railway Dashboard:** Check logs and deployment status
- **Google Sheet:** Watch data appear in real-time
- **Environment Variables:** Verify they're set correctly

This Railway deployment will be much more reliable and memory-efficient than local processing! 🚀
