"""Plot the frozen independent regret-baseline screen without generating prose.

Reads numerical summary CSVs and the frozen protocol. Source files are read-only.
The four displayed families are selected descriptively using the original rule;
all 17 configurations remain in the heatmap and all comparisons remain stored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

SCENARIO_LABELS = {
    "two_close": "Two close arms", "few_arrivals": "Few arrivals", "stable": "Stable benchmark",
    "successive_improvements": "Successive improvements", "burst": "Burst",
    "membership_boundary": "Membership boundary", "many_close_means": "Many close means",
    "late_improvement": "Late improvement", "rare_rewards": "Rare rewards", "ceiling": "Ceiling",
    "larger_pool": "Larger pool", "bounded_low_variance": "Bounded low variance",
}

COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]

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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    repository = Path(__file__).resolve().parents[1]
    study = repository / "experiments/regret_baseline_screen_2026-10-17"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=study / "results",
                        help="Completed baseline-screen result directory")
    parser.add_argument("--output-dir", type=Path, default=repository / "results/baseline_figures",
                        help="Destination for PDF/PNG figures and their numeric-data manifest")
    parser.add_argument("--protocol", type=Path, default=study / "protocol.json",
                        help="Frozen 17-configuration baseline protocol")
    args = parser.parse_args()
    folder = args.results_dir.resolve()
    output_dir = args.output_dir.resolve()
    protocol_path = args.protocol.resolve()
    if output_dir == folder or folder in output_dir.parents:
        parser.error("--output-dir must be outside the read-only --results-dir")
    inputs = [protocol_path] + [folder / name for name in [
        "run-info.json", "analysis-audit.json", "summary.csv",
        "paired-vs-FR.csv", "suite-summary.csv",
    ]]
    for path in inputs:
        if not path.is_file():
            raise FileNotFoundError(f"Missing frozen numerical input: {path}")
    before = {str(path): sha256(path) for path in inputs}
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    info = json.loads((folder / "run-info.json").read_text(encoding="utf-8"))
    audit = json.loads((folder / "analysis-audit.json").read_text(encoding="utf-8"))
    expected = int(protocol["expected_full_rows"])
    if not (info.get("passed") and info.get("full_prespecified_run")
            and info.get("horizon_debug") is None and audit.get("passed")
            and audit.get("formal_complete_matrix") and audit.get("rows") == expected
            and audit.get("methods") == 17 and audit.get("scenarios") == 12
            and audit.get("repetitions_per_cell") == 96):
        raise ValueError("Figures require the completed 12 x 96 x 17 baseline screen")
    protocol_hash = sha256(protocol_path)
    if audit["protocol_sha256"] != protocol_hash or info["protocol_sha256"] != protocol_hash:
        raise ValueError("Plotting protocol differs from the frozen numerical run")
    summary = pd.read_csv(folder / "summary.csv")
    paired = pd.read_csv(folder / "paired-vs-FR.csv")
    suite = pd.read_csv(folder / "suite-summary.csv")
    names = [method["name"] for method in protocol["methods"]]
    scenario_map = summary[["scenario_index", "scenario"]].drop_duplicates().sort_values("scenario_index")
    scenarios = scenario_map.scenario.tolist()
    if (len(names), len(scenarios), len(summary), len(paired), len(suite)) != (17, 12, 204, 204, 17):
        raise ValueError("Unexpected summary dimensions")
    if scenario_map.scenario_index.tolist() != list(range(12)):
        raise ValueError("Scenario indexes are not the frozen order 0,...,11")
    keys = {(scenario, name) for scenario in scenarios for name in names}
    for table in (summary, paired):
        if table.duplicated(["scenario", "method"]).any():
            raise ValueError("Duplicate numerical summary cell")
        if set(table[["scenario", "method"]].itertuples(index=False, name=None)) != keys:
            raise ValueError("Summary omits a frozen method/scenario pair")
    if not (summary.n == 96).all() or set(suite.method) != set(names):
        raise ValueError("Summary replication count or method roster differs from the protocol")
    output_dir.mkdir(parents=True, exist_ok=True)
    selected = plot_results(summary, paired, suite, protocol, scenarios, output_dir)
    after = {str(path): sha256(path) for path in inputs}
    if before != after:
        raise RuntimeError("Numerical inputs changed during plotting")
    records = {
        "input_sha256": {path.name if path.parent == folder else "protocol.json": sha256(path) for path in inputs},
        "scenario_order": scenarios, "method_order": names,
        "selected_display_families": selected,
        "display_selection_changes_inference_family": False,
        "all_configurations_in_heatmap": 17,
        "intervals": "individual two-sided paired t intervals, without multiple-comparison adjustment",
        "inference_family": "all 16 non-F-R methods x 12 scenarios remain in paired-vs-FR.csv",
        "heatmap_color_scale": "logarithmic; annotated cells are raw mean regret",
        "png_dpi": 300,
    }
    (output_dir / "plot-inputs.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output_dir": str(output_dir), "selected_display_families": selected,
                      "complete_rows": expected}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
