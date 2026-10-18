from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha1
from itertools import product
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from algos import build_algo
from env import DynamicArmsEnv, build_replicate_tape


def _json_dumps_sorted(obj: Dict) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def _exp_id_from_config(exp_cfg: Dict) -> str:
    return sha1(_json_dumps_sorted(exp_cfg).encode("utf-8")).hexdigest()[:12]


def build_checkpoints(T: int, max_points: int = 2000) -> List[int]:
    T = int(T)
    max_points = int(max(1, max_points))
    if T <= max_points:
        return list(range(1, T + 1))

    pts = np.linspace(1, T, num=max_points, dtype=int)
    pts = np.unique(pts)
    if pts[-1] != T:
        pts = np.append(pts, T)
    return [int(x) for x in pts]


@dataclass
class MetricsTracker:
    checkpoint_times: Sequence[int]

    def __post_init__(self):
        self.checkpoint_set = set(int(x) for x in self.checkpoint_times)
        self.dynamic_regret_cum = 0.0
        self.chosen_mean_sum = 0.0
        self.wasted_eps = {0.05: 0, 0.1: 0}
        self.current_active_size = 0
        self.round_states: List[Dict] = []
        self.checkpoint_rows: List[Dict] = []

    def set_active_size(self, active_size: int) -> None:
        self.current_active_size = int(active_size)

    def record_round_state(self, t: int, round_id: int, active_size: int) -> None:
        self.round_states.append({"t": int(t), "round": int(round_id), "active_size": int(active_size)})

    def record_step(self, step_result: Dict) -> None:
        t = int(step_result["t"])
        chosen_mean = float(step_result["chosen_mean"])
        r_star = float(step_result["r_star"])

        gap = max(0.0, r_star - chosen_mean)
        self.dynamic_regret_cum += gap
        self.chosen_mean_sum += chosen_mean

        for eps in self.wasted_eps.keys():
            if gap >= eps:
                self.wasted_eps[eps] += 1

        if t in self.checkpoint_set:
            self.checkpoint_rows.append(
                {
                    "t": t,
                    "dynamic_regret": self.dynamic_regret_cum,
                    "wasted_pulls_eps_0_05": self.wasted_eps[0.05],
                    "wasted_pulls_eps_0_1": self.wasted_eps[0.1],
                    "active_size": self.current_active_size,
                }
            )

    def finalize(self, env: DynamicArmsEnv) -> Dict:
        r_star_T = float(env.get_r_star(env.T))
        static_regret = env.T * r_star_T - self.chosen_mean_sum
        return {
            "dynamic_regret": float(self.dynamic_regret_cum),
            "static_regret": float(static_regret),
            "wasted_pulls_eps_0_05": int(self.wasted_eps[0.05]),
            "wasted_pulls_eps_0_1": int(self.wasted_eps[0.1]),
            "final_active_size": int(self.current_active_size),
            "r_star_T": float(r_star_T),
            "steps_completed": int(env.t),
        }


