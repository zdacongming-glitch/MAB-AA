# 前沿研究：因果信息限制、任意完成数量下界与中间预算匹配

日期：2026-10-16。性质：本轮新增理论记录；完整书面证明与内部审查，不代表独立同行核验。

**总状态：部分完成。** 本文没有证明一个实用算法在任意到达、未知未来、全部面积预算下达到完整联合前沿。已经完成的是：一个不可混用的信息基准分离；任意部分恢复数量的下界；多次更新族的一整段中间面积预算上的匹配；以及有限信息模型的精确前沿求解表述。后两者的范围分别列明。

## 0. 固定目标与来源边界

固定确定的永久到达日程，$A_t=\{i:\tau_i\le t\}$ 非空且有限。独立臂流均为 iid $[0,1]$ 奖励，均值 $\mu_i$。选择只依赖已发生的到达、过去观测与独立随机化，每轮一拉，观察后报告。

\[
 B_t=\max_{i\in A_t}\mu_i,\quad
 \Delta_i(t)=B_t-\mu_i,\quad
 G_t^\varepsilon=\{i:\Delta_i(t)\le\varepsilon\},\quad
 R_T=\sum_{t\le T}\Delta_{I_t}(t).
\]
报告 $(P_t,N_t,V_t)$ 划分全部 $A_t$。
\[
 E_{\rm lab}=\{\forall t:P_t\subseteq G_t^\varepsilon\subseteq A_t\setminus N_t\},
 \qquad
 \mathcal U_T(\eta)=\sum_{t\le T}\sum_{i\in A_t}
 1\{i\in V_t,\ |\Delta_i(t)-\varepsilon|>\eta\}.
\]
联合要求不变：$E R_T\le r$，且 $P(E_{\rm lab},\mathcal U_T\le a)\ge1-\delta$。这是**期望 regret 与高概率面积**，不是期望加权和。全过程正确性也不是每臂分别使用同一个 $\delta$。

来源：`manuscript(2).pdf` §5.1；`supplement(2).pdf` Notation and scope。已有的多次更新族、两个端点与 CP 上界来自该稿 §7、Supplement S6–S8；本轮不重新计为新增结果。旧 CCP 的可观测指数差界来自 `maintenance_algorithm_search_2026-10-16/theory.md`；谱 minimax 刻画来自独立的 temporal-geometry 工作。

### 两种不同的“前沿”

- $\mathfrak R^{\rm sch}_{T,\tau}(a;\Theta)$：对指定日程 $\tau$ 分别优化策略；比较者可以知道 $T,\tau$，但不知道实际奖励环境。要求策略在完整奖励模型上可靠，在性能族 $\Theta$ 上满足面积条件。
- $\mathfrak R^{\rm causal}_{T,\mathcal T}(a;\Theta)$：同一策略面对日程类 $\mathcal T$，只能看已发生到达，同时在每条日程与每个环境上满足面积条件；优化最坏 regret。

两种量的策略信息不同。定理 1 证明，不存在把第一种每条日程单独最优值，全部同时提升为一个未知未来策略的常数因子逐日程保证。它**不**否定第二种因果 minimax 问题存在最优解。

## 1. 基础引理

### 引理 A：可靠检查点与可修正报告

若在观察臂 $i$ 之前固定 $q_i$，则 $q_i$ 个观测的均值 $\hat\mu_i$ 满足
\[
 P(|\hat\mu_i-\mu_i|>\rho/2)\le2e^{-q_i\rho^2/2}.
\]
因此 $q_i=\lceil2\rho^{-2}\log(4i(i+1)/\delta)\rceil$ 的总失败率至多 $\delta/2$。这是 Hoeffding 不等式；其 bounded-stream 证明与当前补充材料 S3 相同。

**可预测激活版本。** 在一个全历史停止时刻，根据当时历史选择一条臂，再为它的**后续未观察奖励**预先指定 $q$，上述条件 Hoeffding 界仍成立。原因是下一次尚未揭示的奖励流后缀，在给定截至激活时的观测历史时仍保持原 iid 法则。即使激活时间和臂身份是数据依赖的，未来后缀没有被看过。可先在有界停止时证明，再按激活时刻取条件期望；未发生的激活无失败事件。

