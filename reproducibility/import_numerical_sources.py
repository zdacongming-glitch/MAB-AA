"""Consolidate supplied numerical research sources without altering originals."""
from pathlib import Path
import csv, gzip, hashlib, json, shutil, zipfile

PROJECT=Path(__file__).resolve().parents[1]
REPO=PROJECT.parent
OUT=Path(__file__).resolve().parent
SKIP={'__pycache__','.git','.pytest_cache','.numba_cache'}
EXTERNAL=Path('D:/博士学习/科研/Projects/Bandit with Arriving Arms/simulation_final')

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def files(p):
    return sorted(x for x in p.rglob('*') if x.is_file() and not SKIP.intersection(x.parts))

def planned():
    jobs=[]
    for name,dest in [('CCP_research_2026-10-16','ccp_frozen'),('frontier_research_2026-10-16','frontier_frozen'),('F-CCP_2026-10-17','fccp_frozen')]:
        src=REPO/name
        for f in files(src): jobs.append((f,PROJECT/'experiments'/dest/f.relative_to(src),'byte-copy',name,f.relative_to(src).as_posix()))
    arc=PROJECT/'experiments/original_submission_archive'
    for f in files(EXTERNAL):
        rel=f.relative_to(EXTERNAL)
        if f.parent==EXTERNAL:
            dest=arc/'source'/f.name
        elif rel.as_posix().startswith('outputs/final/scenario_'):
            dest=arc/Path(*rel.parts[2:])
        elif rel.as_posix()=='outputs/final/summary.json':
            dest=arc/'original_summary.json'
        else: continue
        kind='gzip-lossless' if f.name=='raw_checkpoint.csv' else 'byte-copy'
        if kind=='gzip-lossless': dest=dest.with_suffix(dest.suffix+'.gz')
        jobs.append((f,dest,kind,'original_submission',rel.as_posix()))
    return jobs

def decompressed_sha(path):
    h=hashlib.sha256(); size=0
    with gzip.open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block); size+=len(block)
    return h.hexdigest(),size

def main():
    jobs=planned()
    # Validate every existing destination before making the first mutation.
    for src,dst,kind,study,rel in jobs:
        dst.resolve().relative_to(PROJECT.resolve())
        if dst.exists():
            actual=decompressed_sha(dst)[0] if kind=='gzip-lossless' else sha(dst)
            if actual!=sha(src): raise RuntimeError(f'Refusing unequal existing destination: {dst}')
    records=[]
    for src,dst,kind,study,rel in jobs:
        original_sha=sha(src); existed=dst.exists()
        dst.parent.mkdir(parents=True,exist_ok=True)
        if not existed:
            if kind=='gzip-lossless':
                temp=dst.with_name(dst.name+'.tmp')
                with src.open('rb') as i,temp.open('wb') as o:
                    with gzip.GzipFile(filename='',mode='wb',fileobj=o,mtime=0,compresslevel=9) as z:
                        shutil.copyfileobj(i,z,1024*1024)
                temp.replace(dst)
            else: shutil.copyfile(src,dst)
        final_sha=sha(dst)
        if kind=='gzip-lossless':
            uncompressed_sha,uncompressed_bytes=decompressed_sha(dst)
            assert uncompressed_sha==original_sha and uncompressed_bytes==src.stat().st_size
            print(f'Lossless gzip verified: {rel}, {src.stat().st_size} -> {dst.stat().st_size} bytes',flush=True)
        else: assert final_sha==original_sha
        assert sha(src)==original_sha
        records.append(dict(study=study,source=str(src),source_relative=rel,destination=dst.relative_to(PROJECT).as_posix(),operation=kind,source_bytes=src.stat().st_size,source_sha256=original_sha,destination_bytes=dst.stat().st_size,destination_sha256=final_sha,already_present=existed,verified=True))
    archive_parity=[]
    for p in sorted((PROJECT/'experiments/fccp_frozen/original-archives').glob('*.zip')):
        with zipfile.ZipFile(p) as z:
            names=[n for n in z.namelist() if not n.endswith('/')]
            for n in names:
                assert sha(REPO/n)==hashlib.sha256(z.read(n)).hexdigest(),n
        archive_parity.append(dict(path=p.relative_to(PROJECT).as_posix(),sha256=sha(p),member_count=len(names),all_members_match_original_source=True))
    result=dict(date='2026-10-17',scope='Exact consolidation of existing numerical sources and frozen data; no new numerical performance simulations',originals_unchanged=True,compression='gzip with empty embedded filename, mtime=0, compression level 9; decompressed size and SHA-256 checked against original',source_files=len(records),new_files=sum(not r['already_present'] for r in records),files=records,original_zip_parity=archive_parity,known_history_limit='The failed initial F17 compilation engine hash is not preserved; all valid-stage frozen code hashes are available in src or source_snapshots. Failed compilation is not a completed result.')
    (OUT/'numerical-import-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(files=len(records),new_files=result['new_files'],bytes=sum(r['destination_bytes'] for r in records)),indent=2),flush=True)

if __name__=='__main__': main()
