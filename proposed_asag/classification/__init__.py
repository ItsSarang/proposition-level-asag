"""
Additional-Information Classification Package (Stage 13 & Overhaul Phase 7).

Provides components for evaluating unmatched student propositions into:
- CORRECT_ADDITIONAL
- IRRELEVANT
- INCORRECT
- UNCERTAIN
"""

from proposed_asag.classification.additional_info import (
    AdditionalInformationClassifier,
    AdditionalInformationResult,
    CompatibilityAnalyzer,
    CompatibilityEvidence,
    DocumentClassificationResult,
    RelevanceAnalyzer,
    RelevanceEvidence,
)
from proposed_asag.classification.robust_classifier import (
    AdditionalInfoClass,
    ClassifiedProposition,
    RobustAdditionalInfoClassifier,
    RobustClassificationResult,
)

__all__ = [
    "AdditionalInformationClassifier",
    "AdditionalInformationResult",
    "CompatibilityAnalyzer",
    "CompatibilityEvidence",
    "DocumentClassificationResult",
    "RelevanceAnalyzer",
    "RelevanceEvidence",
    "AdditionalInfoClass",
    "ClassifiedProposition",
    "RobustAdditionalInfoClassifier",
    "RobustClassificationResult",
]
