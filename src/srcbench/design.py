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
PROFILES = ["full", "tail", "smoke-small", "smoke-dense", "screen-all"]


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
    if "screen_all" in protocol:
        identifiers = protocol["screen_all"]["methods"]
        if len(identifiers) != len(METHODS) or set(identifiers) != set(METHODS):
            raise ValueError("screen-all must evaluate every registered method exactly once")
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


def _spread_indices(total, mandatory, target):
    """Fill the largest unrepresented rank gap, using earliest-rank ties."""
    chosen = set(mandatory)
    target = min(total, max(target, len(chosen)))
    while len(chosen) < target:
        ordered = sorted(chosen)
        best, distance = None, -1
        for left, right in zip(ordered, ordered[1:]):
            if right-left <= 1:
                continue
            middle = (left+right)//2
            separation = min(middle-left, right-middle)
            if separation > distance or (separation == distance and (best is None or middle < best)):
                best, distance = middle, separation
        if best is None:
            raise ValueError("could not fill the requested deterministic rank subset")
        chosen.add(best)
    return sorted(chosen)


def _screen_derivative(layout, spec):
    """Shrink one layout while preserving actual record identities and batches.

    Target K is a size request. Preserving all record batches and both end
    batches takes precedence, with any necessary expansion explicitly stored.
    Distinct selected source batches remain distinct after time compression.
    """
    result = deepcopy(layout)
    source = layout["arms"]
    total = len(source)
    horizon = int(spec["horizon"])
    group = layout["group"]
    if group in spec["keep_all_groups"]:
        requested = total
    else:
        requested = int(spec["target_arms"][group][str(total)])
    source_flags = record_flags(source)
    # Reconstruct complete source batches; a five-arm burst remains one
    # five-arm burst, including the arms that are not themselves records.
    batches = []
    start = 0
    while start < total:
        end = start+1
        while end < total and source[end]["arrival"] == source[start]["arrival"]:
            end += 1
        batches.append(list(range(start, end)))
        start = end
    bursting = layout["metadata"].get("family") == "bursty_reservoir"
    if bursting:
        batch_size = int(layout["metadata"].get("batch_size", 5))
        if any(len(batch) != batch_size for batch in batches):
            raise ValueError("bursty screen requires complete original equal-sized batches")
        mandatory = {0, len(batches)-1}
        mandatory.update(b for b, members in enumerate(batches) if any(source_flags[i] for i in members))
        target_batches = (requested+batch_size-1)//batch_size
        selected_batches = _spread_indices(len(batches), mandatory, target_batches)
        selected = [i for b in selected_batches for i in batches[b]]
        strategy = "complete five-arm batches; all record batches and first/last; longest-gap rank fill"
    else:
        mandatory = {0, total-1}
        mandatory.update(i for i, flag in enumerate(source_flags) if flag)
        mandatory.add(max(range(total), key=lambda i: source[i]["mean"]))
        selected = _spread_indices(total, mandatory, requested)
        strategy = "all source record identities, source best, first/last; longest-gap rank fill"
    result["arms"] = [deepcopy(source[i]) for i in selected]
    selected_source_times = sorted({a["arrival"] for a in result["arms"]})
    if len(selected_source_times) > horizon:
        raise ValueError("screen horizon cannot preserve distinct selected arrival batches")
    mapped, adjustments, previous = {}, [], 0
    for position, birth in enumerate(selected_source_times):
        nominal = 1+(birth-1)*horizon//layout["T"]
        remaining = len(selected_source_times)-position-1
        actual = max(previous+1, min(nominal, horizon-remaining))
        mapped[birth] = actual
        if actual != nominal:
            adjustments.append(dict(parent_arrival=birth, nominal_arrival=nominal, actual_arrival=actual))
        previous = actual
    for arm in result["arms"]:
        arm["arrival"] = mapped[arm["arrival"]]
    flags = record_flags(result["arms"])
    changes = []
    for arm, parent_index, flag in zip(result["arms"], selected, flags):
        arm["record"] = bool(flag)
        if bool(flag) != bool(source_flags[parent_index]):
            changes.append(parent_index)
    result["T"] = horizon
    actual_k = len(result["arms"])
    result["id"] = f"screen-all__{layout['id']}__T{horizon}__K{actual_k}"
    result["name"] = f"screen-all:{layout['name']}:T{horizon}:K{actual_k}"
    expansion = ("mandatory complete record batches and end batches exceed the target"
                 if actual_k > requested else None)
    result["metadata"]["derivative"] = dict(
        purpose="small-sample derivative screen; not a rerun of the original full setting",
        parent_id=layout["id"], parent_T=layout["T"], parent_arm_count=total,
        requested_arm_count=requested, actual_arm_count=actual_k,
        actual_T=horizon, parent_density=total/layout["T"],
        actual_density=actual_k/horizon, selected_parent_indices=selected,
        parent_canonical_sha256=layout["metadata"]["canonical_sha256"],
        selection_strategy=strategy, expansion_reason=expansion,
        source_batch_count=len(batches), actual_batch_count=len(selected_source_times),
        source_batch_size=5 if bursting else None,
        arrival_transform="nominal 1+floor((birth-1)*screen_T/parent_T), constrained strictly increasing across selected source batches",
        arrival_collision_adjustments=adjustments,
        record_flags="recomputed on the retained derivative with entire-batch semantics",
        record_status_changes=changes,
        noise_record_note="Record-dependent noise uses derivative batch records; every original record is retained, and changes relative to source flags are listed.",
        no_outcome_adaptive_selection=True)
    payload = {k: result[k] for k in ["T", "epsilon", "eta", "delta", "arms"]}
    result["metadata"]["canonical_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
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
    if profile == "screen-all":
        return _screen_tasks(layouts, protocol)
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


def _screen_tasks(layouts, protocol):
    spec = protocol["screen_all"]
    derivatives = [_screen_derivative(s, spec) for s in layouts]
    seed = protocol["seed_bases"][spec["seed_key"]]
    tasks = [_task(s, law, rep, seed, "screen", {m: ["reward", "joint"] for m in spec["methods"]})
             for s in derivatives for law in spec["laws_by_group"][s["group"]]
             for rep in range(spec["replications"])]
    if len(derivatives) != spec["layouts"] or len({t["cell_id"] for t in tasks}) != spec["cells"]:
        raise ValueError("screen-all layout/cell count differs from its frozen profile")
    if sum(len(t["methods"]) for t in tasks) != spec["unique_paths"]:
        raise ValueError("screen-all path count differs from its frozen profile")
    for task in tasks:
        task["diagnostics"] = spec["diagnostics"]
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
                small_derivatives=profile.replace("_", "-") == "screen-all",
                smoke_derivatives=profile.replace("_", "-").startswith("smoke-"))