设所有被使用的非空区间共同覆盖真均值。以 $\underline B=\max_i\ell_i$、$\overline B=\max_i u_i$，报告
\[
 P=\{i:\ell_i\ge\overline B-\varepsilon\},\quad
 N=\{i:u_i<\underline B-\varepsilon\},\quad
 V=A\setminus(P\cup N)
\]
即正确。区间通过相交收缩，新臂初始区间为 $[0,1]$。若交集为空，报告全未决并继续定义收益选择；不会凭空生成标签。

### 引理 B：自适应两环境 KL

两个 Bernoulli 环境只在臂 $i$ 上有参数 $p,q$，对确定终点 $t$，
\[
 D(P_p^{H_t}\|P_q^{H_t})=E_pN_i(t)\operatorname{kl}(p,q).
\]
对可测事件 $F$，上式不小于 $\operatorname{kl}(P_pF,P_qF)$。证明分解历史条件似然，策略动作核抵消，再取迭代期望；对事件划分应用 log-sum 不等式。对 bounded 停止时刻用停止后的空符号补齐也成立。参见 Kaufmann–Cappé–Garivier (2016)，以及本项目补充材料 S3 的自包含版本。

### 引理 C：全历史 UCB 中插入有限服务

普通轮选择所有可用臂中最大
\[
 \hat\mu_i(N_i(t-1))+\sqrt{3\log(2t)/N_i(t-1)}
\]
者，零计数指数为无穷。任意可预测服务轮可替换这一选择，观测仍更新相同终身统计量。固定时刻 $t$，至多 $t$ 个已暴露奖励流、各至多 $t$ 个潜在前缀。Hoeffding 与首次暴露前的独立性给出坏轮概率至多 $1/(32t^4)$。好普通轮选择的正 gap 满足
\[
 \Delta_i(t)\le2\sqrt{3\log(2t)/N_i(t-1)}.
\]
故若 $\gamma_i$ 是该臂最小正 gap、$D_i$ 是最大 gap，其好普通轮只可能使用 $N_i(t-1)\le12\log(2T)/\gamma_i^2$ 的不同计数。计数不会因插入服务重复。服务成本另按实际次数记账，坏轮总期望损失小于 1。该论证不条件于报告事件，无 $\delta T$ 遗漏。以下上界只使用这个明确性质。

## 2. 定理 1：未知任务失效时间阻止逐日程前沿的同时常数逼近

**完整证明。** 固定 $\varepsilon=1/8$、$v=1/32$、$0<\delta\le1/16$。令 $0<d\le1/1024$ 并最终趋于零，$\eta=d/2$。三个 Bernoulli 臂的均值为
\[
 \mu_0=1/2,\qquad \mu_1=1/2-\varepsilon+\sigma d,
 \qquad\mu_2=1/2+v,\quad \sigma\in\{-1,+1\}.
\]
前两个臂在时刻 1 到达。记
\[
 Q_f=\left\lceil32d^{-2}\log(24/\delta)\right\rceil,
 \quad h=16Q_f,
\]
\[
 L_d=\frac{\operatorname{kl}(1-\delta,\delta)}
 {\operatorname{kl}(1/2-\varepsilon-d,\ 1/2-\varepsilon+d)},
 \quad w=\lfloor L_d/2\rfloor,
 \quad a=h+w,\quad T=2(a+1).
\]
定义两个日程：$\tau^{\rm early}_2=h+1$，$\tau^{\rm late}_2=T$。它们具有相同 $T,a,\varepsilon,\eta,\delta$，最终臂数都是 3，且时刻 $h$ 前完全相同。

任何同一非预知策略，只要在 late 日程的两个符号环境上满足联合面积要求，就必然在 early 日程的负号环境上满足
\[
 E_{-,\rm early}R_T\ge
 \varepsilon(L_d/2-1)=\Omega(d^{-2}).\tag{2.1}
\]
然而对 early 日程单独优化的完整奖励模型可靠策略，有
\[
 \mathfrak R^{\rm sch}_{T,\tau^{\rm early}}(a;\Theta)
 =O_{\varepsilon,v,\delta}(\log(1/d)).\tag{2.2}
\]
两个日程上的面积要求分别都可行。因此不存在一个普适常数 $C$ 和同一未知未来策略，逐日程同时达到 $C\mathfrak R^{\rm sch}_{T,\tau}(a;\Theta)$。这个分离即使允许策略知道 $T,a$、两个可能日程的集合、最终臂数与性能族，也成立；它只是不知道哪个日程会实现。

