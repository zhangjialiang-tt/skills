# O0 拆解任务编排器 — 完整 Prompt 模板

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
  preferred_batch_size: 【默认10】
  available_tools: 【Claude/ChatGPT/Excel/Python等】
  constraints: 【时间、上下文窗口、人工抽检比例】
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
S4 爽点工程
S5 商业卡点
S6 数据聚合
S7 可视化
S8 套路公式提炼
S9 章节模板生成
Q0 质量审计
```

## 输出 Schema

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
  "next_action": "调用S0处理原始文本"
}
```

## 质量校验规则

- 是否遗漏用户要求的最终交付物
- 是否把 S5 放在 S1/S2/S4 之前
- 是否有批次检查点和失败恢复方式
- 是否机械地每 10 章切分，而未保留事件完整性规则
- 是否要求人工逐章审核，违背 80% 自动化目标
- 是否出现不存在的章节数或卷数
