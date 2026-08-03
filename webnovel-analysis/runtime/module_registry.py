from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ModuleRegistry:
    modules: dict[str, dict]

    @classmethod
    def load(cls, path: Path) -> "ModuleRegistry":
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        entries = [*data["modules"], *data.get("internal_stages", [])]
        return cls({entry["id"]: dict(entry) for entry in entries})

    def require(self, module_id: str) -> dict:
        if module_id not in self.modules:
            raise KeyError(module_id)
        return dict(self.modules[module_id])
