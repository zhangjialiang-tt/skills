#!/usr/bin/env python3
"""Emit and validate a StorySynopsisPackage (story-design/<design-id>/source/).

The package is the downstream-consumable handoff produced by story-synopsis
when the user confirms finalization:

    story-design/<design-id>/source/
    ├── synopsis.md              # full synopsis (3000-5000 chars)
    └── synopsis-contract.yaml   # machine contract

Commands:
    check  --design-root <dir>            validate an existing package
    build  --design-root <dir> --synopsis <md> --contract <yaml>
                                          validate inputs, write package, re-validate

Exit: 0 = package valid/ready, 2 = validation errors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def derive_design_id(title: str) -> str:
    """Derive design-id from a work title (mirrors SKILL.md rule)."""
    design_id = re.sub(r'[\\/:*?"<>|]', "", title)
    design_id = design_id.rstrip(". ")
    return design_id or "untitled-story"


def load_yaml_text(path: Path) -> dict:
    import yaml
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"error: file not found: {path}")
    except Exception as exc:
        raise SystemExit(f"error: cannot parse {path.name}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"error: {path.name} is not a YAML mapping")
    return data


def validate_contract(data: dict, design_root_name: str | None = None) -> tuple[list[str], list[str]]:
    """Validate contract semantics. Mirrors webnovel-serial-designer preflight
    and adds story-synopsis-specific rules (design-id, revision, frozen).
    Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    if data.get("schema_version") != 1:
        errors.append(f"schema_version must be 1, got {data.get('schema_version')}")
    if data.get("artifact_type") != "story_synopsis_contract":
        errors.append(f"artifact_type must be story_synopsis_contract, got {data.get('artifact_type')}")

    identity = data.get("identity") or {}
    design_id = identity.get("design_id")
    if not design_id:
        errors.append("identity.design_id is required")
    elif design_root_name and design_root_name != design_id:
        errors.append(
            f"design_root directory '{design_root_name}' does not match "
            f"identity.design_id '{design_id}'")

    source = data.get("source") or {}
    revision = source.get("synopsis_revision")
    if not isinstance(revision, int) or revision < 1:
        errors.append("source.synopsis_revision must be an integer >= 1")

    status = data.get("status") or {}
    if status.get("synopsis_status") != "user_confirmed":
        errors.append(
            f"synopsis_status is '{status.get('synopsis_status')}', must be 'user_confirmed'")
    if status.get("handoff_ready") is not True:
        errors.append("status.handoff_ready must be true for handoff")

    quality = data.get("quality") or {}
    if quality.get("blocking_issues"):
        errors.append(f"quality.blocking_issues must be empty, got {quality['blocking_issues']}")

    required_sections = {
        "story_core": ["premise", "genre", "central_question", "story_promise"],
        "protagonist": ["name", "identity", "external_desire", "internal_need", "flaw", "agency"],
        "opposition": ["type", "primary_opponent"],
        "core_conflict": ["external", "internal"],
        "story_truth": ["hidden_truth", "truth_origin"],
        "ending": ["external_outcome", "final_choice", "thematic_answer"],
    }
    for section, fields in required_sections.items():
        sec_data = data.get(section)
        if not sec_data:
            errors.append(f"missing section: {section}")
            continue
        for field in fields:
            val = sec_data.get(field)
            if val is None or (isinstance(val, str) and not val.strip()):
                errors.append(f"empty required field: {section}.{field}")

    protag = data.get("protagonist") or {}
    arc = protag.get("arc") or {}
    for field in ("start", "turning_point", "final_choice", "end"):
        if not arc.get(field):
            errors.append(f"empty required field: protagonist.arc.{field}")

    rules = data.get("world_rules") or []
    if not isinstance(rules, list) or not rules:
        errors.append("world_rules must contain at least one rule")
    else:
        for rule in rules:
            if not isinstance(rule, dict):
                errors.append("world_rules entries must be mappings")
                break
            for field in ("id", "statement", "boundary", "cost"):
                if not rule.get(field):
                    errors.append(f"world_rules entry missing {field}")
            if rule.get("frozen") is not True:
                errors.append(f"world_rules {rule.get('id')}: frozen must be true")

    turns = data.get("major_turning_points") or []
    if not isinstance(turns, list) or len(turns) < 3:
        errors.append(f"major_turning_points must have >= 3 entries, got {len(turns)}")
    else:
        for turn in turns:
            if not isinstance(turn, dict):
                errors.append("major_turning_points entries must be mappings")
                break
            for field in ("id", "stage", "event", "state_change"):
                if not turn.get(field):
                    errors.append(f"major_turning_points entry missing {field}")
            if turn.get("frozen") is not True:
                errors.append(f"major_turning_points {turn.get('id')}: frozen must be true")

    bounds = data.get("adaptation_boundaries") or {}
    if not bounds.get("frozen_facts"):
        errors.append("adaptation_boundaries.frozen_facts must not be empty")
    if not bounds.get("prohibited_directions"):
        warnings.append("adaptation_boundaries.prohibited_directions is empty — downstream may over-expand")
    if not bounds.get("expandable_zones"):
        warnings.append("adaptation_boundaries.expandable_zones is empty")
    if "unresolved_non_blocking" not in bounds:
        warnings.append("adaptation_boundaries.unresolved_non_blocking is missing")

    ending = data.get("ending") or {}
    if ending.get("frozen") is not True:
        errors.append("ending.frozen must be true")
    valid_endings = {"bittersweet", "tragic", "hopeful", "ambiguous", "triumphant"}
    if ending.get("ending_type") not in valid_endings:
        errors.append(
            f"ending.ending_type must be one of {sorted(valid_endings)}, "
            f"got {ending.get('ending_type')}")

    return errors, warnings


