# novel-master V1 实施说明

> 基于冻结基线 `novel-master-architecture-v1.0.1-frozen.md` 和 `novel-master-contracts-v1.0.1-frozen.md`。
> 本文不修改冻结文档，仅补充实施层规范。

## 0. 平台能力调查结论

| 项目 | 结论 |
| --- | --- |
| 当前 Skill 平台 | QoderWork（Agent Skill 平台） |
| Skill 间直接调用 | 不支持原生互调；由主 Agent 按工作流串行编排 |
| Python 脚本执行 | 支持（Python 3.11.3） |
| 项目文件读写 | 支持 |
| 已有 Skill 模板 | 无（本次创建） |
| JSON Schema / 测试框架 | jsonschema 4.24.0 + pytest 9.1.1 可用 |
| 统一命令入口 | 无；脚本通过 `python scripts/<name>.py` 调用 |

默认假设：

- Skill 负责语义推理与创作生成。
- Python 脚本负责确定性验证和文件事务操作。
- `novel-master` 通过工作流说明编排子 Skill，子 Skill 不假设平台原生支持互相调用。

---

## 1. 运行模型

### 1.1 Skill 与脚本的职责边界

```text
LLM（Skill）：语义判断、创作生成、冲突识别、上下文提取、评审诊断。
Python 脚本：JSON Schema 校验、路径越界检测、revision/hash 计算、
             ApprovalRef 有效性校验、写锁管理、ChangeSet 事务执行。
```

Skill 不得声称自己完成了脚本负责的确定性校验。脚本不得做创作判断。

### 1.2 路由方式

`novel-master` 作为编排器 Skill，接收用户请求后：

1. 识别意图、项目阶段、风险。
2. 构造 `TaskEnvelope`。
3. 按路由表选择最小子 Skill 集合。
4. 由主 Agent 按步骤串行调用子 Skill。
5. 校验每步 `SkillResult`。
6. 汇总 `MasterResult`。

### 1.3 子 Skill 调用方式

V1 不依赖平台原生 Skill 间调用。主 Agent 读取 `novel-master` 的路由指令后，依次激活对应子 Skill 并传递 `TaskEnvelope`。

### 1.4 机器协议与用户输出分离

见 §2。

---

## 2. 机器输出与用户输出分离

### 2.1 用户可见输出

只显示：

- 本次完成内容摘要。
- 当前章节生命周期状态。
- 已确认变化（正式生效的 Canon/状态更新）。
- 待确认事项（Proposal、待决策项）。
- 风险和阻塞项。
- 建议的下一步。

### 2.2 机器协议输出

保存到 `workflow/runs/<request_id>/`：

```text
task-envelope.yaml      — 本次请求的完整 TaskEnvelope
route-plan.yaml         — 路由决策和步骤
step-XX-result.yaml     — 每步子 Skill 的 SkillResult
master-result.yaml      — 最终 MasterResult
diagnostics.log         — 脚本校验日志
```

不得默认把完整 TaskEnvelope 和 SkillResult 倾倒给用户。

---

## 3. 文件版本策略

### 3.1 revision 格式

```text
revision = 单调递增整数（字符串形式，如 "1", "2", "3"）
```

每次文件内容变化时递增。内容未变化时不递增。

### 3.2 content_hash

```text
content_hash = SHA-256（hex 小写，64 字符）
```

### 3.3 更新规则

- 文件内容变化 → revision +1，重算 hash。
- 文件内容未变化 → 不更新。
- 新建文件 → revision = "1"。

### 3.4 stale context 校验

执行写操作前，脚本比较 `base_revision` 中记录的 revision/hash 与当前文件实际值。不一致则返回 `STALE_CONTEXT`，阻塞写入。

### 3.5 与 Git 的关系

V1 不依赖 Git 进行 revision 管理。内部 revision 由 `compute_revision.py` 维护。Git 可作为额外备份层，但不替代内部版本校验。

---

## 4. 单项目写锁

### 4.1 锁文件

```text
workflow/.write.lock
```

### 4.2 锁内容

```yaml
request_id: string
created_at: ISO-8601
process_id: string | null
```

