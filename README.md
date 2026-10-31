# SRC / SRC-KL 统一数值实验

论文当前无 H8 的 **SRC** 与理论改进版 **SRC-KL** 的最终实现：19 个奖励 baseline、匹配分类调度对照、45 个布局、540 个环境单元，以及统一配对模拟、校验、分析和绘图入口。SRC-KL 保留原经验分布奖励评分，改变 KL/MOSS 切换参考与奖励账本上限。

**完整原规模正式矩阵尚未运行。** 仓库提供两套流程试跑，以及覆盖全部 setting 的缩小预研究入口；缩小后的比较不能代替原规模实验。完整正式入口覆盖 374,496 条唯一轨迹，包含独立尾部研究；复用的奖励端点只执行、计数一次。

本目录发布最终实现、冻结实验配置、分析程序和有效结果；参数检查只保留两个最终候选的验证产物。正常 Git 历史保留，精简来源记录在 `configs/provenance.json`。运行不依赖相邻 `proposal`、Overleaf、WSL 或 C++ 编译器。

## 本机试跑

使用 Python 3.11；已在原生 Windows、Python 3.11.7 验证。首次运行包含 Numba 编译。

Numba 缓存按包内源码、Numba 版本和 Python cache tag 的指纹隔离；spawn 子进程沿用同一缓存命名空间，无需手动清理旧缓存。

```powershell
python -m pip install -r requirements.txt
python run_main.py run --profile smoke-small --output _runs/my-small --workers 1
python run_main.py run --profile smoke-dense --output _runs/my-dense --workers 1
```

每条命令完成模拟、校验、分析和 PNG/PDF/SVG 绘图。打开输出目录的 `analysis/report.html`，图像在 `figures/`，均可离线阅读。输出目录必须为空；再次运行请换目录，或用 `--resume` 续跑同一配置。

| 小实验 | 环境 | 比较内容 | 唯一轨迹 |
| --- | --- | --- | ---: |
| smoke-small | 双臂与少量到达派生布局，T=1000，两种分布，4 次重复 | 两种主算法的奖励端点、偏好 .6、area；全部 19 baseline | 400 |
| smoke-dense | 稳定 incumbent 与晚到记录派生布局，T=800、K=40，两种分布，4 次重复 | 两种主算法的三个模式；IMED、Empirical-KL-UCB、ACI、Growing-MOSS | 160 |

本次完成的结果在 [results/smoke-small](results/smoke-small) 和 [results/smoke-dense](results/smoke-dense)。派生小实验统一标为 smoke，不混入正式矩阵。

下图是密集到达小试验的配对结果，n=4；只作流程和行为检查，不代表完整正式实验结论。实际运行状态见 [STATUS.json](results/STATUS.json)，验收记录见 [VALIDATION.json](results/VALIDATION.json)。

![密集到达试跑的奖励与未决量权衡](results/smoke-dense/figures/tradeoff_smoke_dense_joint.png)

## 全 setting 的缩小比较

需要先比较所有算法在所有 setting 下的表现时，可运行全 setting 缩小研究：

```powershell
python run_main.py run --profile screen-all --dry-run
python run_main.py run --profile screen-all --output _runs/screen-all --workers auto
```

该 profile 为 45 个来源布局 × 对应分布，共 540 cells；T=400、每单元 4 次配对重复，全部 37 个配置，共 79,920 条轨迹。输出 `relative_regret/report.html` 与两种 SRC 对 19 baseline 的相对 regret 热图。原/实际臂数、配对百分比与统计解释见 [SCREENING.md](docs/SCREENING.md)。

本轮已在当前数值核及隔离缓存下重新跑完并通过独立核验。单元等权总体上，SRC-R 与默认 SRC-KL-R 相对 IMED 的平均 regret 分别降低 22.4% 和 4.5%；来源组等权的敏感性摘要也全部保留。各组有明显差异，不能把总体平均看成每个 setting 的优势。完整结论见[实际结论](results/screen-all/relative_regret/RESULTS.md)、[完整单元表](results/screen-all/relative_regret/all_cell_methods.csv)、[百分比表](results/screen-all/relative_regret/percent_matrix.csv)。