def simulate_one(
    exp_cfg: Dict,
    algo_name: str,
    replicate: int,
    master_seed: int,
    tape: Optional[Dict] = None,
    max_checkpoints: int = 2000,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if tape is None:
        tape = build_replicate_tape(exp_cfg, seed=master_seed, replicate=replicate)

    env = DynamicArmsEnv(config=exp_cfg, tape=tape, seed=master_seed, replicate=replicate)
    checkpoints = build_checkpoints(T=int(exp_cfg["T"]), max_points=max_checkpoints)
    tracker = MetricsTracker(checkpoint_times=checkpoints)

    algo_cfg = dict(exp_cfg.get("algo_params", {}).get(algo_name, {}))
    algo = build_algo(algo_name, algo_cfg=algo_cfg, exp_cfg=exp_cfg)
    algo_info = algo.run(env=env, T=int(exp_cfg["T"]), tracker=tracker)

    params_json = _json_dumps_sorted(exp_cfg)
    exp_id = _exp_id_from_config(exp_cfg)

    final_row = tracker.finalize(env)
    final_row.update(
        {
            "scenario": exp_cfg.get("scenario", "B"),
            "algo": algo_name,
            "replicate": int(replicate),
            "T": int(exp_cfg["T"]),
            "K0": int(exp_cfg["K0"]),
            "arrival_mode": str(exp_cfg.get("arrival_mode", "bernoulli")),
            "params_json": params_json,
            "exp_id": exp_id,
            "algo_info_json": _json_dumps_sorted(algo_info),
        }
    )

    checkpoint_rows = []
    for row in tracker.checkpoint_rows:
        out = dict(row)
        out.update(
            {
                "scenario": exp_cfg.get("scenario", "B"),
                "algo": algo_name,
                "replicate": int(replicate),
                "T": int(exp_cfg["T"]),
                "K0": int(exp_cfg["K0"]),
                "arrival_mode": str(exp_cfg.get("arrival_mode", "bernoulli")),
                "params_json": params_json,
                "exp_id": exp_id,
            }
        )
        checkpoint_rows.append(out)

    final_df = pd.DataFrame([final_row])
    checkpoint_df = pd.DataFrame(checkpoint_rows)
    return final_df, checkpoint_df


def _aggregate_with_ci(df: pd.DataFrame, group_cols: List[str], metric_cols: List[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    agg_frames = []
    for metric in metric_cols:
        grp = df.groupby(group_cols, dropna=False)[metric]
        out = grp.agg(["mean", "std", "count"]).reset_index()
        out["std"] = out["std"].fillna(0.0)
        out["ci95"] = 1.96 * out["std"] / np.sqrt(out["count"].clip(lower=1))
        out = out.rename(
            columns={
                "mean": f"{metric}_mean",
                "std": f"{metric}_std",
                "count": f"{metric}_count",
                "ci95": f"{metric}_ci95",
            }
        )
        agg_frames.append(out)

    merged = agg_frames[0]
    for frame in agg_frames[1:]:
        merged = merged.merge(frame, on=group_cols, how="inner")
    return merged


def _get_tqdm(progress_cfg: Dict):
    try:
        from tqdm.auto import tqdm
    except Exception:
        return None

    progress_mode = str(progress_cfg.get("progress", "auto")).lower()
    if progress_mode == "off":
        return None
    if progress_mode == "on":
        return tqdm
    if progress_mode == "auto":
        return tqdm if sys.stderr.isatty() else None
    return None


def _simulate_one_worker(task: Tuple[Dict, str, int, int, int]):
    exp_cfg, algo_name, replicate, master_seed, max_checkpoints = task
    final_df, checkpoint_df = simulate_one(
        exp_cfg=exp_cfg,
        algo_name=algo_name,
        replicate=replicate,
        master_seed=master_seed,
        tape=None,
        max_checkpoints=max_checkpoints,
    )
    return final_df.to_dict(orient="records"), checkpoint_df.to_dict(orient="records")


def run_grid(grid_cfg: Dict, master_seed: int, n_jobs: int, progress_cfg: Optional[Dict] = None) -> Dict:
    progress_cfg = dict(progress_cfg or {})
    tqdm = _get_tqdm(progress_cfg)
    refresh = float(progress_cfg.get("progress_refresh", 0.2))
    verbose_progress = bool(progress_cfg.get("verbose_progress", False))
    max_checkpoints = int(progress_cfg.get("max_checkpoints", 2000))

    experiments = list(grid_cfg["experiments"])
    algorithms = list(grid_cfg["algorithms"])
    R = int(grid_cfg["R"])

    final_rows: List[Dict] = []
    checkpoint_rows: List[Dict] = []

    top_bar = None
    if tqdm is not None:
        top_bar = tqdm(total=len(experiments), desc="Configs", dynamic_ncols=True, mininterval=refresh)

    for idx, exp_cfg in enumerate(experiments, start=1):
        short = f"scn={exp_cfg.get('scenario')} T={exp_cfg.get('T')} K0={exp_cfg.get('K0')}"
        if top_bar is not None:
            top_bar.set_postfix_str(short)
        else:
            print(f"[progress] config {idx}/{len(experiments)}: {short}")

        if n_jobs <= 1:
            rep_bar = None
            if tqdm is not None:
                rep_bar = tqdm(total=R, desc="Replicates", leave=False, dynamic_ncols=True, mininterval=refresh)

            for rep in range(R):
                tape = build_replicate_tape(exp_cfg, seed=master_seed, replicate=rep)

                algo_bar = None
                if rep_bar is not None and verbose_progress:
                    algo_bar = tqdm(
                        total=len(algorithms),
                        desc=f"Algorithms rep={rep + 1}",
                        leave=False,
                        dynamic_ncols=True,
                        mininterval=refresh,
                    )

                for algo_name in algorithms:
                    final_df, checkpoint_df = simulate_one(
                        exp_cfg=exp_cfg,
                        algo_name=algo_name,
                        replicate=rep,
                        master_seed=master_seed,
                        tape=tape,
                        max_checkpoints=max_checkpoints,
                    )

                    final_rows.extend(final_df.to_dict(orient="records"))
                    checkpoint_rows.extend(checkpoint_df.to_dict(orient="records"))

                    if algo_bar is not None:
                        algo_bar.set_postfix_str(algo_name)
                        algo_bar.update(1)
                    elif rep_bar is not None:
                        rep_bar.set_postfix_str(f"rep={rep + 1}/{R}, algo={algo_name}")

                if algo_bar is not None:
                    algo_bar.close()
                if rep_bar is not None:
                    rep_bar.update(1)

            if rep_bar is not None:
                rep_bar.close()

        else:
            tasks: List[Tuple[Dict, str, int, int, int]] = []
            for rep in range(R):
                for algo_name in algorithms:
                    tasks.append((exp_cfg, algo_name, rep, master_seed, max_checkpoints))

            task_bar = None
            if tqdm is not None and verbose_progress:
                task_bar = tqdm(total=len(tasks), desc="Tasks", leave=False, dynamic_ncols=True, mininterval=refresh)

            with ProcessPoolExecutor(max_workers=n_jobs) as executor:
                futures = [executor.submit(_simulate_one_worker, t) for t in tasks]
                for future in as_completed(futures):
                    final_records, checkpoint_records = future.result()
                    final_rows.extend(final_records)
                    checkpoint_rows.extend(checkpoint_records)
                    if task_bar is not None:
                        task_bar.update(1)

            if task_bar is not None:
                task_bar.close()

        if top_bar is not None:
            top_bar.update(1)

    if top_bar is not None:
        top_bar.close()

    raw_final_df = pd.DataFrame(final_rows)
    raw_checkpoint_df = pd.DataFrame(checkpoint_rows)

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


def _scenario_list(mode: str, requested: Optional[Sequence[str]]) -> List[str]:
    default = ["B", "C", "D", "E", "F"]
    if requested is None:
        return default
    out = [x.strip().upper() for x in requested if x.strip()]
    return [x for x in default if x in set(out)]


def make_default_grid(
    mode: str = "smoke",
    arrival_mode: str = "bernoulli",
    R_override: Optional[int] = None,
    algorithms: Optional[List[str]] = None,
    scenario_filter: Optional[Sequence[str]] = None,
    grid_profile: str = "default",
) -> Dict:
    mode = str(mode).lower()
    arrival_mode = str(arrival_mode).lower()
    grid_profile = str(grid_profile).lower()

    if mode == "smoke":
        T_list = [20000]
        K0_list = [10]
        lambda_list = [1.0 / 200.0]
        M_list = [6]
        R = 10
    else:
        T_list = [20000, 50000, 100000, 200000]
        K0_list = [10, 50]
        lambda_list = [1.0 / 500.0, 1.0 / 200.0, 1.0 / 100.0, 1.0 / 50.0]
        M_list = [6, 8, 10, 12]
        R = 200

    # Legacy full grid (reference only; not used by bcde_cover):
    # T_list=[20000,50000,100000,200000]
    # K0_list=[10,50]
    # lambda_list=[1/500,1/200,1/100,1/50]
    # M_list=[6,8,10,12]
    # Scenario C: Delta_step=[0.05,0.02]
    # Scenario D: B=[20,100,300], p_spike=[0.2,0.5]
    # Scenario E: m0=[5,10], Delta_min=[0.01,0.005]

    if grid_profile == "bcde_cover":
        T_list = [20000, 50000, 100000]
        K0_list = [10, 50]
        lambda_list = [1.0 / 200.0, 1.0 / 100.0]
        M_list = [6, 8]
        if R_override is None:
            R = 30

    if R_override is not None:
        R = int(R_override)

    algos = algorithms or ["custom_elim", "ucb", "moss", "naive_elim"]

    experiments: List[Dict] = []
    keep_scenarios = _scenario_list(mode, scenario_filter)
    if grid_profile == "bcde_cover":
        keep_scenarios = [s for s in keep_scenarios if s in {"B", "C", "D", "E"}]

    for scenario in keep_scenarios:
        if scenario in {"B", "C", "E"}:
            for T, K0, lam, M in product(T_list, K0_list, lambda_list, M_list):
                cfg = {
                    "scenario": scenario,
                    "T": int(T),
                    "K0": int(K0),
                    "arrival_mode": arrival_mode,
                    "lambda": float(lam),
                    "rho": float(lam),
                    "M": int(M),
                }

                if scenario == "C":
                    if grid_profile == "bcde_cover":
                        deltas = [0.05]
                    else:
                        deltas = [0.05] if mode == "smoke" else [0.05, 0.02]
                    for delta_step in deltas:
                        c_cfg = dict(cfg)
                        c_cfg["scenario_params"] = {
                            "gamma": (0.2, 0.5, 0.8),
                            "Delta_step": float(delta_step),
                            "r0": 0.6,
                            "pi_good": 0.1,
                            "mu_h": 0.9,
                            "delta": 0.1,
                            "mu_l": 0.1,
                            "mu_m": 0.5,
                        }
                        experiments.append(c_cfg)
                elif scenario == "E":
                    if grid_profile == "bcde_cover":
                        m0s = [5]
                        dmins = [0.01]
                    else:
                        m0s = [5] if mode == "smoke" else [5, 10]
                        dmins = [0.01] if mode == "smoke" else [0.01, 0.005]
                    for m0, dmin in product(m0s, dmins):
                        e_cfg = dict(cfg)
                        e_cfg["scenario_params"] = {
                            "m0": int(m0),
                            "Delta_min": float(dmin),
                            "p_join_near": 0.3,
                            "mu_top": 0.8,
                            "pi_good": 0.1,
                            "mu_h": 0.9,
                            "delta": 0.1,
                            "mu_l": 0.1,
                            "mu_m": 0.5,
                        }
                        experiments.append(e_cfg)
                else:
                    cfg["scenario_params"] = {
                        "pi_good": 0.1,
                        "mu_h": 0.9,
                        "delta": 0.1,
                        "mu_l": 0.1,
                        "mu_m": 0.5,
                    }
                    experiments.append(cfg)

        elif scenario == "D":
            if grid_profile == "bcde_cover":
                b_list = [20, 100]
                p_spike_list = [0.5]
            else:
                b_list = [20] if mode == "smoke" else [20, 100, 300]
                p_spike_list = [0.5] if mode == "smoke" else [0.2, 0.5]

            for T, K0, B, p_spike, M in product(T_list, K0_list, b_list, p_spike_list, M_list):
                t_burst = [int(0.2 * T), int(0.5 * T), int(0.8 * T)]
                d_cfg = {
                    "scenario": "D",
                    "T": int(T),
                    "K0": int(K0),
                    "arrival_mode": "burst",
                    "B": int(B),
                    "T_burst": t_burst,
                    "M": int(M),
                    "scenario_params": {
                        "B": int(B),
                        "T_burst": t_burst,
                        "p_spike": float(p_spike),
                        "high_mean": 0.8,
                    },
                }
                experiments.append(d_cfg)

        elif scenario == "F":
            T_f = [200000] if mode == "smoke" else [200000, 500000]
            lambda_f = [1.0 / 50.0] if mode == "smoke" else [1.0 / 50.0, 1.0 / 20.0]
            for T, K0, lam, M in product(T_f, K0_list, lambda_f, M_list):
                f_cfg = {
                    "scenario": "F",
                    "T": int(T),
                    "K0": int(K0),
                    "arrival_mode": "bernoulli",
                    "lambda": float(lam),
                    "rho": float(lam),
                    "M": int(M),
                    "scenario_params": {
                        "pi_good": 0.02,
                        "mu_h": 0.9,
                        "delta": 0.1,
                        "mu_l": 0.1,
                        "mu_m": 0.5,
                    },
                }
                experiments.append(f_cfg)

    return {
        "mode": mode,
        "arrival_mode": arrival_mode,
        "grid_profile": grid_profile,
        "R": int(R),
        "algorithms": algos,
        "experiments": experiments,
    }


def _save_outputs(results: Dict, out_dir: str, grid_cfg: Dict, run_meta: Dict) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(out_dir, f"run_{ts}")
    os.makedirs(run_dir, exist_ok=True)

    results["raw_final"].to_csv(os.path.join(run_dir, "raw_final_metrics.csv"), index=False)
    results["raw_checkpoint"].to_csv(os.path.join(run_dir, "raw_checkpoint_metrics.csv"), index=False)
    results["agg_final"].to_csv(os.path.join(run_dir, "agg_final_metrics.csv"), index=False)
    results["agg_checkpoint"].to_csv(os.path.join(run_dir, "agg_checkpoint_metrics.csv"), index=False)

    with open(os.path.join(run_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"grid": grid_cfg, "run_meta": run_meta}, f, ensure_ascii=False, indent=2)

    return run_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dynamic-arrival bandit simulation runner")
    parser.add_argument("--mode", choices=["smoke", "full"], default="smoke")
    parser.add_argument("--arrival", choices=["bernoulli", "poisson", "burst"], default="bernoulli")
    parser.add_argument("--seed", type=int, default=20260302)
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument("--R", type=int, default=None)
    parser.add_argument("--output-dir", type=str, default="outputs")
    parser.add_argument("--algos", type=str, default="custom_elim,ucb,moss,naive_elim")
    parser.add_argument("--scenarios", type=str, default="B,C,D,E,F")
    parser.add_argument("--grid-profile", choices=["default", "bcde_cover"], default="default")

    parser.add_argument("--progress", choices=["auto", "on", "off"], default="auto")
    parser.add_argument("--verbose-progress", action="store_true")
    parser.add_argument("--progress-refresh", type=float, default=0.2)

    parser.add_argument("--max-checkpoints", type=int, default=2000)
    parser.add_argument("--no-plots", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    algorithms = [x.strip() for x in args.algos.split(",") if x.strip()]
    scenarios = [x.strip() for x in args.scenarios.split(",") if x.strip()]
    if args.grid_profile == "bcde_cover":
        scenarios = ["B", "C", "D", "E"]

    grid_cfg = make_default_grid(
        mode=args.mode,
        arrival_mode=args.arrival,
        R_override=args.R,
        algorithms=algorithms,
        scenario_filter=scenarios,
        grid_profile=args.grid_profile,
    )

    progress_cfg = {
        "progress": args.progress,
        "verbose_progress": bool(args.verbose_progress),
        "progress_refresh": float(args.progress_refresh),
        "max_checkpoints": int(args.max_checkpoints),
    }

    results = run_grid(
        grid_cfg=grid_cfg,
        master_seed=int(args.seed),
        n_jobs=int(args.n_jobs),
        progress_cfg=progress_cfg,
    )

    run_meta = {
        "seed": int(args.seed),
        "n_jobs": int(args.n_jobs),
        "mode": args.mode,
        "progress": args.progress,
        "verbose_progress": bool(args.verbose_progress),
        "max_checkpoints": int(args.max_checkpoints),
        "grid_profile": str(args.grid_profile),
    }
    run_dir = _save_outputs(results=results, out_dir=args.output_dir, grid_cfg=grid_cfg, run_meta=run_meta)

    if not args.no_plots:
        from plots import make_all_plots

        make_all_plots(run_dir)

    print(f"Saved outputs to: {os.path.abspath(run_dir)}")


if __name__ == "__main__":
    main()
