import sqlite3
import re
import hashlib
import math
from collections import defaultdict
from datetime import timedelta
from database import get_db_connection

def seconds_to_units(seconds):
    """
    Convert seconds to 6-minute units, rounded UP to nearest 0.1
    
    Examples:
    - 60 seconds (1 min) → 0.1 units (rounded up from 0.17)
    - 360 seconds (6 min) → 1.0 units (exact)
    - 450 seconds (7.5 min) → 1.3 units (rounded up from 1.25)
    - 1800 seconds (30 min) → 5.0 units (exact)
    """
    if seconds <= 0:
        return 0.1  # Minimum 1 unit for any activity
    
    units = seconds / 360  # 360 seconds = 6 minutes = 1 unit
    return math.ceil(units * 10) / 10  # Round up to nearest 0.1

def format_time_units(units):
    """Format time units for display (e.g., 1.5 units = "1.5 units (9 min)")"""
    minutes = units * 6
    return f"{units:.1f} units ({minutes:.0f} min)"

def clean_document_name(doc, activity):
    """
    Cleans up document names for better aggregation using a more robust pipeline.
    """
    cleaned_doc = doc

    # --- Step 1: Application-Specific Cleaning (Highest Priority) ---
    # This is often the most reliable way to get the core task name.
    if "Preview" in activity:
        # Remove page numbers and other Preview-specific suffixes.
        cleaned_doc = re.sub(r' – Page \d+ of \d+$', '', cleaned_doc)
        cleaned_doc = re.sub(r' – \d+ pages$', '', cleaned_doc)
    elif "microsoft word" in activity:
        cleaned_doc = cleaned_doc.replace('  -  Read-Only', '')

    # --- Step 2: General Noise Reduction (mostly for web browsers) ---
    # This removes dynamic titles added by browsers.
    noise_patterns = [
        r' - Google Chrome – .+$',
        r' - Google Chrome$',
        r' - Microsoft​ Edge$',
        r' — Mozilla Firefox$',
        r' \(\d+ unread\)$', # e.g., "Inbox (1 unread)"
    ]
    for pattern in noise_patterns:
        cleaned_doc = re.sub(pattern, '', cleaned_doc)

    # --- Step 3: Filename Fallback (The *.* idea) ---
    # If a filename-like pattern exists, it's a strong signal.
    # This helps catch cases missed by the specific rules.
    file_match = re.search(r'[\w\s\-\_\(\)\[\]]+\.(docx|pdf|xlsx|pptx|csv|md|txt|py|js|html|css)', cleaned_doc, re.IGNORECASE)
    if file_match:
        cleaned_doc = file_match.group(0).strip()

    # --- Step 4: Vague Name Filtering (Final Cleanup) ---
    # These are names that are almost never useful for time entries.
    VAGUE_NAMES = ["No Details", "Paste", "New Tab", "Untitled", "Reminders", "Calendar"]
    if cleaned_doc.strip() in VAGUE_NAMES or cleaned_doc.strip().startswith("Search, Suggestions"):
        return None
        
    return cleaned_doc.strip()

