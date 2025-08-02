# UI Specification - RescueTime Time Entry Assistant

## Overview
The application retrieves activities from the RescueTime application, processes them into clean time entries, and provides a user interface for editing and confirming entries before submission to the ALP practice management system.

## Data Flow
1. **Raw Data**: Activities retrieved from RescueTime API → stored in `activity_log` table
2. **Processed Data**: Cleaned and aggregated activities → stored in `time_entries` table  
3. **User Actions**: Edit, confirm, or ignore entries via the UI

## Core UI Requirements

### 1. Time Entry List View
**Display Format:**
- List view showing all time entries for a selected date
- Each row represents one unique task/document per day
- Default sort: by time spent (descending)

**Required Columns:**
- **Application**: The source application (e.g., "Microsoft Word", "Portal")
- **Task Description**: The document/activity name (editable)
- **Time**: Duration in 6-minute units (editable, rounded UP to nearest 0.1)  
- **Matter Code**: 5-digit client code if detected (editable, manual entry)
- **Status**: pending/submitted/ignored (editable dropdown)
- **Notes**: User comments (editable)
- **Actions**: Confirm/Ignore buttons

### 2. In-Line Editing
**Editable Fields:**
- Task Description (text input)
- Time Duration (decimal input in 6-minute units, auto-rounds UP to nearest 0.1)
- Matter Code (text input with 5-digit validation, manual entry)
- Notes (text area)
- Status (dropdown: pending/submitted/ignored)

**Validation:**
- Time format: decimal units (e.g., 0.5 = 30 minutes), minimum 0.1, rounds UP
- Matter code format validation (5 digits only, optional)
- Required field indicators

### 3. Date Navigation
**Navigation Controls:**
- Date picker for specific date selection
- Previous/Next day arrows
- "Today" quick button
- Optional: Week/Month view toggle

**Date Range Display:**
- Show total time for the selected day
- Display count of pending vs processed entries
- Optional: Mini calendar with activity indicators

### 4. Entry Actions

#### Confirm Entry
- **Trigger**: "Confirm" button click
- **Action**: 
  - Validate all edited fields
  - Create new record in `processed_time_entries` table with edited values
  - Link to original `time_entries` record via foreign key
  - Set status to 'submitted'
  - Show success feedback

#### Ignore Entry  
- **Trigger**: "Ignore" button click
- **Action**:
  - Set status to 'ignored'  
  - Optionally prompt for ignore reason
  - Grey out the row visually

#### Bulk Actions
- Select multiple entries (checkboxes)
- Bulk confirm/ignore selected entries
- Bulk edit common fields (matter code, notes)

### 5. Data Display Options

#### Filter Controls
- **Status Filter**: All/Pending/Submitted/Ignored
- **Application Filter**: Dropdown of available applications
- **Matter Code Filter**: Show only entries with/without matter codes
- **Time Range Filter**: Min/max duration

#### View Options
- **Compact View**: Fewer columns, more entries per screen
- **Detailed View**: All fields visible, larger text
- **Raw Data Toggle**: Show original RescueTime data alongside processed data

### 6. Integration Features

#### ALP System Integration
- **Submit to ALP** button for confirmed entries
- Progress indicator for submission status
- Error handling and retry mechanism
- Success/failure feedback

#### Data Management
- **Refresh Data** button to fetch latest from RescueTime
- **Process Data** button to re-run cleaning algorithms
- Export functionality (CSV download)

## Technical Requirements

### Frontend Technology Stack
**Framework**: Vue.js 3 with Composition API
**Styling**: Tailwind CSS for utility-first styling
**State Management**: Pinia for reactive state management
**Build Tool**: Vite for fast development and building
**Components**: 
- Reusable time entry row components
- Date navigation components  
- Filter and search components
- Modal dialogs for confirmations

**Rationale**: Consistent with existing main application stack, enabling code reuse, shared patterns, and easier future integration.

### Project Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── TimeEntryRow.vue      # Editable time entry row
│   │   ├── DateNavigator.vue     # Date picker and navigation
│   │   ├── FilterControls.vue    # Status and application filters
│   │   ├── TimeEntryList.vue     # Main list container
│   │   ├── LoadingSpinner.vue    # Loading states
│   │   └── ConfirmDialog.vue     # Confirmation modals
│   ├── stores/
│   │   ├── timeEntries.js        # Time entry data and operations
│   │   ├── filters.js            # UI filters and search state
│   │   └── app.js                # Global app state
│   ├── views/
│   │   └── TimeEntries.vue       # Main time entry page
│   ├── utils/
│   │   ├── api.js                # API client functions
│   │   ├── dateUtils.js          # Date formatting utilities
│   │   └── validation.js         # Form validation helpers
│   ├── assets/
│   │   └── main.css              # Tailwind CSS imports
│   └── main.js                   # Vue app initialization
├── public/
│   └── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

