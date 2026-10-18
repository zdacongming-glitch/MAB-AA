"""Freeze the user-authorized 2026-10-16 editorial revision inputs."""
from pathlib import Path
import hashlib
import json
import shutil

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parent
REV = Path(__file__).resolve().parent
SNAP = REV / "baseline"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

if (REV / "input_manifest.json").exists():
    raise SystemExit("Input snapshot already exists; refusing to replace it.")
SNAP.mkdir(parents=True, exist_ok=False)
sources = []
for path in PROJECT.rglob("*"):
    if not path.is_file():
        continue
    rel = path.relative_to(PROJECT)
    if any(part in {"audit", "assessments", "revision_2026-10-16", "__pycache__"} for part in rel.parts):
        continue
    if path.suffix in {".tex", ".bib", ".md", ".ps1", ".py"} or rel.as_posix() in {"manuscript.pdf", "supplement.pdf"} or "original_submission" in rel.as_posix():
        dest = SNAP / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        sources.append({"path": rel.as_posix(), "sha256": sha(path), "bytes": path.stat().st_size})

protected = {}
for folder in ["JASA-template", "reconstruction_jasa_2026-10-13", "reconstruction_jasa_stage2_2026-10-13", "proposal/temporal_geometry_research", "proposal/ucbaa_continuous_maintenance_2026-10-14"]:
    root = REPO / folder
    if root.exists():
        for path in root.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                protected[path.relative_to(REPO).as_posix()] = sha(path)
for folder in [PROJECT / "experiments", PROJECT / "figures"]:
    for path in folder.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            protected[path.relative_to(REPO).as_posix()] = sha(path)

plan = REPO / "proposal/UCB-AA删除与集合维护重构_Codex执行方案_v1.0.md"
manifest = {"revision": "maintenance-editorial-2026-10-16-v1", "project": str(PROJECT), "plan": str(plan), "plan_sha256": sha(plan), "snapshot": sources, "protected_sha256": protected}
(REV / "input_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"snapshot_files": len(sources), "protected_files": len(protected), "main_pdf": sha(PROJECT / "manuscript.pdf"), "supplement_pdf": sha(PROJECT / "supplement.pdf")}, ensure_ascii=False))
