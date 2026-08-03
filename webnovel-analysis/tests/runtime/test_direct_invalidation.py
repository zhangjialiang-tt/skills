from helpers import create_runtime


def test_rerun_preserves_unaffected_revisions_and_recomputes_required_downstream(tmp_path) -> None:
    runtime = create_runtime(tmp_path)
    runtime.run_batch("TASK-0001", "BATCH-001", scenario="valid")
    before = runtime.registry("TASK-0001")
    original = {module: before.latest(module, "BATCH-001") for module in ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "Q0")}

    runtime.rerun("TASK-0001", "BATCH-001", "S2", scenario="corrected")
    after = runtime.registry("TASK-0001")

    for module in ("S0", "S1", "S3"):
        assert after.latest(module, "BATCH-001")["revision"] == 1
        assert after.latest(module, "BATCH-001")["artifact_id"] == original[module]["artifact_id"]
    for module in ("S2", "S4", "S5", "S6", "Q0"):
        assert after.latest(module, "BATCH-001")["revision"] == 2
        assert after.latest(module, "BATCH-001")["status"] == "VALIDATED"
    for module in ("S2", "S4", "S5", "S6", "Q0"):
        old = next(record for record in after.records if record["artifact_id"] == original[module]["artifact_id"])
        assert old["status"] == "INVALIDATED"
    s6 = runtime.task_root("TASK-0001") / after.latest("S6", "BATCH-001")["file_path"]
    records = __import__("json").loads(s6.read_text(encoding="utf-8"))["payload"]["master_records"]
    assert len({record["chapter_id"] for record in records}) == len(records)
