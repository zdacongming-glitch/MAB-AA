"""Frozen eight-comparison inference and figures for the FULL reward study."""
from __future__ import annotations

import csv
import gzip
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

from .full_reward import verify
from .relative_regret import _estimate
from .runner import atomic_json, sha256


def comparison(rows, candidate, comparator, family=1):
    left = rows[rows.method == candidate].set_index(["layout_id", "law", "rep"])
    right = rows[rows.method == comparator].set_index(["layout_id", "law", "rep"])
    if set(left.index) != set(right.index) or left.index.has_duplicates or right.index.has_duplicates:
        raise ValueError("comparison requires complete unique pairs")
    cells = {}
    for (layout, law), a in left.groupby(level=[0, 1]):
        a = a.sort_index()
        b = right.loc[a.index]
        cells[(layout, law)] = dict(candidate=a.regret.tolist(), comparator=b.regret.tolist(), section=str(a.group.iloc[0]))
    estimate = _estimate(cells)
    estimate.update(candidate=candidate, comparator=comparator, family_size=family)
    for stem, key in [("difference", "regret_difference"), ("percent", "percent_change")]:
        df, se, value = estimate[stem+"_df"], estimate[stem+"_mcse"], estimate[key]
        critical = student_t.ppf(1-.05/(2*family), df) if df and math.isfinite(df) else student_t.ppf(1-.05/(2*family), 1e12)
        estimate[stem+"_adjusted_ci_low"] = value-critical*se if value is not None and se is not None else None
        estimate[stem+"_adjusted_ci_high"] = value+critical*se if value is not None and se is not None else None
    estimate["interval"] = "paired cell-stratified t, Satterthwaite df; delta-method relative interval; Bonferroni "+str(family)
    return estimate


