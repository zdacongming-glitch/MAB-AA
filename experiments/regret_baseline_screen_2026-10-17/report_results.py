"""Render the completed, formally checked regret screen; never run policies.

This helper is deliberately outside runner.source_fingerprint. It refuses to
read a partial run and never changes runtime code, the protocol, or manuscripts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SCENARIO_LABELS = {
    "two_close": "Two close arms", "few_arrivals": "Few arrivals", "stable": "Stable benchmark",
    "successive_improvements": "Successive improvements", "burst": "Burst",
    "membership_boundary": "Membership boundary", "many_close_means": "Many close means",
    "late_improvement": "Late improvement", "rare_rewards": "Rare rewards", "ceiling": "Ceiling",
    "larger_pool": "Larger pool", "bounded_low_variance": "Bounded low variance",
}
COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def markdown_table(headers, rows):
    def clean(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    return "\n".join(["| " + " | ".join(map(clean, headers)) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"] +
                     ["| " + " | ".join(map(clean, row)) + " |" for row in rows])


def mean_se(row):
    return f"{row['mean']:.2f} ({row['mcse']:.2f})"


def export_figure(fig, basename):
    fig.savefig(basename.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(basename.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_results(summary, paired, suite, protocol, scenarios, figures):
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
        "pdf.fonttype": 42, "ps.fonttype": 42, "figure.dpi": 150, "savefig.dpi": 300,
        "legend.frameon": False, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False,
    })
    names = [m["name"] for m in protocol["methods"]]
    data = summary.pivot(index="method", columns="scenario", values="mean").loc[names, scenarios].to_numpy()
    if np.any(data <= 0):
        raise RuntimeError("Logarithmic heatmap requires positive scenario mean regrets")
    cmap = LinearSegmentedColormap.from_list("OkabeItoSequential", ["#FFFFFF", "#56B4E9", "#0072B2"])
    fig, ax = plt.subplots(figsize=(15.2, 9.0))
    norm = LogNorm(vmin=float(data.min()), vmax=float(data.max()))
    im = ax.imshow(data, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(np.arange(len(scenarios)), [SCENARIO_LABELS[s] for s in scenarios], rotation=42, ha="right")
    ax.set_yticks(np.arange(len(names)), names)
    ax.set_title("Cumulative dynamic regret: all 17 frozen configurations, 96 paired replications", pad=14)
    for i in range(len(names)):
        for j in range(len(scenarios)):
            ax.text(j, i, f"{data[i, j]:.1f}", ha="center", va="center", fontsize=8,
                    color="white" if norm(data[i, j]) > .72 else "#111111")
    fr = names.index("F-R")
    ax.add_patch(Rectangle((-.5, fr - .5), len(scenarios), 1, fill=False, linewidth=2.0, edgecolor="#D55E00"))
    ax.get_yticklabels()[fr].set_color("#D55E00")
    ax.get_yticklabels()[fr].set_fontweight("bold")
    ax.set_xticks(np.arange(-.5, len(scenarios), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(names), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=.7)
    ax.tick_params(which="minor", bottom=False, left=False)
    fig.colorbar(im, ax=ax, pad=.015, fraction=.03, label="Mean regret (logarithmic color scale; lower is better)")
    fig.text(.11, .015, "Cell labels are raw means, not logarithms. Row order follows protocol.json. All methods have zero certification pulls.", fontsize=9)
    fig.subplots_adjust(bottom=.24, left=.16, right=.92, top=.93)
    export_figure(fig, figures / "mean_regret_heatmap")

    # Rank new algorithm families only for presentation. BL beta=1 is the fixed
    # display representative; selecting the best beta after seeing results would
    # contradict the protocol. All variants remain in the heatmap and tables.
    new_methods = [m for m in protocol["methods"] if m["kind"] != "reference"]
    eligible = [m["name"] for m in new_methods if m["kind"] != "BL-MOSS-countcap-P" or float(m["param0"]) == 1.]
    ranked = suite[suite.method.isin(eligible)].sort_values(["equal_scenario_mean_ratio_to_FR", "method"]).method.head(4).tolist()
    selected = [name for name in names if name in ranked]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharey=True)
    for index, (name, ax) in enumerate(zip(selected, axes.flat)):
        p = paired[paired.method == name].set_index("scenario").loc[scenarios]
        y = np.arange(len(scenarios))
        center = p.paired_difference.to_numpy()
        err = np.stack([center - p.ci95_low.to_numpy(), p.ci95_high.to_numpy() - center])
        ax.axvline(0, color="#555555", linewidth=1, linestyle="--")
        ax.errorbar(center, y, xerr=err, fmt="o", capsize=3, color=COLORS[index], markersize=4.5, linewidth=1.3)
        ax.set_yticks(y, [SCENARIO_LABELS[s] for s in scenarios])
        ax.set_ylim(len(scenarios) - .5, -.5)
        ax.set_title(name)
        ax.set_xlabel("Mean regret difference: baseline minus F-R")
        ax.grid(axis="x", alpha=.18)
        ax.tick_params(labelleft=True)
    fig.suptitle("Four strongest added families by descriptive mean scenario ratio", y=.985)
    fig.text(.11, .015, "Points: paired mean differences; bars: unadjusted two-sided 95% t intervals. Negative values favor the baseline.\n"
             "Families are selected for display after screening; inference retains all 16 x 12 comparisons. BL display representative: beta = 1.", fontsize=9)
    fig.subplots_adjust(left=.17, right=.97, top=.93, bottom=.105, wspace=.70, hspace=.34)
    export_figure(fig, figures / "strongest_added_paired_differences")
    return selected


def generate(folder, protocol_path=None, report_path=None):
    folder = Path(folder).resolve()
    protocol_path = Path(protocol_path).resolve() if protocol_path else ROOT / "protocol.json"
    report_path = Path(report_path).resolve() if report_path else ROOT / "REPORT.md"
    # Validate completion before opening result matrices. A partial or debug run
    # cannot accidentally produce an apparently final report.
    info = json.loads((folder / "run-info.json").read_text(encoding="utf-8"))
    audit = json.loads((folder / "analysis-audit.json").read_text(encoding="utf-8"))
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    expected = int(protocol["expected_full_rows"])
    if not (info.get("passed") and info.get("full_prespecified_run") and info.get("horizon_debug") is None and
            audit.get("passed") and audit.get("formal_complete_matrix") and audit.get("rows") == expected and
            audit.get("methods") == 17 and audit.get("scenarios") == 12 and audit.get("repetitions_per_cell") == 96):
        raise RuntimeError("Only the completed, formally analyzed 12 x 96 x 17 screen can be reported")
    if audit["protocol_sha256"] != sha(protocol_path) or info["protocol_sha256"] != sha(protocol_path):
        raise RuntimeError("Report protocol differs from the frozen run")
    summary = pd.read_csv(folder / "summary.csv")
    paired = pd.read_csv(folder / "paired-vs-FR.csv")
    suite = pd.read_csv(folder / "suite-summary.csv")
    historical = pd.read_csv(folder / "historical-reference-check.csv")
    raw = pd.read_csv(folder / "runs-all.csv")
    original = json.loads((ROOT.parent / "fccp_frozen/protocols/holdout-freeze.json").read_text())
    scenarios = [s["name"] for s in original["scenarios"]]
    names = [m["name"] for m in protocol["methods"]]
    expected_keys = {(s, r, m) for s in scenarios for r in range(96) for m in names}
    if len(raw) != expected or set(raw[["scenario", "rep", "method"]].itertuples(index=False, name=None)) != expected_keys:
        raise RuntimeError("Raw result matrix is incomplete or stale")
    if len(summary) != 12 * 17 or len(paired) != 12 * 17 or len(suite) != 17 or len(historical) != 6:
        raise RuntimeError("Derived tables are incomplete")
    figures = ROOT / "figures"
    figures.mkdir(exist_ok=True)
    selected = plot_results(summary, paired, suite, protocol, scenarios, figures)
    environment = json.loads((folder / "environment.json").read_text(encoding="utf-8"))
    cases = markdown_table(["场景", "T", "已到达臂数", "奖励类型"],
        [[SCENARIO_LABELS[s["name"]], s["T"], len(s["means"]), s["kind"]] for s in original["scenarios"]])
    ranked = suite.sort_values("equal_scenario_mean_ratio_to_FR")
    overview_rows = []
    for row in ranked.to_dict("records"):
        overview_rows.append([row["method"], f"{row['mean_scenario_regret']:.2f} ({row['mean_regret_mcse']:.2f})",
            f"{row['equal_scenario_mean_ratio_to_FR']:.3f}", f"{row['mean_paired_difference']:.2f}",
            f"[{row['ci95_low']:.2f}, {row['ci95_high']:.2f}]", int(row["scenarios_lower_mean"]),
            f"{int(row['scenarios_familywise_lower'])} / {int(row['scenarios_familywise_higher'])}"])
    overview = markdown_table(["配置", "场景等权平均 regret (MCSE)", "场景平均比值 / F-R", "平均配对差值", "平均差值95%区间", "均值低于F-R场景数", "Bonferroni更低/更高场景数"], overview_rows)
    lower = ranked[(ranked.method != "F-R") & (ranked.mean_paired_difference < 0)]
    lower_names = "、".join(lower.method.tolist()) if len(lower) else "无"
    conclusion = (f"按场景等权平均比值排序，最低配置是 **{ranked.iloc[0].method}**。"
                  f"按原始 regret 的场景等权均值计算，低于 F-R 的其他配置为：{lower_names}。"
                  "这些是本组固定环境上的描述性比较，不能推出对任意到达环境的支配关系。")
    exceptions = paired[(paired.method != "F-R") & (paired.simultaneous95_high < 0)].sort_values(["scenario_index", "method"])
    exception_table = markdown_table(["场景", "比F-R更低的方法", "方法均值", "F-R均值", "配对差值", "Bonferroni 95%区间"],
        [[SCENARIO_LABELS[r.scenario], r.method, f"{r.mean_regret:.2f}", f"{r.reference_mean:.2f}",
          f"{r.paired_difference:.2f}", f"[{r.simultaneous95_low:.2f}, {r.simultaneous95_high:.2f}]"] for r in exceptions.itertuples(index=False)])
    tail_fr = summary[summary.method == "F-R"]
    tail_imed = summary[summary.method == "IMED"]
    limitations_upfront = ("**F-R没有逐场景占优，也没有尾部占优。** 下表列出经完整192项Bonferroni校正后仍低于F-R的配置—场景组合。"
        f"此外，F-R的各场景95%分位数平均为{tail_fr.quantile95.mean():.2f}，IMED为{tail_imed.quantile95.mean():.2f}；"
        f"各场景最差10次均值的平均分别为{tail_fr.upper10_mean.mean():.2f}和{tail_imed.upper10_mean.mean():.2f}。"
        "F-R的平均收益优势伴随更大的随机波动，这一点应与平均值一并解释。")
    full_means = []
    indexed = summary.set_index(["method", "scenario"])
    for start in (0, 6):
        subset = scenarios[start:start + 6]
        full_means.append(markdown_table(["方法"] + [SCENARIO_LABELS[s] for s in subset],
            [[m] + [mean_se(indexed.loc[(m, s)]) for s in subset] for m in names]))
    tail_rows = []
    for name in names:
        d = summary[summary.method == name]
        tail_rows.append([name, f"{d.quantile95.mean():.2f}", f"{d.upper10_mean.mean():.2f}", f"{d['max'].max():.2f}"])
    tails = markdown_table(["配置", "各场景95%分位数的平均", "各场景最差10次均值的平均", "全部1152次最大regret"], tail_rows)
    history = markdown_table(["原参考方法", "核对次数", "最大绝对差", "绝对差大于1e-9次数"],
        [[r.method, int(r.n), f"{r.max_absolute_difference:.3g}", int(r.differences_above_1e_9)] for r in historical.itertuples(index=False)])
    history_conclusion = ("6个参考方法的全部6912个重跑终点均在1e-9容差内吻合原冻结结果。" if int(historical.differences_above_1e_9.sum()) == 0
                          else f"共有{int(historical.differences_above_1e_9.sum())}个参考终点与原结果相差超过1e-9；比较全部使用本轮重新配对运行的F-R，不混用历史均值。")
    bl = raw[raw.method.isin(["BL-MOSS-P0.5", "BL-MOSS-P1.0"])].pivot(index=["scenario", "rep"], columns="method", values="action_sha256")
    same_bl = bool((bl["BL-MOSS-P0.5"] == bl["BL-MOSS-P1.0"]).all())
    cap_rows = [[SCENARIO_LABELS[s["name"]], s["T"], len(s["means"])] + [math.ceil(s["T"] ** (1 / (1 + 2 * b))) for b in (.5, 1., 2.)] for s in original["scenarios"]]
    caps = markdown_table(["场景", "T", "总臂数", "beta=.5 接受上限", "beta=1 接受上限", "beta=2 接受上限"], cap_rows)
    bl_text = ("beta=.5 与 beta=1 的全部1152组动作哈希完全一致。" if same_bl else "beta=.5 与 beta=1 的动作哈希不完全一致，须进一步核查，不能宣称二者重复。")
    params = markdown_table(["配置", "算法族", "固定参数", "决策信息"],
        [[m["name"], "原冻结参考规则" if m["kind"] == "reference" else m["kind"],
          "沿用holdout-freeze.json" if m["kind"] == "reference" else ", ".join(f"p{i}={m.get('param' + str(i), 0)}" for i in range(3)), m["information"]] for m in protocol["methods"]])
    contracts = "\n\n".join(f"- **{key}**：{value}" for key, value in protocol["method_contracts"].items())
    links = "\n\n".join(f"- [{key} 原文]({url})" for key, url in protocol["source_urls"].items())
    report = f"""# 独立 regret 基准筛查报告

