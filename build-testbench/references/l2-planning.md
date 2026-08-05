# L2 仿真计划契约

L2 不是 L1 模板的扩展注释，而是一次基于 RTL 设计语义的验证设计。执行 L2 前，必须先产出验证计划，再生成 testbench。

## 必须回答的问题

1. DUT 的时钟、复位、valid/ready 或帧/行边界协议是什么？
2. 参数默认值、合法范围和不同 generate 分支是什么？
3. 每条输出的预期延迟、吞吐率和 bubble 行为是什么？
4. 需要覆盖哪些正常、边界、非法输入和 reset/field 场景？
5. checker 的 oracle 是公式、参考模型、golden 文件，还是协议不变量？
6. 哪些依赖必须使用真实 RTL，哪些可以 stub；stub 会削弱什么证据？
7. 完成条件是什么，日志中使用什么机器可检索的 PASS/FAIL 标记？

## 输出约定

- 计划文件：`sim/sub{x}-{modulename}/data/simulation_plan.md`（按 `l2-plan-template.md` 填充）
- L2 testbench：`sim/sub{x}-{modulename}/tb/tb_<top>_l2.v`（结构参考 `l2-tb-template.v`）
- checker/reference：`sim/sub{x}-{modulename}/scripts/`
- 输入/golden/期望结果：`sim/sub{x}-{modulename}/data/`
- 编译和仿真日志：`sim/sub{x}-{modulename}/log/`

计划必须区分"已由 RTL/代码验证的事实"和"待仿真验证的假设"，并标记未覆盖项。

---

## L2-C（CHARACTERIZATION）vs L2-V（VERIFICATION）

这是 L2 可信度的核心区分。**必须**在计划文件顶部和最终报告中标注本次 L2 属于哪一类。

### L2-C：行为刻画

期望值**主要从 DUT RTL 推导**（读 RTL 算出应该输出什么，再用这个期望验证同一个 RTL）。

**可以证明：**
- 状态机能够到达
- 接口有响应
- 输出符合当前 RTL 的行为
- 没有超时、X 扩散或协议明显违规

**不能宣称：**
- 算法实现正确
- 与产品需求一致
- 与软件模型一致

报告措辞：`[SIM_RESULT] L2 PASS (characterization)`。**禁止**写成"功能验证通过"。

### L2-V：功能验证

期望值**至少存在一种独立证据来源**：

- 设计规格 / 接口协议文档
- Python / C / MATLAB reference model
- golden vectors
- 已确认的数学公式
- 用户确认的输入输出关系
- 项目已有可信 testbench

只有 L2-V 才允许报告：`[SIM_RESULT] L2 PASS (verification)` 或"功能验证 PASS"。

### 判定规则

| 期望行为来源 | 分类 | 报告措辞 |
|---|---|---|
| 仅从 DUT RTL 推导 | L2-C | `PASS (characterization)` |
| 有 spec / golden / reference / invariant | L2-V | `PASS (verification)` |
| 混合（部分 testcase 有独立证据，部分仅 RTL） | 标注每个 testcase 的证据来源 | 主结论取最弱证据等级 |

> 这是提升 skill 可信度最重要的规则。根据实现推导期望、再用该期望验证同一个实现，会形成自证循环——即使全 PASS 也只能说明 TB 与 RTL 行为一致，不能说明 RTL 满足设计需求。

---

## 风险驱动确认

生成 `simulation_plan.md` 后，是否暂停等待用户确认由**风险**决定，不是无条件强制。

### 必须暂停（向用户展示计划摘要并等待确认）

- 期望行为只能从 RTL 猜测（L2-C）
- 多种接口解释都成立（如握手协议不明）
- 缺少关键参数或时序
- testcase 会固化重要产品判断（如错误码定义、帧格式）
- 用户明确要求"先评审计划"

### 可自动继续（不暂停）

- spec / golden / reference 足够明确（L2-V）
- 只是复现已有测试
- 用户已确认过计划（如"一次完成""直接跑"）
- 本次是重新生成或修复 TB

### 摘要格式（需暂停时使用）

```text
=== L2 验证计划摘要 — {module_name} ===
分类: CHARACTERIZATION | VERIFICATION
功能: {一句话功能描述}
状态机: {状态数} 个状态
测试用例: {数量} 个 ({列举名称})
独立证据来源: {spec/golden/reference 路径，或"无，仅 RTL 推导"}
Checker 策略: {简述}
详细计划: {sim_dir}/data/simulation_plan.md
是否确认并开始生成 testbench？(可先编辑 plan 文件)
```

用户可编辑 `simulation_plan.md` 调整测试范围、增删用例、修改期望值。这是防止 AI 误解 DUT 功能的必要检查点。

---

## Explore sub-agent prompt 模板

当用户要求"进入 L2""验证功能""设计 testbench"时，启动 Explore sub-agent 生成验证计划。

```
你是 RTL 验证分析 sub-agent。分析以下 DUT 并输出验证计划。

## 输入
- DUT 文件: {dut_path}
- 端口信息: {ports.json 路径}
- 文件列表: {fileset.f 路径}
- 项目根: {workspace_root}
- 验证计划模板: .pi/skills/build-testbench/references/l2-plan-template.md
- L2 分类规则: .pi/skills/build-testbench/references/l2-planning.md (L2-C vs L2-V 部分)

## 分析任务
1. 阅读 DUT RTL 源码，提取功能描述、状态机、接口分组、错误条件、参数范围、依赖模块
2. 判定本次 L2 属于 L2-C 还是 L2-V（是否有独立于 RTL 的 spec/golden/reference）
3. 按模板格式输出验证计划，在计划顶部标注分类
4. 将验证计划写入: {sim_dir}/data/simulation_plan.md

## 输出格式
严格遵循 l2-plan-template.md 的结构。测试用例数量适中（3-8 个），覆盖主路径、变体场景、错误注入、边界条件。每个 testcase 标注期望值来源（RTL 推导 / spec / golden）。
```

sub-agent 职责：
1. 读取 DUT 完整 RTL，提取功能描述 / 状态机 / 接口分组 / 错误条件 / 参数 / 依赖
2. 读取 L1 产物（`ports.json`、`fileset.f`）和项目已有 testbench/checker/reference
3. 判定 L2-C / L2-V 分类
4. 按 `l2-plan-template.md` 输出计划
