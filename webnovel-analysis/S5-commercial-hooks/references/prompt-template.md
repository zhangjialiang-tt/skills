# S5 商业卡点分析 — 完整 Prompt 模板

> Milestone 1 规范：本模块仅由根 Skill 内部调用。完整输出必须遵循 `../../references/model-output-contract.md` 与 `../../schemas/modules/S5.schema.json`；硬依赖为 S1、S2、S4。下方旧示例仅作为 `payload` 字段语义参考。

## 输入格式

```yaml
mode: 【incremental/consolidation】
chapters: 【当前批次文本】
structure_records: 【S1结果】
emotion_records: 【S2结果】
payoff_records: 【S4结果】
platform_context:
  monetization_mode: 【免费转付费/全付费/未知】
  known_paywall_chapter: 【可选】
```

## 核心 Prompt

```text
你是"付费网文商业阅读机制分析师"。

你分析的是文本如何驱动下一章阅读，不预测真实收入、订阅率或平台推荐结果。

【运行模式】
【incremental/consolidation】

【平台背景】
【platform_context】

【S1结构数据】
【structure_records】

【S2情绪数据】
【emotion_records】

【S4爽点数据】
【payoff_records】

【章节文本】
【chapters】

【断章类型】
危机迫近、行动即将发生、身份将揭露、结果未公布、反转刚发生、
新敌人登场、收益即将兑现、关系即将表态、信息差扩大、
倒计时、场景硬切、自然收束、无明显钩子。

【购买/追读动机】
看结果、看反击、看他人反应、看身份揭露、看收益、看真相、
看关系进展、看危机解决、看新地图、看能力升级、其他。
```

## 领域 payload 参考（旧稿，不可直接输出）

```json
{
  "task_id": "",
  "skill_id": "S5",
  "mode": "",
  "batch_id": "",
  "records": [
    {
      "chapter_id": "",
      "value_delivered_before_break": [],
      "ending_hook": "",
      "cliffhanger_type": "",
      "chapter_break_strength": 0,
      "break_phase": "爽前/爽中/爽后/自然收束",
      "follow_up_question": "",
      "reader_expectation": "",
      "information_gap": "",
      "purchase_motivation": [],
      "commercial_position": "",
      "paywall_suitability": "低/中/高",
      "reason_for_paywall": "",
      "risk_against_paywall": "",
      "expected_resolution_distance": "下一章/1-3章/4章以上/存疑",
      "hook_fairness": "公平/边缘/欺骗风险",
      "core_evidence": [],
      "analysis_confidence": ""
    }
  ],
  "commercial_pattern_summary": {},
  "batch_summary": {},
  "uncertain_items": [],
  "conflicts": [],
  "manual_review_items": []
}
```

## 质量校验规则

- 追读问题是否具体且可在后续回答
- 是否只切断动作，却没有建立新期待
- 付费点前是否已经交付一定价值
- 是否大量使用爽前卡而长期不兑现
- 强钩子是否有下一章或短期兑现承诺
- `chapter_break_strength` 是否因情绪高分而被机械提高
- 是否虚构真实转化率或平台运营规律
- 章末钩子是否和原文最后有效段落一致
