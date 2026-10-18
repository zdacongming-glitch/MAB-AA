# Arriving-Arms Bandits：阶段性理论总结

日期：2026-09-27。本文整理当前研究状态。Part I 已按本轮补充证明更新；Part II、III 保留阶段性状态。

全文按三个层次组织：**Part I 用到达序列刻画最坏情形；Part II 在正则实例上追求更细的实例自适应；Part III 研究正则理论之外的边界。** Part I 的核心定理现已补证，当前最需要完成的是 Part II 的匹配上界。

本文依据《bandit思路修正》《分支 · bandit思路修正》以及原始模型框架整理。已明确放弃的算法与复杂度路线不再列入正文。原始框架中的一般工具，只保留对当前三层结构仍有直接作用的部分。

## 0. 证明状态与统一约定

本文使用以下标签，避免把一个值得研究的目标写成已经成立的定理。

| 标签 | 含义 |
|---|---|
| **theorem** | 在列明的假设和量词下成立的主要结论；提供证明要点，或明确指出沿用前序基本闭合结果 |
| **lemma** | 可独立核验、可以作为后续证明输入的结构事实 |
| **candidate** | 候选复杂度的匹配解释、候选正则类、算法骨架或尚未证明的主结论 |
| **open** | 仍需证明或明确规定的问题；不能作为已完成定理的前提而不加说明 |

证明状态以本文件及所链接的补充证明为准。Part I 的有限时域与 anytime 结论均已有明确证明；Part II 的有效下界与其是否可达仍分别标记。

### 0.1 原始模型

全局臂集可数。臂 $i$ 在外生时刻 $\tau_i\in\mathbb N$ 到达，此后永久可用：

$$
A_t=\{i:\tau_i\le t\},\qquad K_t=|A_t|,
\qquad \varnothing\ne A_t\subseteq A_{t+1},\quad K_t<\infty.
$$

允许 $K_t\to\infty$，但不要求它一定发散。有限时域分析固定一条确定的到达路径。独立于奖励与策略的随机到达可以条件于路径处理；依赖策略的内生到达不在本轮理论内。

臂 $i$ 的奖励流独立同分布，分布为 $P_i$，支持在 $[0,1]$，均值为 $\mu_i$；不同臂的奖励流相互独立。策略 $\pi$ 在第 $t$ 轮观察 $A_t$，根据过去历史选择 $I_t\in A_t$，只观察被选择臂的奖励。

统一记

$$
B_t:=\max_{i\in A_t}\mu_i,
\qquad \Delta_i(t):=B_t-\mu_i\quad(i\in A_t),
$$

$$
N_i(t):=\sum_{s=\tau_i}^{t}\mathbf1\{I_s=i\},
\qquad
R_T:=\sum_{t=1}^{T}\Delta_{I_t}(t),
\qquad
\mathcal R_T(\pi,\mu):=\mathbb E_\mu^\pi R_T.
$$

$R_T$ 是随机 pseudo-regret，$\mathcal R_T$ 是期望风险。一般分布时写 $\mathcal R_T(\pi,P)$。因为臂不消失，$B_t$ 非减，且每个已到达臂的 $\Delta_i(t)$ 非减；奖励分布本身没有发生非平稳变化。

**lemma 0.1 — Bernoulli 化。** 若模型类仅限制均值而允许所有 $[0,1]$ 支持的分布，则相应 bounded-reward minimax 值等于 Bernoulli 子类的 minimax 值。观察 $X\in[0,1]$ 后，另抽 $Y\mid X\sim\operatorname{Ber}(X)$，便有 $Y\sim\operatorname{Ber}(\mu)$。把 $Y$ 输入 Bernoulli 策略给出一个方向；Bernoulli 是子类给出另一方向。

因此 Part II 的信息公式先在 Bernoulli 模型中书写：

$$
\operatorname{kl}(u,v)
=u\log\frac uv+(1-u)\log\frac{1-u}{1-v}.
$$

这不意味着一般分布的实例最优信息复杂度只依赖均值；若追求分布级实例最优性，应使用 $D_{\rm KL}(P_i\Vert Q_i)$。

### 0.2 三种风险量词

固定到达路径，schedule-minimax 风险为

$$
\mathfrak R_T(\tau)
:=\inf_\pi\sup_{P}\mathcal R_T(\pi,P).
$$

在有限时域 minimax 定义中，可以允许策略知道 $T$ 与整条到达路径；若上界由不知未来到达的策略实现，结论更强。

Part II 的目标是找到**同一个不知真实均值的策略**，在每个正则实例上满足更小的风险界。不能用

$$
\inf_\pi\mathcal R_T(\pi,\mu)
$$

作为有意义的实例下界：单点取下确界允许把该实例的最优动作预先写进策略，值可以为零。严格实例相关下界应当对局部环境族取上确界，或明确要求同一个策略在真实环境与替代环境上都达到相应风险。

此外，

$$
\sup_P\mathcal R_T(\pi,P)=o(T)
$$

是 uniform no-regret；它强于逐个固定 $P$ 的 pointwise no-regret。下文不混用这两个概念。

---

## Part I — Arrival-only minimax

这一部分只问：**给定到达路径，不限制均值配置，最坏情形的学习代价是多少？** 它构成论文现已补齐核心证明的基础层，不依赖 Part II 的正则条件。

### I.1 Lifetime volume 与固定点

任取 $a\in A_1$ 作为记账用的 anchor；它不是一个均值已知的臂，也不要求它最优。对 $i\in A_T$ 定义

$$
H_{i,T}:=T-\tau_i+1.
$$

给定整数风险尺度 $r\in\{1,\ldots,T\}$，定义 long-lived arrival volume

$$
\boxed{
V_T(r):=\sum_{i\in A_T\setminus\{a\}}
H_{i,T}\,\mathbf1\{H_{i,T}>r\}.
}
$$

最终保留的 arrival-only complexity 是

$$
\boxed{
\Gamma_T(\tau):=
\min\{r\in\{1,\ldots,T\}:V_T(r)\le r^2\}.
}
\tag{I.1}
$$

若 $K_T=1$，另定义 $\Gamma_T=0$。所有可选 anchor 都从第一轮存在，故其 lifetime 同为 $T$，定义与具体 anchor 选择无关。

解释：$H_{i,T}\le r$ 的臂全部在最后 $r$ 轮内到达，它们对总 regret 的共同影响至多 $r$，不需要按臂分别支付 $r$。其余臂的总 lifetime 才进入信息预算。

**lemma I.1 — 到达曲线恒等式。** 对整数 $0\le r<T$，

$$
\boxed{
V_T(r)=\sum_{s=1}^{T-r}(K_s-1)
+r(K_{T-r}-1).
}
\tag{I.2}
$$

