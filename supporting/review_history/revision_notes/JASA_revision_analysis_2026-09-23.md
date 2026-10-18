# MAB-AA：JASA 审稿诊断与修订方案

日期：2026-09-23。本文是内部诊断与修订建议，不是已经完成修改后的正式回复信。

## 1. 总体判断

这次需要结构性重修。AE 把与 KNS（Kleinberg、Niculescu-Mizil、Sharma，2010）的区别作为主要录用障碍；R2 则指出会影响主定理成立的证明问题。还必须处理实验实现与论文算法不一致的问题。三条线都需要完成，不能用写作改进替代其中任何一条。

建议优先顺序是：先确定正确的算法、时间尺度和可复现结果，再修复证明，最后围绕真正能够支持的新贡献重写文章与回复信。现阶段不宜坚持“提出一个此前没有研究的问题”或“标准 UCB 无法处理该问题”的主张。

有保留价值的部分包括：新臂逐级筛选的思路、单调可用性下永久淘汰的可能性、到达时间与识别代价的细分分析，以及 AE 特别指出的 Theorem 5。但这些是值得继续发展的内容，还不能据此判断重投一定成功。

来信的决定是 Reject and resubmit，按新稿处理。按 2026-09-22 起六个月计算，计划截止日期为 2027-03-22，最终以投稿系统显示为准。来信要求的匿名逐点回复文件属于之后的投稿准备事项。

本次核查覆盖：

- [主稿及其同文件中的补充材料](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex)，共 4235 行。
- [R2 完整审稿报告](D:/博士学习/科研/git/MAB-AA/Reviews_JASA-RA-2026-0866.pdf)，5 页，已检查文字与页面公式。
- 用户粘贴的编辑、AE、R1 来信。
- 用户提供项目目录中的 `simulation_final` 源码、最终配置、100 次重复的原始结果及汇总结果。
- KNS 2010 原文和 Ghalme 等人的 ballooning bandits 原文。此次是围绕审稿意见的重点核查，不是整个领域的穷尽性创新性检索。

## 2. 审稿意见逐条对应

P0 表示会影响定理有效性、实验解释或重投主线；P1 表示必须补足的实证和定位；P2 表示表达与组织。

| 意见 | 分类与优先级 | 核查判断 | 修订动作 |
|---|---|---|---|
| AE / R1.1：相对 KNS 的新意不足 | 创新与定位，P0 | 核心批评成立；现有“单调增长”说明不足 | 明确包含关系和基准等价性；提供同条件下的实质增量 |
| AE：Theorem 5 可能有区别 | 理论定位，P1 | 是可发展的方向，不等于已获认可 | 保留到达分块结构，检查可行参数范围，并寻找同一实例类的上界 |
| R1.2：复杂淘汰机制的必要性 | 方法与实验，P0 | 只战胜 NE / D-SE 不足以回答 | 加入 AUER、简单 UCB 加淘汰和短间隔接纳基线 |
| R1.2：G-UCB 近线性是否异常 | 理论解释与实现，P1 | 固定到达率使臂数线性增长，既有保证不强制次线性 | 明示 $K_T$ 的增长；检查标准实现并区分固定臂数与持续到达实验 |
| R1.3：引言跳跃、符号密集 | 写作，P2 | 成立 | 分离 Related work；增加符号表和算法时间线 |
| R2.1(a)：分解遗漏早期误删损失 | 正确性，P0 | 按当前定义确实存在 | 重写路径分解、基准及坏事件控制 |
| R2.1(b)：分开展示三类 regret | 实验，P1 | 有助于判断实际问题来源 | 记录轮内学习、接纳延迟、早期误删三个分量 |
| R2.2(a)：轮数与真实预算不匹配 | 算法与正确性，P0 | 指出的指数采样尺度成立；实代码还有轮数结束后的利用阶段 | 改以实际拉臂时间为主；公布轮起止时间和预算耗尽规则 |
| R2.2(b)：为何必须等待越来越长的轮 | 算法设计，P0 | 现有稿件没有说明该代价必要 | 将接纳频率与淘汰精度解耦；与固定间隔接纳比较 |
| R2.2(c)：辅助完成时间代替实际时间 | 正确性，P0 | 现有证明没有建立必要的可比关系 | 按真实采样预算做重启或直接构造 anytime 规则 |
| R2.3(a)：$G_3$ 索引替换错误 | 正确性，P0 | 反例成立 | 删除无效的按最终 gap 压缩步骤，重做路径代价和总和分析 |
| R2.3(b)：随机淘汰链概率 | 正确性，P0 | 对固定链取最大值不能控制所有链的并集 | 建立统一置信事件或合法的首次错误事件界 |
| R2.3(c)：最优臂定义与式 (18) | 正确性，P0 | 定义不一致；记录过均值不代表算法执行过比较 | 区分全体已接纳最优臂与活跃最优臂；让证明事件对应实际比较 |
| R2.4(a)：MOSS 比较、长期性能、活跃集价值 | 实验与意义，P0/P1 | 现有结果不支持全面优越；代码停止接纳使解释更需修正 | 修复实验口径后重跑，加入长期、候选池质量及实际成本 |
| R2.4(b)：参数和 MOSS 指数不一致 | 可复现性，P0 | 不止正文与附录冲突；实际配置还有第三种取值 | 以配置与源码统一生成实验说明 |
| R2.4(c)：未给出 $M$ | 可复现性，P0 | 最终配置查到场景 1 为 5，场景 2 为 4 | 报告计划轮数、实际完成轮数及截止后的行为 |
| R2 Minor 1：分辨率、均值、phase、轮数、经验均值与分臂 regret 定义 | 表达及接口，P2 | 应全部修正，其中经验均值口径影响证明 | 明确 $\widetilde\Delta_m=2^{-m}$、$0{:}M$ 共 $M+1$ 轮及统计量公式 |
| R2 Minor 2：图表格式 | 表达，P2 | 接受 | 统一数学标签、图例、字体与置信区间说明 |

