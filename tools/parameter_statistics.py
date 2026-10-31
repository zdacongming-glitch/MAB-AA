"""Stable paired, cell-equal statistics for frozen parameter-check results.

No development drivers, plans, selections, or external study files are needed.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, variance

import numpy as np
from scipy.stats import t as student_t

STUDY_ROOT = Path(__file__).resolve().parent
REFERENCES = ("IMED", "Empirical-KL-UCB", "SRC-KL-R", "SRC-R")
PRIMARY_REFERENCES = REFERENCES[:2]
KEY = ("cohort", "group", "layout_id", "law", "rep")
ORIGINAL_HORIZONS = {"f17": {12000, 14000, 16000},
                     "adaptive": {8000, 9000, 10000, 12000, 14000, 15000, 16000}}
REQUIRED = (*KEY, "method", "regret", "T", "K", "guard_changed", "action_hash")
COLORS = {"candidate": "#D55E00", "IMED": "#0072B2",
          "Empirical-KL-UCB": "#56B4E9", "SRC-R": "#4D4D4D",
          "SRC-KL-R": "#009E73", "diagnostic": "#CC79A7"}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _finite(value, name):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Nonfinite {name}: {value!r}")
    return number


def _rows(path):
    """Preserve uint64 hashes as strings and reject duplicate scientific keys."""
    result, seen = [], set()
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = set(REQUIRED) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Missing endpoint columns: {sorted(missing)}")
        for raw in reader:
            row = dict(raw)
            for name in ("regret", "T", "K", "guard_changed"):
                row[name] = _finite(row[name], name)
            row["rep"] = int(row["rep"])
            if row["T"] < 1 or row["K"] < 1 or row["regret"] < -1e-9:
                raise ValueError("Invalid physical horizon, arm count, or regret")
            if not 0 <= row["guard_changed"] <= row["T"]:
                raise ValueError("guard_changed must count physical rounds")
            for flag in ("label_error", "coverage_error", "empty_intersection"):
                row[flag] = int(raw.get(flag, 0))
                if row[flag] not in (0, 1):
                    raise ValueError(f"Invalid scientific flag {flag}")
            key = tuple(row[k] for k in (*KEY, "method"))
            if key in seen:
                raise ValueError(f"Duplicate paired endpoint: {key}")
            seen.add(key)
            result.append(row)
    if not result:
        raise ValueError("The endpoint file is empty")
    return result


def _definitions(config):
    definitions = config.get("methods", {})
    if isinstance(definitions, list):
        definitions = {item["id"]: item for item in definitions}
    if not definitions:
        raise ValueError("config.json must retain method definitions")
    return definitions


def _study_metadata(config):
    """Read driver annotations retained inside frozen task diagnostics."""
    study = dict(config.get("study", {}))
    annotations = [task.get("diagnostics", {}) for task in config.get("tasks", [])]
    candidate_lists = {tuple(item["primary_candidate_ids"]) for item in annotations
                       if item.get("primary_candidate_ids") is not None}
    phases = {item["study_phase"] for item in annotations if item.get("study_phase")}
    if len(candidate_lists) > 1 or len(phases) > 1:
        raise ValueError("Stage tasks disagree on primary candidates or study phase")
    if candidate_lists:
        study.setdefault("candidate_methods", list(next(iter(candidate_lists))))
    if phases:
        study.setdefault("phase", next(iter(phases)))
    study.setdefault("phase", config.get("study_phase", config.get("profile", "unspecified")))
    return study


def _roles(config, present):
    definitions = _definitions(config)
    study = _study_metadata(config)
    requested = study.get("candidate_methods", config.get("candidate_methods"))
    requested = set(requested) if requested is not None else None
    roles = {}
    for method in sorted(present):
        if method not in definitions:
            raise ValueError(f"Method {method} has no frozen specification")
        definition = definitions[method]
        params = definition.get("params", {})
        coefficient = float(params.get("log_coefficient", .5))
        cap = params.get("cap_multiplier", 1.)
        beta = definition.get("beta_r")
        preference = float(definition.get("preference", 0))
        role = "reference" if method in REFERENCES else "other"
        consider = (method in requested if requested is not None else
                    definition.get("family") == "src_kl" and method not in REFERENCES)
        if consider:
            if definition.get("family") != "src_kl":
                raise ValueError(f"Cap candidate {method} must belong to src_kl")
            if abs(coefficient-.5) > 1e-12 or preference != 0:
                raise ValueError(f"Only c=.5 and lambda=0 are allowed: {method}")
            if params.get("reference", "kl_switch") != "kl_switch" or params.get("reward_cap", "sublog") != "sublog":
                raise ValueError(f"Only the SRC-KL reference and sublog cap may be used: {method}")
            if beta is not None and float(beta) == 0:
                role = "zero_budget_diagnostic"
            else:
                if beta is None or abs(float(beta)-32) > 1e-12:
                    raise ValueError(f"Cap candidates must retain beta_R=32: {method}")
                if cap is None or not math.isfinite(float(cap)) or float(cap) <= 0:
                    raise ValueError(f"Cap multiplier must be finite and positive: {method}")
                role = "cap_candidate"
        # A separately requested beta-zero control is always a diagnostic.
        if (definition.get("family") == "src_kl" and beta is not None
                and float(beta) == 0 and method not in REFERENCES):
            if abs(coefficient-.5) > 1e-12 or preference != 0:
                raise ValueError(f"beta-zero diagnostic changed c or lambda: {method}")
            role = "zero_budget_diagnostic"
        roles[method] = {"method": method, "role": role,
                         "cap_multiplier": float(cap) if cap is not None else None,
                         "log_coefficient": coefficient, "beta_r": beta,
                         "preference": preference,
                         "family": definition.get("family", ""),
                         "params_json": json.dumps(params, sort_keys=True)}
    if requested is not None and not requested <= set(present):
        raise ValueError(f"Missing requested candidates: {sorted(requested-set(present))}")
    if not any(value["role"] == "cap_candidate" for value in roles.values()):
        raise ValueError("No cap candidates; specify study.candidate_methods if needed")
    return roles


def _interval(point, terms, alpha=.05):
    """Satterthwaite t interval for a sum of independent cell mean terms."""
    if not terms or any(value is None or n < 2 for value, n in terms):
        return {"mcse": None, "df": None, "ci_low": None, "ci_high": None}
    total = sum(value for value, _ in terms)
    denominator = sum(value*value/(n-1) for value, n in terms)
    df = total*total/denominator if denominator > 0 else sum(n-1 for _, n in terms)
    se = math.sqrt(max(0., total))
    if df <= 0:
        return {"mcse": se, "df": df, "ci_low": None, "ci_high": None}
    critical = float(student_t.ppf(1-alpha/2, df))
    return {"mcse": se, "df": df,
            "ci_low": point-critical*se, "ci_high": point+critical*se}


def _stratified(values_by_cell, alpha=.05):
    """Equal environmental-cell weights; repetitions are not pooled weights."""
    count = len(values_by_cell)
    if not count:
        raise ValueError("No environmental cells")
    point = mean(mean(values) for values in values_by_cell.values())
    terms = [(variance(values)/len(values)/count**2 if len(values) > 1 else None,
              len(values)) for values in values_by_cell.values()]
    return {"mean": point, **_interval(point, terms, alpha)}


def _scope(config, rows):
    layouts = {value["id"]: value for value in config.get("layouts", [])}
    result = []
    for cohort, group in sorted({(r["cohort"], r["group"]) for r in rows}):
        subset = [r for r in rows if (r["cohort"], r["group"]) == (cohort, group)]
        horizons = sorted({int(r["T"]) for r in subset})
        arms = sorted({int(r["K"]) for r in subset})
        changed = False
        explicit_parent = False
        for row in subset:
            layout = layouts.get(row["layout_id"], {})
            derivative = layout.get("metadata", {}).get("derivative", {})
            if derivative:
                explicit_parent = True
                pt = derivative.get("parent_T", row["T"])
                pk = derivative.get("parent_arm_count", row["K"])
                changed |= int(pt) != int(row["T"]) or int(pk) != int(row["K"])
        if changed:
            size = "reduced or modified horizon/arm set"
        elif explicit_parent:
            size = "original parent horizon and arm count"
        elif group in ORIGINAL_HORIZONS and set(horizons) <= ORIGINAL_HORIZONS[group]:
            size = "original horizon values; arm provenance retained in config"
        else:
            size = "reduced or custom horizon values"
        result.append({"cohort": cohort, "group": group, "size_label": size,
                       "horizons": horizons, "arm_counts": arms,
                       "layouts": len({r["layout_id"] for r in subset}),
                       "cells": len({(r["layout_id"], r["law"]) for r in subset})})
    return result


def _summaries(rows, roles):
    indexed = {tuple(r[k] for k in (*KEY, "method")): r for r in rows}
    cells = defaultdict(list)
    for row in rows:
        cells[(row["cohort"], row["group"], row["layout_id"], row["law"], row["method"])].append(row)
    cell_rows, by_group = [], defaultdict(list)
    for key, block in sorted(cells.items()):
        cohort, group, layout, law, method = key
        values = [r["regret"] for r in block]
        guard = [r["guard_changed"]/r["T"] for r in block]
        matched = [int(r["action_hash"] == indexed[tuple(r[k] for k in KEY)+("SRC-R",)]["action_hash"])
                   for r in block if tuple(r[k] for k in KEY)+("SRC-R",) in indexed]
        n = len(values)
        interval = _interval(mean(values), [(variance(values)/n if n > 1 else None, n)])
        result = dict(cohort=cohort, group=group, layout_id=layout, law=law, method=method,
                      role=roles[method]["role"], cap_multiplier=roles[method]["cap_multiplier"],
                      paths=n, T=int(block[0]["T"]), K=int(block[0]["K"]),
                      regret_mean=mean(values), regret_mcse=interval["mcse"],
                      regret_ci_low=interval["ci_low"], regret_ci_high=interval["ci_high"],
                      guard_changed_fraction=mean(guard),
                      action_hash_pairs_SRC_R=len(matched),
                      action_hash_match_fraction_SRC_R=mean(matched) if matched else None)
        result.update({flag+"_paths": sum(r[flag] for r in block)
                       for flag in ("label_error", "coverage_error", "empty_intersection")})
        cell_rows.append(result)
        by_group[(cohort, group, method)].append((key[2:4], block, result))
    group_rows = []
    for (cohort, group, method), block in sorted(by_group.items()):
        estimate = _stratified({key: [r["regret"] for r in raw] for key, raw, _ in block})
        reps = [len(raw) for _, raw, _ in block]
        hash_values = [summary["action_hash_match_fraction_SRC_R"] for _, _, summary in block]
        group_rows.append(dict(cohort=cohort, group=group, method=method,
            role=roles[method]["role"], cap_multiplier=roles[method]["cap_multiplier"],
            cells=len(block), paths=sum(reps), replications_min=min(reps), replications_max=max(reps),
            regret_mean=estimate["mean"], regret_mcse=estimate["mcse"],
            regret_ci_low=estimate["ci_low"], regret_ci_high=estimate["ci_high"], regret_df=estimate["df"],
            guard_changed_fraction=mean(summary["guard_changed_fraction"] for _, _, summary in block),
            action_hash_match_fraction_SRC_R=mean(hash_values) if all(v is not None for v in hash_values) else None,
            weighting="equal environmental cell", interval="nominal 95% stratified t"))
    return cell_rows, group_rows


def _comparison(pairs, alpha):
    """Compute paired differences and a macro-mean ratio with covariance."""
    count = len(pairs)
    candidate = mean(mean(a for a, _ in values) for values in pairs.values())
    comparator = mean(mean(b for _, b in values) for values in pairs.values())
    # Center before aggregation. Subtracting two large macro means can erase
    # paired differences or manufacture an ulp-sized difference and false CI.
    difference = mean(mean(a-b for a, b in values) for values in pairs.values())
    diff_terms = []
    for values in pairs.values():
        differences = [a-b for a, b in values]
        n = len(values)
        diff_terms.append((variance(differences)/n/count**2 if n > 1 else None, n))
    nominal = _interval(difference, diff_terms)
    adjusted = _interval(difference, diff_terms, alpha)
    relative_difference = difference/comparator if comparator > 0 else None
    ratio = 1+relative_difference if relative_difference is not None else None
    percent = 100*relative_difference if relative_difference is not None else None
    ratio_terms = []
    if ratio is not None:
        for values in pairs.values():
            influence = [100/comparator*((a-b)-relative_difference*b) for a, b in values]
            n = len(influence)
            ratio_terms.append((variance(influence)/n/count**2 if n > 1 else None, n))
    percent_interval = _interval(percent, ratio_terms, alpha) if ratio is not None else {}
    repetitions = [len(values) for values in pairs.values()]
    return dict(cells=count, pairs=sum(repetitions), replications_min=min(repetitions), replications_max=max(repetitions),
        candidate_regret=candidate, comparator_regret=comparator, mean_ratio=ratio,
        regret_difference=difference, difference_mcse=adjusted["mcse"], difference_df=adjusted["df"],
        difference_ci_low=adjusted["ci_low"], difference_ci_high=adjusted["ci_high"],
        difference_nominal_ci_low=nominal["ci_low"], difference_nominal_ci_high=nominal["ci_high"],
        percent_change=percent, percent_mcse=percent_interval.get("mcse"),
        percent_ci_low=percent_interval.get("ci_low"), percent_ci_high=percent_interval.get("ci_high"),
        percent_df=percent_interval.get("df"),
        percent_status="defined" if ratio is not None else "undefined: zero comparator macro mean")


def _contrasts(rows, roles, primary_groups):
    by_method = defaultdict(dict)
    for row in rows:
        by_method[row["method"]][tuple(row[k] for k in KEY)] = row
    candidates = [m for m, v in roles.items() if v["role"] == "cap_candidate"]
    diagnostics = [m for m, v in roles.items() if v["role"] == "zero_budget_diagnostic"]
    family_size = max(4, len(primary_groups)*2)*len(candidates)
    result = []
    for candidate in (*candidates, *diagnostics):
        for comparator in REFERENCES:
            if comparator == candidate or comparator not in by_method:
                continue
            left, right = by_method[candidate], by_method[comparator]
            for cohort, group in sorted({key[:2] for key in left}):
                left_keys = {k for k in left if k[:2] == (cohort, group)}
                right_keys = {k for k in right if k[:2] == (cohort, group)}
                if left_keys != right_keys:
                    raise ValueError(f"Unpaired histories for {candidate}/{comparator} in {cohort}/{group}: "
                                     f"{len(left_keys-right_keys)} candidate-only, {len(right_keys-left_keys)} comparator-only")
                pairs = defaultdict(list)
                for key in sorted(left_keys):
                    for field in ("T", "K", "epsilon", "eta", "delta"):
                        if (left[key].get(field) is not None and right[key].get(field) is not None
                                and float(left[key][field]) != float(right[key][field])):
                            raise ValueError(f"Paired endpoints disagree on {field}: {key}")
                    pairs[key[2:4]].append((left[key]["regret"], right[key]["regret"]))
                primary = candidate in candidates and comparator in PRIMARY_REFERENCES and group in primary_groups
                alpha = .05/family_size if primary else .05
                result.append(dict(cohort=cohort, group=group, candidate=candidate,
                    candidate_role=roles[candidate]["role"], cap_multiplier=roles[candidate]["cap_multiplier"],
                    comparator=comparator, primary=primary,
                    family_size=family_size if primary else 1, confidence=1-alpha,
                    unmatched_candidate=0, unmatched_comparator=0,
                    interval="paired stratified t; ratio uses delta method; no across-metric joint claim",
                    **_comparison(pairs, alpha)))
    return result, family_size


def _write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row)) or ["status"]
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _slug(value):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value)


def _save(fig, destination):
    files = []
    for extension in ("pdf", "png", "svg"):
        path = destination.with_suffix("."+extension)
        fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
        files.append(str(path))
    return files


def _figures(out, roles, group_rows, comparisons, scopes, primary_groups):
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    style = {"font.family": "serif", "font.serif": ["DejaVu Serif"],
             "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
             "legend.fontsize": 7, "legend.frameon": False,
             "axes.spines.top": False, "axes.spines.right": False,
             "axes.axisbelow": True, "pdf.fonttype": 42, "ps.fonttype": 42,
             "svg.fonttype": "none", "lines.linewidth": 1.6}
    scope_lookup = {(v["cohort"], v["group"]): v for v in scopes}
    files = []
    for cohort in sorted({row["cohort"] for row in group_rows}):
        groups = sorted({row["group"] for row in group_rows if row["cohort"] == cohort})
        primary_available = [group for group in primary_groups if group in groups]
        groups = primary_available or groups
        lookup = {(r["group"], r["method"]): r for r in group_rows if r["cohort"] == cohort}
        with plt.rc_context(style):
            fig, axes = plt.subplots(1, len(groups), figsize=(3.7*len(groups), 3.35), squeeze=False)
            for ax, group in zip(axes.flat, groups):
                points = [(roles[m]["cap_multiplier"], lookup[(group, m)]) for m in roles
                          if roles[m]["role"] == "cap_candidate" and (group, m) in lookup]
                points.sort(key=lambda point: (point[0], point[1]["method"]))
                if points:
                    x = [a for a, _ in points]
                    y = np.array([r["regret_mean"] for _, r in points])
                    errors = np.array([r["regret_mcse"] or 0. for _, r in points])
                    ax.errorbar(x, y, yerr=errors, color=COLORS["candidate"], marker="o",
                                markersize=4, capsize=2, label="SRC-KL cap sweep (1 MCSE)")
                    ax.set_xscale("log")
                    ax.set_xticks(sorted(set(x)), [f"{a:g}" for a in sorted(set(x))])
                for reference, linestyle in zip(REFERENCES, ("--", ":", "-.", (0, (5, 2)))):
                    row = lookup.get((group, reference))
                    if row:
                        ax.axhline(row["regret_mean"], color=COLORS[reference], linestyle=linestyle,
                                   linewidth=1.25, label=reference)
                for method, role in roles.items():
                    row = lookup.get((group, method))
                    if role["role"] == "zero_budget_diagnostic" and row:
                        ax.axhline(row["regret_mean"], color=COLORS["diagnostic"], linestyle=(0, (1, 2)),
                                   label=f"{method} (zero reward budget)")
                scope = scope_lookup[(cohort, group)]
                horizon = ("/".join(map(str, scope["horizons"])) if len(scope["horizons"]) <= 3
                           else f"{min(scope['horizons'])}-{max(scope['horizons'])} ({len(scope['horizons'])} horizons)")
                ax.set_title(f"{group} | T={horizon}\n{scope['size_label']}", fontsize=8.2)
                ax.set_xlabel("Cap multiplier a (log scale)")
                ax.set_ylabel("Equal-cell mean dynamic regret")
                ax.grid(True, alpha=.18)
                ax.legend(loc="best")
            fig.suptitle(f"SRC-KL cap sensitivity | cohort: {cohort}\nc=0.5, beta_R=32, lambda=0; no parameter selected here", fontsize=10)
            fig.tight_layout(rect=(0, .03, 1, .87))
            files += _save(fig, out / ("cap_sensitivity_"+_slug(cohort)))
            plt.close(fig)
            candidates = sorted((m for m in roles if roles[m]["role"] == "cap_candidate"),
                                key=lambda m: (roles[m]["cap_multiplier"], m))
            columns = [(g, b) for g in groups for b in PRIMARY_REFERENCES]
            matrix = np.full((len(candidates), len(columns)), np.nan)
            contrast_lookup = {(r["candidate"], r["group"], r["comparator"]): r
                               for r in comparisons if r["cohort"] == cohort}
            for i, candidate in enumerate(candidates):
                for j, (group, baseline) in enumerate(columns):
                    value = contrast_lookup.get((candidate, group, baseline), {}).get("percent_change")
                    if value is not None:
                        matrix[i, j] = value
            limit = max(1., float(np.nanmax(np.abs(matrix)))) if np.any(np.isfinite(matrix)) else 1.
            cmap = LinearSegmentedColormap.from_list("okabe_blue_orange", ["#0072B2", "#FAFAFA", "#D55E00"])
            fig, ax = plt.subplots(figsize=(max(5.8, len(columns)*1.5), max(2.6, len(candidates)*.38+1.8)))
            heat = ax.imshow(np.ma.masked_invalid(matrix), aspect="auto", cmap=cmap,
                             norm=TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit))
            ax.set_xticks(range(len(columns)), [f"{group}\n{baseline}" for group, baseline in columns], fontsize=8)
            ax.set_yticks(range(len(candidates)), [f"a={roles[m]['cap_multiplier']:g} | {m}" for m in candidates], fontsize=8)
            for i in range(len(candidates)):
                for j in range(len(columns)):
                    value = matrix[i, j]
                    label = f"{value:+.1f}%" if math.isfinite(value) else "undefined"
                    ax.text(j, i, label, ha="center", va="center", fontsize=8,
                            color="white" if math.isfinite(value) and abs(value)>.65*limit else "#222222")
            ax.set_title(f"Candidate/reference macro mean regret change | {cohort}\nNegative means lower regret; no significance stars", fontsize=10)
            fig.colorbar(heat, ax=ax, fraction=.04, pad=.03, label="100 x (candidate / reference - 1)")
            fig.tight_layout()
            files += _save(fig, out / ("candidate_comparison_"+_slug(cohort)))
            plt.close(fig)
    return files


def validate_primary_declarations(config):
    """This entry replays the fixed two-group, two-baseline, alpha=.05 check."""
    holders = [config, config.get("study", {})]
    holders.extend(task.get("diagnostics", {}) for task in config.get("tasks", []))
    for diagnostic in holders:
        for field, expected in (("primary_groups", {"f17", "adaptive"}),
                                ("primary_baselines", {"IMED", "Empirical-KL-UCB"})):
            if field in diagnostic and (len(diagnostic[field]) != 2 or set(diagnostic[field]) != expected):
                raise ValueError("Unsupported frozen primary declaration: " + field)
        if "primary_alpha" in diagnostic and float(diagnostic["primary_alpha"]) != .05:
            raise ValueError("Unsupported frozen primary declaration: primary_alpha")


def recorded_provenance(config):
    """Read producer and runtime provenance entirely from the local snapshot."""
    validate_primary_declarations(config)
    annotations = [task.get("diagnostics", {}) for task in config.get("tasks", [])]
    if not annotations or not config.get("source_files"):
        raise ValueError("Configuration must retain tasks and its source snapshot")
    revisions = {item.get("study_revision") for item in annotations}
    caches = {json.dumps(item.get("numba_cache"), sort_keys=True) for item in annotations}
    if len(revisions) != 1 or len(caches) != 1 or None in revisions:
        raise ValueError("Task producer revisions or runtime caches disagree")
    cache = annotations[0].get("numba_cache")
    if not isinstance(cache, dict) or not cache.get("source_fingerprint") or not cache.get("effective_cache_dir"):
        raise ValueError("Missing source-isolated runtime cache provenance")
    declared = {item.get("primary_comparison_family_size") for item in annotations
                if item.get("primary_comparison_family_size") is not None}
    primaries = _study_metadata(config).get("candidate_methods")
    if declared and (len(declared) != 1 or primaries is None or next(iter(declared)) != 4*len(set(primaries))):
        raise ValueError("Frozen primary family must count actual unique candidates")
    replay = annotations[0].get("replay_parameter_check")
    if any(item.get("replay_parameter_check") != replay for item in annotations):
        raise ValueError("Replay entry/configuration fingerprints disagree")
    return dict(study_revision=next(iter(revisions)), runtime_cache=cache,
                replay_parameter_check=replay, source_snapshot=config["source_files"])
