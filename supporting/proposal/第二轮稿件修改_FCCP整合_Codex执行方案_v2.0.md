# 第二轮稿件修改任务书：保留一般维护理论，整合 Flexible CCP

**版本：v2.0｜编制日期：2026-10-17｜执行对象：`manuscript(3).pdf` 与 `supplement(3).pdf` 所对应的 LaTeX 项目**

> **最终主线：在永久外生到达、平稳有界奖励的模型下，保留可靠近优集合维护的基本成本与收益—及时性权衡；以 F-CCP 作为主推的可调节实现，明确其收益优先、认证优先、自适应和基线兼容端点。**
>
> **不得把 Checkpoint-UCB、CCP、ABM 和 F-CCP 改成同一个名字，进而让 F-CCP 自动继承其他策略的结论。** Checkpoint-UCB 不再担任正文主算法，但仍作为旧上界的构造见证完整保留在补充材料。原两阶段 elimination 型 UCB-AA 已经退出本版，不能重新引入。

本文件是一份**可直接执行的编辑任务书**，不是要求 Codex 再做一次研究选题，也不是授权重新调参、寻找更有利的实验或补造最优性证明。默认执行 R2-00 至 R2-31；附录中的数学合同、数据合同和验收脚本具有同样约束力。

## 0. 给 Codex 的启动指令

请在用户当前论文工作区中定位这两个 PDF 对应的实际源文件，读取本任务书及列明的三轮研究包，按依赖顺序执行第二轮整合。

完成后，新正文应该让读者清楚区分四类内容：

1. **任务本身的必要成本**：不针对某个算法的共同认证下界、最坏维护面积、增长率条件、临时任务成本。
2. **已证明的可达性见证**：Checkpoint-UCB，以及受限更新族中的 ABM；它们不是默认 F-CCP 的别名。
3. **主推的灵活实现**：F-CCP 的证据层、证书成本调度、可变服务率、双预算和收益核接口，以及这些机制确实得到的保证。
4. **有限预算证据**：冻结实验中 F-CCP 的均值优势、成本取舍、统计不确定性、报告失败和尾部风险。

### 0.1 执行边界

| 类别 | 本轮处理 |
|---|---|
| 删除重复叙述、迁移现有内容、翻译研究证明、增补现有算法伪代码 | 必做 |
| 从已有逐次结果重算表格、配对差、分位数，重新绘图 | 资源存在时必做；这是再分析，不是新实验 |
| 对冻结算法做小型一致性和接口检查 | 允许；不得改变主测试轨迹或参数 |
| 修改算法决策、置信常数、默认温度、服务控制器或奖励核 | 不在本轮授权内 |
| 新增模拟、扩充重复次数、重新选择默认参数 | 不在本轮授权内；另列研究待办 |
| 为弥补缺口另造定理、把松弛当可达前沿、把局部规划当统计最优 | 禁止 |
| 改写独立 temporal-geometry 论文、合并其主要贡献、修改公开仓库或提交期刊 | 禁止，除非用户另行授权 |
| 将内部核查或编译通过写成独立同行验证 | 禁止 |

保留用户未提交修改；不得使用 `git reset --hard`、`git clean`、强制覆盖原始资料或删除旧实验失败记录。没有源码就不能声称已经完成 LaTeX 修改；不能仅通过删 PDF 页实现内容重构。

### 0.2 与第一轮任务书的关系

本任务书**取代 v1.0 中关于正文算法定位、数值主证据与附录组织的安排**。第一轮已经完成的“去掉两阶段 UCB-AA、固定联合风险、区分活跃集和报告集”继续有效。

特别注意：当前正文第3节是 **Checkpoint-UCB**，不是早期版本中的两阶段 UCB-AA。不要按 v1.0 的旧页码或“删除第3节”字符串直接操作。

### 0.3 完成状态

每个任务只可标记 `DONE`、`BLOCKED_SOURCE`、`BLOCKED_PROOF_INTERFACE`、`BLOCKED_DATA`、`BLOCKED_BUILD` 或 `NOT_AUTHORIZED_RESEARCH`。只因完成了部分文件编辑，不能把被阻塞任务勾成完成。

本轮最终产物是来源可追溯、定理归属清楚、实验不夸大的修订稿；并不表示完整 regret—未决量前沿已被解决。

---

## 1. 输入版本与来源优先级

### 1.1 必须锁定的材料

| 代号 | 文件／研究包 | 在第二轮中的作用 |
|---|---|---|
| **M3** | `manuscript(3).pdf`，20页，*The Cost of Reliable Near-Optimal Set Maintenance with Arriving Arms*，October 15, 2026 | 唯一正文基线；章节、图表和原有结论按本版定位 |
| **S3** | `supplement(3).pdf`，20页，同题补充材料，October 15, 2026 | 唯一既有证明基线；S1—S13需要逐节迁移 |
| **C16** | `CCP_算法探索_研究包_2026-10-16.zip`；包内根目录 `CCP_research_2026-10-16/` | CCP局部规划、混合证据、任意动作指数差界及第一次算法研究 |
| **P16** | `Regret_未决量前沿_理论与算法研究包_2026-10-16.zip`；包内根目录 `frontier_research_2026-10-16/` | 因果／逐日程信息区别、部分恢复下界、ABM与中间预算；旧候选的负面实验 |
| **F17** | `F-CCP_可调算法_理论与实验_2026-10-17.zip`；包内根目录 `F-CCP_2026-10-17/` | 本轮主方法、最终双预算规则、最新冻结实验和修正ALL对照 |
| **G** | 题目为 *The Temporal Geometry of Bandits With Arriving Arms* 的独立正文与补充材料 | 只读外部／伴随研究输入；提供MC-MOSS潜在前缀工具和谱记账 |
| **V1** | `UCB-AA删除与集合维护重构_Codex执行方案_v1.0.md` | 仅用于理解上一轮决策；不得覆盖M3/S3或本任务书 |

这些文件在会话运行环境位于 `/mnt/data/`，**不是对 Codex 本地目录的假设**。Codex 必须先建立实际路径映射；根据文件名、题目、页数和哈希共同确认身份。研究包里的 `theory.md` 多次重名，引用时必须带研究包代号和相对路径。

当前两份PDF已经移除了原两阶段UCB-AA，保留了共同认证、最坏面积和重复更新理论；仍由Checkpoint-UCB承担正文主算法和旧上界。第二轮是从这个状态继续，不是退回29页旧正文和35页旧补充材料。定位依据：M3第5—7页、第8—13页；S3第3—13页。

### 1.2 来源冲突的处理

- **既有数学任务和旧结论**：以M3/S3为基准，不以更早聊天概述覆盖其精确条件。
- **F-CCP精确理论**：以F17的`theory.md`及其明确依赖为准；CCP层调用C16`theory.md`。
- **实际算法和参数**：以冻结生产引擎、当前交互接口和配置的共同合同为准，不以简化文字替代实际分支。
- **实验事实**：逐次CSV／冻结配置 > 自动汇总CSV > 研究报告中的舍入数字 > 聊天中的概述。
- **证明与代码不一致**：不能任选一个悄悄覆盖另一个。记录具体分支和受影响结论，阻塞该接口，保留冻结代码及数据。
- **新结果的成熟度**：研究包提供了书面证明和内部核查，不等于独立同行审计。迁移时检查适用范围与依赖；发现实质问题应上报，不把缺口埋进“显然”或“同理”。

### 1.3 推荐工作区布局

以下是新增工作目录建议，不是既有路径断言；不要覆盖用户现有同名目录。

```text
revision2/
  baseline/                  # M3/S3源码、PDF及哈希快照，只读
  source-map.json            # 本地路径、版本、角色、SHA-256
  claim-map.csv              # 旧／新命题的归属、条件、证明去向
  task-status.md             # R2-00…R2-31逐项状态和证据
  change-log.md
  blocked-items.md
  analysis/                  # 本轮重算表格、配对差和校验结果
  generated/                 # 拟进入论文的.tex表格与新图
  build-logs/
  render-checks/
  future-research.md         # 未获授权的研究工作，不进入成果清单
```

研究包原目录保持只读。第三轮`src/analyze.py`会写回结果，不能直接在唯一原件目录运行；复制到本轮分析工作区后再执行，或编写只读输入的等价校验脚本。

### 1.4 本次实际确认的版本摘要

以下哈希用于匹配已提供材料，不要求新的修订稿维持相同哈希。

| 材料 | SHA-256 |
|---|---|
| `manuscript(3).pdf` | `fb34711aa6da1db3ddd32f0b36cee32b09ba7c955fb69f12d6f6746e397ee494` |
| `supplement(3).pdf` | `0a7e5e9d09df25ef323b4bf91cb1af01b3db6ed3e1b336d26a7c0ebdd6dcdc7f` |
| `CCP_算法探索_研究包_2026-10-16.zip` | `5f5a505081c2f3426d827c0765067f6033d3a6150b6a1cacaadf1c5d2bf7e075` |
| `Regret_未决量前沿_理论与算法研究包_2026-10-16.zip` | `0b86d7f6ffce6e7d439b0c99266b2a37684f1b965305ec9c557050dca00c3bfe` |
| `F-CCP_可调算法_理论与实验_2026-10-17.zip` | `1afc93e92858084be623a39b4bb399239648c342db5da213f393e9ffccdfe519` |

---

## 2. 新稿目标结构与取舍总表

### 2.1 正文目录：保留7节，不建立“第一个算法＋第二个算法＋第三个算法”的研究流水账

1. **Introduction**：持续近优报告的统计成本，以及可调收益—认证分配的实际需求。
2. **Model, reliable reports, and maintenance cost**：保留M3第2节，区分任务参数与算法偏好参数。
3. **Flexible certificate-cost planning**：F-CCP主算法、四种模式、可靠性、收益保护、服务率面积界与兼容端点。
4. **Fundamental costs of continual maintenance**：保留M3第4节的一般下界和最坏风险结果；旧上界见证仍明确为Checkpoint-UCB。
5. **Temporary tasks and limits of the regret–maintenance trade-off**：保留重复更新的必要成本和两端分离；简述新增的信息限制和中间预算结果，完整ABM放附录。
6. **Numerical studies**：以F17冻结测试为主，展示纯收益、可调偏好、公平ALL对照、尾部与失败；旧CP研究降为辅助。
7. **Discussion**：区分可用性提升、已证成本和未闭合前沿。

正文主算法只使用 **Flexible Certificate-Cost Planning (F-CCP)** 一个名称；`CCP`指其证书规划基础或明示的旧配置，不再平行推出多个同等地位的新算法名称。

### 2.2 M3逐块操作总表

| M3位置 | 操作 | 完成后的去向与定位 |
|---|---|---|
| 题目、作者与机构、贡献脚注 | 保留 | 默认仍用现题；不自行改作者次序、署名、通信信息、盲审状态或稿件日期 |
| 第1页摘要末段的Checkpoint主方法叙述 | 重写 | 改成F-CCP是主实现；保留Checkpoint是解析见证的事实，不宣称完整前沿 |
| §1，页1—3 | 保留问题与已有文献；改贡献和组织段 | 一般统计理论＋灵活算法＋有限预算证据，不讲研究版本历史 |
| §2.1—2.3，页3—5 | 保留并做最小增补 | 原模型、风险、边界带与因果信息不变；增加参数分层 |
| §3、Algorithm 1、Proposition 3.1，页5—7 | 正文替换、原文迁移 | 新正文写F-CCP；原Checkpoint算法及命题完整移入新S5 |
| §4.1／Theorem 4.1，页7—8 | 保留 | 算法无关的共同参考环境下界 |
| §4.2／Theorem 4.2，页8—9 | 保留原statement与上界见证 | 显式常数仍对应Checkpoint-UCB；另指向F-CCP相应模式的同阶结论 |
| §4.3／Corollary 4.3，页9—10 | 保留 | 区分固定无限日程、终点臂数类、突发反例和不同参数范围 |
| §5.1—5.2，页10—11 | 保留、精简工具说明 | 奖励gap和边界距离的区别；面积迫使完成临时任务 |
| §5.3／Proposition 5.1，页11—12 | statement及证明迁入新S9；正文留机制公式和指引 | 不再让旧上界算法占据正文方法重心，但不丢掉证据复用的数学依据 |
| §5.4／Theorem 5.2，页12—13 | 保留、压缩证明概述 | 不把快速／暂缓Checkpoints换成F-CCP名称 |
| §5.5／Theorem 5.3，页13 | 保留 | 概率下界与联合分位推论依然属于指定族 |
| §6、Table 1、Figures 1—2，页13—18 | 主体替换，旧材料迁入新S17 | 主实验改为F17；旧四场景不能与新结果拼成同一实验 |
| §7，页18 | 重写 | 最新F-CCP状态和限制；不继续称“尚无可用实践方案” |
| Data and code availability，页18—19 | 重写 | 区分数据代际与实际提供文件，不伪造公开仓库 |
| References，页19—20 | 保留有效项、补核实来源、清理孤立项 | 不加入内部创新分数、聊天来源或虚构发表状态 |

### 2.3 三轮研究的进入位置

| 研究内容 | 默认去向 | 不允许的升级 |
|---|---|---|
| C16：混合证据、矩形gap报告、证书成本规划 | 正文§3＋新S2 | 不把标准置信序列和局部凸解称为整体统计最优 |
| C16：任意动作指数差regret界 | 正文§3的输入与结论＋新S3完整衔接 | 不能只引用“MC-MOSS本身好”就推任意动作好 |
| F17：双预算、服务控制器、四模式及其保证 | 正文§3重点；新S4完整证明 | 不把默认配置称为全前沿最优、全环境支配或尾部更优 |
| P16：未知任务失效时间的日程信息分离 | 正文§5短评述＋新S12完整定理 | 不是否定共同未知日程类上的因果minimax存在性 |
| P16：任意恢复数量引理、ABM中间预算匹配 | 正文§5一段准确概述＋新S13完整合同／证明／伪代码 | ABM不是F-CCP，指定窗口不是任意重叠到达 |
| P16：Shared／Bundle等候选与小模型LP | 项目研究存档；正文不新增专题 | LP是受限对象的计算，不是F-CCP达到完整前沿的证据 |
| C16／P16早期测试 | 新S16简短版本化研发说明；完整数据留发行包 | 不与F17跨场景、跨参数或跨重复数合并计算胜率 |
| F17冻结主实验＋修正ALL对照 | 正文§6的主要证据 | 错误旧ALL自适应输入不能继续用于主优势比较 |
| 三轮创新评价JSON和分数 | 仅项目管理档案 | 不能放入论文、自引当学术证据或贡献定理 |

