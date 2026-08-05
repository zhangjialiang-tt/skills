# Output Risk Profile — rtl-refactor-scan

> 此技能主要失败模式与防御策略。内容短小，聚焦可防可控的风险。

## 风险矩阵

| # | 失败模式 | 后果 | 防御 | 严重度 |
|---|---------|------|------|--------|
| 1 | 假设 RTL 文件路径而未确认 | 扫描错误文件 / 漏扫，审计结论失真 | Phase 1 先用 ls/find/rg 确认文件存在，不猜路径 | 高 |
| 2 | 误将 report_only 风险标为可自动修改 | 过度修改稳定代码，引入新 bug | actionability 由 rules.yaml 决定；manual_design_required/report_only 不得自动改 | 高 |
| 3 | 修改改变了模块外部接口 / 协议语义 | 上下游模块失效，难以定位 | Gate 5 检查项（接口不变 / 协议不变 / 不降 coverage） | 严重 |
| 4 | 回归测试失败却屏蔽问题通过 | 真实缺陷被隐藏，上板才暴露 | Gate 6 失败必须分析原因，禁止"屏蔽问题" | 严重 |
| 5 | 未确认即执行修改 | 用户不知情，修改不可控 | refactor 模式需批准计划（M3）；audit 模式默认只读 | 高 |
| 6 | 大模块一次性扫描 | 超出上下文，维度覆盖不全 | >5000 行建议分模块 / 只扫关键路径 | 中 |
| 7 | 把"快速语法检查"误路由到本 skill | 与 rtl-annotator 职责重叠，产出不对 | frontmatter 排除提示 + trigger-eval.md 边界 #1（Phase 1 确认 quick vs audit） | 中 |
| 8 | ~~A/B/C 分类标准不统一~~ → **已解决** | 报告风险等级不可比 | ✅ v2.0 统一到 rules.yaml 三轴模型，A/B/C 仅显示层 | — |
| 9 | ~~报告缺行号位置~~ → **已解决** | 用户无法定位问题 | ✅ v2.0 finding.locations 强制 start_line/end_line | — |
| 10 | 为精简代码而破坏 EDA 友好性 | 综合/LA 探测不稳定 | 约束：FPGA EDA 友好优先于代码短小 | 中 |
| 11 | 盲目使用 SystemVerilog 语法 | 部分 EDA 工具链不友好 | 优先 Verilog-2001，非必要不升级语法 | 低 |
| 12 | 无 testbench 仍声称"已验证" | 虚假验证结论 | ✅ v2.0 refactor 模式被阻断（无回归入口不得宣称验证完成）；audit 模式只读不涉及验证 | 高 |
| 13 | 把 hypothesis 标为 confirmed | 无证据断言，误导决策 | ✅ v2.0 finding.schema allOf：confidence=confirmed 需 evidence_level >= E2 | 高 |

## 自检清单

执行完成后逐项验证：

- [ ] Phase 1 已确认文件路径、时钟/复位、接口协议（不靠假设）
- [ ] 5 个维度全部扫描，无遗漏
- [ ] 每个 finding 含 rule_id + 位置(行号) + severity + confidence + evidence_level + actionability
- [ ] 三轴分级对照 rules.yaml（唯一权威源），A/B/C 仅显示层
- [ ] report_only / manual_design_required 的 finding 未被自动修改
- [ ] 无 evidence_level=E0/E1 的 finding 标为 confirmed
- [ ] audit 模式不修改代码；refactor 需批准计划（M3）
- [ ] 修改未改变外部接口 / 协议 / ready-valid / reset
- [ ] 未删除有用注释、未降 coverage、未屏蔽问题
- [ ] 有 testbench 时回归已 PASS；无 testbench 时 refactor 被阻断
- [ ] findings.json 已写入并通过 validate_findings.py 校验
- [ ] 审计报告由 render_report.py 从 findings.json 渲染
- [ ] 最终报告含剩余风险与下一步建议
