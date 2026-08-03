import json
from pathlib import Path

from ..errors import ModuleExecutionError


class FixtureAdapter:
    def __init__(self, fixtures_root: Path, *, scenario: str = "valid") -> None:
        self.fixtures_root = Path(fixtures_root)
        self.scenario = scenario

    def execute(self, *, module_id: str, operation: str, input_payload: dict, execution_context: dict) -> dict:
        scenario_path = self.fixtures_root / self.scenario / f"{module_id}.json"
        path = scenario_path if scenario_path.exists() else self.fixtures_root / "valid" / f"{module_id}.json"
        if not path.exists():
            raise ModuleExecutionError(f"fixture missing for {module_id}/{self.scenario}", module_id=module_id, scenario=self.scenario)
        return json.loads(path.read_text(encoding="utf-8"))
