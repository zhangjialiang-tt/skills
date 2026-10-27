# 宿主契约清单与接入记录模板

> 对应官方开发标准 `docs/zh/agent-integrations/18-plugin-development.md` §2。
> 官方原文的原则：**不能用另一款 Agent 的行为补全空白**。每一项都必须有证据，
> 能力不足就标"降级实现"或"不支持"。

## 为什么必须先做这一步

接入一个未覆盖的 Agent，真正的成本不在写代码，而在**猜错宿主行为**。典型翻车：

- 照搬 A 宿主的输出格式到 B 宿主 → 整份输出被 schema 校验丢弃（静默失败，无报错）
- 假设存在 `SessionEnd` → 注册了一个永不触发的事件，会话永不 commit
- 假设 `Stop` = 会话结束 → 只在会话末尾提交，实际每轮都触发，语义完全不同
- 假设 payload 里有用户消息 → 采集到空内容，服务端只有 assistant 侧

**先跑只读探针，拿到真实 payload，再写逻辑。**

## 十项必查（逐项填证据）

| # | 项目 | 要回答的问题 | 填法 |
|---|---|---|---|
| 1 | 版本与平台 | 最低宿主版本、Node 版本、已验证 OS；旧版本怎么降级 | 已验证 / 降级 / 不支持 |
| 2 | 安装方式 | 原生插件 / marketplace / 配置文件 hook / npm 扩展；宿主实际加载哪些目录 | |
| 3 | **事件** | 启动、提交用户输入、轮次结束、压缩前、会话结束、子代理 —— 各自是否存在 | 逐个标 有/无 |
| 4 | **输入** | stdin 是 JSON 还是别的；session / cwd / transcript / turn 字段名；何时缺失 | 附真实 payload 样本 |
| 5 | **输出** | 注入字段名；允许/拒绝字段；空结果怎么写；退出码语义；**未知字段是否导致整份输出被丢弃** | |
| 6 | 时间限制 | 单位（秒/毫秒）、上限、宿主是否截断；超时后杀单进程还是进程组 | |
| 7 | **消息来源** | transcript/rollout 路径与格式、写盘时机、稳定消息 ID、工具调用与结果如何关联 | |
| 8 | 进程模型 | 是否复用 hook 进程；后台进程能否存活；多窗口/多会话是否并发 | |
| 9 | MCP | 配置格式、是否支持 stdio、根路径模板变量、启动 cwd、环境变量继承、工具命名空间 | |
| 10 | 恢复 | resume / clear / 异常退出 / 压缩 / transcript 截短后，哪些身份与状态仍有效 | |

**第 3、4、5、7 项是决定成败的四项。** 其余可以边做边补。

## 只读探针模板

第 4 项（输入）和第 5 项（输出）必须用**实测 payload** 回答，不能靠文档。

```js
// probe.mjs —— 只记录事件名 + 字段名/类型/长度，不外发、不落正文
import { appendFileSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const EVENT = process.argv[2] || "unknown";
const OUT = join(homedir(), "ov-probe");

function project(value, depth = 0) {
  if (value === null) return "null";
  if (Array.isArray(value)) return `array(${value.length})`;
  if (typeof value === "object") {
    if (depth > 1) return "object";
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, project(v, depth + 1)]));
  }
  const t = typeof value;
  return t === "string" ? `string(${value.length})` : t;
}

let raw = "";
for await (const c of process.stdin) raw += c;
let payload = {};
try { payload = JSON.parse(raw); } catch { /* 保留原始长度信息 */ }

mkdirSync(OUT, { recursive: true });
appendFileSync(
  join(OUT, "probe.jsonl"),
  JSON.stringify({ at: new Date().toISOString(), event: EVENT, rawLen: raw.length, shape: project(payload) }) + "\n",
);
// 纯采集：stdout 保持为空，避免污染宿主上下文
```

**三条纪律**（沿用 `workbuddy-hook-ops` 的探针规范）：

1. **零外发** —— 源码不含 `fetch` / `http` / `node:net`；自检时
   `grep -nE "fetch|https?://|node:(http|net)" probe.mjs` 应无命中
2. **结构投影** —— 默认只记字段名/类型/长度，不落正文；需要正文时用环境变量临时开
3. **输出隔离** —— 只写自己的目录

跑完一轮真实会话后读 `probe.jsonl`，逐项填第 4 项。

## 接入记录模板（可直接复制填写）

```markdown
## 宿主接入记录：<宿主名>

### 结论摘要
- 接入形态：<薄宿主适配器 / 独立插件 / npm 扩展 / MCP-only>
- 会话前缀：<xx->
- 最低宿主版本：<>；Node：<>
- 已验证平台：<>
- **不支持的能力**：<列出，不要留空>

### 1. 版本与平台
...

### 3. 事件能力
| 通用责任 | 宿主事件 | 是否存在 | 替代方案 |
|---|---|---|---|
| 会话启动 | SessionStart | ✅ | |
| 用户提交 | UserPromptSubmit | ✅ | |
| 轮次结束 | Stop | ✅ | |
| 压缩前 | PreCompact | ❌ | 不注册；由 Stop 阈值提交兜底 |
| 会话结束 | SessionEnd | ❌ | **必须在 Stop 提交** |

### 4. 输入契约
- stdin 格式：JSON / 其他
- 关键字段：session_id=<名>；cwd=<名>；transcript=<名>
- 用户消息是否在 payload 里：是 / 否（否 → 必须读 rollout：<路径>）
- 实测样本：<粘贴结构投影，勿贴正文>

### 5. 输出契约
- 注入字段：<hookSpecificOutput.additionalContext / additional_context / 其他>
- 未知字段行为：丢弃整份 / 忽略
- 空结果写法：<>

### 6. 时间限制
- 单位：秒 / 毫秒
- 上限：<>；超时行为：杀进程 / 杀进程组

### 7. 消息来源
- 路径：<>；格式：<jsonl 行结构>
- 稳定消息 ID：<turnId / uuid / 行号>
- 游标依据：<>

### 8. 进程模型
- hook 进程复用：是 / 否
- 后台进程可存活：是 / 否（**Windows 上多半为否**，见 `pitfalls.md`）

### 10. 恢复语义
- resume / clear / 异常退出 / 压缩后，session 与 peer 是否仍有效：<>
```

## 从"填完契约"到"能跑"的最短路径

1. **挑一个同族参考实现** —— `ls ~/.openviking/agent-integrations/`。
   ZCode 最完整（hooks 配置 + scripts + servers + DESIGN.md 架构决策）。照它的形状做，比读文档快。
2. **复用共享运行时** —— 见 `adapter-authoring.md`，只写宿主差异的那一层。
3. **先接通配置与 MCP**，验证路径/环境/鉴权，再碰 recall，最后才碰 capture。
4. **按四级验证推进**，第 4 级（真实事件 + 服务端落库）不可省。

> 官方实施顺序（§10）：接入记录 → 选形态 → 配置+MCP → 自动读取 → 可靠写入 → 宿主辅助能力
> → 安装分发 → 验证并更新文档。**顺序不能倒**：先写 capture 再定契约，返工概率极高。
