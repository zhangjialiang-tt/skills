#!/usr/bin/env python3
"""validate_contract.py - JSON Schema 校验工具。

加载指定 JSON Schema 文件，校验 YAML 或 JSON 输入文件，
输出清晰错误路径（jsonpath 格式）。校验失败返回非零退出码。
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
import jsonschema
from jsonschema import Draft202012Validator, ValidationError


ALLOWED_CHAPTER_TRANSITIONS = {
    ("PLANNED", "DRAFT"),
    ("DRAFT", "REVIEWED"),
    ("DRAFT", "ACCEPTED"),
    ("REVIEWED", "DRAFT"),
    ("REVIEWED", "ACCEPTED"),
    ("ACCEPTED", "SUPERSEDED"),
    ("ACCEPTED", "DEPRECATED"),
    ("ACCEPTED", "PUBLISHED"),
}

COMMIT_ELIGIBLE_CHAPTER_STATES = {"ACCEPTED", "PUBLISHED"}


def is_valid_chapter_transition(from_state: str, to_state: str) -> bool:
    """检查章节生命周期转换是否属于冻结合同允许集合。"""
    return (from_state, to_state) in ALLOWED_CHAPTER_TRANSITIONS


def can_commit_chapter_state(status: str) -> bool:
    """检查章节是否可以作为 COMMIT_CHAPTER_STATE 来源。"""
    return status in COMMIT_ELIGIBLE_CHAPTER_STATES


def load_schema(schema_path: Path) -> dict[str, Any]:
    """加载 JSON Schema 文件。"""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema 文件不存在: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_input(input_path: Path) -> Any:
    """加载 YAML 或 JSON 输入文件。"""
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        suffix = input_path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            return yaml.safe_load(f)
        elif suffix == ".json":
            return json.load(f)
        else:
            # 尝试先 JSON 再 YAML
            content = f.read()
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return yaml.safe_load(content)


def format_jsonpath(path: list[Any]) -> str:
    """将 jsonschema 的 path 转换为 jsonpath 格式。"""
    parts = ["$"]
    for segment in path:
        if isinstance(segment, int):
            parts.append(f"[{segment}]")
        else:
            parts.append(f".{segment}")
    return "".join(parts)


def validate(schema: dict[str, Any], data: Any) -> list[str]:
    """执行校验，返回错误列表（jsonpath 格式）。"""
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        path = format_jsonpath(list(error.absolute_path))
        errors.append(f"{path}: {error.message}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验 YAML/JSON 文件是否符合指定 JSON Schema"
    )
    parser.add_argument(
        "--schema", required=True, help="JSON Schema 文件路径"
    )
    parser.add_argument(
        "--input", required=True, help="待校验的 YAML/JSON 输入文件路径"
    )
    args = parser.parse_args()

    schema_path = Path(args.schema)
    input_path = Path(args.input)

    try:
        schema = load_schema(schema_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: 加载 Schema 失败: {e}", file=sys.stderr)
        return 2

    try:
        data = load_input(input_path)
    except (FileNotFoundError, json.JSONDecodeError, yaml.YAMLError) as e:
        print(f"ERROR: 加载输入文件失败: {e}", file=sys.stderr)
        return 2

    try:
        errors = validate(schema, data)
    except jsonschema.SchemaError as e:
        print(f"ERROR: Schema 本身无效: {e.message}", file=sys.stderr)
        return 2

    if errors:
        print(f"VALIDATION_FAILED: {len(errors)} 个错误", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    print(json.dumps({"status": "VALID", "file": str(input_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
