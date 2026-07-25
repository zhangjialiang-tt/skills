#!/usr/bin/env python3
"""v1.3 plan_progress 重建器。

从 ACCEPTED 章节 + PlanningExecution + ReviewReport + 有效 PlanRef 重建 plan_progress.md。
用于 SYNC_PENDING 恢复或手动修复。
"""

import sys
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List

ROOT = Path(__file__).resolve().parent.parent


def usage():
    print("Usage: rebuild_plan_progress.py <project_dir> [--dry-run]", file=sys.stderr)
    sys.exit(1)


def load_yaml(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def rebuild(project_dir: Path, dry_run: bool = False):
    drafts = sorted((project_dir / "chapters" / "drafts").glob("chapter_*.md"))

    completed_milestones = []
    deviations = []
    last_acceptance = ""

    for draft_path in drafts:
        data = load_yaml(draft_path)
        if not data:
            continue
        # Only use ACCEPTED chapters
        lifecycle = data.get("chapter_lifecycle_status", "")
        if lifecycle not in ("ACCEPTED", "PUBLISHED"):
            continue

        acceptance_ref = f"{draft_path.stem}-{data.get('revision', 'unknown')}"
        last_acceptance = acceptance_ref

        # Collect milestone effects from planning_execution
        pe = data.get("chapter_report", {}).get("planning_execution", {})
        for me in pe.get("milestone_effects", []):
            if me.get("status_change") in ("ADVANCED", "COMPLETED"):
                completed_milestones.append({
                    "milestone_ref": me.get("milestone_ref", {}),
                    "completed_by_acceptance_ref": acceptance_ref,
                    "completed_at_chapter_ref": {"path": str(draft_path)},
                })

        # Collect deviations
        for dev in pe.get("actual_deviations", []):
            deviations.append({
                "deviation_id": dev.get("deviation_id", ""),
                "source_acceptance_ref": acceptance_ref,
                "assessment": {},
                "resolution_status": "RECORDED",
            })

    progress = {
        "last_processed_acceptance_ref": last_acceptance,
        "processed_updates": [],
        "active_phase_ref": {},
        "active_volume_ref": {},
        "active_arc_ref": {},
        "active_batch_ref": None,
        "completed_milestones": completed_milestones,
        "deviations": deviations,
        "arc_health": {
            "planned_chapter_count": 0,
            "used_chapter_count": len(drafts),
            "total_required_beats": 0,
            "completed_required_beats": 0,
            "overdue_beats": 0,
            "tactical_deviation_count": 0,
            "unresolved_strategic_deviation_count": 0,
            "derived": {
                "beat_completion_ratio": 0.0,
                "chapter_consumption_ratio": 0.0,
                "drift_score": 0.0,
                "status": "ON_TRACK",
            },
        },
    }

    if dry_run:
        import json
        print(json.dumps(progress, ensure_ascii=False, indent=2))
    else:
        out_path = project_dir / "workflow" / "plan_progress.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(progress, f, allow_unicode=True, default_flow_style=False)
        print(f"plan_progress rebuilt: {out_path}")

    return 0


def main():
    args = sys.argv[1:]
    if not args:
        usage()

    project_dir = Path(args[0])
    dry_run = "--dry-run" in args

    if not project_dir.is_dir():
        print(f"ERROR: project_dir not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    sys.exit(rebuild(project_dir, dry_run))


if __name__ == "__main__":
    main()
