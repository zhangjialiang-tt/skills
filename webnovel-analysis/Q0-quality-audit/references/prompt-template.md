# Q0 质量审计 — 完整 Prompt 模板

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

## 输出 Schema

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

## 质量校验规则

- Q0 是否越权改写原始结论
- 每个问题是否能定位到章节和字段
- 是否生成大量无意义低风险问题
- P0/P1/P2 是否符合严重度
- 审计是否检查跨 Skill 矛盾，而不只是格式
- 最小复核队列是否覆盖多个风险
- 是否把"可能有误"说成"确定错误"
- 没问题时是否仍保留有限性说明
