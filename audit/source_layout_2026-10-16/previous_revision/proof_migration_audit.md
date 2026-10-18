# 补充材料迁移核对

本记录核对执行方案 §5–7 对证明迁移的要求。基线是本目录 `baseline/` 中冻结的 2026-10-15 稿件；新入口是项目根目录的 `supplement.tex`。本轮属于结构重排与措辞修改，不是独立的完整证明验证，也没有新增科学结果。

## 新目录与来源

| 新编号 | 内容 | 冻结来源 | 主要依赖 |
|---|---|---|---|
| S1 | Probability tools and reporting conventions | 原 S3，合并原 S2.1 中实际使用的二元熵／KL 工具 | 独立潜在流、Hoeffding、历史似然比 |
| S2 | Joint guarantee of Checkpoint-UCB | 原 S7 的一般 regret 与任意到达完成界 | S1；真实 lifetime 计数 |
| S3 | Broadcast uncertainty and queue area | 原 S4 | S1；同一参考环境 |
| S4 | Partial simultaneous recovery | 原 S5 | S1；独立符号的后验分解 |
| S5 | Worst-schedule area and growth consequences | 原 S10，加原 S7 的增长后果 | S2 完成引理、S3、S4 |
| S6 | Area-constrained temporary tasks | 原 S6，保留正文移出的完整信息松弛 | S4；同一个 product prior |
| S7 | Shared evidence and rapid/deferred endpoints | 原 S7 的分离窗口证明与原 S8 | S1、S2、S6；出生窗口内完成 |
| S8 | Regret quantiles under the same maintenance protocol | 原 S11 | S4、S6、S7 |
| S9 | Compatible-window truncated area | 原 S12 | S4；可共同实现的完整环境 |
| S10 | Eventual exact classification | 原 S9 | S1、S2；另一套多精度策略 |
| S11 | General information-allocation relaxation | 原 S13 | S1；历史 KL |
| S12 | Intermediate service configurations and disclosed-reference diagnostic | 原 S14 | S7；显式披露额外参照角色 |
| S13 | Computational details | 原 S15、通用记账 | 现有报告实验；由实验迁移子任务生成 |

S1–S12 各自存于 `theory/maintenance_a01_*.tex` 至 `maintenance_a12_*.tex`。S13 输入 `revision_2026-10-16/computational_details.tex`。编号由 LaTeX 自动生成，没有硬编码旧节号。

原 S1 的两阶段 UCB-AA 分析、原 S2 的纯 regret 专题和原 S16 的旧实验图不参与新编译。原有五份 theory 源文件逐字节保留，冻结副本也保留。移除的来源和标签仍在 `theorem-map-supp.csv` 可追溯。

## 数学合同核对

| 合同 | 核对结果 |
|---|---|
| 模型与报告事件 | 保留独立平稳 bounded 流、外生确定日程、到达先于动作、一次观测后报告、全体可用臂的三分划分。资格使用 $\Delta_i(t)\le\varepsilon$，面积只计 $|\Delta_i(t)-\varepsilon|>\eta$。 |
| 检查点 | 配额 $q_i(\rho_i)=\lceil2\rho_i^{-2}\log\{4i(i+1)/\delta\}\rceil$ 未改。固定首个配额均值、冻结区间、所有样本抵扣一次 lifetime 配额、负报告仍可用于收益选择均保留。 |
| 一般联合上界 | $P(E_{\rm lab})\ge1-\delta/2$、一般 UCB 项 $K_T+4\sqrt{3K_TT\log(2T)}+1$ 与真实服务 regret 保留；没有加上分离窗口条件，也没有加 $\delta T$。 |
| 任意到达完成界 | 原 S7 段落独立编号为引理 `app:completion_general`，放在 S2。内容仍为 $\mathcal U_T(\eta)\le\min\{K_TT,2K_T\sum_iq_i\}$，精度仍为 $\rho=\eta/4$。S5 明确引用本引理，不通过被删除的算法上界。 |
| 共同认证 | $q_-$ 的 floor、$Q_t$ 的 post-service 递推、同一零环境期望、$3/4-\delta$、面积阈值 $\mathcal B_T/4$ 与概率 $1/4$ 保留。 |
| 部分同时恢复 | 完整保留 stopped history 下的 posterior factorization、$\kappa$ 的两个方向 KL 最大值和 $m\log(m/\delta)/(1024\kappa)$。单窗口截断与 $1/7$ 概率保留。 |
| 最坏面积 | $2^{-24}$、$256$、$\rho=\eta/4$、$99K\eta^{-2}\log(K/\delta)$ 与全部原参数范围保留。下界仍来自初始静态批次。 |
| 增长量词 | 固定无限日程必要条件、一般充分条件、多项式指数边界、逐终点总臂数类、固定稀疏突发反例分别陈述。反例环境可随终点变化，未改成一个环境同时失败。 |
| 共享证据 | $H_e\ge2S_e$、$b_J-b_0\le\varepsilon/4$、相邻精度分离条件和 $2\max_e\rho_e\le\varepsilon/2$ 原样保留。一般无条件 regret 式的 $[\lceil12\log(2T)/\gamma_i^2\rceil-q_i+1]_+$ 保留。 |
| 两端权衡 | $q_f,q_c,H,T,V$ 的定义、快速面积 $V/8$、粗面积 $9V/8$、快速匹配常数和粗端仅有上界均保留。没有放大到所有长窗口或完整前沿。 |
| 分位加强 | 预算停止仍在第 $q+1$ 个候选样本；完整保留为何不能停在第 $q$ 个样本的解释。存在一个固定符号环境及 $11/80$ 保留。 |
| 兼容窗口 | 同一完整环境、不同候选－时间对只计一次、可共同实现的资格结构保留。 |
| 最终一致性 | 明确属于另一套 revisable multiresolution policy；有限到达、最终有限臂、严格边界分离与无条件 almost-sure 结论保留。 |
| 信息松弛 | $a+\delta W$ 原样保留；未知均值 causal learner 可达性未证的限定保留。 |
| 中间配置与角色披露 | 精细批次事先选定，配置只给可达点；已知哪条参照在本窗口最好属于额外信息，未作为主算法保证。 |

## 可复核检查

`check_proof_math.py` 对冻结的三份维护证明源文件与新 S1–S12 提取全部展示公式，去掉空白和 label 后逐一计数比较。结果：迁移前后均为 72 个展示公式。唯一文本差异是 S1 将原 S2.1 中已存在的二元熵下界并入 data-processing 展示式；其余 71 个展示式相同。完整结果在 `proof_math_preservation.json`。这项检查验证公式迁移，没有验证每条公式的数学正确性。

`theorem-map-supp.csv` 覆盖冻结补充源中的所有实际 label，记录移除、合并或新位置；另记录原 S7 一般完成界的新独立引理标签，以及从正文迁来的 `eq:allocation_lower`。新补充源没有引用旧 UCB-AA 定理或纯 regret 专题。

写作修改遵循 `stat-journal-writing` 的条件与结论就近呈现原则，并按 `humanizer` 检查年代式叙述、重复路标和空泛强调。证明的常数、量词和统计协议优先于句式变化。英文标题已与新正文统一；补充材料的空作者字段及固定日期 October 15, 2026 沿用冻结基线，没有推测或修改作者信息。

最终编译与逐页排版验收由主任务在 S13 和正文整合后执行。本文件不把编译通过等同于证明已获独立验证。
