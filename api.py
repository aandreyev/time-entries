from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import database
import schemas
import alp_api
import jobs

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

@app.get("/")
def read_root():
    """A root endpoint to confirm the API is running."""
    return {"status": "ok", "message": "Welcome to the RescueTime to ALP Integration API"}

# --- Endpoints ---

@app.get("/api/time_entries", response_model=List[schemas.TimeEntry])
def get_time_entries():
    """
    Retrieve all time entries from the local database with a 'pending' status.
    """
    try:
        entries = database.get_pending_time_entries()
        return entries
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
    Triggers a background job to fetch the last N days of data from the RescueTime API.
    """
    background_tasks.add_task(jobs.run_fetch_job, days=request.days)
    return {"message": f"Accepted: Data fetching job for the last {request.days} day(s) started in the background."}

@app.post("/api/jobs/process", status_code=202)
def trigger_process_job(background_tasks: BackgroundTasks):
    """
    Triggers a background job to process all unprocessed raw data into time entries.
    """
    background_tasks.add_task(jobs.run_process_job)
    return {"message": "Accepted: Data processing job started in the background."} 