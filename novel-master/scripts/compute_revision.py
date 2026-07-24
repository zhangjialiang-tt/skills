#!/usr/bin/env python3
"""compute_revision.py - 文件 revision 和 SHA-256 计算工具。

计算文件 SHA-256，读取或生成 revision（从文件同目录的 .revisions.json），
内容变化时更新 revision（+1），内容未变化时不递增。
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def compute_sha256(file_path: Path) -> str:
    """计算文件的 SHA-256 哈希值（hex 小写，64 字符）。"""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def load_revisions(revisions_path: Path) -> dict[str, Any]:
    """加载 .revisions.json 文件。"""
    if not revisions_path.exists():
        return {}
    with open(revisions_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_revisions(revisions_path: Path, data: dict[str, Any]) -> None:
    """保存 .revisions.json 文件。"""
    revisions_path.parent.mkdir(parents=True, exist_ok=True)
    with open(revisions_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def get_relative_key(file_path: Path, project_root: Path) -> str:
    """获取文件相对于项目根目录的路径键。"""
    try:
        return file_path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        # 如果无法计算相对路径，使用文件名
        return file_path.name


def compute_revision(
    file_path: Path, project_root: Path, update: bool = False
) -> dict[str, Any]:
    """计算文件 revision 信息。

    Args:
        file_path: 目标文件路径
        project_root: 项目根目录（用于定位 .revisions.json）
        update: 是否更新 .revisions.json

    Returns:
        结构化结果字典
    """
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    content_hash = compute_sha256(file_path)
    rel_key = get_relative_key(file_path, project_root)

    # .revisions.json 位于项目根目录
    revisions_path = project_root / ".revisions.json"
    revisions = load_revisions(revisions_path)

    existing = revisions.get(rel_key)
    changed = True
    revision: int = 1

    if existing is not None:
        old_hash = existing.get("content_hash", "")
        old_revision = existing.get("revision", 0)
        if old_hash == content_hash:
            # 内容未变化，不递增
            changed = False
            revision = old_revision
        else:
            # 内容变化，revision +1
            changed = True
            revision = old_revision + 1
    
    result: dict[str, Any] = {
        "path": rel_key,
        "revision": str(revision),
        "content_hash": content_hash,
        "changed": changed,
    }

    if update and changed:
        revisions[rel_key] = {
            "revision": revision,
            "content_hash": content_hash,
        }
        save_revisions(revisions_path, revisions)
        result["updated"] = True
    elif update and not changed:
        result["updated"] = False

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="计算文件 SHA-256 和 revision"
    )
    parser.add_argument(
        "--file", required=True, help="目标文件路径"
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="项目根目录（默认当前目录，用于定位 .revisions.json）",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="内容变化时更新 .revisions.json",
    )
    args = parser.parse_args()

    file_path = Path(args.file)
    project_root = Path(args.project_root)

    if not project_root.is_dir():
        print(f"ERROR: 项目根目录不存在: {project_root}", file=sys.stderr)
        return 2

    try:
        result = compute_revision(file_path, project_root, update=args.update)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: 读取/写入 .revisions.json 失败: {e}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
