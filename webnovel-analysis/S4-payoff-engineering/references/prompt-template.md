# S4 爽点工程 — 完整 Prompt 模板

## 输入格式

```yaml
mode: 【incremental/consolidation】
chapters: 【当前批次文本】
emotion_records: 【S2结果；必需，用于 payoff_nature literary 判定】
story_units: 【S1结果；可为空】
previous_payoffs:
  last_major_payoff: 【最近主要爽点】
  rolling_payoff_events: 【最近5个爽点】
```

## 核心 Prompt

```text
你是"网文爽点工程分析师"。

【运行模式】
【incremental/consolidation】

【前序爽点记录】
【previous_payoffs】

【S2情绪数据】
【emotion_records】

【S1故事单元】
【story_units】

【章节文本】
【chapters】

【压抑等级】
0无；1轻；2中；3重；4极重。

【爽点类型】
打脸反转、反杀制敌、智识碾压、能力展示、身份揭露、利益获得、
资源升级、权力提升、情感认可、正义补偿、秘密揭晓、稀缺获得、
群体震惊、危机解除、承诺兑现、其他。

【读者奖励】
掌控感、优越感、正义补偿、安全感、希望感、归属感、认可感、
复仇满足、财富想象、权力想象、知识满足、情感慰藉、其他。
```

## 输出 Schema

```json
{
  "task_id": "",
  "skill_id": "S4",
  "mode": "",
  "batch_id": "",
  "chapter_records": [
    {
      "chapter_id": "",
      "suppression_level": 0,
      "suppression_source": [],
      "suppression_target": [],
      "payoff_present": false,
      "primary_payoff_event_id": "",
      "payoff_type": "",
      "payoff_strength": 0,
      "payoff_nature": "",
      "payoff_interval_chapters": null,
      "payoff_novelty": "",
      "reader_reward": [],
      "unfulfilled_payoff_promises": [],
      "analysis_confidence": ""
    }
  ],
  "payoff_events": [
    {
      "payoff_event_id": "PAY-E001",
      "chapter_id": "BK001-CH0001",
      "setup_start_chapter": "BK001-CH0001",
      "suppression_level": 3,
      "suppression_source": "厂长公开指控林川弄丢采购账本",
      "suppression_target": "林川的职位和名誉",
      "reader_expectation": "主角利用重生信息避免再次背锅",
      "payoff_trigger": "林川提前保留原始账本并交出复印件",
      "release_action": "用账目异常反问厂长",
      "payoff_result": "暂时保住证据并迫使对方暴露急迫性",
      "payoff_type": "智识碾压",
      "release_mode": "部分释放",
      "payoff_strength": 5,
      "publicness": "小范围",
      "irreversibility": "中",
      "reader_reward": ["掌控感"],
      "new_cost_or_problem": "厂长转而要求立即搜查工位",
      "evidence": [],
      "confidence": ""
    }
  ],
  "batch_statistics": {},
  "batch_summary": {},
  "uncertain_items": [],
  "conflicts": [],
  "manual_review_items": []
}
```

## 异常检测规则

| 条件 | 风险等级 | 触发动作 |
|------|----------|----------|
| payoff_strength >= 8 且 suppression_level <= 1 | P1 | 人工检查 |
| payoff_present=true 且 reader_reward 为空 | P1 | 人工检查 |
| 连续3个主要爽点类型相同 | P2 | 重复风险 |
| 超过5章无正反馈 | P2 | 检查有意压抑 |

## payoff_nature 判定规则

`payoff_nature` 字段标识爽点的**性质归属**，决定其进入哪些下游统计：

| 取值 | 定义 | 适用场景 | 下游影响 |
|------|------|---------|---------|
| `commercial` | 商业性爽点 | 主角获得资源/打脸/升级/利益等"获得型"正反馈 | 全量进入 S5/S6/S7/S8/S9 |
| `literary` | 文学性情感释放 | 非反向但情绪回报偏文学性（如悲剧式情感兑现、哲思顿悟），且 S2 release_score ≤ 2 | 进入 S6/S7，降低 S8 商业配方权重，不进入 S5 |
| `reverse` | 反向释放 | 以死亡/自毁/杀死真我等方式完成反叛或情感兑现（release_mode = 反向释放） | 仅进入 S7 热力图（标记为反向释放），**不进入 S5 商业卡点**，**不计入 S4 商业爽点密度统计** |

### 判定优先级

1. **release_mode = 反向释放** → `reverse`
2. **S2 release_score ≤ 2 且 payoff_present = true** → `literary`
3. 其余 → `commercial`

### 注意事项

- `reverse` 类事件仍需完整记录 payoff_strength、reader_reward 等字段，供 S7 热力图使用
- S4 的 `batch_statistics.payoff_density` **仅统计 commercial + literary**，排除 reverse
- S4 的 `batch_statistics.payoff_type_distribution` **仅统计 commercial + literary**，排除 reverse
- `reverse` 类事件在 `batch_summary` 中需单独计数（`reverse_payoff_count`），供 S6 聚合与 S8 配方使用
