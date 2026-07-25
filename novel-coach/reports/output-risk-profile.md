# Output Risk Profile — novel-coach

**Skill type**: Conversational role-play coach
**Output family**: Analysis + question + recommendation (no documents, no files)

## Risk Taxonomy

### 1. 空洞反馈 (Vague Feedback Risk) — HIGH

**症状**：说"这段写得不好"但不指出具体哪里不好、为什么、怎么改。
**根因**：SKILL.md 强调犀利但没有约束"具体到行"的要求。
**缓解**：FOCUS 模式下应强制逐段标注，CHALLENGE 模式下各 Phase 有明确质询问题做锚点。

### 2. 跳过打断条件 (Bypass Red Line Risk) — HIGH

**症状**：发现致命逻辑硬伤/市场毒点/高度雷同但不打断，试图"强力润色"。
**根因**：模型天然倾向于"帮忙修"而非"拒绝修"。
**缓解**：SKILL.md 的"立即打断条件"有明确约束，但无验证机制。建议在 CHALLENGE 模式 Phase 1 中要求显式输出"红线通过/不通过"判定。

### 3. 万能公式输出 (Template Advice Risk) — MEDIUM

**症状**：用"加强冲突""增加反转""深化人物"等空洞建议代替具体诊断。
**根因**：没有具体上下文时，模型倾向于给安全但无用的建议。
**缓解**：SKILL.md "拒绝平庸"段已禁止。需确保每次输出包含至少一个"具体到句子/情节的建议"。

### 4. 体裁错配 (Genre Mismatch Risk) — MEDIUM

**症状**：对甜宠文用升级体系逻辑，对悬疑文用爽点密度逻辑。
**根因**：模型可能未正确识别体裁或忽略体裁切换。
**缓解**：`references/genre-logic.md` 提供各体裁关注维度。需在 Phase 1 确认体裁后再选择逻辑。

### 5. 语气失控 (Tone Drift Risk) — LOW

**症状**：过于温和（变成鼓励师）或过于刻薄（打击创作信心）。
**根因**：长时间对话中 persona drift。
**缓解**：SKILL.md 工作风格段有明确约束。初始化开场白锁定语气基调。

### 6. 阶段跳跃 (Phase Skip Risk) — LOW

**症状**：用户说"先看第三章"，直接跳过 Phase 1/2。
**根因**：模型可能顺从用户而放弃流程。
**缓解**：CHALLENGE 模式明确要求逐阶段确认。FOCUS 模式是合法的跳跃路径。

## Self-Repair Recommendations

1. 每次 Phase 1 结束前必须输出显式判定：`[红线: 通过 / 不通过]`
2. FOCUS 模式下每个问题标注对应 Phase
3. 每次具体建议必须引用用户原文（"你第三章的这句话..."）
4. 模式切换时显式声明："切换到 FOCUS 模式，跳过 Phase 1-3"
