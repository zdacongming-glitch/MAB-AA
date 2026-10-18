# UCB-AA 后续研究：三项核心成果与 CP-UCB-AA 伪代码

[下载本回答的 Markdown 文档](sandbox:/mnt/data/UCB-AA_三项核心成果与CP伪代码_详细汇报.md)

图爷爷，**这轮研究不是要证明“淘汰越彻底，regret 越小”，而是要刻画：可靠地报告当前近优集合，报告得越及时，需要付出多少学习成本。**

下面的定理编号沿用现有研究记录：第一项对应 **T2**，第二项对应 **T8 及其增长率推论**，第三项对应 **T6**。算法部分给出的是这些上界使用的**固定精度 CP-UCB-AA**，不是另一个用于最终强一致性的多精度版本。现有结果已有书面证明与内部核查，但还没有经过独立外部复核。fileciteturn30file0L15-L23 fileciteturn30file1L121-L127

## 一、先把研究对象和四个参数讲清楚

### 1.1 什么是“当前近优集合”？

臂 \(i\) 在时刻 \(\tau_i\) 到达，之后永久可用。每条臂的奖励独立同分布、取值于 \([0,1]\)，均值 \(\mu_i\) 不随时间变化。不同臂的奖励流相互独立；本轮主要理论先固定外生、确定的到达日程。

定义

\[
A_t=\{i:\tau_i\le t\},\qquad
K_t=|A_t|,\qquad
B_t=\max_{i\in A_t}\mu_i.
\]

其中，\(A_t\) 是所有已到达臂，而不是算法当前认为值得保留的臂。令

\[
\Delta_i(t)=B_t-\mu_i.
\]

给定近优容忍度 \(\varepsilon>0\)，真实目标集合为

\[
\boxed{
G_t^\varepsilon
=\{i\in A_t:\Delta_i(t)\le\varepsilon\}
=\{i\in A_t:\mu_i\ge B_t-\varepsilon\}.
}
\]

因此，**判别边界是 \(B_t-\varepsilon\)，不是 \(B_t\)**。例如，当前最好均值为 \(0.50\)，\(\varepsilon=0.10\)，那么均值不低于 \(0.40\) 的臂全部属于目标集合，不只保留最好的那一条。上述模型与目标沿用本轮研究记录。fileciteturn30file0L69-L90

### 1.2 算法报告什么？“可靠”又是什么意思？

每轮观察奖励后，算法把全部 \(A_t\) 划分为三个互不相交的集合：

| 符号 | 算法给出的结论 |
|---|---|
| \(C_t\) | 已有足够证据，认证为当前近优 |
| \(D_t\) | 已有足够证据，认证为当前非近优 |
| \(V_t\) | 证据不足，暂时不作确定判断 |

定义全过程标签正确事件

\[
E_{\mathrm{lab}}
=
\left\{
\forall t\ge1:\quad
C_t\subseteq G_t^\varepsilon
\subseteq A_t\setminus D_t
\right\}.
\]

要求

\[
\boxed{\Pr(E_{\mathrm{lab}})\ge1-\delta.}
\]

这个要求同时控制所有臂、所有报告时刻的错误；它不是“每条臂各自有 \(1-\delta\) 的正确率”。不过，**它允许算法一直回答“不知道”**，所以还需要单独规定及时性。fileciteturn34file0L14-L31

### 1.3 “累计未决量”究竟在数什么？

先定义臂 \(i\) 到近优判别边界的距离：

\[
\boxed{
d_i^\varepsilon(t)
=|\Delta_i(t)-\varepsilon|
=|\mu_i-(B_t-\varepsilon)|.
}
\]

给定边界带宽 \(\eta>0\)，我们不强求算法及时分清距离边界不超过 \(\eta\) 的臂。对边界带外的臂，定义

\[
U_t(\eta)
=
\sum_{i\in A_t}
\mathbf 1\{i\in V_t,\ d_i^\varepsilon(t)>\eta\},
\]

\[
\boxed{
\mathcal A_T(\eta)=\sum_{t=1}^T U_t(\eta).
}
\]

\(U_t(\eta)\) 是本轮仍未判清的边界外臂数；\(\mathcal A_T(\eta)\) 是累计的“臂数×等待时间”。10 条边界外臂持续未决100轮，就贡献1000。

