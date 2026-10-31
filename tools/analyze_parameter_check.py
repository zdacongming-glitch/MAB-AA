"""Analyze completed frozen parameter-check results without development inputs."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
try:
    from . import parameter_statistics as base
except ImportError:
    import parameter_statistics as base

COEFFICIENTS = (.25, .5, .75, 1., 1.5)
BETAS = (32., 128.)


def _metadata(config):
    study = base._study_metadata(config)
    explicit = study.get("primary_candidate_ids", config.get("primary_candidate_ids"))
    if explicit is not None:
        inferred = study.get("candidate_methods")
        if inferred is not None and set(inferred) != set(explicit):
            raise ValueError("Frozen task and study primary candidate lists disagree")
        study["candidate_methods"] = list(explicit)
    study.setdefault("varied_parameters", ["cap_multiplier", "log_coefficient", "beta_r"])
    allowed = {"cap_multiplier", "log_coefficient", "beta_r"}
    if not set(study["varied_parameters"]) <= allowed:
        raise ValueError("Only the declared three numerical constants may vary")
    return study


def _roles(config, present):
    definitions = base._definitions(config)
    study = _metadata(config)
    primary = study.get("candidate_methods", config.get("candidate_methods"))
    if primary is None:
        primary = [name for name, spec in definitions.items()
                   if spec.get("family") == "src_kl" and spec.get("beta_r") != 0]
    primary = set(primary)
    if not primary <= set(present):
        raise ValueError(f"Missing source primary candidates: {sorted(primary-set(present))}")
    roles = {}
    for name in sorted(present):
        if name not in definitions:
            raise ValueError(f"No frozen method specification for {name}")
        definition = definitions[name]
        params = definition.get("params", {})
        cap = params.get("cap_multiplier", 1.)
        coefficient = float(params.get("log_coefficient", .5))
        beta = definition.get("beta_r")
        preference = float(definition.get("preference", 0))
        zero = (definition.get("family") == "src_kl" and beta is not None and float(beta) == 0)
        role = "reference" if name in base.REFERENCES else "other"
        if name in primary or zero:
            if definition.get("family") != "src_kl" or preference != 0:
                raise ValueError(f"Refinement must retain SRC-KL and lambda=0: {name}")
            if not any(abs(coefficient-value) <= 1e-12 for value in COEFFICIENTS):
                raise ValueError(f"Coefficient outside the frozen refinement grid: {name}")
            if params.get("reference", "kl_switch") != "kl_switch" or params.get("reward_cap", "sublog") != "sublog":
                raise ValueError(f"Reference and cap structure changed: {name}")
            if cap is None or not math.isfinite(float(cap)) or float(cap) <= 0:
                raise ValueError(f"Invalid fixed positive cap multiplier: {name}")
            if zero:
                role = "zero_budget_diagnostic"
            else:
                if beta is None or not any(abs(float(beta)-value) <= 1e-12 for value in BETAS):
                    raise ValueError(f"Reward budget outside the frozen refinement grid: {name}")
                # Keep this schema-compatible internal role for phase-one
                # statistical routines and the independent verification code.
                role = "cap_candidate"
        roles[name] = dict(method=name, role=role,
            cap_multiplier=float(cap) if cap is not None else None,
            log_coefficient=coefficient, beta_r=beta, preference=preference,
            family=definition.get("family", ""), params_json=json.dumps(params, sort_keys=True))
    if not any(value["role"] == "cap_candidate" for value in roles.values()):
        raise ValueError("No primary refinement candidates")
    # Verify that all other exposed parameters and mechanism switches match
    # the default implementation, independently of candidate labels.
    reference = definitions.get("SRC-KL-R")
    if reference is not None:
        def remainder(spec):
            answer = {key: value for key, value in spec.items() if key not in ("id", "beta_r", "params")}
            answer["params"] = {key: value for key, value in spec.get("params", {}).items()
                                if key not in ("cap_multiplier", "log_coefficient")}
            return answer
        expected = remainder(reference)
        for name, value in roles.items():
            if value["role"] in ("cap_candidate", "zero_budget_diagnostic") and remainder(definitions[name]) != expected:
                raise ValueError(f"Candidate changes parameters beyond a, c, beta_R: {name}")
    return roles


def _parameter_columns(records, roles, field="method"):
    for row in records:
        spec = roles[row[field]]
        row.update(cap_multiplier=spec["cap_multiplier"],
                   log_coefficient=spec["log_coefficient"], beta_r=spec["beta_r"])
    return records


def _ordering(roles):
    return sorted((name for name, value in roles.items() if value["role"] == "cap_candidate"),
                  key=lambda name: (roles[name]["cap_multiplier"], roles[name]["beta_r"],
                                    roles[name]["log_coefficient"], name))


def _label(role):
    return f"a={role['cap_multiplier']:g}, c={role['log_coefficient']:g}, beta={role['beta_r']:g}"


def _figures(out, roles, groups, comparisons, scopes, primary_groups):
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    style = {"font.family": "serif", "font.serif": ["DejaVu Serif"],
             "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
             "legend.fontsize": 7, "legend.frameon": False,
             "axes.spines.top": False, "axes.spines.right": False,
             "axes.axisbelow": True, "pdf.fonttype": 42, "ps.fonttype": 42,
             "svg.fonttype": "none"}
    files = []
    candidates = _ordering(roles)
    diagnostics = sorted(name for name, value in roles.items() if value["role"] == "zero_budget_diagnostic")
    scope_lookup = {(value["cohort"], value["group"]): value for value in scopes}
    for cohort in sorted({row["cohort"] for row in groups}):
        available = sorted({row["group"] for row in groups if row["cohort"] == cohort})
        panels = [group for group in primary_groups if group in available] or available
        lookup = {(r["group"], r["method"]): r for r in groups if r["cohort"] == cohort}
        labels = [_label(roles[name]) for name in candidates]
        plot_methods = candidates+diagnostics
        plot_labels = labels+[name+" (diagnostic)" for name in diagnostics]
        with plt.rc_context(style):
            fig, axes = plt.subplots(1, len(panels), sharey=True, squeeze=False,
                figsize=(4.3*len(panels)+1.6, max(3., .27*len(plot_methods)+2.25)))
            y = np.arange(len(plot_methods))
            for ax, group in zip(axes.flat, panels):
                for position, name in enumerate(plot_methods):
                    row = lookup.get((group, name))
                    if row is None:
                        continue
                    diagnostic = name in diagnostics
                    color = "#CC79A7" if diagnostic else ("#0072B2" if roles[name]["beta_r"] == 32 else "#D55E00")
                    ax.errorbar(row["regret_mean"], position,
                        xerr=row["regret_mcse"] or 0., fmt="D" if diagnostic else "o",
                        color=color, markersize=4, capsize=2, linewidth=1., zorder=3)
                for reference, linestyle in zip(base.REFERENCES, ("--", ":", "-.", (0, (5, 2)))):
                    row = lookup.get((group, reference))
                    if row:
                        ax.axvline(row["regret_mean"], color=base.COLORS[reference], linestyle=linestyle,
                                   linewidth=1.1, label=reference)
                if diagnostics:
                    ax.axhline(len(candidates)-.5, color="#999999", linewidth=.7)
                ax.set_yticks(y, plot_labels, fontsize=7)
                ax.set_ylim(len(plot_methods)-.5, -.5)
                ax.set_xlabel("Equal-cell mean dynamic regret")
                scope = scope_lookup[(cohort, group)]
                ts = scope["horizons"]
                time_text = "/".join(map(str, ts)) if len(ts) <= 3 else f"{min(ts)}-{max(ts)}"
                ax.set_title(f"{group} | T={time_text}\n{scope['size_label']}", fontsize=8.5)
                ax.grid(axis="x", alpha=.16)
                ax.legend(loc="lower center", bbox_to_anchor=(.5, -.15), ncol=2)
            fig.suptitle(f"Fixed-constant SRC-KL refinement | {cohort}\n"
                         "Dots follow parameter order, not outcome rank; bars show 1 MCSE. Blue beta=32, orange beta=128.", fontsize=10)
            fig.tight_layout(rect=(0, .035, 1, .93))
            files += base._save(fig, out/("refinement_dots_"+base._slug(cohort)))
            plt.close(fig)
            columns = [(group, baseline) for group in panels for baseline in base.PRIMARY_REFERENCES]
            values = np.full((len(candidates), len(columns)), np.nan)
            contrast_lookup = {(r["candidate"], r["group"], r["comparator"]): r
                               for r in comparisons if r["cohort"] == cohort}
            for i, name in enumerate(candidates):
                for j, (group, baseline) in enumerate(columns):
                    change = contrast_lookup.get((name, group, baseline), {}).get("percent_change")
                    if change is not None:
                        values[i, j] = change
            limit = max(1., float(np.nanmax(np.abs(values)))) if np.any(np.isfinite(values)) else 1.
            cmap = LinearSegmentedColormap.from_list("refinement_blue_orange", ["#0072B2", "#FAFAFA", "#D55E00"])
            fig, ax = plt.subplots(figsize=(max(6., len(columns)*1.55+1.5), max(2.7, len(candidates)*.29+1.8)))
            image = ax.imshow(np.ma.masked_invalid(values), cmap=cmap, aspect="auto",
                              norm=TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit))
            ax.set_xticks(range(len(columns)), [group+"\n"+baseline for group, baseline in columns], fontsize=8)
            ax.set_yticks(range(len(candidates)), labels, fontsize=7)
            for i in range(len(candidates)):
                for j in range(len(columns)):
                    value = values[i, j]
                    ax.text(j, i, f"{value:+.1f}%" if math.isfinite(value) else "undefined",
                            ha="center", va="center", fontsize=7.5,
                            color="white" if math.isfinite(value) and abs(value)>.65*limit else "#222222")
            ax.set_title(f"Candidate/reference macro mean regret change | {cohort}\n"
                         "Negative means lower regret; no significance stars or parameter selection", fontsize=10)
            fig.colorbar(image, ax=ax, fraction=.04, pad=.03, label="100 x (candidate/reference - 1)")
            fig.tight_layout()
            files += base._save(fig, out/("refinement_comparison_"+base._slug(cohort)))
            plt.close(fig)
    return files


def analyze(output_dir):
    root = Path(output_dir).resolve()
    config_path, runs_path = root/"config.json", root/"runs.csv.gz"
    if not config_path.is_file() or not runs_path.is_file():
        raise ValueError("Wait for completed config.json and runs.csv.gz")
    inputs = {name: base.sha256(path) for name, path in (("config.json", config_path), ("runs.csv.gz", runs_path))}
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    provenance = base.recorded_provenance(config)
    study = _metadata(config)
    rows = base._rows(runs_path)
    if config.get("expected_runs") is not None and len(rows) != int(config["expected_runs"]):
        raise ValueError("Completed endpoint count differs from the stage configuration")
    present = {row["method"] for row in rows}
    if not set(base.REFERENCES) <= present:
        raise ValueError(f"Missing requested reference controls: {sorted(set(base.REFERENCES)-present)}")
    roles = _roles(config, present)
    actual_groups = sorted({row["group"] for row in rows})
    default_groups = [group for group in ("f17", "adaptive") if group in actual_groups] or actual_groups
    primary_groups = list(study.get("primary_groups", config.get("primary_groups", default_groups)))
    comparisons, family_size = base._contrasts(rows, roles, primary_groups)
    cells, groups = base._summaries(rows, roles)
    _parameter_columns(cells, roles)
    _parameter_columns(groups, roles)
    _parameter_columns(comparisons, roles, "candidate")
    scopes = base._scope(config, rows)
    out = root/"parameter_analysis"
    out.mkdir(exist_ok=True)
    base._write_csv(out/"method_parameters.csv", list(roles.values()))
    base._write_csv(out/"cell_methods.csv", cells)
    base._write_csv(out/"group_methods.csv", groups)
    base._write_csv(out/"paired_contrasts.csv", comparisons)
    diagnostics = [{key: row[key] for key in ("cohort", "group", "method", "role", "cap_multiplier",
                    "log_coefficient", "beta_r", "cells", "paths", "guard_changed_fraction", "action_hash_match_fraction_SRC_R")}
                   for row in groups]
    base._write_csv(out/"diagnostics.csv", diagnostics)
    base._write_csv(out/"input_scope.csv", [dict(scope,
        horizons=";".join(map(str, scope["horizons"])),
        arm_counts=";".join(map(str, scope["arm_counts"]))) for scope in scopes])
    figures = _figures(out, roles, groups, comparisons, scopes, primary_groups)
    if inputs != {name: base.sha256(path) for name, path in (("config.json", config_path), ("runs.csv.gz", runs_path))}:
        raise RuntimeError("Stage inputs changed during analysis")
    candidates = _ordering(roles)
    summary = dict(**provenance, input_directory=str(root), study_phase=study["phase"], input_sha256=inputs,
        analyzer_sha256=base.sha256(Path(__file__)), phase_one_analyzer_sha256=base.sha256(Path(base.__file__)),
        paths=len(rows), environmental_cells=len({(r['cohort'],r['group'],r['layout_id'],r['law']) for r in rows}),
        cap_candidates=candidates, primary_candidates=candidates,
        varied_parameters=study["varied_parameters"], candidate_specifications=[roles[name] for name in candidates],
        diagnostic_methods=[name for name, value in roles.items() if value["role"] == "zero_budget_diagnostic"],
        primary_groups=primary_groups, primary_references=list(base.PRIMARY_REFERENCES), primary_family_size=family_size,
        primary_confidence_rule="Bonferroni four times the actual number of source primary candidates; beta-zero is excluded",
        pairing="exact cohort/group/layout/law/rep keys; no new repetitions created by joining candidate files",
        aggregation="equal weight per environmental cell, using actual matched repetitions",
        difference_interval="paired stratified t with Satterthwaite degrees of freedom; n=2 supported",
        percent_interval="paired ratio delta method with covariance; zero denominator is undefined",
        secondary_comparisons="SRC-R, SRC-KL-R and beta-zero diagnostic use nominal intervals",
        parameter_selection="none; only frozen candidates from the supplied configuration are compared",
        source_provenance="Frozen local configuration; no development inputs are read",
        score_contract="c is an explicitly varied fixed constant; figures do not identify it with the original c=.5 definition",
        scope=scopes, figures=figures,
        failure_paths={flag:sum(row[flag] for row in rows) for flag in ('label_error','coverage_error','empty_intersection')})
    (out/"summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    value = analyze(args.output_dir)
    print(json.dumps({key:value[key] for key in ("study_phase", "paths", "primary_candidates", "primary_family_size", "parameter_selection")}, indent=2))


if __name__ == "__main__":
    main()
