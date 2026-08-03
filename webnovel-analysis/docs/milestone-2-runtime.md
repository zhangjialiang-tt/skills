# Milestone 2 Deterministic Runtime

## 已实现并由测试证明

- 冻结 DAG 和内部 module registry 的机器加载与依赖检查。
- O0→Q0 确定性 fixture 调度；原始输出与已校验输出分离落盘。
- 模块 Schema、task/batch state 和 artifact record 校验。
- Gate A、Gate B、P0 阻断、blocking/non-blocking P1 队列与人工决议。
- 显式模块重跑、revision 保留、直接依赖失效及执行时自然重算。
- 测试专用 Gate C 决议后执行 S7、S8、S9、R0，生成最终报告和交付清单。
- CLI 成功路径及结构化非零错误路径。

## 已定义但尚未实现

- `LLMAdapter` 仅有明确抛出 `NotImplementedError` 的边界。
- Gate C 只有确定性测试决议文件，不是生产人工交互。

## 明确排除

- 真实模型或多 provider 接入。
- 内容 hash、进程崩溃后的 checkpoint resume、传递失效闭包和完整 supersede graph。
- 长篇 consolidation、100/500 章测试、新《悟空传》golden、CI 和可视化增强。

## CLI

由于根目录含连字符，使用显式脚本入口：

```powershell
python .\webnovel-analysis\runtime\cli.py --help
```
