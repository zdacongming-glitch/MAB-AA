"""Publication-exportable, cohort-separated plots of stored benchmark data."""
from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

from .analysis import _read, analyze

PALETTE = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#222222")
LINESTYLES = ("-", "--", "-.", ":")


def _float(row, key):
    value = row.get(key)
    return float(value) if value not in (None, "", "None") else None


def _safe(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value))


def _partition(rows, keys=("cohort", "group", "suite")):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row.get(k, "") for k in keys)].append(row)
    return groups


def _name_key(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _focused(methods, suite):
    fixed = ("SRC-R", "SRC-KL-R", "IMED", "Empirical-KL-UCB", "Empirical_KL_UCB",
             "Growing-MOSS", "Growing_MOSS", "ACI", "BL-MOSS-b2", "BL_MOSS_b2")
    if "joint" in suite:
        fixed = ("SRC-R", "SRC-KL-R", "SRC-L060", "SRC-KL-L060", "SRC-area", "SRC-KL-area")
    normalized = {_name_key(x): x for x in methods}
    chosen = []
    for item in fixed:
        actual = normalized.get(_name_key(item))
        if actual and actual not in chosen:
            chosen.append(actual)
    return chosen[:8]


def _style(method, index):
    if method.startswith("SRC-KL"):
        result = dict(color=PALETTE[1], linestyle="--", linewidth=1.7)
    elif method.startswith("SRC"):
        result = dict(color=PALETTE[0], linestyle="-", linewidth=1.7)
    else:
        return dict(color=PALETTE[(index + 2) % len(PALETTE)],
                    linestyle=LINESTYLES[index % len(LINESTYLES)], linewidth=1.15)
    if method.endswith("-area") or "-L" in method:
        result.update(marker="^" if method.endswith("-area") else "o", markevery=8,
                      markersize=4, markerfacecolor="white", markeredgewidth=.9)
    return result


def _caption(rows, smoke, extra=""):
    reps = [_float(row, "replications_min") for row in rows]
    reps = [x for x in reps if x is not None]
    hi = [_float(row, "replications_max") for row in rows]
    hi = [x for x in hi if x is not None]
    reptext = f"{int(min(reps))}–{int(max(hi or reps))} paired repetitions/cell" if reps else "see CSV for repetition counts"
    prefix = "SMOKE ONLY: full study not run. " if smoke else "Frozen-cell descriptive estimates. "
    return prefix + reptext + ". Cells weighted equally; bands/bars are ±1 Monte Carlo SE. " + extra


def _finish(fig, path, caption, records, plt):
    import textwrap
    fig.text(.015, .015, "\n".join(textwrap.wrap(caption, width=max(70, int(fig.get_figwidth() * 15)))),
             fontsize=7.3, va="bottom", color="#374754")
    fig.tight_layout(rect=(0, .115, 1, .97))
    outputs = []
    for suffix in ("png", "pdf", "svg"):
        destination = path.with_suffix("." + suffix)
        fig.savefig(destination, dpi=180 if suffix == "png" else None, bbox_inches="tight")
        outputs.append(str(destination.resolve()))
    records.append({"figure": path.name, "caption": caption, "files": outputs})
    plt.close(fig)
    return outputs


def _trajectory_plots(rows, folder, smoke, records, plt):
    paths = []
    for key, block in sorted(_partition(rows).items()):
        cohort, group, suite = key
        methods = _focused({r["method"] for r in block}, suite)
        if not methods:
            continue
        fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.5))
        for index, method in enumerate(methods):
            values = sorted([r for r in block if r["method"] == method], key=lambda r: float(r["t"]))
            x = [float(r["t"]) for r in values]
            for ax, metric in zip(axes, ("regret", "unresolved")):
                selected = [(a, _float(r, metric + "_mean"), _float(r, metric + "_mcse")) for a, r in zip(x, values)]
                selected = [(a, b, c) for a, b, c in selected if b is not None]
                if not selected:
                    continue
                xx, yy, se = zip(*selected)
                st = _style(method, index)
                ax.plot(xx, yy, label=method, **st)
                if all(v is not None for v in se):
                    ax.fill_between(xx, [y-s for y, s in zip(yy, se)], [y+s for y, s in zip(yy, se)],
                                    color=st["color"], alpha=.10)
        for ax, label in zip(axes, ("Cumulative dynamic regret", "Unresolved eligible arms")):
            ax.set(xlabel="Round", ylabel=label)
            ax.grid(alpha=.18)
        axes[0].legend(fontsize=7, ncol=2)
        fig.suptitle(f"{cohort} · {group} · {suite}", fontsize=11)
        cap = _caption(block, smoke, "Fixed display shortlist; every method remains in the CSV tables. Snapshot cell counts may differ across horizons.")
        paths += _finish(fig, folder / _safe("trajectory_" + "_".join(key)), cap, records, plt)
        fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.3))
        drew = False
        for index, method in enumerate(methods[:6]):
            values = sorted([r for r in block if r["method"] == method], key=lambda r: float(r["t"]))
            for ax, metric in zip(axes, ("regret_over_log_t", "regret_over_spectrum")):
                selected = [(float(r["t"]), _float(r, metric + "_mean")) for r in values]
                selected = [(x, y) for x, y in selected if y is not None]
                if selected:
                    ax.plot(*zip(*selected), label=method, **_style(method, index)); drew = True
        if drew:
            axes[0].set(xlabel="Round t > 1", ylabel="Regret / log(t)")
            axes[1].set(xlabel="Round", ylabel="Regret / arrival spectrum S(t)")
            for ax in axes:
                ax.grid(alpha=.18)
            axes[0].legend(fontsize=7, ncol=2)
            fig.suptitle(f"Descriptive normalized paths · {cohort} · {group} · {suite}", fontsize=10)
            cap = _caption(block, smoke, "R/log(t) uses checkpoints after the layout's last arrival only. No asymptotic constant is asserted for dense schedules. R/S(t) uses the current arrival spectrum; guards use its running maximum.")
            paths += _finish(fig, folder / _safe("normalized_" + "_".join(key)), cap, records, plt)
        else:
            plt.close(fig)
    return paths


