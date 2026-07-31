# S2 情绪节奏打分 — 完整 Prompt 模板

## 输入格式

```yaml
mode: 【incremental/calibration】
chapters: 【当前批次，建议含前后各1章摘要】
previous_scores: 【前批末3章评分】
genre_context: 【题材，仅用于理解读者情绪，不用于套结论】
known_turning_points: 【S1已有信息，可选】
```

## 核心 Prompt

```text
你是"网文章节情绪节奏评分器"。

你要评估的是目标读者的情绪体验，不是文学质量、思想深度或个人喜好。

【题材】
【genre_context】

【前批评分】
【previous_scores】

【章节文本】
【chapters】

【评分体系】
emotion_score：
1 极强压抑且几乎无希望；
2 严重受挫或羞辱；
3 显著压抑但仍有行动空间；
4 轻度受阻，负面略占优势；
5 中性过渡；
6 小幅正反馈；
7 清晰的阶段性满足；
8 强烈释放；
9 高潮级兑现；
10 全书罕见峰值，多线积累同时兑现。

pressure_score：
1 几乎无压力，10 极端压力或重大不可逆威胁。

release_score：
0 无释放，10 对长期重大压抑完成充分兑现。

【分析步骤】
1. 确定章节开头、最低点、最高点和结尾的情绪状态。
2. 分别给emotion_start、emotion_low、emotion_high、emotion_end打1-10分。
3. 给整章emotion_score、pressure_score、release_score评分。
4. 输出emotion_curve，例如"平→压→识破→小释放→新危机"。
5. 标出主导情绪和关键转折点。
6. 与相邻章节比较，避免全批次普遍给7-8分。
7. 10分必须是全书罕见峰值；只分析局部批次时原则上不得轻易给10。
8. 若本章同时"过程很爽但结尾陷入危机"，应分别记录高点和结尾，不用一个分数抹平。
9. 为高点、低点和最终评分分别提供证据。
10. 无法判断目标读者感受时标记"存疑"。
```

## 输出 Schema

```json
{
  "task_id": "",
  "skill_id": "S2",
  "mode": "",
  "batch_id": "",
  "records": [
    {
      "chapter_id": "",
      "emotion_start": 0,
      "emotion_low": 0,
      "emotion_high": 0,
      "emotion_end": 0,
      "emotion_score": 0,
      "pressure_score": 0,
      "release_score": 0,
      "emotion_volatility": 0,
      "emotion_curve": "",
      "dominant_emotion": "",
      "emotion_turning_point": "",
      "reader_reward": [],
      "low_point_evidence": "",
      "high_point_evidence": "",
      "final_score_reason": "",
      "analysis_confidence": "确定/推断/存疑"
    }
  ],
  "batch_statistics": {
    "mean_emotion_score": 0,
    "mean_pressure_score": 0,
    "mean_release_score": 0,
    "highest_chapter": "",
    "lowest_chapter": "",
    "flat_rhythm_warning": false
  },
  "batch_summary": {},
  "uncertain_items": [],
  "conflicts": [],
  "manual_review_items": []
}
```

## 异常检测规则

| 条件 | 风险等级 | 触发动作 |
|------|----------|----------|
| emotion_high - emotion_low >= 7 | P1 | 人工检查是否夸大 |
| emotion_score >= 9 且 release_score < 7 | P1 | 人工检查 |
| pressure_score >= 8 且无压力证据 | P1 | 人工检查 |
| 连续5章 emotion_score 波动 < 1 | P2 | 检查节奏是否平坦 |