在 $r=T$ 时 $V_T(T)=0$，单独处理即可。每个 $\tau_i\le T-r$ 的非 anchor 臂，在第一项贡献 $T-r-\tau_i+1$，再在第二项贡献 $r$，合计正好为 $H_{i,T}$。

注意这里保留的是**满足寿命阈值的臂的完整 lifetime**。式 (I.2) 的第二项是定义的一部分，不应在转写时遗漏。

### I.2 Minimax 下界

**theorem I.2 — Arrival-schedule lower bound。** 存在绝对常数 $c>0$，对任意到达路径与 $T$，

$$
\boxed{\mathfrak R_T(\tau)\ge c\Gamma_T(\tau).}
\tag{I.3}
$$

证明机制已稳定，且仅需 Bernoulli 奖励。

假设某策略在所有环境上的风险至多 $R$。选 $H_i\ge C_0R$ 的臂，令

$$
\delta_i=c_0R/H_i,
\qquad \mu_a^{(0)}=1/2,
\qquad \mu_i^{(0)}=1/2-\delta_i.
$$

其中 $c_0$ 取足够大的绝对常数，$C_0$ 更大，确保 $\delta_i\le1/4$。其余臂可放在不超过 $1/2$ 的固定均值。替代环境 $\mu^{(i)}$ 只把臂 $i$ 改为 $1/2+\delta_i$。

reference 下的共同预算给出

$$
\sum_i\delta_i\mathbb E_0N_i(T)\le R.
$$

用事件 $E_i=\{N_i(T)\ge H_i/2\}$，reference 下有
$\Pr_0(E_i)\le2/c_0$，alternative 下有
$\Pr_i(E_i^c)\le2/c_0$。因此数据处理与 KL chain rule 给出

$$
\mathbb E_0N_i(T)\,
\operatorname{kl}(1/2-\delta_i,1/2+\delta_i)\gtrsim1,
$$

从而

$$
\mathbb E_0N_i(T)\gtrsim H_i^2/R^2,
\qquad
\sum_{H_i\ge C_0R}H_i\lesssim R^2.
$$

扩大固定点的绝对常数即得 $\Gamma_T\lesssim R$。非平凡实例上 $R$ 的常数级下界和整数边界可单独处理。

这一证明的价值在于：**所有替代环境的样本要求同时落在同一个 reference 风险预算里。** 下界相加来自共同 occupancy 的约束，而不是把互不兼容的局部最坏情形机械相加。

### I.3 普通 anytime UCB 的 lifetime 上界：现已补证

本轮补充证明表明，Part I 不需要 horizon-aware cap。普通 UCB 已经足够；关键是充分利用各臂的到达时间来分析总采样次数。

**lemma I.3 — Lifetime grouping。** 固定任意评估终点 $T$ 与整数 $1\le r<T$，令

$$
J=\left\lceil\log_2(T/r)\right\rceil.
$$

对任意合法动作轨迹，均有

$$
\boxed{
\sum_{i\ne a:\,H_{i,T}>r}\sqrt{N_i(T)}
\le\sqrt{2J V_T(r)}.
}
\tag{I.4}
$$

证明：将臂按 $2^kr<H_{i,T}\le2^{k+1}r$ 分组。每组只能在最后 $2^{k+1}r$ 轮被采样，因此该组样本总数不超过这个长度。组内 Cauchy–Schwarz 给出不超过该组 lifetime 总量平方根的 $\sqrt2$ 倍，再对 $J$ 组使用 Cauchy–Schwarz 即得结论。分组只用于分析，不需要算法知道终点。

**theorem I.3 — Minimax characterization 与 sharp anytime。** 存在绝对常数 $C>0$，同一个不知 $T$、未来到达或最终臂数的 UCB 策略满足，对 $\Gamma_T\ge1$，

$$
\boxed{
\sup_P\mathcal R_T(\pi^{\rm U},P)
\le\min\left\{T,
C\Gamma_T\sqrt{\log(2T)[1+\log(T/\Gamma_T)]}
\right\}.
}
\tag{I.5}
$$

$\Gamma_T=0$ 时风险为零。这里“对所有 $T$”指同一个策略逐前缀满足期望风险界。结合下界，

$$
\boxed{\mathfrak R_T(\tau)=\widetilde\Theta(\Gamma_T).}
$$

具体策略：若存在可用的未采样臂，按固定次序选择一个初始化；否则选取最大 index：

$$
U_i(t)=\widehat\mu_i(N_i(t-1))
+\sqrt{\frac{3\log(2t)}{N_i(t-1)}}.
\tag{I.6}
$$

保留所有历史样本，不重启。对首次被采样的臂按 discovery order 编号，由独立奖励流和 Hoeffding，对截至 $t$ 至多 $t$ 个已采样臂、至多 $t$ 种样本数做 union bound，得到当轮区间失效概率至多 $1/(32t^4)$。不需要对可能远大于 $T$ 的全部 $K_T$ 个臂作 union bound。

在区间有效的非初始化轮次，所选臂的 gap 至多其 confidence radius 的两倍。取 $r=\Gamma_T$ 后：

| 部分 | 已证明的控制 |
|---|---|
| 短寿命臂的全部选择 | 都发生在最后 $r$ 轮，共付至多 $r$ |
| 长寿命臂的初始化 | 臂数至多 $V_T(r)/r\le r$ |
| 长寿命臂的其余选择 | 单臂付 $O(\sqrt{\log(2T)N_i(T)})$；寿命分组使总额为 $O(r\sqrt{J\log(2T)})$ |
| anchor 的次优选择 | 只可能发生在首个竞争者到达后；该窗口长度 $H_{\max}\le r^2$，故付 $O(r\sqrt{\log(2T)})$ |
| 置信事件失败 | 期望累计损失为 $O(1)$，由非平凡情形 $r\ge1$ 吸收 |

这是对任意实际终点的直接分析，因此原先的 sharp-anytime 缺口已经补上。全部证明，包括下界常数、批量到达、未采样臂和单臂退化边界，见 [Part I 闭合证明](/Users/xxy/.codex/.chatgpt-projects/g-p-6ab8d1d3edd8819188334f7a3a24834b/Part-I-Arrival-Minimax-闭合证明.md)。

### I.4 典型到达路径

