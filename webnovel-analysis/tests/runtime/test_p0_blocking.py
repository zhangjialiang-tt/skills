import pytest

from runtime.errors import DeliverableIncompleteError, GateBlockedError

from helpers import create_runtime


def test_q0_p0_blocks_batch_and_task(tmp_path) -> None:
    runtime = create_runtime(tmp_path)
    with pytest.raises(GateBlockedError):
        runtime.run_batch("TASK-0001", "BATCH-001", scenario="q0_p0")

    task, batch = runtime.load_states("TASK-0001")
    assert task.status == "BLOCKED"
    assert batch.status == "BLOCKED"
    assert batch.blocking_issue_ids == ["AUD-P0-001"]
    with pytest.raises(DeliverableIncompleteError):
        runtime.finalize("TASK-0001", __import__("pathlib").Path(__file__).parents[2] / "tests" / "fixtures" / "runtime" / "gate-c-accepted.yaml")
