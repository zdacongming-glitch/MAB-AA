#!/usr/bin/env python3
"""Portable reproduction entry. Frozen policies, data and manuscript stay unchanged.

All generated output is written in a fresh isolated workspace. The default action
verifies stored material and rechecks F17 endpoints without running a policy.
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures
import csv
import datetime as dt
import gzip
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import time
import threading
import uuid
import zipfile
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


def assets() -> list[str]:
    text = (ROOT / "manuscript.tex").read_text(encoding="utf-8")
    found = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text)
    for name in found:
        p = Path(name)
        if p.is_absolute() or ".." in p.parts or not (ROOT / p).is_file():
            raise RuntimeError(f"Nonlocal or missing manuscript graphic: {name}")
    return sorted(set(found))


def frozen_snapshot() -> dict[str, str]:
    # Numerical inputs and current authoring entry are protected in every mode.
    paths = [ROOT / "manuscript.tex", ROOT / "references.bib",
             ROOT / "experiments/run_experiments.py",
             ROOT / "experiments/reference_cp_ucb_aa.py",
             ROOT / "figures/gen_fig_performance.py"]
    for folder in ["experiments/fccp_frozen", "experiments/ccp_frozen",
                   "experiments/frontier_frozen", "experiments/results",
                   "experiments/original_submission_archive"]:
        p = ROOT / folder
        if p.is_dir():
            paths.extend(x for x in p.rglob("*") if x.is_file()
                         and "__pycache__" not in x.parts and x.suffix not in {".pyc", ".nbi", ".nbc"})
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(set(paths))}


class Run:
    def __init__(self, args):
        self.args = args
        self.workspace = args.workspace.expanduser().resolve() if args.workspace else ROOT / "_reproduced"
        if self.workspace == ROOT or self.workspace in ROOT.parents:
            raise RuntimeError("Workspace must be a dedicated output directory, not the project or an ancestor.")
        for protected in ["experiments", "revision2", "audit", "figures", "assessments", "build"]:
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
                       "suite": args.suite, "scope": "isolated portable reproduction",
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
            raise RuntimeError("Protected project inputs changed during the reproduction command.")


def copy_paper(run: Run, numerical=False) -> Path:
    paper = run.path / "paper"
    paper.mkdir()
    for relative in ["manuscript.tex", "references.bib", "revision2/build_papers.py", *assets()]:
        copy_file(relative, paper)
    if numerical:
        for directory in ["experiments/fccp_frozen", "experiments/results"]:
            copy_tree(directory, paper)
        for relative in ["figures/gen_fig_performance.py", "revision2/analysis/reanalyze_fccp.py",
                         "revision2/analysis/release-manifest.json"]:
            copy_file(relative, paper)
        # Transparent adapter in the work copy only: the editorial generator
        # otherwise probes sibling research folders even with --release-only.
        path = paper / "revision2/analysis/reanalyze_fccp.py"
        old = path.read_text(encoding="utf-8")
        assert old.count("REPO = PROJECT.parent") == 1
        path.write_text(old.replace("REPO = PROJECT.parent", "REPO = PROJECT  # standalone work-copy adapter"), encoding="utf-8")
        json_out(run.path / "path-adapter.json", {
            "source": "revision2/analysis/reanalyze_fccp.py", "source_sha256": digest(ROOT / "revision2/analysis/reanalyze_fccp.py"),
            "work_copy_sha256": digest(path), "change": "REPO = PROJECT.parent -> REPO = PROJECT",
            "reason": "Keep all historical research-asset lookups inside the isolated paper copy.",
            "policy_code_changed": False})
    return paper


def verify_original_manifests() -> list[dict]:
    records = []
    f = ROOT / "experiments/fccp_frozen"
    manifest = json.loads((f / "MANIFEST.json").read_text(encoding="utf-8"))
    archive = f / "original-archives/F-CCP_可调算法_理论与实验_2026-10-17.zip"
    with zipfile.ZipFile(archive) as z:
        for rel, metadata in manifest.items():
            if (f / rel).is_file():
                actual = digest(f / rel)
            else:
                matches = [n for n in z.namelist() if n.endswith("/" + rel)]
                if len(matches) != 1:
                    raise RuntimeError(f"Unrecoverable original F17 manifest input: {rel}")
                actual = hashlib.sha256(z.read(matches[0])).hexdigest()
            if actual != metadata["sha256"]:
                raise RuntimeError(f"F17 manifest mismatch: {rel}")
    records.append({"manifest": "experiments/fccp_frozen/MANIFEST.json", "checked": len(manifest)})
    for relative, name in [("experiments/ccp_frozen", "checksums.sha256"),
                           ("experiments/frontier_frozen", "MANIFEST.sha256")]:
        directory = ROOT / relative
        p = directory / name
        if not p.is_file():
            continue
        checked = 0
        for line in p.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            expected, rel = line.split(maxsplit=1)
            rel = rel.lstrip(" *")
            rel = rel.removeprefix("./")
            item = directory / rel
            item.resolve().relative_to(directory.resolve())
            if not item.is_file() or digest(item) != expected:
                raise RuntimeError(f"Historical manifest mismatch: {relative}/{rel}")
            checked += 1
        records.append({"manifest": relative + "/" + name, "checked": checked})
    checkpoint = ROOT / "experiments"
    manifest = json.loads((checkpoint / "results/manifest.json").read_text(encoding="utf-8"))
    checkpoint_inputs = {
        "source_sha256": "reference_cp_ucb_aa.py",
        "runner_sha256": "run_experiments.py",
        "config_sha256": "results/config.json",
        "runs_sha256": "results/runs.csv",
        "paths_sha256": "results/paths.npz",
    }
    for key, relative in checkpoint_inputs.items():
        item = checkpoint / relative
        if not item.is_file() or digest(item) != manifest[key]:
            raise RuntimeError(f"Checkpoint manifest mismatch: experiments/{relative}")
    records.append({"manifest": "experiments/results/manifest.json",
                    "checked": len(checkpoint_inputs)})
    return records


def verify_import_manifests() -> list[dict]:
    reports = []
    for name in ["numerical-import-manifest.json", "support-import-manifest.json"]:
        p = ROOT / "reproducibility" / name
        if not p.is_file():
            raise FileNotFoundError("Missing distributed collection manifest: " + name)
        records = json.loads(p.read_text(encoding="utf-8"))["files"]
        decompressed = 0
        for record in records:
            item = ROOT / record["destination"]
            item.resolve().relative_to(ROOT.resolve())
            expected = record.get("destination_sha256", record.get("sha256"))
            if not item.is_file() or digest(item) != expected:
                raise RuntimeError("Import manifest mismatch: " + record["destination"])
            if record.get("operation") == "gzip-lossless":
                h, size = hashlib.sha256(), 0
                with gzip.open(item, "rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        h.update(block)
                        size += len(block)
                if h.hexdigest() != record["source_sha256"] or size != record["source_bytes"]:
                    raise RuntimeError("Decompressed historical data mismatch: " + record["destination"])
                decompressed += 1
        reports.append({"manifest": "reproducibility/" + name, "files_checked": len(records),
                        "lossless_gzip_streams_checked": decompressed,
                        "original_machine_source_paths_accessed": False})
    return reports


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


def verify_local_imports(folder: str) -> dict:
    source = ROOT / folder
    module_files = list(source.glob("*.py"))
    modules = {p.stem for p in module_files}
    # P16 explicitly vendors its original CCP dependency under prior/.
    modules.update(p.stem for p in (source / "prior").rglob("*.py"))
    allowed = set(sys.stdlib_module_names) | {"numpy", "numba", "pandas", "scipy", "matplotlib", "sympy", "tqdm"} | modules
    missing = set()
    for p in module_files:
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8-sig"))):
            if isinstance(node, ast.Import):
                names = [x.name.split(".")[0] for x in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            else:
                names = []
            missing.update(name for name in names if name not in allowed)
    if missing:
        raise RuntimeError(f"Unresolved distributed module imports in {folder}: {sorted(missing)}")
    return {"folder": folder, "python_files_checked": len(module_files), "unresolved_imports": []}


def do_verify(run: Run):
    resources = assets()
    text = (ROOT / "manuscript.tex").read_text(encoding="utf-8")
    for group in re.findall(r"\\bibliography\{([^}]+)\}", text):
        for name in group.split(","):
            if not (ROOT / (name.strip() + ".bib")).is_file():
                raise RuntimeError("Missing bibliography: " + name)
    if re.search(r"\\(?:input|include)\s*\{", text):
        raise RuntimeError("Unexpected external TeX source dependency in the combined manuscript.")
    manifests = verify_original_manifests()
    import_manifests = verify_import_manifests()
    historical_driver = verify_original_driver()
    import_closure = [verify_local_imports(folder) for folder in [
        "experiments/fccp_frozen/src", "experiments/ccp_frozen", "experiments/frontier_frozen",
        "experiments/original_submission_archive/source"]]
    modules = []
    for folder in ["experiments/fccp_frozen/src", "experiments/ccp_frozen", "experiments/frontier_frozen"]:
        source = ROOT / folder
        if source.is_dir():
            for p in source.glob("*.py"):
                ast.parse(p.read_text(encoding="utf-8-sig"), filename=str(p))
                modules.append(p.relative_to(ROOT).as_posix())
    verifier = run.path / "check_revision2_data.py"
    shutil.copyfile(ROOT / "revision2/analysis/check_revision2_data.py", verifier)
    # Checker reads the frozen inputs and writes its fresh report outside them.
    run.python(verifier, ["--f-root", str(ROOT / "experiments/fccp_frozen"),
                         "--out", str(run.path / "fccp-endpoint-check.json")], run.path, "verify-fccp-endpoints")
    report = {"status": "passed", "manifest_checks": manifests,
              "import_manifest_checks": import_manifests, "original_submission_driver": historical_driver,
              "local_import_closure": import_closure,
              "manuscript_graphics": resources, "python_modules_ast_checked": modules,
              "tex_code_in_single_manuscript": True,
              "no_policy_executed": True, "no_external_research_asset_lookup": True}
    json_out(run.path / "verification.json", report)


def do_figures(run: Run):
    paper = copy_paper(run, numerical=True)
    run.python(paper / "revision2/analysis/reanalyze_fccp.py", ["--release-only"], paper, "figures-fccp-readonly")
    run.python(paper / "figures/gen_fig_performance.py", ["--figures-only"], paper, "figures-checkpoint-readonly")


def do_build(run: Run):
    for tool in ["latexmk", "pdflatex", "bibtex"]:
        if shutil.which(tool) is None:
            raise RuntimeError(f"Missing TeX tool: {tool}. Install a TeX distribution with latexmk.")
    paper = copy_paper(run)
    run.python(paper / "revision2/build_papers.py", [], paper, "build-combined-manuscript")


def do_smoke(run: Run):
    paper = run.path / "paper"
    paper.mkdir()
    copy_tree("experiments/fccp_frozen", paper)
    copy_file("revision2/analysis/check_fccp_interface.py", paper)
    run.python(paper / "revision2/analysis/check_fccp_interface.py", [], paper, "smoke-prescribed-interface")
    for folder in ["experiments/ccp_frozen", "experiments/frontier_frozen", "experiments/original_submission_archive"]:
        copy_tree(folder, paper)
    copy_file("experiments/run_experiments.py", paper)
    copy_file("experiments/reference_cp_ucb_aa.py", paper)
    for entry in ["experiments/fccp_frozen/src/study_v2.py", "experiments/fccp_frozen/src/study_matched.py",
                  "experiments/ccp_frozen/run_study.py", "experiments/frontier_frozen/test_run.py",
                  "experiments/run_experiments.py", "experiments/original_submission_archive/source/ce_five_algo_runner.py"]:
        path = paper / entry
        run.python(path, ["--help"], path.parent, "smoke-driver-" + path.stem)
    json_out(run.path / "smoke-scope.json", {
        "policy_performance_trials": 0,
        "scope": "600 same-backend compatible actions, 320 prescribed-observation API actions, 10 same-state batch-action checks, 6 API rejection checks.",
        "report": "paper/revision2/analysis/interface-checks.json",
        "production_driver_import_and_help_checks": 6,
        "not_claimed": "Full experiment rerun, cross-backend seeded equality, probabilistic certification or independent proof verification."})


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
    suites = ["fccp", "ccp", "frontier", "checkpoint"] if run.args.suite == "all" else [run.args.suite]
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
        "scope": "New independent reruns of the selected distributed test protocols. all means fccp, ccp, frontier and checkpoint. original is an explicit additional historical C/E rerun; development/tuning is archived separately.",
        "cross_version_bitwise_equality_claimed": False,
        "note": "Compare scenario/rep/method or scenario/seed/method metrics, excluding runtime fields. Original failure paths remain in the distributed data."})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    for action, help_text in [
        ("verify", "Verify hashes, local assets, Python syntax and frozen F17 endpoint accounting; no policy run."),
        ("figures", "Recompute tables/figures from stored results in an isolated copy; no simulation."),
        ("build", "Compile the complete manuscript in an isolated copy."),
        ("smoke", "Run only short prescribed-observation interface checks in an isolated copy."),
        ("simulate", "Rerun the complete selected frozen test suite in an isolated copy; can take substantial time."),
    ]:
        group.add_argument("--" + action, dest="action", action="store_const", const=action, help=help_text)
    parser.set_defaults(action="verify")
    parser.add_argument("--suite", choices=["fccp", "ccp", "frontier", "checkpoint", "original", "all"], default="fccp")
    parser.add_argument("--workers", type=int, default=1, help="Concurrent simulation workers; default serial. Does not change frozen seeds or policies.")
    parser.add_argument("--workspace", type=Path, help="Dedicated output base (default: manuscript/_reproduced). Each invocation creates a new run directory.")
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 64:
        parser.error("--workers must be between 1 and 64")
    run = None
    try:
        run = Run(args)
        {"verify": do_verify, "figures": do_figures, "build": do_build,
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
