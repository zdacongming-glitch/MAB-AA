"""Freeze current two-file manuscript and all read-only research inputs."""
from pathlib import Path
import hashlib,json,shutil,subprocess

REV=Path(__file__).resolve().parent
ROOT=REV.parent
REPO=ROOT.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
target=REV/'source-map.json'
if target.exists():raise SystemExit('Input freeze already exists; refusing overwrite')
baseline={}
for name in ['manuscript.tex','supplement.tex','manuscript.pdf','supplement.pdf','references.bib','README.md','build.ps1']:
    src=ROOT/name;dst=REV/'baseline'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    baseline[name]={'path':str(src),'snapshot':str(dst),'sha256':sha(src),'bytes':src.stat().st_size}
protected={}
research={}
for name,role in [('CCP_research_2026-10-16','C16'),('frontier_research_2026-10-16','P16'),('F-CCP_2026-10-17','F17'),('reconstruction_jasa_stage2_2026-10-13','G'),('reconstruction_jasa_2026-10-13','G-prior')]:
    folder=REPO/name
    research[role]={'path':str(folder),'files':{}}
    for path in folder.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            rel=path.relative_to(REPO).as_posix();digest=sha(path);protected[rel]=digest
            research[role]['files'][path.relative_to(folder).as_posix()]=digest
for folder in [ROOT/'experiments',ROOT/'figures']:
    for path in folder.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:protected[path.relative_to(REPO).as_posix()]=sha(path)
plan=REPO/'proposal/第二轮稿件修改_FCCP整合_Codex执行方案_v2.0.md'
mapping={'revision':'fccp-integration-2026-10-17-v2','project':str(ROOT),'plan':str(plan),'plan_sha256':sha(plan),'baseline':baseline,'research':research,'protected_sha256':protected,'git_status':subprocess.run(['git','status','--short'],cwd=REPO,capture_output=True,encoding='utf-8').stdout,'source_structure':'Only manuscript.tex and supplement.tex are editable TeX. Draft exchanges use JSON or text, never new TeX components.'}
target.write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'baseline_pdfs':{k:v['sha256'] for k,v in baseline.items() if k.endswith('.pdf')},'protected_files':len(protected),'research_files':{k:len(v['files']) for k,v in research.items()}},ensure_ascii=False))
