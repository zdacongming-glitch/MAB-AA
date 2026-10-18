# Part I — Arrival-only minimax：闭合证明

2026-09-27。本文补齐阶段性总结中 Part I 的证明，并给出一个更简单的上界实现。

**本轮闭合的范围：** lifetime fixed point 的 minimax 刻画（允许对数因子）、同一个 horizon-free 策略对所有终点的相应期望风险界、以及 uniform anytime no-regret 的精确到达条件。速率结论与无对数 no-regret 结论分别使用下面明确给出的两个策略；不额外声称同一个策略同时满足两种保证。

核心改变有两点。第一，寿命分组直接使普通 anytime UCB 达到 $\widetilde O(\Gamma_T)$，所以无需 horizon-aware capped bonus。第二，通过冻结块内臂集，将 no-regret 充分性完全归约到标准静态 MOSS；不调用未经证明的 growing-MOSS reduction。

## 1. 模型、定义与主定理

固定任意确定、外生的无限到达路径。可数臂集中的臂 $i$ 于 $\tau_i$ 到达，此后永久可用，

$$
\varnothing\ne A_t=\{i:\tau_i\le t\},\qquad K_t=|A_t|<\infty.
$$

允许任意有限大小的 batch arrivals。各臂奖励流相互独立，每个流 i.i.d.，支持在 $[0,1]$，均值 $\mu_i$ 不随时间改变。定义

$$
B_t=\max_{i\in A_t}\mu_i,\qquad
R_T=\sum_{t=1}^T(B_t-\mu_{I_t}),\qquad
\mathcal R_T(\pi,P)=\mathbb E_P^\pi R_T.
$$

$B_t$ 非减且 $0\le B_t\le1$。策略只需观察当前可用集与过去奖励。

任取固定 $a\in A_1$，对 $i\in A_T$ 记

$$
H_i=H_{i,T}=T-\tau_i+1,
\qquad
V_T(r)=\sum_{i\in A_T\setminus\{a\}}H_i\mathbf1\{H_i>r\}.
$$

当 $K_T\ge2$ 时，定义整数固定点

$$
\Gamma_T=\min\{r\in\{1,\ldots,T\}:V_T(r)\le r^2\}.
\tag{1}
$$

当 $K_T=1$ 时定义 $\Gamma_T=0$。该值不依赖具体 anchor，因为所有 $a\in A_1$ 的 lifetime 都为 $T$。

令

$$
F_T(\Gamma)=
\begin{cases}
0,&\Gamma=0,\\
\Gamma\sqrt{\log(2T)\,[1+\log(T/\Gamma)]},&1\le\Gamma\le T.
\end{cases}
$$

**Theorem A — Minimax 与 sharp-anytime（对数精度）。** 存在绝对常数 $c,C>0$ 与一个不知 $T$、未来到达或最终臂数的策略 $\pi^{\rm U}$，使对每个到达路径和每个 $T$，

$$
\boxed{
c\Gamma_T
\le \inf_\pi\sup_P\mathcal R_T(\pi,P)
\le\sup_P\mathcal R_T(\pi^{\rm U},P)
\le\min\{T,CF_T(\Gamma_T)\}.
}
\tag{2}
$$

左侧的下确界即使允许策略事先知道 $T$ 与完整到达路径，下界也成立；右侧由同一个 fully causal、horizon-free UCB 实现。特别地，schedule-minimax 风险是 $\widetilde\Theta(\Gamma_T)$。

“对所有 $T$”指同一个策略逐个终点满足期望风险界，不是未经证明的单一高概率事件上的所有终点界。

**Theorem B — 无对数 coarse anytime 上界。** 存在另一个不知终点、未来到达或到达速率的策略 $\pi^{\rm B}$，使

$$
\boxed{
\sup_P\mathcal R_T(\pi^{\rm B},P)
\le \min\{T,C T^{2/3}K_T^{1/3}\}.
}
\tag{3}
$$

这是用于判定可学习性的上界，不追求 $\Gamma_T$ 的精确速率。$K_T=1$ 时真实风险仍然恰为零。

**Theorem C — 精确 uniform learnability 边界。** 对同一条无限到达路径，

$$
\boxed{
K_t=o(t)
\iff\Gamma_T=o(T)
\iff
\exists\pi_\infty:
\sup_P\frac{\mathcal R_T(\pi_\infty,P)}T\longrightarrow0.
}
\tag{4}
$$