def _tradeoff(rows, folder, smoke, records, plt):
    paths = []
    for key, block in sorted(_partition(rows).items()):
        if "joint" not in key[2]:
            continue
        fig, ax = plt.subplots(figsize=(8.6, 5.3))
        drew = False
        for prefix, color, style in (("SRC", PALETTE[0], "-"), ("SRC-KL", PALETTE[1], "--")):
            points, area = [], []
            for row in block:
                name = row["method"]
                if name == prefix + "-R":
                    points.append((0, row))
                elif name.startswith(prefix + "-L") and name[len(prefix)+2:].isdigit():
                    points.append((int(name[len(prefix)+2:]) / 100, row))
                elif name.lower() == prefix.lower() + "-area":
                    area.append(row)
            points.sort(key=lambda x: x[0])
            if points:
                x = [_float(r, "regret_mean") for _, r in points]
                y = [_float(r, "eta_fraction_mean") for _, r in points]
                if all(z is not None for z in x+y):
                    ex = [_float(r, "regret_mcse") for _, r in points]
                    ey = [_float(r, "eta_fraction_mcse") for _, r in points]
                    if all(z is not None for z in ex+ey):
                        ax.errorbar(x, y, xerr=ex, yerr=ey, fmt="none", ecolor=color,
                                    alpha=.55, elinewidth=.9, capsize=2)
                    ax.plot(x, y, "o", color=color, linestyle=style, label=prefix + " finite service budget")
                    for (pref, _), xx, yy in zip(points, x, y):
                        ax.annotate(f"λ={pref:g}", (xx, yy), xytext=(4, 4), textcoords="offset points", fontsize=7)
                    drew = True
            for row in area:
                xx, yy = _float(row, "regret_mean"), _float(row, "eta_fraction_mean")
                if xx is not None and yy is not None:
                    ex, ey = _float(row, "regret_mcse"), _float(row, "eta_fraction_mcse")
                    if ex is not None and ey is not None:
                        ax.errorbar([xx], [yy], xerr=[ex], yerr=[ey], fmt="none", ecolor=color,
                                    alpha=.55, elinewidth=.9, capsize=2)
                    ax.scatter([xx], [yy], marker="*", s=270 if prefix == "SRC" else 125,
                               facecolor="white" if prefix == "SRC" else color,
                               edgecolor=color if prefix == "SRC" else "black", linewidth=1.1 if prefix == "SRC" else .4,
                               label=prefix + "-area (uncapped service)")
                    drew = True
        for row in block:
            if row["method"] in _focused({r["method"] for r in block}, "reward") and not row["method"].startswith("SRC"):
                xx, yy = _float(row, "regret_mean"), _float(row, "eta_fraction_mean")
                if xx is not None and yy is not None:
                    ax.scatter([xx], [yy], marker="x", color="#777777", s=35)
                    ax.annotate(row["method"], (xx, yy), fontsize=6, xytext=(3, -8), textcoords="offset points")
        if drew:
            ax.set(xlabel="Mean cumulative dynamic regret", ylabel="Eligible arm-time unresolved fraction",
                   title=" · ".join(key))
            ax.grid(alpha=.2); ax.legend(fontsize=7, loc="best")
            cap = _caption(block, smoke, "Segments join tested preferences only. λ=1 with finite service budget is a circle; uncapped area is a separate star and is never joined as the same endpoint.")
            paths += _finish(fig, folder / _safe("tradeoff_" + "_".join(key)), cap, records, plt)
        else:
            plt.close(fig)
    return paths


