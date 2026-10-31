#!/usr/bin/env python3
"""Plot stored final-validation contrasts; never recompute estimates or CIs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np

SCRIPT = Path(__file__).resolve()
COLUMNS = (("f17", "IMED"), ("f17", "Empirical-KL-UCB"),
           ("adaptive", "IMED"), ("adaptive", "Empirical-KL-UCB"))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_stage(root, stage):
    folder = root / (stage + "-validation")
    config_path = folder / "config.json"
    contrast_path = folder / "parameter_analysis/paired_contrasts.csv"
    if not config_path.is_file() or not contrast_path.is_file():
        raise FileNotFoundError("Wait for the completed final-validation files: " + str(folder))
    fingerprints = {path.relative_to(root).as_posix():sha256(path)
                    for path in (config_path, contrast_path)}
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    declared = {tuple(task.get("diagnostics", {}).get("primary_candidate_ids", []))
                for task in config["tasks"]}
    if len(declared) != 1 or len(next(iter(declared))) != 2:
        raise ValueError("Expected exactly two frozen primary candidates")
    candidates = {}
    for name in next(iter(declared)):
        spec = config["methods"][name]
        params = spec["params"]
        coefficient = float(params["log_coefficient"])
        if (spec["family"] != "src_kl" or float(spec["beta_r"]) != 32
                or float(spec["preference"]) != 0 or float(params["cap_multiplier"]) != 8192
                or coefficient not in (.5, 1.)):
            raise ValueError("The overview is restricted to the two final fixed specifications")
        candidates[coefficient] = name
    if set(candidates) != {.5, 1.}:
        raise ValueError("Missing the frozen c=.5 or c=1 candidate")
    layouts = {layout["id"]:layout for layout in config["layouts"]}
    tasks = [task for task in config["tasks"] if layouts[task["layout_id"]]["group"] in ("f17", "adaptive")]
    cells = {(task["layout_id"], task["law"]) for task in tasks}
    repetitions = {cell:[] for cell in cells}
    for task in tasks:
        repetitions[task["layout_id"], task["law"]].append(int(task["rep"]))
    reps = 2 if stage == "original" else 4
    if len(cells) != 384 or any(sorted(values) != list(range(reps)) for values in repetitions.values()):
        raise ValueError("Overview scope must be 384 F17/adaptive cells with the frozen replications")
    horizons = sorted({int(layouts[task["layout_id"]]["T"]) for task in tasks})
    if stage == "scaled" and horizons != [400]:
        raise ValueError("Scaled overview must use the T400 derived settings")
    with contrast_path.open(encoding="utf-8-sig", newline="") as stream:
        contrasts = list(csv.DictReader(stream))
    records = []
    for coefficient in (.5, 1.):
        name = candidates[coefficient]
        for group, baseline in COLUMNS:
            found = [row for row in contrasts if row["candidate"] == name
                     and row["group"] == group and row["comparator"] == baseline]
            if len(found) != 1:
                raise ValueError("Missing or duplicated stored primary contrast")
            row = found[0]
            if (row["primary"].lower() not in ("true", "1") or int(float(row["family_size"])) != 8
                    or not math.isclose(float(row["confidence"]), 1-.05/8, abs_tol=1e-12)):
                raise ValueError("Expected the stored Bonferroni-eight primary interval")
            value, low, high = (float(row[field]) for field in ("percent_change", "percent_ci_low", "percent_ci_high"))
            if not all(math.isfinite(item) for item in (value, low, high)) or not low <= value <= high:
                raise ValueError("Invalid stored percentage estimate or interval")
            records.append(dict(candidate=name, log_coefficient=coefficient, group=group,
                baseline=baseline, percent_change=value, percent_ci_low=low, percent_ci_high=high,
                interval_includes_zero=low <= 0 <= high))
    return dict(stage=stage, records=records, candidates=candidates, input_sha256=fingerprints,
        scope=dict(groups=["f17", "adaptive"], layouts=len({task["layout_id"] for task in tasks}),
                   cells=len(cells), paired_replications_per_cell=reps, horizons=horizons,
                   full_original_settings=stage == "original", other_density_groups_excluded=True,
                   aggregation="Stored macro percentages, with equal environmental-cell weights",
                   point_estimate_only_color=True, primary_family_size=8,
                   interval="Stored Bonferroni-8 simultaneous 95% intervals; no recomputation"))


def number(value, sign=False):
    if value == 0:
        return "0.0"
    return format(value, "+.1f" if sign else ".1f")


def draw(root, stage, color_limit):
    records = stage["records"]
    matrix = np.array([row["percent_change"] for row in records]).reshape(2, 4)
    cmap = LinearSegmentedColormap.from_list("regret_change", ["#23639B", "#F7FAFC", "#BF563E"])
    style = {"font.family":"DejaVu Sans", "font.size":10, "pdf.fonttype":42,
             "ps.fonttype":42, "svg.fonttype":"none", "axes.unicode_minus":False}
    with plt.rc_context(style):
        fig = plt.figure(figsize=(9.6, 4.3))
        ax = fig.add_axes([.245, .29, .62, .45])
        heat = ax.imshow(matrix, cmap=cmap, norm=TwoSlopeNorm(vmin=-color_limit, vcenter=0, vmax=color_limit),
                         aspect="auto", interpolation="nearest")
        ax.set_xticks(range(4), ["F17 / IMED", "F17 / EKL", "Adaptive / IMED", "Adaptive / EKL"], fontsize=10)
        ax.xaxis.tick_top()
        ax.tick_params(axis="both", length=0, pad=10)
        ax.set_yticks(range(2), ["SRC-KL, c=0.5\n(a=8192, beta_R=32)", "SRC-KL, c=1\n(a=8192, beta_R=32)"], fontsize=10)
        ax.set_xticks(np.arange(-.5, 4, 1), minor=True)
        ax.set_yticks(np.arange(-.5, 2, 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=3)
        ax.tick_params(which="minor", bottom=False, left=False)
        ax.axvline(1.5, color="white", linewidth=4)
        for spine in ax.spines.values():
            spine.set_visible(False)
        for row_index in range(2):
            for column in range(4):
                record = records[row_index*4+column]
                value = record["percent_change"]
                color = "white" if abs(value) > .62*color_limit else "#14222C"
                marker = "\u2020" if record["interval_includes_zero"] else ""
                ax.text(column, row_index-.10, number(value, sign=True)+"%"+marker,
                        ha="center", va="center", fontsize=17, fontweight="bold", color=color)
                interval = "["+number(record["percent_ci_low"], sign=True)+", "+number(record["percent_ci_high"], sign=True)+"]"
                ax.text(column, row_index+.23, interval, ha="center", va="center", fontsize=8.5, color=color)
        color_axis = fig.add_axes([.887, .29, .017, .45])
        bar = fig.colorbar(heat, cax=color_axis)
        bar.ax.tick_params(labelsize=8, length=3)
        bar.set_label("Regret change (%)", fontsize=9, labelpad=8)
        title = "Original settings" if stage["stage"] == "original" else "Derived settings (T=400)"
        fig.text(.53, .94, title, ha="center", va="center", fontsize=16, fontweight="bold")
        scope = stage["scope"]
        subtitle = (f"F17 + Adaptive: 24 layouts x 16 laws = 384 cells | "
                    f"{scope['paired_replications_per_cell']} paired replications per cell")
        fig.text(.53, .87, subtitle, ha="center", va="center", fontsize=10)
        fig.text(.245, .185, "Color shows point estimates only; negative means lower regret. Color does not encode significance.", fontsize=9)
        fig.text(.245, .115, "\u2020 Interval includes 0, including exact ties. Brackets: Bonferroni-8 simultaneous 95% intervals.", fontsize=8.5)
        out = root / "figures" / ("relative_regret_"+stage["stage"])
        outputs = []
        for suffix in (".png", ".pdf", ".svg"):
            path = out.with_suffix(suffix)
            fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
            outputs.append(path)
        plt.close(fig)
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=SCRIPT.parents[1])
    args = parser.parse_args(argv)
    root = args.root.resolve()
    stages = [read_stage(root, name) for name in ("original", "scaled")]
    limit = max(10., 10*math.ceil(max(abs(row["percent_change"]) for stage in stages for row in stage["records"])/10))
    (root / "figures").mkdir(exist_ok=True)
    for stage in stages:
        outputs = draw(root, stage, limit)
        for relative, fingerprint in stage["input_sha256"].items():
            if sha256(root / relative) != fingerprint:
                raise RuntimeError("Stored validation input changed during plotting")
        metadata = dict(**stage, script_sha256=sha256(SCRIPT), shared_color_limit_percent=limit,
            output_sha256={path.relative_to(root).as_posix():sha256(path) for path in outputs},
            statistic_recomputed=False)
        path = root / "figures" / ("relative_regret_"+stage["stage"]+".scope.json")
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
        print(json.dumps(dict(stage=stage["stage"], values=[row["percent_change"] for row in stage["records"]],
                             interval_includes_zero=[row["interval_includes_zero"] for row in stage["records"]]), indent=2))


if __name__ == "__main__":
    main()
