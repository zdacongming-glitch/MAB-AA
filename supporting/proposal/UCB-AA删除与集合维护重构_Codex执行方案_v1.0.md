# Codex 执行方案：删除原 UCB-AA，重构为可靠近优集合维护论文

**版本：v1.0｜编制日期：2026-10-16｜用途：交给 Codex 执行的稿件编辑任务书**

> **默认执行范围：在不改变现有数学结果和实验记录的前提下，完成结构重排、原 UCB-AA 专题移除、Checkpoint-UCB 展示完善、引用与证明迁移、实验叙述整理以及编译验收。**
>
> 新定理、新算法、新一轮比较实验不属于本轮默认任务。它们应进入独立待办文件，不能为了让修改稿看起来完整而写成已经完成的工作。

---

## 使用顺序

先执行 **§0–1 的范围确认与源文件发现**，再按 **§3 的 A-00 至 A-22 任务卡**重构。**§4–5**给出图表与补充材料迁移表；**§6–8**是数学、算法和数据的不可误改合同；最后按 **§10–11**交付与验收。**§12 只登记后续研究，不自动执行。**

本任务书中的来源引用和 PDF 页码用于定位；不要把这些 ChatGPT 引用标记复制进论文。正文仍应使用项目原有 LaTeX 文献与交叉引用系统。

---

## 0. 给 Codex 的启动指令

请阅读本文件后，直接执行下文标为 **A：本轮必做** 的任务；不要重新讨论是否保留原 UCB-AA。该取舍已经确定：**原两阶段 elimination 型 UCB-AA 不再作为新稿的研究对象，也不在投稿版补充材料中保留完整专题。**旧版本、源代码和原实验数据仍须完整归档。

新稿围绕一个主问题展开：

> **在臂持续到达、奖励分布保持平稳的条件下，为了可靠且及时地维护全部相对近优臂，在累计 regret 上必须付出什么成本，又有哪些成本是可达到的？**

新稿应以维护成本下界、最坏维护面积和临时资格任务的 regret 权衡为主要贡献；检查点策略承担可达性构造的角色，而不是被包装成在所有有限预算实验中普遍占优的新方法。

### 0.1 本轮授权与禁止事项

| 级别 | 含义 | 默认处理 |
|---|---|---|
| **A：本轮必做** | 由当前稿件与已确定取舍支持的删改、迁移、伪代码展开、现有材料重新组织 | 直接执行；逐项提交验收记录 |
| **B：依赖现有资源** | 读取已有源代码、配置、逐次运行记录以核对数字或重新排版图表 | 资源齐全时执行；缺少资源时标记阻塞，不补造材料 |
| **C：后续研究** | 新证明、改变算法行为、新模拟、扩展理论范围 | 只建立待办，不在本轮自动执行，也不把结果提前写进稿件 |

禁止以下操作：

1. 不得把用户上传的 PDF 当成可直接删页编辑的论文源文件。删除的是内容及其论证依赖，不是机械删除某几页。
2. 不得猜测当前项目主文件叫 `main.tex`、`manuscript.tex` 或某个固定路径；先发现真实入口。
3. 不得为了消除引用错误而删除核心定理、删掉必要假设，或者把未证明命题改写成事实。
4. 不得改变奖励模型、比较器、标签风险、未决量定义或上下界量词。
5. 不得改动已有实验的均值、标准误、参数、重复次数、原始方法 ID 或原始数据。
6. 不得通过把 CP 策略改成动态精度、自动停止或硬删除版本，再继续使用原来的定理和数值结果。
7. 不得把独立的 temporal-geometry 论文中的寿命谱、容量或 MC-MOSS 主定理搬进本稿。
8. 不得销毁旧版本、实验存档或用户已有未提交修改；不得执行 `git reset --hard`、`git clean` 或强制覆盖历史。
9. 不得未经用户另行授权提交到外部仓库、覆盖公开发布版本、向期刊上传或发送材料。
10. 不得将本次编辑或编译通过描述为“全部证明已获独立验证”。

### 0.2 执行完成的定义

本轮完成，指**新主线下的一版可读、可编译、来源与依赖可追溯的修订稿**完成，不指所有后续研究缺口已经解决，也不自动等于论文已达到投稿完成度。

如果当前工作区只有 PDF、没有对应的可编辑源文件：完成源文件清单与内容迁移定位，将实际修改标为 `BLOCKED_SOURCE`，说明需要什么文件；不要声称已经生成修订后的完整 LaTeX 项目。

---

## 1. 输入版本、来源优先级与工作区边界

### 1.1 本方案锁定的稿件

| 代号 | 文件及身份 | 版本识别 | 用途 |
|---|---|---|---|
| **M** | `manuscript(2).pdf` | 29 页；题目 *Multi-armed bandits with arriving arms: sequential screening and reliable set maintenance*；日期 October 15, 2026 | 本次正文删改的唯一主基线 |
| **S** | `supplement(2).pdf` | 35 页；与 M 配套；日期 October 15, 2026 | 本次证明与附录迁移的唯一主基线 |
| **C** | `ucbaa_continuous_maintenance_2026-10-14/cp_ucb_aa.py` | 已有固定精度 CP 参考实现 | 展开伪代码及核对算法运行语义；不是 5,760 次实验的完整工程 |
| **R** | `持续集合维护_理论与完整证明.md`、`proof-audit.md` 及相关阶段性记录 | 2026-10-14 研究记录 | 仅用于追溯，不得以旧记录覆盖 M/S 的后续更新 |
| **G** | 题目为 *The Temporal Geometry of Bandits With Arriving Arms* 的正文及补充材料 | 独立工作；项目内可能存在重名或不同后缀 PDF | 只读、禁止修改；只在已有可靠书目信息支持时简短说明研究分工 |

本次编制方案时实际读取的文件摘要：

```text
M SHA-256:
eeecbd9680c3f14f046e9f898379f6abbb505f5195405a144552ff207ba2386d

S SHA-256:
f2d4ebeec121c1f7e03405da8ff4273facde5d69f48ab2cadc0af8db348d0d6e

C SHA-256:
272815cbb45e2de1a99f849bd4718892ef6bc010d081e0eaf2ec45b21c746ef9
```

上述文件在本次会话的参考位置分别为 `/mnt/data/manuscript(2).pdf`、`/mnt/data/supplement(2).pdf` 及 `/mnt/data/ucbaa_continuous_maintenance_2026-10-14/cp_ucb_aa.py`。**这些不是 Codex 本地仓库的假定路径。**Codex 必须在其实际工作区定位对应源文件。

M 已含新任务和主要结果；S 还含旧算法整套证明，因此须同时重构两者，不能只修改摘要和正文。fileciteturn42file1L13-L29 fileciteturn42file0L31-L40

### 1.2 来源优先级

采用以下优先级：

**用户已确定的删改决策 → M/S 的实际现行陈述与证明 → 对应真实代码和数据 → 阶段性研究记录 → 本方案的编辑建议。**

含义如下：

- 用户决定了取舍，但没有授权扩大定理范围。
- 本方案中的公式快照是防误改检查表；若与真实 LaTeX 源码或 PDF 不一致，先登记差异并核对，不得自动将快照覆盖进源文件。
- 源码若已比 M/S 更新，保留用户新修改，建立版本差异表；能定位的同义部分继续执行，实质冲突单独报告。
- 新稿仍用英文写作；本执行方案和变更日志可用中文。
- 不改变作者顺序、机构、通讯作者、共同贡献标识、致谢或盲审设置；不得凭推测补写这些信息。

### 1.3 源码定位与备份：任务 A-00

**操作：**

1. 查看版本状态，识别用户已有未提交修改。
2. 搜索 M 的完整题目及 `Reliable maintenance of the near-optimal set`、`Broadcast uncertainty` 等现有标题，定位真正的正文入口。
3. 搜索补充材料标题及 `A fixed-budget analysis of the screening-based UCB-AA procedure`，定位配套附录入口。
4. 建立实际 `\input`、`\include`、图片、表格、文献库、宏文件和编译入口依赖图。
5. 保存只读快照或使用现有版本控制记录；对不受版本管理的独有文件另作副本。
6. 确认独立 G 论文的源文件和共享资源。若共享同一个 `.bib` 或宏文件，不得为本稿清理而破坏 G。

**输出：**建议在一个实际新建且不冲突的编辑工作目录下产生 `source-manifest.md`。本方案以下将该目录称为 `<REVISION_DIR>`，其真实路径由 Codex 明确记录。

**验收：**清单列出真实源文件、对应基线版本、受保护文件、缺失资源及实际编译命令；没有把不存在的 `.tex` 文件写成已发现的资源。

---

## 2. 新稿的唯一主线和目标结构

### 2.1 冻结的定位

建议采用题目：

> **The Cost of Reliable Near-Optimal Set Maintenance with Arriving Arms**

核心问题用以下含义组织，而不是另造目标：

> 在相同的相对近优标准、报告错误要求和累计未决量预算下，刻画必要 regret 与可执行策略能达到的 regret。

原两阶段 UCB-AA 退出新稿。固定精度 CP 构造改用描述性展示名称 **Checkpoint-UCB**；重命名不计为新的方法贡献。实验原始 ID 和历史代码名保留映射。

### 2.2 目标正文目录

| 新节 | 建议标题 | 主要来源 |
|---|---|---|
| 1 | Introduction | 重写 M §1 与摘要，复用其中新任务和近邻定位 |
| 2 | Model, Reliable Reports, and Maintenance Cost | M §2.1 与 §5.1；必要的模型结构解释 |
| 3 | A Checkpoint Construction for Joint Guarantees | M §5.2、Proposition 5.1；增加正式伪代码 |
| 4 | Fundamental Costs of Continual Maintenance | M §6；先共同影响，再最坏面积，再增长率与突发边界 |
| 5 | Temporary Membership Tasks and Regret Trade-offs | M §7；提升 S7 的联合上界，保留概率加强 |
| 6 | Numerical Studies | 仅 M §8.2 与 S15 中的新报告实验；未开展实验不占完成态正文 |
| 7 | Discussion | 重写 M §9，删除旧算法的验证义务 |
| — | Data and Code Availability；References | 按真实新稿依赖清理 |

**不要求新稿保持旧页数。**不能用新增无关综述、旧定理或字号压缩填补／挤压篇幅。

### 2.3 主要贡献的允许表述

正文贡献清单固定为三个实质层次：

1. **共同认证影响：**一个尚未被排除为高质量的新臂，可以同时阻碍多个旧候选的正认证；下界可在同一参考环境中跨时间累加。
2. **最坏维护成本：**在明确参数范围与风险协议下，累计未决面积有常数因子匹配的最坏日程阶数，并有相应增长率结论。
3. **临时任务与收益权衡：**在明确的多次更新实例族和规定时域中，快速维护有匹配的逆平方必要成本；更宽松面积预算有显著更小的可达 regret 上界，并有快速成本的非消失概率加强。

算法列为实现这些上界的显式构造。不得写“我们首次提出 arriving-arm 模型”“首次联合 regret 与识别”“一般 Pareto 前沿已解决”或“Checkpoint-UCB 全面优于所有强基线”。这些都不是 M/S 支持的结论。M 对实际覆盖范围和算法角色已有明确区分。fileciteturn43file0L431-L463