def _heatmaps(rows, folder, smoke, records, plt):
    import numpy as np
    paths = []
    direct = [r for r in rows if r.get("contrast") == "direct_kl_src"]
    groups = _partition(direct, ("cohort", "group", "suite", "left", "right", "metric"))
    for key, block in sorted(groups.items()):
        if key[3] not in ("SRC-KL-R", "SRC-KL-L060", "SRC-KL-area"):
            continue
        layouts = sorted({r["layout_id"] for r in block})
        laws = sorted({r["law"] for r in block})
        if len(layouts) * len(laws) < 2:
            continue
        matrix = np.full((len(layouts), len(laws)), np.nan)
        for r in block:
            matrix[layouts.index(r["layout_id"]), laws.index(r["law"])] = float(r["difference"])
        maximum = float(np.nanmax(np.abs(matrix))) or 1
        fig, ax = plt.subplots(figsize=(max(7.2, .65*len(laws)+3), max(4.0, .28*len(layouts)+2.5)))
        raster = ax.imshow(matrix, aspect="auto", cmap="PuOr_r", vmin=-maximum, vmax=maximum)
        ax.set_xticks(range(len(laws)), laws, rotation=45, ha="right", fontsize=7)
        ax.set_yticks(range(len(layouts)), layouts, fontsize=7)
        ax.set_title(" · ".join(key[:3]) + "\n" + key[3] + " minus " + key[4] + " · " + key[5], fontsize=10)
        fig.colorbar(raster, ax=ax, label="Paired mean difference (lower is smaller cost)")
        cap = _caption(block, smoke, "Each tile is one layout × law cell; no tilewise significance claim. Missing combinations remain blank.")
        paths += _finish(fig, folder / _safe("paired_heatmap_" + "_".join(key)), cap, records, plt)
    return paths