![两种默认算法对19个baseline的相对regret](results/screen-all/relative_regret/relative_regret_screen.png)

## SRC-KL 固定参数检查

另外完成了 F17/adaptive 全部 384 个原尺寸组合、每单元 2 次配对重复的两个固定参数候选验证，以及全部 540 个派生组合的 4 次重复压力检查。只把奖励上限系数改为 8192、保留评分系数 0.5，原尺寸 F17/adaptive 相对 IMED 的平均 regret 降低 34.1%/31.5%。四个主要 baseline 比较中三项校正区间低于 0；F17/Empirical-KL-UCB 尚不能确认。该配置表现接近原 SRC，并非 KL 机制独有收益；没有替换默认算法或运行原尺寸 20 次正式批次。详见[参数检查结论与区间](results/parameter-check/RESULTS.md)。

```powershell
python replay_parameter_check.py run --stage original --output _runs/parameter-original --workers 16 --analyze
python replay_parameter_check.py run --stage scaled --output _runs/parameter-scaled --workers 4 --analyze
```

入口只依赖本仓库的最终配置与代码，可用 `--resume` 续跑，或 `python replay_parameter_check.py analyze OUTPUT` 单独分析。

## 完整原规模主实验

```powershell
python run_main.py run --profile full --dry-run
python run_main.py run --profile full --output _runs/main --workers auto
python run_main.py run --profile full --output _runs/main --workers auto --resume
```

`--dry-run` 只打印冻结规模。完整矩阵约有 45 亿次实际拉臂，是长批次任务；不能用首次 JIT 或单次混合负载计时保证完成时间。`auto` 按可用 CPU 和内存选择 worker，上限 8；也可指定 1–64。并行数不改变种子或轨迹。

| 模块 | 布局 × 分布 | 奖励重复数 | 分类重复数 |
| --- | --- | ---: | ---: |
| F17 旧布局 | 12 × 16 | 32 | 8 种分布 × 16 |
| adaptive 新布局 | 12 × 16 | 32 | 8 种分布 × 16 |
| dense | 18 × 8 | 16 | 4 种分布 × 8 |
| scale | 3 × 4 | 8 | 4 种分布 × 8 |
| 独立尾部 | adaptive 中 6 × 2 | 128，四个奖励方法 | 不追加分类 |

原始到达时刻、均值、时域和任务参数均在 `configs/layouts.json`。这是新的统一重复协议，不复用旧算法结果。`full` 已包含尾部研究，也可单独运行 `--profile tail`。

两种主算法各有 reward-only、偏好 .1/.3/.6/.9/1 的有限分类预算模式，以及无限分类预算的 area 模式；奖励系数均为 32，有限分类系数为 1。分类匹配控制是每种算法各自的 widest-interval、LUCB-style，偏好 .6。baseline 的公式、额外信息与别名见 [算法说明](docs/ALGORITHMS.md)。

## 验证与重画

```powershell
python -m pytest -q
python run_main.py verify results/smoke-small --check-current
python run_main.py analyze _runs/my-small
python run_main.py plot _runs/my-small
```

当前测试集已通过 170 项测试，包含接近 1 的实际支持点边界、奖励评分的合法剪枝上界、有限预算指数反演的可行下端点、源码与进程缓存隔离，以及冻结参数配置的重放、分析和续跑。数值核细节见[算法说明](docs/ALGORITHMS.md)。

在线 API 为 `Policy.choose(new_arms)`、`observe(reward)`、`report()`；示例见 [ALGORITHMS.md](docs/ALGORITHMS.md)。配对、统计、输出和续跑规则见 [EXPERIMENTS.md](docs/EXPERIMENTS.md)。全部科学失败路径保留；执行异常单独记录，不能视为零成本或从完整结果中悄悄剔除。
