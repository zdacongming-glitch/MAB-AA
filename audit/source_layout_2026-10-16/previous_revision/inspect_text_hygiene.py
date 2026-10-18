"""Use the requested skill's read-only inspector on every active source."""
from pathlib import Path
import concurrent.futures
import json
import subprocess
import sys
import unicodedata

REV = Path(__file__).resolve().parent
ROOT = REV.parent
CLI = Path(r"C:\Users\12701\.codex\skills\watermarks-remover\scripts\watermarks.py")
validation = json.loads((REV/"validation.json").read_text(encoding="utf-8"))
names = sorted({p for paths in validation["actual_inputs"].values() for p in paths} | {"references.bib"})

def inspect(name):
    result = subprocess.run([sys.executable,"-X","utf8",str(CLI),"inspect",str(ROOT/name)],capture_output=True,encoding="utf-8")
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        report = {"error":result.stdout,"stderr":result.stderr}
    item = {"file":name,"exit_code":result.returncode,"inspection":report}
    if name == "references.bib" and result.returncode == 2 and "Unsupported format" in result.stderr:
        text = (ROOT/name).read_text(encoding="utf-8")
        hits = [{"index":i,"codepoint":f"U+{ord(c):04X}"} for i,c in enumerate(text)
                if unicodedata.category(c) in {"Cf","Cc"} and c not in "\n\r\t"]
        item["manual_fallback"] = {"route":"Read-only Unicode category check; native BibTeX format unsupported", "suspicious_format_or_control_characters":hits,
                                   "metadata_removal_performed":False,"content_unchanged":True}
    return item

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(inspect,names))
report = {"route":"read-only Unicode/provenance text inspection plus authorized prose revision",
          "results":results,"files":len(results),"all_inspections_exit_zero":all(r["exit_code"]==0 for r in results),
          "statistical_watermark_removal_verified":False,"removed_characters":0,
          "originals_retained":"revision_2026-10-16/baseline",
          "pdf_metadata_route_used":False,
          "capability_note":"Native ExifTool returned WinError 623 in capability discovery; PDF metadata cleaning was not needed or performed. Text inspection is available."}
report["all_text_checks_passed"] = all(r["exit_code"]==0 or ("manual_fallback" in r and not r["manual_fallback"]["suspicious_format_or_control_characters"]) for r in results)
(REV/"watermark_inspection.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"files":len(results),"all_native_inspections_exit_zero":report["all_inspections_exit_zero"],"all_text_checks_passed":report["all_text_checks_passed"],"native_unsupported_formats":[r["file"] for r in results if "manual_fallback" in r],"removed_characters":0}))
if not report["all_text_checks_passed"]:
    raise SystemExit(1)
