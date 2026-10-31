"""Cross-platform experiment runner with immutable inputs and atomic shards."""
from __future__ import annotations

import concurrent.futures
import contextlib
import csv
import datetime as dt
import gzip
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import time
import traceback

from .simulation import COUNT_FIELDS, RUN_FIELDS, TRACE_FIELDS, simulate_task, validate_run

ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", suffix=".part", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def atomic_json(path: Path, value) -> None:
    atomic_bytes(path, json_bytes(value))


def compressed_json(path: Path, value) -> None:
    atomic_bytes(path, gzip.compress(json_bytes(value), mtime=0))


@contextlib.contextmanager
def run_lock(path: Path):
    """OS releases the lock after a crash; workers never publish any files."""
    stream = path.open("a+b")
    try:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError("This output directory already has an active runner") from exc
        yield
    finally:
        stream.close()


def input_files(root: Path = ROOT) -> dict[str, str]:
    files = [root / "run_main.py", root / "requirements.txt"]
    files += sorted((root / "src" / "srcbench").glob("*.py"))
    files += sorted((root / "configs").glob("*.json"))
    return {p.relative_to(root).as_posix(): sha256(p) for p in files}


def versions() -> dict:
    found = {"python": sys.version.split()[0], "platform": platform.platform()}
    for name in ["numpy", "numba", "scipy", "pandas", "matplotlib"]:
        found[name] = importlib.metadata.version(name)
    return found


def _worker(task, methods):
    # A cell/rep has its own potential streams and each method its own seed.
    # All filesystem publication is performed by the parent holding run_lock.
    return simulate_task(task, methods)


