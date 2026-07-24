#!/usr/bin/env python3
"""commit_changeset.py - ChangeSet 事务执行工具（V1 最小安全版本）。

只允许修改 state/ 和 workflow/change_log.md。
先校验路径、锁、revision，创建备份，写临时文件，校验，原子替换。
多文件失败时尝试恢复全部备份。记录 ChangeSet 状态。
Canon 项不允许通过 DELETE 移除。

注意：V1 本地文件系统事务不是数据库级全局原子事务。
通过备份 + 临时文件 + 原子替换近似实现。
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from validate_approval import load_approval, validate_approval
from validate_contract import (
    can_commit_chapter_state,
    is_valid_revision,
    is_valid_sha256,
    next_revision,
)
from validate_paths import normalize_path

# 允许修改的路径前缀
ALLOWED_WRITE_PREFIXES = ["state/", "workflow/change_log.md"]

# 不允许 DELETE 的 Canon 路径
CANON_PREFIXES = ["state/"]

VALID_OPERATIONS = {"ADD", "MODIFY", "DELETE"}
APPROVAL_REQUIRED_OPERATIONS = {"COMMIT_CANON", "RETCON"}
CHANGESET_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent / "schemas" / "changeset.schema.json"
)


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def compute_sha256(file_path: Path) -> str:
    """计算文件 SHA-256。"""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def load_yaml_or_json(path: Path) -> dict[str, Any]:
    """加载 YAML 或 JSON 文件。"""
    with open(path, "r", encoding="utf-8") as f:
        suffix = path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            return yaml.safe_load(f) or {}
        else:
            return json.load(f)


def write_yaml_or_json(
    path: Path,
    data: dict[str, Any],
    format_suffix: str | None = None,
) -> None:
    """按目标扩展名写入 YAML 或 JSON。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        suffix = (format_suffix or path.suffix).lower()
        if suffix in (".yaml", ".yml"):
            yaml.safe_dump(
                data,
                f,
                allow_unicode=True,
                sort_keys=False,
            )
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")


