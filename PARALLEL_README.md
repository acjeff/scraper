# Parallel URL Scraper with Chunking and Resume

This system provides a much faster and more robust way to process your large TestLinks.csv file.

## 🆕 **NEW: Super Memory Efficient Google Sheets Scraper**

For the most memory-efficient solution, check out the new Google Sheets scraper:

- **Zero local storage** - Data goes directly to Google Sheets
- **Immediate memory clearing** - No memory buildup
- **Easy tracking** - Resume from any row number
- **Crash-proof** - Data saved after each link

**Files:**
- `memory_efficient_google_sheets_scraper.py` - Main scraper
- `resume_google_sheets_scraper.py` - Resume functionality
- `GOOGLE_SHEETS_SETUP.md` - Complete setup guide

**Quick Start:**
```bash
# Install dependencies
pip install -r requirements_google_sheets.txt

# Set up Google credentials (see GOOGLE_SHEETS_SETUP.md)
# Update SPREADSHEET_ID in the script

# Run the scraper
python3 memory_efficient_google_sheets_scraper.py
```

---

## 🚀 **Speed Improvements**

### **Original Sequential Processing:**
- **Time**: ~40-45 hours (1.7 days)
- **Method**: One URL at a time
- **Risk**: If it stops, you lose all progress

### **New Parallel Processing:**
- **Time**: ~8-12 hours (overnight!)
- **Method**: 4-8 URLs processed simultaneously
- **Safety**: Chunked processing with resume capability

## 📁 **How It Works**

### **Step 1: Split into Chunks**
- Splits your 24,523 URLs into chunks of 100 URLs each
- Creates ~245 chunk files in `chunks/` folder

### **Step 2: Parallel Processing**
- Processes multiple chunks simultaneously
- Each chunk processes 10 URLs in parallel
- Saves results to `processed_chunks/` folder

### **Step 3: Resume Capability**
- If processing stops, you can resume from where it left off
- Already processed chunks are skipped
- Final combination creates `UpdatedTestLinks.csv`

## 🛠️ **Usage Instructions**

### **First Time Setup:**
```bash
python3 parallel_scraper.py
```

### **If Processing Stops - Resume:**
```bash
python3 resume_scraper.py
```

### **Check Progress:**
```bash
python3 resume_scraper.py
```
(This will show you how many chunks are processed vs remaining)

## 📊 **Expected Performance**

### **With 4 CPU Cores:**
- **Processing Speed**: ~4x faster than sequential
- **Estimated Time**: 8-12 hours
- **Memory Usage**: ~2-4GB RAM

### **With 8 CPU Cores:**
- **Processing Speed**: ~6-8x faster than sequential  
- **Estimated Time**: 5-8 hours
- **Memory Usage**: ~4-6GB RAM

## 🔧 **Configuration Options**

### **Adjust Chunk Size:**
In `parallel_scraper.py`, change:
```python
chunk_size = 100  # Increase for fewer files, decrease for more granularity
```

### **Adjust Parallel Workers:**
In `parallel_scraper.py`, change:
```python
max_workers=4  # Increase for more parallel processing
```

### **Adjust Batch Size:**
In `process_chunk_file()`, change:
```python
batch_size = 10  # URLs processed simultaneously within each chunk
```

## 📂 **File Structure**

```
scraper/
├── TestLinks.csv                    # Your input file
├── parallel_scraper.py              # Main parallel processor
├── resume_scraper.py                # Resume functionality
├── chunks/                          # Split CSV chunks
│   ├── chunk_0001.csv
│   ├── chunk_0002.csv
│   └── ...
├── processed_chunks/                # Processed results
│   ├── chunk_0001_processed.csv
│   ├── chunk_0002_processed.csv
│   └── ...
└── UpdatedTestLinks.csv             # Final combined output
```

## ⚠️ **Important Notes**

1. **Don't delete the `chunks/` or `processed_chunks/` folders** - they're needed for resume functionality
2. **Monitor disk space** - you'll need ~500MB for temporary files
3. **Keep your computer awake** - processing will stop if it goes to sleep
4. **Check progress regularly** - use `resume_scraper.py` to see status

## 🎯 **Recommended Workflow**

1. **Start before bed**: Run `python3 parallel_scraper.py`
2. **Check in morning**: Run `python3 resume_scraper.py` to see progress
3. **If incomplete**: Let it continue, or resume manually
4. **When complete**: You'll have `UpdatedTestLinks.csv` with all extracted data

## 🔍 **Troubleshooting**

### **If it stops unexpectedly:**
```bash
python3 resume_scraper.py
```

### **If you want to start over:**
```bash
rm -rf chunks/ processed_chunks/
python3 parallel_scraper.py
```

### **If you want to process a smaller test:**
```bash
# Copy a few lines from TestLinks.csv to test_parallel_small.csv
# Then modify parallel_scraper.py to use test_parallel_small.csv
```

This system should reduce your processing time from 2 days to overnight! 🚀
