"""Import original support bytes without changing their source files.

This one-time collector requires the original research workspace. The resulting
supporting tree and its SHA-256 manifest are the portable research inputs;
normal reproduction never calls this historical collection script.
"""
from __future__ import annotations

import collections
import hashlib
import json
import re
import shutil
from pathlib import Path

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parent
REPO = PROJECT.parent
SUPPORT = PROJECT/'supporting'
SUPPORT.mkdir(exist_ok=True)
records = []


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_one(source: Path, destination: Path, group: str) -> None:
    source = source.resolve()
    destination = destination.resolve()
    if not source.is_relative_to(REPO) or (source.is_relative_to(PROJECT)
                                         and not source.is_relative_to(PROJECT/'audit')):
        raise RuntimeError(f'Unexpected original source: {source}')
    if not destination.is_relative_to(SUPPORT):
        raise RuntimeError(f'Unexpected output location: {destination}')
    before = sha(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha(destination) != before:
            raise RuntimeError(f'An existing support copy differs: {destination}')
    else:
        shutil.copy2(source, destination)
    after = sha(source)
    actual = sha(destination)
    if before != after or before != actual:
        raise RuntimeError(f'Support copy failed byte equality: {source}')
    records.append(dict(group=group, source=source.relative_to(REPO).as_posix(),
                        destination=destination.relative_to(PROJECT).as_posix(),
                        sha256=actual, bytes=destination.stat().st_size,
                        source_unchanged=True))


for source in sorted((REPO/'proposal').rglob('*')):
    if source.is_file() and '__pycache__' not in source.parts:
        copy_one(source, SUPPORT/'proposal'/source.relative_to(REPO/'proposal'), 'proposal')

valid_original_extensions = {'.tex', '.pdf', '.bib', '.bst', '.png', '.jpg',
                             '.jpeg', '.eps', '.svg', '.sty', '.cls'}
for source in sorted((REPO/'JASA-template').rglob('*')):
    if source.is_file() and source.suffix.lower() in valid_original_extensions:
        copy_one(source, SUPPORT/'original_submission'/source.relative_to(REPO/'JASA-template'),
                 'original_submission')
review = REPO/'Reviews_JASA-RA-2026-0866.pdf'
copy_one(review, SUPPORT/'original_submission'/review.name, 'original_review')

for directory in ['revision_notes', 'reviewer1_response_2026-09-24',
                  'adversarial_review_2026-09-23']:
    for source in sorted((REPO/directory).rglob('*')):
        if source.is_file() and '__pycache__' not in source.parts:
            copy_one(source, SUPPORT/'review_history'/directory/source.relative_to(REPO/directory),
                     'review_history')

# Resolve the C16 packet's historical manuscript(2)/supplement(2) input
# identities by content, preserving them even if bulky audit folders are
# excluded from the public versioned working tree.
old_pdf_dir = PROJECT/'audit/source_layout_2026-10-16/previous_revision/baseline'
for stem in ['manuscript', 'supplement']:
    copy_one(old_pdf_dir/f'{stem}.pdf', SUPPORT/'research_input_pdfs'/f'{stem}(2).pdf',
             'historical_research_input_pdfs')

g = REPO/'reconstruction_jasa_stage2_2026-10-13'
gdest = SUPPORT/'companion_temporal_geometry'
for name in ['reproducibility_package.zip', 'manuscript.pdf', 'supplement.pdf',
             'README.md', 'README_reproduction.md', 'requirements.txt', 'jasa-reference.bst']:
    copy_one(g/name, gdest/name, 'companion_temporal_geometry')

# Preserve all current mathematical sections and the full build-resource
# closure of all three companion documents. Their separate experiments stay
# attributed to that companion project, and the ZIP retains their runnable code.
pending = [g/'manuscript.tex', g/'supplement.tex', g/'computational_supplement.tex']
pending.extend(sorted((g/'sections').glob('*.tex')))
seen = set()
while pending:
    source = pending.pop()
    if source in seen:
        continue
    seen.add(source)
    copy_one(source, gdest/source.relative_to(g), 'companion_temporal_geometry')
    text = source.read_text(encoding='utf-8')
    for rel in re.findall(r'\\(?:input|include)\s*\{([^}]+)\}', text):
        path = g/rel
        if not path.suffix:
            path = path.with_suffix('.tex')
        if not path.is_file():
            raise RuntimeError(f'Missing companion source input: {path}')
        pending.append(path)
    for rel in re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', text):
        path = g/rel
        candidates = [path] if path.suffix else [path.with_suffix(ext) for ext in ['.pdf', '.png', '.jpg', '.eps']]
        path = next((p for p in candidates if p.is_file()), None)
        if path is None:
            raise RuntimeError(f'Missing companion graphic: {rel}')
        if path not in seen:
            seen.add(path)
            copy_one(path, gdest/path.relative_to(g), 'companion_temporal_geometry')
    for group in re.findall(r'\\bibliography\{([^}]+)\}', text):
        for rel in group.split(','):
            path = (g/rel.strip()).with_suffix('.bib')
            if path not in seen:
                seen.add(path)
                copy_one(path, gdest/path.relative_to(g), 'companion_temporal_geometry')

readme = '''# 本稿研究支撑档案

本目录将原来分散在仓库根目录、proposal及另一篇伴随稿目录中的支撑材料，原样收进当前resubmission目录。原件未删除或修改。逐文件来源、字节数和SHA-256见 [support-import-manifest.json](../reproducibility/support-import-manifest.json)。

- `proposal/`：完整保留本地proposal目录的40个非缓存文件（原目录另有1个Python缓存），包括两轮执行方案、10月14日完整维护理论/证明/诊断、早期理论记录及原研究ZIP。它记录研究与修订过程，不能把全部探索记录视为当前稿件主张。
- `original_submission/`：原UCB-AA投稿的TeX、PDF、文献库、样式和图片，以及原审稿报告。保留main、mab_aa_main及preprint不同历史入口；本次重投稿仍只编辑resubmission根目录的 `manuscript.tex`。
- `review_history/`：旧审稿分析、内部技术审计和工作回复草稿。只有原审稿PDF是收到的逐字报告；内部审查及作者草稿的身份不作更改。旧回复不自动等同于当前稿件的可提交回复。
- `research_input_pdfs/`：C16来源清单中的 `manuscript(2).pdf` 和 `supplement(2).pdf`。已按SHA-256找到其本地历史稿件副本并原样保存；原清单中的 `(1)` 两PDF则对应下述G伴随稿。这些是输入身份档案，不是当前编辑入口。
- `companion_temporal_geometry/`：正文引用的 *The Temporal Geometry of Bandits With Arriving Arms* 当前匿名未公开伴随稿。包含完整原复现ZIP、可读正文/补充PDF、所有数学section，以及三份伴随文档的TeX/文献/图资源依赖闭包。完整可执行代码和原始计算结果在该ZIP中，独立解压后按包内README运行。不要把伴随稿的实验计成本稿新增实验；其谱结论和概率工具仍是明确引用的既有输入。

C16、P16、F17三轮研究的完整原ZIP另已保存在 `../experiments/fccp_frozen/original-archives/`；当前主数值实验的可运行发行代码与冻结结果在 `../experiments/fccp_frozen/`。两处共同构成研究来源和计算材料，不需要父目录中的展开研究包。

伴随稿的公开作者清单、DOI或arXiv编号尚未取得，仍应由作者在正式发行前确认。此处按实际匿名稿和项目版本保存，没有假设它已经发表。

原稿使用biblatex/Biber；伴随稿有自己的构建和计算入口。它们是来源档案，不应与当前根目录单文件稿的pdfLaTeX/BibTeX构建混用。本次复制未重跑这些历史性能实验。
'''
assert not re.search(r'\\[()\[\]]', readme)
(SUPPORT/'README.md').write_text(readme, encoding='utf-8')

for row in records:
    if sha(REPO/row['source']) != row['sha256'] or sha(PROJECT/row['destination']) != row['sha256']:
        raise RuntimeError(f'Final source/destination equality failed: {row["source"]}')
input_locations = {
    'manuscript(2).pdf': SUPPORT/'research_input_pdfs/manuscript(2).pdf',
    'supplement(2).pdf': SUPPORT/'research_input_pdfs/supplement(2).pdf',
    'manuscript(1).pdf': gdest/'manuscript.pdf',
    'supplement(1).pdf': gdest/'supplement.pdf',
    'cp_ucb_aa.py': SUPPORT/'proposal/ucbaa_continuous_maintenance_2026-10-14/cp_ucb_aa.py',
}
input_identities = []
for entry in json.loads((REPO/'CCP_research_2026-10-16/source-documents.json').read_text(encoding='utf-8')):
    path = input_locations[entry['source']]
    if sha(path) != entry['sha256']:
        raise RuntimeError(f'Historical input identity mismatch: {entry["source"]}')
    input_identities.append(dict(historical_name=entry['source'],
                                 packaged_path=path.relative_to(PROJECT).as_posix(),
                                 sha256=sha(path), bytes=path.stat().st_size,
                                 matches_c16_source_documents=True))
report = dict(date='2026-10-17', status='passed',
              policy='Byte-exact copies; sources unchanged; no manuscript or Git edits.',
              files=records,
              groups={group:dict(files=sum(r['group']==group for r in records),
                                 bytes=sum(r['bytes'] for r in records if r['group']==group))
                      for group in sorted({r['group'] for r in records})},
              copied_files=len(records), total_bytes=sum(r['bytes'] for r in records),
              final_source_and_destination_hashes_verified=True,
              companion_scope='Separate cited input. Its complete ZIP contains independent experiments; no result is reattributed to the current paper.',
              current_editable_tex_entry='manuscript.tex',
              historical_c16_input_identities=input_identities,
              added_document=dict(path='supporting/README.md', sha256=sha(SUPPORT/'README.md')))
(OUT/'support-import-manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['files']}, ensure_ascii=False, indent=2))
