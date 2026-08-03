import json
import re
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

from .errors import ModuleOutputSchemaError, RuntimeContractError


class SchemaValidator:
    def __init__(self, schemas_root: Path) -> None:
        self.schemas_root = Path(schemas_root)
        self.registry = Registry()
        for dependency in (self.schemas_root / "output-envelope.schema.json", self.schemas_root / "common-types.schema.json"):
            contents = json.loads(dependency.read_text(encoding="utf-8"))
            self.registry = self.registry.with_resource(dependency.as_uri(), Resource.from_contents(contents, default_specification=DRAFT7))

    def _validate(self, schema_path: Path, value: dict) -> list[dict]:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema["$id"] = schema_path.as_uri()
        errors = sorted(Draft7Validator(schema, registry=self.registry).iter_errors(value), key=lambda error: (list(error.path), error.message))
        violations = []
        for error in errors:
            path = "$" + "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path)
            if error.validator == "required":
                match = re.search(r"'([^']+)' is a required property", error.message)
                if match:
                    path += f".{match.group(1)}"
            violations.append({"path": path, "message": error.message})
        return violations

    def validate_module(self, module_id: str, output: dict) -> None:
        schema_path = self.schemas_root / "modules" / f"{module_id}.schema.json"
        violations = self._validate(schema_path, output)
        if violations:
            raise ModuleOutputSchemaError(
                f"{module_id} output failed schema validation",
                module_id=module_id,
                schema_path=f"schemas/modules/{module_id}.schema.json",
                violations=violations,
            )

    def validate_runtime(self, schema_name: str, value: dict) -> None:
        violations = self._validate(self.schemas_root / "runtime" / schema_name, value)
        if violations:
            raise RuntimeContractError(f"runtime schema {schema_name} failed", violations=violations)