**证明。** 在 late 日程，臂 1 至时刻 $t_0=a+1<T$ 的资格就是符号，且边界距离 $d>\eta$。若到 $t_0$ 仍从未对它作确定报告，它单独贡献 $a+1$ 面积。因此标签正确与面积成功迫使它在 $t_0$ 前正确报告。

令 $F$ 为截至 $t_0$ 至少一次把臂 1 报告为非近优。负号环境中 $P_-F\ge1-\delta$，正号环境中 $P_+F\le\delta$。由引理 B，
\[
 E_{-,\rm late}N_1(t_0)\ge L_d.
\]
从 $h+1$ 至 $t_0$ 只有 $w+1$ 个观测槽，因此
\[
 E_{-,\rm late}N_1(h)\ge L_d-w-1\ge L_d/2-1.
\]
early 与 late 在 $h$ 前拥有同一到达与奖励历史法则，同一策略的 $N_1(h)$ 分布相同。此时每次拉臂 1 的 regret 为 $\varepsilon+d\ge\varepsilon$，得到 (2.1)。内部 Bernoulli 参数给出 $L_d\asymp_\delta d^{-2}$。

检验可行性与 (2.2)。对 late，固定精度 $\rho_f=d/4$ 的检查点策略，在前两个臂上每臂配额不超过 $Q_f$；偶数轮服务，最多 $4Q_f$ 轮完成。共同覆盖上全部旧臂可分类，早期面积不超过 $8Q_f$。最后一轮新臂最多增加 3，故对小 $d$ 总面积不超过 $8Q_f+3<a$。

对 early，使用同一形式但粗精度 $\rho_c=v/8$。三个臂的配额不超过常数
\[
 Q_c=\left\lceil128v^{-2}\log(48/\delta)\right\rceil,
\]
与 $d$ 无关。前两臂在 $4Q_c$ 轮内完成粗证据；初始参照可正认证，候选可继续未决。新参照在到达后 $2Q_c$ 轮内形成证据。因为 $d+2\rho_c<v$，其下界配合候选旧上界即可把候选判为非近优；两个参照均可正认证。面积由初始候选的 $h$、初始参照至多 $4Q_c$、更新后至多 $6Q_c$ 控制：
\[
 \mathcal U_T\le h+10Q_c.
\]
当 $d$ 足够小时，$w\ge10Q_c$，故满足相同预算 $a$。这是高概率面积，覆盖概率至少 $1-\delta/2$。

该粗策略的指定服务次数至多 $3Q_c$。普通全历史 UCB 的所有正 gap 均至少 $v$（候选 gap 更大），由引理 C，$ER_T\le3Q_c+O_v(\log T)$。又 $T\asymp_\delta d^{-2}$，得到 (2.2)。算法始终依据置信区间出报告，而非把性能族的已知均值当作标签，因此仍在完整 bounded 模型上可靠。证毕。

**不能推出的结论。** 本定理不否定在“共同面对两种日程”的因果 minimax 类中存在最优策略，也不否定在给定日程、已知终点的小模型中精确计算前沿。它否定的是同一个未知未来策略相对于每条日程分别优化比较者的普遍常数因子保证。

### 推论 1：固定 $\beta$ 的 CCP 不可能覆盖严格维护区间

在旧稿的规定重复更新族上固定 $J,M,\varepsilon,v,\delta$，$d\downarrow0$ 时 $T\asymp d^{-2}$、$K$ 固定，而快速面积预算要求 regret 为 $\Omega(d^{-2})$。谱保护算法若满足 $ER_T\le C\mathcal S_T$，则 $ER_T=O(\sqrt T)=O(d^{-1})$，不可能同时满足该快速预算。旧 CCP 的固定有限 $\beta$ 界正属于此类。按该保护式允许达到快速成本，至少需要 $\beta$ 随 $d^{-1}$ 量级增长，或改变预算机制。

这是旧下界与旧保护上界的直接推论，不单列为新机制突破；也不把相互冲突的两个上界误写成算法已同时实现。

