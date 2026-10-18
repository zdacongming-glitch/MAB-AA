from pathlib import Path
import hashlib,json,platform,importlib,sys
import numpy as np,pandas as pd
P=Path(__file__).parent
su=pd.read_csv(P/'holdout-summary.csv');pa=pd.read_csv(P/'holdout-paired.csv');df=pd.read_csv(P/'holdout-all.csv')
avg=su.groupby('method')[['regret_mean','area_mean']].mean()
names=['UCB','Growing-MOSS','MC-MOSS','MC-MOSS-clipped','Thompson','KL-UCB','ALLplus-b1.0','CCP-b1.0','Shared-b1.0','CCP-b0.25','CCP-free','Shared-free']
table='| 方法 | 平均 regret | 平均面积 / 1000 |\n|---|---:|---:|\n'
for n in names:table+=f'| {n} | {avg.loc[n,"regret_mean"]:.2f} | {avg.loc[n,"area_mean"]/1000:.3f} |\n'
wide=su.pivot(index='scenario',columns='method',values=['regret_mean','area_mean'])
regtab=wide['regret_mean'][['UCB','Growing-MOSS','MC-MOSS','Thompson','KL-UCB','CCP-b1.0','Shared-b1.0']].round(2).to_markdown()
areatab=(wide['area_mean'][['ALLplus-b1.0','CCP-b1.0','Shared-b1.0']]/1000).round(3).to_markdown()
text=r'''# regret—未决量完整前沿：本轮结果与算法检验

研究日期：2026-10-16。当前结论：**没有得到任意到达、未知未来、全部服务预算下同时理论最优且数值全面领先的实用算法。** 这不是把缺口换个名称：本轮给出一个明确的因果信息障碍、一个覆盖大段中间预算的匹配结果，并完成了新的算法开发和独立测试。实践上没有足够证据把默认 CCP 替换成新候选。

## 1. 最重要的理论结论：先固定比较者知道什么

原稿目标保持为
\[
 ER_T\le r,\qquad P(E_{\rm lab},\mathcal U_T(\eta)\le a)\ge1-\delta.
\]
“整个前沿”应指对每个可行 a，都在相同信息与可靠性要求下尽量减少 regret；不是要求一个固定配置同时达到两个单独最小值。也不能用 $ER+\lambda E\mathcal U$ 的最优性替代高概率面积约束。

### 1.1 本轮新证明：逐日程最优值不能总由同一个未知未来算法追上

只有三个 Bernoulli 臂。初始参照均值为 1/2，候选为 $1/2-\varepsilon\pm d$，以后有参照均值 $1/2+v$ 到达。两个日程直到 h 都相同：一个在 h+1 改善，另一个到终点 T 才改善。两个实验使用相同 T、a、ε、η、δ 和最终臂数。

本轮证明，在明确的参数序列中：任何必须在晚改善日程上及时可靠维护的同一因果策略，在早改善日程上也付出 $\Omega(d^{-2})$ regret；但针对早改善日程单独选择的可靠策略只需 $O(\log(1/d))$。

原因不是候选不消失，而是它的**旧资格问题**会不会及时失效。晚改善情况下，面积预算迫使算法在 h 之前已经投入精细观测；早改善情况下，这些观测随后本可不做。过去相同，算法不能根据未发生的到达提前选择不同动作。

这个结果否定未知未来算法相对于“每条日程分别优化”的前沿的普遍常数逼近。它**不**否定在共同未知日程类上的因果 minimax 问题存在最优解。完整构造、相同预算、两边可行性与证明见 `theory_frontier.md` 定理 1。

### 1.2 固定 β 的 CCP 不能覆盖快速维护区间

在既有重复更新族，固定其他参数令 d→0 时 T 为 d^-2 阶。快速服务需要 d^-2 级 regret，而固定 β 的 CCP 谱保护只允许 d^-1 级 regret。因此这不是“差一个证明技巧”：固定预算族确实不能同时满足该严格面积预算。需要让服务强度随服务要求变化，不能把谱最优收益保护与严格识别服务同时无条件宣称。

## 2. 从两个端点推进到一段连续预算区间

### 2.1 任意数量的部分恢复

对于 m 个独立隐藏符号、每观测双向 KL 不超过 κ、全过程任一错误概率≤δ，若在有界停止时刻至少恢复 s 个符号的先验概率≥1/2，则
\[
 \overline E\sum_iN_i\ge \frac{s}{48\kappa}\log(s/\delta),\quad1\le s\le m.
\]
这允许 s 远小于 m。证明使用非负的后验信息漂移
$f(e)=(1-2e)\log((1-e)/e)$，不再减去全部 m 个坐标。它为中间服务预算提供了需要的完成数量接口。

### 2.2 对应的 regret 下界

仍使用 J 个窗口、每批 M 个候选的重复更新族，m=JM，每窗长 H，候选均值 $b_e-\varepsilon\pm d$，$\eta=d/2$。令 V=mH。对 a<V，定义
\[
 k(a)=\lceil(V-a)/H\rceil.
\]
面积成功迫使至少 k(a) 个候选在其有效窗口内有过确定标签；否则未完成候选自己就耗尽面积预算。由上面引理得到
\[
 \mathfrak R_\Theta(a)\ge
 \frac{\varepsilon k(a)}{3072d^2}\log\{k(a)/\delta\}.
\]
所有候选及其后期观测都属于同一个兼容实验，没有把不同最坏环境拼接，也没有用额外逐批 deadline 偷换任务。

### 2.3 ABM：按细任务激活数量分配精度

本轮构造了理论算法 ABM（Activation-Budgeted Maintenance）。它先对每批形成粗证据，再从非经验参照的候选中选至多 s 个进行精细认证；候选进入细层时，共享该批的一条细参照。只给实际激活的细任务分配置信预算，所以细成本按 s 而不是最终所有候选 m 收费。

激活由粗数据决定，因此细层从**激活后的新奖励块**获得置信证据。原数据不删除，仍进入收益估计与粗区间，但不能拿数据选择后的旧前缀冒充新的固定样本置信检验。每个激活序号使用可预测的错误预算，合计≤δ/2；粗层占另一个δ/2。

所有服务与全历史 UCB 交错进行，负报告不永久删除收益资格。可执行参考在 `abm.py`。

### 2.4 匹配范围与不能省略的条件

在完整证明中定义粗服务工作上界 Lc、粗细总完成上界 L，以及跨更新粗恢复面积 B，要求 H≥4(L+B)。对
\[
 mL+B\le a<V,
 \quad s(a)=\left\lceil\frac{V+B-a}{H-L}\right\rceil,
\]
证明
\[
 \frac{\varepsilon k(a)}{3072d^2}\log\frac{k(a)}\delta
 \le\mathfrak R_\Theta(a)
 \le R_0(T)+1024\frac{\varepsilon k(a)}{d^2}\log\frac{k(a)}\delta.
\]
其中 R0 是显式的粗维护和普通收益探索成本。取 H=16(L+B)，区间的左端不超过3V/32，所以包括旧快速端V/8，并覆盖其后所有a<V的中间预算。固定 J,M,ε,v,δ，d→0 时 R0=O(log(1/d))，主项匹配。

**这不是任意模型的完整前沿。** 未处理小于左端的预算、延迟端的全部边界、任意重叠到达；从a换算s使用性能族规模m,H，算法给定s运行不知未来，但并没有一个自动估计未来规模的校准器。ABM也不继承CCP的谱保护。不能把ABM的受限族定理与Shared的数值表拼成同一个“全局最优算法”。

## 3. 实际算法路线：没有把开发集改善当作最后结论

首轮有效开发共576条轨迹，覆盖共同证书收益、共享端点边际分配、后验标签向量信息增益和联合凸规划。预先选中 Shared（模式28）为主候选，再冻结12个新测试环境、22配置、每环境48个配对重复，共12,672条测试轨迹。

Shared 保留 CCP 的报告、价格、收益核与预算，只改变服务选择：对每个当前证书 c，记双端点规划成本为 Cc，对其端点 j 累加
\[
 \operatorname{score}_j
 =\sum_{c:j\in c}\frac1{\max(1,C_c)^{3/2}}
       \frac{r_j}{\max(1,N_j)c_j},
\]
然后选择得分最大的未完成端点。它尝试让一个参照的观测为多个证书服务。局部代理并非真实统计前沿，没有新增的全局最优性定理。

其后另做672条原开发环境中的多见证/Thompson/KL收益核探索，没有稳定的大改进，未替换主候选，也未把这些开发结果当成独立检验。因此有效开发总计1248条，独立主测试仍是冻结的12,672条。

## 4. 新独立小规模测试

### 4.1 公平条件

- 每场景48次重复。通常T=14,000，many_new为18,000，serial_arrivals为15,000；最终臂数最多25。
- 11个Bernoulli场景、1个低方差有界两点场景。不同政策共享相同潜在臂奖励流，不被强迫选相同动作。
- 全历史UCB、Growing-MOSS、MC-MOSS、截断MC-MOSS、Thompson、KL-UCB均保留自己的收益动作，**没有插入认证服务或预算限制**；只附加相同有效报告器，用于额外诊断未决量。
- ALLplus与CCP、Shared使用相同报告工具、服务周期、检查点兜底、MC-MOSS收益核和指数差预算。它是自然的历史保留ALL-ε适配，不是FAREAST/(ST)^2的原版实现。
- “UCB”使用稿件指定的sqrt(3log(2t)/n)指数；Growing-MOSS使用t/(Ktn)的当前时钟；MC-MOSS按竞争臂数翻倍重新校准虚拟时钟但不删除数据；KL-UCB使用Bernoulli KL指数；TS使用Beta(1+S,1+n-S)。非Bernoulli场景的分数Beta更新是启发式，不能称为正确Bayesian后验。
- 下面的跨场景数字是12个场景均值的描述性平均，不是对一个统一分布或minimax风险的估计。ε、η及终点在场景间不同，全部逐场景表同时提供。

### 4.2 描述性平均

__TABLE__

相对同预算ALLplus，默认CCP的平均面积下降20.56%，regret下降2.80%；12个场景的面积点估计全部下降，6个场景两个点估计同时下降。

预先选中的Shared相对CCP，平均面积只下降0.39%，regret增加1.98%；8个场景面积下降，但仅1个场景两个点估计同时下降。**这不足以宣布Shared取代CCP。** 其中边界场景与低方差场景，Shared的两个指标都变差；改善场景regret增加较明显。全部不利结果均保留。

纯收益TS在本组多数场景regret最低；它未承担主动认证的服务要求，未决面积也明显更大。CCP并没有在纯regret上击败TS/MOSS，这不应被隐藏。全历史UCB与CCP平均regret接近，CCP的平均面积低24.75%。

较高预算或不拒绝服务可降低面积但提高regret。对CCP与Shared，本组β=4已与无拒绝配置产生相同端点结果，因此不是两个不同的有效权衡点。连线只连接配置，不证明中间高概率服务预算可由均值线性插值得到。

### 4.3 全部场景 regret

__REGTAB__

### 4.4 全部场景面积（千臂时间）

__AREATAB__

完整标准误、经验95%分位、服务次数、服务regret和失败数在 `holdout-summary.csv`；配对差与逐比较95% t区间在 `holdout-paired.csv`。均值Pareto图不是高概率约束前沿的验证。

### 4.5 失败与复核

全部12,672条运行未出现错误标签，但部分运行有置信覆盖失败和空区间回退。默认CCP/Shared/ALLplus各576条中，9条覆盖失败、2条空交集。这些轨迹仍进入全部统计。跨方法共享奖励流，不能把它们当成独立重复来证明极小错误概率。

单个场景48次零标签错误的单侧95%二项上界约为0.0605，不能靠这一小实验验证δ=.05，更不能验证全环境全过程可靠性。实际保证来自置信过程的数学论证。

实现接口与冻结模拟引擎共112,000轮逐动作、服务标志、样本计数一致。另有ABM10,000轮实现检查，但不是ABM在其渐近定理族上的性能比较。

## 5. 真正求解了小模型的完整前沿，但没有冒充通用算法

构建了有限行为状态的线性规划：优化同一策略的动作流，使用每个候选环境的终点regret和“标签出错或面积超标”指示量作约束，而不是用平均面积替代概率。

一个静态两臂四环境诊断，候选均值向量为(.01,.99)、(.99,.01)、(.4,.6)、(.6,.4)，T=10，ε=.95，η=.01，δ=.1。固定报告器使用原始、未跨时间相交的beta-mixture置信区间，并将δ/2用于报告；这不是CCP实际使用的区间交。得到：

| 面积预算a | 最小最坏期望regret |
|---|---:|
| a≤12 | 不可行（对该固定报告器） |
| 13 | 1.1443575 |
| 14 | 0.6991625 |
| 15–20 | 0.6970063 |

另一个两臂到达诊断，第二臂在第4轮到达，T=12，其余同上，a≤8不可行，a=9时最优regret为0.5647346，a=10–18时为0.5396202。

这些数值由同一动作概率策略重新逐环境前向传播验证，最大LP/前向误差在约1e-11或更小。它们是浮点优化结果，不是有理算术证书。早期其他诊断模型的不可行结果与一次求解器数值失败也保留，没有混入成功结果。

**信息边界：**求解器知道四个候选环境、终点和指定日程，实际均值环境未知；报告器固定并且完整bounded模型可靠。它不是未知未来的大规模CCP，也没有优化所有可能的报告检验。有限模型的行为策略/序列形式LP是已有原则，这里作为“真的有一个最优前沿可以核对”的实验标尺。

## 6. 创新性评价

按指定 `statistical-innovation-assessment` 的三级十分制，本轮新增成果整体定位为：

**第二级，5.8/10，理论创新为主；新颖性判断置信度中等。**

| 新增内容 | 分数 | 定位理由 |
|---|---:|---|
| 未知任务失效时间导致的逐日程前沿分离 | 5.8 | 给出具体信息障碍，限定“整个前沿”的合法比较对象；不是泛泛说没有万能算法 |
| 任意恢复数量s的同时信息下界 | 4.5 | 改进与任务选择相匹配的技术接口；基本工具仍是已有后验/信息论方法 |
| ABM与大段中间面积预算匹配 | 5.7 | 从两个端点推进到按实际完成数量定价的连续预算区间，但限于指定更新族且有加性基准项 |
| 有限模型精确前沿LP | 3.1 | 标准行为策略/约束决策工具的系统适配，不是新的全局算法原理 |
| Shared/Bundle/多见证工程算法 | 3.0 | 没有建立新的最优性或稳定取代CCP的实证优势，不抬成主要方法创新 |
| 固定β不能覆盖快速区间 | 2.5 | 既有谱保护与既有快速下界的直接推论 |

总体不是以上分数的平均或相加；主要由信息基准分离与中间预算匹配支撑。不把先前谱minimax、已有两端权衡或旧CCP证明重新计分。

最邻近研究核查包括：Mason等的全部相对近优识别；Yang–Tan–Jin的最小regret最佳臂识别；Zhong等的固定时域regret–BAI错误率前沿；Cho等的收益驱动好臂识别；Kanarios等的异质采样成本BAI；von Stengel的行为策略计算。它们分别覆盖已使用的目标、成本和优化工具；本轮不能以“同时优化两个目标”或“凸规划分配”本身宣称新颖。

**实际评分次数为1；未完成五轮隔离上下文重复。** 没有报告虚构均值、方差或一致意见。未穷尽所有在线调度与序贯实验文献，也没有独立同行审查，因此不把5.8视为客观测量或录用预测。更高分需要真正更广的因果前沿刻画，或一个在同任务强基线上稳定改善的新分配原则。

## 7. 本轮结论

“再做一个更复杂的CCP就必然达到全部前沿”没有得到支持。真正需要分清的是：未知未来与逐日程优化比较者的信息差；需要完成多少项临时任务；以及哪些采样只是局部代理认为有用。

本轮的理论已经超出旧的两个端点，但实践算法没有确认新的统治性赢家。**目前仍建议保留CCP作为主要实际候选、保留Shared等不利对照，把新增理论作为前沿边界与部分匹配，而不是将三种不同算法的长处合并宣传为一个完整最优算法。**

参考及完整证明见 `theory_frontier.md`；版本、异常和未闭合接口见 `proof_audit.md`。
'''
text=text.replace('__TABLE__',table).replace('__REGTAB__',regtab).replace('__AREATAB__',areatab)
(P/'研究报告_前沿与算法.md').write_text(text,encoding='utf-8')
env=dict(python=sys.version,platform=platform.platform(),libraries={m:importlib.import_module(m).__version__ for m in ['numpy','scipy','pandas','numba','sympy']})
(P/'environment.json').write_text(json.dumps(env,indent=2))
refs=[
 dict(id='Mason2020',title='Finding All epsilon-Good Arms in Stochastic Bandits',url='https://arxiv.org/abs/2006.08850',scope='fixed-arm relative near-optimal set identification; primary abstract and prior project model audit'),
 dict(id='Yang2026',title='Best Arm Identification with Minimal Regret',url='https://www.jmlr.org/beta/papers/v27/24-1612.html',scope='single-best fixed-confidence minimal regret; primary publication abstract'),
 dict(id='Zhong2023',title='Achieving the Pareto Frontier of Regret Minimization and Best Arm Identification in Multi-Armed Bandits',url='https://arxiv.org/abs/2110.08627',scope='fixed-horizon regret/terminal BAI error, not cumulative unresolved-arm-time'),
 dict(id='Cho2025',title='Reward Maximization for Pure Exploration',url='https://proceedings.mlr.press/v258/cho25a.html',scope='fixed-threshold GAI with anytime tests/reward allocation'),
 dict(id='Kanarios2024',title='Cost Aware Best Arm Identification',url='https://rlj.cs.umass.edu/2024/papers/Paper193.html',scope='heterogeneous testing costs and asymptotic BAI, not our cumulative maintenance protocol'),
 dict(id='vonStengel1996',title='Efficient Computation of Behavior Strategies',url='https://doi.org/10.1006/game.1996.0050',scope='sequence-form LP; linear in tree size, not polynomial in horizon'),
 dict(id='Basu2006',title='Algorithms in Real Algebraic Geometry',scope='standard real quantifier elimination, imported only for theoretical finite computability')]
