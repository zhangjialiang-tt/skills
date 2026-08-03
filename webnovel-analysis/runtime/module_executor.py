from .artifact_store import ArtifactStore
from .errors import ModuleOutputSchemaError
from .registry import ArtifactRegistry
from .schema_validator import SchemaValidator


class ModuleExecutor:
    def __init__(self, *, store: ArtifactStore, registry: ArtifactRegistry, validator: SchemaValidator, adapter) -> None:
        self.store = store
        self.registry = registry
        self.validator = validator
        self.adapter = adapter

    def execute(
        self,
        *,
        task_id: str,
        batch_id: str,
        module_id: str,
        operation: str,
        input_payload: dict,
        input_artifact_ids: list[str],
        replaces_artifact_id: str | None = None,
    ) -> dict:
        record = self.registry.create_record(
            task_id=task_id,
            batch_id=batch_id,
            module_id=module_id,
            operation=operation,
            schema_path=f"schemas/modules/{module_id}.schema.json",
            input_artifact_ids=input_artifact_ids,
            replaces_artifact_id=replaces_artifact_id,
        )
        output = self.adapter.execute(
            module_id=module_id,
            operation=operation,
            input_payload=input_payload,
            execution_context={"task_id": task_id, "batch_id": batch_id, "artifact_id": record["artifact_id"]},
        )
        self.store.write_raw(record, output)
        try:
            self.validator.validate_module(module_id, output)
        except ModuleOutputSchemaError as error:
            record["status"] = "FAILED"
            record["validation_errors"] = error.context["violations"]
            self.validator.validate_runtime("artifact-record.schema.json", record)
            self.registry.save(record)
            error.context.update({"task_id": task_id, "batch_id": batch_id, "artifact_id": record["artifact_id"]})
            raise
        self.store.write_validated(record, output)
        record["status"] = "VALIDATED"
        self.validator.validate_runtime("artifact-record.schema.json", record)
        self.registry.save(record)
        return record
