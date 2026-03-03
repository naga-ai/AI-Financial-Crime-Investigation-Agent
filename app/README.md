# WS Intelligence — Application

Backend API, frontend dashboard, and AI agents.

**Full documentation:** See the [top-level README](../README.md).

## Quick commands

```bash
# Generate sample data
python scripts/generate_data.py

# Run API (port 8000)
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000

# Run frontend (port 3000)
cd frontend && npm run dev

# Docker
docker compose up -d
```
