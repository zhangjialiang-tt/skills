# Skill IR — ai-plat-bridge

## 基本信息

| 字段 | 值 |
|---|---|
| name | ai-plat-bridge |
| version | 3.0.0 |
| owner | zhangjl |
| maturity | production |
| target_platforms | Codex / WorkBuddy |

## 能力契约

### 负责

- 在 vault 内外统一路由四类卡片访问。
- 把请求归一化为 `operation_mode`、`card_type` 和 `action`。
- 将读取限制在单一卡片类型目录。
- 对显式主写入执行固定事件联动。
- 对宽泛、歧义、越界和旧记忆请求返回澄清或拒绝。

### 不负责

- 在用户未要求时主动记录工程进展。
- 扫描整个 vault 生成概览。
- 访问四类卡片和只读治理文件以外的目录。
- 删除卡片、创建缺失的联动项目卡或修改治理文件。
- 迁移或删除历史记忆文件。

## 输入

| 字段 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `user_request` | string | 是 | 用户原始请求 |
| `current_working_directory` | string | 是 | 仅用于上下文；不改变访问规则 |
| `project_context` | object | 否 | 项目名称、任务关联和已有约束 |

## 输出

| 字段 | 类型 | 说明 |
|---|---|---|
| `operation_mode` | enum | `read \| write \| clarify \| none` |
| `card_type` | enum/null | `task \| knowledge \| log \| project \| null` |
| `action` | enum/null | `list \| search \| read \| create \| update \| append \| archive \| null` |
| `needs_clarification` | boolean | 是否必须在访问前询问 |
| `primary_target` | string/null | 主卡片目标 |
| `linked_actions` | array | 固定事件联动列表 |
| `verification_result` | boolean/null | 写后重读结果 |

## 状态机

1. 识别卡片类型和动作。
2. 无卡片类型或跨类型歧义时返回 `clarify`，不访问文件。
3. 越界、旧记忆或不支持动作返回 `none`。
4. 读取时只进入对应类型目录，不联动。
5. 写入时确认显式授权，计算并展示联动目标。
6. 读取所有写入目标，去重并局部修改。
7. 重读验证后返回结果。

## 固定联动

| 主事件 | 联动 |
|---|---|
| 任务卡创建、推进、归档 | 日志卡；满足项目关联和项目状态变化条件时再更新项目卡 |
| 项目卡创建、更新 | 日志卡 |
| 知识卡创建、更新 | 日志卡 |
| 日志卡写入或任何读取 | 无 |

## 信任边界

- 卡片目录和动作采用明确白名单。
- 治理文件和模板只读。
- 路径规范化后必须仍在相应类型目录内。
- 所有写入必须前读、去重、局部修改、后读验证。
- 保留 vault 已有未提交修改，不写敏感信息。

## 评测

运行：

```powershell
python scripts/trigger_eval.py
```

评测覆盖卡片路由、澄清、拒绝、联动和写入安全不变量。
