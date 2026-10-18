"""Check source expansion, document identity, and unchanged numerical assets."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from PIL import Image

ARCHIVE=Path(__file__).resolve().parent
ROOT=ARCHIVE.parents[1]
manifest=json.loads((ARCHIVE/"merge_manifest.json").read_text(encoding="utf-8"))
issues=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={"documents":{},"issues":issues}
for stem in ["manuscript","supplement"]:
    source=(ROOT/f"{stem}.tex").read_text(encoding="utf-8")
    expected=(ARCHIVE/f"{stem}_expanded_before.txt").read_text(encoding="utf-8").replace("revision_2026-10-16/build/supplement","build/supplement")
    exact=source==expected
    if not exact:issues.append(f"Expanded source differs: {stem}")
    if re.search(r"\\(?:input|include)(?![a-zA-Z])",source):issues.append(f"External TeX input remains: {stem}")
    if source.count(r"\documentclass")!=1 or source.count(r"\end{document}")!=1:issues.append(f"Invalid standalone document: {stem}")
    before=(ARCHIVE/"baseline_compiled"/f"{stem}.pdf").relative_to(ROOT)
    after=Path(f"{stem}.pdf")
    extract=lambda path:subprocess.run(["pdftotext","-layout",str(path),"-"],cwd=ROOT,capture_output=True,check=True).stdout
    text_same=extract(before)==extract(after)
    if not text_same:issues.append(f"PDF text/layout differs: {stem}")
    images={}
    for kind,pdf in [("before",before),("after",after)]:
        folder=ARCHIVE/f"render_{kind}"
        folder.mkdir(exist_ok=True)
        subprocess.run(["pdftoppm","-r","72","-png",str(pdf),str((folder/stem).relative_to(ROOT))],cwd=ROOT,capture_output=True,check=True)
        pages=sorted(folder.glob(f"{stem}-*.png"))
        images[kind]=[hashlib.sha256(Image.open(p).convert("RGB").tobytes()).hexdigest() for p in pages]
    equal_pixels=images["before"]==images["after"]
    if not equal_pixels:issues.append(f"Rendered pages differ: {stem}")
    log=(ROOT/"build"/f"{stem}.log").read_text(encoding="utf-8",errors="replace")
    warnings=[line for line in log.splitlines() if re.search(r"Warning|Overfull|Underfull|undefined|multiply defined",line)]
    if warnings:issues.append(f"Build warnings: {stem}: {warnings}")
    report["documents"][stem]={"source_expansion_exact":exact,"all_tex_inline":True,"lines":len(source.splitlines()),"pages":len(images["after"]),"pdf_text_and_layout_equal":text_same,"every_page_pixel_equal":equal_pixels,"pdf_sha256":sha(ROOT/after),"source_sha256":sha(ROOT/f"{stem}.tex"),"build_warnings":warnings}

for name,digest in manifest["protected_sha256"].items():
    if not (ROOT/name).is_file() or sha(ROOT/name)!=digest:issues.append(f"Numerical asset changed: {name}")
for name,digest in manifest["snapshot_sha256"].items():
    if sha(ARCHIVE/"before"/name)!=digest:issues.append(f"Original source backup changed: {name}")
for name in ["README.md","experiments/README.md"]:
    fenced=False;displays=0
    for number,line in enumerate((ROOT/name).read_text(encoding="utf-8").splitlines(),1):
        if line.lstrip().startswith(("```","~~~")):fenced=not fenced;continue
        if fenced:continue
        if re.search(r"\\[()\[\]]",line):issues.append(f"Markdown delimiter: {name}:{number}")
        if "$$" in line:
            displays+=line.count("$$")
            if line.strip()!="$$":issues.append(f"Markdown display delimiter: {name}:{number}")
    if displays%2:issues.append(f"Unmatched Markdown display: {name}")
report["protected_numerical_files_unchanged"]=len(manifest["protected_sha256"])
report["passed"]=not issues
(ARCHIVE/"verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False))
if issues:raise SystemExit(1)
