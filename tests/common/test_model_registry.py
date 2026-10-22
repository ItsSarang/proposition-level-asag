"""Integration tests for Central Model Registry and unified V0, V1, V5 evaluation."""
import pytest
from common.types import GradingResult
from models.registry import get_model, list_models, get_metadata

def test_list_models():
    models = list_models()
    assert len(models) == 3
    versions = [m["version"] for m in models]
    assert versions == ["V0", "V1", "V5"]
    for m in models:
        assert m["status"] == "ACTIVE"

def test_get_metadata():
    meta = get_metadata("V5")
    assert meta is not None
    assert meta.version == "V5"
    assert "Proposed" in meta.name

    meta_none = get_metadata("V99")
    assert meta_none is None

def test_get_model_invalid():
    with pytest.raises(ValueError):
        get_model("V99")

@pytest.mark.parametrize("version", ["V0", "V1", "V5"])
def test_all_models_unified_evaluate(version):
    q = "What is the purpose of a primary key?"
    r = "A primary key uniquely identifies each record in a table."
    s = "A primary key uniquely identifies each record in a table and cannot contain NULL values."
    
    model = get_model(version, scale=5.0)
    result = model.evaluate(q, r, s)
    
    assert isinstance(result, GradingResult)
    assert result.model_version == version
    assert 0.0 <= result.normalized_score <= 1.0
    assert 0.0 <= result.grade <= 5.0
    assert result.max_points == 5.0
    assert isinstance(result.explanation, str)
    assert len(result.explanation) > 0