这里对P16采用“正文简述、附录保留”的选择，是为了不让ABM夺走F-CCP主实现地位；不是删除这轮已有实质理论。

---

## 3. 逐项执行任务卡

### R2-00｜锁定源码、快照与工作区

**定位／输入：** M3/S3，用户当前LaTeX项目；本文件§1。

**执行要求：**

1. 查找实际主入口、补充入口、`\input`/`\include`子文件、共享宏、文献库、图片和表格生成脚本。将路径写入`source-map.json`；不要假设入口必叫`main.tex`。
2. 用正文题目、§3的Checkpoint-UCB、§4—5定理名称及页数验证确实对应M3/S3。页数不同但内容已更新时，先列差异，不退回旧版。
3. 保存源文件与PDF只读快照；记录git状态、已有用户修改和编译入口。后续工作限定在新分支或明确的修订目录。
4. 提取全部现有`\label`、引用及`\includegraphics`，建立基线清单；使用项目实际构建工具做一次基线编译，保存日志。

**验收标准：**

- `source-map.json`包含M3/S3对应入口、资源路径、哈希和各研究包路径。
- 基线编译成功，或确实记录原有编译问题；不把基线原有错误记成新方案已解决。
- 旧版文件与用户工作未丢失。

**阻塞处理：** 没有对应TeX源文件时标记`BLOCKED_SOURCE`；可完成内容映射和资料检查，不能伪造可编辑源码或声明已修稿。

### R2-01｜区分唯一主方法与解析见证

**定位／输入：** 本文件§2；M3§3—5；F17`theory.md`；P16`theory_frontier.md`。

**执行要求：**

建立`claim-map.csv`，至少包括：来源代号、原编号／标题、算法归属、模型／量词、关键参数范围、正文去向、证明去向、实现ID、状态。

明确记录五个对象：原两阶段UCB-AA（不在本稿）、Checkpoint-UCB（旧上界见证）、CCP（规划基础／旧对照）、F-CCP（主实现）、ABM（指定族中间预算见证）。一般下界的算法归属填“所有满足协议的策略”，不能填F-CCP。

新命题使用语义标签，如`thm:fccp-budget`、`prop:fccp-report`；不要占用旧数字后全文手改`Theorem 4.2`字符串。

**验收标准：**

- 每个保留或引入的主要命题都能追到完整证明和适用算法。
- 没有“换名继承”，没有删除旧见证后仍保留悬空的可达性结论。
- 无把C16/P16/F17三个研究批次的贡献重复计为三个不同的新定理。

### R2-02｜统一数学记号但不改任务

**定位／输入：** M3§2及S3 Notation and scope；本文件附录A。

**执行要求：**

保留稿件的$r_i,r^*(t),\Delta_i(t),P_t,N_t,V_t,\mathcal U_T(\eta)$与物理时间约定。新研究中的$\mu_i,B_t$只作符号映射，不改对象。

建立`notation-map.md`：真实均值$r_i$与规划半径不能同名；候选数$M_t$与beta-mixture过程、奖励和$S_i$与谱$\mathcal S_t$、分析队列$Q_t$与总配额$Q_T^{\mathrm{cap}}$、服务拒绝$D_T^{\mathrm{srv}}$与旧最大gap$D_i^T$必须区分。

新F报告按最大值排除自身坐标；旧Checkpoint见证仍使用其原报告规则。不能为了统一外观，把两种报告器悄悄替换成同一公式。

**验收标准：**

- 增加一份读者可用的参数／符号表；同一对象全稿一致，不同对象无歧义。
- $\mathcal U_T$仍是边界带外的累计未决臂时间；不是仅首次决定时间、未决比例、单次终点错误或平均分类准确率。
- 图表与模拟仍保持各实验固定的$\varepsilon,\eta,\delta$。

### R2-03｜改摘要，不更换统计主线

**定位／输入：** M3第1页摘要、关键词。

**执行要求：**

摘要保留任务模型、全程标签可靠性、共同认证负担、最坏面积与临时任务权衡四个要点。替换“唯一方法是固定精度Checkpoint-UCB”的叙述，加入F-CCP的可调目标、共享证据、收益核与双预算。

说明解析上界有显式构造支撑，但不能把旧两个端点指定为F-CCP达到。经验句应写“在冻结的多场景测试中改善若干／多数有限预算权衡，并披露尾部和失败”，不能写“uniformly superior”“dominates all benchmarks”或“achieves the full Pareto frontier”。

默认保留原题目；关键词可增加`confidence sequences`或`adaptive allocation`，但不要用关键词列表堆满算法名。摘要不写内部创新分数、开发耗时、对话轮次或未核实的发表状态。

**验收标准：**

- 摘要中的每项claim在正文或附录有落点。
- 概率模式与期望模式不混淆；“最优阶”只用于相应对象及模式。
- 作者、机构、通信方式、盲审状态不变；日期按用户原稿构建机制处理，不自动伪造投稿日期。

### R2-04｜重写引言的贡献与组织段

**定位／输入：** M3§1，页1—3，特别是最后两段。

**执行要求：**

保留已有模型定位与ALL-$\varepsilon$/联合收益识别的文献关系。把最后一段改成：固定检查点解释可达成本，但过于保守；F-CCP把有效报告与收益选择解耦，通过证书规划和两类预算提供可调实现。

贡献分三组：①一般维护困难；②指定多次更新中的收益—及时性结构；③F-CCP的可靠性、可控成本与有限预算实现。P16的新中间区间和日程信息限制以准确的一两句并入②，不另外罗列所有研究工具。

强调$\lambda$是服务偏好，不是已证明的Pareto对偶乘子；温度改变仅为行动启发式。更新全文组织句。

**验收标准：**

- 引言不再以“保存旧算法”或“修复旧代码”为中心。
- 不声称永久到达模型、近优集合、Thompson、置信序列或历史保留本身是新概念。
- F-CCP主推的是可调实施能力，不替代一般理论的创新依据。

### R2-05｜保留第2节并增加任务／调度参数分层

**定位／输入：** M3§2.1—2.3，页3—5。

**执行要求：**

原始模型和式(1)—(2)保持数学内容不变。参数表拆成：任务参数$(\varepsilon,\eta,\delta)$；调度参数$(\lambda,p_0,k_0,\nu)$；收益行为参数$(\mathsf B,\theta)$；保护参数$(\beta_R,\beta_C)$。固定检查点$\rho$列为辅助证据参数；F-CCP兜底取$\rho=\eta/4$。

在§2.3保留正、负证据不对称与任务失效解释，补充“均值彼此接近”和“接近$\varepsilon$边界”的区别。明确后者未必意味着认证便宜。

基础算法信息集仍不含未来日程和终点。后面受限性能族比较允许的已知信息单独规定，不能悄悄改掉此处合同。

**验收标准：**

- 不添加全局唯一最优、统一正gap、已知最优参照或所有臂远离边界假设。
- 保留$K_T>T$及任意有限批到达；每轮只有一个真实观测。
- 全模型标签可靠性与性能族上的面积条件仍分开；不以加权期望损失替代原风险。

### R2-06｜将Checkpoint-UCB完整迁入解析见证附录

**定位／输入：** M3§3、Algorithm 1、Proposition 3.1；S3§S2及Lemma S2.1。

**执行要求：**

把原正文算法、式(3)—(7)、不重置历史、固定前缀与总服务量说明，连同S3§S2合并为新S5“Checkpoint-UCB as an attainability witness”。去掉重复证明，但保留完整算法、精确常数、报告器和无条件regret界。

新正文§3开头只留一小段交代见证位置。将原Proposition 3.1和Algorithm 1的所有内部引用迁到新的语义标签。M3§4.2、Corollary 4.3、§5两个端点继续引用该见证，不得将见证删除。

正文主Algorithm 1的位置交给F-CCP；Checkpoint伪代码改为补充算法编号。

**验收标准：**

- 旧$1-\delta/2$报告概率、$3\log(2t)$UCB核、偶数FIFO、固定报告区间均保留。
- 上界(7)、总服务数$\le\sum_iq_i$及Lemma S2.1有完整证明来源。
- 文中不出现“F-CCP with $\lambda=1$ is exactly Checkpoint-UCB”；这在报告、调度和收益核上都不成立。

### R2-07｜建立F-CCP共享证据层

**定位／输入：** 新正文§3.1；C16§2—3；F17`theory.md`§2。

**执行要求：**

按附录B完整说明混合检验反演、所有已观察前缀交，以及达到事前固定$q_i$后额外交入检查点区间。二者各用$\delta/2$总错误预算；不要求二者独立。

新主算法不再在$q_i$之前一律报告区间$[0,1]$。区别必须写清：固定Checkpoint的报告证据只形成一次；F-CCP从每次观测提取时间一致证据，检查点仅作有限工作兜底。

给出排除自身的$g_i^-,g_i^+$，确定标签、$Z_t$边界带暂停与$W_t$主动工作集。单臂$g_i^-=g_i^+=0$；空交集采用持久失败标志、全未决、停止主动服务、收益层继续定义。

**验收标准：**

- 报告区间、Beta行为评分、虚拟MC指数三种对象分别命名。
- 不把后验credible interval当频率置信序列，不使用冷温度倍增后的伪样本数做报告。
- 旧S1全前缀Hoeffding及其exclusion-first失败规则只限对应旧实验；不能误写为F-CCP失败合同。

### R2-08｜写清证书成本规划，而不是只说“调用CCP”

**定位／输入：** 新正文§3.2；C16§4；F17§3；F17`src/flexible_engine.py::service_plan`。

**执行要求：**

给出规划中心、半径、比较对象选择、目标精度和双端点凸代理。F-CCP采用$c_i=\nu+(1-\lambda_t)\zeta_t(i)$，而旧CCP对照的$c_i=\nu+\zeta_t(i)$不同；不能把旧公式全文复制。

正文保留代理目标和一段解释，完整闭式／边界解、零半径数值正则化和端点优先级放新S2。明确每次只真实采一个端点，随后重新规划；正认证可能有多个竞争者，一个pair被解决不等于整项报告完成。

候选服务动作必须满足真实$N_i<q_i$；无合法规划时按源代码选未完成检查点中的最宽区间兜底。严格按冻结平局规则执行，不自行加UCB式硬删除。

**验收标准：**

- 读者能从伪代码和新S2完整复现服务对象选择。
- 只声称局部连续代理解最优，不把代理成本当作已证明的信息复杂度。
- $\max(1,N_i)$和$10^{-12}$规划正则化不进入真实计数或统计证据。

### R2-09｜将虚拟收益指数与双预算写成可执行合同

**定位／输入：** 新正文§3.3；F17§4、§6；C16§5—6。

**执行要求：**

定义截断MC-MOSS虚拟时钟、$J_i(t)$、$\zeta_t(i)$、当前前缀谱及其running maximum。只用已到达臂的年龄；第一条初始臂是计数锚点，不是已知最优臂。

引入两本从不清零的账本$C_R,C_C$：按实际收益轮和实际认证轮分别计费。认证提议超出$\beta_C\overline{\mathcal S}_t$时，转入收益轮；在收益可行集$\mathcal F_R(t)$中最大化已生成的收益评分。拒绝的未执行服务不能产生观测或真实regret。

明确`None/null`表示关闭该保护（数学$\infty$），不是预算0。预算系数为运行前固定参数；本轮只证明偏好$\lambda_t$可预测切换，不额外宣称任意在线重置预算合法。

**验收标准：**

- 最大$J_i$臂的$\zeta=0$，保证收益可行集非空；证明和实现都处理$K_t=1$。
- 拒绝服务后不是无条件“采MC-MOSS最大臂”：最终版本要在收益可行集中最大化所选收益核评分。
- 不把$C_R+C_C$叫作相对某个独立运行基线的已实现regret差。

### R2-10｜加入服务偏好、预设模式和运行中切换说明

**定位／输入：** 新正文§3.4；F17§3、§9；F17 API。

**执行要求：**

展示附录B中的$p_t$公式、固定服务模式与相位累积器。固定$\lambda>0$给$p_{\min}(\lambda)$，同时写明$\lambda=0$不具有正服务下限。

用一张表给四预设：F-R、Balanced、Classification、Compatibility。默认值严格来自冻结配置／API：$\lambda=0,.6,1,0$；温度$.5,.5,.5,1$；收益预算$16,16,16,\infty$；认证预算按相应模式。

把“少量便宜／昂贵待办”的启发式意义说清；当前控制器使用$|W_t|$而非仅$K_t$。不声称能观察真实gap或真正未决面积进行调参。

明确`set_priority(1)`不会自动关闭认证预算，模式切换不重置相位、证据、计数或账本；从有服务切到纯收益，不等于该基线从零独立运行的历史。

**验收标准：**

- 用户能根据目标选择配置，不需要读取源代码才知道哪个模式是否受认证预算限制。
- 不能把$\lambda$叫作已验证最优的拉格朗日乘子；不能声称实测两指标随$\lambda$严格单调。
- 不把`adaptive=True`解释为自动精度最优、自动到达预测或在线选择最佳基线。

### R2-11｜用正式伪代码替换原主Algorithm 1

**定位／输入：** F17`src/flexible_ccp.py`与生产`src/flexible_v2.py::choose_dual`；本文件附录C。

**执行要求：**

正文Algorithm 1给出接纳、虚拟时钟、当前报告工作、计划、相位、认证预算检查、收益投影、单次观测、证据更新和最终报告的完整顺序。繁长pair-plan写成有定义且可追溯的子程序，不以“choose a good arm”代替。

区别三份代码：`flexible_engine.py::choose_flexible`是早期单账本开发分支；冻结主测试使用`flexible_v2.py::choose_dual`；交互接口用`FlexibleCCP`。不能误将早期单账本函数作为最终算法。

算法所有持久状态、初始化、零样本、失败状态、平局、随机数消费和边界模式必须可追溯到冻结实现。数学算法采用精确比较；数值容差单独列入实现说明。

**验收标准：**

- 每个物理时刻恰好一拉；观测后报告。
- 不先看拟服务奖励再决定是否改选；不循环重抽Thompson直到某个“满意”动作出现。
- 负报告不永久删除收益资格；所有历史样本保留。
- 源码／伪代码逐分支对照表完成。

### R2-12｜加入新可靠性与基线兼容性命题

**定位／输入：** F17 Proposition 1、Theorem 2；正文§3.5。

**执行要求：**

可靠性命题必须覆盖任意合法可预测调度及各模式，不依赖局部代理规划正确。给简短证明思路，完整超鞅／反演和矩形极值证明移入新S2。