## 3. 定理 2：任意部分完成数量的同时恢复下界

**完整证明。** 有 $m\ge1$ 个独立均匀符号，各坐标观测法则为 $P_i^+,P_i^-$，
\[
 0<\kappa:=\max_i\max\{D(P_i^+\|P_i^-),D(P_i^-\|P_i^+)\}<\infty.
\]
其他观测不编码这些符号。允许自适应交错采样、独立策略随机化以及有界停止时刻 $\tau$。报告数据依赖子集 $S$ 及各自符号；每个符号配置下任一报告错误的概率至多 $0<\delta\le1/16$。

若某个整数 $1\le s\le m$ 满足
\[
 \overline P(|S|\ge s)\ge1/2,
\]
则
\[
 \boxed{\overline E\sum_iN_i(\tau)\ge
 \frac{s}{48\kappa}\log\frac{s}{\delta}.}\tag{3.1}
\]
横线表示同一个独立符号乘积先验，先验仅是证明工具。

**证明。** 令 $L_i$ 为坐标正对负的观测对数似然比。完整停止历史中，采样、报告及停止核抵消；其似然对坐标分解，故后验仍分解，尽管随机采样次数不独立。最小后验符号错误为
\[
 e_i=(1+e^{|L_i|})^{-1}\in(0,1/2].
\]
实际报告即使不是 MAP，条件共同正确概率仍至多 $\prod_{i\in S}(1-e_i)$。所以
\[
 \overline E\left[1-\prod_{i\in S}(1-e_i)\right]\le\delta.
\]
由 Markov，概率至少 $3/4$ 时该乘积至少 $1-4\delta$，从而
\[
 \sum_{i\in S}e_i\le v_\delta:=-\log(1-4\delta)\le16\delta/3.
\]
与 $|S|\ge s$ 相交，概率至少 $1/4$。

定义
\[
 f(e)=(1-2e)\log((1-e)/e),\qquad 0<e\le1/2.
\]
它非负、递减、凸，而且
\[
 f''(e)=\frac1{e^2(1-e)^2}>0.
\]
条件于历史，$E(\sigma_iL_i\mid H)=f(e_i)$。另一方面，有界停止及有限双向 KL 给出
\[
 \overline E\sum_i f(e_i)=\overline E\sum_i\sigma_iL_i
 \le\kappa\overline E\sum_iN_i(\tau).
\]
这是直接使用非负的条件信息漂移，**不需要从 $\sum|L_i|$ 中减去全部 $m$**。

在上述相交事件上，$k=|S|\ge s$。由 Jensen 与递减性，
\[
 \sum_i f(e_i)\ge\sum_{i\in S}f(e_i)
 \ge k f(v_\delta/k)\ge s f(v_\delta/s).
\]
最后一步因为 $f\ge0$ 且 $k\mapsto f(v_\delta/k)$ 非减。
$v_\delta/s\le1/3$，因此
\[
 f(v_\delta/s)\ge\tfrac13\log\frac{s}{8\delta}
 \ge\tfrac1{12}\log\frac{s}{\delta}.
\]
第二步用 $s/\delta\ge16$。相交事件概率至少 $1/4$，结合信息漂移即得 (3.1)。边界 $e_i=0$ 可取极限；有限停止与双向 KL 使所用对数似然可积，不产生未控制无穷项。证毕。

**与旧引理的区别。** 旧稿 S5 主要定价至少恢复一半坐标，并在绝对似然推导中出现减去 $m$。这里允许任意 $s$，包括 $s\ll m$，这是中间面积预算所需要的接口。后验分解、KL 漂移和同时恢复的统计思想已有前作；新增的是适用于本轮选中子集的完整界及下面的成本连接。

## 4. 定理 3：重复更新族的任意面积预算下界

采用旧稿同类型、但暂不指定窗口长度的族：
\[
 J\ge1,\ M\ge\max\{2,J\},\quad0<\varepsilon\le1/8,\quad
 0<\delta\le1/16,\quad Jv\le\varepsilon/4,\quad0<d\le v/32,
 \quad\eta=d/2.
\]
令 $m=JM$、$K=J(M+1)+1$。第 $e=0,\ldots,J-1$ 批于 $1+eH$ 到达，包含参照 $b_e=1/2+ev$ 及 $M$ 条候选
\[
 \mu_{e,k}=b_e-\varepsilon+\sigma_{e,k}d.
\]
第 $J$ 批只到达最后参照，$T=(J+1)H$、$V=mH$。包括全部符号与批内排列；上界策略不知道参照身份。所有候选从出生起始终有 regret gap 至少 $\varepsilon-d\ge\varepsilon/2$。

