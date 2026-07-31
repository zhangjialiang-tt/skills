#!/usr/bin/env python3
"""Preflight check for inkos-brief-compiler.

Validates that a SerialDesignPackage is ready for compilation.
Exit: 0 = ready, 1 = blocked.

Usage:
    python scripts/preflight.py --design-root story-design/<design-id>
"""

import argparse
import sys
from pathlib import Path


def load_yaml_safe(path: Path) -> tuple[dict | None, str | None]:
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


def check_serial_package(design_root: Path) -> tuple[list[str], list[str]]:
    """Check SerialDesignPackage readiness for compilation."""
    errors = []
    warnings = []

    serial_contract_path = design_root / "serial" / "serial-contract.yaml"
    if not serial_contract_path.exists():
        errors.append(f"Missing: {serial_contract_path}")
        return errors, warnings

    data, err = load_yaml_safe(serial_contract_path)
    if err:
        errors.append(err)
        return errors, warnings

    # Schema version
    if data.get("schema_version") != 1:
        errors.append(f"Unsupported schema_version: {data.get('schema_version')}")

    # Status checks
    status = data.get("status", {})
    if status.get("serial_design_status") != "frozen":
        errors.append(
            f"serial_design_status is '{status.get('serial_design_status')}', must be 'frozen'")
    if status.get("handoff_ready") is not True:
        errors.append("handoff_ready is not true")
    if status.get("readiness_verdict") != "pass":
        errors.append(
            f"readiness_verdict is '{status.get('readiness_verdict')}', must be 'pass'")

    # Upstream reference
    source = data.get("source", {})
    if not source.get("synopsis_contract_ref"):
        errors.append("Missing source.synopsis_contract_ref")
    if not source.get("synopsis_revision"):
        errors.append("Missing source.synopsis_revision")

    # Serialization target
    target = data.get("serialization_target", {})
    if not target.get("platform"):
        errors.append("Missing serialization_target.platform")
    if not target.get("target_chapters"):
        errors.append("Missing serialization_target.target_chapters")
    if not target.get("chapter_words"):
        errors.append("Missing serialization_target.chapter_words")

    # Assertions: check critical ones are confirmed
    assertions = data.get("assertions", [])
    if not assertions:
        errors.append("No assertions in serial-contract")
    else:
        critical_unconfirmed = [
            a.get("id", "?") for a in assertions
            if a.get("importance") == "critical" and a.get("status") != "confirmed"
        ]
        if critical_unconfirmed:
            errors.append(
                f"Critical assertions not confirmed: {critical_unconfirmed}")

    # Story engine present
    engine = data.get("story_engine", {})
    if not engine.get("loop"):
        errors.append("Missing story_engine.loop")

    # Volumes present
    volumes = data.get("volumes", [])
    if len(volumes) < 2:
        errors.append(f"Only {len(volumes)} volumes (need ≥2)")

    # Endgame convergence
    endgame = data.get("endgame_convergence", {})
    if not endgame.get("required_upstream_ending_ref"):
        errors.append("Missing endgame_convergence.required_upstream_ending_ref")

    # Launch plan
    launch = data.get("launch_plan", {})
    first_three = launch.get("first_three_chapters", [])
    if len(first_three) < 3:
        errors.append(f"launch_plan.first_three_chapters has {len(first_three)} entries (need 3)")

    # Compilation policy
    policy = data.get("compilation_policy", {})
    if not policy.get("must_preserve"):
        warnings.append("No compilation_policy.must_preserve defined")
    if not policy.get("block_if_missing"):
        warnings.append("No compilation_policy.block_if_missing defined")

    # Gate approval (check reviews directory)
    gate_a = design_root / "serial" / "reviews" / "gate-a-architecture.yaml"
    gate_b = design_root / "serial" / "reviews" / "gate-b-freeze.yaml"
    if gate_a.exists():
        gate_a_data, _ = load_yaml_safe(gate_a)
        if gate_a_data and gate_a_data.get("status") != "approved":
            errors.append(f"Gate A status is '{gate_a_data.get('status')}', not approved")
    else:
        warnings.append("gate-a-architecture.yaml not found (may not be generated yet)")

    if gate_b.exists():
        gate_b_data, _ = load_yaml_safe(gate_b)
        if gate_b_data and gate_b_data.get("status") != "approved":
            errors.append(f"Gate B status is '{gate_b_data.get('status')}', not approved")
    else:
        warnings.append("gate-b-freeze.yaml not found (may not be generated yet)")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Brief compiler preflight")
    parser.add_argument("--design-root", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    design_root = args.design_root
    if not design_root.is_dir():
        print(f"ERROR: Design root not found: {design_root}", file=sys.stderr)
        sys.exit(1)

    errors, warnings = check_serial_package(design_root)

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
            print("❌ NOT READY for compilation:", file=sys.stderr)
            for e in errors:
                print(f"  {e}", file=sys.stderr)
        if warnings:
            print("⚠️  Warnings:")
            for w in warnings:
                print(f"  {w}")
        if not errors:
            print("✅ SerialDesignPackage ready for compilation.")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
