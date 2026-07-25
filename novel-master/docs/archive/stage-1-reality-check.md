# v1.3.0 启动前确认报告

> 基线：v1.2.0 冻结文档 + 168 条测试（2026-07-25）

## 1. file-ownership.md 所有权确认

| 区域 | 写入者 | v1.3 新文件归属 |
| --- | --- | --- |
| `architecture/story_engine.md` | STORY | ✅ architecture/ |
| `architecture/project_spine.md` | STORY | ✅ architecture/ |
| `outline/volume_index.md` | PLOT | ✅ outline/ |
| `outline/volumes/volume_*.md` | PLOT | ✅ outline/（需更新 PLOT 标准文件名列表） |
| `outline/arc_index.md` | PLOT | ✅ outline/ |
| `outline/arcs/arc_*.md` | PLOT | ✅ outline/（需更新 PLOT 标准文件名列表） |
| `chapters/batches/batch_*.md` | chapter-planner | ✅ chapters/（需更新 file-ownership.md） |
| `workflow/plan_progress.md` | novel-master | ✅ workflow/ |

**待修**：`file-ownership.md` 需增加 `chapters/batches/` 归属 chapter-planner；PLOT 标准文件名需增加 volume_*.md、arc_*.md、volume_index.md、arc_index.md。

## 2. PLOT scope / task type 枚举

当前 task type enum：`INIT_PROJECT, REFINE_BRIEF, DESIGN_STORY, DESIGN_CHARACTER, DESIGN_WORLD, PLAN_PLOT, PLAN_VOLUME, PLAN_CHAPTER, WRITE_CHAPTER, CONTINUE_CHAPTER, REVIEW_TEXT, EDIT_TEXT, CHECK_CONTINUITY, UPDATE_CANON, RETCON, RESUME_PROJECT, BRAINSTORM, SUMMARIZE_STATE`

当前 scope enum：`SNIPPET, SCENE, CHAPTER, MULTI_CHAPTER, VOLUME, ARC, PROJECT, FULL`

v1.3 影响：
- 新增 task type `CHECK_PLAN_PROGRESS`
- 重规划复用 `PLAN_PLOT + scope: ARC` / `PLAN_VOLUME + scope: VOLUME`
- scope ARC/VOLUME 已存在，无需新增

## 3. review-dimensions 当前枚举

4 个维度：`CONTRACT_COMPLIANCE, NARRATIVE_SOUNDNESS, READER_EXPERIENCE, CRAFT_EXECUTION`

v1.3 新增 `PLAN_ALIGNMENT` → 5 个维度。

## 4. approval-ref operation 枚举

当前：`COMMIT_CANON, RETCON, EDIT_L3, EDIT_L4, ACCEPT_CHAPTER, INIT_PROJECT`

v1.3 需增加：`REPLAN_ARC, REPLAN_VOLUME`

## 5. v1.2 冻结文档原路径依赖

| 文件 | 引用 | 操作 |
| --- | --- | --- |
| `AGENTS.md` L37, L167–168 | `v1.1.0-frozen` | 更新为 v1.2.0-frozen |
| `chapter-planner/SKILL.md` L124 | `v1.1.0-frozen` | 更新为 v1.2.0-frozen |
| `continuity-keeper/SKILL.md` L136 | `v1.1.0-frozen` | 更新为 v1.2.0-frozen |
| `chapter-writer/SKILL.md` L112 | `v1.1.0-frozen` | 更新为 v1.2.0-frozen |
| `novel-reviewer/SKILL.md` L108 | `v1.1.0-frozen` | 更新为 v1.2.0-frozen |
