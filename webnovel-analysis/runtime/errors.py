class RuntimeContractError(Exception):
    code = "RUNTIME_CONTRACT_ERROR"

    def __init__(self, message: str, **context: object) -> None:
        super().__init__(message)
        self.context = context


class DagDependencyError(RuntimeContractError):
    code = "DAG_DEPENDENCY_ERROR"


class ModuleExecutionError(RuntimeContractError):
    code = "MODULE_EXECUTION_ERROR"


class ModuleOutputSchemaError(RuntimeContractError):
    code = "MODULE_OUTPUT_SCHEMA_INVALID"


class ArtifactNotFoundError(RuntimeContractError):
    code = "ARTIFACT_NOT_FOUND"


class ArtifactInvalidatedError(RuntimeContractError):
    code = "ARTIFACT_INVALIDATED"


class GateBlockedError(RuntimeContractError):
    code = "GATE_BLOCKED"


class ReviewRequiredError(RuntimeContractError):
    code = "REVIEW_REQUIRED"


class UnsupportedOperationError(RuntimeContractError):
    code = "UNSUPPORTED_OPERATION"


class DeliverableIncompleteError(RuntimeContractError):
    code = "DELIVERABLE_INCOMPLETE"