例如，边界为 \(0.40\)、\(\eta=0.005\) 时，均值为 \(0.39\) 的未决臂要计入，因为它距边界 \(0.01\)；均值为 \(0.401\) 的未决臂暂不计入，因为它距边界仅 \(0.001\)。但后一条臂仍然受到标签正确性约束，不能因为不计等待就随便把它报错。

**\(\eta\) 只放宽及时性，不放宽正确性。**而且，\(U_t(\eta)\) 和 \(\mathcal A_T(\eta)\) 用到了未知真均值，是理论评价指标，不是算法能直接计算的状态。fileciteturn34file0L14-L31

### 1.4 四个参数不要混淆

| 参数 | 含义 | 决定什么 |
|---|---|---|
| \(\varepsilon\) | 近优容忍度 | 真正要维护的是哪个集合 |
| \(\delta\) | 总错误概率上限 | 报告需要多可靠 |
| \(\eta\) | 及时性评价的边界带宽 | 哪些未决臂需要计入等待成本 |
| \(\rho\) | CP-UCB-AA 的服务精度 | 每条臂采到多少样本后形成检查点证据 |

累计 pseudo-regret 仍然是

\[
R_T=\sum_{t=1}^T\bigl(B_t-\mu_{I_t}\bigr).
\]

于是统一的联合要求是：对每个确定的评价终点 \(T\)，

\[
\boxed{
\mathbb E R_T\le r_T,
\qquad
\Pr\!\left(
E_{\mathrm{lab}}\cap
\{\mathcal A_T(\eta)\le a_T\}
\right)\ge1-\delta.
}
\tag{1}
\]

\(a_T\) 越小，要求报告越及时；\(r_T\) 越小，要求收益损失越小。本轮研究的是两者之间的限制和可达关系。这里的 regret 是期望保证，维护及时性是高概率保证，不能混用。fileciteturn34file0L26-L39

## 二、成果一：一个未知新臂会同时阻碍许多旧臂的正认证

### 2.1 先看它为什么是一个共同成本

假设有很多旧臂，我们已经很了解它们的均值。新臂 \(j\) 到达后，如果它可能远好于旧臂，那么当前阈值 \(B_t-\varepsilon\) 就可能大幅提高。

因此，旧臂是否仍然近优，取决于是否能排除“新臂 \(j\) 很好”这一可能性。**多条旧臂的报告，都被同一个新臂的不确定性阻碍。**这不是旧样本作废，而是旧样本尚不能单独回答新的比较问题。

### 2.2 核心定理 T2：共同认证负担下界

取

\[
0<\varepsilon\le\frac1{16},\qquad
0<\delta\le\frac1{16},\qquad
0<\eta<\frac\varepsilon2.
\]

初始参照臂的均值为

\[
b=\frac14+\frac\varepsilon2.
\]

其他候选按任意确定日程到达。考虑下面一组 Bernoulli 环境：

\[
\mu^0:\quad\text{所有候选均值都是 }p=\frac14;
\]

\[
\mu^j:\quad\text{只把第 }j\text{ 个候选均值改成 }p+2\varepsilon.
\]

在 \(\mu^0\) 中，全部候选都近优；在 \(\mu^j\) 中，\(j\) 到达后，其他候选全部非近优。所以，要给其他候选正认证，就必须积累足以排除 \(\mu^j\) 的信息。

记

\[
M_t=K_t-1,\qquad
m_t=\#\{\text{本轮到达的候选}\}.
\]

为了描述必要信息工作量，定义

\[
q_-=
\left\lfloor
\frac{\operatorname{kl}(1/4,\delta)}
{\operatorname{kl}(1/4,1/4+2\varepsilon)}
\right\rfloor,
\]

其中

\[
\operatorname{kl}(x,y)
=x\log\frac xy+(1-x)\log\frac{1-x}{1-y}.
\]

再定义一个**用于下界分析的队列**：

\[
Q_0=0,\qquad
Q_t=(Q_{t-1}+q_-m_t-1)_+,
\]

这里 \((x)_+=\max\{x,0\}\)。其含义是：每个新候选带来 \(q_-\) 个单位的分析工作量，每轮最多消化一个单位。

最后令

\[
\mathcal B_T
=
\sum_{t=1}^T
(M_t-1)_+\mathbf 1\{Q_t>0\}.
\]

它不是单纯累加欠多少样本，而是累加：**信息工作仍积压时，有多少其他候选会受到影响。**注意，这个 \(Q_t\) 不是后文算法的实际工作队列。

