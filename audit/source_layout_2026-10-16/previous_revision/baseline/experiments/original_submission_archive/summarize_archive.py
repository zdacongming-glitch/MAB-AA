"""Preserve and summarize the original submitted experiments; run no simulations.

Default: summarize the local, unmodified archival CSVs.  --collect additionally
copies the explicitly enumerated original sources and figures into this new
archive.  An existing unequal destination is never overwritten by collection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parent
PAPER = ROOT.parents[1]
REPOSITORY = PAPER.parent
ORIGINAL = Path("D:/博士学习/科研/Projects/Bandit with Arriving Arms/simulation_final")
METHODS = ["custom_elim", "ucb", "moss", "naive_elim", "erse"]
NAMES = {
    "custom_elim": "Archived UCB-AA",
    "ucb": "Growing UCB1",
    "moss": "Growing MOSS-t",
    "naive_elim": "Naive elimination",
    "erse": "Dynamic SE",
}
METRICS = ["dynamic_regret", "wasted_pulls_eps_0_05",
           "wasted_pulls_eps_0_1", "final_active_size"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect() -> list[dict]:
    copies = []
    source_names = ["algos.py", "env.py", "runner.py", "ce_five_algo_runner.py",
                    "scenario_ce_runner.py", "plots.py"]
    planned = [(ORIGINAL / name, ROOT / "source" / name) for name in source_names]
    for scenario in ["C", "E"]:
        base = ORIGINAL / "outputs" / "final" / f"scenario_{scenario}"
        for name in ["config.json", "raw_final.csv", "agg_final.csv"]:
            planned.append((base / name, ROOT / f"scenario_{scenario}" / name))
        for suffix in ["dynamic_regret_vs_t", "wasted_pulls_eps_0_1", "arm_set_size_vs_t"]:
            name = f"scenario_{scenario}_{suffix}.png"
            planned.append((REPOSITORY / "JASA-template" / name,
                            PAPER / "figures" / "original_submission" / name))
    for source, destination in planned:
        if not source.is_file():
            raise FileNotFoundError(source)
        destination.resolve().relative_to(PAPER.resolve())
        source_hash = sha256(source)
        if destination.exists():
            if sha256(destination) != source_hash:
                raise RuntimeError(f"Refusing to replace unequal archive file: {destination}")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        assert sha256(destination) == source_hash
        copies.append({"source": source.as_posix(),
                       "archive": destination.relative_to(PAPER).as_posix(),
                       "bytes": source.stat().st_size,
                       "sha256": source_hash})
    return copies


def statistics(values) -> dict:
    values = np.asarray(values, dtype=float)
    n = len(values)
    mean = float(values.mean())
    sd = float(values.std(ddof=1))
    se = sd / np.sqrt(n)
    half = float(student_t.ppf(0.975, n - 1) * se)
    return {"n": n, "mean": mean, "sd": sd, "se": float(se),
            "ci95_low": mean - half, "ci95_high": mean + half}


def summarize() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    rows, pairs, checks = [], [], {}
    for scenario, expected_m in [("C", 5), ("E", 4)]:
        config = json.loads((ROOT / f"scenario_{scenario}" / "config.json").read_text())
        raw = pd.read_csv(ROOT / f"scenario_{scenario}" / "raw_final.csv")
        archived_aggregate = pd.read_csv(ROOT / f"scenario_{scenario}" / "agg_final.csv").set_index("algo")
        assert len(raw) == 500 and not raw.duplicated(["algo", "replicate"]).any()
        assert set(raw["algo"]) == set(METHODS)
        assert set(raw["replicate"]) == set(range(100))
        assert set(raw["T"]) == {60000} and set(raw["steps_completed"]) == {60000}
        assert config["final_R"] == 100 and config["seed"] == 20260309
        assert config["best_config"]["M"] == expected_m
        assert config["best_config"]["arrival_mode"] == "bernoulli"
        for encoded in raw["params_json"].unique():
            assert json.loads(encoded) == config["best_config"]
        custom = raw[raw["algo"] == "custom_elim"].set_index("replicate").sort_index()
        for info in custom["algo_info_json"]:
            assert json.loads(info)["effective_M"] == expected_m
        for method in METHODS:
            selected = raw[raw["algo"] == method].set_index("replicate").sort_index()
            assert len(selected) == 100
            row = {"scenario": scenario, "algorithm": method, "method": NAMES[method],
                   "T": 60000, "planned_M": expected_m,
                   "status": "original_archived_implementation_not_revised_validation"}
            for metric in METRICS:
                stats = statistics(selected[metric])
                assert np.isclose(stats["mean"], archived_aggregate.loc[method, f"{metric}_mean"], rtol=1e-12, atol=1e-10)
                assert np.isclose(stats["sd"], archived_aggregate.loc[method, f"{metric}_std"], rtol=1e-12, atol=1e-10)
                for key, value in stats.items():
                    row[f"{metric}_{key}"] = value
            rows.append(row)
            if method != "custom_elim":
                for metric in METRICS:
                    paired = custom[metric] - selected[metric]
                    pairs.append({"scenario": scenario, "candidate": "custom_elim",
                                  "comparator": method, "metric": metric,
                                  "contrast": "archived_UCB_AA_minus_comparator",
                                  **statistics(paired)})
        checks[scenario] = {"rows": len(raw), "methods": len(METHODS),
                            "replications_per_method": 100, "replicate_ids": "0 through 99", "T": 60000,
                            "M": expected_m, "master_seed": config["seed"],
                            "raw_configuration_matches_archive": True,
                            "recomputed_means_and_SD_match_archived_aggregate": True,
                            "custom_effective_M_matches_configuration": True}
    return pd.DataFrame(rows), pd.DataFrame(pairs), checks


def table(summary: pd.DataFrame) -> str:
    lines = [r"% Recomputed from archived raw_final.csv; no new simulation was run.",
             r"\begin{table}[tbp]", r"\centering", r"\small",
             r"\caption{Original archived experiments at $T=60{,}000$ (100 replications per scenario and method). Entries are means with Monte Carlo standard errors in parentheses. Archived UCB-AA is the explore-then-commit implementation with $M=5$ in C and $M=4$ in E; these are not validation results for a repaired or continuously admitting implementation. Buffered arrivals excluded from the final active count were not necessarily screened or certified inferior.}",
             r"\label{tab:original-archive}",
             r"\begin{tabular}{llrrr}", r"\toprule",
             r"Scenario & Method & $R_T$ & $W_T$ ($0.1$) & Final active \\",
             r"\midrule"]
    for scenario in ["C", "E"]:
        for method in METHODS:
            row = summary[(summary.scenario == scenario) & (summary.algorithm == method)].iloc[0]
            formatted = []
            for metric in ["dynamic_regret", "wasted_pulls_eps_0_1", "final_active_size"]:
                formatted.append(f"{row[f'{metric}_mean']:,.1f} ({row[f'{metric}_se']:.1f})")
            lines.append(f"{scenario} & {NAMES[method]} & " + " & ".join(formatted) + r" \\")
        if scenario == "C":
            lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collect", action="store_true")
    args = parser.parse_args()
    metadata_path = ROOT / "metadata.json"
    if args.collect:
        copied = collect()
    else:
        copied = json.loads(metadata_path.read_text(encoding="utf-8"))["preserved_files"]
        for item in copied:
            assert sha256(PAPER / item["archive"]) == item["sha256"]
    summary, paired, checks = summarize()
    summary.to_csv(ROOT / "summary.csv", index=False, float_format="%.12g")
    paired.to_csv(ROOT / "paired_differences.csv", index=False, float_format="%.12g")
    (ROOT / "table_original_archive.tex").write_text(table(summary), encoding="utf-8")
    metadata = {
        "created_date": "2026-10-15", "archive_status": "historical_experiments_only",
        "new_simulations_run": 0,
        "implementation": "Original archived explore-then-commit implementation, not a repaired theoretical Algorithm 1 and not CP-UCB-AA or AA-FB.",
        "original_root": ORIGINAL.as_posix(), "original_results_seed": 20260309,
        "source_policy": "All original files copied byte-for-byte; originals read only.",
        "summaries": {"metrics": METRICS,
                      "standard_error": "Sample SD with ddof=1 divided by sqrt(n).",
                      "intervals": "Two-sided pointwise 95% Student-t Monte Carlo intervals with n-1 degrees of freedom; no multiplicity adjustment or correction for historical tuning.",
                      "historical_interval_difference": "Original agg_final.csv used 1.96*SE. This summary uses the Student-t critical value while preserving the same means and sample SDs.",
                      "pairing": "Differences use matching replicate IDs within a scenario.",
                      "active_size": "Original recorded final active size; not total storage, certified quality, or evidence that all later arrivals were screened."},
        "checks": checks, "preserved_files": copied,
        "specification_discrepancies": [
            {"item": "C background arrivals", "manuscript": "Poisson", "archived": "Bernoulli probability 0.005"},
            {"item": "C step starting parameter r0", "manuscript": "0.6 in main text; 0.7 in supplement", "archived": 0.7},
            {"item": "E near-optimal means", "manuscript": "[0.7,0.8] in main text; [0.89,0.90] in supplement", "archived": "Uniform[0.75,0.90]"},
            {"item": "M", "manuscript": "Not specified for experiments", "archived": "C:5; E:4"},
            {"item": "Growing MOSS clock", "manuscript": "T in main text; t in supplement", "archived": "current t"},
            {"item": "Formal elimination reference set", "manuscript": "merged active set", "archived": "C_prev when nonempty"},
            {"item": "Empirical means", "manuscript": "first n_p observations", "archived": "all observations obtained so far"},
            {"item": "After completion of planned rounds", "manuscript": "Not fully specified to physical horizon", "archived": "Fixed exploit pool; later arrivals remain buffered and are not admitted"},
            {"item": "Arrival timing", "manuscript": "Available-arm decision formulation", "archived": "An action is selected before env.step reveals arrivals at that time; regret benchmark includes the arrivals"},
            {"item": "Budget truncation", "manuscript": "Full phase target", "archived": "A phase can end at T before its target and still evaluate elimination with the planned phase radius"}
        ],
        "not_preserved": [{"files": "raw_checkpoint.csv in both source scenarios",
                           "reason": "Approximately 380 MB combined; final raw observations and six original figures are preserved here. Historical trajectories remain at the recorded source root; no trajectory is reconstructed from the final table."}],
        "outputs": ["summary.csv", "paired_differences.csv", "table_original_archive.tex"],
        "output_sha256": {name: sha256(ROOT / name) for name in ["summary.csv", "paired_differences.csv", "table_original_archive.tex"]},
        "summarizer_sha256": sha256(Path(__file__)),
        "recompute_command": "python -B experiments/original_submission_archive/summarize_archive.py"
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"archive": ROOT.as_posix(), "summary_rows": len(summary),
                      "paired_rows": len(paired), "checks": checks}, ensure_ascii=False))


if __name__ == "__main__":
    main()
