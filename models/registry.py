"""
Central Model Registry for Proposition-Level ASAG Research Project.

Enables seamless model discovery and instantiation across the three benchmarked systems:
- V0: TF-IDF Baseline (Model 1)
- V1: Base ASAG (Basak et al. 2019-inspired) (Model 2)
- V5: Proposed Proposition-Level ASAG (Model 3)
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

@dataclass(frozen=True)
class ModelMetadata:
    version: str
    name: str
    description: str
    status: str
    pipeline_module: str
    config: Dict[str, Any]

MODELS: Dict[str, ModelMetadata] = {
    "V0": ModelMetadata(
        version="V0",
        name="Model 1 — TF-IDF Baseline",
        description="Simple TF-IDF + cosine similarity lexical baseline.",
        status="ACTIVE",
        pipeline_module="models.v0_tfidf.predictor.V0Predictor",
        config={"scale": 5.0},
    ),
    "V1": ModelMetadata(
        version="V1",
        name="Model 2 — Base ASAG (Basak et al. 2019-inspired)",
        description="Classical semantic/dependency clausal triple ASAG pipeline.",
        status="ACTIVE",
        pipeline_module="models.v1_base_asag.pipeline.BaseASAGPipeline",
        config={"scale": 5.0, "threshold": 0.55},
    ),
    "V5": ModelMetadata(
        version="V5",
        name="Model 3 — Proposed Proposition-Level ASAG",
        description="Proposed model with canonical fragments, core paraphrase recovery, contradiction guards, and 4-way classification.",
        status="ACTIVE",
        pipeline_module="models.v5_proposed.pipeline.Experiment5Pipeline",
        config={"scale": 5.0, "scorer": "Model D2", "core_recovery": True, "guards": True},
    ),
}

class ModelRegistry:
    """
    Central discovery, configuration, and instantiation registry for ASAG models.

    Supports the three benchmarked systems (V0, V1, V5), providing a uniform discovery layer so that
    evaluation runners, backend APIs, and CLI tools do not depend on internal
    pipeline paths.
    """

    @staticmethod
    def get_model(version: str, **kwargs: Any) -> Any:
        """
        Instantiate an ASAG pipeline model by version identifier.

        Parameters
        ----------
        version : str
            Model version string: 'V0', 'V1', 'V2', 'V3', 'V4', or 'V5'.
            Case-insensitive and whitespace-tolerant.
        **kwargs : Any
            Optional configuration overrides passed to model constructor
            (e.g., scale=5.0). Filtered by constructor signature.

        Returns
        -------
        Any
            Instantiated pipeline model providing the standardized .evaluate() method.

        Raises
        ------
        ValueError
            If the requested version is not recognized.
        """
        ver = version.upper().strip()
        if ver not in MODELS:
            raise ValueError(f"Unknown model version: '{version}'. Valid options: {list(MODELS.keys())}")
        
        meta = MODELS[ver]
        mod_name, cls_name = meta.pipeline_module.rsplit(".", 1)
        import importlib
        import inspect
        module = importlib.import_module(mod_name)
        cls = getattr(module, cls_name)
        sig = inspect.signature(cls.__init__)
        has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
        if has_varkw:
            call_kwargs = kwargs
        else:
            call_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
        return cls(**call_kwargs)

    @staticmethod
    def list_models() -> List[Dict[str, Any]]:
        """
        List all registered model versions and their research descriptions.

        Returns
        -------
        List[Dict[str, Any]]
            Dictionaries containing version, name, description, and frozen status.
        """
        return [
            {
                "version": m.version,
                "name": m.name,
                "description": m.description,
                "status": m.status,
            }
            for m in MODELS.values()
        ]

    @staticmethod
    def get_metadata(version: str) -> Optional[ModelMetadata]:
        """
        Retrieve frozen metadata for a specific model version.

        Parameters
        ----------
        version : str
            Model version identifier (e.g. 'V5').

        Returns
        -------
        Optional[ModelMetadata]
            Metadata record if found, or None if unrecognized.
        """
        return MODELS.get(version.upper().strip())

get_model = ModelRegistry.get_model
list_models = ModelRegistry.list_models
get_metadata = ModelRegistry.get_metadata

__all__ = ["ModelRegistry", "ModelMetadata", "MODELS", "get_model", "list_models", "get_metadata"]
