"""Schemas for ASAG Backend API."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class GradingRequest(BaseModel):
    model: str = Field(default="V5", description="Model version: V0, V1, V2, V3, V4, V5")
    question: str = Field(..., description="Question prompt text")
    reference_answer: str = Field(..., description="Ground truth reference answer")
    student_answer: str = Field(..., description="Student response text")
    scale: float = Field(default=5.0, description="Grading scale maximum (e.g. 5.0)")

class GradingResponse(BaseModel):
    model_version: str
    question: str
    reference_answer: str
    student_answer: str
    normalized_score: float
    grade: float
    max_points: float
    explanation: str
    metadata: Optional[Dict[str, Any]] = None

class ModelInfo(BaseModel):
    version: str
    name: str
    description: str
    status: str

class ModelListResponse(BaseModel):
    models: List[ModelInfo]
