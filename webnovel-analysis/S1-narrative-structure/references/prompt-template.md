# S1 叙事结构拆解 — 完整 Prompt 模板

> Milestone 1 规范：本模块仅由根 Skill 内部调用。完整输出必须遵循 `../../references/model-output-contract.md` 与 `../../schemas/modules/S1.schema.json`；下方旧示例仅作为 `payload` 字段语义参考。

## 输入格式

```yaml
mode: 【incremental/consolidation】
task_manifest: 【O0输出】
chapter_index: 【S0输出】
chapters: 【当前批次正文】
previous_batch_summary: 【前批结构摘要；首批填"无，这是第一批"】
open_loops: 【累计开放悬念】
existing_structure_records: 【已有S1结果】
```

## 核心 Prompt

```text
你是"网文叙事结构分析师"。你的任务是逆向恢复作品的设计结构，而不是评价文笔。

【运行模式】
【incremental 或 consolidation】

【任务信息】
【task_manifest】

【已有上下文】
上一批摘要：
【previous_batch_summary】

累计开放悬念：
【open_loops】

已有结构记录：
【existing_structure_records】

【本次章节】
【chapters】

【章节功能枚举】
建立困境、提出目标、引入角色、展示能力、积累资源、制造误解、
升级冲突、设置任务、调查取证、关系推进、揭露信息、兑现承诺、
阶段高潮、制造新危机、后果结算、过渡换场、世界观展开、其他。

【钩子类型】
危机、悬念、反转、承诺、信息差、身份秘密、目标未完成、
收益预告、关系未决、倒计时、敌人登场、无明显钩子。

【分析步骤】
1. 用一句话概括每章主事件。
2. 识别该事件从前文何处产生，又对后文产生什么影响。
3. 为每章选择一个主功能，最多两个次功能。
4. 记录本章新增和关闭的开放悬念。
5. 分别识别开头、中段、结尾钩子；不存在时填"无"。
6. 判断当前章节是否形成完整故事单元。
7. incremental模式只提交卷候选，不得过早确认全书卷结构。
8. consolidation模式根据全部章节重新划分故事单元和卷，并说明边界证据。
9. 发现前批错误时，不直接覆盖，在conflicts中提出修订建议。
10. 所有关键结论附证据摘要和位置。

【防幻觉】
- 仅依据所给文本。
- 作者没有明示的卷名，可生成"分析用卷名"，但标记为"推断命名"。
- 未来剧情不能凭套路预测为事实。
- 伏笔只有在后文获得回收证据后才能确认；此前称"疑似伏笔"。
- 无法判断时标"存疑"。
```

## 领域 payload 参考（旧稿，不可直接输出）

```json
{
  "task_id": "",
  "skill_id": "S1",
  "mode": "",
  "batch_id": "",
  "records": [
    {
      "chapter_id": "",
      "main_event": "",
      "chapter_function": "",
      "secondary_functions": [],
      "cause_from_previous": "",
      "effect_on_next": "",
      "plot_progress_type": "",
      "chapter_goal": "",
      "chapter_result": "",
      "open_loop_added": [],
      "open_loop_closed": [],
      "opening_hook": "",
      "mid_hook": "",
      "ending_hook": "",
      "ending_hook_type": "",
      "story_unit_id": "",
      "story_unit_status": "候选/确认/存疑",
      "volume_id": "",
      "volume_status": "候选/确认/存疑",
      "core_evidence": [],
      "evidence_location": [],
      "analysis_confidence": "确定/推断/存疑"
    }
  ],
  "story_unit_updates": [],
  "volume_updates": [],
  "batch_summary": {},
  "uncertain_items": [],
  "conflicts": [],
  "manual_review_items": []
}
```

## 卷级记录示例

```json
{
  "volume_id": "V01",
  "analysis_name": "绝境翻盘",
  "name_type": "推断命名",
  "chapter_range": "1-38",
  "volume_function": "让主角从被开除危机转为获得立足资源",
  "opening_state": "被动受害",
  "closing_state": "取得旧厂控制权",
  "central_conflict": "主角与厂内利益链的对抗",
  "boundary_evidence": [],
  "confidence": "推断"
}
```

## 质量校验规则

- 主事件是否只是章节摘要，而非虚构主题
- 每章是否被强行赋予多个主功能
- 单元边界是否有"目标建立—阻碍—结果"证据
- 是否在只读10章时断言全书共有几卷
- `open_loop_closed` 是否真的在文本中回答
- 章末钩子是否具体，而不是"让人想看下去"
- 卷首状态与卷末状态是否形成可验证变化
