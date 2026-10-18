"""Record actual final build, source, input-integrity and numerical-table checks."""
from pathlib import Path
import collections,csv,hashlib,json,re,subprocess,unicodedata

REV=Path(__file__).resolve().parent
ROOT=REV.parent
REPO=ROOT.parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

source_map=json.loads((REV/'source-map.json').read_text(encoding='utf-8'))
protected=source_map['protected_sha256']
changed=[name for name,sha in protected.items()
         if not (REPO/name).is_file() or digest(REPO/name)!=sha]
release=json.loads((REV/'analysis/release-manifest.json').read_text(encoding='utf-8'))
copy_failures=[entry['destination'] for entry in release['files']
               if digest(ROOT/entry['destination'])!=entry['sha256']]
texts={stem:(ROOT/f'{stem}.tex').read_text(encoding='utf-8')
       for stem in ['manuscript','supplement']}
def inventory(source):
    return {'labels':re.findall(r'\\label\{([^}]+)\}',source),
            'references':re.findall(r'\\(?:eqref|ref|pageref)\{([^}]+)\}',source),
            'citation_groups':re.findall(r'\\cite\w*(?:\[[^\]]*\])*\{([^}]+)\}',source),
            'graphics':re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',source),
            'tex_inputs':re.findall(r'\\(?:input|include)\s*\{([^}]+)\}',source),
            'bibliography':re.findall(r'\\bibliography\{([^}]+)\}',source)}
source_map['baseline_tex_inventory']={stem:inventory((REV/'baseline'/f'{stem}.tex').read_text(encoding='utf-8')) for stem in texts}
source_map['current_tex_inventory']={stem:inventory(source) for stem,source in texts.items()}
assets=set(path for entry in source_map['current_tex_inventory'].values() for path in entry['graphics'])
source_map['current_graphics']={path:{'absolute_path':str(ROOT/path),'sha256':digest(ROOT/path)} for path in sorted(assets)}
source_map['build_entry']='python revision2/build_papers.py (pdfLaTeX/BibTeX/latexmk, build/ output, two cross-document passes)'
(REV/'source-map.json').write_text(json.dumps(source_map,ensure_ascii=False,indent=2),encoding='utf-8')
label_pattern=r'\\label\{([^}]+)\}'
new_labels=set(re.findall(label_pattern,'\n'.join(texts.values())))
preservation={stem:sorted(set(re.findall(label_pattern,(REV/'baseline'/f'{stem}.tex').read_text(encoding='utf-8')))-new_labels)
              for stem in texts}
records=json.loads((REV/'analysis/inline-table-record.json').read_text(encoding='utf-8'))
table_rows={}
for group,rows in records.items():
    missing=[]
    for row in rows:
        row=list(row)
        if row[0]=='F-R' and len(row)==4:
            row[1]='inactive'
        exact=' & '.join(row)+r' \\'
        if exact not in texts['manuscript']:
            missing.append(row)
    table_rows[group]={'rows':len(rows),'missing':missing}
numeric=json.loads((REV/'numerical_sections.json').read_text(encoding='utf-8'))
table_pattern=r'\\begin\{(tabular|longtable)\}.*?\\end\{\1\}'
numerical_table_checks=[]
for key,source in numeric.items():
    destination=texts['manuscript'] if key=='main_section' else texts['supplement']
    blocks=[match.group(0) for match in re.finditer(table_pattern,source,re.S)]
    missing=[index for index,block in enumerate(blocks)
             if block.replace('F-R & $1$ (inactive)','F-R & inactive') not in destination]
    numerical_table_checks.append({'block':key,'tables':len(blocks),'missing_indices':missing})
pdfs={}
for stem in texts:
    info=subprocess.run(['pdfinfo',f'{stem}.pdf'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',check=True)
    (REV/'build-logs'/f'final-{stem}-pdfinfo.txt').write_text(info.stdout,encoding='utf-8')
    pages=int(re.search(r'^Pages:\s+(\d+)',info.stdout,re.M)[1])
    log=(ROOT/'build'/f'{stem}.log').read_text(encoding='utf-8',errors='replace')
    problems=[line for line in log.splitlines()
              if any(token in line for token in ['undefined','multiply defined','Overfull','Too large','! LaTeX Error'])]
    pdfs[stem]={'pages':pages,'bytes':(ROOT/f'{stem}.pdf').stat().st_size,
                'pdf_sha256':digest(ROOT/f'{stem}.pdf'),
                'tex_sha256':digest(ROOT/f'{stem}.tex'),
                'root_matches_build_pdf':digest(ROOT/f'{stem}.pdf')==digest(ROOT/'build'/f'{stem}.pdf'),
                'final_log_problems':problems}
md_files=[ROOT/'README.md',ROOT/'experiments/fccp_frozen/README_release.md']
md_files += [p for p in REV.rglob('*.md') if not any(x in p.relative_to(REV).parts for x in ['baseline','baseline-build'])]
bad_md=[str(p.relative_to(ROOT)) for p in md_files
        if re.search(r'\\[()\[\]]',p.read_text(encoding='utf-8-sig'))]
bib=(ROOT/'references.bib').read_text(encoding='utf-8')
bib_controls=[{'offset':index,'codepoint':f'U+{ord(char):04X}'} for index,char in enumerate(bib)
              if unicodedata.category(char) in ('Cf','Co') or (unicodedata.category(char)=='Cc' and char not in '\n\r\t')]
status=subprocess.run(['git','status','--porcelain=v1'],cwd=REPO,capture_output=True,text=True,encoding='utf-8',errors='replace',check=True)
claim_rows=list(csv.DictReader((REV/'claim-map.csv').open(encoding='utf-8-sig',newline='')))
report={'scope':'editorial integration and existing-result/interface checks; no new performance experiment or theorem',
        'protected_files_checked':len(protected),'protected_files_changed_or_missing':changed,
        'release_copies_checked':len(release['files']),'release_copy_failures':copy_failures,
        'baseline_labels_missing':preservation,
        'primary_inline_rows':table_rows,'all_numerical_tables':numerical_table_checks,
        'pdfs':pdfs,'claim_map_rows':len(claim_rows),
        'markdown_files_checked':len(md_files),'markdown_delimiter_problems':bad_md,
        'bib_invisible_control_findings':bib_controls,'git_status':status.stdout,
        'visual_review_reports':['page-review/manuscript-pages-01-25-review.md',
                                 'page-review/supplement-pages-01-36-review.md',
                                 'page-review/supplement-pages-37-64-review.md']}
passed=(not changed and not copy_failures and not any(preservation.values()) and
        not any(v['missing'] for v in table_rows.values()) and
        not any(v['missing_indices'] for v in numerical_table_checks) and
        not any(v['final_log_problems'] or not v['root_matches_build_pdf'] for v in pdfs.values()) and
        not bad_md and not bib_controls)
report['status']='passed' if passed else 'failed'
(REV/'final-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if passed else 1)