| 到达路径 | $\Gamma_T$ | 解释 |
|---|---:|---|
| 始终只有一个臂 | $0$ | 没有决策损失 |
| $K\ge2$ 个臂从第一轮存在 | $\asymp\min\{T,\sqrt{(K-1)T}\}$ | 静态有限臂基准 |
| $M$ 个竞争者在剩余 $H$ 轮时同时到达 | $\asymp\min\{H,\sqrt{MH}\}$ | 大量晚到臂的影响受共同剩余时段限制 |
| $K_t\sim c t^\alpha$，$0<\alpha<1$ | $\sim\sqrt{c/(1+\alpha)}T^{(1+\alpha)/2}$ | 多项式次线性增长 |
| $K_t\sim\rho t$，$\rho>0$ | $\sim T\sqrt{\rho/(\rho+2)}$ | 线性最坏情形 |
| $K_t=t$ | $\sim T/\sqrt3$ | 每轮到达一个新臂 |

当 $\alpha=0$ 时应使用静态的 $K-1$，不能把逐渐发散时忽略 anchor 的渐近常数原样沿用。表中的精确极限常数是 **$\Gamma_T$ 的常数**，不是 minimax regret 的精确极限常数。

### I.5 Learnability 边界与 anytime 的范围

**theorem I.4 — 到达几何的精确边界。** 对同一条无限到达路径，

$$
\boxed{\Gamma_T=o(T)\quad\Longleftrightarrow\quad K_t=o(t).}
\tag{I.7}
$$

充分性：令 $S_T=\sum_{s\le T}(K_s-1)$，则 $K_t=o(t)$ 推出 $S_T=o(T^2)$，而 $\Gamma_T\le\lceil\sqrt{S_T}\rceil$（取与 $T$ 的截断）。

必要性：若沿 $t_n$ 有 $K_{t_n}\ge\varepsilon t_n$，则在 $T_n=2t_n$ 时，这些臂都具有至少 $t_n$ 的 lifetime，迫使 $\Gamma_{T_n}\gtrsim_\varepsilon T_n$。

结合 minimax 下界，$K_t=o(t)$ 是 uniform anytime no-regret 的必要条件。这里的结论是沿无限路径的渐近陈述，不否定某个固定终点出现巨大 late batch 而仍只有很小 $\Gamma_T$。

**theorem I.5 — 无对数 coarse anytime 保证。** 另有一个不知未来与终点的分块策略 $\pi^{\rm B}$ 满足

$$
\boxed{
\sup_P\mathcal R_T(\pi^{\rm B},P)
\le\min\{T,C T^{2/3}K_T^{1/3}\}.
}
\tag{I.8}
$$

构造完全明确：在长度 $n=2^m$ 的固定几何 epoch 中，每个 block 起点 $s$ 观察当前臂数 $k=K_s$，取计划块长 $\lceil n^{2/3}k^{1/3}\rceil$，并在 epoch 末尾截断；块内冻结臂集为 $A_s$，只运行标准静态 MOSS，块间再接纳新臂。

关键确定性不等式是：若该 epoch 的最大块长为 $L_{\max}$，则

$$
\sum_{\text{blocks }[s,e]}\sum_{t=s}^{e}(B_t-B_s)
\le L_{\max}\sum_{\text{blocks }[s,e]}(B_e-B_s)
\le L_{\max}.
$$

