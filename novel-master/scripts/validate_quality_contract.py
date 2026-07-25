#!/usr/bin/env python3
"""validate_quality_contract.py — Cross-object semantic validation for V1.2 quality contract.

Validates that:
  (a) STANDARD/STRICT chapter_plan has reader_experience (requires both TaskEnvelope and ChapterPlan)
  (b) style_modulation_ref references exist in style_guide.scene_modulations
  (c) override_policy.protected_fields are not violated by any modulation
  (d) relative_to_global operators are legal per field

JSON Schema handles single-object structure; this script handles cross-object/cross-file semantics.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_json_or_yaml(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    text = p.read_text(encoding="utf-8")
    if p.suffix in (".json",):
        return json.loads(text)
    # YAML fallback
    try:
        import yaml
        return yaml.safe_load(text)
    except ImportError:
        raise RuntimeError("YAML support requires PyYAML. Install: pip install pyyaml")


# ---------------------------------------------------------------------------
# Conditionally-required validation
# ---------------------------------------------------------------------------

MODE_REQUIRED_MODES = {"STANDARD", "STRICT"}


def validate_reader_experience_required(task_envelope: dict,
                                         chapter_plan: dict) -> list[str]:
    """STANDARD/STRICT must have reader_experience."""
    errors: list[str] = []
    mode = _task_mode(task_envelope)
    if mode not in MODE_REQUIRED_MODES:
        return errors
    cp = chapter_plan.get("chapter_plan", chapter_plan)
    re = cp.get("reader_experience")
    if re is None:
        errors.append(f"STANDARD/STRICT requires reader_experience (task.mode={mode})")
        return errors
    if isinstance(re, dict) and len(re) == 0:
        errors.append("reader_experience must not be empty in STANDARD/STRICT")
    return errors


# ---------------------------------------------------------------------------
# Cross-file reference validation
# ---------------------------------------------------------------------------

def validate_modulation_refs(chapter_plan: dict,
                              style_guide: dict) -> list[str]:
    """Every style_modulation_ref must exist in style_guide.scene_modulations."""
    errors: list[str] = []
    cp = chapter_plan.get("chapter_plan", chapter_plan)
    sg = style_guide.get("style_guide", style_guide)
    mod_defs = sg.get("scene_modulations", {})
    scenes = cp.get("scenes", [])
    for i, scene in enumerate(scenes):
        ref = scene.get("style_modulation_ref")
        if ref is None:
            continue
        if ref not in mod_defs:
            errors.append(
                f"scene[{i}].style_modulation_ref '{ref}' not found in style_guide.scene_modulations. "
                f"Available: {list(mod_defs.keys())}")
    return errors


# ---------------------------------------------------------------------------
# Protected field enforcement
# ---------------------------------------------------------------------------

def validate_protected_fields(style_guide: dict) -> list[str]:
    """No modulation's overrides may touch a protected_field."""
    errors: list[str] = []
    sg = style_guide.get("style_guide", style_guide)
    protected = sg.get("override_policy", {}).get("protected_fields", [])
    if not protected:
        return errors
    modulations = sg.get("scene_modulations", {})
    for mod_id, mod_def in modulations.items():
        overrides = mod_def.get("overrides", {})
        for field_path in overrides:
            field_name = f"/{field_path}"
            for pf in protected:
                if field_name.startswith(pf.rstrip("/")) or pf.startswith(field_name):
                    errors.append(
                        f"Modulation '{mod_id}' overrides field '{field_name}' "
                        f"which is protected by override_policy.protected_fields: {pf}")
    return errors


# ---------------------------------------------------------------------------
# Operator legality
# ---------------------------------------------------------------------------

FIELD_OPERATOR_MAP = {
    "sentence_rhythm": {"SHORTER", "LONGER", "SAME"},
    "action_density": {"HIGHER", "LOWER", "SAME"},
    "narrative_distance": {"CLOSER", "FARTHER", "SAME"},
    "description_density": {"HIGHER", "LOWER", "SAME"},
    "dialogue_ratio": {"HIGHER", "LOWER", "SAME"},
}


