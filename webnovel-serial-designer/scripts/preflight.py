#!/usr/bin/env python3
"""Preflight check for webnovel-serial-designer.

Validates that a StorySynopsisPackage is ready for serialization.
Exit: 0 = ready, 1 = blocked.

Usage:
    python scripts/preflight.py --design-root story-design/<design-id>
"""

import argparse
import sys
from pathlib import Path


def load_yaml_safe(path: Path) -> tuple[dict | None, str | None]:
    """Load YAML, return (data, error)."""
    try:
        import yaml
    except ImportError:
        return None, "YAML_PARSER_UNAVAILABLE: PyYAML required"
    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            return None, f"{path.name} is not a valid YAML mapping"
        return data, None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except Exception as e:
        return None, f"Cannot parse {path.name}: {e}"


def check_synopsis_package(design_root: Path) -> tuple[list[str], list[str]]:
    """Check StorySynopsisPackage readiness. Returns (errors, warnings)."""
    errors = []
    warnings = []

    # Check synopsis.md exists
    synopsis_md = design_root / "source" / "synopsis.md"
    if not synopsis_md.exists():
        errors.append(f"Missing: {synopsis_md}")

    # Check synopsis-contract.yaml exists
    contract_path = design_root / "source" / "synopsis-contract.yaml"
    if not contract_path.exists():
        errors.append(f"Missing: {contract_path}")
        return errors, warnings  # Can't proceed without contract

    # Load and validate contract
    data, err = load_yaml_safe(contract_path)
    if err:
        errors.append(err)
        return errors, warnings

    # Schema version
    if data.get("schema_version") != 1:
        errors.append(f"Unsupported schema_version: {data.get('schema_version')}")

    # Status checks
    status = data.get("status", {})
    if status.get("synopsis_status") != "user_confirmed":
        errors.append(
            f"synopsis_status is '{status.get('synopsis_status')}', "
            f"must be 'user_confirmed' for handoff")
    if status.get("handoff_ready") is not True:
        errors.append("handoff_ready is not true — package not ready for serialization")

    # Blocking issues
    quality = data.get("quality", {})
    blocking = quality.get("blocking_issues", [])
    if blocking:
        errors.append(f"Blocking issues present: {blocking}")

    # Required sections completeness
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
            errors.append(f"Missing section: {section}")
            continue
        for field in fields:
            val = sec_data.get(field)
            if val is None or (isinstance(val, str) and not val.strip()):
                errors.append(f"Empty required field: {section}.{field}")

    # Protagonist arc
    protag = data.get("protagonist", {})
    arc = protag.get("arc", {})
    for field in ["start", "turning_point", "final_choice", "end"]:
        if not arc.get(field):
            errors.append(f"Empty required field: protagonist.arc.{field}")

    # World rules
    rules = data.get("world_rules", [])
    if not rules:
        errors.append("No world_rules defined")

    # Turning points
    turns = data.get("major_turning_points", [])
    if len(turns) < 3:
        errors.append(f"Only {len(turns)} turning points (need ≥3)")

    # Adaptation boundaries
    bounds = data.get("adaptation_boundaries", {})
    if not bounds.get("frozen_facts"):
        errors.append("No frozen_facts in adaptation_boundaries")
    if not bounds.get("prohibited_directions"):
        warnings.append("No prohibited_directions — downstream may over-expand")

    # Ending frozen
    ending = data.get("ending", {})
    if ending.get("frozen") is not True:
        errors.append("Ending is not frozen — cannot proceed to serialization")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Serial designer preflight")
    parser.add_argument("--design-root", type=Path, required=True,
                        help="Path to story-design/<design-id>")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    design_root = args.design_root
    if not design_root.is_dir():
        print(f"ERROR: Design root not found: {design_root}", file=sys.stderr)
        sys.exit(1)

    errors, warnings = check_synopsis_package(design_root)

    if args.json:
        import json
        print(json.dumps({
            "design_root": str(design_root),
            "ready": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }, ensure_ascii=False, indent=2))
    else:
        if errors:
            print("❌ NOT READY for serialization:", file=sys.stderr)
            for e in errors:
                print(f"  {e}", file=sys.stderr)
        if warnings:
            print("⚠️  Warnings:")
            for w in warnings:
                print(f"  {w}")
        if not errors:
            print("✅ StorySynopsisPackage ready for serialization.")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
