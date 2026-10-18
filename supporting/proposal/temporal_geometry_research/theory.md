# The Temporal Geometry of Bandits with Arriving Arms
## 精确多尺度 minimax、保留历史的未知终点算法，以及学习边界

**研究日期：2026-10-12。版本：理论整合稿 v1.0。**

**主任务状态：完整证明稿。** 本文给出最新选定主线的全部核心证明：单调到达结构 → 多尺度谱 → 匹配上下界 → 同一未知终点策略 → 学习边界与代表实例。这里的“完整”指下述模型与量词中的证明义务已逐项展开，不表示通过了独立同行审查或形式化证明器验证，也不表示一般 sleeping、任意实例最优性和任意置信水平的最优尾界均已解决。

本文依据上一轮《MAB-AA 的发散重构：从算法适配到到达时间的多尺度统计复杂度》第 4–8 节继续推进。原 PDF 的收益模型保留；不再附加集合认证、内存限制或内生候选生成任务。原文件没有被覆盖。

---

## 0. 本轮复核与新增结果

上轮的谱 minimax 主证明，经本轮重新逐项推导，没有发现需要撤回其主要结论的缺口。真正的新推进不是重复给定理编号，而是以下几项。

| 模块 | 本轮结果 | 与上轮的关系 |
|---|---|---|
| 逐日程 minimax | \(\mathfrak R_T\asymp\mathscr S_T\)，绝对常数匹配 | 复核并重写完整证明 |
| 未知终点实现 | **只重置探索时钟，不清空任何历史统计量**的 MC-MOSS 同样谱最优 | 新增；算法比上轮的冷重启版本更简单、数据利用更充分 |
| 无网格表述 | \(\mathscr C_T=\max_{n\in\mathcal N_T}\sum_i\min\{n_i,\sqrt{n_i}\}\)，且 \(\mathscr S_T/4\le\mathscr C_T\le\mathscr S_T\) | 新增；将谱解释为受到达约束的统计采样容量 |
| 可计算性 | \(\mathscr C_T\) 的精确对偶、凸次包络构造与最优性证书 | 新增；不需要知道均值或求解 bandit 动态规划 |
| 固定点缺失了什么 | \(\Gamma_T\asymp\|s_T\|_2\)，而 \(\mathfrak R_T\asymp\|s_T\|_1\) | 新增；把上轮分离提升为一般等价关系 |
| 有效尺度数 | \(D_T^{\rm eff}=\|s_T\|_1^2/\|s_T\|_2^2\)，故 \(\mathfrak R_T\asymp\Gamma_T\sqrt{D_T^{\rm eff}}\) | 新增；精确解释尺度累积，不只是给一个反例 |
| 下界的概率强度 | 存在 Bernoulli 环境，使 \(\Pr(R_T\ge\mathscr S_T/20000)\ge1/8\) | 新增；困难不只由极小概率的巨大损失造成 |
| 历史复用的实际作用 | 同一采样指数、同一重启时刻，仅是否清空数据不同，可产生 \(\Omega((\log T)^2)\) 对 \(O(\log T)\) 的确定性实例分离 | 新增；不是普遍支配结论 |
| 随机奖励 gap 上界 | 同一 MC-MOSS 具有全模型谱保证与显式 gap-sensitive 上界 | 新增；不宣称实例最优 |
| 到达扰动 | \(\mathscr C_T\) 对最大到达抖动是 1-Lipschitz；巨大晚批次的增量由共同剩余时间控制 | 新增 |
| 学习边界、典型增长 | \(K_t=o(t)\) 的精确 uniform 边界，由同一保留历史策略实现 | 既有边界的整合与强化实现 |

**不计作新研究发现的工具：** Hoeffding 型集中、指数超鞅、Ville 不等式、bandit KL 恒等式、Pinsker、几何级数和普通 MOSS 思想。本文将所需版本写明或证明，避免把这些依赖留成隐含缺口。文献定位见第 15 节。

---

## 1. 模型、风险和量词

固定一条确定、外生的无限到达路径。臂集可数，臂 \(i\) 在整数时刻 \(\tau_i\ge1\) 到达，此后永久可用：

\[
\varnothing\ne A_t=\{i:\tau_i\le t\},\qquad K_t=|A_t|<\infty.
\]

各臂有相互独立的潜在奖励流 \((X_{i,n})_{n\ge1}\)，每条流 i.i.d.、取值于 \([0,1]\)，均值为固定的 \(\mu_i\)。第 \(n\) 次拉臂 \(i\) 时观察 \(X_{i,n}\)。每步先观察当前可用集合，再基于过去奖励和独立随机种子选择 \(I_t\in A_t\)，只观察该次奖励。

允许任意有限 batch、\(K_T\gg T\)、并列最优、任意 benchmark jump；不要求到达率或 gap 演化规律。定义

\[
B_t=\max_{i\in A_t}\mu_i,\qquad
\Delta_i(t)=B_t-\mu_i,\qquad
R_T=\sum_{t=1}^T\Delta_{I_t}(t).
\tag{1.1}
\]

\(R_T\) 是随机 pseudo-regret，\(0\le R_T\le T\)。\(B_t\) 与每条旧臂的 \(\Delta_i(t)\) 非减，但各臂的奖励分布没有漂移。

定义逐到达路径的 minimax 风险

\[
\mathfrak R_T(\tau)=\inf_{\pi\in\Pi_{T,\tau}}\sup_P\mathbb E_P^\pi R_T.
\tag{1.2}
\]

这里 \(P\) 遍历全部上述奖励分布；下确界里的策略允许预先知道 \(T\) 和完整到达日程，但不知道均值。我们构造的上界策略不使用这些未来信息，并对每条无限路径的每个确定终点使用同一规则。

### 1.1 假设与范围台账

| 项目 | 状态 | 在证明中的作用 |
|---|---|---|
| 平稳、独立、\([0,1]\) 奖励流 | 原模型 | 潜在样本前缀集中及 KL 分解 |
| 到达外生且每步可用集有限非空 | 原模型 | 段起点、真实最佳臂标签在固定环境下确定；动作可定义 |
| 允许 batch、ties、未知 \(T,K_T\) | 必须保留 | 不能靠完整初始化、已知最后到达等假设绕过 |
| gap/jump 正则性 | 不使用 | 所有主定理为全分布、全到达路径结论 |
| 实例最优／所有未来时刻的尖锐高概率界 | 未包含在主定理 | 分别需要更强结果，不能由期望定理自动升级 |
| 独立随机到达 | 第 14 节的条件化推论 | 不交换 \(\sup_P\) 与对到达的期望 |

### 1.2 伯努利化

**命题 1（minimax 的 Bernoulli 化）。** 固定日程后，在允许随机化策略的条件下，全部 bounded 奖励的 minimax 值等于 Bernoulli 子模型的 minimax 值。

**证明。** Bernoulli 是子类，给出一个方向。反之，面对任意 \([0,1]\) 观测 \(X\)，算法独立抽取 \(U\sim\mathrm{Unif}[0,1]\)，令 \(Y=\mathbf1\{U\le X\}\)。于是每条臂被提供给 Bernoulli 策略的潜在流是 i.i.d. \(\mathrm{Ber}(\mu_i)\)，跨臂独立；采样动作的期望收益仍由同一 \(\mu_i\) 决定。将任意近似最优的 Bernoulli 策略用此方式运行，再取下确界，得到另一方向。证毕。

这只是 minimax 的模型化简，不表示一般分布的实例最优信息量只由其均值决定。

---

## 2. 多尺度谱与主定理

任选 \(a\in A_1\) 为 anchor，仅用于记账；不假设其均值已知或最优。固定终点 \(T\)，令

\[
H_i=T-\tau_i+1,\quad L=\lceil\log_2T\rceil,\quad b_\ell=2^\ell.
\]

对非 anchor 臂定义

\[
G_0=\{i\ne a:H_i=1\},\qquad
G_\ell=\{i\ne a:2^{\ell-1}<H_i\le2^\ell\},\ 1\le\ell\le L,
\qquad k_\ell=|G_\ell|.
\]

记

\[
s_{\ell,T}=\min\{b_\ell,\sqrt{k_\ell b_\ell}\},\qquad
\mathscr S_T=\sum_{\ell=0}^L s_{\ell,T}.
\tag{2.1}
\]

所有可选 anchor 的寿命均为 \(T\)，故 \(\mathscr S_T\) 与其身份无关。空组贡献零；\(K_T=1\) 时 \(\mathscr S_T=0\)。谱仅用于事后评价，算法不计算未来寿命。

**定理 1（精确谱 minimax 与保留历史的 anytime 可达性）。** 存在同一完全因果策略 \(\pi^{\rm MC}\)，对每条允许的到达路径与每个确定 \(T\)，

\[
\boxed{
\frac{\mathscr S_T}{10000}
\le\mathfrak R_T(\tau)
\le\sup_P\mathbb E_P R_T(\pi^{\rm MC})
\le\min\{T,300\mathscr S_T\}.
}
\tag{2.2}
\]

\(\pi^{\rm MC}\) 不知终点、未来到达、最终臂数或均值，且保留从第一轮开始的全部样本计数和累计奖励。常数均未优化。上界证明在第 3–5 节，下界在第 6 节。

**量词提醒：** 此处是同一策略逐个确定终点的期望保证。不能据此直接声称 \(\mathbb E R_\zeta\le300\mathbb E\mathscr S_\zeta\) 对任意奖励依赖停时 \(\zeta\) 成立，也不能省略证明升级为时间一致高概率结论。

---

## 3. 集中与非重复计数工具

### 3.1 指数超鞅与两个最大不等式

若 \(X\in[0,1]\)、\(\mathbb EX=\mu\)，则

\[
\mathbb E\exp\{\lambda(\mu-X)\}\le e^{\lambda^2/8}.
\tag{3.1}
\]

一个直接证明是：对数矩母函数在零点的函数值和一阶导均为零，其二阶导为指数倾斜分布下的方差，不超过 \(1/4\)；积分两次即可。

对 \(S_n=\sum_{r=1}^n(\mu-X_r)\)，过程
\(M_n(\lambda)=\exp\{\lambda S_n-n\lambda^2/8\}\) 为非负超鞅。将首次超过阈值的时刻截断到确定 \(N\)，用超鞅期望不增，再让 \(N\to\infty\)，得到
\(\Pr(\sup_nM_n\ge c)\le1/c\)。因此，对 \(x>0,v>0\)，

\[
\Pr\{\exists n>v:S_n/n\ge x\}\le e^{-2vx^2},
\tag{3.2}
\]

其中取 \(\lambda=4x\)。对确定整数 \(N\ge1\) 与 \(y>0\)，取 \(\lambda=4y/N\) 同样得到

\[
\Pr\{\max_{n\le N}S_n\ge y\}\le e^{-2y^2/N}.
\tag{3.3}
\]

同理，对单个前缀经验均值，\(\Pr(\widehat\mu_n-\mu\ge x)\le e^{-2nx^2}\)。这些是标准工具的所需版本；不作为新的 bandit 贡献。

### 3.2 MOSS 最大低估量

**引理 1。** 对 \(v>0\)，定义

\[
Z(v)=\sup_{n\ge1}\left[
\mu-\widehat\mu_n-
\sqrt{\frac{[\log(v/n)]_+}{n}}
\right]_+.
\tag{3.4}
\]

则

\[
\mathbb EZ(v)\le\frac5{\sqrt v},\qquad
\Pr\{Z(v)>x\}\le\min\left\{1,\frac5{vx^2}\right\},\quad x>0,
\tag{3.5}
\]

以及

\[
\mathbb E[Z(v)\mathbf1\{Z(v)\ge z\}]\le\frac{10}{vz},\quad z>0.
\tag{3.6}
\]