---

## 3. 正文逐项执行卡

以下页码一律指基线 M 的 PDF 页码，从 1 开始；重排后页码会变化。执行时必须使用**章节标题、定理标题、公式内容和真实 LaTeX label**定位，不能按页码切割源码。

### A-01｜题目、摘要、关键词和 PDF 元数据：重写

**原位置：**M p.1，题目、Abstract、Keywords。

**执行要求：**

- 主标题采用 §2.1 的建议题目；补充材料标题同步修改。
- 摘要移除原 UCB-AA 的预筛选、两阶段架构、接纳延迟分解和修正旧分析的叙述。
- 摘要直接从持续可靠报告和累计收益的联合任务开始；依次交代共同认证负担、最坏面积、规定实例族上的快速／暂缓权衡、非消失概率下界、检查点可达性和有限预算局限。
- 叙述逆平方与对数分离时，必须出现“a specified repeated-update family”或等义限定；不能写成任意到达模型的普遍分离。
- 检查点构造不得在摘要中被称为数值普遍最优。保留模拟揭示保守认证成本的结论。
- 关键词建议使用 `sequential experimentation; arriving arms; near-optimal set maintenance; dynamic regret; simultaneous inference`。这是编辑建议，不是新术语的创新主张。
- 作者、机构和贡献说明保持原样。日期遵循当前项目实际版本机制，不手填虚构发布日。

**验收标准：**摘要不再以原 UCB-AA 为主语；不把“附加报告功能”作为后半段补充问题；新题目同时出现在正文、补充材料及可编辑的 PDF metadata 中；所有实质主张都能指向保留结果。

### A-02｜引言：由“筛选算法故事”改为“持续报告成本问题”

**原位置：**M §1，pp.1–4；精确锚点包括 `Methodologically, the two challenges`、`UCB for Arriving Arms (UCB-AA) implements this screening design`、`The active set alone does not describe`。

**执行要求：**

1. 保留外生新候选不断出现、旧臂永久可用、均值平稳的基本动机。
2. 开篇一到两段内说明两个目标：获得奖励，以及可靠、及时地报告全部相对近优候选。
3. 删除为原预筛选设计服务的两段方法介绍、原算法上界与 unknown-horizon wrapper 的贡献介绍。
4. 将原文“we then ask”“a further question”“additional maintenance analysis”等年代式叙述改为直接陈述本文主问题。
5. 用数学边界 `r^*(t)-ε` 解释旧臂均值不变但报告目标随新臂变化；不要把基准变化写成旧奖励分布漂移。
6. 复用当前引言已经给出的 sleeping／ballooning、ALL-ε、联合收益与识别文献定位；只压缩和重组已有内容，不在本轮开展无边界文献更新。
7. 对一般统计 bandit 历史介绍压缩到一个紧凑段落。与当前问题没有直接作用的文献可以不再在正文引用，但不得改写其原有结论。
8. 用 §2.3 的三层贡献结束引言，并更新全文导航。

**验收标准：**未读过旧稿的读者可以独立理解研究问题；“模型／比较器不是新提出的”这一来源边界仍保留；引言没有以旧算法被审稿质疑作为论证依据；没有独立 G 论文的定理被计为本稿新贡献。

### A-03｜原 Figure 1 与 oncology 专属材料：移出新投稿包

**原位置：**M p.2，FDA approval 图及图注；摘要之外相关 oncology 动机段；M 数据声明中的 oncology 句子。

**执行要求：**

- 从新正文移除整幅 FDA 图及其图注。原始图片、公开数据来源和旧稿中的使用记录保留在只读历史档案。
- 删除依赖该图的精确治疗数量、年份趋势和“original submission”叙述；可以保留不含额外经验断言的通用序贯实验动机。
- 默认不新增替代图片。可先用一个文字／公式例子解释资格边界变化；将来绘制示意图属于单独展示工作，必须明确不是实验结果。
- 文献列表不再展示仅服务于已删除图的 FDA 项，但共享 `.bib` 中的原条目不物理删除。

**验收标准：**新稿不再引用旧 Figure 1；图序号自动重排；没有因删除图而留下“as shown above”等悬空句；旧资源仍可追溯。

### A-04｜原 §2.1：保留基础模型，移除旧轮次负担

**原位置：**M pp.4–5，`Problem formulation`。

**保留：**`A_t`、`τ_i`、`K_t`、独立平稳 bounded 奖励流、`Y_{i,n}` 潜在观测、策略信息集、`N_i(t)`、`r_i`、`r^*(t)`、`Δ_i(t)`、确定终点 `R_T`。

**执行要求：**

- 保持 `r_i` 为均值、`r^*(t)` 为当前最佳均值，避免为“更统一”而全稿改成另一份研究记录的 `μ_i,B_t`。
- 到达先于动作、每轮仅观察所选臂一次、报告晚于该次观察；这些顺序写入模型。
- 写明 `A_1≠∅`、每个有限时刻 `K_t<∞`、允许任意有限批次和 `K_T>T`。
- 保留与奖励及策略随机化独立的外生到达约定；基本定理按固定确定日程陈述。不能把随机日程期望与对环境的上确界擅自交换。
- `R_T` 为随机 pseudo-regret，`E R_T` 才是期望；不要写成 realised reward loss。
- 删除“algorithmic rounds are indexed separately by m”等只服务于旧 UCB-AA 的说明。窗口索引 `e` 和证明停止时刻仍按后文需要单独定义。
- 确定终点为主；停止时刻工具留在证明部分。若保留 `R_τ` 的一般定义，必须保留“不因此推广确定终点定理”的说明。

**验收标准：**新模型不需要 `M_T,N,n_p,b_p,C_m,A(m)` 就能定义；没有把分析窗口、算法时钟和真实物理时间混为一谈。

### A-05｜原 §2.2：压缩 AID／DB，改为两种认证机制

**原位置：**M p.5，`Main statistical challenges`。

**执行要求：**

- 不再把 AID、DB 缩写作为核心贡献或关键词；可以在通俗文字中保留样本不平衡与基准非减的事实。
- 将有价值的解释并入新 §2 或引言：一个未知新臂影响多个旧报告；新参照可以使旧精细资格问题不再需要。
- 明确对旧臂 `Δ_i(t)` 非减，但 `|Δ_i(t)-ε|` 不必非减；不能把边界距离与收益 gap 混用。
- 区分真实资格的单向变化与统计正标签的反复更新；不得声称所有算法的负标签在坏事件上都是真实正确的。

**验收标准：**剩余文字直接解释新指标与后面定理；没有“因此必须采用预筛选”的结论。

### A-06｜原 §2.3 三项 regret 分解：移出正文，保留为基线记账

**原位置：**M p.5，`Admission and retirement in the reward account`，原式 (1)；新实验的 Batch100-UCB 分解见 M pp.24–25。

**默认决定：**本轮保留现有九方法比较中的 Batch100-UCB，因此保留一份通用分解，但放入新附录 A13 的 computational details，不保留旧 UCB-AA 专属版本。

**执行要求：**

- 迁移通用的 admitted／reward-active 定义与路径分解。保持选中臂属于非空 reward-active set 的条件。
- 删除“revised UCB-AA comparisons make the third term zero”等旧算法专属推论。
- 对 Checkpoint-UCB 仅说明所有已到达臂立即进入收益可选集，故 admission 与 retirement deficit 两项恒为零；不保留为主要定理。
- 从新正文移除旧轮次形式 `R_round+H_T+D_T` 及延迟曝光公式，除非原实验计算明确还需引用。现有 Batch100 数据使用的通用记账不得丢失。

**验收标准：**正文主理论不依赖该分解；Batch100 记账仍有明确来源和定义；没有以较小 active set 代替完整可靠报告。

### A-07｜原 §3 UCB-AA：整体移出新稿及投稿附录

**原位置：**M pp.5–9，`UCB for Arriving Arms (UCB-AA)`、Algorithm 1、Theorem 3.1、Corollary 3.2。

**必须移除的内容：**

- 两阶段预筛选与正式淘汰算法；`Elim(S,R,p)` 伪代码。
- 缓冲接纳的 algorithmic rounds、`M_T,N,\widetilde\Delta_p,n_p,b_p` 校准。
- 本算法的固定预算定理、静态／固定 gap 推论、physical-time doubling wrapper 的正文说明。
- 旧算法的 best-admitted-arm survival、回顾原修复工作的文字和相应示例。

**执行要求：**先在 dependency map 中标记所有引用，然后删除旧专题。对后文仍需要的普通集中不等式和 distinct-count 理由，从现有 S3/S7 中引用或迁入统一工具，不要把旧 Theorem 3.1 作为新上界黑箱。

**验收标准：**新的正文和投稿附录里均没有完整旧 UCB-AA 算法或其专属定理；旧源片段和旧图仍存在于不参与新稿编译的档案；不再保留“需重跑修正 UCB-AA”作为未来工作。

### A-08｜原 §4 纯 regret 专题：整体移出，保住共用信息工具

**原位置：**M pp.9–11，Theorems 4.1、4.2；S §S2。

**执行要求：**

- 移除 inferior arrivals／static specialization 的 uniform-goodness 下界专题。
- 移除 successive near-tied benchmark improvements 的纯 regret 构造、`J=O(T^{1/3})` 可行性说明及对应定理。
- 不把这些量直接改名为报告边界 `d`；二者原本是不同目标。
- S2.1 中仍被新证明使用的事件 KL、Pinsker、bounded-variable TV 和自适应历史 KL 工具，应与 S3 去重合并到新附录 A1。保留精确适用条件和文献出处。
- 新稿中不把被删除结果重新包装成新集合维护定理，也不以独立 G 论文结果替代填充。

**验收标准：**新正文无原 Theorems 4.1/4.2 的残余交叉引用；新证明需要的每个共用引理仍有可解析的定义／证明位置；`J=O(T^{1/3})` 不再作为本稿维护可实现性边界出现。

### A-09｜原 §5.1：提前并成为新 §2 的核心

**原位置：**M pp.11–12，`Reporting reliability and unresolved time`，原式 (13)–(14)。

**执行要求：**

- 保留目标 `G_t^ε={i∈A_t:Δ_i(t)≤ε}`，以及报告划分 `\mathcal P_t,\mathcal N_t,\mathcal V_t`；不再需要以“区别于 UCB-AA survivor set”作为定义前言。
- 保留全过程事件 `E_lab`、full-model reliability、边界带外未决量、联合风险和受限最坏 regret `\mathfrak R_Θ(a)`。
- 新增一个符号表解释 `ε,δ,η,ρ`，仅展开原有含义，不改变统计任务。
- 明确未决量包括刚到达但零样本的臂，也包括新到达导致的旧正认证撤回后等待；不能改成只计第一次判断前的时间。
- 真均值只用于评价与理论分析；算法不能直接检查 `d_i^ε(t)>η` 作为停止条件。
- 继续写清 full-model 标签可靠性与 performance family 上面积保证的区分，以及不可行策略类对应 `+∞`。