def load_revisions(project_root: Path) -> dict[str, Any]:
    """加载 .revisions.json。"""
    rev_path = project_root / ".revisions.json"
    if not rev_path.exists():
        return {}
    with open(rev_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_revisions(project_root: Path, data: dict[str, Any]) -> None:
    """保存 .revisions.json。"""
    rev_path = project_root / ".revisions.json"
    with open(rev_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def is_allowed_path(relative_path: str) -> bool:
    """检查路径是否在允许修改的范围内。"""
    for prefix in ALLOWED_WRITE_PREFIXES:
        if prefix.endswith("/"):
            if relative_path.startswith(prefix):
                return True
        else:
            if relative_path == prefix:
                return True
    return False


def is_canon_path(relative_path: str) -> bool:
    """检查路径是否为 Canon 路径。"""
    for prefix in CANON_PREFIXES:
        if relative_path.startswith(prefix):
            return True
    return False


@lru_cache(maxsize=1)
def _changeset_validator() -> Draft202012Validator:
    """加载并缓存 ChangeSet Schema 校验器。"""
    with open(CHANGESET_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    return Draft202012Validator(schema)


def append_change_log(project_root: Path, message: str) -> None:
    """向 workflow/change_log.md 追加记录。"""
    log_path = project_root / "workflow" / "change_log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"\n- [{timestamp}] {message}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# 锁校验（复用 project_lock 逻辑）
# ---------------------------------------------------------------------------


def verify_lock(project_root: Path, request_id: str) -> tuple[bool, str]:
    """校验当前 request_id 是否持有锁。"""
    lock_path = project_root / "workflow" / ".write.lock"
    if not lock_path.exists():
        return False, "无锁文件，请先获取锁"
    with open(lock_path, "r", encoding="utf-8") as f:
        lock_data = yaml.safe_load(f) or {}
    held_by = lock_data.get("request_id", "")
    if held_by != request_id:
        return False, f"锁由 '{held_by}' 持有，当前 request_id='{request_id}' 无权操作"
    return True, ""


# ---------------------------------------------------------------------------
# ChangeSet 校验
# ---------------------------------------------------------------------------


def validate_changeset(
    changeset: dict[str, Any], project_root: Path, request_id: str
) -> list[str]:
    """校验 ChangeSet 合法性，返回错误列表。"""
    errors: list[str] = []

    # Schema 是所有后续语义校验的字段类型前提。
    for error in sorted(
        _changeset_validator().iter_errors(changeset),
        key=lambda item: list(item.absolute_path),
    ):
        path = ".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"Schema {path}: {error.message}")
    if errors:
        return errors

    # 基本字段检查
    cs_request_id = changeset.get("request_id", "")
    if cs_request_id != request_id:
        errors.append(
            f"ChangeSet request_id='{cs_request_id}' 与命令行 request_id='{request_id}' 不匹配"
        )

    if changeset.get("status") not in ("PREPARED", "VALIDATED"):
        errors.append(
            "ChangeSet 只有 PREPARED 或 VALIDATED 状态可以提交"
        )

    # 检查 target_updates
    target_updates = changeset.get("target_updates", [])
    if not target_updates:
        errors.append("target_updates 为空")
        return errors

    seen_targets: set[str] = set()
    current_revisions = load_revisions(project_root)
    base_revision = changeset.get("base_revision", {})

    for i, update in enumerate(target_updates):
        target_file = update.get("target_file", "")
        operation = update.get("operation", "")
        resolved_target, path_error = normalize_path(
            project_root,
            target_file,
        )
        if path_error or resolved_target is None:
            errors.append(
                f"target_updates[{i}]: 路径不安全: {path_error}"
            )
            continue
        target_path = resolved_target

        if target_file in seen_targets:
            errors.append(
                f"target_updates[{i}]: 同一 ChangeSet 不得重复更新 '{target_file}'"
            )
        seen_targets.add(target_file)

        if operation not in VALID_OPERATIONS:
            errors.append(
                f"target_updates[{i}]: 未知操作 '{operation}'"
            )

        # 路径允许性
        if not is_allowed_path(target_file):
            errors.append(
                f"target_updates[{i}]: 路径 '{target_file}' 不在允许修改范围内"
                f"（仅允许 state/ 和 workflow/change_log.md）"
            )

        # Canon DELETE 禁止
        if operation == "DELETE" and is_canon_path(target_file):
            errors.append(
                f"target_updates[{i}]: Canon 项 '{target_file}' 不允许 DELETE"
                "（只能 DEPRECATED）"
            )

        # ADD/MODIFY 必须有非空 content
        if operation in ("ADD", "MODIFY") and not update.get("content"):
            errors.append(
                f"target_updates[{i}]: 操作 '{operation}' 缺少非空 content"
            )

        if operation in ("MODIFY", "DELETE") and not target_path.exists():
            errors.append(
                f"target_updates[{i}]: 操作 '{operation}' 的目标不存在: '{target_file}'"
            )
        elif operation == "MODIFY":
            try:
                if target_path.read_text(encoding="utf-8") == update.get(
                    "content", ""
                ):
                    errors.append(
                        f"target_updates[{i}]: '{target_file}' 内容未变化"
                    )
            except OSError as error:
                errors.append(
                    f"target_updates[{i}]: 无法读取 '{target_file}': {error}"
                )

        if (
            target_file.startswith("state/")
            and target_path.exists()
            and target_file not in base_revision
        ):
            errors.append(
                f"base_revision 未覆盖已存在的目标文件 '{target_file}'"
            )

    # 校验 base_revision，并用 content_hash 检测 revision 清单与磁盘内容漂移。
    for file_key, expected_rev in base_revision.items():
        resolved_file, path_error = normalize_path(project_root, file_key)
        if path_error or resolved_file is None:
            errors.append(f"base_revision 路径不安全 '{file_key}': {path_error}")
            continue
        if not file_key.startswith("state/"):
            errors.append(
                f"base_revision 只允许引用 state/ 文件: '{file_key}'"
            )
            continue
        entry = current_revisions.get(file_key, {})
        current_rev = entry.get("revision")
        target_path = resolved_file
        if current_rev is None:
            if target_path.exists():
                errors.append(
                    f"base_revision: 文件 '{file_key}' 存在但无 revision 记录"
                )
            continue
        if str(current_rev) != str(expected_rev):
            errors.append(
                f"STALE_CONTEXT: 文件 '{file_key}' "
                f"base_revision='{expected_rev}'，当前 revision='{current_rev}'"
            )
        expected_hash = entry.get("content_hash")
        if target_path.exists() and expected_hash:
            current_hash = compute_sha256(target_path)
            if current_hash != expected_hash:
                errors.append(
                    f"STALE_CONTEXT: 文件 '{file_key}' content_hash 与 revision 清单不一致"
                )

    return errors


def validate_source_deliverable(
    changeset: dict[str, Any],
    source_deliverable: dict[str, Any] | None,
    accepted_record: dict[str, Any] | None = None,
) -> list[str]:
    """校验 COMMIT_CHAPTER_STATE 的来源交付物。"""
    if source_deliverable is None:
        return ["COMMIT_CHAPTER_STATE 必须提供 source_deliverable"]

    errors: list[str] = []
    deliverable_id = source_deliverable.get("deliverable_id", "")
    revision = source_deliverable.get("revision", "")
    content_hash = source_deliverable.get("content_hash", "")
    lifecycle = source_deliverable.get("chapter_lifecycle_status")

    if not deliverable_id:
        errors.append("source_deliverable.deliverable_id 不能为空")
    if not revision:
        errors.append("source_deliverable.revision 不能为空")
    elif not is_valid_revision(str(revision)):
        errors.append("source_deliverable.revision 格式无效")
    if not is_valid_sha256(str(content_hash)):
        errors.append("source_deliverable.content_hash 必须是 64 位小写 SHA-256")
    if not can_commit_chapter_state(str(lifecycle)):
        errors.append(
            "COMMIT_CHAPTER_STATE 来源章节必须是 ACCEPTED 或 PUBLISHED"
        )
    elif accepted_record is None:
        errors.append("COMMIT_CHAPTER_STATE 必须提供接受记录")
    else:
        if accepted_record.get("accepted_by") not in (
            "user",
            "approved_workflow",
        ):
            errors.append(
                "接受记录 accepted_by 必须是 user 或 approved_workflow"
            )
        if not accepted_record.get("acceptance_ref"):
            errors.append("接受记录 acceptance_ref 不能为空")

        for field in (
            "deliverable_id",
            "revision",
            "content_hash",
            "chapter_lifecycle_status",
        ):
            if source_deliverable.get(field) != accepted_record.get(field):
                errors.append(f"{field} 与接受记录不一致")

    expected_source_ref = f"{deliverable_id}@{revision}"
    if changeset.get("source_ref") != expected_source_ref:
        errors.append(
            "ChangeSet source_ref 与 source_deliverable 不一致: "
            f"期望 '{expected_source_ref}'"
        )
    return errors


# ---------------------------------------------------------------------------
# 事务执行
# ---------------------------------------------------------------------------


def execute_changeset(
    changeset: dict[str, Any],
    project_root: Path,
    approval: dict[str, Any] | None = None,
    approval_path: Path | None = None,
) -> dict[str, Any]:
    """执行 ChangeSet 事务。

    流程：备份 → 写临时文件 → 校验 → 原子替换 → 更新 revision → 记录日志。
    失败时从备份恢复。
    """
    change_set_id = changeset.get("change_set_id", "unknown")
    preflight_errors = validate_changeset(
        changeset,
        project_root,
        str(changeset.get("request_id", "")),
    )
    if preflight_errors:
        return {
            "status": "VALIDATION_FAILED",
            "change_set_id": change_set_id,
            "errors": preflight_errors,
        }

    target_updates = changeset.get("target_updates", [])
    backup_dir = project_root / "workflow" / "backups" / change_set_id
    backup_dir.mkdir(parents=True, exist_ok=True)

    replaced_files: list[tuple[Path, Path]] = []  # (target, backup)
    created_files: list[Path] = []
    tmp_files: list[Path] = []
    expected_tmp_hashes: dict[Path, str] = {}
    errors: list[str] = []
    revisions_path = project_root / ".revisions.json"
    change_log_path = project_root / "workflow" / "change_log.md"
    transaction_backup_dir = backup_dir / "__transaction__"
    revisions_backup = transaction_backup_dir / ".revisions.json"
    change_log_backup = transaction_backup_dir / "change_log.md"
    approval_backup = transaction_backup_dir / "approval-ref"
    revisions_existed = revisions_path.exists()
    change_log_existed = change_log_path.exists()
    consume_approval = bool(
        approval
        and approval.get("expires_after_use")
        and approval_path is not None
    )
    approval_tmp: Path | None = None

    try:
        # Phase 1: 备份目标文件和事务元数据
        transaction_backup_dir.mkdir(parents=True, exist_ok=True)
        if revisions_existed:
            shutil.copy2(revisions_path, revisions_backup)
        if change_log_existed:
            shutil.copy2(change_log_path, change_log_backup)
        if consume_approval:
            assert approval_path is not None
            if not approval_path.exists():
                raise FileNotFoundError(
                    f"一次性 ApprovalRef 文件不存在: {approval_path}"
                )
            shutil.copy2(approval_path, approval_backup)

        for update in target_updates:
            target_file = update.get("target_file", "")
            operation = update.get("operation", "")
            target_path = project_root / target_file

            if operation in ("ADD", "MODIFY", "DELETE") and target_path.exists():
                backup_path = backup_dir / target_file
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target_path, backup_path)
                replaced_files.append((target_path, backup_path))
            elif operation == "ADD":
                created_files.append(target_path)

        # Phase 2: 写临时文件
        for update in target_updates:
            target_file = update.get("target_file", "")
            operation = update.get("operation", "")
            content = update.get("content", "")
            target_path = project_root / target_file

            if operation in ("ADD", "MODIFY"):
                if operation == "ADD" and target_path.exists():
                    existing = target_path.read_text(encoding="utf-8")
                    if existing and not existing.endswith("\n"):
                        existing += "\n"
                    if existing and content and not content.startswith("\n"):
                        existing += "\n"
                    content = existing + content
                tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
                tmp_path.parent.mkdir(parents=True, exist_ok=True)
                with open(
                    tmp_path,
                    "w",
                    encoding="utf-8",
                    newline="",
                ) as f:
                    f.write(content)
                tmp_files.append(tmp_path)
                expected_tmp_hashes[tmp_path] = hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest()

        if consume_approval:
            assert approval is not None
            assert approval_path is not None
            consumed_approval = dict(approval)
            consumed_approval["status"] = "USED"
            approval_tmp = approval_path.with_suffix(
                approval_path.suffix + ".tmp"
            )
            write_yaml_or_json(
                approval_tmp,
                consumed_approval,
                format_suffix=approval_path.suffix,
            )
            tmp_files.append(approval_tmp)

        # Phase 3: 校验临时文件
        for tmp_path in tmp_files:
            if not tmp_path.exists():
                errors.append(f"临时文件不存在: {tmp_path}")
                continue
            expected_hash = expected_tmp_hashes.get(tmp_path)
            if expected_hash and compute_sha256(tmp_path) != expected_hash:
                errors.append(f"临时文件内容校验失败: {tmp_path}")

        if approval_tmp is not None:
            consumed = load_approval(approval_tmp)
            if consumed.get("status") != "USED":
                errors.append("一次性 ApprovalRef 临时状态不是 USED")

        if errors:
            raise RuntimeError(f"临时文件校验失败: {errors}")

        # Phase 4: 原子替换（os.replace）
        for update in target_updates:
            target_file = update.get("target_file", "")
            operation = update.get("operation", "")
            target_path = project_root / target_file

            if operation in ("ADD", "MODIFY"):
                tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
                target_path.parent.mkdir(parents=True, exist_ok=True)
                os.replace(tmp_path, target_path)
            elif operation == "DELETE":
                # 非 Canon 文件的 DELETE（Canon DELETE 已在校验阶段拦截）
                if target_path.exists():
                    target_path.unlink()

        if approval_tmp is not None and approval_path is not None:
            os.replace(approval_tmp, approval_path)

        # Phase 5: 更新 revision
        revisions = load_revisions(project_root)
        for update in target_updates:
            target_file = update.get("target_file", "")
            operation = update.get("operation", "")
            target_path = project_root / target_file

            if operation in ("ADD", "MODIFY") and target_path.exists():
                new_hash = compute_sha256(target_path)
                old_entry = revisions.get(target_file, {})
                old_rev = old_entry.get("revision", 0)
                revisions[target_file] = {
                    "revision": next_revision(old_rev),
                    "content_hash": new_hash,
                }
            elif operation == "DELETE":
                revisions.pop(target_file, None)

        save_revisions(project_root, revisions)

        # Phase 6: 记录 change_log
        append_change_log(
            project_root,
            f"CHANGESET_COMMITTED: id='{change_set_id}', "
            f"files={[u.get('target_file') for u in target_updates]}",
        )

        # 清理临时文件（正常情况下已在 replace 中消耗）
        for tmp_path in tmp_files:
            if tmp_path.exists():
                tmp_path.unlink()

        if consume_approval and approval is not None:
            approval["status"] = "USED"

        return {
            "status": "COMMITTED",
            "change_set_id": change_set_id,
            "files_modified": [u.get("target_file") for u in target_updates],
            "backup_dir": str(backup_dir),
        }

    except Exception as e:
        # 回滚：恢复正式文件、revision 清单和 change_log。
        errors.append(str(e))
        rollback_errors: list[str] = []

        for target_path in created_files:
            try:
                if target_path.exists():
                    target_path.unlink()
            except OSError as re:
                rollback_errors.append(f"删除新增文件失败 {target_path}: {re}")

        for target_path, backup_path in replaced_files:
            try:
                if backup_path.exists():
                    shutil.copy2(backup_path, target_path)
            except OSError as re:
                rollback_errors.append(f"恢复失败 {target_path}: {re}")

        try:
            if revisions_existed and revisions_backup.exists():
                shutil.copy2(revisions_backup, revisions_path)
            elif not revisions_existed and revisions_path.exists():
                revisions_path.unlink()
        except OSError as re:
            rollback_errors.append(f"恢复 revision 清单失败: {re}")

        try:
            if change_log_existed and change_log_backup.exists():
                shutil.copy2(change_log_backup, change_log_path)
            elif not change_log_existed and change_log_path.exists():
                change_log_path.unlink()
        except OSError as re:
            rollback_errors.append(f"恢复 change_log 失败: {re}")

        if consume_approval and approval_path is not None:
            try:
                if approval_backup.exists():
                    shutil.copy2(approval_backup, approval_path)
            except OSError as re:
                rollback_errors.append(f"恢复 ApprovalRef 失败: {re}")

        # 清理临时文件
        for tmp_path in tmp_files:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                pass

        status = "ROLLBACK_FAILED" if rollback_errors else "ROLLED_BACK"
        try:
            append_change_log(
                project_root,
                f"CHANGESET_{status}: id='{change_set_id}', errors={errors}",
            )
        except OSError as re:
            rollback_errors.append(f"记录回滚日志失败: {re}")
            status = "ROLLBACK_FAILED"

        if rollback_errors:
            # 记录诊断信息
            diag_dir = project_root / "workflow" / "runs"
            diag_dir.mkdir(parents=True, exist_ok=True)
            diag_path = diag_dir / "diagnostics.log"
            with open(diag_path, "a", encoding="utf-8") as f:
                f.write(
                    f"\n[{datetime.now(timezone.utc).isoformat()}] "
                    f"ROLLBACK_FAILED for {change_set_id}:\n"
                )
                for err in errors + rollback_errors:
                    f.write(f"  {err}\n")

        return {
            "status": status,
            "change_set_id": change_set_id,
            "errors": errors,
            "rollback_errors": rollback_errors,
        }


# ---------------------------------------------------------------------------
# 统一提交入口
# ---------------------------------------------------------------------------


def commit_changeset(
    changeset: dict[str, Any],
    project_root: Path,
    request_id: str,
    operation: str = "COMMIT_CHAPTER_STATE",
    approval: dict[str, Any] | None = None,
    approval_current_revision: str | None = None,
    approval_target_items: list[str] | None = None,
    approval_path: Path | None = None,
    source_deliverable: dict[str, Any] | None = None,
    accepted_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """执行不可绕过的提交前校验，并在全部校验通过后提交。"""
    errors = validate_changeset(changeset, project_root, request_id)

    target_files = [
        update.get("target_file", "")
        for update in changeset.get("target_updates", [])
    ]
    if operation == "COMMIT_CHAPTER_STATE":
        errors.extend(
            validate_source_deliverable(
                changeset,
                source_deliverable,
                accepted_record=accepted_record,
            )
        )

    if operation in APPROVAL_REQUIRED_OPERATIONS and approval is None:
        errors.append(f"{operation} 必须提供 ApprovalRef")

    if approval is not None:
        if approval_current_revision is None:
            errors.append("ApprovalRef 校验缺少来源交付物的当前 revision")
        else:
            if approval_path is not None:
                try:
                    relative_approval_path = (
                        approval_path.resolve()
                        .relative_to(project_root.resolve())
                        .as_posix()
                    )
                    if not relative_approval_path.startswith(
                        "workflow/approvals/"
                    ):
                        errors.append(
                            "ApprovalRef 文件必须位于 workflow/approvals/"
                        )
                    persisted_approval = load_approval(approval_path)
                    if persisted_approval != approval:
                        errors.append(
                            "传入 ApprovalRef 与磁盘文件内容不一致"
                        )
                except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as error:
                    errors.append(f"加载 ApprovalRef 文件失败: {error}")
            elif approval.get("expires_after_use"):
                errors.append(
                    "一次性 ApprovalRef 必须提供 workflow/approvals/ 下的文件路径"
                )

            approval_errors = validate_approval(
                approval,
                operation=operation,
                target_files=target_files,
                current_revision=approval_current_revision,
                request_id=request_id,
                target_items=approval_target_items,
            )
            errors.extend(
                f"INVALID_APPROVAL: {error}" for error in approval_errors
            )

    if errors:
        return {
            "status": "VALIDATION_FAILED",
            "change_set_id": changeset.get("change_set_id", "unknown"),
            "errors": errors,
        }

    try:
        lock_ok, lock_err = verify_lock(project_root, request_id)
    except (OSError, yaml.YAMLError, AttributeError) as error:
        lock_ok = False
        lock_err = f"读取锁失败: {error}"
    if not lock_ok:
        return {
            "status": "LOCK_FAILED",
            "change_set_id": changeset.get("change_set_id", "unknown"),
            "errors": [lock_err],
        }

    return execute_changeset(
        changeset,
        project_root,
        approval=approval,
        approval_path=approval_path,
    )


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="执行 ChangeSet 事务（V1 最小安全版本）"
    )
    parser.add_argument(
        "--project-root", required=True, help="项目根目录"
    )
    parser.add_argument(
        "--changeset", required=True, help="ChangeSet YAML/JSON 文件路径"
    )
    parser.add_argument(
        "--request-id", required=True, help="请求 ID（必须与锁和 ChangeSet 一致）"
    )
    parser.add_argument(
        "--operation",
        default="COMMIT_CHAPTER_STATE",
        help="本次提交操作（如 COMMIT_CHAPTER_STATE、COMMIT_CANON、RETCON）",
    )
    parser.add_argument(
        "--approval",
        default=None,
        help="ApprovalRef 文件；一次性授权必须位于项目 workflow/approvals/ 下",
    )
    parser.add_argument(
        "--approval-current-revision",
        default=None,
        help="用户批准的来源交付物的当前 revision",
    )
    parser.add_argument(
        "--approval-target-items",
        nargs="*",
        default=None,
        help="需要 ApprovalRef 覆盖的条目标识",
    )
    parser.add_argument(
        "--source-deliverable",
        default=None,
        help="COMMIT_CHAPTER_STATE 的来源交付物 YAML/JSON 文件",
    )
    parser.add_argument(
        "--accepted-record",
        default=None,
        help="COMMIT_CHAPTER_STATE 的接受记录 YAML/JSON 文件",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root)
    changeset_path = Path(args.changeset)

    if not project_root.is_dir():
        print(f"ERROR: 项目根目录不存在: {project_root}", file=sys.stderr)
        return 2

    if not changeset_path.exists():
        print(f"ERROR: ChangeSet 文件不存在: {changeset_path}", file=sys.stderr)
        return 2

    # 加载 ChangeSet
    try:
        changeset = load_yaml_or_json(changeset_path)
    except (yaml.YAMLError, json.JSONDecodeError, OSError) as e:
        print(f"ERROR: 加载 ChangeSet 失败: {e}", file=sys.stderr)
        return 2

    approval = None
    approval_path = None
    if args.approval:
        approval_path = Path(args.approval)
        if not approval_path.is_absolute():
            approval_path = project_root / approval_path
        try:
            approval = load_approval(approval_path)
        except (
            FileNotFoundError,
            ValueError,
            yaml.YAMLError,
            json.JSONDecodeError,
            OSError,
        ) as error:
            print(f"ERROR: 加载 ApprovalRef 失败: {error}", file=sys.stderr)
            return 2

    source_deliverable = None
    if args.source_deliverable:
        source_path = Path(args.source_deliverable)
        if not source_path.is_absolute():
            source_path = project_root / source_path
        try:
            source_deliverable = load_yaml_or_json(source_path)
        except (yaml.YAMLError, json.JSONDecodeError, OSError) as error:
            print(
                f"ERROR: 加载 source_deliverable 失败: {error}",
                file=sys.stderr,
            )
            return 2

    accepted_record = None
    if args.accepted_record:
        accepted_path = Path(args.accepted_record)
        if not accepted_path.is_absolute():
            accepted_path = project_root / accepted_path
        try:
            accepted_record = load_yaml_or_json(accepted_path)
        except (yaml.YAMLError, json.JSONDecodeError, OSError) as error:
            print(
                f"ERROR: 加载 accepted_record 失败: {error}",
                file=sys.stderr,
            )
            return 2

    result = commit_changeset(
        changeset,
        project_root,
        request_id=args.request_id,
        operation=args.operation,
        approval=approval,
        approval_current_revision=args.approval_current_revision,
        approval_target_items=args.approval_target_items,
        approval_path=approval_path,
        source_deliverable=source_deliverable,
        accepted_record=accepted_record,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

    status = result.get("status", "")
    if status == "COMMITTED":
        return 0
    elif status in (
        "VALIDATION_FAILED",
        "LOCK_FAILED",
        "ROLLED_BACK",
        "ROLLBACK_FAILED",
    ):
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())