**定理 T2。** 对任何在 \(\mu^0\) 与全部 \(\mu^j\) 上都满足全过程 \(\delta\)-可靠性的同一策略，

\[
\boxed{
\mathbb E_0\mathcal A_T(\eta)
\ge\left(\frac34-\delta\right)\mathcal B_T.
}
\tag{2}
\]

当 \(\mathcal B_T>0\) 时，还有

\[
\boxed{
\Pr_0\!\left(
\mathcal A_T(\eta)\ge\frac{\mathcal B_T}{4}
\right)\ge\frac14.
}
\tag{3}
\]

其中 \(\mathbb E_0,\Pr_0\) 表示共同参考环境 \(\mu^0\) 下的期望和概率。即使把完整到达日程、终点和旧参照的真实分布告诉算法，结论仍成立。fileciteturn34file1L109-L141

### 2.3 这项结果具体证明了什么？

证明的关键是：若 \(Q_t>0\)，至少有一条候选 \(j\) 的期望采样数还不足。若此时算法却很有把握地给其他候选正认证，就会在备择 \(\mu^j\) 中造成过大的误报概率。因此，其他很多候选必须继续未决。整个时间轴上的下界都在同一个 \(\mu^0\) 中成立，不是把不同时间彼此不兼容的最坏环境相加。fileciteturn34file1L143-L163

向老师汇报时，这项结果的核心句是：

> **持续维护的成本具有跨臂影响：一个新臂的证据不足，可以同时阻碍许多旧臂的可靠正认证。**

它不意味着每次到达都必然使全部旧臂失去认证，而是证明存在这样的困难环境，而且这一现象不能靠换一个算法彻底消除。

## 三、成果二：最坏维护面积已经得到匹配阶数

### 3.1 这里的 minimax 到底在优化什么？

固定 \(T,K,\varepsilon,\eta,\delta\)。记 \(\nu\) 为各臂奖励分布组成的环境，\(\tau\) 为到达日程，定义

\[
\mathfrak A_{T,K}
=
\inf_{\pi\text{ 为全模型 }\delta\text{-可靠策略}}
\inf\left\{
a\ge0:
\sup_{\tau:K_T\le K}\sup_\nu
\Pr_{\nu,\tau}^{\pi}
\left(
E_{\mathrm{lab}}^c\cup
\{\mathcal A_T(\eta)>a\}
\right)
\le\delta
\right\}.
\]

用一句话解释：

> **在不知道均值的前提下，设计最好的可靠策略，使它对所有不超过 \(K\) 条臂的到达实验，都能承诺尽可能小的累计未决量。**

这里首先优化的是维护面积本身，并没有额外指定一个很小的 regret 预算。之后我们再检查达到上界的策略同时能获得什么 regret 保证。fileciteturn34file3L363-L393

### 3.2 核心定理 T8：最坏维护面积匹配

假设

\[
0<\varepsilon\le\frac18,\qquad
0<\eta\le\frac\varepsilon{32},\qquad
0<\delta\le\frac1{16},\qquad
K\ge2,
\]

其中 \(T,K\) 为整数，且 \(T\ge1\)。则存在通用常数 \(c,C>0\)，使

\[
\boxed{
c\min\left\{
KT,\frac{K^2}{\eta^2}\log\frac K\delta
\right\}
\le\mathfrak A_{T,K}
\le
C\min\left\{
KT,\frac{K^2}{\eta^2}\log\frac K\delta
\right\}.
}
\tag{4}
\]

也就是

\[
\mathfrak A_{T,K}
\asymp
\min\left\{
KT,\frac{K^2}{\eta^2}\log\frac K\delta
\right\}.
\]

这里 \(\asymp\) 表示相差通用乘法常数，不是精确常数相等。

达到右端阶数的同一个 CP-UCB-AA 策略，不需要知道 \(T\)、未来到达和最终臂数，而且有

\[
\boxed{
\mathbb E R_T
\le
\min\left\{
T,\;
K+4\sqrt{3KT\log(2T)}+1
+99K\eta^{-2}\log(K/\delta)
\right\}.
}
\tag{5}
\]

这是**维护面积的匹配结论，加上同一算法的 regret 上界**；不是两个指标都在所有参数区域同时达到各自最优。fileciteturn34file3L365-L399

### 3.3 为什么会有 \(K^2\)？

可以先看达到上界的机制。把每条臂采到 \(\eta\) 量级的精度，其检查点样本数约为