**验收标准：**通过下文 §6.1 的所有风险定义锁定项；全篇没有 FDR、期望面积、固定截止任务或模糊的“两目标各自最优”偷换主协议。

### A-10｜原 §5.2：改名为 Checkpoint-UCB，增加完整算法

**原位置：**M pp.12–13，原式 (15)–(18)；C 的 `choose/observe/report`。

**执行要求：**

- 新正文统一展示名 `Checkpoint-UCB`，新增 Algorithm 1。原 UCB-AA Algorithm 1 已删除，不保留两个“主算法”。
- 执行语义严格按下文 §7 伪代码合同：全部接纳、偶数 FIFO 服务、其余全历史 UCB、共享累计计数、一次固定报告检查点、负标签不删除收益选择资格。
- 保持 `q_i(ρ)`、报告半径 `ρ/2`、UCB bonus 中的 `3 log(2t)`、零样本无穷大和平局规则。
- 事先固定的异质 `ρ_i` 或 `ρ_e` 只作为现有定理允许的配置扩展；主伪代码展示共同 `ρ` 即可。
- 不在本轮改公共代码的类名、函数签名或原始方法 ID。只做论文展示名和日志映射；如必须增加新别名，保持旧接口可用并做等价核对。
- 不把冻结报告区间改成全前缀收缩；后者是实验中的另一个报告组件，不能继承固定检查点所有界。

**验收标准：**伪代码无需真实均值、真实近优集、未来到达或评估终点即可逐轮执行；见 §7 的全部状态检查。

### A-11｜Proposition 5.1：保留为基础联合保证

**原位置：**M p.13，`Simultaneous reporting and unconditional reward cost`；S7 pp.19–20。

**执行要求：**

- 迁移为新 §3 的 proposition，保留 `P(E_lab)≥1−δ/2` 和同一算法的期望 regret 式。
- 保留 service slots 的集合 `\mathcal I_T` 与路径上 `|\mathcal I_T|≤\sum_iq_i`。
- 强调样本被同一 lifetime count 记账；插入服务会跳过部分 UCB 的选前计数，不会重复同一 arm-count pair。
- 保留对收益层的独立、可求和集中分析，不通过条件化报告正确事件来计算期望，不恢复 `δT` 遗漏。
- 不把这个基础上界解释为“额外识别真实只增加这么多 regret”的两算法轨迹差值，也不称其为主要最优性结论。

**验收标准：**与 §6.2 的公式相同；证明不再引用旧筛选定理；服务次数和全部样本次数明确区分。

### A-12｜Theorem 6.1 与队列解释：保留为新 §4 首个主要结果

**原位置：**M p.14，`Broadcast uncertainty`，原式 (20)–(21)；S4 pp.15–16。

**执行要求：**

- 保留一个共同参考环境与逐候选备择的构造、全部参数范围、分析队列和加权忙期量。
- 明确 `Q_t` 是信息容量的分析证书，不是 Checkpoint-UCB 的 FIFO 队列，也不是每条臂无条件必须采到的算法配额。
- 保留期望下界及 `1/4` 概率下界，不能只留下“有二次成本”的非定量段落。
- 保留从**期望样本数**中选取确定难臂标签的论证，不改成在样本路径上挑选最有利标签。
- 保留全时间使用同一参考环境的说明；不能使用不兼容的逐时最坏环境相加。
- 队列的最后服务轮必须保持“观察后报告”的端点处理，保留 `(q−1)m(m−1)/2`，不能写成未经证明的 `qm(m−1)/2`。

**验收标准：**定理与 §6.3 数学锁一致；第一项动态机制与后面的静态突发最坏下界明确区分；没有声称每次新到达必定撤回所有旧正标签。

### A-13｜Theorem 6.3、Corollary 6.2 与突发反例：重排并锁定量词

**原位置：**M pp.15–16，`Arrival-growth boundary`、`Worst-schedule area and joint attainability`；S7、S10。

**目标顺序：**共同认证下界之后，先给最坏面积定理，再给增长率推论及不同量词的限制。

**执行要求：**

1. 保留 `\mathfrak A_{T,K}` 的 minimax／概率风险定义；优化面积本身时不能暗加固定 regret 预算。
2. 保留全部参数范围、`min{KT,K²η^{-2}log(K/δ)}` 截断、明确常数和同一 CP 构造的 regret 上界。
3. 保留最坏下界由初始静态大批量到达达到的说明；统计 `log K` 因子不作为新的动态发现宣传。
4. 增长率段区分三种陈述：给定无限日程的必要条件；`K_t≍t^α` 的指数边界；按每个终点总臂数上限定义的统一日程类边界。
5. 保留稀疏但突发日程反例和“困难环境允许依终点变化”的量词说明。完整构造证明在附录，正文可压缩。
6. 对原 Corollary 6.2 的引用接口作**显式编辑修正**：原文的 `η<ε/2` 范围比 Theorem 6.3 的 `η≤ε/32` 宽，因此把 `The sufficiency follows from the next theorem` 改为引用 S7 迁移后的一般检查点完成上界。不要默默缩小 corollary 的范围，也不要放大 Theorem 6.3。若实际源码中的一般完成引理不足以支持该范围，登记为阻塞，由作者决定数学修正。

**验收标准：**读者可以明确回答“对什么日程、什么环境、什么参数、哪个风险模式、同一策略还是逐终点策略”成立；没有无条件的 `K_t=o(√t)` 充分性。

**来源说明：**上述引用范围差异可直接见 M p.15；一般完成界在 S7 中单独给出。本任务是修复依赖指向，不是提出新数学结论。fileciteturn43file0L221-L253 fileciteturn40file2L350-L365

### A-14｜原 §7.1 多次更新族：保留并提前解释两种 gap

**原位置：**M p.16，原式 (25)–(26)。

**执行要求：**

- 将其作为新 §5 的起点，完整保留 `J,M,ε,δ,v,d,η,H,T` 的关系。
- 在公式后直接写出当前候选的收益 gap 是 `ε−σd`，资格边界距离是 `d`；下一参照到达后 gap 为 `ε+v−σd`。
- 保留所有奖励为 Bernoulli、所有臂永久可用、每批内部任意标签排列、主策略不知道参照身份的设定。
- 最后一批仅有新参照；最终近优集合是**所有参照**，不是只有最后一个参照。
- `Jv≤ε/4` 是真实范围限制：不能声称在固定 `v>0,ε` 下任意增大 `J`。
- 不把暂时有效的分类任务写成臂本身消失，也不把 `d↓0` 写成同一条固定臂的均值随时间变化。

**验收标准：**不同符号环境在同一个合法到达实验中兼容；主算法信息与下界允许额外披露的信息明确区分；未引入“已知最佳臂”输入。

### A-15｜原 §7.2：保留半完成逻辑，把长松弛公式移入附录

**原位置：**M pp.16–17，原式 (27)–(28)；S5、S6。

**执行要求：**

- 正文保留部分同时恢复引理的必要样本阶数，以及低面积要求为什么迫使足够多窗口达到半完成的解释。
- `\Phi_δ`、`g_{m,δ}`、异质完成概率 `p_e` 的完整定义与凸分配松弛迁到新 A6；正文保留简短指向。
- 不在同一版正文／附录中重复给出两份略有差异的 `g` 定义。
- 证明中的共同乘积先验是工具，不把统计任务改成 Bayesian policy requirement。
- 保留适应性采样、bounded stopping、无关观测不编码当前符号、条件后验因子化等接口；不写随机样本计数独立。
- 保留一般松弛“必要但未证可达”的地位；不把定义优化问题等同于已经解决了一般 Pareto 前沿。

**验收标准：**正文的快速成本下界有完整依赖指向；附录不丢失失败概率、半完成概率或同一环境的兼容性；不会把“每批都有硬截止承诺”偷加到主任务。

### A-16｜Proposition 7.1：提升为同时呈现面积与收益的共享证据结果

**原位置：**M pp.17–18，原式 (29)–(30)；S7 pp.20–21。

**执行要求：**

- 保留 `H_e≥2S_e`、总体参照增量、邻批精度与改善差距等完整条件。
- 将 S7 已有的**无条件期望 regret 上界**迁入正文，与面积式放在同一 proposition 或紧随其后的 corollary。只迁移现成结果，不改变常数或适用类。
- 在同处定义 `γ_i=min_{t:Δ_i(t)>0}Δ_i(t)` 和 `D_i^T=max_{t≤T}Δ_i(t)`；仅对存在正 gap 的臂求和，避免除零。
- 解释每臂 `q_i` 是 lifetime 总量；旧候选退休用旧上界与新参照下界，无需为同一次证据复用重新收全体旧臂费用。
- 严格写明“无需新增旧臂观测来完成该报告”，不是“从此收益层完全不采旧臂”。
- 保留 `H_e≥2S_e` 用来确保配额样本发生在出生窗口的作用；不得把这个第一项计费直接推广到任意重叠到达。

**验收标准：**通过 §6.5 数学锁；新增正文公式可以逐字追溯到 S7，而不是“推测应当成立”的上界。

### A-17｜Theorem 7.2：保留两端结论，不夸大匹配范围

**原位置：**M p.18，原式 (31)–(33)；S8。

**执行要求：**

- 完整保留 `K,L_K,q_f,q_c,H,V,T` 和 `ρ_f,ρ_c` 的定义关系，不省略规定终点。
- 对同一 `Θ,ε,η,δ,T` 比较 `V/8` 与 `9V/8`，保持前者上下界匹配、后者只有上界。
- 保留 `d↓0` 时固定哪些参数，以及 `η=d/2`、`T=Θ(d^{-2})` 同步变化。
- 保留快速上界在规定族中使用 `R_T≤2εT` 的事实；不把它宣传为任意长窗口下的尖锐新算法性能。
- 粗精度是预先选定配置，不宣称已实现对未知改善尺度 `v` 的自动适应。
- 不把面积预算扩大 9 倍解释成每条臂的个体延迟恰好扩大 9 倍；也不说暂缓策略满足快速面积预算。

**验收标准：**所有局限都出现在定理附近或同节固定的“Scope”段，而不是只藏在 Discussion；没有完整前沿、一般实例最优或暂缓端匹配的新主张。

### A-18｜Theorem 7.3 与 S11.3：保留概率加强

**原位置：**M p.19；S11 pp.24–26。

**执行要求：**

- 保留 `11/80` 非消失概率下界及固定环境的结论；不能改成 `1−δ` 概率下界。
- 保留相同累计面积协议，而不是换成逐批 deadline。
- 主文说明该结果支持快速端的联合 regret 分位版本；精确 `\mathfrak R_Θ^{joint}` 定义与推论保留在附录 A8，或正文用一个简短推论引用。
- 保留预算截断在 `q+1` 个候选样本处停止的细节；不能简化到第 `q` 个样本，从而漏掉随后参照观测带来的完成。
- 不假定各窗口完成事件独立；保留共同先验到固定环境的转换。

**验收标准：**期望风险、非消失概率 lower 和 joint high-probability upper 三者分别写清；辅助推论不被当成暂缓端的联合高概率最优性。

### A-19｜原 §8.1 与 archived 实验：整体移出投稿包

