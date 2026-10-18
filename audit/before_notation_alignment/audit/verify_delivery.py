from pathlib import Path
import csv,hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
issues=[]; markdown=[]
for p in sorted(ROOT.rglob('*.md')):
    text=p.read_text(encoding='utf-8-sig'); inside=False; displays=0
    for number,line in enumerate(text.splitlines(),1):
        if line.lstrip().startswith(('```','~~~')): inside=not inside;continue
        if inside: continue
        if re.search(r'\\[()\[\]]',line): issues.append(f'{p.relative_to(ROOT)}:{number}: forbidden Markdown math delimiter')
        if '$$' in line:
            if line.strip()!='$$': issues.append(f'{p.relative_to(ROOT)}:{number}: display delimiter not standalone')
            displays+=line.count('$$')
    if displays%2:issues.append(f'{p.relative_to(ROOT)}: unmatched display delimiter')
    markdown.append({'file':p.relative_to(ROOT).as_posix(),'display_delimiters':displays})
manifest=json.loads((ROOT/'assessments'/'final_manifest.json').read_text())
merge_path=ROOT/'audit'/'section_merge.json'
merge=json.loads(merge_path.read_text(encoding='utf-8')) if merge_path.exists() else None
if merge and sha(ROOT/'manuscript.tex')!=merge['merged_manuscript_sha256']:
    issues.append('Manuscript changed after the recorded section merge')
for name,digest in manifest['source_files'].items():
    # Frozen assessments describe the pre-merge layout. Check those source
    # snapshots separately from the merged manuscript; do not rewrite history.
    source=ROOT/name
    if merge and name in merge['original_source_sha256']:
        source=ROOT/merge['backup_directory']/name
        if not source.is_file() or sha(source)!=merge['original_source_sha256'][name]:
            issues.append(f'Section merge backup changed or missing: {name}')
    if not source.is_file() or sha(source)!=digest:issues.append(f'Frozen final evidence changed: {name}')
for name,digest in manifest['files'].items():
    if sha(ROOT/'assessments'/name)!=digest:issues.append(f'Frozen packet changed: {name}')
rows=list(csv.DictReader((ROOT/'experiments'/'results'/'runs.csv').open(encoding='utf-8')))
if len(rows)!=5760:issues.append('Expected 5760 recorded production runs')
if len({(r['scenario'],r['seed'],r['method']) for r in rows})!=5760:issues.append('Duplicate/missing production keys')
run_manifest=json.loads((ROOT/'experiments'/'results'/'manifest.json').read_text())
for key,name in [('runner_sha256','run_experiments.py'),('source_sha256','reference_cp_ucb_aa.py')]:
    if sha(ROOT/'experiments'/name)!=run_manifest[key]:issues.append(f'Experiment source hash mismatch: {name}')
for key,name in [('config_sha256','config.json'),('runs_sha256','runs.csv'),('paths_sha256','paths.npz')]:
    if sha(ROOT/'experiments'/'results'/name)!=run_manifest[key]:issues.append(f'Experiment result hash mismatch: {name}')
source=ROOT.parent/'proposal'/'ucbaa_continuous_maintenance_2026-10-14'
inventory={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(source.iterdir()) if p.is_file()}
known={'持续集合维护_理论与完整证明.md':'1fb396aac5a827d661a1fc87988f8126a454eb22eca1125a37fa8b74b6a73257',
       'cp_ucb_aa.py':'272815cbb45e2de1a99f849bd4718892ef6bc010d081e0eaf2ec45b21c746ef9'}
for name,digest in known.items():
    if inventory[name]['sha256']!=digest:issues.append(f'Original source changed: {name}')
original=ROOT.parent/'JASA-template'/'mab_aa_main.pdf'
if sha(original)!='44c19acf42498b41179ae52d2a0951a004c76c834b2eb244c22fc1b05135fb8e':issues.append('Original PDF changed')
report={'passed':not issues,'issues':issues,'markdown_files_checked':markdown,
        'production_runs':len(rows),'final_packet_id':manifest['packet_id'],
        'original_source_inventory':inventory,'original_pdf_sha256':sha(original)}
(ROOT/'audit'/'delivery_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':not issues,'issues':issues,'markdown_files':len(markdown),'production_runs':len(rows)},ensure_ascii=False))
if issues: raise SystemExit(1)