def get_canonical_name(doc, activity):
    """
    Determines the canonical (grouping) name for a raw document entry.
    Enhanced with better normalization to reduce duplicates.
    """
    cleaned_doc = doc

    # --- Step 1: Application-Specific Cleaning (Highest Priority) ---
    if "microsoft word" in activity:
        # Remove "Read-Only" and similar suffixes. This is a common source of duplication.
        cleaned_doc = re.sub(r'\s*-\s*Read-Only$', '', cleaned_doc, flags=re.IGNORECASE).strip()
        # Remove " - Compatibility Mode" suffix (handle multiple spaces)
        cleaned_doc = re.sub(r'\s+-\s+Compatibility Mode$', '', cleaned_doc, flags=re.IGNORECASE).strip()
        
        # Normalize bracket variations - convert [22069] to 22069 format for consistency
        cleaned_doc = re.sub(r'_\[(\d+)\]', r'_\1', cleaned_doc)
        
        # Normalize Portal naming - consolidate variations
        if cleaned_doc.startswith('Portal'):
            # Convert "Portal - Analytics" to "Portal Analytics" for consistency
            cleaned_doc = re.sub(r'^Portal\s*-\s*', 'Portal ', cleaned_doc)
            # Convert multiple spaces to single space
            cleaned_doc = re.sub(r'\s+', ' ', cleaned_doc)
        
        # Filter out generic document names that aren't useful for billing
        if re.match(r'^Document\d+$', cleaned_doc):
            return None  # Filter out Document1, Document2, etc.
            
        return cleaned_doc

    if "Preview" in activity and ".pdf" in doc:
        # For PDFs in Preview, the canonical name is the PDF filename itself.
        match = re.search(r'(.+?\.pdf)', doc)
        if match:
            return match.group(1).strip()

    # --- Step 2: General Fallback for other file types ---
    file_match = re.search(r'([\w\s\-\_\[\]]+\.(docx|xlsx|pptx|csv|md|txt|py|js|html|css))', cleaned_doc, re.IGNORECASE)
    if file_match:
        return file_match.group(1).strip()

    # If no file-based rule applies, return the document name for further filtering.
    return doc

def is_vague_name(doc_name):
    """Checks if a document name is vague and should be filtered out."""
    doc_stripped = doc_name.strip()
    
    # Safety check: Never filter descriptions longer than 25 characters
    # This ensures we only remove short, generic terms, not descriptive entries
    if len(doc_stripped) > 25:
        return False
    
    VAGUE_NAMES = [
        "No Details", "Paste", "New Tab", "Untitled", "Reminders", "Calendar", 
        "Microsoft Teams", "Cursor", "ALP Clone", "Coding", "Notes",
        "Balloons", "Accept", "Table of Contents", "Change Case", "Styles",
        "Text Highlight Color", "Markup Options", "Open new and recent files",
        # Generic single words (only filtered if short)
        "TV", "Downloads", "Recents", "OneDrive", "Google", "Welcome", "GitHub",
        "Rules", "RescueTime", "Copilot", "reMarkable", "Pilot"
    ]
    
    # Exact matches for short terms
    if doc_stripped in VAGUE_NAMES:
        return True
        
    # Pattern-based filtering (also only for short terms)
    if (doc_stripped.startswith("Search, Suggestions") or
        re.match(r'^Document\d+$', doc_stripped) or  # Document1, Document2, etc.
        re.match(r'^\d+ Reminder$', doc_stripped) or  # "1 Reminder", etc.
        doc_stripped in ["Downloads", "Recent", "TV"]):  # Common system folders/apps
        return True
        
    return False

def extract_matter_code(task_description):
    """
    Extracts 5-digit matter codes from task descriptions.
    Only extracts 5-digit numbers that are properly delimited to avoid partial dates.
    Returns the first valid matter code found, or None if no code is found.
    """
    if not task_description:
        return None
    
    # Pattern 1: Square brackets [12345] - surrounded by brackets
    bracket_match = re.search(r'\[(\d{5})\]', task_description)
    if bracket_match:
        return bracket_match.group(1)
    
    # Pattern 2: Underscores _12345_ - surrounded by underscores
    underscore_surrounded = re.search(r'_(\d{5})_', task_description)
    if underscore_surrounded:
        return underscore_surrounded.group(1)
    
    # Pattern 3: Underscore before, non-digit after: _12345 (space, underscore, or end)
    underscore_before = re.search(r'_(\d{5})(?=[_\s]|$)', task_description)
    if underscore_before:
        return underscore_before.group(1)
    
    # Pattern 4: Non-digit before, underscore after: (space or start) 12345_
    underscore_after = re.search(r'(?:^|[_\s])(\d{5})_', task_description)
    if underscore_after:
        return underscore_after.group(1)
    
    # Pattern 5: Space delimited: (space or start) 12345 (space or end)
    space_delimited = re.search(r'(?:^|\s)(\d{5})(?:\s|$)', task_description)
    if space_delimited:
        return space_delimited.group(1)
    
    return None

