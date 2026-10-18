# F-CCP 算法流程图

本图解释当前算法的一轮执行过程。橙色表示专门认证，蓝色表示收益选臂，绿色表示两分支共用的观测与报告。论文、算法和冻结数值结果均未修改。

![F-CCP 一轮选臂与分类流程](fccp_flowchart.png)

主流程中，认证提议只是一个候选；只有相位触发且认证预算允许时，才执行认证采样。其余情况都进入收益分支，两个分支最后合并为一次真实观测。

```mermaid
flowchart TB
    accTitle: F-CCP One Round Sampling Flow
    accDescr: Each round computes current work from retained evidence, chooses either a certification action or a reward action, makes exactly one observation, and recomputes all labels.

    arrivals["本轮开始：接收新臂，保留旧观测<br/>更新虚拟指数与预算尺度<br/>未失败时，由当前区间重算待办 W_t"]
    cert_enabled{"未失败、λ > 0<br/>且 W_t 非空？"}
    cert_plan["认证规划：提出一个候选 j_t<br/>计算服务率 p_t<br/>累加相位：φ ← φ + p_t"]
    phase_ready{"φ ≥ 1？"}
    cert_budget{"先扣相位：φ ← φ − 1<br/>认证预算允许？"}
    cert_action["认证分支：选择候选 j_t<br/>将指数差记入认证账本 C_C"]
    reward_action["收益分支<br/>全体收益评分只生成一次<br/>在收益预算可行集合中选最高分<br/>将指数差记入收益账本 C_R"]
    actual_pull["合流：只拉所选臂 1 次<br/>观察奖励，更新真实 n_i、Σ_i<br/>仅更新被拉臂的置信区间"]
    all_reports["用更新后的区间重算所有臂标签<br/>输出正、负、未决：P_t、N_t、V_t<br/>进入下一轮"]

    arrivals --> cert_enabled
    cert_enabled -->|是| cert_plan
    cert_enabled -->|否| reward_action
    cert_plan --> phase_ready
    phase_ready -->|是| cert_budget
    phase_ready -->|否| reward_action
    cert_budget -->|允许| cert_action
    cert_budget -->|拒绝；不退相位| reward_action
    cert_action --> actual_pull
    reward_action --> actual_pull
    actual_pull --> all_reports
    all_reports -->|下一轮；保留全部历史| arrivals

    classDef neutral fill:#f3f4f6,stroke:#6b7280,stroke-width:2px,color:#1f2937
    classDef decision fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#713f12
    classDef certificate fill:#ffedd5,stroke:#ea580c,stroke-width:2px,color:#7c2d12
    classDef reward fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
    classDef shared fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d
    class arrivals neutral
    class cert_enabled,phase_ready,cert_budget decision
    class cert_plan,cert_action certificate
    class reward_action reward
    class actual_pull,all_reports shared
```

分类规则对每个已到达臂分别计算；更新一只臂的区间，也可能同时改变其他臂的报告。

```mermaid
flowchart TB
    accTitle: F-CCP Classification And Work Sets
    accDescr: Gap bounds determine positive, negative or unresolved reports. An unresolved arm is paused only when its complete gap interval lies within the boundary band; otherwise it remains in the work set.

    gap_bounds["根据全部当前区间<br/>计算每个臂的 gap 下界与上界"]
    positive["gap 上界 ≤ ε：正认证 P_t<br/>所有允许均值下都属于目标集合"]
    negative["gap 下界 > ε：负认证 N_t<br/>所有允许均值下都不属于目标集合"]
    unresolved["其余：未决 V_t<br/>当前证据尚不能确定标签"]
    paused["gap 区间全在 [ε − η, ε + η]<br/>暂缓 Z_t；仍报告未决"]
    work_set["其余未决臂：待办 W_t<br/>下一轮可安排专门认证"]

    gap_bounds --> positive
    gap_bounds --> negative
    gap_bounds --> unresolved
    unresolved --> paused
    unresolved --> work_set

    classDef positive_label fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d
    classDef negative_label fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#7f1d1d
    classDef pending fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#713f12
    classDef paused_label fill:#f3f4f6,stroke:#6b7280,stroke-width:2px,color:#1f2937
    classDef active_work fill:#ffedd5,stroke:#ea580c,stroke-width:2px,color:#7c2d12
    class gap_bounds paused_label
    class positive positive_label
    class negative negative_label
    class unresolved pending
    class paused paused_label
    class work_set active_work
```

图中的 gap 上下界为

$$
g_i^- = \max\{0,\max_{j\ne i}\ell_j-u_i\},\qquad
g_i^+ = \max\{0,\max_{j\ne i}u_j-\ell_i\}.
$$

收益分支选择

$$
I_t=\arg\max_{i\in\mathcal F_R(t)}\Xi_i(t),\qquad
\mathcal F_R(t)=\{i:C_R(t-1)+\zeta_t(i)\le\beta_R\overline{\mathcal S}_t\}.
$$

认证提议的预算检查为

$$
C_C(t-1)+\zeta_t(j_t)\le\beta_C\overline{\mathcal S}_t.
$$

在图的认证规划节点内，程序逐个检查待办与参考臂的配对，选择局部规划价格最低的合法配对，再选其中当前最值得补样本的一端。若没有合法配对端点，就选尚未达到检查点的最宽区间。每次只执行一拉，下一轮重新规划。

- 相位决定是否尝试认证；预算决定是否允许执行。被预算拒绝时，相位不退还。
- 两类采样共用真实观测统计量。仅被拉臂的区间更新，但全部已到达臂的标签都重算。
- 负标签不删除臂；新臂可能使旧正标签重新未决。边界带内暂缓的臂仍报告未决。
- 若区间交集为空，程序设置永久失败标志：停止专门认证，所有报告未决；收益采样和真实统计量更新继续。
- 检查点不是开始分类的门槛。达到检查点时加入额外区间，其他轮次也持续更新混合置信证据。

依据：[当前稿件算法](../manuscript.tex)、[交互执行实现](../experiments/fccp_frozen/src/flexible_ccp.py)、[认证规划及服务率](../experiments/fccp_frozen/src/flexible_engine.py)。

`render_flowchart.py` 从本文件的两个 Mermaid 图读取节点文字和有向边，生成便于阅读的合并 PNG/PDF；布局单独固定。运行时检查渲染边与 Mermaid 源一致。