**完整证明。** 对 $0\le a<V$ 定义
\[
 k(a)=\left\lceil\frac{V-a}{H}\right\rceil\in\{1,\ldots,m\}.
\]
则
\[
 \boxed{\mathfrak R_\Theta(a)\ge
 \frac{\varepsilon k(a)}{3072d^2}\log\frac{k(a)}{\delta}.}\tag{4.1}
\]
不可行时左端为无穷，结论仍成立。

**证明。** 对每条候选，只保存它在自身出生窗口中**首次**得到的确定标签，作为该候选符号的估计。窗口之后新参照使它非近优，不再把那时的标签当成旧符号答案。若候选在自己的整个窗口都没有确定标签，它就贡献 $H$ 未决面积，因为其边界距离为 $d>\eta$。因此面积成功时，至少 $k(a)$ 条候选在自己的有效窗口中得到过确定报告。

这些保留标签在 $E_{\rm lab}$ 上全部正确。把全部 $m$ 个符号放在同一个乘积先验下，在最终 $T$ 对保留集合使用定理 2；停止时刻就是确定的 $T$，而不是预设每批必须完成。恢复数量事件概率至少 $1-\delta>1/2$。内部 Bernoulli 两向 KL 不超过 $32d^2$，故
\[
 \overline E\sum_{e,k}N_{e,k}(T)
 \ge\frac{k(a)}{1536d^2}\log\frac{k(a)}\delta.
\]
这里包括有效窗口之后的样本：它们可能仍编码符号，但每个这样的候选样本的 regret 也仍至少 $\varepsilon/2$。所以无需错误地把后期信息丢掉，直接由总计数得到 (4.1)。从先验平均取到一个固定符号环境，再对策略取下确界。证毕。

## 5. ABM：按激活数量分配细精度的两分辨率维护

ABM 是本轮的**理论可达性算法族**，不是下面实验中的 CCP-shared，也不宣称有限预算下胜过 CCP。它解决的是原来“所有细任务按最终总臂数分置信预算”会产生的中间任务数量计费问题。

### 5.1 输入与机制

输入 $\varepsilon,\delta,\rho_c,\rho_f$ 和整数细候选预算 $s\ge0$。运行时不输入 $T,H,J,M,K$、真均值、实际参照身份或未来到达。

- 所有臂都有按到达编号 $i$ 预设的粗检查点，$q_i^c=\lceil2\rho_c^{-2}\log(4i(i+1)/\delta)\rceil$。粗证据错误预算总计 $\delta/2$。
- 偶数轮优先完成粗 FIFO 队列，队列清空时再完成细任务；其他轮使用全历史 UCB。每次只有一条实际观测。
- 一批全部粗检查点完成后，以保存的粗样本均值选出该批经验最好臂。按标签顺序，从其他臂中选择至多剩余预算数量的细候选。每选至少一条细候选，同时为该批经验最好臂激活一项细参照任务。
- 最多激活 $s$ 条细候选，以及至多 $s$ 条细参照，总细任务数不超过 $2s$。
- 第 $r$ 项细激活发生后，才开始为它积累一个新观测块。事前设 $q_r^f=\lceil2\rho_f^{-2}\log(4r(r+1)/\delta)\rceil$。包括普通 UCB 获得的后续样本在内，块长达到 $q_r^f$ 时保存细区间。细任务总错误预算为 $\delta/2$。
- **全部旧样本仍保留**在收益估计与粗报告中。只是不能将数据选择后的旧前缀当成未经选择的“激活排名置信证据”；细层采用合法的新块，避免后选择错误。
- 报告采用粗、细区间的交集；负报告不删除收益资格。空区间时报告全未决。

用引理 A 的条件版本对每个激活排名分配错误率，得到 $P(E_{\rm lab})\ge1-\delta$，在完整 bounded 模型上成立。

