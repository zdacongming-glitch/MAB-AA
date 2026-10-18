#!/usr/bin/env python3
"""Frozen Bernoulli comparisons for continuous relative-good-arm maintenance.

Run from any directory: python -X utf8 experiments/run_experiments.py
Numba accelerates physical-round loops; it does not change policy information.
All policies use the same per-arm potential reward array within each replication.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import platform
import sys
import time
from pathlib import Path

import numpy as np
import numba
from numba import njit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = HERE / "reference_cp_ucb_aa.py"
REFERENCE_ORIGIN = "proposal/ucbaa_continuous_maintenance_2026-10-14/cp_ucb_aa.py"

# These settings and all scenarios are fixed before collecting comparisons.
CONFIG = {
    "protocol_version": "1.1",
    "horizon": 20000, "replications": 160, "seed_start": 202610150,
    "epsilon": .30, "eta": .10, "delta": .05,
    "path_stride": 100,
    "scenarios": [
        {"name": "stable_benchmark", "arrivals": [[1, [.65, .50]], [4037, [.05, .15]], [8037, [.20, .10]], [12037, [.12, .08]]]},
        {"name": "successive_improvements", "arrivals": [[1, [.45, .10, .22]], [5037, [.70, .40]], [10037, [.90, .60]], [15037, [.98]]]},
        {"name": "burst", "arrivals": [[1, [.60, .45]], [8037, [.05, .10, .15, .20, .85, .65]]]},
        {"name": "arrivals_stop", "arrivals": [[1, [.50, .15]], [2037, [.65, .35, .20]], [4037, [.85, .58, .10]]]},
    ],
    "methods": [
        # kind: 0 UCB; 1 FIFO quota; 2 confidence-driven quota;
        # 3 prefix confidence-driven; 4 batch UCB with confidence elimination.
        {"name": "CP-FIFO-fine", "kind": 1, "rho": .04, "period": 2, "interval": "checkpoint", "admission_period": 1},
        {"name": "CP-FIFO", "kind": 1, "rho": .12, "period": 2, "interval": "checkpoint", "admission_period": 1},
        {"name": "CP-confidence", "kind": 2, "rho": .12, "period": 2, "interval": "checkpoint", "admission_period": 1},
        {"name": "CP-period8", "kind": 1, "rho": .12, "period": 8, "interval": "checkpoint", "admission_period": 1},
        {"name": "UCB-checkpoint", "kind": 0, "rho": .12, "period": 2, "interval": "checkpoint", "admission_period": 1},
        {"name": "UCB-prefix", "kind": 0, "rho": .12, "period": 2, "interval": "prefix", "admission_period": 1},
        {"name": "Growing-MOSS", "kind": 5, "rho": .12, "period": 2, "interval": "prefix", "admission_period": 1},
        {"name": "ALL-epsilon-adapt", "kind": 3, "rho": .12, "period": 2, "interval": "prefix", "admission_period": 1},
        {"name": "Batch100-UCB", "kind": 4, "rho": .12, "period": 2, "interval": "prefix", "admission_period": 100},
    ],
    "interpretation": {
        "fine_precision": "2*rho < eta; completed checkpoints suffice to resolve all eta-separated arms on coverage event",
        "coarse_precision": "rho=.12 is a reliable but coarser engineering choice; it does not ensure eta=.10 completeness",
        "ALL-epsilon-adapt": "A history-retaining confidence-driven allocation inspired by all-relative-good-arm identification; not a reproduction of FAREAST or ST2",
        "Batch100-UCB": "Reviewer-inspired fixed-100-pull admission and confidence elimination; retained histories and all-arrival reports",
        "Growing-MOSS": "Anytime growing-arm index mean + sqrt(max(log(t/(K_t*n)),0)/n); no inherited offline MOSS minimax claim",
        "admission_clock": "arrivals at t are visible before action; Batch100 admits at t=1,101,201,...",
        "reward_coupling": "PCG64 SeedSequence([seed,scenario_index]); U[i,n] potential reward shared by all methods",
        "error": "any false positive C or false negative D at any observed round",
        "report": "after each physical observation; epsilon-good includes equality",
        "ties": "smallest arrival label; truth comparisons use tolerance 1e-12",
        "no_tuning": "All methods, parameters, scenarios and seeds are specified here before production runs; no winner selection",
    },
}


@njit(cache=True)
def simulate(rewards, means, births, horizon, eps, eta, delta,
             kind, rho, period, prefix, admission_period, path_times, record_trace=False):
    kmax = len(means)
    counts = np.zeros(kmax, np.int64)
    sums = np.zeros(kmax)
    lower = np.zeros(kmax)
    upper = np.ones(kmax)
    quota = np.empty(kmax, np.int64)
    for i in range(kmax):
        quota[i] = math.ceil(2/rho**2 * math.log(4*(i+1)*(i+2)/delta))
    # status: 0 unresolved, 1 positive, -1 negative. Recomputed each round.
    status = np.zeros(kmax, np.int64)
    # Elimination only concerns reward selection in the reviewer-inspired baseline.
    reward_active = np.ones(kmax, np.bool_)
    admitted = np.zeros(kmax, np.bool_)
    paths = np.zeros((len(path_times), 4))
    trace = np.zeros((horizon if record_trace else 0, 2+2*kmax),np.int64)
    next_path = 0
    k = 0
    regret = 0.
    area_eta = 0
    area_all = 0
    error_rounds = 0
    service_pulls = 0
    service_regret = 0.
    admission_delay_regret = 0.
    elimination_deficit_regret = 0.
    within_active_regret = 0.
    certified = 0
    last_birth = births[-1]
    first_eta_clear = -1
    last_u_eta = 0
    last_u_all = 0
    for t in range(1, horizon+1):
        while k < kmax and births[k] == t:
            k += 1
        if (t-1) % admission_period == 0:
            for i in range(k):
                admitted[i] = True
        best = means[0]
        for i in range(1,k):
            best = max(best, means[i])
        # Pre-observation reports determine confidence-driven allocation.
        max_l = 0.
        max_u = 0.
        for i in range(k):
            max_l = max(max_l, lower[i])
            max_u = max(max_u, upper[i])
        selected = -1
        is_service = False
        if t % period == 0 and kind == 1:
            for i in range(k):
                if counts[i] < quota[i]:
                    selected = i
                    is_service = True
                    break
        if t % period == 0 and (kind == 2 or kind == 3):
            # Include unresolved arms and the optimistic reference. The largest
            # width (then smallest count, label) gives a transparent non-oracle rule.
            optimistic = 0
            for i in range(1,k):
                if upper[i] > upper[optimistic]:
                    optimistic = i
            needs_report = False
            for i in range(k):
                if not (upper[i] < max_l-eps or lower[i] >= max_u-eps):
                    needs_report = True
            widest = -1.
            for i in range(k):
                unresolved = not (upper[i] < max_l-eps or lower[i] >= max_u-eps)
                eligible = needs_report and (unresolved or i == optimistic)
                if kind == 2:
                    eligible = eligible and counts[i] < quota[i]
                width = upper[i]-lower[i]
                if eligible and (width > widest+1e-15 or
                    (abs(width-widest) <= 1e-15 and
                     (selected < 0 or counts[i] < counts[selected]))):
                    selected = i
                    widest = width
            is_service = selected >= 0
        if selected < 0:
            best_index = -math.inf
            for i in range(k):
                if admitted[i] and (kind != 4 or reward_active[i]):
                    index = math.inf if counts[i] == 0 else sums[i]/counts[i] + math.sqrt(3*math.log(2*t)/counts[i])
                    if kind == 5 and counts[i] > 0:
                        index = sums[i]/counts[i] + math.sqrt(max(0.,math.log(t/(k*counts[i])))/counts[i])
                    if selected < 0 or index > best_index:
                        selected = i
                        best_index = index
        # At least an initial arm is admitted; elimination preserves an arm on
        # nonempty interval paths. Empty intersections are handled below.
        if selected < 0:
            selected = 0
        best_admitted = -math.inf
        best_active = -math.inf
        for i in range(k):
            if admitted[i]:
                best_admitted = max(best_admitted, means[i])
                if kind != 4 or reward_active[i]:
                    best_active = max(best_active, means[i])
        admission_delay_regret += best-best_admitted
        elimination_deficit_regret += best_admitted-best_active
        within_active_regret += best_active-means[selected]
        reward = rewards[selected, counts[selected]]
        counts[selected] += 1
        sums[selected] += reward
        if prefix:
            n = counts[selected]
            rad = math.sqrt(math.log(8*(selected+1)**2*n*n/delta)/(2*n))
            lo = max(0., sums[selected]/n-rad)
            hi = min(1., sums[selected]/n+rad)
            lower[selected] = max(lower[selected], lo)
            upper[selected] = min(upper[selected], hi)
        elif counts[selected] == quota[selected]:
            lower[selected] = max(0., sums[selected]/counts[selected]-rho/2)
            upper[selected] = min(1., sums[selected]/counts[selected]+rho/2)
            certified += 1
        gap = best-means[selected]
        regret += gap
        if is_service:
            service_pulls += 1
            service_regret += gap
        max_l = 0.
        for i in range(k):
            max_l = max(max_l, lower[i])
        # Exclusion-priority report for prefix intersections, including the
        # (rare) empty-interval path, as specified in the theoretical packet.
        max_u_remaining = -math.inf
        for i in range(k):
            if upper[i] < max_l-eps:
                status[i] = -1
            else:
                status[i] = 0
                max_u_remaining = max(max_u_remaining, upper[i])
        max_u = 0.
        for i in range(k):
            max_u = max(max_u, upper[i])
        u_eta = 0
        u_all = 0
        wrong = False
        for i in range(k):
            positive_threshold = max_u_remaining if prefix else max_u
            if status[i] != -1 and lower[i] >= positive_threshold-eps:
                status[i] = 1
            good = best-means[i] <= eps+1e-12
            if (status[i] == 1 and not good) or (status[i] == -1 and good):
                wrong = True
            if status[i] == 0:
                u_all += 1
                if abs(best-means[i]-eps) > eta+1e-12:
                    u_eta += 1
        if kind == 4:
            max_l_admitted = 0.
            for i in range(k):
                if admitted[i] and reward_active[i]:
                    max_l_admitted = max(max_l_admitted, lower[i])
            for i in range(k):
                if admitted[i] and reward_active[i] and upper[i] < max_l_admitted:
                    reward_active[i] = False
        if wrong:
            error_rounds += 1
        area_eta += u_eta
        area_all += u_all
        last_u_eta = u_eta
        last_u_all = u_all
        if t >= last_birth and u_eta == 0 and first_eta_clear < 0:
            first_eta_clear = t
        if next_path < len(path_times) and t == path_times[next_path]:
            paths[next_path,0] = regret
            paths[next_path,1] = u_eta
            paths[next_path,2] = area_eta
            paths[next_path,3] = u_all
            next_path += 1
        if record_trace:
            trace[t-1,0] = selected+1
            trace[t-1,1] = int(is_service)
            for i in range(k):
                trace[t-1,2+i] = counts[i]
                trace[t-1,2+kmax+i] = status[i]
    metrics = np.array([regret, area_eta, area_all, error_rounds, service_pulls,
                        service_regret, last_u_eta, last_u_all, first_eta_clear,
                        certified, np.sum(counts >= quota),admission_delay_regret,
                        elimination_deficit_regret,within_active_regret], np.float64)
    return metrics, paths, counts, lower, upper, trace


def scenario_arrays(scenario):
    means, births = [], []
    for t, mus in scenario["arrivals"]:
        means.extend(mus)
        births.extend([t]*len(mus))
    return np.asarray(means), np.asarray(births, dtype=np.int64)


def parity_check():
    """Check compiled FIFO against the original public choose/observe class."""
    spec = importlib.util.spec_from_file_location("original_cp_ucb_aa", SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    means, births = scenario_arrays(CONFIG["scenarios"][1])
    horizon = 20000
    rng = np.random.default_rng(812463)
    rewards = (rng.random((len(means), horizon)) < means[:,None]).astype(np.uint8)
    out, _, counts, lower, upper, trace = simulate(rewards, means, births, horizon,
        .30,.10,.05,1,.12,2,False,1,np.array([horizon],dtype=np.int64),True)
    alg = module.CheckpointUCBAA(.30,.05,.12)
    next_arm = 0
    regret = 0.
    area = 0
    for t in range(1,horizon+1):
        labels = []
        while next_arm < len(means) and births[next_arm] == t:
            next_arm += 1
            labels.append(next_arm)
        i, service = alg.choose(labels)
        assert i == trace[t-1,0], ("action",t,i,int(trace[t-1,0]))
        assert service == bool(trace[t-1,1]), ("service flag",t)
        alg.observe(float(rewards[i-1, alg.arms[i].count]))
        c,d,v = alg.report()
        for j in range(next_arm):
            assert alg.arms[j+1].count == trace[t-1,2+j], ("count",t,j+1)
            status = 1 if j+1 in c else -1 if j+1 in d else 0
            assert status == trace[t-1,2+len(means)+j], ("report",t,j+1)
        best = max(means[:next_arm])
        regret += best-means[i-1]
        area += sum(abs(best-means[j-1]-.30)>.10+1e-12 for j in v)
    assert np.array_equal(counts, [alg.arms[i+1].count for i in range(len(means))])
    assert np.allclose(lower, [alg.arms[i+1].lower for i in range(len(means))], atol=1e-14)
    assert np.allclose(upper, [alg.arms[i+1].upper for i in range(len(means))], atol=1e-14)
    assert abs(out[0]-regret)<1e-8 and out[1] == area
    return {"kind": "compiled implementation parity with original public interface",
            "seed": 812463, "horizon": horizon, "passed": True,
            "per_round_comparisons": ["action", "service flag", "all available arm counts", "C/D/V report"],
            "counts": counts.tolist(), "pseudo_regret": regret, "eta_area": int(area)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true", help="2-rep smoke execution; never writes production output")
    args = parser.parse_args()
    config = json.loads(json.dumps(CONFIG))
    if args.pilot:
        config["replications"] = 2
    dest = HERE / ("pilot" if args.pilot else "results")
    dest.mkdir(parents=True, exist_ok=True)
    (dest/"config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    parity = parity_check()
    (dest/"source_parity.json").write_text(json.dumps(parity, indent=2), encoding="utf-8")
    horizon = config["horizon"]
    path_times = np.unique(np.r_[1, np.arange(config["path_stride"],horizon+1,config["path_stride"]),
        [t for sc in config["scenarios"] for t,_ in sc["arrivals"]]]).astype(np.int64)
    paths = np.zeros((len(config["scenarios"]), config["replications"], len(config["methods"]), len(path_times),4))
    fieldnames = ["scenario", "seed", "method", "regret", "area_eta", "area_all", "error_rounds", "error_ever",
                  "service_pulls", "service_regret", "final_u_eta", "final_u_all", "first_eta_clear",
                  "checkpoint_crossings", "quota_completed", "counts", "coverage_at_end"]
    fieldnames += ["admission_delay_regret", "elimination_deficit_regret", "within_active_regret"]
    started = time.perf_counter()
    with (dest/"runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for s, scenario in enumerate(config["scenarios"]):
            means,births = scenario_arrays(scenario)
            for rep in range(config["replications"]):
                seed = config["seed_start"]+rep
                rng = np.random.default_rng(np.random.SeedSequence([seed,s]))
                rewards = (rng.random((len(means),horizon)) < means[:,None]).astype(np.uint8)
                for m,method in enumerate(config["methods"]):
                    out, p, counts, lower, upper, _ = simulate(rewards,means,births,horizon,
                        config["epsilon"],config["eta"],config["delta"],method["kind"],method["rho"],
                        method["period"],method["interval"]=="prefix",method["admission_period"],path_times)
                    paths[s,rep,m] = p
                    writer.writerow(dict(scenario=scenario["name"],seed=seed,method=method["name"],
                        regret=out[0],area_eta=int(out[1]),area_all=int(out[2]),error_rounds=int(out[3]),error_ever=int(out[3]>0),
                        service_pulls=int(out[4]),service_regret=out[5],final_u_eta=int(out[6]),final_u_all=int(out[7]),
                        first_eta_clear=int(out[8]),checkpoint_crossings=int(out[9]),quota_completed=int(out[10]),
                        counts=json.dumps(counts.tolist()),coverage_at_end=int(np.all((lower<=means)&(means<=upper))),
                        admission_delay_regret=out[11],elimination_deficit_regret=out[12],within_active_regret=out[13]))
            stream.flush()
            print(f"finished {scenario['name']}: {config['replications']} paired replications", flush=True)
    np.savez_compressed(dest/"paths.npz", paths=paths, times=path_times,
        scenarios=np.array([s["name"] for s in config["scenarios"]]),
        methods=np.array([m["name"] for m in config["methods"]]),
        metrics=np.array(["regret","u_eta","area_eta","u_all"]))
    manifest = {"source_sha256":sha(SOURCE),"runner_sha256":sha(Path(__file__)),
        "reference_origin_repository_relative":REFERENCE_ORIGIN,
        "config_sha256":sha(dest/"config.json"),"runs_sha256":sha(dest/"runs.csv"),"paths_sha256":sha(dest/"paths.npz"),
        "elapsed_seconds":time.perf_counter()-started,"python":sys.version,"platform":platform.platform(),
        "numpy":np.__version__,"numba":numba.__version__,"replications_per_scenario":config["replications"],
        "rounds_per_run":horizon,"total_runs":len(config["scenarios"])*config["replications"]*len(config["methods"]),
        "policy_information":"No policy receives true means, future births, final arm count, horizon or evaluation truth; array size is storage only. Means/reward table are accessed only by the environment and evaluator.",
        "notes":"Monte Carlo results concern the four frozen scenarios; not a proof of uniform reliability or asymptotic optimality."}
    (dest/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest,indent=2))


if __name__ == "__main__":
    main()
