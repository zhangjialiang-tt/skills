#!/usr/bin/env python3
"""validate_approval.py - ApprovalRef 有效性校验工具。

校验 ApprovalRef YAML/JSON 文件：status 是否 ACTIVE、operation 是否匹配、
approved_scope 是否覆盖目标文件、based_on_revision 是否与当前一致、
一次性授权是否已使用。输出 INVALID_APPROVAL 具体原因。
"""

import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


APPROVAL_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "approval-ref.schema.json"
)


def load_approval(approval_path: Path) -> dict[str, Any]:
    """加载 ApprovalRef 文件（YAML 或 JSON）。"""
    if not approval_path.exists():
        raise FileNotFoundError(f"ApprovalRef 文件不存在: {approval_path}")
    with open(approval_path, "r", encoding="utf-8") as f:
        suffix = approval_path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            data = yaml.safe_load(f)
        elif suffix == ".json":
            data = json.load(f)
        else:
            content = f.read()
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ValueError(f"ApprovalRef 格式无效（非字典）: {approval_path}")
    return data


def load_revisions(revisions_path: Path) -> dict[str, Any]:
    """加载 .revisions.json。"""
    if not revisions_path.exists():
        return {}
    with open(revisions_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_scope_coverage(
    approved_scope: list[str] | str, target_files: list[str]
) -> list[str]:
    """检查 approved_scope 是否覆盖所有目标文件。

    Returns:
        未覆盖的文件列表
    """
    if isinstance(approved_scope, str):
        approved_scope = [approved_scope]

    uncovered: list[str] = []
    for target in target_files:
        covered = False
        for scope in approved_scope:
            if scope.endswith("/"):
                # 目录前缀匹配
                if target.startswith(scope) or target == scope.rstrip("/"):
                    covered = True
                    break
            else:
                # 精确匹配或通配符
                if target == scope:
                    covered = True
                    break
                # 支持简单的 * 通配
                if "*" in scope:
                    import fnmatch
                    if fnmatch.fnmatch(target, scope):
                        covered = True
                        break
        if not covered:
            uncovered.append(target)
    return uncovered


@lru_cache(maxsize=1)
def _approval_validator() -> Draft202012Validator:
    """加载并缓存 ApprovalRef Schema 校验器。"""
    with open(APPROVAL_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    return Draft202012Validator(schema)


def validate_approval(
    approval: dict[str, Any],
    operation: str,
    target_files: list[str],
    current_revision: str,
    request_id: str | None = None,
    target_items: list[str] | None = None,
) -> list[str]:
    """执行 ApprovalRef 校验，返回错误原因列表。"""
    errors: list[str] = []

    # 1. 检查 Schema
    for error in sorted(
        _approval_validator().iter_errors(approval),
        key=lambda item: list(item.absolute_path),
    ):
        path = ".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"Schema {path}: {error.message}")

    # Schema 错误可能意味着下方字段类型不安全，避免派生异常。
    if errors:
        return errors

    # 2. 检查 status
    status = approval.get("status", "")
    if status != "ACTIVE":
        errors.append(f"status 不是 ACTIVE（当前: '{status}'）")

    # 3. 检查 request_id 绑定
    if request_id is not None and approval.get("request_id") != request_id:
        errors.append(
            f"request_id 不匹配: 授权为 '{approval.get('request_id', '')}'，"
            f"请求为 '{request_id}'"
        )

    # 4. 检查 operation 匹配
    approved_op = approval.get("operation", "")
    init_covers_initial_canon = (
        approved_op == "INIT_PROJECT" and operation == "COMMIT_CANON"
    )
    if approved_op != operation and not init_covers_initial_canon:
        errors.append(
            f"operation 不匹配: 授权为 '{approved_op}'，请求为 '{operation}'"
        )

    # 5. 检查 approved_scope 覆盖
    approved_scope = approval.get("approved_scope", {})
    approved_files = approved_scope.get("files", [])
    approved_items = approved_scope.get("items", [])
    if not approved_files:
        errors.append("approved_scope 为空，未授权任何文件")
    else:
        uncovered = check_scope_coverage(approved_files, target_files)
        if uncovered:
            errors.append(
                f"approved_scope 未覆盖以下文件: {uncovered}"
            )

    if target_items:
        uncovered_items = [
            item for item in target_items if item not in approved_items
        ]
        if uncovered_items:
            errors.append(
                f"approved_scope 未覆盖以下条目: {uncovered_items}"
            )

    # 6. based_on_revision 绑定的是用户审阅的来源交付物。
    based_on = approval.get("based_on_revision", "")
    if str(based_on) != str(current_revision):
        errors.append(
            "based_on_revision 不一致: "
            f"授权时 revision='{based_on}'，当前 revision='{current_revision}'"
        )

    # 7. L4/RETCON 必须使用一次性授权；已使用由 status=USED 表达。
    expires_after_use = approval.get("expires_after_use", False)
    if operation in ("EDIT_L4", "RETCON") and not expires_after_use:
        errors.append(f"{operation} 必须使用 expires_after_use=true 的一次性授权")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验 ApprovalRef 有效性"
    )
    parser.add_argument(
        "--approval", required=True, help="ApprovalRef 文件路径（YAML/JSON）"
    )
    parser.add_argument(
        "--operation", required=True, help="请求的操作名称"
    )
    parser.add_argument(
        "--target-files", nargs="+", required=True, help="目标文件列表"
    )
    parser.add_argument(
        "--current-revision",
        required=True,
        help="用户批准的来源文件或交付物的当前 revision",
    )
    parser.add_argument("--request-id", default=None, help="当前请求 ID")
    parser.add_argument(
        "--target-items",
        nargs="*",
        default=None,
        help="需要授权覆盖的条目标识",
    )
    args = parser.parse_args()

    approval_path = Path(args.approval)

    try:
        approval = load_approval(approval_path)
    except (FileNotFoundError, ValueError, yaml.YAMLError, json.JSONDecodeError) as e:
        print(f"ERROR: 加载 ApprovalRef 失败: {e}", file=sys.stderr)
        return 2

    errors = validate_approval(
        approval,
        args.operation,
        args.target_files,
        args.current_revision,
        request_id=args.request_id,
        target_items=args.target_items,
    )

    if errors:
        result = {
            "status": "INVALID_APPROVAL",
            "approval_file": str(approval_path),
            "reasons": errors,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        for err in errors:
            print(f"  INVALID_APPROVAL: {err}", file=sys.stderr)
        return 1

    result = {
        "status": "VALID",
        "approval_file": str(approval_path),
        "operation": args.operation,
        "target_files": args.target_files,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
