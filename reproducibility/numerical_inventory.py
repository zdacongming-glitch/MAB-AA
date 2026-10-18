"""Read-only inventory of the numerical dependency closure (no simulations)."""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, re, zipfile

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parent
OUT = Path(__file__).resolve().parent
EXCLUDED_PARTS = {'__pycache__', '.git', '.pytest_cache', '.numba_cache'}

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def files(p):
    return sorted(x for x in p.rglob('*') if x.is_file() and not EXCLUDED_PARTS.intersection(x.parts))

def describe(p):
    ff = files(p)
    return dict(path=str(p), files=len(ff), bytes=sum(f.stat().st_size for f in ff), extensions=dict(Counter(f.suffix or '<none>' for f in ff)))

def rows(p):
    with p.open(encoding='utf-8', newline='') as f: return sum(1 for _ in csv.DictReader(f))

def compare(source, destination):
    ss=files(source); missing=[]; unequal=[]; matched=[]
    for f in ss:
        rel=f.relative_to(source); d=destination/rel
        info=dict(relative=rel.as_posix(), bytes=f.stat().st_size, sha256=sha(f))
        if not d.is_file(): missing.append(info)
        elif sha(d)!=info['sha256']: unequal.append(info)
        else: matched.append(info)
    return dict(source=str(source), destination=str(destination), matched=len(matched), missing=missing, unequal=unequal)

def main():
    studies=[('C16','CCP_research_2026-10-16','experiments/ccp_2026-10-16'),('P16','frontier_research_2026-10-16','experiments/frontier_2026-10-16'),('F17','F-CCP_2026-10-17','experiments/fccp_frozen')]
    comparisons={k: compare(REPO/src,PROJECT/dest) for k,src,dest in studies}
    archives=[]
    for p in files(PROJECT/'experiments/fccp_frozen/original-archives'):
        if p.suffix!='.zip': continue
        with zipfile.ZipFile(p) as z:
            entries=[n for n in z.namelist() if not n.endswith('/')]
            roots=sorted({n.split('/')[0] for n in entries})
            archives.append(dict(path=p.relative_to(PROJECT).as_posix(),bytes=p.stat().st_size,sha256=sha(p),members=len(entries),member_roots=roots))
    package_sources=[]
    for p in files(REPO/'proposal'):
        if p.suffix in {'.py','.csv','.npz','.json','.zip'}:
            package_sources.append(dict(relative=p.relative_to(REPO).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    external=Path('D:/博士学习/科研/Projects/Bandit with Arriving Arms/simulation_final')
    historical=[]
    if external.is_dir():
        for f in files(external):
            if 'outputs/final' not in f.as_posix() and f.parent != external: continue
            historical.append(dict(source=str(f),relative=f.relative_to(external).as_posix(),bytes=f.stat().st_size,sha256=sha(f)))
    data_paths=[('CP legacy',PROJECT/'experiments/results/runs.csv'),('C16',REPO/'CCP_research_2026-10-16/test-results.csv'),('P16',REPO/'frontier_research_2026-10-16/holdout-all.csv'),('F17 original',PROJECT/'experiments/fccp_frozen/results/holdout-all.csv'),('F17 corrected ALL',PROJECT/'experiments/fccp_frozen/results/matched-all-all.csv')]
    datasets=[dict(study=s,path=str(p),rows=rows(p),bytes=p.stat().st_size,sha256=sha(p)) for s,p in data_paths]
    active_artifacts=re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', (PROJECT/'manuscript.tex').read_text(encoding='utf-8'))
    data=dict(scope='Read-only numerical inventory; no comparative simulation run',project=str(PROJECT),datasets=datasets,comparisons=comparisons,original_archives=archives,proposal_computational_files=package_sources,original_submission_external_files=historical,main_tex_figures=[dict(path=p,present=(PROJECT/p).is_file()) for p in active_artifacts],root_studies=[describe(REPO/s) for _,s,_ in studies])
    (OUT/'numerical-inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(datasets=datasets,comparisons={k:dict(matched=v['matched'],missing=len(v['missing']),unequal=len(v['unequal'])) for k,v in comparisons.items()},proposal_files=len(package_sources),external_files=len(historical)),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
