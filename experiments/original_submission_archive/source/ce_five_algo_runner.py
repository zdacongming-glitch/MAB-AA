from __future__ import annotations

import argparse
import copy
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Tuple

import pandas as pd

from env import build_replicate_tape
from runner import _aggregate_with_ci, simulate_one
from scenario_ce_runner import _save_final_run

try:
    from tqdm.auto import tqdm
except Exception:  # pragma: no cover - tqdm may be unavailable in minimal envs
    tqdm = None


ALGORITHMS = ["custom_elim", "ucb", "moss", "naive_elim", "erse"]
BEST_CONFIGS: Dict[str, Dict[str, Any]] = {
    "C": {
        "scenario": "C",
        "T": 60000,
        "K0": 10,
        "arrival_mode": "bernoulli",
        "lambda": 0.005,
        "rho": 0.005,
        "M": 5,
        "scenario_params": {
            "gamma": [0.3, 0.6, 0.9],
            "Delta_step": 0.05,
            "r0": 0.7,
            "pi_good": 0.1,
            "mu_h": 0.8,
            "delta": 0.1,
            "mu_l": 0.1,
            "mu_m": 0.4,
        },
    },
    "E": {
        "scenario": "E",
        "T": 60000,
        "K0": 20,
        "arrival_mode": "bernoulli",
        "lambda": 0.005,
        "rho": 0.005,
        "M": 4,
        "scenario_params": {
            "m0": 5,
            "Delta_min": 0.15,
            "p_join_near": 0.3,
            "mu_top": 0.9,
            "pi_good": 0.1,
            "mu_h": 0.8,
            "delta": 0.1,
            "mu_l": 0.1,
            "mu_m": 0.4,
        },
    },
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run five algorithms on fixed Scenario C/E best configs")
    parser.add_argument("--output-dir", type=str, default="outputs")
    parser.add_argument("--seed", type=int, default=20260309)
    parser.add_argument("--R", type=int, default=12)
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument("--max-checkpoints", type=int, default=1000)
    parser.add_argument("--progress", choices=["auto", "on", "off"], default="on")
    return parser.parse_args()


def _should_show_progress(mode: str) -> bool:
    if mode == "off":
        return False
    if mode == "on":
        return True
    return tqdm is not None


def _aggregate_results(raw_final_df: pd.DataFrame, raw_checkpoint_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    group_final = ["scenario", "algo", "T", "K0", "arrival_mode", "params_json", "exp_id"]
    final_metrics = [
        "dynamic_regret",
        "static_regret",
        "wasted_pulls_eps_0_05",
        "wasted_pulls_eps_0_1",
        "final_active_size",
        "steps_completed",
    ]
    agg_final_df = _aggregate_with_ci(raw_final_df, group_cols=group_final, metric_cols=final_metrics)

    group_ckpt = ["scenario", "algo", "T", "K0", "arrival_mode", "params_json", "exp_id", "t"]
    ckpt_metrics = ["dynamic_regret", "wasted_pulls_eps_0_05", "wasted_pulls_eps_0_1", "active_size"]
    agg_checkpoint_df = _aggregate_with_ci(raw_checkpoint_df, group_cols=group_ckpt, metric_cols=ckpt_metrics)

    return {
        "raw_final": raw_final_df,
        "raw_checkpoint": raw_checkpoint_df,
        "agg_final": agg_final_df,
        "agg_checkpoint": agg_checkpoint_df,
    }


def _run_replicate_unit(
    task: Tuple[str, Dict[str, Any], int, int, int]
) -> Tuple[str, int, float, List[Dict[str, Any]], List[Dict[str, Any]]]:
    scenario, cfg, rep, seed, max_checkpoints = task
    t0 = time.time()
    tape = build_replicate_tape(cfg, seed=int(seed), replicate=int(rep))
    final_rows: List[Dict[str, Any]] = []
    checkpoint_rows: List[Dict[str, Any]] = []

    for algo_name in ALGORITHMS:
        final_df, checkpoint_df = simulate_one(
            exp_cfg=cfg,
            algo_name=algo_name,
            replicate=int(rep),
            master_seed=int(seed),
            tape=tape,
            max_checkpoints=int(max_checkpoints),
        )
        final_rows.extend(final_df.to_dict(orient="records"))
        checkpoint_rows.extend(checkpoint_df.to_dict(orient="records"))

    elapsed = time.time() - t0
    return scenario, int(rep), float(elapsed), final_rows, checkpoint_rows


def _scenario_summary(agg_final_df: pd.DataFrame) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    ordered = agg_final_df.sort_values("algo")
    for _, row in ordered.iterrows():
        algo = str(row["algo"])
        summary[algo] = {
            "dynamic_regret_mean": float(row["dynamic_regret_mean"]),
            "dynamic_regret_ci95": float(row["dynamic_regret_ci95"]),
            "wasted_pulls_eps_0_05_mean": float(row["wasted_pulls_eps_0_05_mean"]),
            "wasted_pulls_eps_0_1_mean": float(row["wasted_pulls_eps_0_1_mean"]),
            "final_active_size_mean": float(row["final_active_size_mean"]),
        }
    if "custom_elim" in summary and "moss" in summary:
        summary["custom_vs_moss_gap"] = float(
            summary["moss"]["dynamic_regret_mean"] - summary["custom_elim"]["dynamic_regret_mean"]
        )
    return summary


def main() -> None:
    args = _parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root_dir = os.path.join(args.output_dir, f"ce_five_algo_{timestamp}")
    os.makedirs(root_dir, exist_ok=True)

    raw_final_rows: List[Dict[str, Any]] = []
    raw_checkpoint_rows: List[Dict[str, Any]] = []
    total_units = 2 * int(args.R)
    unit_times: List[float] = []

    bar = None
    if tqdm is not None and _should_show_progress(str(args.progress)):
        bar = tqdm(total=total_units, desc="Scenario Replicates", dynamic_ncols=True)

    tasks: List[Tuple[str, Dict[str, Any], int, int, int]] = []
    for rep in range(int(args.R)):
        for scenario in ["C", "E"]:
            tasks.append(
                (
                    scenario,
                    copy.deepcopy(BEST_CONFIGS[scenario]),
                    rep,
                    int(args.seed),
                    int(args.max_checkpoints),
                )
            )

    n_jobs = int(max(1, args.n_jobs))

    if n_jobs <= 1:
        for scenario, cfg, rep, seed, max_checkpoints in tasks:
            _, _, elapsed, final_records, checkpoint_records = _run_replicate_unit((scenario, cfg, rep, seed, max_checkpoints))
            raw_final_rows.extend(final_records)
            raw_checkpoint_rows.extend(checkpoint_records)

            unit_times.append(elapsed)
            avg_time = sum(unit_times) / len(unit_times)
            remaining_units = total_units - len(unit_times)
            eta_seconds = max(0.0, remaining_units * avg_time)
            eta_min = eta_seconds / 60.0

            if bar is not None:
                bar.set_postfix_str(
                    f"scenario={scenario} rep={rep + 1}/{args.R} last={elapsed:.1f}s eta≈{eta_min:.1f}m"
                )
                bar.update(1)
            else:
                print(
                    f"[progress] {len(unit_times)}/{total_units} "
                    f"scenario={scenario} rep={rep + 1}/{args.R} last={elapsed:.1f}s eta≈{eta_min:.1f}m"
                )
    else:
        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            future_map = {
                executor.submit(_run_replicate_unit, task): (task[0], int(task[2]))
                for task in tasks
            }
            for future in as_completed(future_map):
                scenario, rep = future_map[future]
                scenario_name, rep_idx, elapsed, final_records, checkpoint_records = future.result()
                raw_final_rows.extend(final_records)
                raw_checkpoint_rows.extend(checkpoint_records)

                unit_times.append(elapsed)
                avg_time = sum(unit_times) / len(unit_times)
                remaining_units = total_units - len(unit_times)
                eta_seconds = max(0.0, remaining_units * avg_time)
                eta_min = eta_seconds / 60.0

                if bar is not None:
                    bar.set_postfix_str(
                        f"scenario={scenario_name} rep={rep_idx + 1}/{args.R} last={elapsed:.1f}s eta≈{eta_min:.1f}m"
                    )
                    bar.update(1)
                else:
                    print(
                        f"[progress] {len(unit_times)}/{total_units} "
                        f"scenario={scenario_name} rep={rep_idx + 1}/{args.R} last={elapsed:.1f}s eta≈{eta_min:.1f}m"
                    )

    if bar is not None:
        bar.close()

    raw_final_df = pd.DataFrame(raw_final_rows)
    raw_checkpoint_df = pd.DataFrame(raw_checkpoint_rows)

    summary_payload = {
        "seed": int(args.seed),
        "R": int(args.R),
        "algorithms": ALGORITHMS,
        "scenarios": {},
    }

    for scenario in ["C", "E"]:
        scenario_raw_final = raw_final_df[raw_final_df["scenario"] == scenario].copy()
        scenario_raw_checkpoint = raw_checkpoint_df[raw_checkpoint_df["scenario"] == scenario].copy()
        scenario_results = _aggregate_results(
            raw_final_df=scenario_raw_final,
            raw_checkpoint_df=scenario_raw_checkpoint,
        )

        scenario_dir = os.path.join(root_dir, f"scenario_{scenario}")
        _save_final_run(
            scenario=scenario,
            best_cfg=BEST_CONFIGS[scenario],
            results=scenario_results,
            scenario_dir=scenario_dir,
            final_r=int(args.R),
            seed=int(args.seed),
        )
        summary_payload["scenarios"][scenario] = _scenario_summary(scenario_results["agg_final"])

    with open(os.path.join(root_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, ensure_ascii=False, indent=2)

    print(f"Saved outputs to: {os.path.abspath(root_dir)}")


if __name__ == "__main__":
    main()
