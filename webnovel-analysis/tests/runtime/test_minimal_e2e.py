import json

from helpers import ROOT, create_runtime


def test_mini_novel_runs_from_s0_to_r0_and_builds_delivery(tmp_path) -> None:
    runtime = create_runtime(tmp_path)
    runtime.run_batch("TASK-0001", "BATCH-001", scenario="valid")
    manifest_path = runtime.finalize("TASK-0001", ROOT / "tests" / "fixtures" / "runtime" / "gate-c-accepted.yaml")

    task, batch = runtime.load_states("TASK-0001")
    assert task.status == "DELIVERABLE_READY"
    assert batch.status == "ACCEPTED"
    registry = runtime.registry("TASK-0001")
    assert {record["module_id"] for record in registry.records if record["status"] == "VALIDATED"} == {"O0", "S0", "S1", "S2", "S3", "S4", "S5", "S6", "Q0", "S7", "S8", "S9", "R0"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest["deliverables"]) == 5
    report_path = manifest_path.parent / "analysis_report.md"
    assert report_path.is_file()
    assert "拆书分析报告" in report_path.read_text(encoding="utf-8")
