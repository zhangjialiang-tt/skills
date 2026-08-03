from runtime.errors import ArtifactNotFoundError, GateBlockedError

from helpers import create_runtime


def test_gate_a_blocks_duplicate_chapters_before_analysis(tmp_path) -> None:
    runtime = create_runtime(tmp_path)
    try:
        runtime.run_batch("TASK-0001", "BATCH-001", scenario="gate_a_duplicate")
    except GateBlockedError:
        pass
    else:
        raise AssertionError("Gate A must block duplicate chapter IDs")

    _, batch = runtime.load_states("TASK-0001")
    assert batch.status == "BLOCKED"
    for module_id in ("S1", "S2", "S3"):
        with __import__("pytest").raises(ArtifactNotFoundError):
            runtime.registry("TASK-0001").latest(module_id, "BATCH-001")