{conclusion}

## 实验范围与完整性

本轮只比较 cumulative dynamic regret，目标方法是 F-CCP 的纯收益配置 F-R。全部方法的认证采样次数均为零；没有比较未决面积，也未修改论文。共12个原场景、每场景96个配对重复、17个配置，合计 **{expected:,}次完整运行**。其中包括5个原基准、F-R，以及9个新增算法族；BL-MOSS的3个固定参数配置属于同一算法族。

正式分析已逐格检查 scenario × rep × method 的完整集合、rep=0,...,95、原始T与臂数、真实采样次数、无重复无错误行，以及相同环境与随机数配对。总壁钟时间为{info['elapsed_seconds'] / 60:.2f}分钟；运行环境为Python {environment['python']}、NumPy {environment['numpy']}、Numba {environment['numba']}。

{cases}

## 核心比较

下表差值统一为“基准方法减F-R”；负值表示该基准的regret较低。原始regret先对每个场景求96次均值，再对12个场景等权平均。比值则先对各场景计算“方法均值/F-R均值”，再等权平均；两种摘要不能互换。不同场景的T、间隙和奖励分布不同，不把该摘要解释为普遍最优排名。

{overview}

MCSE是Monte Carlo标准误。每场景配对差值使用双侧95% Student t区间；同时提供对16个非F-R配置×12个场景、共192项比较的Bonferroni区间。上表最后一列按这一完整比较族统计，未因为展示子集而减少校正范围。平均差值区间属于描述性的总体摘要，使用分层配对方差与保守自由度；它没有对17个总体摘要另做多重校正。