def get_source_hash(date_str, application, task_description):
    """Creates a unique hash for a given task."""
    hash_input = f"{date_str}-{application}-{task_description}".encode('utf-8')
    return hashlib.md5(hash_input).hexdigest()

def process_all_data(debug=False, start_date=None, end_date=None):
    """
    Processes unprocessed raw data (or date range), aggregating per day.
    Since fetch now clears data before insertion, unprocessed records represent
    complete data for their respective dates, ensuring proper aggregation.
    Groups by (date, application, canonical_name) so each day gets separate entries.
    """
    conn = get_db_connection()
    
    # Get only unprocessed data
    from database import get_unprocessed_data, mark_records_as_processed
    rows = get_unprocessed_data(start_date, end_date)
    
    if not rows:
        date_filter_msg = ""
        if start_date and end_date:
            date_filter_msg = f" for date range {start_date} to {end_date}"
        elif start_date:
            date_filter_msg = f" from {start_date}"
        elif end_date:
            date_filter_msg = f" until {end_date}"
        print(f"No unprocessed data found{date_filter_msg}.")
        return

    # --- Data Aggregation Per Day ---
    grouped_tasks = defaultdict(list)
    processed_record_ids = []  # Track records we successfully process
    
    for row in rows:
        canonical_name = get_canonical_name(row['document'], row['activity'])
        
        # Apply general noise reduction after getting the canonical name
        if canonical_name:
            noise_patterns = [
                r' - Google Chrome – .+$', r' - Google Chrome$',
                r' - Microsoft​ Edge$', r' — Mozilla Firefox$',
                r' \(\d+ unread\)$',
            ]
            for pattern in noise_patterns:
                canonical_name = re.sub(pattern, '', canonical_name)

        if canonical_name and not is_vague_name(canonical_name):
            # Key includes date - this creates separate entries per day
            key = (row['log_date'], row['activity'], canonical_name)
            grouped_tasks[key].append(row)
            # Track this record for marking as processed later
            processed_record_ids.append((row['log_date'], row['activity'], row['document']))

    if debug:
        # --- Debug Mode: Print Analysis and Exit ---
        date_filter_msg = ""
        if start_date and end_date:
            date_filter_msg = f" (dates {start_date} to {end_date})"
        elif start_date:
            date_filter_msg = f" (from {start_date})"
        elif end_date:
            date_filter_msg = f" (until {end_date})"
            
        print(f"\n--- Processing Analysis{date_filter_msg} ---")
        print(f"{'Date':<12} | {'Task Description':<45} | {'Time':<8}")
        print("-" * 70)
        for (date, application, canonical_name), task_rows in sorted(grouped_tasks.items()):
            total_time = sum(r['time_spent_seconds'] for r in task_rows)
            hours_mins = f"{total_time//3600}h {(total_time%3600)//60}m"
            print(f"{date:<12} | {canonical_name[:43]:<45} | {hours_mins:<8}")
        
        print(f"\nTotal unprocessed records: {len(rows)}")
        print(f"Records that would be processed: {len(processed_record_ids)}")
        print(f"Unique task-day combinations: {len(grouped_tasks)}")
        return

    if not grouped_tasks:
        print("No valid tasks found in unprocessed data after cleaning.")
        return

    total_raw_seconds = sum(row['time_spent_seconds'] for row in rows)
    dates = sorted(set(row['log_date'] for row in rows))
    print(f"Processing {len(grouped_tasks)} unique task-day combinations from {len(rows)} unprocessed records...")

    # --- Prepare for Upsert ---
    entries_to_upsert = []
    total_processed_seconds = 0
    for (date, application, canonical_name), task_rows in grouped_tasks.items():
        # Sum the time for all entries for this task on this specific date
        # Since fetch clears data before insertion, this represents complete aggregation
        total_seconds = sum(r['time_spent_seconds'] for r in task_rows)
        task_description = canonical_name
        
        # Extract matter code from task description
        matter_code = extract_matter_code(task_description)
        
        # Use the original per-date source hash
        source_hash = get_source_hash(date, application, canonical_name)
        time_units = seconds_to_units(total_seconds)
        entries_to_upsert.append((date, application, task_description, total_seconds, time_units, source_hash, matter_code))
        total_processed_seconds += total_seconds

    # --- Database Upsert ---
    cursor = conn.cursor()
    upsert_sql = """
    INSERT INTO time_entries (entry_date, application, task_description, total_seconds, time_units, source_hash, matter_code)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(source_hash) DO UPDATE SET
        total_seconds = excluded.total_seconds,
        time_units = excluded.time_units,
        task_description = excluded.task_description,
        matter_code = excluded.matter_code,
        updated_at = CURRENT_TIMESTAMP;
    """

    try:
        cursor.executemany(upsert_sql, entries_to_upsert)
        conn.commit()
        
        # Mark processed records as processed
        mark_records_as_processed(processed_record_ids)
        
        print(f"Successfully processed and saved {len(entries_to_upsert)} time entries.")
    except sqlite3.Error as e:
        print(f"Database error during processing: {e}")
        conn.rollback()
    finally:
        conn.close()

    # --- Summary Report ---
    date_range = f"{dates[0]} to {dates[-1]}" if len(dates) > 1 else dates[0]
    leakage_seconds = total_raw_seconds - total_processed_seconds
    leakage_percentage = (leakage_seconds / total_raw_seconds * 100) if total_raw_seconds > 0 else 0
    
    print("\n--- Processing Summary ---")
    print(f"Date range processed:      {date_range}")
    print(f"Unprocessed records:       {len(rows)}")
    print(f"Records marked processed:  {len(processed_record_ids)}")
    print(f"Total time in processed:   {timedelta(seconds=total_processed_seconds)}")
    print(f"Filtered time (leakage):   {timedelta(seconds=leakage_seconds)} ({leakage_percentage:.2f}%)")
    print("-" * 45)