### 5.2 分辨率与充分窗口条件

在第 4 节性能族上选
\[
 \rho_c=v/8,\qquad\rho_f=d/4=\eta/2.
\]
算法的粗配置是事先选择的服务参数，不声称自动发现未知 $v$。
定义分析量
\[
 Q_c=\left\lceil128v^{-2}\log\frac{4K(K+1)}\delta\right\rceil,
\]
\[
 Q_f(r)=\left\lceil32d^{-2}\log\frac{4r(r+1)}\delta\right\rceil\quad(r\ge1),
\]
\[
 L_c=2(M+1)Q_c,\quad
 L=L_c+2(M+1)Q_f(2m),
\]
\[
 B=L_c\left\{\frac{(J+1)(J+2)}2+JM\right\}.
\]
要求整数窗口
\[
 \boxed{H\ge4(L+B).}\tag{5.1}
\]
这属于性能族条件，不是算法获知未来信息的方式。这里的 $B$ 是分析常数，不是当前真实最好均值 $B_t$。

### 定理 4：ABM 的面积与无条件收益上界

对 $0\le s\le m$，ABM 在该性能族上满足
\[
 P\{E_{\rm lab},\ \mathcal U_T\le(m-s)H+sL+B\}\ge1-\delta,\tag{5.2}
\]
以及 $s\ge1$ 时
\[
 \boxed{\sup_\Theta ER_T\le R_0(T)+4\varepsilon s Q_f(2s),}\tag{5.3}
\]
其中可取
\[
 R_0(T)=2\varepsilon KQ_c+
 128\left(\frac m\varepsilon+\frac{J^2}{v}\right)\log(2T)+1.
\]
$s=0$ 时没有细层项，右侧为 $R_0(T)$。

**证明。** 不论奖励路径如何，每批粗任务最多 $(M+1)Q_c$ 个样本，细任务最多 $(M+1)Q_f(2m)$ 个新样本。偶数服务及普通轮额外数据保证全部任务在出生后的 $L$ 轮内结束。由 (5.1) 与逐批归纳，前批不积压至新批。该工作量陈述不依赖参考臂是否选对。

在覆盖事件上，候选低于出生参照至少 $\varepsilon-d$，粗样本均值误差各至多 $\rho_c/2$，故经验最好者确为该批参照。旧参照的粗上界低于当前参照细上界的可能控制尺度，因为 $v>\rho_c+\rho_f$；候选的粗上界也显著低于参照。细候选与细参照完成后，两端点各误差至多 $\rho_f$，$2\rho_f<d$，因此正确判清所有被选细候选。共有 $s$ 个，每个出生窗口面积最多 $L$；其余 $m-s$ 个每个最多 $H$。

新批粗证据在 $L_c$ 轮内完成。因为 $d+2\rho_c<v$，上一批候选的旧粗上界配合新参照下界即可排除，不需新增旧候选数据。更旧排除持续有效。所有参照的 gap 至多 $\varepsilon/4$，两端粗误差至多 $2\rho_c<\varepsilon/2$，故当前批粗证据完成后全部参照可正认证。在第 $e$ 个窗口，额外暂时受影响的至多 $e+1$ 个参照与上一批的 $M_{e-1}$ 个候选。对 $e=0,\ldots,J$ 相加，上述额外面积至多 $B$，得到 (5.2)。

无条件 regret 不使用覆盖事件。所有小于粗检查点的实际样本总计不超过 $KQ_c$；每次 gap 至多 $2\varepsilon$。细服务额外观测总计至多 $2sQ_f(2s)$，每次仍至多 $2\varepsilon$，这是 (5.3) 两个检查点项。其余样本是全历史 UCB 普通轮。每个候选的最小正 gap 至少 $3\varepsilon/4$、最大 gap 至多 $2\varepsilon$；旧参照的最小正 gap 至少 $v$、最大 gap 至多 $Jv$。引理 C 的不同计数收费加上坏轮总期望小于 1，被所列 $128$ 常数控制。所有首次观测已经在粗计数项中覆盖。无条件计数仍合法，即使粗层在失败路径上选错了参照。证毕。

### 定理 5：整个中间预算区间的匹配

