# Centralized API Server Setup

## Architecture:
```
Computer 1 (Server) ──── SQLite Database
    │
    └── FastAPI Server (Port 8000)
         │
         ├── Computer 2 (Client) ── Frontend only
         ├── Computer 3 (Client) ── Frontend only  
         └── Computer N (Client) ── Frontend only
```

## Setup Steps:

### 1. Server Computer Setup:
```bash
# Run the API server accessible from network
uvicorn api:app --host 0.0.0.0 --port 8000
```

### 2. Client Computer Setup:
Update frontend API configuration to point to server:

```javascript
// frontend/src/utils/api.js
const API_BASE = 'http://SERVER_IP:8000/api'  // Replace SERVER_IP
```

### 3. Network Configuration:
- Open port 8000 on server firewall
- Use static IP or dynamic DNS for server
- Consider VPN for security

## Pros:
- ✅ Single source of truth
- ✅ No concurrent access issues  
- ✅ Centralized data processing
- ✅ Easy to add authentication later

## Cons:
- ⚠️ Server dependency (single point of failure)
- ⚠️ Network latency
- ⚠️ Need to keep server running
