"""Validate the editorial delivery without rerunning comparative simulations."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import re
import subprocess

REV = Path(__file__).resolve().parent
ROOT = REV.parent
REPO = ROOT.parent
issues = []
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
baseline = json.loads((REV / "input_manifest.json").read_text(encoding="utf-8"))

def walk(entry, visited=None):
    visited = set() if visited is None else visited
    path = ROOT / entry
    if path in visited:
        return visited
    if not path.exists():
        issues.append(f"Missing input: {entry}")
        return visited
    visited.add(path)
    text = path.read_text(encoding="utf-8")
    for name in re.findall(r"\\(?:input|include)\{([^}]+)\}", text):
        if not Path(name).suffix:
            name += ".tex"
        walk(name, visited)
    return visited

graphs = {name: sorted(walk(name), key=str) for name in ["manuscript.tex", "supplement.tex"]}
active = set().union(*graphs.values())
texts = {p: p.read_text(encoding="utf-8") for p in active}
labels = collections.defaultdict(list)
refs = []
cites = set()
resources = set()
for path, text in texts.items():
    for label in re.findall(r"\\label\{([^}]+)\}", text):
        labels[label].append(str(path.relative_to(ROOT)))
    refs.extend(re.findall(r"\\(?:ref|eqref|autoref|[cC]ref)\*?\{([^}]+)\}", text))
    for keys in re.findall(r"\\cite\w*\*?(?:\[[^\]]*\])*\{([^}]+)\}", text):
        cites.update(k.strip() for k in keys.split(","))
    for resource in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text):
        resources.add(resource)
        if not (ROOT / resource).is_file():
            issues.append(f"Missing figure: {resource}")
    for word in ["UCB-AA", "Online UCB-AA", "pre-elimination", "preliminary screening", "formal elimination", "repaired procedure", "repaired fixed-budget", "original submission", "archived implementation", "original six figures", "The original two arrival scenarios", "reviewer’s proposed", "The sufficiency follows from the next theorem", "No data were created"]:
        if word in text:
            issues.append(f"Disallowed legacy narrative: {path.relative_to(ROOT)}: {word}")
    if re.search(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff\x00]", text):
        issues.append(f"Review invisible Unicode in {path.relative_to(ROOT)}")
    if re.search(r"[\ue000-\uf8ff]|TODO|FIXME|TBD", text):
        issues.append(f"Review task marker or private-use character in {path.relative_to(ROOT)}")

for key, occurrences in labels.items():
    if len(occurrences) > 1:
        issues.append(f"Duplicate label {key}: {occurrences}")
for key in refs:
    for label in key.split(","):
        if label not in labels:
            issues.append(f"Unresolved source reference: {label}")
bib = (ROOT / "references.bib").read_text(encoding="utf-8")
bibkeys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)", bib))
if cites - bibkeys:
    issues.append(f"Missing bibliography keys: {sorted(cites-bibkeys)}")

protected_changed = []
for name, digest in baseline["protected_sha256"].items():
    path = REPO / name
    if not path.is_file() or sha(path) != digest:
        protected_changed.append(name)
if protected_changed:
    issues.append(f"Protected files changed: {protected_changed}")
snapshot_changed = []
for entry in baseline["snapshot"]:
    path = REV / "baseline" / entry["path"]
    if not path.is_file() or sha(path) != entry["sha256"]:
        snapshot_changed.append(entry["path"])
if snapshot_changed:
    issues.append(f"Snapshot changed: {snapshot_changed}")
for entry in baseline["snapshot"]:
    if entry["path"] == "references.bib" or entry["path"].startswith("theory/"):
        path = ROOT/entry["path"]
        if not path.is_file() or sha(path) != entry["sha256"]:
            issues.append(f"Original bibliography/theory archive changed: {entry['path']}")

main = (ROOT / "manuscript.tex").read_text(encoding="utf-8")
supp = (ROOT / "supplement.tex").read_text(encoding="utf-8")
if len(re.findall(r"^\\section\{", main, re.M)) != 7:
    issues.append("Expected seven main sections")
if sum(len(re.findall(r"^\\section\{", t, re.M)) for p,t in texts.items() if p in graphs["supplement.tex"]) != 13:
    issues.append("Expected thirteen numbered supplementary sections")
if "original_submission" in "\n".join(str(p.relative_to(ROOT)) for p in active) or any("original_submission" in r for r in resources):
    issues.append("Archived experiments or old illustration remain active")
old_labels = ["thm:ucbaa_actual_prefix", "cor:ucbaa_static_fixed_gap"]
for label in old_labels:
    if label in labels:
        issues.append(f"Old dedicated theorem remains: {label}")

markdown_checked = []
mdpaths = [ROOT/"README.md", ROOT/"revision_map_zh.md", ROOT/"response_to_reviewers.md"]
mdpaths += [p for p in REV.glob("*.md")]
for path in mdpaths:
    if not path.is_file():
        continue
    fence = False
    dollars = 0
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence:
            continue
        if re.search(r"\\[()\[\]]", line):
            issues.append(f"Markdown delimiter: {path.name}:{number}")
        if "$$" in line:
            dollars += line.count("$$")
            if line.strip() != "$$":
                issues.append(f"Markdown display delimiter: {path.name}:{number}")
    if dollars % 2:
        issues.append(f"Unmatched Markdown display: {path.name}")
    markdown_checked.append(str(path.relative_to(ROOT)))

pdfs = {}
for stem in ["manuscript", "supplement"]:
    log = (REV/"build"/f"{stem}.log").read_text(encoding="utf-8", errors="replace")
    warnings = [line for line in log.splitlines() if re.search(r"Warning|Overfull|Underfull|undefined|multiply defined", line)]
    if warnings:
        issues.append(f"Build warnings in {stem}: {warnings}")
    info = subprocess.run(["pdfinfo", str(ROOT/f"{stem}.pdf")], capture_output=True, check=True).stdout.decode("utf-8", errors="replace")
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    extracted = subprocess.run(["pdftotext", "-layout", str(ROOT/f"{stem}.pdf"), "-"], capture_output=True, check=True).stdout.decode("utf-8", errors="replace")
    if "??" in extracted:
        issues.append(f"Unresolved PDF reference in {stem}")
    if "UCB-AA" in extracted or "FDA approval" in extracted:
        issues.append(f"Old narrative remains in PDF {stem}")
    used_cites = set(re.findall(r"\\citation\{([^}]+)\}", (REV/"build"/f"{stem}.aux").read_text(encoding="utf-8")))
    used_cites = {k for group in used_cites for k in group.split(",")}
    bblpath = REV/"build"/f"{stem}.bbl"
    if not bblpath.exists():
        issues.append(f"Missing isolated bibliography for {stem}")
        shown_cites = set()
    else:
        shown_cites = set(re.findall(r"\\bibitem(?:\[[\s\S]*?\])?\{([^}]+)\}", bblpath.read_text(encoding="utf-8")))
    if shown_cites != used_cites:
        issues.append(f"Bibliography displays uncited/missing entries in {stem}: extra={shown_cites-used_cites}, missing={used_cites-shown_cites}")
    pdfs[stem] = {"pages": pages, "sha256": sha(ROOT/f"{stem}.pdf"), "build_warnings": warnings, "bibliography_entries": len(shown_cites)}

experiment = json.loads((REV/"experiments_validation.json").read_text(encoding="utf-8"))
proof = json.loads((REV/"proof_math_preservation.json").read_text(encoding="utf-8"))
if not experiment["passed"]:
    issues.append("Saved-data or code-semantics validation did not pass")
if not proof["expected_information_tools_merge_only"] or not proof["legacy_theory_sources_unchanged"]:
    issues.append("Proof display migration/archival checks did not pass")
hygiene_path = REV/"watermark_inspection.json"
if hygiene_path.exists() and not json.loads(hygiene_path.read_text(encoding="utf-8")).get("all_text_checks_passed"):
    issues.append("Text hygiene inspection remains unresolved")
report = {"revision": baseline["revision"], "passed": not issues, "issues": issues,
          "actual_inputs": {k:[p.relative_to(ROOT).as_posix() for p in v] for k,v in graphs.items()},
          "graphics": sorted(resources), "labels": len(labels), "references": len(refs), "cited_keys": len(cites),
          "protected_files": len(baseline["protected_sha256"]), "protected_changed": protected_changed,
          "snapshot_files": len(baseline["snapshot"]), "snapshot_changed": snapshot_changed,
          "pdfs": pdfs, "markdown_checked": markdown_checked,
          "experiment_validation_file": "experiments_validation.json", "proof_preservation": proof,
          "new_comparison_experiments": False, "new_theoretical_results": False,
          "public_release_url_verified": False,
          "scope": "Editorial migration, source contracts, saved numerical data, code semantics, bibliography and build checks; not independent verification of all proofs."}
(REV/"validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"passed": not issues, "issues": issues, "pdfs": pdfs, "protected_files": len(baseline["protected_sha256"])}, ensure_ascii=False))
if issues:
    raise SystemExit(1)
