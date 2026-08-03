import pytest

from runtime.errors import RuntimeContractError
from runtime.state import BatchState, TaskState


def test_state_transitions_are_validated() -> None:
    task = TaskState.new(task_id="TASK-0001", book_id="BOOK-0001", source_ref="source.md")
    batch = BatchState.new(task_id="TASK-0001", batch_id="BATCH-001", chapter_ids=["BOOK-0001-CH0001"])

    task.transition("RUNNING")
    batch.transition("RUNNING", current_stage="S0")
    assert task.status == "RUNNING"
    assert batch.current_stage == "S0"
    with pytest.raises(RuntimeContractError):
        batch.transition("DELIVERABLE_READY")
