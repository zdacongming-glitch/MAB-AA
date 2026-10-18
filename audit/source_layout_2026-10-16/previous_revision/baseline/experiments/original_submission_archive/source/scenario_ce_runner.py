from __future__ import annotations

import argparse
import copy
import json
import os
from dataclasses import dataclass
from datetime import datetime
from itertools import product
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from runner import run_grid

ALGO_ORDER = ["custom_elim", "moss", "naive_elim", "ucb", "erse"]
LABEL_MAP = {
    "custom_elim": "UCB-AA",
    "moss": "G-MOSS",
    "naive_elim": "NE",
    "ucb": "G-UCB1",
    "erse": "D-SE",
}
COLOR_MAP = {
    "custom_elim": "#1f77b4",
    "moss": "#ff7f0e",
    "naive_elim": "#2ca02c",
    "ucb": "#d62728",
    "erse": "#8c564b",
}
SCENARIO_PLOT_LABELS = {"C": "1", "E": "2"}
TITLE_FONTSIZE = 20
LABEL_FONTSIZE = 16
TICK_FONTSIZE = 13
LEGEND_FONTSIZE = 13


def _plot_scenario_name(scenario: str) -> str:
    scen = str(scenario).upper()
    mapped = SCENARIO_PLOT_LABELS.get(scen, scen)
    return f"scenario {mapped}"


@dataclass(frozen=True)
class SearchBlock:
    name: str
    priority: str
    params: Sequence[Tuple[str, Sequence[Any]]]


