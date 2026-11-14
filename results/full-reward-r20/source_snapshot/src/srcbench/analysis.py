"""Read-only scientific aggregation of a srcbench run, with explicit pairing.

Analysis never removes a trajectory for a coverage, label, or intersection flag.
The semicolon-delimited ``suites`` field is membership, not another simulation.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import html
import json
import itertools
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import NormalDist, mean, variance

KEYS = ("cohort", "group", "layout_id", "law", "rep", "method")
CELL = ("cohort", "group", "suite", "layout_id", "law", "method")
METRICS = ("regret", "area", "area_all", "eta_fraction", "all_fraction",
           "service_fraction", "unseen_fraction", "service_pulls", "service_denials",
           "guard_exclusions", "guard_changed", "final_unresolved", "reward_tax",
           "service_tax", "checkpoint_hits", "runtime_seconds", "service_regret",
           "service_mass", "old_arms", "old_never_sampled", "old_unseen_fraction")
FLAGS = ("label_error", "coverage_error", "empty_intersection")


def _read(path):
    return list(_iter_rows(path))


def _iter_rows(path):
    path = Path(path)
    if not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def _input_rows(root, name):
    path = Path(root) / f"{name}.csv.gz"
    return _iter_rows(path if path.exists() else Path(root) / f"{name}.csv")


def _number(value, default=0.0):
    if value is None or value == "":
        return default
    if str(value).lower() in ("true", "false"):
        return float(str(value).lower() == "true")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"Nonfinite scientific value: {value!r}")
    return result


def _key(row):
    return tuple(str(row.get(k, "")) for k in KEYS)


def _members(row):
    value = row.get("suites", row.get("suite", "reward"))
    suites = value if isinstance(value, list) else str(value).split(";")
    return tuple(dict.fromkeys(str(x).strip() for x in suites if str(x).strip()))


def _ratio(a, b):
    return a / b if b > 0 else None


def _prepare(rows):
    seen = set()
    out = []
    for original in rows:
        key = _key(original)
        if key in seen:
            raise ValueError(f"Duplicate trajectory key: {key}")
        seen.add(key)
        row = dict(original)
        for field in (*METRICS, *FLAGS, "T", "K", "eligible_arm_time", "all_arm_time",
                      "never_sampled", "service_attempts", "epsilon", "eta", "delta"):
            if field not in ("eta_fraction", "all_fraction", "service_fraction", "unseen_fraction", "old_unseen_fraction"):
                row[field] = _number(row.get(field))
        row["eta_fraction"] = _ratio(row["area"], row["eligible_arm_time"])
        row["all_fraction"] = _ratio(row["area_all"], row["all_arm_time"])
        row["service_fraction"] = _ratio(row["service_pulls"], row["T"])
        row["unseen_fraction"] = _ratio(row["never_sampled"], row["K"])
        row["old_unseen_fraction"] = _ratio(row["old_never_sampled"], row["old_arms"])
        row["suites"] = ";".join(_members(row))
        out.append(row)
    return out


def _expanded(rows):
    return [dict(row, suite=suite) for row in rows for suite in _members(row)]


def _stats(values):
    values = [x for x in values if x is not None]
    n = len(values)
    if not n:
        return {"n": 0, "mean": None, "mcse": None}
    return {"n": n, "mean": mean(values),
            "mcse": math.sqrt(variance(values) / n) if n > 1 else None}


def _write(path, rows, preferred=()):
    fields = list(preferred)
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    if not fields:
        fields = ["status"]
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _groups(rows, keys):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row.get(k, "") for k in keys)].append(row)
    return groups


def _cell_summaries(rows):
    result = []
    for key, block in sorted(_groups(rows, CELL).items(), key=lambda x: str(x[0])):
        record = dict(zip(CELL, key), K=block[0]["K"], T=block[0]["T"], paths=len(block))
        for metric in METRICS:
            for name, value in _stats([row[metric] for row in block]).items():
                record[f"{metric}_{name}"] = value
        for flag in FLAGS:
            record[flag + "_paths"] = sum(row[flag] != 0 for row in block)
        result.append(record)
    return result


def _macro(cells, keys):
    """Each environmental cell has equal weight, independent of its repetitions."""
    result = []
    for key, block in sorted(_groups(cells, keys).items(), key=lambda x: str(x[0])):
        record = dict(zip(keys, key), cells=len(block), paths=sum(r["paths"] for r in block),
                      replications_min=min(r["paths"] for r in block),
                      replications_max=max(r["paths"] for r in block),
                      weighting="equal environmental cell; stratified Monte Carlo SE")
        for metric in METRICS:
            valid = [r for r in block if r.get(metric + "_mean") is not None]
            record[metric + "_cells"] = len(valid)
            record[metric + "_mean"] = mean([r[metric + "_mean"] for r in valid]) if valid else None
            known = valid and all(r.get(metric + "_mcse") is not None for r in valid)
            record[metric + "_mcse"] = (math.sqrt(sum(r[metric + "_mcse"] ** 2 for r in valid))
                                         / len(valid)) if known else None
        for flag in FLAGS:
            record[flag + "_paths"] = sum(r[flag + "_paths"] for r in block)
        result.append(record)
    return result


def _critical(alpha, df):
    try:
        from scipy.stats import t
        return float(t.isf(alpha / 2, df)), "stratified paired t (Satterthwaite)"
    except ImportError:
        return NormalDist().inv_cdf(1 - alpha / 2), "normal approximation (SciPy unavailable)"


def _method_kind(method):
    if method.startswith("SRC-KL"):
        return "kl"
    if method.startswith("SRC"):
        return "src"
    return "baseline"


def _planned_pairs(methods, suite):
    pairs = []
    for method in sorted(methods):
        if method.startswith("SRC-KL"):
            other = method.replace("SRC-KL", "SRC", 1)
            if other in methods:
                pairs.append((method, other, "direct_kl_src",
                              method == "SRC-KL-L060" if "joint" in suite else method == "SRC-KL-R"))
    if "reward" in suite or suite in ("tail", "scale"):
        for target in ("SRC-R", "SRC-KL-R"):
            if target in methods:
                for baseline in sorted(m for m in methods if _method_kind(m) == "baseline"):
                    pairs.append((target, baseline, "reward_baselines", True))
    if "joint" in suite:
        for target in ("SRC-L060", "SRC-KL-L060"):
            if target not in methods:
                continue
            for control in sorted(methods):
                text = control.lower()
                if ("widest" in text or "lucb" in text) and ("060" in text or "0.6" in text):
                    if (target.startswith("SRC-KL") == control.startswith("SRC-KL")):
                        pairs.append((target, control, "matched_planner", True))
    return list(dict.fromkeys(pairs))


def _paired_estimate(left, right, metric):
    common = sorted(set(left) & set(right))
    cells = defaultdict(list)
    for key in common:
        a, b = left[key].get(metric), right[key].get(metric)
        if a is not None and b is not None:
            cells[key[:-1]].append(a - b)
    if not cells:
        return None
    parts = [_stats(values) for values in cells.values()]
    c = len(parts)
    estimate = mean([part["mean"] for part in parts])
    complete_se = all(part["mcse"] is not None for part in parts)
    terms = [(part["mcse"] / c) ** 2 for part in parts] if complete_se else []
    total = sum(terms)
    denom = sum(term ** 2 / (part["n"] - 1) for term, part in zip(terms, parts))
    df = total ** 2 / denom if denom > 0 else (sum(p["n"] for p in parts) - c)
    return {"cells": c, "pairs": sum(p["n"] for p in parts), "difference": estimate,
            "mcse": math.sqrt(total) if complete_se else None, "df": df,
            "replications_min": min(p["n"] for p in parts),
            "replications_max": max(p["n"] for p in parts),
            "unmatched_left": len(set(left) - set(right)),
            "unmatched_right": len(set(right) - set(left))}


def _comparisons(rows, by=()):
    outer = ("cohort", "group", "suite", *by)
    results = []
    for key, block in sorted(_groups(rows, outer).items(), key=lambda x: str(x[0])):
        methods = _groups(block, ("method",))
        mapping = {name[0]: {(r["layout_id"], r["law"], str(r["rep"])): r for r in entries}
                   for name, entries in methods.items()}
        suite = str(key[2])
        pairs = _planned_pairs(set(mapping), suite)
        metrics = ("regret", "area", "area_all", "eta_fraction") if "joint" in suite else ("regret",)
        for metric in metrics:
            family_size = len(pairs)
            for left, right, kind, primary in pairs:
                stats = _paired_estimate(mapping[left], mapping[right], metric)
                if stats is None:
                    continue
                record = dict(zip(outer, key), left=left, right=right, metric=metric,
                              contrast=kind, primary=primary, family_size=family_size,
                              family="/".join(map(str, (*key, metric))),
                              direction="left minus right; lower is smaller cost", **stats)
                se, df = stats["mcse"], stats["df"]
                if se is None or df < 1:
                    record.update(ci_low=None, ci_high=None, adjusted_low=None, adjusted_high=None,
                                  interval_method="unavailable: fewer than two pairs per cell")
                else:
                    q, label = _critical(.05, df)
                    qa, _ = _critical(.05 / max(1, family_size), df)
                    record.update(ci_low=stats["difference"] - q * se,
                                  ci_high=stats["difference"] + q * se,
                                  adjusted_low=stats["difference"] - qa * se,
                                  adjusted_high=stats["difference"] + qa * se,
                                  interval_method=label)
                results.append(record)
    return results


def _trajectory_summary(raw, endpoints, config=None):
    memberships = {_key(row): _members(row) for row in endpoints}
    last_arrivals = {layout["id"]: max((a.get("arrival", a.get("birth", 1)) for a in layout.get("arms", [])), default=1)
                     for layout in (config or {}).get("layouts", [])}
    metrics = ("regret", "area", "area_all", "unresolved", "unresolved_all", "service_pulls",
               "never_sampled", "budget_scale", "regret_over_log_t", "regret_over_spectrum")
    macro, closed = {}, set()
    # Runner writes task order (layout/law, then repetitions); one cell's
    # moments suffice even for tens of millions of stored snapshots.
    for cellkey, entries in itertools.groupby(raw, key=lambda r: tuple(r.get(k, "") for k in ("cohort", "group", "layout_id", "law"))):
        if cellkey in closed:
            raise ValueError("Trajectory CSV must keep each cohort/layout/law cell contiguous")
        closed.add(cellkey)
        moments, seen, paths = {}, set(), Counter()
        for original in entries:
            key = (*_key(original), original.get("t"))
            if key in seen:
                raise ValueError(f"Duplicate trajectory snapshot: {key}")
            seen.add(key)
            row = {name: _number(original.get(name)) for name in
                   ("t", "regret", "area", "area_all", "unresolved", "unresolved_all",
                    "service_pulls", "never_sampled", "budget_scale", "K")}
            last_arrival = last_arrivals.get(original.get("layout_id"))
            row["regret_over_log_t"] = (_ratio(row["regret"], math.log(row["t"]))
                                            if row["t"] > 1 and last_arrival is not None and row["t"] >= last_arrival else None)
            denominator = _number(original.get("arrival_spectrum", row["budget_scale"]))
            row["regret_over_spectrum"] = _ratio(row["regret"], denominator)
            for suite in memberships.get(_key(original), _members(original)):
                mkey = (cellkey[0], cellkey[1], suite, original["method"], row["t"])
                paths[mkey] += 1
                state = moments.setdefault(mkey, {metric: [0, 0., 0.] for metric in metrics})
                for metric in metrics:
                    value = row[metric]
                    if value is None:
                        continue
                    acc = state[metric]
                    acc[0] += 1
                    delta = value-acc[1]
                    acc[1] += delta/acc[0]
                    acc[2] += delta*(value-acc[1])
        for key, state in moments.items():
            acc = macro.setdefault(key, dict(cells=0, paths=0, replications_min=math.inf,
                                            replications_max=0, metrics={m: [0, 0., 0., True] for m in metrics}))
            acc["cells"] += 1; acc["paths"] += paths[key]
            acc["replications_min"] = min(acc["replications_min"], paths[key])
            acc["replications_max"] = max(acc["replications_max"], paths[key])
            for metric, (n, avg, m2) in state.items():
                if not n:
                    continue
                target = acc["metrics"][metric]
                target[0] += 1; target[1] += avg
                if n > 1:
                    target[2] += max(0., m2)/(n*(n-1))
                else:
                    target[3] = False
    result = []
    for key, state in sorted(macro.items(), key=lambda x: str(x[0])):
        record = dict(zip(("cohort", "group", "suite", "method", "t"), key))
        record.update({k: v for k, v in state.items() if k != "metrics"})
        for metric, (n, total, se2, known) in state["metrics"].items():
            record[metric+"_mean"] = total/n if n else None
            record[metric+"_mcse"] = math.sqrt(se2)/n if n and known else None
        result.append(record)
    return result


def _count_summaries(raw, endpoints):
    endpoints = {_key(row): row for row in endpoints}
    aggregate, theory = [], []
    closed_runs = set()
    previous_run, previous_t = None, -1
    prepared = (dict(row, t=row.get("t") or endpoints.get(_key(row), {}).get("T", "")) for row in raw)
    for fullkey, entries in itertools.groupby(prepared, key=lambda r: tuple(r.get(k, "") for k in (*KEYS, "t"))):
        block = list(entries)
        key, snapshot_t = fullkey[:-1], _number(fullkey[-1])
        if key != previous_run:
            if key in closed_runs:
                raise ValueError("Count CSV must keep each trajectory contiguous")
            closed_runs.add(key)
            previous_run, previous_t = key, -1
        if snapshot_t <= previous_t:
            raise ValueError(f"Repeated or unordered count checkpoint: {fullkey}")
        previous_t = snapshot_t
        seen = set()
        endpoint = endpoints.get(tuple(map(str, key)))
        if endpoint is None:
            raise ValueError(f"Arm counts have no endpoint: {key}")
        n_values, mature, mature_unseen = [], 0, 0
        t = snapshot_t
        for r in block:
            armkey = r.get("arm")
            if armkey in seen:
                raise ValueError(f"Duplicate arm count: {armkey}")
            seen.add(armkey)
            n = _number(r.get("n")); n_values.append(n)
            old = t - _number(r.get("birth")) + 1 >= t / 4
            mature += old; mature_unseen += old and n == 0
            law = str(r.get("law", "")).lower()
            p, gap = _number(r.get("mean")), _number(r.get("final_gap"))
            m = p + gap
            d = None
            if gap > 0 and 0 < m < 1:
                if "bernoulli" in law:
                    d = (p * math.log(p / m) if p else 0) + ((1-p) * math.log((1-p)/(1-m)) if p < 1 else 0)
                elif law in ("deterministic", "constant", "point_mass"):
                    d = math.log((1-p)/(1-m))
            if d is not None and d > 0 and r.get("method") in ("SRC-R", "SRC-KL-R") and "two_close" in r.get("layout_id", ""):
                theory.append(dict(zip(KEYS, key), arm=r.get("arm"), birth=r.get("birth"),
                                   mean=p, final_gap=gap, current_gap=r.get("current_gap"), n=n, t=t, T=endpoint["T"],
                                   n_over_log_t=n/math.log(t) if t > 1 else None,
                                   src_count_constant=1/gap**2, kl_count_constant=1/d,
                                   assumption="Asymptotic reference only: fixed final arm set, arrivals stop, fixed task parameters, interior best mean; no finite-time equality"))
        if t == endpoint["T"]:
            aggregate.append(dict(zip(KEYS, key), t=t, T=endpoint["T"], sampled_arms=sum(n > 0 for n in n_values),
                                  recorded_arms=len(block), mature_arms=mature, mature_unseen=mature_unseen,
                                  mature_unseen_fraction=_ratio(mature_unseen, mature)))
    return aggregate, theory


def _table(rows, fields, limit=30):
    heads = "".join(f"<th>{html.escape(f)}</th>" for f in fields)
    body = []
    for row in rows[:limit]:
        values = []
        for f in fields:
            value = row.get(f, "")
            text = f"{value:.5g}" if isinstance(value, float) else str(value if value is not None else "—")
            values.append(f"<td>{html.escape(text)}</td>")
        body.append("<tr>" + "".join(values) + "</tr>")
    return "<div class='table'><table><thead><tr>" + heads + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>"


def _tail_summaries(rows):
    result = []
    for key, block in _groups(rows, ("cohort", "group", "suite", "method")).items():
        cells = _groups(block, ("layout_id", "law"))
        weighted = sorted((r["regret"], 1 / (len(cells) * len(cell))) for cell in cells.values() for r in cell)
        record = dict(zip(("cohort", "group", "suite", "method"), key), cells=len(cells), paths=len(block),
                      quantile_definition="equal-cell weighted inverse empirical CDF; descriptive, no extreme-tail precision claim")
        for quantile in (.90, .95, .99):
            cumulative = 0
            selected = weighted[-1][0]
            for value, weight in weighted:
                cumulative += weight
                if cumulative + 1e-14 >= quantile:
                    selected = value; break
            record[f"regret_q{int(quantile * 100)}"] = selected
        record["regret_maximum"] = weighted[-1][0]
        remaining, tail_sum = .05, 0.
        for value, weight in reversed(weighted):
            take = min(remaining, weight)
            tail_sum += take * value
            remaining -= take
            if remaining <= 1e-14:
                break
        record["regret_upper_5pct_mean"] = tail_sum / .05
        result.append(record)
    return result


def _report(out, summary, modules, comparisons, failures):
    smoke = summary["smoke_only"]
    headline = "SMOKE / PIPELINE CHECK ONLY — full scientific study not run" if smoke else summary["scientific_status"]
    intro = ("Small-replication smoke outputs check implementation and reporting. They do not establish superiority, tail reliability, or asymptotic constants."
             if smoke else "Intervals describe Monte Carlo uncertainty conditional on the frozen environmental cells. They do not establish general dominance.")
    sections = [f"<h1>SRC versus SRC-KL benchmark</h1><p class='status'>{html.escape(headline)}</p>",
                f"<p>{intro}</p><p>{summary['unique_trajectories']} unique simulated trajectories; "
                f"{summary['suite_memberships']} analysis memberships. Reused reward/joint endpoints are counted once as simulations.</p>",
                "<p>Every coverage, incorrect-label, and empty-intersection path is retained. Execution failures are separate from these scientific flags. "
                "Cohorts and source groups remain separate. Means weight environmental cells equally; reported SEs are stratified Monte Carlo SEs. "
                "Paired differences are left minus right. Bonferroni families are defined by cohort, group, suite, and metric; subgroup intervals are descriptive.</p>",
                f"<p>Manifest status: {html.escape(str(summary['manifest_status']))}. "
                f"Execution failure records: {summary['execution_failure_records']}. "
                f"Expected unique paths: {summary['expected_unique_trajectories'] or 'unspecified'}.</p>"]
    for cohort in sorted({r["cohort"] for r in modules}):
        sections.append(f"<h2>Cohort: {html.escape(str(cohort))}</h2>")
        subset = [r for r in modules if r["cohort"] == cohort]
        sections.append(_table(subset, ("group", "suite", "method", "cells", "paths", "replications_min", "replications_max", "regret_mean", "regret_mcse", "area_mean", "eta_fraction_mean"), 200))
    sections.append("<h2>Direct matched comparisons</h2>")
    sections.append(_table([r for r in comparisons if r["contrast"] == "direct_kl_src"],
                           ("cohort", "group", "suite", "left", "right", "metric", "pairs", "difference", "mcse", "adjusted_low", "adjusted_high", "unmatched_left", "unmatched_right"), 120))
    sections.append("<h2>Scientific failure flags</h2>")
    sections.append(_table(failures, ("cohort", "group", "suite", "method", "paths", "label_error_paths", "coverage_error_paths", "empty_intersection_paths"), 200))
    sections.append("<p>Complete tables, comparator contrasts, subgroup summaries, diagnostics, and figure captions are supplied as CSV files alongside this report.</p>")
    document = "<!doctype html><html lang='en'><meta charset='utf-8'><title>SRC benchmark analysis</title><style>body{font:15px system-ui;max-width:1500px;margin:32px auto;padding:0 20px;color:#17232d} .status{font-weight:700;background:#fff2cf;padding:15px} .table{overflow:auto}table{border-collapse:collapse;font-size:12px;margin:18px 0}td,th{padding:6px 9px;text-align:right;border-bottom:1px solid #ddd}th{background:#eef4f7}td:first-child,th:first-child{text-align:left}h2{margin-top:35px}</style><body>" + "".join(sections) + "</body></html>"
    (out / "report.html").write_text(document, encoding="utf-8")


def analyze(outputdir):
    """Analyze stored outcomes; write derived files only under ``analysis/``."""
    root = Path(outputdir)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    config_path = root / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    for name in ("runs.csv.gz", "trajectories.csv.gz", "counts.csv.gz"):
        info = manifest.get("files", {}).get(name, {})
        if info.get("sha256") and (root / name).is_file():
            digest = hashlib.sha256()
            with (root / name).open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != info["sha256"]:
                raise ValueError(f"Stored input hash mismatch: {name}")
    runs = _prepare(_input_rows(root, "runs"))
    if not runs:
        raise ValueError("No scientific endpoint records in runs.csv.gz or runs.csv")
    rows = _expanded(runs)
    cells = _cell_summaries(rows)
    macrokeys = ("cohort", "group", "suite", "method")
    modules = _macro(cells, macrokeys)
    density = _macro(cells, (*macrokeys, "K"))
    law = _macro(cells, (*macrokeys, "law"))
    comparisons = _comparisons(rows)
    paired_cells = _comparisons(rows, ("layout_id", "law"))
    failures = []
    for key, block in sorted(_groups(rows, macrokeys).items(), key=lambda x: str(x[0])):
        record = dict(zip(macrokeys, key), paths=len(block))
        for flag in FLAGS:
            record[flag + "_paths"] = sum(r[flag] != 0 for r in block)
        failures.append(record)
    trajectory = _trajectory_summary(_input_rows(root, "trajectories"), runs, config)
    counts, theory = _count_summaries(_input_rows(root, "counts"), runs)
    tails = _tail_summaries(rows)
    profile = str(config.get("profile", manifest.get("profile", "unknown")))
    smoke = "smoke" in profile.lower()
    expected = manifest.get("expected_runs", config.get("expected_runs", config.get("expected_unique_runs")))
    if isinstance(expected, dict):
        expected = expected.get("unique", expected.get("total"))
    failures_raw = manifest.get("failures", manifest.get("execution_failures", []))
    failure_count = len(failures_raw) if isinstance(failures_raw, (list, dict)) else int(failures_raw or 0)
    status = str(manifest.get("status", "UNKNOWN"))
    summary = {"profile": profile, "smoke_only": smoke, "manifest_status": status,
               "scientific_status": "SMOKE_ONLY_FULL_NOT_RUN" if smoke else ("COMPLETE" if status == "PASS" else "INCOMPLETE_EXECUTION"),
               "unique_trajectories": len(runs), "suite_memberships": len(rows),
               "expected_unique_trajectories": expected, "expected_count_matches": expected is None or len(runs) == expected,
               "execution_failure_records": failure_count, "all_scientific_failure_paths_retained": True,
               "unique_by_cohort": dict(Counter(r["cohort"] for r in runs)),
               "membership_by_suite": dict(Counter(r["suite"] for r in rows)),
               "weighting": "equal environmental cell; independent replications within each fixed cell",
               "difference_direction": "left minus right", "bonferroni_family": "cohort/group/suite/metric",
               "files": ["cell_summary.csv", "module_summary.csv", "density_summary.csv", "law_summary.csv",
                         "paired_differences.csv", "paired_cells.csv", "failures.csv", "trajectories_summary.csv",
                         "count_diagnostics.csv", "theory_counts.csv", "tail_summary.csv", "report.html"]}
    if expected is not None and status == "PASS" and len(runs) != expected:
        raise ValueError(f"PASS manifest expects {expected} unique runs, found {len(runs)}")
    out = root / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    for name, data in (("cell_summary", cells), ("module_summary", modules), ("density_summary", density),
                       ("law_summary", law), ("paired_differences", comparisons), ("paired_cells", paired_cells),
                       ("failures", failures), ("trajectories_summary", trajectory),
                       ("count_diagnostics", counts), ("theory_counts", theory), ("tail_summary", tails)):
        _write(out / f"{name}.csv", data)
    _report(out, summary, modules, comparisons, failures)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
