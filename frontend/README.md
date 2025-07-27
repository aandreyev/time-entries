# RescueTime Frontend

Vue.js 3 frontend for the RescueTime Time Entry Assistant.

## Tech Stack

- **Vue.js 3** with Composition API
- **Tailwind CSS** for styling
- **Pinia** for state management
- **Vite** for build tooling

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 3. Ensure Backend is Running

Make sure the Python backend is running on `http://localhost:8000`:

```bash
cd ..
python main.py run-api
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally

## Project Structure

```
src/
├── components/        # Reusable Vue components
├── stores/           # Pinia state management
├── views/            # Page components
├── utils/            # Utility functions
└── assets/           # CSS and static assets
```

## API Integration

The frontend connects to the Python backend via proxy configuration in `vite.config.js`. All `/api/*` requests are proxied to `http://localhost:8000`.

## Features

- **Date Navigation**: Navigate between days using arrows, date picker, or "Today" button
- **Real-time Stats**: View pending, submitted, and ignored time entries
- **Batch Operations**: Confirm or ignore time entries
- **Data Management**: Fetch new data from RescueTime and process existing data
- **Responsive Design**: Works on desktop and mobile devices

## Development

### Adding New Components

Create components in `src/components/` and import them where needed.

### State Management

Use the Pinia stores in `src/stores/` for managing application state:
- `timeEntries.js` - Main time entry data and operations
- Add additional stores as needed

### Styling

This project uses Tailwind CSS with custom utility classes defined in `src/assets/main.css`.

## Production Build

```bash
npm run build
```

The built files will be in the `dist/` directory, ready for deployment to any static hosting service. 