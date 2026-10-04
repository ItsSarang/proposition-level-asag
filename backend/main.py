"""FastAPI application entry point for ASAG Backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import health, models, grading, analysis

app = FastAPI(
    title="Proposition-Level ASAG API",
    description="Backend API adapter for Automatic Short Answer Grading models V0-V5.",
    version="1.0.0",
)

# Enable CORS for React/Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(models.router, prefix="/api", tags=["Models"])
app.include_router(grading.router, prefix="/api", tags=["Grading"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])

@app.get("/")
def root():
    return {
        "message": "Proposition-Level ASAG API is running.",
        "documentation": "/docs",
        "health": "/api/health",
        "models": "/api/models",
    }
