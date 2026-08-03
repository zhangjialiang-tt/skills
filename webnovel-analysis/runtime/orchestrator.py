import json
import shutil
from pathlib import Path

import yaml

from .adapters import FixtureAdapter
from .artifact_store import ArtifactStore
from .dag import ExecutionDag
from .errors import DeliverableIncompleteError, GateBlockedError, ModuleOutputSchemaError, ReviewRequiredError
from .gates import evaluate_gate_a, evaluate_gate_b
from .invalidation import invalidate_target_and_direct_dependents
from .module_executor import ModuleExecutor
from .module_registry import ModuleRegistry
from .registry import ArtifactRegistry
from .schema_validator import SchemaValidator
from .state import BatchState, TaskState, utc_now


OPERATIONS = {
    "O0": "plan", "S0": "preprocess", "S1": "analyze", "S2": "analyze", "S3": "analyze",
    "S4": "analyze", "S5": "analyze", "S6": "aggregate", "Q0": "audit",
    "S7": "design_visualization", "S8": "derive_formula", "S9": "genre_specific_template", "R0": "render_final_report",
}


class RuntimeOrchestrator:
    def __init__(self, *, package_root: Path, runs_root: Path | None = None) -> None:
        self.package_root = Path(package_root).resolve()
        self.runs_root = Path(runs_root or self.package_root / "runs").resolve()
        self.dag = ExecutionDag.load(self.package_root / "references" / "execution-dag.yaml")
        self.modules = ModuleRegistry.load(self.package_root / "references" / "internal-module-registry.yaml")
        self.validator = SchemaValidator(self.package_root / "schemas")

    def task_root(self, task_id: str) -> Path:
        return self.runs_root / task_id

    def registry(self, task_id: str) -> ArtifactRegistry:
        return ArtifactRegistry(self.task_root(task_id) / "registry.json")

    def create_task(self, request_path: Path) -> TaskState:
        request_path = Path(request_path).resolve()
        request = yaml.safe_load(request_path.read_text(encoding="utf-8"))
        self.validator.validate_runtime("run-request.schema.json", request)
        root = self.task_root(request["task_id"])
        root.mkdir(parents=True, exist_ok=False)
        source_path = (request_path.parent / request["source"]).resolve()
        (root / "source").mkdir()
        shutil.copy2(source_path, root / "source" / "source.md")
        task = TaskState.new(task_id=request["task_id"], book_id=request["book_id"], source_ref="source/source.md", batch_id=request["batch_id"])
        batch = BatchState.new(task_id=request["task_id"], batch_id=request["batch_id"], chapter_ids=request["chapter_ids"])
        self._save_states(task, batch)
        ArtifactRegistry(root / "registry.json").path.write_text('{"artifacts": []}\n', encoding="utf-8")
        (root / "reviews").mkdir()
        (root / "reviews" / "pending.json").write_text("[]\n", encoding="utf-8")
        (root / "reviews" / "decisions.jsonl").write_text("", encoding="utf-8")
        (root / "execution-log.jsonl").write_text("", encoding="utf-8")
        self._log(task.task_id, "TASK_CREATED")
        return task

    def load_states(self, task_id: str) -> tuple[TaskState, BatchState]:
        root = self.task_root(task_id)
        task = TaskState.from_dict(yaml.safe_load((root / "task.yaml").read_text(encoding="utf-8")))
        batch = BatchState.from_dict(yaml.safe_load((root / "batch.yaml").read_text(encoding="utf-8")))
        return task, batch

    def _save_states(self, task: TaskState, batch: BatchState) -> None:
        root = self.task_root(task.task_id)
        root.mkdir(parents=True, exist_ok=True)
        self.validator.validate_runtime("task-state.schema.json", task.to_dict())
        self.validator.validate_runtime("batch-state.schema.json", batch.to_dict())
        (root / "task.yaml").write_text(yaml.safe_dump(task.to_dict(), allow_unicode=True, sort_keys=False), encoding="utf-8")
        (root / "batch.yaml").write_text(yaml.safe_dump(batch.to_dict(), allow_unicode=True, sort_keys=False), encoding="utf-8")

    def _log(self, task_id: str, event: str, **details: object) -> None:
        record = {"at": utc_now(), "event": event, **details}
        with (self.task_root(task_id) / "execution-log.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _scope(self, module_id: str, batch_id: str) -> str:
        if module_id == "O0":
            return "TASK"
        if module_id in {"S7", "S8", "S9", "R0"}:
            return "BOOK"
        return batch_id

    def _execute(
        self,
        task: TaskState,
        batch: BatchState,
        module_id: str,
        executor: ModuleExecutor,
        *,
        replaces: str | None = None,
        extra_dependencies: tuple[str, ...] = (),
    ) -> dict:
        self.modules.require(module_id)
        registry = executor.registry
        dependency_records = []
        statuses = {}
        dependencies = list(dict.fromkeys([*self.dag.dependencies(module_id), *extra_dependencies]))
        for dependency in dependencies:
            record = registry.latest(dependency, self._scope(dependency, batch.batch_id))
            dependency_records.append(record)
            statuses[dependency] = record["status"]
        self.dag.assert_ready(module_id, statuses)
        inputs = {record["module_id"]: executor.store.read(record) for record in dependency_records}
        record = executor.execute(
            task_id=task.task_id,
            batch_id=self._scope(module_id, batch.batch_id),
            module_id=module_id,
            operation=OPERATIONS[module_id],
            input_payload=inputs,
            input_artifact_ids=[record["artifact_id"] for record in dependency_records],
            replaces_artifact_id=replaces,
        )
        self._log(task.task_id, "MODULE_VALIDATED", module_id=module_id, artifact_id=record["artifact_id"])
        return record

    def _executor(self, task_id: str, scenario: str) -> ModuleExecutor:
        root = self.task_root(task_id)
        return ModuleExecutor(
            store=ArtifactStore(root),
            registry=ArtifactRegistry(root / "registry.json"),
            validator=self.validator,
            adapter=FixtureAdapter(self.package_root / "tests" / "fixtures" / "runtime" / "module-outputs", scenario=scenario),
        )

    def run_batch(self, task_id: str, batch_id: str, *, scenario: str = "valid") -> BatchState:
        task, batch = self.load_states(task_id)
        if batch.batch_id != batch_id:
            raise KeyError(batch_id)
        if task.status != "RUNNING":
            task.transition("RUNNING")
        if batch.status != "RUNNING":
            batch.transition("RUNNING", current_stage="O0")
        self._save_states(task, batch)
        executor = self._executor(task_id, scenario)
        try:
            self._execute(task, batch, "O0", executor)
            s0 = self._execute(task, batch, "S0", executor)
            decision_a = evaluate_gate_a(executor.store.read(s0))
            self._write_decision(task_id, batch_id, "gate-a.yaml", decision_a)
            if decision_a.decision == "BLOCKED":
                batch.blocking_issue_ids = [issue.get("issue_id", issue.get("code", "GATE-A")) for issue in decision_a.blocking_issues]
                batch.transition("BLOCKED", current_stage="GATE_A")
                task.transition("BLOCKED")
                self._save_states(task, batch)
                raise GateBlockedError("Gate A blocked the batch", task_id=task_id, batch_id=batch_id)
            for module_id in ("S1", "S2", "S3", "S4", "S5", "S6", "Q0"):
                batch.current_stage = module_id
                self._execute(task, batch, module_id, executor)
            batch.transition("AUDITING", current_stage="GATE_B")
            q0 = executor.registry.latest("Q0", batch_id, usable_only=True)
            decision_b = evaluate_gate_b(executor.store.read(q0))
            self._write_decision(task_id, batch_id, "gate-b.yaml", decision_b)
            self._write_pending(task_id, decision_b.review_items)
            batch.review_item_ids = [item["review_id"] for item in decision_b.review_items]
            if decision_b.decision == "BLOCKED":
                batch.blocking_issue_ids = [issue["issue_id"] for issue in decision_b.blocking_issues]
                batch.transition("BLOCKED")
                task.transition("BLOCKED")
                self._save_states(task, batch)
                raise GateBlockedError("Gate B found an open P0", task_id=task_id, batch_id=batch_id)
            if decision_b.decision == "AWAITING_HUMAN":
                batch.transition("AWAITING_HUMAN")
                task.transition("AWAITING_HUMAN")
            else:
                batch.transition("ACCEPTED")
            self._save_states(task, batch)
            return batch
        except ModuleOutputSchemaError as error:
            batch.transition("BLOCKED", current_stage=error.context.get("module_id"))
            task.transition("BLOCKED")
            task.failure = {"code": error.code, "message": str(error)}
            self._save_states(task, batch)
            self._log(task_id, "MODULE_FAILED", module_id=error.context.get("module_id"), code=error.code)
            raise

    def _write_decision(self, task_id: str, batch_id: str, name: str, decision) -> None:
        root = self.task_root(task_id) / "decisions"
        root.mkdir(exist_ok=True)
        gate_label = name.removesuffix(".yaml").upper()
        value = {"gate_id": f"{gate_label}-{batch_id}", "decision": decision.decision, "blocking_issues": decision.blocking_issues, "review_items": decision.review_items, "decided_by": "automatic-policy"}
        (root / name).write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def _write_pending(self, task_id: str, reviews: list[dict]) -> None:
        (self.task_root(task_id) / "reviews" / "pending.json").write_text(json.dumps(reviews, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def pending_reviews(self, task_id: str) -> list[dict]:
        return json.loads((self.task_root(task_id) / "reviews" / "pending.json").read_text(encoding="utf-8"))

    def submit_review(self, task_id: str, review_id: str, decision: str, *, reason: str, reviewer: str = "user") -> None:
        pending = self.pending_reviews(task_id)
        item = next((review for review in pending if review["review_id"] == review_id), None)
        if item is None:
            raise ReviewRequiredError(f"pending review not found: {review_id}")
        if decision not in {"ACCEPT", "REJECT_AND_RERUN", "ACCEPT_WITH_RISK"}:
            raise ReviewRequiredError(f"unsupported review decision: {decision}")
        record = {"review_id": review_id, "decision": decision, "reason": reason, "reviewer": reviewer, "decided_at": utc_now()}
        if item.get("target_module"):
            record["target_module"] = item["target_module"]
        self.validator.validate_runtime("review-decision.schema.json", record)
        with (self.task_root(task_id) / "reviews" / "decisions.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        item["status"] = "RESOLVED"
        item["decision"] = decision
        self._write_pending(task_id, pending)
        task, batch = self.load_states(task_id)
        if decision in {"ACCEPT", "ACCEPT_WITH_RISK"} and not any(review["blocking"] and review["status"] == "PENDING" for review in pending):
            batch.transition("ACCEPTED")
            task.transition("RUNNING")
            self._save_states(task, batch)
        elif decision == "REJECT_AND_RERUN":
            self.rerun(task_id, batch.batch_id, item["target_module"], scenario="corrected")

    def rerun(self, task_id: str, batch_id: str, module_id: str, *, scenario: str = "corrected") -> BatchState:
        if module_id not in {"S1", "S2", "S3", "S4", "S5"}:
            raise KeyError(f"Milestone 2 rerun does not support {module_id}")
        task, batch = self.load_states(task_id)
        registry = self.registry(task_id)
        old_target = registry.latest(module_id, batch_id, usable_only=True)
        direct = set(invalidate_target_and_direct_dependents(
            registry=registry,
            dag=self.dag,
            module_id=module_id,
            batch_id=batch_id,
            invalidated_by=f"RERUN-{module_id}-R{old_target['revision'] + 1}",
        ))
        executor = self._executor(task_id, scenario)
        if batch.status != "RUNNING":
            batch.transition("RUNNING", current_stage=module_id)
        if task.status != "RUNNING":
            task.transition("RUNNING")
        rerun_modules: set[str] = set()
        order = ["S1", "S2", "S3", "S4", "S5", "S6", "Q0"]
        for candidate in order[order.index(module_id):]:
            dependencies_changed = any(dependency in rerun_modules for dependency in self.dag.dependencies(candidate))
            if candidate != module_id and candidate not in direct and not dependencies_changed:
                continue
            try:
                old = executor.registry.latest(candidate, batch_id)
            except Exception as error:
                if getattr(error, "code", None) == "ARTIFACT_NOT_FOUND":
                    old = None
                else:
                    raise
            if old and old["status"] != "INVALIDATED":
                executor.registry.invalidate(old["artifact_id"], invalidated_by=f"RERUN-{module_id}")
            batch.current_stage = candidate
            self._execute(task, batch, candidate, executor, replaces=old["artifact_id"] if old else None)
            rerun_modules.add(candidate)
        batch.transition("AUDITING", current_stage="GATE_B")
        q0 = executor.registry.latest("Q0", batch_id, usable_only=True)
        gate_b = evaluate_gate_b(executor.store.read(q0))
        self._write_decision(task_id, batch_id, "gate-b.yaml", gate_b)
        self._write_pending(task_id, gate_b.review_items)
        if gate_b.decision == "BLOCKED":
            batch.transition("BLOCKED")
            task.transition("BLOCKED")
        elif gate_b.decision == "AWAITING_HUMAN":
            batch.transition("AWAITING_HUMAN")
            task.transition("AWAITING_HUMAN")
        else:
            batch.transition("ACCEPTED")
        self._save_states(task, batch)
        return batch

    def finalize(self, task_id: str, gate_c_decision_path: Path, *, scenario: str = "valid") -> Path:
        task, batch = self.load_states(task_id)
        if batch.status != "ACCEPTED" or task.status in {"BLOCKED", "AWAITING_HUMAN", "FAILED"}:
            raise DeliverableIncompleteError(
                "batch must be accepted before finalization",
                task_id=task_id,
                batch_id=batch.batch_id,
                task_status=task.status,
                batch_status=batch.status,
            )
        decision = yaml.safe_load(Path(gate_c_decision_path).read_text(encoding="utf-8"))
        if decision.get("decision") != "ACCEPTED":
            raise DeliverableIncompleteError("Gate C test decision is not accepted", task_id=task_id, batch_id=batch.batch_id)
        decisions_dir = self.task_root(task_id) / "decisions"
        decisions_dir.mkdir(exist_ok=True)
        (decisions_dir / "gate-c-test-acceptance.yaml").write_text(
            yaml.safe_dump(decision, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        executor = self._executor(task_id, scenario)
        s7 = self._execute(task, batch, "S7", executor)
        s8 = self._execute(task, batch, "S8", executor)
        s9 = self._execute(task, batch, "S9", executor, extra_dependencies=("S8",))
        r0 = self._execute(task, batch, "R0", executor, extra_dependencies=("S6", "S7", "S8", "S9"))
        r0_output = executor.store.read(r0)
        r0_dir = self.task_root(task_id) / "artifacts" / "BOOK" / "R0" / f"r{r0['revision']}"
        report_path = r0_dir / "analysis_report.md"
        report_path.write_text(r0_output["payload"]["analysis_report_md"], encoding="utf-8")
        s6 = executor.registry.latest("S6", batch.batch_id, usable_only=True)
        q0 = executor.registry.latest("Q0", batch.batch_id, usable_only=True)
        manifest = {
            "task_id": task_id,
            "book_id": task.book_id,
            "status": "DELIVERABLE_READY",
            "deliverables": [
                {"type": "reverse_outline", "artifact_ref": s6["artifact_id"]},
                {"type": "emotion_payoff_visualization", "artifact_ref": s7["artifact_id"]},
                {"type": "genre_formula", "artifact_ref": s8["artifact_id"]},
                {"type": "chapter_template", "artifact_ref": s9["artifact_id"]},
                {"type": "final_report", "artifact_ref": r0["artifact_id"], "path": "analysis_report.md"},
            ],
            "audit_artifact_ref": q0["artifact_id"],
        }
        manifest_path = r0_dir / "deliverable-manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        task.transition("DELIVERABLE_READY")
        batch.current_stage = "R0"
        self._save_states(task, batch)
        self._log(task_id, "DELIVERABLE_READY", manifest_path=str(manifest_path.relative_to(self.task_root(task_id))))
        return manifest_path
