from pathlib import Path

from runtime.orchestrator import RuntimeOrchestrator


ROOT = Path(__file__).parents[2]


def create_runtime(tmp_path: Path) -> RuntimeOrchestrator:
    runtime = RuntimeOrchestrator(package_root=ROOT, runs_root=tmp_path / "runs")
    runtime.create_task(ROOT / "examples" / "mini-urban-rebirth" / "request.yaml")
    return runtime
