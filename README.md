# RescueTime Time-Entry Assistant

A powerful Python application that transforms RescueTime data into clean, aggregated time entries perfect for legal practice management software and professional time tracking.

## 🎯 Overview

The RescueTime Time-Entry Assistant bridges the gap between RescueTime's detailed activity tracking and professional time billing requirements. It automatically:

- **Fetches** raw activity data from RescueTime API
- **Cleans** and aggregates document-level activities  
- **Identifies** client matter codes from document names
- **Prevents** duplicate entries with intelligent source hashing
- **Tracks** current day progress with periodic updates
- **Exports** ready-to-bill time entries

Perfect for lawyers, consultants, and professionals who need accurate billable time tracking.

## 🚀 Key Features

### **Intelligent Data Processing**
- **Document Aggregation**: Consolidates PDF page views, Word read-only copies, and browser tabs into single time entries
- **Smart Cleaning**: Removes noise like "Page 1 of 67", "Read-Only", browser titles
- **Matter Code Detection**: Automatically extracts 5-digit matter codes from document names
- **Duplicate Prevention**: Source hash system prevents duplicate billing entries

### **Flexible Time Tracking**
- **Historical Data**: Fetch and process multiple days of past activity
- **Current Day Tracking**: Real-time updates throughout the workday
- **Periodic Updates**: Smart interval-based refresh (15-min default)
- **Manual Override**: Force updates when needed

### **Professional Workflow**
- **Status Management**: Track entries as pending, submitted, or in-progress
- **Notes System**: Add detailed descriptions for billing context
- **CSV Export**: Generate reports for practice management software
- **Data Integrity**: Manual changes preserved during updates

## 📋 Prerequisites