兼容命题明确：从初始时刻起服务恒为0、关闭收益保护、相同收益核和完整状态、相同后端随机数源，才得到逐路径相同动作与regret。把该端点与温度$.5$且有限保护的F-R区分。

基线兼容命题不得扩大到“自动选中每个环境最好的基线”，也不得将相同seed跨NumPy／Numba后端解释成逐位一致。

**验收标准：**

- F-CCP总可靠性写$1-\delta$；Checkpoint见证的$1-\delta/2$不机械迁移。
- 兼容性声明不包含默认F-R的纯数值优势，也不声称任何额外及时性保证。
- 在数值部分明确哪个结果属于路径等价、哪个只是比较均值。

### R2-13｜加入双预算regret定理和完整依赖桥梁

**定位／输入：** F17 Theorem 4；C16 Theorem D；G的潜在前缀和到达时钟记账。

**执行要求：**

正文陈述附录B中有限双预算界、纯收益特例，以及无认证上限时额外$Q_T^{cap}$的界。条件是固定预算系数，动作只依赖合法历史，奖励范围为$[0,1]$。

新S3必须给出“任意动作＋指数差”的关键比较，不可以仅引用“MC-MOSS自身的最优阶”。明确潜在前缀、不同臂—拉前计数对、截断指数与到达时钟不依赖服务选择的接口，之后才给双账本代入。

将G的谱最优性标为既有结果，提供准确可引用的来源身份；不复制独立论文的capacity、固定点、随机到达等无关主理论。

**验收标准：**

- 界为$(300+2\beta_R+2\beta_C)\mathcal S_T$而非平均各核regret。
- F-R固定$(16,0)$的界为$332\mathcal S_T$；任意mode不能都标成332。
- 不条件于标签成功，不遗漏坏事件；不宣称保守常数是精确最优常数。

**阻塞处理：** 若G的必要证明文本或可识别来源缺失，标记`BLOCKED_PROOF_INTERFACE`。不得用有洞的引用继续宣称谱最优，也不得无说明地把定理改成另一条较弱结论。

### R2-14｜加入可变服务率面积定理和不饥饿推论

**定位／输入：** F17 Theorem 5、Corollary 6；正文§3.5／新S4。

**执行要求：**

陈述共同覆盖事件上的面积界，明确保留服务拒绝$D_T^{srv}$与$p_{min}$。分类优先模式设置$\lambda=1,\beta_C=\infty$，可得最坏面积同阶；有限预算默认模式不得删除拒绝项。

有限最终臂数的不饥饿结果作为正文简短推论、完整保守界留新S4。写清$\beta_C>0$、忙轮服务率正下界、到达最终停止、结论在覆盖事件上且仅对边界带外未决。

任意变化$\lambda_t$的可靠性仍有效，但没有统一正下界时，不援引服务完成速度定理。

**验收标准：**

- 不把“最终边界外完成”写成无条件几乎必然精确oracle-set一致性。
- $\lambda=0$只报告已有信息，没有主动及时性保证。
- 最坏面积匹配仅在原下界共同参数范围中声称；多数新实验不满足该窄范围，不冒充渐近验证。

### R2-15｜保留共同认证下界，不使其服从新算法

**定位／输入：** M3§4.1／Theorem 4.1，S3§S3。

**执行要求：**

保留同一个参考环境、全部one-candidate alternatives、$q_-$、分析队列和概率常数。只更新符号冲突、前后指引与新附录引用。

保留对算法可以知道完整日程、终点和参照分布仍成立的限定；保留困难标签从期望计数选取而非随机事后挑选。

删除任何把此信息队列描述成F-CCP实际服务队列的句子。正文解释可以连接新$W_t$：它提醒不确定性有跨臂作用，但不直接证明局部CCP的最优分配。

**验收标准：**

- $(3/4-\delta)\mathcal B_T$、$\mathcal B_T/4$和概率$1/4$及其参数范围未改。
- 分析队列与算法相位、F工作量$Q_T^{cap}$没有混同。
- 新算法没有被当成下界成立的前提。

### R2-16｜保留最坏面积与增长边界，并明确两套上界角色

**定位／输入：** M3§4.2—4.3，Theorem 4.2、Corollary 4.3；S3§S5。

**执行要求：**

原最坏面积definition和显式常数$2^{-24},256$保留，Checkpoint-UCB继续作为原upper witness。原联合regret式(11)默认保留在定理后的“Checkpoint见证”说明段，完整证明迁入新S5；不能把这些常数改挂到F-CCP名下。

追加一句：F-CCP分类优先模式由新服务定理得到相同最坏阶，但其regret保证和常数另外陈述。两种可达性不要合成“默认F-CCP同时最小”。

Corollary 4.3保留固定无限日程与终点臂数类的不同量词；必要$K_t=o(\sqrt t)$不升级为一般充分。S3 Lemma S2.1覆盖较宽$\eta$范围的引用已在M3修好，不能回退到旧错误引文。

**验收标准：**

- 一般下界不依赖新服务启发式，minimax面积本身未增加regret预算。
- 保留静态第一轮批次即可达到最坏下界的解释。
- 保留突发反例及“困难环境可随终点变化”的均匀性范围。

### R2-17｜压缩但保留临时任务和两端分离

**定位／输入：** M3§5.1—5.5，S3§S6—S8。

**执行要求：**

保留性能族$(J,M,v,d,H)$、奖励gap与边界距离、未知参照身份、最终近优集包含全部参照这些事实。保留Theorems 5.2、5.3的完整statement与条件。

将Proposition 5.1完整statement及证明移入新S9；正文§5.3保留旧上界与新参照下界如何比较的机制公式，并明确此处证明的是Checkpoint见证，不是任意F配置。

快速端upper使用规定$H$及$R_T\le2\varepsilon T$，暂缓端只有upper；$d\downarrow0$时$\eta=d/2$和$T$也改变。不能删这些限定来写成更普遍的曲线。

Theorem 5.3的概率下界与联合分位推论保留；停止在第$q+1$个候选观测的技术约定保留在证明中。

**验收标准：**

- 所有保留上界仍有具体可执行见证及完整证明，不给F-CCP改名套用。
- 主文用较短篇幅讲清机制；旧heterogeneous上界细节不与新算法展开争夺篇幅。
- 没有把“允许面积扩大9倍”解释为每个个体延迟扩大9倍。

### R2-18｜整合P16理论，但不制造第四个正文主算法

**定位／输入：** P16`theory_frontier.md`§2—5；M3§1、§5、§7原“中间预算仍完全未知”表述。

**执行要求：**

正文§5增加短小一节“Information limits and intermediate service levels”：分别概述未知失效时间的日程信息分离，以及ABM在指定充分分离族中覆盖一段中间预算的结果；指向新S12/S13。

新S12迁入P16定理1及两边可行性；新S13迁入任意$s$部分恢复引理、面积转完成数的下界、ABM激活后新块证据、窗口条件、含$R_0(T)$的匹配式。

正文不完整展开ABM伪代码，不把Shared命名成优于CCP的新主方法。将原文“中间预算尚未刻画”改成“在一个充分分离的更新族上已有区间结果；任意重叠和一般因果前沿仍未解决”。

**验收标准：**

- ABM的$s(a)$使用性能族$m,H$；运行无需未来不等于面积参数映射无需未来。
- ABM不同于F-CCP；不把局部前沿下界视为默认F配置的matching。
- 新附录的完整条件见附录D，不能只迁移结果公式。

**阻塞处理：** P16源证明缺失或接口审查发现未闭合问题时，暂停该新附录和对应成果claim。原M3结果继续保留，不把未核查结果写成已完成。

### R2-19｜重排补充材料并修复所有引用

**定位／输入：** S3§S1—S13；本文件§4。

**执行要求：**

按§4迁移表建立新S1—S17。完整保留一般下界证明、旧Checkpoint见证、量词和失败事件；F新证明与旧见证分节，不拼接成一个模糊算法。

旧S1的标准概率工具保留，混合置信证明另列新S2；旧S10的多精度强一致性保留为独立扩展，不加到F-CCP的定理列表。旧S11信息松弛和旧S9兼容窗口结果仍只是lower constraints。

引入全稿统一语义标签，自动编号；重建主—补交叉引用与附录目录。不要在PDF式号上手工加减常数完成重排。

**验收标准：**

- `claim-map.csv`每行都有最终label、正文／附录位置和证明状态。
- 无undefined reference、误引相同数字、重复label，主文中所有supplement指向真实条目。
- 旧或新含义不同的“同一个策略”没有被合并。

### R2-20｜冻结算法代码与名字映射

**定位／输入：** F17`src/`、三个包的manifest；旧CP实验源码。

**执行要求：**

发行代码中保留F17的`flexible_ccp.py`、`flexible_v2.py`、`flexible_engine.py`、`ccp_primitives.py`、`matched_all.py`和修正对照驱动的依赖闭包。若整理路径或命名，使用薄包装／导入适配，并留下原始只读副本、哈希与映射。

主方法ID使用原数据的`F-R`,`F-auto-0.6`,`F-area`等；显示名称可以美化但ID不能改写原CSV。`CCP-original`指F17套件中的旧CCP配置，不是M3里的CP-FIFO，也不自动等于C16历史的每一个实现细节。

不删除开发分支以伪装只试过赢家；但对外文档只推荐清楚的最终入口，不要求用户猜哪个`choose_*`函数是生产版。

**验收标准：**

- 代码依赖完整，不只拷贝一个会导入缺失模块的`flexible_ccp.py`。
- 冻结文件哈希不变；重定位适配有独立版本及测试。
- `compatibility`同一后端路径等价与跨后端仅同分布的边界写入README。

### R2-21｜为各代实验建立不可混用的数据清单

**定位／输入：** M3/S3旧5760次；C16/P16旧测试；F17主测试及修正对照。

**执行要求：**

以F17为新主实验，建立四代数据表：旧Checkpoint四场景5760条；C16的13440条测试；P16的12672条测试；F17的27648条主测试＋1152条修正ALL。

开发轨迹单列，不与测试合并。三个时代中的stable、burst、ALL等相似名称并不表示同一个环境或算法配置。

保留F17的错误旧`ALL-auto-0.6`记录，但主对照改用`ALL-auto-costmatched`。保留审计发现、修正时间和只改对照成本输入的说明；不能把补跑伪装成最初24配置之一未发生变化。

旧M3四场景完整表格及失败结论移入新S17；C16/P16只留必要研发说明及发行数据，不能占据新的主测试胜率。

**验收标准：**

- F17存储记录总数28800；源summary有300行、25个方法×12场景，其中旧ALL与修正ALL同时存在。
- 如果制作“24方法修正后主清单”，是用1152条修正数据替换对应旧ALL行，仍为27648条；不是无说明地丢弃原数据。
- 不写成27648次独立环境试验；同seed方法共享奖励，重复单位是配对实验。

### R2-22｜重写实验协议和基线定义

**定位／输入：** 新正文§6.1；F17`protocols/holdout-freeze.json`和`matched-all-freeze.json`。

**执行要求：**

明确12场景、每场景96次配对重复、2—20条臂、12000—16000物理终点、11类Bernoulli＋1类有界两点环境，以及各场景$\varepsilon,\eta$可能不同。列场景总表，完整arrival／means放新S15。

解释潜在流共享与同批均值标签共同随机置换，策略不接收未来／真均值／终点。保留开发—测试分离及预设选参标准，不能根据测试重新选默认值。

五个收益基线为UCB1、Growing-MOSS、MC-MOSS、标准Thompson和KL-UCB：不加认证服务；附带同样有效报告器仅用于观察未决量。别把M3的保守UCB误当成本轮UCB1。

联合对照是修正ALL、旧CCP和预设F配置；明确它们共享哪些证据／收益／预算，哪个模块不同。ALL是自然适配，不称FAREAST或$(ST)^2$原版实现。

**验收标准：**

- 协议的真实参数从JSON生成，不从聊天舍入示例抄入。
- 非Bernoulli测试中Beta行动评分不被称作正确Bernoulli后验。
- 新协议不沿用旧全部$T=20000,\varepsilon=.30,\eta=.10$或160重复的叙述。

### R2-23｜制作纯收益主表并限定“不差于基线”的含义

**定位／输入：** 新正文§6.2；F17`holdout-all.csv`、`pure-regret-paired.csv`。

**执行要求：**

主表展示12场景×六方法（五基线＋F-R）的平均regret；标准误可同表或附录给出。按附录E数值快照核对，重点保留two_close反例及温度／保护消融。

正文允许说明11/12场景中F-R均值低于全部五基线、59/60个比较点估计更低及等权均值降19.5%，但这些是冻结套件的描述，不是全环境定理。

配对比较按同一scenario与rep合并；报告逐比较95%区间以及预先设定的60次Bonferroni单侧近似t检查。零差上端点通过52/60、宽松5%+2通过54/60；后者不是用户原来的严格零差条件。

说明纯收益关闭了证书调度，优势主要属于收益核配置及保护，不能归因于未执行的认证计划。

**验收标准：**

- `F-R`与`F-R-TS-exact`不混淆；兼容端点不能与基线列作为两个独立胜出方法重复计数。
- 不用“未显著更差”推导零容忍非劣性，不把59个低均值叫59个显著胜利。
- 所有均值由原始值重算后舍入，不用表格舍入数再算百分比或标准误。

### R2-24｜制作偏好权衡和公平调度比较

**定位／输入：** 新正文§6.3；F17`joint-paired.csv`、修正对照及预设列表。

**执行要求：**

展示$\lambda=0,.1,.3,.6,.9,1$且认证预算固定为1的成本点，另列分类优先$\beta_C=\infty$，不可将两者无区分连成一条“同参数”曲线。

重点比较F-auto-0.6与ALL-auto-costmatched；F-area与ALL-area；F-auto-0.6与CCP-original。保留后者是regret更低、面积更高的权衡，不写成全面改善。

给出控制器实际提议服务率、成功服务、被拒绝服务和最终未决等诊断；提议服务率不等于实际分配比例。

保留固定率、自适应、无认证上限、温度1与温度.5等已有消融；没有对应数据的因果机制不补造实验。

**验收标准：**

- 主优势比较不使用错误旧ALL自适应cost=0分支。
- 不把“相同$\lambda$”说成“相同实际服务次数／相同面积预算”，也不把相近均值成本说成证明Pareto支配。
- $\lambda=.9$与1的非单调点保留，不通过平滑或挑点制造单调性。

### R2-25｜把失败、尾部和局限纳入主结果

**定位／输入：** 新正文§6.4；F17`audit.md`及raw/summary。

**执行要求：**

正文至少保留：F-R与Thompson在burst、ceiling、larger_pool的经验95%regret分位数对照；默认自适应模式存在1/1152误标；覆盖失败与空交集回退有非零记录。