**原位置：**M pp.19–20，Table 1；S16 pp.31–34。

**执行要求：**

- 原两环境的 archived UCB-AA 表和全部对应图，从新正文及新投稿附录中同时移出。
- 有利和不利结果一起归档；同时删除由它们支持的优越性、较小活跃集、减少 wasted pulls 的新稿主张。
- 原代码、配置、源快照、结果及版本限制说明继续留在项目历史档案，不覆盖、不重命名为 Checkpoint-UCB 实验。
- 新稿不再承诺重跑修正 UCB-AA、不再新增预筛选消融任务。
- 注意：这里移除的是旧 §8.1 的整套实验，不是从新 §8.2 中选择性删掉 CP 的不利表现。

**验收标准：**新正文只保留与可靠维护任务直接相关的实验；60,000 轮／100 次重复／旧 survivor pool 的结果不会混入新 20,000 轮／160 次重复的表。

### A-20｜原 §8.2：保留全部新报告实验，重组为有限预算证据

**原位置：**M pp.20–25；原 Table 2、Figures 2–3；S15 的 allocation table 和 Figure 1。

**默认决定：**保留已有九方法、四环境和全部 5,760 次报告实验的结论范围；不在本轮增删算法运行，不重新选择有利 seed。

**执行要求：**

1. 新第6节从联合任务和评价协议开始，不再以“additional experiments”相对旧 UCB-AA 介绍。
2. 保留 Bernoulli 奖励、`T=20,000, ε=.30, η=.10, δ=.05`、终点8臂、每环境每方法160次重复、共同潜在流以及物理时间顺序。
3. 原 Table 2 迁为新主表；数字、标准误、面积单位 `10^3` 全部不变。原表为六方法，图中九方法，附录含分配诊断；这个展示关系保持明确。
4. `CP-FIFO`、`CP-confidence`、`CP-period8` 等可作为配置短名保留，并在首次出现给出它们属于 Checkpoint-UCB 的说明；不要为了更名修改原始数据 ID。
5. 原 `ALL-ε adapt.` 继续称自然适配；不得改称真正的 FAREAST、`(ST)^2` 或新的原创算法。
6. 保留 Growing-MOSS 的实际 index 定义与“不能直接继承固定时域 MOSS minimax 定理”的限制。不得擅自替换为 G 论文的 MC-MOSS。
7. 保留 Batch100-UCB，但删掉 `reviewer’s proposed` 这类修订历史语句；清楚写实际接纳网格、收益退休、全物理臂报告和缓冲臂 `[0,1]` 处理。
8. 保留精细配置完全未分类、粗配置被强适配双指标改善、successive-improvement 中不同服务成本可能混杂机制的全部重要不利发现。
9. `ρ=.04` 满足 `2ρ<η`，不是 T8 所用的 `ρ=η/4=.025`；不得把现有精细实验写成 T8 配置完全相同的直接数值验证。
10. `ρ=.12` 的标签可靠性不等于对 `η=.10` 的一般完整性；两配置的完整性不能被标题或图例掩盖。
11. 把 admission／retirement 分解的细节放到新 A13；正文保留一两句解释和引用即可。
12. 本轮不新增“最优前沿已被实验恢复”“验证了渐近下界”或“新方法普遍占优”等结论。

**验收标准：**通过 §8 的全部实验数值与解释锁；缺少逐次数据时只能保留来源支持的汇总，不能逆向编造数据或新的 error bars。

**来源说明：**原稿明确报告了保守检查点在当前预算下的局限，并明确四个实验并非分离定理族。fileciteturn43file1L536-L567 fileciteturn43file1L631-L704

### A-21｜原 §9 Discussion：重写，删除旧算法义务

**原位置：**M pp.25–26。

**执行要求：**

- 开头总结维护成本与两个动态机制，不再总结原预筛选算法。
- 明确 Checkpoint-UCB 是可达性构造；理论阶数与有限预算效率不是一回事。
- 保留任意重叠到达的一般前沿、自动精度、暂缓端 converse 尚未完成的范围说明。
- 保留最终一致性属于另一个可复核、多精度策略，且要求到达停止、最终臂数有限和边界分离。
- 删除修正 UCB-AA 的重跑义务、预筛选必要性义务，以及无关的“保存两套方法”总结。
- contextual／delayed feedback／reward drift 至多保留一句远期扩展；不让它们盖过当前真正缺口，也不暗示现有定理已覆盖。

**验收标准：**讨论不将未来目标作为已完成结论；不因为本轮移除了旧算法，就把现有 CP 的数值劣势也抹掉。

### A-22｜Data and Code Availability、文献和复现说明：按实际资源重写

**原位置：**M p.26 与 References pp.26–29；S References p.35。

**执行要求：**

- 数据声明只围绕新稿实际使用的模拟配置、运行记录、代码和检查；不能写“没有生成数据”，因为本稿使用了模拟记录。
- 删除 oncology 图和旧实验作为新稿结果来源的句子；历史存档若仍实际随项目保存，可在 README 的 provenance 中说明，不必占据正文。
- `release contains 5,760 runs`、`public class`、公开代码链接等必须与当前可核实资源一致。只有 PDF 宣称、未找到实际资源时，不得声称本轮已核验发布；在 blocker 中登记并由真实资源状态决定最终措辞。
- 仅清理本稿不再引用的文献显示，不物理删除共享 `.bib` 条目，不影响独立 G 论文。
- 保留新证明使用的统计来源和现有近邻定位；不要凭作者名重建文献条目，也不要编造最新发表信息、DOI 或链接。
- 未经另行要求不更换模板、参考文献系统或整体字体；只修复新稿需要的引用与排序。

**验收标准：**没有未定义 cite key 或参考文献全库输出；源码、图表和复现说明的实际可用状态一致；所有旧结果出现在归档而非新研究贡献清单。

---

## 4. 图表和展示对象的迁移表

| 基线对象 | 新稿默认处理 | 验收重点 |
|---|---|---|
| M Figure 1，FDA 批准趋势 | 移出新稿和投稿附录，独立归档 | 删除其图注、正文引用、专属经验数字 |
| M Algorithm 1，原 UCB-AA | 删除 | 不改名冒充检查点算法 |
| 新 Algorithm 1，Checkpoint-UCB | 新增，依据已存在机制展开 | 算法语义不变；完整状态、动作、观察、报告顺序 |
| M Table 1，旧60,000轮实验 | 移出新稿和投稿附录，完整归档 | 有利与不利结果一并移出 |
| M Table 2，新报告实验 | 保留，重编号为新 Table 1 | 24个方法－环境条目、所有数字和单位保持一致 |
| M Figure 2，九方法 regret–area 散点 | 保留，重编号 | 不只保留 Pareto 表现好的点；不改成一条已证最优前沿 |
| M Figure 3，稳定／改善路径 | 保留，重编号 | 物理时间、arrival 标记、置信带说明保持 |
| S Table 1，Allocation diagnostics | 保留于新 A13 | 虽浮动到 S14 附近的 p.29，内容属于新实验，绝不能随旧专题删除 |
| S Figure 1，burst／stop 路径 | 保留于新 A13 | 不与旧档案 Figure 2–4 混淆 |
| S Figure 2–4，旧 archived 曲线 | 移出投稿附录，完整归档 | 所有子图和脚注一起处理 |

**B-01：图表重命名规则。**若有原绘图脚本和结果文件，可只修改展示文本再重绘，核对数值位置不变。若仅有现成图，可保留图中 `CP` 缩写并在图注给出名称映射；不得用手工覆盖图像伪造曲线或误差条。不得因为图中保留 `CP` 缩写就误判为旧 UCB-AA 尚未清理。

**B-02：float 迁移规则。**按 LaTeX 环境与语义迁移，不按 PDF 所在页机械删除。特别注意 S p.29 的 allocation table 与 S14 的已知参照说明交错排版。

---

## 5. 补充材料逐项迁移与证明依赖

### 5.1 目标附录目录

下表的新编号 A1–A13 是**建议源码组织标签**。最终 PDF 可按当前模板输出为 S1–S13，但交叉引用必须自动生成；不能在文本中硬编码旧编号。

| 基线 S 部分与页码 | 操作 | 新位置与执行要求 |
|---|---|---|
| 标题、Notation and scope，p.1 | 重写标题，保留任务约定 | 新附录开头；与新正文模型完全一致 |
| S1：旧 UCB-AA 固定预算、固定 gap、doubling，pp.1–9 | 整体移出投稿包 | 只保留历史档案；不可作为新证明依赖 |
| S2.1：Information inequalities，pp.9–10 | 按真实使用情况迁移并去重 | **A1 Probability tools and reporting conventions**；与原 S3 合并 |
| S2.2–S2.3：纯 regret 下界，pp.10–14 | 移出投稿包 | 删除对应证明、例子、label和新稿引用；保留存档 |
| S3：潜在流、prefix与checkpoint、历史KL，pp.14–15 | 保留 | **A1**；基础工具只定义一次，保留文献来源 |
| S7 的一般 UCB 与服务 regret 证明，pp.19–20 | 拆分保留 | **A2 Joint guarantee of Checkpoint-UCB**；一般 regret 不附加分离窗口条件 |
| S4：共同影响与队列，pp.15–16 | 保留 | **A3 Broadcast uncertainty and queue area** |
| S5：部分同时恢复与单窗口截断，pp.17–18 | 保留 | **A4 Partial simultaneous recovery**；被面积与多窗口证明共用 |
| S10＋S7 的一般完成界，pp.23–24及20 | 合并保留 | **A5 Worst-schedule area and growth consequences**；全日程上界与静态突发下界配对 |
| S6：面积迫使完成及异质松弛，pp.18–19 | 保留 | **A6 Area-constrained temporary tasks**；承接 A4 |
| S7 分离窗口复用＋S8，pp.20–22 | 合并保留 | **A7 Shared evidence and rapid/deferred endpoints**；与新正文联合 proposition 对应 |
| S11，pp.24–26 | 保留 | **A8 Regret quantiles under the same maintenance protocol**；保留 `q+1` 截断 |
| S12，pp.26–27 | 保留 | **A9 Compatible-window truncated area**；可重叠不等于任意重叠结构已被实现 |
| S9，pp.22–23 | 保留为扩展 | **A10 Eventual exact classification**；与固定精度算法隔离 |
| S13，pp.27–28 | 保留为扩展 | **A11 General information-allocation relaxation**；保留 `δW`，不声称可达 |
| S14，pp.28–29 | 保留为扩展 | **A12 Intermediate service configurations and disclosed-reference diagnostic**；额外角色信息必须显式 |
| S15，pp.29–30 | 保留、重写年代式描述 | **A13 Computational details**；包含新实验全表、补充路径及 Batch100 通用记账 |
| S16，pp.31–34 | 整体移出投稿包 | 旧实验完整归档，不挪到另一个新附录里继续充数 |
| References，p.35 | 清理本稿引用 | 保留所有新证明真正使用的出处；共享 `.bib` 不破坏 |

### 5.2 删除前必须完成的依赖记录

建立 `theorem-migration-map.csv` 或等价表，至少包含：

