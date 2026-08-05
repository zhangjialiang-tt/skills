"""验证 finding.schema.json 能校验提案 §5.1 的示例 Finding，且拒绝缺证据的 confirmed。"""
import json
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "finding.schema.json"


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


VALID_FINDING = {
    "finding_id": "RTL-CDC-001",
    "rule_id": "CDC-MULTIBIT-DIRECT-001",
    "category": "cdc",
    "title": "多 bit 信号直接跨时钟域",
    "locations": [{"file": "rtl/foo.v", "start_line": 120, "end_line": 127}],
    "severity": "critical",
    "confidence": "confirmed",
    "evidence_level": "E2",
    "evidence": [{"type": "source_relation", "description": "wr_data 在 clk_a 域赋值，在 clk_b 域直接使用"}],
    "impact": ["data tearing", "metastability"],
    "actionability": "manual_design_required",
    "change_policy": "do_not_auto_fix",
    "verification_obligations": ["CDC structure validation", "existing regression"]
}


def test_valid_finding_passes():
    jsonschema.validate(VALID_FINDING, load_schema())


def test_missing_required_field_fails():
    schema = load_schema()
    bad = {k: v for k, v in VALID_FINDING.items() if k != "rule_id"}
    try:
        jsonschema.validate(bad, schema)
        assert False, "should have rejected missing rule_id"
    except jsonschema.ValidationError:
        pass


def test_confidence_confirmed_requires_e2_plus():
    """提案 M1 验收：无证据（E0）的 Finding 不能标 confirmed。"""
    schema = load_schema()
    bad = dict(VALID_FINDING)
    bad["evidence_level"] = "E0"
    bad["confidence"] = "confirmed"
    try:
        jsonschema.validate(bad, schema)
        assert False, "E0 evidence cannot be confirmed"
    except jsonschema.ValidationError:
        pass


def test_severity_enum_enforced():
    schema = load_schema()
    bad = dict(VALID_FINDING)
    bad["severity"] = "catastrophic"
    try:
        jsonschema.validate(bad, schema)
        assert False
    except jsonschema.ValidationError:
        pass
