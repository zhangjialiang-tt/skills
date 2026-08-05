#!/usr/bin/env python3
"""校验 rules.yaml：每条规则有三轴、rule_id 合法、detection.method 在允许集合内。"""
import re
import sys
from pathlib import Path

import yaml

ALLOWED_METHODS = {"deterministic", "semantic", "tool_assisted"}
ALLOWED_CATEGORIES = {"synthesis", "reset", "cdc", "handshake", "pipeline", "memory", "timing-heuristic", "debug"}
RULE_ID_PATTERN = re.compile(r"^[A-Z]+-[A-Z0-9-]+-[0-9]{3}$")


def validate_rules(rules_path):
    """返回违规规则 id 列表（空列表 = 全部合规）。"""
    data = yaml.safe_load(Path(rules_path).read_text(encoding="utf-8"))
    violations = []
    for r in data.get("rules", []):
        rid = r.get("rule_id", "<unknown>")
        if not RULE_ID_PATTERN.match(str(rid)):
            violations.append(f"{rid}: invalid rule_id format")
        if r.get("category") not in ALLOWED_CATEGORIES:
            violations.append(f"{rid}: bad category {r.get('category')}")
        for field in ("default_severity", "default_confidence", "default_actionability"):
            if field not in r:
                violations.append(f"{rid}: missing {field}")
        det = r.get("detection", {})
        if det.get("method") not in ALLOWED_METHODS:
            violations.append(f"{rid}: bad detection.method {det.get('method')}")
    return violations


def main():
    if len(sys.argv) < 2:
        print("usage: validate_rules.py <rules.yaml>", file=sys.stderr)
        return 2
    violations = validate_rules(sys.argv[1])
    if violations:
        for v in violations:
            print(f"  VIOLATION: {v}", file=sys.stderr)
        return 1
    print(f"[PASS] {sys.argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
