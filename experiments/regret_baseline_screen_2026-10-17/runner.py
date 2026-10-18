"""Independent regret-only screen on the unmodified F17 paired environments.

No certification, interval updates, tuning, or manuscript changes. Reference
selection calls the original production choose_dual with priority zero. Its
unused reporting state can therefore be omitted without changing any action.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import traceback

os.environ.setdefault("NUMBA_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np
from numba import njit

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT.parent / "fccp_frozen"
sys.path.insert(0, str(FROZEN / "src"))
from study import streams
from flexible_v2 import choose_dual, simulate_dual
from flexible_engine import update_interval

REFERENCE_NAMES = ["UCB1", "Growing-MOSS", "MC-MOSS", "Thompson", "KL-UCB", "F-R"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    tmp.replace(path)


def source_fingerprint():
    # Audit/report helpers may be added while a long run is active. Only code
    # actually imported by simulation belongs in this immutable runtime payload.
    own = [ROOT / n for n in ("runner.py", "new_policies.py", "sb_exp3.py") if (ROOT / n).is_file()]
    frozen = [FROZEN / "src" / n for n in ("study.py", "study_v2.py", "flexible_v2.py", "flexible_engine.py", "ccp_primitives.py")]
    return {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else "../fccp_frozen/" + str(p.relative_to(FROZEN)).replace("\\", "/"): sha(p) for p in own + frozen}


def reference_spec(name, original):
    return next(p for p in original["policies"] if p["name"] == name)


def make_case(original, si, rep, horizon=None):
    s = original["scenarios"][si]
    mu = np.asarray(s["means"], dtype=np.float64).copy()
    arrivals = np.asarray(s["arrivals"], dtype=np.int64)
    if original.get("shuffle_within_batch", False):
        rng = np.random.default_rng(original["reward_seed"] + 50_000_000 + si * 10000 + rep)
        for at in np.unique(arrivals):
            ids = np.flatnonzero(arrivals == at)
            mu[ids] = mu[ids][rng.permutation(len(ids))]
    # Generate the full original matrix even in small/debug runs. Truncating T
    # before generation would shift every arm after the first to different draws.
    rewards = streams(dict(s, means=mu.tolist()), original["reward_seed"] + si * 10000 + rep)
    T = s["T"] if horizon is None else min(s["T"], horizon)
    seed = original["policy_seed"] + si * 10000 + rep
    return s, mu, arrivals, rewards, T, seed


@njit(cache=False)
def simulate_reference(rewards, means, births, T, core, temperature, prior, beta_r, seed, stride=200, reporting_trace=False, eps=.2, eta=.05, delta=.05):
    """Same production action selection; optional true reporting state for audit."""
    np.random.seed(seed)
    K = len(means)
    n = np.zeros(K, np.int64)
    S = np.zeros(K)
    lower = np.zeros(K)
    upper = np.ones(K)
    q = np.empty(K, np.int64)
    for i in range(K):
        q[i] = math.ceil(2 / (eta / 4) ** 2 * math.log(4 * (i + 1) * (i + 2) / delta))
    k = 0; base = 0; segstart = 1; busy = 0; phase = 0.
    rtax = 0.; stax = 0.; smax = 0.; failed = False
    regret = 0.; projections = 0
    path = np.zeros((T // stride + 1, 2))
    actions = np.zeros(T, np.int64)
    for t in range(1, T + 1):
        while k < K and births[k] <= t:
            k += 1
        a, service, attempt, denial, mod, base, segstart, busy, phase, rtax, stax, smax, rate = choose_dual(
            n, S, lower, upper, q, births, k, t, base, segstart, busy, phase,
            rtax, stax, smax, failed, eps, eta, core, 0., False,
            beta_r, 1e100, .1, .02, 4., 50, temperature, prior)
        projections += mod
        actions[t - 1] = a
        x = rewards[a, n[a]]
        n[a] += 1
        S[a] += x
        if reporting_trace:
            failed = update_interval(n, S, lower, upper, q, a, eta, delta, failed)
        regret += np.max(means[:k]) - means[a]
        if t % stride == 0:
            path[t // stride, 0] = t
            path[t // stride, 1] = regret
    return regret, path, n, actions, S, rtax, projections, smax


def call_reference(rewards, means, births, T, pol, seed, stride=200, reporting_trace=False, scenario=None):
    s = scenario or {"epsilon": .2, "eta": .05, "delta": .05}
    return simulate_reference(rewards, means, births, T, int(pol["core"]), float(pol["temperature"]), float(pol["prior"]),
                              1e100 if pol["beta_r"] is None else float(pol["beta_r"]), seed, stride, reporting_trace,
                              s["epsilon"], s["eta"], s["delta"])


def load_new_module():
    sys.path.insert(0, str(ROOT))
    return importlib.import_module("new_policies")


_NEW_SIMULATOR = None


def get_new_simulator():
    global _NEW_SIMULATOR
    if _NEW_SIMULATOR is not None:
        return _NEW_SIMULATOR
    mod = load_new_module()
    choose = mod.new_choose
    update = mod.update_new

    @njit(cache=False)
    def simulate_new(rewards, means, births, T, code, p0, p1, p2, seed, stride=200):
        np.random.seed(seed)
        K = len(means)
        n = np.zeros(K, np.int64)
        S = np.zeros(K)
        Q = np.zeros(K)
        aux = np.zeros((K + 8, 8))
        k = 0; regret = 0.
        path = np.zeros((T // stride + 1, 2))
        actions = np.zeros(T, np.int64)
        for t in range(1, T + 1):
            while k < K and births[k] <= t:
                k += 1
            # The action function sees only past sufficient statistics and the
            # already observed arrival times, never means or potential rewards.
            a = choose(n, S, Q, k, t, births[:k], code, p0, p1, p2, aux)
            if a < 0 or a >= k:
                raise ValueError("Policy selected an unavailable arm")
            actions[t - 1] = a
            x = rewards[a, n[a]]
            update(n, S, Q, aux, k, t, a, x, code, p0, p1, p2)
            n[a] += 1
            S[a] += x
            Q[a] += x * x
            regret += np.max(means[:k]) - means[a]
            if t % stride == 0:
                path[t // stride, 0] = t
                path[t // stride, 1] = regret
        return regret, path, n, actions

    _NEW_SIMULATOR = simulate_new
    return simulate_new


def setting_audit(output):
    original_path = FROZEN / "protocols" / "holdout-freeze.json"
    original = json.loads(original_path.read_text())
    import numba
    import pandas
    obj = {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_protocol": "../fccp_frozen/protocols/holdout-freeze.json",
        "source_protocol_sha256": sha(original_path),
        "scenarios": [{"index": i, "name": s["name"], "T": s["T"], "K": len(s["means"]), "kind": s["kind"], "arrivals": s["arrivals"], "means": s["means"]} for i, s in enumerate(original["scenarios"])],
        "reps": original["reps"], "reward_seed": original["reward_seed"], "policy_seed": original["policy_seed"],
        "shuffle_within_batch": original.get("shuffle_within_batch", False),
        "reward_seed_formula": "reward_seed + scenario_index * 10000 + replication",
        "shuffle_seed_formula": "reward_seed + 50000000 + scenario_index * 10000 + replication",
        "policy_seed_formula": "policy_seed + scenario_index * 10000 + replication",
        "rewards": "Original study.streams; same full K by original T potential reward array reused across every method in each paired replication.",
        "policy_information": "Past statistics, physical clock, currently observed births, and explicitly declared constants only.",
        "existing_reference_specs": [reference_spec(n, original) for n in REFERENCE_NAMES],
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "numba": numba.__version__, "pandas": pandas.__version__, "platform": platform.platform()},
        "frozen_source_hash_match": {f: sha(FROZEN / "src" / f) == digest for f, digest in original["hashes"].items()},
    }
    if not all(obj["frozen_source_hash_match"].values()):
        raise RuntimeError("Original production source differs from holdout freeze")
    write_json(output, obj)
    return obj


def audit_reference_equivalence(outdir, horizon=800, full_endpoint=False):
    """Audit every reference on every environment, independently of new methods."""
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    original = json.loads((FROZEN / "protocols" / "holdout-freeze.json").read_text())
    import pandas as pd
    old = pd.read_csv(FROZEN / "results" / "holdout-all.csv")
    records = []
    for si in range(len(original["scenarios"])):
        s, mu, arr, rew, T, seed = make_case(original, si, 0, None if full_endpoint else horizon)
        for name in REFERENCE_NAMES:
            pol = reference_spec(name, original)
            start = time.perf_counter()
            fast = call_reference(rew, mu, arr, T, pol, seed, reporting_trace=False, scenario=s)
            traced = call_reference(rew, mu, arr, T, pol, seed, reporting_trace=True, scenario=s)
            # This is the actual frozen production simulator, not a local clone.
            production, prod_path, prod_counts = simulate_dual(rew, mu, arr, s["epsilon"], s["eta"], s["delta"], T,
                pol["core"], 0., False, 1e100 if pol["beta_r"] is None else pol["beta_r"], 1e100,
                pol["price"], pol["pfloor"], pol["k0"], pol["scheduler"], pol["temperature"], pol["prior"], seed, 200)
            matches = {
                "all_actions_reporting_omission": bool(np.array_equal(fast[3], traced[3])),
                "all_final_statistics": bool(np.array_equal(fast[2], traced[2]) and np.array_equal(fast[4], traced[4])),
                "regret_actual_production": bool(fast[0] == production[0]),
                "counts_actual_production": bool(np.array_equal(fast[2], prod_counts)),
                "paths_actual_production": bool(np.array_equal(fast[1][:, 1], prod_path[:, 1])),
                "ledger_actual_production": bool(fast[5] == production[15] and fast[6] == production[10] and fast[7] == production[17]),
            }
            row = dict(scenario=s["name"], method=name, T=T, rep=0, runtime=time.perf_counter() - start, checks=matches,
                       regret=float(fast[0]), counts=fast[2].tolist(), action_sha256=hashlib.sha256(fast[3].tobytes()).hexdigest())
            if T == s["T"]:
                frozen_value = float(old.loc[(old.scenario == s["name"]) & (old.rep == 0) & (old.method == name), "regret"].iloc[0])
                row.update(frozen_regret=frozen_value, difference_from_frozen=float(fast[0] - frozen_value))
            records.append(row)
            if not all(matches.values()):
                write_json(outdir / "reference-equivalence.json", {"passed": False, "records": records})
                raise RuntimeError("Reference action equivalence failed: " + name + " / " + s["name"])
        print("reference-audit", si, s["name"], "passed", flush=True)
    result = dict(passed=True, records=records, full_endpoint=full_endpoint,
                  note="Different backend versions may change stochastic trajectories. Any historical endpoint difference is disclosed; all expanded comparisons use freshly rerun paired references.")
    write_json(outdir / "reference-equivalence.json", result)
    return result


ROW_FIELDS = ["stage", "scenario_index", "scenario", "rep", "method", "kind", "T", "K", "regret", "runtime_seconds", "total_pulls", "counts", "action_sha256", "means_sha256", "rewards_sha256", "policy_seed", "reward_seed", "protocol_sha256", "source_payload_sha256", "frozen_regret", "difference_from_frozen", "status", "error"]


def run_scenario(args):
    si, protocol_path, outdir, repetitions, horizon, resume = args
    protocol_path = Path(protocol_path); outdir = Path(outdir)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    original = json.loads((FROZEN / "protocols" / "holdout-freeze.json").read_text())
    fingerprints = source_fingerprint()
    payload_hash = canonical_hash(fingerprints)
    protocol_hash = sha(protocol_path)
    outdir.mkdir(parents=True, exist_ok=True)
    scenario = original["scenarios"][si]
    target = outdir / f"runs-{si:02d}.csv"
    paths_target = outdir / f"paths-{si:02d}.npz"
    paths = {}
    done = set()
    import pandas as pd
    frozen = pd.read_csv(FROZEN / "results" / "holdout-all.csv")
    if target.exists():
        if not resume:
            raise RuntimeError(f"Refusing to overwrite {target}; use a fresh output or --resume")
        with target.open(encoding="utf-8", newline="") as previous:
            reader = csv.DictReader(previous)
            if reader.fieldnames != ROW_FIELDS:
                raise RuntimeError("Resume CSV header differs from the current schema")
            prior_rows = list(reader)
        successful_rows = []
        failed_rows = []
        for row in prior_rows:
            if None in row or any(value is None for value in row.values()):
                raise RuntimeError("Truncated resume CSV row; preserve it and repair explicitly")
            if row["protocol_sha256"] != protocol_hash or row["source_payload_sha256"] != payload_hash:
                raise RuntimeError("Resume protocol/source hash mismatch")
            rep = int(row["rep"])
            expected_T = scenario["T"] if horizon is None else min(scenario["T"], horizon)
            method_names = {m.get("name", m["id"]) for m in protocol["methods"]}
            if (int(row["scenario_index"]) != si or row["scenario"] != scenario["name"] or
                    int(row["T"]) != expected_T or rep < 0 or rep >= repetitions or row["method"] not in method_names):
                raise RuntimeError("Resume row lies outside this scenario/horizon/replication/method matrix")
            if row["status"] == "ok":
                key = (rep, row["method"])
                if key in done:
                    raise RuntimeError("Duplicate successful resume row")
                done.add(key)
                successful_rows.append(row)
            elif row["status"] == "error":
                failed_rows.append(row)
            else:
                raise RuntimeError("Unknown resume row status")
        if failed_rows:
            # Preserve every failure as evidence, while the active CSV remains
            # one successful row per intended cell when that cell is retried.
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            write_json(outdir / f"failed-attempts-{si:02d}-{stamp}.json", failed_rows)
            compact = target.with_suffix(".csv.tmp")
            with compact.open("w", newline="", encoding="utf-8") as handle:
                compact_writer = csv.DictWriter(handle, fieldnames=ROW_FIELDS)
                compact_writer.writeheader()
                compact_writer.writerows(successful_rows)
            compact.replace(target)
        if paths_target.exists():
            with np.load(paths_target) as saved:
                paths = {key: saved[key] for key in saved.files}
    started = time.perf_counter()
    methods = protocol["methods"]
    needs_new = any(m.get("kind") != "reference" for m in methods)
    new_module = load_new_module() if needs_new else None
    new_simulator = get_new_simulator() if needs_new else None
    completed = len(done); errors = []
    with target.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELDS)
        if target.stat().st_size == 0:
            writer.writeheader(); handle.flush()
        for rep in range(repetitions):
            s, mu, arr, rew, T, seed = make_case(original, si, rep, horizon)
            means_hash = hashlib.sha256(mu.tobytes()).hexdigest()
            rewards_hash = hashlib.sha256(rew.tobytes()).hexdigest()
            for method in methods:
                name = method.get("name", method["id"])
                if (rep, name) in done:
                    continue
                row = dict(stage=protocol.get("stage", "regret-screen"), scenario_index=si, scenario=s["name"], rep=rep,
                    method=name, kind=method["kind"], T=T, K=len(mu), means_sha256=means_hash, rewards_sha256=rewards_hash,
                    policy_seed=seed, reward_seed=original["reward_seed"] + si * 10000 + rep,
                    protocol_sha256=protocol_hash, source_payload_sha256=payload_hash, frozen_regret="", difference_from_frozen="", status="ok", error="")
                tm = time.perf_counter()
                try:
                    if method["kind"] == "reference":
                        pol = reference_spec(method.get("reference_name", name), original)
                        out = call_reference(rew, mu, arr, T, pol, seed, scenario=s)
                    else:
                        code = new_module.METHOD_CODES[method["kind"]]
                        params = [float(s["T"]) if method.get(f"param{i}", 0.) == "T" else float(method.get(f"param{i}", 0.)) for i in range(3)]
                        if method.get("horizon_parameter") is not None:
                            params[int(method["horizon_parameter"])] = float(s["T"])
                        out = new_simulator(rew, mu, arr, T, code, *params, seed, int(protocol.get("path_stride", 200)))
                    regret, path, counts, actions = out[:4]
                    if int(counts.sum()) != T or len(actions) != T or np.any(counts < 0) or not np.isfinite(regret):
                        raise RuntimeError("Invalid trajectory totals")
                    row.update(regret=float(regret), total_pulls=int(counts.sum()), counts=json.dumps(counts.tolist(), separators=(",", ":")), action_sha256=hashlib.sha256(actions.tobytes()).hexdigest())
                    if rep < int(protocol.get("path_reps", 4)):
                        paths[method["id"] + "-" + str(rep)] = path
                    if method["kind"] == "reference" and T == s["T"]:
                        match = frozen.loc[(frozen.scenario == s["name"]) & (frozen.rep == rep) & (frozen.method == method.get("reference_name", name)), "regret"]
                        if len(match) == 1:
                            fv = float(match.iloc[0]); row.update(frozen_regret=fv, difference_from_frozen=float(regret - fv))
                    completed += 1
                except Exception:
                    row.update(status="error", error=traceback.format_exc())
                    errors.append(dict(rep=rep, method=name, error=row["error"]))
                row["runtime_seconds"] = time.perf_counter() - tm
                writer.writerow(row); handle.flush()
                if row["status"] == "error":
                    write_json(outdir / f"errors-{si:02d}.json", errors)
                    raise RuntimeError(f"Failed {name} at {s['name']} replication {rep}: {row['error']}")
            if rep % 8 == 7 or rep == repetitions - 1:
                np.savez_compressed(paths_target, **paths)
                write_json(outdir / f"checkpoint-{si:02d}.json", dict(scenario=s["name"], completed_rep=rep + 1, repetitions=repetitions,
                    rows=completed, methods=len(methods), elapsed_seconds=time.perf_counter() - started, protocol_sha256=protocol_hash,
                    source_payload_sha256=payload_hash, errors=errors))
                print("screen", si, s["name"], rep + 1, "/", repetitions, round(time.perf_counter() - started, 2), "seconds", flush=True)
    if fingerprints != source_fingerprint():
        raise RuntimeError("Source code changed during scenario run")
    return dict(index=si, scenario=scenario["name"], rows=completed, elapsed_seconds=time.perf_counter() - started)


def run(protocol_path, outdir, repetitions=None, horizon=None, workers=8, scenario_indices=None, resume=False):
    protocol_path = Path(protocol_path).resolve(); outdir = Path(outdir).resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    original_path = FROZEN / "protocols" / "holdout-freeze.json"
    original = json.loads(original_path.read_text())
    # A new screen may add policies, never silently redefine the original test.
    expected = protocol.get("original_protocol_sha256")
    if expected is not None and expected != sha(original_path):
        raise RuntimeError("Frozen source protocol hash mismatch")
    repetitions = int(protocol.get("reps", original["reps"])) if repetitions is None else repetitions
    if repetitions < 1 or repetitions > original["reps"]:
        raise ValueError("Repetitions must be between 1 and the original 96")
    workers = max(1, min(int(workers), 8))
    indices = list(range(len(original["scenarios"]))) if scenario_indices is None else scenario_indices
    if len(set(indices)) != len(indices) or any(i < 0 or i >= len(original["scenarios"]) for i in indices):
        raise ValueError("Scenario indices must be unique valid original indices")
    if horizon is not None and horizon < 1:
        raise ValueError("Debug horizon must be positive")
    names = [m.get("name", m["id"]) for m in protocol["methods"]]
    ids = [m["id"] for m in protocol["methods"]]
    if len(set(names)) != len(names) or len(set(ids)) != len(ids):
        raise ValueError("Method names and IDs must be unique")
    before = source_fingerprint()
    outdir.mkdir(parents=True, exist_ok=True)
    old_info_path = outdir / "run-info.json"
    if resume and old_info_path.exists():
        old_info = json.loads(old_info_path.read_text(encoding="utf-8"))
        if (old_info.get("protocol_sha256") != sha(protocol_path) or
                old_info.get("source_payload_sha256") != canonical_hash(before) or
                old_info.get("horizon_debug") != horizon):
            raise RuntimeError("Resume source/protocol/debug-horizon differs from the existing run")
    write_json(outdir / "environment.json", setting_audit(outdir / "settings-audit.json")["environment"])
    run_info = dict(created_utc=dt.datetime.now(dt.timezone.utc).isoformat(), protocol_sha256=sha(protocol_path), sources=before,
        source_payload_sha256=canonical_hash(before), workers=workers, repetitions=repetitions, horizon_debug=horizon,
        scenarios=indices, expected_rows=len(indices) * repetitions * len(protocol["methods"]), paired_potential_streams=True,
        manuscript_and_frozen_results_modified=False, full_prespecified_run=(repetitions == original["reps"] and horizon is None and len(indices) == 12))
    write_json(outdir / "run-info.json", run_info)
    start = time.perf_counter()
    jobs = [(i, str(protocol_path), str(outdir), repetitions, horizon, resume) for i in indices]
    if workers == 1:
        records = [run_scenario(job) for job in jobs]
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(run_scenario, job) for job in jobs]
            records = [f.result() for f in concurrent.futures.as_completed(futures)]
    if before != source_fingerprint():
        raise RuntimeError("Source code changed during run")
    run_info.update(completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(), elapsed_seconds=time.perf_counter() - start, completed=sorted(records, key=lambda x: x["index"]), passed=True)
    write_json(outdir / "run-info.json", run_info)
    print(json.dumps(dict(passed=True, elapsed_seconds=run_info["elapsed_seconds"], rows=run_info["expected_rows"])), flush=True)
    return run_info


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--protocol", default=str(ROOT / "protocol.json"))
    p.add_argument("--output", default=str(ROOT / "results"))
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--reps", type=int)
    p.add_argument("--horizon", type=int, help="Debug cutoff only; original full reward streams still generated")
    p.add_argument("--scenarios", help="Comma-separated original scenario indices")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--audit-settings", action="store_true")
    p.add_argument("--audit-references", action="store_true")
    p.add_argument("--full-audit", action="store_true")
    a = p.parse_args()
    if a.audit_settings:
        obj = setting_audit(Path(a.output) / "settings-audit.json")
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    elif a.audit_references:
        audit_reference_equivalence(a.output, a.horizon or 800, a.full_audit)
    else:
        indices = None if a.scenarios is None else [int(i) for i in a.scenarios.split(",")]
        run(a.protocol, a.output, a.reps, a.horizon, a.workers, indices, a.resume)


if __name__ == "__main__":
    main()
