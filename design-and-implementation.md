
# Design & Implementation Plan: RescueTime to ALP API

## 1. Objective

The primary objective of this project is to create a robust, standalone API that serves cleaned and aggregated time-tracking data from RescueTime.

This API will be consumed by the main Andreyev Lawyers Practice (ALP) development team. It will provide them with a set of well-defined endpoints to:
1.  Retrieve processed time entries ready for integration.
2.  Access proxied data from the main ALP API (e.g., Matters, Users, Components) in a secure and consistent manner.

This service will act as the definitive bridge between raw RescueTime data and the ALP ecosystem.

## 2. System Architecture

-   **Backend API**: A high-performance, asynchronous REST API built with **FastAPI**. This modern framework provides automatic data validation and interactive documentation, making it ideal for consumption by another development team.
-   **Core Components**:
    -   **`database.py`**: Manages the local SQLite database (`rescuetime.db`) where all raw and processed data is stored.
    -   **`processor.py`**: Contains the core business logic for cleaning and aggregating RescueTime data.
    -   **`alp_api.py`**: A dedicated module that securely proxies requests to the main ALP API.
    -   **`api.py`**: The main FastAPI application file, defining all public-facing endpoints.
    -   **`schemas.py`**: Contains all Pydantic models for request and response validation.

-   **Data Flow**:

    ```mermaid
    graph TD
        subgraph "ALP Frontend (External)"
            A[ALP Application UI]
        end

        subgraph "External ALP API"
            B[Main ALP API]
        end

        subgraph "Our RescueTime API Service"
            C[Python FastAPI Server]
            D[rescuetime.db]
        end
        
        A -->|Reads enriched data| B
        C -->|POSTs formatted time entry| B
        C -->|Queries local data| D
        B -->|Fetches Matters, Users, etc.| C
    ```

## 3. API Endpoints

The API provides a set of endpoints for retrieving processed time data and proxying requests for ALP-specific entities.

-   `GET /api/time_entries`: Returns a JSON list of all pending time entries from the local `rescuetime.db`.
-   `GET /api/alp/matters`: Securely proxies a request to the ALP API to fetch a list of all active matters.
-   `GET /api/alp/matters/{matter_id}/outcomes`: Fetches all outcomes for a specific matter.
-   `GET /api/alp/outcomes/{outcome_id}/components`: Fetches all components for a specific outcome.
-   `GET /api/alp/users`: Proxies a request to fetch users.
-   `GET /api/alp/gst_types`: Fetches the available GST type enums.
-   `POST /api/time_entries`: The primary endpoint for creating a new time entry in the main ALP system. It receives a complex time entry object, validates it, and posts it to the ALP API.
-   `PUT /api/time_entries/{entry_id}/ignore`: Updates a local time entry's status to `'ignored'` so it is no longer returned in the pending list.

The API includes interactive documentation (Swagger UI) available at the `/docs` endpoint for easy testing and developer reference.

## 4. Implementation Details

-   **Dependencies**: The project requires `fastapi`, `uvicorn`, `requests`, and `python-dotenv`.
-   **Configuration**: All sensitive information, such as the `ALP_API_URL` and `ALP_API_KEY`, must be stored in a `.env` file.
-   **Running the Server**: The API can be started by running the command `python main.py run-api`.

## 5. Future Enhancements

-   **Webhooks**: Implement webhook support to notify the main ALP system when new time entries are processed and ready for review.
-   **Enhanced Caching**: Add a caching layer (e.g., using Redis) for proxied requests to improve performance and reduce load on the main ALP API.
-   **Bi-directional Sync**: Explore a mechanism to update the status of a time entry in our local DB if it's changed or invoiced in the main ALP system.

## 6. Multi-User Integration with ALP

To extend this service for multiple users within the ALP system, a user-specific approach for handling RescueTime API keys is required. The current single-key model (via `.env`) is suitable for a single user but must be adapted for a team.

### 6.1. Core Concept

Each user within the main ALP application who wishes to sync their RescueTime data must provide their own personal RescueTime API key. This ensures that data is fetched securely and is correctly associated with the individual who generated it.

### 6.2. Proposed Workflow

1.  **Secure Key Storage**: The main ALP application should provide a secure field in the user's profile or settings page where they can save their RescueTime API key. This key should be encrypted at rest in the ALP database.

2.  **API-Driven Fetch**: When an ALP user initiates a data fetch, the ALP system will call our API's fetch endpoint. Instead of our API using a single, globally configured key, the ALP system will need to securely pass the specific user's key for the duration of the request.

### 6.3. Required Architectural Changes

To support this multi-user workflow, the following changes would be necessary in this RescueTime API service:

-   **Parameterized Fetch Logic**: The `fetcher.py` and `jobs.py` modules would need to be updated to accept a RescueTime API key as a parameter for each job run, rather than reading it from the environment.

-   **Data Scoping in Local DB**: To prevent data from different users from mixing, a `user_id` column (corresponding to the user's ID in the ALP system) must be added to the `activity_log` and `time_entries` tables in the local `rescuetime.db`. This would become part of the primary key structure to ensure uniqueness.

-   **Modified API Endpoints**:
    -   The `POST /api/jobs/fetch` endpoint would be modified to accept an `alp_user_id` and the corresponding `rescue_time_api_key`.
    -   The `GET /api/time_entries` endpoint would need to be updated to accept an `alp_user_id` parameter to ensure it only returns pending entries for that specific user. 