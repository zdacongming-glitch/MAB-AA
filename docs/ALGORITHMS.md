# 最终算法合同

来源为 2026-10-31 当前稿件第 3 节及用户指定两份实例依赖理论报告。两种候选均不含 H8/H16。`configs/methods.json` 是最终注册表，来源别名不增加独立方法数。

## 共用证据

每轮接收本轮到达的新臂，选择一个可用臂，再观察唯一一次真实奖励。两分支共享终身计数 $n_i$、奖励和 $S_i$、平方和 $Q_i$ 与完整经验分布。时钟或偏好改变均不重置样本与账本，负标签不删除臂。

置信区间来自 $\alpha_i=\delta/[2i(i+1)]$ 的 beta-mixture 反演，并对全部已观察前缀取交集：

$$
M_{i,n}(m)=\frac{\mathrm B(S_{i,n}+1/2,n-S_{i,n}+1/2)}{\mathrm B(1/2,1/2)m^{S_{i,n}}(1-m)^{n-S_{i,n}}}.
$$

在配额 $q_i$ 处额外交上以固定前缀均值为中心、宽度 $\eta/4$ 的区间并保留：

$$
q_i=\left\lceil\frac{32}{\eta^2}\log\frac{4i(i+1)}{\delta}\right\rceil.
$$

gap 区间严格排除自身：

$$
g_i^-=\max\{0,\max_{j\ne i}\ell_j-u_i\},\qquad g_i^+=\max\{0,\max_{j\ne i}u_j-\ell_i\}.
$$

正标签条件为 $g_i^+\le\varepsilon$，负标签为 $g_i^->\varepsilon$；单臂时两界为零。未决且 gap 区间完全进入豁免带的臂不进入工作集。空交集触发永久失败：全部后续报告未决、分类服务停止，奖励采样及其 guard 继续。

## SRC 的参考与选择

竞争臂数首次非零或相对阶段起点翻倍时重启到达时钟，令 $s=t-\sigma+1$、$d=2\mathrm{base}$，保留所有计数。参考为

$$
J_i(t)=\begin{cases}1,&n_i=0,\\
\min\{1,S_i/n_i+\sqrt{[\log\{s/(dn_i)\}]_+/n_i}\},&n_i>0.
\end{cases}
$$

单臂直接用指数 1、费用 0。令 $\zeta_t(i)=\max_jJ_j-J_i$，奖励与分类分别累计执行时的费用。年龄 dyadic 分组形成谱尺度，省略第一只初始臂：

$$
S_t=\sum_{\ell\ge0}\min\{2^\ell,\sqrt{k_{\ell,t}2^\ell}\},\qquad \overline S_t=\max_{u\le t}S_u.
$$

奖励轮在 $C_R+\zeta_t(i)\le\beta_R\overline S_t$ 的臂中最大化

$$
\Xi_i(t)=\begin{cases}+\infty,&n_i=0,\\
-n_iD_{\inf}(\widehat F_i,\widehat\mu_{\max})-\tfrac12\log n_i,&n_i>0.
\end{cases}
$$

所有平局按到达顺序。信息量使用全部真实观测支持点，不用 Bernoulli 化近似。目标为 1 时取左极限：只有全一支持的信息量为零，其他支持为无穷。

数值核只使用正计数的实际支持点判断边界；目标接近 1 时累加相对目标的中心化观测，不用固定绝对均值容差将信息量判为零。奖励评分剪枝的上界来自实际计算过的奖励可行臂。有限预算的经验信息量反演保留并返回满足预算的可行下端点，避免相邻浮点数的中点舍入到不可行端点。这些处理保持原算法定义及平局规则。

## SRC-KL 的变化

该版本按改进报告第 5 节实现，保留原奖励评分与分类机制。令 $v=s/d$，

$$
\phi(x)=\log_+\{x[1+(\log_+x)^2]\},\qquad f(v)=\lfloor v^{1/5}\rfloor,
$$

$$
J_i^K(v,n)=\sup\{m\in[0,1):nD_{\inf}(\widehat F_{i,n},m)\le\phi(v/n)\}.
$$

新参考为

$$
V_i(t)=\begin{cases}1,&n_i=0,\\J_i^K(v,n_i),&1\le n_i\le f(v),\\J_i(t),&n_i>f(v).\end{cases}
$$

