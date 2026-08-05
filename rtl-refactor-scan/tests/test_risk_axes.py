"""验证三轴分类模型的枚举值与提案 §5.2 一致。"""
import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "risk-axes.schema.json"


def load_axes():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return schema["properties"]


def test_severity_values():
    axes = load_axes()
    assert axes["severity"]["enum"] == ["critical", "high", "medium", "low", "info"]


def test_confidence_values():
    axes = load_axes()
    assert axes["confidence"]["enum"] == ["confirmed", "probable", "hypothesis", "unknown"]


def test_actionability_values():
    axes = load_axes()
    assert axes["actionability"]["enum"] == [
        "safe_candidate",
        "plan_required",
        "manual_design_required",
        "report_only",
        "out_of_scope",
    ]


def test_abc_mapping_documented():
    """A/B/C 兼容显示层映射必须存在（提案 §5.3）。"""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert "_abc_compatible_display" in schema
    mapping = schema["_abc_compatible_display"]
    assert mapping["A"] == ["critical", "high"]
    assert mapping["B"] == ["medium"]
    assert mapping["C"] == ["low", "info"]
