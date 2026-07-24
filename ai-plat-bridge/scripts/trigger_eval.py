#!/usr/bin/env python3
"""Deterministic routing smoke test for ai-plat-bridge."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
EVALS_FILE = SKILL_DIR / "evals" / "evals.json"
VAULT_ROOT = (
    r"C:\Users\zhangjl\Documents\obsidian-syncthing\AI-Plat\AI-Plat"
).lower()

SCOPES = {
    "task": "20-Tasks",
    "knowledge": "70-Knowledge",
    "log": "10-Daily",
    "project": "30-Projects",
}

ALLOWED_ACTIONS = {
    "task": {"list", "search", "read", "create", "update", "archive"},
    "knowledge": {"list", "search", "read", "create", "update"},
    "log": {"list", "read", "create", "append"},
    "project": {"list", "search", "read", "create", "update"},
}


def base_result() -> dict:
    return {
        "operation_mode": "none",
        "card_type": None,
        "action": None,
        "needs_clarification": False,
        "access_allowed": False,
        "allowed_scope": None,
        "linked_actions": [],
        "requires_pre_read": False,
        "requires_dedup": False,
        "requires_post_read": False,
        "create_daily_if_missing": False,
        "preserve_dirty_files": True,
        "denied_reason": None,
    }


def deny(reason: str) -> dict:
    result = base_result()
    result["denied_reason"] = reason
    return result


def has_external_absolute_path(prompt: str) -> bool:
    paths = re.findall(r"[A-Za-z]:\\[^\s，。；;]*", prompt)
    return any(not path.lower().startswith(VAULT_ROOT) for path in paths)


def detect_card_types(prompt: str) -> list[str]:
    matches = []
    patterns = {
        "task": ["任务卡", "活跃任务", "完成任务", "归档任务"],
        "knowledge": ["知识卡", "知识库", "知识条目"],
        "log": ["日志卡", "今日日志", "今天干了什么", "写工作日志"],
        "project": ["项目卡", "项目状态", "项目文件", "项目记忆"],
    }
    for card_type, keywords in patterns.items():
        if any(keyword in prompt for keyword in keywords):
            matches.append(card_type)
    return matches


def detect_action(prompt: str, card_type: str) -> str:
    if any(word in prompt for word in ["归档", "完成任务"]):
        return "archive"
    if any(word in prompt for word in ["创建", "新建"]):
        return "create"
    if card_type == "log" and any(
        word in prompt for word in ["写工作日志", "追加", "记录"]
    ):
        return "append"
    if any(word in prompt for word in ["更新", "推进", "同步", "修改", "补充"]):
        return "update"
    if any(word in prompt for word in ["搜索", "查找"]):
        return "search"
    if any(word in prompt for word in ["列出", "哪些", "活跃任务"]):
        return "list"
    return "read"


def classify(prompt: str) -> dict:
    legacy_file_name = "memory" + ".md"
    if any(word in prompt.lower() for word in [".workbuddy", legacy_file_name]):
        return deny("legacy-memory")
    if "旧记忆" in prompt:
        return deny("legacy-memory")
    if "../" in prompt or "..\\" in prompt or has_external_absolute_path(prompt):
        return deny("path-outside-allowlist")

    card_types = detect_card_types(prompt)
    is_write_request = any(
        word in prompt
        for word in ["创建", "新建", "更新", "推进", "同步", "修改", "补充", "追加", "归档"]
    ) or "写工作日志" in prompt
    if is_write_request and any(word in prompt for word in ["模板", "template"]):
        return deny("read-only-control-file")

    broad_request = any(
        phrase in prompt for phrase in ["查工作台", "工作台同步", "记录到工作台"]
    )
    if broad_request and not card_types:
        result = base_result()
        result["operation_mode"] = "clarify"
        result["needs_clarification"] = True
        return result

    if len(card_types) > 1:
        if set(card_types) == {"task", "project"} and "关联项目" in prompt:
            card_types = ["task"]
        else:
            result = base_result()
            result["operation_mode"] = "clarify"
            result["needs_clarification"] = True
            return result

    if not card_types:
        return base_result()

    card_type = card_types[0]
    action = detect_action(prompt, card_type)
    if card_type == "log" and action == "update":
        action = "append"
    if action not in ALLOWED_ACTIONS[card_type]:
        return deny("action-not-allowed")

    write_actions = {"create", "update", "append", "archive"}
    result = base_result()
    result.update(
        {
            "operation_mode": "write" if action in write_actions else "read",
            "card_type": card_type,
            "action": action,
            "access_allowed": True,
            "allowed_scope": SCOPES[card_type],
        }
    )

    if action in write_actions:
        result["requires_pre_read"] = True
        result["requires_dedup"] = True
        result["requires_post_read"] = True

        if card_type == "task":
            result["linked_actions"] = ["log"]
            project_changes = [
                "项目状态",
                "项目目标",
                "项目阻塞",
                "已验证结论",
                "关键决策",
                "下一步",
            ]
            if "关联项目" in prompt and any(
                change in prompt for change in project_changes
            ):
                result["linked_actions"].append("project")
        elif card_type in {"project", "knowledge"} and action in {
            "create",
            "update",
        }:
            result["linked_actions"] = ["log"]

        result["create_daily_if_missing"] = "log" in result["linked_actions"]

    return result


def compare_expected(actual: dict, expected: dict) -> list[str]:
    failures = []
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if actual_value != expected_value:
            failures.append(
                f"{key}: expected={expected_value!r}, actual={actual_value!r}"
            )
    return failures


def run_eval() -> int:
    with EVALS_FILE.open("r", encoding="utf-8") as handle:
        cases = json.load(handle).get("evals", [])

    failed = 0
    print("ai-plat-bridge card routing eval")
    print(f"cases={len(cases)}")

    for case in cases:
        actual = classify(case.get("prompt", ""))
        failures = compare_expected(actual, case.get("expected", {}))
        if failures:
            failed += 1
            print(f"FAIL case={case.get('id')}")
            for failure in failures:
                print(f"  {failure}")
        else:
            print(f"PASS case={case.get('id')}")

    passed = len(cases) - failed
    print(f"result passed={passed} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_eval())