def get_cross_date_source_hash(application, task_description):
    """Creates a unique hash for a task across all dates (no date component)."""
    hash_input = f"{application}-{task_description}".encode('utf-8')
    return hashlib.md5(hash_input).hexdigest()

def process_data_for_date(date_str, debug=False):
    """
    Processes raw data for a date, aggregates it, and upserts it into the time_entries table.
    Includes a debug mode to analyze the cleaning process.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activity_log WHERE log_date = ?", (date_str,))
    rows = cursor.fetchall()
    
    if not rows:
        print(f"No raw data found for {date_str}. Run the 'fetch' command first.")
        conn.close()
        return

    # --- Data Aggregation ---
    # We now group raw entries by a canonical name, but store the originals.
    grouped_tasks = defaultdict(list)
    for row in rows:
        canonical_name = get_canonical_name(row['document'], row['activity'])
        
        # Apply general noise reduction after getting the canonical name
        # Only apply if canonical_name is not None
        if canonical_name:
            noise_patterns = [
                r' - Google Chrome – .+$', r' - Google Chrome$',
                r' - Microsoft​ Edge$', r' — Mozilla Firefox$',
                r' \(\d+ unread\)$',
            ]
            for pattern in noise_patterns:
                canonical_name = re.sub(pattern, '', canonical_name)

        if canonical_name and not is_vague_name(canonical_name):
            key = (row['activity'], canonical_name)
            grouped_tasks[key].append(row)

    if debug:
        # --- Debug Mode: Print Analysis and Exit ---
        print("\n--- Cleaning Analysis Report ---")
        print(f"{'Original Document':<60} | {'Canonical Name':<60} | {'Status'}")
        print("-" * 140)
        for row in rows:
            original_doc = row['document']
            canonical_name = get_canonical_name(original_doc, row['activity'])
            
            # Replicate the full cleaning logic for accurate debugging
            # Only apply noise reduction if canonical_name is not None
            if canonical_name:
                noise_patterns = [
                    r' - Google Chrome – .+$', r' - Google Chrome$',
                    r' - Microsoft​ Edge$', r' — Mozilla Firefox$',
                    r' \(\d+ unread\)$',
                ]
                for pattern in noise_patterns:
                    canonical_name = re.sub(pattern, '', canonical_name)

            status = "Kept" if canonical_name and not is_vague_name(canonical_name) else "Filtered Out"
            print(f"{original_doc[:58]:<60} | {(canonical_name or 'N/A')[:58]:<60} | {status}")
        conn.close()
        return

    total_raw_seconds = sum(row['time_spent_seconds'] for row in rows)
    
    print(f"Processing {len(grouped_tasks)} unique tasks for {date_str}...")

    # --- Prepare for Upsert ---
    entries_to_upsert = []
    total_processed_seconds = 0
    for (application, canonical_name), task_rows in grouped_tasks.items():
        # Sum the time for all entries in the group
        total_seconds = sum(r['time_spent_seconds'] for r in task_rows)
        # The final description should be the clean, canonical name itself.
        task_description = canonical_name
        
        # Extract matter code from task description
        matter_code = extract_matter_code(task_description)
        
        source_hash = get_source_hash(date_str, application, canonical_name)
        time_units = seconds_to_units(total_seconds)
        entries_to_upsert.append((date_str, application, task_description, total_seconds, time_units, source_hash, matter_code))
        total_processed_seconds += total_seconds

    # --- Database Upsert ---
    upsert_sql = """
    INSERT INTO time_entries (entry_date, application, task_description, total_seconds, time_units, source_hash, matter_code)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(source_hash) DO UPDATE SET
        total_seconds = excluded.total_seconds,
        time_units = excluded.time_units,
        task_description = excluded.task_description,
        matter_code = excluded.matter_code,
        updated_at = CURRENT_TIMESTAMP;
    """

    try:
        cursor.executemany(upsert_sql, entries_to_upsert)
        conn.commit()
        print(f"Successfully processed and saved {len(entries_to_upsert)} time entries.")
    except sqlite3.Error as e:
        print(f"Database error during processing: {e}")
        conn.rollback()
    finally:
        conn.close()

    # --- Leakage Report ---
    leakage_seconds = total_raw_seconds - total_processed_seconds
    leakage_percentage = (leakage_seconds / total_raw_seconds * 100) if total_raw_seconds > 0 else 0
    
    print("\n--- Data Processing Summary ---")
    print(f"Total time in raw logs:    {timedelta(seconds=total_raw_seconds)}")
    print(f"Total time in time entries: {timedelta(seconds=total_processed_seconds)}")
    print(f"Unaccounted time (leakage): {timedelta(seconds=leakage_seconds)} ({leakage_percentage:.2f}%)")
    print("---------------------------------")


def update_time_entry(entry_id, status=None, notes=None):
    """Updates the status or notes of a time entry."""
    if not status and not notes:
        print("No update provided. Please specify a status or notes.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    if status:
        updates.append("status = ?")
        params.append(status)
    if notes:
        updates.append("notes = ?")
        params.append(notes)
    
    params.append(entry_id)
    
    update_sql = f"UPDATE time_entries SET {', '.join(updates)} WHERE entry_id = ?"
    
    try:
        cursor.execute(update_sql, params)
        if cursor.rowcount == 0:
            print(f"Error: No time entry found with ID {entry_id}.")
        else:
            conn.commit()
            print(f"Successfully updated time entry {entry_id}.")
    except sqlite3.Error as e:
        print(f"Database error during update: {e}")
    finally:
        conn.close() 