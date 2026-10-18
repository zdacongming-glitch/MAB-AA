**Reviewer 1 回应策略与英文工作稿**

日期：2026-09-24。对象：当前正式已投稿稿件及 Reviewer 1、AE 的意见。本文只准备回应，不把独立研究分支当作已投稿成果，也不声称正文修订、证明修复或补充实验已经完成。原稿和原代码不作修改。

**建议坚持的立场：有限时域的模型嵌入，并不等于持续到达下的统计问题已被解决。**

尊重审稿人，应体现为承认他指出的真实联系、精确比较定理条件，并直接回答简单基线是否足够。立场鲜明，应体现为明确区分“能表示为一个有限 sleeping 实例”“能运行已有算法”“已有保证在增长区间仍然有效”和“本文得到额外贡献”这四件事。它们不能互相替代。

不建议把总论点写成“我们的模型与 sleeping bandit 完全不同”。建议写成：本文针对持续扩张且永久保留已到达臂的结构，研究增长机制、统计识别与筛选之间的关系；这一研究问题不能仅凭固定臂池的次线性结论作答。是否已取得足够的额外成果，则须由具体定理和公平比较支持。

**原文核对及证据入口。**

- KNS 第 1.1 节规定已知有限总臂池；随机奖励分支仍允许对抗可用集合。算法 2 的指数不依赖总臂数。其 Theorem 10 保留相邻均值差之和，Theorem 12 保留对数因子。Lemma 13 的证明分块开放不同臂对。[KNS 2010 原文](https://link.springer.com/content/pdf/10.1007/s10994-010-5178-7.pdf)
- 当前稿件允许潜在无限臂池：[模型定义](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:394)。主要上界使用随机完成时刻及其期望：[Theorem 1](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:641)；这一时间尺度须先与固定实际预算统一。
- 当前稿件的单调到达下界：[Theorem 5](D:/博士学习/科研/git/MAB-AA/JASA-template/mab_aa_main.tex:1216)。其可行参数范围与“匹配”范围需要明确，不能只比较平方根外形。
- Ghalme 等已研究到达后不消失的臂以及当前可用最优臂 regret，并讨论一般情形的线性困难和受限到达下的可学习性。因此不能把模型及目标本身重新作为首次贡献。[Ballooning Multi-Armed Bandits](https://arxiv.org/pdf/2001.10055)
- 本次独立逻辑和例子见[技术说明](D:/博士学习/科研/git/MAB-AA/reviewer1_response_2026-09-24/technical_positioning_note.md)。这些例子用于限定论断，不是新算法的优势证明。

**逐项回应的重点。**

| 审稿人关切 | 类型及严重性 | 应明确承认的部分 | 可以坚持的部分 | 还需完成的工作 |
|---|---|---|---|---|
| MAB-AA 是 sleeping 的特例 | 定位、创新性；高 | 有限到达前缀可以嵌入；比较目标在固定均值下相同 | 固定有限臂数的渐近区间与持续增长不同；嵌入不自动给出增长区间的有效保证 | 在正文列出实例类、增长条件和信息条件 |
| AUER 已有同阶上界 | 创新性、适用范围；高 | 简单 UCB 可在到达时初始化；本地已有适配推导 | 需保留臂数、gap、对数和预算定义；形式同阶不等于逐项覆盖 | 把已验证的本稿界与直接 UCB 界放在同一实际预算下 |
| 额外 gap/jump 假设削弱贡献 | 意义、适用范围；高 | 强假设下仅复现粗速率不足以支撑贡献 | 特殊结构下取得更精细结论是合理研究目标 | 给出明确实例族及可核查改进；若没有，收缩贡献表述 |
| 下界只是经典速率重述 | 创新性；高 | 静态下界是校准；局部 KL 检验也是成熟方法 | 一般 sleeping 难例不能自动成为永久到达难例；Theorem 5 必须保留旧臂仍维持局部测试困难 | 写清构造困难、可行参数和额外认识；不声称已建立新指数 |
| 淘汰机制复杂且动机不足 | 方法、意义；高 | 简单 UCB 加淘汰是必要对照 | 永久可用性使可靠的劣势认证具有永久效力 | 拆出初筛、持续采样、复查和正式淘汰的独立作用 |
| MOSS 数值更强 | 实验证据、公平性；高 | 当前结果不能宣称普遍 regret 优势 | 可以研究特定实例或明确成本目标上的收益，但必须实证 | 对强基线公平调参、冻结验证；活跃集合小不等于总成本低 |
| G-UCB 近线性令人意外 | 理论解释、实现核查；中高 | 仍需检查实现、系数和到达处理 | 臂数线性增长时，固定臂数次线性保证不构成反证；存在简单解析例子 | 增加停止到达、次线性到达和恒定速率到达对照 |
| 引言、符号与算法流程不清 | 写作；中 | 接受这一建议 | 无需争辩 | 重组引言，补符号表及单轮流程图 |

**最有力的论证顺序。**

先承认有限时域嵌入与 AUER 的基线地位，再说明增长区间中的结论为何不同；接着用永久认证和下界构造解释“单调性”到底改变了什么；最后用同一条件下的定理及数值结果证明额外价值。不要把指出审稿人的省略对数作为开场或中心。

对“本质不同”的具体表达，建议落在三个可验证问题上：

1. 持续出现的新臂是否导致不断新增的识别成本？固定臂数下的次线性不能单独回答这一点。
2. 永久保留的优质 incumbent 是否使过去得到的劣势认证继续有效？这解释永久筛选为什么有结构依据。
3. 当旧臂不能被环境撤走时，如何构造仍然迫使学习者反复识别新挑战者的难例？这解释为何下界不能直接照搬一般可用性构造。

这三个问题都值得研究，但前两个不是本文首次发现的事实，第三个也仍使用经典信息论工具。回应应说明最终增加了哪些结论，而不是仅替问题换名称。

**当前可以使用的英文工作稿。**

以下文字是回应草稿，保留将来时；它没有声称实验或正文修订已完成。英文中的 proposed revision 表示建议采用的修订方案。

> We thank the reviewer for highlighting the connection with sleeping bandits and for asking whether the proposed screening mechanism provides value beyond a simpler UCB-type policy. We agree that this comparison should be central to the paper. Our current presentation does not distinguish sufficiently clearly between a finite-horizon embedding into a sleeping-bandit instance and the growth-dependent statistical question that motivates our work.
>
> For any fixed horizon with finitely many arrivals, the available sets can indeed be represented by keeping each arm asleep until its arrival and awake thereafter. With stationary arm means, the mean-ordered comparator also agrees with the best currently available arm. We therefore do not base our distinction on a different regret comparator, and we agree that AUER is an essential baseline.
>
> The distinction we wish to make concerns the regime and the structure of the problem. The number of distinct arms need not be bounded by a fixed finite constant as the horizon increases. An upper bound that is sublinear for fixed arm count need not remain sublinear in this regime. For example, even an upper bound of order $\sqrt{K_TT}$ is of linear order when $K_T$ grows proportionally to $T$. Thus, the finite-horizon embedding alone does not establish sublinear regret under persistent arrivals. The relevant comparison must retain the dependence on arm growth and identify the arrival conditions under which the resulting guarantee is informative. At the same time, lack of advance knowledge of $K_T$ does not by itself prevent a UCB policy from being implemented by initializing arms when they arrive.
>
> Permanent availability also has a concrete consequence for screening. Once a valid statistical comparison certifies that an arm is inferior to an already available arm, that dominance remains valid at every later time because the dominating arm remains available and both means are stationary. This provides a structural motivation for permanent elimination. It does not, by itself, establish the necessity of our particular two-stage design: a simpler confidence-based elimination baseline must be included in the comparison.
>
> These observations motivate a more precise positioning of the paper: the intended contribution is to characterize and exploit the structure of persistent arrivals, rather than to introduce a different comparator or claim that ordinary UCB is inapplicable. We also recognize that additional assumptions are justified only if they yield conclusions beyond the generic baseline. Accordingly, our proposed revision will distinguish baseline guarantees from arrival-specific refinements, state the conditions and parameter ranges of each result explicitly, and avoid treating a generic square-root rate alone as the distinctive contribution.

**对下界问题，可接着使用以下段落。**

> We agree that the appearance of logarithmic or square-root rates is not, by itself, evidence of a new statistical complexity. Our static lower bound is intended as a calibration to established results. The substantive issue in the progressive-arrival construction is that previously introduced arms must remain available. A hard instance based on successively restricting availability to different arm pairs does not automatically satisfy this constraint: a previously learned, better arm may remove the need to explore the next pair. The construction underlying our Theorem 5 addresses this by placing successive local tests at increasing reference levels while retaining all earlier arms. We will make this distinction explicit and state the feasible parameter range imposed by bounded rewards. We will also avoid claiming a matched minimax characterization unless the upper and lower bounds are established on the same instance class and resource scale.

**对 G-UCB 曲线与 MOSS 问题，可使用以下段落。**

> The near-linear G-UCB curves require an explanation, but they are not inconsistent with sublinear guarantees for a fixed number of arms. To illustrate the distinction, suppose an initial arm has deterministic reward $3/4$ and a new arm with deterministic reward zero arrives every $h$ rounds. A UCB policy that gives priority to every unobserved arm incurs regret at least $(3/4)\lfloor(T-1)/h\rfloor$ from first pulls alone. This is an admissible persistent-arrival instance. The example explains why continual admission can generate linear regret; it does not establish that our method avoids the same cost, nor does it diagnose the mechanism behind every empirical curve.
>
> We agree that the comparison with Growing MOSS is consequential. The current evidence does not support a claim that UCB-AA uniformly improves cumulative regret over strong index-based baselines. Our proposed empirical revision will compare implementations under the same pull budget, arrival information and regret benchmark; separate stopped, sublinear and constant-rate arrivals; and report tuning, admission behavior and component-level sampling costs. If a benefit is primarily a reduction in the maintained candidate set, it will be reported as a separate outcome and assessed against appropriate elimination baselines, rather than used as a substitute for a regret improvement.

**对写作意见，可简短接受。**

> We agree with the reviewer that the current introduction and algorithm presentation make the main ideas difficult to follow. We plan to organize the introduction around the statistical question, the closest existing guarantees and the specific remaining contribution; provide a notation table; and add a diagram showing the screening, admission and elimination steps within a round.

**在正式提交前，必须补齐的证据。**

| 工作 | 验收要求 | 当前状态 |
|---|---|---|
| 统一理论比较 | 相同的确定实际预算、奖励信息、到达日程和 comparator；列出全部增长及 gap 条件 | 独立简单 UCB 推导已有，正式主证明仍有修复节点 |
| 找到实质区别 | 至少一个明确实例族上，已证明的精细结论严格超出粗基线界；若声称算法优越，须进一步比较算法实际风险或相应下界 | 尚未完成；“旧上界较松”不等于“旧算法较差” |
| 解释特殊条件 | 把 gap/jump 条件转成可解释的环境限制；说明简单 UCB 在同一限制下能达到什么 | 原表述尚不足以完成这一比较 |
| 核查下界 | 明确 Theorem 5 的块数与总臂数区别、奖励范围限制和实例类；静态部分定位为校准 | 技术说明已列出必须保留的限制 |
| 解释近线性 | 给出解析首拉成本，并在实际代码中记录首次采样、重复探索与新优臂响应的代价 | 解析例子本次已写出；新的针对性仿真尚未运行 |
| 验证筛选价值 | 完整接纳 UCB/MOSS、简单严格置信淘汰、原双阶段机制的公平对照；持续接纳到实际预算结束 | 已有试验提示强基线很有竞争力，不能报成方法优势已建立 |
| 如果主张资源收益 | 区分可用集合、接纳集合、活跃集合和认证淘汰；报告实际存储、决策计算及候选质量 | 活跃集合大小本身不充分 |

现有独立研究分支中，[固定预算修复试验](D:/博士学习/科研/git/MAB-AA/revision_trial_2026-09-23/README.md)没有带来强基线之上的 regret 优势；[GuardMOSS 探索](D:/博士学习/科研/git/MAB-AA/revision_exploration_2026-09-23/results/admission_report.md)只提供有条件的数值改善，并有原一般模型内的反例。二者都不能写成当前正式 UCB-AA 已取得的新成果。

**措辞边界。**

| 不建议写 | 建议表达 |
|---|---|
| The reviewer has overlooked the fundamental difference. | Our current presentation does not make the relevant distinction sufficiently explicit. |
| Our problem is not a sleeping-bandit problem. | A finite-horizon embedding is valid; what requires a separate comparison is the guarantee in the persistent-growth regime. |
| Sleeping bandits are adversarial, whereas ours are stochastic. | Separate reward assumptions from availability assumptions; compare with the stochastic-reward branch. |
| KNS does not apply because the final number of arms is unknown. | Unknown arm count can be handled by initialization on arrival; the growth dependence of the guarantee must still be examined. |
| Our dynamic comparator is fundamentally different. | Under stationary means the finite-prefix comparators agree; the intended distinction is in structure and attainable guarantees. |
| The linear UCB curve proves the superiority of screening. | The curve is compatible with growth-dependent exploration cost; any advantage of screening needs an additional comparison. |
| Our lower bound establishes a completely new rate. | The construction establishes local-testing difficulty under permanent arrivals, within its stated feasible regime. |
| Extra assumptions are harmless. | State exactly what additional conclusion the assumptions enable and compare a simple baseline under the same assumptions. |

可以坚定地捍卫“需要单独研究的结构化增长问题”，但对“我们已经解决了它，并且优于强基线”的表述，仍应以完成的证据为界。
