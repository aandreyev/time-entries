from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import database
import schemas
import alp_api
import jobs
import os

app = FastAPI(
    title="RescueTime to ALP Integration API",
    description="An API to bridge the RescueTime assistant with the ALP practice management software.",
    version="0.1.0",
)

# Configure CORS to allow the Vue.js frontend to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted to the frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static Frontend Mount (built Vue app) ---
# Expect the production build to exist at frontend/dist (run via run.sh)
try:
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
except Exception:
    # Build may not have run yet; ignore so API still works
    pass

@app.get("/", include_in_schema=False)
def serve_index():  # pragma: no cover - simple file response
    """Serve the SPA index HTML (frontend)."""
    try:
        return FileResponse("frontend/dist/index.html")
    except Exception:
        # Fallback simple JSON if frontend not built yet
        return {"status": "ok", "message": "Frontend not built yet. Run ./run.sh to build."}

## (Fallback moved to end of file to avoid overshadowing API routes.)

# --- Endpoints ---

@app.get("/api/settings", response_model=dict)
def get_settings():
    """Return minimal runtime settings for the UI."""
    return {
        "backend_port": int(os.getenv("BACKEND_PORT", 8000)),
        "database_path": os.getenv("DATABASE_PATH", "rescuetime.db"),
        "has_api_key": bool(os.getenv("RESCUETIME_API_KEY")),
    }

@app.get("/api/time_entries", response_model=List[schemas.TimeEntry])
def get_time_entries(date: Optional[str] = None):
    """
    Retrieve time entries from the local database with a 'pending' status, optionally filtered by date.
    """
    try:
        if date:
            entries = database.get_time_entries_by_date(date)
        else:
            entries = database.get_pending_time_entries()
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/time_entries_raw")
def get_time_entries_raw(date: Optional[str] = None):
    """
    Test endpoint to return raw database entries without Pydantic validation.
    """
    try:
        import os
        cwd = os.getcwd()
        db_file = os.path.join(cwd, "rescuetime.db")
        db_exists = os.path.exists(db_file)
        
        if date:
            entries = database.get_time_entries_by_date(date)
        else:
            entries = database.get_pending_time_entries()
            
        return {
            "debug": {
                "cwd": cwd,
                "db_file": db_file,
                "db_exists": db_exists,
                "query_date": date,
                "entries_count": len(entries) if entries else 0
            },
            "raw_entries": entries
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/api/processed_time_entries", response_model=List[schemas.ProcessedTimeEntry])
def get_processed_time_entries(date: Optional[str] = None):
    """
    Retrieve processed time entries, optionally filtered by date.
    """
    try:
        entries = database.get_processed_time_entries(date)
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/processed_time_entries", response_model=schemas.ProcessedTimeEntry)
def create_processed_time_entry(entry: schemas.ProcessedTimeEntryCreate):
    """
    Create a new processed time entry and mark the original as submitted.
    """
    try:
        created_entry = database.create_processed_time_entry(entry.dict())
        # Also update the original time entry status to 'submitted'
        if entry.original_entry_id:
            database.update_time_entry_status(entry.original_entry_id, "submitted")
        return created_entry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/time_entries/{entry_id}/ignore", response_model=dict)
def ignore_time_entry(entry_id: int):
    """
    Update a time entry's status to 'ignored' in the local database.
    """
    try:
        database.update_time_entry_status(entry_id, "ignored")
        return {"status": "success", "message": f"Time entry {entry_id} has been ignored."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/processed_time_entries/{entry_id}/revert", response_model=dict)
def revert_processed_time_entry(entry_id: int):
    """
    Revert a processed time entry back to pending status.
    This removes the processed entry and sets the original entry status back to 'pending'.
    """
    try:
        # Get the processed entry to find the original entry ID
        processed_entry = database.get_processed_entry_by_id(entry_id)
        if not processed_entry:
            raise HTTPException(status_code=404, detail="Processed time entry not found")
        
        original_entry_id = processed_entry.get('original_entry_id')
        if not original_entry_id:
            raise HTTPException(status_code=400, detail="Original entry ID not found in processed entry")
        
        # Delete the processed entry
        database.delete_processed_time_entry(entry_id)
        
        # Revert the original entry status back to pending
        database.update_time_entry_status(original_entry_id, "pending")
        
        return {"status": "success", "message": f"Processed entry {entry_id} has been reverted to pending."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alp/matters")
def get_alp_matters():
    # TODO: Proxy request to ALP API to fetch matters
    return alp_api.get_matters()

@app.get("/api/alp/matters/{matter_id}/outcomes")
def get_alp_matter_outcomes(matter_id: int):
    # TODO: Proxy request to ALP API
    return alp_api.get_matter_outcomes(matter_id)

@app.get("/api/alp/outcomes/{outcome_id}/components")
def get_alp_outcome_components(outcome_id: int):
    # TODO: Proxy request to ALP API
    return alp_api.get_outcome_components(outcome_id)

@app.post("/api/time_entries", response_model=dict)
def create_alp_time_entry(entry: schemas.AlpTimeEntryCreate):
    """
    Receives a validated time entry object and posts it to the main ALP API.
    """
    try:
        response = alp_api.post_time_entry(entry.dict())
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/fetch", status_code=202)
def trigger_fetch_job(request: schemas.FetchJobRequest, background_tasks: BackgroundTasks):
    """
    Triggers a background job to fetch data from the RescueTime API.
    If target_date is provided, fetches data for that date plus the specified number of days before it.
    If no target_date is provided, fetches data for the last N days from today.
    """
    background_tasks.add_task(jobs.run_fetch_job, days=request.days, target_date=request.target_date)
    
    if request.target_date:
        return {"message": f"Accepted: Data fetching job for {request.days} day(s) from {request.target_date} started in the background."}
    else:
        return {"message": f"Accepted: Data fetching job for the last {request.days} day(s) started in the background."}

@app.post("/api/jobs/process", status_code=202)
def trigger_process_job(background_tasks: BackgroundTasks):
    """
    Triggers a background job to process all unprocessed raw data into time entries.
    """
    background_tasks.add_task(jobs.run_process_job)
    return {"message": "Accepted: Data processing job started in the background."} 

# --- SPA Fallback (must be last) ---
@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):  # pragma: no cover
    """Serve index.html for any non-API path so the Vue router can handle it."""
    # Let real 404s happen for API paths
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    try:
        return FileResponse("frontend/dist/index.html")
    except Exception:
        raise HTTPException(status_code=404, detail="Frontend not built")