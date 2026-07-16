# Split Decision Criteria

单条提交应当内聚。当 staged diff **同时**包含以下多类变更时，应建议拆分（不生成单一 message）。SKILL.md 第 1 步的脚本会输出 `split_signals`，本文件定义判定标准与分组方式。

## 应拆分的信号

1. **代码逻辑 + 文档大改**：如代码改动伴随 README 重写（小修文档注释不算）。
2. **功能新增 + bug 修复**：除非该修复就是该功能的一部分。
3. **纯格式化 / lint + 业务逻辑修改**：格式调整与功能变更应分开。
4. **多个互不相关模块**：如同时改 `gvsp` 与 `cooler` 且无关联。
5. **依赖升级 + 功能修改**：除非升级正是为了该功能。

## 判定步骤

1. 将 staged 文件按类别与模块分组（脚本已给出 `categories` 与模块分布）。
2. 检查是否命中上述 5 类信号。
3. 命中 → 按类/模块分组，**为每组各生成一条 message 草案**，并建议提交顺序。
4. 在展示时明确"建议拆分为 N 条提交"，**默认不执行**，等用户决定。
5. 未命中 → 生成单条 message。

## 分组示例

```text
# 命中"代码 + 文档大改"
建议拆分为 2 条：
1) fix(gvsp): 🐛 correct packet length calculation      # 代码
2) docs(readme): 📝 document packet framing changes     # 文档大改

# 命中"依赖 + 功能"
1) build(deps): 📦 bump pyyaml to 6.0.1                 # 依赖
2) feat(collector): ✨ add yaml config loader          # 功能
```

## 边界

- 测试代码与对应实现一起提交通常是合理的，不必强行拆分。
- 同模块内的小范围格式化 + 小修复可合并，但跨"逻辑 vs 格式"的显著改动建议分。
- 拆分建议是**提醒**而非强制；最终由用户决定。
