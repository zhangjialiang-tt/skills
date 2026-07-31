"""Regression tests for the thin Steward/Coach collaboration contract."""

from pathlib import Path


STEWARD_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = STEWARD_ROOT.parent
STEWARD_SKILL = STEWARD_ROOT / "SKILL.md"
COACH_SKILL = WORKSPACE_ROOT / "novel-coach" / "SKILL.md"
PREBUILD = STEWARD_ROOT / "references" / "prebuild-workflow.md"
GREEN_ZONE = STEWARD_ROOT / "references" / "green-zone-editing.md"
COMPILATION = STEWARD_ROOT / "references" / "design-to-inkos-compilation.md"
STORY_OUTLINE = STEWARD_ROOT / "templates" / "story-outline.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_minimal_request_and_result_are_aligned():
    for path in (STEWARD_SKILL, COACH_SKILL):
        text = _read(path)
        for required in (
            "stage: story_promise | plot_structure | final_readiness | postbuild_diagnosis",
            "artifacts:",
            "focus:",
            "frozen_decisions:",
            "verdict: pass | revise | block",
            "severity: blocking | major | minor",
            "problem:",
            "recommendation:",
        ):
            assert required in text, f"{path.name} missing contract field: {required}"
        for forbidden in (
            "review_id:",
            "artifact_refs:",
            "review_focus:",
            "open_questions:",
            "permissions:",
        ):
            assert forbidden not in text, f"{path.name} retains heavy field: {forbidden}"


def test_prebuild_has_three_candidate_checkpoints_and_no_stage4_gate():
    text = _read(PREBUILD)
    assert "只在以下 3 个节点" in text
    assert "PREBUILD 全程最多调用 Coach 3 次" in text
    assert text.count("stage: ") == 3
    assert "stage: story_promise" in text
    assert "stage: plot_structure" in text
    assert "stage: final_readiness" in text
    assert "阶段 4：人物系统" in text
    assert "本阶段不单独调用 Coach" in text
    assert "检查点 2：整体结构质量评审" in text
    assert "world_character" not in text
    assert "Gate 4" not in text


def test_postbuild_coach_is_exception_not_default():
    text = _read(GREEN_ZONE)
    assert "普通绿区规则补充不调用 Coach" in text
    assert "核心目标、核心冲突、结局、整卷结构发生重大变化" in text
    assert "作者接受、拒绝或带风险接受" in _read(STEWARD_SKILL)


def test_compilation_mapping_covers_all_design_families():
    text = _read(COMPILATION)
    for source in (
        "00-project-brief.md",
        "02-world-system.md",
        "03-character-system.md",
        "04-conflict-engine.md",
        "05-plot-architecture.md",
        "06-payoff-system.md",
        "07-foreshadowing-and-mystery.md",
        "08-volume-outline.md",
        "09-story-outline.md",
        "10-readiness-review.md",
    ):
        assert source in text
    for target in (
        "author_intent.md",
        "story_frame.md",
        "book_rules.md",
        "roles/**",
        "volume_map.md",
        "pending_hooks.md",
    ):
        assert target in text
    assert "不得补造" in text
    assert "`mapped`" in text
    assert "`design-only`" in text
    assert "`blocked`" in text


def test_creative_outputs_are_observable_in_story_outline():
    text = _read(STORY_OUTLINE)
    for marker in (
        "主角主动选择",
        "对手/配角行动",
        "三层代价升级",
        "知识边界",
        "下一步行动",
        "下一轮期待",
        "错误解释",
        "回收条件",
        "意义反转",
    ):
        assert marker in text


def test_story_diagnosis_has_seven_dimensions_and_stuck_taxonomy():
    text = _read(GREEN_ZONE)
    assert "固定诊断七项" in text
    for dimension in (
        "promise_drift",
        "protagonist_agency",
        "payoff_repetition",
        "hook_decay",
        "inactive_character",
        "next_volume_escalation",
        "stuck_cause",
    ):
        assert dimension in text
    for cause in ("information_missing", "conflict_missing", "choice_missing"):
        assert cause in text
    assert "诊断本身只读" in text