充分性由同一个 $\pi^{\rm B}$ 对所有满足 $K_t=o(t)$ 的路径实现，不需要知道 $K_t/t$ 趋零的速度。这里的 supremum 覆盖全部独立 stationary bounded reward laws；不是仅对每个固定环境分别断言 no-regret。

## 2. 下界的完整证明

### 2.1 非平凡实例的常数风险下界

若 $K_T\ge2$，选择首次存在至少两个可用臂的时刻及其中一个当时尚未观察过的臂 $i$。将其余臂均值固定为 $1/2$，仅令 $\mu_i$ 为 $0$ 或 $1$。这两个环境在该时刻动作选择之前具有相同历史分布。

若当轮选择 $i$ 的概率为 $p$，则两环境当轮的期望 regret 分别为 $p/2$ 和 $(1-p)/2$，故最坏风险至少为 $1/4$。因此任何全模型统一风险界 $R$ 均满足 $R\ge1/4$。

### 2.2 同一个 reference 支付所有信息需求

固定任意策略，令 $R=\sup_P\mathcal R_T(\pi,P)$。若 $R$ 已与 $T$ 同阶，由 $\Gamma_T\le T$ 立即得到结论；下面的证明也包括该截断情形。

设

$$
\mathcal L_R=\{i\ne a:H_i\ge64R\},
\qquad\delta_i=8R/H_i\le1/8.
$$

构造 Bernoulli reference：

$$
\mu_i^{(0)}=1/2-\delta_i\quad(i\in\mathcal L_R),
\qquad\mu_j^{(0)}=1/2\quad(j\notin\mathcal L_R).
$$

anchor 始终可用，所以 reference benchmark 恒为 $1/2$，且

$$
\sum_{i\in\mathcal L_R}\delta_i\mathbb E_0N_i(T)\le R.
\tag{5}
$$

对每个 $i\in\mathcal L_R$，替代环境只将 $\mu_i$ 改为 $1/2+\delta_i$。令

$$
E_i=\{N_i(T)\ge H_i/2\}.
$$

reference 下，由单臂 regret 预算与 Markov，

$$
\Pr_0(E_i)\le\frac{2R}{\delta_iH_i}=1/4.
$$

替代环境中，臂 $i$ 到达后的每次不选 $i$ 都损失至少 $\delta_i$，所以

$$
\Pr_i(E_i^c)\le\frac{2R}{\delta_iH_i}=1/4.
$$

数据处理与 bandit KL chain rule 得到

$$
\mathbb E_0N_i(T)\,
\operatorname{kl}(1/2-\delta_i,1/2+\delta_i)
\ge\operatorname{kl}(1/4,3/4)=\tfrac12\log3.
\tag{6}
$$

对于 $0<\delta\le1/8$，

$$
\operatorname{kl}(1/2-\delta,1/2+\delta)
=2\delta\log\frac{1+2\delta}{1-2\delta}
\le16\delta^2.
$$

将 (6) 代入 (5)，得到

$$
\sum_{i\in\mathcal L_R}H_i
\le\frac{256}{\log3}R^2<234R^2.
\tag{7}
$$

若 $r_0=\lceil64R\rceil<T$，则

$$
V_T(r_0)\le234R^2\le r_0^2,
$$

因此 $\Gamma_T\le r_0\le68R$，最后一步使用 $R\ge1/4$。若 $r_0\ge T$，则同样 $\Gamma_T\le T\le r_0\le68R$。

于是 $\mathfrak R_T(\tau)\ge\Gamma_T/68$。常数没有优化。该论证只用 Bernoulli 子类，故适用于全部 bounded rewards。

## 3. 新的核心引理：按剩余寿命控制整个 occupancy

**Lemma 1 — Lifetime grouping。** 固定 $T$、整数 $1\le r<T$。对任意合法动作轨迹，令 $n_i=N_i(T)$，并令

$$
J=\left\lceil\log_2(T/r)\right\rceil.
$$

则

$$
\boxed{
\sum_{i\ne a:\,H_i>r}\sqrt{n_i}
\le\sqrt{2J V_T(r)}.
}
\tag{8}
$$

**证明。** 将长寿命臂划分为

$$
G_k=\{i\ne a:2^kr<H_i\le2^{k+1}r\},
\qquad k=0,\ldots,J-1.
$$

