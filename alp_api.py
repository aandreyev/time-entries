import os
import requests
from dotenv import load_dotenv

load_dotenv()

ALP_API_URL = os.getenv("ALP_API_URL")
ALP_API_KEY = os.getenv("ALP_API_KEY")

def get_auth_headers():
    """Returns the authorization headers for ALP API requests."""
    if not ALP_API_KEY:
        raise ValueError("ALP_API_KEY is not set in the .env file.")
    return {"Authorization": f"Bearer {ALP_API_KEY}"}

def get_matters():
    """
    Fetches all matters from the ALP API.
    (Placeholder implementation)
    """
    # In a real scenario, you would make a request like:
    # response = requests.get(f"{ALP_API_URL}/matters", headers=get_auth_headers())
    # response.raise_for_status()
    # return response.json()
    print("Fetching matters from ALP API...")
    # Returning mock data for now
    return [
        {"id": 1, "name": "Matter 001 - Corporate Restructuring"},
        {"id": 2, "name": "Matter 002 - IP Litigation"},
    ]

def get_matter_outcomes(matter_id: int):
    """
    Fetches all outcomes for a specific matter from the ALP API.
    (Placeholder implementation)
    """
    print(f"Fetching outcomes for matter_id {matter_id}...")
    return [
        {"id": 101, "name": "Phase 1: Discovery"},
        {"id": 102, "name": "Phase 2: Negotiation"},
    ]

def get_outcome_components(outcome_id: int):
    """
    Fetches all components for a specific outcome from the ALP API.
    (Placeholder implementation)
    """
    print(f"Fetching components for outcome_id {outcome_id}...")
    return [
        {"id": 1001, "name": "Initial client meeting"},
        {"id": 1002, "name": "Drafting discovery documents"},
    ]

def post_time_entry(entry_data: dict):
    """
    Posts a new time entry to the ALP API.
    (Placeholder implementation)
    """
    print(f"Posting time entry to ALP API: {entry_data}")
    # response = requests.post(f"{ALP_API_URL}/time_entries", json=entry_data, headers=get_auth_headers())
    # response.raise_for_status()
    # return response.json()
    return {"status": "success", "message": "Time entry posted successfully (mock)"} 