(P/'literature.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2))
files=['theory_frontier.md','holdout-freeze.json','holdout-summary.csv','holdout-paired.csv','proof_audit.md','literature.json','研究报告_前沿与算法.md']
evidence={f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in files}
(P/'evidence-packet.json').write_text(json.dumps(dict(files=evidence,scope='this round incremental contributions; not the unseen Codex-revised manuscript'),ensure_ascii=False,indent=2))
assessment=dict(schema_version=1,object='this round incremental research',date='2026-10-16',basis='current',model='GPT-6 Astra Pro',model_snapshot=None,
 protocol_source='zdacongming-glitch/statistical-innovation-assessment',execution_method='single_current_context',actual_assessments=1,planned_independent_repeats=5,independent_repeats_completed=False,variance=None,standard_deviation=None,
 contributions=[dict(id='causal_frontier_separation',tier=2,score=5.8),dict(id='partial_recovery',tier=2,score=4.5),dict(id='ABM_intermediate_budgets',tier=2,score=5.7),dict(id='exact_finite_LP',tier=3,score=3.1),dict(id='engineering_schedulers',tier=3,score=3.0),dict(id='fixed_beta_obstruction',tier=3,score=2.5)],
 overall=dict(tier=2,score=5.8,rationale='Core novelty is the explicit future-information obstruction and the completion-count-dependent intermediate-budget matching. Not a complete general frontier and not a universally superior practical method.'),
 novelty_confidence='medium',verification='self-contained written proofs and internal diagnostics; no isolated agent/external peer/formal verification',evidence_files=evidence)
(P/'assessment.json').write_text(json.dumps(assessment,ensure_ascii=False,indent=2))
print('report chars',len(text),'valid development',sum(len(pd.read_csv(P/f)) for f in ['development-round1.csv','development-round2.csv','development-round3.csv']),'test',len(df))
