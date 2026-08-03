import json
from pathlib import Path

from .errors import ArtifactNotFoundError


class ArtifactRegistry:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        if self.path.exists():
            self.records = json.loads(self.path.read_text(encoding="utf-8"))["artifacts"]
        else:
            self.records: list[dict] = []

    def create_record(
        self,
        *,
        task_id: str,
        batch_id: str,
        module_id: str,
        operation: str,
        schema_path: str,
        input_artifact_ids: list[str],
        replaces_artifact_id: str | None = None,
    ) -> dict:
        revisions = [record["revision"] for record in self.records if record["batch_id"] == batch_id and record["module_id"] == module_id]
        revision = max(revisions, default=0) + 1
        artifact_id = f"ART-{module_id}-{batch_id}-R{revision}"
        return {
            "artifact_id": artifact_id,
            "task_id": task_id,
            "batch_id": batch_id,
            "module_id": module_id,
            "operation": operation,
            "revision": revision,
            "file_path": f"artifacts/{batch_id}/{module_id}/r{revision}/output.json",
            "schema_path": schema_path,
            "status": "GENERATED",
            "input_artifact_ids": list(input_artifact_ids),
            "replaces_artifact_id": replaces_artifact_id,
            "invalidated_by": None,
            "validation_errors": [],
        }

    def save(self, record: dict) -> None:
        existing = next((index for index, item in enumerate(self.records) if item["artifact_id"] == record["artifact_id"]), None)
        if existing is None:
            self.records.append(dict(record))
        else:
            self.records[existing] = dict(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"artifacts": self.records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def latest(self, module_id: str, batch_id: str, *, usable_only: bool = False) -> dict:
        candidates = [record for record in self.records if record["module_id"] == module_id and record["batch_id"] == batch_id]
        if usable_only:
            candidates = [record for record in candidates if record["status"] in {"VALIDATED", "ACCEPTED"}]
        if not candidates:
            raise ArtifactNotFoundError(f"no artifact for {module_id}/{batch_id}", module_id=module_id, batch_id=batch_id)
        return dict(max(candidates, key=lambda record: record["revision"]))

    def invalidate(self, artifact_id: str, *, invalidated_by: str) -> dict:
        record = next((item for item in self.records if item["artifact_id"] == artifact_id), None)
        if record is None:
            raise ArtifactNotFoundError(artifact_id)
        record["status"] = "INVALIDATED"
        record["invalidated_by"] = invalidated_by
        self.save(record)
        return dict(record)