def validate_relative_operators(style_guide: dict) -> list[str]:
    """relative_to_global values must be legal per field type."""
    errors: list[str] = []
    sg = style_guide.get("style_guide", style_guide)
    modulations = sg.get("scene_modulations", {})
    for mod_id, mod_def in modulations.items():
        overrides = mod_def.get("overrides", {})
        for field_name, override_obj in overrides.items():
            op = override_obj.get("relative_to_global", "")
            allowed = FIELD_OPERATOR_MAP.get(field_name)
            if allowed is None:
                errors.append(
                    f"Modulation '{mod_id}': unknown field '{field_name}'. "
                    f"Defined fields: {list(FIELD_OPERATOR_MAP.keys())}")
                continue
            if op not in allowed:
                errors.append(
                    f"Modulation '{mod_id}': field '{field_name}' has illegal operator '{op}'. "
                    f"Allowed: {sorted(allowed)}")
    return errors


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _task_mode(task_envelope: dict) -> str:
    return (task_envelope.get("task", {}) or {}).get("mode", "")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cross-object semantic validation for V1.2 quality contract")
    sub = parser.add_subparsers(dest="command")

    p_re = sub.add_parser("check-reader-experience",
                           help="Validate reader_experience is required for STANDARD/STRICT")
    p_re.add_argument("--task-envelope", required=True)
    p_re.add_argument("--chapter-plan", required=True)

    p_mod = sub.add_parser("check-modulation-refs",
                            help="Validate style_modulation_ref references exist")
    p_mod.add_argument("--chapter-plan", required=True)
    p_mod.add_argument("--style-guide", required=True)

    p_prot = sub.add_parser("check-protected-fields",
                             help="Validate no modulation overrides protected fields")
    p_prot.add_argument("--style-guide", required=True)

    p_op = sub.add_parser("check-operators",
                           help="Validate relative_to_global operators are legal")
    p_op.add_argument("--style-guide", required=True)

    p_all = sub.add_parser("validate-all",
                            help="Run all quality contract checks")
    p_all.add_argument("--task-envelope", default=None)
    p_all.add_argument("--chapter-plan", default=None)
    p_all.add_argument("--style-guide", default=None)

    args = parser.parse_args()
    errors_all: list[str] = []

    try:
        if args.command == "check-reader-experience":
            te = load_json_or_yaml(args.task_envelope)
            cp = load_json_or_yaml(args.chapter_plan)
            errors_all = validate_reader_experience_required(te, cp)

        elif args.command == "check-modulation-refs":
            cp = load_json_or_yaml(args.chapter_plan)
            sg = load_json_or_yaml(args.style_guide)
            errors_all = validate_modulation_refs(cp, sg)

        elif args.command == "check-protected-fields":
            sg = load_json_or_yaml(args.style_guide)
            errors_all = validate_protected_fields(sg)

        elif args.command == "check-operators":
            sg = load_json_or_yaml(args.style_guide)
            errors_all = validate_relative_operators(sg)

        elif args.command == "validate-all":
            if args.task_envelope and args.chapter_plan:
                te = load_json_or_yaml(args.task_envelope)
                cp = load_json_or_yaml(args.chapter_plan)
                errors_all += validate_reader_experience_required(te, cp)
            if args.chapter_plan and args.style_guide:
                cp = load_json_or_yaml(args.chapter_plan)
                sg = load_json_or_yaml(args.style_guide)
                errors_all += validate_modulation_refs(cp, sg)
            if args.style_guide:
                sg = load_json_or_yaml(args.style_guide)
                errors_all += validate_protected_fields(sg)
                errors_all += validate_relative_operators(sg)
        else:
            parser.print_help()
            return 2
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        return 2

    if errors_all:
        for err in errors_all:
            print(f"FAIL: {err}")
        return 1

    print("PASS: all quality contract checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
