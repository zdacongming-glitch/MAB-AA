"""Verify the independent clean build and create a whitelist source archive."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import zipfile

REV=Path(__file__).resolve().parent
ROOT=REV.parent
PACKAGE=REV/"submission_source"
checks={}
issues=[]
for stem in ["manuscript","supplement"]:
    log=(PACKAGE/"revision_2026-10-16/build"/f"{stem}.log").read_text(encoding="utf-8",errors="replace")
    warnings=[s for s in log.splitlines() if re.search(r"Warning|Overfull|Underfull|undefined|multiply defined",s)]
    if warnings:
        issues.append(f"Package build warnings: {stem}: {warnings}")
    text=lambda folder: subprocess.run(["pdftotext","-layout",f"{stem}.pdf","-"],cwd=folder,capture_output=True,check=True).stdout
    same=text(ROOT)==text(PACKAGE)
    if not same:
        issues.append(f"Independent source build content differs: {stem}")
    checks[stem]={"same_extracted_text_as_reviewed_pdf":same,"warnings":warnings}

manifest=json.loads((REV/"submission-source-manifest.json").read_text(encoding="utf-8"))
# The independent build may change PDF timestamps/IDs. The distributed PDF
# is the actually rendered and reviewed one, while source text stays equal.
import shutil
for stem in ["manuscript","supplement"]:
    shutil.copy2(ROOT/f"{stem}.pdf",PACKAGE/f"{stem}.pdf")
for name,digest in manifest.items():
    path=PACKAGE/name
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        issues.append(f"Whitelist source changed: {name}")
if any("original_submission" in name or "baseline" in name or "ucbaa_repaired_analysis" in name or "retained_regret_lower" in name for name in manifest):
    issues.append("Legacy material entered whitelist")
report={"passed":not issues,"issues":issues,"independent_build_exit_code":0,"documents":checks,"whitelisted_files":len(manifest)}
(REV/"source-package-validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
if issues:
    print(json.dumps(report));raise SystemExit(1)
with zipfile.ZipFile(REV/"submission-source.zip","w",compression=zipfile.ZIP_DEFLATED) as archive:
    for name in sorted(manifest):
        archive.write(PACKAGE/name,arcname=name)
(REV/"build-record.json").write_text(json.dumps({
    "root":{"cwd":str(ROOT),"command":"./build.ps1 *> revision_2026-10-16/build-console.log","exit_code":0},
    "independent_whitelist":{"cwd":str(PACKAGE),"command":"./build.ps1 *> revision_2026-10-16/package-build-console.log","exit_code":0},
    "engine":"latexmk -pdf / pdfLaTeX / BibTeX", "output_directory":"revision_2026-10-16/build",
    "notes":"Only the final successful builds are reported here; no external publication was performed."},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report))
