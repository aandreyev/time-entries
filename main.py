import argparse
from datetime import datetime, timedelta
import database
import fetcher
import processor
import reporter
import uvicorn
from api import app as fastapi_app
import jobs

def handle_fetch(args):
    """Handles the fetch command."""
    print("Received fetch command via CLI.")
    jobs.run_fetch_job(days=args.days)

def handle_process(args):
    """Handles the process command."""
    if args.all:
        print("Received process --all command via CLI.")
        jobs.run_process_job()
    elif args.date:
        print(f"Received process --date {args.date} command via CLI.")
        processor.process_data_for_date(args.date, debug=args.debug)
    else:
        print("Processing unprocessed data.")
        jobs.run_process_job()

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

def handle_clear(args):
    """Handles the 'clear' command."""
    print("Clearing all processed time entries...")
    database.clear_time_entries()

def handle_init_db(args):
    """Handles the 'initdb' command."""
    print("Initializing the database...")
    database.initialize_database()

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
    parser_process.add_argument("--all", action="store_true", help="Process all unprocessed data.")
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

    # --- New Subparser for running the API ---
    run_api_parser = subparsers.add_parser("run-api", help="Run the FastAPI server for the web interface.")
    run_api_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host for the API server.")
    run_api_parser.add_argument("--port", type=int, default=8000, help="Port for the API server.")
    run_api_parser.set_defaults(func=lambda args: uvicorn.run(fastapi_app, host=args.host, port=args.port))

    # --- Clear Command ---
    parser_clear = subparsers.add_parser("clear", help="Clear all processed time entries.")
    parser_clear.set_defaults(func=handle_clear)

    # --- Init DB Command ---
    parser_init_db = subparsers.add_parser("initdb", help="Initialize the database.")
    parser_init_db.set_defaults(func=handle_init_db)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main() 