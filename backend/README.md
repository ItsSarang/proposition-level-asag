# Backend API Adapter

## Role & Architecture
This directory contains the Python backend API adapter for the Automatic Short Answer Grading (ASAG) research engine.

### Strict Architectural Separation
- **The backend is ONLY an API adapter.**
- No NLP algorithms, parsing logic, or scoring heuristics are implemented here.
- The backend delegates all grading operations to `models.registry.get_model()`.

```
Frontend (React/Vite)
       │ HTTP (JSON)
       ▼
Backend API (FastAPI)
       │
GradingService
       │
ModelRegistry (`models/registry.py`)
       │
  ┌────┴────┬─────────┬─────────┬─────────┬─────────┐
  ▼         ▼         ▼         ▼         ▼         ▼
  V0        V1        V2        V3        V4        V5
```

## Endpoints
- `GET /api/health`: Health status.
- `GET /api/models`: List available models (V0 through V5) and metadata.
- `POST /api/grade`: Grade a student answer using a selected model version.

## Deployment Notes (Vercel / Serverless)
- Heavy NLP dependencies (spaCy `en_core_web_sm`, NLTK WordNet) require ~100-200MB memory.
- If deployed on Vercel Serverless Functions, ensure memory is configured to 1024MB+ and python runtime dependencies are pre-warmed.
- For production or self-hosted deployment, running `uvicorn backend.main:app --port 8000` is recommended.
