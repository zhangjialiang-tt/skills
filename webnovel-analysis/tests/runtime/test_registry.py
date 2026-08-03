import json

from runtime.artifact_store import ArtifactStore
from runtime.registry import ArtifactRegistry


def test_artifact_revisions_are_preserved(tmp_path) -> None:
    store = ArtifactStore(tmp_path)
    registry = ArtifactRegistry(tmp_path / "registry.json")
    first = registry.create_record(task_id="TASK-0001", batch_id="BATCH-001", module_id="S2", operation="analyze", schema_path="schemas/modules/S2.schema.json", input_artifact_ids=[])
    store.write_validated(first, {"revision": 1})
    registry.save(first)
    second = registry.create_record(task_id="TASK-0001", batch_id="BATCH-001", module_id="S2", operation="analyze", schema_path="schemas/modules/S2.schema.json", input_artifact_ids=[], replaces_artifact_id=first["artifact_id"])
    store.write_validated(second, {"revision": 2})
    registry.save(second)

    assert first["revision"] == 1
    assert second["revision"] == 2
    assert json.loads((tmp_path / first["file_path"]).read_text(encoding="utf-8")) == {"revision": 1}
    assert json.loads((tmp_path / second["file_path"]).read_text(encoding="utf-8")) == {"revision": 2}
