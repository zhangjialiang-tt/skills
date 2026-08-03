# Milestone 2 Runtime Contract

该运行时只证明确定性 fixture 下的控制流，不代表真实 LLM 或文学分析质量。

- CLI seam：`python webnovel-analysis/runtime/cli.py <command>`。
- 所有 adapter 原始输出先保存为 `raw-output.json`，Schema 通过后才产生 `output.json`。
- 旧 revision 永不覆盖；registry 只保存最小状态和直接依赖。
- Gate A、Gate B 和测试专用 Gate C 决议写入任务目录。
- P0 阻断；blocking P1 等待用户决议；模型输出不被 runtime 自动修复。
- 不含内容 hash、进程崩溃恢复、传递失效闭包、真实 LLM 或长篇能力。
