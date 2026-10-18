# 新正文第3—5节分块核对

本记录只覆盖 `main_theory_blocks.tex`，由主编辑整合进单一 `manuscript.tex`。冻结对照源是同目录 `baseline/manuscript.tex` 和 `baseline/theory/supplementary_proofs.tex`；算法对照为现有 `experiments/reference_cp_ucb_aa.py`。本次没有直接修改主入口、补充材料入口、原理论源、算法代码或运行记录。

## 任务卡

| 任务 | 分块状态 | 实际处理及定位 |
|---|---|---|
| A-10 | DONE | 新第3节展示名为 Checkpoint-UCB；`alg:checkpoint-ucb` 给出全部状态、到达、选择、一次观察、冻结检查点和报告。没有改类名、接口、方法ID或算法行为。 |
| A-11 | DONE | `prop:reporting` 保持全过程标签概率、无条件期望regret式和服务计数界。收益分析采用可求和集中与不重复预拉取计数，不条件化标签成功事件。 |
| A-12 | DONE | `thm:broadcast` 保持共同参考环境、所有参数、期望与概率下界；`Q_t` 与实际FIFO队列分开说明；`eq:queue_area` 保持观察后报告的末轮修正。 |
| A-13 | DONE | `thm:worst_area` 提前到 `cor:growth` 之前。增长充分性引用补充材料独立 `app:completion_general`，没有把增长推论的参数范围收窄到最坏面积定理。单日程、增长指数、逐终点日程类与突发反例分别叙述。 |
| A-14 | DONE | `eq:family_parameters`、`eq:family_means` 保持多次更新族。显式说明当前收益gap、边界距离、更新后gap、永久可用、未知参照身份及最终全部参照为近优集合。 |
| A-15 | DONE | 保留 `eq:partial_recovery`、半完成的面积逻辑及共同乘积先验。长的异质松弛定义从正文移除，并指向 `app:area_lower`；证明编辑负责在附录完整保留定义与原公式。 |
| A-16 | DONE | `thm:reuse` 保留面积式并增加 `eq:reuse_regret`；后者逐项迁自冻结源S7的既有无条件期望式。定义有限时域内有正gap的求和域、最小正gap与最大gap。没有增加重叠到达推广。 |
| A-17 | DONE | `thm:tradeoff` 保持全部常数、指定窗口和终点、两种面积预算、快速端匹配与暂缓端仅上界。范围限制紧随定理。 |
| A-18 | DONE | `thm:quantile_main` 保持固定环境上的非消失概率下界；解释停止在超过候选样本预算的第一次样本处。联合分位定义与推论指向 `sec:quantile_extension`。 |

`DONE` 指分块编辑及源级核对完成。最终双文档构建、跨文档引用和整页视觉验收由主编辑整合后执行，不在此虚构已通过的记录。

## 数学内容核对

忽略空白及集合符号命令中不影响排版的花括号后，下列17个带label的原数学环境保持一致：

`eq:checkpoint`、`eq:fixed_interval`、`eq:ucb`、`eq:reports`、`eq:reward_bound`、`eq:broadcast_queue`、`eq:queue_area`、`eq:worst_area`、`eq:joint_general`、`eq:queue_upper`、`eq:family_means`、`eq:partial_recovery`、`eq:reuse_conditions`、`eq:reuse_area`、`eq:rapid_matched`、`eq:coarse_regret`、`eq:quantile_main`。

其他需要单独说明的文字展开：

- 家族参数显式写出 $v>0$；原来的 $d>0$ 与 $d\le v/32$ 已蕴含该条件。
- 指定终点式再次写出 $T=(J+1)H$，原家族定义已包含它。
- 最坏面积定理中显式写出 $K,T$ 为整数，未改变原任务的离散臂数和物理时间范围。
- 一般共享证据结果明确窗口划分物理时间，邻批条件仅对 $e<J$，总工作与窗口完成条件包含末批；这是既有多次更新族和原证明的索引展开。
- 新的 `eq:reuse_regret` 逐项与旧S7一致；$\gamma_i$ 的定义域限定到截至 $T$ 已到达且出现正gap的臂。未引入除零项，也没有反复征收旧臂配额。

未新增理论、未修改保留结论的常数、概率、截断或风险协议；源级等价核对不构成全部证明的独立验证。

## 算法语义对照

| 正文伪代码操作 | 真实参考类中的对应操作 |
|---|---|
| 固定到达次序接纳全部新臂并赋连续标签 | `choose()` 中 `labels` 与 `expected` 检查及逐臂初始化 |
| 逐臂一次配额与初始区间 | `ArmState` 的 `quota/count/reward_sum/lower/upper` |
| 清除已完成的队首，再在偶数轮服务队首 | `pending` 的前缀清除与 `time % 2 == 0` 分支 |
| 其余轮在全部已到达臂上算UCB，零计数无穷大、小标签破平局 | `index()` 与 `max(..., key=(index(i), -i))` |
| 每轮一次观察、更新同一总计数及奖励和 | `observe()` 中 `count += 1`、`reward_sum += reward` |
| 仅在首次等于配额时形成区间 | `if a.count == a.quota`；超过配额不会重算 |
| 观察后按上下最佳端点报告三分区 | `report()` 的 `L/U/C/D` 与集合补 |
| 报负不剔除收益选择资格 | `self.arms` 从未依报告删臂；UCB对全部该字典键求最大 |

主伪代码不使用真实均值、未来到达、评估终点、真实标签或边界带评价条件。每个UCB样本也抵扣同一lifetime配额；服务轮不追加第二次观察。实际FIFO队列记为 $\mathcal Q^{\rm srv}$，广播下界分析证书记为 $Q_t$，二者分开。

## 英文编辑与范围

依据 `stat-journal-writing`，每个结果附近说明统计作用、参数作用和适用界限；构造承担可达性角色，不宣称普遍优越。依据 `humanizer`，删除旧稿修复过程、重复导航和口号式过渡，保留技术措辞及负面范围限定。没有把文字润色描述为作者身份认证或可检测统计水印的保证。

本分块未发现需要新增假设或修改数学才能继续编辑的已知阻塞。没有开展新比较实验；本记录不把代码阅读等同于本轮重新运行历史实验。