def _facets(rows, dimension, folder, smoke, records, plt):
    import numpy as np
    paths = []
    for key, block in sorted(_partition(rows).items()):
        methods = [m for m in ("SRC-R", "SRC-KL-R", "SRC-L060", "SRC-KL-L060") if any(r["method"] == m for r in block)]
        if not methods:
            continue
        categories = sorted({r[dimension] for r in block}, key=(lambda x: float(x)) if dimension == "K" else str)
        if len(categories) < 2:
            continue
        fig, ax = plt.subplots(figsize=(max(8, len(categories)*.6), 4.6))
        width = .8/len(methods)
        x = np.arange(len(categories))
        for i, method in enumerate(methods):
            lookup = {r[dimension]: r for r in block if r["method"] == method}
            y = [_float(lookup.get(cat, {}), "regret_mean") for cat in categories]
            se = [_float(lookup.get(cat, {}), "regret_mcse") for cat in categories]
            offset = x - .4 + width/2 + i*width
            style = _style(method, i)
            ax.bar(offset, [v if v is not None else math.nan for v in y], width=width,
                   color=style["color"], hatch="//" if "KL" in method else None, label=method,
                   alpha=.9 if "L060" not in method else .48,
                   yerr=[s if s is not None else 0 for s in se], capsize=2)
        ax.set_xticks(x, categories, rotation=45 if dimension == "law" else 0,
                      ha="right" if dimension == "law" else "center", fontsize=8)
        ax.set(ylabel="Mean cumulative dynamic regret", xlabel="Final arm count" if dimension == "K" else "Reward law",
               title=" · ".join(key))
        ax.grid(axis="y", alpha=.2); ax.legend(fontsize=7, ncol=2)
        cap = _caption(block, smoke, "Law/density summaries are conditional on the fixed suite, with cohorts and source groups separate.")
        paths += _finish(fig, folder / _safe(dimension + "_" + "_".join(key)), cap, records, plt)
    return paths


def _diagnostics(rows, folder, smoke, records, plt):
    import numpy as np
    paths = []
    for key, block in sorted(_partition(rows).items()):
        chosen = _focused({r["method"] for r in block}, key[2])
        selected = [next(r for r in block if r["method"] == m) for m in chosen]
        if not selected:
            continue
        fig, axes = plt.subplots(1, 3, figsize=(12.3, 4.6))
        for ax, metric, title in zip(axes, ("service_fraction", "service_denials", "unseen_fraction"),
                                     ("Fraction of pulls used for service", "Mean service guard denials", "Fraction of final arms unseen")):
            values = [_float(r, metric + "_mean") for r in selected]
            ax.barh(np.arange(len(chosen)), [x if x is not None else math.nan for x in values],
                    color=[_style(m, i)["color"] for i, m in enumerate(chosen)],
                    hatch=None)
            ax.set_yticks(range(len(chosen)), chosen, fontsize=7)
            ax.set_title(title, fontsize=9); ax.grid(axis="x", alpha=.15)
        fig.suptitle("Diagnostics · " + " · ".join(key), fontsize=10)
        cap = _caption(block, smoke, "Guard exclusions, reward/service tax, and checkpoint hits are also retained in module_summary.csv. Unseen means zero real observations.")
        paths += _finish(fig, folder / _safe("diagnostics_" + "_".join(key)), cap, records, plt)
    return paths


