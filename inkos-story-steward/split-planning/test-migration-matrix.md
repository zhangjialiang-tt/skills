# 测试迁移矩阵

> 基线: 99 tests @ e0d6736 (feature/novel-master)
> 状态: PLANNED — 迁移在 Phase 6 执行

---

## 处置类型

| 标记 | 含义 |
|------|------|
| MOVE_UNCHANGED | 原样迁移到新 Skill |
| MOVE_AND_ADAPT | 迁移并适配新路径/新模式名 |
| SPLIT | 拆分到多个 Skill |
| REPLACED | 被新契约测试替代 |
| OBSOLETE | 废弃（注明原因） |

---

## test_classify_path.py (15 tests)

| 测试 | 处置 | 新归属 |
|------|------|--------|
| test_green_author_intent | MOVE_UNCHANGED | inkos-project-steward |
| test_green_book_rules | MOVE_UNCHANGED | inkos-project-steward |
| test_green_roles | MOVE_UNCHANGED | inkos-project-steward |
| test_green_outline | MOVE_UNCHANGED | inkos-project-steward |
| test_yellow_pending_hooks | MOVE_UNCHANGED | inkos-project-steward |
| test_yellow_chapter | MOVE_UNCHANGED | inkos-project-steward |
| test_yellow_book_json | MOVE_UNCHANGED | inkos-project-steward |
| test_red_index_json | MOVE_UNCHANGED | inkos-project-steward |
| test_red_runtime | MOVE_UNCHANGED | inkos-project-steward |
| test_red_snapshots | MOVE_UNCHANGED | inkos-project-steward |
| test_red_memory_db | MOVE_UNCHANGED | inkos-project-steward |
| test_red_write_lock | MOVE_UNCHANGED | inkos-project-steward |
| test_unknown_books_path_defaults_yellow | MOVE_UNCHANGED | inkos-project-steward |
| test_runtime_backup_not_red | MOVE_UNCHANGED | inkos-project-steward |
| test_roles_backup_not_green | MOVE_UNCHANGED | inkos-project-steward |

新增（inkos-project-steward）：classify_extended 的 design_source/compiled_inkos/legacy_design 测试。

---

## test_collaboration_contract.py (6 tests)

| 测试 | 处置 | 新归属 |
|------|------|--------|
| test_minimal_request_and_result_are_aligned | SPLIT | serial-designer（Gate 协议）+ project-steward（建书后评审） |
| test_prebuild_has_three_candidate_checkpoints_and_no_stage4_gate | REPLACED | serial-designer 新 Gate A/B 测试 |
| test_postbuild_coach_is_exception_not_default | MOVE_AND_ADAPT | inkos-project-steward |
| test_compilation_mapping_covers_all_design_families | MOVE_AND_ADAPT | inkos-brief-compiler |
| test_creative_outputs_are_observable_in_story_outline | SPLIT | story-synopsis（梗概）+ serial-designer（连载设计） |
| test_story_diagnosis_has_seven_dimensions_and_stuck_taxonomy | MOVE_AND_ADAPT | webnovel-serial-designer |

---

## test_design_id.py (20 tests)

| 测试 | 处置 | 新归属 |
|------|------|--------|
| TestPrebuildInProject::test_empty_books_prebuild_in_project | MOVE_AND_ADAPT | inkos-project-steward（模式检测） |
| TestMultiBookNewDesign::test_new_design_does_not_touch_existing | MOVE_AND_ADAPT | inkos-project-steward |
| TestDesignConflict::test_existing_design_root_warning | MOVE_AND_ADAPT | inkos-project-steward |
| TestCompilePath::test_new_compile_path_in_workflow | MOVE_AND_ADAPT | inkos-brief-compiler |
| TestBookBinding::test_bound_manifest_active | MOVE_UNCHANGED | inkos-project-steward |
| TestBookCreationFailure::test_bound_book_not_found | MOVE_UNCHANGED | inkos-project-steward |
| TestFoundationAlignment::test_manifest_locates_design | MOVE_UNCHANGED | inkos-project-steward |
| TestDuplicateBinding::test_two_manifests_same_book | MOVE_UNCHANGED | inkos-project-steward |
| TestLegacyLayout::test_legacy_detected | MOVE_UNCHANGED | inkos-project-steward |
| TestPrebuildWriteBoundary::test_prebuild_blocks_books_write | SPLIT | serial-designer + compiler（各自边界） |
| TestPrebuildWriteBoundary::test_cross_design_blocked | MOVE_UNCHANGED | inkos-project-steward |
| TestDesignIdDerivation (6 tests) | MOVE_UNCHANGED | 共享模块或 inkos-project-steward |
| TestLifecycleTransitions (3 tests) | SPLIT | serial-designer（设计生命周期）+ project-steward（绑定生命周期） |

---

## test_pending_hooks_template.py (7 tests)

