"""Read-only audit of non-numerical inputs; writes only this inventory directory."""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path


OUT = Path(__file__).resolve().parent
PROJECT = OUT.parent
REPO = PROJECT.parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def item(source: str, role: str, destination: str, rationale: str) -> dict:
    path = REPO / source
    record = dict(source=source, role=role, proposed_destination=destination,
                  rationale=rationale, exists=path.exists())
    if path.is_file():
        record.update(bytes=path.stat().st_size, sha256=sha(path))
    elif path.is_dir():
        files = sorted(p for p in path.rglob('*') if p.is_file()
                       and '__pycache__' not in p.parts)
        record.update(files=len(files), bytes=sum(p.stat().st_size for p in files))
    return record


required = [
    item('Reviews_JASA-RA-2026-0866.pdf', 'review provenance',
         'supporting/reviews/Reviews_JASA-RA-2026-0866.pdf',
         'Original detailed reviewer report referred to by this resubmission.'),
    item('JASA-template/mab_aa_main.pdf', 'original submitted paper',
         'supporting/original_submission/mab_aa_main.pdf',
         'Original paper identity and notation; local copy makes this folder independent of its sibling.'),
    item('proposal/UCB-AA删除与集合维护重构_Codex执行方案_v1.0.md',
         'revision instruction history', 'supporting/plans/round1.md',
         'Explains removal of the two-stage UCB-AA method and retained setting/theory.'),
    item('proposal/第二轮稿件修改_FCCP整合_Codex执行方案_v2.0.md',
         'revision instruction history', 'supporting/plans/round2.md',
         'Detailed C16/P16/F17 integration contract and source attribution.'),
    item('proposal/ucbaa_continuous_maintenance_2026-10-14',
         'original maintenance research', 'supporting/research/maintenance_2026-10-14/',
         'Complete retained maintenance theory/proofs, audits, diagnostics and original CP implementation.'),
    item('reconstruction_jasa_stage2_2026-10-13/reproducibility_package.zip',
         'external theorem input and its complete project archive',
         'supporting/companion_temporal_geometry/reproducibility_package.zip',
         'Contains the companion full source, mathematical proofs and independent computational support; its results retain companion attribution.'),
    item('reconstruction_jasa_stage2_2026-10-13/manuscript.pdf',
         'companion readable paper', 'supporting/companion_temporal_geometry/manuscript.pdf',
         'Readable source for the cited spectral minimax characterization.'),
    item('reconstruction_jasa_stage2_2026-10-13/supplement.pdf',
         'companion readable proofs', 'supporting/companion_temporal_geometry/supplement.pdf',
         'Readable complete probability, spectral, counting and clock arguments.'),
]

provenance = [
    item('revision_notes', 'prior review analysis', 'supporting/reviews/revision_notes/',
         'Author analysis; must not be presented as a verbatim referee letter.'),
    item('reviewer1_response_2026-09-24', 'prior response draft',
         'supporting/reviews/reviewer1_response_2026-09-24/',
         'Working response and technical positioning; historical rather than current response letter.'),
    item('adversarial_review_2026-09-23', 'prior internal audit',
         'supporting/reviews/adversarial_review_2026-09-23/',
         'Internal proof and baseline challenges leading to later work, not external review.'),
    item('proposal/论文重构方案_持续到达下的相对近优集合维护与文献审计_2026-10-11.md',
         'earlier maintenance source provenance', 'supporting/plans/maintenance-origin-2026-10-11.md',
         'Listed by the 10/14 evidence manifest as an input.'),
    item('proposal/Part-II-Instance-Sensitive-研究记录.md',
         'earlier research source provenance', 'supporting/plans/instance-sensitive-notes.md',
         'Listed by the 10/14 evidence manifest; distinguishes earlier exploration from final theorem claims.'),
    item('proposal/UCB-AA_三项核心成果与CP伪代码_详细汇报.md',
         'maintenance explanation history', 'supporting/plans/maintenance-progress.md',
         'Narrative explanation of the maintenance claims and CP construction.'),
    item('proposal/UCB-AA_阶段性研究汇报_聊天原文.md',
         'maintenance research discussion', 'supporting/plans/maintenance-discussion.md',
         'Historical discussion; not an additional theorem or numerical dataset.'),
]

already_inside = []
for path in sorted((PROJECT/'experiments/fccp_frozen/original-archives').glob('*.zip')):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        theory = [name for name in names
                  if name.endswith(('theory.md', 'theory_frontier.md', 'proof_audit.md',
                                    'proof-and-experiment-audit.md', 'audit.md'))]
    already_inside.append(dict(path=path.relative_to(PROJECT).as_posix(),
                               bytes=path.stat().st_size, sha256=sha(path),
                               zip_members=len(names), theory_and_audit_members=theory))