该组全部臂只能在最后 $2^{k+1}r$ 轮内被采样。因此，无论 arrivals 如何成批、策略如何自适应，

$$
\sum_{i\in G_k}n_i\le2^{k+1}r.
$$

由 Cauchy–Schwarz，记 $V_k=\sum_{i\in G_k}H_i$，有

$$
\sum_{i\in G_k}\sqrt{n_i}
\le\sqrt{|G_k|\sum_{i\in G_k}n_i}
\le\sqrt{|G_k|2^{k+1}r}
\le\sqrt{2V_k}.
$$

再对至多 $J$ 组作一次 Cauchy–Schwarz，得到 (8)。证毕。

**该引理为何关键？** 普通 UCB 的 regret 可以按臂写成若干 $\sqrt{N_i}$。以往若仅用 $\sum_iN_i=T$，会得到粗糙的 $\sqrt{K_TT}$。式 (8) 利用每组的到达时间窗口，把它改成 $\sqrt{V_T(r)}$，只损失一个寿命层数的平方根。

分组只用于事后分析。算法不需要知道 $T$、$r$ 或任何臂的最终 lifetime。

**Lemma 2 — Anchor 的竞争窗口。** 若 $K_T\ge2$，记

$$
H_{\max}=\max_{i\ne a}H_i.
$$

则

$$
\boxed{H_{\max}\le\Gamma_T^2.}
\tag{9}
$$

若 $H_{\max}>\Gamma_T$，该臂进入 $V_T(\Gamma_T)$，故 $H_{\max}\le V_T(\Gamma_T)\le\Gamma_T^2$。否则 $H_{\max}\le\Gamma_T\le\Gamma_T^2$。anchor 在首个其他臂到达以前是唯一可用臂，regret 为零；其可能产生正 regret 的轮数至多 $H_{\max}$。

## 4. 普通 anytime UCB 的 $\Gamma_T$ 上界

### 4.1 算法完全指定

第 $t$ 轮：

1. 若存在尚未采样的可用臂，从中按固定标签次序选一个并采样。
2. 否则，选择最大 index 的可用臂，其中

$$
U_i(t)=\widehat\mu_i(N_i(t-1))
+\sqrt{\frac{3\log(2t)}{N_i(t-1)}}.
\tag{10}
$$

ties 按固定次序处理。所有历史样本持续保留，不重启、不截断 bonus。所有可用集合均有限，所以动作定义良好。$a$ 仅用于证明，不影响策略。

### 4.2 不依赖 $K_T$ 的集中控制

**Lemma 3 — Discovery-order confidence。** 令 $\mathcal E_t$ 表示时刻 $t$ 之前已经采样的每个臂，其当前经验均值满足

$$
|\widehat\mu_i(N_i(t-1))-\mu_i|
\le\sqrt{\frac{3\log(2t)}{N_i(t-1)}}.
$$

则

$$
\Pr(\mathcal E_t^c)\le\frac1{32t^4},
\qquad
\sum_{t\ge1}\Pr(\mathcal E_t^c)<1.
\tag{11}
$$

**证明。** 按“首次被采样”的顺序标记臂。第 $j$ 个被首次采样的臂，在其第一次奖励被观察以前，其完整奖励流仍与此前历史独立。条件于该历史与被选标签，对它的前 $n$ 个奖励用 Hoeffding，得到偏离阈值的概率至多

$$
2\exp[-6\log(2t)].
$$

截至时刻 $t$，至多出现 $t$ 个这样的标签，每个实际样本数至多为 $t$。对 discovery rank 与样本数各作一次 union bound，得到

$$
2t^2(2t)^{-6}=1/(32t^4).
$$

也可预先生成各臂独立奖励流，对尚未发生的样本使用这些潜在变量书写同一证明。全程不需要对全部 $K_T$ 个臂 union bound。证毕。

如果本轮不是初始化轮，则所有可用臂都已经采样。因此在 $\mathcal E_t$ 上，真实最优臂的 index 不小于 $B_t$，由 index 最大性可得

$$
B_t-\mu_{I_t}
\le2\sqrt{\frac{3\log(2t)}{N_{I_t}(t-1)}}.
\tag{12}
$$

若仍有未采样臂，本轮由初始化单独计费，不调用 (12)。

### 4.3 分项计费