记 $A_{\min}=mL+B$。对任意
\[
 \boxed{A_{\min}\le a<V=mH}
\]
取
\[
 s(a)=\left\lceil\frac{V+B-a}{H-L}\right\rceil.
\]
则 $1\le s(a)\le m$，ABM 达到面积预算 $a$；且
\[
 \boxed{
 \frac{\varepsilon k(a)}{3072d^2}\log\frac{k(a)}\delta
 \le\mathfrak R_\Theta(a)
 \le R_0(T)+1024\frac{\varepsilon k(a)}{d^2}\log\frac{k(a)}\delta.
 }\tag{5.4}
\]
这里 $k(a)=\lceil(V-a)/H\rceil$。

**证明。** $a\ge mL+B$ 给出 $s(a)\le m$；定义直接保证 $(m-s)H+sL+B\le a$。若 $k=k(a)$，则 $V-a\le kH$。由 $H\ge4(L+B)$，
\[
 \frac{V+B-a}{H-L}\le\frac{kH+B}{H-L}\le2k.
\]
右端为整数，故 $s(a)\le2k$。对 $s\ge1$，
\[
 \log\frac{4(2s)(2s+1)}\delta\le3\log(s/\delta),
 \quad Q_f(2s)\le97d^{-2}\log(s/\delta).
\]
又 $\log(2k/\delta)\le\tfrac54\log(k/\delta)$，因此定理 4 的细层项至多
$388\varepsilon s d^{-2}\log(s/\delta)\le970\varepsilon k d^{-2}\log(k/\delta)$，放宽为 1024。下界就是定理 3。证毕。

**量级说明。** 若显式取 $H=16(L+B)$，则
\[
 A_{\min}/V\le(1+1/m)/16\le3/32<1/8.
\]
所以该区间包含旧快速预算 $V/8$，并延伸至所有 $a<V$ 的中间服务水平。固定 $J,M,\varepsilon,v,\delta$、$d\downarrow0$，$H,T=\Theta(d^{-2})$，$R_0(T)=O(\log(1/d))$，细项至少 $\Omega(d^{-2})$；从而在该区间具有同一任务上的匹配阶数。

**绝不能省略的范围。** (i) 不是任意到达模型；(ii) $a<A_{\min}$ 尚未刻画；(iii) $[V,V+B)$ 的细边界没有由本界闭合，$a\ge V+B$ 只有粗策略上界，未证明匹配；(iv) 操作算法给定 $s$ 不使用未来，但由期望服务预算 $a$ 选出 $s(a)$ 用到了性能族的 $m,H$。这不是一个只看到 $a$ 就自动识别未来规模的因果校准器；(v) $R_0$ 是必要明确保留的加性保底，不宣称在全部联合增长区间可忽略；(vi) ABM 使用普通 UCB，不把 CCP/Shared 的谱最优保护未经证明地移植过来。

## 6. 定理 6：有限时域的精确前沿表述与小型数值求解

### 6.1 全均值模型的存在性表述

固定有限 $T,K$ 与已知确定日程；性能类由均值限制定义，可靠性覆盖完整 bounded 模型。允许策略知道这些信息但不知道均值。Bernoulli 化 $Y=1\{U\le X\}$ 保留每臂均值；由于 $R_T$、真标签和边界距离只取决于均值，bounded minimax 值等于 Bernoulli 子类的相应值。

Bernoulli 有限历史树及每次报告的有限标签集合给出有限多个确定性完整行为计划 $d=1,\ldots,D$。所有随机策略的风险向量可由在根节点随机选择完整计划的权重 $w\in\Delta_D$ 表示；可预先为每个信息历史独立采样其行为随机数，得到此混合。对每个均值向量 $\mu$，记
\[
 R_d(\mu)=E_\mu^dR_T,\quad
 F_d(\mu;a)=P_\mu^d(E_{\rm lab}^{(T)c}\cup\{\mathcal U_T>a\}),
 \quad G_d(\mu)=P_\mu^d(E_{\rm lab}^{(T)c}).
\]
则前沿恰等于半无限线性规划
\[
 \min_{w\in\Delta_D,r\in[0,T]}r
\]
约束为
\[
 \sum_dw_dR_d(\mu)\le r,\quad
 \sum_dw_dF_d(\mu;a)\le\delta\quad(\mu\in\Theta),
\]
\[
 \sum_dw_dG_d(\mu)\le\delta\quad(\mu\in[0,1]^K).
\]
之后永远报告全未决即可把截至 $T$ 的可靠性扩展到全过程。任意固定 $\mu$ 的约束对 $(w,r)$ 是闭半空间，因此可行集是紧集；只要可行，最小值取到。这是精确存在性，不是统计复杂度刻画。