```text
source_file
source_section_or_label
source_statement_name
action = keep | move | remove | merge | rewrite
new_file
new_label
proof_dependencies
assumption_changes = none | separately_reported
status
```

对于从正文删除的每个 theorem、lemma、equation、figure label，必须搜索所有 `\ref`、`\eqref`、`\autoref`、`\cref`、`\Cref`、`\hyperref`、跨文档引用和文字硬编码引用。仍被引用的共用工具先迁移，再删除旧入口。

### 5.3 保留结果的最低依赖链

```text
A1 概率工具／报告覆盖／历史 KL
 ├─ A2 UCB 子序列＋共享实际计数 → 基础联合上界
 ├─ A3 同一参考环境＋队列 → 共同认证与必要增长条件
 └─ A4 部分同时恢复
      ├─ A5 初始静态批次 → 最坏面积 lower
      ├─ A6 多窗口完成 → 快速维护期望 lower
      ├─ A8 有预算停止 → 快速维护分位 lower
      └─ A9 兼容窗口截断 → 面积扩展

A1＋A2＋检查点完成队列 → A5 最坏面积 upper／增长充分性
A1＋A2＋分离窗口条件 → A7 共享证据／快速和暂缓 upper
A6＋A7＋A8 → 新正文第5节的主要权衡结果
```

A10、A11、A12 是扩展，不应被误当成一般最优性主链已经闭合的证据。核心新结果不应再经过旧 UCB-AA Theorem 3.1 或原 S1。

### 5.4 附录验收标准

- 保留结果有完整证明，不能只剩“proof follows from deleted Section S1”。
- 同名 `Lemma 1`、`Theorem 1` 等均有唯一实际 label；主辅材料跳转正确。
- 部分同时恢复的 posterior factorization 与 `κ` 定义没有在迁移中丢失。
- 一般 CP regret 与分离窗口的更细 regret 是不同范围的两条保证，不能合并为无条件一般实例式。
- S11 的概率强化、S12 的兼容性、S13 的不可达声明、S9 的有限到达要求仍在。
- “原稿曾如何修复”的元叙述移出，但必要数学假设不删。

---

## 6. 数学内容锁定表：重排时不得改变的合同

**本节用于防止编辑误改，并不取代原证明。**若发现原稿证明存在潜在问题，应在 `blockers.md` 记录准确位置、影响结果和需要的数学工作；不得以“编辑优化”为名偷偷改变假设或降低／增强结论。

### 6.1 模型与主协议锁

必须保持：

\[
A_t=\{i:\tau_i\le t\},\quad 1\le K_t=|A_t|<\infty,
\quad r^*(t)=\max_{i\in A_t}r_i,\quad\Delta_i(t)=r^*(t)-r_i,
\]

\[
R_T=\sum_{t=1}^{T}\Delta_{I_t}(t),\qquad
G_t^\varepsilon=\{i\in A_t:\Delta_i(t)\le\varepsilon\}.
\]

报告是在本轮观测之后、对全部 `A_t` 给出的互不相交划分：

\[
\mathcal P_t\cup\mathcal N_t\cup\mathcal V_t=A_t,
\qquad
E_{\rm lab}=\{\forall t:\mathcal P_t\subseteq G_t^\varepsilon
\subseteq A_t\setminus\mathcal N_t\}.
\]

\[
d_i^\varepsilon(t)=|\Delta_i(t)-\varepsilon|,\quad
U_t(\eta)=\sum_{i\in A_t}\mathbf1\{i\in\mathcal V_t,\ d_i^\varepsilon(t)>\eta\},
\quad\mathcal U_T(\eta)=\sum_{t=1}^TU_t(\eta).
\]

\[
\mathbb E_\theta R_T\le r,\qquad
\mathbb P_\theta\{E_{\rm lab},\ \mathcal U_T(\eta)\le a\}\ge1-\delta.
\]

额外审查：

- `≤ε` 的成员定义与 `>η` 的计罚定义保持；边界等号不能随意翻转。
- `\mathcal N_t` 是负报告集合，`N_i(t)` 是样本计数；不要混淆。
- `U_t` 是时点未决数，`\mathcal U_T` 是累计面积；不能因 PDF 提取丢失书法字体就把两者写成一个变量。
- 真均值、真实边界距离和真实最优标签不是算法信息。
- 所有正标签可能在到达后重新待定；可靠负标签的持久性来自平稳奖励和永久可用。
- 主面积保证针对每个确定终点；不能无证明地放大成同一事件上所有终点同时满足任意选定包络。
- 不把 `\mathcal U_T/T→0` 换成除以总 arm-time 的比例收敛。
- 不通过强加全模型 gap 下界排除本来允许的边界带环境。

### 6.2 检查点与基础联合上界锁

\[
q_i(\rho_i)=\left\lceil\frac{2}{\rho_i^2}
\log\frac{4i(i+1)}\delta\right\rceil.
\]

达到检查点以前用 `[0,1]`；达到后报告区间永久为

\[
[\ell_i,u_i]
=[\widehat r_i(q_i)-\rho_i/2,\widehat r_i(q_i)+\rho_i/2]\cap[0,1].
\]

收益 index 为

\[
J_i(t)=\widehat r_i(N_i(t-1))
+\sqrt{\frac{3\log(2t)}{N_i(t-1)}},
\]

零计数用 `+∞`，不截到 `[0,1]`。报告用

\[
\underline r^*(t)=\max_{i\in A_t}\ell_i,
\qquad \overline r^*(t)=\max_{i\in A_t}u_i,
\]

\[
\mathcal P_t=\{i:\ell_i\ge\overline r^*(t)-\varepsilon\},\qquad
\mathcal N_t=\{i:u_i<\underline r^*(t)-\varepsilon\}.
\]

注意上下横线和严格／非严格不等号，不要信任丢失装饰符号的 PDF 文本提取。

基础保证：

\[
\mathbb P(E_{\rm lab})\ge1-\delta/2,
\]

\[
\mathbb E R_T\le
\min\left\{T,\ K_T+4\sqrt{3K_TT\log(2T)}+1
+\mathbb E\sum_{t\in\mathcal I_T}\Delta_{I_t}(t)\right\},
\qquad |\mathcal I_T|\le\sum_{i\le K_T}q_i.
\]

`\mathcal I_T` 仅含指定认证服务轮；所有奖励轮也进入总样本计数。该式不是与未插入服务的另一条算法轨迹之间的差值恒等式。

### 6.3 共同认证下界锁：原 Theorem 6.1

范围为

\[
0<\varepsilon\le1/16,\quad0<\delta\le1/16,\quad0<\eta<\varepsilon/2.
\]

初始参照均值 `1/4+ε/2`；共同环境候选均值 `1/4`；第 `j` 个备择仅把候选 `j` 提高到 `1/4+2ε`。

\[
q_-=
\left\lfloor\frac{\operatorname{kl}(1/4,\delta)}
{\operatorname{kl}(1/4,1/4+2\varepsilon)}\right\rfloor,
\quad Q_t=(Q_{t-1}+q_-a_t-1)_+,\quad Q_0=0,
\]

\[
\mathcal B_T=\sum_{t\le T}(M_t-1)_+\mathbf1\{Q_t>0\}.
\]

\[
\mathbb E_0\mathcal U_T(\eta)\ge(3/4-\delta)\mathcal B_T,
\qquad
\mathbb P_0\{\mathcal U_T(\eta)\ge\mathcal B_T/4\}\ge1/4
\quad(\mathcal B_T>0).
\]

`a_t` 在本定理是到达候选数，`a` 在主协议是面积预算；不要通过误替换把两者合并。

### 6.4 最坏面积与增长量词锁：原 Theorem 6.3／Corollary 6.2

对 `K≥2,T≥1` 的整数，及

\[
0<\varepsilon\le1/8,\quad0<\eta\le\varepsilon/32,\quad0<\delta\le1/16,
\]

保留

\[
2^{-24}\min\left\{KT,\frac{K^2}{\eta^2}\log\frac K\delta\right\}
\le\mathfrak A_{T,K}\le
256\min\left\{KT,\frac{K^2}{\eta^2}\log\frac K\delta\right\}.
\]

同一策略使用 `ρ=η/4`，并有

\[
\mathbb E R_T\le
\min\left\{T,\ K+4\sqrt{3KT\log(2T)}+1
+99K\eta^{-2}\log(K/\delta)\right\}.
\]

风险优化是全模型可靠策略对所有 `K_T≤K` 日程与奖励环境的联合标签－面积概率保证。lower 允许更多未来信息，upper 不使用 `T,K`。

增长后果必须分开：

| 陈述 | 保留的含义 |
|---|---|
| 给定无限日程的必要性 | 对所有环境有确定 `a_T=o(T)` 服务包络，必须 `K_t=o(√t)` |
| 一般充分性 | `K_T²log(eK_T)=o(T)` 足以共同实现次线性期望 regret 和面积包络 |
| 多项式日程 | 固定合法任务参数，`K_t≍t^α,0<α<1` 时，指数边界为 `α<1/2` |
| 逐终点总臂数类 | 对每个终点允许所有 `K_T≤k(T)` 日程时，统一边界为 `k(T)²log k(T)=o(T)` |
| 突发反例 | 有一条 `K_t=o(√t)` 日程仍不支持全环境统一 `o(T)` 面积；困难环境可随终点变化 |

不得把这些不同量词整理成一条无条件的等价链。

### 6.5 共享证据联合上界锁：原 Proposition 7.1＋S7

对现有异质 repeated-update family，保留合法均值和参照角色等构造条件，并定义

\[
S_e=\sum_{i\in F_e}q_i(\rho_e),\quad M_{-1}=M_J=0,
\]

\[
H_e\ge2S_e,\quad b_J-b_0\le\varepsilon/4,
\quad d_e+\rho_e+\rho_{e+1}<b_{e+1}-b_e,
\quad2\max_e\rho_e\le\varepsilon/2.
\]

令 `F={e<J:2ρ_e<d_e}`。在共同检查点覆盖事件上，

\[
\mathcal U_T(\eta)\le
\sum_{e\notin F}M_eH_e
+2\sum_{e\in F}M_eS_e
+2\sum_{e=0}^{J}(e+1+M_{e-1})S_e.
\]

需要时保留当前边界距离 `d_e>η` 的说明；该范围之外只能按原证据称保守上界，不得宣称同样完成了全部精细分类。

对在 `[1,T]` 内出现过正 gap 的臂，

\[
\gamma_i=\min_{t\le T:i\in A_t,\,\Delta_i(t)>0}\Delta_i(t),
\qquad D_i^T=\max_{t\le T:i\in A_t}\Delta_i(t).
\]

无条件期望上界为

\[
\begin{aligned}
\mathbb E R_T\le{}&
\sum_{e<J}\sum_{k=1}^{M_e}(\varepsilon+d_e)q_{e,k}\\
&+\sum_{i:\gamma_i\text{ 存在}}D_i^T
\left[
\left\lceil\frac{12\log(2T)}{\gamma_i^2}\right\rceil-q_i+1
\right]_++1.
\end{aligned}
\]

`q_i` 为一次 lifetime 配额，不按新参照次数反复收费。该式只对规定的出生窗口完成条件成立；一般到达只能使用基础联合界。

