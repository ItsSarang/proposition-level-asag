"""
Grading Service coordinating model execution and response serialization.

Decouples API route handlers from model registry and evaluation logic.
"""
from typing import Any, Dict, Optional
from backend.api.schemas.grading_schema import GradingRequest, GradingResponse
from backend.services.model_registry import BackendModelRegistry
from common.types import GradingResult


class GradingService:
    """
    Application service that executes grading requests via the model registry.
    """

    def __init__(self, registry: Optional[BackendModelRegistry] = None) -> None:
        """
        Initialize GradingService with an optional model registry instance.

        Parameters
        ----------
        registry : Optional[BackendModelRegistry], default=None
            Registry instance used for model discovery.
        """
        self.registry = registry or BackendModelRegistry()

    def grade_answer(self, req: GradingRequest) -> GradingResponse:
        """
        Grade a student answer using the model version specified in the request.

        Parameters
        ----------
        req : GradingRequest
            Structured request payload containing model version and input texts.

        Returns
        -------
        GradingResponse
            Serialized response containing score, scaled grade, and explanation.
        """
        model = self.registry.get_model(req.model, scale=req.scale)
        res: GradingResult = model.evaluate(
            question=req.question,
            reference_answer=req.reference_answer,
            student_answer=req.student_answer,
        )
        return GradingResponse(
            model_version=res.model_version,
            question=res.question,
            reference_answer=res.reference_answer,
            student_answer=res.student_answer,
            normalized_score=res.normalized_score,
            grade=res.grade,
            max_points=res.max_points,
            explanation=res.explanation,
            metadata=None,  # Avoid transmitting bulky internal parse graphs over HTTP
        )