**证明。** 对 \(n>v\) 使用 (3.2)。对 \(n\le v\)，令 \(m_k=v2^{-(k+1)}\)，分成 \(m_k<n\le2m_k\)，\(k\ge0\)。若相应前缀使 (3.4) 超过 \(x\)，则

\[
S_n>m_kx+\sqrt{m_k k\log2}.
\]

对非空整数区间，以 \(N=\lfloor2m_k\rfloor\) 使用 (3.3)，得该区间概率至多
\(2^{-k}\exp\{-vx^2/2^{k+1}\}\)。所以

\[
\Pr\{Z(v)>x\}
\le e^{-2vx^2}+\sum_{k\ge0}2^{-k}e^{-vx^2/2^{k+1}}.
\tag{3.7}
\]

尾积分给出

\[
\mathbb EZ(v)
\le\frac{\sqrt\pi}{2\sqrt{2v}}+
\frac{\sqrt\pi}{\sqrt{2v}}\sum_{k\ge0}2^{-k/2}
<\frac5{\sqrt v}.
\]

再令 \(u_k=vx^2/2^{k+1}\)。由于
\(u_ke^{-u_k}\le2\int_{u_k/2}^{u_k}e^{-u}\,du\)，且这些积分区间不交，(3.7) 中的级数至多 \(4/(vx^2)\)；第一项至多 \(1/(vx^2)\)。这证明概率界。最后，

\[
\mathbb E[Z\mathbf1\{Z\ge z\}]
=z\Pr(Z\ge z)+\int_z^\infty\Pr(Z>x)\,dx
\le\frac{10}{vz}.
\]

概率界的非严格版本由极限得到。上确界是可数的；级数与积分均为非负，交换使用 Tonelli。证毕。

### 3.3 自适应样本数不能被当作独立样本数

**引理 2（非重复计数的总高估界）。** 固定有限的 \(k\) 条臂。在不超过 \(h\) 次动作中，每次选中的“臂标签、选前总样本数 \(n\ge1\)”组合至多出现一次；样本数可以来自任意自适应历史。则

\[
\mathbb E\sum_{\text{这些动作}}
(\widehat\mu_{I,n}-\mu_I)_+
\le\sqrt{2kh}.
\tag{3.8}
\]

**证明。** 任取 \(\vartheta>0\)，路径上

\[
\sum (\widehat\mu_{I,n}-\mu_I)_+
\le\vartheta h+
\sum_{i=1}^k\sum_{n\ge1}
(\widehat\mu_{i,n}-\mu_i-\vartheta)_+.
\]

固定臂的后项期望至多

\[
\sum_{n\ge1}\int_\vartheta^\infty e^{-2nx^2}dx
=\int_\vartheta^\infty\frac{dx}{e^{2x^2}-1}
\le\frac1{2\vartheta}.
\]

取 \(\vartheta=\sqrt{k/(2h)}\) 即得。零动作时直接取零。这里没有将随机 \(n\) 与经验均值解耦。证毕。

**引理 3（bonus 求和）。** 对 \(a>0\)，

\[
\sum_{n\ge1}\sqrt{\frac{[\log(a/n)]_+}{n}}
\le\sqrt{2\pi a}.
\tag{3.9}
\]

**证明。** 函数 \(x\mapsto\sqrt{\log(a/x)/x}\) 在 \((0,a)\) 递减，故和式被从零开始的积分控制。以 \(x=ae^{-u}\) 代换，积分等于
\(\sqrt a\int_0^\infty\sqrt u e^{-u/2}du=\sqrt{2\pi a}\)。\(a<1\) 时左侧为零也成立。证毕。

---

## 4. MC-MOSS：只重置时钟，保留全部历史

### 4.1 完全指定的算法

每条臂维护终身样本数 \(N_i\) 和累计奖励 \(S_i\)，\(\widehat\mu_i=S_i/N_i\)。这些量**永不因到达或时钟重置而清空**。初始 `base=0`。

每轮先接纳新臂。若 \(K_t=1\)，拉唯一臂并更新其终身统计量。否则，当 `base=0` 或 \(K_t-1\ge2\,\mathrm{base}\) 时，令

\[
\mathrm{base}=K_t-1,\qquad \sigma=t,\qquad d=2\,\mathrm{base}.
\tag{4.1}
\]

其他轮保持 \(\sigma,d\) 不变。令局部探索时钟 \(s=t-\sigma+1\)，使用

\[
U_i(t)=
\begin{cases}
+\infty,&N_i(t-1)=0,\\[2mm]
\widehat\mu_i(N_i(t-1))+
\sqrt{\dfrac{[\log(s/(dN_i(t-1)))]_+}{N_i(t-1)}},&N_i(t-1)\ge1.
\end{cases}
\tag{4.2}
\]

选择最大指数；平局按固定到达次序、批内固定标签顺序打破。每次时钟重置前先接纳本轮整个 batch，故若 batch 触发阈值，它属于新段。

```text
base := 0
maintain lifetime counts N_i and lifetime reward sums S_i
for t = 1, 2, ...:
    receive the whole new batch; initialize its counts and sums to zero
    if K_t == 1:
        pull the unique arm and update its lifetime statistics
        continue
    if base == 0 or K_t - 1 >= 2 * base:
        base := K_t - 1
        sigma := t
        d := 2 * base
        # DO NOT reset any N_i or S_i
    s := t - sigma + 1
    if an available arm has N_i == 0:
        choose the first such arm in the fixed tie-breaking order
    else:
        choose argmax_i [ S_i/N_i + sqrt(log_+(s/(d*N_i))/N_i) ]
    pull the chosen arm and update its lifetime statistics
```

这里的 \(d\) 是本段有效的臂数上限，不是对最终 \(K_T\) 的预测。段内总臂数始终不超过 \(d\)，因为达到下一阈值即在该次选臂前开启新段。算法既没有延迟接纳，也没有删除臂。

MOSS 指数和 anytime optimism 有直接前作 [W2,W3]；本文贡献不在于重新命名这条指数。与上轮相比，本算法也不再需要按臂序号设置不同 bonus，固定本段容量 \(d\) 已经足够。

### 4.2 有历史的局部内核界

**引理 4（无须清空历史的内核界）。** 固定一个确定起点的运行段及其确定长度 \(h\) 前缀。段内允许持续到达，截至该前缀共有 \(k\le d\) 条臂可用。以 (4.2) 选臂，均值和计数使用同一实验从第一轮起的所有样本，则

\[
\mathbb E R_{\rm segment}\le\min\{h,15\sqrt{dh}\}.
\tag{4.3}
\]

该结论为**原实验下的无条件期望界**；不声称给定任意历史后的旧样本仍是独立或无偏的。

**证明。** \(d>h\) 时使用平凡界。以下 \(d\le h\)。本段真正首次被观察的臂至多 \(k\le d\)，其总 regret 至多 \(d\le\sqrt{dh}\)。其他时刻，若当前最佳臂仍零样本，则算法必选择零样本臂，因此已经在首次拉取部分计费。

固定到达路径与真实均值后，选一条确定的最佳可用臂 \(i_s^*\)。其标签不依赖已观察的奖励。用**全历史潜在样本前缀**定义该臂的 \(Z_{i_s^*}(s/d)\)。在任意实际计数处，最大指数比较给出

\[
\Delta_{I_t}(t)
\le Z_{i_s^*}(s/d)
+(\widehat\mu_{I_t,n}-\mu_{I_t})_+
+\sqrt{\frac{[\log(s/(dn))]_+}{n}},
\quad n=N_{I_t}(t-1)\ge1.
\tag{4.4}
\]

由引理 1，低估项的期望和至多
\(5\sum_{s\le h}\sqrt{d/s}\le10\sqrt{dh}\)。
由引理 2，高估项至多 \(\sqrt{2kh}\le\sqrt{2dh}\)。
历史计数可能跳过很多整数，但同一臂的同一选前计数不会重复；于是引理 3 使 bonus 总和至多

\[
k\sqrt{2\pi h/d}\le\sqrt{2\pi dh}.
\]

合计系数为 \(1+10+\sqrt2+\sqrt{2\pi}<15\)。证毕。

**本轮的关键修补原则。** 保留历史之后，不能条件于段开始的历史再直接套用“旧样本是新的 i.i.d. 样本”。正确做法是先在全局潜在流上，对所有样本前缀同时建立最大偏差和非重复计数控制，再取原实验的无条件期望。段起点由外生到达决定而不由奖励决定，这一点不可省略。

---

## 5. 任意到达路径的谱上界

写 \(f_b(k)=\min\{b,\sqrt{kb}\}\)。以下使用其次可加性
\(f_b(\sum_r k_r)\le\sum_r f_b(k_r)\)：若任一项饱和则显然；否则由平方根次可加性即可。

### 5.1 延后与删除的谱比较

