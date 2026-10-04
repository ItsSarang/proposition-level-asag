"""Grading endpoint route."""
from fastapi import APIRouter, HTTPException
from backend.api.schemas.grading_schema import GradingRequest, GradingResponse
from backend.services.grading_service import GradingService

router = APIRouter()
grading_service = GradingService()

@router.post("/grade", response_model=GradingResponse)
def grade_answer(request: GradingRequest):
    try:
        return grading_service.grade_answer(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grading error: {str(e)}")
