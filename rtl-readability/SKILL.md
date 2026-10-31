---
name: rtl-readability
version: "2.2.0-rebuilt"
description: 对 Verilog/SystemVerilog 做可读性审计与分步优化：命名、模块结构、时序语义、状态机、参数位宽、接口协议契约、注释、代码风格八个维度。默认只读输出逐条建议（文件+行号+改前改后+理由+风险等级），用户确认后才改。当用户说「RTL 可读性」「代码命名不规范」「状态机可读性」「补协议契约说明」「注释解释 why」「代码不好读」时使用。功能缺陷（综合/CDC/握手/复位/时序收敛）请走 rtl-refactor-scan。
output_contract:
  artifacts:
    - "readability_findings.json — 唯一权威审计结果"
    - "可读性报告_<模块>.md — 由 readability_findings.json 渲染的阅读物"
  format: markdown
---

# RTL 可读性审计（rtl-readability）

> **重建说明**：本版本为 2026-10-31 按 v2.1 设计记录重建（原 rule-based audit 版随仓库事故丢失，无逐字节副本）。
> 重建蓝本：OpenViking 记忆「rtl-readability v2/v2.1 升级记录」。功能按 v2.1 设计意图重建，非逐字节恢复。

对 Verilog/SystemVerilog 做可读性审计与分步优化。默认只读：输出逐条建议（文件+行号+改前改后+理由+风险等级），
用户确认后才改。功能缺陷（综合/CDC/握手/复位/时序收敛）走 rtl-refactor-scan，两者互补不重叠。

## 六阶段工作流

1. **审计**：只读扫描目标模块，产出 `readability_findings.json`（唯一权威审计结果）。
2. **测卷**：用 `scripts/readability_model.py check` 生成 14 项问答测卷（probes），
   区分 answered / implicit（源码可答但未写进注释）/ undocumented（真不可答）。
3. **门禁**：三档门禁——L0 契约注释、L1 测卷得分、L2 修复复验，逐档通过。
4. **修复**：按 L0–L3 修复阶梯执行（见 references/fix-and-verify.md）：
   L0 契约注释（comments-only，不动逻辑）→ L1 测卷复测 → L2 结构调整 → L3 重命名（跨文件传播）。
5. **复验**：修复后复跑测卷与审计，分数提升与 implicit→answered 转化记入报告。
6. **报告**：`scripts/readability_model.py render` 从 JSON 权威渲染六节报告
   （速览/发现/测卷/门禁/修复复验/遗留），**禁止手写报告绕过 JSON**。

## 八个审计维度

命名（READ-NAME-*）、模块结构（READ-STRUCT-*）、时序语义（READ-TIMING-*）、状态机（READ-FSM-*）、
参数位宽（READ-PARAM-*）、接口协议契约（READ-PROTOCOL-*）、注释（READ-COMMENT-*）、代码风格（READ-STYLE-*）。

## 隐含契约三态

测卷区分三态，防止把「源码可答但没写」误标为缺失：

| 态 | 含义 | 处理 |
|---|---|---|
| answered | 注释/文档已写明 | 保持 |
| implicit | 源码可答但未写进注释 | 建议 L0 补注释（不是"缺失"） |
| undocumented | 真不可答 | 计入门禁失分 |

## 工具

### scripts/readability_model.py

```bash
# 测卷生成与判分（14 项问答，三态区分）
python <skill>/scripts/readability_model.py check <verilog 文件> --sheet <sheet.json>
# 测卷对比（v2.1：只比 status/default/signals/UNKNOWNS，不比纯文本 diff）
python <skill>/scripts/readability_model.py compare --facts before.json after.json
# 六节报告渲染（从 JSON 权威渲染，禁止手写绕过）
python <skill>/scripts/readability_model.py render <findings.json> --out 可读性报告_<模块>.md
```

退出码 0=通过，1=校验失败，2=用法错误。

## references

- `references/probes.md` — 14 项问答测卷设计（含 ADDRESS_MAP 维度：寄存器文件类模块的
  RO/RW/触发/位图门控/读覆盖/地址别名归宿）
- `references/fix-and-verify.md` — L0–L3 修复阶梯与复验要求
- `references/report-template.md` — 六节报告模板（JSON 权威）

## 交付纪律

- 默认只读；改动等用户确认，L3 重命名（跨文件传播）必须用户逐项确认。
- 修复留工作区不 commit，等用户验收。
- 报告与 findings JSON 冲突时以 JSON 为权威。
