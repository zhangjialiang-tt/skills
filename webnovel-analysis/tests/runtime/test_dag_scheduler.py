from pathlib import Path

import pytest

from runtime.dag import ExecutionDag
from runtime.errors import DagDependencyError
from runtime.module_registry import ModuleRegistry


ROOT = Path(__file__).parents[2]


def test_dag_and_module_registry_load_frozen_contracts() -> None:
    dag = ExecutionDag.load(ROOT / "references" / "execution-dag.yaml")
    registry = ModuleRegistry.load(ROOT / "references" / "internal-module-registry.yaml")

    assert dag.dependencies("S4") == ["S2"]
    assert dag.dependencies("S5") == ["S1", "S2", "S4"]
    assert registry.require("S2")["external_routeable"] is False
    with pytest.raises(KeyError):
        registry.require("UNKNOWN")


def test_dependency_check_rejects_unvalidated_input() -> None:
    dag = ExecutionDag.load(ROOT / "references" / "execution-dag.yaml")
    with pytest.raises(DagDependencyError):
        dag.assert_ready("S4", {"S2": "GENERATED"})
    dag.assert_ready("S4", {"S2": "VALIDATED"})
