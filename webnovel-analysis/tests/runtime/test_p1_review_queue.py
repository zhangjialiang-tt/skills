from helpers import create_runtime


def test_blocking_p1_requires_review_before_acceptance(tmp_path) -> None:
    runtime = create_runtime(tmp_path)
    runtime.run_batch("TASK-0001", "BATCH-001", scenario="q0_p1_blocking")
    task, batch = runtime.load_states("TASK-0001")
    assert task.status == "AWAITING_HUMAN"
    assert batch.status == "AWAITING_HUMAN"

    pending = runtime.pending_reviews("TASK-0001")
    assert pending[0]["review_id"] == "REV-0001"
    runtime.submit_review("TASK-0001", "REV-0001", "ACCEPT_WITH_RISK", reason="测试接受风险")
    _, accepted_batch = runtime.load_states("TASK-0001")
    assert accepted_batch.status == "ACCEPTED"


def test_non_blocking_p1_is_preserved_without_blocking(tmp_path) -> None:
    runtime = create_runtime(tmp_path)
    runtime.run_batch("TASK-0001", "BATCH-001", scenario="q0_p1_nonblocking")
    _, batch = runtime.load_states("TASK-0001")
    assert batch.status == "ACCEPTED"
    assert runtime.pending_reviews("TASK-0001")[0]["blocking"] is False
