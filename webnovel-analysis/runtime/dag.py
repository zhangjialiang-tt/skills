from dataclasses import dataclass
from pathlib import Path

import yaml

from .errors import DagDependencyError


@dataclass(frozen=True)
class ExecutionDag:
    dependency_map: dict[str, list[str]]

    @classmethod
    def load(cls, path: Path) -> "ExecutionDag":
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls({key: list(value or []) for key, value in data["dependencies"].items()})

    def dependencies(self, module_id: str) -> list[str]:
        if module_id not in self.dependency_map:
            raise KeyError(module_id)
        return list(self.dependency_map[module_id])

    def direct_dependents(self, module_id: str) -> list[str]:
        return [node for node, dependencies in self.dependency_map.items() if module_id in dependencies]

    def assert_ready(self, module_id: str, dependency_statuses: dict[str, str]) -> None:
        unavailable = [dependency for dependency in self.dependencies(module_id) if dependency_statuses.get(dependency) not in {"VALIDATED", "ACCEPTED"}]
        if unavailable:
            raise DagDependencyError(
                f"{module_id} dependencies are not validated: {', '.join(unavailable)}",
                module_id=module_id,
                dependencies=unavailable,
            )
