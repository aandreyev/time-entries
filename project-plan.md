# Project Plan: RescueTime Time-Entry Assistant

This document outlines the development plan for the RescueTime Time-Entry Assistant, a tool to fetch, process, and summarize RescueTime data for easier time-entry creation.

## Phase 1: Core Functionality (Completed)

The initial phase focused on building a robust data pipeline to transform raw RescueTime data into a clean, actionable summary.

### Key Features Implemented:

*   **Modular Architecture:** The application is split into logical modules (`main.py`, `database.py`, `fetcher.py`, `reporter.py`).
*   **Local Data Storage:** A local **SQLite** database (`rescuetime.db`) is used to store raw activity data in an `activity_log` table.
*   **Command-Line Interface:** The application is controlled via a simple CLI with `initdb`, `fetch`, and `report` commands.
*   **Data Aggregation and Cleaning:** The reporting module aggregates time spent on unique documents and applies cleaning rules to produce a clean, one-line-per-task summary suitable for time entries.

---

## Phase 2: Time-Entry Management & Reporting (In Progress)

This phase will upgrade the tool from a simple reporter to a stateful time-entry management system, ensuring data integrity and providing more powerful features.

### 1. Database Enhancements

*   **Create `time_entries` Table:** A new table will be added to the database to store the processed, aggregated time entries.
    *   **Schema:** `entry_id` (PK), `entry_date`, `application`, `task_description`, `total_seconds`, `status`, `notes`, `source_hash`.
*   **"Source Hash" for Data Integrity:** The `source_hash` column will act as a unique fingerprint for each time entry, created from the date, application, and task description. This prevents duplicate entries when re-processing data and preserves manual changes (like status or notes).

### 2. New Application Workflow & Commands

*   **`fetch` (Restored to Original Design):** Fetches raw data from the API and stores it in the `activity_log` table, clearing old data for the fetched dates to ensure complete aggregation when processing.
*   **`process` (New Command):**
    *   Reads raw data from `activity_log` for a given date.
    *   Cleans and aggregates the data.
    *   Calculates the `source_hash` for each aggregated task.
    *   "Upserts" the data into the `time_entries` table:
        *   If `source_hash` exists, it updates `total_seconds`.
        *   If `source_hash` is new, it inserts a new record with a default `pending` status.
*   **`update` (New Command):**
    *   Allows for manual updates to a time entry's status or notes.
    *   Example: `python main.py update --id 123 --status "submitted"`
*   **`report` (Updated Command):**
    *   Reads directly from the clean `time_entries` table.
    *   **CSV Export:** Includes a new `--export csv` flag to save the report to a CSV file, perfect for analysis in Excel or other tools.

### 3. Improved Data Cleaning Logic

*   **External Configuration for Rules:** (Future) Move the data cleaning rules to an external configuration file (e.g., `config.json`) for easier customization.

This plan provides a clear roadmap for the project. We will now execute on this plan, starting with the database enhancements. 