#!/usr/bin/env python3

import database
import schemas
from typing import List

# Get time entries from the database
entries = database.get_time_entries_by_date('2025-07-27')
if not entries:
    print("No entries found!")
    exit(1)

print(f"Found {len(entries)} entries")

# Test single entry
raw_entry = entries[0]
print("\nRaw database entry:")
print(f"  Keys: {list(raw_entry.keys())}")
print(f"  source_hash: {repr(raw_entry.get('source_hash'))}")

# Test list of Pydantic models like FastAPI does
try:
    pydantic_entries = [schemas.TimeEntry(**entry) for entry in entries]
    print(f"\nCreated {len(pydantic_entries)} Pydantic models successfully!")
    
    first_entry = pydantic_entries[0]
    print(f"  First entry source_hash: {repr(first_entry.source_hash)}")
    
    # Serialize list to dict (like FastAPI JSON response)
    serialized_list = [entry.model_dump() for entry in pydantic_entries]
    print(f"\nSerialized list with {len(serialized_list)} entries")
    print(f"  First entry keys: {list(serialized_list[0].keys())}")
    print(f"  First entry source_hash: {repr(serialized_list[0].get('source_hash'))}")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc() 