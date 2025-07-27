import csv
from database import get_db_connection

def format_seconds_to_hhmmss(seconds):
    """Formats seconds into hh:mm:ss."""
    if seconds is None:
        return "00:00:00"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def format_time_units(units):
    """Format time units for display (e.g., 1.5 units)"""
    if units is None:
        return "0.0"
    return f"{units:.1f}"

def generate_report(date_str, export_to_csv=False):
    """
    Generates and displays a report from the time_entries table.
    Optionally exports the report to a CSV file.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM time_entries WHERE entry_date = ? ORDER BY total_seconds DESC", (date_str,))
    rows = cursor.fetchall()
    

    if not rows:
        print(f"No processed time entries found for {date_str}. Run the 'process' command first.")
        conn.close()
        return

    # Display console report
    print(f"\n--- Time Entry Report for {date_str} ---")
    print(f"{'ID':<5} {'Application':<20} {'Task Description':<50} {'Units':<8} {'Time':<12} {'Status':<12} {'Notes'}")
    print("-" * 128)
    for row in rows:
        time_formatted = format_seconds_to_hhmmss(row['total_seconds'])
        units_formatted = format_time_units(row['time_units'] if 'time_units' in row.keys() else None)
        app = (row['application'] or '')[:20]
        task = (row['task_description'] or '')[:50]
        status = row['status'] or 'pending'
        notes = row['notes'] or ''
        print(f"{row['entry_id']:<5} {app:<20} {task:<50} {units_formatted:<8} {time_formatted:<12} {status:<12} {notes}")

    # Export to CSV if requested
    if export_to_csv:
        csv_filename = f"report-{date_str}.csv"
        print(f"\nExporting report to {csv_filename}...")
        try:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow([h[0] for h in cursor.description])
                # Write data rows
                writer.writerows(rows)
            print("Export successful.")
        except IOError as e:
            print(f"Error exporting to CSV: {e}")
    
    conn.close() 