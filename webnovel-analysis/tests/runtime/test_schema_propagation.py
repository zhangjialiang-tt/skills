import pytest

from runtime.errors import ArtifactNotFoundError, ModuleOutputSchemaError

from helpers import create_runtime


def test_invalid_s2_output_stops_its_downstream(tmp_path) -> None:
    runtime = create_runtime(tmp_path)
    with pytest.raises(ModuleOutputSchemaError):
        runtime.run_batch("TASK-0001", "BATCH-001", scenario="invalid_s2")

    registry = runtime.registry("TASK-0001")
    assert registry.latest("S2", "BATCH-001")["status"] == "FAILED"
    for module_id in ("S4", "S5", "S6", "Q0"):
        with pytest.raises(ArtifactNotFoundError):
            registry.latest(module_id, "BATCH-001")
    _, batch = runtime.load_states("TASK-0001")
    assert batch.status == "BLOCKED"