因此延迟接纳的代价按 benchmark 总涨幅控制，不按新臂数重复收费。静态 MOSS 在块内给出 $O(\sqrt{kh})$；按上述块长累加，任意完整或截断 epoch 的风险为 $O(n^{2/3}K_T^{1/3})$，再作几何求和即得 (I.8)。唯一外部算法输入是在固定臂集上的标准 [Audibert–Bubeck (2009), Theorem 5](https://www.cs.mcgill.ca/~colt2009/papers/022.pdf)，无需 growing-MOSS reduction。

**theorem I.6 — 精确 uniform anytime no-regret 边界。** 结合 (I.7)、下界与 (I.8)，

$$
\boxed{
\exists\pi_\infty:\sup_P\mathcal R_T(\pi_\infty,P)=o(T)
\quad\Longleftrightarrow\quad K_t=o(t).
}
\tag{I.9}
$$

充分性直接来自 $\mathcal R_T/T\le C(K_T/T)^{1/3}\to0$。同一个 $\pi^{\rm B}$ 对所有次线性到达路径成立，无需知道增长速率。

本轮用一个已证明的较弱辅助式替代原先未经完整证明的 $\Gamma_T+\sqrt{\Gamma_TT}$：忽略最后 $\Gamma_T$ 轮到达的臂，再对至多 $\Gamma_T+1$ 个保留臂应用 (I.8)，得到

$$
\mathfrak R_T(\tau)
\le\min\{T,C[\Gamma_T+T^{2/3}\Gamma_T^{1/3}]\},
\qquad\Gamma_T\ge1.
$$

**Part I 的闭合范围。** 现在已证明对数精度 minimax matching、sharp-anytime 期望速率与精确 uniform learnability。速率结论使用 $\pi^{\rm U}$，无对数充分性使用 $\pi^{\rm B}$。无对数精确 $\Theta(\Gamma_T)$、更强的原辅助式，以及将两个策略的保证合并到同一个策略，均未在本轮额外证明，也不是以上定理的前提。

---

## Part II — Instance-sensitive theory on regular instances

这一部分固定具体均值配置。研究目标是：**明显较差、信息已积累充分、或决策后果很小的 arrivals，是否能自动比 schedule-minimax 更便宜？**

当前可冻结的是若干结构引理、一套 all-prefix 信息下界和候选 cPT 半径。正则条件的最终形式与统一匹配上界仍未闭合。

### II.1 后果、采样价格与决策期限

固定臂 $i$，在存在其他可用臂时定义 outside benchmark

$$
b_{-i}(s):=\max_{j\in A_s\setminus\{i\}}\mu_j.
$$

考虑只改变臂 $i$ 的 point alternative

$$
\lambda^{i,q}_i=q>\mu_i,
\qquad \lambda^{i,q}_j=\mu_j\ (j\ne i).
$$

外部选择仍未达到 $q$ 时，忽略该机会的潜在损失面积为

$$
\mathcal A_{i,q}(t):=
\sum_{s=\tau_i}^{t}(q-b_{-i}(s))_+.
$$

唯一可用臂时期没有 outside 决策，该时期单独按强制选择处理。定义机会失效时刻

$$
d_i(q):=\inf\{s\ge\tau_i:b_{-i}(s)\ge q\},
$$

有限前缀中从未失效时取 $T+1$。这是机会价值消失的时间，**不是 all-prefix 信息约束唯一需要检查的时间**。

$\mathcal A_{i,q}$ 只表示完全错过机会的后果；它尚未扣除学习者可以通过直接拉该臂而同时 hedge 两个环境的作用。真正用于下界的是下面的风险前沿。

### II.2 Occupancy 表示与精确 KL

令 $\mathcal X_t$ 是所有合法分数 schedule：

$$
x_{s,i}\ge0,\quad x_{s,i}=0\ (i\notin A_s),
\quad \sum_{i\in A_s}x_{s,i}=1,\qquad s\le t.
$$

其累计次数 $n_i(t)=\sum_{s\le t}x_{s,i}$ 构成 occupancy polytope

$$
\mathcal N_t=\sum_{s=1}^{t}\Delta(A_s).
$$

**lemma II.1 — Support 与信息恒等式。**

$$
h_t(\mu):=\sup_{n\in\mathcal N_t}\langle n,\mu\rangle
=\sum_{s\le t}B_s,
$$

$$
L_{\mu,t}(n):=h_t(\mu)-\langle n,\mu\rangle,
\qquad R_t=L_{\mu,t}(N(t)),
$$

$$
D_{\rm KL}(\mathbb P_\mu^{\pi,t}\Vert\mathbb P_\lambda^{\pi,t})
=\sum_i\mathbb E_\mu N_i(t)\operatorname{kl}(\mu_i,\lambda_i).
\tag{II.1}
$$

动作规则在两个环境中相同，KL 只来自实际观察的奖励。point alternative 使右侧退化为
$\mathbb E_\mu N_i(t)\operatorname{kl}(\mu_i,q)$。

同一份样本同时服务该臂的全部 $q$；多臂之间则共享单轮采样容量。

### II.3 Prefix cross-risk frontier

统一使用分数 occupancy 版本：

$$
\boxed{
\Phi_{i,q,t}(R):=
\inf_{n\in\mathcal N_t:\,L_{\mu,t}(n)\le R}
L_{\lambda^{i,q},t}(n).
}
\tag{II.2}
$$

它衡量：一份在 reference 下至多花费 $R$ 的共同动作安排，在 alternative 下仍至少损失多少。它是**零额外识别信息的决策前沿**，不是一个已实现的自适应测试策略的最优风险。

这里采取分数 relaxation 是为了统一 LP 与 cost curve。若使用整数轨迹版本，前沿只可能更大；下文下界对分数版本仍严格有效，不把二者逐字等同。

**lemma II.2 — 单臂前沿的 knapsack 几何。** 只有

$$
\mathcal W_{i,q,t}:=\{s\in[\tau_i,t]:\mu_i<b_{-i}(s)<q\}
$$

上的动作存在两环境冲突。其余时刻可同时选择两环境的最优臂；在 $b_{-i}(s)=\mu_i$ 时可免费选择 $i$。故

$$
\Phi_{i,q,t}(R)=
\min_{0\le z_s\le1:\,\sum_{s\in\mathcal W}a_sz_s\le R}
\sum_{s\in\mathcal W}c_s(1-z_s),
\tag{II.3}
$$

其中

$$
a_s=b_{-i}(s)-\mu_i,\qquad c_s=q-b_{-i}(s),
\qquad a_s+c_s=q-\mu_i.
$$

在该冲突窗口中，$a_s$ 非减、$c_s$ 非增，所以 $c_s/a_s$ 非增；最优 hedge 从最早时刻开始，至多包含一个分数边界槽。

因此可冻结以下性质：

1. $\Phi_{i,q,t}(R)$ 随 $t$ 非减，随 $R$ 非增。
2. hedge 预算耗尽前，前沿可为零；完全耗尽后，后续新增风险由递减的 $c_s$ 累积。
3. 除去分数 cutoff 的边界槽后，增长尾段离散凹。

**范围限制。** 凹性不直接适用于包含最初零平台的整个时间轴；对整数取整的“窗口前 $\theta$ 比例已揭示 $\theta$ 风险”必须处理分数边界。即使有准确的单臂 early-revelation 不等式，也不能据此直接宣布所有前缀任务可以在线调度。

### II.4 严格 pointwise change-of-measure 下界

为固定常数，定义

$$
\psi(x)=
\begin{cases}
0,&0\le x\le2,\\
\operatorname{kl}(1/2,1/x),&x>2.
\end{cases}
$$

它在 $x\to\infty$ 时为 $\tfrac12\log x+O(1)$。此前采用其他固定概率常数的写法与此同阶；本文统一用这个直接的两点版本。

**theorem II.3 — All-prefix point-alternative lower。** 若同一个策略满足

$$
\mathcal R_T(\pi,\mu)\le r,
\qquad \mathcal R_T(\pi,\lambda^{i,q})\le r,
\quad r>0,
$$

则对每个 $t\le T$，

$$
\boxed{
\mathbb E_\mu N_i(t)\operatorname{kl}(\mu_i,q)
\ge\psi\!\left(\frac{\Phi_{i,q,t}(2r)}r\right).
}
\tag{II.4}
$$

**证明。** 令 $E=\{L_{\mu,t}(N(t))\le2r\}$。非负 prefix regret 与 Markov 不等式给 $\Pr_\mu(E)\ge1/2$。在 $E$ 上，定义 (II.2) 保证
$L_{\lambda^{i,q},t}(N(t))\ge\Phi_{i,q,t}(2r)$，所以
$\Pr_{\lambda^{i,q}}(E)\le r/\Phi_{i,q,t}(2r)$。若右侧小于 $1/2$，对事件用 KL 数据处理，再用 (II.1)；否则只需零下界。证毕。

这条结论不依赖 R1、R2*、R3。正则条件属于 upper 的候选适用范围，不是本下界成立的必要条件。

### II.5 cPT demand、LP 与候选 critical radius

先固定合法 alternatives 集 $\mathcal Q_i\subset(\mu_i,1)$。它属于模型定义，不得随着证明需要临时变化。定义

$$
\beta^-_{i,q,t}(r)
:=\psi\!\left(\frac{\Phi_{i,q,t}(2r)}r\right),
\qquad
m^-_{i,q,t}(r):=
\frac{\beta^-_{i,q,t}(r)}{\operatorname{kl}(\mu_i,q)},
$$

$$
\boxed{D_i(t;r):=\sup_{q\in\mathcal Q_i}m^-_{i,q,t}(r).}
\tag{II.5}
$$

对 $t<\tau_i$ 取 $D_i(t;r)=0$。$D_i$ 随时间非减。这里是 $\sup_q$，不是 $\sum_q$。

接着定义 screening-cost LP

$$
\boxed{
\begin{aligned}
\mathfrak C_{\mu,T}(r):=\inf_x\quad&
\sum_{s=1}^{T}\sum_{i\in A_s}x_{s,i}\Delta_i(s)\\
\text{s.t.}\quad&
\sum_{s=\tau_i}^{t}x_{s,i}\ge D_i(t;r),\quad\forall i,t,\\
&\sum_{i\in A_s}x_{s,i}\le1,\quad x_{s,i}\ge0.
\end{aligned}}
\tag{II.6}
$$

不可行时取 $+\infty$。此处允许 idle，是因为 $x$ 表示证书采样；在已知真值的解释中，剩余容量可用当前最优臂补齐，成本不增。它不授予实际 learner 已知最优臂的能力。

候选半径为

$$
\boxed{r_{\mu,T}:=\mathcal C_T^{\rm cPT}(\mu,\tau)
:=\inf\{r>0:\mathfrak C_{\mu,T}(r)\le r\}.}
\tag{II.7}
$$

**定义的状态：** (II.5)–(II.7) 是明确的数学对象；**candidate** 指它们是否完整刻画可达的实例复杂度，不能把有效下界误读成匹配性已证。

**theorem II.4 — 严格局部下界。** 令

$$
\mathcal N_T(\mu)
=\{\mu\}\cup\{\lambda^{i,q}:i\in A_T,q\in\mathcal Q_i\}.
$$

则按以上常数约定，

$$
\boxed{
\inf_\pi\sup_{\lambda\in\mathcal N_T(\mu)}
\mathcal R_T(\pi,\lambda)\ge r_{\mu,T}.
}
\tag{II.8}
$$

证明：若局部族上风险均不超过 $r$，取 $x_{s,i}=\Pr_\mu(I_s=i)$。定理 II.3 使所有 demand 约束成立，而目标函数等于 $\mathcal R_T(\pi,\mu)\le r$。因此 $\mathfrak C_{\mu,T}(r)\le r$。

**量词限制。** 这不是 $\mathcal R_T(\pi,\mu)\ge r_{\mu,T}$ 的无条件逐实例结论。将来即使证明
$\mathcal R_T(\pi,\mu)\lesssim r_{\mu,T}\operatorname{polylog}T$，也不能立刻与 (II.8) 合并成局部 minimax matching：还需控制邻域内各 $r_{\lambda,T}$、正则条件与风险保证的共同适用性。

### II.6 保留的 water-filling 解释

在固定 benchmark、可分 point tests 的受限模型中，若第 $i$ 个测试的后果为 $v_i$、每样本信息为 $d_i$、每样本 regret 为 $c_i$，则

$$
F(r)=\sum_i\frac{c_i}{d_i}[\log(v_i/r)]_+,
\qquad C=\inf\{r:F(r)\le r\}.
$$

**lemma II.5 — Fixed point 与 penalized form。** 对这样的非负连续非增 $F$，

$$
C\le\inf_{r>0}\{r+F(r)\}\le2C
$$

（零值与未取到的下确界按极限解释）。这是 water-filling 的稳定数学依据。

固定 gap 的 interior Bernoulli 情形有 $c_i\asymp\Delta_i$、$d_i\asymp\Delta_i^2$，因而出现 $\Delta_i^{-1}\log(v_i/r)$。当机会后果与目标风险同阶或更小，测试可以不启动。这里保留的是**风险决定认证精度**的原则，不把逐臂可分公式当成一般 arriving-arms 的最终 complexity。

### II.7 确定性采样几何：哪些已经成立？

**lemma II.6 — 单臂最早采样成本。** 对 $0\le m\le t-\tau_i+1$ 定义

$$
C_{i,t}(m):=
\min_{0\le z_s\le1:\,\sum_{s=\tau_i}^{t}z_s\ge m}
\sum_{s=\tau_i}^{t}z_s\Delta_i(s).
$$

由于 $\Delta_i(s)$ 非减，令 $k=\lfloor m\rfloor$，有

$$
C_{i,t}(m)=
\sum_{\ell=0}^{k-1}\Delta_i(\tau_i+\ell)
+(m-k)\Delta_i(\tau_i+k),
\tag{II.9}
$$

整数 $m$ 时省略最后一项；超过可用槽数则为 $+\infty$。单臂任何可行的 $m$ 样本方案都不比最早采样便宜。这是一个成本排序事实，不是未知均值 learner 已经知道该给每个臂分配多少预算。

**lemma II.7 — 共同 benchmark 成本分解。** 若 $y_s=\sum_i x_{s,i}$、$M_i=\sum_sx_{s,i}$，则

$$
\boxed{
\sum_{s,i}x_{s,i}\Delta_i(s)
=\sum_s B_sy_s-\sum_i\mu_iM_i.
}
\tag{II.10}
$$

固定每臂总工作量 $M_i$ 后，时间安排只通过总服务时刻影响成本。若全部 jobs 及其需求在对应臂到达时已知，可提前工作，且采用可抢占的分数调度，则 work-conserving schedule 使用最早可用服务槽；其中 EDF 可以同时满足一切可行 deadline，故取得该已知 job 系统的最小成本。

把非减需求拆成

$$
d_{i,u}(r)=D_i(u;r)-D_i(u-1;r)
$$

时，一个 job 的 release 为 $\tau_i$、deadline 为 $u$、work 为 $d_{i,u}$。其 processor demand 为

$$
\operatorname{DBF}_{\mu,r}([s,t])
=\sum_{i:\,s\le\tau_i\le t}D_i(t;r).
\tag{II.11}
$$

任意窗口满足 $\operatorname{DBF}([s,t])\le t-s+1$，正是这个可抢占分数 job 系统的容量可行性条件。实际整数 pulls 的取整开销需另计。

**必须保留的边界：** 统计 learner 通常不知道未来 demand，甚至在臂到达时不知道已有 job 的真实大小。于是“物理上可以开始采样的 release time”与“算法知道应做何种测试的 revelation time”不同。上述 oracle 调度 lemma 没有解决后者。

### II.8 正则类：R1 + 候选 R2* + 候选 R3+

当前最值得保留的正则类思路是：限制信息置信度升级的成本突变，并保留足够采样容量。它不直接约束 benchmark 的跳跃速度。

**R1 — Interior geometry。** 固定 $\eta>0$，要求

$$
\eta\le\mu_i\le1-\eta.
\tag{R1}
$$

当 $\mu_i,q$ 都处于固定 interior 区间时，Bernoulli KL 与 $(q-\mu_i)^2$ 在常数因子内等价。若要使用所有真实 benchmark 之上的统一 coarse alternative，可取 $q^+=1-\eta/2$，但必须明确 ambient alternative class 允许这个值；它不属于上端点为 $1-\eta$ 的同一个 base class。也可采用更强的 headroom 版本 $\mu_i\le1-2\eta$、$q^+=1-\eta$。

R1 本身不会自动保证所有 downward/upward alternatives 都仍然正则，也不会单独证明未知 newcomer search 已由 cPT 完全覆盖。

**candidate R2* — Confidence stability / no information cliff。** 对一个已经精确定义为 relevant 的证书 $c=(i,q,t)$，以

$$
m_c^-=\beta_c^-/\operatorname{kl}(\mu_i,q)
$$

表示 lower 的风险敏感需求；以

$$
m_c^+=\beta_c^+/\operatorname{kl}(\mu_i,q)
$$

表示拟采用 upper 所需的置信需求，其中固定时域高置信构造通常考虑 $\beta_c^+\asymp\log(eT)$，但多臂、多尺度的具体阈值必须由实际测试给出。候选条件为

$$
\boxed{
C_{i,t}(m_c^+)\le L_T C_{i,t}(m_c^-),
\qquad L_T=(\log(eT))^{O(1)}.
}
\tag{R2*}
$$

还必须显式要求所需的 $m_c^+$ 在 deadline 前可取得；不能把 $+\infty\le L_T\cdot+\infty$ 当作条件成立。

静态 gap 下 $C(m)=m\Delta$，所以在 $m^-\asymp1/d$、$m^+\asymp\log T/d$ 的可行范围内，成本膨胀为 $O(\log T)$。若免费样本窗口已经足以容纳 $m^+$，两侧同为零。若免费窗口只容纳 $m^-$，之后采样代价突然上升，则该条件可能失败。

**open R2*-definition。** 当前“relevant / dominant certificates”尚无可冻结的完整选择规则。必须说明：怎样处理 $\beta_c^-=0$ 或趋零、near ties、短窗口，以及低后果但数量很多的 arrivals。不能对全部 $q>\mu_i$ 无差别地要求 $\log T/\operatorname{kl}(\mu_i,q)$；也不能临时把趋零的 lower demand 替换成 $1/\operatorname{kl}$ 后仍声称它来自 (II.4)。

**candidate R3+ — Subcritical high-confidence screening traffic。** 一旦 relevant 证书族 $\mathcal J(r)$ 定义完成，应定义累计 upper envelope

$$
\widetilde D_i(t;r)
:=\sup_{\substack{(i,q,u)\in\mathcal J(r)\\u\le t}}m^+_{i,q,u},
\tag{II.12}
$$

空集上取零。这里显式对 $u\le t$ 取上确界，确保它是累计 due-by demand；不能把随 benchmark 变好而下降的当前消除阈值直接称为累计需求。然后要求

$$
\boxed{
\Lambda^+_{\mu,T}(r):=
\sup_{1\le s\le t\le T}
\frac{\sum_{i:\,s\le\tau_i\le t}\widetilde D_i(t;r)}{t-s+1}
\le1-\zeta,
\quad\zeta>0.
}
\tag{R3+}
$$

应区分两种版本：$\Lambda^-$ 用 lower demand $D$；$\Lambda^+$ 用 inflated upper demand $\widetilde D$。最新提议采用的是后者，它更强；二者不能混记为同一个 R3。

R3+ 约束的是统计证据工作量，不是 raw arrival 数。它允许某些大量但低后果的晚到臂，也允许 benchmark 大跳；是否纳入某个具体实例，仍取决于证书选择规则。它保证上述已知 job 系统的容量余量，尚不保证在线统计算法可以及时发现并完成这些 jobs。

**正则类当前状态。**

$$
\boxed{
\mathcal G_{\eta,\zeta,L}
\quad\text{拟由 R1、R2*、R3+ 定义，但仍是 candidate class。}
}
$$

特别不能仅凭 R2* 对每个臂的最早槽成立，以及 R3+ 的容量可行，就推断 joint inflated schedule 的总成本至多 lower LP 的 polylog 倍：多臂不能同时独占同一个早期便宜槽。这一 joint cost 比较仍需证明。

### II.9 未知均值的稳定算法构件

当前保留的实现方向是 **risk-sensitive、两侧比较的多尺度 successive elimination**。它是一组待完善的算法构件，还不是已证明的完整 policy。

维护同时有效的 confidence intervals $[L_i(t),U_i(t)]$，并保留旧样本。新臂从粗尺度进入，必要时才提高比较精度。

**lemma II.8 — 永久淘汰安全性。** 在所有区间覆盖真值的事件上，若

$$
U_i(t)<\max_{j\in A_t}L_j(t),
$$

则存在永久可用且均值严格高于 $\mu_i$ 的臂，故 $i$ 今后永不可能最优，可以永久淘汰。

**lemma II.9 — 未解决比较的双侧性。** 在 confidence event 上，若 $\mu_j>\mu_i$ 而 $U_i(t)\ge L_j(t)$，则

$$
(U_i(t)-\mu_i)+(\mu_j-L_j(t))\ge\mu_j-\mu_i.
$$

所以至少一侧的单边误差不小于两臂均值差的一半。它说明应在 challenger 与 benchmark side 之间选择采样对象；但不说明任意 active-arm pull 都在有效完成所需工作。

令 $c_t$ 为当前 incumbent。在 confidence event 上有精确不等式

$$
\boxed{
(q-L_{c_t}(t))_+
\le(q-B_t)_+
+(B_t-\mu_{c_t})
+(\mu_{c_t}-L_{c_t}(t)).
}
\tag{II.13}
$$

它把可观察的保守后果拆为真实反事实后果、incumbent 的次优程度、以及 incumbent 的统计不确定性。

**解释边界：** $B_t-\mu_{c_t}$ 只有在实际选择 $c_t$ 的轮次才等于已支付 regret。若算法在别处采样，或同一项被许多 challenger 共用，必须加上相应服务权重或公共 potential，不能直接对每个 challenger 分别当作实际 regret 收费。

自适应采样下的 time-uniform KL/GLR 工具可以提供检验有效性；它们不会自动给出本项目的 regret charging。可用技术来源是 [Kaufmann–Koolen, Mixture Martingales Revisited (2021)](https://jmlr.org/papers/v22/18-798.html)。

### II.10 当前上界的真实障碍

**障碍 A：需要认证哪些比较，仍未完全定义。** 普通高置信淘汰会对低后果、短窗口或 near-tie 比较做过多工作。必须把实际启动的比较与 cPT 风险证书关联。仅写一个 $\log T/\Delta_i(t)^2$ 的目标不足以完成这一步。

**障碍 B：incumbent 的证据也是工作。** 当 $i$ 已估得很准，比较仍可能因为真正更优的臂尚未估准而未解决。逐臂 quota 不自动覆盖 leader refinement、leader 更换与新 record 的发现成本。

**障碍 C：便宜信息、置信度升级与联合调度。** R2* 针对单臂信息 cliff；它尚未证明同时升级所有证书的联合成本受 lower LP 控制。R3+ 针对容量；它尚未控制算法何时知道该用哪些便宜槽，以及未及时利用便宜槽的额外 regret。

**障碍 D：oracle 可行不等于任意 work-conserving 算法可行。** EDF 的已知-job 结论不能直接移植给“选择最大 confidence radius 的 active arm”。后者是否拥有正确 priority、是否能避免无关比较占用容量，都需要证明。仅由 $\Lambda^+\le1-\zeta$ 不能推出 $O(\log T)$ backlog；长 deadline 的大批任务本就可以有很大待处理量。

**障碍 E：benchmark 大跳的两种效应必须分开。** 对已有次优臂，若真实 $B_t$ 已知，$\log T/\operatorname{kl}(\mu_i,B_t)$ 会随 $B_t$ 上升而下降。但发现新 best 需要样本；旧 best 被超越也会成为新的比较对象；延迟到昂贵时期的同样一个 pull 可能更贵。因此只能说旧 challenger 的 oracle 区分阈值下降，不能说 benchmark jump 自动消除了所有统计和 regret 困难。

**障碍 F：存在 self-charging 不等式，不等于它可吸收。** 真正需要

$$
\mathcal R_T\le C L_T r_{\mu,T}+\theta\mathcal R_T,
\qquad\theta<1,
$$

而不是系数为 $1$ 或更大的循环上界。incumbent uncertainty 若按 confidence widths 粗加，通常重新产生平方根级损失；若公共误差按 challenger 重复收费，则产生额外臂数因子。

### II.11 尚缺关键引理：固定证明接口

以下是当前主框架内应完成的接口，不是提出新的复杂度路线。

| 编号与状态 | 必须证明的输入—输出 | 为什么缺它就不能闭合 |
|---|---|---|
| **open L1：Relevant-certificate selection** | 由 $\mu,\tau,r$ 定义明确的证书族、lower/upper quota 与 residual-risk 规则 | R2*、R3+ 才成为不依赖任意选择的实例条件 |
| **open L2：Two-sided service/charging** | 将算法的非平凡采样映射到真实证书工作、有效 leader refinement 或可吸收公共误差；控制复用与整数开销 | 区间覆盖和淘汰安全本身不控制 regret |
| **open L3：Joint confidence-cost comparison** | 将可行的 inflated joint schedule 的最优成本与 $\mathfrak C_{\mu,T}(r)+r$ 比较 | 逐臂 $C_{i,t}$ 的比较不等于共同容量下的比较 |
| **open L4：Causal realization with costs** | 对实际揭示时间、priority、共享 samples 和失效比较，证明及时服务以及迟延成本界 | 物理 release 时的 oracle EDF 不能直接当作 online algorithm |
| **open L5：Residual risk and bootstrap** | 低后果 ambiguity、误淘汰、leader 错误的总风险为 $O(L_Tr)$，且 self-charge 系数严格小于 $1$ | 防止只分析 screening 而遗漏利用损失 |
| **open L6：Adaptation and safety composition** | 去掉未知 $r_{\mu,T}$；构造真正同时具有实例保证和 Part I 保证的同一策略 | 两个策略分别有界，不意味着能免费取二者的最小值 |

这些接口可以在一个总 charging lemma 中合并证明；但在证明之前，应保留它们各自的逻辑作用。尤其不能把 L2–L5 全部归为“标准置信区间 bookkeeping”。

### II.12 候选主定理及其正确量词

**candidate II.A — Regular-instance upper。** 在完成证书定义与上述引理后，希望存在同一个不知真实均值的 causal 策略，使

$$
\boxed{
\mathcal R_T(\pi,\mu)
\le C_{\eta,\zeta}L_T\,\bar r_{\mu,T},
\qquad \mu\in\mathcal G_{\eta,\zeta,L}.
}
\tag{II.14}
$$

其中暂记 $\bar r_{\mu,T}=1\vee r_{\mu,T}$，用来显式承认初始化和退化半径问题；若最终声称纯乘法的 $L_Tr_{\mu,T}$，还需证明这些开销已经由半径支付，特别是 $r_{\mu,T}=0$ 的情形。这个归一化是待解决的 theorem convention，不是额外得到的 matching 结果。

**candidate II.B — Minimax-safe instance adaptation。** 对所有实例保留 Part I 有限时域保证，并在正则类内达到

$$
\boxed{
\mathcal R_T(\pi,\mu)
\le\widetilde O\!\left(
\min\{\Gamma_T,\bar r_{\mu,T}\}\right).
}
\tag{II.15}
$$

单臂情形单独取零。式 (II.15) 的组合策略尚未构造完成，不能把“minimax fallback”当作无需证明的外壳。若进一步要求不知 $T$，还需证明实例自适应策略本身的 anytime 实现及其与 Part I 策略的组合；Part I 单独的 sharp-anytime 保证现已成立。

**open II.C — Matching 的最终表述。** 已有 (II.8) 与拟议 (II.14) 使用不同量词。若目标是

$$
\inf_\pi\sup_{\lambda\in\mathcal N_T(\mu)}
\mathcal R_T(\pi,\lambda)
\asymp_{\rm polylog}r_{\mu,T},
$$

必须保证所用邻域属于 upper 的适用范围，并有
$\sup_{\lambda\in\mathcal N_T(\mu)}\bar r_{\lambda,T}\lesssim L_Tr_{\mu,T}$
或另一个能直接控制该局部风险的证明。否则论文应诚实表述为“实例上界及对应的局部信息下界”，暂不宣称两者已经严格匹配。

---

## Part III — Irregular examples / frontier of the theory

这一部分尚未系统展开。当前只有若干诊断性机制，不能把“某个证明失效”直接当成“任何算法都不可能”的定理。它的任务是区分：哪些正则条件反映真实统计困难，哪些只是当前算法或证明的限制。

### III.1 Information cliffs

**open。** 构造并分析

$$
C_{i,t}(m^-)\ll C_{i,t}(m^+)/\operatorname{polylog}T
$$

的实例族，包括低置信信息免费而高置信信息昂贵的情形。需要回答：这是 uniform high-confidence screening 的代价，还是 expected-regret 最优策略也必然支付的代价？能否用允许小错误概率的策略避免？若不能，现有 cPT 是否缺失了不可忽略的复杂度？

### III.2 Screening saturation 与 bursts

**open。** 研究 $\Lambda^+\uparrow1$、$\Lambda^+>1$ 或多个工作窗口重叠的情形。R3+ 失败只说明指定的 inflated certificate 系统不能按该方案完成；不自动推出线性 regret。最优策略可能放弃小后果任务、容许剩余 ambiguity，或采用不同置信度分配。

应建立容量不足、可容忍错误后果与真实最优 regret 的定量关系，并区分物理采样容量与任务揭示过晚。

### III.3 Boundary means 与 newcomer search

**open。** 当均值接近 $0$ 或 $1$ 时，uniform quadratic KL geometry 和固定 upward headroom 会失效。需要检查 point alternatives 的可用性、免费观察最优臂的作用，以及寻找正确臂本身的代价。

此前 perfect-arm/search 现象可作为诊断素材，但本部分尚没有一个可取代 regular theory 的完整 search characterization。不把旧的全局算法框架重新混入 Part II。

### III.4 Multiway near ties 与退化半径

**open。** 对多个近似并列臂，哪些情形能由同时施加全部 point constraints 捕捉，哪些需要联合替代环境或额外局部稳定性？同一策略能否在 near-tie 区域保持 minimax 安全，又在 fixed-gap 区域支付正确的认证成本？

特别需要审核 $r_{\mu,T}=0$ 或非常小的实例、邻域 complexity 突变，以及“在中心实例上容易”与“整个邻域都容易”的差别。Part I 提供全模型上限，但不自动证明局部 matching。

### III.5 Regularity 的必要性、覆盖范围与无限时域

**open。** 要给出可明确验证 R1/R2*/R3+ 的自然正则例子，也要分别违反其中一个条件的例子；否则正则类可能过窄，或者条件彼此重复。

候选测试对象包括：固定 gap distractors、长时间作为最优臂而积累样本的 record arms、突发大幅 benchmark 改善、短窗口密集 arrivals、多层嵌套的便宜采样窗口。对每类都应比较 $\Gamma_T$、$r_{\mu,T}$、confidence-inflated cost 和实际可达 regret。

从有限 $T$ 延伸到 anytime 时，还需说明正则参数是否对所有前缀统一有效，以及失败概率、证书风险与样本复用如何跨 epoch 累积。

---

## 4. 论文当前可以冻结的结构

| 部分 | 可以保留的主线 | 当前完成度 |
|---|---|---|
| Part I | lifetime volume $\to\Gamma_T\to$ minimax lower / lifetime-grouped UCB upper | 核心定理已有完整补充证明 |
| Part I 的 learnability | $\Gamma_T=o(T)\iff K_t=o(t)$；uniform anytime no-regret iff | 已证明；充分性由分块静态 MOSS 实现 |
| Part I 的 sharp anytime | 同一 horizon-free UCB 逐前缀达到 $\widetilde O(\Gamma_T)$ | 已证明，期望风险保证 |
| Part II 的表示与下界 | occupancy/KL、prefix frontier、sup-envelope、cPT LP、局部下界 | 可独立成立 |
| Part II 的正则性 | interior + confidence stability + high-confidence traffic | candidate；证书族与共同成本桥未定稿 |
| Part II 的上界 | risk-sensitive 双侧多尺度淘汰与 charging | open；不能称为已闭合 matching theorem |
| Part III | information cliff、overload、boundary/search、multiway 等边界 | 尚未系统开展 |

下一阶段若恢复证明工作，应沿 Part II 的 L1–L6 补齐当前框架；是否宣告闭合，以这些接口的实际证明为准，而不是以算法名字是否成熟或正则条件是否看起来足够为准。

## 5. 符号索引

| 符号 | 含义 |
|---|---|
| $\tau_i,A_t,K_t$ | 到达时间、可用集合、可用臂数 |
| $P_i,\mu_i$ | 固定奖励分布与均值 |
| $B_t,\Delta_i(t)$ | 当前最优均值与臂 $i$ 的即时 gap |
| $N_i(t),R_T,\mathcal R_T$ | 样本数、随机 pseudo-regret、期望风险 |
| $\mathfrak R_T(\tau)$ | 固定到达路径上的全分布 minimax 风险 |
| $a,H_{i,T},V_T(r),\Gamma_T$ | anchor、剩余 lifetime、长寿命 volume、arrival-only 半径 |
| $J,\ell,n_m$ | Part I 的寿命层数、计划块长、几何 epoch 长度 |
| $b_{-i}(t),\lambda^{i,q},d_i(q)$ | outside benchmark、point alternative、机会失效时刻 |
| $\mathcal A_{i,q}(t)$ | 完全错过该反事实机会的累计后果 |
| $\mathcal X_t,\mathcal N_t,h_t,L_{\mu,t}$ | 分数 schedule、occupancy polytope、support function、轨迹风险 |
| $\Phi_{i,q,t}(R)$ | prefix cross-risk frontier |
| $\beta^-,m^-,D_i(t;r)$ | lower 所需证据、样本需求、按臂复用后的累计 envelope |
| $\mathfrak C_{\mu,T}(r),r_{\mu,T}$ | cPT 采样成本 LP 与其 critical radius |
| $C_{i,t}(m)$ | 单臂独占最早可用槽的最小采样成本 |
| $\widetilde D_i,\Lambda^+,\zeta$ | inflated upper demand、窗口负载密度、容量 slack |
| $L_i,U_i,c_t$ | 置信界与 incumbent |
| $L_T$ | 允许的 polylog 成本因子；不表示任何臂的下置信界 |

## 6. 来源与本次整理范围

- [bandit思路修正](https://chatgpt.com/c/6ab666a7-f2f4-83ee-99dd-a719e51a6458)：本次接口返回的最近五轮完整回复，包含 all-prefix cPT、双侧比较、R2* 和 R3+ 的最新讨论。
- [分支 · bandit思路修正](https://chatgpt.com/c/6ab8d604-4428-83e8-b9fd-c27190b0fdca)：本次读取的 Part I 详细总结与 preceding minimax 推导，是 lifetime-volume 定义和 capped-UCB 结果的直接来源。
- 《Open-Ended-Arriving-Arms-Bandits-理论框架主线版.md》：从相关会话附件读取，用于核对原始模型、bounded/Bernoulli 关系、occupancy 与局部风险表示。
- 外部文献只用于核对 sequential-testing 工具及前序所引 BL-MOSS reduction 的适用范围；本文不进行新颖性评估，也不以文献名称替代尚未完成的项目上界证明。

本文对原记录做了必要的状态校准：Part I 的 no-regret 充分性与 sharp-anytime 已由补充证明闭合；Part II 则继续严格区分下界量词、分数与整数对象、oracle release 与在线 revelation，以及 lower/upper workload，不把 regular-instance matching 写成已经完成的定理。同步的原始参考文件未作修改。

本轮补充证明：[Part I — Arrival-only minimax 闭合证明](/Users/xxy/.codex/.chatgpt-projects/g-p-6ab8d1d3edd8819188334f7a3a24834b/Part-I-Arrival-Minimax-闭合证明.md)。其中给出新寿命分组引理、普通 UCB 的 anytime 上界、分块静态 MOSS 的无对数充分性及全部边界处理。
