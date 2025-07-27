from pydantic import BaseModel, Field
from typing import Optional, Union
from datetime import date

class TimeEntryBase(BaseModel):
    """
    Base time entry model with common fields.
    """
    entry_date: date
    application: str
    task_description: str
    total_seconds: int
    matter_code: Optional[str] = None
    notes: Optional[str] = None

class TimeEntry(TimeEntryBase):
    """
    Full time entry model including the database ID.
    """
    entry_id: int
    status: str
    time_units: Optional[float] = None
    source_hash: str

    class Config:
        from_attributes = True

class FetchJobRequest(BaseModel):
    """
    Model for the request to trigger a fetch job.
    """
    days: int = Field(default=1, ge=1, le=30, description="Number of past days to fetch data for (e.g., 1 for today).")

class AlpTimeEntryCreate(BaseModel):
    """
    Model for creating a new time entry in the ALP system.
    This reflects the fields required by the ALP API.
    """
    matter_component_id: int
    user_id: int
    date: date
    units: int
    description: str
    rate: int
    billable_type: int
    gst_type: int
    discriminator: str = "MatterComponentTimeEntry"
    notes: Optional[str] = None 

class ProcessedTimeEntryCreate(BaseModel):
    """
    Model for creating a new processed time entry.
    """
    original_entry_id: int
    entry_date: date
    application: str
    task_description: str
    time_units: float
    matter_code: Optional[str] = None
    status: str = "submitted"
    notes: Optional[str] = None
    source_hash: str

class ProcessedTimeEntry(ProcessedTimeEntryCreate):
    """
    Full processed time entry model including the database ID.
    """
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    submitted_to_alp_at: Optional[str] = None
    alp_entry_id: Optional[str] = None

    class Config:
        from_attributes = True 