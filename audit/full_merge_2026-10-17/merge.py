"""Make one self-contained TeX entry, preserving the current two-file baseline."""
from pathlib import Path
import hashlib,json,re,shutil

AUDIT=Path(__file__).resolve().parent
ROOT=AUDIT.parent.parent
BEFORE=AUDIT/'before'
if BEFORE.exists():
    raise SystemExit('The pre-merge snapshot already exists; refusing to overwrite it.')
BEFORE.mkdir()
names=['manuscript.tex','supplement.tex','manuscript.pdf','supplement.pdf',
       'references.bib','README.md','build.ps1','revision2/build_papers.py',
       'revision2/integrate.py','revision2/check_sources.py']
hashes={}
for name in names:
    src=ROOT/name
    dst=BEFORE/name
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
    hashes[name]=hashlib.sha256(src.read_bytes()).hexdigest()
main=(BEFORE/'manuscript.tex').read_text(encoding='utf-8')
supp=(BEFORE/'supplement.tex').read_text(encoding='utf-8')
main_end=main.index(r'\bibliographystyle{plainnat}')
supp_start=supp.index(r'\begin{document}')+len(r'\begin{document}')
supp_body=supp[supp_start:supp.index(r'\bibliographystyle{plainnat}')].strip()
assert supp_body.startswith(r'\maketitle')
supp_body=supp_body[len(r'\maketitle'):].lstrip()
main_body=main[:main_end].rstrip()
main_body=main_body.replace(r'\usepackage{xr-hyper}'+'\n','')
main_body=re.sub(r'^\\externaldocument.*\n','',main_body,flags=re.M)
main_body=main_body.replace(r'\usepackage{graphicx,booktabs,array,enumitem,setspace,placeins}',
                            r'\usepackage{graphicx,booktabs,array,enumitem,setspace,placeins,longtable}')
main_body=main_body.replace(r'\maketitle',
    r'\maketitle'+'\n'+r'\addtocontents{toc}{\protect\setcounter{tocdepth}{-1}}',1)
main_body=main_body.replace(r'\section*{Data and code availability}',
    r'\section*{Data and code availability}'+'\n'+r'\enlargethispage{\baselineskip}',1)
supp_body=supp_body.replace(r'\tableofcontents',
    r'\renewcommand{\contentsname}{Supplementary contents}'+'\n'+
    r'\addtocontents{toc}{\protect\setcounter{tocdepth}{2}}'+'\n'+r'\tableofcontents',1)
boundary=r"""

% ============================================================================
% BEGIN MERGED SUPPLEMENTARY MATERIAL
% ============================================================================
\FloatBarrier
\clearpage
\setcounter{section}{0}
\setcounter{equation}{0}
\setcounter{figure}{0}
\setcounter{table}{0}
\setcounter{algorithm}{0}
\setcounter{page}{1}
\renewcommand{\thesection}{S\arabic{section}}
\renewcommand{\theequation}{S\arabic{equation}}
\renewcommand{\thefigure}{S\arabic{figure}}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thealgorithm}{S\arabic{algorithm}}
\renewcommand{\thepage}{S-\arabic{page}}
\renewcommand{\theHsection}{supp.\arabic{section}}
\renewcommand{\theHsubsection}{\theHsection.\arabic{subsection}}
\renewcommand{\theHsubsubsection}{\theHsubsection.\arabic{subsubsection}}
\renewcommand{\theHequation}{supp.\arabic{equation}}
\renewcommand{\theHfigure}{supp.\arabic{figure}}
\renewcommand{\theHtable}{supp.\arabic{table}}
\providecommand{\theHalgorithm}{}
\renewcommand{\theHalgorithm}{supp.\arabic{algorithm}}
\renewcommand{\theHtheorem}{\theHsection.\arabic{theorem}}
\phantomsection
\pdfbookmark[0]{Supplementary material}{supplementary-material}
\begin{center}
{\Large\bfseries Supplementary material\par}
\medskip
{\large The Cost of Reliable Near-Optimal Set Maintenance\\with Arriving Arms\par}
\end{center}
\medskip

"""
merged=main_body+boundary+supp_body+r"""

% END MERGED SUPPLEMENTARY MATERIAL
\FloatBarrier
\bibliographystyle{plainnat}
\bibliography{references}
\end{document}
"""
labels=lambda s:re.findall(r'\\label\{([^}]+)\}',s)
original_labels=labels(main)+labels(supp)
assert len(original_labels)==len(set(original_labels))
assert set(original_labels)==set(labels(merged))
assert merged.count(r'\documentclass')==1
assert merged.count(r'\begin{document}')==1
assert merged.count(r'\end{document}')==1
assert not re.search(r'\\(?:input|include|externaldocument)\s*(?:\[|{)',merged)
(ROOT/'manuscript.tex').write_text(merged,encoding='utf-8',newline='\n')
report={'before_sha256':hashes,'retained_labels':len(original_labels),
        'numbered_sections':len(re.findall(r'\\section\{',merged)),
        'manuscript_lines':len(merged.splitlines()),
        'bibliographies':merged.count(r'\bibliography{references}'),
        'editable_entry':'manuscript.tex',
        'archival_source_directory':str(BEFORE),
        'manuscript_sha256':hashlib.sha256((ROOT/'manuscript.tex').read_bytes()).hexdigest()}
(AUDIT/'merge-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
