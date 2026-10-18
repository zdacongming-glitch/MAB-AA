# 第二轮符号与术语映射

日期：2026-10-17。以当前正文§2和原M3/S3的定义为准，将C16／P16／F17记号映射到同一物理问题。最终稿仍由完整 `manuscript.tex` 与 `supplement.tex` 两个TeX文件维护。

## 固定任务与真实对象

| 原稿／当前稿 | 新研究包中对应记号 | 含义与限制 |
|---|---|---|
| $\mathcal A_t$ | $A_t$ | 时刻$t$已到达并永久可用的臂，不是算法奖励活跃集 |
| $K_t=|\mathcal A_t|$ | $K_t$ | 当前真实可用臂数；可大于$t$ |
| $r_i$ | $\mu_i$ | 臂的真实期望奖励，不给算法 |
| $r^*(t)$ | $B_t$ | 当前真实最优均值，不作工作量常数或谱 |
| $\Delta_i(t)$ | $\Delta_i(t)$ | $r^*(t)-r_i$；regret收益gap |
| $|\Delta_i(t)-\varepsilon|$ | boundary distance | 到近优资格边界的距离，与收益gap不同 |
| $X_{t,I_t}=Y_{I_t,N_{I_t}(t-1)+1}$ | 实际奖励／潜在流 | 一物理轮仅揭示一个真实奖励；潜在前缀用于证明及共享模拟 |
| $N_i(t)$、$n_i=N_i(t-1)$ | $N_i$、$n_i$ | 真实终身计数，不因到达、报告、模式或时钟变化重置 |
| $\Sigma_i$、$\Sigma_{i,n}$ | $S_i$、$S_{i,n}$ | 真实奖励和，避免与到达谱同名 |
| $\hat r_i(n)$ | $\hat\mu_i(n)$ | 真实前$n$次观测均值 |
| $\mathcal G_t^\varepsilon$ | $G_t^\varepsilon$ | 全部真实近优臂，允许并列 |
| $\mathcal P_t,\mathcal N_t,\mathcal V_t$ | $P_t,N_t,V_t$ | 报告的正／负／未决划分；负报告不自动删除奖励资格 |
| $E_{\rm lab}$ | $E_{\rm lab}$ | 全部物理时刻共同标签正确事件 |
| $\mathcal U_T(\eta)$ | $\mathcal U_T$ | 边界带外累计未决臂时间；可因新到达让旧臂再次未决而重新计费 |
| $R_T$ | $R_T$ | 累计dynamic regret；主风险是其无条件期望，不改称经验分类错误或加权期望面积 |
| $\vartheta$、$\Theta$ | 环境$\theta$、性能族 | 环境索引用$\vartheta$与温度$\theta$区分；族及量词按所属定理规定 |

## F-CCP可观察状态与调度

| 当前符号 | 含义 | 不可混淆的对象 |
|---|---|---|
| $\mathsf M_{i,n}(m)$ | 有界均值beta-mixture检验过程 | 旧广播候选数$M_t$ |
| $\operatorname B(a,b)$ | beta函数 | 当前最优均值$r^*(t)$、批次或工作量 |
| $[\ell_i,u_i]$ | 有效报告置信区间 | Beta动作评分的可信区间或虚拟MC指数 |
| $g_i^-,g_i^+$ | 置信矩形内排除自身的精确gap极值 | 旧Checkpoint共用最大上下端点报告公式 |
| $Z_t$ | 可证明处于容忍边界带、暂停主动服务的未决集 | 已分类集合；它仍报告未决 |
| $W_t=\mathcal V_t\setminus Z_t$ | 当前主动报告工作集 | 真实面积贡献集；真实边界距离不给算法 |
| $m_i,v_i^{\rm plan}$ | 规划中心和规划半径 | $r_i$真均值；不使用同一个$r_i$表示半径 |
| $\bar n_i=\max(1,n_i)$ | 代理规划下界 | 真实计数；不制造虚拟统计观测 |
| $x_i,c_i,h_i$ | 代理目标计数、采样价格、pair目标尺度 | 已证明真实信息复杂度或Pareto对偶量 |
| $J_i(t)$、$\zeta_t(i)$ | 截断虚拟MC指数及其与最大值之差 | 真实regret、报告区间或独立两算法轨迹差 |
| $d_{\rm clock}$、$s=t-\sigma+1$ | 到达时钟容量和局部时钟 | 临时任务边界距离$d$、ABM激活预算$s$ |
| $\mathcal S_t$、$\overline{\mathcal S}_t$ | 当前年龄谱及其running maximum | 奖励和$\Sigma_i$或历史面积 |
| $q_i$、$Q_T^{\rm cap}=\sum_{i\in\mathcal A_T}q_i$ | 每臂固定检查点配额及总配额 | 旧广播下界分析队列$Q_t$；算法不运行该分析队列 |
| $C_R,C_C$ | 收益／认证两个累计指数差账本 | 单一共享guard或真实累计regret |
| $D_T^{\rm srv}$ | 被认证guard拒绝的服务尝试数 | 旧异质regret中最大gap $D_i^T$ |
| $\phi,p_t,p_{\min}$ | 相位、提出的服务率及busy轮统一正下界 | Bernoulli服务随机抽签或实际成功服务比例 |
| $\mathcal E$ | 混合和检查点的共同覆盖事件，概率至少$1-\delta$ | 旧Checkpoint独立的$1-\delta/2$覆盖事件 |

## 参数身份与算法区别

| 层次 | 符号 | 含义 |
|---|---|---|
| 固定任务 | $\varepsilon,\eta,\delta$ | 近优容忍度、面积豁免边界宽度、联合错误预算 |
| 服务偏好 | $\lambda_t,p_0,k_0,\nu$ | 可预测偏好、率下限参数、压力尺度、代理正价格 |
| 收益行为 | $\mathsf B,\theta$ | 收益评分核及Beta评分温度；温度不进入真实证据样本数 |
| 保护 | $\beta_R,\beta_C$ | 预先固定预算系数；$\infty$绕过guard，不当作0 |
| 辅助证据 | $\rho=\eta/4$ | F的固定兜底精度；Checkpoint见证可事前选其他精度 |

F-R是$\lambda=0,\theta=.5,\beta_R=16$；标准TS兼容端点要求从开始$\lambda=0,\theta=1,\beta_R=\infty$及相同完整核状态／后端随机流。Checkpoint-UCB有自己的固定报告与偶数FIFO，不能称为某个F参数的同一算法。CCP-original只指F17中的旧CCP配置，既不是旧CP-FIFO，也不自动等于每一代旧CCP实现。

## P16与旧端点的专用符号

ABM的性能族记作$\Theta_H$，保留$J,M,v,d,H$、$m=JM$、$K=J(M+1)+1$、$T=(J+1)H$及$V=mH$。其细候选预算$s$与恢复目标$k(a)$在S13内部定义。$B_{\rm rec}$仅重命名P16分析面积常数$B$，不与$r^*(t)$或F账本混用。

旧端点窗口$H=128(M+J+1)q_f$与ABM充分条件$H\ge4(L+B_{\rm rec})$分别属于不同定理合同。给定$s$的ABM运行不知未来；从$a$计算$s(a)$仍用性能族$m,H$，不声称自动未来无关校准。ABM中的$s$不能改写为F偏好$\lambda$来转移结论。
