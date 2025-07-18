import argparse
from datetime import datetime, timedelta
import database
import fetcher
import processor
import reporter

def handle_fetch(args):
    """Handles the 'fetch' command."""
    if args.current:
        # Current day mode - fetch only today's data
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Check if we should update (unless forced)
        should_update, reason = database.should_update_current_day(min_interval_minutes=15)
        
        if not should_update and not getattr(args, 'force', False):
            print(f"⏸️ Skipping current day update: {reason}")
            print("💡 Use --force to update anyway, or wait for the interval to pass.")
            return
        
        print(f"Fetching current day data for {today}...")
        print(f"📄 Reason: {reason}")
        
        # Clear existing data for today to ensure complete refresh
        database.mark_date_for_reprocessing(today)
        
        # Fetch raw data from the API
        raw_data = fetcher.fetch_data_for_date(today)
        
        if raw_data and 'rows' in raw_data:
            # Prepare data for insertion (clean slate approach)
            headers = raw_data['row_headers']
            data_to_insert = []
            try:
                # Get column indices
                time_idx = headers.index('Time Spent (seconds)')
                act_idx = headers.index('Activity')
                cat_idx = headers.index('Category')
                prod_idx = headers.index('Productivity')
                doc_idx = headers.index('Document')
                
                for row in raw_data['rows']:
                    data_to_insert.append((
                        today,
                        row[time_idx],
                        row[act_idx],
                        row[cat_idx],
                        row[prod_idx],
                        row[doc_idx]
                    ))
                
                # Insert the fresh data (all records will be unprocessed)
                if data_to_insert:
                    database.upsert_activity_data(data_to_insert)
                    print(f"✅ Updated current day with {len(data_to_insert)} activity records.")
                    
                    # Record this update
                    database.set_last_current_day_update(today)
                    
                    # Auto-process the current day data
                    print("🔄 Auto-processing current day data...")
                    processor.process_data_for_date(today, debug=False)
                else:
                    print("⚠️ No current day data to update.")
            except ValueError as e:
                print(f"Error processing data for {today}: Missing expected column - {e}")
        else:
            print(f"No current day data returned from API.")
    else:
        # Original multi-day mode
        print(f"Fetching data for the last {args.days} day(s).")
        for i in range(args.days):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # Clear existing data for this date to ensure complete refresh
            database.mark_date_for_reprocessing(date_str)
            
            # Fetch raw data from the API
            raw_data = fetcher.fetch_data_for_date(date_str)
            
            if raw_data and 'rows' in raw_data:
                # Prepare data for insertion (clean slate approach)
                headers = raw_data['row_headers']
                data_to_insert = []
                try:
                    # Get column indices
                    time_idx = headers.index('Time Spent (seconds)')
                    act_idx = headers.index('Activity')
                    cat_idx = headers.index('Category')
                    prod_idx = headers.index('Productivity')
                    doc_idx = headers.index('Document')
                    
                    for row in raw_data['rows']:
                        data_to_insert.append((
                            date_str,
                            row[time_idx],
                            row[act_idx],
                            row[cat_idx],
                            row[prod_idx],
                            row[doc_idx]
                        ))
                    
                    # Insert the fresh data (all records will be unprocessed)
                    if data_to_insert:
                        database.upsert_activity_data(data_to_insert)
                except ValueError as e:
                    print(f"Error processing data for {date_str}: Missing expected column - {e}")
            else:
                print(f"No data returned for {date_str}.")

def handle_process(args):
    """Handles the 'process' command."""
    print(f"Processing data for {args.date}...")
    processor.process_data_for_date(args.date, args.debug)

def handle_process_all(args):
    """Handles the 'process-all' command."""
    if args.start_date or args.end_date:
        date_msg = f" for date range {args.start_date or 'beginning'} to {args.end_date or 'end'}"
    else:
        date_msg = " for all dates"
    print(f"Processing raw data{date_msg}...")
    processor.process_all_data(args.debug, args.start_date, args.end_date)

def handle_report(args):
    """Handles the 'report' command."""
    print(f"Generating report for date: {args.date}")
    reporter.generate_report(args.date, args.export)

