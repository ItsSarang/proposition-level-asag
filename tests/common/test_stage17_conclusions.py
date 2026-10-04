"""
Unit tests for Stage 17: Research Conclusions and Final Synthesis.

Validates the presence, structure, benchmark consistency, and epistemic integrity
of the final research conclusions report.
"""

from pathlib import Path
import re
import pytest

REPORT_PATH = Path("reports/research_conclusions.md")


def test_research_conclusions_report_exists():
    """Verify that reports/research_conclusions.md exists and is non-empty."""
    assert REPORT_PATH.exists(), f"Missing report at {REPORT_PATH}"
    content = REPORT_PATH.read_text(encoding="utf-8")
    assert len(content) > 2000, "Report is unexpectedly brief"


def test_research_conclusions_required_sections():
    """Verify that all mandatory research sections are present."""
    content = REPORT_PATH.read_text(encoding="utf-8")
    required_sections = [
        "Executive Summary",
        "Research Story and Methodological Foundations",
        "Comprehensive Benchmark Results",
        "Key Discoveries and Scientific Insights",
        "System Comparison & Architectural Evaluation",
        "Answers to the Core Research Question",
        "Threats to Validity and Study Limitations",
        "Recommendations for Future Research",
        "Final Research Statement",
    ]
    for section in required_sections:
        assert section.lower() in content.lower(), f"Missing required section: {section}"


def test_research_conclusions_benchmark_consistency():
    """Verify that reported benchmark numbers match empirical results from Stage 15.2 and 16."""
    content = REPORT_PATH.read_text(encoding="utf-8")

    # Sample sizes
    assert "2,273" in content, "Missing total active sample count 2,273"
    assert "3,611" in content, "Missing total unmatched proposition count 3,611"
    assert "33" in content and "40.7%" in content, "Missing 33 non-clausal reference count"

    # Baseline metrics
    assert "2.6571" in content, "Missing TF-IDF MAE 2.6571"
    assert "0.4184" in content, "Missing TF-IDF Pearson 0.4184"
    assert "0.4424" in content, "Missing TF-IDF Spearman 0.4424"

    # Base ASAG metrics
    assert "3.7794" in content, "Missing Base ASAG MAE 3.7794"
    assert "0.1419" in content, "Missing Base ASAG Pearson 0.1419"
    assert "0.1177" in content, "Missing Base ASAG Spearman 0.1177"

    # Proposed ASAG metrics
    assert "3.2036" in content, "Missing Proposed ASAG MAE 3.2036"
    assert "0.1377" in content, "Missing Proposed ASAG Pearson 0.1377"
    assert "0.0797" in content, "Missing Proposed ASAG Spearman 0.0797"


def test_research_conclusions_epistemic_integrity():
    """Verify that scientific distinctions are rigorously observed."""
    content = REPORT_PATH.read_text(encoding="utf-8")
    assert "PAPER FACT" in content
    assert "IMPLEMENTATION DECISION" in content
    assert "RESEARCH HYPOTHESIS" in content
    assert "EXPERIMENTAL RESULT" in content
    assert "INTERPRETATION" in content


def test_research_conclusions_subquestions_answered():
    """Verify that both research sub-questions are explicitly addressed."""
    content = REPORT_PATH.read_text(encoding="utf-8")
    assert "Research Sub-Question 1" in content
    assert "Research Sub-Question 2" in content
    assert "AFFIRMATIVE" in content or "YES" in content
    assert "MIXED EVIDENCE" in content or "NUANCED" in content
