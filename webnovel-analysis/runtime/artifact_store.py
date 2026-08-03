import json
from pathlib import Path


class ArtifactStore:
    def __init__(self, task_root: Path) -> None:
        self.task_root = Path(task_root)

    def _revision_dir(self, record: dict) -> Path:
        return self.task_root / "artifacts" / record["batch_id"] / record["module_id"] / f"r{record['revision']}"

    def write_raw(self, record: dict, output: dict) -> Path:
        path = self._revision_dir(record) / "raw-output.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def write_validated(self, record: dict, output: dict) -> Path:
        path = self.task_root / record["file_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def read(self, record: dict) -> dict:
        return json.loads((self.task_root / record["file_path"]).read_text(encoding="utf-8"))