def handle_auto_update(args):
    """Handles the 'auto-update' command for periodic current day updates."""
    from datetime import datetime
    
    print(f"🔄 AUTO-UPDATE: Current Day Data")
    print(f"{'='*40}")
    
    # Get update status
    last_update = database.get_last_current_day_update()
    should_update, reason = database.should_update_current_day(min_interval_minutes=args.interval)
    
    current_time = datetime.now().strftime('%H:%M:%S')
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Current time: {current_time}")
    print(f"Target date: {today}")
    
    if last_update:
        print(f"Last update: {last_update['date']} at {last_update['timestamp'][:19]}")
    else:
        print("Last update: Never")
    
    print(f"Update needed: {reason}")
    
    if should_update or args.force:
        print(f"\n⚡ Proceeding with update...")
        
        # Create a mock args object for handle_fetch
        class MockArgs:
            def __init__(self):
                self.current = True
                self.force = args.force
        
        mock_args = MockArgs()
        handle_fetch(mock_args)
        
        # Show summary
        print(f"\n📊 CURRENT DAY SUMMARY")
        print(f"{'='*40}")
        reporter.generate_report(today, export_to_csv=False)
        
    else:
        print(f"\n⏸️ No update needed at this time.")
        print(f"💡 Next update available in {args.interval - (datetime.now() - datetime.fromisoformat(last_update['timestamp'])).total_seconds()/60:.0f} minutes")
        
        # Still show current summary
        print(f"\n📊 CURRENT DAY SUMMARY (Last Updated)")
        print(f"{'='*40}")
        try:
            reporter.generate_report(today, export_to_csv=False)
        except:
            print("No time entries found for today. Run with --force to fetch initial data.")

def handle_update(args):
    """Handles the 'update' command."""
    print(f"Updating time entry {args.id}...")
    database.update_time_entry(args.id, status=args.status, notes=args.notes)

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="RescueTime Data Fetcher and Reporter.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Common date argument
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    # --- Fetch Command ---
    parser_fetch = subparsers.add_parser("fetch", help="Fetch data from the RescueTime API.")
    parser_fetch.add_argument("--days", type=int, default=1, help="Number of past days to fetch data for (default: 1).")
    parser_fetch.add_argument("--current", action="store_true", help="Fetch only the current day's data.")
    parser_fetch.add_argument("--force", action="store_true", help="Force update even if interval is not met.")
    parser_fetch.set_defaults(func=handle_fetch)

    # --- Process Command ---
    parser_process = subparsers.add_parser("process", help="Process raw data into time entries.")
    parser_process.add_argument("--date", type=str, default=yesterday, help=f"Date to process in YYYY-MM-DD format (default: {yesterday}).")
    parser_process.add_argument("--debug", action="store_true", help="Run in debug mode to see cleaning analysis.")
    parser_process.set_defaults(func=handle_process)
    
    # --- Process All Command ---
    parser_process_all = subparsers.add_parser("process-all", help="Process all raw data with cross-date aggregation.")
    parser_process_all.add_argument("--debug", action="store_true", help="Run in debug mode to see cleaning analysis.")
    parser_process_all.add_argument("--start-date", type=str, help="Start date for process-all in YYYY-MM-DD format.")
    parser_process_all.add_argument("--end-date", type=str, help="End date for process-all in YYYY-MM-DD format.")
    parser_process_all.set_defaults(func=handle_process_all)

    # --- Report Command ---
    parser_report = subparsers.add_parser("report", help="Generate a report from local data.")
    parser_report.add_argument("--date", type=str, default=yesterday, help=f"Date for the report in YYYY-MM-DD format (default: {yesterday}).")
    parser_report.add_argument("--export", action="store_true", help="Export the report to a CSV file.")
    parser_report.set_defaults(func=handle_report)

    # --- Update Command ---
    parser_update = subparsers.add_parser("update", help="Update a time entry.")
    parser_update.add_argument("--id", type=int, required=True, help="The ID of the time entry to update.")
    parser_update.add_argument("--status", type=str, help="The new status (e.g., 'submitted').")
    parser_update.add_argument("--notes", type=str, help="Add or update notes for the entry.")
    parser_update.set_defaults(func=handle_update)

    # --- Auto-Update Command ---
    parser_auto_update = subparsers.add_parser("auto-update", help="Periodically update current day data with smart timing.")
    parser_auto_update.add_argument("--interval", type=int, default=15, help="Minimum interval in minutes between updates (default: 15).")
    parser_auto_update.add_argument("--force", action="store_true", help="Force update even if interval is not met.")
    parser_auto_update.set_defaults(func=handle_auto_update)
    
    # --- Clear Command ---
    parser_clear = subparsers.add_parser("clear", help="Clear all processed time entries.")
    parser_clear.set_defaults(func=lambda args: database.clear_time_entries())

    # --- Init DB Command ---
    parser_init_db = subparsers.add_parser("initdb", help="Initialize the database.")
    parser_init_db.set_defaults(func=lambda args: database.initialize_database())

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main() 