# 验证依据分级与 golden 接入契约

本 skill 的核心立场：**测试的期望值必须有独立来源**。框架不禁止 agent 从 RTL 推导
期望，但报告措辞必须与依据等级一致。

## 证据阶梯（低→高）

| 等级 | 证据 | 允许宣称 |
|---|---|---|
| E0 build | 编译/elaboration 通过 | 「可编译」——仅此 |
| E1 smoke | 时钟/复位/无 X-Z settle | 「可运行、基本驱动无异常」——仅此 |
| E2 characterization | 期望值来自读 RTL | 「行为刻画：与当前 RTL 实现一致」；RTL 改行为时该测试跟随失败，不构成独立证明 |
| E3 golden | 期望值来自独立参考模型/实测向量/规格 | 「功能与 <来源> 一致」 |

只有 E3 可以说「功能验证通过」。E2→E3 的唯一途径是接入独立来源，不是改断言。

## golden 接入契约

1. 探测：workspace 内已有 Python 参考实现（如 `caf_float_ref.py`）或测试向量
   （CSV/NPZ/RAW golden 文件）时，向用户确认是否作为 golden。
2. 配置：`design.json["golden_model"] = "python_module.function"`；
   仿真进程通过 `PYTHONPATH`（继承 pytest sys.path）import 该模块——
   模块须位于 pytest 运行目录可发现的包内，否则先把参考模块目录加入
   conftest 的 sys.path（`sys.path.insert`）而不是复制代码。
3. 形态约定：golden 函数应为纯函数式 `expected = golden(input_sample)`，
   TB 负责时序（驱动、等待 latency、采样），golden 不负责。
4. 对拍纪律：位精确比较；浮点模型须显式声明容差与来源（量化文档），
   禁止为凑 PASS 现场调宽容差。
5. golden 自身错误：需要独立证据（规格、另一实现交叉验证）才能改 golden，
   与 Test Independence 原则一致。

## characterization 纪律

- docstring 首词 `characterization:`；报告中单列，不与 golden 结果混排。
- 期望值旁注明来源行号/信号行为（「RTL 第 N 行计数逻辑」），便于后续升级为 E3。
- 无 golden 且用户要求「验证功能正确」→ 声明上限为 E2，给出接入 E3 的最小路径
  （需要用户提供什么）。

## pytest 标记映射

| 生成物 | marker | 含义 |
|---|---|---|
| `test_<top>_smoke.py` 控制函数 | `smoke` | E0+E1 |
| `test_<top>_functional.py` golden 对拍 | `functional` | E3（有模型时） |
| 其余 functional 协程测试 | `functional` + docstring `characterization` | E2 |

`-m smoke` / `-m functional` 分级运行；CI 可 `-m "functional and not characterization"`
预留（characterization 目前是文档约定，转成正式 marker 是 next-iteration 项）。
