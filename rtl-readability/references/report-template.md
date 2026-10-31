# 六节报告模板（JSON 权威）

> 报告由 readability_model.py render 从 JSON 权威渲染，禁止手写绕过。

```markdown
# 可读性报告_<模块名>

## 1 速览
模块 / 文件 / 测卷得分 / 三态分布 / verdict

## 2 发现
逐条建议：文件+行号+改前改后+理由+风险等级

## 3 测卷
14 项问答逐项：状态（answered/implicit/undocumented）+ 答案来源行号

## 4 门禁
L0/L1/L2 三档门禁状态与证据

## 5 修复复验
修复前后测卷对比（compare --facts）：得分变化、三态转化数

## 6 遗留
未处理项与理由、待用户确认项
```
