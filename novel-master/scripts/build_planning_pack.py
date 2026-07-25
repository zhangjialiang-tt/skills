#!/usr/bin/env python3
"""v1.3 确定性 PlanningPack 构建器。

由 novel-master 调用，从活动规划产物和最新章节执行记录构建 PlanningPack。
"""

import sys
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List

ROOT = Path(__file__).resolve().parent.parent


def usage():
    print("Usage: build_planning_pack.py <project_dir> [--output <file>]", file=sys.stderr)
    print("  Builds PlanningPack from active planning artifacts.", file=sys.stderr)
    sys.exit(1)


def load_yaml(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_plan_ref(data: Dict[str, Any], key: str) -> Optional[Dict[str, Any]]:
    meta = data.get("planning_artifact_meta", {})
    ref = {
        "artifact_type": meta.get("artifact_type"),
        "artifact_id": meta.get("artifact_id"),
        "path": str(data.get("_source_path", "")),
        "revision": meta.get("revision"),
        "content_hash": data.get("_content_hash", ""),
    }
    return ref if all(ref.values()) else None


def extract_milestones(spine: Dict[str, Any]) -> List[str]:
    milestones = []
    for phase in spine.get("project_spine", {}).get("phases", []):
        for m in phase.get("non_negotiable_milestones", []):
            milestones.append(m.get("description", ""))
    return milestones


def extract_beats(arc: Dict[str, Any]) -> List[str]:
    beats = []
    for b in arc.get("arc_plan", {}).get("required_beats", []):
        beats.append(b.get("description", ""))
    return beats


def extract_slots(batch: Dict[str, Any]) -> List[Dict[str, str]]:
    slots = []
    for slot in batch.get("chapter_batch", {}).get("chapter_slots", []):
        if slot.get("status") in ("PLANNED", "ASSIGNED"):
            slots.append({
                "slot_id": slot.get("slot_id", ""),
                "intended_function": slot.get("intended_function", ""),
            })
    return slots


def build_pack(project_dir: Path):
    arch_dir = project_dir / "architecture"
    outl_dir = project_dir / "outline"
    chap_dir = project_dir / "chapters"

    engine = load_yaml(arch_dir / "story_engine.md") or {}
    spine = load_yaml(arch_dir / "project_spine.md") or {}
    volume = load_yaml(outl_dir / "volumes" / "volume_01.md") or {}
    arc = load_yaml(outl_dir / "arcs" / "arc_01_01.md") or {}

    batch = None
    batch_dir = chap_dir / "batches"
    if batch_dir.exists():
        batch_files = sorted(batch_dir.glob("batch_*.md"))
        if batch_files:
            batch = load_yaml(batch_files[-1])  # latest

    pack = {
        "schema_version": "1.0",
        "generated_for_request": "",
        "active_phase": {
            "ref": load_plan_ref(spine, "project_spine") or {},
            "core_question": (spine.get("project_spine", {}).get("phases", [{}])[0].get("core_question", "")
                              if spine.get("project_spine", {}).get("phases") else ""),
            "non_negotiable_milestones": extract_milestones(spine),
        },
        "active_volume": {
            "ref": load_plan_ref(volume, "volume_arc") or {},
            "core_question": volume.get("volume_arc", {}).get("core_question", ""),
            "irreversible_change": volume.get("volume_arc", {}).get("irreversible_change", ""),
            "reader_payoff": volume.get("volume_arc", {}).get("reader_payoff", ""),
        },
        "active_arc": {
            "ref": load_plan_ref(arc, "arc_plan") or {},
            "arc_goal": arc.get("arc_plan", {}).get("arc_goal", ""),
            "dramatic_question": arc.get("arc_plan", {}).get("dramatic_question", ""),
            "required_beats": extract_beats(arc),
        },
        "active_batch": None,
        "current_progress": {
            "completed_beat_refs": [],
            "delayed_beat_refs": [],
            "deviation_summary": [],
        },
        "prohibited_strategic_changes": [],
        "unknowns": [],
    }

    if batch:
        pack["active_batch"] = {
            "ref": load_plan_ref(batch, "chapter_batch") or {},
            "remaining_slots": extract_slots(batch),
        }

    return pack


def main():
    args = sys.argv[1:]
    if not args:
        usage()

    project_dir = Path(args[0])
    if not project_dir.is_dir():
        print(f"ERROR: project_dir not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    pack = build_pack(project_dir)
    output = json.dumps(pack, ensure_ascii=False, indent=2)

    if len(args) >= 3 and args[1] == "--output":
        with open(args[2], "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