\[
q_i\asymp\eta^{-2}\log(i/\delta).
\]

所有臂的检查点采样工作合计约为

\[
K\eta^{-2}\log(K/\delta).
\]

这些工作尚未完成时，最多有 \(K\) 条臂在等待，所以累计面积的上界量级为

\[
\underbrace{K}_{\text{同时等待的臂数}}
\times
\underbrace{K\eta^{-2}\log(K/\delta)}_{\text{所需采样时间}}.
\]

定理的下界说明，在最坏情形中，这个量级不能普遍降低。需要注意：T8 的下界可以由第一轮的一次大批量到达达到；它不依赖复杂的多次更新。**T2 解释跨臂影响，T8 则闭合最坏面积，两者不是同一个结论的重复命名。**fileciteturn34file3L395-L415

### 3.4 一个容易汇报的增长率推论

在共同适用的参数范围 \(0<\varepsilon\le1/16,\ 0<\eta\le\varepsilon/32,\ 0<\delta\le1/16\) 内固定这些参数。对

\[
K_t\asymp t^\alpha,\qquad0<\alpha<1
\]

的日程族中，同一个策略能够对所有奖励环境同时保证

\[
\sup_\nu\mathbb E_\nu R_T=o(T)
\]

和式（1）中某个确定的 \(a_T=o(T)\)，当且仅当

\[
\boxed{\alpha<\frac12.}
\tag{6}
\]

充分性来自 \(K_T^2\log(eK_T)=o(T)\) 的联合上界；必要性来自共同认证负担下界。fileciteturn31file3L378-L390

这要求的是**时间平均未决臂个数趋零**，不是未决比例趋零。对一般无限日程，单独的 \(K_t=o(\sqrt t)\) 仍不充分，突发到达可能造成额外拥塞；现有记录已经给出了反例。fileciteturn34file1L180-L191 fileciteturn31file1L237-L268

## 四、成果三：快速维护与暂缓维护，可以具有不同阶的 regret 成本

### 4.1 先区分“收益差距”和“资格判别难度”

构造 \(J\) 次基准提高，每批有 \(M\) 条候选。第 \(e\) 个窗口中，参照臂 \(r_e\) 的均值是

\[
b_e=\frac12+ev,
\]

当前候选 \(c_{e,k}\) 的均值是

\[
\boxed{
\mu_{e,k}=b_e-\varepsilon+\sigma_{e,k}d,
\qquad\sigma_{e,k}\in\{-1,+1\}.
}
\tag{7}
\]

其中 \(v\) 是下一次基准提高的幅度，\(d\) 是候选距离近优边界的距离。

在当前窗口，

\[
\Delta_{e,k}=\varepsilon-\sigma_{e,k}d,
\qquad
d_{e,k}^{\varepsilon}=d.
\]

所以：候选距离最优臂约为 \(\varepsilon\)，每次采样损失约为 \(\varepsilon\)；但要知道它是否近优，必须区分边界两侧的 \(\pm d\)。

下一条参照到达后，基准变成 \(b_e+v\)，旧候选的 gap 变为

\[
\Delta_{e,k}^{\mathrm{new}}
=\varepsilon+v-\sigma_{e,k}d>\varepsilon.
\]

**只要 \(v>d\)，无论原来是哪一个符号，这批候选现在都非近优。**因此，原来“到底是 \(+d\) 还是 \(-d\)”的精细问题，已经不再是当前集合必须回答的问题。fileciteturn32file2L108-L133

### 4.2 定理使用的实例族和窗口长度

取整数 \(J,M\)，核心定理采用以下明确条件：

\[
J\ge1,\quad M\ge\max\{2,J\},\quad
0<\varepsilon\le\frac18,\quad0<\delta\le\frac1{16},
\]

\[
0<v,\qquad Jv\le\frac\varepsilon4,
\qquad0<d\le\frac v{32},\qquad\eta=\frac d2.
\]

第 \(e\) 批于 \(1+eH\) 到达。对 \(e=0,\ldots,J-1\)，该批包含一条参照和 \(M\) 条式（7）的候选；最后第 \(J\) 批只加入参照 \(r_J\)。所有奖励为 Bernoulli。

算法**不知道哪条臂是参照**；实例族允许批内任意标签排列。由于 \(Jv\le\varepsilon/4\)，所有参照最终仍近优，而全部候选最终都非近优，因此

\[
G_T^\varepsilon=\{r_0,r_1,\ldots,r_J\},
\]