全部失败轨迹继续进入均值、面积和分位数；不在成功路径子集上比较regret。空交集全未决不能被写成有效完成。

将“zero errors in all 5760 runs”限定在新S17旧实验；新主实验绝不能沿用“全体零错”。若报告全方法误标总数，说明共享潜在流导致事件相关，不能当独立可靠性试验数量。

现有96重复零错的描述不能验证所有环境、所有时间的理论保证；经验分位数也不是regret高概率定理。

**验收标准：**

- 主文同时保留均值收益和尾部代价，不只在发行日志埋入不利结果。
- 错误ALL修正、相位浮点临界和初始编译失败的审计归档可追溯。
- 不宣称本次编辑重新独立验证了全部概率理论。

### R2-26｜重排图表，避免伪造不存在的路径数据

**定位／输入：** M3 Table 1、Figures 1—2；S3 Figure 1、Table 1；F17数据与图。

**执行要求：**

按本文件§5生成新正文表图。旧M3 Table 1和Figures 1—2迁入新S17，与旧S13数据说明保持关联；图中的CP仍然是Checkpoint配置，不重新贴F-CCP图例。

新主图以端点数据为主：纯收益配对差图；预设偏好成本图。可用逐次CSV制作终点分布图，不能从端点均值反推整条学习曲线。

F17每场景只保存前4个重复、间隔200轮的诊断路径。若使用，只能标明“4条诊断路径／该保存网格”；不能画成96次均值及置信带。需要96路径的新模拟另行申请，不在本轮执行。

重新绘图和表格脚本只读冻结数据，输出到`revision2/generated/`。图注写清误差条类型、重复单位、面积单位和非最优前沿性质。

**验收标准：**

- 所有图表能由一条记录的脚本命令重建；原数据和旧图无被覆盖。
- 不跨场景或跨代混算误差条，不把折线连接的参数点称为已证前沿。
- PDF中图例可读、轴标题完整、无缩到不可辨认的24方法一张图。

### R2-27｜重写讨论、开放接口与结论强度

**定位／输入：** M3§7；C16/P16/F17结果状态表。

**执行要求：**

讨论按“成本理论告诉了什么—F实现增加了什么—仍不能声称什么”展开。明确默认F-R低均值优势与尾部代价；分类优先有最坏阶而非逐实例最快；固定有限双预算不保证严格面积。

更新中间预算状态：P16在受限分离族已有匹配区间；共同未知日程类、一般重叠和默认F的前沿仍未闭合。原最终强一致性仍属于另一个复核算法。

把以后可能研究的自动精度、尾部稳健收益核、原版FAREAST忠实适配、大臂数计算复杂度、完整因果前沿列为限制／方向，不写成当前承诺。

**验收标准：**

- 没有同时出现“intermediate budgets completely open”和“已完整刻画一般frontier”等互相冲突句子。
- 不以首轮不可能反例否定所有模型选择／渐近非劣性可能；反例只说明明示的零余项要求。
- 不重新要求保存／重跑已退出的两阶段UCB-AA作为本稿前置条件。

### R2-28｜增补文献与独立谱工作的引用

**定位／输入：** M3/S3文献库；三个研究包中的来源列表；G。

**执行要求：**

保留当前已经相关的ALL-$\varepsilon$、收益—识别、信息下界和到达文献。补入新证据层、Thompson／KL基线、随机评分保护等实际使用的来源；优先复用已核实Bib条目。

必须将已有的MOTS、Conservative Bandits等与本方法区别说清，不声称本轮重新发明混合置信序列、温度评分或预算原则。只讨论实际相关差异，不能为了增加条目而扩写无关综述。

G的MC-MOSS和谱定理是明确既有输入；检查题目、作者、版本、预印本信息后建立真实引用。没有公开标识时按可证实的unpublished companion manuscript身份处理，不能虚构arXiv号、DOI或发表年份。

稿件中不出现ChatGPT的`filecite`标记或本任务书路径；使用项目`\cite`和`\ref`。本任务书的页码定位不是论文参考文献。

**验收标准：**

- 每个新方法事实和引用都有真实来源条目，不将标准结果当新增贡献。
- 需要补充核验但尚未取得的书目信息记入`blocked-items.md`，不得凭常识补作者／卷期／DOI。
- 未经实际外部核查，不声称本轮完成最新文献审计或更新创新评分。

### R2-29｜更新数据可用性、资源说明与发行目录

**定位／输入：** M3 Data and code availability；S3§S13.3；三个包README/manifest。

**执行要求：**

说明本文使用模拟数据；区分F17主测试27648、审计修正1152及旧CP辅助实验5760。列出实际随文提供的代码、配置、逐次数据、汇总和审计材料。

旧S13的Windows硬件、Python3.11.7和13.5秒只属于旧实验；不得覆盖到F17。新资源说明从F17`environment.json`及真实执行记录提取；没有准确运行时间就不提供估计冒充实测。

修订前后代码、源PDF、源码和数据均版本化。公开代码仓库／永久档案只有实际存在且可核查时才写出；目前M3明确尚无公开URL，不能自动写“publicly available”。

发行清单中保留完整旧记录的归档去向，正文不需要展示研究评分JSON和开发全部失败日志，但这些不能被删掉。

**验收标准：**

- 公共可用性与本地随包提供分开。
- 各代环境信息不混写，跨后端seed不声称位级等价。
- 新稿结果所需依赖、数据和生成脚本齐全；缺失资源精确列明。

### R2-30｜运行数学、代码、数值和交叉引用验收

**定位／输入：** 本文件附录A—F；实际项目构建。

**执行要求：**

数学：逐项核对claim-map中的模式、假设、常数、时间和概率量词，特别审查Checkpoint／ABM／F的归属。

代码：核查冻结hash；在复制工作区做短接口和基线兼容检查，保留真实命令和输出。不要为通过断言而修改主实验算法。

数值：从原始F数据重算所有论文新表格，运行附录F的只读核验；完整保留失败路径、旧ALL及修正ALL的身份。

编译：按真实入口编译正文和补充，检查引文／编号／图表；渲染并查看全部页面，特别长公式、模式表、主伪代码、跨页表格和补充目录。

**验收标准：**

- 编译日志无新增undefined citation/reference、duplicate label、遗漏资源；溢出有逐页处理记录。
- 冻结算法／数据hash保持不变；再分析与新增实验明确区分。
- 不把仅限本轮结构／算术核验的范围标成独立完整证明审计。

### R2-31｜交付完整修订与未完成接口清单

**定位／输入：** 全部任务状态、源文件、生成输出。

**执行要求：**

交付新正文和补充PDF、对应可编辑源码、必要图表与生成脚本、`source-map.json`、`claim-map.csv`、`task-status.md`、`change-log.md`及`blocked-items.md`。附录C的接口说明和数据版本映射放入复现README。

逐项报告真正执行的命令和检查；给出一般理论保留清单、Checkpoint迁移清单、F新增清单和P16附录清单。

未获授权的新实验、新定理、改温度或改控制器只列在`future-research.md`。没有源码或关键研究材料时，交付可完成部分和明确阻塞，不声称“稿件已完成第二轮整合”。

**验收标准：**

- R2-00…R2-31均有状态、具体修改位置及验证证据；不能只给“已优化全文”的笼统总结。
- 用户可以直接找到正文主算法、对应证明、每个数值claim的CSV来源及不利结果。
- 旧版本可恢复，新稿不会把所有算法的最强结论错误相加。

---

## 4. 补充材料逐节迁移与目标目录

下表的“旧S编号”只指本次 `supplement(3).pdf`。新编号是建议顺序；实际TeX用语义label自动生成，不能引用旧35页版本的S编号。

| 新补充节 | 内容 | 确切来源／迁移操作 |
|---|---|---|
| **S1. Probability tools and risk conventions** | 物理观测、潜在流、Hoeffding、KL、概率／期望区别 | 旧S1页1—3及scope；保留被后文使用的工具，不混入算法特定失败处理 |
| **S2. Sequential evidence and certificate planning** | 混合置信序列、检查点交集、矩形gap、边界带暂停、pair-plan闭式解 | C16§2—4、F17§2—3；加新主算法的报告合同 |
| **S3. Virtual indices and the optimism-gap bound** | MC时钟、截断、潜在前缀、任意动作指数差及谱归并 | C16§5—6＋G的精确输入；列明复用归属 |
| **S4. Guarantees for Flexible CCP** | 模式、兼容、双预算、可变服务率、有限臂完成、零余项反例 | F17§5—8及§11；不把反例当作主创新 |
| **S5. Checkpoint-UCB as an attainability witness** | 原算法完整伪代码、报告正确、无条件regret、任意到达完成 | M3§3／原Prop3.1＋旧S2页3—4；不改变行为 |
| **S6. Broadcast uncertainty** | 共同参考环境及队列二次面积 | 旧S3页4—5 |
| **S7. Partial recovery, worst area, and growth** | 原半完成引理、截断、最坏面积和增长反例 | 旧S4—S5页5—8 |
| **S8. Area constraints on temporary tasks** | 同一乘积先验的面积到任务成本；异质凸松弛 | 旧S6页8—9 |
| **S9. Shared evidence and two endpoint witnesses** | 异质共享证据、含gap的无条件upper、快速／暂缓、旧中间配置 | M3Prop5.1＋旧S7页9—11；旧S12页16—17合并成后续子节 |
| **S10. Regret quantiles** | bounded candidate-budget lemma、非消失概率、joint quantile | 旧S8页11—13，保留$q+1$停止规则 |
| **S11. General lower-bound extensions** | 兼容窗口截断、一般信息分配松弛 | 旧S9页13—14＋旧S11页15—16；保留“必要非可达”标识 |
| **S12. Schedule information and causal comparison** | 早／晚更新共同信息历史分离 | P16定理1及其完整可行性说明 |
| **S13. Activation-budgeted intermediate maintenance** | 任意$s$部分恢复、ABM、预算区间、含$R_0(T)$的界 | P16定理2—5，全部算法合同和窗口条件 |
| **S14. A separate exact-consistency extension** | 可复核多精度算法的最终强一致性 | 旧S10页14—15；不得归为F-CCP性质 |
| **S15. Main numerical protocol and full results** | F17配置、方法映射、全场景表、失败／尾部／配对统计 | F17最终主实验与修正ALL对照；包括代码和后端区别 |
| **S16. Development, ablations, and implementation audit** | 三轮研发范围、已有消融、失败修正、有限资源和数值容差 | F17审计及必要C16/P16研发记录；不放内部创新评分 |
| **S17. Earlier checkpoint comparison** | M3旧四场景全部表图、服务数、Batch100记账、资源说明 | 原M3§6、旧S13页17—20整体迁移并去重；旧结果保持原身份 |

### 4.1 旧S3每节的最终去向检查

```text
旧 S1  -> 新 S1 + 新 S5中Checkpoint报告规则；旧前缀报告细节供新S17引用
旧 S2  -> 新 S5
旧 S3  -> 新 S6
旧 S4  -> 新 S7
旧 S5  -> 新 S7
旧 S6  -> 新 S8
旧 S7  -> 新 S9
旧 S8  -> 新 S10
旧 S9  -> 新 S11
旧 S10 -> 新 S14
旧 S11 -> 新 S11
旧 S12 -> 新 S9的旧中间配置与已知参照诊断（非ABM替代品）
旧 S13 -> 新 S17；不能把旧资源说明当作F17资源
```

无需为了所有节都等长而删证明。若版面过长，先合并同一工具的重复说明、将研发日志移至发行材料；不要削掉主要定理的假设、坏事件处理和可达性见证。

---

## 5. 图表与实验展示的具体合同

最终编号自动生成；以下名称是建议的TeX label。

| 位置／label | 内容 | 数据与绘制要求 |
|---|---|---|
| §3 `tab:fccp-modes` | 四个预设、输入、两个预算、温度、保证范围 | 从F17冻结配置／API生成；不是实验结果表 |
| §3 `alg:flexible-ccp` | 主算法，含独立预算和相位 | 按附录C，不重用旧Checkpoint伪代码改名 |
| §6 `tab:reward-baselines` | 12场景的F-R和五收益基线 | 96配对重复；正文均值和SE可分层展示，全部数值必须在新S15 |
| §6 `fig:reward-paired` | F-R减Thompson的12场景配对差及逐比较区间 | 同时给60比较校正结论；负值含义明确；不能画成全部显著胜出 |
| §6 `tab:preference-costs` | 预设偏好与两项指标 | 明示跨场景等权平均仅描述；全部场景分解见附录 |
| §6 `fig:preference-tradeoff` | 固定认证预算的偏好点；无限认证预算单独符号 | 禁止称“optimal frontier”；点顺序按预设参数，不按有利结果排序 |
| §6／S15 `tab:tail-and-failure` | 重要尾部分位数、误标签、覆盖失败、空交集 | 不只报零错误方法；denominator与独立单位明确 |
| S15 `tab:all-methods` | 全部冻结方法和修正ALL的逐场景表 | 错误旧ALL单列“superseded controller diagnostic”，不放主优势列 |
| S17 `tab:legacy-checkpoint` | 原M3 Table 1，24行，旧160重复 | 原数值／场景／方法名保持，禁止替换为F数据 |
| S17 `fig:legacy-costs`、`fig:legacy-paths` | 原M3 Figures 1—2及旧S13追加路径 | 标明旧4场景9方法；不得与新均值图连用 |

### 5.1 主实验不能成立的展示方式

- 用不同实验中的`stable`结果拼成同一行比较。
- 把旧CP的160条路径和F17的前4条保存路径合成“同样重复数”的误差带。
- 把F17每场景的终点值拟合成不存在的逐轮学习曲线。
- 只画收益最优配置的regret，同时画另一个配置最小面积，再统称“F-CCP的同一表现”。
- 给未决比例、原始未决臂数和边界带外未决面积使用相同图例却不标量纲。
- 将两个不同算法的置信区间当成其指标差的配对区间。
- 用开发数据挑优再称测试前冻结；或删掉空交集轨迹再算更好的平均面积。

---

## 6. 执行顺序与门禁

| 阶段 | 任务 | 进入下一阶段的条件 |
|---|---|---|
| Ⅰ 版本与依赖 | R2-00—02、R2-20—21 | 源码和研究材料确认；数据代际、算法身份、证明归属已分清 |
| Ⅱ 数学和方法 | R2-05—19 | 主算法合同与新旧上界的见证均有精确落点；重要冲突已记录 |
| Ⅲ 主证据 | R2-22—26 | 新表格由冻结数据生成；修正ALL、失败、尾部和比较范围核查通过 |
| Ⅳ 叙事和来源 | R2-03—04、R2-27—29 | 摘要／贡献／讨论与实际完成内容一致 |
| Ⅴ 验收交付 | R2-30—31 | 编译、渲染、哈希、数学和数值检查有实际记录 |

