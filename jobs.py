from datetime import date, timedelta
import fetcher
import database
import processor

def run_fetch_job(days: int = 1):
    """
    Runs the data fetching job for the last N days.
    This function is designed to be called from the CLI or as a background task from the API.
    """
    print(f"Starting fetch job for the last {days} day(s)...")
    today = date.today()
    # Fetch for the number of days specified, including today if days > 0
    dates_to_fetch = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    
    for date_str in dates_to_fetch:
        print(f"--> Processing {date_str}")
        # Mark existing raw data for this date for reprocessing to ensure full aggregation
        database.mark_date_for_reprocessing(date_str)
        
        # Fetch new data from the RescueTime API
        data = fetcher.fetch_data_for_date(date_str)
        
        if data:
            database.upsert_activity_data(data)
            print(f"    Successfully fetched and upserted {len(data)} records for {date_str}.")
        else:
            print(f"    No new data found for {date_str}.")
            
    print("Fetch job completed successfully.")

def run_process_job():
    """
    Runs the data processing job for all unprocessed entries.
    This can be called from the CLI or as a background task.
    """
    print("Starting data processing job...")
    processor.process_all_data(debug=False) # Assuming debug=False for automated runs
    print("Processing job completed successfully.") 