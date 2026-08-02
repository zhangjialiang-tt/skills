# O0 拆解任务编排器 — 完整 Prompt 模板

> Milestone 1 规范：本模块仅由根 Skill 内部调用。完整输出必须遵循 `../../references/model-output-contract.md` 与 `../../schemas/modules/O0.schema.json`；下方旧示例仅作为 `payload` 字段语义参考。

## 输入格式

```yaml
project_request:
  book_title: 【书名】
  genre: 【题材；未知可填存疑】
  purpose: 【竞品拆解/自有作品复盘/结构研究】
  source_files:
    - file_name: 【文件名】
      format: 【txt/md/docx/其他】
      estimated_chapters: 【数量或未知】
  desired_outputs:
    - 【全书逆向大纲】
    - 【情绪-爽点热力图】
    - 【题材套路公式】
    - 【章节分析模板】
    - 【人类可读汇总报告】
  preferred_batch_size: 【默认10】
  available_tools: 【Claude/ChatGPT/Excel/Python/LLM only等】
  constraints: 【时间限制、上下文窗口大小、人工抽检比例、工具限制等】
```

## 核心 Prompt

```text
你是"爆款网文拆解工作流编排器"。

你的任务不是分析小说内容，而是将拆解任务转化为一份可执行、可恢复、可审计的运行计划。

【输入】
项目需求：
【粘贴 project_request】

【工作流模块】
O0 编排
S0 文本预处理
S1 叙事结构拆解
S2 情绪节奏打分
S3 人物关系网
S4 爽点工程（依赖 S2 结果）
S5 商业卡点（依赖 S1/S2/S4 结果）
S6 数据聚合
S7 可视化
S8 套路公式提炼
S9 章节模板生成
Q0 质量审计

【强制规则】
1. 仅依据输入规划，不假设不存在的章节数量、卷结构或文本质量
2. 不确定的信息标记为"存疑"
3. 默认每批10章；单章超5000字建议每批5章；单章低于2000字可每批15章
4. 完整事件单元不可拆散——事件完整性优先于章节数量
5. S1、S2、S3、S4可在S0后并行；S5在S1/S2/S4后；S6在S1-S5后
6. 每批完成后必须运行Q0；全书完成后再运行全局Q0
7. 默认使用Markdown、CSV/XLSX，不设计数据库
8. 计划必须支持失败后从最近完成批次恢复
9. 批次摘要包字数限制：不超过批次章节总字数的5%，且不超过3000字

【执行步骤】
A. 建立task_id、book_id和版本号
B. 评估输入文件是否需要合并、清洗或章节识别
C. 规划批次，不虚构具体章节边界
D. 建立Skill依赖图（标注S4→S2、S5→S1/S2/S4的依赖）
E. 建立每批输入、输出和人工抽检点
F. 给出运行状态清单
G. 给出五项最终交付物的验收条件

【next_action 决策规则】
- 若用户已提供原始文本 → next_action: "调用S0处理原始文本"
- 若用户未提供文本但提供了书名/来源 → next_action: "向用户索取原始文本文件"
- 若用户仅表达意向但未提供任何具体信息 → next_action: "向用户确认书名、分析目的与原始文本来源"
```

## 领域 payload 参考（旧稿，不可直接输出）

```json
{
  "task_manifest": {
    "task_id": "BK20260731-001",
    "book_id": "BK001",
    "book_title": "",
    "genre": "",
    "analysis_version": "v1.0",
    "default_batch_size": 10,
    "manual_sampling_rate": 0.2
  },
  "source_plan": [],
  "batching_policy": {
    "default_rule": "",
    "boundary_rules": [],
    "estimated_batches": "存疑"
  },
  "execution_graph": [],
  "file_manifest": [],
  "checkpoint_policy": {},
  "manual_review_policy": {},
  "deliverable_acceptance": [],
  "uncertain_items": [],
  "next_action": ""
}
```

## 质量校验规则

- 是否遗漏用户要求的最终交付物
- 是否把 S5 放在 S1/S2/S4 之前
- 是否有批次检查点和失败恢复方式
- 是否机械地每 10 章切分，而未保留事件完整性规则
- 是否要求人工逐章审核，违背 80% 自动化目标
- 是否出现不存在的章节数或卷数
- 是否包含人类可读汇总报告的验收条件
