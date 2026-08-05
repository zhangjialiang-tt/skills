#!/usr/bin/env python3
"""规则引擎：加载 rules.yaml，按 rule_id 索引，过滤 deterministic 规则。"""
from pathlib import Path
import yaml


class RuleEngine:
    def __init__(self, rules_path):
        data = yaml.safe_load(Path(rules_path).read_text(encoding="utf-8"))
        self.rules = data.get("rules", [])
        self._by_id = {r["rule_id"]: r for r in self.rules}

    def get(self, rule_id):
        return self._by_id.get(rule_id)

    def deterministic_rules(self):
        return [r for r in self.rules if r.get("detection", {}).get("method") == "deterministic"]

    def by_category(self, category):
        return [r for r in self.rules if r.get("category") == category]
