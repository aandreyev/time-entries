import sqlite3
import os
from datetime import datetime, timedelta, date

def convert_db_entry_to_dict(row):
    """Convert database row to dict with proper date conversion for Pydantic."""
    entry_dict = dict(row)
    
    # Convert entry_date string to date object if present
    if 'entry_date' in entry_dict and entry_dict['entry_date']:
        try:
            # Parse YYYY-MM-DD string to date object
            entry_dict['entry_date'] = datetime.strptime(entry_dict['entry_date'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            # Keep as string if parsing fails
            pass
    
    return entry_dict

DB_FILE = "rescuetime.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Initializes the database and creates tables with enhanced schema."""
    if os.path.exists(DB_FILE):
        print("Database already exists.")
    else:
        print("Creating new database...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Enhanced activity_log table with processing tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        log_date TEXT NOT NULL,
        time_spent_seconds INTEGER NOT NULL,
        activity TEXT NOT NULL,
        category TEXT,
        productivity INTEGER,
        document TEXT,
        processed INTEGER NOT NULL DEFAULT 0,  -- 0 = unprocessed, 1 = processed
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (log_date, activity, document)
    )
    """)

    # Enhanced time_entries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS time_entries (
        entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT NOT NULL,
        application TEXT NOT NULL,
        task_description TEXT NOT NULL,
        total_seconds INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        notes TEXT,
        matter_code TEXT,
        source_hash TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Metadata table for tracking update times
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS update_metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Add indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_log_processed ON activity_log(processed)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_log_date ON activity_log(log_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_date ON time_entries(entry_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_matter ON time_entries(matter_code)")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def mark_date_for_reprocessing(date_str):
    """Sets the 'processed' flag to 0 for all records on a specific date."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE activity_log SET processed = 0 WHERE log_date = ?", (date_str,))
        conn.commit()
        print(f"Marked all entries for {date_str} for reprocessing.")
    finally:
        conn.close()

def upsert_activity_data(data_list):
    """
    Upserts activity data, marking records as unprocessed when updated.
    This preserves existing data while allowing for updates.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    upsert_sql = """
    INSERT INTO activity_log (log_date, time_spent_seconds, activity, category, productivity, document, processed)
    VALUES (?, ?, ?, ?, ?, ?, 0)
    ON CONFLICT(log_date, activity, document) DO UPDATE SET
        time_spent_seconds = excluded.time_spent_seconds,
        category = excluded.category,
        productivity = excluded.productivity,
        processed = 0,  -- Mark as unprocessed when data changes
        updated_at = CURRENT_TIMESTAMP
    """
    
    try:
        cursor.executemany(upsert_sql, data_list)
        conn.commit()
        print(f"Successfully upserted {len(data_list)} activity records.")
        return len(data_list)
    except sqlite3.Error as e:
        print(f"Database error during upsert: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def get_unprocessed_data(start_date=None, end_date=None):
    """
    Gets all unprocessed activity data, optionally filtered by date range.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if start_date and end_date:
        cursor.execute("""
            SELECT * FROM activity_log 
            WHERE processed = 0 AND log_date BETWEEN ? AND ? 
            ORDER BY log_date, activity, document
        """, (start_date, end_date))
    elif start_date:
        cursor.execute("""
            SELECT * FROM activity_log 
            WHERE processed = 0 AND log_date >= ? 
            ORDER BY log_date, activity, document
        """, (start_date,))
    elif end_date:
        cursor.execute("""
            SELECT * FROM activity_log 
            WHERE processed = 0 AND log_date <= ? 
            ORDER BY log_date, activity, document
        """, (end_date,))
    else:
        cursor.execute("""
            SELECT * FROM activity_log 
            WHERE processed = 0 
            ORDER BY log_date, activity, document
        """)
    
    rows = cursor.fetchall()
    conn.close()
    return rows

def mark_records_as_processed(record_ids):
    """
    Marks specified activity_log records as processed.
    record_ids should be a list of (log_date, activity, document) tuples.
    """
    if not record_ids:
        return 0
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    update_sql = """
    UPDATE activity_log 
    SET processed = 1, updated_at = CURRENT_TIMESTAMP 
    WHERE log_date = ? AND activity = ? AND document = ?
    """
    
    try:
        cursor.executemany(update_sql, record_ids)
        affected_rows = cursor.rowcount
        conn.commit()
        print(f"Marked {affected_rows} records as processed.")
        return affected_rows
    except sqlite3.Error as e:
        print(f"Database error marking records as processed: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def clear_time_entries():
    """Deletes all records from the time_entries table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM time_entries")
    conn.commit()
    conn.close()
    print("Cleared all records from the time_entries table.")

# Backward compatibility - deprecated functions
def clear_data_for_date(date_str):
    """DEPRECATED: Use mark_date_for_reprocessing instead."""
    print("WARNING: clear_data_for_date is deprecated. Use mark_date_for_reprocessing instead.")
    return mark_date_for_reprocessing(date_str)

def insert_activity_data(data):
    """DEPRECATED: Use upsert_activity_data instead."""
    print("WARNING: insert_activity_data is deprecated. Use upsert_activity_data instead.")
    return upsert_activity_data(data)

def set_last_current_day_update(date_str=None):
    """Records when we last updated current day data."""
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    timestamp = datetime.now().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO update_metadata (key, value, updated_at)
        VALUES ('last_current_day_update', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = CURRENT_TIMESTAMP
    """, (f"{date_str}|{timestamp}",))
    
    conn.commit()
    conn.close()

def get_last_current_day_update():
    """Gets info about the last current day update."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT value, updated_at FROM update_metadata 
        WHERE key = 'last_current_day_update'
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        value, updated_at = result
        try:
            date_str, timestamp = value.split('|', 1)
            return {
                'date': date_str,
                'timestamp': timestamp,
                'db_updated_at': updated_at
            }
        except ValueError:
            return None
    return None

def should_update_current_day(min_interval_minutes=15):
    """Determines if current day should be updated based on last update time."""
    
    today = datetime.now().strftime('%Y-%m-%d')
    last_update = get_last_current_day_update()
    
    if not last_update:
        return True, "No previous current day update found"
    
    if last_update['date'] != today:
        return True, f"Last update was for {last_update['date']}, today is {today}"
    
    try:
        last_timestamp = datetime.fromisoformat(last_update['timestamp'])
        minutes_since = (datetime.now() - last_timestamp).total_seconds() / 60
        
        if minutes_since >= min_interval_minutes:
            return True, f"Last update was {minutes_since:.1f} minutes ago"
        else:
            return False, f"Last update was only {minutes_since:.1f} minutes ago (min interval: {min_interval_minutes}m)"
    except Exception as e:
        return True, f"Error parsing last update time: {e}"

def get_pending_time_entries():
    """Retrieves all time entries with a 'pending' status."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM time_entries WHERE status = 'pending' ORDER BY entry_date DESC")
        entries = cursor.fetchall()
        return [convert_db_entry_to_dict(row) for row in entries]
    finally:
        conn.close()