def check_package(design_root: Path, json_out: bool) -> int:
    source_dir = design_root / "source"
    synopsis_md = source_dir / "synopsis.md"
    contract_path = source_dir / "synopsis-contract.yaml"
    errors: list[str] = []
    warnings: list[str] = []

    if not synopsis_md.exists():
        errors.append(f"missing: {synopsis_md}")
    if not contract_path.exists():
        errors.append(f"missing: {contract_path}")
    else:
        try:
            data = load_yaml_text(contract_path)
        except SystemExit as exc:
            errors.append(str(exc))
            data = None
        if data is not None:
            errs, warns = validate_contract(data, design_root.name)
            errors.extend(errs)
            warnings.extend(warns)

    report = {
        "design_root": str(design_root),
        "ready": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
    if json_out:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if errors:
            print("NOT READY:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
        for w in warnings:
            print(f"warning: {w}")
        if not errors:
            print("StorySynopsisPackage ready for downstream consumption.")
    return 0 if not errors else 2


def build_package(
    design_root: Path,
    synopsis_path: Path,
    contract_path: Path,
    json_out: bool,
) -> int:
    if not synopsis_path.exists():
        print(f"error: synopsis file not found: {synopsis_path}", file=sys.stderr)
        return 2
    synopsis_text = synopsis_path.read_text(encoding="utf-8")
    if len(synopsis_text.strip()) < 200:
        print(
            f"error: synopsis.md looks incomplete ({len(synopsis_text.strip())} chars)",
            file=sys.stderr,
        )
        return 2

    data = load_yaml_text(contract_path)
    errors, warnings = validate_contract(data, design_root.name)
    if errors:
        print("build blocked by contract errors:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 2

    source_dir = design_root / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    out_md = source_dir / "synopsis.md"
    out_yaml = source_dir / "synopsis-contract.yaml"
    out_md.write_text(synopsis_text, encoding="utf-8")
    out_yaml.write_text(
        dump_yaml(data),
        encoding="utf-8",
    )

    report = {
        "design_root": str(design_root),
        "written": [str(out_md), str(out_yaml)],
        "warnings": warnings,
        "ready": True,
    }
    if json_out:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for w in warnings:
            print(f"warning: {w}")
        print(f"written: {out_md}")
        print(f"written: {out_yaml}")
        print("StorySynopsisPackage emitted and valid.")
    return 0


def dump_yaml(data: dict) -> str:
    import yaml
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit/validate StorySynopsisPackage")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="validate an existing package")
    p_check.add_argument("--design-root", type=Path, required=True)
    p_check.add_argument("--json", action="store_true")

    p_build = sub.add_parser("build", help="write package from synopsis + contract")
    p_build.add_argument("--design-root", type=Path, required=True)
    p_build.add_argument("--synopsis", type=Path, required=True)
    p_build.add_argument("--contract", type=Path, required=True)
    p_build.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "check":
        if not args.design_root.is_dir():
            print(f"error: design root not found: {args.design_root}", file=sys.stderr)
            return 2
        return check_package(args.design_root, args.json)
    return build_package(args.design_root, args.synopsis, args.contract, args.json)


if __name__ == "__main__":
    sys.exit(main())
