# PostgreSQL version of database.py
# Use this as a reference for converting to PostgreSQL

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'rescuetime'),
        user=os.getenv('DB_USER', 'rescuetime_user'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', '5432'),
        cursor_factory=RealDictCursor
    )
    return conn

def initialize_database():
    """Initializes the PostgreSQL database and creates tables with enhanced schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Enhanced activity_log table with processing tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        log_date DATE NOT NULL,
        time_spent_seconds INTEGER NOT NULL,
        activity TEXT NOT NULL,
        category TEXT,
        productivity INTEGER,
        document TEXT,
        processed INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (log_date, activity, document)
    )
    """)

    # Enhanced time_entries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS time_entries (
        entry_id SERIAL PRIMARY KEY,
        entry_date DATE NOT NULL,
        application TEXT NOT NULL,
        task_description TEXT NOT NULL,
        total_seconds INTEGER NOT NULL,
        time_units REAL,
        status TEXT NOT NULL DEFAULT 'pending',
        notes TEXT,
        matter_code TEXT,
        source_hash TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Processed time entries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_time_entries (
        id SERIAL PRIMARY KEY,
        original_entry_id INTEGER NOT NULL,
        entry_date DATE NOT NULL,
        application TEXT NOT NULL,
        task_description TEXT NOT NULL,
        time_units REAL NOT NULL,
        matter_code TEXT,
        status TEXT NOT NULL DEFAULT 'submitted',
        notes TEXT,
        source_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        submitted_to_alp_at TIMESTAMP,
        alp_entry_id TEXT,
        UNIQUE(source_hash, entry_date),
        FOREIGN KEY (original_entry_id) REFERENCES time_entries (entry_id)
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_time_entries_date ON processed_time_entries(entry_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_time_entries_matter ON processed_time_entries(matter_code)")
    
    conn.commit()
    conn.close()
    print("PostgreSQL database initialized successfully.")

# Example .env configuration for PostgreSQL
"""
# Add these to your .env file:
DB_HOST=your-postgres-host.com
DB_NAME=rescuetime
DB_USER=rescuetime_user
DB_PASSWORD=your-secure-password
DB_PORT=5432
RESCUETIME_API_KEY=your-rescuetime-api-key
"""
