from pathlib import Path

import json

import pytest
from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7


ROOT = Path(__file__).parents[1]
MODULE_IDS = ["O0", "S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "Q0", "R0"]


@pytest.mark.parametrize("module_id", MODULE_IDS)
def test_contract_fixture_validates_against_module_schema(module_id: str) -> None:
    schema_path = ROOT / "schemas" / "modules" / f"{module_id}.schema.json"
    fixture_path = ROOT / "tests" / "fixtures" / "contracts" / f"{module_id}.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["$id"] = schema_path.as_uri()
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    registry = Registry()
    for dependency in (ROOT / "schemas" / "output-envelope.schema.json", ROOT / "schemas" / "common-types.schema.json"):
        contents = json.loads(dependency.read_text(encoding="utf-8"))
        registry = registry.with_resource(dependency.as_uri(), Resource.from_contents(contents, default_specification=DRAFT7))
    errors = sorted(Draft7Validator(schema, registry=registry).iter_errors(fixture), key=lambda error: list(error.path))
    assert not errors, "\n".join(error.message for error in errors)


def test_model_output_envelope_excludes_runtime_registry_fields() -> None:
    schema = json.loads((ROOT / "schemas" / "output-envelope.schema.json").read_text(encoding="utf-8"))
    properties = schema["properties"]
    for runtime_field in ("output_hash", "validated_at", "invalidated_by", "status"):
        assert runtime_field not in properties


def test_s4_payoff_event_requires_payoff_nature() -> None:
    schema = json.loads((ROOT / "schemas" / "modules" / "S4.schema.json").read_text(encoding="utf-8"))
    payload = schema["allOf"][1]["properties"]["payload"]
    required = payload["properties"]["payoff_events"]["items"]["required"]
    assert "payoff_nature" in required


def test_s6_has_no_final_report_payload() -> None:
    schema = json.loads((ROOT / "schemas" / "modules" / "S6.schema.json").read_text(encoding="utf-8"))
    payload_properties = schema["allOf"][1]["properties"]["payload"]["properties"]
    assert "analysis_report" not in payload_properties
    assert "analysis_report_md" not in payload_properties
