# 简化算法与原尺寸纯奖励配对实验

实现依据是 2026-11-14《简化算法稿》的第 3–5 节。代码运行完全不读取相邻 proposal 目录。`src/srcbench/simplified.py` 提供 FULL、GT_M、最小终身计数服务和状态价格门控；`FullPolicy` 与原政策都遵守 `choose(new_arms)`、`observe(reward)`、`report()` 的接口。

## 算法

竞争规模首次非零或翻倍时更新时钟，记块首轮为 sigma、块初始竞争规模为 b，有效时钟为 $v=(t-\sigma+1)/(2b)$。终身样本不重置。单臂直接选择唯一臂；多臂时先观察到达秩最小的未观察臂，否则选择最大 FULL 指数：

$$
J_i(t)=\sup\left\{x\in[\widehat\mu_i,1):n_iD_{\inf}(\widehat F_i,x)\le\phi(v/n_i)\right\},
\qquad \phi(z)=\log_+z+\log\left(1+(\log_+z)^2\right).
$$

信息量使用全部实际经验支持，不把一般有界分布替换成 Bernoulli。全部计数使用同一公式，无 KL/MOSS 切换、双账本、奖励 cap 或 H8。全一支持指数为 1；有限预算且存在非一观察的指数严格小于 1。并列按到达秩。

GT_M 使用权重为一半的 Hoeffding 分量和 M 个等权乘积赌注，乘积赌注为 $2^{-j}$，$j=0,\ldots,M-1$，单侧风险为 $\delta/[4i(i+1)]$。每次真实观察后反演双侧财富并取历史交。保护失败持久化；标签、工作集和可能最佳参考集按当前证据重算。ON 模式在参考与工作集的并集中选择终身计数最少者，以概率

$$
p_t=\frac{|\mathcal W_t^-|}{|\mathcal W_t^-|+\lambda(J_{i_t^R}-J_{i_t^S})}
$$

执行服务。价格为 0 时全速服务；OFF 为独立的纯奖励模式。在线算法不读取真实 gap、未来日程或离线资源 LP。默认 M 从公开 eta 以精确有理数比较确定；浮点原型支持整数 M=1 至 64。财富在 log 空间计算，零乘积因子保留为零财富。反演使用向外端点，但普通双精度及回归检查不构成端到端认证区间运算。

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))  # 在复现仓库根目录运行
from srcbench import FullPolicy

policy = FullPolicy(epsilon=.2, eta=.015, delta=.05, mode="OFF")
arm = policy.choose(["first", "second"])
policy.observe(.7)
positive, negative, unresolved = policy.report()
```

## 本轮冻结实验

`configs/full_reward.json` 冻结 24 个原始布局、384 个环境单元，每单元 20 次配对重复。F17、adaptive 各 12 布局，各用原始 16 种有界分布；不压缩 T、K、到达时刻或改变均值、任务和分布参数。纳入统计的唯一轨迹共 7,680 个新世界、38,400 条轨迹、483,200,000 次策略反馈。中断后重算的在途任务不增加统计样本数。

方法为 FULL-R、SRC-R、SRC-KL-R、IMED、Empirical-KL-UCB。两种旧 SRC 沿用正式默认值，包括奖励预算系数 32、评分 log 系数 .5、SRC-KL sublog cap 系数 1；不使用先前调参候选。新主实验 seed 为 2026111401。所有方法共享每臂按观测次数索引的潜在奖励流和同批到达置换；政策私有随机流独立。按需缓存奖励，实际计数只在取得反馈后增加。

本轮对所有方法关闭被动置信报告计算，纯奖励动作仍执行原规则。逐轮一致性回归比较报告开启与关闭两种运行。输出明确标识 `reports_evaluated=false`，不以零值冒充分类正确率、未决面积或覆盖失败率。ON 实现有定向测试，本轮没有 ON 数值性能结论。

```powershell
python run_full_reward.py run --dry-run
python run_full_reward.py run --output _runs/full-reward-r20 --workers 16
python run_full_reward.py run --output _runs/full-reward-r20 --workers 16 --resume
python run_full_reward.py verify --output _runs/full-reward-r20 --check-current
python run_full_reward.py analyze --output _runs/full-reward-r20
```

入口在计算后自动汇总并输出 PNG/PDF/SVG。需要推迟汇总可加 `--no-render`。另有 `--pilot`：两个事先指定原尺寸布局、全部 16 分布、各 1 次，使用独立 seed 2026111402，只作性能估时，不进入正式统计。

## 统计与复现

主要比较预先固定为 FULL 对四个对照，分别在 F17、adaptive 汇总，共八项，使用 Bonferroni 的整体 95% 区间。每个环境单元等权；先逐世界计算配对差，再做分层 Monte Carlo 聚合。百分比为宏观均值之差除以对照宏观均值，采用保留配对协方差的 delta method 和 Satterthwaite t 近似。区间描述固定测试矩阵中的采样误差，不代表对任意环境的保证。

逐布局、逐分布、逐单元对比为探索性分析，报告未校正区间；不把全部单元的点估计优胜数解释成显著优胜数。失败、错误和不利路径不能删除后继续宣称完整实验。执行错误会记录并中止，修复原因后按原指纹续跑。

每个世界独立原子分片，包含五个方法的终点、时间轨迹、每臂终点计数及实际 Numba 缓存来源。配置、源码、种子、数值软件版本及 Python 平台均进入续跑指纹；worker 数不参与。运行目录保存完整源码快照。旧已发布结果仍对应各自快照；新增实现不把旧实验重新标记成当前源码的运行。

Windows 下通过标准输出或其追加日志查看运行进度，避免在运行期间持续轮询或占用 `manifest.json`；打开的读取句柄可能阻止该文件的原子替换。本轮曾发生一次此类文件替换访问错误，原始错误日志和当时清单保存在结果目录的 `validation/execution_incidents.json` 所列文件中。取消运行时清单轮询后，以相同指纹续跑并复用已验证分片；该事件属于执行中断，不是删除不利数值路径的理由。
