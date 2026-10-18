"""Markdown/LaTeX delimiter checks, not semantic or formal proof verification."""
from __future__ import annotations
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parent
p=root/'theory.md'
s=p.read_text(encoding='utf-8')
# Count standalone display delimiters, not the valid row spacing token \\[2mm].
opens=re.findall(r'^\\\[\s*$',s,re.M)
closes=re.findall(r'^\\\]\s*$',s,re.M)
assert len(opens)==len(closes)
assert s.count(r'\(')==s.count(r'\)')
assert s.count('```')%2==0
labels=re.findall(r'\\tag\{([^}]+)\}',s)
assert len(labels)==len(set(labels))
theorems=re.findall(r'\*\*定理 (\d+)（([^）]+)）',s)
lemmas=re.findall(r'\*\*引理 (\d+)',s)
props=re.findall(r'\*\*命题 (\d+)',s)
assert len(theorems)==len(set(x[0] for x in theorems))
assert len(lemmas)==len(set(lemmas))
assert len(props)==len(set(props))
for block in re.findall(r'^\\\[\s*\n(.*?)^\\\]\s*$',s,re.M|re.S):
    clean=re.sub(r'\\[{}]','',block)
    depth=0
    for c in clean:
        depth += (c=='{')-(c=='}')
        assert depth>=0
    assert depth==0
    stack=[]
    for begin,end in re.findall(r'\\begin\{([^}]+)\}|\\end\{([^}]+)\}',block):
        if begin:stack.append(begin)
        else:assert stack and stack.pop()==end
    assert not stack
report={"display_math_blocks":len(opens),"inline_math_pairs":s.count(r'\('),
        "unique_equation_tags":len(labels),"theorem_count":len(theorems),
        "lemma_count":len(lemmas),"proposition_count":len(props),
        "characters":len(s),"utf8_bytes":len(s.encode()),"lines":len(s.splitlines()),
        "status":"delimiter, equation-label and environment checks passed",
        "limitations":"No formal verification of mathematical validity."}
(root/'document_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