若 $\Gamma_T=0$，唯一可用臂被选择，风险为零。若 $\Gamma_T=T$，平凡界 $R_T\le T$ 足够。下设 $r=\Gamma_T\in[1,T)$。

**短寿命臂。** $H_i\le r$ 的所有臂只会在最后 $r$ 轮被选择，故其全部 regret 至多 $r$，包括它们的初始化和坏置信事件。

**长寿命臂初始化。** 每个长寿命臂只初始化一次，且

$$
|\{i\ne a:H_i>r\}|\le V_T(r)/r\le r.
$$

故该部分 regret 至多 $r$。

**长寿命臂的其余 good-event pulls。** 对单个臂累加 (12)，使用
$\sum_{n=1}^m n^{-1/2}\le2\sqrt m$，得到

$$
R_{\rm long,good}
\le4\sqrt{3\log(2T)}\sum_{i\ne a:H_i>r}\sqrt{N_i(T)}.
$$

由 Lemma 1 和 $V_T(r)\le r^2$，

$$
R_{\rm long,good}
\le4\sqrt{6J\log(2T)}\,r.
\tag{13}
$$

**Anchor。** 首次采样至多付 1。其余产生正 regret 的 good-event pulls 至多 $H_{\max}$ 次；对应的历史样本数严格增加，所以同样累加 (12) 得

$$
R_{a,good}\le1+4\sqrt{3\log(2T)}\sqrt{H_{\max}}
\le1+4r\sqrt{3\log(2T)}.
\tag{14}
$$

早期对 anchor 的免费样本只会让分母增大，不妨碍此界。

**坏事件。** 每轮损失至多 1，由 (11) 得总期望贡献小于 1。

合并，

$$
\mathcal R_T(\pi^{\rm U},P)
\le2r+2+4r\sqrt{3\log(2T)}
+4r\sqrt{6J\log(2T)}.
$$

由于

$$
J\le1+\log_2(T/r),
$$

上述式子被 $CF_T(r)$ 控制。所有常数与奖励分布无关，故可以对 $P$ 取 supremum。Theorem A 证毕。

**结论：sharp-anytime 不再是独立缺口。** (10) 的同一策略没有使用终点，但对每个实际前缀都满足 (2)。这来自直接的前缀分析，不需要从 horizon-doubling 推断。

## 5. 无对数充分性：冻结臂集的分块算法

### 5.1 唯一调用的外部 bandit 定理

使用标准静态有限臂 MOSS 定理：对 $k$ 个从区块开始就全部可用的臂、已知区块长度 $h$，存在策略满足

$$
\sup_P\mathbb E\sum_{u=1}^{h}(\mu^\star-\mu_{I_u})
\le C_0\sqrt{kh}.
\tag{15}
$$

