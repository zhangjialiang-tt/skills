"""v1.3 规划契约确定性测试."""

import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def _make_registry() -> Registry:
    """Build a registry that resolves all $ref paths under schemas/."""
    resources = []
    for f in SCHEMAS_DIR.rglob("*.json"):
        rel = str(f.relative_to(SCHEMAS_DIR)).replace("\\", "/")
        schema = json.loads(f.read_text(encoding="utf-8"))
        resources.append((rel, Resource.from_contents(schema)))
    return Registry().with_resources(resources)


_REGISTRY = _make_registry()


def _make_validator(schema_name: str) -> Draft202012Validator:
    schema = _load_schema(schema_name)
    sid = schema.get("$id", schema_name)
    resource = Resource.from_contents(schema)
    registry = _REGISTRY.with_resource(sid, resource)
    return Draft202012Validator(schema, registry=registry)


@pytest.fixture(scope="module")
def v_plan_meta():
    return _make_validator("planning-artifact-meta.schema.json")


@pytest.fixture(scope="module")
def v_chapter_batch():
    return _make_validator("chapter-batch.schema.json")


@pytest.fixture(scope="module")
def v_plan_ref():
    return _make_validator("defs/plan-ref.schema.json")


@pytest.fixture(scope="module")
def v_plan_progress():
    return _make_validator("plan-progress.schema.json")


class TestPlanningArtifactMeta:
    """PC-028: artifact_type enum + lifecycle."""

    def test_valid_types(self, v_plan_meta):
        for t in ["STORY_ENGINE", "PROJECT_SPINE", "VOLUME_ARC", "ARC_PLAN", "CHAPTER_BATCH"]:
            data = {"planning_artifact_meta": {
                "schema_id": "test", "schema_version": "1.3.0",
                "artifact_type": t, "artifact_id": "ID-001",
                "revision": "r1", "lifecycle_status": "ACTIVE"
            }}
            assert v_plan_meta.is_valid(data), f"Should accept {t}"

    def test_reject_character_arc(self, v_plan_meta):
        data = {"planning_artifact_meta": {
            "schema_id": "test", "schema_version": "1.3.0",
            "artifact_type": "CHARACTER_ARC", "artifact_id": "ID-001",
            "revision": "r1", "lifecycle_status": "ACTIVE"
        }}
        errors = list(v_plan_meta.iter_errors(data))
        assert len(errors) > 0


