# 第二轮逐项执行记录

日期：2026-10-17。依据 `proposal/第二轮稿件修改_FCCP整合_Codex执行方案_v2.0.md`。本轮是冻结研究成果的整合与既有数据再分析，没有新增比较实验、重新选参、创新评分或补造定理。

最终工程验收已完成。正文25页、补充64页全部渲染并实际查看；最终日志无未定义引用、重复标签或溢出。32项任务均已完成本轮规定的编辑／核对范围；伴随稿公开元数据的待确认项单列于 `blocked-items.md`，不冒充外部完整证明认证。

| 任务 | 状态 | 实际位置与处理 | 已有验收证据／尚待事项 |
|---|---|---|---|
| R2-00 锁定基线 | DONE | `baseline/`保存两份20页PDF、全部当前TeX入口、文献和构建脚本；`source-map.json`记录入口、研究包、基线与受保护输入哈希 | 原PDF哈希匹配任务书M3/S3；`build-logs/baseline-commands.json`六条基线构建命令均exit 0；git状态保留 |
| R2-01 区分主方法和见证 | DONE | 正文§3唯一主方法F-CCP；S5旧Checkpoint、S13 ABM独立；`claim-map.csv`统一原／新命题归属与数值来源 | 两份专属合同表合并；旧两阶段UCB-AA未重新引入；一般下界不归属某个算法 |
| R2-02 统一记号 | DONE | 正文§2参数表、§3新记号；`notation-map.md`逐项映射均值、半径、混合过程、谱、队列、配额和拒绝数 | 保留原任务与物理观察顺序；环境索引和温度分开；Checkpoint与F报告规则分开 |
| R2-03 摘要 | DONE | `manuscript.tex`摘要保留一般维护问题、最坏面积及临时任务，加入F的共享证据与双预算实施 | 每项结论对应正文／补充；无完整前沿或全环境支配claim，原题名／署名／日期机制保留 |
| R2-04 引言 | DONE | 正文§1保留原模型和相关文献关系，贡献组织为一般困难、临时任务结构、可调实施；准确纳入P16信息限制及中间区间 | 不以研究版本历史为主线；不把标准置信序列／TS／历史保留当新增概念 |
| R2-05 模型与参数分层 | DONE | 正文§2固定原风险，区分任务、调度、收益行为、保护和辅助证据参数 | 保留并列、任意有限批和$K_T>T$；无新增统一正gap或已知参照；全模型可靠性与性能族面积分开 |
| R2-06 Checkpoint迁移 | DONE | 补充S5含原正文§3全部公式、完整算法、原Prop及旧S2证明／completion | `retained_contract_audit.md`；$1-\delta/2$、$3\log(2t)$、偶数FIFO、单次固定前缀和无条件regret均保留 |
| R2-07 新证据层 | DONE | 正文§3.1和S2：混合区间、全已观察前缀交、固定检查点、排除自身gap、暂停集和持久失败 | `fccp_contract_audit.csv`；`fccp_independent_interface_review.md`复核一般bounded超鞅与两份$\delta/2$预算 |
| R2-08 证书成本规划 | DONE | 正文§3.2与S2：中心、半径、pair代理、闭式／边界解、真实配额资格及兜底 | 与冻结`service_plan`／`pair_plan`分支对照；明确代理优化不等于统计全局最优 |
| R2-09 虚拟指数与双预算 | DONE | 正文§3.3及S3—S4：到达时钟、谱running maximum、两账本、可行集投影与一次完整评分向量 | 生产入口`choose_dual`；拒绝不先观察、不退相位；所有统计和账本不重置 |
| R2-10 偏好与四模式 | DONE | 正文§3.4、`tab:fccp-modes`、S4；F-R／Balanced／Classification／Compatibility分开 | 映射冻结JSON与交互预设；inactive服务预算不改写原null／0记录；切换只发生在完整物理轮之间 |
| R2-11 主伪代码 | DONE | 正文`alg:flexible-ccp`含到达、计划、相位、两guard、唯一观察、证据和报告 | `fccp_contract_audit.csv`的code-dual行；最终正文第10页完整算法已放大检查，保证小节置于其后 |
| R2-12 可靠性与兼容性 | DONE | 正文`prop:fccp-report`／`prop:fccp-compat`，完整证明S2／S4 | 总可靠性$1-\delta$；从起点同核、完整状态、同后端随机流才路径相同；F-R不冒充标准TS端点 |
| R2-13 双预算regret | DONE | 正文`thm:fccp-budget`；S3任意动作桥梁、潜在前缀、不重复计数、时钟谱归并；S4账本代入 | 独立接口复核确认常数300有余量，F-R332／Balanced334，认证无限额保留$Q_T^{\mathrm{cap}}$；无遗漏$\delta T$ |
| R2-14 服务率与有限臂 | DONE | 正文`thm:fccp-area`／`cor:fccp-finite`，S4完整面积及非饥饿证明 | 保留拒绝项、正busy率、正认证预算和停止到达条件；coverage事件上边界外完成不写成a.s.精确一致性 |
| R2-15 共同认证下界 | DONE | 正文§4.1、补充S6保持同一参考环境及全部替代环境 | 原$q_-$、分析队列、$(3/4-\delta)\mathcal B_T$、$\mathcal B_T/4$与$1/4$概率及参数范围不变 |
| R2-16 最坏面积与增长 | DONE | 正文§4.2—4.3、补充S5—S7；旧常数与Checkpoint伴随regret保留；另述F分类模式同阶 | $2^{-24}$和256不挂到F名下；固定日程、终点臂数类及突发反例量词分开 |
| R2-17 旧临时任务与两端 | DONE | 正文§5压缩机制；旧Prop5.1完整迁S9；S8—S10保留原两端与概率下界 | 原端点$H$、快速$V/8$、暂缓$9V/8$仅upper、$q+1$停止及$11/80$概率保留 |
| R2-18 P16信息与中间预算 | DONE | 正文§5末短节，S12日程分离，S13任意恢复数／ABM完整算法和证明 | `p16_independent_interface_review.md`；fresh blocks、激活排名、独立$H\ge4(L+B_{\rm rec})$、$R_0$和$s(a)$使用$m,H$均保留 |
| R2-19 S1—S17及引用 | DONE | 17节均内联到唯一`supplement.tex`，各算法归属分开，全部基线标签保留 | `source-checks.json`无重复／未定义引用；主补双向引用经两轮构建闭合；全部原标签的保留见`final-verification.json` |
| R2-20 冻结代码与映射 | DONE | `experiments/fccp_frozen/`精确发行副本；生产／开发入口映射位于`analysis/production-branch-map.csv` | 172份发行输入副本；`numerical-validation.json`记录175个原manifest项核对，冻结原件不变；短接口检查passed |
| R2-21 数据代际清单 | DONE | `analysis/dataset-inventory.json`列旧CP5760、C16 13440、P16 12672、F17主27648与修正1152 | 原与修正ALL共同保留总28800；主分析替换旧ALL仍27648，25个存储ID与24个主ID分开 |
| R2-22 主协议及基线 | DONE | 正文§6.1、S15全场景／方法表、冻结两JSON | 12场景、96配对重复、2—20臂、12000—16000终点、11 Bernoulli+1有界两点；纯收益不加服务 |
| R2-23 纯收益主表 | DONE | `tab:reward-baselines`、`fig:reward-paired`、S15全SE／60配对表 | `pure-reward-paired-recomputed.csv`和只读核验：11/12、59/60、52/60、宽松54/60；保留two_close例外和19.4846%等权描述 |
| R2-24 偏好及公平ALL | DONE | `tab:preference-costs`、`fig:preference-tradeoff`、S15配对和服务诊断 | 修正`ALL-auto-costmatched`作为主对照；固定认证预算点与无限额F-area分开；保留$.9$至1的非单调与CCP权衡 |
| R2-25 失败和尾部 | DONE | 正文§6.4及S15完整失败／经验尾表，S16审计 | 所有失败保留计入指标；F-auto一次误标、非零覆盖／空交集及三个不利尾部分位显式呈现；`all-failure-records.csv`可追溯 |
| R2-26 图表重排 | DONE | 新主图由终点记录生成至`generated/`；旧24行表、全部旧图／服务表移S17 | 数值脚本生成0个独立TeX组件；未从仅4条保存路径伪造96次学习曲线；最终全部图表已实际查看，13个新数值表块与再分析一致 |
| R2-27 讨论及边界 | DONE | 正文§7区分可调实施、各自保证与未闭合一般前沿 | 不继续称没有可用方案；不把有限测试优势、ABM或兼容端点变成默认F全环境最优 |
| R2-28 来源与引用 | DONE | 正文相关文献和`references.bib`；`literature-check.md`记录实际primary核对 | MC-MOSS谱输入按匿名未公开companion身份、题名和项目版本引用；缺公开作者元数据／永久号列入`blocked-items.md`，不虚构 |
| R2-29 可用性与资源 | DONE | 正文Data and code availability、S16、发行代码／配置／结果和`analysis/release-manifest.json` | 模拟数据、主／修正／旧CP角色分开；F17资源来自其environment，不套用旧Windows运行13.5秒；不称已有公共URL |
| R2-30 综合验收 | DONE | 数学及实现接口复核、只读重算、两文档构建和89页图像检查全部完成 | `final-verification.json` passed；1527个受保护文件未变、172份发行副本匹配、25个主表行及13个数值表块匹配；`page-review/`三份报告绑定最终PDF；最终12条构建命令exit 0 |
| R2-31 交付 | DONE | 两份完整TeX、25／64页PDF、代码和数据副本、92行claim映射、任务记录、变更、阻塞、记号及后续研究清单 | 根目录`README.md`和发行`README_release.md`给出实际入口；最终源码／PDF哈希、全部页面和实际命令可查；本轮完成不等同于新增研究或期刊接收保证 |

可重现的实际命令及输出见对应Python脚本、`build-logs/`和`analysis/`。本表没有将数据重算当新实验，也没有把内部接口复核表述成外部独立概率认证。