两个账本统一改用 $\max_jV_j-V_i$，历史费用不重算。奖励预算为

$$
B_R(t)=\min\{\beta_R\overline S_t,\sqrt{\log(e+t)}\}.
$$

这里 $t$ 是全局物理时间；KL 指数使用到达阶段的 $s/d$，不是全局 $t/K$。分类预算仍为 $\beta_C\overline S_t$，每次实际服务须满足 $n_i<q_i$。单臂不计算 $s/d$。这不是直接把奖励 proposal 改成普通 KL-UCB。

## 分类规划

规划中心是 smoothed mean 在当前区间的投影。候选与中心最优臂或排除自身的最大上界参考配对，根据成员、非成员或进入豁免带的方向使用对应单侧半径。价格基线为 .02，二端点代理凸问题保留当前计数下界。

相关性 $R_i$ 用观测矩计算 Gaussian 尾评分并截在 $[.02,1]$；共享信用为

$$
G_k=\sqrt{\max\{1,\sum_{i\in W:k\in\{i,j(i)\}}R_i\}}.
$$

按代理成本除以 $\max(G_i,G_j)R_i$ 选择 pair，再按方向半径、共享信用、计数及价格选择合法端点。无合法 pair 时回退到配额以下最宽区间。每次只观察一次后重规划。

令 $B_t=\max_{i\in W}R_i$，工作数为 $b$，提案中心奖励损失为 $\widehat c$：

$$
w_t=.02+.98\frac b{b+4}\frac{\varepsilon}{\varepsilon+\widehat c},\qquad p_t=B_t\frac{\lambda w_t}{1-\lambda+\lambda w_t}.
$$

phase 累加 $p_t$，达到 1 时扣 1 并尝试服务；guard 拒绝后保留扣减，转奖励分支。偏好 1 时频率仍是 $B_t$；有限预算偏好 1 与 area 分别命名。

## baseline 与信息条件

| 配置 | 固定规则或区别 |
| --- | --- |
| UCB1 / AUER / UCB-log2t-c3 | bonus 分别为 $\sqrt{2\log t/n}$、$\sqrt{8\log t/n}$、$\sqrt{3\log(2t)/n}$ |
| Growing-MOSS | 当前时间与当前臂数，不知道终点 |
| ACI / Clipped-ACI | 原到达时钟，未截断/截断指数；未观测分数为无穷/1 |
| IMED | 完整经验信息量，加 $\log n$；无 SRC guard |
| Empirical-KL-UCB | 完整经验信息量反演，预算 $\log t$；无 SRC guard |
| KL-UCB-c0/c3 / KL-UCB+ | Bernoulli KL，预算分别为 $\log t$、$\log t+3[\log\log t]_+$、$[\log(t/n)]_+$ |
| UCB1-Tuned / UCB-V | 原经验方差规则与固定常数 |
| TS / TS-Jeffreys | uniform / Jeffreys Beta 评分；非 Bernoulli fractional 更新是动作启发式 |
| TS-SMAB-bounded | 对真实奖励另做私有 Bernoulli 化更新动作评分；报告仍用真实奖励 |
| Bayes-UCB | uniform-prior Beta 的 $1-1/t$ 分位数；不强制初始化 |
| SB-EXP3-ATGT | 嵌套可用集合的双层 doubling 与损失估计 |
| MOSS-T-currentK | 额外获知 T、使用当前臂数；不同于 Growing-MOSS |

ACI、Clipped-ACI、UCB-log2t-c3 是明确规则的比较配置，不另计成三篇外部文献算法。旧 MC-MOSS 两个名字映射到 ACI 两配置；Thompson 与 TS-exact 去重。三个旧代码已有但旧正式实验未运行的配置为 MOSS-T-currentK、TS-Jeffreys、TS-SMAB-bounded。

## 在线使用

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))
from srcbench import Policy
from srcbench.methods import get_method

policy = Policy(get_method("SRC-KL-L060"), epsilon=.15, eta=.03, delta=.05)
chosen = policy.choose(new_arms=["first", "second"])
policy.observe(.7)  # 替换为 chosen 对应的唯一真实观测
positive, negative, unresolved = policy.report()
print(policy.state())
```

无新臂的后续轮调用 `choose([])`。必须先完成待观察奖励，才能选择下一轮或改变偏好。