### 6.6 两端权衡锁：原 Theorem 7.2

\[
J\ge1,\quad M\ge\max\{2,J\},\quad
0<\varepsilon\le1/8,\quad0<\delta\le1/16,
\]

\[
0<v,\quad Jv\le\varepsilon/4,\quad0<d\le v/32,\quad\eta=d/2.
\]

第 `e` 批参照均值 `b_e=1/2+ev`，候选均值

\[
r_{e,k}=b_e-\varepsilon+\sigma_{e,k}d,
\qquad\sigma_{e,k}\in\{-1,+1\}.
\]

所有符号配置及批内标签排列属于同一 `Θ`。最后仅到达参照。定义

\[
K=J(M+1)+1,\quad L_K=\log\frac{4K(K+1)}\delta,
\quad\rho_f=d/4,\quad\rho_c=v/8,
\]

\[
q_f=\lceil32L_K/d^2\rceil,\quad q_c=\lceil128L_K/v^2\rceil,
\quad H=128(M+J+1)q_f,\quad V=JMH,\quad T=(J+1)H.
\]

这里 `q_f,q_c` 是逐臂实际配额的共同分析上界，不得在代码中悄悄要求算法使用未知最终 `K` 计算它们。

\[
2^{-20}\frac{\varepsilon JM}{d^2}\log\frac M\delta
\le\mathfrak R_\Theta(V/8)
\le2^{18}\frac{\varepsilon JM}{d^2}\log\frac M\delta.
\]

粗策略在面积预算 `9V/8` 下，

\[
\sup_{\theta\in\Theta}\mathbb E_\theta R_T
\le2\varepsilon JMq_c+
64\left(\frac{JM}{\varepsilon}+\frac{J^2}{v}\right)\log(2T)+1.
\]

当合法的 `J,M,ε,v,δ` 固定而 `d↓0`，

\[
\mathfrak R_\Theta(V/8)=\Theta(d^{-2}),\qquad
\mathfrak R_\Theta(9V/8)=O(\log(1/d)).
\]

必须同时说明：`η` 和 `T` 按定义变化；粗端只有 upper；既未证明所有中间预算最优，也未证明所有日程都存在同样分离。

### 6.7 概率加强锁：原 Theorem 7.3／S11

在同一 repeated-update family 和快速面积要求下，存在一个固定符号配置，使

\[
\mathbb P_\sigma\left\{
R_T\ge2^{-20}\frac{\varepsilon JM}{d^2}\log\frac M\delta
\right\}\ge11/80.
\]

保持“存在固定环境”的位置：它可依策略与该实验而定，不是每个环境都同样困难。

联合 regret 分位版本定义为同一事件上

\[
\inf_{\theta\in\Theta}
\mathbb P_\theta\{E_{\rm lab},\ \mathcal U_T\le a,\ R_T\le r\}
\ge1-\delta.
\]

只保留快速端在规定 `H` 的同阶结果。不要把 `11/80` 写成错误率 `δ`，不要由一次模拟零失败验证该量词。

### 6.8 扩展结果锁

| 扩展 | 不可省略的边界 |
|---|---|
| 最终强一致性，原 S9 | 使用**另一个**可复核多精度策略；到达最终停止、最终有限臂、无臂恰在近优边界；不能归给固定检查点 |
| 兼容窗口截断，原 S12 | 共用一个可实现的完整环境；每个候选－时间对计一次；窗口可重叠不等于所有任意重叠 arrival 问题已解决 |
| 一般信息松弛，原 S13 | 下界 occupancy 只给必要性；面积转换必须保留 `a+δW`；未知均值 causal learner 可达性未证 |
| 中间精度配置，原 S14 | 精细批次集合事先选择；只是可达点，不是已证全前沿 |
| 已知参照角色诊断，原 S14 | 明确额外披露哪条参照在本窗口最好；不拿它替代主算法未知最佳身份的性能 |

---

## 7. Algorithm 1 的伪代码合同与行为验收

本节是新增正式伪代码的操作规范，不授权改变策略。实际排版可复用项目现有 algorithm 环境，不必引入新宏包系统。

### 7.1 建议直接翻译为英文 LaTeX 的伪代码

```text
Algorithm: Checkpoint-UCB
Input: ε ∈ (0,1), δ ∈ (0,1/2), predetermined ρ ∈ (0,1)
State: arrived-arm set A; FIFO queue Q_srv; next label k
For each arm i: count n[i], reward sum S[i], quota q[i], interval [l[i],u[i]]

Initialize A = ∅, Q_srv empty, k = 0.
For physical time t = 1,2,...:
    Receive every arm arriving at t, in a fixed within-batch order.
    For each new arm:
        k ← k+1; i ← k; A ← A∪{i}
        n[i] ← 0; S[i] ← 0
        q[i] ← ceil((2/ρ²) log(4i(i+1)/δ))
        l[i] ← 0; u[i] ← 1
        Append i to Q_srv.

    While Q_srv is nonempty and n[front] ≥ q[front]:
        Pop its front.

    If t is even and Q_srv is nonempty:
        I ← front(Q_srv)                  # designated service pull
    Else:
        For i ∈ A:
            J[i] ← +∞ if n[i]=0
            J[i] ← S[i]/n[i] + sqrt(3log(2t)/n[i]) otherwise
        I ← maximizer of J[i]; ties use the smallest arrival-order label.

    Pull I exactly once; observe x ∈ [0,1].
    n[I] ← n[I]+1; S[I] ← S[I]+x

    If n[I]=q[I]:
        m ← S[I]/q[I]
        l[I] ← max(0,m−ρ/2)
        u[I] ← min(1,m+ρ/2)
    # If n[I]>q[I], the reporting interval is not recomputed.

    L ← max_{i∈A} l[i]; U ← max_{i∈A} u[i]
    P_t ← {i∈A: l[i] ≥ U−ε}
    N_t ← {i∈A: u[i] < L−ε}
    V_t ← A \ (P_t∪N_t)
    Report (P_t,N_t,V_t).
```

正文中的 `N_t` 必须排成负报告集合的数学字体，不能与 `N_i(t)` 混淆。伪代码中 `S[i]` 是每臂奖励和，理论中 `S_e` 是整批检查点工作量，正文须在各自出现处定义。

### 7.2 必须写在算法附近的四点说明

- 每轮只有一个样本；偶数服务轮不是在 UCB 样本之外追加第二个样本。
- 所有样本共同抵扣一次 lifetime 配额，UCB 轮也可能触发检查点并冻结区间。
- `n_i=q_i` 只代表固定精度证据形成，不代表已经被分类；竞争者未成熟或边界更细都可能继续未决。
- 负报告不从收益集合删除臂；已判负臂仍可能由 UCB 选择。删除原算法不等于删除统计排除标签。

### 7.3 不允许出现的“看似优化”

本轮不得加入：

- 根据真实 `d_i^ε(t)` 或真实 `G_t^ε` 决定服务对象／停止。
- 为每条新臂重置旧计数；对每次到达重复征收旧 `q_i`。
- 只从未决臂中选择 UCB；把负报告臂永久移出收益选择。
- 在观测到有利经验均值后再挑选 `ρ_i`，仍沿用固定检查点错误预算。
- FIFO 改成 confidence-driven，或者每二轮服务改成每八轮，却不另作实验配置标识。
- 把新臂的完整初始化作为当轮可免费完成的操作；大批量到达仍只能每轮拉一臂。
- 未到达臂进入报告或被提前采样。

### 7.4 行为检查（B 级：源代码存在时执行）

如只改论文伪代码，实际代码无需重写。若新增别名或为展示抽取一个 reference implementation，应与 C 逐轮对照：选择臂、服务标记、计数、累计奖励和、冻结区间及三个报告集合必须一致。

至少覆盖：

| 检查场景 | 通过标准 |
|---|---|
| 初始单臂／多臂、奖励0或1 | 每轮有且只有一个合法动作；计数总和等于物理时间 |
| 同时到达批次大于剩余评估轮数 | 不进行超预算全初始化；全部物理臂仍属于报告范围 |
| 恰在奇数／偶数轮到达 | 先接纳再选臂；只在偶数且队列非空时走服务分支 |
| UCB 先完成队列后方臂的配额 | 该轮即形成区间；以后它到队首时能被正确跳过 |
| `q_i−1 → q_i → q_i+1` | 区间只在第一个转移更新一次；计数与收益估计继续更新 |
| 已报负臂 | 仍在 A 和 UCB 比较范围；不得仅因标签被跳过 |
| 标签集合 | 两两不交且并为 A；不把所有未决当成已完整分类 |
| 改名等价 | 同一潜在流上与原 C 动作和报告完全一致；原类接口继续可用 |

已完成过的历史 20,000 轮检查不能算作本轮又做了一次；本轮是否执行、执行哪份程序、输入和结果必须如实记录。

---

## 8. 实验数据锁与原始结果保全

### 8.1 本轮保持不变的实验范围

- 四环境：Stable benchmark；Successive improvements；Burst；Arrivals stop。
- 九方法，主表显示其中六方法；总运行数为 `4×9×160=5,760`。
- 每次 `T=20,000`；`ε=.30,η=.10,δ=.05`；终点8臂。
- 每个环境／方法160次重复；跨方法采用共同潜在奖励流，而不是强制相同动作。
- 两个 FIFO 检查点配置为 `ρ=.04` 和 `ρ=.12`；八臂总配额分别为73,083和8,123。
- 不存在一个已经执行的“原 UCB-AA 经修正后验证实验”可供迁入新稿。

这些值的依据是 M 的实验描述，不表示本次方案编制独立重跑了它们。fileciteturn43file1L547-L567

### 8.2 原 Table 2 的数值快照

面积单位为 `10^3`；括号为 Monte Carlo standard error，不是理论置信半径。Codex 应从真实数据／表格源码逐项核对，不凭 PDF 排版位置重建记录。