若某新模块因证据缺失被阻塞，先完成不依赖它的模块。**不允许删除“未闭合”的说明来让摘要更完整。**作者决定是否暂缓该模块；Codex不自行用一个新研究问题代替用户既定任务。

## 7. 编制本任务书时的核查范围

本轮已读取当前两份20页PDF及其主要图表，读取F17理论／代码／冻结配置／审计，检查三轮研究包的文件组织，并从F17的27,648条原始主记录和1,152条修正对照记录重算了均值与若干校验项。没有新增算法、重跑比较实验、独立复核全部数学证明，也没有重评创新性。

以下附录是供Codex执行的精确迁移合同和验收基线；数值诊断不能代替普遍证明。正文及补充材料的最终文献引用仍使用正式可核实来源，不使用本任务书作为算法或定理的学术出处。

---

## 附录A｜必须保留的一般数学内容

### A.1 模型与主风险

以下对象仅允许改符号或排版，不能改语义：

\[
A_t=\{i:\tau_i\le t\},\quad 1\le K_t=|A_t|<\infty,
\quad r^*(t)=\max_{i\in A_t}r_i,\quad\Delta_i(t)=r^*(t)-r_i.
\]

独立臂流、每流iid $[0,1]$，外生永久到达；首先固定确定日程。新臂先到达，策略只选一条，观察后报告。允许并列和$K_T>T$。

\[
R_T=\sum_{t\le T}\Delta_{I_t}(t),\qquad
G_t^\varepsilon=\{i:\Delta_i(t)\le\varepsilon\},
\]
\[
E_{\mathrm{lab}}=\{\forall t:P_t\subseteq G_t^\varepsilon\subseteq A_t\setminus N_t\},
\]
\[
\mathcal U_T(\eta)=\sum_{t\le T}\sum_{i\in A_t}
\mathbf1\{i\in V_t,|\Delta_i(t)-\varepsilon|>\eta\}.
\]

保持$\mathbb E R_T\le r$与$\Pr(E_{\mathrm{lab}},\mathcal U_T\le a)\ge1-\delta$。
高概率面积不是期望面积；风险定义首先逐个确定终点。某个上界在共同覆盖事件上可同时对所有终点成立，应在该定理单独说明，不能据此把所有lower风险量词一并改变。

### A.2 旧结论锁定表

| 命题 | 不可丢失的内容 | 见证／范围 |
|---|---|---|
| M3 Theorem 4.1 | $\mathbb E_0\mathcal U_T\ge(3/4-\delta)\mathcal B_T$；$\Pr_0(\mathcal U_T\ge\mathcal B_T/4)\ge1/4$ | $\varepsilon\le1/16,\delta\le1/16,0<\eta<\varepsilon/2$；一个共同参考环境 |
| 分析队列 | $q_-=\lfloor\operatorname{kl}(1/4,\delta)/\operatorname{kl}(1/4,1/4+2\varepsilon)\rfloor$；$Q_t=(Q_{t-1}+q_-a_t-1)_+$ | 不是每条臂路径上的必需配额，$a_t$是新候选数 |
| M3 Theorem 4.2 | $2^{-24}\min\{KT,K^2\eta^{-2}\log(K/\delta)\}\le\mathfrak A_{T,K}\le256\min\{KT,K^2\eta^{-2}\log(K/\delta)\}$ | $K\ge2,T\ge1,\varepsilon\le1/8,\eta\le\varepsilon/32,\delta\le1/16$；原upper由Checkpoint实现 |
| Checkpoint的伴随regret | $\min\{T,K+4\sqrt{3KT\log(2T)}+1+99K\eta^{-2}\log(K/\delta)\}$ | 不替换成F模式而保持常数不变 |
| M3 Corollary 4.3 | 必要$K_t=o(\sqrt t)$；充分$K_T^2\log(eK_T)=o(T)$；$K_t\asymp t^\alpha$的指数阈值$1/2$ | 固定无限日程与均匀环境；不要遗漏对数与突发例外 |
| 终点臂数类 | $k(T)^2\log k(T)=o(T)$的联合可行性判别 | 最坏日程允许随终点变化，不等于逐固定日程充分必要 |
| M3 Proposition 5.1 | 原异质窗口area界、无新增旧候选观测的排除、含$\gamma_i,D_i^T$的无条件regret界 | Checkpoint的$H_e\ge2S_e$和相邻精度／基准间隔条件 |
| M3 Theorem 5.2 | 快速$V/8$的$\varepsilon JM d^{-2}\log(M/\delta)$匹配，暂缓$9V/8$只有upper | 原$H=128(M+J+1)q_f$；固定其余参数且$\eta,T$随$d$变 |
| M3 Theorem 5.3 | 一固定符号环境中成本至少$2^{-20}\varepsilon JM d^{-2}\log(M/\delta)$的概率至少$11/80$ | 原重复更新族；不是F-R的经验尾部保证 |
| S3 S9/S11 | 兼容窗口lower、occupation松弛含$a+\delta W$ | 仅必要，不是可达复杂度，不可删$\delta W$ |
| S3 S10 | 最终停止到达＋有限臂＋无边界等值下另一个复核算法的a.s.一致性 | 不继承给F或固定Checkpoint |

**引用注意：**上述常数都按M3/S3保留。若新符号或新事件分配影响常数，不能在编辑中“顺手优化”；需保留旧见证或标记需要证明的接口。

---

## 附录B｜F-CCP的精确数学迁移合同

本附录概括应转写的公式与条件。完整证明来源是F17 `theory.md`，CCP规划和任意动作桥梁见C16；不要只依据本附录的摘要跳过证明。

### B.1 参数、数据和可观察状态

固定任务$0<\varepsilon,\eta<1$、$0<\delta<1/2$。令$\lambda_t\in[0,1]$是观测当前奖励前可决定的偏好。$p_0\in(0,1),k_0>0,\nu>0$；实验取$.02,4,.1$。

$\beta_R,\beta_C\in[0,\infty]$预先固定；$\infty$表示禁用对应guard。收益核$\mathsf B$只依赖合法状态和独立随机化。$\theta>0$是Beta动作评分温度，不是证据样本增益。

记真实计数$n_i=N_i(t-1)$、奖励和$\Sigma_i$。持久状态包括每臂到达时刻、$n_i,\Sigma_i,[\ell_i,u_i],q_i$，虚拟MC时钟、谱running maximum、相位$\phi$、账本$C_R,C_C$及失败标识。旧数据和账本不得因到达、报告改变或切换偏好重置。

### B.2 证据与报告

\[
\alpha_i=\frac{\delta}{2i(i+1)},\quad
\mathsf M_{i,n}(m)=
\frac{B(\Sigma_{i,n}+1/2,n-\Sigma_{i,n}+1/2)}
{B(1/2,1/2)m^{\Sigma_{i,n}}(1-m)^{n-\Sigma_{i,n}}}.
\]

报告区间为所有已观察前缀集合$\{m:\mathsf M_{i,n}(m)\le1/\alpha_i\}$之交，再按时机交入一个固定检查点：

\[
\rho=\eta/4,\quad
q_i=\left\lceil\frac{2}{\rho^2}\log\frac{4i(i+1)}\delta\right\rceil,
\qquad[\hat r_i(q_i)-\rho/2,\hat r_i(q_i)+\rho/2]\cap[0,1].
\]

后一证据仅在真实第$q_i$个样本出现时加入；随后混合区间仍然更新，不被冻结。两个来源各分配总$\delta/2$，共同覆盖至少$1-\delta$，不需要独立。

\[
g_i^-=\max\{0,\max_{j\ne i}\ell_j-u_i\},\qquad
g_i^+=\max\{0,\max_{j\ne i}u_j-\ell_i\}.
\]

单臂两者为0；否则上式确为置信矩形中的gap极值。

\[
P_t=\{i:g_i^+\le\varepsilon\},\quad
N_t=\{i:g_i^->\varepsilon\},\quad V_t=A_t\setminus(P_t\cup N_t),
\]
\[
Z_t=\{i\in V_t:[g_i^-,g_i^+]\subseteq[\varepsilon-\eta,\varepsilon+\eta]\},
\qquad W_t=V_t\setminus Z_t.
\]

$Z_t$只暂停主动服务，仍然报告为未决。新到达后重新计算，不能锁定成永久免计任务。真实未决面积仅评价者能计算，不是算法状态。

空交集时持久失败：以后全部未决，不再主动服务，收益选择仍按合同运行。不要用旧exclusion-first规则代替。

### B.3 虚拟MC指数与前缀谱

$K_t>1$且初始竞争或$K_t-1\ge2\,\mathrm{base}$时，令

\[
\mathrm{base}\leftarrow K_t-1,\quad \sigma\leftarrow t,\quad d_{\mathrm{clock}}\leftarrow2\,\mathrm{base}.
\]

计数和奖励和不清零。令$s=t-\sigma+1$，

\[
J_i(t)=
\begin{cases}
1,&n_i=0,\\
\min\{1,\hat r_i(n_i)+\sqrt{[\log\{s/(d_{\mathrm{clock}}n_i)\}]_+/n_i}\},&n_i>0,
\end{cases}
\quad
\zeta_t(i)=\max_jJ_j(t)-J_i(t).
\]

只有一个臂时令$\zeta=0$，不计算未初始化时钟的比值。

排除第一条初始计数锚点，按**当前**年龄$t-\tau_i+1$分组：第0组年龄1，第$\ell\ge1$组$(2^{\ell-1},2^\ell]$；数量$k_{\ell,t}$。定义

\[
\mathcal S_t=\sum_{\ell\ge0}\min\{2^\ell,\sqrt{k_{\ell,t}2^\ell}\},\qquad
\overline{\mathcal S}_t=\max_{u\le t}\mathcal S_u.
\]

这是当前前缀日程复杂度，不是未来终点的剩余寿命预测。G中已有删除／推迟比较给出$\overline{\mathcal S}_T\le2\mathcal S_T$；迁移时核对其假设。

### B.4 CCP局部证书计划

为避免与真实均值$r_i$冲突，规划半径记为$v_i^{\mathrm{plan}}$：

\[
m_i=\Pi_{[\ell_i,u_i]}\frac{\Sigma_i+1/2}{n_i+1},\quad
v_i^{\mathrm{plan}}=\max(m_i-\ell_i,u_i-m_i),\quad \bar n_i=\max(1,n_i).
\]

对每个$i\in W_t$，若经验最好与$i$差超过$\varepsilon$，比较对象$j$取经验最好；否则$j$取本臂以外上界最高者。平局遵循冻结代码的到达序。

\[
z_i=|m_j-m_i-\varepsilon|,\quad h_i=.95\max\{z_i,\eta-z_i\},
\quad c_k=\nu+(1-\lambda_t)\zeta_t(k).
\]

以$a_k=v_k^{\mathrm{plan}}\sqrt{\bar n_k}$解

\[
\min_{x_i\ge\bar n_i,x_j\ge\bar n_j}
 c_i(x_i-\bar n_i)+c_j(x_j-\bar n_j)
\quad\text{s.t.}\quad a_i/\sqrt{x_i}+a_j/\sqrt{x_j}\le h_i.
\]

内点闭式令

\[
D=\frac{a_i^{2/3}c_i^{1/3}+a_j^{2/3}c_j^{1/3}}{h_i},\quad
x_i=D^2(a_i/c_i)^{2/3},\quad x_j=D^2(a_j/c_j)^{2/3}.
\]

已有精度足够则零新增；内点越过已有计数下界时固定该坐标、解另一坐标。选择代理成本最小的当前pair；在确有计划增量且$n_k<q_k$的端点中按$v_k^{\mathrm{plan}}/(\bar n_kc_k)$选择，只执行一拉。没有合法pair时用最宽未完成检查点臂兜底。

不能声称上述确定性代理就是原随机问题的精确解；其他竞争者、未知中心及置信序列缩减规律并未被该凸问题完整描述。数值$10^{-12}$等正则化只属规划实现，不能改变报告条件。

### B.5 优先级与相位

令$b_t=|W_t|$、$j_t$为规划拟服务臂、$\widehat c_t=\max_i m_i-m_{j_t}$。
自适应模式：

\[
w_t=p_0+(1-p_0)\frac{b_t}{b_t+k_0}\frac{\varepsilon}{\varepsilon+\widehat c_t},
\qquad
p_t=
\begin{cases}
0,&b_t=0,\\
\dfrac{\lambda_t w_t}{1-\lambda_t+\lambda_t w_t},&b_t>0.
\end{cases}
\]

固定率模式取$p_t=\lambda_t\mathbf1\{b_t>0\}$。失效状态或$\lambda=0$时服务率0。

$\phi_0=0$；每轮加$p_t$，若$\phi\ge1$则尝试服务并减1。恰好记录一次attempt，即使随后预算拒绝，也不退回相位或在同轮再尝试。
精确算术下attempts$=\lfloor\sum_{t\le T}p_t\rfloor$。

固定$\lambda>0$时

\[
p_{\min}(\lambda)=\frac{\lambda p_0}{1-\lambda+\lambda p_0}>0.
\]

任意趋零的$\lambda_t$不能套统一$p_{\min}$。一般可靠性允许可预测切换，但完成速度另需条件。

### B.6 双预算与评分规则

\[
C_R(t)=\sum_{s\le t:\,\mathrm{reward}}\zeta_s(I_s),\qquad
C_C(t)=\sum_{s\le t:\,\mathrm{service}}\zeta_s(I_s).
\]

服务提议只有在

\[
C_C(t-1)+\zeta_t(j_t)\le\beta_C\overline{\mathcal S}_t
\]

时接受。否则在

\[
\mathcal F_R(t)=\{i:C_R(t-1)+\zeta_t(i)\le\beta_R\overline{\mathcal S}_t\}
\]

内最大化收益核分数。禁用guard时不计算$\infty\times0$；直接不作该检查。最大虚拟指数臂必可行。

默认Beta行动分数：

\[
\Xi_i(t)\sim\operatorname{Beta}\left(1+\Sigma_i/\theta,\,1+(n_i-\Sigma_i)/\theta\right).
\]

全部臂各抽一次，投影后在可行集中取最大该分数；不能重抽直到动作通过保护。$\theta=1$且Bernoulli奖励时是标准Beta(1,1) TS；$\theta=.5$是冷温度行动规则。$\theta$不进入置信证据。

