#!/usr/bin/env python3
"""Replay frozen parameter-check configurations without development files.

Examples:
  python replay_parameter_check.py run --stage original --output _runs/check-original
  python replay_parameter_check.py run --config CONFIG.json --output OUTPUT --resume
  python replay_parameter_check.py analyze OUTPUT
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys

ENTRY_PATH = Path(__file__).resolve()
ROOT = ENTRY_PATH.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("NUMBA_NUM_THREADS", "1")
REVISION = "parameter-check-replay-v1"
ASSET_NAMES = ("replay_parameter_check.py", "tools/__init__.py",
               "tools/parameter_statistics.py", "tools/analyze_parameter_check.py")
# Preserve scientific definitions and output sampling, while keeping historical
# producer hashes and its runtime environment explicitly under origin_diagnostics.
SCIENTIFIC_DIAGNOSTICS = {
    "primary_candidate_ids", "primary_comparison_family_size", "primary_groups",
    "primary_baselines", "primary_alpha", "study_phase", "varied_parameters",
    "linear_points", "log_points", "trajectory_replications", "per_arm_methods",
    "smoke_all_methods"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def asset_bytes():
    return {name: (ENTRY_PATH if name == ASSET_NAMES[0] else ROOT / name).read_bytes()
            for name in ASSET_NAMES}


def prepare(config_path):
    """Rebuild exact scientific tasks; producer/runtime metadata describe this replay."""
    from srcbench import numba_cache_info
    from srcbench.design import _task
    from srcbench.runner import input_files
    from tools.parameter_statistics import validate_primary_declarations

    raw = Path(config_path).read_bytes()
    origin = json.loads(raw.decode("utf-8-sig"))
    current = input_files()
    if origin.get("source_files") != current:
        raise ValueError("Frozen configuration source_files differ from current source SHA values")
    validate_primary_declarations(origin)
    assets = asset_bytes()
    metadata = dict(schema_version=1, entry_revision=REVISION,
        entry_sha256=digest(assets[ASSET_NAMES[0]]), origin_config_sha256=digest(raw),
        asset_sha256={name:digest(data) for name, data in assets.items()},
        origin_profile=origin.get("profile"),
        source_match="exact source-file SHA mapping; Git HEAD is not consulted",
        execution_scope="new replay of frozen tasks; not the producer of original results")
    methods = deepcopy(origin.get("methods", {}))
    layouts = {item["id"]:deepcopy(item) for item in origin.get("layouts", [])}
    if not methods or any(spec.get("id") != name for name, spec in methods.items()):
        raise ValueError("Missing methods or inconsistent frozen method identifiers")
    if not layouts or len(layouts) != len(origin["layouts"]):
        raise ValueError("Missing or duplicate frozen layouts")
    records = origin.get("tasks", [])
    tasks, seen, scientific_keys = [], set(), set()
    cache = dict(strategy="package-source-hash-isolated-Numba-cache", **numba_cache_info())
    for record in records:
        names = record["methods"]
        if (not names or len(names) != len(set(names)) or not set(names) <= set(methods)
                or set(record["method_suites"]) != set(names)):
            raise ValueError("Frozen task has inconsistent methods or suite membership")
        if record["layout_id"] not in layouts:
            raise ValueError("Frozen task refers to a missing layout")
        for field in ("rep", "seed_base"):
            if isinstance(record[field], bool) or not isinstance(record[field], int):
                raise ValueError("Frozen replication and seed must be integers")
        task = _task(layouts[record["layout_id"]], record["law"], record["rep"],
                     record["seed_base"], record["cohort"],
                     {name:deepcopy(record["method_suites"][name]) for name in names})
        for field in ("task_id", "cell_id", "law", "rep", "seed_base", "cohort",
                      "methods", "suites", "method_suites"):
            if task[field] != record[field]:
                raise ValueError("Frozen task identity or seed fingerprint differs: " + field)
        key = (record["cohort"], record["layout_id"], record["law"], record["rep"])
        if task["task_id"] in seen or key in scientific_keys:
            raise ValueError("Duplicate frozen task identity or scientific world")
        seen.add(task["task_id"])
        scientific_keys.add(key)
        previous = deepcopy(record.get("diagnostics", {}))
        task["diagnostics"] = {key:deepcopy(value) for key, value in previous.items()
                               if key in SCIENTIFIC_DIAGNOSTICS}
        task["diagnostics"].update(study_revision=REVISION, numba_cache=deepcopy(cache),
            origin_diagnostics=previous, replay_parameter_check=deepcopy(metadata))
        tasks.append(task)
    used_methods = {name for task in tasks for name in task["methods"]}
    used_layouts = {task["layout"]["id"] for task in tasks}
    if not tasks or used_methods != set(methods) or used_layouts != set(layouts):
        raise ValueError("Frozen snapshot has empty tasks or unused method/layout definitions")
    if sum(len(task["methods"]) for task in tasks) != origin.get("expected_runs"):
        raise ValueError("Frozen expected_runs differs from reconstructed tasks")
    return tasks, methods, metadata, {"origin_config.json":raw, **assets}


def _validate_assets(output, metadata, snapshots, write=False):
    """Called under the run lock. Never overwrite changed provenance snapshots."""
    from srcbench.runner import atomic_bytes

    folder = output / "replay_inputs"
    for name, data in snapshots.items():
        path = folder / name
        if path.exists() and path.read_bytes() != data:
            raise ValueError("Replay input snapshot changed: " + name)
        if write and not path.exists():
            atomic_bytes(path, data)
    return folder


def _recorded_replay(output):
    path = output / "config.json"
    if not path.is_file():
        return None
    config = json.loads(path.read_text(encoding="utf-8-sig"))
    records = [task.get("diagnostics", {}).get("replay_parameter_check")
               for task in config.get("tasks", [])]
    if not records or any(item != records[0] for item in records):
        raise ValueError("Recorded replay task fingerprints disagree")
    return records[0]


def run(config_path, output, workers="auto", resume=False, dry_run=False, render=False):
    from srcbench.runner import _run_locked, atomic_json, choose_workers, preview, run_lock

    tasks, methods, metadata, snapshots = prepare(config_path)
    profile = "parameter-check-replay"
    plan = dict(preview(tasks, profile), origin_config_sha256=metadata["origin_config_sha256"],
                entry_sha256=metadata["entry_sha256"], formal_experiment=False)
    plan["kind"] = "replay of frozen parameter-check tasks"
    print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
    if dry_run:
        return plan
    output = Path(output).resolve()
    if output == ROOT or output in ROOT.parents or any(
            output == ROOT / name or ROOT / name in output.parents
            for name in ("src", "configs", "tools", "tests")):
        raise ValueError("Output must be a dedicated run directory outside source/configuration/tools/tests")
    output.mkdir(parents=True, exist_ok=True)
    with run_lock(output / ".runner.lock"):
        if resume:
            if _recorded_replay(output) != metadata:
                raise ValueError("Cannot resume changed replay entry, tools, or origin configuration")
            _validate_assets(output, metadata, snapshots)
        try:
            manifest = _run_locked(profile, output, tasks, methods,
                                   choose_workers(workers, profile), resume, False)
        finally:
            # A normal completion, exception or Ctrl-C preserves exact inputs.
            # A hard crash before this point can recover them on the next resume,
            # whose config fingerprint must first match these exact bytes.
            if _recorded_replay(output) == metadata:
                _validate_assets(output, metadata, snapshots, write=True)
                manifest_path = output / "manifest.json"
                if manifest_path.is_file():
                    recorded = json.loads(manifest_path.read_text(encoding="utf-8"))
                    recorded.update(scientific_scope="Replay of frozen parameter-check tasks; no parameter selection",
                                    formal_experiment=False, replay_parameter_check=metadata)
                    atomic_json(manifest_path, recorded)
                    if "manifest" in locals():
                        manifest = recorded
        if render:
            analyze(output)
        return manifest


def analyze(output):
    from srcbench.runner import sha256, verify
    from tools.analyze_parameter_check import analyze as summarize

    output = Path(output).resolve()
    verify(output, check_current=True)
    metadata = _recorded_replay(output)
    if metadata is not None:
        if {name:digest(data) for name, data in asset_bytes().items()} != metadata["asset_sha256"]:
            raise ValueError("Current replay entry or analysis tools differ from the recorded snapshot")
        folder = output / "replay_inputs"
        expected = {"origin_config.json":metadata["origin_config_sha256"], **metadata["asset_sha256"]}
        for name, fingerprint in expected.items():
            path = folder / name
            if not path.is_file() or sha256(path) != fingerprint:
                raise ValueError("Replay provenance checksum mismatch: " + name)
    return summarize(output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    launch = commands.add_parser("run", help="Replay only the supplied frozen snapshot")
    origin = launch.add_mutually_exclusive_group(required=True)
    origin.add_argument("--config", type=Path)
    origin.add_argument("--stage", choices=["original", "scaled"])
    launch.add_argument("--output", type=Path, required=True)
    launch.add_argument("--workers", default="auto")
    launch.add_argument("--resume", action="store_true")
    launch.add_argument("--dry-run", action="store_true")
    launch.add_argument("--analyze", action="store_true", help="Summarize and draw after a complete replay")
    report = commands.add_parser("analyze", help="Analyze a completed parameter-check output")
    report.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    if args.command == "run":
        config = args.config or ROOT / "results/parameter-check" / (args.stage + "-validation") / "config.json"
        return run(config, args.output, args.workers, args.resume, args.dry_run, args.analyze)
    return analyze(args.output)


if __name__ == "__main__":
    main()