{limitations_upfront}

{exception_table}

## 全部场景均值与标准误

每格为mean (MCSE)，方法顺序沿用预先冻结的protocol.json。

{full_means[0]}

{full_means[1]}

## 尾部表现

{tails}

每个场景只有96次重复，95%分位数是样本分位数；“最差10次”取该场景96次结果中最大的10个。上述量用于发现偶发高regret，不能作为尾概率保证。完整逐场景分位数、最大值和未采样臂数保留在summary.csv，逐次结果保留在runs-all.csv。

## 与原冻结实验的对应

{history_conclusion}

{history}

在扩展实验之前，已对12个场景×6个原参考方法的第0次重复、完整T，核验省略报告计算后的runner与原production simulate_dual：逐次动作、终点计数、真实统计量、regret路径和预算账本一致。此次比较仍重新运行全部原参考方法，不从旧表直接拼接新方法结果。

## 配对、随机种子与参数

奖励种子基数是{original['reward_seed']}，策略种子基数是{original['policy_seed']}。第s个场景、第r次重复的奖励和策略种子分别加上10000*s+r。批内均值置换使用奖励种子基数+50000000+10000*s+r。每个scenario-rep只生成一次完整的“臂×原始T”潜在奖励矩阵，所有方法读取同一矩阵，每个臂按自己的累计拉取次数索引。共享的是潜在奖励流；随机算法共享数值种子不意味着相同随机动作。