### B.7 四种配置与精确保证矩阵

| 显示名称／数据ID | $\lambda$与控制 | $\theta$ | $\beta_R$ | $\beta_C$ | 保证／界限 |
|---|---|---:|---:|---:|---|
| Reward / `F-R` | 0，服务关闭 | .5 | 16 | 不起作用 | $\mathbb ER_T\le\min(T,332\mathcal S_T)$；无主动完成速度 |
| Balanced / `F-auto-0.6` | .6，自适应 | .5 | 16 | 1 | 可靠、$334\mathcal S_T$regret上界；面积保留拒绝项 |
| Classification / `F-area` | 1，全部busy轮尝试 | .5 | 16 | $\infty$ | 最坏面积同阶；regret额外$Q_T^{cap}$ |
| Compatibility / `F-R-TS-exact`或指定其他核 | 0，服务关闭 | 对TS为1 | $\infty$ | 不起作用 | 从起点起同核同状态同随机化的逐路径等价；无通用面积保证 |

F-R和Compatibility在F17冻结JSON中`beta_s=null`，交互预设中`service_budget=0`。因为两者$\lambda=0$而从不尝试服务，二者行为等价。**不能为了表格统一改写冻结JSON、哈希或历史结果。**正文表格写“inactive”即可避免误导。

### B.8 应迁入正文／附录的定理清单

**F-1 可靠性。** 所有模式以及合法可预测偏好切换满足$\Pr(E_{\mathrm{lab}})\ge1-\delta$。

**F-2 兼容性。** 从起点起$\lambda_t\equiv0$、$\beta_R=\infty$，同收益核、完整状态和同后端随机数，则全部动作、真实计数和$R_T$逐路径相同。中途切换不能追溯得到相同历史。

**F-3 收益保护。** 对合法未知均值策略，明确复用任意动作输入

\[
\mathbb ER_T\le\min\{T,300\mathcal S_T+\mathbb E\sum_{t\le T}\zeta_t(I_t)\}.
\]

两预算均固定有限时：

\[
\mathbb ER_T\le\min\{T,(300+2\beta_R+2\beta_C)\mathcal S_T\}.
\]

服务关闭可去掉$\beta_C$项；$\beta_C=\infty$、$\beta_R<\infty$时：

\[
\mathbb ER_T\le\min\{T,(300+2\beta_R)\mathcal S_T+Q_T^{\mathrm{cap}}\},\quad
Q_T^{\mathrm{cap}}=\sum_{i\in A_T}q_i.
\]

这些是无条件期望界，不是某个独立基线的轨迹差，也不是精确常数最优。

**F-4 服务率与面积。** 若每busy轮$p_t\ge p_{\min}>0$，共同覆盖事件上对全部确定终点同时有

\[
\mathcal U_T(\eta)\le K_T\min\left\{T,\frac{Q_T^{\mathrm{cap}}+D_T^{\mathrm{srv}}+1}{p_{\min}}\right\}.
\]

没有认证拒绝时$D_T^{\mathrm{srv}}=0$，得到$K_T^2\eta^{-2}\log(K_T/\delta)/p_{\min}$阶。不能把默认有限预算的$D_T^{\mathrm{srv}}$删掉。

**F-5 不饥饿。** $\beta_C>0$、$p_{\min}>0$及最终有限臂数／最终停止到达时，覆盖事件上边界带外未决最终消失。保守界为

\[
\mathcal U_T\le K_T\min\left\{T,
\left\lceil(Q_T^{\mathrm{cap}}/\beta_C)^2\right\rceil+1+
\frac{Q_T^{\mathrm{cap}}+1}{p_{\min}}\right\}.
\]

只因它有限，不能声称面积最优；也不是全体边界内臂的a.s.精确分类。

**F-6 零余项支配反例。** 保留在新S4：两初始臂、$T=1$、固定初始化MC-MOSS与对称TS，在$(3/4,1/4)$及反向环境中，任意首轮选臂1概率$p$的最大超额至少

\[
\min_{p\in[0,1]}\max\{(1-p)/2,p/2-1/4\}=1/8.
\]

只针对明确的“所有环境、所有终点、同时不差于所有这些基线、零余项”要求；不否定渐近、局部或有代价模型选择。

---

## 附录C｜主算法伪代码与代码合同

以下为迁移到LaTeX算法环境的结构，不是让Codex重新发明一个相似算法。所有未展开子程序都必须指向本任务书附录B及源代码对应函数。

```text
Algorithm: Flexible Certificate-Cost Planning (F-CCP)
Input: fixed ε, η, δ; reward kernel B; temperature θ;
       preference λ (or predictable λ_t); controller type;
       price ν, floor p0, backlog scale k0; fixed β_R, β_C.

State: revealed arm set and arrival ranks;
       actual n_i, reward sum Σ_i, intervals [l_i,u_i], checkpoints q_i;
       MC base and clock start; running spectrum Smax;
       phase φ=0; reward ledger C_R=0; service ledger C_C=0;
       persistent report-failure flag=false.

For physical t = 1,2,...:
  Receive all arrivals; initialize only those arms:
       n_i=0, Σ_i=0, [l_i,u_i]=[0,1], q_i from η/4 checkpoint.
  Update virtual MC clock if competing-arm count crosses its threshold.
  Compute clipped virtual J_i, ζ_i=max J-J_i, and current prefix spectrum.
  Smax ← max(Smax, current spectrum). Do not reset any history.

  service candidate j ← none; attempt ← false.
  If no report failure and λ_t>0:
       Compute current labels, Z_t and W_t after receiving arrivals.
       If W_t is nonempty:
           (j, estimated_sampling_cost) ← CertificatePlan(...).
           p_t ← fixed or adaptive controller.
           φ ← φ + p_t.
           If φ≥1: φ←φ-1; attempt←true.
  Otherwise p_t=0.

  service ← attempt and a valid j was proposed.
  If service and its C guard is enabled and C_C+ζ_j>β_C*Smax:
       record a service denial; service←false.

  If service:
       I_t←j; C_C←C_C+ζ_j.
  Else:
       Draw/compute one complete vector of reward scores on available arms.
       If R guard enabled: F_R←{i:C_R+ζ_i≤β_R*Smax}; else F_R←all.
       I_t←smallest-rank maximizer of that score over F_R.
       C_R←C_R+ζ_(I_t).

  Pull only I_t once; observe one real reward x in [0,1].
  n_(I_t)←n_(I_t)+1; Σ_(I_t)←Σ_(I_t)+x.
  If no persistent report failure:
       Intersect the chosen arm's old interval with its new mixture-CS interval.
       If n_(I_t)=q_(I_t): also intersect its predetermined checkpoint interval.
       If the intersection is empty: set persistent report failure.

  If failure: report (empty,empty,all arrived arms).
  Else: report P_t,N_t,V_t from exact rectangular gap bounds.
  Keep all arms eligible for future reward choices.
```

### C.1 必须补齐的子程序

| 子程序 | 实际冻结实现／数学位置 |
|---|---|
| evidence update | `ccp_primitives.py::beta_mix_interval`，`flexible_engine.py::update_interval`；附录B.2 |
| rectangular reports and work set | `ccp_primitives.py::gap_bounds`、`labels_work` |
| certificate proposal | `flexible_engine.py::service_plan`的scheduler=50；修正统一接口`matched_all.py::service_plan_matched` |
| pair allocation | `ccp_primitives.py::pair_plan`；附录B.4 |
| adaptive rate | `flexible_engine.py::control_rate`；附录B.5 |
| actual two-ledger loop | `flexible_v2.py::choose_dual`；不能用旧`choose_flexible` |
| reference interactive implementation | `flexible_ccp.py::FlexibleCCP.choose/observe/report` |
| corrected ALL comparator | `matched_all.py`、`flexible_matched.py`、`study_matched.py` |

### C.2 行为层与证据层不能混用

- 最大MC指数为保护参照，不是近优报告的置信上界。
- 温度Beta分数用于动作选择，不是有效报告区间。
- `priority`改变服务意愿和局部价格，不改变$\varepsilon,\eta,\delta$。
- `set_priority()`只能在完成上一轮观测后调用；此前账本不清零。
- `service_budget=None`是无限额；`0`只允许零指数差服务，不等于无穷。
- 相位规则不是Bernoulli抽签；改变为随机掷币会改变算法与确定性工作量证明。
- 禁止为减少存储把已负认证臂真正删掉，除非重新研究相应无条件regret。

### C.3 数值实现与理论的区别必须保留

F17使用$10^{-12}$预算容差、规划正则化与向外求根。相位在浮点整数边界可能晚一个服务槽；历史主测试1035条存在此现象，记录的全局$\sum p_t-\mathrm{attempts}$范围为$[0,1+3\times10^{-9}]$附近。

数学statement对应精确算法，不得将上述数值诊断称作所有机器时间和输入下的正式保证。本轮不改变冻结容差、不更换随机数后端、不“修正”既有轨迹；需要变更时新建版本并单列用户审批。

交互接口使用自有NumPy Generator；批实验使用Numba RNG。兼容性在相同后端、相同调用顺序和随机流下逐路径成立，不承诺跨后端仅凭相同seed位级一致。

F实现直接使用双循环找比较对象、规划和报告，不能继承旧Checkpoint的$O(K_t)$每轮复杂度描述。应按实际源代码给$O(K_t^2)$级的直接规划／报告开销说明，并说明谱分箱循环与数值求根开销；有界机器整数和固定64分箱是当前实现限制，不是数学模型对任意$T$的限制。不要为了给更漂亮复杂度而在本轮悄悄改代码。

---

## 附录D｜P16新增结果的迁入合同：保留成果，不转移算法归属

本附录对应R2-17、R2-18和新补充S12—S13。P16的`theory_frontier.md`与`abm.py`是输入；本轮不是再次推导这些结论。迁移发现证明问题时，记录实际缺口并阻塞相应结果，不擅自删掉假设后继续使用。

### D.1 两种前沿必须区分

对指定日程分别设计策略的$\mathfrak R_{T,\tau}^{\rm sch}(a)$，与要求同一个未知未来策略在日程类$\mathcal T$上可行的$\mathfrak R_{T,\mathcal T}^{\rm causal}(a)$，信息条件不同。二者均不知道实际奖励环境；前者允许在日程／终点已知条件下设计策略。

P16定理1以初始参照$1/2$、候选$1/2-\varepsilon\pm d$及后来的参照$1/2+v$，构造共同前缀一致的早改善、晚改善日程。在源文件规定的$h,T,a$及$\eta=d/2$下，满足晚改善及时性要求的同一因果策略，在早改善日程上也可能必须承担$\Omega(d^{-2})$，而早改善日程专门配置的比较者有$O(\log(1/d))$可达成本。

**必须完整迁移：**相同终点、相同预算、相同最终臂数；两侧各自可行性；完整模型的标签可靠性；具体$h,T,a$的选择；因果共同前缀；先验到固定环境的转换。

**正文只需一句结论和一个信息模型解释。**不得写成“不存在因果minimax最优算法”“所有动态前沿都不可能达到”或“F-CCP已经达到最优因果前沿”。不把收益已知oracle与日程已知比较者混同。

### D.2 任意恢复数量的引理

源文件定理2：$m$个独立均匀符号、每坐标两向单次KL不超过$0<\kappa<\infty$；允许自适应交错采样、有界停止及数据依赖报告子集$S$，任一错误报告的总概率在每个配置下至多$0<\delta\le1/16$。若整数$1\le s\le m$满足

\[
\overline{\Pr}(|S|\ge s)\ge\tfrac12,
\]

则

\[
\overline{\mathbb E}\sum_iN_i\ge
\frac{s}{48\kappa}\log\frac{s}{\delta}.
\]

这里的横线是一个共同符号乘积先验，不是算法的主观先验；不能假设随机计数独立。证明使用$f(e)=(1-2e)\log((1-e)/e)$及其非负凸性。

默认保留旧S4的半数恢复引理作为旧定理依赖，再把本引理作为中间预算扩展的工具。不要未经核验，按新常数自动替换所有旧证明的常数和概率。

### D.3 中间预算下界与ABM合同

使用同类重复更新结构，但**窗口长度$H$按P16另行规定**：

\[
J\ge1,\quad M\ge\max\{2,J\},\quad
0<\varepsilon\le\tfrac18,\quad0<\delta\le\tfrac1{16},
\quad Jv\le\varepsilon/4,\quad0<d\le v/32,\quad\eta=d/2.
\]

令$m=JM$、$K=J(M+1)+1$、$T=(J+1)H$、$V=mH$。对$0\le a<V$，

\[
k(a)=\left\lceil\frac{V-a}{H}\right\rceil,
\qquad
\mathfrak R_\Theta(a)\ge
\frac{\varepsilon k(a)}{3072d^2}\log\frac{k(a)}{\delta}.
\]

这个下界包括候选在自身有效窗口之后获得的样本：那些样本仍可能编码符号，也仍有至少$\varepsilon/2$的regret价格。不得以“任务已经过期”为由把这些信息从KL中删掉。

ABM保留为**独立解析构造**：

- 所有臂按到达排名预设粗检查点；粗层$\rho_c=v/8$。
- 每批粗证据完成后选批内经验最好者；至多激活$s$个细候选及相应批次细参照，细任务不超过$2s$。
- 精细层$\rho_f=d/4$，按**实际激活排名**分配置信预算。
- 细任务使用激活后的新观测块，不能对由粗数据选择的旧前缀重新分配较有利错误率。旧数据仍保留在收益与粗证据中。
- 偶数服务轮先粗FIFO再细任务，其他轮全历史UCB；不是F-CCP的随机收益核或双预算调度。

定义源文件分析量：

\[
Q_c=\left\lceil128v^{-2}\log\frac{4K(K+1)}\delta\right\rceil,
\quad
Q_f(r)=\left\lceil32d^{-2}\log\frac{4r(r+1)}\delta\right\rceil,
\]
\[
L_c=2(M+1)Q_c,\quad L=L_c+2(M+1)Q_f(2m),
\quad
B_{\rm rec}=L_c\left\{\frac{(J+1)(J+2)}2+JM\right\}.
\]

本任务书用$B_{\rm rec}$重命名源文件常数$B$，避免与当前最优均值混淆；迁移时应同步做符号映射。

要求

\[
H\ge4(L+B_{\rm rec}).
\]

对$0\le s\le m$，ABM满足

\[
\Pr\{E_{\rm lab},\ \mathcal U_T\le(m-s)H+sL+B_{\rm rec}\}\ge1-\delta,
\]
\[
\sup_\Theta\mathbb ER_T\le R_0(T)+4\varepsilon sQ_f(2s)\quad(s\ge1),
\]
\[
R_0(T)=2\varepsilon KQ_c+
128\left(\frac m\varepsilon+\frac{J^2}{v}\right)\log(2T)+1.
\]

