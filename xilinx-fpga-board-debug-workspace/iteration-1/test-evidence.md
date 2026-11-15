# iteration-1 · 应用场景微测试记录（2026-11-15）

## 方法
`completion()` 全新上下文 ×2（带技能 system / 无技能对照），同一场景：
build 假成功（exit 0 + mtime 陈旧）→ jtag 后串口无输出 → ping 不通，四问。

## 预注册评分清单（先于看答案定）
1. 管道假成功识别 + mtime 复核 + 重建命令形状
2. bit 溯源（入口+sha256，同名不同物）
3. bootrom 固件重传 = 串口无输出第一嫌疑（双速波特率/发 h 判活）
4. 不执行 rst -system（batch 无命令 / xsdb 报错 / PROGRAM_B 重载 flash 旧 bit）+ 替代流程
5. ping 分流三类：烧错 bit / ARP 占用 / 防火墙入向拦
6. 登记清单（退出码原文、烧板输出行、覆盖面声明、证据层级）

## 结果
- 带技能：6/6 全中，且给出正确命令形状（重定向落盘 + echo BUILD_EXIT、sha256、mtime 复核）。
- 无技能对照：命中 1 与部分 5/6（通用工程常识），**给出错误建议「不行再 rst -system 一次」**
  （恰为本技能要防的实战坑），且缺固件重传、ARP 占用窗口、防火墙入向按 exe 拦三条。
- 判定：PASS。技能差异点 = rst -system 三层不可用 + flash 回退、固件重传强制、
  控制面/数据面防火墙分流。

## 遗留
- 子代理（scout）环境无模型配置，改用 completion() 微测试（writing-skills 认可的
  fresh-context 单样本法）；纪律型压力场景不适用（本技能为 reference 型）。