| 环境 | 方法 | Regret | Area / 10³ |
|---|---|---:|---:|
| Stable benchmark | CP-FIFO (ρ=.04) | 1360.5 (1.5) | 111.78 (0.00) |
| Stable benchmark | CP-FIFO (ρ=.12) | 3629.9 (0.7) | 49.72 (0.23) |
| Stable benchmark | UCB-prefix | 441.7 (2.3) | 83.97 (0.46) |
| Stable benchmark | Growing-MOSS | 77.3 (0.8) | 92.43 (0.00) |
| Stable benchmark | ALL-ε adapt. | 1367.8 (11.6) | 11.31 (0.09) |
| Stable benchmark | Batch100-UCB | 209.3 (2.6) | 85.27 (0.52) |
| Successive improvements | CP-FIFO (ρ=.04) | 5297.4 (1.2) | 74.82 (0.00) |
| Successive improvements | CP-FIFO (ρ=.12) | 1194.7 (0.0) | 14.74 (0.10) |
| Successive improvements | UCB-prefix | 246.2 (1.7) | 18.45 (0.14) |
| Successive improvements | Growing-MOSS | 53.1 (0.8) | 33.65 (0.11) |
| Successive improvements | ALL-ε adapt. | 2905.8 (2.4) | 9.53 (0.13) |
| Successive improvements | Batch100-UCB | 238.8 (2.1) | 22.85 (0.09) |
| Burst | CP-FIFO (ρ=.04) | 2798.0 (1.6) | 75.89 (0.00) |
| Burst | CP-FIFO (ρ=.12) | 3392.2 (0.2) | 28.21 (0.17) |
| Burst | UCB-prefix | 354.1 (2.2) | 41.75 (0.39) |
| Burst | Growing-MOSS | 69.3 (0.9) | 57.03 (0.01) |
| Burst | ALL-ε adapt. | 2017.4 (9.8) | 10.31 (0.09) |
| Burst | Batch100-UCB | 278.9 (2.7) | 55.87 (0.15) |
| Arrivals stop | CP-FIFO (ρ=.04) | 4759.0 (1.3) | 89.86 (0.00) |
| Arrivals stop | CP-FIFO (ρ=.12) | 2645.9 (0.3) | 25.14 (0.01) |
| Arrivals stop | UCB-prefix | 248.8 (1.5) | 45.96 (0.56) |
| Arrivals stop | Growing-MOSS | 52.0 (0.6) | 71.59 (0.01) |
| Arrivals stop | ALL-ε adapt. | 3027.5 (4.3) | 12.07 (0.07) |
| Arrivals stop | Batch100-UCB | 214.2 (1.8) | 55.28 (0.21) |

此表是现有结果的核对快照，不是新增实验。fileciteturn43file1L591-L618

### 8.3 不利结论也属于必须保留的数据解释

必须保留且不能淡化成“方法表现良好”的内容：

1. 全部640次 finer-checkpoint 运行中，所有可用臂一直未决；边界豁免导致终点被计罚的臂数可以少于全部臂数，不等于其余臂已完成分类。
2. 稳定基准和 burst 中，较粗 CP-FIFO 的两个均值指标被 ALL-ε adaptation 同时改善。
3. successive-improvement 中两者位于不同成本点，但现有比较不能独立识别任务失效机制，因为服务量和对边界带内工作的处理不同。
4. Growing-MOSS 在四环境中平均 regret 最小，却有较大的未决面积；这只说明收益与报告目标不同，不证明它无法增加有效认证层。
5. 无误报的5,760次有限实验不证明所有环境、所有时间上的可靠性；一个固定方法／环境下160次零失败对应的原文0.0186上界不得被当成全模型界。
6. 当前四环境不属于分离定理的完整参数族，不验证其渐近阶数；不因图上有 trade-off 就称已恢复最优前沿。

上述结论在现稿已有明确陈述。fileciteturn43file1L691-L704 fileciteturn43file1L764-L791

### 8.4 B 级数据资源检查

有完整记录时，核对并记录配置文件、seed机制、结果文件路径、文件hash和绘图入口；允许基于原数据重新排版或计算等价的显示精度，但不得改变结果选择。

只有 PDF 汇总、没有逐次数据时：

- 可原样迁移已有表格和图；在编辑报告里说明未核对底层数据。
- 不能从均值与标准误伪造160条样本、分位数或 paired differences。
- 不能把 `.py` 中的单次 sanity run 当成九方法完整实验工程。
- 在新稿实际公开可用性未核实前，不替作者声称已有可访问发布地址。

---

## 9. 命名、交叉引用和论文语言清理

### 9.1 展示名与资源名的映射

| 原称呼 | 新稿默认称呼 | 处理规则 |
|---|---|---|
| 两阶段 UCB-AA／Online UCB-AA／repaired UCB-AA | 不再作为新稿方法出现 | 完整专题和方法主张删除；历史档案保留 |
| CP-UCB-AA（理论构造） | Checkpoint-UCB | 论文展示名更新；不是新增机制 |
| CP-FIFO (ρ=.04/.12) | 可保留短名；首次说明为 Checkpoint-UCB 配置 | 不改变原数据 ID 和数值 |
| CP-confidence／CP-period8 | 可保留为明确标识的变体 | 不把一般FIFO定理自动移植给变体 |
| `CheckpointUCBAA`、`cp_ucb_aa.py` | 原接口／文件名默认保持 | 在复现README记录名称映射，必要时增加非破坏性别名 |
| ALL-ε adaptation | 保持 | 不重命名为原创算法，不冒充 FAREAST／(ST)^2 |
| Growing-MOSS | 保持现有实现名称及公式 | 不替换成独立论文的MC-MOSS |
| `U_t`、`\mathcal U_T` | 分别保持时点数、累计面积 | 字体和下标必须清楚 |

默认在新正文主叙述中不保留 `UCB-AA` 字样。若复现附录必须写实际旧文件名或名称映射，允许保留一个明确 provenance 用途的出现，并在检查报告列为允许例外。

### 9.2 建议 label 迁移键

实际 label 先由源码发现。下表只提供语义目标，不表示这些 label 已经存在：

| 旧对象 | 新语义键示例 |
|---|---|
| 原 §5.1 主协议 | `eq:joint-protocol` |
| 新 Algorithm 1 | `alg:checkpoint-ucb` |
| 原 Proposition 5.1 | `prop:checkpoint-joint` |
| 原 Theorem 6.1 | `thm:broadcast-obstruction` |
| 原 Theorem 6.3 | `thm:worst-area` |
| 原 Corollary 6.2 | `cor:arrival-growth` |
| 突发反例 | `rem:bursty-schedule` 或实际对应命题标签 |
| 原 Proposition 7.1 | `prop:shared-evidence` |
| 原 Theorem 7.2 | `thm:rapid-deferred` |
| 原 Theorem 7.3 | `thm:rapid-quantile` |
| 原 Table 2 | `tab:maintenance-comparison` |
| 原 Figure 2 | `fig:regret-area` |
| 原 Figure 3 | `fig:maintenance-paths` |

不要为了采用这些键批量重写所有已良好工作的 label；保留既有键也可以，但必须更新编号和引用，并提供 old→new 映射。正文与附录的 theorem 编号按模板自动生成，不手工承诺固定新数字。

### 9.3 需要逐条审查的残余语句

在**实际参与编译的新正文和附录源文件**中搜索以下片段，逐条处理；不要对整个仓库做破坏式替换：

```text
UCB-AA
Online UCB-AA
pre-elimination
preliminary screening
formal elimination
repaired procedure
repaired fixed-budget
original submission
archived implementation
original six figures
The original two arrival scenarios
reviewer’s proposed
The sufficiency follows from the next theorem
No data were created
```

处理标准：

- 旧方法叙事和被删除对象的引用必须清理。
- 文献标题中的 `elimination`、Batch100 的真实 retirement 机制、新任务中的 statistical exclusion 不属于禁止内容，不能误删。
- 保留结果附近的范围限制、负面数据解释不能因出现“does not claim”就删掉。
- 删除表述中的“we now supplement”而不是删除联合任务本身。
- 不以大规模同义改写掩盖定义变化；英文编辑目标是准确和可读，不是声称比原稿更强。

### 9.4 禁止残留的科学主张

新稿不得出现以下无支持的结论，除非只是明确的反例或未完成问题：

- 近优集合等于收益竞争活跃集。
- 未被接纳的臂视为已统计排除。
- 所有有效 elimination 必然恶化 regret。
- Checkpoint-UCB 在所有新实验中双指标占优。
- `ρ=.12` 保证对任意 `η=.10` 环境完整分类。
- 模拟零误报验证全环境可靠性。
- 初始静态批量下界证明了所有特有动态机制。
- 最坏面积匹配等于每条日程复杂度已匹配。
- 稀疏到达总数条件已完整刻画所有临界日程。
- 暂缓端上界已匹配、所有中间面积预算的Pareto前沿已解决。
- 固定检查点具有S9另一个策略的几乎必然最终一致性。
- 已知最佳参照身份诊断与未知均值、未知最佳身份主算法同难。
- 一般信息松弛可行就存在未知均值的因果策略达到它。

---

## 10. 本轮工作流、任务状态和交付物

### 10.1 推荐执行顺序

**阶段 I：冻结输入与发现依赖。**执行 A-00；记录实际源、表图、配置、数据和共用文件；保留旧版本快照。

**阶段 II：建立新骨架并迁移核心定义。**先完成 A-01、A-02、A-04、A-09，建立第1–7节空骨架；此时不要留下“结果以后再补”的投稿正文，而是立即迁入已有核心内容。

**阶段 III：先救出依赖，再删旧专题。**按 §5 建立 theorem map；迁移共用工具；执行 A-06、A-07、A-08、A-19。不得先全删再用文字假装证明还在。

**阶段 IV：算法与主定理整理。**执行 A-10 至 A-18，完整保留数学合同、补伪代码、迁入共享证据的收益上界、修复增长推论的引用接口。

**阶段 V：图表、数值和叙述统一。**执行 A-03、A-20、A-21、A-22；既有实验结果不变，只整理其角色和必要限制；更新图表、参考文献和资源说明。

**阶段 VI：编译和完整验收。**执行 §11；完成 report、blockers 和 future work 文件；明确哪些检查实际运行过。

### 10.2 每张任务卡的状态记录

建立 `edit-checklist.md`，列出 A-00 至 A-22，使用以下状态之一：

| 状态 | 含义 |
|---|---|
| `TODO` | 尚未执行 |
| `DONE` | 已执行且通过该卡验收；给出文件和label位置 |
| `BLOCKED_SOURCE` | 缺少可编辑源码、图或真实数据等输入 |
| `BLOCKED_MATH` | 来源公式／证明接口存在需作者裁定的实质冲突 |
| `BLOCKED_BUILD` | 编译工具或依赖缺失；不是内容已经通过 |
| `DEFERRED_C` | 属于后续研究，不属于本轮默认执行 |
| `NOT_APPLICABLE` | 实际版本已无此对象；说明检查位置和理由 |

不能把只删除标题、尚未迁移证明的任务标为完成。不要把缺失的新实验标为“验证失败”；应区分未运行与结果不利。

### 10.3 建议交付文件

下列是**Codex 完成编辑后应生成的交付物名称建议**，不是当前已存在文件的声明：

| 交付物 | 内容 |
|---|---|
| 修订后的实际 LaTeX 源文件与必要资源 | 在真实项目结构内组织；不破坏另一篇论文 |
| `manuscript_revised.pdf` | 新主线正文；原算法专题已经移出 |
| `supplement_revised.pdf` | 对应新正文的证明和扩展 |
| `REVISION_REPORT.md` | 摘要式说明实际删、留、迁移与新增展示；完成及阻塞情况 |
| `source-manifest.md` | 输入版本、真实路径、编译入口、受保护文件、源hash |
| `theorem-migration-map.csv` | 核心定理与证明依赖的旧－新对应 |
| `edit-checklist.md` | A-00 至 A-22 的实际状态与验收证据 |
| `validation-report.md` | 引用、数学合同、图表数值、算法语义、渲染检查的实际结果 |
| `blockers.md` | 未解决的资源／数学／编译问题；空时明确写“未发现已知阻塞”，不等于证明全对 |
| `future-work.md` | 本方案 §12 的 C 级工作，不写入已完成贡献 |
| 编译日志及可选文本diff | 保存实际命令与运行结果；不编造通过记录 |

