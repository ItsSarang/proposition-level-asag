"""
Shared grading explanation trace generator.

Constructs structured, human-readable audit traces explaining how reference
proposition coverage and proposition-level adjustments combine into final grades.
"""
from proposed_asag.explanation.trace_generator import (
    ExplanationTraceGenerator,
    GradingExplanationTrace,
)

__all__ = ["ExplanationTraceGenerator", "GradingExplanationTrace"]
