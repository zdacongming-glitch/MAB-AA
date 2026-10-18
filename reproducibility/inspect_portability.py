"""Read-only static/dependency audit of the numerical reproduction inputs.

Only writes audit reports beside this script. Does not import policies or simulate.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import json
import platform
import re
import shutil
import sys
import zipfile
from pathlib import Path

import pandas as pd

PAPER = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
FROZEN = PAPER / "experiments/fccp_frozen"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    # Every manifest item must be locally present, or recoverable from the exact
    # original ZIP distributed inside this manuscript folder.
    original = json.loads((FROZEN / "MANIFEST.json").read_text(encoding="utf-8"))
    archive = FROZEN / "original-archives/F-CCP_可调算法_理论与实验_2026-10-17.zip"
    manifest_items = []
    with zipfile.ZipFile(archive) as z:
        for rel, meta in original.items():
            p = FROZEN / rel
            if p.is_file():
                data, location = p.read_bytes(), "extracted"
            else:
                matches = [n for n in z.namelist() if n.endswith("/" + rel)]
                assert len(matches) == 1, rel
                data, location = z.read(matches[0]), "original_zip"
            assert sha(data) == meta["sha256"], rel
            manifest_items.append({"path": rel, "location": location, "sha256": sha(data)})

    source_imports = {}
    for p in sorted((FROZEN / "src").glob("*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        source_imports[p.name] = sorted(imports)
    local_modules = {p.stem for p in (FROZEN / "src").glob("*.py")}
    third_party = {"numpy", "numba", "pandas", "scipy", "matplotlib"}
    unresolved_imports = sorted({m for modules in source_imports.values() for m in modules
                                 if m not in local_modules and m not in third_party
                                 and m not in sys.stdlib_module_names})
    assert not unresolved_imports, unresolved_imports

    tex = (PAPER / "manuscript.tex").read_text(encoding="utf-8")
    assets = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex)
    missing_assets = [a for a in assets if not (PAPER / a).is_file()]
    assert not missing_assets, missing_assets
    bibliography = re.findall(r"\\bibliography\{([^}]+)\}", tex)
    for group in bibliography:
        for item in group.split(","):
            assert (PAPER / (item.strip() + ".bib")).is_file(), item

    f_data = pd.concat([pd.read_csv(FROZEN / "results/holdout-all.csv"),
                        pd.read_csv(FROZEN / "results/matched-all-all.csv")], ignore_index=True)
    runtimes = {stage: float(group.runtime.sum()) for stage, group in f_data.groupby("stage")}
    earlier = []
    for name, member, runtime_col in [
        ("CCP_算法探索_研究包_2026-10-16.zip", "CCP_research_2026-10-16/test-results.csv", "runtime_sec"),
        ("Regret_未决量前沿_理论与算法研究包_2026-10-16.zip", "frontier_research_2026-10-16/holdout-all.csv", "runtime"),
    ]:
        with zipfile.ZipFile(FROZEN / "original-archives" / name) as z:
            with z.open(member) as stream:
                data = pd.read_csv(stream)
        earlier.append({"archive": name, "member": member, "rows": len(data),
                        "sum_recorded_runtime_seconds": float(data[runtime_col].sum())})

    report = {
        "audit_date": "2026-10-17",
        "scope": "Read-only portability audit during repository packaging; no policy simulation or parameter change.",
        "f17_original_manifest_items_verified": len(manifest_items),
        "f17_manifest_items": manifest_items,
        "f17_python_modules_ast_parsed": len(source_imports),
        "f17_module_imports": source_imports,
        "unresolved_f17_imports": unresolved_imports,
        "current_manuscript_graphic_references": assets,
        "missing_manuscript_assets": missing_assets,
        "f17_runtime_sums_seconds": runtimes,
        "earlier_runtime_records": earlier,
        "runtime_caveat": "Recorded per-run timing sums from original machines; not a measured end-to-end runtime on this machine. JIT, I/O, worker concurrency, development, original-submission studies and exact LP runs are additional or differently bounded.",
        "current_audit_environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "libraries": {name: importlib.metadata.version(name) for name in sorted(third_party)},
            "latex_tools": {name: shutil.which(name) for name in ["latexmk", "pdflatex", "bibtex", "kpsewhich"]},
        },
        "independent_directory_findings": [
            {"id": "P1", "status": "portable_with_explicit_mode", "entry": "revision2/analysis/reanalyze_fccp.py --release-only",
             "detail": "Reads manuscript-local F17 files and recovers C16/P16 test rows from the three bundled ZIPs; its default mode otherwise prefers a sibling F-CCP directory when present."},
            {"id": "P2", "status": "needs_isolated_work_directory", "entry": "experiments/fccp_frozen/src/study_v2.py and study_matched.py",
             "detail": "Drivers derive package paths from __file__, but overwrite results in their own copied package. Default workers=4, worker=0 processes only one quarter of scenarios. Use workers=1 for a complete serial rerun or execute all disjoint workers."},
            {"id": "P3", "status": "needs_isolated_work_directory", "entry": "experiments/run_experiments.py",
             "detail": "Local reference_cp_ucb_aa.py closes the original source dependency; normal run overwrites experiments/results, pilot overwrites experiments/pilot."},
            {"id": "P4", "status": "historical_collection_only", "entry": "experiments/original_submission_archive/summarize_archive.py --collect",
             "detail": "Collection uses an original absolute Projects path and sibling JASA-template. Default summarization reads local archived inputs but overwrites summaries, metadata and a historical table .tex file."},
            {"id": "P5", "status": "closed_by_packaging" if all((PAPER / "experiments/original_submission_archive" / ("scenario_" + s) / "raw_checkpoint.csv.gz").is_file() for s in ["C", "E"]) else "original_history_gap_identified", "entry": "experiments/original_submission_archive/metadata.json",
             "detail": "Earlier release omitted original scenario C/E raw_checkpoint.csv, approximately 380 MB combined. Repository packaging now collects lossless gzip copies; reproduce.py --verify checks both compressed identity and decompressed original size/SHA. The unchanged old metadata records its historical omission rather than the new collection status."},
            {"id": "P6", "status": "separate_environments", "entry": "experiments/requirements.txt and experiments/fccp_frozen/environment.json",
             "detail": "Legacy CP recorded Python3.11.7/NumPy1.26.4/Numba0.59.0; F17 recorded Python3.13.5/NumPy2.3.5/Numba0.65.1. Their historical environment files must not be collapsed into a claim of cross-version bitwise equality."},
            {"id": "P7", "status": "portable_current_build", "entry": "revision2/build_papers.py",
             "detail": "Current combined manuscript compiles with local paths and cwd explicitly set to the manuscript root; historical --baseline option is a guarded archival workflow, not a fresh-clone acceptance command."},
            {"id": "P8", "status": "historical_scripts_not_reproduction_entries", "entry": "revision2/integrate.py, editorial_main.py, freeze_inputs.py, audit/*",
             "detail": "Revision-time editorial/provenance scripts can refer to prior research directories, baseline layouts and old split documents. Preserve them as history and do not execute them in the main reproduce command."},
        ],
    }
    destination = OUT / "portability-audit.json"
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed_static_checks", "manifest_items": len(manifest_items),
                      "python_modules": len(source_imports), "graphics": len(assets),
                      "report": destination.relative_to(PAPER).as_posix()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
