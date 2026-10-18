# 强基线归约与理论边界核查

本文档是评审时的独立推导，用于判断正式稿件增加了什么。它没有修改正式算法，也不为其提供替代证明。全文中 $T$ 始终表示实际、确定的拉臂次数。

## 1. 与 stochastic sleeping-bandit comparator 的关系

固定一个外生到达日程和有限预算 $T$，设截至 $T$ 共有 $K_T<\infty$ 个臂到达，每个臂均值固定。将这些臂按真实均值递减排序为 $\sigma^\star$，并用固定规则处理并列。则每个时刻都有

$$
\mu_{\sigma^\star(\mathcal A_t)}
=\max_{i\in\mathcal A_t}\mu_i.
$$

所以，与这个 mean-ordered policy 比较的 expected pseudo-regret，恰好是稿件的 expected dynamic pseudo-regret。这里没有把期望之外的最大实现奖励当作 comparator。

Kleinberg、Niculescu-Mizil、Sharma 的正式论文第 1.1 节区分了 maximum expected reward 与 expected maximum reward；其 stochastic 模型适用于这里的均值比较。[KNS 2010，正式全文](https://link.springer.com/content/pdf/10.1007/s10994-010-5178-7.pdf)

KNS 原文假设已知有限总臂池；这与潜在无限到达池存在形式差别。下面直接使用到达序号分配置信预算，说明不预知全部臂或 $K_T$ 本身，并不阻止简单 UCB 构造。

## 2. 不预知最终臂数的简单 UCB 上界

**假设。** 每个有限时域到达臂数有限，初始可用集非空；所有臂一旦到达就永久可用；奖励在 $[0,1]$，各臂具有相互独立的 i.i.d. 奖励流。到达日程外生且与这些奖励流独立。若日程随机，下述推导先条件于日程。当前新臂在本次动作之前可见；这是清晰化时序的约定，不是对原存档代码的描述。

**策略。** 已知实际预算 $T\ge1$。给臂分配从 1 开始的到达序号 $i$。对已采样 $n\ge1$ 次的臂，设

$$
\ell_i=\log\!\left(\frac{\pi^2 i^2 T^2}{3}\right),
\qquad
b_i(n)=\sqrt{\frac{\ell_i}{2n}},
\qquad
U_i(n)=\widehat\mu_i(n)+b_i(n).
$$

未采样臂指数为 $+\infty$。每一步在当前可用臂中选最大指数；其余并列以固定规则处理。算法不知道 $K_T$，不需要 gap 稳定性、累计跳跃条件、轮数 $M$ 或未来到达界 $K(m)$。

**统一事件。** 令 $\mathcal E$ 为所有到达序号、所有前缀 $1\le n\le T$ 的经验均值都在上述半径内。对固定的 $i,n$，双侧 Hoeffding 给出

$$
\Pr\!\left\{|\widehat\mu_i(n)-\mu_i|>b_i(n)\right\}
\le 2e^{-\ell_i}
=\frac{6}{\pi^2 i^2T^2}.
$$

因此

$$
\Pr(\mathcal E^c)
\le \sum_{i=1}^{\infty}\sum_{n=1}^{T}
\frac{6}{\pi^2 i^2T^2}
=\frac1T.
$$

这是对全部奖励前缀的事件，允许实际采样次数和动作依赖过去奖励；不需要条件于随机选中的样本量或删除链。

**逐拉臂收费。** 在 $\mathcal E$ 上，除首次采样外，若当前选择 $I_t=i$，则所有当前可用臂均已初始化。令 $i_t^\star$ 为当前可用最优臂，则

$$
\mu_{i_t^\star}
\le U_{i_t^\star}
\le U_i
\le \mu_i+2b_i(n_i(t-1)).
$$

记 $\ell_K=\log(\pi^2 K_T^2T^2/3)$、最终计数为 $N_i(T)$。最多 $K_T$ 次初始化各损失至多 1，并且

$$
\begin{aligned}
R_T
&\le K_T+
\sqrt{2\ell_K}
\sum_{i=1}^{K_T}\sum_{n=1}^{(N_i(T)-1)_+}\frac1{\sqrt n}\\
&\le K_T+2\sqrt{2\ell_K}\sum_{i=1}^{K_T}\sqrt{N_i(T)}\\
&\le K_T+2\sqrt{2K_TT\ell_K}.
\end{aligned}
$$

坏事件上 $R_T\le T$。故对于确定的外生到达日程，

$$
\boxed{
\mathbb E R_T
\le
\min\!\left\{
T,\;
K_T+2\sqrt{2K_TT\log(\pi^2K_T^2T^2/3)}+1
\right\}.
}
$$

若日程随机，应再对右侧取期望，不能把随机 $K_T$ 无说明地当作确定数。这一推导是标准乐观性分析在当前模型中的直接适配，不作为新研究贡献。

**它证明了什么。** 对 $K_T\log(K_TT)=o(T)$ 的路径，简单 UCB 已能实现次线性 dynamic regret，而无需稿件两项 gap/jump 条件。因此，“首次能处理 drifting benchmark”或“简单 UCB 在目标上不适用”不是可用的创新论据。

**它没有证明什么。** 这里的对数项不是稿件声称的 $\log K$；它不证明原文精细上界完全被同一个定理覆盖，不证明该保守 UCB 数值表现最佳，也不把原固定臂 MOSS 的最优性无条件移植到增长臂集。若稿件的对数改进或路径精细化能够在相同实际预算、相同实例类下严格成立，仍应另行评估其价值。

## 3. 单调可用性确实有可用结构，但普通置信淘汰也能使用

若置信区间同时有效，且

$$
U_i<\max_{j\in C_t}L_j,
$$

则存在已到达的臂 $j$ 满足 $\mu_i<\mu_j$。因为 $j$ 永久可用，臂 $i$ 以后不会成为所有已到达臂中的最优者。并列最优臂不会被严格不等式删除。即使参考臂随后也被删除，真实性质“存在一个永久可用且更好的臂”仍成立。

这说明单调到达值得单独研究；同时也说明“能永久安全淘汰”并非双层 UCB-AA 独有。要体现第二级创新，需要进一步展示新的筛选代价、候选集质量、有效维护成本或信息复杂度结论。

如果单纯把接纳放到间距不超过 $H$ 的固定日历网格，而暂不讨论接纳后采样等待和误删，那么每次最佳均值上升 $\beta_j$ 的纯接纳延迟至多 $H-1$，从而

$$
D_T^{\mathrm{arrival}}
\le (H-1)\sum_j\beta_j
=(H-1)(\mu_T^\star-\mu_1^\star)
\le H-1.
$$

这个独立路径界说明长轮接纳造成的 delay 很大一部分来自算法安排。它不消除识别新优臂所需的统计成本，也不自动证明“固定网格 + 原 UCB-AA”整个算法的 regret 界。

## 4. Theorem 5 构造的非空参数范围

正式稿 Theorem 5 的参数要求

$$
\theta_{m+1}\ge\theta_m+\varepsilon_m,
\qquad
\theta_m-\varepsilon_m,\theta_m+\varepsilon_m\in[\gamma,1-\gamma].
$$

对第一组不等式求和，结合最后一个臂的上界以及 $\theta_1\ge\gamma+\varepsilon_1$，得到

$$
\sum_{m=1}^{K_T}\varepsilon_m+\varepsilon_1\le1-2\gamma.
$$

特别地，$\sum_m\varepsilon_m\le1-2\gamma$。同质化推论同时要求 $\varepsilon_m\ge c_\varepsilon\sqrt{K_T/T}$，所以

$$
c_\varepsilon\,\frac{K_T^{3/2}}{\sqrt T}\le1-2\gamma,
\qquad
K_T=O(T^{1/3}).
$$

这里的 $K_T$ 是该定理的块数，实际新臂数为 $2K_T$。结论限制的是这个具体逐级抬升构造及其同质化推论，不是整个 arriving-arm 模型。它也没有否定该定理：在可行区间中，其“成对改变 challenger → 前缀 KL → TV → 对符号向量平均”的主体推导是自洽的。

但这不能与采用随机内生轮边界的 UCB-AA 上界直接宣称 minimax 匹配。需确认下界实例族满足上界的全部条件，并统一实际时间和参数范围。

## 5. Distractor 下界与 uniform goodness 的相容性

正式稿的 Definition 1 要求对随 $T$ 变化的整个局部实例族

$$
\sup_{\nu\in\mathcal V_T}\mathbb E_\nu R_T
=o(H_{\min}(T)^a)
\qquad\text{对每个 }a>0.
$$

而固定正 gap、统一有界 KL 的 distractor 定理给出

$$
\mathbb E_{\nu^{(0)}}R_T
\ge c|\mathcal I_T|\log H_{\min}(T).
$$

因此，只要 $\mathcal I_T$ 以 $H_{\min}$ 的某个正幂增长，取更小的 $a$ 就产生矛盾。在这些增长区间内，不存在满足前提的策略；这不意味着条件下界为假，而意味着它不能作为非空策略类上的最优性依据。

例如等间隔到达且 $K_T\asymp T^{1/2}$ 时，$H_{\min}\asymp T^{1/2}$。下界为 $\Omega(T^{1/2}\log T)$，但取 $a=1/2$ 的 uniform goodness 要求 $o(T^{1/4})$，二者不能同时成立。仅写 $K_T=o(T)$ 不足以解决这个问题。

## 6. 已确认的 G3 压缩反例与结论边界

两初始臂均值分别为 $1/2$ 与 $1/2-2^{-M}$；均值 $0.9$ 的第三臂在第 $M$ 轮接纳，奖励为确定值。轮边界在该构造中确定，可预先安排外生到达。取 $K=3$ 和原理论标定 $N=30n_M$。

较差初始臂满足 $m_i=M$、$\widetilde m_i=3$，且 gap 稳定性常数可取 1。原稿的累计识别项是

$$
\widetilde S_i=n_{M-1}2^{-M}=\Theta(2^M),
$$

但其所声称的单臂压缩上界

$$
\frac{32\log(N\Delta_i(M)^2)}{\Delta_i(M)}+4\Delta_i(M)
$$

仅为 $O(M)$。本次重新计算 $M=12$ 时两者分别为 14846.57 和 1653.97，后者不足前者的九分之一；$M=16,20$ 的违反继续扩大。

这反证了 [原稿第 2355 行](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:2355) 所用压缩步骤，以及依赖该步骤的现有证明链。它没有反证所有可能的平方根总 regret 上界：总采样时间也按 $4^M$ 的尺度增长。新的有效总和论证仍有可能，但必须重新完成。
