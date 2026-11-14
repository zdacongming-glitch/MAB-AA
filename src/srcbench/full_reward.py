"""Original-size five-method paired reward experiment, with atomic resume."""
from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import gzip
import hashlib
import json
import math
import multiprocessing
from pathlib import Path
import time

import numpy as np

from . import numba_cache_info
from .design import load_layouts, LAWS_16
from .environment import PotentialRewards, stable_seed
from .methods import get_method
from .policy import Policy
from .simplified import FullPolicy, FULL_METHOD
from .runner import ROOT, atomic_json, atomic_bytes, compressed_json, sha256, json_bytes, input_files, versions, run_lock


def specification():
    protocol = json.loads((ROOT/"configs/full_reward.json").read_text(encoding="utf-8"))
    methods = {m: FULL_METHOD.copy() if m == "FULL-R" else get_method(m) for m in protocol["methods"]}
    layouts = [x for x in load_layouts() if x["group"] in protocol["groups"]]
    return protocol, methods, layouts


def config_for(pilot=False):
    protocol, methods, layouts = specification()
    if pilot:
        layouts = [x for x in layouts if x["id"] in protocol["pilot_layouts"]]
        if len(layouts) != len(protocol["pilot_layouts"]):
            raise ValueError("pilot layout does not exist")
    reps = 1 if pilot else protocol["replications"]
    seed = protocol["pilot_seed_base"] if pilot else protocol["seed_base"]
    tasks = []
    for layout in layouts:
        for law in LAWS_16:
            for rep in range(reps):
                key = [layout["id"], law, rep, seed]
                task_id = hashlib.sha256(json_bytes(key)).hexdigest()[:24]
                tasks.append(dict(task_id=task_id, layout_id=layout["id"], law=law, rep=rep, seed_base=seed))
    sources = input_files()
    sources["run_full_reward.py"] = sha256(ROOT/"run_full_reward.py")
    config = dict(profile="full-reward", pilot=pilot, protocol=protocol, methods=methods,
                  layouts=layouts, tasks=tasks, replications=reps, source_files=sources,
                  expected_worlds=len(tasks), expected_runs=len(tasks)*len(methods),
                  cache=numba_cache_info(), environment=versions(), raw_schema="reward-only-v1")
    # Cache root is a physical deployment detail; namespace identifies kernels.
    config["cache"] = {k: v for k, v in config["cache"].items() if k not in ("cache_root", "effective_cache_dir")}
    return config


def simulate_world(task, layout, methods, fractions, track_reports=False):
    """Only this evaluator owns future arrivals, means and potential streams."""
    world = PotentialRewards(layout, task["law"], task["rep"], task["seed_base"])
    arms = world.layout["arms"]
    births = np.array([a["arrival"] for a in arms], dtype=np.int64)
    means = np.array([a["mean"] for a in arms])
    T, K = layout["T"], len(arms)
    checkpoints = {max(1, int(round(f*T))): f for f in fractions if f > 0}
    result = dict(task_id=task["task_id"], runs=[], trajectories=[], counts=[],
                  numba_cache=numba_cache_info(), execution_errors=[])
    meta = dict(layout_id=layout["id"], group=layout["group"], law=task["law"], rep=task["rep"],
                seed_base=task["seed_base"], T=T, K=K)
    for method_id, spec in methods.items():
        seed = stable_seed(task["seed_base"], layout["id"], task["law"], task["rep"], "policy", method_id)
        cls = FullPolicy if spec["family"] == "full" else Policy
        policy = cls(spec, epsilon=layout["epsilon"], eta=layout["eta"], delta=layout["delta"],
                     seed=seed, track_reports=track_reports)
        started = time.perf_counter()
        regret, active, best = 0., 0, 0.
        action_hash = 14695981039346656037
        for t in range(1, T+1):
            previous = active
            while active < K and births[active] <= t:
                best = max(best, means[active])
                active += 1
            chosen = policy.choose(range(previous, active))
            if not 0 <= chosen < active:
                raise RuntimeError("unavailable arm chosen")
            reward = world.draw(int(chosen), int(policy.n[chosen]))
            policy.observe(reward)
            regret += best-means[chosen]
            action_hash = ((action_hash ^ (int(chosen)+1))*1099511628211) & ((1 << 64)-1)
            if t in checkpoints:
                result["trajectories"].append(dict(**meta, method=method_id, t=t,
                    fraction=checkpoints[t], regret=regret))
        if not math.isfinite(regret) or not 0 <= regret <= T or int(np.sum(policy.n)) != T:
            raise ValueError("invalid reward endpoint or sample accounting")
        result["runs"].append(dict(**meta, method=method_id, regret=regret, action_hash=str(action_hash),
            never_sampled=int(np.count_nonzero(policy.n == 0)),
            guard_changed=int(getattr(policy, "guard_changed", 0)),
            guard_exclusions=int(getattr(policy, "guard_exclusions", 0)),
            runtime_seconds=time.perf_counter()-started, reports_evaluated=track_reports))
        for i in range(K):
            result["counts"].append(dict(**meta, method=method_id, arm=i, original_arm=arms[i]["original_id"],
                birth=int(births[i]), mean=float(means[i]), n=int(policy.n[i])))
    result["potential_draws"] = sum(map(len, world.cache))
    return result


