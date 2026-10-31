# 全 setting 缩小预研究与相对 regret 热图

`screen-all` 覆盖全部 45 个来源布局、540 个 layout-law 组合，每个组合 4 次配对重复、全部 40 个最终方法配置，共 86,400 条唯一轨迹。它是明确缩小后的研究，不是原时域与原臂数的正式主实验。

```powershell
python run_main.py run --profile screen-all --dry-run
python run_main.py run --profile screen-all --output _runs/screen-all --workers auto
python run_main.py run --profile screen-all --output _runs/screen-all --workers auto --resume
python run_main.py relative _runs/screen-all
```

## 缩小规则

时域统一为 T=400。F17 与 adaptive 保留全部原臂；dense 来源 K=100/500/2000 分别以 K=20/40/80 为目标，scale 来源 K=4000 以 K=100 为目标。保留全部原记录臂、第一/最后到达、全局最优身份和完整五臂 burst；保真约束需要时允许实际臂数超过目标并明确记录。

因此来源 K100 的 burst 布局实际有 30 臂，该列实际 K 范围为 20–30。所有保留的原到达批次映到不同物理时点，原批次内部的同时性不变。重新计算 record 后，45 个派生布局的 record 身份均未改变。选择规则仅使用冻结布局参数，在读取本研究结果前确定，不按结果挑选环境或算法。

来源、原/实际 T/K、所选原臂编号、时间变换和扩容原因均记录在结果 `config.json` 的 `metadata.derivative` 中。图列同时标注原始与实际臂数，不能将这一缩小研究的结果当成原 K=2000/4000 的测量。

## 百分比的含义

主要热图分别比较 **SRC-R** 和 **SRC-KL-R** 与 22 个 canonical baseline。它们关闭专门分类服务，适合评价奖励效率。所有正分类偏好、area 和匹配调度控制均实际运行，数值保存在完整表中，不与 reward-only 比较混淆。

每个来源组先对 layout-law 单元的重复均值等权，再计算

$$
\mathrm{change}(C,B)=100\left(\frac{\overline R_C}{\overline R_B}-1\right)\%.
$$

负值表示候选 regret 更低，正值表示更高。例如 -20% 表示候选平均 regret 为该 baseline 的 80%；它不是 regret/T 减少 20 个百分点。先取宏均值之比，不平均各单元的百分比。baseline 均值为零时百分比记为未定义，不添加任意小常数。

主要 overall 对全部 540 cells 等权；另给六个来源 section 等权、section 内各 cell 等权的 balanced 敏感性摘要。两者都预先定义，结果不同也全部报告。CI 使用保留候选/基线配对协方差的分层 delta-method t 区间，属于描述性、未调整区间；主图不画显著性星号。四次重复不能据此宣称普遍支配或长期渐近优势。

热图在正负 100% 外饱和以保持较小变化可见，但文字和 CSV 始终保留真实完整值。蓝色为降低 regret，红色为增加 regret。

## 输出

结果目录下 `relative_regret/` 提供：

- `relative_regret_screen.png`、PDF、SVG：两种候选分别对全部 baseline 的分组热图。
- `percent_matrix.csv`：相对百分比、绝对 regret 差、配对标准误和描述性区间。
- `percent_matrix_SRC-R.csv`、`percent_matrix_SRC-KL-R.csv`：可直接读取的宽表。
- `all_cell_methods.csv`：40 方法 × 540 cells，共 21,600 个单元均值与 MCSE。
- `section_methods.csv`：全部方法在各来源与两种总体权重下的表现。
- `all_method_relative_overall.csv`：全部方法相对 22 baseline 的总体百分比。
- `direct_KL_minus_SRC.csv`：两候选之间的直接配对比较。
- `summary.json`、`report.html`：完整性、失败旗标与离线图表报告。

所有 coverage、错误标签和空交集路径保留。没有根据表现删除方法、选择最好的 BL-MOSS 参数或改变算法参数。以上结论只条件于这套预先确定的缩小环境矩阵。