与所有隐藏符号无关。这里不是只留下最后一条参照。fileciteturn32file2L108-L133

为给出闭合的两端权衡，定义

\[
K=J(M+1)+1,\qquad
L_K=\log\frac{4K(K+1)}\delta,
\]

\[
q_f=\left\lceil\frac{32L_K}{d^2}\right\rceil,
\qquad
q_c=\left\lceil\frac{128L_K}{v^2}\right\rceil,
\]

\[
H=128(M+J+1)q_f,\qquad
T=(J+1)H,\qquad
V=JMH.
\tag{8}
\]

其中，\(q_f,q_c\) 分别是精细和粗配置下实际逐臂检查点配额的共同上界；算法真正使用的是后文式（13）的 \(q_i\)。

这里 \(V\) 是标量，表示全部当前候选在各自窗口中一直未决时的面积，**不要与未决集合 \(V_t\) 混淆**。这些 \(K,H,T,q_f,q_c\) 用来定义和分析实例族，不是算法运行时接收的未来信息。fileciteturn34file2L277-L290

### 4.3 核心定理 T6：同一任务下的两端权衡

对上述实例族 \(\Theta\)，定义

\[
\mathfrak R_\Theta(a)
=
\inf_{\pi\in\Pi_\delta(a,\Theta)}
\sup_{\theta\in\Theta}\mathbb E_\theta^\pi R_T.
\]

\(\Pi_\delta(a,\Theta)\) 中的策略必须在全部基础模型环境上标签可靠，并在每个 \(\theta\in\Theta\) 上满足

\[
\Pr_\theta^\pi\!\left(E_{\mathrm{lab}}\cap
\{\mathcal A_T(\eta)\le a\}\right)\ge1-\delta.
\]

这个值表示：**维护面积最多允许为 \(a\) 时，最好的策略仍须支付的最坏 regret。**fileciteturn34file0L33-L39

**定理 T6。** 存在通用常数 \(c,C>0\)，使快速维护预算 \(a=V/8\) 下

\[
\boxed{
c\frac{\varepsilon JM}{d^2}\log\frac M\delta
\le
\mathfrak R_\Theta(V/8)
\le
C\frac{\varepsilon JM}{d^2}\log\frac M\delta.
}
\tag{9}
\]

另一方面，存在粗精度 CP-UCB-AA，在同样的 \(\varepsilon,\eta,\delta\)、同样日程和终点下满足

\[
\Pr\!\left(
E_{\mathrm{lab}}\cap
\{\mathcal A_T(\eta)\le9V/8\}
\right)\ge1-\delta,
\]

并且

\[
\boxed{
\sup_{\theta\in\Theta}\mathbb E_\theta R_T
\le
2\varepsilon JM q_c
+
64\left(\frac{JM}{\varepsilon}+\frac{J^2}{v}\right)
\log(2T)+1.
}
\tag{10}
\]

固定合法的 \(J,M,\varepsilon,v,\delta\)，令 \(d\downarrow0\)，并按式（8）同步选择终点，得到

\[
\boxed{
\mathfrak R_\Theta(V/8)=\Theta(d^{-2}),
\qquad
\mathfrak R_\Theta(9V/8)=O(\log(1/d)).
}
\tag{11}
\]

快速端上下界匹配；暂缓端目前只有可达上界，没有匹配下界。fileciteturn34file2L292-L315

### 4.4 为什么暂缓能够省掉精细成本？

快速策略采用 \(\rho_f=d/4\)，在当前窗口内把候选的资格判清。粗策略采用 \(\rho_c=v/8\)，先得到足够粗的区间，允许候选暂时未决。

在区间覆盖事件上，上一批候选的旧上界满足

\[
u_{e,k}\le b_e-\varepsilon+d+\rho_c,
\]

下一参照形成的下界满足

\[
\ell_{r_{e+1}}\ge b_e+v-\rho_c.
\]

因为

\[
d+2\rho_c<v,
\]

所以

\[
\boxed{
u_{e,k}<\ell_{r_{e+1}}-\varepsilon.
}
\tag{12}
\]

这就足以把上一批所有候选认证为非近优，**无需为了这个报告再采它们**。已经获得的旧样本没有浪费；未执行的更细采样也不再需要。收益层以后是否还采这些臂，是另一个问题。fileciteturn34file2L262-L273