def _validate(value, task, layout, config):
    if value["task_id"] != task["task_id"] or value.get("execution_errors"):
        raise ValueError("invalid task shard")
    if {r["method"] for r in value["runs"]} != set(config["methods"]) or len(value["runs"]) != len(config["methods"]):
        raise ValueError("unpaired or duplicated method results")
    for row in value["runs"]:
        for field in ("layout_id", "law", "rep", "seed_base"):
            if row[field] != task[field]:
                raise ValueError("incorrect world identity")
        if row["reports_evaluated"] or row["T"] != layout["T"] or row["K"] != len(layout["arms"]):
            raise ValueError("incorrect evaluation scope")
        if not math.isfinite(row["regret"]) or not 0 <= row["regret"] <= row["T"]:
            raise ValueError("invalid regret")
        counts = [r for r in value["counts"] if r["method"] == row["method"]]
        if (len(counts) != row["K"] or sum(r["n"] for r in counts) != row["T"]
                or {r["arm"] for r in counts} != set(range(row["K"]))
                or any(not isinstance(r["n"], int) or r["n"] < 0 for r in counts)):
            raise ValueError("sample accounting mismatch")
        trace = [r for r in value["trajectories"] if r["method"] == row["method"]]
        checkpoints = {max(1, int(round(f*layout["T"]))): f
                       for f in config["protocol"]["trajectory_fractions"] if f > 0}
        if (not trace or len(trace) != len(checkpoints)
                or {r["t"] for r in trace} != set(checkpoints)
                or any(r["fraction"] != checkpoints[r["t"]] for r in trace)
                or trace[-1]["t"] != row["T"] or trace[-1]["regret"] != row["regret"]):
            raise ValueError("incomplete regret trajectory")
        for r in counts+trace:
            if any(r[field] != row[field] for field in ("layout_id", "group", "law", "rep", "seed_base", "T", "K")):
                raise ValueError("diagnostic identity mismatch")
    if value["numba_cache"]["source_fingerprint"] != config["cache"]["source_fingerprint"]:
        raise ValueError("worker loaded a different compiled source namespace")


