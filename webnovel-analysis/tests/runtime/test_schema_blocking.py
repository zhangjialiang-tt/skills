from pathlib import Path

import pytest

from runtime.errors import ModuleOutputSchemaError
from runtime.schema_validator import SchemaValidator


ROOT = Path(__file__).parents[2]


def test_invalid_module_output_is_rejected_without_repair() -> None:
    output = {
        "task_id": "TASK-0001",
        "batch_id": "BATCH-001",
        "skill_id": "S2",
        "schema_version": "1.0.0",
        "operation": "analyze",
        "payload": {"records": [], "batch_statistics": {}, "batch_summary": {}},
        "uncertain_items": [],
        "conflicts": [],
        "manual_review_items": [],
    }
    with pytest.raises(ModuleOutputSchemaError) as error:
        SchemaValidator(ROOT / "schemas").validate_module("S2", output)

    assert error.value.context["violations"][0]["path"] == "$.skill_version"
    assert "skill_version" not in output
