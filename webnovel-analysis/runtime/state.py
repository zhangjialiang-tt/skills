from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from .errors import RuntimeContractError


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


TASK_TRANSITIONS = {
    "CREATED": {"RUNNING", "FAILED"},
    "RUNNING": {"AWAITING_HUMAN", "BLOCKED", "DELIVERABLE_READY", "FAILED", "COMPLETED"},
    "AWAITING_HUMAN": {"RUNNING", "BLOCKED", "FAILED"},
    "BLOCKED": {"RUNNING", "FAILED"},
    "DELIVERABLE_READY": {"COMPLETED", "RUNNING", "FAILED"},
    "COMPLETED": set(),
    "FAILED": {"RUNNING"},
}
BATCH_TRANSITIONS = {
    "PLANNED": {"RUNNING", "FAILED"},
    "RUNNING": {"AUDITING", "BLOCKED", "FAILED", "INVALIDATED"},
    "AUDITING": {"AWAITING_HUMAN", "BLOCKED", "ACCEPTED", "FAILED"},
    "AWAITING_HUMAN": {"ACCEPTED", "BLOCKED", "RUNNING", "FAILED"},
    "BLOCKED": {"RUNNING", "INVALIDATED", "FAILED"},
    "ACCEPTED": {"RUNNING", "INVALIDATED"},
    "FAILED": {"RUNNING"},
    "INVALIDATED": {"RUNNING", "FAILED"},
}


@dataclass
class TaskState:
    task_id: str
    book_id: str
    status: str
    current_batch_id: str
    source_ref: str
    created_at: str
    updated_at: str
    failure: dict = field(default_factory=lambda: {"code": None, "message": None})

    @classmethod
    def new(cls, *, task_id: str, book_id: str, source_ref: str, batch_id: str = "BATCH-001") -> "TaskState":
        now = utc_now()
        return cls(task_id, book_id, "CREATED", batch_id, source_ref, now, now)

    @classmethod
    def from_dict(cls, data: dict) -> "TaskState":
        return cls(**data)

    def transition(self, status: str) -> None:
        if status not in TASK_TRANSITIONS.get(self.status, set()):
            raise RuntimeContractError(f"invalid task transition {self.status} -> {status}")
        self.status = status
        self.updated_at = utc_now()

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BatchState:
    task_id: str
    batch_id: str
    chapter_ids: list[str]
    status: str
    current_stage: str | None
    blocking_issue_ids: list[str] = field(default_factory=list)
    review_item_ids: list[str] = field(default_factory=list)

    @classmethod
    def new(cls, *, task_id: str, batch_id: str, chapter_ids: list[str]) -> "BatchState":
        return cls(task_id, batch_id, chapter_ids, "PLANNED", None)

    @classmethod
    def from_dict(cls, data: dict) -> "BatchState":
        return cls(**data)

    def transition(self, status: str, *, current_stage: str | None = None) -> None:
        if status not in BATCH_TRANSITIONS.get(self.status, set()):
            raise RuntimeContractError(f"invalid batch transition {self.status} -> {status}")
        self.status = status
        if current_stage is not None:
            self.current_stage = current_stage

    def to_dict(self) -> dict:
        return asdict(self)
