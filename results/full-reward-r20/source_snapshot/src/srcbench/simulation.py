"""Simulation is the only layer allowed to see means and future arrivals."""
from __future__ import annotations

import math
import time

import numpy as np

from .environment import PotentialRewards, stable_seed


RUN_FIELDS = ("cohort group layout_id law rep method suites T K epsilon eta delta "
              "regret area area_all eligible_arm_time all_arm_time final_unresolved "
              "final_all_unresolved service_pulls service_attempts service_denials "
              "guard_exclusions guard_changed label_error coverage_error empty_intersection "
              "reward_tax service_tax budget_scale arrival_spectrum checkpoint_hits never_sampled action_hash "
              "runtime_seconds service_regret service_mass old_arms old_never_sampled").split()
TRACE_FIELDS = ("cohort group layout_id law rep method suites t T K regret area area_all "
                "unresolved unresolved_all service_pulls never_sampled budget_scale arrival_spectrum").split()
COUNT_FIELDS = ("cohort group layout_id law rep method suites t T arm birth mean n "
                "current_gap final_gap last_arrival").split()


def snapshot_times(T: int, linear_points=41, log_points=20) -> set[int]:
    linear = np.linspace(1, T, min(linear_points, T), dtype=int)
    logarithmic = np.geomspace(1, T, min(log_points, T)).astype(int)
    return {1, T, *map(int, linear), *map(int, logarithmic)}