原Bernoulli和two-point生成机制、全部均值、到达时刻、批内置换均未改变。所有方法只看到既有观测、当前时刻和已到达臂的信息；BL-MOSS另知T和固定假设beta，信息差已明示。没有按本轮性能调整参数或只保留较好的BL版本。

{params}

### BL-MOSS参数版本的关系

BL-MOSS接受上限为ceil(T^(1/(1+2*beta)))。

{caps}

{bl_text} 在本组小臂池中，beta=.5和beta=1的接受上限均超过最终臂数，均退化为接受全部已到达臂的同一已知T-MOSS规则。它们不算两份独立证据。beta=2的上限为7，会拒绝后续到达序号超过上限的臂。保留3版用于说明这一敏感性，不能事后选择最有利参数作为BL-MOSS唯一结果。

## 图形

![全部配置的regret均值](figures/mean_regret_heatmap.png)

图1色阶采用对数尺度，格内数字是原始regret均值。橙色框标出F-R，所有配置均保留。

![新增算法的分场景配对差值](figures/strongest_added_paired_differences.png)

图2展示按场景平均比值选择的4个新增算法族：{'、'.join(selected)}。这是结果后的展示筛选，不是新的检验集合；BL若入选，固定使用beta=1作为展示代表。误差线为每场景未校正95%配对区间，192项比较的Bonferroni结论仍以完整paired-vs-FR.csv为准。两图同时提供矢量PDF和300dpi PNG。

