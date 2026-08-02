from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


def test_milestone_one_dependencies_are_frozen() -> None:
    dag = yaml.safe_load((ROOT / "references" / "execution-dag.yaml").read_text(encoding="utf-8"))
    assert dag["parallel_groups"]["primary_analysis"] == ["S1", "S2", "S3"]
    assert dag["dependencies"]["S4"] == ["S2"]
    assert dag["dependencies"]["S5"] == ["S1", "S2", "S4"]
    assert dag["dependencies"]["S6"] == ["S1", "S2", "S3", "S4", "S5"]
    assert dag["dependencies"]["Q0"] == ["S6"]
    assert dag["dependencies"]["R0"] == ["Q0"]


def test_execution_graph_is_acyclic() -> None:
    dependencies = yaml.safe_load((ROOT / "references" / "execution-dag.yaml").read_text(encoding="utf-8"))["dependencies"]
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise AssertionError(f"cycle detected at {node}")
        if node in visited:
            return
        visiting.add(node)
        for dependency in dependencies.get(node, []):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in dependencies:
        visit(node)

