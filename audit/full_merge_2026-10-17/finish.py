"""Archive the retired entry and verify the current single-file publication."""
from pathlib import Path
import hashlib,json,re,subprocess

AUDIT=Path(__file__).resolve().parent
ROOT=AUDIT.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((AUDIT/'merge-manifest.json').read_text(encoding='utf-8'))
source=(ROOT/'manuscript.tex').read_text(encoding='utf-8')
log=(ROOT/'build/manuscript.log').read_text(encoding='utf-8',errors='replace')
issues=[line for line in log.splitlines() if any(term in line for term in
        ['undefined','multiply defined','destination with the same','Overfull',
         'Too large','! LaTeX Error'])]
assert not issues,issues
assert sha(ROOT/'manuscript.pdf')==sha(ROOT/'build/manuscript.pdf')
assert sha(ROOT/'references.bib')==manifest['before_sha256']['references.bib']
if (ROOT/'supplement.tex').is_file():
    assert sha(ROOT/'supplement.tex')==manifest['before_sha256']['supplement.tex']
    archive=AUDIT/'retired_root_products'
    archive.mkdir(exist_ok=True)
    for path in ROOT.glob('supplement.*'):
        assert path.resolve().parent==ROOT.resolve()
        target=archive/path.name
        assert target.resolve().is_relative_to(ROOT.resolve()) and not target.exists()
        path.rename(target)
info=subprocess.run(['pdfinfo','manuscript.pdf'],cwd=ROOT,capture_output=True,
                    text=True,encoding='utf-8',errors='replace',check=True)
(AUDIT/'pdfinfo.txt').write_text(info.stdout,encoding='utf-8')
subprocess.run(['pdftotext','-layout','manuscript.pdf',
                (AUDIT/'combined-text.txt').relative_to(ROOT).as_posix()],cwd=ROOT,check=True)
text=(AUDIT/'combined-text.txt').read_text(encoding='utf-8')
pages=text.split('\f')
labels=re.findall(r'\\label\{([^}]+)\}',source)
refs=re.findall(r'\\(?:eqref|ref|pageref)\{([^}]+)\}',source)
assert len(labels)==145 and len(set(labels))==145
assert not set(refs)-set(labels)
assert source.count(r'\documentclass')==source.count(r'\begin{document}')==source.count(r'\end{document}')==1
assert source.count(r'\bibliography{references}')==1
assert not re.search(r'\\(?:input|include|externaldocument)\s*(?:\[|{)',source)
assert sorted(p.name for p in ROOT.glob('*.tex'))==['manuscript.tex']
mds=[ROOT/'README.md',*AUDIT.glob('*.md')]
bad_md=[str(p) for p in mds if re.search(r'\\[()\[\]]',p.read_text(encoding='utf-8'))]
assert not bad_md
report={'status':'passed','editable_tex_files':['manuscript.tex'],
        'pdf_pages':int(re.search(r'^Pages:\s+(\d+)',info.stdout,re.M)[1]),
        'numbered_sections':len(re.findall(r'\\section\{',source)),
        'labels_preserved':len(labels),'undefined_references':[],
        'bibliographies':1,'compile_log_issues':issues,
        'tex_sha256':sha(ROOT/'manuscript.tex'),'pdf_sha256':sha(ROOT/'manuscript.pdf'),
        'reference_database_unchanged':True,
        'supplement_start_physical_page':next(i+1 for i,p in enumerate(pages)
             if 'Supplementary material' in p and 'Notation and scope' in p),
        'archived_root_products':sorted(p.name for p in (AUDIT/'retired_root_products').iterdir()),
        'scope':'source organization, numbering and build only; no research/data changes'}
(AUDIT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
manifest.update({'manuscript_sha256':report['tex_sha256'],'pdf_sha256':report['pdf_sha256'],
                 'pdf_pages':report['pdf_pages'],'status':'passed'})
(AUDIT/'merge-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
