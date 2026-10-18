#!/usr/bin/env python3
"""Numerical reproduction entry, independent of manuscripts and research archives.

Every action writes to a fresh isolated workspace and checks that distributed
inputs remain unchanged. The default --verify checks stored files and F-CCP
endpoint accounting without running a policy or repeating a simulation.
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures
import datetime as dt
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import threading
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.nbi", "*.nbc", ".DS_Store")


def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_out(p: Path, value) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy_file(relative: str, target: Path) -> None:
    source = ROOT / relative
    if not source.is_file():
        raise FileNotFoundError(f"Missing distributed input: {relative}")
    destination = target / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def copy_tree(relative: str, target: Path) -> Path:
    source = ROOT / relative
    if not source.is_dir():
        raise FileNotFoundError(f"Missing distributed input directory: {relative}")
    destination = target / relative
    shutil.copytree(source, destination, ignore=IGNORE, dirs_exist_ok=True)
    return destination


BASELINE = "experiments/regret_baseline_screen_2026-10-17"
INPUT_DIRS = ("experiments", "analysis", "figures", "metadata")


def frozen_snapshot() -> dict[str, str]:
    paths = [ROOT / "reproduce.py", ROOT / "requirements-reproduce.txt"]
    for folder in INPUT_DIRS:
        paths.extend(path for path in (ROOT / folder).rglob("*")
                     if path.is_file() and "__pycache__" not in path.parts
                     and path.suffix not in {".pyc", ".pyo", ".nbi", ".nbc"})
    return {path.relative_to(ROOT).as_posix(): digest(path)
            for path in sorted(set(paths)) if path.is_file()}


class Run:
    def __init__(self, args):
        self.args = args
        self.workspace = args.workspace.expanduser().resolve() if args.workspace else ROOT / "_reproduced"
        if self.workspace == ROOT or self.workspace in ROOT.parents:
            raise RuntimeError("Workspace must be a dedicated output directory, not the project or an ancestor.")
        for protected in [*INPUT_DIRS, ".git"]:
            if self.workspace == ROOT / protected or (ROOT / protected) in self.workspace.parents:
                raise RuntimeError("Workspace cannot be inside a distributed input directory.")
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.path = self.workspace / (stamp + "-" + uuid.uuid4().hex[:8])
        self.path.mkdir(parents=True, exist_ok=False)
        self.commands = []
        self.lock = threading.RLock()
        self.env = os.environ.copy()
        self.env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1",
                        NUMBA_CACHE_DIR=str(self.path / "numba-cache"),
                        MPLCONFIGDIR=str(self.path / "matplotlib-cache"))
        self.before = frozen_snapshot()
        self.result = {"started_utc": stamp, "action": args.action,
                       "suite": args.suite, "scope": "isolated numerical reproduction",
                       "workspace": str(self.path), "commands": self.commands}
        self.flush()

    def flush(self):
        with self.lock:
            json_out(self.path / "commands.json", self.result)

    def command(self, command: list[str], cwd: Path, name: str) -> None:
        # Commands receive only work copies; no project-parent research path is used.
        cwd.resolve().relative_to(self.path.resolve())
        log_path = self.path / "logs" / (name + ".log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        print("RUN", name, flush=True)
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.run(command, cwd=cwd, env=self.env, stdout=log,
                                     stderr=subprocess.STDOUT, check=False)
        entry = {"name": name, "command": command, "cwd": str(cwd),
                 "log": str(log_path.relative_to(self.path)),
                 "exit_code": process.returncode,
                 "elapsed_seconds": round(time.monotonic() - start, 4)}
        with self.lock:
            self.commands.append(entry)
            self.flush()
        if process.returncode:
            raise RuntimeError(f"{name} failed (exit {process.returncode}); see {log_path}")

    def python(self, script: Path, arguments: list[str], cwd: Path, name: str):
        self.command([sys.executable, "-B", "-X", "utf8", str(script), *arguments], cwd, name)

    def final(self, success: bool, error=None):
        after = frozen_snapshot()
        self.result.update(success=success, frozen_inputs_unchanged=self.before == after,
                           protected_files_checked=len(self.before))
        if error is not None:
            self.result["error"] = str(error)
        self.flush()
        if self.before != after:
            raise RuntimeError("Distributed numerical inputs changed during the reproduction command.")


def verify_original_driver() -> dict:
    package = ROOT / "experiments/original_submission_archive"
    p = package / "source/ce_five_algo_runner.py"
    tree = ast.parse(p.read_text(encoding="utf-8"))
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"BEST_CONFIGS", "ALGORITHMS"}:
                    values[target.id] = ast.literal_eval(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "BEST_CONFIGS":
            values[node.target.id] = ast.literal_eval(node.value)
    for scenario in ["C", "E"]:
        cfg = json.loads((package / ("scenario_" + scenario) / "config.json").read_text(encoding="utf-8"))
        if values["BEST_CONFIGS"][scenario] != cfg["best_config"]:
            raise RuntimeError("Original-submission driver configuration differs from archived " + scenario)
        if set(values["ALGORITHMS"]) != set(cfg["algorithms"]) or cfg["final_R"] != 100 or cfg["seed"] != 20260309:
            raise RuntimeError("Original-submission roster, repetition count or seed differs.")
    return {"entry": "experiments/original_submission_archive/source/ce_five_algo_runner.py",
            "matches_archived_configs_C_E": True, "replications_per_scenario": 100, "seed": 20260309,
            "manual_ce_final_used": False}


def checked_input(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    path.relative_to(ROOT.resolve())
    if not path.is_file():
        raise FileNotFoundError(f"Missing distributed numerical input: {relative}")
    return path


def verify_release() -> dict:
    manifest = json.loads(checked_input("metadata/files.sha256.json").read_text(encoding="utf-8-sig"))
    records = manifest["files"]
    seen = set()
    for record in records:
        relative = record["path"]
        if relative in seen:
            raise RuntimeError(f"Duplicate numerical manifest entry: {relative}")
        seen.add(relative)
        path = checked_input(relative)
        if path.stat().st_size != record["bytes"] or digest(path) != record["sha256"]:
            raise RuntimeError(f"Numerical release manifest mismatch: {relative}")
    gzip_records = manifest.get("original_gzip", [])
    for record in gzip_records:
        value, size = hashlib.sha256(), 0
        with gzip.open(checked_input(record["path"]), "rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                value.update(block)
                size += len(block)
        if size != record["source_bytes"] or value.hexdigest() != record["source_sha256"]:
            raise RuntimeError(f"Lossless historical data check failed: {record['path']}")
    return {"manifest": "metadata/files.sha256.json", "files_checked": len(records),
            "lossless_gzip_streams_checked": len(gzip_records)}


def do_verify(run: Run):
    manifest = verify_release()
    modules = []
    for folder in ("experiments", "analysis", "figures"):
        for path in sorted((ROOT / folder).rglob("*.py")):
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            modules.append(path.relative_to(ROOT).as_posix())
    historical_driver = verify_original_driver()
    verifier = run.path / "check_revision2_data.py"
    shutil.copyfile(checked_input("analysis/check_revision2_data.py"), verifier)
    run.python(verifier, ["--f-root", str(ROOT / "experiments/fccp_frozen"),
                         "--out", str(run.path / "fccp-endpoint-check.json")],
               run.path, "verify-fccp-endpoints")
    json_out(run.path / "verification.json", {
        "status": "passed", "release_manifest": manifest,
        "python_modules_ast_checked": modules, "original_submission_driver": historical_driver,
        "no_policy_executed": True, "manuscript_required": False,
        "external_research_archives_required": False})


def do_figures(run: Run):
    work = run.path / "numerical"
    work.mkdir()
    for directory in ("experiments/fccp_frozen", "experiments/results", BASELINE):
        copy_tree(directory, work)
    for relative in ("analysis/plot_fccp.py", "analysis/plot_baselines.py", "figures/gen_fig_performance.py"):
        copy_file(relative, work)
    run.python(work / "analysis/plot_fccp.py",
               ["--data-root", str(work / "experiments/fccp_frozen"),
                "--output-dir", str(work / "figures/fccp")], work, "figures-fccp")
    run.python(work / "figures/gen_fig_performance.py", ["--figures-only"], work, "figures-checkpoint")
    screen = work / BASELINE
    run.python(screen / "analyze.py", [str(screen / "results"), "--protocol", str(screen / "protocol.json")],
               screen, "analyze-baseline-stored-results")
    run.python(work / "analysis/plot_baselines.py",
               ["--results-dir", str(screen / "results"), "--output-dir", str(screen / "figures")],
               work, "figures-baseline")
    json_out(run.path / "figure-outputs.json", {
        "fccp": "numerical/figures/fccp", "checkpoint": "numerical/figures",
        "baseline": "numerical/" + BASELINE + "/figures", "policy_simulations": 0})


def do_smoke(run: Run):
    work = run.path / "numerical"
    work.mkdir()
    for directory in ("experiments/fccp_frozen", "experiments/ccp_frozen",
                      "experiments/frontier_frozen", "experiments/original_submission_archive", BASELINE):
        copy_tree(directory, work)
    for relative in ("analysis/check_fccp_interface.py", "experiments/run_experiments.py",
                     "experiments/reference_cp_ucb_aa.py"):
        copy_file(relative, work)
    run.python(work / "analysis/check_fccp_interface.py", [], work, "smoke-prescribed-interface")
    entries = ["experiments/fccp_frozen/src/study_v2.py", "experiments/fccp_frozen/src/study_matched.py",
               "experiments/ccp_frozen/run_study.py", "experiments/frontier_frozen/test_run.py",
               "experiments/run_experiments.py", "experiments/original_submission_archive/source/ce_five_algo_runner.py",
               BASELINE + "/runner.py"]
    for index, entry in enumerate(entries):
        path = work / entry
        run.python(path, ["--help"], path.parent, f"smoke-driver-{index + 1}-{path.stem}")
    json_out(run.path / "smoke-scope.json", {
        "policy_performance_trials": 0,
        "scope": "600 compatibility actions, 320 prescribed-observation API actions, 10 same-state action checks and 6 API rejection checks.",
        "report": "numerical/analysis/interface-checks.json",
        "production_driver_import_and_help_checks": len(entries),
        "not_claimed": "Full experiment rerun, seeded equality across random-number backends or probabilistic certification."})


def tasks(run: Run, items: list[tuple[list[str], Path, str]]):
    if run.args.workers == 1:
        for cmd, cwd, name in items:
            run.command(cmd, cwd, name)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=run.args.workers) as pool:
            futures = [pool.submit(run.command, cmd, cwd, name) for cmd, cwd, name in items]
            for future in futures:
                future.result()


def driver(script: Path, *arguments: str) -> list[str]:
    return [sys.executable, "-B", "-X", "utf8", str(script), *arguments]


def do_simulate(run: Run):
    suites = ["fccp", "ccp", "frontier", "checkpoint", "baseline"] if run.args.suite == "all" else [run.args.suite]
    outputs = []
    for suite in suites:
        paper = run.path / "simulations" / suite
        paper.mkdir(parents=True)
        if suite == "fccp":
            package = copy_tree("experiments/fccp_frozen", paper)
            for stage, entry in [("holdout", "study_v2.py"), ("matched-all", "study_matched.py")]:
                jobs = [(driver(package / "src" / entry, "--stage", stage, "--worker", str(w),
                                "--workers", str(run.args.workers)), package, f"simulate-fccp-{stage}-worker{w}")
                        for w in range(run.args.workers)]
                tasks(run, jobs)
            run.python(package / "src/analyze.py", [], package, "summarize-fccp-rerun")
            outputs.extend([str((package / "results/holdout-all.csv").relative_to(run.path)),
                            str((package / "results/matched-all-all.csv").relative_to(run.path))])
        elif suite == "ccp":
            package = copy_tree("experiments/ccp_frozen", paper)
            jobs = []
            for scenario in range(10):
                for offset in [0, 16, 32, 48]:
                    jobs.append((driver(package / "run_study.py", "--stage", "test", "--scenario", str(scenario),
                                        "--rep", "16", "--offset", str(offset), "--out", f"test-s{scenario}-r{offset}",
                                        "--policies", str(package / "test-policies-frozen.json")), package,
                                 f"simulate-ccp-s{scenario}-r{offset}"))
            tasks(run, jobs)
            run.python(package / "analyze.py", [], package, "summarize-ccp-rerun")
            outputs.append(str((package / "test-results.csv").relative_to(run.path)))
        elif suite == "frontier":
            package = copy_tree("experiments/frontier_frozen", paper)
            # This historical driver hard-codes four disjoint scenario shards.
            tasks(run, [(driver(package / "test_run.py", "--worker", str(w)), package,
                         f"simulate-frontier-worker{w}") for w in range(4)])
            run.python(package / "analyze_holdout.py", [], package, "summarize-frontier-rerun")
            outputs.append(str((package / "holdout-all.csv").relative_to(run.path)))
        elif suite == "checkpoint":
            copy_file("experiments/run_experiments.py", paper)
            copy_file("experiments/reference_cp_ucb_aa.py", paper)
            copy_file("figures/gen_fig_performance.py", paper)
            run.python(paper / "experiments/run_experiments.py", [], paper, "simulate-checkpoint-all")
            run.python(paper / "figures/gen_fig_performance.py", ["--figures-only"], paper, "figures-checkpoint-rerun")
            outputs.append(str((paper / "experiments/results/runs.csv").relative_to(run.path)))
        elif suite == "baseline":
            copy_tree("experiments/fccp_frozen", paper)
            package = copy_tree(BASELINE, paper)
            destination = package / "results-rerun"
            run.python(package / "runner.py",
                       ["--protocol", str(package / "protocol.json"), "--output", str(destination),
                        "--workers", str(run.args.workers)], package, "simulate-baseline-all")
            run.python(package / "analyze.py", [str(destination), "--protocol", str(package / "protocol.json")],
                       package, "summarize-baseline-rerun")
            outputs.append(str((destination / "runs-all.csv").relative_to(run.path)))
        elif suite == "original":
            verify_original_driver()
            package = copy_tree("experiments/original_submission_archive", paper)
            destination = paper / "new-original-submission-results"
            run.python(package / "source/ce_five_algo_runner.py",
                       ["--R", "100", "--seed", "20260309", "--n-jobs", str(run.args.workers),
                        "--max-checkpoints", "1000", "--progress", "off", "--output-dir", str(destination)],
                       package / "source", "simulate-original-submission-C-E")
            outputs.append(str(destination.relative_to(run.path)))
    json_out(run.path / "simulation-outputs.json", {
        "suites": suites, "outputs": outputs,
        "protocols_regenerated": False,
        "scope": "New independent reruns of the selected distributed test protocols. all means fccp, ccp, frontier, checkpoint and baseline. original is an explicit additional historical C/E rerun; development/tuning is archived separately.",
        "cross_version_bitwise_equality_claimed": False,
        "note": "Compare scenario/rep/method or scenario/seed/method metrics, excluding runtime fields. Original failure paths remain in the distributed data."})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    for action, help_text in [
        ("verify", "Verify numerical release hashes, lossless data, Python syntax and F-CCP endpoint accounting; no policy run."),
        ("figures", "Recompute numerical summaries and figures from stored results in an isolated copy; no simulation."),
        ("smoke", "Run only short prescribed-observation interface checks in an isolated copy."),
        ("simulate", "Rerun the complete selected frozen test suite in an isolated copy; can take substantial time."),
    ]:
        group.add_argument("--" + action, dest="action", action="store_const", const=action, help=help_text)
    parser.set_defaults(action="verify")
    parser.add_argument("--suite", choices=["fccp", "ccp", "frontier", "checkpoint", "baseline", "original", "all"], default="fccp")
    parser.add_argument("--workers", type=int, default=1, help="Concurrent simulation workers; default serial. Does not change frozen seeds or policies.")
    parser.add_argument("--workspace", type=Path, help="Dedicated output base (default: repository/_reproduced). Each invocation creates a new run directory.")
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 64:
        parser.error("--workers must be between 1 and 64")
    run = None
    try:
        run = Run(args)
        {"verify": do_verify, "figures": do_figures,
         "smoke": do_smoke, "simulate": do_simulate}[args.action](run)
        run.final(True)
        print(json.dumps({"status": "passed", "action": args.action,
                          "output": str(run.path), "frozen_inputs_unchanged": True}, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        if run is not None:
            run.final(False, error)
        print(f"Reproduction failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
