# Sleeping and index baseline implementation review

复核日期：2026-10-17。复核范围：只读 `new_policies.py` 的 AUER、UCB-V、UCB1-Tuned、KL-UCB+，以及 `sb_exp3.py`。未修改运行源码，未读取或运行冻结测试场景。合成核对结果与源码 SHA256 见 `sleeping-implementation-review.json`。

结论：在永久到达、每轮一个实际观测的接口约定下，未发现这五个实现的公式、初始化或状态重置错误。下述理论适用范围和探索参数应在结果说明中保留。

## 1. AUER

原始定位：[Kleinberg、Niculescu-Mizil 和 Sharma，COLT 2008 版本](https://www.cs.cornell.edu/~rdk/papers/colt08.pdf)，Section 3.2.1，Algorithm 2，PDF 第 8 页。代码 `kind == 1` 使用

$$
\frac{S_i}{n_i}+\sqrt{\frac{8\log t}{n_i}}.
$$

常数 8 与原稿一致。原算法先选可用且尚未观测的臂，代码也先扫描 `n[i] == 0`。同批到达多个臂时，按到达顺序逐轮完成初次观测，不额外增加物理采样。旧臂统计量保留。该方法与常见 available-arm UCB1 属同一机制，区别是探索半径常数，不能在方法数量上当作完全独立的机制。

## 2. UCB1-Tuned

原始定位：[Auer、Cesa-Bianchi 和 Fischer 2002](https://homes.di.unimi.it/~cesabian/Pubblicazioni/ml-02.pdf)，Section 4，期刊第 245 页，PDF 第 11 页。代码 `kind == 3` 使用

$$
\widehat\mu_i+\sqrt{\frac{\log t}{n_i}\min\left\{\frac14,\widehat V_i+\sqrt{\frac{2\log t}{n_i}}\right\}},
\qquad
\widehat V_i=\frac{Q_i}{n_i}-\widehat\mu_i^2.
$$

这是原文的经验方差分母 $n_i$，不是无偏样本方差。代码将舍入造成的负方差截为零，属于数值保护。初次采样规则正确。原文明确未为该 tuned 版本证明 regret 界，因此不应把 UCB1 的定理自动转给它。

## 3. UCB-V

原始定位：[Audibert、Munos 和 Szepesvári，Tuning bandit algorithms in stochastic environments](https://sites.ualberta.ca/~szepesva/papers/ucb_alt.pdf)，Section 2.1、式 (3)，PDF 第 6 页。原文允许调参 $c$ 和探索函数 $E_{s,t}$。代码 `kind == 2` 对应支持上界 $b=1$、$c=1$、$E_{s,t}=\log t$：

$$
\widehat\mu_i+\sqrt{\frac{2\widehat V_i\log t}{n_i}}+\frac{3\log t}{n_i}.
$$

公式与该参数配置一致。该版本不等于作者在 PDF 第 11 页另讨论的激进临界参数 $c=1/6$。需要区分代码定义与定理：原文一项 logarithmic-regret 推论要求 $E_t=\zeta\log t$ 且 $\zeta>1$，当前临界取值 $\zeta=1$ 不能直接援引那条推论。这里不存在实现偏差，也未进行结果导向调参。

## 4. KL-UCB+

原始定位：[Garivier 和 Cappé 2011](https://proceedings.mlr.press/v19/garivier11a/garivier11a.pdf)，Algorithm 1（期刊第 363 页、PDF 第 5 页）；Section 5.1 的 KL-UCB+ 定义跨期刊第 367–368 页、PDF 第 9–10 页。代码 `kind == 4` 使用实验版 $c=0$：

$$
\sup\left\{q\in[\widehat\mu_i,1]:n_i d_{\mathrm{Ber}}(\widehat\mu_i,q)\le\log(t/n_i)\right\}.
$$

在合法物理状态中 $1\le n_i\le t-1$，对数非负，所以 `max(0, log(t / ni))` 不改变合法状态下的策略。每个新臂先实际观测一次，符合原始 index 策略的初始化逻辑。32 次二分保留上侧端点，指数绝对近似误差至多 $2^{-32}$；通常不会改变排序，近乎完全相等时应理解为数值求解误差。Bernoulli KL 的零、一端点已单独处理。一般有界奖励直接使用 Bernoulli KL 是该方法允许的 bounded-reward 版本，不要求将观测随机二值化。

原文以 $c=3$ 证明的原始 KL-UCB 渐近结果，不可直接当作当前 $c=0$、plus 版本或永久到达版本的已证明结果。

## 5. SB-EXP3-ATGT

原始定位：[Nguyen 和 Mehta 2024](https://proceedings.mlr.press/v238/nguyen24d/nguyen24d.pdf)，Appendix F，Algorithm 5，PDF 第 33 页；概率和估计见 Algorithm 1、式 (4)–(6)，PDF 第 4 页。

逐项核对：

1. 初始 $U=0,C=1,b=1$，所有尚未到达臂没有采样概率；到达时分数 $L_i=0$。
2. 到达先于本轮决策。永久可用使 $|V\cup\mathcal A_t|=k$，因此代码以 `log(k)` 判断第一层阈值是合法的 setting 特化。
3. 第一层使用严格大于 $2^C$。触发后先让 $C$ 增加一次，再继续增加直到容纳当前 $\log k$；清空分数并重置 $U=0,b=1$。
4. 第二层随后判断 $U+k>2^b$，相等时不重置。触发后先让 $b$ 增加一次，再继续增加直到容纳当前 $k$；重置 $U=0$ 和分数。注意不是简单把阈值扩大到包含旧的 $U+k$：原算法会丢弃旧 subepisode 的累计量，代码与此一致。
5. 完成以上两层后才更新 $U\leftarrow U+k$，再令 $\eta=\sqrt{2^{C+1}/2^b}$ 并由 $\exp(\eta L_i)$ 构造概率。
6. 当前使用 $\gamma=0$，观测损失 $\ell=1-x$ 后，所有 awake 分数增加 $\ell$，选中臂再扣除 $\ell/p_i$。保留绝对分数使以后到达的臂能正确从零开始。不能省略共同增加项后仍让新臂从零初始化。
7. 原文没有强制逐臂初拉，代码也没有。数值 softmax 减去最大指数，仅用于构造概率，没有改变存储分数。浮点累计概率尾部的 fallback 选择正概率臂，避免除零。

保证范围仍是 per-action sleeping regret，不是本研究的逐轮 best-current-arm dynamic regret 定理。这是比较器范围限制，不是运行实现错误。

## 合成核对

- AUER、UCB-V、UCB1-Tuned、KL-UCB+ 各 400 个独立合成状态，覆盖 Bernoulli 和一般有界观测；与直接公式比较，全部动作一致。KL-UCB+ 参考使用独立 Brent 求根。
- 4 个 index 策略各检查一例混合旧臂和多个未拉新臂的状态，均选择首个尚未实际观测的可用臂。
- SB-EXP3 使用 90 轮合成轨迹，臂数由 1 增至 3、64、10000。覆盖累计量阈值恰等、第一层多次递增、同轮两层重置及大批到达。与保留显式集合 $V$ 的独立参考比较：概率误差小于 $10^{-12}$，分数误差小于 $10^{-9}$，元数据完全一致。
- 检查前后 `new_policies.py` 和 `sb_exp3.py` 的 SHA256 相同。没有以冻结测试结果更改算法或参数。
