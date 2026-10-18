"""Inline reviewed revision blocks into the two complete submission sources.

The JSON files are a revision record, not TeX compilation dependencies.
Normal editing and compilation require only manuscript.tex/supplement.tex.
"""
from pathlib import Path
import json,re

REV = Path(__file__).resolve().parent
ROOT = REV.parent

def read(name):
    return json.loads((REV / name).read_text(encoding='utf-8'))

editorial = read('editorial_main.json')
method = read('fccp_method.json')
retained = read('retained_supplement.json')
numerical = read('numerical_sections.json')
main = ''.join([
    editorial['header'], editorial['introduction'], editorial['model'],
    method['main_section'], editorial['costs'],
    editorial['temporary_tasks'], numerical['main_section'], editorial['ending'],
])
supp = retained['header'] + retained['s1']
for number in range(2, 18):
    if number <= 4:
        supp += method[f'supplement_s{number}']
    elif number in (15, 16):
        supp += numerical[f'supplement_s{number}']
    else:
        supp += retained[f's{number}']
supp += '\n\\FloatBarrier\n\\bibliographystyle{plainnat}\n\\bibliography{references}\n\\end{document}\n'
# Keep the historical main-section cross-reference while naming the new rule.
main = main.replace('\\label{sec:fccp}', '\\label{sec:fccp}\\label{sec:method}', 1)
main = main.replace('with $n_k<q_k$ and a positive planned increment.',
                    'with $n_k<q_k$ and $x_k>n_k$ (using the actual count).')
supp = supp.replace('\\section{Earlier checkpoint comparison}',
                    '\\section{Earlier checkpoint comparison}\\label{sec:legacy-checkpoint-study}', 1)
supp = supp.replace('\\usepackage{graphicx,booktabs,array,enumitem,setspace,placeins}',
                    '\\usepackage{graphicx,booktabs,array,enumitem,setspace,placeins,longtable}')
supp = supp.replace('\\begin{document}',
                    '\\externaldocument[][nocite]{build/manuscript}[manuscript.pdf]\n\\begin{document}', 1)
toc_settings = r'''
\makeatletter
\renewcommand{\@pnumwidth}{2.8em}
\renewcommand{\@tocrmarg}{3.8em}
\renewcommand{\l@section}{\@dottedtocline{1}{0em}{3em}}
\renewcommand{\l@subsection}{\@dottedtocline{2}{1.5em}{4em}}
\renewcommand{\l@subsubsection}{\@dottedtocline{3}{3.8em}{5em}}
\makeatother
'''
supp = supp.replace('\\tableofcontents',toc_settings+'\\tableofcontents',1)
# Inline numerical tuples may wrap between means without changing any values.
supp = re.sub(r'\$\(([0-9., ]+)\)\$',
              lambda m:'$('+m[1].replace(', ',r',\allowbreak ')+')$',supp)
# Temperature and the environment index have distinct symbols.
for old,new in [(r'\theta\in\Theta',r'\vartheta\in\Theta'),
                (r'_\theta',r'_\vartheta')]:
    main=main.replace(old,new)
    supp=supp.replace(old,new)
main=main.replace(r'\Theta_{\rm ABM}',r'\Theta_H')
main=main.replace('F-R & $1$ (inactive)', 'F-R & inactive')
main=main.replace('This is not the linear-overhead claim\nfor the older checkpoint witness. ', '')
main=main.replace('the fact that MC-MOSS itself has small regret would not suffice.',
                  'the potential-prefix bounds apply to the actual sequence of selected actions.')
main=main.replace('The five reward comparators are UCB1, Growing-MOSS, MC-MOSS, Thompson sampling and KL-UCB.',
                  r'The five reward comparators are UCB1, Growing-MOSS, MC-MOSS, Thompson sampling and KL-UCB \citep{garivier2011klucb}.')
supp=supp.replace('Arms 0 and 1 arrive at time 1. Define',
                  r'Let $\Theta$ be the two sign environments specified above. Arms 0 and 1 arrive at time 1. Define',1)
# Page review: keep the method algorithm ahead of its guarantees and avoid
# short theorem fragments, an empty legacy wrapper, and forward float leaks.
main=main.replace('\\begin{algorithm}[p]', '\\begin{algorithm}[tbp]',1)
main=main.replace('\\subsection{Reliability, reward protection, and service completion}',
                  '\\FloatBarrier\n\\subsection{Reliability, reward protection, and service completion}',1)
supp=supp.replace('\\begin{lemma}[Distinct arm--count pairs]',
                  '\\Needspace{11\\baselineskip}\n\\begin{lemma}[Distinct arm--count pairs]',1)
supp=supp.replace('\\subsection{Recovery of an arbitrary number of coordinates}',
                  '\\Needspace{18\\baselineskip}\n\\subsection{Recovery of an arbitrary number of coordinates}',1)
supp=supp.replace('\\section{Main numerical protocol and full results}',
                  '\\FloatBarrier\n\\section{Main numerical protocol and full results}',1)
supp=supp.replace('\\subsection{Computational details of the earlier experiment}\n\\label{app:computation}\n\n\\subsection{Configuration, records, and implementation names}',
                  '\\subsection{Configuration, records, and implementation names}\n\\label{app:computation}',1)
supp=supp.replace('Table~\\ref{tab:simulation} displays six methods; the cost--area figure and\nTable~\\ref{tab:allocation} include all nine. The additional path figure\nbelow uses the same six methods as Figure~\\ref{fig:paths}.',
                  'The six methods in Table~\\ref{tab:simulation} appear in both path\nfigures. The cost--area figure and Table~\\ref{tab:allocation} include all nine.')
for name, source in [('manuscript.tex', main), ('supplement.tex', supp)]:
    (ROOT / name).write_text(source, encoding='utf-8', newline='\n')
print(json.dumps({'manuscript_lines': len(main.splitlines()),
                  'supplement_lines': len(supp.splitlines())}))