def analyze(output):
    output = Path(output)
    verify(output)
    config = json.loads((output/"config.json").read_text(encoding="utf-8"))
    if config["replications"] < 2:
        raise ValueError("runtime pilot is excluded from inferential analysis")
    protocol = config["protocol"]
    data = pd.read_csv(output/"runs.csv.gz", dtype={"action_hash": str})
    if len(data) != config["expected_runs"]:
        raise ValueError("incorrect endpoint scope")
    analysis, figures = output/"analysis", output/"figures"
    analysis.mkdir(exist_ok=True)
    figures.mkdir(exist_ok=True)
    primary = []
    for group in protocol["groups"]:
        subset = data[data.group == group]
        for baseline in protocol["primary_comparators"]:
            primary.append(dict(group=group, **comparison(subset, "FULL-R", baseline, protocol["primary_family_size"])))
    primary = pd.DataFrame(primary)
    primary.to_csv(analysis/"primary_comparisons.csv", index=False)
    means = data.groupby(["group", "method"], sort=False).agg(mean_regret=("regret", "mean"),
        worlds=("regret", "size"), maximum_observed_regret=("regret", "max"),
        mean_runtime_seconds=("runtime_seconds", "mean")).reset_index()
    means.to_csv(analysis/"method_means.csv", index=False)
    cell_means = data.groupby(["group", "layout_id", "law", "method"]).regret.agg(["mean", "std", "count"]).reset_index()
    cell_means.to_csv(analysis/"cell_means.csv", index=False)
    details = []
    for scope, columns in [("layout", ["group", "layout_id"]), ("law", ["group", "law"]),
                           ("cell", ["group", "layout_id", "law"])]:
        for keys, subset in data.groupby(columns):
            meta = dict(zip(columns, keys))
            for baseline in protocol["primary_comparators"]:
                details.append(dict(scope=scope, **meta, **comparison(subset, "FULL-R", baseline)))
    pd.DataFrame(details).to_csv(analysis/"exploratory_comparisons.csv", index=False)
    win_counts = []
    for group in protocol["groups"]:
        pivot = cell_means[cell_means.group == group].pivot(index=["layout_id", "law"], columns="method", values="mean")
        for baseline in protocol["primary_comparators"]:
            diff = pivot["FULL-R"]-pivot[baseline]
            win_counts.append(dict(group=group, comparator=baseline, lower_mean=int((diff < -1e-10).sum()),
                higher_mean=int((diff > 1e-10).sum()), ties=int((abs(diff) <= 1e-10).sum())))
    pd.DataFrame(win_counts).to_csv(analysis/"cell_win_counts.csv", index=False)
    summary = dict(scope="original F17 and adaptive; no horizon, arrival or arm compression",
        worlds=config["expected_worlds"], runs=len(data), cells=384, repetitions=config["replications"],
        primary_family_size=8, reports_evaluated=False,
        interval_scope="Monte Carlo uncertainty conditional on this fixed benchmark; approximate t and delta method",
        method_means=means.to_dict("records"), primary=primary.to_dict("records"), wins=win_counts,
        raw_sha256=sha256(output/"runs.csv.gz"))
    atomic_json(analysis/"summary.json", summary)
    plot(output, primary, means, cell_means, pd.DataFrame(details), config)
    lines = ["# FULL 原尺寸纯奖励配对实验", "",
        f"F17 与 adaptive 各 12 布局、16 分布，每单元 {config['replications']} 次新配对重复，共 {config['expected_worlds']} 个世界、{len(data)} 条轨迹。时域、臂数、到达、均值及分布参数均为原始设置。", "",
        "SRC-R、SRC-KL-R 沿用正式默认参数；未采用此前调参候选。所有方法共享按臂的观察次数索引的潜在奖励与同批标签置换。没有参数搜索或依照结果提前停止。", "",
        "只比较动态 pseudo-regret。被动报告计算对所有方法关闭；本实验不报告分类可靠性或未决面积。", "",
        "## 主要比较", "",
        "百分比 = 100 ×（FULL 平均 regret − 对照平均 regret）/ 对照平均 regret。负值有利于 FULL。单元等权；八个主比较共同采用 Bonferroni 95% 校正，百分比区间使用保留配对协方差的 delta method。", "",
        "| 组别 | 对照 | FULL regret | 对照 regret | 相对变化 | 校正区间 |", "|---|---|---:|---:|---:|---:|"]
    for r in primary.to_dict("records"):
        lines.append(f"| {r['group']} | {r['comparator']} | {r['candidate_regret']:.4f} | {r['comparator_regret']:.4f} | {r['percent_change']:+.2f}% | [{r['percent_adjusted_ci_low']:+.2f}, {r['percent_adjusted_ci_high']:+.2f}]% |")
    lines += ["", "![主比较](../figures/relative_regret.png)", "",
        "逐布局、逐分布及全部 384 单元结果见 exploratory_comparisons.csv；其区间为未作多重校正的探索性区间。总体均值优势不意味着逐单元支配。区间只描述固定测试矩阵的 Monte Carlo 误差。", "",
        "所有原始路径保留。最大观察 regret 属于样本诊断，不是尾部概率保证。该批种子与简化稿所引用的 32 次 adaptive 实验不同，未合并为同一批样本。", ""]
    (analysis/"RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def plot(output, primary, means, cell_means, details, config):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "pdf.fonttype": 42})
    figures = output/"figures"
    def save(fig, name):
        for suffix in ("png", "pdf", "svg"):
            fig.savefig(figures/(name+"."+suffix), dpi=180, bbox_inches="tight")
        plt.close(fig)
    groups = config["protocol"]["groups"]
    baselines = config["protocol"]["primary_comparators"]
    matrix = np.array([[float(primary[(primary.group == g)&(primary.comparator == b)].percent_change.iloc[0]) for g in groups] for b in baselines])
    limit = max(30., float(np.max(abs(matrix))))
    fig, ax = plt.subplots(figsize=(9, 5.8), layout="constrained")
    im = ax.imshow(matrix, cmap="RdBu_r", norm=TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit), aspect="auto")
    for i, b in enumerate(baselines):
        for j, g in enumerate(groups):
            r = primary[(primary.group == g)&(primary.comparator == b)].iloc[0]
            lo, hi = r.percent_adjusted_ci_low, r.percent_adjusted_ci_high
            star = "*" if lo > 0 or hi < 0 else ""
            color = "white" if abs(r.percent_change) > .7*limit else "#222222"
            ax.text(j, i, f"{r.percent_change:+.1f}%{star}\n[{lo:+.1f}, {hi:+.1f}]", ha="center", va="center", color=color, fontsize=12)
    ax.set(xticks=range(2), xticklabels=["F17 (192 cells)", "Adaptive (192 cells)"], yticks=range(4), yticklabels=baselines,
           title="FULL relative regret vs four controls (%)\nOriginal settings | 20 paired repeats/cell | Negative favors FULL")
    fig.colorbar(im, ax=ax, label="Relative regret change (%)")
    fig.supxlabel("Intervals: approximate familywise 95%, Bonferroni 8. * excludes zero.", fontsize=10)
    save(fig, "relative_regret")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), layout="constrained")
    colors = ["#007f86", "#4c9c45", "#9467bd", "#df7e25", "#4779b9"]
    methods = config["protocol"]["methods"]
    for ax, g in zip(axes, groups):
        table = means[means.group == g].set_index("method").loc[methods]
        bars = ax.bar(range(5), table.mean_regret, color=colors)
        ax.bar_label(bars, fmt="%.2f", padding=3)
        ax.set(xticks=range(5), xticklabels=methods, title=g.upper(), ylabel="Mean cumulative dynamic regret")
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=.2)
        ax.set_axisbelow(True)
    fig.suptitle("Original F17 and adaptive | Equal cell weights | 20 paired repeats")
    save(fig, "mean_regret")
    traces = pd.read_csv(output/"trajectories.csv.gz")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), layout="constrained")
    for ax, g in zip(axes, groups):
        for method, color in zip(methods, colors):
            vals = traces[(traces.group == g)&(traces.method == method)].groupby("fraction").regret.mean()
            ax.plot(vals.index, vals.values, label=method, color=color)
        ax.set(title=g.upper(), xlabel="Fraction of each original horizon", ylabel="Mean cumulative dynamic regret")
        ax.grid(alpha=.2)
    axes[1].legend()
    save(fig, "regret_trajectories")
    layout_ids = [x["id"] for x in config["layouts"]]
    table = details[details.scope == "layout"].pivot(index="layout_id", columns="comparator", values="percent_change").loc[layout_ids, baselines]
    fig, ax = plt.subplots(figsize=(10, 12), layout="constrained")
    im = ax.imshow(table.to_numpy(), cmap="RdBu_r", vmin=-100, vmax=100, aspect="auto")
    for i in range(len(table)):
        for j in range(len(baselines)):
            value = table.iloc[i, j]
            ax.text(j, i, f"{value:+.1f}", ha="center", va="center", fontsize=9,
                    color="white" if abs(value) > 70 else "#222222")
    ax.set(xticks=range(4), xticklabels=baselines, yticks=range(len(table)),
           yticklabels=[s.replace("adaptive__", "A: ").replace("f17__", "F: ") for s in table.index],
           title="FULL relative regret by original layout (%)\n16 laws per layout; descriptive point estimates")
    fig.colorbar(im, ax=ax, label="Change (%) | Colors clipped at +/-100; labels are untruncated")
    save(fig, "relative_regret_by_layout")
    laws = list(dict.fromkeys(t["law"] for t in config["tasks"]))
    fig, axes = plt.subplots(2, 2, figsize=(25, 19), layout="constrained")
    cells = details[details.scope == "cell"]
    for ax, baseline in zip(axes.flat, baselines):
        table = cells[cells.comparator == baseline].pivot(index="layout_id", columns="law", values="percent_change").loc[layout_ids, laws]
        im = ax.imshow(table.to_numpy(), cmap="RdBu_r", vmin=-100, vmax=100, aspect="auto")
        ax.set(xticks=range(len(laws)), xticklabels=laws, yticks=range(len(layout_ids)),
               yticklabels=[s.split("__", 1)[-1] for s in layout_ids], title="FULL vs "+baseline)
        ax.tick_params(axis="x", rotation=80, labelsize=9)
        ax.tick_params(axis="y", labelsize=9)
        ax.axhline(11.5, color="black", linewidth=1)
    fig.colorbar(im, ax=list(axes.flat), label="Relative regret (%) | Negative favors FULL; colors clipped +/-100", shrink=.7)
    fig.suptitle("All 384 original cells | 20 paired repeats | F17 above line, adaptive below")
    save(fig, "relative_regret_by_cell")