def choose_workers(value: str | int, profile: str) -> int:
    if value == "auto":
        import psutil
        # Dense empirical supports, compiler memory and other desktop activity
        # make RAM a more useful bound than the number of logical CPUs alone.
        available = psutil.virtual_memory().available / 1024 ** 3
        return max(1, min(2 if profile.startswith("smoke-") else 8,
                          (os.cpu_count() or 2) // 2, int(available / 1.5)))
    workers = int(value)
    if not 1 <= workers <= 64:
        raise ValueError("workers must be auto or an integer from 1 to 64")
    return workers


def task_records(tasks: list[dict]) -> list[dict]:
    return [{k: task[k] for k in ["task_id", "cell_id", "law", "rep", "seed_base",
                                  "cohort", "methods", "suites", "method_suites"]}
            | {"layout_id": task["layout"]["id"], "diagnostics": task.get("diagnostics", {})} for task in tasks]


def preview(tasks: list[dict], profile: str) -> dict:
    groups = {}
    for task in tasks:
        key = task["layout"]["group"] + "/" + task["cohort"]
        item = groups.setdefault(key, {"shards": 0, "trajectories": 0, "physical_rounds": 0})
        item["shards"] += 1
        item["trajectories"] += len(task["methods"])
        item["physical_rounds"] += len(task["methods"]) * task["layout"]["T"]
    return {"profile": profile, "kind": "derived smoke" if profile.startswith("smoke-") else "formal",
            "layouts": len({t["layout"]["id"] for t in tasks}),
            "cells": len({(t["layout"]["id"], t["law"]) for t in tasks}),
            "shards": len(tasks), "unique_trajectories": sum(len(t["methods"]) for t in tasks),
            "groups": groups, "complete_formal_run_performed": False}


def _validate_shard(shard: dict, task: dict) -> None:
    if shard["task_id"] != task["task_id"]:
        raise ValueError("Shard identity mismatch")
    expected = set(task["methods"])
    seen = set()
    for row in shard["runs"]:
        validate_run(row)
        if row["method"] not in expected or row["method"] in seen:
            raise ValueError("Duplicate or unexpected method in shard")
        if (row["layout_id"], row["law"], row["rep"], row["cohort"]) != (
                task["layout"]["id"], task["law"], task["rep"], task["cohort"]):
            raise ValueError("Shard environment mismatch")
        seen.add(row["method"])
    if seen != expected:
        raise ValueError("Missing shard methods")
    for table, fields in [("trajectories", TRACE_FIELDS), ("counts", COUNT_FIELDS)]:
        diagnostic = task.get("diagnostics", {})
        expect = (task["cohort"] == "smoke" or task["rep"] < diagnostic.get("trajectory_replications", 4)) if table == "trajectories" else (
            task["cohort"] == "smoke" or bool(set(task["methods"]) & set(diagnostic.get("per_arm_methods", ["SRC-R", "SRC-KL-R"]))))
        if expect and not shard[table]:
            raise ValueError("Missing prespecified trajectory or sample-count diagnostics")
        if not expect and shard[table]:
            raise ValueError("Diagnostics differ from the prespecified subset")
        if any(set(fields) - set(row) for row in shard[table]):
            raise ValueError("Missing diagnostic columns")


def _read_shard(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def _write_csv_tables(output: Path, tasks: list[dict]) -> dict:
    """Write in deterministic task order even when execution order differs."""
    records = {}
    specs = [("runs", RUN_FIELDS), ("trajectories", TRACE_FIELDS), ("counts", COUNT_FIELDS)]
    with contextlib.ExitStack() as stack:
        writers = {}
        staged = {}
        row_counts = {key: 0 for key, _ in specs}
        for key, fields in specs:
            target = output / (key + ".csv.gz")
            fd, temp = tempfile.mkstemp(prefix=key, suffix=".part", dir=output)
            binary = stack.enter_context(os.fdopen(fd, "wb"))
            compressed = stack.enter_context(gzip.GzipFile(filename="", mode="wb", fileobj=binary, mtime=0))
            text = stack.enter_context(io.TextIOWrapper(compressed, encoding="utf-8", newline=""))
            writer = csv.DictWriter(text, fieldnames=fields, extrasaction="raise")
            writer.writeheader()
            writers[key] = writer
            staged[key] = (Path(temp), target)
        for task in tasks:
            shard = _read_shard(output / "shards" / (task["task_id"] + ".json.gz"))
            _validate_shard(shard, task)
            for key, _ in specs:
                writers[key].writerows(shard[key])
                row_counts[key] += len(shard[key])
    for key, (temp, target) in staged.items():
        os.replace(temp, target)
        records[target.name] = {"sha256": sha256(target), "bytes": target.stat().st_size,
                                "rows": row_counts[key]}
    return records


def run(profile: str, output: Path, workers: str | int = "auto", resume: bool = False,
        dry_run: bool = False, render: bool = True) -> dict:
    from .design import build_tasks
    from .methods import METHODS

    tasks = build_tasks(profile)
    plan = preview(tasks, profile)
    print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
    if dry_run:
        return plan
    output = Path(output).resolve()
    if output == ROOT or output in ROOT.parents:
        raise ValueError("Output must be a dedicated run directory")
    if (ROOT / "src") in output.parents or (ROOT / "configs") in output.parents:
        raise ValueError("Output cannot be inside source or configuration directories")
    output.mkdir(parents=True, exist_ok=True)
    with run_lock(output / ".runner.lock"):
        return _run_locked(profile, output, tasks, METHODS,
                           choose_workers(workers, profile), resume, render)


def _run_locked(profile, output, tasks, methods, workers, resume, render):
    protocol = json.loads((ROOT / "configs" / "protocol.json").read_text(encoding="utf-8"))
    layouts = {t["layout"]["id"]: t["layout"] for t in tasks}
    method_ids = sorted({m for t in tasks for m in t["methods"]})
    config = {"profile": profile, "protocol": protocol,
              "methods": {m: methods[m] for m in method_ids}, "layouts": list(layouts.values()),
              "expected_runs": sum(len(t["methods"]) for t in tasks),
              "tasks": task_records(tasks), "source_files": input_files()}
    fingerprint = hashlib.sha256(json_bytes(config)).hexdigest()
    manifest_path = output / "manifest.json"
    if resume:
        if not manifest_path.is_file():
            raise ValueError("Cannot resume without an existing manifest")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["fingerprint"] != fingerprint:
            raise ValueError("Cannot resume changed source, configuration, methods or seeds")
        if sha256(output / "config.json") != manifest["config_sha256"]:
            raise ValueError("Stored configuration snapshot changed")
        manifest["resume_count"] = manifest.get("resume_count", 0) + 1
    else:
        if any(p.name != ".runner.lock" for p in output.iterdir()):
            raise ValueError("Output already contains files; use --resume or choose a new directory")
        atomic_json(output / "config.json", config)
        manifest = {"schema_version": 1, "profile": profile, "fingerprint": fingerprint,
            "config_sha256": sha256(output / "config.json"), "environment": versions(),
            "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "scientific_scope": "derived smoke experiment" if profile.startswith("smoke-") else "formal",
            "expected_shards": len(tasks), "expected_runs": config["expected_runs"],
            "shards": {}, "files": {}, "resume_count": 0}
    manifest.update(status="RUNNING", workers=workers, failures=[])
    atomic_json(manifest_path, manifest)
    shards = output / "shards"
    shards.mkdir(exist_ok=True)
    todo = []
    for task in tasks:
        path = shards / (task["task_id"] + ".json.gz")
        recorded = manifest["shards"].get(task["task_id"])
        if path.exists() and recorded:
            if sha256(path) != recorded["sha256"]:
                raise ValueError("Corrupt recorded shard: " + path.name)
            _validate_shard(_read_shard(path), task)
        elif path.exists():
            # A parent crash can occur between atomic shard publication and the
            # manifest update. Validate that orphan before adopting it.
            _validate_shard(_read_shard(path), task)
            manifest["shards"][task["task_id"]] = {"sha256": sha256(path),
                "rows": len(task["methods"]), "bytes": path.stat().st_size}
        else:
            if recorded:
                raise ValueError("Manifest refers to missing shard: " + path.name)
            todo.append(task)
    start = time.monotonic()

    def publish(task, value):
        _validate_shard(value, task)
        path = shards / (task["task_id"] + ".json.gz")
        compressed_json(path, value)
        manifest["shards"][task["task_id"]] = {"sha256": sha256(path),
            "rows": len(task["methods"]), "bytes": path.stat().st_size}
        manifest["completed_shards"] = len(manifest["shards"])
        manifest["elapsed_seconds"] = time.monotonic() - start
        atomic_json(manifest_path, manifest)
        print(f'{len(manifest["shards"])}/{len(tasks)} {task["task_id"]} '
              f'elapsed={time.monotonic()-start:.1f}s', flush=True)

    def failure(task, exc):
        manifest["failures"].append({"task_id": task["task_id"], "error": repr(exc),
                                      "traceback": traceback.format_exc()})
        atomic_json(manifest_path, manifest)
        print(f'FAILED {task["task_id"]}: {exc!r}', flush=True)

    try:
        if workers == 1:
            for task in todo:
                try:
                    publish(task, _worker(task, methods))
                except Exception as exc:
                    failure(task, exc)
        else:
            # Spawn makes Windows and Linux follow the same process lifecycle.
            import multiprocessing
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers,
                    mp_context=multiprocessing.get_context("spawn")) as pool:
                iterator = iter(todo)
                running = {}
                for _ in range(min(len(todo), workers * 2)):
                    task = next(iterator)
                    running[pool.submit(_worker, task, methods)] = task
                while running:
                    finished, _ = concurrent.futures.wait(running,
                        return_when=concurrent.futures.FIRST_COMPLETED)
                    for future in finished:
                        task = running.pop(future)
                        try:
                            publish(task, future.result())
                        except Exception as exc:
                            failure(task, exc)
                        next_task = next(iterator, None)
                        if next_task is not None:
                            running[pool.submit(_worker, next_task, methods)] = next_task
        if manifest["failures"]:
            raise RuntimeError(f'{len(manifest["failures"])} execution shards failed; see manifest and resume')
        manifest["files"] = _write_csv_tables(output, tasks)
        if manifest["files"]["runs.csv.gz"]["rows"] != manifest["expected_runs"]:
            raise RuntimeError("Aggregate does not contain the expected unique trajectories")
        manifest.update(status="PASS", completed_shards=len(tasks),
                        actual_runs=manifest["expected_runs"],
                        completed_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        atomic_json(manifest_path, manifest)
        verify(output, check_current=True)
        if render:
            from .analysis import analyze
            from .plotting import plot
            analyze(output)
            plot(output)
        print(f'PASS {manifest["actual_runs"]} unique trajectories: {output}', flush=True)
        return manifest
    except BaseException:
        manifest["status"] = "FAIL" if manifest["failures"] else "INTERRUPTED"
        atomic_json(manifest_path, manifest)
        raise


def verify(output: Path, check_current: bool = False) -> dict:
    output = Path(output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "PASS":
        raise ValueError("Run is not complete: " + manifest["status"])
    config = json.loads((output / "config.json").read_text(encoding="utf-8"))
    if sha256(output / "config.json") != manifest["config_sha256"]:
        raise ValueError("Configuration checksum mismatch")
    if hashlib.sha256(json_bytes(config)).hexdigest() != manifest["fingerprint"]:
        raise ValueError("Configuration fingerprint mismatch")
    if check_current and config["source_files"] != input_files():
        raise ValueError("Current code/configuration differs from the recorded run")
    for name, info in manifest["files"].items():
        if sha256(output / name) != info["sha256"]:
            raise ValueError("Aggregate checksum mismatch: " + name)
    layouts = {s["id"]: s for s in config["layouts"]}
    for record in config["tasks"]:
        task = dict(record, layout=layouts[record["layout_id"]])
        path = output / "shards" / (task["task_id"] + ".json.gz")
        info = manifest["shards"][task["task_id"]]
        if sha256(path) != info["sha256"]:
            raise ValueError("Shard checksum mismatch: " + path.name)
        _validate_shard(_read_shard(path), task)
    seen = set()
    with gzip.open(output / "runs.csv.gz", "rt", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            key = tuple(row[k] for k in ["cohort", "layout_id", "law", "rep", "method"])
            if key in seen:
                raise ValueError("Duplicate aggregate trajectory")
            seen.add(key)
    if len(seen) != manifest["expected_runs"]:
        raise ValueError("Unexpected aggregate trajectory count")
    return {"status": "PASS", "unique_trajectories": len(seen),
            "checked_shards": len(manifest["shards"])}