当 $\varepsilon,\eta,\delta,a$ 与均值约束为有理半代数输入，可按 $\mu_j-\mu_i=0,\varepsilon,\varepsilon\pm\eta$ 等超平面划分参数空间。在每个面上，真标签、边界资格和每条终端历史的面积指示固定；似然是多项式，regret 是分段仿射乘似然。因此上述全称约束可由实闭域量词消去处理，给出理论上的有限精确算法。该计算既没有小复杂度保证，也不等于本轮实际代码已经完成了连续参数消去。

这是行为策略/序列形式与半代数计算的标准工具适配，非本轮主要创新。参考 von Stengel (1996)；Basu–Pollack–Roy (2006)。

### 6.2 实际实现求解的范围

`exact_frontier.py` 实际解的是**有限四环境、两臂、给定终点和日程、固定完整模型有效报告器**的前沿。只优化采样，不优化报告器；这比 6.1 的全问题严格更受限。

状态包括每臂成功数与次数、累计面积、各候选环境的历史报告错误标志；只在本示例全部臂始终边界外时，面积是共同可观测整数。若边界资格在不同环境中不同，必须维护每环境面积向量或完整历史，不得沿用该简化。

用固定正先验混合历史法则作为参考测度，终点的模型似然比有界。共同状态流满足线性守恒，模型 regret 与联合失败概率都是终点流的线性函数。LP 不仅求目标值，还恢复共同动作概率，并在每个真实候选环境下从头前向传播，核对风险、失败率与概率质量。

这些都是浮点最优化结果，不是有理算术形式证明。求解器出现未解决的数值状态时保留日志，不把它算成不可行。严格不可行状态可以借助面积可行性的单调性推断更小预算不可行，并明确标识哪些不是单独求解。

## 7. 本轮不能合并的结论

| 对象 | 已证明 | 未证明 |
|---|---|---|
| 固定 $\beta$ CCP | 可观测指数差保护；由旧结果推出某些快速预算不可达 | 完整联合前沿 |
| 逐日程比较者 vs 未知未来策略 | 定理 1 的非恒定逼近比反例 | 因果共同日程类不存在最优策略 |
| 任意部分符号恢复 | 定理 2 | 对所有联合统计目标都是新最优界 |
| ABM | 指定更新族、连续中间预算区间、含 $R_0$ 的匹配 | 一般重叠到达、所有面积区域、无需规模信息自动校准 |
| CCP-shared / 多见证规划 | 完整模型报告可靠；继承旧 guard 的 regret 界和有限工作量界 | 新的匹配前沿、数值全面优越 |
| 精确 LP | 所列有限模型与固定报告器的精确优化表述 | 大规模未知未来模型的实用精确解 |

## 8. 来源与证明归属

- 当前项目：`manuscript(2).pdf` §5–7 与 `supplement(2).pdf` S3–S8、S11–S14；定义、老更新族、老端点与工具。
- 独立项目论文：The Temporal Geometry of Bandits With Arriving Arms，Theorem 1 及 Supplement S3.3；谱保证，不重新计新。
- Kaufmann, Cappé and Garivier (2016), On the Complexity of Best-Arm Identification in Multi-Armed Bandit Models；KL 换测度。
- Malloy and Nowak (2014), Sequential Testing for Sparse Recovery；同时恢复的统计背景。
- Mason et al. (2020), Finding All epsilon-Good Arms in Stochastic Bandits；固定臂相对集合识别。
- von Stengel (1996), Efficient Computation of Behavior Strategies；行为策略与序列形式。
- Basu, Pollack and Roy (2006), Algorithms in Real Algebraic Geometry；半代数量词消去。

本轮证明流程采用指定 `prove-stat-ml-probability-theorems` 的目标冻结、路线比较、反例、依赖核查与对抗审计。不存在独立代理复核；数值断言检查不替代以上解析证明。
