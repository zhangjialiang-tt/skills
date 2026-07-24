#!/usr/bin/env python3
"""validate_paths.py - 路径安全校验工具。

确认路径位于 root_path 内，防止 `..`、符号链接和路径规范化逃逸，
校验目标路径是否属于目标 Skill 所有权区域，检测跨项目访问。
"""

import argparse
import json
import os
import sys
from pathlib import Path, PurePosixPath
from typing import Any

# 所有权映射（与 references/file-ownership.md 一致）
OWNERSHIP: dict[str, dict[str, list[str]]] = {
    "novel-master": {"write": ["project.yaml", "workflow/"]},
    "novel-brief": {"write": ["project_brief.md"]},
    "story-architect/STORY": {"write": ["architecture/"]},
    "story-architect/CHARACTER": {"write": ["characters/"]},
    "story-architect/WORLD": {"write": ["world/"]},
    "story-architect/PLOT": {"write": ["outline/"]},
    "chapter-planner": {"write": ["chapters/plans/"]},
    "chapter-writer": {"write": ["chapters/drafts/"]},
    "novel-reviewer": {"write": ["reviews/"]},
    "continuity-keeper": {"write": ["state/"]},
}


def normalize_path(root: Path, relative: str) -> tuple[Path | None, str | None]:
    """将相对路径规范化并确认在 root 内。

    Returns:
        (resolved_path, None) 如果合法
        (None, error_message) 如果非法
    """
    # 检测显式 .. 组件
    parts = PurePosixPath(relative).parts
    if ".." in parts:
        return None, f"路径包含 '..' 组件: {relative}"

    # 检测绝对路径
    if PurePosixPath(relative).is_absolute():
        return None, f"路径为绝对路径，不允许: {relative}"

    # 规范化
    candidate = (root / relative).resolve()
    root_resolved = root.resolve()

    # 确认在 root 内
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        return None, f"路径逃逸出项目根目录: {relative} -> {candidate}"

    # 检测符号链接逃逸
    if candidate.exists() and candidate.is_symlink():
        link_target = candidate.resolve()
        try:
            link_target.relative_to(root_resolved)
        except ValueError:
            return None, f"符号链接指向项目外部: {relative} -> {link_target}"

    return candidate, None


def check_ownership(relative: str, skill: str) -> tuple[bool, str | None]:
    """检查路径是否在指定 Skill 的写权限范围内。

    Returns:
        (True, None) 如果合法
        (False, error_message) 如果越权
    """
    if skill not in OWNERSHIP:
        return False, f"未知 Skill: {skill}"

    write_zones = OWNERSHIP[skill]["write"]
    # 规范化相对路径（使用 posix 风格）
    normalized = PurePosixPath(relative).as_posix()

    for zone in write_zones:
        if zone.endswith("/"):
            # 目录前缀匹配
            if normalized.startswith(zone) or normalized == zone.rstrip("/"):
                return True, None
        else:
            # 精确文件匹配
            if normalized == zone:
                return True, None

    return False, (
        f"路径 '{relative}' 不在 Skill '{skill}' 的写权限范围内。"
        f"允许区域: {write_zones}"
    )


def detect_cross_project(root: Path, relative: str) -> str | None:
    """检测是否存在跨项目访问（路径中包含其他项目标识）。"""
    # V1 简化实现：检测路径是否试图访问上级目录中的其他项目
    normalized = PurePosixPath(relative).as_posix()
    # 如果路径尝试回到上级再进入其他目录，normalize_path 已拦截
    # 此处额外检测是否包含明确的项目外引用模式
    suspicious_patterns = ["../", "..\\"]
    for pattern in suspicious_patterns:
        if pattern in normalized:
            return f"检测到跨项目访问模式: {pattern} in '{relative}'"
    return None


def validate_paths(
    root: Path, skill: str, paths: list[str]
) -> list[dict[str, Any]]:
    """校验一组路径，返回结果列表。"""
    results: list[dict[str, Any]] = []

    for rel_path in paths:
        entry: dict[str, Any] = {"path": rel_path, "valid": True, "errors": []}

        # 1. 路径安全校验
        resolved, err = normalize_path(root, rel_path)
        if err:
            entry["valid"] = False
            entry["errors"].append(err)

        # 2. 跨项目检测
        cross_err = detect_cross_project(root, rel_path)
        if cross_err:
            entry["valid"] = False
            entry["errors"].append(cross_err)

        # 3. 所有权校验
        if skill:
            owned, own_err = check_ownership(rel_path, skill)
            if not owned:
                entry["valid"] = False
                entry["errors"].append(own_err or "所有权校验失败")

        results.append(entry)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验路径安全性和 Skill 所有权"
    )
    parser.add_argument(
        "--root", required=True, help="项目根目录路径"
    )
    parser.add_argument(
        "--skill", default="", help="目标 Skill 名称（用于所有权校验）"
    )
    parser.add_argument(
        "--paths", nargs="+", required=True, help="待校验的相对路径列表"
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"ERROR: 项目根目录不存在: {root}", file=sys.stderr)
        return 2

    results = validate_paths(root, args.skill, args.paths)

    all_valid = all(r["valid"] for r in results)
    output = {
        "status": "VALID" if all_valid else "INVALID",
        "root": str(root),
        "skill": args.skill or None,
        "results": results,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

    if not all_valid:
        for r in results:
            if not r["valid"]:
                for err in r["errors"]:
                    print(f"  PATH_ERROR: {err}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