可取 $C_0=49$。这是 [Audibert–Bubeck (2009), Theorem 5](https://www.cs.mcgill.ca/~colt2009/papers/022.pdf) 的静态 bounded-reward 结论。若 $k>h$，直接使用任意动作规则即可，因为 $R_h\le h\le\sqrt{kh}$；不要求在 $h$ 轮内初始化全部 $k$ 个臂。

MOSS 的局部 index 可写为

$$
\widehat\mu_i(n)+\sqrt{\frac{[\log(h/(kn))]_+}{n}},
\qquad n\ge1,
$$

未采样臂 index 为 $+\infty$。这里只在真正固定的臂集上运行它。

### 5.2 延迟接纳的确定性损失

**Lemma 4 — Frozen-block delay。** 在一个 epoch 中，将时间划为连续 blocks $[s_b,e_b]$。block 内仅允许选择 $A_{s_b}$ 中的臂；新 arrivals 在下个 block 才接纳。若每个 block 长度至多 $L_{\max}$，则

$$
\boxed{
\sum_b\sum_{t=s_b}^{e_b}(B_t-B_{s_b})
\le L_{\max}.
}
\tag{16}
$$

证明：每个 block 的贡献不超过
$L_{\max}(B_{e_b}-B_{s_b})$。各 block 不交叠且 $B_t$ 非减，故这些增量之和不超过 1。证毕。

这个界利用的是整个 benchmark 的总涨幅，允许单次跳跃很大、record arms 很多以及任意 batches。它没有对 arrival 数逐个收费。

### 5.3 算法完全指定

使用固定几何 epochs

$$
E_m=\{2^m,\ldots,2^{m+1}-1\},\qquad n_m=2^m,
\quad m=0,1,\ldots.
$$

在 epoch $E_m$ 的每个 block 起点 $s$：

1. 观察当前 $A_s$，记 $k=K_s$，冻结本 block 的臂集为 $A_s$。
2. 取计划长度

$$
\ell=\left\lceil n_m^{2/3}k^{1/3}\right\rceil,
\qquad
h=\min\{\ell,2^{m+1}-s\}.
\tag{17}
$$

3. 在该固定臂集上，以局部 horizon $h$ 重新运行静态 MOSS；不使用以前 blocks 的样本。若 $k>h$，用上一节说明的平凡替代规则。
4. 执行满 $h$ 轮，再开始下一 block；在 epoch 结束时进入下一 epoch。

舍弃旧样本是为了使证明直接归约到静态定理，并非效率上的必要设计。块长只依赖已知 epoch 尺度与当前臂数。该策略不知道评估终点 $T$，也不知道未来 arrivals 或增长速率。

### 5.4 对任意截断前缀的 epoch 界

固定任意评估终点 $T$，考察某个与 $[1,T]$ 相交的 epoch，其完整长度为 $n=2^m$。记 $M=K_T$。

若 $M>n$，本 epoch 的 regret 至多 $n\le n^{2/3}M^{1/3}$，已经足够。

下设 $M\le n$。截至 $T$ 已启动的每个 block 满足 $k\le M$，故

$$
L_{\max}:=\max\ell
\le\left\lceil n^{2/3}M^{1/3}\right\rceil\le n.
$$

除最后一个 block 外，其余已完成 blocks 的实际长度均为计划长度；最后一个可能被 epoch 末端或评估终点截断。因此

$$
\sum_{b:\,s_b\le T}\ell_b\le n+L_{\max}\le2n.
\tag{18}
$$

固定 block 内，以 $B_{s_b}$ 为 benchmark 的损失非负。所以即使 $T$ 落在 block 中途，该前缀的期望内部 regret 也不超过运行完计划的静态实验的期望内部 regret。利用 (15)，

$$
\mathbb E R^{\rm int}_{b,\le T}
\le C_0\sqrt{k_bh_b}
\le C_0\sqrt{k_b\ell_b}.
$$

由 $\ell_b\ge n^{2/3}k_b^{1/3}$，

$$
\sqrt{k_b\ell_b}
=\ell_b\sqrt{k_b/\ell_b}
\le\ell_b(k_b/n)^{1/3}
\le\ell_b(M/n)^{1/3}.
$$

使用 (18) 后，内部 regret 总额至多

$$
2C_0 n^{2/3}M^{1/3}.
\tag{19}
$$

条件于 block 开始前的历史，未使用奖励仍是相互独立的 i.i.d. 样本，因此可以在每个 block 合法使用静态定理并取迭代期望。

另一方面，由 Lemma 4，接纳延迟造成的 regret 至多

$$
L_{\max}\le2n^{2/3}M^{1/3}.
\tag{20}
$$

于是对任意完整或截断 epoch，

$$
\boxed{
\mathbb E R_{E_m\cap[1,T]}
\le C_1(2^m)^{2/3}K_T^{1/3}.
}
\tag{21}
$$

### 5.5 几何求和

由于 $\sum_{2^m\le T}(2^m)^{2/3}\le C_2T^{2/3}$，由 (21) 得

$$
\sup_P\mathcal R_T(\pi^{\rm B},P)
\le C T^{2/3}K_T^{1/3}.
$$

再与 $R_T\le T$ 合并，得到 Theorem B。证明既不包含 $\log T$ 损失，也不需要事先确定 $K_T=o(T)$ 的收敛速度。

## 6. Learnability 的充要条件

### 6.1 到达几何

若 $K_t=o(t)$，则

$$
S_T:=\sum_{i\ne a}H_i=\sum_{t=1}^T(K_t-1)=o(T^2).
$$

由 $V_T(r)\le S_T$，取 $r=\lceil\sqrt{S_T}\rceil$ 并与 $T$ 截断，得到 $\Gamma_T=o(T)$。

反之，若存在 $\varepsilon>0$ 与 $t_j\to\infty$ 满足 $K_{t_j}\ge\varepsilon t_j$，令 $T_j=2t_j$。在 $t_j$ 前到达的非 anchor 臂均有 $H_{i,T_j}\ge t_j+1$。对 $r<t_j$，

$$
V_{T_j}(r)\ge(K_{t_j}-1)t_j\gtrsim\varepsilon T_j^2.
$$

因此 $\Gamma_{T_j}\ge c_\varepsilon T_j$，不可能 $\Gamma_T=o(T)$。

### 6.2 算法充分性

若 $K_T=o(T)$，Theorem B 直接给出

$$
\sup_P\frac{\mathcal R_T(\pi^{\rm B},P)}T
\le C(K_T/T)^{1/3}\longrightarrow0.
$$

这使用同一个 horizon-free 策略，因而是 uniform anytime 充分性。

### 6.3 信息论必要性

若 $K_t\not=o(t)$，上一节给出某个子序列上 $\Gamma_{T_j}\gtrsim T_j$。Theorem A 的下界迫使每个策略在该子序列上的全模型最坏风险为 $\Omega(T_j)$。故不存在 uniform anytime no-regret 策略。Theorem C 证毕。

这不推出存在一个固定 reward instance 在所有这些终点都使某策略线性失败；后者需要不同量词。当前必要性恰好对应全文定义的 $\sup_P\mathcal R_T$。

## 7. 可以保留的无对数 $\Gamma_T$ coarse 推论

原记录提出的较强辅助式

$$
\mathfrak R_T(\tau)\lesssim\Gamma_T+\sqrt{\Gamma_TT}
$$

本轮没有证明，也不用于任何主定理。现在可用一个足够闭合 learnability、且有直接证明的版本替代它：

$$
\boxed{
\mathfrak R_T(\tau)
\le\min\{T,C[\Gamma_T+T^{2/3}\Gamma_T^{1/3}]\},
\quad \Gamma_T\ge1.
}
\tag{22}
$$

证明：取 $r=\Gamma_T$，忽略 $T-r$ 之后到达的臂，外部损失至多 $r$。留下的非 anchor 臂数至多 $V_T(r)/r\le r$，故总臂数至多 $r+1\le2r$。在保留的到达过程上应用 Theorem B，得到内部风险 $CT^{2/3}r^{1/3}$。此推论只陈述 schedule-minimax 上界，允许知道相应截断点；Theorem C 的 unknown-future 实现仍直接使用不依赖该截断的 $\pi^{\rm B}$。

## 8. 结论的最终边界

| 命题 | 本轮状态 |
|---|---|
| $c\Gamma_T$ 的 minimax 下界 | theorem，完整两点/共同预算证明 |
| $\widetilde O(\Gamma_T)$ 有限时域上界 | theorem，由普通 UCB 与寿命分组证明 |
| 同一 horizon-free UCB 对全部终点的 $\widetilde O(\Gamma_T)$ 期望界 | theorem，直接前缀分析 |
| $\Gamma_T=o(T)\iff K_t=o(t)$ | theorem，确定性几何 |
| 存在 uniform anytime no-regret 策略当且仅当 $K_t=o(t)$ | theorem，分块静态 MOSS 充分性加信息下界 |
| 无对数精确 minimax $\Theta(\Gamma_T)$ | 本轮未证明，不属于“对数精度匹配”的结论 |
| 原辅助式 $\Gamma_T+\sqrt{\Gamma_TT}$ | 本轮未证明，已用 (22) 替代，不再作为主链条前提 |
| 同一个策略同时具有 sharp-$\Gamma_T$ 与全部 $o(t)$ 路径上的无对数 no-regret 保证 | 本轮未合并证明；两项存在性分别由 $\pi^{\rm U}$、$\pi^{\rm B}$ 实现 |

本文的算法与证明均允许任意有限 batches、未知未来 arrivals 和 $K_T\gg T$。没有使用 gap 正则性、benchmark jump 正则性或 Part II 的候选 R1/R2*/R3+。

## 9. 核验说明

本轮对下界常数、寿命分组的容量约束、anchor 窗口、discovery-order 集中控制、评估终点落在 block 中间的情况，以及 $k>h$ 的初始化边界分别作了核验。另对寿命分组和块长代数不等式进行了 20,000 组随机数值检查；这些检查仅用于发现转写错误，理论依据仍是上述逐项证明。

唯一作为标准外部输入的非平凡算法定理，是固定臂集上的静态 MOSS $O(\sqrt{kh})$ 界，其原始来源和适用范围已在第 5.1 节给出。本文未对新颖性作判断。