### 4.3 锁协议

| 操作 | 行为 |
| --- | --- |
| 获取锁 | 文件不存在时创建；已存在时检查归属 |
| 检测陈旧锁 | `created_at` 超过 30 分钟且 `process_id` 无响应 → 视为陈旧 |
| 释放锁 | 删除锁文件 |
| 写入失败清理 | ChangeSet 回滚后释放锁 |
| 并发保护 | 同一项目同一时间只允许一个状态写事务 |

`--force` 选项可强制获取锁，但必须记录操作理由到 `workflow/change_log.md`。

---

## 5. ChangeSet 简化实现

### 5.1 V1 定位

V1 本地文件系统事务不是数据库级全局原子事务。通过备份 + 临时文件 + 原子替换近似实现。不声称多文件替换在所有平台上绝对原子。

### 5.2 提交流程

```text
1. 校验锁（必须持有当前 request_id 的锁）
2. 校验 base_revision / hash（所有目标文件）
3. 创建 PREPARED ChangeSet 记录
4. 备份原文件到 workflow/backups/<change_set_id>/
5. 写入 *.tmp 临时文件
6. 校验临时文件（格式、内容、交叉一致性）
7. 使用 os.replace() 逐文件替换正式文件
8. 更新 revision / hash
9. 更新 workflow/change_log.md
10. 标记 COMMITTED
```

### 5.3 失败处理

```text
- 任一步骤失败 → 从 backups 恢复全部已替换文件
- 标记 ROLLED_BACK
- 回滚失败 → 标记 ROLLBACK_FAILED，停止所有后继写操作
- 清理临时文件
- 释放锁
```

### 5.4 约束

- Canon 项不允许通过 DELETE 移除（只能 DEPRECATED）。
- `change_log.md` 与状态文件属于同一事务。
- 回滚失败时保留诊断信息到 `workflow/runs/<request_id>/diagnostics.log`。

---

## 6. ApprovalRef 生成规则

### 6.1 生成权限

- 子 Skill 不得自行创建用户授权。
- 只有 `novel-master` 或授权脚本可以生成 `ApprovalRef`。
- 必须基于用户明确确认。
- 必须绑定 revision / hash。

### 6.2 用户表达判断

| 用户表达 | 是否构成批准 |
| --- | --- |
| "可以，按这个执行" | 是，明确批准 |
| "这个方向不错" | 否，不构成批准 |
| "先看看" | 否，不构成批准 |
| "继续" | 仅批准当前明确步骤 |
| "你决定" | 只能生成范围受限的授权 |

### 6.3 高风险审批

高风险审批不可由模糊积极反馈代替。必须：

- 明确操作范围。
- 绑定当前 revision。
- 标记 `expires_after_use: true`（L4/RETCON）。

---

## 7. 自动接受策略

### 7.1 V1 默认

```yaml
auto_accept:
  enabled: false
```

保留接口，首个实现不默认启用。

### 7.2 自动接受中止条件

以下任一条件成立时，自动接受必须中止并转人工：

- 存在 HIGH 风险计划偏离。
- 存在 Canon 冲突。
- 新增核心能力或世界规则。
- 主要人物死亡、退场或根本关系变化。
- Reviewer 返回 blocker。
- 关键上下文为 UNKNOWN。
- revision 已变化（stale context）。
- 章节计划核心目标未完成。

---

## 8. 已知限制

| 限制 | 说明 |
| --- | --- |
| Skill 间调用 | 平台不原生支持，由主 Agent 串行编排 |
| 多文件事务 | 通过备份和恢复近似实现，非数据库级原子 |
| 文风质量 | 需人工评估，机器只做结构校验 |
| 最小上下文包 | 可能遗漏远距离隐含约束 |
| 跨项目读取 | V1 不支持 |
| 自动日更 | V1 不开放默认授权 |
| Retcon 自动重写 | V1 不实现完整 Retcon |
| 并发写保护 | 基于文件锁，非操作系统级互斥 |

---

## 9. 待决策项

当前无与冻结文档的冲突。如后续实施中发现冲突，将记录到 `docs/implementation-known-issues.md`。
