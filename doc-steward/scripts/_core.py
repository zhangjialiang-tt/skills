"""Shared helpers for doc-steward deterministic scripts.

Implements the file/path rules from `references/registry-schema.md` and the
invariants from `docs/spec-frozen.md`. No CLI here — see the individual
script modules for command-line entry points.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Protocol

import yaml

# ---------------------------------------------------------------------------
# Constants (mirror docs/spec-frozen.md §1 / references/registry-schema.md)
# ---------------------------------------------------------------------------

REGISTRY_FILENAME = "registry.yaml"
SNAPSHOTS_DIRNAME = ".doc-steward/snapshots"
SCHEMA_VERSION = "1.0"

STATUSES = ("DRAFT", "REVIEWING", "ACTIVE", "FROZEN", "SUPERSEDED", "ARCHIVED")
DOC_TYPES = ("design", "prd", "plan", "spec", "adr", "note", "other")

# spec §1.3 Transition Matrix — allowed migrations (from_status -> set of to_status)
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"REVIEWING", "SUPERSEDED", "ARCHIVED"},
    "REVIEWING": {"ACTIVE", "SUPERSEDED", "ARCHIVED"},
    "ACTIVE": {"FROZEN", "SUPERSEDED", "ARCHIVED"},
    "FROZEN": {"ACTIVE", "ARCHIVED"},  # unfreeze → ACTIVE (Tier2)
    "SUPERSEDED": {"ARCHIVED", "SUPERSEDED"},  # restore listed separately
    "ARCHIVED": {"SUPERSEDED"},  # restore only to SUPERSEDED (never DRAFT)
}

# Tier2 transitions requiring explicit user approval (spec §1.3 / §2.3)
TIER2_TRANSITIONS = {
    ("ACTIVE", "FROZEN"),
    ("FROZEN", "ACTIVE"),  # unfreeze
    ("ACTIVE", "SUPERSEDED"),
    ("REVIEWING", "SUPERSEDED"),
    ("DRAFT", "SUPERSEDED"),
    ("ARCHIVED", "SUPERSEDED"),  # restore
}

DOC_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]+$")
SUPERSEDED_BY_PATTERN = re.compile(r"^.+@r\d+$")


# ---------------------------------------------------------------------------
# YAML helpers — preserve dates as YYYY-MM-DD strings
# ---------------------------------------------------------------------------


class _DateYamlMixin:
    """Representer / constructor so `date` objects round-trip as ISO strings."""

    @classmethod
    def _represent_date(cls, dumper: yaml.Dumper, data: date) -> yaml.Node:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data.isoformat())

    @classmethod
    def _construct_date(cls, loader: yaml.Loader, node: yaml.Node) -> date:
        return date.fromisoformat(loader.construct_scalar(node))


yaml.add_representer(date, _DateYamlMixin._represent_date)
yaml.add_constructor(
    "tag:yaml.org,2002:timestamp",
    _DateYamlMixin._construct_date,
    Loader=yaml.SafeLoader,
)


def load_registry(path: Path) -> dict[str, Any]:
    """Load a registry YAML file. Returns the parsed dict."""
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def save_registry(path: Path, registry: dict[str, Any]) -> None:
    """Atomically write a registry YAML file (write-then-rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".yaml.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        yaml.dump(
            registry,
            fh,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        )
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Path / hashing helpers
# ---------------------------------------------------------------------------


def find_project_root(start: Path | None = None) -> Path:
    """Walk up from *start* (or cwd) to the nearest parent containing
    `.doc-steward/registry.yaml`, else return the starting directory."""
    cur = (start or Path.cwd()).resolve()
    for parent in [cur, *cur.parents]:
        if (parent / ".doc-steward" / REGISTRY_FILENAME).exists():
            return parent
    return cur


def registry_path(project_root: Path | None = None) -> Path:
    root = project_root or find_project_root()
    return root / ".doc-steward" / REGISTRY_FILENAME


def snapshots_dir(project_root: Path | None = None) -> Path:
    root = project_root or find_project_root()
    return root / SNAPSHOTS_DIRNAME