def simulate_task(task: dict, methods: dict) -> dict:
    """A shard is one potential-world replicate, shared by all its methods."""
    from .policy import Policy

    layout, law, rep = task["layout"], task["law"], task["rep"]
    seed_base = task["seed_base"]
    world = PotentialRewards(layout, law, rep, seed_base)
    arms = world.layout["arms"]
    births = np.array([a["arrival"] for a in arms], dtype=np.int64)
    means = np.array([a["mean"] for a in arms], dtype=float)
    T, Kmax = int(layout["T"]), len(arms)
    diagnostic = task.get("diagnostics", {})
    checkpoints = snapshot_times(T, diagnostic.get("linear_points", 41),
                                 diagnostic.get("log_points", 20))
    smoke = task["cohort"] == "smoke"
    keep_trace = smoke or rep < diagnostic.get("trajectory_replications", 4)
    result = {"task_id": task["task_id"], "runs": [], "trajectories": [], "counts": []}
    for method_id in task["methods"]:
        spec = methods[method_id]
        policy = Policy(spec, epsilon=layout["epsilon"], eta=layout["eta"],
                        delta=layout["delta"],
                        seed=stable_seed(seed_base, layout["id"], law, rep, "policy", method_id),
                        horizon=T if spec.get("known_horizon", False) else None)
        membership = task.get("method_suites", {}).get(method_id, task.get("suites", []))
        meta = {"cohort": task["cohort"], "group": layout["group"],
                "layout_id": layout["id"], "law": law, "rep": rep,
                "method": method_id, "suites": ";".join(membership)}
        regret = service_regret = service_mass = 0.0
        area = area_all = eligible_arm_time = all_arm_time = 0
        service_pulls = attempts = denials = exclusions = changed = 0
        label_error = coverage_error = 0
        action_hash = 14695981039346656037
        active = 0
        started = time.perf_counter()
        for t in range(1, T + 1):
            previous = active
            while active < Kmax and births[active] <= t:
                active += 1
            chosen = policy.choose(list(range(previous, active)))
            if not isinstance(chosen, (int, np.integer)) or not 0 <= chosen < active:
                raise RuntimeError("Policy selected an unavailable arm")
            best = float(np.max(means[:active]))
            gap = best - float(means[chosen])
            regret += gap
            d = policy.last_decision
            service = d.get("branch") in {"classification", "service"}
            service_pulls += int(service)
            service_regret += gap if service else 0.0
            attempts += int(d.get("attempt", False))
            denials += int(d.get("denied", False))
            exclusions += int(d.get("guard_exclusions", 0))
            changed += int(d.get("guard_changed", False))
            service_mass += float(d.get("probability", 0.0))
            reward = world.draw(int(chosen), int(policy.n[chosen]))
            policy.observe(reward)
            positive, negative, unresolved_ids = policy.report()
            pos = np.array(positive, dtype=np.int64)
            neg = np.array(negative, dtype=np.int64)
            unresolved = np.array(unresolved_ids, dtype=np.int64)
            gaps = best - means[:active]
            eligible = np.abs(gaps - layout["epsilon"]) > layout["eta"] + 1e-12
            pending = int(np.count_nonzero(eligible[unresolved]))
            pending_all = len(unresolved)
            area += pending
            area_all += pending_all
            eligible_arm_time += int(np.count_nonzero(eligible))
            all_arm_time += active
            if (len(pos) and np.any(gaps[pos] > layout["epsilon"] + 1e-12)) or (
                    len(neg) and np.any(gaps[neg] <= layout["epsilon"] + 1e-12)):
                label_error = 1
            if policy.lower[chosen] > means[chosen] + 1e-12 or policy.upper[chosen] < means[chosen] - 1e-12:
                coverage_error = 1
            action_hash = ((action_hash ^ (int(chosen) + 1)) * 1099511628211) & ((1 << 64) - 1)
            keep_counts = smoke or method_id in diagnostic.get("per_arm_methods", ["SRC-R", "SRC-KL-R"])
            if t in checkpoints and (keep_trace or (t == T and keep_counts)):
                state = policy.state()
                if keep_trace:
                    result["trajectories"].append({**meta, "t": t, "T": T, "K": active,
                        "regret": regret, "area": area, "area_all": area_all,
                        "unresolved": pending, "unresolved_all": pending_all,
                        "service_pulls": service_pulls,
                        "never_sampled": int(np.count_nonzero(policy.n[:active] == 0)),
                        "budget_scale": float(state["budget_scale"]),
                        "arrival_spectrum": float(state["arrival_spectrum"])})
                if keep_counts and ((Kmax <= 28 and keep_trace) or t == T):
                    for i in range(active):
                        result["counts"].append({**meta, "t": t, "T": T, "arm": i,
                            "birth": int(births[i]), "mean": float(means[i]),
                            "n": int(policy.n[i]), "current_gap": float(gaps[i]),
                            "final_gap": float(np.max(means) - means[i]),
                            "last_arrival": int(births[-1])})
        state = policy.state()
        old = (T - births + 1) >= T / 4
        row = {**meta, "T": T, "K": Kmax, "epsilon": layout["epsilon"],
            "eta": layout["eta"], "delta": layout["delta"], "regret": regret,
            "area": area, "area_all": area_all, "eligible_arm_time": eligible_arm_time,
            "all_arm_time": all_arm_time, "final_unresolved": pending,
            "final_all_unresolved": pending_all, "service_pulls": service_pulls,
            "service_attempts": attempts, "service_denials": denials,
            "guard_exclusions": exclusions, "guard_changed": changed,
            "label_error": label_error, "coverage_error": coverage_error,
            "empty_intersection": int(state.get("failed", False)),
            "reward_tax": float(state["reward_tax"]), "service_tax": float(state["service_tax"]),
            "budget_scale": float(state["budget_scale"]),
            "arrival_spectrum": float(state["arrival_spectrum"]),
            "checkpoint_hits": int(state.get("checkpoint_hits", 0)),
            "never_sampled": int(np.count_nonzero(policy.n == 0)),
            "action_hash": str(action_hash), "runtime_seconds": time.perf_counter() - started,
            "service_regret": service_regret, "service_mass": service_mass,
            "old_arms": int(np.count_nonzero(old)),
            "old_never_sampled": int(np.count_nonzero(old & (policy.n == 0)))}
        validate_run(row)
        result["runs"].append(row)
    return result


def validate_run(row: dict) -> None:
    T, K = int(row["T"]), int(row["K"])
    for field in RUN_FIELDS:
        if field in {"cohort", "group", "layout_id", "law", "method", "suites", "action_hash"}:
            continue
        if not math.isfinite(float(row[field])):
            raise ValueError(f"Nonfinite endpoint {field}")
    if not -1e-9 <= row["regret"] <= T + 1e-8:
        raise ValueError("Invalid regret")
    if not 0 <= row["area"] <= row["area_all"] <= row["all_arm_time"] <= T * K:
        raise ValueError("Invalid unresolved area")
    if row["area"] > row["eligible_arm_time"]:
        raise ValueError("Unresolved cost exceeds eligible arm-time")
    if not 0 <= row["service_pulls"] <= T or row["service_attempts"] != row["service_pulls"] + row["service_denials"]:
        raise ValueError("Inconsistent service counters")
    for flag in ("label_error", "coverage_error", "empty_intersection"):
        if row[flag] not in (0, 1):
            raise ValueError("Invalid scientific failure flag")
