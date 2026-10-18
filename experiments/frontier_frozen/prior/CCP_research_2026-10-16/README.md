# CCP 算法研究包

## 先读哪几个文件

`算法探索报告_CCP.md`：研究结论、算法解释和独立测试摘要。

`theory.md`：模型、完整证明、最优性含义及不能宣称的内容。

`proof-and-experiment-audit.md`：假设账本、路线登记、失败记录和复核范围。

`ccp.py`：可交互运行的算法API；`engine.py`是冻结的实验引擎与数值子程序。

`test-results.csv`：13440条测试轨迹的端点指标；`test-summary.csv`：210个环境—配置组合的均值、标准误、经验95%分位数；`paired-primary.csv`：默认CCP与同工具升级ALL的配对差异；`secondary-scores.csv`：预先指定的加权均值诊断，不能替代高概率面积目标。

`protocol.json`、`test-policies-frozen.json`、`test-freeze-record.json`：环境、所有策略配置、预测试冻结记录与哈希。每个分片的counts.npz保存终点臂计数，paths.npz保存四个预设方法每200轮的轨迹摘要。

## 安装与运行

需要Python 3.10以上及numpy、numba、pandas、scipy、matplotlib。`environment.json`记录实际环境版本，不要求把环境完整锁死才能复现。

```bash
python -m pip install numpy numba pandas scipy matplotlib
python diagnostics.py
```

增量算法示例：

```python
from ccp import CertificateCostPlanner

alg = CertificateCostPlanner(epsilon=0.2, eta=0.05, delta=0.05,
                             beta=1.0, time_price=0.1, period=2)
# 每轮先调用choose，输入仅本轮真实到达的新臂标识。
arm, is_service = alg.choose(new_arms=['initial-a', 'initial-b'])
# reward必须是从实际选择的arm获得的一次[0,1]观测。
reward = 0.7
alg.observe(reward)
certified_good, certified_bad, unresolved = alg.report()
print(alg.state())
```

`beta=None`禁用预算拒绝，是另一个服务配置：它有最坏面积阶数保证，但不自动有有限beta配置的regret最优阶保证。代码不会永久删除收益候选；`certified_bad`是报告标签而非接口删除指令。

`report_failure=True`表示历史置信区间交为空，算法采用全未决回退、继续收益选择。不能从结果分析中删除这种轨迹。

## 重现测试

为了不覆盖随包交付的原始记录，下面命令使用reproduce前缀；`analyze.py`默认读取随包交付的test前缀。复跑后应比较对应CSV指标，runtime_sec除外。

```bash
for s in 0 1 2 3 4 5 6 7 8 9; do
  for r in 0 16 32 48; do
    python run_study.py --stage test --scenario "$s" --rep 16 --offset "$r" \
      --out "reproduce-s${s}-r${r}" --policies test-policies-frozen.json
  done
done
python analyze.py
python plot_results.py
```

首次运行numba需要编译；这不计为算法的稳态运行开销。端点指标的runtime_sec未用于算法优越性结论。跨平台浮点与库版本可能引起临界比较后的动作差异；概率保证不是机器浮点形式化认证。

## 研究边界

该包不包含或修改论文LaTeX。独立Temporal Geometry工作中的谱界被明确作为收益模块的既有项目输入，不在此重新计作发现。

本轮测试不是当前稿件Table 2的复现。原始完整配置/源码未在运行环境出现；所有新任务参数已完整公开。自然ALL-ε与ST2-style比较不是原版FAREAST或(ST)^2的逐字复现。

默认CCP显著改善了多个测试环境中的未决量，但不是一般联合最优算法证明。请保留全部胜负与失败记录，再决定是否作为下一稿主要实际实现。

## 开发文件

`development-screen-complete.csv`、`development-phase2.csv`、`development-phase3.csv`、`development-phase4.csv`共3488条完整开发轨迹。`engine-stage1.py`至stage3是阶段快照；最后阶段使用冻结engine.py。早期被超时截断的development-screen.csv不计入完成轨迹数。开发阶段不是独立验证数据。
