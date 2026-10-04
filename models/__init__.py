"""
ASAG Research Models Registry & Version Isolated Implementations.

Versions:
- V0: TF-IDF + Cosine Similarity Baseline
- V1: Basak et al. (2019)-inspired Base ASAG
- V2: Proposition-Level ASAG (Stages 11-14)
- V3: Enhanced Proposition-Level ASAG (System 4 Overhaul)
- V4: Severity-Aware Proposition ASAG (Experiment 4, Model D)
- V5: Final Proposition-Level ASAG (Experiment 5, Model D2)
"""
from models.registry import get_model, list_models, ModelRegistry

__all__ = ["get_model", "list_models", "ModelRegistry"]