旧内容放在不参与新稿编译的版本快照或档案。无需为存档再创建一篇同体量的“旧理论补充材料”，也不把档案自动加入投稿ZIP。

### 10.4 Codex 完成后的回复必须交代

- 实际修改了哪些入口文件，是否成功编译出两份PDF。
- 原 UCB-AA 已从哪些地方移除，核心定理是否全部迁移。
- Checkpoint-UCB 是否只改展示、是否有代码行为变化；默认应无变化。
- 是否重跑实验；默认应写“未开展新比较实验”，不能含糊称“验证完成”。
- 是否存在 `BLOCKED_*` 条目，分别影响什么。
- C级后续任务尚未执行。

---

## 11. 最终验收清单

以下清单必须逐项判断。编译通过只是其中一项。

### 11.1 结构和范围

- [ ] 论文开头直接定义持续近优集合维护与收益的联合任务。
- [ ] 原两阶段 UCB-AA 不再是摘要、引言或讨论的主要贡献。
- [ ] 原 Algorithm 1、Theorem 3.1、Corollary 3.2 与配套S1专题已退出新投稿包。
- [ ] 原纯 regret 第4节与专属S2证明已退出；共用工具被保留。
- [ ] 原旧实验整套退出；不是只删除不利结果。
- [ ] 新第3节只有已明确的检查点构造，不暗中替换为新算法。
- [ ] 主要维护结果和概率加强均在新正文／附录中可定位。
- [ ] 独立 temporal-geometry 论文的受保护文件与资源未被改动。

### 11.2 数学和定义

- [ ] 所有假设、参数区间和风险量词均按 §6 核对。
- [ ] `ε`、`η`、`ρ`、`δ` 分工不变。
- [ ] `\mathcal U_T` 的累计定义和边界严格不等号未改。
- [ ] 期望 regret 与高概率标签－面积的主协议未被替换。
- [ ] 已报负臂不被主收益策略永久排除。
- [ ] lower 的信息增强与 upper 的未知未来条件写清。
- [ ] 共同参考环境、乘积先验和窗口兼容性都保留。
- [ ] 最坏面积定理的静态下界来源没有被隐藏。
- [ ] 增长推论的参数引用接口已按 A-13 处理。
- [ ] `K_t=o(√t)` 未被写成一般充分条件。
- [ ] 快速／暂缓分离保留指定 `H,T`，以及 `η=d/2`。
- [ ] 粗端只是上界，完整前沿仍未闭合。
- [ ] 原 S9 的最终一致性不归给固定检查点。
- [ ] 原 S13 的 `δW` 没有丢失。
- [ ] 未新增未经来源支持的 theorem、assumption 或优越性结论。

### 11.3 算法和数据

- [ ] 伪代码的每轮只观察一个样本，先到达、后选择、再观察、最后报告。
- [ ] 实际FIFO队列与分析下界队列分开命名。
- [ ] 服务样本和收益样本共享计数，没有两份独立账本。
- [ ] 检查点区间只生成一次；以后只更新收益估计。
- [ ] 代码／文件重命名有映射，无需破坏旧API或原始数据ID。
- [ ] 原 Table 2 的24条记录、单位和标准误全部核对一致。
- [ ] 九方法图、六方法主表与完整附录诊断的展示关系清楚。
- [ ] 640次全未决的事实和CP不利比较仍保留。
- [ ] `ρ=.04` 与 `ρ=.12` 的完整性差别被明确说明。
- [ ] 未从汇总数据伪造新分位数、置信带或新实验。
- [ ] 未把原 `.py` 单次sanity检查当成完整复现实验。
- [ ] 数据发布状态以实际文件／链接为准，未确认项列为阻塞。

### 11.4 引用、编译和视觉

- [ ] 所有 `\ref/\eqref/\cref` 等指向存在且正确的对象。
- [ ] 无重复label、未定义citation、正文／附录硬编码旧编号。
- [ ] 清理不使用的宏之前，已经检查共享文件和所有保留证明。
- [ ] 采用项目原有编译引擎与文献工具；没有无理由改成另一套模板。
- [ ] 在独立输出目录执行干净构建，不删除用户源文件或原编译产物。
- [ ] 编译日志无未定义引用；版面警告逐项人工检查，不以“exit code=0”代替版面验收。
- [ ] 实际渲染并检查新主算法、参数长公式、两端定理、主表和图例；无截断、重叠、缺符号。
- [ ] 上下界横线、书法字体、正部运算、下标和指数经图像核对，未被PDF抽取误导。
- [ ] 主辅文档标题、日期机制、作者身份和盲审设置一致。
- [ ] 没有把工作区任务指令、TODO占位符或本方案的ChatGPT引用标记混进论文正文。

### 11.5 发布前的诚实状态

- [ ] `REVISION_REPORT.md` 区分编辑、编译、代码检查、数值复核和独立证明审查。
- [ ] 未运行的检查没有被标记为通过。
- [ ] 存在数学冲突时报告准确位置，没有静默“修好”并宣称结论仍然相同。
- [ ] 旧存档完整保留，但不会随新投稿包自动打包。
- [ ] 本轮无需重跑旧UCB-AA，也不把它留作“必须补完”的任务。

---

## 12. 后续增强任务：只登记，不纳入本轮完成条件

本节内容应写入 `future-work.md`。这些是基于已确定主线提出的**后续工作建议**，不是来源已经提供的实验或新定理。

### C-01｜共同认证负担的机制实验

**目标：**区分新臂自身未决与它对旧候选报告造成的共同等待。

**后续执行要求：**固定旧候选的真实资格和可追溯历史，改变旧候选数量、新臂质量及到达时刻；分别记录旧臂与新臂的未决时间。旧历史若来自先前采样，必须计入实际预算与regret；不能把大量免费warm start偷偷加入原模型。

**完成标准：**能展示新臂到达时真实仍近优的旧候选为何暂时无法正认证；不把旧候选真正变坏的事件与证据不足混为一谈。结果不能仅用总面积一条曲线概括。

### C-02｜临时任务失效与跨更新证据复用实验

**目标：**识别旧候选的精细任务失效后，哪些报告无需自身新增样本即可完成。

**后续执行要求：**记录每批候选在出生窗口的样本数、新参照到来后的样本数、负认证时刻、有效证据对及参照成熟时刻。设置明确的证据复用消融，但不把一个故意丢弃全部旧数据的弱对照作为唯一竞争者。

**完成标准：**共享证据机制与不同服务比例、不同边界带处理分别被控制；任何改动置信区间的消融需要独立的有效性说明，不能直接继承固定检查点保证。

### C-03｜同任务的regret—面积曲线与有限终点联合成功率

**目标：**在固定 `ε,η,δ,T` 下比较服务水平，而不只挑几个任意参数点。

**后续执行要求：**预先设定服务强度与精度扫描网格，保留全部结果；参数开发与最终评估分开。可以比较不同有效置信层，但共同任务、物理信息、评价指标应相同。记录有限终点 `E_lab^(T)` 与面积门槛的联合成功情况。

**完成标准：**只报告实际有限实验支持的成功率／分位数，不冒称全环境、全时间保证。数据只存在汇总时不能执行此项，需要真实逐次记录或经授权新模拟。

### C-04｜更一般窗口长度下的联合上界

**目标：**超过当前规定 `H` 的构造，分开刻画认证成本与普通收益探索成本。

**后续执行要求：**先明确新定理的窗口类、算法信息与风险协议；不能把快速端已有的 `R_T≤2εT` 直接当成更一般时域的尖锐上界。证明必须自成闭合依赖。

**完成标准：**新界在原族上可核对，并说明比当前规定时域结果新增了什么；未完成时不改变现有 Theorem 7.2 的范围。

### C-05｜暂缓端converse、自动精度与部分重叠到达

三项是可分别研究的方向，不要求本轮一起完成：

- 暂缓面积预算下的匹配regret下界；
- 不知道改善尺度时的有效精度选择；
- 可实现的重叠任务类上的联合可达保证。

**完成标准：**须使用同一报告协议与兼容环境；不得从一般信息松弛可行性自动推出causal可达性，也不得通过给算法真实最优标签完成所谓自适应结果。

---

## 13. 阻塞处理规则与交接说明

### 13.1 发现问题时不要静默修正

| 发现的问题 | Codex 应做的事 | 不应做的事 |
|---|---|---|
| 源文件不存在或与PDF明显不同 | 列出已找到版本、差异和所需输入；继续不冲突的定位任务 | 从旧稿重造一套源码并声称与现稿一致 |
| 核心公式存在疑似错误 | 保留原陈述快照，记录定位与影响；将相关任务标为 `BLOCKED_MATH` | 偷换常数、风险或假设后说只是排版修改 |
| 图表只有图片没有原数据 | 原样迁移可用图，注明没有底层复核；登记所缺文件 | 凭图逆推随机样本或新误差条 |
| 代码命名需更新 | 论文展示名与方法ID建立映射；必要时非破坏性别名 | 改类名导致原实验无法复现 |
| 共享宏／文献库影响G论文 | 新建本稿局部配置或使用安全范围修改 | 全局删条目／宏导致另一篇编译失败 |
| 编译工具缺失 | 报告依赖和未完成状态，交付实际已改源码 | 声称PDF已成功生成或已查看 |
| 原负面结果影响叙事 | 调整主张和算法定位，保留结果 | 删除不利算法配置或只挑有利场景 |

### 13.2 本任务书的完成标准不包括什么

不包括：证明新一般前沿、优化定理常数、发明新的强算法、重新完成完整文献创新性评估、验证所有实验概率、做期刊投稿操作，或恢复已经移出的UCB-AA方法专题。

**交接目标只有一个：让新稿的每一部分都直接服务于可靠近优集合维护的统计成本与收益权衡，同时保存来源、数学范围和实验事实。**

---

## 14. 供作者快速验收的一页摘要

**删除出新投稿稿件：**原两阶段UCB-AA算法与整套修正分析；相应静态／near-tied纯regret专题；旧60,000轮archived实验和旧FDA图；修复旧稿的过程叙述与旧算法验证义务。

**保留为主干：**全物理臂的可靠三分类；累计边界外未决量；共同认证负担；最坏面积匹配及量词明确的增长后果；临时任务的面积到regret下界；共享证据联合上界；快速／暂缓两端结果与概率加强。

**保留但不夸大：**Checkpoint-UCB作为简单可达性构造；新有限预算实验中的不利结果；最终一致性、信息松弛、中间配置等作为附录扩展。

**本轮应新增的只是展示和组织：**正式检查点伪代码；模型与参数表；主辅依赖地图；共享证据regret式的正文展示；数据与名称映射；范围和验收说明。不是新增理论或新实验结果。

**默认不执行：**新模拟、新算法、新理论扩展。它们有清楚的后续任务，不阻碍本轮先形成一版结构完整、事实不变的修订稿。

> 最终检验：删掉旧UCB-AA之后，新稿应当仍然是一篇问题清楚、证明链完整、构造可执行、实验不选择性呈现的独立论文，而不是一份删去前半部后留下的研究记录。