### Database Schema
**Existing Tables:**
- `activity_log`: Raw RescueTime data
- `time_entries`: Processed time entries (auto-generated drafts)

**New Table Required:**
- `processed_time_entries`: User-edited, confirmed entries ready for ALP submission
  - Links to original `time_entries` via `original_entry_id` foreign key
  - Contains edited task description, time units, matter code, notes
  - Prevents duplicates during data re-processing

**Status Field Values:**
- `pending`: Newly processed, awaiting user review
- `submitted`: User confirmed, ready for ALP submission  
- `ignored`: User chose to ignore this entry

**Time Unit Conversion:**
- All time stored and displayed in 6-minute units (0.1 hour increments)
- Conversion: seconds → units = CEILING(seconds / 360)
- Example: 450 seconds → 2 units (12 minutes, rounded up)

### API Endpoints Required
- `GET /api/time_entries?date=YYYY-MM-DD` - Get draft entries for date
- `GET /api/processed_time_entries?date=YYYY-MM-DD` - Get confirmed entries for date
- `POST /api/processed_time_entries` - Create new confirmed entry from draft
- `PUT /api/time_entries/{id}/ignore` - Mark draft entry as ignored
- `POST /api/jobs/fetch` - Trigger data fetch from RescueTime
- `POST /api/jobs/process` - Trigger data processing (single day only)

### User Experience

#### Loading States
- Show loading spinners during data fetch/process operations
- Disable form fields during submission
- Progress bars for bulk operations

#### Error Handling
- Clear error messages for validation failures
- Retry mechanisms for API failures
- Graceful degradation when services are unavailable

#### Responsive Design
- Mobile-friendly layout for quick edits using Tailwind responsive utilities
- Keyboard shortcuts for power users (Vue event handlers)
- Accessibility compliance (WCAG 2.1) with proper ARIA labels
- Optimized for desktop-first workflow with mobile fallback

## Design Decisions

1. **Data Persistence**: ✅ **CONFIRMED** - Edited entries create new records in a separate `processed_time_entries` table, linked to original entries. This prevents duplicates during re-processing.

2. **Matter Code Lookup**: ✅ **DEFERRED** - Manual entry initially, ALP integration for autocomplete/validation in future version.

3. **Time Format**: ✅ **CONFIRMED** - Time displayed and entered in 6-minute units (0.1 hour increments). All time rounded UP to nearest unit.

4. **Approval Workflow**: ✅ **CONFIRMED** - No approval required. Direct submission to ALP after user confirmation.

5. **Audit Trail**: ✅ **DEFERRED** - Track ALP submissions in future version, not required for MVP.

6. **Batch Processing**: ✅ **CONFIRMED** - Single day processing only. No multi-day batch operations.

7. **Mobile App**: ✅ **DEFERRED** - Web-only for MVP. Mobile app and enhanced API in future version.

## Future Enhancements

### Version 2.0 Features
- **Matter Code Integration**: ALP database lookup for autocomplete/validation
- **Mobile Application**: Native mobile app with enhanced API
- **Audit Trail**: Track ALP submissions, user changes, timestamps
- **Batch Processing**: Multi-day processing and submission

### Future Versions
- Real-time sync with RescueTime
- AI-powered matter code suggestion
- Time entry templates for common tasks
- Integration with other time tracking tools
- Advanced reporting and analytics
- Team collaboration features

## Implementation Notes

### Time Unit Examples
- 1 minute = 0.1 units (rounded up from 0.02)
- 5 minutes = 0.9 units (rounded up from 0.83)
- 6 minutes = 1.0 units (exact)
- 10 minutes = 1.7 units (rounded up from 1.66)
- 30 minutes = 5.0 units (exact)
- 1 hour = 10.0 units (exact)

### Data Separation Benefits
- **Re-processing Safe**: Can re-run RescueTime imports without affecting confirmed entries
- **Data Integrity**: Original raw data preserved for auditing
- **Duplicate Prevention**: Confirmed entries remain stable regardless of source data changes
- **Clear Workflow**: Distinct stages from raw → draft → confirmed → submitted
