"""Model listing route."""
from fastapi import APIRouter
from backend.api.schemas.grading_schema import ModelListResponse, ModelInfo
from backend.services.model_registry import BackendModelRegistry

router = APIRouter()

@router.get("/models", response_model=ModelListResponse)
def list_models():
    models_raw = BackendModelRegistry.list_models()
    models = [
        ModelInfo(
            version=m["version"],
            name=m["name"],
            description=m["description"],
            status=m["status"],
        )
        for m in models_raw
    ]
    return ModelListResponse(models=models)
