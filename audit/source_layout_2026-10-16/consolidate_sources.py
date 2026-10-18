"""One-time, content-preserving consolidation into the two editable TeX files."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys

ARCHIVE = Path(__file__).resolve().parent
ROOT = ARCHIVE.parents[1]
MANIFEST = ARCHIVE / "merge_manifest.json"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
pattern = re.compile(r"\\(?:input|include)\{([^}]+)\}")

def safe(path):
    path = path.resolve()
    if not path.is_relative_to(ROOT.resolve()) or path == ROOT.resolve():
        raise RuntimeError(f"Path outside manuscript workspace: {path}")
    return path

def expand(path, stack=()):
    path = safe(path)
    if path in stack:
        raise RuntimeError("Cyclic TeX dependency")
    text = path.read_text(encoding="utf-8-sig")
    def replace(match):
        name = match.group(1)
        if not Path(name).suffix:
            name += ".tex"
        return expand(ROOT/name, stack+(path,))
    return pattern.sub(replace, text)

def sources(path, found=None):
    found = set() if found is None else found
    path = safe(path)
    if path in found:
        return found
    found.add(path)
    for match in pattern.finditer(path.read_text(encoding="utf-8-sig")):
        name = match.group(1)
        sources(ROOT/(name if Path(name).suffix else name+".tex"), found)
    return found

phase = sys.argv[1]
if phase == "freeze":
    if MANIFEST.exists():
        raise SystemExit("Snapshot exists; refusing overwrite.")
    found = set().union(*(sources(ROOT/name) for name in ["manuscript.tex", "supplement.tex"]))
    extra = [ROOT/name for name in ["build.ps1", "README.md", "experiments/README.md", "references.bib", "manuscript.pdf", "supplement.pdf"]]
    frozen = {}
    for path in sorted(found|set(extra),key=str):
        name = path.relative_to(ROOT).as_posix()
        target = ARCHIVE/"before"/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
        frozen[name] = sha(path)
    for stem in ["manuscript","supplement"]:
        (ARCHIVE/f"{stem}_expanded_before.txt").write_text(expand(ROOT/f"{stem}.tex"),encoding="utf-8")
    protected = {}
    for folder in [ROOT/"experiments",ROOT/"figures"]:
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix not in {".tex",".md"} and "__pycache__" not in path.parts:
                protected[path.relative_to(ROOT).as_posix()] = sha(path)
    MANIFEST.write_text(json.dumps({"active_sources_before":[p.relative_to(ROOT).as_posix() for p in sorted(found,key=str)],"snapshot_sha256":frozen,"protected_sha256":protected},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"active_tex_before":len(found),"snapshots":len(frozen),"protected_experiment_and_figure_files":len(protected)}))

elif phase == "flatten":
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for name in manifest["active_sources_before"]:
        if sha(ROOT/name) != manifest["snapshot_sha256"][name]:
            raise SystemExit(f"Source changed after snapshot: {name}")
    moves = [(ROOT/"theory",ARCHIVE/"components/theory"),
             (ROOT/"revision_2026-10-16",ARCHIVE/"previous_revision"),
             (ROOT/"preamble.tex",ARCHIVE/"components/preamble.tex"),
             (ROOT/"experiments/results/table_main.tex",ARCHIVE/"components/experiments/results/table_main.tex"),
             (ROOT/"experiments/results/table_allocation.tex",ARCHIVE/"components/experiments/results/table_allocation.tex")]
    # Resolve every recursive move target before mutating anything.
    for source,target in moves:
        safe(source);safe(target)
        if not source.exists() or target.exists():
            raise RuntimeError(f"Move precondition failed: {source} -> {target}")
    for stem in ["manuscript","supplement"]:
        text = (ARCHIVE/f"{stem}_expanded_before.txt").read_text(encoding="utf-8")
        text = text.replace("revision_2026-10-16/build/supplement","build/supplement")
        if pattern.search(text):
            raise RuntimeError("Unexpanded input")
        (ROOT/f"{stem}.tex").write_text(text,encoding="utf-8")
    for source,target in moves:
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.move(str(source),str(target))
    script = ROOT/"build.ps1"
    text = script.read_text(encoding="utf-8")
    text = text.replace("revision_2026-10-16/build","build")
    script.write_text(text,encoding="utf-8")
    manifest["archived_paths"] = {s.relative_to(ROOT).as_posix():t.relative_to(ROOT).as_posix() for s,t in moves}
    manifest["merged_source_sha256"] = {f"{stem}.tex":sha(ROOT/f"{stem}.tex") for stem in ["manuscript","supplement"]}
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"active_tex_after":2,"archived_paths":manifest["archived_paths"]},ensure_ascii=False))
elif phase == "notes":
    (ROOT/"README.md").write_text("""# 稿件文件

直接编辑以下两个文件：

- `manuscript.tex`：正文、全部宏包与符号定义、算法和主表。
- `supplement.tex`：补充材料、全部宏包与符号定义、S1–S13证明和计算细节、分配表。

两份文件均已包含各自全部TeX源代码，没有外部分节、公共preamble或表格input。图片保存在 `figures/`，文献库为 `references.bib`；实验源和数据仍在 `experiments/`。

使用 `build.ps1` 编译；中间产物在 `build/`，生成的两份PDF同时更新到本目录。正文从 `build/supplement.aux` 自动读取附录编号，因此先编译补充材料，再编译正文。

原拆分TeX与上一轮编辑记录完整移至 `audit/source_layout_2026-10-16/`。它们只用于追溯，不再是编辑入口；不要运行历史整合脚本覆盖当前两个文件。合并记录及编译内容核对见该目录的 `merge_manifest.json` 和 `verification.json`。

本轮只整理文件组织，未改文章文字、公式、数字、算法代码或实验数据。绘图脚本的 `--figures-only` 模式不重建表格；默认模式仍可能生成表格快照，生成后须明确同步到上述两份TeX，当前稿件不会自动读取这些快照。
""",encoding="utf-8")
    note = ROOT/"experiments/README.md"
    text = note.read_text(encoding="utf-8")
    old = "- `results/table_main.tex`, `results/table_allocation.tex`: generated manuscript tables."
    new = "- The manuscript tables are now embedded directly in `../manuscript.tex` and `../supplement.tex`. The previous generated TeX snapshots were archived under `../audit/source_layout_2026-10-16/components/experiments/results/`. The plotting script can regenerate `results/table_main.tex` and `results/table_allocation.tex`; those files no longer enter manuscript compilation automatically. Use `--figures-only` to redraw without generating table snapshots."
    if old not in text:
        raise SystemExit("Expected experiment README entry not found")
    note.write_text(text.replace(old,new),encoding="utf-8")
    print("Updated the two-file editing instructions.")
else:
    raise SystemExit("Expected freeze, flatten, or notes")
