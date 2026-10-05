# Backend API Adapter (Flask)

## Role & Architecture
This directory contains the lightweight Flask backend API adapter for the Automatic Short Answer Grading (ASAG) research engine.

### Strict Architectural Separation
- **The backend is ONLY an API adapter.**
- No NLP algorithms, parsing logic, or scoring heuristics are implemented here.
- The backend delegates all grading operations to `models.registry.get_model()`.

```
Frontend (React/Vite)
       │ HTTP (JSON)
       ▼
Backend API (Flask + CORS)
       │
GradingService / ASAGAnalysisService
       │
ModelRegistry (`models/registry.py`)
       │
  ┌────┴────┬─────────┬─────────┬─────────┬─────────┐
  ▼         ▼         ▼         ▼         ▼         ▼
  V0        V1        V2        V3        V4        V5
```

## Running the Backend
```bash
source .venv/bin/activate
python backend/main.py
```
Server runs on `http://localhost:8000` with CORS enabled for the React frontend.

## Endpoints
- `GET /`: API overview and root metadata.
- `GET /api/health`: Health status.
- `GET /api/models`: List available models (V0 through V5).
- `POST /api/analyze`: 7-phase deep proposition inspection for ASAG Lab Workbench.
- `POST /api/grade`: Direct evaluation across models V0–V5.
