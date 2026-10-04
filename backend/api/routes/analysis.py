"""
Analysis route exposing deep 7-phase ASAG inspection for ASAG Lab.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

from backend.services.analysis_service import ASAGAnalysisService

router = APIRouter()
analysis_service = ASAGAnalysisService()


class AnalysisRequest(BaseModel):
    question: str = Field(..., description="Question prompt")
    reference_answer: str = Field(..., description="Reference answer")
    student_answer: str = Field(..., description="Student response")
    scale: float = Field(default=5.0, description="Grading scale max")


@router.post("/analyze")
def analyze_answer(req: AnalysisRequest) -> Dict[str, Any]:
    """
    Execute 7-phase ASAG analysis and return structured provenance.
    """
    try:
        return analysis_service.analyze(
            question=req.question,
            reference_answer=req.reference_answer,
            student_answer=req.student_answer,
            scale=req.scale,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis engine error: {str(e)}")
