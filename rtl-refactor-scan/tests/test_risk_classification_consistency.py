"""验证 risk-classification.md 不再包含独立的 A/B/C 规则定义，
且明确声明 rules.yaml 为唯一权威源。"""
from pathlib import Path

RC_PATH = Path(__file__).resolve().parent.parent / "references" / "risk-classification.md"


def test_no_independent_rule_definitions():
    """旧文件 L16 把 variable part-select 列为 A 类——新文件不得再独立定义。"""
    text = RC_PATH.read_text(encoding="utf-8")
    # 必须声明权威源
    assert "rules.yaml" in text
    assert "唯一权威" in text
    # 不应出现旧的独立分级表标题
    assert "## A 类：必须优先处理" not in text
    assert "## B 类：建议优化" not in text
    assert "## C 类：只报告，不修改" not in text


def test_abc_is_display_mapping_only():
    text = RC_PATH.read_text(encoding="utf-8")
    assert "显示层" in text or "display" in text.lower()
    assert "severity" in text
    assert "actionability" in text