定理的准确意义是：**允许的累计等待预算扩大9倍，在这个明确实例族中可以换来不同阶的 regret 成本。**它不是说每条臂的报告延迟只扩大9倍，也不是说任意环境都应该等待下一次改善。

还有两点必须保留：\(d\to0\) 时，\(\eta=d/2\) 也在变小，\(T=\Theta(d^{-2})\) 同步增大；快速端的匹配只对规定的窗口族成立。因此不能把式（11）解释成固定终点、固定精度下的普遍结论，更不能称为完整 Pareto 前沿。fileciteturn34file2L309-L351

## 五、CP-UCB-AA：先看状态，再看完整伪代码

### 5.1 每条臂到底保存什么？

先讲使用同一个固定精度 \(\rho\in(0,1)\) 的版本。算法输入为 \(\varepsilon,\delta,\rho\)，按到达顺序把臂编号为 \(1,2,\ldots\)。

每条臂 \(i\) 保存：

| 状态 | 含义 |
|---|---|
| \(n_i\) | 到目前为止的总采样次数 |
| \(S_i\) | 全部已观察奖励之和 |
| \(q_i\) | 事先固定的检查点样本数 |
| \([\ell_i,u_i]\) | 专门用于报告的区间 |

检查点定义为

\[
\boxed{
q_i=
\left\lceil
\frac{2}{\rho^2}
\log\frac{4i(i+1)}\delta
\right\rceil.
}
\tag{13}
\]

它不使用未知均值、未来到达或终点。**这是累计总样本目标，不是“额外再采 \(q_i\) 次”。**UCB 轮采到的样本也会完成这份配额。fileciteturn34file0L69-L87 fileciteturn34file2L211-L215

### 5.2 收益指数与报告区间，是两套不同的量

收益选择用当前全部数据计算

\[
\operatorname{UCB}_i(t)=
\begin{cases}
+\infty,&n_i=0,\\[2mm]
\displaystyle\frac{S_i}{n_i}
+\sqrt{\frac{3\log(2t)}{n_i}},&n_i\ge1.
\end{cases}
\tag{14}
\]

报告区间则是

\[
[\ell_i,u_i]=
\begin{cases}
[0,1],&n_i<q_i,\\[1mm]
\displaystyle
[\widehat\mu_{i,q_i}-\rho/2,
\widehat\mu_{i,q_i}+\rho/2]\cap[0,1],&n_i\ge q_i.
\end{cases}
\tag{15}
\]

其中 \(\widehat\mu_{i,q_i}\) 是该臂前 \(q_i\) 次实际观测的平均值，包含认证轮与收益轮获得的样本。

**关键区别：到达第 \(q_i\) 个样本时，报告区间只生成一次，之后冻结；收益指数仍然随新样本和物理时间更新。**例如，\(n_i\) 从 \(q_i\) 增加到 \(q_i+100\)，收益指数使用这全部样本，但报告区间仍使用第 \(q_i\) 个样本时保存的那一份。现有代码就是这样实现的。fileciteturn34file4L492-L520

固定检查点的一个作用，是让共同覆盖概率直接得到控制：

\[
\Pr\!\left(
\exists i:\left|\widehat\mu_{i,q_i}-\mu_i\right|>\rho/2
\right)
\le
\sum_{i=1}^\infty
\frac{\delta}{2i(i+1)}
=\frac\delta2.
\]

这为后续反复使用同一份证据提供可靠性基础。**不能事后随意挑选最有利的检查点，再继续沿用这个概率保证。**fileciteturn34file0L71-L87

### 5.3 由区间怎样生成三类报告？

每轮观测后，计算

\[
\underline B_t=\max_{j\in A_t}\ell_j,
\qquad
\overline B_t=\max_{j\in A_t}u_j.
\]

在共同覆盖事件上，

\[
\underline B_t\le B_t\le\overline B_t.
\]

报告规则为

\[
\boxed{
C_t=\{i\in A_t:\ell_i\ge\overline B_t-\varepsilon\},
}
\tag{16}
\]

\[
\boxed{
D_t=\{i\in A_t:u_i<\underline B_t-\varepsilon\},
\qquad
V_t=A_t\setminus(C_t\cup D_t).
}
\tag{17}
\]

正认证需要“自己的保守下界仍足够好”；负认证只需要“自己的乐观上界也落后于某条臂的保守下界”。这里取最大值的范围是**所有已到达臂**。fileciteturn34file0L89-L95

### 5.4 完整伪代码

