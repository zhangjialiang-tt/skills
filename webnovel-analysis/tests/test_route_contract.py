from pathlib import Path

import json


ROOT = Path(__file__).parents[1]


def test_trigger_cases_cover_positive_negative_and_neighbor_intents() -> None:
    cases = json.loads((ROOT / "evals" / "trigger_cases.json").read_text(encoding="utf-8"))
    assert len(cases["should_trigger"]) >= 5
    assert len(cases["should_not_trigger"]) >= 5
    assert len(cases["near_neighbor"]) >= 3


def test_internal_module_names_are_not_public_skill_triggers() -> None:
    route_policy = (ROOT / "references" / "route-policy.md").read_text(encoding="utf-8")
    assert "唯一外部入口" in route_policy
    assert "不得直接路由" in route_policy

