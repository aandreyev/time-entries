import requests
import os
from dotenv import load_dotenv

def get_api_key():
    """
    Reads the API key from environment variables loaded from .env
    """
    load_dotenv()
    api_key = os.getenv('RESCUETIME_API_KEY')
    if not api_key:
        raise ValueError("Error: RESCUETIME_API_KEY not found in .env file.")
    return api_key

def fetch_data_for_date(date_str):
    """
    Fetches the raw document-level data from the RescueTime API for a specific date.
    """
    print(f"Fetching data from RescueTime API for {date_str}...")
    try:
        api_key = get_api_key()
    except (FileNotFoundError, ValueError) as e:
        print(e)
        return None

    base_url = "https://www.rescuetime.com/anapi/data"
    params = {
        'key': api_key,
        'format': 'json',
        'restrict_begin': date_str,
        'restrict_end': date_str,
        'perspective': 'rank',
        'restrict_kind': 'document', # Fetch the most granular data
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        print("Successfully fetched data.")
        return response.json()
    else:
        print(f"Error fetching data: {response.status_code}")
        print(response.text)
        return None 