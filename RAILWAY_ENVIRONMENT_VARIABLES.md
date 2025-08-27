# Railway.app Environment Variables Setup

This guide shows you exactly what environment variables to set in Railway.app for the Google Sheets scraper.

## 🔧 **Required Environment Variables**

You need to set **3 environment variables** in Railway.app:

### **1. GOOGLE_CREDENTIALS_JSON**
**Purpose:** Your Google service account credentials (the entire JSON file content)

**How to get it:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "APIs & Services" > "Credentials"
3. Find your service account and click on it
4. Go to "Keys" tab
5. Click "Add Key" > "Create new key" > "JSON"
6. Download the JSON file
7. **Open the JSON file and copy the ENTIRE contents**

**Example value:**
```json
{
  "type": "service_account",
  "project_id": "your-project-id-123456",
  "private_key_id": "abc123def456ghi789",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project-id-123456.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id-123456.iam.gserviceaccount.com"
}
```

### **2. GOOGLE_INPUT_SPREADSHEET_ID**
**Purpose:** The ID of your input Google Sheet (where your URLs are stored)

**How to get it:**
1. Open your input Google Sheet (the one with your URLs)
2. Look at the URL: `https://docs.google.com/spreadsheets/d/YOUR_INPUT_SPREADSHEET_ID/edit`
3. Copy the part between `/d/` and `/edit`

**Example value:**
```
1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

### **3. GOOGLE_OUTPUT_SPREADSHEET_ID**
**Purpose:** The ID of your output Google Sheet (where processed data will be written)

**How to get it:**
1. Open your output Google Sheet (or create a new one)
2. Look at the URL: `https://docs.google.com/spreadsheets/d/YOUR_OUTPUT_SPREADSHEET_ID/edit`
3. Copy the part between `/d/` and `/edit`

**Example value:**
```
1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

## 📋 **How to Set Environment Variables in Railway.app**

### **Step 1: Go to Railway Dashboard**
1. Log into [Railway.app](https://railway.app/)
2. Open your project
3. Click on your service

### **Step 2: Add Environment Variables**
1. Click on the **"Variables"** tab
2. Click **"New Variable"**
3. Add each variable:

   **For GOOGLE_CREDENTIALS_JSON:**
   - **Name:** `GOOGLE_CREDENTIALS_JSON`
   - **Value:** Paste the entire JSON content from your service account file
   - **Type:** Plain text

   **For GOOGLE_INPUT_SPREADSHEET_ID:**
   - **Name:** `GOOGLE_INPUT_SPREADSHEET_ID`
   - **Value:** Your input spreadsheet ID (just the ID, not the full URL)
   - **Type:** Plain text

   **For GOOGLE_OUTPUT_SPREADSHEET_ID:**
   - **Name:** `GOOGLE_OUTPUT_SPREADSHEET_ID`
   - **Value:** Your output spreadsheet ID (just the ID, not the full URL)
   - **Type:** Plain text

### **Step 3: Save and Deploy**
1. Click **"Save"** for each variable
2. Railway will automatically redeploy with the new environment variables

## 🔍 **How the Code Uses These Variables**

The scraper automatically reads these environment variables:

```python
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
```

## ✅ **Verification Steps**

### **Check if Variables are Set:**
1. In Railway dashboard, go to "Variables" tab
2. You should see both variables listed
3. The values should be filled in (not empty)

### **Check Deployment Logs:**
After deployment, look for these messages in the logs:
- ✅ `"Connected to input sheet: [Sheet Name]"` (success)
- ✅ `"Connected to existing output worksheet: Scraped Data"` (success)
- ❌ `"GOOGLE_CREDENTIALS_JSON environment variable not set"` (error)
- ❌ `"GOOGLE_INPUT_SPREADSHEET_ID environment variable not set"` (error)
- ❌ `"GOOGLE_OUTPUT_SPREADSHEET_ID environment variable not set"` (error)

## 🚨 **Common Issues & Solutions**

### **Issue: "GOOGLE_CREDENTIALS_JSON environment variable not set"**
**Solution:** 
- Make sure you copied the ENTIRE JSON content
- Check that the variable name is exactly `GOOGLE_CREDENTIALS_JSON`
- Ensure there are no extra spaces or characters

### **Issue: "GOOGLE_INPUT_SPREADSHEET_ID environment variable not set"**
**Solution:**
- Make sure you copied just the ID part (not the full URL)
- Check that the variable name is exactly `GOOGLE_INPUT_SPREADSHEET_ID`

### **Issue: "GOOGLE_OUTPUT_SPREADSHEET_ID environment variable not set"**
**Solution:**
- Make sure you copied just the ID part (not the full URL)
- Check that the variable name is exactly `GOOGLE_OUTPUT_SPREADSHEET_ID`

### **Issue: "Google authentication error"**
**Solution:**
- Verify your service account JSON is valid
- Make sure you've shared the Google Sheet with the service account email
- Check that the Google Sheets API is enabled in your Google Cloud project

### **Issue: "403 Forbidden" when inserting rows**
**Solution:**
- Ensure the **output** Google Sheet is shared with the service account email
- The service account email is in the `client_email` field of your JSON

### **Issue: "Error connecting to input sheet"**
**Solution:**
- Ensure the **input** Google Sheet is shared with the service account email
- Check that the input sheet has data (at least headers and some rows)

## 🔒 **Security Notes**

- ✅ **Environment variables are encrypted** in Railway
- ✅ **No credential files** stored in your code
- ✅ **Secure storage** - Railway handles encryption
- ✅ **Easy updates** - Change credentials without code changes

## 📊 **Example Railway Dashboard Setup**

Your Railway Variables tab should look like this:

| Variable Name | Value |
|---------------|-------|
| `GOOGLE_CREDENTIALS_JSON` | `{"type": "service_account", "project_id": "...", ...}` |
| `GOOGLE_INPUT_SPREADSHEET_ID` | `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms` |
| `GOOGLE_OUTPUT_SPREADSHEET_ID` | `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms` |

That's it! Once you set these 3 environment variables, your Railway deployment will be able to read from your input Google Sheet and write processed data to your output Google Sheet. 🚀
