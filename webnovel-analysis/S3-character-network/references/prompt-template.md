# S3 人物关系网 — 完整 Prompt 模板

> Milestone 1 规范：本模块仅由根 Skill 内部调用。完整输出必须遵循 `../../references/model-output-contract.md` 与 `../../schemas/modules/S3.schema.json`；下方旧示例仅作为 `payload` 字段语义参考。

## 输入格式

```yaml
mode: 【incremental/consolidation】
chapters: 【当前批次】
existing_character_registry: 【已有角色表】
existing_relationships: 【已有关系边】
previous_character_states: 【上一批角色状态】
```

## 核心 Prompt

```text
你是"网文角色与关系网络分析师"。

【运行模式】
【incremental/consolidation】

【已有角色注册表】
【existing_character_registry】

【已有关系】
【existing_relationships】

【上一批角色状态】
【previous_character_states】

【本批章节】
【chapters】

【角色功能枚举】
主角行动发动机、核心对手、阶段对手、资源提供者、信息提供者、
能力导师、情感支点、价值观镜像、见证者、喜剧调节、危机制造者、
任务发布者、世界观入口、奖励确认者、其他。

【关系类型】
亲属、伴侣、朋友、师徒、同事、上下级、交易、合作、竞争、
敌对、控制、利用、债务、秘密关联、单向崇拜、单向警惕、未知。
```

## 领域 payload 参考（旧稿，不可直接输出）

```json
{
  "task_id": "",
  "skill_id": "S3",
  "mode": "",
  "batch_id": "",
  "chapter_records": [
    {
      "chapter_id": "",
      "pov_character": "",
      "active_characters": [],
      "new_characters": [],
      "character_goal": {},
      "character_action": {},
      "relationship_change": [],
      "faction_change": [],
      "core_evidence": [],
      "analysis_confidence": "确定/推断/存疑"
    }
  ],
  "character_registry_updates": [
    {
      "character_id": "C001",
      "canonical_name": "林川",
      "aliases": ["小林", "林技术员"],
      "first_appearance": "BK001-CH0001",
      "current_role": "主角",
      "narrative_functions": ["主角行动发动机"],
      "current_goal": "保住账本并查清陷害者",
      "known_information": ["前世自己被赵海陷害"],
      "suspected_information": ["采购账可能牵涉厂领导"],
      "resources": ["前世记忆", "原始账本"],
      "current_status": "被调查",
      "faction_ids": [],
      "confidence": "确定"
    }
  ],
  "relationship_events": [
    {
      "event_id": "REL-E001",
      "chapter_id": "BK001-CH0001",
      "source_character_id": "C001",
      "target_character_id": "C002",
      "relationship_type_before": "上下级",
      "relationship_type_after": "隐性敌对",
      "strength_before": 0,
      "strength_after": -2,
      "change_reason": "赵海试图迫使林川交出异常账本",
      "evidence": "赵海拒绝解释账目并公开威胁开除",
      "confidence": "确定"
    }
  ],
  "faction_updates": [],
  "batch_summary": {},
  "uncertain_items": [],
  "conflicts": [],
  "manual_review_items": []
}
```

## 质量校验规则

- 是否把职位称呼误建为新角色
- 同名角色是否错误合并
- 是否把"推断动机"写进 `known_information`
- 关系变化是否有事件触发，而非无缘无故改变
- 阵营与关系是否混为一谈
- 角色功能是否随章节证据更新，而非一次定终身