def _read(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def _aggregate(output, config):
    import io
    files = {}
    for table in ("runs", "trajectories", "counts"):
        buffer = io.StringIO(newline="")
        writer = None
        total = 0
        for task in config["tasks"]:
            value = _read(output/"shards"/(task["task_id"]+".json.gz"))
            if writer is None:
                writer = csv.DictWriter(buffer, fieldnames=list(value[table][0]))
                writer.writeheader()
            writer.writerows(value[table])
            total += len(value[table])
        path = output/(table+".csv.gz")
        atomic_bytes(path, gzip.compress(buffer.getvalue().encode("utf-8"), mtime=0))
        files[path.name] = dict(sha256=sha256(path), rows=total)
    return files


def run(output, workers=8, resume=False, pilot=False, dry_run=False):
    config = config_for(pilot)
    preview = dict(layouts=len(config["layouts"]), cells=len(config["layouts"])*len(LAWS_16),
        worlds=config["expected_worlds"], trajectories=config["expected_runs"],
        replications=config["replications"], pilot=pilot,
        feedbacks=sum(x["T"] for x in config["layouts"])*len(LAWS_16)*config["replications"]*len(config["methods"]))
    print(json.dumps(preview, ensure_ascii=False), flush=True)
    if dry_run:
        return preview
    output = Path(output).resolve()
    if output == ROOT or output in ROOT.parents or (ROOT/"src") in output.parents or (ROOT/"configs") in output.parents:
        raise ValueError("output must be a dedicated results directory")
    if workers < 1:
        raise ValueError("workers must be positive")
    output.mkdir(parents=True, exist_ok=True)
    with run_lock(output/".runner.lock"):
        fingerprint = hashlib.sha256(json_bytes(config)).hexdigest()
        manifest_path = output/"manifest.json"
        if resume:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest["fingerprint"] != fingerprint or sha256(output/"config.json") != manifest["config_sha256"]:
                raise ValueError("cannot resume changed source, settings, methods or seeds")
        else:
            if any(x.name != ".runner.lock" for x in output.iterdir()):
                raise ValueError("output is occupied; use --resume")
            atomic_json(output/"config.json", config)
            for name, checksum in config["source_files"].items():
                atomic_bytes(output/"source_snapshot"/name, (ROOT/name).read_bytes())
            manifest = dict(fingerprint=fingerprint, config_sha256=sha256(output/"config.json"),
                started_utc=dt.datetime.now(dt.timezone.utc).isoformat(), environment=versions(), shards={}, files={},
                elapsed_seconds=0., resume_count=0)
        manifest.update(status="RUNNING", workers=workers, errors=[])
        manifest["resume_count"] += int(resume)
        atomic_json(manifest_path, manifest)
        (output/"shards").mkdir(exist_ok=True)
        layouts = {x["id"]: x for x in config["layouts"]}
        todo = []
        for task in config["tasks"]:
            path = output/"shards"/(task["task_id"]+".json.gz")
            if path.exists():
                if task["task_id"] in manifest["shards"] and sha256(path) != manifest["shards"][task["task_id"]]:
                    raise ValueError("corrupt shard")
                _validate(_read(path), task, layouts[task["layout_id"]], config)
                manifest["shards"][task["task_id"]] = sha256(path)
            else:
                if task["task_id"] in manifest["shards"]:
                    raise ValueError("missing recorded shard")
                todo.append(task)
        previous_elapsed = manifest["elapsed_seconds"]
        start = time.perf_counter()
        def publish(task, value):
            _validate(value, task, layouts[task["layout_id"]], config)
            path = output/"shards"/(task["task_id"]+".json.gz")
            compressed_json(path, value)
            manifest["shards"][task["task_id"]] = sha256(path)
            manifest["elapsed_seconds"] = previous_elapsed + time.perf_counter()-start
            manifest["completed_worlds"] = len(manifest["shards"])
            atomic_json(manifest_path, manifest)
            if len(manifest["shards"]) % 20 == 0 or pilot:
                print(f'{len(manifest["shards"])}/{len(config["tasks"])} elapsed={manifest["elapsed_seconds"]:.1f}s', flush=True)
        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as pool:
                iterator = iter(todo)
                futures = {}
                def submit_next():
                    task = next(iterator, None)
                    if task is not None:
                        f = pool.submit(simulate_world, task, layouts[task["layout_id"]], config["methods"],
                                        config["protocol"]["trajectory_fractions"])
                        futures[f] = task
                for _ in range(min(len(todo), 2*workers)):
                    submit_next()
                while futures:
                    done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
                    for future in done:
                        task = futures.pop(future)
                        try:
                            publish(task, future.result())
                        except Exception as exc:
                            manifest["errors"].append(dict(task_id=task["task_id"], error=repr(exc)))
                            atomic_json(manifest_path, manifest)
                            raise
                        submit_next()
            manifest["files"] = _aggregate(output, config)
            manifest.update(status="PASS", completed_utc=dt.datetime.now(dt.timezone.utc).isoformat())
            atomic_json(manifest_path, manifest)
            verify(output, check_current=True)
            return manifest
        except BaseException:
            manifest["status"] = "FAILED" if manifest["errors"] else "INTERRUPTED"
            atomic_json(manifest_path, manifest)
            raise


def verify(output, check_current=False):
    output = Path(output)
    config = json.loads((output/"config.json").read_text(encoding="utf-8"))
    manifest = json.loads((output/"manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "PASS" or sha256(output/"config.json") != manifest["config_sha256"]:
        raise ValueError("incomplete run or changed config")
    if hashlib.sha256(json_bytes(config)).hexdigest() != manifest["fingerprint"]:
        raise ValueError("config fingerprint mismatch")
    for name, checksum in config["source_files"].items():
        if sha256(output/"source_snapshot"/name) != checksum:
            raise ValueError("source snapshot mismatch: "+name)
        if check_current and sha256(ROOT/name) != checksum:
            raise ValueError("current source mismatch: "+name)
    if check_current and config["environment"] != versions():
        raise ValueError("current numerical environment differs from the frozen run")
    layouts = {x["id"]: x for x in config["layouts"]}
    if len(manifest["shards"]) != len(config["tasks"]):
        raise ValueError("missing worlds")
    for task in config["tasks"]:
        path = output/"shards"/(task["task_id"]+".json.gz")
        if sha256(path) != manifest["shards"][task["task_id"]]:
            raise ValueError("shard digest mismatch")
        _validate(_read(path), task, layouts[task["layout_id"]], config)
    for name, meta in manifest["files"].items():
        if sha256(output/name) != meta["sha256"]:
            raise ValueError("aggregate digest mismatch")
    if manifest["files"]["runs.csv.gz"]["rows"] != config["expected_runs"]:
        raise ValueError("wrong endpoint count")
    return dict(status="PASS", worlds=len(config["tasks"]), runs=config["expected_runs"])