下面展开的是现有 `cp_ucb_aa.py` 的运行逻辑。`Queue` 是实际的 FIFO 工作队列，与定理 T2 的分析队列 \(Q_t\) 不同；平局一律选择编号最小的臂。fileciteturn34file4L477-L532

```text
算法：CP-UCB-AA（固定精度版本）

输入：
    ε ∈ (0, 1)       近优容忍度
    δ ∈ (0, 1/2)     总错误概率参数
    ρ ∈ (0, 1)       事先固定的服务精度

初始化：
    A ← 空集合                  # 所有已到达臂
    Queue ← 空 FIFO 队列         # 尚待完成检查点工作的臂
    k ← 0                       # 已分配的臂编号数

对物理时刻 t = 1, 2, ... 重复：

    1. 接纳本轮全部新臂
       按固定批内顺序，对每条新臂执行：
           k ← k + 1
           i ← k
           A ← A ∪ {i}
           n[i] ← 0
           S[i] ← 0
           q[i] ← ceil((2 / ρ²) * log(4 * i * (i + 1) / δ))
           lower[i] ← 0
           upper[i] ← 1
           将 i 加入 Queue 尾部
       # 基础模型保证本轮 A 非空

    2. 清理队首已经完成检查点的臂
       当 Queue 非空，且 n[Queue.front] ≥ q[Queue.front]：
           弹出 Queue 队首
       # 完成可能来自此前的认证采样，也可能来自 UCB 采样

    3. 决定本轮采哪条臂
       如果 t 为偶数，并且 Queue 非空：
           I ← Queue.front      # 认证服务：先来先服务
       否则：
           对每条 i ∈ A：
               如果 n[i] = 0：
                   index[i] ← +∞
               否则：
                   index[i] ← S[i] / n[i]
                               + sqrt(3 * log(2 * t) / n[i])
           I ← index 最大的臂；平局取最小编号
       # UCB 比较范围始终是 A，不是 C，也不是 A \ D

    4. 只拉取 I 一次，观察奖励 x ∈ [0, 1]
       n[I] ← n[I] + 1
       S[I] ← S[I] + x

    5. 如果刚好达到检查点，则保存报告区间
       如果 n[I] = q[I]：
           checkpoint_mean ← S[I] / q[I]
           lower[I] ← max(0, checkpoint_mean - ρ / 2)
           upper[I] ← min(1, checkpoint_mean + ρ / 2)
       # n[I] < q[I] 时继续使用 [0, 1]
       # n[I] > q[I] 时不再更新报告区间
       # 但步骤 4 的总计数和奖励和始终更新

    6. 用保存的区间重新计算本轮报告
       L ← max{lower[i] : i ∈ A}
       U ← max{upper[i] : i ∈ A}

       C ← {i ∈ A : lower[i] ≥ U - ε}
       D ← {i ∈ A : upper[i] < L - ε}
       V ← A \ (C ∪ D)

       输出本轮选择 I 和报告 (C, D, V)

    7. 进入下一轮
       不因新到达、报告变化或队列出队而重置历史统计量
       不把 D 中的臂从 A 中删除
```

### 5.5 最容易误解的四个运行细节

**第一，偶数轮不是额外增加一次采样。**每个物理时刻总共只拉一条臂。有认证欠账时，偶数轮用于认证；奇数轮用于 UCB。认证队列为空时，偶数轮也改做 UCB。

**第二，FIFO 不是轮流给每条臂采一下。**偶数服务轮优先处理当前队首，直到它累计达到 \(q_i\)；但奇数轮的 UCB 可以选择任何臂，提前完成后面某条臂的配额。后面的臂即使暂未从队列物理弹出，达到检查点的当轮也会生成报告区间。

**第三，完成检查点不等于完成分类。**一条臂达到 \(q_i\) 后，只是形成了固定精度证据；它仍可能在 \(V_t\)，因为自己的证据不够细，或者其他竞争者还没估清。

**第四，报告为非近优不等于永久停止拉取。**它仍留在 \(A_t\)，可以由 UCB 再次选择。报告层不能因为一次低概率误判，就让收益层永久丢失真正最优臂。上述四点都对应现有代码，而不是在文字之外另外添加的机制。fileciteturn34file4L492-L532

### 5.6 一个区间更新例子：旧臂不用再采，标签也能改变

取 \(\varepsilon=0.10\)、\(\rho=0.004\)。下面只演示报告公式，假设已经保存了以下检查点区间，不是一次仿真的结果：

