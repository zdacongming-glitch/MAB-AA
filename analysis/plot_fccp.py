"""Recompute numerical F-CCP summaries and the two frozen-suite figures.

Only the two terminal-outcome CSV files and their JSON protocols are read.
This script does not run policies, read manuscript sources, or generate prose.
The superseded ALL-auto-0.6 output remains a separately identified diagnostic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import t as student_t


BASES = ["UCB1", "Growing-MOSS", "MC-MOSS", "Thompson", "KL-UCB"]
PREFERENCES = [
    "F-R", "F-auto-0.1", "F-auto-0.3", "F-auto-0.6",
    "F-auto-0.9", "F-all-service-budgeted",
]
PREFERENCE_VALUES = [0, .1, .3, .6, .9, 1]
SCENARIO_LABELS = {
    "two_close": "Two close arms", "few_arrivals": "Few arrivals",
    "stable": "Stable benchmark", "successive_improvements": "Successive improvements",
    "burst": "Burst", "membership_boundary": "Membership boundary",
    "many_close_means": "Many close means", "late_improvement": "Late improvement",
    "rare_rewards": "Rare rewards", "ceiling": "Ceiling",
    "larger_pool": "Larger pool", "bounded_low_variance": "Bounded low variance",
}
METRICS = [
    "regret", "area", "service_pulls", "service_regret", "service_denials",
    "reward_projections", "service_mass", "service_attempts", "active_service_rounds",
    "final_unresolved", "final_all_unresolved", "reward_tax", "service_tax",
]
FAILURES = ["label_error", "coverage_error", "empty_intersection"]
JOINT_COMPARISONS = [
    ("F-auto-0.6", "ALL-auto-costmatched"), ("F-area", "ALL-area"),
    ("F-auto-0.6", "CCP-original"), ("F-R", "Cold-TS-unprotected"),
    ("F-auto-0.6", "F-fixed-0.6"),
    ("F-auto-0.6", "F-auto-0.6-no-service-cap"),
    ("F-auto-0.6", "F-auto-0.6-TS"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_data(data_root: Path):
    paths = [
        data_root / "protocols/holdout-freeze.json",
        data_root / "protocols/matched-all-freeze.json",
        data_root / "results/holdout-all.csv",
        data_root / "results/matched-all-all.csv",
    ]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Missing numerical input: {path}")
    freeze = json.loads(paths[0].read_text(encoding="utf-8"))
    correction = json.loads(paths[1].read_text(encoding="utf-8"))
    names = [scenario["name"] for scenario in freeze["scenarios"]]
    policies = {p["name"]: p for p in freeze["policies"] + correction["policies"]}
    methods = list(policies)
    main_data = pd.read_csv(paths[2])
    corrected = pd.read_csv(paths[3])
    data = pd.concat([main_data, corrected], ignore_index=True)
    # These are the frozen experiment dimensions, not inferred new simulations.
    if (len(names), len(main_data), len(corrected), len(data)) != (12, 27648, 1152, 28800):
        raise ValueError("Unexpected frozen-suite dimensions")
    if len(methods) != 25 or set(data.method) != set(methods) or set(data.scenario) != set(names):
        raise ValueError("Outcome identifiers do not match the frozen protocols")
    if data.duplicated(["scenario", "rep", "method"]).any():
        raise ValueError("Duplicate scenario/replication/method outcome")
    if not (data.groupby(["scenario", "method"]).size() == 96).all():
        raise ValueError("Every method/scenario cell must contain 96 repetitions")
    rep_sets = data.groupby(["scenario", "method"])["rep"].apply(lambda s: tuple(sorted(s)))
    for scenario in names:
        if rep_sets.loc[scenario].nunique() != 1:
            raise ValueError(f"Methods have different replication identifiers: {scenario}")
    return data, names, methods, paths


def compute_summaries(data, names, methods):
    records = []
    for scenario in names:
        for method in methods:
            group = data[(data.scenario == scenario) & (data.method == method)]
            row = {"scenario": scenario, "method": method, "n": len(group)}
            for key in METRICS:
                values = group[key].to_numpy()
                row.update({
                    key + "_mean": float(values.mean()),
                    key + "_se": float(values.std(ddof=1) / np.sqrt(len(values))),
                    key + "_q95": float(np.quantile(values, .95)),
                    key + "_max": float(values.max()),
                })
            for key in FAILURES:
                row[key + "_count"] = int(group[key].sum())
            busy_rounds = group.active_service_rounds.sum()
            row["proposed_busy_rate"] = float(group.service_mass.sum() / busy_rounds) if busy_rounds else 0.
            records.append(row)
    summary = pd.DataFrame(records)
    suite = summary.groupby("method").mean(numeric_only=True)

    pure = []
    for scenario in names:
        pivot = data[data.scenario == scenario].pivot(index="rep", columns="method", values="regret")
        candidate = pivot["F-R"].to_numpy()
        for baseline in BASES:
            values = pivot[baseline].to_numpy()
            difference = candidate - values
            se = difference.std(ddof=1) / np.sqrt(96)
            relaxed = candidate - 1.05 * values - 2
            pure.append(dict(
                scenario=scenario, baseline=baseline, n=96,
                F_mean=float(candidate.mean()), baseline_mean=float(values.mean()),
                delta_mean=float(difference.mean()), delta_se=float(se),
                delta_l95=float(difference.mean() - student_t.ppf(.975, 95) * se),
                delta_u95=float(difference.mean() + student_t.ppf(.975, 95) * se),
                delta_upper95_family60=float(difference.mean() + student_t.ppf(1 - .05 / 60, 95) * se),
                relaxed_upper95_family60=float(
                    relaxed.mean() + student_t.ppf(1 - .05 / 60, 95)
                    * relaxed.std(ddof=1) / np.sqrt(96)
                ),
            ))
    paired = pd.DataFrame(pure)

    joint = []
    for candidate, baseline in JOINT_COMPARISONS:
        for scenario in names:
            for key in ["regret", "area", "service_pulls"]:
                pivot = data[data.scenario == scenario].pivot(index="rep", columns="method", values=key)
                values = (pivot[candidate] - pivot[baseline]).to_numpy()
                se = values.std(ddof=1) / np.sqrt(96)
                joint.append(dict(
                    candidate=candidate, baseline=baseline, scenario=scenario, metric=key,
                    delta_mean=float(values.mean()), se=float(se),
                    lower95=float(values.mean() - student_t.ppf(.975, 95) * se),
                    upper95=float(values.mean() + student_t.ppf(.975, 95) * se),
                ))
    failure_records = data[(data[FAILURES] > 0).any(axis=1)]
    return summary, suite, paired, pd.DataFrame(joint), failure_records


def draw_figures(paired, suite, names, output_dir: Path):
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9,
        "axes.spines.top": False, "axes.spines.right": False,
        "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.bbox": "tight",
    })
    values = paired[paired.baseline == "Thompson"].set_index("scenario").loc[names]
    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    yy = np.arange(len(names))
    ax.errorbar(
        values.delta_mean, yy,
        xerr=np.vstack((values.delta_mean - values.delta_l95, values.delta_u95 - values.delta_mean)),
        fmt="o", color="#24638a", ecolor="#658ca3", capsize=3, markersize=4,
    )
    ax.axvline(0, color=".4", lw=.8)
    ax.set_yticks(yy, [SCENARIO_LABELS[name] for name in names])
    ax.invert_yaxis()
    ax.set_xlabel("F-R minus Thompson: cumulative dynamic regret")
    ax.grid(axis="x", alpha=.2)
    fig.tight_layout()
    fig.savefig(output_dir / "reward-paired.pdf")
    fig.savefig(output_dir / "reward-paired.png", dpi=210)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.7, 4.6))
    xs = [suite.loc[method, "regret_mean"] for method in PREFERENCES]
    ys = [suite.loc[method, "area_mean"] / 1000 for method in PREFERENCES]
    ax.plot(xs, ys, "o-", color="#24638a", lw=1.1, markersize=5,
            label=r"F-CCP, $\beta_C=1$ (inactive at $\lambda=0$)")
    offsets = [(6, 5), (5, 6), (5, 5), (-40, 12), (7, -4), (-28, -17)]
    for x, y, preference, offset in zip(xs, ys, PREFERENCE_VALUES, offsets):
        ax.annotate(r"$\lambda=" + str(preference) + "$", (x, y),
                    xytext=offset, textcoords="offset points", fontsize=8)
    for method, marker, color, label in [
        ("F-area", "*", "#bc6b23", r"F-area, $\beta_C=\infty$"),
        ("ALL-auto-costmatched", "s", "#8c4662", "ALL-auto-costmatched"),
        ("CCP-original", "D", "#7c7c39", "CCP-original"),
        ("ALL-area", "^", "#777777", "ALL-area"),
    ]:
        ax.scatter([suite.loc[method, "regret_mean"]], [suite.loc[method, "area_mean"] / 1000],
                   marker=marker, color=color, s=68 if marker == "*" else 38, label=label, zorder=3)
    ax.set_xlabel("Cumulative dynamic regret")
    ax.set_ylabel(r"Cumulative unresolved arm-time / $10^3$")
    ax.grid(alpha=.17)
    ax.legend(fontsize=8, loc="upper right", frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "preference-tradeoff.pdf")
    fig.savefig(output_dir / "preference-tradeoff.png", dpi=210)
    plt.close(fig)


def main():
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=repository / "experiments/fccp_frozen",
                        help="Frozen data directory containing protocols/ and results/")
    parser.add_argument("--output-dir", type=Path, default=repository / "results/fccp_reanalysis",
                        help="Destination for the numerical CSV summaries and figures")
    args = parser.parse_args()
    data_root = args.data_root.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir == data_root or data_root in output_dir.parents:
        parser.error("--output-dir must be outside the frozen --data-root directory")
    data, names, methods, inputs = load_data(data_root)
    before = {str(path.relative_to(data_root)): sha256(path) for path in inputs}
    summary, suite, paired, joint, failures = compute_summaries(data, names, methods)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_dir / "full-results-recomputed.csv", index=False)
    paired.to_csv(output_dir / "pure-reward-paired-recomputed.csv", index=False)
    joint.to_csv(output_dir / "joint-paired-recomputed.csv", index=False)
    suite[["regret_mean", "area_mean", "service_pulls_mean", "service_denials_mean",
           "final_unresolved_mean"]].to_csv(output_dir / "equal-scenario-means.csv")
    failures.to_csv(output_dir / "all-failure-records.csv", index=False)
    draw_figures(paired, suite, names, output_dir)
    after = {str(path.relative_to(data_root)): sha256(path) for path in inputs}
    if before != after:
        raise RuntimeError("Frozen inputs changed during reanalysis")
    record = {
        "source_sha256": before, "records": len(data), "scenarios": len(names),
        "method_ids": len(methods), "replications_per_cell": 96,
        "summary_rows": len(summary), "pure_reward_paired_rows": len(paired),
        "joint_paired_rows": len(joint), "failure_records": len(failures),
        "negative_reward_mean_differences": int((paired.delta_mean < 0).sum()),
        "negative_family60_upper_endpoints": int((paired.delta_upper95_family60 < 0).sum()),
        "negative_relaxed_family60_upper_endpoints": int((paired.relaxed_upper95_family60 < 0).sum()),
        "scenarios_with_all_five_mean_differences_negative": int((paired.groupby("scenario").delta_mean.max() < 0).sum()),
        "F_R_mean_regret": float(suite.loc["F-R", "regret_mean"]),
        "Thompson_mean_regret": float(suite.loc["Thompson", "regret_mean"]),
        "status": "recomputed from frozen terminal outcomes; no new simulations",
        "confidence_intervals": "individual paired t intervals; reward family60 endpoints use one-sided Bonferroni adjustment",
        "tradeoff_points": "equal-weight means of 12 scenarios; connected preferences do not estimate an optimal frontier",
        "superseded_diagnostic": "ALL-auto-0.6 is retained separately; ALL-auto-costmatched is its corrected primary comparator",
    }
    (output_dir / "reanalysis-summary.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output_dir": str(output_dir), **record}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