g = REPO/'reconstruction_jasa_stage2_2026-10-13'
g_checks = []
with zipfile.ZipFile(g/'reproducibility_package.zip') as archive:
    for rel in ['manuscript.tex', 'supplement.tex', 'sections/S1_spectral_proofs.tex',
                'sections/S2_geometry_proofs.tex', 'sections/03_policy.tex',
                'theory/new_results.tex', 'references.bib']:
        matches = [n for n in archive.namelist() if n == rel or n.endswith('/'+rel)]
        digest = sha(g/rel)
        g_checks.append(dict(source=rel, sha256=digest, archive_members=matches,
                             archive_identical=len(matches)==1 and
                             hashlib.sha256(archive.read(matches[0])).hexdigest()==digest))

script_issues = [
    dict(path='revision2/freeze_inputs.py', lines=[7, 17, 18, 27, 28],
         classification='historical snapshot creator, not current reproduction',
         dependency='Five research directories and proposal plan under the old repository parent; Git working tree; old two-document root layout.',
         action='Keep its original records unchanged and exclude from normal reproduction. Use a portable manifest verifier over packaged files.'),
    dict(path='revision2/final_verify.py', lines=[7, 14, 15, 21, 79],
         classification='historical two-document acceptance check',
         dependency='All 1527 original protected inputs at old repository locations, root supplement.tex/pdf and Git parent.',
         action='Do not run as current acceptance check after the merge; provide a new single-document self-contained validator. Preserve historical result JSON.'),
    dict(path='revision2/render_review.py', lines=[50],
         classification='historical two-document renderer',
         dependency='Both root manuscript.pdf and root supplement.pdf; Poppler commands and Pillow.',
         action='Use the current merged-PDF renderer or a wrapper selecting manuscript only. Do not recreate a second editable TeX entry.'),
    dict(path='revision2/analysis/reanalyze_fccp.py', lines=[17, 21, 22, 275, 287, 356, 358],
         classification='portable release path already present; external preference remains',
         dependency='Prefers parent F17 tree if present; C16/P16 CSVs have an existing ZIP fallback; original ZIP copy mode reads repository parent.',
         action='Invoke --release-only from a portable wrapper. This forces the packaged F17 tree, skips external copying, and retains predecessor ZIP fallback. No missing external predecessor dataset was established.'),
    dict(path='revision2/analysis/check_revision2_data.py', lines=[31, 32, 36, 37],
         classification='portable explicit-path data validator',
         dependency='Requires --f-root and a fresh --out outside the frozen F17 tree; NumPy, pandas and SciPy.',
         action='Wrapper supplies project-relative absolute paths resolved at runtime, and a new verification output name.'),
    dict(path='revision2/analysis/check_fccp_interface.py', lines=[5, 6, 8],
         classification='portable copied-code validator',
         dependency='Only packaged experiments/fccp_frozen/src; writes local audit and local Numba cache.',
         action='Can run without old repository directories; avoid importing from external research paths.'),
    dict(path='revision2/build_papers.py', lines=[18, 25, 31, 32],
         classification='portable current build',
         dependency='Local manuscript.tex, bibliography, figures; external installed latexmk/pdfLaTeX/BibTeX executables.',
         action='Current merged build is portable. --baseline is intentionally unavailable after source changes and is historical, not needed.'),
    dict(path='revision2/integrate.py', lines=[11, 12],
         classification='guarded historical content rewriter',
         dependency='Local JSON blocks and old two-document organization.',
         action='Keep guard; never call for reproduction of the merged manuscript.'),
]

literal_path_hits = []
for script in sorted((PROJECT/'revision2').rglob('*')):
    if not script.is_file() or script.suffix not in ('.py', '.ps1'):
        continue
    for n, line in enumerate(script.read_text(encoding='utf-8-sig').splitlines(), 1):
        if re.search(r'(?<![A-Za-z])[A-Za-z]:[/\\]|/mnt/|/home/|/workspace|\.codex[/\\]', line):
            literal_path_hits.append(dict(path=script.relative_to(PROJECT).as_posix(),
                                          line=n, text=line))

main = (PROJECT/'manuscript.tex').read_text(encoding='utf-8')
graphics = re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', main)
local_assets = [dict(path=rel, exists=(PROJECT/rel).is_file(), sha256=sha(PROJECT/rel))
                for rel in graphics]
local_assets.append(dict(path='references.bib', exists=True, sha256=sha(PROJECT/'references.bib')))

