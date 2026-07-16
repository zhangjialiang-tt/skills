# Diff Analysis Strategy

大 diff、lock 文件、图片、二进制文件会让 `git diff --cached` 极长或不可读。采用**分层分析**，从概要到细节逐步深入。SKILL.md 第 1 步的脚本即按此策略执行；脚本不可用时手动运行以下命令。

## 分层命令

```bash
git diff --cached --stat          # 文件级增删概览
git diff --cached --name-status   # 每个文件是 A/M/D/R，便于判类型
git diff --cached --numstat       # 行数统计；二进制文件两列均为 "-"
git diff --cached                 # 仅在小 diff 时读取全文
```

## 分析维度

- **文件类型**：代码 / 测试 / 文档 / 配置 / 生成物（lock、build 产物）？
- **变更性质**：新增功能、修复、重构、格式化、依赖、文档？
- **影响范围**：涉及哪些模块（用于 scope）？
- **规模**：小修还是大型重构？

## 大 diff 处理策略

满足任一即按"概要优先"处理：

- staged 文件 **> 20** 个
- `git diff --cached --numstat` 累加行数 **> 2000**

做法：

- 先基于 `--stat` / `--name-status` 给出分组概览
- 再对**每组**局部读 diff，不要试图一次性通读超大 diff（那会导致类型判断失真）
- 在展示时明确提示用户"可能需要拆分提交"

## 二进制 / 生成文件策略

- **二进制识别**：`git diff --cached --numstat` 中某行两列均为 `-`（如 `-	-	assets/logo.png`）即二进制文件。
- **判断依据**：只根据**文件名、路径、大小变化**判断（如图片资源更新、模型权重替换），**不解读内容**。
- **lock / 生成文件**：`package-lock.json` / `yarn.lock` / `poetry.lock` / `go.sum` / `Cargo.lock` / 构建产物等，只说明"依赖/锁文件更新"，**不要逐行推断业务逻辑**。
- 若大段 diff 来自生成文件，在 message 中轻描淡写，不喧宾夺主。