BASE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "C": {
        "scenario": "C",
        "T": 100000,
        "K0": 10,
        "arrival_mode": "bernoulli",
        "lambda": 0.005,
        "rho": 0.005,
        "M": 6,
        "scenario_params": {
            "gamma": (0.2, 0.5, 0.8),
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
        "T": 100000,
        "K0": 10,
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


def _scenario_blocks(reduced_search: bool = False, critical_only: bool = False) -> Dict[str, List[SearchBlock]]:
    if reduced_search or critical_only:
        t_values = [40000, 100000, 200000]
        k0_values = [5, 10, 20, 50]
    else:
        t_values = [40000, 80000, 120000, 160000, 200000]
        k0_values = [5, 10, 20, 30, 50]

    if critical_only:
        return {
            "C": [
                SearchBlock(
                    name="primary_core",
                    priority="primary",
                    params=(
                        ("T", t_values),
                        ("K0", [5, 20, 50]),
                        ("lambda_rho", [0.0025, 0.005]),
                    ),
                ),
                SearchBlock(
                    name="critical_structure",
                    priority="primary",
                    params=(
                        ("scenario_params.Delta_step", [0.02, 0.05, 0.08]),
                        ("scenario_params.r0", [0.5, 0.6, 0.7]),
                    ),
                ),
            ],
            "E": [
                SearchBlock(
                    name="primary_core",
                    priority="primary",
                    params=(
                        ("T", t_values),
                        ("K0", [5, 20, 50]),
                        ("lambda_rho", [0.0025, 0.005]),
                    ),
                ),
                SearchBlock(
                    name="critical_structure",
                    priority="primary",
                    params=(
                        ("scenario_params.m0", [3, 5, 8]),
                        ("scenario_params.Delta_min", [0.005, 0.01, 0.02]),
                        ("scenario_params.p_join_near", [0.1, 0.3, 0.5]),
                    ),
                ),
            ],
        }

    return {
        "C": [
            SearchBlock(
                name="primary_core",
                priority="primary",
                params=(
                    ("T", t_values),
                    ("K0", k0_values),
                    ("lambda_rho", [0.0025, 0.005, 0.01]),
                ),
            ),
            SearchBlock(
                name="primary_structure",
                priority="primary",
                params=(
                    ("scenario_params.Delta_step", [0.02, 0.05, 0.08]),
                    ("scenario_params.r0", [0.5, 0.6, 0.7]),
                    (
                        "scenario_params.gamma",
                        [
                            (0.2, 0.5, 0.8),
                            (0.15, 0.45, 0.75),
                            (0.25, 0.55, 0.85),
                        ],
                    ),
                ),
            ),
            SearchBlock(
                name="secondary_distribution",
                priority="secondary",
                params=(
                    ("scenario_params.pi_good", [0.05, 0.1, 0.2]),
                    ("scenario_params.delta", [0.05, 0.1, 0.15]),
                    ("scenario_params.mu_h", [0.85, 0.9, 0.95]),
                ),
            ),
            SearchBlock(
                name="secondary_background",
                priority="secondary",
                params=(
                    ("scenario_params.mu_l", [0.05, 0.1, 0.15]),
                    ("scenario_params.mu_m", [0.4, 0.5, 0.6]),
                ),
            ),
        ],
        "E": [
            SearchBlock(
                name="primary_core",
                priority="primary",
                params=(
                    ("T", t_values),
                    ("K0", k0_values),
                    ("lambda_rho", [0.0025, 0.005, 0.01]),
                ),
            ),
            SearchBlock(
                name="primary_structure",
                priority="primary",
                params=(
                    ("scenario_params.m0", [3, 5, 8]),
                    ("scenario_params.Delta_min", [0.005, 0.01, 0.02]),
                    ("scenario_params.p_join_near", [0.1, 0.3, 0.5]),
                    ("scenario_params.mu_top", [0.75, 0.8, 0.85]),
                ),
            ),
            SearchBlock(
                name="secondary_distribution",
                priority="secondary",
                params=(
                    ("scenario_params.pi_good", [0.05, 0.1, 0.2]),
                    ("scenario_params.delta", [0.05, 0.1, 0.15]),
                    ("scenario_params.mu_h", [0.85, 0.9, 0.95]),
                ),
            ),
            SearchBlock(
                name="secondary_background",
                priority="secondary",
                params=(
                    ("scenario_params.mu_l", [0.05, 0.1, 0.15]),
                    ("scenario_params.mu_m", [0.4, 0.5, 0.6]),
                ),
            ),
        ],
    }


def _json_dumps_sorted(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def _clone_cfg(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(cfg)


def _extract_choice(cfg: Dict[str, Any], key: str) -> Any:
    if key == "lambda_rho":
        return float(cfg["lambda"])
    if key.startswith("scenario_params."):
        return cfg["scenario_params"][key.split(".", 1)[1]]
    return cfg[key]


def _apply_choice(cfg: Dict[str, Any], key: str, value: Any) -> None:
    if key == "lambda_rho":
        cfg["lambda"] = float(value)
        cfg["rho"] = float(value)
        return
    if key.startswith("scenario_params."):
        cfg["scenario_params"][key.split(".", 1)[1]] = value
        return
    cfg[key] = value


def _value_matches(left: Any, right: Any) -> bool:
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        if len(left) != len(right):
            return False
        return all(_value_matches(l_item, r_item) for l_item, r_item in zip(left, right))
    if isinstance(left, float) or isinstance(right, float):
        try:
            return abs(float(left) - float(right)) <= 1e-12
        except Exception:
            return left == right
    return left == right


def _find_value_index(values: Sequence[Any], target: Any) -> int:
    for idx, value in enumerate(values):
        if _value_matches(value, target):
            return idx
    raise ValueError(f"Target {target!r} not found in candidate list.")


def _neighbor_values(values: Sequence[Any], target: Any) -> List[Any]:
    idx = _find_value_index(values, target)
    lo = max(0, idx - 1)
    hi = min(len(values), idx + 2)
    return list(values[lo:hi])


def _build_block_experiments(base_cfg: Dict[str, Any], block: SearchBlock) -> List[Dict[str, Any]]:
    keys = [key for key, _ in block.params]
    value_lists = [list(values) for _, values in block.params]

    experiments: List[Dict[str, Any]] = []
    for choice_tuple in product(*value_lists):
        cfg = _clone_cfg(base_cfg)
        for key, value in zip(keys, choice_tuple):
            _apply_choice(cfg, key, value)
        experiments.append(cfg)
    return experiments


def _build_refine_block(block: SearchBlock, incumbent: Dict[str, Any]) -> SearchBlock:
    refined_params = []
    for key, values in block.params:
        target = _extract_choice(incumbent, key)
        refined_params.append((key, _neighbor_values(list(values), target)))
    return SearchBlock(name=f"{block.name}_refine", priority=block.priority, params=tuple(refined_params))


def _summarize_scores(agg_final_df: pd.DataFrame) -> pd.DataFrame:
    cols = ["scenario", "algo", "params_json", "exp_id", "dynamic_regret_mean"]
    pivot = (
        agg_final_df[cols]
        .pivot_table(
            index=["scenario", "params_json", "exp_id"],
            columns="algo",
            values="dynamic_regret_mean",
            aggfunc="first",
        )
        .reset_index()
    )
    pivot = pivot.rename(columns={"custom_elim": "custom_regret", "moss": "moss_regret"})
    pivot["score"] = pivot["moss_regret"] - pivot["custom_regret"]
    pivot = pivot.sort_values(["score", "custom_regret"], ascending=[False, True]).reset_index(drop=True)
    return pivot


def _run_grid_for_experiments(
    experiments: Sequence[Dict[str, Any]],
    algorithms: Sequence[str],
    R: int,
    seed: int,
    n_jobs: int,
    progress: str,
    verbose_progress: bool,
    max_checkpoints: int,
) -> Dict[str, pd.DataFrame]:
    grid_cfg = {
        "mode": "custom",
        "arrival_mode": "bernoulli",
        "grid_profile": "scenario_ce",
        "R": int(R),
        "algorithms": list(algorithms),
        "experiments": list(experiments),
    }
    progress_cfg = {
        "progress": progress,
        "verbose_progress": bool(verbose_progress),
        "progress_refresh": 0.2,
        "max_checkpoints": int(max_checkpoints),
    }
    return run_grid(grid_cfg=grid_cfg, master_seed=int(seed), n_jobs=int(n_jobs), progress_cfg=progress_cfg)


def _run_block(
    scenario: str,
    incumbent: Dict[str, Any],
    block: SearchBlock,
    search_r: int,
    seed: int,
    search_n_jobs: int,
    progress: str,
    verbose_progress: bool,
    max_checkpoints: int,
    search_dir: str,
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    experiments = _build_block_experiments(incumbent, block)
    results = _run_grid_for_experiments(
        experiments=experiments,
        algorithms=["custom_elim", "moss"],
        R=search_r,
        seed=seed,
        n_jobs=search_n_jobs,
        progress=progress,
        verbose_progress=verbose_progress,
        max_checkpoints=max_checkpoints,
    )
    summary = _summarize_scores(results["agg_final"])
    summary["block"] = block.name
    summary["priority"] = block.priority

    block_tag = f"{scenario}_{block.name}"
    summary.to_csv(os.path.join(search_dir, f"{block_tag}_scores.csv"), index=False)
    results["agg_final"].to_csv(os.path.join(search_dir, f"{block_tag}_agg_final.csv"), index=False)

    best_cfg = json.loads(str(summary.iloc[0]["params_json"]))
    return best_cfg, summary


def _select_ordered_algos(df: pd.DataFrame, algo_col: str = "algo") -> List[str]:
    algos = [algo for algo in ALGO_ORDER if algo in set(df[algo_col].astype(str))]
    return algos


def _plot_line(
    df: pd.DataFrame,
    metric_mean: str,
    metric_ci: str,
    ylabel: str,
    title: str,
    out_path: str,
    include_algos: Optional[Sequence[str]] = None,
) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))

    ordered_algos = _select_ordered_algos(df)
    if include_algos is not None:
        allow = {str(algo) for algo in include_algos}
        ordered_algos = [algo for algo in ordered_algos if algo in allow]

    for algo in ordered_algos:
        sub = df[df["algo"] == algo].sort_values("t")
        x = sub["t"].to_numpy()
        y = sub[metric_mean].to_numpy()
        ci = sub[metric_ci].to_numpy()
        color = COLOR_MAP.get(algo, None)
        ax.plot(x, y, label=LABEL_MAP.get(algo, algo), linewidth=2, color=color)
        ax.fill_between(x, y - ci, y + ci, alpha=0.2, color=color)

    ax.set_title(title, fontsize=TITLE_FONTSIZE)
    ax.set_xlabel("t", fontsize=LABEL_FONTSIZE)
    ax.set_ylabel("")
    ax.tick_params(axis="both", labelsize=TICK_FONTSIZE)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=LEGEND_FONTSIZE)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _plot_bar(
    df: pd.DataFrame,
    metric_mean: str,
    metric_ci: str,
    ylabel: str,
    title: str,
    out_path: str,
) -> None:
    algos = _select_ordered_algos(df)
    sub = df.set_index("algo").loc[algos].reset_index()
    labels = [LABEL_MAP.get(algo, algo) for algo in sub["algo"]]
    vals = sub[metric_mean].to_numpy()
    cis = sub[metric_ci].to_numpy()
    colors = [COLOR_MAP.get(algo, "#4c4c4c") for algo in sub["algo"]]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(labels))
    ax.bar(x, vals, yerr=cis, capsize=4, alpha=0.88, color=colors)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0, ha="center", fontsize=TICK_FONTSIZE)
    ax.set_ylabel("")
    ax.set_title(title, fontsize=TITLE_FONTSIZE)
    ax.tick_params(axis="y", labelsize=TICK_FONTSIZE)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _save_final_run(
    scenario: str,
    best_cfg: Dict[str, Any],
    results: Dict[str, pd.DataFrame],
    scenario_dir: str,
    final_r: int,
    seed: int,
) -> None:
    os.makedirs(scenario_dir, exist_ok=True)

    for name, df in results.items():
        df.to_csv(os.path.join(scenario_dir, f"{name}.csv"), index=False)

    with open(os.path.join(scenario_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "scenario": scenario,
                "best_config": best_cfg,
                "final_R": int(final_r),
                "seed": int(seed),
                "algorithms": ALGO_ORDER,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    plots_dir = os.path.join(scenario_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    agg_final = results["agg_final"].copy()
    agg_ckpt = results["agg_checkpoint"].copy()

    _plot_line(
        df=agg_ckpt,
        metric_mean="dynamic_regret_mean",
        metric_ci="dynamic_regret_ci95",
        ylabel="Cumulative Dynamic Regret",
        title=f"Dynamic Regret vs t\n{_plot_scenario_name(scenario)}",
        out_path=os.path.join(plots_dir, f"scenario_{scenario}_dynamic_regret_vs_t.png"),
    )
    _plot_line(
        df=agg_ckpt,
        metric_mean="active_size_mean",
        metric_ci="active_size_ci95",
        ylabel="Arm Set Size",
        title=f"Arm Set Size vs t\n{_plot_scenario_name(scenario)}",
        out_path=os.path.join(plots_dir, f"scenario_{scenario}_arm_set_size_vs_t.png"),
        include_algos=["custom_elim", "naive_elim", "erse"],
    )
    _plot_bar(
        df=agg_final,
        metric_mean="wasted_pulls_eps_0_05_mean",
        metric_ci="wasted_pulls_eps_0_05_ci95",
        ylabel="Wasted Pulls (eps=0.05)",
        title=f"Wasted Pulls (eps=0.05)\n{_plot_scenario_name(scenario)}",
        out_path=os.path.join(plots_dir, f"scenario_{scenario}_wasted_pulls_eps_0_05.png"),
    )
    _plot_bar(
        df=agg_final,
        metric_mean="wasted_pulls_eps_0_1_mean",
        metric_ci="wasted_pulls_eps_0_1_ci95",
        ylabel="Wasted Pulls (eps=0.1)",
        title=f"Wasted Pulls (eps=0.1)\n{_plot_scenario_name(scenario)}",
        out_path=os.path.join(plots_dir, f"scenario_{scenario}_wasted_pulls_eps_0_1.png"),
    )


def _search_scenario(
    scenario: str,
    blocks: Sequence[SearchBlock],
    search_r: int,
    seed: int,
    search_n_jobs: int,
    progress: str,
    verbose_progress: bool,
    max_checkpoints: int,
    search_dir: str,
    skip_secondary: bool,
) -> Tuple[Dict[str, Any], List[pd.DataFrame]]:
    incumbent = _clone_cfg(BASE_CONFIGS[scenario])
    summaries: List[pd.DataFrame] = []
    executed_blocks: List[SearchBlock] = []
    best_score = float("-inf")

    for block in blocks:
        if skip_secondary and block.priority == "secondary":
            continue
        if block.priority == "secondary" and best_score > 0.0:
            continue

        incumbent, summary = _run_block(
            scenario=scenario,
            incumbent=incumbent,
            block=block,
            search_r=search_r,
            seed=seed,
            search_n_jobs=search_n_jobs,
            progress=progress,
            verbose_progress=verbose_progress,
            max_checkpoints=max_checkpoints,
            search_dir=search_dir,
        )
        best_score = float(summary.iloc[0]["score"])
        summaries.append(summary)
        executed_blocks.append(block)

    for block in executed_blocks:
        refine_block = _build_refine_block(block, incumbent)
        incumbent, summary = _run_block(
            scenario=scenario,
            incumbent=incumbent,
            block=refine_block,
            search_r=search_r,
            seed=seed,
            search_n_jobs=search_n_jobs,
            progress=progress,
            verbose_progress=verbose_progress,
            max_checkpoints=max_checkpoints,
            search_dir=search_dir,
        )
        best_score = float(summary.iloc[0]["score"])
        summaries.append(summary)

    return incumbent, summaries


def _final_compare_row(agg_final_df: pd.DataFrame) -> Dict[str, Any]:
    pivot = _summarize_scores(agg_final_df)
    row = pivot.iloc[0].to_dict()
    return {
        "score": float(row["score"]),
        "custom_regret": float(row["custom_regret"]),
        "moss_regret": float(row["moss_regret"]),
    }


def _write_summary(root_dir: str, best_configs: Dict[str, Dict[str, Any]], final_rows: Dict[str, Dict[str, Any]]) -> None:
    summary = {
        "best_configs": best_configs,
        "final_comparison": final_rows,
    }
    with open(os.path.join(root_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scenario C/E targeted grid search and final plotting")
    parser.add_argument("--output-dir", type=str, default="outputs")
    parser.add_argument("--seed", type=int, default=20260309)
    parser.add_argument("--n-jobs", type=int, default=8)
    parser.add_argument("--search-n-jobs", type=int, default=None)
    parser.add_argument("--final-n-jobs", type=int, default=None)
    parser.add_argument("--search-r", type=int, default=8)
    parser.add_argument("--final-r", type=int, default=50)
    parser.add_argument("--max-checkpoints", type=int, default=2000)
    parser.add_argument("--progress", choices=["auto", "on", "off"], default="on")
    parser.add_argument("--verbose-progress", action="store_true")
    parser.add_argument("--skip-secondary", action="store_true")
    parser.add_argument("--reduced-search", action="store_true")
    parser.add_argument("--critical-only", action="store_true")
    parser.add_argument("--scenarios", type=str, default="C,E")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    scenarios = [item.strip().upper() for item in args.scenarios.split(",") if item.strip()]
    search_n_jobs = int(args.search_n_jobs) if args.search_n_jobs is not None else int(args.n_jobs)
    final_n_jobs = int(args.final_n_jobs) if args.final_n_jobs is not None else int(args.n_jobs)
    blocks_by_scenario = _scenario_blocks(
        reduced_search=bool(args.reduced_search),
        critical_only=bool(args.critical_only),
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root_dir = os.path.join(args.output_dir, f"ce_search_{timestamp}")
    os.makedirs(root_dir, exist_ok=True)
    search_dir = os.path.join(root_dir, "search")
    os.makedirs(search_dir, exist_ok=True)

    best_configs: Dict[str, Dict[str, Any]] = {}
    final_rows: Dict[str, Dict[str, Any]] = {}
    all_search_summaries: List[pd.DataFrame] = []

    for scenario in scenarios:
        incumbent, summaries = _search_scenario(
            scenario=scenario,
            blocks=blocks_by_scenario[scenario],
            search_r=int(args.search_r),
            seed=int(args.seed),
            search_n_jobs=search_n_jobs,
            progress=str(args.progress),
            verbose_progress=bool(args.verbose_progress),
            max_checkpoints=int(args.max_checkpoints),
            search_dir=search_dir,
            skip_secondary=bool(args.skip_secondary),
        )
        best_configs[scenario] = incumbent
        all_search_summaries.extend(summaries)

        final_results = _run_grid_for_experiments(
            experiments=[incumbent],
            algorithms=ALGO_ORDER,
            R=int(args.final_r),
            seed=int(args.seed),
            n_jobs=final_n_jobs,
            progress=str(args.progress),
            verbose_progress=bool(args.verbose_progress),
            max_checkpoints=int(args.max_checkpoints),
        )
        scenario_dir = os.path.join(root_dir, f"scenario_{scenario}")
        _save_final_run(
            scenario=scenario,
            best_cfg=incumbent,
            results=final_results,
            scenario_dir=scenario_dir,
            final_r=int(args.final_r),
            seed=int(args.seed),
        )
        final_rows[scenario] = _final_compare_row(final_results["agg_final"])

    if all_search_summaries:
        pd.concat(all_search_summaries, ignore_index=True).to_csv(
            os.path.join(root_dir, "search_summary.csv"),
            index=False,
        )

    _write_summary(root_dir=root_dir, best_configs=best_configs, final_rows=final_rows)
    print(f"Saved outputs to: {os.path.abspath(root_dir)}")


if __name__ == "__main__":
    main()
