from __future__ import annotations

import json
import os
import textwrap
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCENARIO_PLOT_LABELS = {"C": "1", "E": "2"}
ALGO_PLOT_LABELS = {
    "custom_elim": "UCB-AA",
    "moss": "G-MOSS",
    "naive_elim": "NE",
    "ucb": "G-UCB1",
    "erse": "D-SE",
}
TITLE_FONTSIZE = 20
LABEL_FONTSIZE = 16
TICK_FONTSIZE = 13
LEGEND_FONTSIZE = 13


def _plot_scenario_name(scenario: Any) -> str:
    scen = str(scenario).upper()
    mapped = SCENARIO_PLOT_LABELS.get(scen, scen)
    return f"scenario {mapped}"


def _plot_algo_name(algo: Any) -> str:
    key = str(algo)
    return ALGO_PLOT_LABELS.get(key, key)


def _safe_fname(x: str) -> str:
    out = []
    for ch in x:
        if ch.isalnum() or ch in {"-", "_"}:
            out.append(ch)
        else:
            out.append("_")
    return "".join(out)


def _fmt_value(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.6g}"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(_fmt_value(x) for x in v) + "]"
    return str(v)


def _parse_params(params_json: Any) -> Dict[str, Any]:
    if isinstance(params_json, str):
        try:
            obj = json.loads(params_json)
            if isinstance(obj, dict):
                return obj
        except Exception:
            return {}
    return {}


def _build_param_text(scenario: Any, params_json: Any) -> str:
    params = _parse_params(params_json).copy()
    params.pop("scenario", None)
    scenario_params = params.pop("scenario_params", {})
    if not isinstance(scenario_params, dict):
        scenario_params = {}

    preferred = ["T", "K0", "arrival_mode", "lambda", "rho", "M", "B", "T_burst"]
    parts = []

    for key in preferred:
        if key in params:
            parts.append(f"{key}={_fmt_value(params[key])}")

    for key in sorted(k for k in params.keys() if k not in preferred):
        parts.append(f"{key}={_fmt_value(params[key])}")

    for key in sorted(scenario_params.keys()):
        parts.append(f"{key}={_fmt_value(scenario_params[key])}")

    if not parts:
        return _plot_scenario_name(scenario)

    wrapped = textwrap.fill(
        ", ".join(parts),
        width=100,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return f"{_plot_scenario_name(scenario)}\n{wrapped}"


def _build_param_tag(params_json: Any) -> str:
    params = _parse_params(params_json).copy()
    params.pop("scenario", None)
    scenario_params = params.pop("scenario_params", {})
    if not isinstance(scenario_params, dict):
        scenario_params = {}

    tag_parts = []
    for key in ["T", "K0", "M", "arrival_mode"]:
        if key in params:
            tag_parts.append(f"{key}{_fmt_value(params[key])}")

    if "lambda" in params:
        tag_parts.append(f"lam{_fmt_value(params['lambda'])}")
    if "rho" in params and "lambda" not in params:
        tag_parts.append(f"rho{_fmt_value(params['rho'])}")

    for key in ["Delta_step", "delta_step", "m0", "Delta_min", "delta_min", "B", "p_spike", "pi_good"]:
        if key in scenario_params:
            tag_parts.append(f"{key}{_fmt_value(scenario_params[key])}")

    if not tag_parts:
        tag_parts = ["cfg"]

    tag = "_".join(tag_parts)
    tag = _safe_fname(tag)
    return tag[:120]


def plot_regret_vs_t(agg_ckpt_df: pd.DataFrame, out_dir: str) -> None:
    if agg_ckpt_df.empty:
        return

    plot_dir = os.path.join(out_dir, "plots")
    os.makedirs(plot_dir, exist_ok=True)

    for (scenario, params_json), sub in agg_ckpt_df.groupby(["scenario", "params_json"], dropna=False):
        fig, ax = plt.subplots(figsize=(11, 6))

        for algo, grp in sub.groupby("algo", dropna=False):
            g = grp.sort_values("t")
            x = g["t"].to_numpy()
            y = g["dynamic_regret_mean"].to_numpy()
            ci = g["dynamic_regret_ci95"].to_numpy()

            ax.plot(x, y, label=_plot_algo_name(algo), linewidth=2)
            ax.fill_between(x, y - ci, y + ci, alpha=0.2)

        ax.set_title(f"Dynamic Regret vs t\n{_build_param_text(scenario, params_json)}", fontsize=TITLE_FONTSIZE)
        ax.set_xlabel("t", fontsize=LABEL_FONTSIZE)
        ax.set_ylabel("")
        ax.tick_params(axis="both", labelsize=TICK_FONTSIZE)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=LEGEND_FONTSIZE)

        tag = _build_param_tag(params_json)
        fname = _safe_fname(f"regret_vs_t_{scenario}_{tag}.png")
        fig.tight_layout()
        fig.savefig(os.path.join(plot_dir, fname), dpi=160)
        plt.close(fig)


def plot_final_bars(agg_final_df: pd.DataFrame, metric: str, out_dir: str) -> None:
    if agg_final_df.empty:
        return

    mean_col = f"{metric}_mean"
    ci_col = f"{metric}_ci95"
    if mean_col not in agg_final_df.columns:
        return

    plot_dir = os.path.join(out_dir, "plots")
    os.makedirs(plot_dir, exist_ok=True)

    for (scenario, params_json), sub in agg_final_df.groupby(["scenario", "params_json"], dropna=False):
        s = sub.sort_values("algo")
        labels = [_plot_algo_name(algo) for algo in s["algo"].astype(str).tolist()]
        vals = s[mean_col].to_numpy()
        cis = s[ci_col].to_numpy() if ci_col in s.columns else np.zeros_like(vals)

        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(len(labels))
        ax.bar(x, vals, yerr=cis, capsize=4, alpha=0.85)

        ax.set_xticks(x)
        if metric.startswith("wasted_pulls"):
            ax.set_xticklabels(labels, rotation=0, ha="center", fontsize=TICK_FONTSIZE)
        else:
            ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=TICK_FONTSIZE)
        ax.set_ylabel("")
        ax.set_title(f"{metric}\n{_build_param_text(scenario, params_json)}", fontsize=TITLE_FONTSIZE)
        ax.tick_params(axis="y", labelsize=TICK_FONTSIZE)
        ax.grid(axis="y", alpha=0.25)

        tag = _build_param_tag(params_json)
        fname = _safe_fname(f"bar_{metric}_{scenario}_{tag}.png")
        fig.tight_layout()
        fig.savefig(os.path.join(plot_dir, fname), dpi=160)
        plt.close(fig)


def make_all_plots(results_dir: str) -> None:
    agg_ckpt_path = os.path.join(results_dir, "agg_checkpoint_metrics.csv")
    agg_final_path = os.path.join(results_dir, "agg_final_metrics.csv")

    if not os.path.exists(agg_ckpt_path) or not os.path.exists(agg_final_path):
        return

    agg_ckpt_df = pd.read_csv(agg_ckpt_path)
    agg_final_df = pd.read_csv(agg_final_path)

    plot_regret_vs_t(agg_ckpt_df, results_dir)

    plot_final_bars(agg_final_df, metric="final_active_size", out_dir=results_dir)
    plot_final_bars(agg_final_df, metric="wasted_pulls_eps_0_05", out_dir=results_dir)
    plot_final_bars(agg_final_df, metric="wasted_pulls_eps_0_1", out_dir=results_dir)