report = dict(
    date='2026-10-17', scope='Read-only inventory of non-numerical support; no source copied or manuscript/Git changed.',
    required_external_support=required, recommended_provenance=provenance,
    already_packaged_complete_research_archives=already_inside,
    companion_archive_current_source_checks=g_checks,
    current_document_local_assets=local_assets,
    revision2_script_portability=script_issues,
    literal_absolute_path_hits_in_revision2_scripts=literal_path_hits,
    historical_absolute_paths='source-map.json and other historical reports store original machine paths as provenance; those are not current build dependencies. Preserve them, while the new public manifest uses relative paths.',
    companion_bibliographic_limit='Anonymous unpublished companion version dated 2026-10-13; no verified public author list, DOI or arXiv identifier. Packaging the actual paper/proofs resolves local availability, not public publication status.',
    not_required_for_current_claims=[
        dict(paths=['reconstruction_jasa_2026-10-13/'], reason='Superseded G-prior project. Keep its historical hash map, but current companion archive provides the actual required spectral proofs.'),
        dict(paths=['moss_2026-10-04/', 'moss_elimination_2026-10-02/', 'moss_elimination_2026-10-03/'], reason='Abandoned alternative algorithm studies; current paper does not cite or use their numerical outputs.'),
        dict(paths=['revision_trial_2026-09-23/', 'revision_exploration_2026-09-23/'], reason='Earlier repair/exploration branches. Original paper archive and explicit retained research provenance suffice; do not mix these runs into final numerical evidence.'),
        dict(paths=['proposal/temporal_geometry_research/'], reason='Earlier G development input; the complete current G archive already preserves its necessary code and provenance.'),
    ],
)
imports_path = OUT/'support-import-manifest.json'
if imports_path.is_file():
    imported = json.loads(imports_path.read_text(encoding='utf-8'))
    by_source = {row['source']: row for row in imported['files']}
    report['collection_result'] = dict(status=imported['status'],
                                        manifest='reproducibility/support-import-manifest.json',
                                        copied_files=imported['copied_files'],
                                        total_bytes=imported['total_bytes'],
                                        historical_c16_input_identities=imported.get('historical_c16_input_identities', []))
    for record in required + provenance:
        prefix = record['source'].rstrip('/')+'/'
        copies = [row['destination'] for source, row in by_source.items()
                  if source == record['source'] or source.startswith(prefix)]
        record['packaged_destinations'] = copies
        record['collection_complete'] = bool(copies)
(OUT/'support-inventory.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

markdown = '''# 非数值支撑材料盘点

日期：2026-10-17。盘点程序只读原件、不修改稿件或 Git；后续收集程序已将必要材料原样补入 `supporting/`。精确来源、文件大小、SHA-256和脚本行号见 `support-inventory.json`，实际120份副本及历史输入PDF身份映射见 `support-import-manifest.json`。

最初需要补入自含目录的材料是：原审稿报告 `Reviews_JASA-RA-2026-0866.pdf`、原投稿PDF、两轮修改执行方案、10月14日完整维护理论研究包，以及当前正文实际引用的 Temporal Geometry 伴随稿及完整证明档案。这些已补齐，原件保持未改。完整proposal来源包含40个非缓存文件；另有1个Python缓存未复制。

三轮新研究的完整原ZIP已在 `experiments/fccp_frozen/original-archives/`。其中包含C16和P16完整理论、证明审计及研究报告；无须为了取得这些内容再次依赖根目录的展开版本。10月14日原始维护研究仍应补入，因为它不等同于上述三代包。

G伴随稿已有完整 `reproducibility_package.zip`，205个成员，大小12,763,769字节。本次逐一核对其中正文、补充、S1谱证明、S2几何证明、策略节、扩展理论和文献库，均与当前源文件字节相同。建议同时保存可读的正文与补充PDF。伴随稿是收益模块既有输入，不能把其中独立实验改称本稿新增实验。其公开作者、DOI/arXiv信息仍待作者确认，本地封装不会改变未公开状态。

当前合并稿的5张图片和文献库均在resubmission目录内部，没有外部TeX引用。已有历史审核中的绝对机器路径是当时来源记录，应保留原貌；当前复现入口和新增清单则应使用项目相对路径。

`revision2/analysis/reanalyze_fccp.py --release-only` 已支持从本地发行目录与前驱ZIP完成再分析，C16/P16有现成ZIP回退。普通调用会优先寻找父目录中的F17展开目录，建议新复现入口统一强制 `--release-only`。短接口和冻结数据核验也可用本地发行文件执行。

不要把 `freeze_inputs.py`、`final_verify.py`、`render_review.py` 当作当前完整单文件稿的统一验收入口：前两者核验的是旧仓库位置和旧两文件阶段，最后一个仍尝试渲染独立supplement。应保留历史脚本与结果，新增面向当前单文件稿及本地支撑档案的可移植核验入口。`integrate.py`已有防止覆盖合并稿的保护，应继续保留。

更早的G-prior、MOSS淘汰实验、9月试修分支并非当前稿件结果的必要输入。不应将其全部运行混入最终比较；若保存，也须单列历史研究。原审稿分析与旧回复草稿可以作为修订来源保存，但它们不是逐字审稿信，也不是当前可以直接提交的回复。
'''
assert not re.search(r'\\[()\[\]]', markdown)
(OUT/'support-inventory.md').write_text(markdown, encoding='utf-8')
print(json.dumps(dict(required_items=len(required), provenance_items=len(provenance),
                      companion_archive_proofs_match=all(x['archive_identical'] for x in g_checks),
                      missing_current_assets=[x for x in local_assets if not x['exists']],
                      literal_absolute_path_hits=len(literal_path_hits)), ensure_ascii=False))
