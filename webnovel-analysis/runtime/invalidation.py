from .dag import ExecutionDag
from .registry import ArtifactRegistry


def invalidate_target_and_direct_dependents(
    *, registry: ArtifactRegistry, dag: ExecutionDag, module_id: str, batch_id: str, invalidated_by: str
) -> list[str]:
    affected = [module_id, *dag.direct_dependents(module_id)]
    invalidated = []
    for affected_module in affected:
        try:
            record = registry.latest(affected_module, batch_id, usable_only=True)
        except Exception as error:
            if getattr(error, "code", None) == "ARTIFACT_NOT_FOUND":
                continue
            raise
        registry.invalidate(record["artifact_id"], invalidated_by=invalidated_by)
        invalidated.append(affected_module)
    return invalidated