\[
[\ell_1,u_1]=[0.498,0.502],
\qquad
[\ell_2,u_2]=[0.398,0.402].
\]

此时

\[
\underline B=0.498,\qquad\overline B=0.502.
\]

臂1被正认证，因为 \(0.498\ge0.502-0.10\)。臂2既不满足正认证，也不满足负认证，所以

\[
C=\{1\},\qquad D=\varnothing,\qquad V=\{2\}.
\]

现在臂3到达，在尚未完成检查点时，其报告区间为 \([0,1]\)。于是 \(\overline B\) 变成1，臂1也不能再满足正认证，三个臂都暂时未决。**臂1的旧区间没变，改变的是当前比较对象的最大上界。**

后来臂3完成检查点，保存区间

\[
[\ell_3,u_3]=[0.518,0.522].
\]

现在

\[
\underline B=0.518,\qquad\overline B=0.522.
\]

臂2满足

\[
0.402<0.518-0.10=0.418,
\]

因此进入 \(D\)；臂1和臂3都满足正认证，于是

\[
\boxed{C=\{1,3\},\qquad D=\{2\},\qquad V=\varnothing.}
\]

**在这个更新中，臂2完全可以没有获得任何新增观测。它的旧区间配合臂3的新证据，就足以得出新的资格结论。**这正是式（12）在数值上的解释。

### 5.7 如何选择 \(\rho\)？这些保证不是同一个配置自动全部获得

| 目标 | 研究记录中的服务配置 | 对应结果 |
|---|---|---|
| 任意到达下，控制 \(\eta\) 边界外的最坏维护面积 | \(\rho=\eta/4\) | T8 |
| 多次更新实例族中的快速维护 | \(\rho_f=d/4=\eta/2\) | T6 的快速端 |
| 同一实例族中允许暂缓，以粗证据跨更新退休旧候选 | \(\rho_c=v/8\) | T6 的暂缓端 |

粗策略的配置与实例族的更新尺度 \(v\) 有关。它是一个**事先给定、满足定理条件的服务配置**，不是算法已经能够从数据中自动估计未知 \(v\)，再免费调到最优精度。特别是，粗配置不承诺在任意环境中及时判清所有 \(\eta\) 边界外臂。fileciteturn34file3L395-L399 fileciteturn34file2L282-L290

## 六、它与原 UCB-AA 的关系，汇报时应当怎样说？

原 UCB-AA 的主要结构是：**新臂预筛选，再与旧臂合并正式淘汰；精度随轮数逐渐细化。**CP-UCB-AA 则是：**为每条臂安排固定检查点认证，和全历史 UCB 收益选择交错运行，再持续更新近优报告。**因此，它是后续研究中的新构造，不是原 Algorithm 1 不变后的附加性质。fileciteturn33file5L391-L490 fileciteturn34file2L203-L217

还有一个需要说准确的地方：**当前固定精度 CP-UCB-AA 并没有复杂的“发现新参照后，自动取消所有旧配额”模块。**在暂缓策略中，它先完成所配置的粗检查点；新参照出现后，使原本未启动的、更细的识别需求不再必要。因此，“任务取消”在本轮主构造中的含义，是避免补做不再需要的精细任务，而不是声称所有动态任务调度都已解决。fileciteturn34file2L262-L273

向老师汇报时，可以把目前的主张压成下面一段：

> 我们现在把原稿的筛选功能明确成一个持续统计任务：在控制 regret 的同时，可靠且及时地维护全部相对近优臂。理论上，一是证明新臂的不确定性会对多个旧臂产生共同认证负担；二是得到最坏累计未决面积的匹配阶数和相应增长率限制；三是在明确的多次更新族中，证明快速精细维护与允许跨更新暂缓，具有不同阶的 regret 成本。为实现上界，我们构造了检查点认证与全历史 UCB 分开的算法。当前贡献主要在成本刻画与联合权衡，而不是已经证明这个算法在所有环境或所有强基线上都更优。

**完成度的边界也很清楚：最坏维护面积已匹配，规定实例族上的快速端 regret 已匹配；任意重叠到达、异质边界距离和全部服务预算下的完整最优权衡，仍未闭合。**最终强一致性另有多精度复核版本，不能把它的性质自动归给这里的固定精度伪代码。fileciteturn30file1L140-L166 fileciteturn32file0L11-L43
