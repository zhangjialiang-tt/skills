from typing import Protocol


class ModuleAdapter(Protocol):
    def execute(self, *, module_id: str, operation: str, input_payload: dict, execution_context: dict) -> dict:
        ...
