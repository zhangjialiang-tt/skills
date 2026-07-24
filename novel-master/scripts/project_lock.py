#!/usr/bin/env python3
"""project_lock.py - 单项目写锁管理工具。

获取锁、释放锁、检测锁归属、检测超时或陈旧锁（超过 30 分钟视为陈旧）。
不自动删除仍可能有效的锁。提供 --force 但必须记录操作理由。
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

# 陈旧锁阈值：30 分钟
STALE_THRESHOLD_MINUTES = 30

LOCK_FILENAME = ".write.lock"


def get_lock_path(project_root: Path) -> Path:
    """获取锁文件路径。"""
    return project_root / "workflow" / LOCK_FILENAME


def load_lock(lock_path: Path) -> dict[str, Any] | None:
    """加载锁文件内容。不存在返回 None。"""
    if not lock_path.exists():
        return None
    with open(lock_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_lock(lock_path: Path, lock_data: dict[str, Any]) -> None:
    """写入锁文件。"""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w", encoding="utf-8") as f:
        yaml.dump(lock_data, f, default_flow_style=False, allow_unicode=True)


def remove_lock(lock_path: Path) -> None:
    """删除锁文件。"""
    if lock_path.exists():
        lock_path.unlink()


def is_stale(lock_data: dict[str, Any]) -> bool:
    """判断锁是否陈旧（超过 30 分钟）。"""
    created_at_str = lock_data.get("created_at", "")
    if not created_at_str:
        return True  # 无时间戳视为陈旧
    try:
        created_at = datetime.fromisoformat(created_at_str)
        # 如果没有时区信息，假设 UTC
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - created_at) > timedelta(minutes=STALE_THRESHOLD_MINUTES)
    except (ValueError, TypeError):
        return True  # 解析失败视为陈旧


def append_change_log(project_root: Path, message: str) -> None:
    """向 workflow/change_log.md 追加记录。"""
    log_path = project_root / "workflow" / "change_log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"\n- [{timestamp}] {message}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


def acquire_lock(
    project_root: Path,
    request_id: str,
    force: bool = False,
    reason: str = "",
) -> dict[str, Any]:
    """获取写锁。

    Returns:
        结果字典，包含 status 和详情
    """
    lock_path = get_lock_path(project_root)
    existing = load_lock(lock_path)

    if existing is not None:
        existing_request = existing.get("request_id", "")
        stale = is_stale(existing)

        # 同一 request_id 重复获取 → 幂等成功
        if existing_request == request_id:
            return {
                "status": "ACQUIRED",
                "request_id": request_id,
                "note": "锁已由此 request_id 持有（幂等）",
                "stale": stale,
            }

        # 不同 request_id 持有锁
        if not force:
            return {
                "status": "CONFLICT",
                "held_by": existing_request,
                "created_at": existing.get("created_at", ""),
                "stale": stale,
                "message": (
                    f"锁被 '{existing_request}' 持有。"
                    + ("（锁已陈旧）" if stale else "（锁仍有效）")
                    + " 使用 --force --reason 强制获取。"
                ),
            }

        # force 模式
        if not reason:
            return {
                "status": "ERROR",
                "message": "--force 需要提供 --reason 参数",
            }

        # 记录强制获取操作
        append_change_log(
            project_root,
            f"LOCK_FORCE_ACQUIRE: request_id='{request_id}' 强制获取锁，"
            f"原持有者='{existing_request}'，理由: {reason}",
        )

    # 创建新锁
    lock_data = {
        "request_id": request_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "process_id": str(os.getpid()),
    }
    save_lock(lock_path, lock_data)

    return {
        "status": "ACQUIRED",
        "request_id": request_id,
        "lock_file": str(lock_path),
    }


def release_lock(project_root: Path, request_id: str) -> dict[str, Any]:
    """释放写锁。"""
    lock_path = get_lock_path(project_root)
    existing = load_lock(lock_path)

    if existing is None:
        return {
            "status": "NO_LOCK",
            "message": "当前无锁文件",
        }

    existing_request = existing.get("request_id", "")
    if existing_request != request_id:
        return {
            "status": "DENIED",
            "held_by": existing_request,
            "message": f"锁由 '{existing_request}' 持有，'{request_id}' 无权释放",
        }

    remove_lock(lock_path)
    return {
        "status": "RELEASED",
        "request_id": request_id,
    }


def lock_status(project_root: Path) -> dict[str, Any]:
    """查询锁状态。"""
    lock_path = get_lock_path(project_root)
    existing = load_lock(lock_path)

    if existing is None:
        return {
            "status": "UNLOCKED",
            "lock_file": str(lock_path),
        }

    stale = is_stale(existing)
    return {
        "status": "LOCKED",
        "request_id": existing.get("request_id", ""),
        "created_at": existing.get("created_at", ""),
        "process_id": existing.get("process_id"),
        "stale": stale,
        "lock_file": str(lock_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="项目写锁管理"
    )
    parser.add_argument(
        "--project-root", required=True, help="项目根目录"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--acquire", action="store_true", help="获取锁"
    )
    group.add_argument(
        "--release", action="store_true", help="释放锁"
    )
    group.add_argument(
        "--status", action="store_true", help="查询锁状态"
    )

    parser.add_argument("--request-id", default="", help="请求 ID")
    parser.add_argument(
        "--force", action="store_true", help="强制获取锁"
    )
    parser.add_argument("--reason", default="", help="强制操作理由")
    args = parser.parse_args()

    project_root = Path(args.project_root)
    if not project_root.is_dir():
        print(f"ERROR: 项目根目录不存在: {project_root}", file=sys.stderr)
        return 2

    if args.acquire:
        if not args.request_id:
            print("ERROR: --acquire 需要 --request-id", file=sys.stderr)
            return 2
        if args.force and not args.reason:
            print("ERROR: --force 需要 --reason 说明操作理由", file=sys.stderr)
            return 2
        result = acquire_lock(
            project_root, args.request_id, force=args.force, reason=args.reason
        )
    elif args.release:
        if not args.request_id:
            print("ERROR: --release 需要 --request-id", file=sys.stderr)
            return 2
        result = release_lock(project_root, args.request_id)
    else:  # --status
        result = lock_status(project_root)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 退出码：ACQUIRED/RELEASED/UNLOCKED/LOCKED = 0, CONFLICT/DENIED/ERROR = 1
    status = result.get("status", "")
    if status in ("CONFLICT", "DENIED", "ERROR"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
