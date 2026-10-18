# 数值代码、最终结果与重跑入口

本轮只整合和核验已有代码、数据与支撑材料，没有运行新的性能模拟。输入逐文件记录在 `numerical-import-manifest.json`；整合前的盘点快照在 `numerical-inventory.json`。所有原始研究目录、原 ZIP 和仓库外的 `simulation_final` 均未改动。路径以下均相对于本稿目录。

## 五代数据分别保留

| 研究 | 可运行副本 | 最终记录 | 用途 |
|---|---|---:|---|
| 原投稿 C/E | `experiments/original_submission_archive/` | 每场景五方法、各 100 次重复 | 历史原稿，不能与后续主表合并 |
| 第一轮 CP | `experiments/` | 5,760 | 当前附录 S17 的四场景、九方法、160 次重复 |
| C16 CCP | `experiments/ccp_frozen/` | 13,440 | 独立开发研究，十场景、21 方法、64 次重复 |
| P16 Frontier/Shared | `experiments/frontier_frozen/` | 12,672 | 十二场景、22 方法、48 次重复；ABM 理论与有限 LP 另存 |
| F17 F-CCP | `experiments/fccp_frozen/` | 27,648 + 1,152 | 当前主实验：原始主测试及随后冻结的 ALL 成本接口修正 |

F17 的 `holdout-all.csv` 有 24 个原方法，`matched-all-all.csv` 有一个修正方法；两者共同保存 25 个方法 ID。主分析用修正的 `ALL-auto-costmatched` 替换原 `ALL-auto-0.6`，仍为 24 方法、27,648 条；不能把两个 ALL 版本平均。全部失败路径、不利结果、开发轮次和诊断记录均保留。不同研究中同名场景并不代表相同参数或潜在随机流。

整合核验结果：C16 原始 287 个文件、P16 原始 109 个文件、F17 原始 176 个文件均已具有直接可读的本地副本。三个原 ZIP 的全部成员分别按 SHA-256 对照原始目录通过，ZIP 本身仍保留在 `experiments/fccp_frozen/original-archives/`。缓存目录不属于源码或结果，不复制。

## 已补齐的散落文件

F17 原先只提取 169 个文件；本轮补入 `theory.md`、`audit.md`、`README.md`、中文研究报告、`dependencies/ccp_theory_20261016.md` 与两份内部评价 JSON。内部评分只是研究过程材料，不作为论文方法有效性证据。

仓库外原投稿 `simulation_final` 的根源代码/README 保存在归档的 `source/`；原 `outputs/final/scenario_C`、`scenario_E` 对应归档同名目录，保留 checkpoint 汇总、原图、终点 CSV 和配置；原最终总汇保存在 `original_summary.json`。已有相同文件只复核而未覆盖。`source/manual_ce_final.py` 是另一个历史四方法探索入口；复现原最终五方法配置应使用 `ce_five_algo_runner.py`，不能混用。

两份曾遗漏的逐 checkpoint 原始数据分别为 188,110,597 和 192,061,426 字节，现保存为各场景目录的 `raw_checkpoint.csv.gz`。压缩使用空内嵌文件名、`mtime=0`、级别 9；每份流式解压后的长度和 SHA-256 都已与原件一致核验。原 `metadata.json` 保留其生成时的历史说明；本轮新增清单说明如今已经补齐的内容。

如需普通 CSV，请在运行副本中解压，避免向 Git 提交大于 100 MiB 的未压缩文件：

```python
from pathlib import Path
import gzip, shutil

root = Path("experiments/original_submission_archive")
for scenario in ("C", "E"):
    path = root / f"scenario_{scenario}" / "raw_checkpoint.csv.gz"
    with gzip.open(path, "rb") as src, path.with_suffix("").open("wb") as dst:
        shutil.copyfileobj(src, dst)
```

## 现有结果的再分析

从本稿目录运行，不生成新的奖励轨迹：

```powershell
python -X utf8 revision2/analysis/reanalyze_fccp.py --release-only
python -X utf8 revision2/analysis/check_revision2_data.py --f-root experiments/fccp_frozen --out reproducibility/fccp-check-fresh.json
python -X utf8 revision2/analysis/check_fccp_interface.py
python -X utf8 figures/gen_fig_performance.py --figures-only
```

验证器拒绝覆盖已有输出；再次检查请换一个 `--out` 文件名。再分析生成 JSON、CSV 和图，不应再次拆出可编辑 TeX 分节。原数值生成器在历史上含有 `supplement.tex` 字符串，那是合并前的版式说明，不是数值依赖；当前唯一稿件入口为 `manuscript.tex`。

## 从头重跑冻结的最终测试

下面均在**新复制的运行目录**中执行。驱动器会写入原命名的分片/汇总，故不要直接覆盖随稿冻结记录。四个 worker 可以顺序或并行运行；它们分割场景，参数和种子不变。保留随包协议，不重新执行 `freeze_test.py` 或重建冻结记录。

F17：复制整个 `experiments/fccp_frozen/` 到独立运行目录，进入该目录，然后：