## 3. 如何回应 KNS：承认包含关系，寻找更具体的贡献

### 3.1 基准的区别不能作为主辩护

KNS 的 stochastic sleeping bandits 使用按均值排序的可用臂选择规则作为比较对象，其 AUER 是在当前可用臂上运行的 UCB 规则。Theorem 10 是相邻均值间距的对数上界；由 Theorem 12 的截断式可推出带 $\log T$ 的平方根上界。R1 对无对数平方根阶的概括不够精确，但这不足以化解其主要批评。[KNS 原文，Algorithm 2、Theorems 10/12](https://link.springer.com/content/pdf/10.1007/s10994-010-5178-7.pdf)

下面是对本文的直接推论。对截至固定时间 $T$ 到达的有限臂集按真实均值降序排列，记该排列为 $\sigma^\star$，则逐时有

$$
r_{\sigma^\star(\mathcal A_t)}=\max_{i\in\mathcal A_t}r_i.
$$

因此，本文的 expected dynamic pseudo-regret 与这个 stochastic best-ordering comparator 相同。这里讨论的是固定均值、对均值的 regret；不把它混同于对随机实现奖励事后取最大值的另一种基准。

KNS 固定有限臂池与本文潜在无限臂池存在形式差异，但 AUER 指数本身不依赖事先知道所有臂的名称；新臂到达时初始化统计量即可。这个差异不能单独承担主要创新。

Ghalme 等人的 ballooning bandits 已明确研究臂集增长和 best-currently-available benchmark，并基于最优臂到达等分布条件设计停止接纳的策略。因此，“首次定义增长臂集及该 regret”尤其不宜保留。[Ghalme 等，原文](https://arxiv.org/pdf/2001.10055)

### 3.2 可发展的两条贡献路线

**优先考察：持续接纳下的安全筛选与淘汰。** 单调可用性的实际作用是：一旦一个臂被可靠证明劣于某个永久可用臂，它不会因对手休眠而重新成为必要选项。应把这种结构转化成可证明的淘汰正确性、筛选采样代价、候选池质量和维护成本。简单 AUER/UCB 加同样的淘汰规则是必须比较的强基线。

**另一条：到达路径决定的更细 regret 复杂度。** 与其只报告 $K_T,T$ 的经典平方根阶，不如刻画剩余可用时间、近优竞争持续时间及真正改变 benchmark 的到达。需要证明比同一环境中的直接 UCB 分析更有信息，最好与同一实例类上的下界对应。仅比 KNS 的一个较粗通用上界小，还不等于算法更优。

这两条都是待验证的研究路线。若简单 UCB 加淘汰已经达到拟议全部性质，应继续找实质增量或收缩论文主张，不能靠给标准机制换术语解决新意问题。

## 4. 理论修订的具体入口

### 4.1 先统一三个集合及 regret 分解

现稿把最优臂定义在 [活跃集合 $B_m$](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:446) 上，但后文又按从未删去任何已接纳臂的基准推导。这会使 gap 的单调性和“之前已被删除的最优臂”论证冲突。

令 $a_m=\max_{i\in A(m)}r_i$ 表示全体已接纳臂的最佳均值，$b_m=\max_{i\in B_m}r_i$ 表示该轮起始活跃集最佳均值。逐路径成立的分解是

$$
R_{T_0}
=\underbrace{\sum_m\sum_{t\in\mathcal I_m}(b_m-r_{I_t})}_{\text{轮内学习损失}}
+\underbrace{\sum_m\sum_{t\in\mathcal I_m}(r^*(t)-a_m)}_{\text{新臂接纳延迟}}
+\underbrace{\sum_m L_m(a_m-b_m)}_{\text{此前误删导致的损失}}.
$$

建议在内部分析和实验中保留三项；正文也可将第一、第三项合并成相对全体已接纳臂的学习 regret。无论如何，不能省掉第三项。[现有两项分解](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:554)

一条可能的证明路线是在统一置信事件上证明最优已接纳臂始终保留，因而第三项为零；再控制坏事件贡献。固定采样预算 $T$ 时可用 $T\Pr(\mathcal E^c)$。若保留随机停止时间 $T_0$，需要界住 $\mathbb E[T_0\mathbf1_{\mathcal E^c}]$，不能直接把它换成 $\mathbb E[T_0]\Pr(\mathcal E^c)$。

### 4.2 $G_3$ 反例应接受，但不能过度推断

[错误步骤](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:2349) 用 $\widetilde\Delta_{m_i}$ 替代应与 gap 对应的 $\widetilde\Delta_{\widetilde m_i}$。Assumption 1 只限制识别以后的 gap 放大，不限制识别以前长时间的小 gap，所以它不能排除 R2 的例子。

初始两个臂的均值是 $1/2$ 与 $1/2-2^{-M}$，第 $M$ 轮接纳均值 $0.9$ 的新臂。对原次优臂，有 $m_i=M$、$\widetilde m_i=3$，且 Assumption 1 可取 $\widetilde C=1$。其历史代价

$$
\widetilde S_i=n_{M-1}2^{-M}=\Theta(2^M)
$$

不能用现稿写出的 $O(\log N/\Delta_i(M))=O(M)$ 控制。按 $N=30n_M$ 的原始隐式校准数值核验如下；这是公式核验，不是额外随机仿真。

| $M$ | 实际定义的 $\widetilde S_i$ | 声称的单臂上界 | 比值 |
|---:|---:|---:|---:|
| 12 | 14846.57 | 1653.97 | 8.98 |
| 16 | 237545.11 | 2098.42 | 113.20 |
| 20 | 3800721.82 | 2542.10 | 1495.11 |

它否定了当前单臂上界和由此出发的证明，不直接否定最终所有平方根总 regret 结论。反例中总采样量也在指数增长，平方根量级仍可能通过另一种论证得到。

建议保留 $G_3$ 的历史 gap 加权采样项，尝试直接对真实采样次数求和，或分别处理识别前小 gap 代价与识别后代价。若必须新增限制，应明确是增加假设，并验证它是否排除了文章最想处理的突变到达。不能把它作为原 Assumption 1 的等价改写。

### 4.3 随机淘汰链与不存在的比较

[式 (30) 对应源码](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:2156) 实际需要控制“存在一条数据依赖的坏链”。一般只有

$$
\Pr\!\left(\bigcup_{\gamma}E_\gamma\right)
\le\sum_{\gamma}\Pr(E_\gamma),
$$

不能换成对固定链概率界取最大值。直接枚举所有链可能代价过大，更合适的入口是统一置信事件、首次错误淘汰事件，或针对随机选择合法的集中不等式。新的置信预算会改变 $N$、样本量和常数，必须一起重算。

[式 (18) 对应源码](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:1997) 使用已删除臂的历史 LCB。仅仅“保存了这个均值”不能推出新臂与它比较过。若要使用永久历史证书，应把它明确加入算法并重新分析、重跑；否则只能基于当前实际参考集证明。

### 4.4 真实拉臂时间应成为主时间尺度

[online 证明](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:2590) 明确把 $T$ 设为补完最后阶段后的期望采样量。由于 $M_\ell=2^\ell$ 而样本目标含 $4^{M_\ell}$，对轮数翻倍不能视为对样本预算翻倍。

更稳妥的修订路线是按实际拉臂预算 $1,2,4,8,\ldots$ 构造阶段，或直接使用随时间有效的置信界。两者都仍需处理阶段截断、已有臂数据保留、到达臂接纳和坏事件，而不是把现有推论中的符号 $T$ 替换一下。

还需检查 [静态例子](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:3709) 中“给定 $T$ 选 $M$”之后是否真能在 $T$ 次拉臂内完成；同类时间尺度问题并不限于 online 一节。

### 4.5 一个值得优先尝试的简化：短接纳周期

下面是根据本文单调 benchmark 得到的直接计算。如果新臂从到达到接纳的等待不超过 $H$ 次拉臂，且每次 benchmark 提升幅度为 $\beta_j\ge0$，则纯接纳延迟满足

$$
D_T^{\mathrm{arrival}}
\le H\sum_j\beta_j
\le H,
$$

因为奖励均值位于 $[0,1]$，单调 benchmark 的总提升不超过 1。这一界不包含估计错误、排队筛选和误删代价，也不自动给出完整 regret 定理。

这说明，应认真考虑把“每隔多久接纳新臂”与“估计精度如何加深”分开设计。它能直接回应 R2.2(b)，并可能替代目前很难解释的 Assumption 2。必须允许筛选任务被中断或重新调度，不能只把仍然无法参与选择的新臂在符号上宣布为已接纳。

### 4.6 下界还需补两项审计

**Theorem 5 的可行范围。** [构造条件](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:1238) 要求均值逐块升高且留在 $[\gamma,1-\gamma]$。因此存在总抬升预算，特别有

$$
\sum_{m=1}^{K_T}\varepsilon_m\le1-2\gamma.
$$

若同质化推论令 $\varepsilon_m\asymp\sqrt{K_T/T}$，则必须有 $K_T^{3/2}/\sqrt T=O(1)$，即 $K_T=O(T^{1/3})$。这限制的是该构造与该推论的可行区域，不是说所有 arriving-arm 问题都有这个限制。正文应写出非空参数例子，避免把它宣传为任意增长速度下的统一匹配下界。

**增长臂数下的 uniform goodness。** [定义](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:1004) 对随 $T$ 扩张的整个实例族取 supremum，再要求对所有 $a>0$ 都是 $o(H_{\min}^a)$，比固定有限实例族的通常条件更强。在固定 gap 且臂数按 $H_{\min}$ 的正幂增长时，它会与 $K_T\log H_{\min}$ 下界冲突。应确认所讨论增长区间内满足前提的策略确实存在，不能只用 $K_T=o(T)$ 概括适用范围。

另外，[NE 的“失败例子”](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:3744) 目前主要证明的是某个 regret 上界表达式 $B_{A2}$ 很大。上界很大不推出实际 regret 很大。若要声称线性 regret，须直接证明该算法实际强制采样造成的下界；否则改成“现有上界不能保证次线性”。

### 4.7 随机轮边界的处理

即使原始到达过程是外生的，按算法随机轮边界形成的 $A_m,t_i,m_i$ 仍可能依赖观测。再加上现稿用活跃集定义最优臂，若直接把这些量当成固定参数套逐臂 Hoeffding 界，需说明合法性。定理应清楚区分确定性日历到达、算法产生的轮划分，以及界中哪些量需要取期望。单纯条件化在整条随机轮划分上并不能自动保留未选择样本的分布性质。

## 5. 实验审计：已确认的事实

### 5.1 六张图的来源已确定

对论文六张 `scenario_C/E_*.png` 逐个计算 SHA-256，均与以下目录内对应图文件字节一致：

[最终结果目录](<D:/博士学习/科研/Projects/Bandit with Arriving Arms/simulation_final/outputs/final>)。

因此，下表不是根据图形外观推测参数。进一步使用该目录配置、主种子 `20260309`，复跑两个场景各 `replicate=1,2,3`，六个 UCB-AA regret 均与存档 CSV 数值一致。该验证覆盖六次重复，不冒充重新运行了全部 100 次实验。

### 5.2 论文描述、实际配置和实际算法的差异

| 项目 | 论文 | 对应图的实际配置 / 当前源码 |
|---|---|---|
| 场景 1 到达过程 | Poisson | Bernoulli，概率 0.005 |
| 场景 1 的 $r_0$ | 正文 0.6，附录 0.7 | 0.7 |
| 场景 1 的轮数 $M$ | 未报告 | 5，执行轮次 $0,\ldots,5$ |
| 场景 2 初始与新到达近优臂 | 正文 $[0.7,0.8]$，附录 $[0.89,0.90]$ | $[0.75,0.90]$，因为 `mu_top=0.9, Delta_min=0.15` |
| 场景 2 的轮数 $M$ | 未报告 | 4，执行轮次 $0,\ldots,4$ |
| Growing MOSS 指数 | 正文使用 $T$，附录使用 $t$ | 使用当前 $t$ |
| UCB-AA 正式淘汰参考集 | 当前合并活跃集 $B_m^p$ | 若旧臂集非空，使用旧臂集 `C_prev` |
| 老臂在低精度筛选中的经验均值 | 写作 $\hat r_i(n_p)$ | 使用全部已有观测的均值 |
| 完成 $M+1$ 轮之后 | 未说明继续到固定 $T$ 的行为 | 固定 `exploit_pool`，其后新臂只进入 buffer，不再接纳 |

配置依据：[场景 1](<D:/博士学习/科研/Projects/Bandit with Arriving Arms/simulation_final/outputs/final/scenario_C/config.json>)、[场景 2](<D:/博士学习/科研/Projects/Bandit with Arriving Arms/simulation_final/outputs/final/scenario_E/config.json>)。实现依据：[均值与淘汰](<D:/博士学习/科研/Projects/Bandit with Arriving Arms/simulation_final/algos.py:102>)、[正式阶段参考集](<D:/博士学习/科研/Projects/Bandit with Arriving Arms/simulation_final/algos.py:198>)、[MOSS](<D:/博士学习/科研/Projects/Bandit with Arriving Arms/simulation_final/algos.py:247>)。

还有两个应修正的实现接口：预算在 phase 中途耗尽后，代码仍可能用原定完整 phase 的半径进行最后一次淘汰，影响最终 active-size 统计；计划 $M$ 会被 `n_M <= 0.2T` 的启发式裁剪，但 $N$ 在裁剪前计算。这两个行为应写明或修正，不能只报告输入 $M$。

### 5.3 停止接纳足以改变“小活跃集”的解释

[相关代码](<D:/博士学习/科研/Projects/Bandit with Arriving Arms/simulation_final/algos.py:144>) 完成设定轮数后进入纯利用。复跑结果：

| 场景 | 重复 | 完成最后一轮的时间 | 此后利用次数 | 总到达臂数 | 从未接纳的臂数 |
|---|---:|---:|---:|---:|---:|
| 1 | 1 | 9323 | 50677 | 317 | 291 |
| 1 | 2 | 20895 | 39105 | 309 | 249 |
| 1 | 3 | 16261 | 43739 | 320 | 277 |
| 2 | 1 | 4682 | 55318 | 324 | 296 |
| 2 | 2 | 7466 | 52534 | 316 | 277 |
| 2 | 3 | 8730 | 51270 | 327 | 287 |

例如场景 1 第一个重复只接纳 26 个臂，停止探索时尚未出现任何一个预定 step arm；最终 291 个臂根本没有进入筛选。场景 2 第一个重复在 4682 次采样后就开始余下 55318 次利用。

停止接纳本身可以是一种合法策略，但需要被明确建模、分析和比较。它不同于文中强调的持续接纳与筛选。因此现有 regret 优势不能全部归因于 pre-elimination，小活跃集也不能全部解释为已认证淘汰了大多数到达臂。

指标需要至少区分：已到达、待接纳、已接纳待筛选、正式活跃、已认证淘汰，以及误删的臂。当前 active size 在轮结束才更新，不能直接代表筛选期间的工作集大小。实现还保存已采样臂的计数与和，故小 active set 不自动等于内存占用小。

### 5.4 原始结果支持什么

以下是最终目录中原始 100 次重复的汇总，不是修订后算法的结果。

| 场景 | UCB-AA regret | G-MOSS regret | UCB-AA wasted pulls，阈值 0.1 | G-MOSS wasted pulls，阈值 0.1 |
|---|---:|---:|---:|---:|
| 1 | 5139.94 | 2036.72 | 8225.18 | 3331.00 |
| 2 | 1880.88 | 2043.75 | 3264.08 | 5010.18 |

场景 1 的 regret 差距较大，不能描述为 G-MOSS 仅“略好”。场景 2 的 UCB-AA 均值较低，但其方差和算法口径都需一起考虑。

基于共同随机数重复计算 `UCB-AA - MOSS` 的配对均值差及正态近似 95% 区间：场景 1 为 3103.22，区间 [2443.96, 3762.48]；场景 2 为 -162.87，区间 [-320.08, -5.67]。这些区间仅描述存档这套实现；不用于替代修订后的确认实验，也不据此宣称普遍优越。

### 5.5 对 G-UCB 近线性的解释

[G-UCB 源码](<D:/博士学习/科研/Projects/Bandit with Arriving Arms/simulation_final/algos.py:214>) 中可见的指数是标准的 $\hat\mu_i+\sqrt{2\log t/n_i}$；目前没有在这段指数计算中发现导致线性曲线的明显错误。这里不声称已经完整验证所有实现细节或复跑所有基线。

两个场景的固定到达率使

$$
\mathbb E[K_T]=K_0+0.005T+O(1).
$$

因此固定臂数下的次线性结论不能直接套在这条增长路径上。进一步，G-UCB 和当前 G-MOSS 都至少首拉每个新臂一次；如果持续有正比例新臂与 incumbent 存在常数 gap，这些首拉本身就可累积线性探索损失。这是可以回应 R1 的关键澄清，并非 dynamic regret 目标不匹配。

存档中 G-MOSS 的 $R_t/t$ 也大致稳定在 0.034 左右，说明“regret 数值更小”与“具有次线性增长阶”必须分开讨论。

最后，当前场景 1 插入的均值为 0.75、0.80、0.85，而背景好臂可接近 0.80。第一次插入不保证提高 benchmark。修订实验必须记录真实 benchmark 跳点，或生成保证超过当前最佳均值的 step arms。

## 6. 必须补做的实验与可澄清项

### 6.1 先做口径修复，再补性能实验

1. 冻结一个与伪代码一致的参考实现；区分旧稿存档实现、修订算法与明确标注的实用变体。
2. 在真实 $T$ 次采样停止，记录完整与未完成的 rounds / phases，禁止把部分 phase 当成完成的认证。
3. 持续接纳方案必须真的接纳后续臂；若保留 cutoff 策略，把 cutoff 作为明确设计变量，并加入具有相同 cutoff 的对照来分离收益来源。
4. 保存每次 admission、screening、elimination、benchmark jump 的时间及证书；由此计算三项 regret、误删概率和等待时间。
5. 统一当前时刻到达与决策先后顺序；现代码先选择旧可见臂、再揭示该步到达，文中的策略定义应与此一致。

### 6.2 核心基线

| 基线 | 作用 |
|---|---|
| AUER，按 KNS 原始置信系数 | 直接回应 AE / R1 |
| Growing UCB1 | 保留现有标准指数对照 |
| UCB + 置信淘汰 + 固定间隔接纳 | 回应 R2.2(b)，检验复杂筛选是否必要 |
| G-MOSS，分别标明 current-$t$ 与 known-$T$ 版本 | 防止把不同算法当成同一实现；增长臂数版本的保证须另核查 |
| UCB-AA 去掉预筛选 | 仅作机制消融，不承担全部优越性证据 |
| 保留 incumbent 所有样本的异步筛选变体 | 检查预筛选、接纳周期和旧样本利用各自作用 |

基线参数应事先规定合理范围，或使用独立调参种子后冻结；最终评估不能继续根据测试结果选环境或参数。确认实验应使用未参与探索设计的重复种子，并报告配对差异。

### 6.3 环境与指标

环境至少覆盖：无到达、次线性增长的臂数、固定正速率到达、固定 gap 的劣臂流、近优到达、在长轮开头出现的突变好臂，以及 R2 的三臂反例。次线性增长与线性增长必须分别解释。

先保留 $T=60000$ 做旧稿到修订稿的可比检查，再增加多个更长 $T$，展示 $R_T/T$ 与时间曲线。不要仅凭较长区间上某两条曲线交叉就声称渐近阶更好。

除 regret 和 wasted pulls 外，记录：接纳延迟的分布与最大值、三项 regret、最佳臂误删率、候选池中最佳臂保留率、待处理队列、真正占用的统计量数量、每步更新时间和峰值内存。若“小活跃集”成为主贡献，还应报告单位维护成本下的 regret–成本关系；成本系数须有解释，不能临时挑选使某方法胜出的值。

接纳间隔 $H$、置信水平、计划与实际 $M$、理论与实用 $N$ 是必要敏感性分析。对于实际工作集，应把 pending 和 screening 中的臂纳入合适的成本定义。

### 6.4 可通过澄清解决、但不能替代实质修改的内容

- G-UCB 近线性与 $K_T=\Theta(T)$ 并不矛盾。
- 特殊情形本身值得研究，但必须说明研究它带来了什么更强或更具体的结果。
- R2 的 $G_3$ 反例否定当前证明步骤，不等于已经证明全部平方根界错误。
- NE / D-SE 的坏表现说明特定接纳和补齐策略可能浪费预算，不说明所有直接 UCB 方法失败。
- 当前图的参数可以从存档恢复，但恢复参数不能解决算法实现差异。

## 7. 文章重写建议

引言按“应用与已有设定 → 既有算法已经能做到什么 → 尚未解决的具体问题 → 本文可验证的新结果”组织。将长篇文献回顾移到独立 Related work。将 AID、DB 保留为现象解释时，应减少大写缩写带来的额外术语负担，避免把其命名本身列作贡献。

建议的正文顺序为：问题与已有基线；主要结果和适用范围；直观算法与伪代码；核心证明结构；到达结构下的下界；仿真与局限。主要结果用同一真实时间尺度和同一个 regret 定义。

增加一张符号表，明确区分日历时间 $t$、轮 $m$、phase $p$、阶段 $\ell$，以及全体可用、已接纳、活跃和待处理集合。算法图应画出新臂到达、进入 buffer、进入筛选、进入正式集合以及下一次接纳的具体时间。

将标准静态下界缩成引用或简短校验；把 Theorem 5 的具体意义、参数可行区域以及与上界是否同类对应讲清楚。不要把不同实例类、不同随机时间尺度上的上下界直接标成 matching。

如果最后的核心结果是安全筛选与实际维护成本，标题和摘要也应相应调整；不要先确定一个强标题，再补证据。

## 8. 建议执行顺序与阶段产物

| 阶段 | 工作 | 完成标准 |
|---|---|---|
| 第一步：恢复事实 | 配置、伪代码、源码、图、CSV 逐一对应 | 一个可复现清单；旧稿实现和修订实现明确区分 |
| 第二步：校正理论基础 | 定义、分解、反例、统一置信事件、实际时间 | 每条主结果标明：可保留、需重证、需改弱、删除 |
| 第三步：验证贡献 | 简单 UCB + 淘汰、短接纳周期、持续接纳实验 | 能具体回答复杂算法新增了什么，而非只胜过较弱消融 |
| 第四步：确定主线 | 到达路径复杂度或安全筛选 / 成本 | 至少一条正确、清晰、与最强相关基线可比的新结论 |
| 第五步：重投准备 | 重写正文、重跑确认实验、逐点回复 | 每条回复对应新定理、证明位置、图表或明确删改 |

建议先设置一个约两周的内部可行性检查点，重点看第三、第四步能否形成有说服力的结果；它不是对完整修改工期的保证。如果届时只能恢复经典 regret 阶，且简单 UCB 加淘汰覆盖全部优势，应重新评估重投 JASA 的投入，而不是只靠语言包装继续。

## 9. 回复信的工作草稿

以下使用“计划”“需要”口径，不能在尚未完成时改成“we have established / we have added”。正式重投时应逐项替换成确切的新结果和页码。

**给 AE / R1 的定位回应：**

> We agree that monotone arm availability is a special case of the stochastic sleeping-bandit framework and that the best-available-arm benchmark coincides with the mean-ordered comparator in this setting. Our revision should therefore make explicit what is gained from the monotonicity structure, beyond the existence of a sublinear regret guarantee. We plan to evaluate this through a direct comparison with AUER and a simple UCB procedure equipped with elimination and frequent admission.

**给 R1 关于 G-UCB 的回应：**

> The simulation environments use a constant arrival rate, so the number of arrived arms grows proportionally to elapsed time. Consequently, a regret guarantee stated for a fixed number of arms does not imply sublinear growth along these environments. We will distinguish these regimes explicitly and include experiments with fixed and sublinearly growing arm counts. We will also report the precise implementation and tuning of each baseline.

**给 R2.1 的回应：**

> We agree that, under the current definition using the active set, the residual regret includes both admission delay and losses caused by earlier erroneous elimination. The decomposition and subsequent analysis require revision. We plan to distinguish these components explicitly and provide separate control of erroneous elimination.

**给 R2.2 的回应：**

> We agree that completing an auxiliary stage does not by itself yield an anytime guarantee in terms of the actual number of pulls. The revision needs an analysis indexed by actual sampling time, including partial rounds and stages. We will also examine admission schedules that do not require waiting for an entire elimination round.

**给 R2.3 的回应：**

> The counterexample identifies a genuine failure of the stated intermediate bound for the third arm class. We will retain the pre-identification gap history in the analysis instead of substituting the terminal gap in that step. The data-dependent elimination-sequence argument and the comparison with an eliminated reference arm also require new justifications tied to the comparisons actually performed by the algorithm.

**给 R2.4 的回应：**

> Our initial audit has recovered the configurations associated with the reported figures and identified discrepancies between the manuscript and the implementation, including the behavior after the prescribed rounds have ended. We will align the algorithm specification, code, and parameter tables and regenerate the empirical comparisons before drawing conclusions about screening or active-set reduction.

R1.3 与 R2 minor comments 的正式回复应对应符号表、时间线、正文结构和图表格式的实际改动。所有尚未重证的结果应标为待处理，而不是在回复里预先宣称修复成功。

## 10. 高风险表述

| 避免 | 更准确的表述 |
|---|---|
| “MAB-AA 与 sleeping bandits 完全不同” | “研究单调可用性下的具体结构与收益” |
| “使用 dynamic regret，因此 KNS 不适用” | “当前随机平稳模型的基准可对应；区别必须来自更具体的结论” |
| “G-UCB 线性证明传统 UCB 不适用于本文” | “解释臂数增长和新臂首拉成本，并按增长区间比较” |
| “R2 只是误解了符号” | “承认定义与证明不一致，给出完整修订” |
| “反例证明最终平方根界必然错误” | “现有推导失效；最终速率需要独立重证” |
| “小活跃集证明内存低、筛选好” | “同时报告未处理臂、淘汰证书、候选质量和真实资源使用” |
| “NE 上界为线性，所以 NE 实际 regret 线性” | “直接证明实际损失下界，或仅说明该上界不提供次线性保证” |
| “仿真已经验证修订算法” | “当前只核实了存档实现；新算法需重新实验” |

本轮的结论建立在稿件与代码审计、六次重复复现和少量独立代数核验上。完整主定理的重新证明、修订算法和新增确认实验尚未完成；它们是本方案列出的下一阶段工作。