$s=0$时没有细层项。令$A_{\min}=mL+B_{\rm rec}$，对

\[
A_{\min}\le a<V,\qquad
s(a)=\left\lceil\frac{V+B_{\rm rec}-a}{H-L}\right\rceil,
\]

得到

\[
\frac{\varepsilon k(a)}{3072d^2}\log\frac{k(a)}\delta
\le\mathfrak R_\Theta(a)
\le R_0(T)+1024\frac{\varepsilon k(a)}{d^2}\log\frac{k(a)}\delta.
\]

采用$H=16(L+B_{\rm rec})$时，$A_{\min}/V\le3/32<1/8$；固定其余合法参数，$d\downarrow0$时$R_0(T)=O(\log(1/d))$。**必须保留加性$R_0(T)$，不能在非渐近statement中删去。**

### D.4 不可越过的四个边界

1. **不是M3旧终点的原样加强。** M3式(19)用$H=128(M+J+1)q_f$；这里用更强窗口条件。必须分别命名性能族／窗口合同，不把两套$H$混成一套。
2. **不是F-CCP定理。** 本结果由ABM实现；不得把ABM中的$s$改成F-CCP的$\lambda$，也不得宣称F-CCP继承这段匹配。
3. **不是自动面积控制器。** 给定$s$后ABM无需未来日程；由$a$计算$s(a)$却使用$m,H$等性能族参数。两种信息声明都须保留。
4. **不是完整通用前沿。** $a<A_{\min}$、所有暂缓端预算、任意重叠到达及未知日程共同前沿没有由该定理解决。

### D.5 不进入正文的新算法／工具

Shared、Bundle、有限候选环境LP继续在研究发行包中保留。Shared相对CCP的有限测试并未建立稳健优势，不用它替换F-CCP主方法。小模型LP假设有限候选环境、已知日程与终点、固定报告器，只优化该受限策略问题；其曲线不能成为本文主方法“接近完整前沿”的证据。

若正文篇幅受限，默认压缩的是本附录所列结果的正文解释长度，而不是删掉信息条件，也不是把ABM并入主算法。

---

## 附录E｜冻结数值证据、字段与验收快照

以下数字在编制任务书时已从F17的实际CSV重新计算，用于检测错误迁移；不是新的实验结果。Codex仍须从自己的本地输入重新核验，并记录实际完成的检查。不能只将本表复制进去就宣称已经复现。

### E.1 四套实验不能混合

| 数据代际 | 原协议 | 第二轮用途 |
|---|---|---|
| M3/S3旧CP实验 | 4场景×9配置×160重复＝5760条，$T=20000$、$\varepsilon=.30,\eta=.10,\delta=.05$ | 新S17保留完整旧结果及失败，非新主表 |
| C16第一次CCP测试 | 10场景×21配置×64重复＝13440条 | 研发谱系与原始研究档案；不合并新胜率 |
| P16前沿／Shared测试 | 12场景×22配置×48重复＝12672条 | 研发谱系与负面候选档案；不合并新胜率 |
| F17冻结主测试 | 12场景×24配置×96重复＝27648条 | 新正文主证据 |
| F17修正ALL对照 | 12场景×1配置×96重复＝1152条 | 替换错误旧ALL的主比较；两版本数据都归档 |

F17原始主文件与修正文件合计28800条、25个method ID。以修正ALL替换旧ALL形成同任务主分析口径后，仍是24个配置、27648条；**不要把修正对照当成原来冻结时已经存在的第25种方法。**研发阶段14016条也不能算成独立主测试重复。

### E.2 本轮主输入与用途

| F17相对路径 | 实际角色／执行要求 |
|---|---|
| `protocols/holdout-freeze.json` | 原主测试场景、24配置、种子、批内shuffle和预先比较规则 |
| `protocols/matched-all-freeze.json` | 对照修正说明、同场景同种子和新增ID；不覆盖原freeze |
| `results/holdout-all.csv` | 原27648条逐次结果，含错误对照ID；只读 |
| `results/matched-all-all.csv` | 修正对照1152条；只读 |
| `results/holdout-summary.csv` | 300行：12场景×25配置；必须核对其中旧ALL不得用于主要优势比较 |
| `results/pure-regret-paired.csv` | 60组F-R对5基线的配对比较；保留符号、置信区间与多重比较范围 |
| `results/joint-paired.csv` | 均衡模式、分类模式及相应对照的配对结果 |
| `results/analysis-checks.json` | 历史再分析诊断；不是本轮Codex自动完成的检查 |
| `results/holdout-*-paths.npz` | 只保存每场景前4次重复、每200轮网格；不是96次均值轨迹 |
| `results/matched-all-*-paths.npz` | 修正对照的同类有限路径记录 |
| `audit.md`、`results/implementation-audit.json` | 失败、兼容、源码分支、数据更正、数值容差等核查范围 |
| `environment.json`、`requirements.txt`、`README.md` | 实际F17环境与运行方式；不要使用S3旧Windows资源数字 |

**字段定义：**`regret`为累计pseudo-regret；`area`为本场景固定$\eta$下累计未决臂时间；`final_unresolved`与`final_all_unresolved`不同；`service_pulls`是实际认证次数，`service_attempts`含拒绝，`service_denials`是拒绝次数；`tax`为指数差总账，分为`reward_tax`和`service_tax`；`service_regret`才是评价者用真均值计算的服务损失。`label_error`、`coverage_error`、`empty_intersection`应按各自指标计数，不混为“错误标签”。

### E.3 同任务修正不可省略

原`ALL-auto-0.6`的服务规划返回了零经验价格，使自适应服务控制器与F-CCP不匹配。正式主对照必须使用`ALL-auto-costmatched`，其价格是相同区间投影中心计算的$\max_i m_i-m_j$。

修正只更改ALL的该接口，没有调节F-CCP或收益基线参数；补跑发生在发现问题之后。这一点写进新S16的审计记录。原错误对照保留在单独标记的档案，不作为方法优势的主证据，也不与修正结果平均。

### E.4 主测试场景快照

以下场景全部$\delta=.05$。完整arrival数组和mean数组直接来自freeze，不得根据场景名称重新猜测或手工生成。

| 场景ID | $K_T$ | $T$ | $\varepsilon$ | $\eta$ | 奖励类型 |
|---|---:|---:|---:|---:|---|
| `two_close` | 2 | 12000 | 0.027 | 0.006 | `bernoulli` |
| `few_arrivals` | 3 | 12000 | 0.18 | 0.045 | `bernoulli` |
| `stable` | 8 | 12000 | 0.2 | 0.05 | `bernoulli` |
| `successive_improvements` | 11 | 14000 | 0.2 | 0.05 | `bernoulli` |
| `burst` | 14 | 14000 | 0.2 | 0.05 | `bernoulli` |
| `membership_boundary` | 9 | 14000 | 0.2 | 0.035 | `bernoulli` |
| `many_close_means` | 13 | 12000 | 0.115 | 0.03 | `bernoulli` |
| `late_improvement` | 8 | 14000 | 0.2 | 0.05 | `bernoulli` |
| `rare_rewards` | 9 | 12000 | 0.018 | 0.005 | `bernoulli` |
| `ceiling` | 9 | 12000 | 0.08 | 0.02 | `bernoulli` |
| `larger_pool` | 20 | 16000 | 0.2 | 0.05 | `bernoulli` |
| `bounded_low_variance` | 10 | 12000 | 0.2 | 0.05 | `two_point` |

### E.5 应能再生成的纯收益主表

每格为96次重复均值，保留两位小数。完整主表需同时给标准误或另提供不确定性表，不能只保留加粗优胜值。两臂接近场景中F-R不是最小均值；该行不可删除。

| 场景ID | UCB1 | Growing-MOSS | MC-MOSS | Thompson | KL-UCB | F-R |
|---|---:|---:|---:|---:|---:|---:|
| `two_close` | 75.52 | 52.16 | 52.16 | 51.37 | 62.63 | 52.07 |
| `few_arrivals` | 32.60 | 10.71 | 11.02 | 7.47 | 12.52 | 5.63 |
| `stable` | 393.14 | 98.11 | 92.20 | 66.47 | 181.01 | 41.90 |
| `successive_improvements` | 313.99 | 105.44 | 86.29 | 57.61 | 123.14 | 53.59 |
| `burst` | 532.82 | 140.79 | 131.95 | 80.01 | 177.09 | 68.56 |
| `membership_boundary` | 482.45 | 115.74 | 113.09 | 83.32 | 225.66 | 53.57 |
| `many_close_means` | 341.20 | 188.60 | 190.01 | 202.27 | 267.46 | 169.80 |
| `late_improvement` | 364.87 | 126.45 | 101.93 | 83.89 | 196.49 | 70.56 |
| `rare_rewards` | 146.50 | 102.35 | 81.43 | 60.16 | 78.06 | 50.29 |
| `ceiling` | 366.96 | 126.06 | 102.01 | 28.42 | 59.24 | 26.46 |
| `larger_pool` | 702.32 | 189.70 | 179.02 | 121.25 | 254.50 | 98.74 |
| `bounded_low_variance` | 365.81 | 111.25 | 88.96 | 62.89 | 171.08 | 37.61 |

若给出场景平均，必须标为“对预设场景均值的等权描述性平均”；不同场景有不同$T,K,\varepsilon,\eta$，不能称为共同概率模型下的风险、minimax值或精确前沿。相对TS的19.5%是两者场景等权均值之比，不是逐场景百分比的平均。

### E.6 服务偏好与对照的均值快照

面积以下按原始“臂×时间”单位给出；进入论文若除以$10^3$，标题和每行必须统一换算。

| 冻结method ID | 平均regret | 平均累计未决面积 |
|---|---:|---:|
| `F-R` | 60.731091 | 62218.970486 |
| `F-auto-0.1` | 114.682545 | 48286.086806 |
| `F-auto-0.3` | 213.548584 | 38458.271701 |
| `F-auto-0.6` | 392.989635 | 31698.348958 |
| `F-auto-0.9` | 425.034849 | 30844.000868 |
| `F-all-service-budgeted` | 421.520260 | 31001.503472 |
| `F-area` | 1210.021035 | 27121.206597 |
| `CCP-original` | 440.321594 | 30069.196181 |
| `ALL-auto-costmatched` | 435.679272 | 36718.073785 |
| `ALL-area` | 1581.724534 | 36807.490451 |

不要把$\lambda=.9$、$\lambda=1$有限预算两点的非单调性“修成”单调曲线。不得把未使用预算的分类优先点与有限预算曲线平滑插值成已知可达的连续前沿。预算、收益核、温度均要在图例或配置表说明。

### E.7 必须保留的统计边界与尾部结果

- 12场景×5基线＝60个比较，F-R有59个严格较低的均值；11个场景的均值低于全部5基线。
- Bonferroni族60、单侧近似$t$区间的严格上端点小于0者为52个，不是60个。
- 事先设置的宽松容忍度“基线均值的5%＋2单位”下通过54个；该门槛不等于零差距非劣性。
- 两臂接近场景F-R减TS均值约$+0.70$，逐比较双侧95%区间约$[-5.28,6.68]$；不支持“所有场景都严格更好”。
- 经验95%regret分位数如下；禁止只展示均值而宣称尾部也改善。

| 场景 | F-R经验95%分位数 | Thompson经验95%分位数 |
|---|---:|---:|
| `burst` | 208.88750 | 123.06875 |
| `ceiling` | 90.94000 | 48.97050 |
| `larger_pool` | 237.30125 | 184.17500 |

分位数是96次结果的经验分位数，不是已估计到任意精度的真实尾分位数。逐比较误差条不自动控制全体方法／场景的共同错误概率。不能把较低均值写成逐路径支配。

### E.8 失败记录：不能沿用旧稿“所有运行零错误”

下表每种方法分母均为1152＝12×96，计数从已保留全部轨迹得到。共享随机流使不同方法的相同失败相关，不能当作独立样本叠加概率。

| 方法 | 至少一次错误标签的运行数 | 覆盖失败运行数 | 空交集运行数 |
|---|---:|---:|---:|
| `F-R` | 0 | 6 | 1 |
| `F-auto-0.6` | 1 | 7 | 1 |
| `F-area` | 0 | 8 | 0 |
| `Thompson` | 0 | 5 | 1 |
| `CCP-original` | 1 | 7 | 1 |
| `ALL-auto-costmatched` | 1 | 7 | 1 |
| `ALL-area` | 0 | 8 | 0 |

不因失败而删去轨迹，不仅在覆盖事件内计算regret或面积，也不以零标签错误替代理论可靠性证明。F-auto-.6有一条错误标签轨迹，不妨碍其误差受控理论，但禁止抹掉后声称零失误。

### E.9 关键源码／数据哈希

如果用户另给更新版，保留新旧版本关系并重新核对，不要强行使更新文件匹配旧哈希。本轮冻结输入的哈希差异必须上报。

| F17相对路径 | SHA-256 |
|---|---|
| `theory.md` | `16d75dce4bab7e77403660fd8c54c94d4b6a2b353dc9b7d1f72fa5633ec4b630` |
| `src/flexible_ccp.py` | `7286f226f49a8fc3e0ca0d53c8f42dacc92f360e04d74dad337c771a5478ab7a` |
| `src/flexible_v2.py` | `4b3f895b0e6352fd660283bc75b1e2e5bb90eb5268ef627c23386862b416dac7` |
| `src/matched_all.py` | `46a7b8b308a89467f8c5dac3d464e1a9ec5eacbf6ca56e60dd06091af815251c` |
| `protocols/holdout-freeze.json` | `7d4b8536869250ce3b19ad5f15ddf388c16ed17ca058a94171b694ad29229668` |
| `protocols/matched-all-freeze.json` | `69bac0a73fb6f3af7525e61036673ff26dbccc25ef7345148c83ada1892c9689` |
| `results/holdout-all.csv` | `f7e77d4df069477ca5b4708a73e6f2898d8df4251514510eb93c017f78a63d90` |
| `results/matched-all-all.csv` | `35d20a058abbe34ea8bf4248de97ba95f6cbd7b25ead7e798ab37e50b9f2e4dd` |
| `results/holdout-summary.csv` | `b996f557f56db86013d7d3770fb37a11dc1a4f650188c589e0da48d56c2bf97c` |

---

## 附录F｜只读数据验收脚本、整体验收和最终交付

### F.1 可直接运行的只读验收脚本