- Python 3.7+
- RescueTime account with API access
- RescueTime API key ([Get yours here](https://www.rescuetime.com/anapi/manage))

## 🛠️ Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Access

Create a `.env` file in the project directory:

```bash
API_KEY=YOUR_RESCUETIME_API_KEY_HERE
```

Get your API key from the [RescueTime API management page](https://www.rescuetime.com/anapi/manage).

### 3. Initialize Database

```bash
python main.py initdb
```

This creates a local SQLite database (`rescuetime.db`) to store your activity data and time entries.

## 📖 Usage Guide

### **Basic Workflow**

```bash
# 1. Fetch recent activity data
python main.py fetch --days 3

# 2. Process raw data into time entries  
python main.py process-all

# 3. Generate a report
python main.py report --date 2025-07-18 --export
```

### **Command Reference**

#### **Data Fetching**

```bash
# Fetch last 3 days of data
python main.py fetch --days 3

# Update current day only (smart interval protection)
python main.py fetch --current

# Force current day update (ignore interval)
python main.py fetch --current --force
```

#### **Data Processing**

```bash
# Process specific date
python main.py process --date 2025-07-18

# Process all unprocessed data
python main.py process-all

# Process with cleaning analysis (debug mode)
python main.py process --date 2025-07-18 --debug
```

#### **Periodic Updates**

```bash
# Smart auto-update (checks if update needed)
python main.py auto-update

# Auto-update with custom interval (5 minutes)
python main.py auto-update --interval 5

# Force auto-update regardless of timing
python main.py auto-update --force
```

#### **Time Entry Management**

```bash
# View daily report
python main.py report --date 2025-07-18

# Export to CSV
python main.py report --date 2025-07-18 --export

# Update entry status
python main.py update --id 123 --status "submitted"

# Add notes to entry
python main.py update --id 123 --notes "Client meeting re contract review"

# Update both status and notes
python main.py update --id 123 --status "in_progress" --notes "Draft legal brief"
```

#### **Database Management**

```bash
# Clear all processed time entries
python main.py clear

# Reinitialize database (preserves existing data)
python main.py initdb
```

## 🔄 Typical Daily Workflow

### **Morning Setup** (5 minutes)
```bash
# Get yesterday's complete data + any recent days
python main.py fetch --days 2
python main.py process-all

# Review yesterday's entries
python main.py report --date 2025-07-17 --export
```

### **Throughout the Day** (automated)
```bash
# Set up periodic current day tracking (every 15-30 minutes)
python main.py auto-update
```

### **End of Day** (2 minutes)
```bash
# Final current day update
python main.py fetch --current --force

# Review and update entries
python main.py report --date 2025-07-18
python main.py update --id 456 --status "submitted" --notes "Client consultation"

# Export for billing
python main.py report --date 2025-07-18 --export
```

## 📊 Data Processing Intelligence

### **Document Aggregation Examples**

| Raw RescueTime Data | Cleaned Result |
|---------------------|----------------|
| `Trust_Deed_27_Jan_2000.pdf – Page 1 of 67`<br>`Trust_Deed_27_Jan_2000.pdf – Page 2 of 67`<br>`Trust_Deed_27_Jan_2000.pdf – Page 15 of 67` | `Trust_Deed_27_Jan_2000.pdf`<br>**Total: 45 minutes** |
| `Contract_Review_22069.docx`<br>`Contract_Review_22069.docx - Read-Only` | `Contract_Review_22069.docx`<br>**Matter: 22069** |

### **Matter Code Detection**

The system automatically detects 5-digit matter codes in these formats:
- `[12345]` - Square brackets
- `_12345_` - Surrounded by underscores  
- `Document_12345_Final.pdf` - Within filename
- `Client Meeting 12345 Notes` - Space delimited

### **Smart Filtering**

Automatically filters out non-billable activities:
- Browser navigation ("New Tab", "Search")
- System activities ("Downloads", "Settings")
- Short generic terms (< 25 characters)
- Application-specific noise (unread counts, page numbers)

## 📈 Sample Output

```
--- Time Entry Report for 2025-07-18 ---
ID    Application          Task Description                                   Time         Status       Notes
------------------------------------------------------------------------------------------------------------------
1001  microsoft word       Trust_Deed_27_Jan_2000.pdf                        01:45:23     pending      
1002  Microsoft Teams      Weekly Client Review | SYNTAQ                     00:33:07     submitted    
1003  microsoft outlook    Client_Correspondence_22069                       00:28:15     in_progress  Follow-up required
1004  Preview              Contract_Analysis_22155.pdf                       00:22:30     pending      
1005  Cursor               Legal_Brief_Draft.docx                            00:18:45     submitted    
```

## 🔧 Advanced Configuration

### **Custom Intervals**
- Default: 15 minutes between current day updates
- Minimum: 1 minute (for testing)
- Recommended: 15-30 minutes for production

### **Matter Code Patterns**
The system uses regex patterns to extract matter codes. Modify `extract_matter_code()` in `processor.py` to customize for your firm's naming conventions.

### **Cleaning Rules**
Document cleaning rules are in `get_canonical_name()` in `processor.py`. Add custom patterns for your specific applications or document types.

## 📁 File Structure

```
rescuetime/
├── main.py              # CLI interface and command handlers
├── database.py          # SQLite database operations
├── fetcher.py           # RescueTime API client
├── processor.py         # Data cleaning and aggregation
├── reporter.py          # Report generation and CSV export
├── requirements.txt     # Python dependencies
├── .env                 # API key configuration (create this)
├── rescuetime.db        # SQLite database (auto-created)
└── README.md           # This file
```

## 🗄️ Database Schema

### **activity_log** - Raw RescueTime Data
- `log_date`, `activity`, `document` (Primary Key)
- `time_spent_seconds`, `category`, `productivity`
- `processed` flag for incremental processing

### **time_entries** - Processed Time Entries  
- `entry_id` (Primary Key)
- `entry_date`, `application`, `task_description`
- `total_seconds`, `status`, `notes`, `matter_code`
- `source_hash` (prevents duplicates)

### **update_metadata** - System Tracking
- Tracks last current day update timing
- Enables smart interval protection

## 🛡️ Data Integrity Features

- **Source Hash System**: Prevents duplicate time entries during re-processing
- **Clearing Approach**: Complete data refresh ensures accurate aggregation
- **Manual Preservation**: Status and notes survive automatic updates
- **Incremental Processing**: Only processes unprocessed raw data for efficiency

## 🚨 Troubleshooting

### **No Data Returned**
- Verify API key in `.env` file
- Check date format (YYYY-MM-DD)
- Ensure RescueTime has data for the requested date

### **Processing Errors**
- Run with `--debug` flag to see cleaning analysis
- Check for missing database initialization: `python main.py initdb`

### **Duplicate Entries**
- The system prevents duplicates automatically via source hashing
- If you see duplicates, they may be legitimate separate activities

### **Current Day Updates Not Working**
- Check interval timing with `python main.py auto-update`
- Use `--force` flag to override interval protection
- Verify RescueTime is tracking current activity

## 📞 Support

For issues or feature requests:
1. Check the troubleshooting section above
2. Review command help: `python main.py --help`
3. Use debug mode: `python main.py process --debug`

## 📄 License

This project is for professional time tracking and billing assistance. Ensure compliance with your organization's data handling policies.

---

**Transform your RescueTime data into billable hours with precision and confidence.** ⚡ 