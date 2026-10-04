"""
TF-IDF + Cosine Similarity Baseline Package.
"""

from baseline.tfidf_cosine.baseline import (
    TfidfCosineBaseline,
    compute_tfidf_cosine_similarity,
)

__all__ = ["TfidfCosineBaseline", "compute_tfidf_cosine_similarity"]