def _count_plot(rows, config, folder, smoke, records, plt):
    """Only a named static two-arm layout receives an asymptotic overlay."""
    paths = []
    static_ids = {layout["id"] for layout in config.get("layouts", [])
                  if "two_close" in layout.get("name", "") and all(a.get("arrival", 1) == 1 for a in layout.get("arms", []))}
    eligible = [r for r in rows if r.get("layout_id") in static_ids and _float(r, "birth") == 1
                and r.get("method") in ("SRC-R", "SRC-KL-R")]
    for key, block in sorted(_partition(eligible, ("cohort", "group", "layout_id", "law")).items()):
        times = sorted({_float(r, "t") for r in block})
        if len(times) < 2:
            continue
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for i, method in enumerate(("SRC-R", "SRC-KL-R")):
            selected = [r for r in block if r["method"] == method]
            grouped = _partition(selected, ("t",))
            points = []
            for time, values in grouped.items():
                y = [_float(r, "n_over_log_t") for r in values]
                y = [v for v in y if v is not None]
                if y:
                    avg = sum(y)/len(y)
                    se = math.sqrt(sum((v-avg)**2 for v in y)/(len(y)*(len(y)-1))) if len(y) > 1 else None
                    points.append((float(time[0]), avg, se))
            if points:
                points.sort()
                xx, yy, se = zip(*points)
                style = _style(method, i)
                ax.plot(xx, yy, label=method + " observed n/log(t)", **style)
                if all(s is not None for s in se):
                    ax.fill_between(xx, [y-s for y,s in zip(yy,se)], [y+s for y,s in zip(yy,se)],
                                    color=style["color"], alpha=.12)
                field = "kl_count_constant" if "KL" in method else "src_count_constant"
                value = _float(selected[0], field)
                if value is not None:
                    ax.axhline(value, color=_style(method, i)["color"], linestyle=":", linewidth=1,
                               label=method + " analytic asymptotic reference")
        ax.set(xlabel="Round after static initialization", ylabel="Suboptimal-arm count / log(t)",
               title=" · ".join(key))
        ax.grid(alpha=.2); ax.legend(fontsize=7)
        nrep = len({str(r.get("rep")) for r in block})
        cap = ("SMOKE ONLY: no convergence conclusion. " if smoke else "Descriptive convergence diagnostic. ") + f"{nrep} paired repetitions; bands are ±1 Monte Carlo SE. Analytic Bernoulli/deterministic information constants only. Fixed finite static instance, fixed task parameters, interior best mean. Reference lines are asymptotic, not finite-time guarantees."
        paths += _finish(fig, folder / _safe("counts_" + "_".join(key)), cap, records, plt)
    return paths


def plot(outputdir):
    """Return absolute PNG/PDF/SVG paths; never rerun a simulation."""
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    root = Path(outputdir)
    analysis = root / "analysis"
    if not (analysis / "summary.json").exists():
        analyze(root)
    summary = json.loads((analysis / "summary.json").read_text(encoding="utf-8"))
    config_file = root / "config.json"
    config = json.loads(config_file.read_text(encoding="utf-8")) if config_file.exists() else {}
    folder = root / "figures"
    folder.mkdir(parents=True, exist_ok=True)
    records, paths = [], []
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none", "pdf.fonttype": 42}):
        paths += _trajectory_plots(_read(analysis / "trajectories_summary.csv"), folder, summary["smoke_only"], records, plt)
        paths += _tradeoff(_read(analysis / "module_summary.csv"), folder, summary["smoke_only"], records, plt)
        paths += _heatmaps(_read(analysis / "paired_cells.csv"), folder, summary["smoke_only"], records, plt)
        paths += _facets(_read(analysis / "density_summary.csv"), "K", folder, summary["smoke_only"], records, plt)
        paths += _facets(_read(analysis / "law_summary.csv"), "law", folder, summary["smoke_only"], records, plt)
        paths += _diagnostics(_read(analysis / "module_summary.csv"), folder, summary["smoke_only"], records, plt)
        paths += _count_plot(_read(analysis / "theory_counts.csv"), config, folder, summary["smoke_only"], records, plt)
    with (folder / "captions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("figure", "caption", "files"))
        writer.writeheader()
        for record in records:
            writer.writerow(dict(record, files=";".join(record["files"])))
    (folder / "index.json").write_text(json.dumps({"profile": summary["profile"], "smoke_only": summary["smoke_only"],
                                                   "figures": records}, indent=2), encoding="utf-8")
    report = analysis / "report.html"
    if report.exists() and records:
        markup = "<h2>Figures</h2>" + "".join("<figure><img style='max-width:100%' src='../figures/" + record["figure"] + ".png'><figcaption>" + record["caption"] + "</figcaption></figure>" for record in records)
        text = report.read_text(encoding="utf-8")
        start, end = "<!-- srcbench figures start -->", "<!-- srcbench figures end -->"
        if start in text:
            text = text[:text.index(start)] + text[text.index(end) + len(end):]
        report.write_text(text.replace("</body>", start + markup + end + "</body>"), encoding="utf-8")
    return paths
