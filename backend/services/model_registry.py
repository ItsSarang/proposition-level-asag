"""
Backend adapter for Central Model Registry.

Provides an isolated service boundary for accessing the models package from
FastAPI route controllers.
"""
from typing import Any, Dict, List
from models.registry import get_model as _get_model, list_models as _list_models


class BackendModelRegistry:
    """
    Service adapter wrapping models.registry for backend API dependency injection.
    """

    @staticmethod
    def get_model(version: str, **kwargs: Any) -> Any:
        """
        Retrieve instantiated model pipeline by version key.
        """
        return _get_model(version, **kwargs)

    @staticmethod
    def list_models() -> List[Dict[str, Any]]:
        """
        List all available registered ASAG model versions.
        """
        return _list_models()
