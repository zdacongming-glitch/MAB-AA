"""Check self-contained source structure, references, and Markdown delimiters."""
from pathlib import Path
import collections,json,re

REV=Path(__file__).resolve().parent
ROOT=REV.parent
sources={name:(ROOT/name).read_text(encoding='utf-8')
         for name in ['manuscript.tex','supplement.tex'] if (ROOT/name).is_file()}
labels=collections.Counter()
refs=[]
for source in sources.values():
    labels.update(re.findall(r'\\label\{([^}]+)\}',source))
    refs.extend(re.findall(r'\\(?:eqref|ref|pageref)\{([^}]+)\}',source))
sections={name:re.findall(r'\\section\{([^}]+)\}',source)
          for name,source in sources.items()}
bad_markdown=[]
for file in REV.rglob('*.md'):
    if 'baseline' in file.relative_to(REV).parts:
        continue
    content=file.read_text(encoding='utf-8-sig')
    if re.search(r'\\[()\[\]]',content):
        bad_markdown.append(str(file.relative_to(ROOT)))
result={'sections':sections,
        'duplicate_labels':sorted(label for label,count in labels.items() if count>1),
        'undefined_reference_labels':sorted(set(refs)-set(labels)),
        'tex_input_commands':{name:re.findall(r'\\(?:input|include)\s*\{[^}]+\}',source)
                              for name,source in sources.items()},
        'root_tex_files':sorted(p.name for p in ROOT.glob('*.tex')),
        'markdown_noncompliant_delimiters':bad_markdown}
(REV/'source-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