def get_time_entries_by_date(date):
    """Retrieves all time entries for a specific date."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Convert date object to string for SQL query if needed
        date_str = date.strftime('%Y-%m-%d') if isinstance(date, datetime) or hasattr(date, 'strftime') else str(date)
        cursor.execute("SELECT * FROM time_entries WHERE entry_date = ? ORDER BY created_at DESC", (date_str,))
        entries = cursor.fetchall()
        return [convert_db_entry_to_dict(row) for row in entries]
    finally:
        conn.close()

def update_time_entry(entry_id, status=None, notes=None):
    """Updates a time entry's status and/or notes without affecting time aggregation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build update query dynamically
    updates = []
    params = []
    
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    
    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)
    
    if not updates:
        print("No updates specified.")
        conn.close()
        return False
    
    # Add updated timestamp
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(entry_id)
    
    update_sql = f"""
    UPDATE time_entries 
    SET {', '.join(updates)}
    WHERE entry_id = ?
    """
    
    try:
        cursor.execute(update_sql, params)
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ Updated time entry {entry_id}")
            
            # Show the updated entry
            cursor.execute("SELECT * FROM time_entries WHERE entry_id = ?", (entry_id,))
            updated_entry = cursor.fetchone()
            if updated_entry:
                print(f"   Status: {updated_entry['status']}")
                if updated_entry['notes']:
                    print(f"   Notes: {updated_entry['notes']}")
            
            return True
        else:
            print(f"❌ No time entry found with ID {entry_id}")
            return False
            
    except sqlite3.Error as e:
        print(f"Database error updating entry: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_time_entry_status(entry_id: int, status: str):
    """Updates the status of a specific time entry."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE time_entries SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE entry_id = ?", (status, entry_id))
        if cursor.rowcount == 0:
            raise ValueError(f"No time entry found with ID {entry_id}")
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        raise Exception(f"Database error updating entry status: {e}")
    finally:
        conn.close()

def get_processed_time_entries(date=None):
    """Retrieves processed time entries, optionally filtered by date."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if date:
            # Convert date object to string for SQL query if needed
            date_str = date.strftime('%Y-%m-%d') if isinstance(date, datetime) or hasattr(date, 'strftime') else str(date)
            cursor.execute("""
                SELECT * FROM processed_time_entries 
                WHERE entry_date = ? 
                ORDER BY created_at DESC
            """, (date_str,))
        else:
            cursor.execute("""
                SELECT * FROM processed_time_entries 
                ORDER BY entry_date DESC, created_at DESC
            """)
        entries = cursor.fetchall()
        return [convert_db_entry_to_dict(row) for row in entries]
    finally:
        conn.close()

def create_processed_time_entry(entry_data):
    """Creates or updates a processed time entry (upsert on source_hash+entry_date)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Convert date object to string for database storage if needed
        entry_date = entry_data['entry_date']
        if hasattr(entry_date, 'strftime'):
            entry_date = entry_date.strftime('%Y-%m-%d')

        upsert_sql = """
        INSERT INTO processed_time_entries (
            original_entry_id,
            entry_date,
            application,
            task_description,
            time_units,
            matter_code,
            status,
            notes,
            source_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_hash, entry_date) DO UPDATE SET
            original_entry_id = excluded.original_entry_id,
            application       = excluded.application,
            task_description  = excluded.task_description,
            time_units        = excluded.time_units,
            matter_code       = excluded.matter_code,
            status            = excluded.status,
            notes             = excluded.notes,
            updated_at        = CURRENT_TIMESTAMP
        """

        cursor.execute(
            upsert_sql,
            (
                entry_data['original_entry_id'],
                entry_date,
                entry_data['application'],
                entry_data['task_description'],
                entry_data['time_units'],
                entry_data.get('matter_code'),
                entry_data.get('status', 'submitted'),
                entry_data.get('notes'),
                entry_data['source_hash'],
            ),
        )

        # Fetch the upserted row
        cursor.execute(
            "SELECT * FROM processed_time_entries WHERE source_hash = ? AND entry_date = ?",
            (entry_data['source_hash'], entry_date),
        )
        created_entry = cursor.fetchone()
        conn.commit()
        return convert_db_entry_to_dict(created_entry) if created_entry else None

    except sqlite3.Error as e:
        print(f"Database error creating processed entry: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def populate_missing_time_units():
    """Populate time_units for entries that don't have them calculated."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Find entries without time_units
        cursor.execute("SELECT entry_id, total_seconds FROM time_entries WHERE time_units IS NULL")
        entries_to_update = cursor.fetchall()
        
        if not entries_to_update:
            print("All time entries already have time_units calculated.")
            return
        
        # Import the conversion function
        import math
        def seconds_to_units(seconds):
            if seconds <= 0:
                return 0.1  # Minimum 1 unit for any activity
            units = seconds / 360  # 360 seconds = 6 minutes = 1 unit
            return math.ceil(units * 10) / 10  # Round up to nearest 0.1
        
        # Update each entry
        updated_count = 0
        for entry in entries_to_update:
            entry_id = entry['entry_id']
            total_seconds = entry['total_seconds']
            time_units = seconds_to_units(total_seconds)
            
            cursor.execute(
                "UPDATE time_entries SET time_units = ?, updated_at = CURRENT_TIMESTAMP WHERE entry_id = ?",
                (time_units, entry_id)
            )
            updated_count += 1
        
        conn.commit()
        print(f"Successfully populated time_units for {updated_count} entries.")
        
    except sqlite3.Error as e:
        print(f"Database error populating time_units: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    initialize_database() 