把下面代码保存到新修订工作区的`check_revision2_data.py`。它不调用任何bandit策略，不生成新奖励，不覆盖原始CSV；输出目录必须在F17冻结根目录之外。输入版本不一致或数据缺失时抛出错误，不能跳过断言后报告通过。

需要`numpy`、`pandas`和`scipy`。示例中的目录由Codex替换为已经确认的本地路径，不是固定机器路径。

```text
python check_revision2_data.py \
  --f-root "/actual/path/F-CCP_2026-10-17" \
  --out "/actual/path/revision2/analysis/fccp-checks.json"
```

本脚本核对端点数据及指定统计量；不能替代源码行为检查、逐动作兼容性核查、数学证明审计或完整图形复核。

```python
#!/usr/bin/env python3
"""Read-only verification of the frozen F-CCP results. No policy is run.
Usage: python check_revision2_data.py --f-root /path/F-CCP_2026-10-17 \
       --out /path/revision2/analysis/fccp-checks.json
Requires numpy, pandas, scipy. Input files are never overwritten.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t as student_t

HASHES = {
    'results/holdout-all.csv': 'f7e77d4df069477ca5b4708a73e6f2898d8df4251514510eb93c017f78a63d90',
    'results/matched-all-all.csv': '35d20a058abbe34ea8bf4248de97ba95f6cbd7b25ead7e798ab37e50b9f2e4dd',
    'results/holdout-summary.csv': 'b996f557f56db86013d7d3770fb37a11dc1a4f650188c589e0da48d56c2bf97c',
    'protocols/holdout-freeze.json': '7d4b8536869250ce3b19ad5f15ddf388c16ed17ca058a94171b694ad29229668',
    'protocols/matched-all-freeze.json': '69bac0a73fb6f3af7525e61036673ff26dbccc25ef7345148c83ada1892c9689',
}
BASES = ['UCB1', 'Growing-MOSS', 'MC-MOSS', 'Thompson', 'KL-UCB']

def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--f-root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root, out = args.f_root.resolve(), args.out.resolve()
    require(not out.is_relative_to(root), 'Output must be outside the frozen source tree.')
    require(not out.exists(), 'Output already exists; choose a new audit filename.')
    actual_hashes = {}
    for rel, expected in HASHES.items():
        path = root / rel
        require(path.is_file(), f'Missing input: {rel}')
        actual_hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        require(actual_hashes[rel] == expected, f'Input version mismatch: {rel}')
    freeze = json.loads((root/'protocols/holdout-freeze.json').read_text(encoding='utf-8'))
    correction = json.loads((root/'protocols/matched-all-freeze.json').read_text(encoding='utf-8'))
    d0 = pd.read_csv(root/'results/holdout-all.csv')
    dc = pd.read_csv(root/'results/matched-all-all.csv')
    require(len(d0) == 27648 and len(dc) == 1152, 'Unexpected run count.')
    require(set(dc.method) == {'ALL-auto-costmatched'}, 'Wrong corrected comparator.')
    d = pd.concat([d0, dc], ignore_index=True)
    keys = ['scenario', 'rep', 'method']
    require(not d.duplicated(keys).any(), 'Duplicate trajectory keys.')
    require(d.scenario.nunique() == 12 and d.method.nunique() == 25, 'Unexpected suite.')
    require((d.groupby(['scenario','method']).size() == 96).all(), 'Missing repeats.')
    require((d.total_pulls == d['T']).all(), 'Physical pull count differs from endpoint.')
    for scenario in freeze['scenarios']:
        g = d[d.scenario == scenario['name']]
        require((g['T'] == scenario['T']).all(), 'Mixed endpoint in a scenario.')
        require((g.K == len(scenario['means'])).all(), 'Wrong final count.')
    primary = d[d.method != 'ALL-auto-0.6']
    require(len(primary) == 27648 and primary.method.nunique() == 24,
            'Corrected primary roster must replace, not duplicate, the old ALL.')
    stored = pd.read_csv(root/'results/holdout-summary.csv').set_index(['scenario','method'])
    recomputed = d.groupby(['scenario','method'])[['regret','area']].mean()
    error = {}
    for metric in ['regret','area']:
        error[metric] = float(np.max(np.abs(recomputed[metric] - stored[metric+'_mean'])))
        require(error[metric] < 1e-7, f'Summary mean mismatch: {metric}')
    require(np.max(np.abs(d.tax-d.reward_tax-d.service_tax)) < 1e-8, 'Ledger mismatch.')
    require((d.service_attempts == d.service_pulls+d.service_denials).all(), 'Attempt mismatch.')
    residual = d.service_mass-d.service_attempts
    require(residual.min() >= -1e-7 and residual.max() <= 1+1e-7, 'Phase mismatch.')
    policies = {p['name']:p for p in freeze['policies']+correction['policies']}
    for name, p in policies.items():
        g = d[d.method == name]
        for key, col in [('beta_r','reward_tax'), ('beta_s','service_tax')]:
            if p[key] is not None:
                require((g[col] <= p[key]*g.spectrum_max+1e-8).all(), f'Budget: {name}/{col}')
        if p['priority'] == 0:
            require((g.service_pulls == 0).all(), f'Pure-reward method has service: {name}')
    for scenario in freeze['scenarios']:
        k, eta, delta = len(scenario['means']), scenario['eta'], scenario['delta']
        q = sum(np.ceil(32/eta**2*np.log(4*i*(i+1)/delta)) for i in range(1,k+1))
        require((d[d.scenario == scenario['name']].service_pulls <= q).all(), 'Quota charge mismatch.')
    # Endpoint equality is checked here, not asserted to prove pathwise equivalence.
    compat_cols = ['regret','area','service_pulls','label_error','coverage_error',
                   'empty_intersection','tax','final_unresolved','final_all_unresolved']
    def indexed(name: str) -> pd.DataFrame:
        return d[d.method == name].set_index(['scenario','rep'])[compat_cols].sort_index()
    require(indexed('F-R-TS-exact').equals(indexed('Thompson')), 'Compatibility record mismatch.')
    pairs = []
    for scenario, g in d.groupby('scenario'):
        p = g.pivot(index='rep',columns='method',values='regret')
        f = p['F-R'].to_numpy()
        for b in BASES:
            base = p[b].to_numpy(); x = f-base; n = len(x)
            se = x.std(ddof=1)/np.sqrt(n)
            ni = f-1.05*base-2
            pairs.append({'scenario':scenario, 'baseline':b, 'delta':float(x.mean()),
                'upper60':float(x.mean()+student_t.ppf(1-.05/60,n-1)*se),
                'relaxed_upper60':float(ni.mean()+student_t.ppf(1-.05/60,n-1)*ni.std(ddof=1)/np.sqrt(n))})
    wins = sum(p['delta'] < 0 for p in pairs)
    strict = sum(p['upper60'] < 0 for p in pairs)
    relaxed = sum(p['relaxed_upper60'] < 0 for p in pairs)
    require((len(pairs),wins,strict,relaxed) == (60,59,52,54), 'Paired counts differ.')
    failures = d.groupby('method')[['label_error','coverage_error','empty_intersection']].sum().astype(int)
    require(failures.loc['F-auto-0.6'].tolist() == [1,7,1], 'F-auto failure records differ.')
    require(failures.loc['F-R'].tolist() == [0,6,1], 'F-R failure records differ.')
    require(failures.loc['F-area'].tolist() == [0,8,0], 'F-area failure records differ.')
    suite = recomputed.groupby('method').mean()
    require(abs(suite.loc['F-R','regret']-60.73109114583333) < 1e-6, 'F-R sentinel differs.')
    report = {'kind':'read-only reanalysis; no new simulation or probability certificate',
        'input_sha256':actual_hashes, 'main_rows':len(d0), 'correction_rows':len(dc),
        'all_retained_rows':len(d), 'corrected_primary_rows':len(primary),
        'scenarios':12, 'replications_per_method_scenario':96,
        'summary_max_abs_error':error, 'paired_comparisons':len(pairs),
        'mean_wins':wins, 'strict_family60_upper_below_zero':strict,
        'relaxed_family60_upper_below_zero':relaxed,
        'relaxed_margin':'5% of comparator plus 2; not the literal zero-margin target',
        'phase_residual_range':[float(residual.min()),float(residual.max())],
        'phase_integer_boundary_cases':int((d.service_attempts != np.floor(d.service_mass+1e-8)).sum()),
        'compatibility_endpoint_pairs':1152,
        'failure_counts':failures.to_dict(orient='index'),
        'suite_means':suite.to_dict(orient='index')}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['main_rows','correction_rows','all_retained_rows',
        'corrected_primary_rows','summary_max_abs_error','mean_wins',
        'strict_family60_upper_below_zero','relaxed_family60_upper_below_zero']},indent=2))

if __name__ == '__main__':
    main()
```

编制任务书时已在提供的F17研究包上运行这个脚本：原主文件27648条、修正1152条、合计28800条；修正替换口径27648条。重算与汇总的最大均值偏差为regret约$6.82\times10^{-13}$、面积约$1.46\times10^{-11}$。60组配对的计数为59／52／54，与附录E一致。这些是本次实际再分析结果，**不是Codex未来执行已经完成**，也不是新增独立测试。

### F.2 最终核查清单

#### 内容与数学

- [ ] 基线确认为20页M3、20页S3；没有对旧29页／35页版本继续打补丁。
- [ ] 原两阶段elimination UCB-AA未被重新引入。
- [ ] F-CCP成为正文主算法；旧Checkpoint被完整保存为旧上界见证。
- [ ] 一般下界、最坏面积、增长率、旧重复更新两端及概率下界均有明确去向。
- [ ] 旧显式常数与旧检查点／UCB证明相配，没有改名转送给F-CCP。
- [ ] 新F定理涵盖证据、双预算、服务控制和兼容性；各自有限／无限预算、正服务率条件清楚。
- [ ] 风险仍为期望regret＋联合高概率标签／面积，没有悄悄换成期望加权和。
- [ ] $\varepsilon,\eta,\delta$固定任务，$\lambda,\beta_R,\beta_C,\theta$是行为参数，两者分开。
- [ ] “均值差小”和“接近近优边界”没有混同。
- [ ] P16的因果信息分离没有被写成所有前沿不可能。
- [ ] ABM的窗口、激活排名、新观测块、$R_0(T)$和参数校准全部保留，未成为F定理。
- [ ] 单独一致性构造不被归给有持久失败回退的F-CCP。
- [ ] 不存在“默认配置完整前沿最优／普遍支配基线／尾部更好”等无支撑主张。

#### 算法与实现

- [ ] 采用最终双账本生产分支，不误用旧单账本开发函数。
- [ ] 服务被拒后只观察一次；相位不退回，收益账本按实际选择计算。
- [ ] 收益分数在可行集上选择；不是强行改成所有拒绝后均选最大MC指数。
- [ ] 每轮真实计数与奖励和共享且单次更新；冷温度不制造虚拟置信信息。
- [ ] 模式切换不重置计数、区间、相位或账本；关闭服务不等于此前历史与独立基线重合。
- [ ] 零预算、禁用预算、单臂、未采样、平局、空区间和终点中止均有明确合同。
- [ ] 交互接口不接受真均值、未来到达、隐藏身份或测试终点。
- [ ] 复杂度按F实际代码给出，不继承旧Checkpoint的线性开销声明。

#### 数据与展示

- [ ] F17原主、修正ALL、旧CP、C16、P16五种数据身份分开。
- [ ] 主要ALL比较使用`ALL-auto-costmatched`；原错误ALL独立归档并披露修正。
- [ ] 纯收益五基线不被加入额外服务；主表用标准UCB1，保守UCB可在附表。
- [ ] 所有场景、关键配置与不利案例可查；没有只保留F胜出的表格行。
- [ ] 两臂接近例外、59／60均值、52／60严格区间和尾部分位风险均准确。
- [ ] 默认均衡F的一条标签错误、覆盖失败、空交集均进入统计。
- [ ] 单场景95%区间与跨比较校正区别明确，宽松非劣性门槛没有改成严格支配。
- [ ] 不从前4条保存路径生成声称96条重复的均值置信带。
- [ ] 场景等权汇总不被称作minimax值，参数连线不被称作最优前沿。
- [ ] 新资源环境不沿用旧实验的操作系统、耗时和CPU数字。
- [ ] 只读重算脚本通过或具体失败已记录；没有重写唯一原始数据。

#### 工程与出版文件

- [ ] 主文与补充全部`\label`/`\ref`/`\eqref`/`\cite`正确闭合，正文能定位每个新证明。
- [ ] 公式符号与算法编号统一；Beta函数与最优均值、收益和与谱量等未混淆。
- [ ] 所有实际引用的文献来源已核实，不加入内部评分作为学术证据。
- [ ] 主文和补充成功构建；缺少工具时如实标记，未伪称编译完成。
- [ ] 逐页检查主文与补充的最终渲染，尤其长公式、模式表、伪代码分页和图中文字。
- [ ] 原始输入、用户改动、科研包与失败记录均保留；未擅自上传、推送、提交。
- [ ] `claim-map.csv`、任务状态、阻塞项、哈希和变更摘要齐备。

### F.3 最终交付给用户的目录与说明

Codex完成后至少交付：

1. **修订后的论文源码与实际生成的正文／补充PDF**；若未构建成功，交付源码并明确状态，不能提供假成品名。
2. **逐任务变更记录**：每项R2任务的执行位置、旧内容去向、新来源、实际验收证据和阻塞原因。
3. **数学归属表**：一般理论、Checkpoint见证、F-CCP、ABM与独立谱输入分栏。
4. **实验再分析产物与审计**：本轮生成的表格／图／校验JSON、主对照替换规则、数据版本映射。
5. **仍待处理的事项**：缺源码、缺证明输入、待核文献、不能支持的主张或未授权研究；不得用“全部完成”掩盖这些事项。

所有用户可见文件路径必须实际存在。不要把工作区里仅有的文件名拼成不存在的下载链接。源码输出保留图表脚本及必要依赖，不向用户附送字体文件。

### F.4 不计入本轮完成条件的后续研究

更广到达类的联合最优前沿、暂缓端匹配下界、F-CCP相对最佳收益基线的带余项自适应界、更好的尾部控制、改进证书规划、大规模计算优化、新的独立验证环境与忠实FAREAST比较，继续记入`future-research.md`，**不要求Codex在这轮编辑任务里顺便解决**。

同样，不为了“算法换新”而删除理论限制，也不为了“保住新算法”而隐藏ALL或Thompson的优势。第二轮成功标准是：**一般成本理论完整保留、F-CCP作为可调实施方案自然进入主文、数学保证与实验证据的边界一一对应。**