**引理 5。** 从非 anchor 臂集合中删除任意臂，并将其余到达时间任意延后而不超过 \(T\)，得到 \(\mathscr S'_T\)。则

\[
\mathscr S'_T\le2\mathscr S_T.
\tag{5.1}
\]

**证明。** 原尺度 \(m\) 的 \(k_m\) 条臂只能迁入 \(\ell\le m\)，令数量为 \(k_{m,\ell}\)。先使用 \(f\) 的次可加性，将不同原组分开。固定原组，新的总贡献同时不超过

\[
\sum_{\ell\le m}b_\ell<2b_m,
\qquad
\sum_{\ell\le m}\sqrt{k_{m,\ell}b_\ell}
\le\sqrt{2k_mb_m}.
\]

因此该组贡献不超过 \(2f_{b_m}(k_m)\)。求和即得。证毕。

这只是谱的比较，不声称延后到达总会逐实例降低 regret。

### 5.2 长寿命竞争者的共同下限

**引理 6。** 若至少 \(m\) 条竞争臂均有寿命至少 \(H\)，则

\[
\mathscr S_T\ge\min\{H,\sqrt{mH}\}.
\tag{5.2}
\]

**证明。** 它们所在每个尺度满足 \(b_\ell\ge H\)，对应贡献至少 \(f_H\) 在该组数量处的值。再用 \(f_H\) 的次可加性反向合并这些下限。证毕。

### 5.3 对时钟段进行计费

固定 \(T\)，令运行段起点 \(\sigma_0<\cdots<\sigma_J\le T\)，段长 \(h_j\)，段首竞争臂数 \(c_j=K_{\sigma_j}-1\)，终点剩余长度 \(H_j=T-\sigma_j+1\)。则

\[
c_{j+1}\ge2c_j,\qquad d_j=2c_j,
\qquad K_t\le d_j\quad(t\text{ 在第 }j\text{ 段}).
\tag{5.3}
\]

首次竞争出现以前 regret 为零。

若存在 \(j_\star\) 使 \(c_{j_\star}\ge H_{j_\star}\)，取最早者。此后整个尾段 regret 至多 \(H_{j_\star}\)，而引理 6 给出

\[
H_{j_\star}\le\mathscr S_T.
\tag{5.4}
\]

不存在时将尾段视为空。下面只讨论这些早段，它们满足 \(c_j<H_j\)。设 \(c_{-1}=0\)，把在相邻段起点之间到达的竞争臂组成 \(E_j\)，首组包含截至 \(\sigma_0\) 的全部竞争臂。则

\[
m_j=|E_j|=c_j-c_{j-1}\ge c_j/2.
\]

在分析中仅保留早段的这些组，并把每条 \(E_j\) 中的臂延后到 \(\sigma_j\)。引理 5 给出新谱 \(\mathscr S'\le2\mathscr S_T\)。这不是算法的延迟操作。

按 \(H_j\) 的 dyadic 尺度分组。固定尺度 \(\ell\)，令 \(j_{\rm last}\) 为组内最后一段。由 \(c_j\) 几何增长，

\[
\sum_{j:\,2^{\ell-1}<H_j\le2^\ell}\sqrt{c_jH_j}
\le\frac{\sqrt{c_{j_{\rm last}}b_\ell}}{1-2^{-1/2}}.
\]

新谱该尺度的数量 \(k'_\ell=\sum_jm_j\) 满足

\[
c_{j_{\rm last}}/2\le k'_\ell\le c_{j_{\rm last}}<H_{j_{\rm last}}\le b_\ell.
\]

故该尺度上述和式至多
\(\sqrt2 f_{b_\ell}(k'_\ell)/(1-2^{-1/2})\)。于是

\[
\sum_{j<j_\star}\sqrt{c_jh_j}
\le\frac{2\sqrt2}{1-2^{-1/2}}\mathscr S_T.
\tag{5.5}
\]

无 \(j_\star\) 时求和包括全部段。引理 4 与 (5.4)–(5.5) 给出

\[
\mathbb ER_T(\pi^{\rm MC})
\le\left(1+\frac{60}{1-2^{-1/2}}\right)\mathscr S_T
<210\mathscr S_T.
\]

定理 1 使用较宽松的常数 300。整个证明没有把未知的 \(T,H_j,j_\star\) 或分组传给算法。历史没有清空，且也没有遗漏给旧臂采样的 regret。

---

## 6. 匹配下界：共同环境族中的可兼容尺度

### 6.1 KL 与总变差

同一策略、相同日程、仅臂 \(i\) 在两个环境下不同，到确定时刻 \(u\) 的历史分布满足

\[
D(\mathbb P_0^u\Vert\mathbb P_i^u)
=\mathbb E_0N_i(u)\operatorname{kl}(p_i,q_i).
\tag{6.1}
\]

理由是动作核在两个环境相同，条件似然比相消；只需将被观察奖励的对数似然比逐步条件求和。独立算法随机种子可以放入共同历史，其 KL 贡献为零。这也是 [W5] 中换测度方法的确定终点版本。

所需 Pinsker 形式为 \(\mathrm{TV}(P,Q)\le\sqrt{D(P\Vert Q)/2}\)。它可由对事件的 KL 数据处理和
\(\operatorname{kl}(p,q)\ge2(p-q)^2\) 得到；后一不等式对 \(p\) 求二阶导，使用 \(1/[p(1-p)]\ge4\) 后在 \(p=q\) 积分。故对 \(0\le Y\le h\)，

\[
|\mathbb E_PY-\mathbb E_QY|\le h\sqrt{D(P\Vert Q)/2}.
\tag{6.2}
\]

同时，由 \(\log x\le x-1\)，
\(\operatorname{kl}(p,q)\le(p-q)^2/[q(1-q)]\)。下述均值范围保证每次所用 KL 不超过 \(32\epsilon^2\)。

### 6.2 单臂及小尺度部分

若 \(K_T\ge2\)，取寿命最大的竞争臂 \(i\)，记 \(H_{\max}=H_i\)。其他臂全部均值为 \(1/2\)，只令 \(\mu_i=1/2\pm\epsilon\)，其中
\(\epsilon=1/(32\sqrt{H_{\max}})\)，奖励均 Bernoulli。到达前两环境历史相同，全部 KL 至多 \(32H_{\max}\epsilon^2\)，故 TV 至多 \(1/8\)。两环境等权 Bayes 风险至少

\[
\frac{\epsilon H_{\max}}2(1-1/8)
\ge\frac{\sqrt{H_{\max}}}{128}.
\tag{6.3}
\]

将所有 \(k_\ell=1\) 的尺度及 \(\ell=0,1\) 的尺度并集记为 rest，其谱质量为 \(S_{\rm rest}\)。几何级数给出

\[
S_{\rm rest}
\le\frac{\sqrt{2H_{\max}}}{1-2^{-1/2}}+3
\le8\sqrt{H_{\max}}.
\]

所以 \(\mathfrak R_T\ge S_{\rm rest}/1024\)。并集里的重叠在这个上界中重复计算只会放大右端，不影响结论。

### 6.3 保留足够质量，但控制 benchmark 总增长

其余尺度满足 \(\ell\ge2,k_\ell\ge2\)，记谱质量 \(S_{\rm high}\)。令

\[
m_\ell=k_\ell-1,\qquad
v_\ell=\min\{1,\sqrt{m_\ell/b_\ell}\}.
\]

则

\[
b_\ell v_\ell\ge2^{-1/2}s_{\ell,T}.
\tag{6.4}
\]

先选 \(\sum b_\ell v_\ell\) 较大的奇数或偶数尺度，保留至少一半该质量。按尺度由大到小扫描，保留第一个，以后只在 \(v_\ell>2v_{\rm last}\) 时保留，得到集合 \(\mathcal J\)。

同奇偶相邻尺度的 \(b\) 至少缩小四倍。每个保留尺度之后、下一个保留尺度之前被略去的项，都有 \(v\le2v_{\rm last}\)，其 \(b\) 之和不超过 \(b_{\rm last}/3\)。因此略去质量至多该保留项的 \(2/3\)。由此

\[
\sum_{\ell\in\mathcal J}b_\ell v_\ell
\ge\frac{3}{10\sqrt2}S_{\rm high},\qquad
\sum_{\ell\in\mathcal J}v_\ell\le2.
\tag{6.5}
\]

第二式来自保留的 \(v\) 沿实际时间顺序至少翻倍且最后不超过 1。它解决“多个局部最坏环境是否能装进同一个有界奖励模型”的兼容性问题。

### 6.4 单一乘积先验

按保留尺度由大到小排列，令

\[
\epsilon_\ell=v_\ell/32,\qquad
\theta_\ell=1/2+\sum_{r\in\mathcal J:\,r>\ell}\epsilon_r.
\]

每个被保留组，任选一条真实臂为参照，均值 \(\theta_\ell\)。其余 \(m_\ell\) 条候选受独立潜变量 \(Z_\ell\) 控制：以概率 \(1/2\)，全部为 \(\theta_\ell-\epsilon_\ell\)；对每个候选 \(i\)，以概率 \(1/(2m_\ell)\)，仅它提升为 \(\theta_\ell+\epsilon_\ell\)。anchor 均值 \(1/2\)，其他所有未选臂均值 \(1/4\)，全部奖励 Bernoulli。

参照水平只使用确定的 \(\epsilon\)，不使用其他组潜变量。因 \(\sum\epsilon_\ell\le1/16\)，所有均值合法，且后续组的参照不泄露前组的答案。

仅在下列区间对第 \(\ell\) 组计费：

\[
Q_\ell=\{T-b_\ell/2+1,\ldots,T-b_\ell/4\},
\qquad h_\ell=b_\ell/4.
\tag{6.6}
\]

所有该组臂在区间前已到达；下一个保留组最早在区间结束的下一轮到达。各 \(Q_\ell\) 不交。即使最大 \(b_\ell\) 大于 \(T\)，该区间仍落在 \([1,T]\)，因为该组非空保证 \(T>b_\ell/2\)。过去各组的最高可能均值不超过当前参照 \(\theta_\ell\)。所以 null 中参照最优，spike 中对应候选最优。

**预先观察必须计入。** 该组可能在 \(Q_\ell\) 之前获得奖励。我们将这些全部包含在下一步的完整历史 KL 内；从本组最早可能到达到 \(Q_\ell\) 末尾，总采样槽至多 \(b_\ell\)。

### 6.5 条件比较与合法加总

固定其他潜变量，比较当前组的 null 与 spike \(i\)。令

\[
A=\sum_{i=1}^{m_\ell}\mathbb E_0N_i(Q_\ell),\qquad
D_i=\operatorname{kl}(\theta_\ell-\epsilon_\ell,
\theta_\ell+\epsilon_\ell)\,\mathbb E_0N_i(\operatorname{end}Q_\ell).
\]

完整历史计数和 Cauchy–Schwarz 给出

\[
\frac1{m_\ell}\sum_i\sqrt{D_i/2}
\le\sqrt{\frac{32\epsilon_\ell^2b_\ell}{2m_\ell}}
\le\frac18.
\tag{6.7}
\]

null 区间风险至少 \(\epsilon_\ell A\)，spike \(i\) 风险至少
\(\epsilon_\ell(h_\ell-\mathbb E_iN_i(Q_\ell))\)。使用 (6.2) 后，条件 Bayes 风险至少

\[
\begin{aligned}
\frac{\epsilon_\ell}2A+
\frac{\epsilon_\ell}{2m_\ell}\sum_i
(h_\ell-\mathbb E_iN_i(Q_\ell))
&\ge\frac{\epsilon_\ell}2
\left[h_\ell+(1-1/m_\ell)A
-h_\ell\frac1{m_\ell}\sum_i\sqrt{D_i/2}\right]\\
&\ge\frac{\epsilon_\ell h_\ell}{4}
=\frac{b_\ell v_\ell}{512}.
\end{aligned}
\tag{6.8}
\]

它对其他潜变量的每个配置都成立。对这些配置积分，再对不交区间求和，得到同一个乘积先验下的风险下界；没有将不同的最坏环境直接相加。由 (6.5)，

\[
\mathfrak R_T\ge\frac{3}{5120\sqrt2}S_{\rm high}
\ge\frac{S_{\rm high}}{2500}.
\]

与 rest 下界取最大值，至少为
\((S_{\rm rest}+S_{\rm high})/10000\)。无竞争臂时双方为零。定理 1 的下界证毕。

**附带结论。** 以上构造的 anchor 分布始终固定为 \(\mathrm{Ber}(1/2)\)。因此，即使把 anchor 的完整分布提前告诉策略，下界仍然成立。该完整模型的最坏难度不能仅靠消除 incumbent 的不确定性而消失。

---

## 7. 无网格的统计采样容量：表述、精确解和对偶

### 7.1 到达约束的完整分数 occupancy

仅对非 anchor 臂记样本工作量，定义

\[
\mathcal N_T^{\rm arr}
=\left\{n\ge0:\ \sum_{i:H_i\le h}n_i\le h,
\quad h=1,\ldots,T\right\}.
\tag{7.1}
\]

**引理 7（后缀容量条件的充要性）。** 向量 \(n\) 属于 (7.1)，当且仅当存在一个合法分数采样安排：每个物理时刻的总分配不超过 1，未到达臂分配为零，臂 \(i\) 的总分配为 \(n_i\)。未使用的容量可以由 anchor 补齐。

**证明。** 必要性来自：寿命不超过 \(h\) 的臂只能在最后 \(h\) 个时间槽采样。为证充分性，按寿命从短到长处理各臂。在其最后 \(H_i\) 个槽里，以任意方式分配 \(n_i\) 单位尚未占用的容量。已经处理的全部臂的分配也在此后缀内，而 (7.1) 保证它们连同当前臂的总需求不超过 \(H_i\)。所以每一步都能完成。允许一个槽被分数分配，避免不必要的整数取整问题。证毕。

定义凹函数

\[
\phi(x)=\min\{x,\sqrt x\},\quad x\ge0,
\qquad
\boxed{\mathscr C_T=\max_{n\in\mathcal N_T^{\rm arr}}
\sum_{i\ne a}\phi(n_i).}
\tag{7.2}
\]

\(\phi\) 单调、凹、1-Lipschitz；在零点附近线性，在 \(x>1\) 时按平方根增长。可行集是有限维紧集，故最大值存在。没有竞争臂时定义 \(\mathscr C_T=0\)。这不是 bandit 风险的动态规划，也不使用未知均值；它只衡量到达约束下可分配的统计采样容量。最大化该确定性函数不是要求实际 learner 按其最优向量采样，也不表示这种分配对每个未知均值实例都最优；它与学习风险的联系由下面的常数等价和定理 1 建立。

### 7.2 与谱的常数等价

**定理 2（无网格容量刻画）。** 对每条到达路径、每个终点，

\[
\boxed{\frac14\mathscr S_T\le\mathscr C_T\le\mathscr S_T.}
\tag{7.3}
\]

从而

\[
\frac{\mathscr C_T}{10000}
\le\mathfrak R_T(\tau)
\le\sup_P\mathbb ER_T(\pi^{\rm MC})
\le\min\{T,1200\mathscr C_T\}.
\tag{7.4}
\]

**证明。** 对任意可行 \(n\)，第 \(\ell\) 组的总分配不超过 \(b_\ell\)。由于 \(\phi(x)\le x\) 且 \(\phi(x)\le\sqrt x\)，

\[
\sum_{i\in G_\ell}\phi(n_i)
\le\min\left\{\sum_{i\in G_\ell}n_i,
\sqrt{k_\ell\sum_{i\in G_\ell}n_i}\right\}
\le s_{\ell,T}.
\]

求和给上界。下界使用明确可行向量：对每个非空组，令

\[
n_i=\frac{b_\ell}{4k_\ell},\qquad i\in G_\ell.
\]

固定整数后缀 \(h\)，凡 \(H_i\le h\) 的臂所在组，其最大 dyadic 上端点 \(b_{\max}\) 满足 \(b_{\max}<2h\)。将所有这些组都完整计入，只会放大需求；总量不超过
\(\frac14\sum_{b_\ell\le b_{\max}}b_\ell<h\)。故向量可行。其每组目标为

\[
k_\ell\phi\!\left(\frac{b_\ell}{4k_\ell}\right)
=\min\{b_\ell/4,\sqrt{k_\ell b_\ell}/2\}
\ge s_{\ell,T}/4.
\]

(7.4) 由定理 1 得到。证毕。

**解释。** 小于一次观测的分数容量不能贡献 \(\sqrt{n_i}\) 那样过大的收益，所以需要 \(\phi\) 的线性截断；直接使用 \(\sum_i\sqrt{n_i}\) 会在末期巨大 batch 上失真。这是 (7.2) 中截断不可省略的原因。

### 7.3 精确最优解：下凸包的斜率

将竞争臂寿命排序为
\(H_{(1)}\le\cdots\le H_{(M)}\)，其中 \(M=K_T-1\)。
(7.1) 等价于

\[
\sum_{i=1}^r n_{(i)}\le H_{(r)},\qquad r=1,\ldots,M.
\tag{7.5}
\]

重复寿命不会造成问题：相同寿命组末端的约束蕴含其前面的部分约束。

**定理 3（容量的精确计算与最优性证书）。** 对平面点
\((0,0),(r,H_{(r)})\)，取连接起点和终点的下凸包。设其顶点横坐标为
\(0=r_0<r_1<\cdots<r_B=M\)，记 \(H_{(0)}=0\)，并令

\[
q_b=\frac{H_{(r_b)}-H_{(r_{b-1})}}{r_b-r_{b-1}},\qquad
n_{(i)}^*=q_b\quad(r_{b-1}<i\le r_b).
\tag{7.6}
\]

则 \(q_b>0\) 且非减，\(n^*\) 达到 (7.2) 的最大值，并且

\[
\boxed{\mathscr C_T=
\sum_{b=1}^B(r_b-r_{b-1})\phi(q_b).}
\tag{7.7}
\]

排序需要 \(O(M\log M)\) 次比较；排序后的下凸包用单调栈在线性步数内构造。此复杂度为比较／算术操作数，不额外声称任意大整数的单位位复杂度。

**证明。** 一个不依赖几何直觉的等价构造是：从 \(r_{b-1}\) 出发，对全部 \(r>r_{b-1}\) 最小化
\((H_{(r)}-H_{(r_{b-1})})/(r-r_{b-1})\)，取最大的最小化点为 \(r_b\)。第一段斜率严格正；若下一斜率比当前小，则到该下一终点的合并斜率也更小，与当前最小化矛盾。取最大最小化点排除不必要的共线顶点。因此斜率非减且严格正。

最小斜率的定义保证每条弦均位于中间点下方，故 \(n^*\) 满足全部 (7.5)，且每个 \(r_b\) 处约束取等号。

为证最优性，取 \(\phi\) 在 \(q_b\) 处的超梯度

\[
p_b=\begin{cases}1,&q_b\le1,\\
1/(2\sqrt{q_b}),&q_b>1.\end{cases}
\]

\(p_b\) 非增；在折点 1，取 1 是合法超梯度。令 \(p_{B+1}=0\)，在 \(r_b\) 处放置乘子
\(\lambda_{r_b}=p_b-p_{b+1}\ge0\)，其余 \(\lambda_r=0\)。对块内标签，记 \(p_i=p_b=\sum_{r\ge i}\lambda_r\)。任意可行 \(n\) 满足

\[
\begin{aligned}
\sum_i[\phi(n_i)-\phi(n_i^*)]
&\le\sum_i p_i(n_i-n_i^*)\\
&=\sum_r\lambda_r\left(\sum_{i\le r}n_i-\sum_{i\le r}n_i^*\right)\\
&=\sum_r\lambda_r\left(\sum_{i\le r}n_i-H_{(r)}\right)\le0.
\end{aligned}
\]

最后一个等号只对非零乘子处使用紧约束。由此得到最优性，不需要假定严格凹性或最优解唯一。单调栈在新弦导致斜率不递增时删除中间点，每点至多入栈、出栈一次；以交叉相乘比较斜率，可以不用浮点数判断凸性。证毕。

### 7.4 精确对偶

令

\[
g(c)=\sup_{x\ge0}\{\phi(x)-cx\}
=\begin{cases}
+\infty,&c=0,\\
1/(4c),&0<c\le1/2,\\
1-c,&1/2\le c\le1,\\
0,&c\ge1.
\end{cases}
\tag{7.8}
\]

端点公式一致。分别在 \([0,1]\) 与 \([1,\infty)\) 上求一元最大值即可验证。

**推论 3.1（对偶及可核验证书）。** 当 \(M\ge1\) 时，

\[
\boxed{
\mathscr C_T=\min_{\lambda_r\ge0}
\left\{\sum_{r=1}^M H_{(r)}\lambda_r+
\sum_{i=1}^M g\!\left(\sum_{r=i}^M\lambda_r\right)\right\}.
}
\tag{7.9}
\]

**证明。** 对任意非负乘子，用
\(\phi(n_i)\le c_i n_i+g(c_i)\)、\(c_i=\sum_{r\ge i}\lambda_r\)，再使用 (7.5)，得到弱对偶。采用定理 3 的乘子，每个 \(c_i\) 都是 \(n_i^*\) 的超梯度，所以共轭不等式取等号；非零乘子处约束也取等号。故达到对偶下界，得到精确等式与可达性。证毕。

这个对偶可以视为“时间容量价格”的分析工具。凸包与对偶方法本身是常规凸优化技术，不应被单独包装为新的统计原理；其价值在于它们给出了与真实 minimax 风险等价的可计算对象。

---

## 8. 固定点的精确含义：\(\ell_2\) 与 \(\ell_1\) 的区别

### 8.1 一般等价，不只是一条分离路径

保留 Part I 的整数固定点：当 \(M\ge1\)，

\[
V_T(r)=\sum_{i\ne a}H_i\mathbf1\{H_i>r\},\qquad
\Gamma_T=\min\{r\in\{1,\ldots,T\}:V_T(r)\le r^2\}.
\]

无竞争臂时 \(\Gamma_T=0\)。另记

\[
Q_T=\left(\sum_\ell s_{\ell,T}^2\right)^{1/2}.
\]

**定理 4（固定点的平方谱解释）。** 当 \(M\ge1\)，

\[
\boxed{\Gamma_T\le\lceil Q_T\rceil\le2Q_T,
\qquad Q_T\le3\Gamma_T.}
\tag{8.1}
\]

**证明。** \(Q_T\ge1\)。令 \(r=\lceil Q_T\rceil\)。若 \(r>T\)，则第一个不等式显然；否则，凡 \(H_i>r\) 的臂所在组都有 \(b_\ell>Q_T\)。该组不可能饱和，因为饱和会使单个分量 \(s_\ell=b_\ell>Q_T\)。所以

\[
V_T(r)\le\sum_{\ell:\,b_\ell>Q_T}k_\ell b_\ell
=\sum_{\ell:\,b_\ell>Q_T}s_\ell^2\le Q_T^2\le r^2.
\]

于是 \(\Gamma_T\le r\)，再用 \(Q_T\ge1\) 即得 \(r\le2Q_T\)。

反之，令 \(r=\Gamma_T\)，\(m=\lceil\log_2r\rceil\)。小尺度的平方和满足

\[
\sum_{\ell\le m}s_\ell^2\le\sum_{\ell\le m}4^\ell
<\frac{16}{3}r^2.
\]

大尺度 \(\ell>m\) 的全部寿命均大于 \(r\)，且 \(b_\ell<2H_i\)。因此

\[
\sum_{\ell>m}s_\ell^2\le\sum_{\ell>m}k_\ell b_\ell
\le2V_T(r)\le2r^2.
\]

总平方和小于 \((22/3)r^2<9r^2\)。证毕。

**推论 4.1（有效尺度数）。** 定义

\[
D_T^{\rm eff}=\frac{\mathscr S_T^2}{Q_T^2},\qquad M\ge1.
\tag{8.2}
\]

则 \(1\le D_T^{\rm eff}\le1+\lceil\log_2T\rceil\)，并且

\[
\boxed{
\mathfrak R_T(\tau)\asymp\mathscr S_T
\asymp\Gamma_T\sqrt{D_T^{\rm eff}}.
}
\tag{8.3}
\]

无竞争臂时另定义 \(D_T^{\rm eff}=0\)。证明仅使用定理 1、(8.1) 及 Cauchy–Schwarz。

这里 \(D_T^{\rm eff}\) 使用指定 dyadic 网格，但 \(\Gamma_T\)、\(\mathscr C_T\) 不依赖网格；(7.3)、(8.1) 保证其在常数精度上的结构解释不是网格选择的产物。\(\asymp\) 不代表已求出 minimax 的精确渐近常数。

### 8.2 以原固定点书写的加强上界

**推论 4.2。** 对 \(r=\Gamma_T\ge1\)，

\[
\mathscr S_T\le4r+r\sqrt{2(L-\lceil\log_2r\rceil)_+}
\le C r\sqrt{1+\log(T/r)}.
\tag{8.4}
\]

因此同一 MC-MOSS 满足

\[
\sup_P\mathbb ER_T
\le\min\{T,C\Gamma_T\sqrt{1+\log(T/\Gamma_T)}\}.
\tag{8.5}
\]

**证明。** 将前证的小尺度按 \(s_\ell\le b_\ell\) 求和，得到小于 \(4r\)。大尺度共有至多 \(L-\lceil\log_2r\rceil\) 组，平方和不超过 \(2r^2\)，使用 Cauchy–Schwarz 即得。证毕。

与旧 Part I 的 \(\Gamma_T\sqrt{\log(2T)[1+\log(T/\Gamma_T)]}\) 相比，额外的集中对数被移除了；剩余的尺度因子不能一般性删掉。

### 8.3 多尺度反例与最大分离

**命题 2（固定点漏掉的因子确实可达）。** 取整数 \(m\ge1\)、\(T=16^m\)。在初始 anchor 外，第 \(j\) 批含 \(4^j\) 条臂，剩余寿命

\[
H_j=4^{2m-j},\qquad j=0,\ldots,m.
\tag{8.6}
\]

则

\[
\mathscr S_T=(m+1)\sqrt T,\quad Q_T=\sqrt{(m+1)T},\quad
\Gamma_T\asymp\sqrt{mT},\quad
\mathfrak R_T\asymp\sqrt T\log T.
\tag{8.7}
\]

**证明。** 各批在互异 dyadic 尺度，\(4^jH_j=T\)，且 \(4^j\le H_j\)，所以每批分量均为 \(\sqrt T\)。于是前两个等式直接成立，第三个由定理 4，最后一个由定理 1。所有到达时刻 \(T-H_j+1\) 合法。证毕。

总竞争臂数为 \((4^{m+1}-1)/3=\Theta(\sqrt T)\)。只用总臂数得到的 \(\sqrt{K_TT}\) 为 \(\Theta(T^{3/4})\)，明显偏大；只用 \(\Gamma_T\) 又少一个 \(\sqrt{\log T}\)。

结合 (8.4)，在所有日程中 \(\mathscr S_T/\Gamma_T\) 的最大阶为 \(\Theta(\sqrt{\log(eT)})\)。上界已证；下界对一般充分大的 \(T\)，取最大的 \(16^m\le T\)，将 (8.6) 的实验放入最后 \(16^m\) 轮，之前只有 anchor。竞争臂的寿命谱不变，且 \(m\asymp\log T\)。

**再加强的诊断。** 在同一个 \(T=16^m\) 上，另取同样最终臂数的日程：\(m+1\) 条竞争臂第一轮到达，其余在最后一轮到达。其 \(\Gamma_T\asymp\sqrt{mT}\) 与 (8.6) 同阶，但 \(\mathscr S_T\asymp\sqrt{mT}\)。所以即使同时记录最终 \(K_T\) 和固定点 \(\Gamma_T\)，仍不能在常数因子内区分这两类日程的最优风险。

---

## 9. 下界并非罕见坏事件：常数概率和分位数

**定理 5（常数概率谱下界）。** 对任意到达路径、\(T\) 和策略，存在一个固定的合法 Bernoulli 环境，使

\[
\boxed{\Pr\{R_T\ge\mathscr S_T/20000\}\ge1/8.}
\tag{9.1}
\]

无竞争臂时事件为 \(R_T\ge0\)，结论平凡。困难环境允许依赖策略、日程和终点；不声称同一环境同时让全部终点困难。

**证明。** 不能直接从期望下界推断 (9.1)，因为 \(R_T\) 的平凡最大值是 \(T\) 而非 \(\mathscr S_T\)。需要使用第 6 节构造中的有界代理损失。

若 \(S_{\rm high}\ge\mathscr S_T/2\)，使用其乘积先验。每个区间定义：null 中
\(Y_\ell=\epsilon_\ell\sum_iN_i(Q_\ell)\)；spike \(i\) 中
\(Y_\ell=\epsilon_\ell[h_\ell-N_i(Q_\ell)]\)。逐路径有

\[
0\le Y:=\sum_\ell Y_\ell\le R_T,
\quad Y\le A:=\sum_\ell\epsilon_\ell h_\ell,
\quad \mathbb EY\ge A/4,
\]

最后一式正是 (6.8)。因此
\(\mathbb EY\le A/8+A\Pr(Y\ge A/8)\)，得到
\(\Pr(Y\ge A/8)\ge1/8\)。又由 (6.5)，

\[
A/8=\frac1{1024}\sum_{\ell\in\mathcal J}b_\ell v_\ell
\ge\frac{3}{20480\sqrt2}\mathscr S_T
\ge\mathscr S_T/20000.
\]

若 \(S_{\rm rest}\ge\mathscr S_T/2\)，采用 (6.3) 的两环境等权先验。代理为“较差环境选候选的次数乘 \(\epsilon\)”或“较好环境不选候选的次数乘 \(\epsilon\)”。此时 \(Y\le A=\epsilon H_{\max}=\sqrt{H_{\max}}/32\)，且 \(\mathbb EY\ge A/4\)。同一论证给出 \(\Pr(Y\ge A/8)\ge1/8\)，并由 \(S_{\rm rest}\le8\sqrt{H_{\max}}\) 得
\(A/8\ge\mathscr S_T/4096\)。两种情形都先得到先验平均概率下界，再取至少一个支持点环境，其概率不小于平均值。证毕。

**推论 5.1（固定置信水平的 minimax 分位数）。** 令

\[
r_\delta(T,\tau)=\inf_\pi\inf\{r\ge0:
\sup_P\Pr_P(R_T>r)\le\delta\}.
\]

对 \(0<\delta<1/8\)，

\[
\frac{\mathscr S_T}{20000}
\le r_\delta(T,\tau)
\le\min\{T,300\mathscr S_T/\delta\}.
\tag{9.2}
\]

下界来自 (9.1)，上界为定理 1 加 Markov。对每个固定 \(\delta\)，分位数也由谱刻画到常数因子；**没有得到随 \(\delta\downarrow0\) 的最优依赖**，不能把 (9.2) 称为尖锐小错误概率定理。

---

## 10. 到达扰动、巨大晚批次和逐时增长

下面的精确稳定性针对无网格容量 \(\mathscr C\)。不能把这些精确不等式直接移植为实际 minimax 风险的加性不等式，因为 (7.4) 只给常数等价。

**定理 6（容量的稳定性）。** 以下结论均不使用均值。

**(a) 巨大晚批次。** 在固定终点添加任意有限数量、且寿命都不超过 \(h\) 的竞争臂，容量的增加量介于 0 和 \(h\) 之间。

**(b) 日程抖动。** 对同一竞争臂集合的两个合法寿命向量 \(H,H'\)，若
\(\max_i|H_i-H_i'|\le d\)，其中 \(d\) 为非负整数，则

\[
\boxed{|\mathscr C(H)-\mathscr C(H')|\le d.}
\tag{10.1}
\]

**(c) 一步时间推进。** 在同一条无限到达路径上，允许下一轮出现任意大但有限的 batch，仍有

\[
\boxed{0\le\mathscr C_{T+1}-\mathscr C_T\le1.}
\tag{10.2}
\]

**证明。** (a) 添加臂扩大可行集。反向取新系统的任意最优分数安排，删除新臂的分配；其总量由后缀容量限制在 \(h\) 以内。由于 \(\phi(x)\le x\)，目标最多减少 \(h\)，余下安排在旧系统可行。

(b) 取 \(H'\) 下的最优向量 \(n\)，但按 \(H\) 升序排列其标签。对任意前缀 \(r\)，这些标签在新系统中的寿命都不超过 \(H_{(r)}+d\)，故其分配和不超过 \(H_{(r)}+d\)。若该数超过 \(T\)，则使用总分配不超过 \(T\) 仍得同一结论。

从短寿命前缀开始，遇到原约束超额时删除刚好足够的分配。删除只会帮助先前的上界约束，且累计删除量可取为

\[
D_r=\max_{q\le r}\left(\sum_{i\le q}n_{(i)}-H_{(q)}\right)_+\le d.
\]

在每个步骤总有足够的已分配质量可以删除；总删除量至多 \(d\)。由于 \(\phi\) 为 1-Lipschitz，目标减少至多 \(d\)，因此 \(\mathscr C(H')\le\mathscr C(H)+d\)。交换两个系统得到 (10.1)。

(c) 把旧安排原样嵌入新终点，得非减性。取新终点的最优分数物理安排，删去最后一个时间槽；在这一轮才到达的臂，其全部分配随之删除。其余是截至 \(T\) 的合法安排。最后一槽总容量为 1，\(\phi\) 的 Lipschitz 性保证目标损失至多 1。证毕。

**附带性质。** 寿命逐坐标增加使 \(\mathscr C\) 非减；删除臂或延后其到达使之非增。只要至少存在一个竞争者，

\[
\sqrt{H_{\max}}\le\mathscr C_T\le H_{\max}\le T.
\tag{10.3}
\]

下界将 \(H_{\max}\) 个分数样本都分给一个最长寿命臂；上界使用所有竞争臂都只能在最后 \(H_{\max}\) 轮采样，以及 \(\phi\le\mathrm{id}\)。这同时解释：一个极长的单臂独占前缀不会凭空产生决策难度，而大量只剩最后一轮的新臂也不会让原始学习成本跳升到臂数级。

---

## 11. 学习边界与可解释日程

### 11.1 同一保留历史策略实现精确边界

**定理 7（uniform anytime 可学习性的等价条件）。** 对同一条无限外生到达路径，以下命题等价：

\[
\boxed{
K_t=o(t)
\ \Longleftrightarrow\ \mathscr S_T=o(T)
\ \Longleftrightarrow\ \mathscr C_T=o(T)
\ \Longleftrightarrow\
\exists\pi_\infty:\sup_P\mathbb E_PR_T(\pi_\infty)=o(T).
}
\tag{11.1}
\]

充分性由第 4 节同一个 \(\pi^{\rm MC}\) 对所有这类路径实现，不必知道 \(K_t/t\) 的收敛速度。

**证明。** 由 Cauchy–Schwarz 与 \(\sum_{\ell\le L}b_\ell<4T\)，

\[
\mathscr S_T\le\sum_\ell\sqrt{k_\ell b_\ell}
\le2\sqrt{(K_T-1)T}.
\tag{11.2}
\]

故 \(K_T=o(T)\) 推出 \(\mathscr S_T=o(T)\)，定理 1 给出同一算法的充分性。容量与谱等价。

反之，若沿 \(t_j\to\infty\) 有 \(K_{t_j}\ge\varepsilon t_j\)，取 \(T_j=2t_j\)。截至 \(t_j\) 的至少 \(\varepsilon t_j-1\) 条竞争臂均有寿命至少 \(t_j+1\)。引理 6 使 \(\mathscr S_{T_j}\ge c_\varepsilon T_j\)。定理 1 的下界排除任何策略的 uniform no-regret。证毕。

这个条件在 Part I 已成立，本轮的新点是：同一保留历史策略不仅实现该边界，也达到逐日程的精确谱速率。\(\sup_P\) 不能去掉或移到极限外；本定理不声称存在同一个固定环境在所有困难终点都使每条策略线性失败。

**推论 7.1（uniform 依概率版本）。** (11.1) 也等价于存在同一策略使每个 \(\epsilon>0\) 满足
\(\sup_P\Pr_P(R_T/T>\epsilon)\to0\)。

证明：一个方向使用 Markov；另一个方向使用 \(0\le R_T/T\le1\)，因而
\(\sup_P\mathbb E(R_T/T)\le\epsilon+\sup_P\Pr(R_T/T>\epsilon)\)，先让 \(T\to\infty\)，再让 \(\epsilon\downarrow0\)。

### 11.2 静态与单次到达

**推论 7.2。** 初始 anchor 之外，\(M\ge1\) 个竞争者在剩余 \(H\) 轮时同时到达，则

\[
\mathscr C_T=\min\{H,\sqrt{MH}\},\qquad
\mathfrak R_T\asymp\min\{H,\sqrt{MH}\}.
\tag{11.3}
\]

**证明。** 所有竞争者仅有共同约束 \(\sum_i n_i\le H\)。Jensen 给出最大值 \(M\phi(H/M)\)，均分容量达到它。再用 (7.4)。证毕。

\(H=T\) 恢复静态 minimax；\(H=1\) 时任意大 \(M\) 的难度仍为常数。\(M=0\) 时风险为零，不能使用含正平方根的静态表达掩盖这一退化情形。

### 11.3 规则增长与接近边界的日程

**命题 3（早期臂数足够时的总臂数速率）。** 若固定 \(a\in(0,1]\)，对所考虑的终点有

\[
K_{\lfloor T/2\rfloor}-1\ge a(K_T-1)>0,
\]

则

\[
\mathfrak R_T\asymp_a\min\{T,\sqrt{(K_T-1)T}\}.
\tag{11.4}
\]

证明由早期臂的寿命至少 \(T/2\)、引理 6、(11.2) 和平凡上界 \(T\) 组成；比较常数允许依赖 \(a\)。

由此得到以下**阶数**，不是精确的 minimax 极限常数：

| 日程 | 风险阶 |
|---|---|
| \(K_t\asymp t^\alpha\)，固定 \(0<\alpha<1\) | \(T^{(1+\alpha)/2}\) |
| \(K_t\asymp t^\alpha\)，固定 \(\alpha\ge1\) | \(T\) |
| \(K_t\asymp t/(\log t)^p\)，固定 \(p>0\) | \(T/(\log T)^{p/2}\) |
| \(K_t\asymp t/\log\log t\)，足够大的 \(t\) | \(T/\sqrt{\log\log T}\) |
| 固定 \(K\ge2\)，全部早已到达 | \(\sqrt{(K-1)T}\) |

表中 \(\asymp\) 的上下常数使 (11.4) 的早期比例条件最终成立。它们说明同一算法可覆盖任意慢的次线性臂数增长；不能仅根据带 \(\log T\) 的普通 UCB 上界来推断必须有 \(K_T\log T=o(T)\)。

### 11.4 一个可证明但非最强的几乎处处结论

**推论 7.3。** 若

\[
\sum_{m\ge0}\frac{\mathscr S_{2^m}}{2^m}<\infty,
\tag{11.5}
\]

则对于每个固定奖励环境，MC-MOSS 满足 \(R_T/T\to0\) 几乎处处。

**证明。** 对任意有理 \(\epsilon>0\)，Markov 与定理 1 使
\(\sum_m\Pr(R_{2^m}>\epsilon2^m)<\infty\)。Borel–Cantelli 和可数有理数交集给出 dyadic 终点收敛。对于 \(2^m\le T<2^{m+1}\)，非负累计 regret 使
\(R_T/T\le2R_{2^{m+1}}/2^{m+1}\to0\)。证毕。

例如 \(K_t=O(t^\alpha)\)、\(\alpha<1\) 满足 (11.5)。这里只给充分条件；没有证明所有 \(K_t=o(t)\) 都使该策略几乎处处 no-regret。

---

## 12. 同一个谱最优策略的实例敏感上界

这一节不改变主模型。所有 gap 参数只进入事后分析，不作为算法输入。

固定 \(T\)，令 \(\mathcal B_T\) 为截至 \(T\) 曾严格次优的臂，定义

\[
\gamma_i=\min_{t\le T:\,i\in A_t,\,\Delta_i(t)>0}\Delta_i(t),
\quad i\in\mathcal B_T,
\qquad L_T^0=\log(eT).
\]

各集合有限，所以非空时 \(\gamma_i>0\)。另定义
\(\gamma_t=\min_{i\in A_t:\,\Delta_i(t)>0}\Delta_i(t)\)；若本轮全部并列最优，令 \(\gamma_t=+\infty\)。设本轮所在时钟段容量为 \(d_j\)，局部时间为 \(s\)，并记

\[
\mathcal U_T=
\sum_{t\le T:\,\gamma_t<\infty}
\min\left\{1,15\sqrt{d_j/s},\frac{90d_j}{s\gamma_t}\right\}.
\tag{12.1}
\]

在出现竞争前该求和为空。

**定理 8（随机奖励的 gap 上界）。** 同一 MC-MOSS 满足

\[
\mathbb ER_T\le
\sum_{i\in\mathcal B_T}
\left[1+\frac{9+18L_T^0}{\gamma_i}\right]+\mathcal U_T.
\tag{12.2}
\]

特别地，若 \(\mathcal B_T\ne\varnothing\)，令
\(\gamma=\min_i\gamma_i\)，则

\[
\boxed{\mathbb ER_T\le
\min\left\{T,300\mathscr S_T,
\frac{400(K_T-1)\log(eT)}{\gamma}\right\}.}
\tag{12.3}
\]

全部均值相同且始终并列时 regret 为零。

**证明。** 真正首次观察一个严格次优臂的总损失至多 \(|\mathcal B_T|\)。对其余正 regret 选择，使用 (4.4)，写 \(\Delta\le Z+e+b\)。将该选择按顺序分到第一个满足条件的类别：\(Z\ge\Delta/3\)，否则 \(e\ge\Delta/3\)，否则 \(b\ge\Delta/3\)。至少一类成立，避免隐含遗漏。

低估类的每轮损失至多
\(\min\{1,3Z\mathbf1\{Z\ge\gamma_t/3\}\}\)。分别使用 (3.5)、(3.6) 及损失至多 1，期望总和不超过 (12.1)。该最佳臂标签在固定日程和均值下确定，故可用引理 1 的全局前缀版本。

高估类中，对臂 \(i\) 有 \(\Delta\le3e\)、\(e\ge\gamma_i/3\)。同一臂的全局选前计数只出现一次。对任意 \(a>0\)，Hoeffding 尾界与非负交换给出

\[
\begin{aligned}
\sum_{n\ge1}\mathbb E[e_n\mathbf1\{e_n\ge a\}]
&\le\frac{a}{e^{2a^2}-1}
+\int_a^\infty\frac{dx}{e^{2x^2}-1}\\
&\le\frac1{2a}+\frac1{2a}=\frac1a.
\end{aligned}
\]

取 \(a=\gamma_i/3\) 并乘 3，得到 \(9/\gamma_i\)。

bonus 类中，\(b\le\sqrt{L_T^0/n}\)，而 \(b\ge\gamma_i/3\) 蕴含
\(n\le9L_T^0/\gamma_i^2\)。将非重复计数扩展到这些整数并用 \(\sum_{n\le u}n^{-1/2}\le2\sqrt u\)，得到该臂总损失至多
\(18L_T^0/\gamma_i\)。合并证明 (12.2)。

最后，存在至少一个终点最优臂在其到达之后从未严格次优，故 \(|\mathcal B_T|\le K_T-1\)。由容量段几何增长，\(\sum_jd_j\le4(K_T-1)\)，每段 \(\sum_{s\le h_j}1/s\le\log(eT)\)，所以
\(\mathcal U_T\le360(K_T-1)L_T^0/\gamma\)。其余项至多 \(28(K_T-1)L_T^0/\gamma\)，总常数小于 400。与定理 1 合并即得 (12.3)。证毕。

**解释边界。** 在固定有限 gap 的模型中，得到通常的对数增长；但一般 arriving 实例中，早期很小的正 gap 可能让 \(\gamma\) 极小。这不是完整实例复杂度，不是 Lai–Robbins 常数最优，也没有证明相对于所有合理强基线的逐实例优势。[W7] 已在静态指数族给出同时 minimax 与渐近最优的结果，不能把“存在两个上界取最小”本身当作全新的目标。

### 12.1 确定性奖励的更强上界

**命题 4。** 若每条臂奖励恒等于其均值，MC-MOSS 路径上满足

\[
R_T\le\sum_{i\in\mathcal B_T}
\left[1+\frac{2\log(eT)}{\gamma_i}\right].
\tag{12.4}
\]

**证明。** 已观察臂的经验均值精确等于真值，当前最佳指数不小于 \(B_t\)。若选中已观察次优臂，则
\(\Delta_i(t)\le b_i(t)\le\sqrt{\log(eT)/N_i(t-1)}\)。于是其正 regret 选择的选前计数不超过 \(\log(eT)/\gamma_i^2\)，全局计数不重复。逐项求和与一次初始化计费给出结论。证毕。

确定性奖励是主模型的合法子类。这条上界并不利用“奖励确定”作为算法的已知条件；只是对同一算法作事后评价。

---

## 13. 一个严格算法分离：冷重启会反复支付旧臂的探索成本

令 \(\pi^{\rm cold}\) 使用第 4 节相同的时钟重置日程、相同 \(d_j\)、相同指数和平局规则，唯一差别是在每次时钟重置时清空全部旧臂统计量。其局部证明使用新奖励流，仍有定理 1 的谱上界。所以以下比较是在两个都具备谱最优保证的策略之间进行。

**定理 9（历史保留与冷重启的实例阶分离）。** 存在一个确定性奖励、固定 gap 的日程族，使

\[
R_T(\pi^{\rm MC})=O(\log T),\qquad
R_T(\pi^{\rm cold})=\Omega((\log T)^2).
\tag{13.1}
\]

两条策略仅有是否清空历史的差异。

**构造与证明。** 取整数 \(m\ge1\)，令
\(h=2^{16m}\)、\(T=mh\)。第一轮有两条臂，均值分别为 \(1/2\) 和 \(1/4\)。对 \(j=1,\ldots,m-1\)，在 \(jh+1\) 加入 \(2^{j-1}\) 条均值 \(1/2\) 的新臂，所有奖励确定。全程唯一坏臂是初始均值 \(1/4\) 的臂，gap 为 \(1/4\)。

第 \(j\) 个段（从 0 编号）的竞争数为 \(c_j=2^j\)，\(d_j=2^{j+1}\)，每段长度恰为 \(h\)。对 MC-MOSS，坏臂被选择且已有 \(n\ge1\) 个全局样本时，其指数必须至少为 \(1/2\)，所以

\[
\frac14\le\sqrt{\frac{\log_+(s/(d_j n))}{n}}
\le\sqrt{\frac{\log T}{n}}.
\]

故坏臂终身拉取次数不超过 \(1+16\log T\)，从而

\[
R_T(\pi^{\rm MC})\le\frac14+4\log T.
\tag{13.2}
\]

对冷重启，固定任一段，令 \(q=\lfloor\log h\rfloor\)。假设此段结束时坏臂被拉少于 \(q\) 次。在后半段 \(s\ge h/2\) 内，若坏臂仍零样本，其指数为无穷大；若有 \(1\le n<q\) 个样本，则

\[
\frac{\log(s/(d_j n))}{n}
\ge\frac{\log[h/(2d_j\log h)]}{\log h}
\ge\frac12.
\tag{13.3}
\]

最后一步使用 \(d_j\le2^m\)、\(\log h=16m\log2\)，因此
\(2d_j\log h\le\sqrt h\)，对全部 \(m\ge1\) 成立。

坏臂指数于是至少 \(1/4+1/\sqrt2>0.95\)。另一方面，任何好臂只要已经拥有至少 \(\lceil16\log h\rceil\) 个段内样本，其指数至多
\(1/2+1/4=0.75\)。所以在坏臂样本仍不足 \(q\) 时，后半段不可能选择已经达到该门槛的好臂。

这限制后半段总选择次数不超过

\[
K_j\lceil16\log h\rceil+q
\le273m2^m<h/2.
\tag{13.4}
\]

其中 \(K_j=2^j+1\le2^m\)，并使用 \(\log h\le16m\)；最后的不等式由 \(m\le2^{m-1}\) 和 \(273<2^{14}\) 得到。这与后半段有 \(h/2\) 次选择矛盾。因此每段坏臂都至少被拉 \(q\) 次，

\[
R_T(\pi^{\rm cold})\ge\frac m4\lfloor\log h\rfloor.
\tag{13.5}
\]

由于 \(\log T=16m\log2+\log m=\Theta(m)\)，(13.2)、(13.5) 给出 (13.1)。证毕。

**这个分离证明什么、不证明什么。** 它证明达到相同 minimax 谱保证不等于具有相同实例效率，清空旧证据确实可能增加一个对数因子。它不证明 MC-MOSS 支配 AUER、全历史 UCB 或所有全历史 G-MOSS；这些策略同样可能避免重复采样。它也不是所有算法都必须付 \((\log T)^2\) 的信息论下界。

---

## 14. 可安全组合的扩展及其限制

### 14.1 一个较弱的时间一致概率界

**命题 5（同一策略的时间一致包络）。** 对固定无限到达路径、每个固定奖励环境和 \(0<\delta<1\)，MC-MOSS 满足

\[
\Pr\left\{\forall T\ge1:\
R_T\le\min\left[T,\frac{5000}{\delta}\mathscr C_T
(1+\log_2\mathscr C_T)^2\right]\right\}\ge1-\delta,
\tag{14.1}
\]

其中 \(\mathscr C_T=0\) 时第二项按 0 定义。非零时 \(\mathscr C_T\ge1\)，故对数没有零点问题。

**证明。** 若从未出现竞争臂，结论平凡。否则 (10.3) 说明 \(\mathscr C_T\to\infty\)，(10.2) 保证它非减。对每个 \(m\ge0\)，设 \(t_m\) 为满足 \(\mathscr C_t<2^{m+1}\) 的最后一个时刻；若该集合为空，不使用该指标。\(t_m\) 是由日程确定的有限终点，不是奖励依赖停时。由 (7.4)，
\(\mathbb ER_{t_m}\le1200\,2^{m+1}\)。令
\(\delta_m=\delta/[2(m+1)^2]\)，则 \(\sum_m\delta_m<\delta\)。Markov 和并集界使概率至少 \(1-\delta\) 时对全部这些 \(m\)，

\[
R_{t_m}\le\frac{2400\,2^{m+1}(m+1)^2}{\delta}.
\]

若 \(2^m\le\mathscr C_T<2^{m+1}\)，则 \(T\le t_m\) 且累计 regret 非减，所以

\[
R_T\le\frac{4800}{\delta}\mathscr C_T
(1+\log_2\mathscr C_T)^2.
\]

与 \(R_T\le T\) 合并，放宽常数得到 (14.1)。证毕。

这是从期望风险与单调几何得到的通用包络，不是最优 \(\delta\) 依赖或最优时间一致对数。它与主定理的逐确定终点量词明确分开。

### 14.2 任意可预测的插入采样

**命题 6（观测共享下的插入稳定性）。** 在保持物理到达时钟和全部历史统计量的条件下，允许策略在一个由选前信息决定的时刻集合 \(\mathcal I_T\) 上，用任意合法选择替代 MC-MOSS 的选择；其他时刻使用 (4.2)。则

\[
\boxed{\mathbb ER_T\le
\min\left\{T,300\mathscr S_T+
\mathbb E\sum_{t\in\mathcal I_T}\Delta_{I_t}(t)\right\}.}
\tag{14.2}
\]

**证明。** 对普通时刻，最大指数不等式不变。引理 1 针对全部潜在样本前缀；引理 2、3 针对非重复计数，插入观察只使普通时刻的计数跳过某些整数。故引理 4 对普通动作子序列仍以段的完整物理长度计费。第 5 节的时钟段由到达决定，没有改变。将插入动作实际发生的损失另加即可。证毕。

这里没有比较两条不同策略在同一随机轨迹下的 regret 差，也没有假设插入采样之后其余动作保持不变。式 (14.2) 只是可组合保证，不表示认证或其他额外目标能够免费实现。

### 14.3 已知奖励上界的安全裁剪

**命题 7（可避免强制探测的裁剪版本）。** 将已观察臂的指数改为 \(\min\{1,U_i(t)\}\)，未观察臂指数改为 1，按同一固定顺序打破平局，其余规则不变。记该策略为 \(\pi^{\rm MC,clip}\)。它同样满足定理 1、定理 8 和命题 4 的上界。

**证明。** 若当前最优臂已观察，其裁剪指数至少为 \(B_t-Z\)，因为 \(B_t\le1\)；若仍未观察，其指数为 1，同样至少为 \(B_t-Z\)。若本轮选择未观察臂，仍归入单次初始化；若选择已观察臂，其裁剪指数不超过原始 \(\widehat\mu+b\)。因此 (4.4) 对所有这类选择仍成立，不再需要“最佳臂未观察必选未观察臂”。其余非重复计数、gap 分类和时钟计费证明保持有效。证毕。

一个严格但简单的实例区别是：初始唯一臂的确定奖励为 1，之后每轮加入一条奖励为 0 的臂。原 MC-MOSS 因每轮都有一个未观察臂，累计 regret 为 \(T-1\)；裁剪版从第一轮观察到 1 后总是选择最早的初始臂，regret 恰为 0。两者仍有同一 uniform minimax 保证，因为该日程 \(K_t=t\) 的最坏风险本来是线性的。

这个例子同时提醒：谱最优不等于每个具体实例都好，保留历史也不自动实现全部实例适应。裁剪是利用已知取值范围的标准设计，不以这个简单改动作为主要创新。

### 14.4 独立随机到达与未来信息的价格

**推论 7.4（独立随机日程上界）。** 若到达路径随机但独立于奖励流和策略随机种子，并且每个有限时刻的可用集几乎处处有限非空，则对每个固定奖励分布环境，

\[
\mathbb ER_T(\pi^{\rm MC})
\le\mathbb E\min\{T,300\mathscr S_T(\tau)\}
\le\min\{T,1200\mathbb E\mathscr C_T(\tau)\}.
\tag{14.3}
\]

**证明。** 条件于完整外生日程应用定理 1，再取期望；该条件化不改变潜在奖励流的分布。证毕。

不据此宣称随机日程的 minimax 下界为 \(c\mathbb E\mathscr S_T\)：逐日程下界的困难均值可以依赖日程，而随机日程模型可能要求奖励环境在日程随机化之前固定，\(\sup_P\) 与期望不能随意交换。

**推论 7.5（不知道终点与未来日程只付常数因子）。** 对每个固定日程和终点，MC-MOSS 风险至多为知道终点和完整日程的 minimax 值的一个绝对常数倍。直接由定理 1，非退化情形可取 \(3\times10^6\)，常数未优化。无竞争臂时两者均为零。

这个推论表达的是未知均值学习问题中未来到达信息的价格；它不是与“知道所有均值的 oracle”比较，后者 regret 为零。

---

## 15. 文献审计与理论成果的创新性评估

### 15.1 核查范围和最近邻

检索日期为 2026-10-12。使用原作者公开论文、出版社及 PMLR/JMLR 页面，关键词包含 stochastic sleeping、best-awake regret、arriving/ballooning arms、arrival schedule minimax、lifetime、temporal geometry、MOSS、anytime、nonuniform exploration。检索到的本项目 2026 年公开预印本不作为独立前作来支持新颖性；第三方自动摘要不作为算法或定理的归属依据。

| 最近邻 | 已有工作实际覆盖的内容 | 本文与其不同的理论目标／需避免的过度声称 |
|---|---|---|
| [W1] Kleinberg–Niculescu-Mizil–Sharma | 随机平稳奖励的 sleeping、最佳排序比较器、AUER；本文查阅了模型和主要随机奖励结果 | 承认 arriving 是单调可用子类；主增量是每个固定到达日程的常数精度复杂度，而非发明比较器 |
| [W4] Ghalme 等，Ballooning MAB | 增长臂集与最佳当前可用臂 regret；基于到达分布的接纳及次线性保证；本文核查模型和主要算法机制 | 本文允许任意确定外生日程与有限 batch，精确分解多尺度难度；不把到达本身当作新模型 |
| [W2,W3] MOSS、Anytime MOSS | 静态随机 bandit 的无对数 minimax 和未知终点保证 | MOSS 指数及其最大偏差控制属于基础；新内容是全历史有效的局部内核、因果时钟与到达谱的匹配 |
| [W6] Lattimore | 非均匀最坏 regret 分配及 Pareto 前沿；已查作者摘要并对照上轮涉及的非均匀探索机制 | 不宣称 rank bonus 或探索不对称本身新颖；本轮统一容量指数不再依赖 rank bonus |
| [W7] Ménard–Garivier | 静态指数族的 kl-UCB++ 同时 minimax 与渐近最优 | 本文 gap 上界不是新的静态双重最优理论，也没有证明 arriving 实例的 Lai–Robbins 常数 |
| [W5] Kaufmann–Cappé–Garivier | 自适应 bandit 换测度与识别复杂度下界 | 本文 KL 原理沿用；真正需要新组织的是多个尺度能否在一个合法、受限均值范围的先验里兼容相加 |
| [W8] Nguyen–Mehta | 对抗性损失与可用集下的 per-action sleeping regret | 与这里的平稳、最佳可用臂及逐固定到达日程风险不是同一量词，不作直接速率支配比较 |

本轮未发现已核查文献给出本文的完整 \(\mathscr S_T\)／\(\mathscr C_T\) 常数精度刻画及其全部等价关系。但这不是穷尽性“首次”证明；尤其尚未系统穷尽所有结构化 bandit、资源分配及 sleeping 的等价表述。正式投稿前应继续沿最近邻的引用及被引结果做定理级排查。

### 15.2 使用指定量表后的逐项评价

按照用户指定仓库的量表，先定层级再评分：第二级为 4.0–7.9 的实质方法／理论创新；第三级为 1.0–3.9 的适配；第一级 8.0 以上需要基础概念或研究范式改变。以下是**当前书面理论成果的评价**，不是把未完成的后续愿望记入分数；正确性核验程度与新颖性判断分别说明。

| 成果组 | 当前定位 | 主要依据及升档所缺内容 |
|---|---|---|
| 定理 1：精确谱 minimax、共同先验下界、因果未知终点实现 | **第二级，6.8/10** | 解决总臂数和单一固定点都无法精确表达的时间尺度累积，且上下界匹配；高于局部新界。尚不是一般 sleeping 的统一复杂度理论 |
| 定理 4：\(\Gamma\asymp\ell_2\)，风险 \(\asymp\ell_1\)，有效尺度数与最大分离 | **第二级，6.3/10** | 给出可复用的机制解释，识别哪些对数属于真实难度；该结论建立在本项目先前固定点定义上，不应重复计算为独立领域体系 |
| 引理 4、定理 9：只重置时钟、全历史控制及冷重启阶分离 | **第二级，5.5/10** | 消除到达谱可达性中的数据重置并给出真实实例收益；不是首次复用历史，也尚未证明最优实例适应 |
| 定理 2、3、6：无网格容量、精确对偶、可计算证书与到达稳定性 | **第二级，5.4/10** | 将风险阶变成可计算、可扰动分析的日程函数；凸包、凹分配和对偶技术本身是标准方法 |
| 定理 5：常数概率谱下界 | **第二级，4.2/10** | 通过有界代理保留共同先验，把期望困难升级为非罕见困难；是有限范围的实质强化，不是完整尾理论 |
| 定理 8：同一策略的随机 gap 上界 | **第三级，3.3/10** | 主要是标准 MOSS 偏差分解与全局非重复计数的适配；未达到实例最优性的核心目标 |
| 定理 7 的 \(K_t=o(t)\) 边界 | **不作为本轮新发现独立计分** | Part I 已经建立；本轮价值是由同一精确谱策略实现，不重复收取创新分 |
| 代表增长日程、弱时间一致包络、插入采样、裁剪与随机日程上界 | **第三级，2.5–3.2/10** | 有实际解释和组合价值，但主要来自已证定理和标准工具的推论 |
| Hoeffding、KL、Pinsker、Markov、基础凸对偶 | **标准工具，不独立计分** | 写出证明是可靠性要求，不意味着新颖性 |

**总体评价：第二级，6.9/10，理论与方法原则贡献；当前理论整合稿评价。** 总体分不由各项相加或平均，而由“可计算的精确到达复杂度 + 无信息重置的因果实现 + 固定点差距的机制解释”这条主链决定。相对 6.0 锚点，本稿给出了超出单一界限的相互衔接结论；相对 7.0 锚点，仍缺更广的可用性模式或更成熟的实例自适应统一原则，且尚未完成独立定理级新颖性核查。

没有给 8.0 以上的评价，因为目前仍沿用标准 regret、观测和 minimax 基础问题观；新的复杂度与证明原则虽有内容，但不等于基础范式改变。也不把上一轮一般 sleeping 方向的 7.4 条件性潜力当作本轮已经实现的成果。

**判断置信度：中。** 原始最近邻的模型、目标和关键保证已核对，核心差别明确；但不能据有限检索排除等价前作。**证明核验状态：本轮逐项推导、反例攻击和诊断通过，未经过独立同行复核或形式化验证。** 小数评分是研究定位判断，不是客观测量精度或录用概率。

### 15.3 最强合理替代解释与主张约束

最强的替代解释不是“静态算法完全不能用于到达”，而是：“某个自然全历史 MOSS 或 AUER 经过更好的分析，可能也达到同样的谱。”本文没有排除这种可能；若它成立，复杂度定理仍有价值，但不应坚持新算法具有独占优势。

本文能够主张的算法优势仅包括定理 9 和命题 7 所说明的明确配对比较。它不能据此宣称实际全面优于 AUER、全历史 G-MOSS、任何 KL 方法或原 UCB-AA。正式实验仍应使用这些强基线，并分别比较日程最坏族、固定 gap 实例与历史复用的消融。

---

## 16. 证明依赖、反例审查与计算记录

### 16.1 证明义务的闭合关系

| 目标 | 实际使用的已展开输入 | 核查中的关键风险 |
|---|---|---|
| 全历史局部内核 | 引理 1–3 + 确定的真实最优标签 + 非重复总计数 | 没有把旧数据条件化后当成 fresh samples |
| 全日程上界 | 局部内核 + 延后谱比较 + 竞争数翻倍几何 | 巨大 batch 先进入新段；尾部容量共同截断 |
| 多尺度下界 | 单臂检验 + 可兼容尺度抽取 + 单一乘积先验 | 有界 benchmark 总增长；未来参照不泄露旧答案；全部提前观察计入 KL |
| 容量与谱等价 | 完整 suffix 可行性 + 明确分数配置 | 短寿命 arm 的重复收费和亚一次观测的平方根失真 |
| 凸包与对偶 | 可行斜率 + 超梯度 + 紧约束乘子 | 重复寿命、折点 1、非唯一最优解 |
| 固定点与有效尺度 | 截断平方和的两个方向 | \(\Gamma=T\)、\(Q>T\)、单臂及整数取整 |
| 概率下界 | 有界代理而非仅期望下界 | 不由 \(\mathbb ER\ge cS\) 直接推出常数概率 |
| gap 上界 | 三类划分 + 截断偏差尾和 + 全局计数 | 比较器随到达改变；首次成为次优的旧最佳臂 |
| 冷重启分离 | 同一指数、同一时钟、确定性样本计数 | 下界作用于真实拉取次数，不是某个上界表达式 |
| 学习边界 | 逐前缀谱界 + 延长到两倍终点 | uniform 与 pointwise 的量词不混用 |

研究中采用不同数学机制分别推进：直接最大偏差／计数上界、共同先验的信息下界、分数 occupancy 与凸对偶、显式反例及算法消融。以上是最终证明结构，不以探索过程或数值一致代替证明。

### 16.2 实际完成的诊断

代码与结果位于配套 `temporal_geometry_research` 文件夹。随机种子为 `20261012`。

**日程几何。** 穷举 \(T\le6\)、竞争臂数不超过 6 的寿命多重集，共 1,715 个；另生成 10,000 个随机日程，含多尺度、空竞争集和批量到达。总共进行了 11,715 次容量原始／对偶比较、时钟段计费比较和可兼容尺度选择比较。另有 10,000 次最大抖动 Lipschitz 与一步时间推进检查。凸包斜率比较及样本前缀可行性使用整数／有理数；目标与对偶值使用浮点计算。最大观测相对原始—对偶差为约 \(3.15\times10^{-16}\)。

**策略诊断。** 14 条确定性轨迹、24 条 Bernoulli 完整轨迹，以及 24 次截断前缀复跑，主诊断合计 **4,105,304 个实际策略步骤**，不包含编译预热。另对不接收终点和真实均值的在线 API 完成 2,001 个步骤，核查输入校验及命题 7 的裁剪例子；这部分单独记录，不混入前述主诊断计数。前缀复跑逐动作核查：同一算法和随机种子，不同模拟终点的公共前缀一致。选择规则仅使用已到达集合、历史观测和局部时钟；模拟器中的真实均值只用于生成奖励与核算 regret。

确定性有限样本诊断使用每段 \(h=65536\)、段数 \(m=1,\ldots,7\)，是定理 9 机制的有限版本，**不是**将定理中的 \(h=2^{16m}\) 原样运行到巨大终点。结果如下：

| 段数 | 保留历史 regret | 冷重启 regret |
|---:|---:|---:|
| 1 | 23.50 | 23.50 |
| 2 | 23.50 | 44.75 |
| 3 | 23.50 | 63.75 |
| 4 | 23.50 | 80.50 |
| 5 | 23.50 | 95.00 |
| 6 | 23.50 | 107.25 |
| 7 | 23.50 | 117.50 |

这些运行只用于发现时钟、样本重置、计数和公式转写错误。没有估计定理的覆盖率，没有做完整 AUER/G-MOSS/UCB-AA 的多次重复统计比较，也没有用数值最大比率代替解析最优常数。穷举仅覆盖明确的有限集合，不构成对任意日程的穷举证明。

### 16.3 审计后仍需保留的边界

1. 不知 \(T\) 的逐终点期望保证已证；最优的小 \(\delta\) 尾界与最优时间一致界未证。(14.1) 是较弱包络。
2. 不依赖 gap 正则性的谱 minimax 已证；全部实例上的历史信息最优利用未证。(12.3) 可能保守。
3. 外生到达下证明成立；奖励依赖到达或由奖励触发的时钟重置没有由本稿自动覆盖。
4. 一般 sleeping 的信息—竞争时间顺序复杂度未完成，不将其并入本稿的已证主定理。
5. 不声称得到了精确的 minimax 渐近常数；当前是绝对常数因子 matching。
6. 所有下界对合法环境族、策略及量词成立；不存在单一实例上无策略要求的非零 \(\inf_\pi\mathcal R_T(\pi,\mu)\) 下界。
7. 配套冷重启分离不等于对所有强基线的普遍改进；可行算法可以不唯一。

---

## 17. 新论文可直接采用的理论主线

建议正文将主要贡献集中为三个互相衔接的结论，而不是并排列出所有辅助命题。

**第一，精确到达复杂度。** 每个固定单调到达路径的最优风险由多尺度谱 \(\mathscr S_T\) 描述；一个有界均值范围内的共同环境族证明各尺度困难能兼容相加。无网格容量 \(\mathscr C_T\) 给出可计算的等价表述。

**第二，因果且保留历史的可达性。** 不需要知道终点和未来臂数，不需要清空旧样本。只在竞争数翻倍时重置探索时钟，即可由同一策略达到谱界，并恢复全部 \(K_t=o(t)\) 路径上的 uniform 学习边界。

**第三，解释原粗复杂度与实例效率。** 固定点对应平方谱，真实风险对应一阶谱；有效尺度数解释必要的 \(\sqrt{\log T}\) 分离。历史保留则在不牺牲 minimax 安全的同时，避免冷重启在固定 gap 实例上重复付费。

正文可以保留定理 1、定理 2／4、定理 7 和定理 9 的主要表述；完整集中、凸包对偶、尾界、稳定性与 gap 分解进入补充材料。原 UCB-AA 可以保留为筛选型基线，不需要把本稿的新算法性质归给它。

**可采用的英文核心陈述：**

> We characterize the schedule-dependent minimax regret of stochastic bandits with persistently arriving arms up to universal constants. The optimal rate is an additive multiscale functional of the arrival schedule, equivalently a concave sampling-capacity functional over feasible occupancies. A single horizon-free policy attains this rate while retaining all historical observations. The characterization identifies the effective number of difficulty scales, explains the failure of a single lifetime fixed point to capture the exact rate, and yields the precise boundary for uniform no-regret learning.

这段陈述对应已写出的定理；不加入“首次”、独占算法优势、一般 sleeping 最优性或完整实例最优性。

---

## 18. 可核验来源与使用协议

以下 URL 用于离线 Markdown 的来源定位。正文中的 [W#] 指向对应项；这些文献支持背景和标准工具的归属，不负责证明本文新增命题。

**[W1]** Kleinberg, R., Niculescu-Mizil, A., and Sharma, Y. *Regret Bounds for Sleeping Experts and Bandits*. COLT 2008 会议版；后发表于 *Machine Learning* 80, 245–272 (2010)。本轮查阅作者会议全文的模型与随机奖励章节。  
https://www.cs.cornell.edu/~rdk/papers/colt08.pdf

**[W2]** Audibert, J.-Y., and Bubeck, S. *Minimax Policies for Adversarial and Stochastic Bandits*. COLT 2009。  
https://www.microsoft.com/en-us/research/publication/minimax-policies-adversarial-stochastic-bandits/

**[W3]** Degenne, R., and Perchet, V. *Anytime optimal algorithms in stochastic multi-armed bandits*. ICML 2016, PMLR 48。  
https://proceedings.mlr.press/v48/degenne16.html

**[W4]** Ghalme, G., Dhamal, S., Jain, S., Gujar, S., and Narahari, Y. *Ballooning multi-armed bandits*. *Artificial Intelligence* 296, 103485 (2021)。  
https://research.chalmers.se/publication/522732/file/522732_Fulltext.pdf

**[W5]** Kaufmann, E., Cappé, O., and Garivier, A. *On the Complexity of Best-Arm Identification in Multi-Armed Bandit Models*. *JMLR* 17(1), 1–42 (2016)。  
https://jmlr.org/papers/v17/kaufman16a.html

**[W6]** Lattimore, T. *The Pareto Regret Frontier for Bandits*. NeurIPS 2015。  
https://arxiv.org/abs/1511.00048

**[W7]** Ménard, P., and Garivier, A. *A minimax and asymptotically optimal algorithm for stochastic bandits*. ALT 2017。本轮核查原作者摘要及算法目标，不调用其定理作为本稿上界的输入。  
https://arxiv.org/abs/1702.07211

**[W8]** Nguyen, Q. M., and Mehta, N. *Near-optimal Per-Action Regret Bounds for Sleeping Bandits*. AISTATS 2024, PMLR 238, 2827–2835。  
https://proceedings.mlr.press/v238/nguyen24d.html

**项目来源。** 上一轮谱研究稿 `MAB-AA_发散重构与创新性评估_多尺度到达谱_2026-10-12.md`；`Part-I-Arrival-Minimax-闭合证明.md`；原始 `mab_aa_main.pdf`。谱定理和分离族在上轮稿中已有书面证明，本轮复核、简化并扩展，不能把所有结果重新称为本轮首次发现。

**证明协议。** 已读取并使用以下仓库的 `SKILL.md`、`references/proof-protocol.md`、`references/domain-routes.md`、`references/adversarial-audit.md`：  
https://github.com/zdacongming-glitch/prove-stat-ml-probability-theorems

**评估协议。** 已读取并使用以下仓库的 `SKILL.md` 与 `references/rubric.md`；本轮仅做理论创新性评价，不将其扩展为对完整论文的四维审稿：  
https://github.com/zdacongming-glitch/statistical-innovation-assessment

**最后核查意见。** 当前可作为主稿基础的是常数精度谱刻画、全历史时钟算法和固定点—有效尺度关系。最有价值的下一次独立审核应集中于第 6 节共同先验的可兼容性，以及第 4 节全历史无条件偏差控制；它们决定主结论，而不是新增实验数量或常数小幅改动。
