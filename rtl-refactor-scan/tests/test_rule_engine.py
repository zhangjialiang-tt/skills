"""验证规则引擎能加载 rules.yaml 并按 rule_id 索引。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from rule_engine import RuleEngine

RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "rules.yaml"


def test_engine_loads_all_rules():
    engine = RuleEngine(str(RULES_PATH))
    assert len(engine.rules) >= 10


def test_engine_indexes_by_rule_id():
    engine = RuleEngine(str(RULES_PATH))
    r = engine.get("SYN-MIXED-BLOCKING-001")
    assert r is not None
    assert r["category"] == "synthesis"


def test_engine_filters_deterministic():
    engine = RuleEngine(str(RULES_PATH))
    det = engine.deterministic_rules()
    # 至少 8 条 deterministic（M2 验收门槛）
    assert len(det) >= 8
    for r in det:
        assert r["detection"]["method"] == "deterministic"
