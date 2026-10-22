"""
ASAG Research Models Registry & Benchmark Implementations.

Three Benchmarked Paradigms:
- V0: Model 1 — TF-IDF + Cosine Similarity Baseline
- V1: Model 2 — Basak et al. (2019)-inspired Base ASAG
- V5: Model 3 — Proposed Proposition-Level ASAG (Experiment 5, Model D2)
"""
from models.registry import get_model, list_models, ModelRegistry

__all__ = ["get_model", "list_models", "ModelRegistry"]
