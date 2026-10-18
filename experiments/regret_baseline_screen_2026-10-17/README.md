# Regret 基线独立筛查，2026-10-17

本目录比较用户选定的九类新增基线与当前 F-R，只评价累计动态 regret。不改论文，也不覆盖原 F17 冻结代码或结果。环境完全沿用 `../fccp_frozen/protocols/holdout-freeze.json` 中的12个场景、各自完整时域、奖励分布、批内均值置换和96次配对重复。

## 协议与方法

`candidate-selection.json` 保存用户选择；`protocol.json` 在新增性能批次运行之前固定全部参数；`audit/execution-freeze.json` 记录运行源码和协议哈希。新增算法共九类：IMED、Bayes-UCB、KL-UCB+、empirical KL-UCB、UCB-V、UCB1-Tuned、BL-MOSS、SB-EXP3-ATGT、AUER。

BL-MOSS 预先指定三个 Pareto 指数，分别为0.5、1和2，全部保留，不事后择优。加上原五个基线及F-R，共17个配置，每格96次重复，完整矩阵为19,584条轨迹。每次配对使用同一个潜在奖励数组；臂的第几次真实采样决定读取其哪一个奖励，而不是按物理时间共享一项奖励。

- F-R：原生产实现，认证关闭、温度0.5、收益保护系数16。
- 原对照：UCB1、Growing-MOSS、MC-MOSS、Thompson sampling、KL-UCB，均调用原生产选择函数。
- AUER：原文的探索常数8，保留历史；与UCB1同属指数方法，不能将探索常数变化解释成独立新机制。
- UCB-V：原作者实验配置 $c=1,\zeta=1,b=1$。UCB1-Tuned使用标准经验方差公式。
- Bayes-UCB：均匀Beta先验、$c=0$、分位数 $1-1/t$。非Bernoulli场景的fractional更新是动作启发式，不宣称正确指定的Bernoulli后验。
- KL-UCB+：Bernoulli KL、探索项 $\log(t/n_i)$、$c=0$；empirical KL-UCB使用经验分布及探索项 $\log t$。
- IMED与empirical KL-UCB：精确利用已经观察到的一点或两点经验分布，不输入真实支持点。当前场景均满足两点支持；实现遇到第三个不同观测值会报错，不能直接用于任意连续分布而不扩展存储。
- BL-MOSS：仅它获得时域 $T$；按到达顺序接纳前 $\lceil T^{1/(1+2\beta)}\rceil$ 个臂，在当前已接纳集合中运行MOSS。批内沿用原协议的标签顺序，不按均值排序。参数是固定敏感性值，不是已知真实到达尾参数，原论文的单臂到达和尾分布保证不转移到当前固定批量场景。
- SB-EXP3-ATGT：原文Algorithm 5、无偏估计、两级doubling，不读取时域或未来臂数。原理论的per-action sleeping regret与本实验的当前最好臂动态比较器不同。

BL参数0.5和1在本套场景下的接纳上限均大于最终臂数，因此两者逐动作相同；这是参数与环境的结构关系，不是两份独立性能证据。参数2的接纳上限为7，在两个小场景也不产生截断。

## 重跑

依赖使用项目根目录的 `../../requirements-reproduce.txt`，本轮实际环境另存于 `results/environment.json`。在本目录执行：

```powershell
python -m pip install -r ../../requirements-reproduce.txt
python -X utf8 validate_new.py
python -u -X utf8 runner.py --protocol protocol.json --output rerun_results --workers 8
python -X utf8 analyze.py rerun_results --protocol protocol.json
```

请为重新执行指定新的输出目录。`results/` 是本次完整性能批次，`smoke_execution/` 只是短程执行检查，禁止混入正式分析。需要恢复同一批中断运行时，可在原命令末尾加 `--resume`；协议、源码、时域和成功行身份必须匹配。

## 核验与解释

- `audit/reference-equivalence.json`：12场景乘6个原方法，每格第0次重复的完整时域核验。省去不影响动作的报告计算后，动作、统计量、regret、路径和预算账本均与原生产代码一致。
- `audit/new-policy-numerical-validation.json`：独立标量优化、公开SciPy分位数、边界状态及指数公式核验。
- `audit/sleeping-implementation-review.*`、`audit/ballooning-imed-review.md`：独立实现复核和原文定位。IMED在经验最好均值等于1时使用从下方趋近1的极限约定。
- `audit/analysis-synthetic-check.json`：缺失、重复、非配对、错误时域等合成数据拒绝检查。
- `audit/protected-before.json`：当前稿件与原研究材料的运行前哈希；结束后另行逐项核对。

分析保留全部方法和场景。配对差值定义为“基线减去F-R”，负值表示该基线的regret更低。逐格给出MCSE、双侧95%配对t区间及覆盖所有16乘12个比较的Bonferroni区间，同时保留分位数和尾部均值。

本次是在已经看过的测试场景上补充基线，属于描述性筛查，不是全新独立验证集。区间反映模拟误差，不提供跨环境普遍优越性保证；存在重尾或极少数灾难轨迹时，应结合逐次记录和尾部统计阅读。
