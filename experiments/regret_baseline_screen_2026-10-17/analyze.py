"""Descriptive paired analysis; never selects or changes policy settings."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t as student_t


def se(values):
    x = np.asarray(values, float)
    return float(np.std(x, ddof=1) / np.sqrt(len(x))) if len(x) > 1 else float("nan")


def analyze(folder, protocol_path=None, allow_partial=False):
    folder = Path(folder)
    # Exclude our own derived runs-all.csv on subsequent analysis calls.
    files = sorted(folder.glob("runs-[0-9][0-9].csv"))
    if not files:
        raise RuntimeError("No scenario result files")
    rows = pd.concat([pd.read_csv(p) for p in files], ignore_index=True)
    if rows.duplicated(["scenario", "rep", "method"]).any():
        raise RuntimeError("Duplicate scenario/rep/method rows")
    if not rows.status.eq("ok").all():
        raise RuntimeError("Errored runs cannot be silently omitted")
    if not np.isfinite(rows.regret).all() or not rows.total_pulls.eq(rows["T"]).all() or (rows.regret < -1e-12).any():
        raise RuntimeError("Invalid trajectory accounting")
    if rows.protocol_sha256.nunique() != 1 or rows.source_payload_sha256.nunique() != 1:
        raise RuntimeError("Mixed source/protocol versions")
    pair_columns = ["means_sha256", "rewards_sha256", "policy_seed", "reward_seed", "T", "K"]
    if (rows.groupby(["scenario", "rep"])[pair_columns].nunique() != 1).any().any():
        raise RuntimeError("Methods did not use exactly paired environment payloads")
    n_methods = rows.method.nunique()
    counts = rows.groupby(["scenario", "method"]).size()
    if counts.nunique() != 1:
        raise RuntimeError("Unbalanced result matrix")
    protocol_path = Path(protocol_path) if protocol_path is not None else Path(__file__).resolve().parent / "protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    expected_names = {m["name"] for m in protocol["methods"]}
    if len(expected_names) != len(protocol["methods"]) or set(rows.method) != expected_names:
        raise RuntimeError("Protocol methods missing, duplicated, or unexpected in results")
    protocol_hash = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    if rows.protocol_sha256.iloc[0] != protocol_hash:
        raise RuntimeError("Result protocol hash differs from the analyzed protocol")
    original_path = Path(__file__).resolve().parent.parent / "fccp_frozen" / "protocols" / "holdout-freeze.json"
    original = json.loads(original_path.read_text(encoding="utf-8"))
    if protocol.get("original_protocol_sha256") not in {None, hashlib.sha256(original_path.read_bytes()).hexdigest()}:
        raise RuntimeError("Screen protocol does not refer to the original holdout")
    if not allow_partial:
        if len(original["scenarios"]) != 12 or original["reps"] != 96 or protocol.get("reps", 96) != 96:
            raise RuntimeError("A formal screen requires all 12 original scenarios and 96 replications")
        expected = {(si, s["name"], r, method) for si, s in enumerate(original["scenarios"]) for r in range(96) for method in expected_names}
        actual = set(rows[["scenario_index", "scenario", "rep", "method"]].itertuples(index=False, name=None))
        if actual != expected or len(rows) != len(expected):
            raise RuntimeError(f"Formal screen is not the full 12 x 96 x methods matrix: expected {len(expected)}, actual {len(rows)}")
        for si, scenario in enumerate(original["scenarios"]):
            data = rows.loc[rows.scenario_index == si]
            if not data["T"].eq(scenario["T"]).all() or not data.K.eq(len(scenario["means"])).all():
                raise RuntimeError("Debug horizon or incorrect arm count cannot enter the formal screen")
        info_path = folder / "run-info.json"
        if info_path.exists():
            info = json.loads(info_path.read_text(encoding="utf-8"))
            if info.get("horizon_debug") is not None or not info.get("full_prespecified_run", False):
                raise RuntimeError("Run metadata identifies a debug/partial run, not a formal screen")
    if rows.rep.min() < 0 or (rows.rep % 1 != 0).any():
        raise RuntimeError("Invalid replication indices")
    for record in rows.itertuples(index=False):
        c = np.asarray(json.loads(record.counts))
        if len(c) != record.K or np.any(c < 0) or np.any(c % 1 != 0) or int(c.sum()) != record.T:
            raise RuntimeError("Per-arm counts do not match total physical observations")
    rows.sort_values(["scenario_index", "rep", "method"]).to_csv(folder / "runs-all.csv", index=False)
    summaries = []
    for (si, scenario, method), d in rows.groupby(["scenario_index", "scenario", "method"]):
        values = d.regret.to_numpy()
        count_array = np.stack(d.counts.map(lambda x: np.asarray(json.loads(x), dtype=int)))
        summaries.append(dict(scenario_index=si, scenario=scenario, method=method, n=len(d), T=int(d["T"].iloc[0]),
            mean=float(values.mean()), mcse=se(values), median=float(np.median(values)), sd=float(np.std(values, ddof=1)),
            quantile90=float(np.quantile(values, .9)), quantile95=float(np.quantile(values, .95)), max=float(values.max()),
            upper10_mean=float(np.sort(values)[-max(1, int(np.ceil(.1 * len(values)))):].mean()),
            mean_unpulled_arms=float((count_array == 0).sum(axis=1).mean()),
            sum_runtime_seconds=float(d.runtime_seconds.sum())))
    summary = pd.DataFrame(summaries).sort_values(["scenario_index", "mean"])
    summary.to_csv(folder / "summary.csv", index=False)
    pivot = rows.pivot(index=["scenario_index", "scenario", "rep"], columns="method", values="regret")
    if pivot.isna().any().any() or "F-R" not in pivot.columns:
        raise RuntimeError("Incomplete paired comparisons or missing F-R")
    tests = (n_methods - 1) * rows.scenario.nunique()
    differences = []
    for (si, scenario), p in pivot.groupby(level=[0, 1]):
        reference = p["F-R"].to_numpy()
        for method in p.columns:
            values = p[method].to_numpy()
            d = values - reference
            sem = se(d)
            radius = float(student_t.ppf(.975, len(d) - 1) * sem)
            simultaneous = float(student_t.ppf(1 - .05 / (2 * max(1, tests)), len(d) - 1) * sem)
            ratio = float(values.mean() / reference.mean())
            # Delta-method uncertainty for a ratio of paired means includes the
            # denominator variance and its covariance with the numerator.
            ratio_sem = se(values - ratio * reference) / float(reference.mean())
            differences.append(dict(scenario_index=si, scenario=scenario, method=method, n=len(d),
                mean_regret=float(values.mean()), reference_mean=float(reference.mean()), ratio_to_FR=ratio, ratio_mcse_delta=ratio_sem,
                mean_regret_mcse=se(values),
                paired_difference=float(d.mean()), paired_mcse=sem, ci95_low=float(d.mean() - radius), ci95_high=float(d.mean() + radius),
                simultaneous95_low=float(d.mean() - simultaneous), simultaneous95_high=float(d.mean() + simultaneous),
                rep_win_fraction=float(np.mean(d < 0)), rep_tie_fraction=float(np.mean(d == 0))))
    paired = pd.DataFrame(differences).sort_values(["scenario_index", "paired_difference"])
    paired.to_csv(folder / "paired-vs-FR.csv", index=False)
    suite = []
    scenario_count = rows.scenario.nunique()
    for method, d in paired.groupby("method"):
        # Equal weight per prespecified scenario. Different scenario seeds are
        # independent; combine their Monte Carlo variances rather than treating
        # heterogeneous scenario means as random observations.
        mean = float(d.mean_regret.mean())
        sem = float(np.sqrt(np.sum(d.paired_mcse.to_numpy() ** 2)) / scenario_count)
        difference = float(d.paired_difference.mean())
        normalized_sem = float(np.sqrt(np.sum(d.ratio_mcse_delta.to_numpy() ** 2)) / scenario_count)
        ratios = d.ratio_to_FR.to_numpy()
        crit = float(student_t.ppf(.975, int(d.n.min()) - 1))
        suite.append(dict(method=method, n_scenarios=len(d), n_per_scenario=int(d.n.min()),
            mean_scenario_regret=mean, mean_regret_mcse=float(np.sqrt(np.sum(d.mean_regret_mcse.to_numpy() ** 2)) / scenario_count),
            mean_paired_difference=difference, paired_mcse=sem,
            ci95_low=difference - crit * sem, ci95_high=difference + crit * sem,
            equal_scenario_mean_ratio_to_FR=float(np.mean(ratios)), mean_ratio_mcse_delta=normalized_sem,
            scenarios_lower_mean=int((d.paired_difference < 0).sum()),
            scenarios_unadjusted_significant_lower=int((d.ci95_high < 0).sum()),
            scenarios_unadjusted_significant_higher=int((d.ci95_low > 0).sum()),
            scenarios_familywise_lower=int((d.simultaneous95_high < 0).sum()),
            scenarios_familywise_higher=int((d.simultaneous95_low > 0).sum())))
    suite = pd.DataFrame(suite).sort_values("equal_scenario_mean_ratio_to_FR")
    suite.to_csv(folder / "suite-summary.csv", index=False)
    references = rows[rows.frozen_regret.notna()]
    historical = []
    for method, d in references.groupby("method"):
        absdiff = np.abs(d.difference_from_frozen.to_numpy())
        historical.append(dict(method=method, n=len(d), max_absolute_difference=float(absdiff.max()),
            differences_above_1e_9=int((absdiff > 1e-9).sum()), differences_above_1e_6=int((absdiff > 1e-6).sum())))
    pd.DataFrame(historical).to_csv(folder / "historical-reference-check.csv", index=False)
    meta = dict(passed=True, formal_complete_matrix=not allow_partial, rows=len(rows), methods=n_methods, scenarios=scenario_count,
        repetitions_per_cell=int(counts.iloc[0]), protocol_sha256=rows.protocol_sha256.iloc[0], source_payload_sha256=rows.source_payload_sha256.iloc[0],
        interval_note="Paired two-sided Student t intervals; Bonferroni simultaneous intervals cover all non-F-R methods times scenarios. Descriptive screening on an already observed holdout, not a fresh confirmatory test.",
        suite_note="Equal scenario weighting. Raw cumulative regret has scenario-dependent horizon/gaps. Mean ratio SE uses a paired delta approximation, including denominator covariance. Aggregate paired-difference intervals conservatively use the smallest per-scenario degrees of freedom; cross-scenario seeds are independent.",
        historical_references=historical)
    (folder / "analysis-audit.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(suite.to_string(index=False))
    return summary, paired, suite


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("folder", type=Path)
    p.add_argument("--protocol", type=Path)
    p.add_argument("--allow-partial", action="store_true", help="Explicitly label debug/partial analyses; forbidden for the final full screen")
    a = p.parse_args()
    analyze(a.folder, a.protocol, a.allow_partial)