## 理论适用边界与结论范围

- 当前availability只增不减，是sleeping bandit的特殊可用集合。一般sleeping算法在此可以运行，但其逐臂sleeping comparator不等于本文每时刻最好已到达臂的dynamic comparator；不能直接移植regret上界。
- AUER与原UCB1属于同一UCB类，区别包括原文探索常数。本轮新增的是忠实对照配置，不能把它视为另一项方法创新。
- BL-MOSS原分析含到达尾部及逐轮到达假设。本轮采用明示的批量到达序号截断适配，beta=.5、1、2只是事先固定的假设值，不是这些确定性场景已满足的真实尾指数。已知T也是额外信息。
- IMED和empirical-KL-UCB按实际观测support计算有界分布Dinf；本套每臂最多两点支持，当前精确实现专用于这一条件，不应宣称支持任意多点奖励分布。
- Bayes-UCB及原TS在Bernoulli场景按Beta更新；在有界非Bernoulli场景使用分数计数只是明示的采样适配，不宣称其为正确Bernoulli后验。UCB-V采用原论文实验参数，不能援引要求严格大于1的探索常数条件。
- 本次是对已经查看过的原测试集进行回顾性筛查，新增规则和参数在新性能运行前冻结，仍不构成新的独立holdout。配对区间反映给定场景的Monte Carlo不确定性，不覆盖场景选择或方法展示选择。

### 固定实现约定

{contracts}

### 原始算法来源

{links}

## 复核与复现文件

- protocol.json：事前冻结的场景来源、17个配置、参数、信息条件和来源链接。
- runner.py、new_policies.py、sb_exp3.py：冻结执行入口及算法实现。
- results/run-info.json、settings-audit.json：完整运行、环境与原设置记录。
- results/runs-all.csv、runs-00.csv至runs-11.csv：所有逐次regret、计数、潜在流哈希和动作哈希。
- results/summary.csv、paired-vs-FR.csv、suite-summary.csv、historical-reference-check.csv：全部描述统计、配对区间和原结果核对。
- results/paths-00.npz至paths-11.npz：每方法前4次重复、每200轮记录的regret路径。
- audit/reference-equivalence.json、analysis-synthetic-check.json：原选择等价核验及独立分析器合成测试。
- analyze.py、report_results.py：完成矩阵的分析和本报告/图形生成器。

在本目录运行：`python analyze.py results --protocol protocol.json`，随后`python report_results.py results --protocol protocol.json`。完整实验入口为`python runner.py --protocol protocol.json --output results-new --workers 8`；请使用新的输出目录保存独立重跑，避免覆盖本次结果。

协议SHA256：`{sha(protocol_path)}`。冻结运行源payload SHA256：`{audit['source_payload_sha256']}`。
"""
    if re.search(r"\\[\(\)\[\]]", report):
        raise RuntimeError("Generated Markdown contains forbidden backslash math delimiters")
    report_path.write_text(report, encoding="utf-8")
    inputs = [protocol_path] + [folder / name for name in ("run-info.json", "analysis-audit.json", "runs-all.csv", "summary.csv", "paired-vs-FR.csv", "suite-summary.csv", "historical-reference-check.csv", "environment.json")]
    outputs = [report_path] + sorted(figures.glob("*.png")) + sorted(figures.glob("*.pdf"))
    manifest = dict(passed=True, inputs={str(p.relative_to(ROOT)): sha(p) for p in inputs},
        outputs={str(p.relative_to(ROOT)): sha(p) for p in outputs}, generator_sha256=sha(__file__),
        selected_display_families=selected, display_selection_changes_inference_family=False,
        identical_BL05_BL1_actions=same_bl, complete_rows=expected, figure_skill="academic-plotting", png_dpi=300)
    (ROOT / "report-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(dict(report=str(report_path), selected=selected, rows=expected), ensure_ascii=False, indent=2))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", nargs="?", type=Path, default=ROOT / "results")
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    generate(args.folder, args.protocol, args.report)
