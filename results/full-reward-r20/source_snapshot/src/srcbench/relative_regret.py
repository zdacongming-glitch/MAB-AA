"""Matched regret-ratio summaries for the scaled all-settings screen.

Percent change is the ratio of equally weighted macro means, never the
mean of cellwise percentages. Pilot figures intentionally have no stars.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, variance

from .analysis import (_cell_summaries, _critical, _input_rows, _macro,
                       _prepare, _write)

SECTIONS = ("f17", "adaptive", "dense_K100", "dense_K500", "dense_K2000", "scale_K4000")
OVERALL = "all_cells"
BALANCED = "balanced_sections"
COLUMNS = (*SECTIONS, OVERALL, BALANCED)
TARGETS = ("SRC-R", "SRC-KL-R")


def _layout_metadata(layouts):
    metadata = {}
    for layout in layouts:
        details = layout.get("metadata", {})
        derivative = details.get("derivative", {})
        actual_k = len(layout.get("arms", []))
        source_k = derivative.get("parent_arm_count", details.get("source_K", details.get("parent_K", actual_k)))
        group = layout["group"]
        if group == "dense":
            section = f"dense_K{int(source_k)}"
        elif group == "scale":
            section = f"scale_K{int(source_k)}"
        else:
            section = group
        metadata[layout["id"]] = dict(
            section=section, source_group=group, source_K=int(source_k), actual_K=actual_k,
            source_T=derivative.get("parent_T", details.get("source_T", layout.get("T"))),
            actual_T=layout.get("T"), source_layout_id=derivative.get("parent_id", layout["id"]),
            transformed=bool(derivative))
    return metadata


def _moments(values):
    n = len(values)
    return mean(values), variance(values) / n if n > 1 else None


def _interval(value, terms):
    if not terms or any(term is None for term, _ in terms):
        return None, None, None, None
    total = sum(term for term, _ in terms)
    denominator = sum(term**2/(n-1) for term, n in terms if n > 1)
    df = total**2/denominator if denominator else sum(n-1 for _, n in terms)
    se = math.sqrt(max(0., total))
    if df < 1:
        return se, None, None, df
    critical, _ = _critical(.05, df)
    return se, value-critical*se, value+critical*se, df


def _cell_weights(cells, balanced=False):
    if not balanced:
        return {key: 1/len(cells) for key in cells}
    sections = Counter(values["section"] for values in cells.values())
    return {key: 1/(len(sections)*sections[value["section"]]) for key, value in cells.items()}


def _estimate(cells, balanced=False):
    """Paired, stratified ratio delta method retaining numerator covariance."""
    weights = _cell_weights(cells, balanced)
    candidate = math.fsum(weights[key]*mean(value["candidate"]) for key, value in cells.items())
    comparator = math.fsum(weights[key]*mean(value["comparator"]) for key, value in cells.items())
    # Center each paired world before aggregating. Macro-mean subtraction can
    # erase a small paired change or create an ulp-sized change and false CI.
    difference = math.fsum(weights[key]*mean(a-b for a, b in zip(value["candidate"], value["comparator"]))
                           for key, value in cells.items())
    relative_difference = difference/comparator if comparator > 0 else None
    percent = 100*relative_difference if relative_difference is not None else None
    difference_terms, ratio_terms = [], []
    for key, cell in cells.items():
        pairs = list(zip(cell["candidate"], cell["comparator"]))
        n, w = len(pairs), weights[key]
        diff = [a-b for a, b in pairs]
        difference_terms.append((w*w*variance(diff)/n if n > 1 else None, n))
        if relative_difference is not None:
            # This centered form retains the paired numerator/denominator
            # covariance even when 1 + relative_difference rounds to one.
            influence = [100/comparator*((a-b)-relative_difference*b) for a, b in pairs]
            ratio_terms.append((w*w*variance(influence)/n if n > 1 else None, n))
    dse, dlo, dhi, ddf = _interval(difference, difference_terms)
    pse, plo, phi, pdf = _interval(percent, ratio_terms) if percent is not None else (None, None, None, None)
    repetitions = [len(v["candidate"]) for v in cells.values()]
    return dict(cells=len(cells), sections=len({v["section"] for v in cells.values()}),
                pairs=sum(repetitions), replications_min=min(repetitions), replications_max=max(repetitions),
                candidate_regret=candidate, comparator_regret=comparator,
                regret_difference=difference, difference_mcse=dse, difference_ci_low=dlo,
                difference_ci_high=dhi, difference_df=ddf,
                percent_change=percent, percent_mcse=pse, percent_ci_low=plo, percent_ci_high=phi,
                percent_df=pdf, percent_status="defined" if comparator > 0 else "undefined: comparator mean is zero",
                weighting="equal section, then equal cell" if balanced else "equal environmental cell",
                interval="nominal paired stratified t; percent uses delta method with covariance; no multiplicity-adjusted claim")


def _paired_cells(left, right, metadata):
    common = sorted(set(left) & set(right))
    cells = defaultdict(lambda: dict(candidate=[], comparator=[], section=""))
    for key in common:
        cell = cells[key[:2]]
        cell["candidate"].append(left[key]["regret"])
        cell["comparator"].append(right[key]["regret"])
        cell["section"] = metadata[key[0]]["section"]
    return cells, len(set(left)-set(right)), len(set(right)-set(left))


def _contrasts(rows, metadata, targets, comparators):
    by_cohort = defaultdict(list)
    for row in rows:
        by_cohort[row["cohort"]].append(row)
    result = []
    for cohort, block in sorted(by_cohort.items()):
        methods = defaultdict(dict)
        for row in block:
            methods[row["method"]][(row["layout_id"], row["law"], str(row["rep"]))] = row
        for target in targets:
            if target not in methods:
                continue
            for baseline in comparators:
                if baseline == target or baseline not in methods:
                    continue
                cells, unmatched_left, unmatched_right = _paired_cells(methods[target], methods[baseline], metadata)
                if not cells:
                    continue
                for section in COLUMNS:
                    selected = cells if section in (OVERALL, BALANCED) else {k: v for k, v in cells.items() if v["section"] == section}
                    if not selected:
                        continue
                    record = dict(cohort=cohort, candidate=target, comparator=baseline, section=section,
                                  unmatched_candidate=unmatched_left, unmatched_comparator=unmatched_right,
                                  **_estimate(selected, section == BALANCED))
                    result.append(record)
    return result


def _section_method_table(cells, metadata):
    enriched = [dict(row, section=metadata[row["layout_id"]]["section"]) for row in cells]
    result = _macro(enriched, ("cohort", "section", "method"))
    for row in result:
        row["summary"] = row["section"]
    global_rows = _macro(enriched, ("cohort", "method"))
    for row in global_rows:
        row.update(section=OVERALL, summary=OVERALL)
    result.extend(global_rows)
    # A section mean contributes equally here, independent of its cell count.
    grouped = defaultdict(list)
    for row in result:
        if row["section"] in SECTIONS:
            grouped[(row["cohort"], row["method"])].append(row)
    for (cohort, method), block in grouped.items():
        row = dict(cohort=cohort, method=method, section=BALANCED, summary=BALANCED,
                   cells=sum(r["cells"] for r in block), sections=len(block), paths=sum(r["paths"] for r in block),
                   replications_min=min(r["replications_min"] for r in block),
                   replications_max=max(r["replications_max"] for r in block),
                   weighting="equal section, then equal environmental cell")
        metrics = [key[:-5] for key in block[0] if key.endswith("_mean")]
        for metric in metrics:
            values = [r.get(metric+"_mean") for r in block]
            ses = [r.get(metric+"_mcse") for r in block]
            row[metric+"_mean"] = mean(values) if all(v is not None for v in values) else None
            row[metric+"_mcse"] = math.sqrt(sum(v*v for v in ses))/len(ses) if all(v is not None for v in ses) else None
        result.append(row)
    return result


def _label(section, metadata):
    if section == OVERALL:
        return "All cells\nequal cells (primary)"
    if section == BALANCED:
        return "Balanced sections\nequal sections (secondary)"
    matching = [r for r in metadata.values() if r["section"] == section]
    actual = sorted({r["actual_K"] for r in matching})
    source = sorted({r["source_K"] for r in matching})
    actual_text = (str(actual[0]) if len(actual) == 1 else f"{min(actual)}–{max(actual)}") if actual else "?"
    source_text = "/".join(map(str, source)) or "?"
    if section in ("f17", "adaptive"):
        return ("F17" if section == "f17" else "Adaptive") + f"\nK {actual_text}"
    prefix = "Dense" if section.startswith("dense") else "Scale"
    return f"{prefix}\nK {source_text} → {actual_text}"


def _figures(records, metadata, baseline_ids, summary, out):
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import TwoSlopeNorm
    files = []
    for cohort in sorted({r["cohort"] for r in records}):
        selected = [r for r in records if r["cohort"] == cohort]
        lookup = {(r["candidate"], r["comparator"], r["section"]): r for r in selected}
        baselines = [b for b in baseline_ids if any(r["comparator"] == b for r in selected)]
        if not baselines:
            continue
        with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 9,
                             "svg.fonttype": "none", "pdf.fonttype": 42}):
            fig, axes = plt.subplots(1, 2, figsize=(19, max(8, .32*len(baselines)+2.6)), sharey=True)
            color = None
            for ax, target in zip(axes, TARGETS):
                matrix = np.full((len(baselines), len(COLUMNS)), np.nan)
                for i, baseline in enumerate(baselines):
                    for j, section in enumerate(COLUMNS):
                        value = lookup.get((target, baseline, section), {}).get("percent_change")
                        if value is not None:
                            matrix[i, j] = value
                color = ax.imshow(np.ma.masked_invalid(matrix), cmap="coolwarm", aspect="auto",
                                  norm=TwoSlopeNorm(vmin=-100, vcenter=0, vmax=100))
                ax.set_xticks(range(len(COLUMNS)), [_label(c, metadata) for c in COLUMNS],
                              fontsize=8, rotation=30, ha="right")
                ax.set_yticks(range(len(baselines)), baselines, fontsize=8)
                ax.set_title(f"{target} versus {len(baselines)} baselines", fontweight="bold", pad=12)
                ax.set_xticks(np.arange(-.5, len(COLUMNS), 1), minor=True)
                ax.set_yticks(np.arange(-.5, len(baselines), 1), minor=True)
                ax.grid(which="minor", color="white", linewidth=1)
                ax.tick_params(which="minor", bottom=False, left=False)
                for i in range(len(baselines)):
                    for j in range(len(COLUMNS)):
                        value = matrix[i, j]
                        text = "—" if not math.isfinite(value) else f"{value:+.1f}%"
                        ax.text(j, i, text, ha="center", va="center", fontsize=7.1,
                                color="white" if math.isfinite(value) and abs(value) > 65 else "#1c2730")
            fig.subplots_adjust(left=.12, right=.91, top=.88, bottom=.20, wspace=.08)
            barax = fig.add_axes([.93, .25, .015, .56])
            fig.colorbar(color, cax=barax, extend="both", label="Regret change (%) · blue decreases / red increases")
            actual_t = summary["actual_horizons"]
            ttext = str(actual_t[0]) if len(actual_t) == 1 else "/".join(map(str, actual_t))
            reps = summary["replications"]
            rtext = str(reps[0]) if len(reps) == 1 else f"{min(reps)}–{max(reps)}"
            fig.suptitle(f"Scaled all-settings screening · {cohort}\nT={ttext} · {rtext} paired repetitions/cell · "
                         f"{summary['layouts']} source layouts / {summary['cells']} cells · {summary['methods']} methods executed",
                         fontsize=13, fontweight="bold", y=.975)
            caption = ("Each value = 100 × (candidate macro mean / comparator macro mean − 1). Negative means less regret. "
                       "All-cells primary pools cells equally; balanced secondary weights six source sections equally.\n"
                       "Reduced horizons/arm sets are transformed environments, not the original full-size experiment. "
                       "Small-n descriptive estimates: no significance stars or superiority claims.\n"
                       "Colors saturate outside ±100%; printed values and CSV retain full magnitudes. Zero comparator means are undefined (—). "
                       "Nominal paired delta-method intervals are in CSV.")
            fig.text(.12, .025, caption, fontsize=8, va="bottom", linespacing=1.65)
            name = "relative_regret_" + re.sub(r"[^A-Za-z0-9_.-]", "_", cohort)
            for suffix in ("png", "pdf", "svg"):
                destination = out / f"{name}.{suffix}"
                fig.savefig(destination, dpi=200 if suffix == "png" else None, bbox_inches="tight")
                files.append(str(destination.resolve()))
            plt.close(fig)
    return files


def analyze_relative(outputdir):
    """Write a new relative_regret/ bundle using stored endpoints only."""
    root = Path(outputdir)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "PASS":
        raise ValueError("Relative screening requires a completed PASS manifest")
    record = manifest.get("files", {}).get("runs.csv.gz", {})
    if record.get("sha256"):
        digest = hashlib.sha256()
        with (root / "runs.csv.gz").open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024*1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != record["sha256"]:
            raise ValueError("Endpoint SHA256 differs from the completed manifest")
    rows = _prepare(_input_rows(root, "runs"))
    if not rows:
        raise ValueError("No endpoints for relative-regret analysis")
    expected = manifest.get("expected_runs", config.get("expected_runs"))
    if isinstance(expected, int) and len(rows) != expected:
        raise ValueError(f"Expected {expected} unique paths, found {len(rows)}")
    metadata = _layout_metadata(config.get("layouts", []))
    for row in rows:
        if row["layout_id"] not in metadata:
            raise ValueError(f"Layout {row['layout_id']} missing from configuration snapshot")
    from .methods import BASELINE_IDS
    present = {r["method"] for r in rows}
    definitions = config.get("methods", {})
    baselines = [m for m in BASELINE_IDS if m in present]
    baselines += sorted(m for m in present if m not in baselines and
                        (definitions.get(m, {}).get("family") == "baseline" or not m.startswith("SRC")))
    cells = _cell_summaries([dict(row, suite="all-settings") for row in rows])
    for row in cells:
        row.update(metadata[row["layout_id"]])
    section_methods = _section_method_table(cells, metadata)
    comparisons = _contrasts(rows, metadata, TARGETS, baselines)
    direct = _contrasts(rows, metadata, ("SRC-KL-R",), ("SRC-R",))
    sections = sorted({metadata[r["layout_id"]]["section"] for r in rows})
    summary = dict(profile=config.get("profile", manifest.get("profile")), manifest_status="PASS",
                   scope="Scaled all-settings pilot; original full-size experiment not run",
                   unique_trajectories=len(rows), layouts=len({r["layout_id"] for r in rows}),
                   cells=len({(r["layout_id"], r["law"]) for r in rows}), methods=len(present),
                   cohorts=sorted({r["cohort"] for r in rows}), sections=sections,
                   all_six_sections_present=set(SECTIONS).issubset(sections),
                   actual_horizons=sorted({int(r["T"]) for r in rows}),
                   replications=sorted({r["paths"] for r in cells}),
                   candidates=list(TARGETS), comparators=baselines, comparator_count=len(baselines),
                   percent_definition="100*(candidate macro mean/comparator macro mean-1); never average cell percentages",
                   primary_overall="equal weight per environmental cell", secondary_overall="equal weight per source section, then per cell",
                   intervals="nominal paired stratified delta-method t intervals with covariance; descriptive only",
                   stars=False, all_failure_paths_retained=True,
                   scientific_flag_paths={name: sum(r[name] != 0 for r in rows) for name in ("label_error", "coverage_error", "empty_intersection")})
    out = root / "relative_regret"
    out.mkdir(parents=True, exist_ok=True)
    _write(out / "all_cell_methods.csv", cells)
    _write(out / "section_methods.csv", section_methods)
    all_method_relative = []
    macro_lookup = {(r["cohort"], r["method"], r["section"]): r for r in section_methods}
    for row in section_methods:
        if row["section"] not in (OVERALL, BALANCED):
            continue
        for baseline in baselines:
            other = macro_lookup.get((row["cohort"], baseline, row["section"]))
            if other is None or row["method"] == baseline:
                continue
            numerator, denominator = row["regret_mean"], other["regret_mean"]
            all_method_relative.append(dict(
                cohort=row["cohort"], candidate=row["method"], comparator=baseline, section=row["section"],
                candidate_regret=numerator, comparator_regret=denominator,
                percent_change=100*(numerator/denominator-1) if denominator > 0 else None,
                cells=row["cells"], paths=row["paths"], replications_min=row["replications_min"],
                replications_max=row["replications_max"], weighting=row["weighting"],
                interpretation="descriptive macro-mean ratio; paired intervals for the two R candidates are in percent_matrix.csv"))
    _write(out / "all_method_relative_overall.csv", all_method_relative)
    _write(out / "percent_matrix.csv", comparisons)
    _write(out / "direct_KL_minus_SRC.csv", direct)
    for candidate in TARGETS:
        relevant = [r for r in comparisons if r["candidate"] == candidate]
        wide = []
        for cohort in summary["cohorts"]:
            for baseline in baselines:
                record = dict(cohort=cohort, candidate=candidate, comparator=baseline)
                for section in COLUMNS:
                    match = next((r for r in relevant if r["cohort"] == cohort and r["comparator"] == baseline and r["section"] == section), None)
                    record[section] = match["percent_change"] if match else None
                wide.append(record)
        _write(out / f"percent_matrix_{candidate}.csv", wide)
    summary["figures"] = _figures(comparisons, metadata, baselines, summary, out)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    images = "".join(f"<figure><img style='max-width:100%' src='{html.escape(Path(path).name)}'></figure>"
                     for path in summary["figures"] if path.endswith(".png"))
    report = ("<!doctype html><html lang='en'><meta charset='utf-8'><title>Relative regret screening</title>"
              "<body style='font:15px system-ui;margin:30px'><h1>Scaled all-settings regret screen</h1>"
              "<p>Original full-size experiment not run. All scientific failure paths are retained. "
              f"The main heatmap compares the two reward endpoints against {summary['comparator_count']} canonical baseline configurations; "
              f"all {summary['methods']} executed methods, including positive-service modes, are in all_cell_methods.csv and section_methods.csv.</p>"
              "<p>Primary overall: every layout × law cell has equal weight. Secondary balanced overall: every source section "
              "has equal weight. Percentages compare the corresponding macro means and are not averages of cell percentages. "
              "No significance stars are shown; nominal small-sample intervals are descriptive and unadjusted.</p>"
              + images + "</body></html>")
    (out / "report.html").write_text(report, encoding="utf-8")
    return summary
