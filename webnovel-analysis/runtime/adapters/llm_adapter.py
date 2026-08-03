class LLMAdapter:
    def execute(self, *, module_id: str, operation: str, input_payload: dict, execution_context: dict) -> dict:
        raise NotImplementedError("Real LLM execution is outside Milestone 2.")
