# Q0 质量审计 — 完整 Prompt 模板

> Milestone 1 规范：本模块仅由根 Skill 内部调用。完整输出必须遵循 `../../references/model-output-contract.md` 与 `../../schemas/modules/Q0.schema.json`；P0 必须阻断，P1 采用风险判定。下方旧示例仅作为 `payload` 字段语义参考。

## 输入格式

```yaml
audit_scope: 【batch/volume/book】
task_manifest: 【O0】
chapter_index: 【S0】
master_table: 【S6】
payoff_events: 【S4】
relationship_events: 【S3】
source_chapters: 【仅需复核范围原文】
previous_audit: 【上一轮审计结果】
```

## 核心 Prompt

```text
你是"网文拆解数据质量审计器"。

你不负责重新分析整本书，而是寻找高风险错误，并把人工工作压缩到最少。

【审计范围】
【batch/volume/book】

【任务信息】
【task_manifest】

【章节索引】
【chapter_index】

【中央数据表】
【master_table】

【爽点事件】
【payoff_events】

【关系事件】
【relationship_events】

【原文】
【source_chapters】

【上一轮审计】
【previous_audit】
```

## 领域 payload 参考（旧稿，不可直接输出）

```json
{
  "task_id": "",
  "skill_id": "Q0",
  "audit_scope": "",
  "audit_summary": {
    "records_checked": 0,
    "p0_count": 0,
    "p1_count": 0,
    "p2_count": 0,
    "overall_status": "PASS/PASS_WITH_REVIEW/BLOCKED"
  },
  "issues": [
    {
      "issue_id": "AUD-P1-003",
      "severity": "P1",
      "category": "跨Skill评分冲突",
      "chapter_ids": ["BK001-CH0018"],
      "fields": ["release_score", "payoff_strength"],
      "problem": "S2释放分为2，但S4爽点强度为9",
      "evidence": "本章主要是主角发现线索，尚未产生公开结果",
      "impact": "会抬高热力图峰值并扭曲爽点间隔统计",
      "suggested_resolution": "复核该事件是爽点兑现还是爽点承诺",
      "auto_fix_allowed": false
    }
  ],
  "minimal_review_queue": [
    {
      "chapter_id": "BK001-CH0018",
      "reason": ["评分冲突", "主要爽点候选", "付费点候选"],
      "questions_for_reviewer": [
        "本章是否已经兑现明确结果",
        "读者获得的是满足还是期待",
        "下一章是否立即给出结果"
      ]
    }
  ],
  "distribution_checks": {},
  "cross_skill_checks": {},
  "cross_batch_checks": {},
  "unresolved_items": [],
  "next_action": ""
}
```

## 跨 Skill 冲突检查规则

### "S2 低释放但 S4 高爽点"触发条件（需同时满足）：
- S4 `payoff_present = true` 且 `payoff_strength >= 5`
- S2 `release_score <= 2`
- **S4 `payoff_nature != "reverse"`**（反向释放不触发此检查）

### 当 `payoff_nature = "reverse"` 时：
- 不标记为跨 Skill 冲突
- 仅在审计备注中记录"本章含反向释放事件，已排除冲突检查"
- 如反向释放强度 >= 7，标记为 P2 备注项（供人工参考）

### 其他跨 Skill 检查逻辑保持不变：
- S1 无钩子但 S5 断章极高
- S2 低情绪但 S4 连续爽点
- S3 角色状态倒退
- S1 已关闭悬念重新开放
