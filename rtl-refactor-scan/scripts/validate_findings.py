#!/usr/bin/env python3
"""校验 findings.json：JSON Schema 合法性 + 业务规则（E0 不能 confirmed 等）。"""
import json
import sys
from pathlib import Path

import jsonschema

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"


def load_schema(name):
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validate_findings(findings_path):
    """返回 {passed, errors, finding_count}。"""
    data = json.loads(Path(findings_path).read_text(encoding="utf-8"))
    schema = load_schema("finding.schema.json")
    errors = []

    findings = data.get("findings", [])
    for i, f in enumerate(findings):
        try:
            jsonschema.validate(f, schema)
        except jsonschema.ValidationError as e:
            errors.append(f"finding[{i}] ({f.get('finding_id', '?')}): {e.message}")
            continue
        # 业务规则：E0/E1 不能 confirmed（schema 的 allOf 已覆盖，这里双保险）
        if f.get("confidence") == "confirmed" and f.get("evidence_level") in ("E0", "E1"):
            errors.append(f"{f['finding_id']}: confidence=confirmed requires E2+ evidence, got {f['evidence_level']}")

    return {"passed": len(errors) == 0, "errors": errors, "finding_count": len(findings)}


def main():
    if len(sys.argv) < 2:
        print("usage: validate_findings.py <findings.json> [--json]", file=sys.stderr)
        return 2
    path = sys.argv[1]
    as_json = "--json" in sys.argv[2:]
    result = validate_findings(path)
    if as_json:
        print(json.dumps({"file": path, **result}, ensure_ascii=False, indent=2))
    else:
        verdict = "PASS" if result["passed"] else "FAIL"
        print(f"[{verdict}] {path}  findings={result['finding_count']}")
        for e in result["errors"]:
            print(f"  - {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