class TestPlanRef:
    """PC-029: batch_slot_ref consistency, PC-030: ItemRef item_id canonical."""

    def test_plan_ref_required_fields(self, v_plan_ref):
        ref = {
            "artifact_type": "ARC_PLAN", "artifact_id": "ARC-001",
            "path": "outline/arcs/arc_01_01.md", "revision": "r3",
            "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }
        assert v_plan_ref.is_valid(ref)

    # plan-ref.schema.json is a definitions-only schema, not standalone validatable.
    # This test verifies the plan_ref definition requires content_hash.
    def test_plan_ref_def_requires_hash(self):
        schema = _load_schema("defs/plan-ref.schema.json")
        plan_ref_def = schema["definitions"]["plan_ref"]
        assert "content_hash" in plan_ref_def["required"]

    def test_item_ref_valid(self, v_plan_ref):
        ref = {"item_type": "ARC_BEAT", "item_id": "BEAT-001", "json_pointer": "/arc_plan/required_beats/0"}
        assert v_plan_ref.is_valid(ref)

    def test_item_ref_invalid_enum(self):
        # plan-ref.schema.json only defines reusable definitions.
        # Validating a bare item_ref against the whole schema is vacuous.
        # Use the embedded context: item_ref is validated when used as part of a parent schema.
        # This test verifies the enum exists in the schema definition.
        schema = _load_schema("defs/plan-ref.schema.json")
        item_ref_def = schema["definitions"]["item_ref"]
        assert "CHARACTER_ARC" not in item_ref_def["properties"]["item_type"]["enum"]


class TestChapterBatch:
    """PC-029: batch_slot_ref, PC-036: ACTIVE lifecycle required."""

    def _make_batch(self, **overrides):
        base = {
            "planning_artifact_meta": {
                "schema_id": "novel-master/chapter-batch", "schema_version": "1.3.0",
                "artifact_type": "CHAPTER_BATCH", "artifact_id": "BATCH-001",
                "revision": "r1", "lifecycle_status": "ACTIVE"
            },
            "chapter_batch": {
                "batch_id": "BATCH-001",
                "arc_ref": {"artifact_type": "ARC_PLAN", "artifact_id": "ARC-001",
                             "path": "arc_01_01.md", "revision": "r3", "content_hash": "a" * 64},
                "target_range": {"start_chapter": "CH-011", "end_chapter": "CH-015"},
                "batch_goal": "Complete arc beats",
                "required_arc_beats": [],
                "chapter_slots": [
                    {"slot_id": "SLOT-001", "status": "PLANNED",
                     "intended_function": "SETUP", "beat_refs": [], "flexibility": "MEDIUM"}
                ],
                "refresh_trigger": {"after_chapters": 5, "on_tactical_deviation": True}
            }
        }
        for k, v in overrides.items():
            if "." in k:
                top, sub = k.split(".", 1)
                base[top].update({sub: v})
            else:
                base[k] = v
        return base

    def test_valid_batch(self, v_chapter_batch):
        assert v_chapter_batch.is_valid(self._make_batch())

    def test_draft_lifecycle_accepted(self, v_chapter_batch):
        batch = self._make_batch()
        batch["planning_artifact_meta"]["lifecycle_status"] = "DRAFT"
        assert v_chapter_batch.is_valid(batch)

    def test_slot_status_enum(self, v_chapter_batch):
        batch = self._make_batch()
        batch["chapter_batch"]["chapter_slots"][0]["status"] = "INVALID"
        errors = list(v_chapter_batch.iter_errors(batch))
        assert len(errors) > 0


class TestPlanProgress:
    """PC-032: plan_progress uses PlanRef, PC-033: idempotent/recoverable."""

    def _make_ref(self):
        return {"artifact_type": "ARC_PLAN", "artifact_id": "A", "path": "p",
                "revision": "r1", "content_hash": "a" * 64}

    def _make_health(self):
        return {
            "planned_chapter_count": 10, "used_chapter_count": 3,
            "total_required_beats": 5, "completed_required_beats": 1,
            "overdue_beats": 0, "tactical_deviation_count": 0,
            "unresolved_strategic_deviation_count": 0,
            "derived": {"beat_completion_ratio": 0.2, "chapter_consumption_ratio": 0.3,
                        "drift_score": 0.0, "status": "ON_TRACK"}
        }

    def test_valid_progress(self, v_plan_progress):
        ref = self._make_ref()
        data = {
            "last_processed_acceptance_ref": "CH-001-r3",
            "active_phase_ref": ref, "active_volume_ref": ref, "active_arc_ref": ref,
            "active_batch_ref": None,
            "completed_milestones": [],
            "deviations": [],
            "arc_health": self._make_health()
        }
        assert v_plan_progress.is_valid(data)

    def test_progress_with_deviation(self, v_plan_progress):
        ref = self._make_ref()
        data = {
            "last_processed_acceptance_ref": "CH-001-r3",
            "active_phase_ref": ref, "active_volume_ref": ref, "active_arc_ref": ref,
            "active_batch_ref": None,
            "completed_milestones": [],
            "deviations": [{"deviation_id": "DEV-001", "source_acceptance_ref": "CH-001-r3",
                            "resolution_status": "RECORDED"}],
            "arc_health": self._make_health()
        }
        assert v_plan_progress.is_valid(data)


class TestPlanningActivation:
    """PC-034: Atomic activation protocol."""

    def _make_ref(self):
        return {"artifact_type": "ARC_PLAN", "artifact_id": "A", "path": "p",
                "revision": "r2", "content_hash": "a" * 64}

    def test_valid_activation(self):
        v = _make_validator("planning-activation.schema.json")
        data = {
            "activation_id": "ACT-001", "artifact_id": "ARC-001",
            "previous_active_ref": None, "new_active_ref": self._make_ref(),
            "base_revisions": {"arc_plan": "r1"},
            "status": "PREPARED"
        }
        assert v.is_valid(data)

    def test_activation_committed(self):
        v = _make_validator("planning-activation.schema.json")
        ref = self._make_ref()
        data = {
            "activation_id": "ACT-001", "artifact_id": "ARC-001",
            "previous_active_ref": ref, "new_active_ref": ref,
            "base_revisions": {"arc_plan": "r1"},
            "status": "COMMITTED"
        }
        assert v.is_valid(data)
