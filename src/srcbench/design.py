"""Frozen layouts and task expansion; no numerical outcomes are consulted."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .methods import (BASELINE_IDS, REWARD_METHOD_IDS, JOINT_METHOD_IDS,
                      TAIL_METHOD_IDS, METHODS, validate_registry)

CONFIG_ROOT = Path(__file__).resolve().parents[2] / "configs"
LAWS_16 = ["bernoulli", "beta02", "beta2", "beta20", "binomial4",
           "binomial16", "deterministic", "two_point", "uniform", "spike_mix",
           "hetero_best_noisy", "hetero_best_quiet", "hetero_jackpot",
           "endpoint_two", "rare_jackpot", "trunc_normal"]
LAWS_8 = ["bernoulli", "beta02", "beta20", "uniform", "hetero_best_noisy",
          "hetero_best_quiet", "hetero_jackpot", "trunc_normal"]
LAWS_4 = ["bernoulli", "beta20", "hetero_best_noisy", "hetero_best_quiet"]
TAIL_LAYOUT_NAMES = ["h_record_staircase", "h_two_large_bursts",
                     "h_irregular_arrivals", "h_late_challenger",
                     "h_early_flood_late_record", "h_anchor_reversal"]
PROFILES = ["full", "tail", "smoke-small", "smoke-dense"]


def load_layouts(path=None):
    """Read the local canonical snapshot, without any proposal dependency."""
    with Path(path or CONFIG_ROOT / "layouts.json").open(encoding="utf-8") as f:
        layouts = json.load(f)
    if len({s["id"] for s in layouts}) != len(layouts):
        raise ValueError("duplicate layout IDs in frozen configuration")
    return layouts


def _config_reference(value):
    path = (CONFIG_ROOT.parent / value).resolve()
    if not path.is_relative_to(CONFIG_ROOT.resolve()):
        raise ValueError("protocol inputs must be frozen files under configs/")
    return path


def load_protocol(path=None):
    """Read the actual driver, validating method identities before expansion."""
    with Path(path or CONFIG_ROOT / "protocol.json").open(encoding="utf-8") as stream:
        protocol = json.load(stream)
    validate_registry(_config_reference(protocol["method_file"]))
    for suite in ["reward", "joint", "tail"]:
        identifiers = protocol[suite]["methods"]
        if len(set(identifiers)) != len(identifiers) or any(m not in METHODS for m in identifiers):
            raise ValueError(f"invalid frozen {suite} method list")
    for name, spec in protocol["smoke_profiles"].items():
        if any(m not in METHODS for m in spec["methods"]):
            raise ValueError(f"invalid frozen {name} method list")
    return protocol


def record_flags(arms):
    """Original reader semantics: compare the WHOLE simultaneous batch.

    A record meets the maximum mean through its batch, to 1e-14. The flags
    are computed before any simultaneous-label permutation and travel with
    the arm. This prevents an early arm within a batch becoming a fake record.
    """
    result = []
    running = 0.
    i = 0
    while i < len(arms):
        j = i + 1
        while j < len(arms) and arms[j]["arrival"] == arms[i]["arrival"]:
            j += 1
        running = max(running, *(a["mean"] for a in arms[i:j]))
        result.extend(a["mean"] >= running - 1e-14 for a in arms[i:j])
        i = j
    return result


def _derivative(layout, horizon, max_arms=None, label="smoke"):
    result = deepcopy(layout)
    old_horizon = result["T"]
    original_arms = result["arms"]
    if max_arms is not None and len(original_arms) > max_arms:
        # Even rank spacing retains all ten block starts for K100 -> K40,
        # including both late record changes at 80% and 90% of the horizon.
        selected = [i * len(original_arms) // max_arms for i in range(max_arms)]
        result["arms"] = [original_arms[i] for i in selected]
    else:
        selected = list(range(len(original_arms)))
    for arm in result["arms"]:
        arm["arrival"] = min(horizon, 1 + (arm["arrival"] - 1) * horizon // old_horizon)
    for arm, flag in zip(result["arms"], record_flags(result["arms"])):
        arm["record"] = flag
    result["T"] = horizon
    result["id"] = f"{label}__{layout['id']}__T{horizon}__K{len(result['arms'])}"
    result["name"] = f"{label}:{layout['name']}:T{horizon}:K{len(result['arms'])}"
    result["metadata"]["derivative"] = dict(
        purpose="implementation smoke only; excluded from scientific summaries",
        parent_id=layout["id"], parent_T=old_horizon,
        parent_arm_count=len(original_arms), selected_parent_indices=selected,
        arrival_transform="1 + floor((birth - 1) * smoke_T / parent_T)",
        record_flags="recomputed on the derivative with simultaneous-batch semantics")
    return result


def _task(layout, law, rep, seed_base, cohort, method_suites):
    cell_id = f"{layout['id']}__{law}"
    key = [cell_id, int(rep), int(seed_base), cohort]
    digest = hashlib.sha256(json.dumps(key, separators=(",", ":")).encode()).hexdigest()[:20]
    suites = sorted({suite for tags in method_suites.values() for suite in tags})
    return dict(task_id=f"{cohort}_{digest}", cell_id=cell_id, layout=layout,
                law=law, rep=int(rep), seed_base=int(seed_base), cohort=cohort,
                methods=list(method_suites), method_suites=method_suites, suites=suites)


def _full_tasks(layouts, protocol):
    tasks = []
    for layout in layouts:
        group = layout["group"]
        if group not in {"f17", "adaptive", "dense", "scale"}:
            raise ValueError(f"unsupported layout group: {group}")
        bucket = "small" if group in {"f17", "adaptive"} else group
        laws = protocol["reward"][f"{bucket}_laws"]
        reps = protocol["reward"]["replications"][bucket]
        joint_laws = protocol["joint"][f"{bucket}_laws"]
        joint_reps = protocol["joint"]["replications"][bucket]
        if not set(joint_laws).issubset(laws) or joint_reps > reps:
            raise ValueError("joint endpoints must be a matched subset of reward repetitions")
        for law in laws:
            for rep in range(reps):
                tags = {m: ["reward"] for m in protocol["reward"]["methods"]}
                if law in joint_laws and rep < joint_reps:
                    # All reward methods get the SAME joint subset as the
                    # positive-service methods, including the reused R paths.
                    for value in tags.values():
                        value.append("joint")
                    for m in protocol["joint"]["methods"]:
                        if m not in tags:
                            tags[m] = ["joint"]
                tasks.append(_task(layout, law, rep, protocol["seed_bases"]["main"], "main", tags))
    return tasks


def build_tasks(profile="full", protocol_path=None):
    """Expand one declared profile; one task shares an environment/replicate.

    The full profile covers all 540 cells, merges reward/joint method
    sets, and includes the independent 128-replicate tail cohort.
    Smoke profiles are explicitly tagged derivatives of frozen layouts.
    """
    profile = profile.replace("_", "-")
    protocol = load_protocol(protocol_path)
    layouts = load_layouts(_config_reference(protocol["layout_file"]))
    if profile == "full":
        tasks = _full_tasks(layouts, protocol) + _tail_tasks(layouts, protocol)
        if len(layouts) != protocol["layouts"] or len({t["cell_id"] for t in tasks}) != protocol["cells"]:
            raise ValueError("expanded layouts/cells differ from the frozen protocol")
        if sum(len(t["methods"]) for t in tasks) != protocol["unique_paths"]:
            raise ValueError("expanded path count differs from the frozen protocol")
        return _attach_diagnostics(tasks, protocol)
    if profile == "tail":
        return _attach_diagnostics(_tail_tasks(layouts, protocol), protocol)
    if profile not in protocol["smoke_profiles"]:
        raise ValueError(f"unknown profile {profile!r}; choose one of {PROFILES}")
    spec = protocol["smoke_profiles"][profile]
    chosen = [s for s in layouts if s["group"] == spec["parent_group"] and s["name"] in spec["layout_names"]]
    chosen = [_derivative(s, spec["horizon"], max_arms=spec.get("max_arms"), label=profile) for s in chosen]
    methods, laws = spec["methods"], spec["laws"]
    seed = protocol["seed_bases"][spec["seed_key"]]
    if len(chosen) != 2:
        raise ValueError("smoke profile must contain its two frozen parent layouts")
    tasks = [_task(s, law, rep, seed, "smoke", {m: ["reward", "joint"] for m in methods})
             for s in chosen for law in laws for rep in range(spec["replications"])]
    return _attach_diagnostics(tasks, protocol)


def _attach_diagnostics(tasks, protocol):
    for task in tasks:
        task["diagnostics"] = protocol["diagnostics"]
    return tasks


def _tail_tasks(layouts, protocol):
    spec = protocol["tail"]
    chosen = [s for s in layouts if s["group"] == "adaptive" and s["name"] in spec["layout_names"]]
    if len(chosen) != len(spec["layout_names"]):
        raise ValueError("the six frozen tail layouts are missing")
    return [_task(s, law, rep, protocol["seed_bases"]["tail"], "tail", {m: ["tail"] for m in spec["methods"]})
            for s in chosen for law in spec["laws"] for rep in range(spec["replications"])]


def preview(profile="full"):
    """Return a JSON-serializable, simulation-free workload summary."""
    tasks = build_tasks(profile)
    groups = {}
    for group in sorted({t["layout"]["group"] for t in tasks}):
        subset = [t for t in tasks if t["layout"]["group"] == group]
        groups[group] = dict(layouts=len({t["layout"]["id"] for t in subset}),
                             cells=len({t["cell_id"] for t in subset}), tasks=len(subset),
                             paths=sum(len(t["methods"]) for t in subset))
    suite_counts = Counter()
    for task in tasks:
        for tags in task["method_suites"].values():
            suite_counts.update(tags)
    return dict(profile=profile, layouts=len({t["layout"]["id"] for t in tasks}),
                cells=len({t["cell_id"] for t in tasks}), tasks=len(tasks),
                unique_paths=sum(len(t["methods"]) for t in tasks),
                methods=sorted({m for t in tasks for m in t["methods"]}),
                groups=groups, suite_paths=dict(suite_counts),
                no_simulation_performed=True,
                smoke_derivatives=profile.replace("_", "-").startswith("smoke-"))