```powershell
python -X utf8 src/study_v2.py --stage holdout --worker 0 --workers 4
python -X utf8 src/study_v2.py --stage holdout --worker 1 --workers 4
python -X utf8 src/study_v2.py --stage holdout --worker 2 --workers 4
python -X utf8 src/study_v2.py --stage holdout --worker 3 --workers 4
python -X utf8 src/study_matched.py --stage matched-all --worker 0 --workers 4
python -X utf8 src/study_matched.py --stage matched-all --worker 1 --workers 4
python -X utf8 src/study_matched.py --stage matched-all --worker 2 --workers 4
python -X utf8 src/study_matched.py --stage matched-all --worker 3 --workers 4
python -X utf8 src/analyze.py
```

主生产动作入口是 `src/flexible_v2.py::choose_dual`，交互接口是 `src/flexible_ccp.py::FlexibleCCP`。原 `choose_flexible` 是历史单账本开发版本。修正 ALL 使用 `flexible_matched.py` 和 `matched_all.py`。主测试只保存每场景前四次重复、200 轮间隔的诊断路径，不存在全部 96 次重复的逐轮原始轨迹。

C16：复制整个 `experiments/ccp_frozen/` 到独立运行目录并进入。下面使用与原分析器匹配的 40 个分片名：

```powershell
foreach ($scenario in 0..9) {
    foreach ($offset in @(0, 16, 32, 48)) {
        python -X utf8 run_study.py --stage test --scenario $scenario --rep 16 --offset $offset --out "test-s$scenario-r$offset" --policies test-policies-frozen.json
    }
}
python -X utf8 analyze.py
python -X utf8 plot_results.py
```

P16：复制整个 `experiments/frontier_frozen/` 到独立运行目录并进入：

```powershell
python -X utf8 test_run.py --worker 0
python -X utf8 test_run.py --worker 1
python -X utf8 test_run.py --worker 2
python -X utf8 test_run.py --worker 3
python -X utf8 analyze_holdout.py
```

`exact_easy.py`、`exact_arrival.py` 是小型有限环境的 LP 结果重算入口；`exact_frontier.py` 提供 LP 构造/求解。其已知候选集、已知日程与终点的信息条件不同于未知环境主算法。`abm.py` 是理论 ABM 构造，不是 Shared 数值候选。`audit_checks.py` 和 `verify_api.py` 会运行额外短验证，属于诊断而非原主测试。

第一轮 CP：复制本稿到单独运行目录，进入该目录：

```powershell
python -X utf8 experiments/run_experiments.py
python -X utf8 figures/gen_fig_performance.py --figures-only
```

`run_experiments.py` 直接读取同目录 `reference_cp_ucb_aa.py`。源码中的 `proposal/.../cp_ucb_aa.py` 是来源记录，不会在运行时访问仓库外 `proposal`。

原投稿五方法 C/E：复制归档 `source/` 到独立运行目录并进入：

```powershell
python -X utf8 ce_five_algo_runner.py --output-dir outputs --seed 20260309 --R 100 --n-jobs 1 --max-checkpoints 1000 --progress off
```

该命令使用随最终配置保存的 $T=60{,}000$、两场景、五方法、100 次重复。原研究存在历史调参及文字/实现差异，归档 `metadata.json` 如实保留差异；不应宣称它是理论修复后的 F-CCP。

## 环境、开发历史与可复现边界

F17/C16/P16 原环境为 Python 3.13.5、NumPy 2.3.5、Numba 0.65.1、pandas 2.2.3、SciPy 1.17.0；作图另需 matplotlib 3.10.8，P16 代数审计另需 sympy 1.14.0。第一轮 CP 的独立版本记录在 `experiments/requirements.txt`、`results/manifest.json`，不要误当成 F17 环境。原投稿源码依赖 numpy、pandas、matplotlib，tqdm 为可选；其历史精确环境未保存，不能凭当前机器环境补造。

F17 有效开发阶段的每份冻结源码都能在单一保存目录中找到完整匹配：development/development2 对应 `source_snapshots/after_dev2/`；development3 对应 `source_snapshots/after_dev3/`；holdout 与 matched-all 对应当前 `src/`。重跑开发阶段需在工作副本中先恢复相应快照至 `src/`，再用保留协议的 `study.py --stage development` 或 `study_v2.py --stage development2/development3`（分别运行 worker 0–3）。原始编译失败记录 `development-initial-compile-failed.json` 所指的失败版 `flexible_engine.py` 未保留；其日志和哈希仍在，但不能复现那份失败源码。它没有产生计入研究的有效结果。P16 的 stale-cache 失效运行也仅作为失败历史保存，不计入有效结果。

已有逐运行计时之和约为 C16 592 秒、P16 721 秒、F17 主测试 1,408 秒及 ALL 修正 102 秒。它们受原始并发、编译、计时边界影响，既不是总耗时，也不是对当前机器的运行预算。原投稿 C/E 有 $60{,}000\times2\times5\times100$ 轮，Python 多进程实现的重跑成本明显不同，本轮未计时。

完整数值可复现指代码、协议、种子、最终统计记录和已保存路径齐全，且能在本地重新运行及重算。不同系统、Numba/NumPy 版本、浮点临界比较和随机数后端可能导致路径差别；运行时间字段本身也不会相同，因此不承诺所有平台得到逐字节相同的新 CSV。未保存的全部逐轮路径不能从端点数据反演。本轮逐字节核验针对已交付的原始材料，不等于独立证明验证或新增实验验证。