def hash_file(path: Path) -> str:
    """SHA-256 of file content (spec §1.5 / registry-schema `content_hash`)."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_excluded(rel_path: str, exclude_patterns: list[str]) -> bool:
    """Return True if *rel_path* matches any exclude pattern (glob, fnmatch-style)."""
    from fnmatch import fnmatch

    return any(fnmatch(rel_path, pat) for pat in exclude_patterns)


def doc_id_from_path(rel_path: str) -> str:
    """Derive a stable `doc_id` (uppercase, hyphens) from a relative path.

    `docs/system-design.md` → `DOC-SYSTEM-DESIGN`
    `docs/API_Spec.md`      → `DOC-API-SPEC`
    """
    stem = Path(rel_path).stem
    # Replace spaces/underscores with hyphens, strip non-alphanumeric (keep hyphens)
    cleaned = re.sub(r"[\s_]+", "-", stem)
    cleaned = re.sub(r"[^A-Za-z0-9-]", "", cleaned)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-").upper()
    return f"DOC-{cleaned}" if not cleaned.startswith("DOC-") else cleaned


# ---------------------------------------------------------------------------
# Registry access helpers
# ---------------------------------------------------------------------------


def find_doc(registry: dict[str, Any], doc_id: str) -> dict[str, Any] | None:
    for doc in registry.get("documents", []):
        if doc.get("doc_id") == doc_id:
            return doc
    return None


def find_doc_index(registry: dict[str, Any], doc_id: str) -> int:
    for i, doc in enumerate(registry.get("documents", [])):
        if doc.get("doc_id") == doc_id:
            return i
    return -1


def get_config(registry: dict[str, Any]) -> dict[str, Any]:
    return registry.get("config", {})


# ---------------------------------------------------------------------------
# Transition validation
# ---------------------------------------------------------------------------


def transition_is_allowed(from_status: str, to_status: str) -> bool:
    return to_status in ALLOWED_TRANSITIONS.get(from_status, set())


def transition_is_tier2(from_status: str, to_status: str) -> bool:
    return (from_status, to_status) in TIER2_TRANSITIONS


def assert_valid_transition(from_status: str, to_status: str) -> None:
    """Raise `ValueError` if the migration violates spec §1.3."""
    if from_status == to_status:
        return  # no-op is always "allowed"
    if not transition_is_allowed(from_status, to_status):
        raise ValueError(
            f"illegal transition {from_status} → {to_status} (spec §1.3)"
        )


# ---------------------------------------------------------------------------
# Data model helpers
# ---------------------------------------------------------------------------


@dataclass
class DomainConflict:
    domain: str
    contenders: list[str]  # doc_id@revision strings


def detect_conflicts(registry: dict[str, Any]) -> list[DomainConflict]:
    """Find domains with ≥2 ACTIVE/FROZEN `source_of_truth` docs (spec §2.2)."""
    from collections import defaultdict

    contenders: dict[str, list[str]] = defaultdict(list)
    for doc in registry.get("documents", []):
        status = doc.get("status")
        if status not in ("ACTIVE", "FROZEN"):
            continue
        if not doc.get("source_of_truth"):
            continue
        key = f"{doc.get('doc_id')}@r{doc.get('revision', 1)}"
        for domain in doc.get("assigned_domain", []) or []:
            contenders[domain].append(key)
    return [
        DomainConflict(domain=domain, contenders=keys)
        for domain, keys in contenders.items()
        if len(keys) >= 2
    ]


@dataclass
class ValidationResult:
    conflicts: list[DomainConflict] = field(default_factory=list)
    drifts: list[str] = field(default_factory=list)
    stale_dependencies: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def validate_registry_against_schema(registry: dict[str, Any]) -> list[str]:
    """Validate registry structure against spec invariants.
    
    Returns list of error strings. Empty list means valid.
    """
    errors: list[str] = []
    
    # Check top-level required fields
    for field in ("version", "config", "documents"):
        if field not in registry:
            errors.append(f"missing required top-level field: {field}")
    
    if "documents" not in registry:
        return errors
    
    doc_ids: set[str] = set()
    paths: set[str] = set()
    
    for i, doc in enumerate(registry.get("documents", [])):
        prefix = f"documents[{i}]"
        
        # Required fields
        for field in ("doc_id", "path", "status", "revision", "content_hash", "updated_at", "decision"):
            if field not in doc:
                errors.append(f"{prefix}: missing required field: {field}")
        
        doc_id = doc.get("doc_id")
        path = doc.get("path")
        status = doc.get("status")
        
        # I1: unique doc_id
        if doc_id in doc_ids:
            errors.append(f"{prefix}: duplicate doc_id: {doc_id}")
        doc_ids.add(doc_id)
        
        # Unique path
        if path in paths:
            errors.append(f"{prefix}: duplicate path: {path}")
        paths.add(path)
        
        # doc_id format
        if doc_id and not DOC_ID_PATTERN.match(str(doc_id)):
            errors.append(f"{prefix}: invalid doc_id format: {doc_id}")
        
        # status enum
        if status and status not in STATUSES:
            errors.append(f"{prefix}: invalid status: {status}")
        
        # I3: SUPERSEDED requires superseded_by
        if status == "SUPERSEDED":
            sb = doc.get("superseded_by")
            if not sb:
                errors.append(f"{prefix}: SUPERSEDED without superseded_by")
            elif not SUPERSEDED_BY_PATTERN.match(str(sb)):
                errors.append(f"{prefix}: invalid superseded_by format: {sb}")
        
        # I4: ARCHIVED requires archive triple
        if status == "ARCHIVED":
            arch = doc.get("archive")
            if not arch:
                errors.append(f"{prefix}: ARCHIVED without archive block")
            else:
                for key in ("reason", "archived_at", "last_status"):
                    if not arch.get(key):
                        errors.append(f"{prefix}: ARCHIVED archive missing {key}")
        
        # revision >= 1
        rev = doc.get("revision")
        if rev is not None and (not isinstance(rev, int) or rev < 1):
            errors.append(f"{prefix}: revision must be integer >= 1")
        
        # content_hash format
        ch = doc.get("content_hash")
        if ch and not re.match(r"^[0-9a-f]{64}$", str(ch)):
            errors.append(f"{prefix}: invalid content_hash format")
    
    return errors


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------


def safe_resolve_path(project_root: Path, relative_path: str) -> Path:
    """Safely resolve a relative path within project_root.
    
    Raises ValueError if path escapes project_root or is absolute.
    """
    if Path(relative_path).is_absolute():
        raise ValueError(f"absolute path not allowed: {relative_path}")
    
    candidate = (project_root / relative_path).resolve()
    root_resolved = project_root.resolve()
    
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        raise ValueError(
            f"path escapes project root: {relative_path} -> {candidate}"
        )
    
    return candidate


# ---------------------------------------------------------------------------
# Change set
# ---------------------------------------------------------------------------


@dataclass
class ChangeSetEntry:
    """Single operation in a change set."""
    operation: str          # e.g. "register", "promote", "accept_revision"
    doc_id: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeSet:
    """Proposed set of changes to registry."""
    entries: list[ChangeSetEntry] = field(default_factory=list)
    expected_registry_hash: str = ""
    
    def add(self, operation: str, doc_id: str, **details: Any) -> None:
        self.entries.append(ChangeSetEntry(
            operation=operation, doc_id=doc_id, details=details
        ))
    
    def is_empty(self) -> bool:
        return len(self.entries) == 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_registry_hash": self.expected_registry_hash,
            "operations": [
                {
                    "type": e.operation,
                    "doc_id": e.doc_id,
                    **e.details,
                }
                for e in self.entries
            ],
        }


# ---------------------------------------------------------------------------
# Revision event
# ---------------------------------------------------------------------------


@dataclass
class RevisionEvent:
    """Append-only revision history entry."""
    event_id: str           # e.g. "EVT-20260729-001"
    event_type: str         # REGISTERED, REVISION_ACCEPTED, STATUS_CHANGED
    doc_id: str
    revision: int
    content_hash: str
    at: str                 # ISO date
    actor: str              # "user"
    reason: str
    from_revision: int | None = None
    from_status: str | None = None
    to_status: str | None = None


def generate_event_id() -> str:
    """Generate a simple event ID based on timestamp."""
    from datetime import datetime
    return f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
# ---------------------------------------------------------------------------
# Content drift detection
# ---------------------------------------------------------------------------


def detect_content_drift(registry: dict[str, Any], project_root: Path) -> dict[str, dict]:
    """Detect content drift for all documents.
    
    Returns a dict of doc_id -> {path, registered_hash, live_hash, content_drift, missing}.
    """
    from scan_docs import hash_file
    
    config = get_config(registry)
    exclude = config.get("exclude", [])
    
    results: dict[str, dict] = {}
    
    for doc in registry.get("documents", []):
        doc_id = doc.get("doc_id")
        rel_path = doc.get("path", "")
        registered_hash = doc.get("content_hash", "")
        
        # Skip excluded paths
        if is_excluded(rel_path, exclude):
            continue
        
        file_path = project_root / rel_path
        
        if not file_path.exists():
            results[doc_id] = {
                "path": rel_path,
                "registered_hash": registered_hash,
                "live_hash": None,
                "content_drift": False,
                "missing": True,
            }
        else:
            live_hash = hash_file(file_path)
            results[doc_id] = {
                "path": rel_path,
                "registered_hash": registered_hash,
                "live_hash": live_hash,
                "content_drift": live_hash != registered_hash,
                "missing": False,
            }
    
    return results


def compute_needs_attention(doc: dict[str, Any], drift_info: dict | None) -> tuple[bool, str]:
    """Compute whether a document needs attention and its priority.
    
    Returns (needs_attention, priority) where priority is "must_read" | "change_only" | "no_need".
    """
    status = doc.get("status")
    attention = doc.get("attention", {})
    
    # Blocking conditions
    if status == "REVIEWING":
        return True, "must_read"
    
    if attention.get("level") == "high":
        return True, "must_read"
    
    # Content drift from observations
    if drift_info and drift_info.get("missing"):
        return True, "must_read"
    
    if drift_info and drift_info.get("content_drift"):
        # FROZEN drift is blocking
        if status == "FROZEN":
            return True, "must_read"
        return True, "change_only"
    
    # Stale dependency
    if doc.get("stale_dependency"):
        return True, "must_read"
    
    return False, "no_need"


# ---------------------------------------------------------------------------
# Revision history
# ---------------------------------------------------------------------------


def append_revision_event(
    registry: dict[str, Any],
    doc_id: str,
    event_type: str,
    revision: int,
    content_hash: str,
    reason: str,
    from_revision: int | None = None,
    from_status: str | None = None,
    to_status: str | None = None,
) -> RevisionEvent:
    """Append a revision event to the document's history.
    
    Returns the created event.
    """
    event = RevisionEvent(
        event_id=generate_event_id(),
        event_type=event_type,
        doc_id=doc_id,
        revision=revision,
        content_hash=content_hash,
        at=date.today().isoformat(),
        actor="user",
        reason=reason,
        from_revision=from_revision,
        from_status=from_status,
        to_status=to_status,
    )
    
    # Find the document and append to its history
    for doc in registry.get("documents", []):
        if doc.get("doc_id") == doc_id:
            if "history" not in doc:
                doc["history"] = []
            doc["history"].append(event.__dict__)
            break
    
    return event


def get_latest_revision_event(registry: dict[str, Any], doc_id: str) -> RevisionEvent | None:
    """Get the latest revision event for a document."""
    for doc in registry.get("documents", []):
        if doc.get("doc_id") == doc_id:
            history = doc.get("history", [])
            if history:
                latest = history[-1]
                return RevisionEvent(**latest)
    return None
