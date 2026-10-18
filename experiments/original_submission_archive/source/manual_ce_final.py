from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict

from scenario_ce_runner import _final_compare_row, _run_grid_for_experiments, _save_final_run, _write_summary

BEST_CONFIGS: Dict[str, Dict[str, Any]] = {
    "C": {
        "scenario": "C",
        "T": 200000,
        "K0": 5,
        "arrival_mode": "bernoulli",
        "lambda": 0.005,
        "rho": 0.005,
        "M": 6,
        "scenario_params": {
            "gamma": [0.2, 0.5, 0.8],
            "Delta_step": 0.05,
            "r0": 0.6,
            "pi_good": 0.1,
            "mu_h": 0.9,
            "delta": 0.1,
            "mu_l": 0.1,
            "mu_m": 0.5,
        },
    },
    "E": {
        "scenario": "E",
        "T": 200000,
        "K0": 20,
        "arrival_mode": "bernoulli",
        "lambda": 0.005,
        "rho": 0.005,
        "M": 6,
        "scenario_params": {
            "m0": 5,
            "Delta_min": 0.01,
            "p_join_near": 0.3,
            "mu_top": 0.8,
            "pi_good": 0.1,
            "mu_h": 0.9,
            "delta": 0.1,
            "mu_l": 0.1,
            "mu_m": 0.5,
        },
    },
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run final four-algorithm evaluation for selected C/E configs")
    parser.add_argument("--output-dir", type=str, default="outputs")
    parser.add_argument("--seed", type=int, default=20260309)
    parser.add_argument("--final-r", type=int, default=20)
    parser.add_argument("--n-jobs", type=int, default=12)
    parser.add_argument("--max-checkpoints", type=int, default=1000)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    root = os.path.join(args.output_dir, f"ce_final_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(root, exist_ok=True)
    search_dir = os.path.join(root, "search")
    os.makedirs(search_dir, exist_ok=True)

    src_c = os.path.join("outputs", "ce_search_20260310_035922", "search", "C_primary_core_scores.csv")
    src_e = os.path.join("outputs", "manual_e_core_scores.csv")
    if os.path.exists(src_c):
        shutil.copyfile(src_c, os.path.join(search_dir, "C_primary_core_scores.csv"))
    if os.path.exists(src_e):
        shutil.copyfile(src_e, os.path.join(search_dir, "E_primary_core_scores.csv"))

    final_rows = {}
    for scenario, cfg in BEST_CONFIGS.items():
        results = _run_grid_for_experiments(
            experiments=[cfg],
            algorithms=["custom_elim", "moss", "naive_elim", "ucb"],
            R=int(args.final_r),
            seed=int(args.seed),
            n_jobs=int(args.n_jobs),
            progress="off",
            verbose_progress=False,
            max_checkpoints=int(args.max_checkpoints),
        )
        scenario_dir = os.path.join(root, f"scenario_{scenario}")
        _save_final_run(
            scenario=scenario,
            best_cfg=cfg,
            results=results,
            scenario_dir=scenario_dir,
            final_r=int(args.final_r),
            seed=int(args.seed),
        )
        final_rows[scenario] = _final_compare_row(results["agg_final"])

    _write_summary(root, BEST_CONFIGS, final_rows)
    print(os.path.abspath(root))


if __name__ == "__main__":
    main()