| 测试 | 处置 | 新归属 |
|------|------|--------|
| test_exactly_two_hooks | MOVE_UNCHANGED | inkos-brief-compiler |
| test_hook_ids_are_h001_h002 | MOVE_UNCHANGED | inkos-brief-compiler |
| test_no_fake_hooks_from_field_description | MOVE_UNCHANGED | inkos-brief-compiler |
| test_status_values_valid | MOVE_UNCHANGED | inkos-brief-compiler |
| test_payoff_timing_valid | MOVE_UNCHANGED | inkos-brief-compiler |
| test_promoted_semantics | MOVE_UNCHANGED | inkos-brief-compiler |
| test_13_columns | MOVE_UNCHANGED | inkos-brief-compiler |

---

## test_preflight.py (14 tests)

| 测试 | 处置 | 新归属 |
|------|------|--------|
| TestNoProject::test_no_project_prebuild_exit0 | MOVE_AND_ADAPT | inkos-project-steward |
| TestMultiBook::test_multi_book_no_id_exit1 | MOVE_UNCHANGED | inkos-project-steward |
| TestWriteLock::test_write_lock_exit1 | MOVE_UNCHANGED | inkos-project-steward |
| TestGitDirty::test_git_dirty_exit1 | MOVE_UNCHANGED | inkos-project-steward |
| TestNotGitRepo::test_not_git_repo_exit1 | MOVE_UNCHANGED | inkos-project-steward |
| TestInkosNotInstalled::test_inkos_not_installed_exit1 | MOVE_UNCHANGED | inkos-project-steward |
| TestJsonOutput::test_json_output_has_write_allowed | MOVE_UNCHANGED | inkos-project-steward |
| TestSingleBookAutoResolved::test_single_book_auto_resolved | MOVE_UNCHANGED | inkos-project-steward |
| TestChapterIndexConsistency (6 tests) | MOVE_UNCHANGED | inkos-project-steward |

新增（webnovel-serial-designer）：synopsis contract preflight 测试。
新增（inkos-brief-compiler）：serial contract preflight 测试。

---

## test_verify_diff.py (15 tests)

| 测试 | 处置 | 新归属 |
|------|------|--------|
| test_red_zone_always_blocked | MOVE_UNCHANGED | inkos-project-steward |
| test_allowed_green_passes | MOVE_UNCHANGED | inkos-project-steward |
| test_unauthorized_green_blocked | MOVE_UNCHANGED | inkos-project-steward |
| test_unauthorized_root_file_blocked | MOVE_UNCHANGED | inkos-project-steward |
| test_yellow_without_allow_yellow_blocked | MOVE_UNCHANGED | inkos-project-steward |
| test_yellow_with_allow_yellow_passes | MOVE_UNCHANGED | inkos-project-steward |
| test_enforce_no_allow_exit1 | MOVE_UNCHANGED | inkos-project-steward |
| test_directory_prefix_allow | MOVE_UNCHANGED | inkos-project-steward |
| test_prefix_collision_roles_backup | MOVE_UNCHANGED | inkos-project-steward |
| test_git_failure_exit1 | MOVE_UNCHANGED | inkos-project-steward |
| test_staged_and_untracked_detected | MOVE_UNCHANGED | inkos-project-steward |
| test_explicit_files_without_allow_blocked | MOVE_UNCHANGED | inkos-project-steward |
| test_diagnostic_yellow_exit0 | MOVE_UNCHANGED | inkos-project-steward |
| test_diagnostic_red_exit1 | MOVE_UNCHANGED | inkos-project-steward |
| test_diagnostic_no_allow_needed | MOVE_UNCHANGED | inkos-project-steward |

新增（inkos-brief-compiler）：verify_compile_diff 只允许写 compile/inkos/ 测试。

---

## test_verify_runtime_context.py (22 tests)

| 测试 | 处置 | 新归属 |
|------|------|--------|
| 全部 22 个测试 | MOVE_UNCHANGED | inkos-project-steward |

---

## 汇总

| 新 Skill | 迁移测试数 | 新增测试需求 |
|----------|--------:|----------|
| inkos-project-steward | ~70 | classify_extended, 新模式名 |
| inkos-brief-compiler | ~8 | preflight, compile diff, mapping 覆盖率 |
| webnovel-serial-designer | ~4 | synopsis preflight, Gate A/B, assertion 生成 |
| story-synopsis | ~2 | contract 生成, handoff_ready |
| 共享 (design_id) | ~9 | — |

---

## 迁移规则

1. 任何测试删除必须在本文档中标注替代测试
2. MOVE_AND_ADAPT 只允许修改路径和模式名，不允许弱化断言
3. SPLIT 必须产生至少两个替代测试
4. REPLACED 必须说明新测试覆盖了旧测试的哪些行为
5. 迁移完成后运行全量套件，通过数 ≥ 99
