"""Write the reviewable editorial handoff from actual validation records."""
from pathlib import Path
import csv
import hashlib
import json
import re
import shutil

REV = Path(__file__).resolve().parent
ROOT = REV.parent
validation = json.loads((REV/"validation.json").read_text(encoding="utf-8"))
if not validation["passed"]:
    raise SystemExit("Resolve validation issues before finalizing the handoff.")
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
pages = {k:v["pages"] for k,v in validation["pdfs"].items()}

def write(name, text):
    path = ROOT/name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip()+"\n", encoding="utf-8")

write("README.md", f"""
# 可靠近优集合维护稿件

当前编辑版本：2026-10-16。题目为 *The Cost of Reliable Near-Optimal Set Maintenance with Arriving Arms*。本轮按作者指定修改方案，将原两阶段UCB-AA、其专属regret分析和旧实验整体移出投稿稿件，以可靠集合维护的成本与收益权衡为主线。原始文稿、代码、数据与图保留归档；独立时间几何论文未修改。

## 阅读与编辑入口

- `manuscript.tex`：单文件英文正文，全部七节直接在此编辑；`manuscript.pdf` 为 {pages['manuscript']} 页。
- `supplement.tex`：补充材料入口；`supplement.pdf` 为 {pages['supplement']} 页，按S1–S13组织维护证明与计算细节。
- `revision_2026-10-16/REVISION_REPORT.md`：本轮删、留、迁移、展示完善与证据边界。
- `revision_2026-10-16/edit-checklist.md`：A-00至A-22逐项状态。
- `revision_2026-10-16/theorem-migration-map.csv`：正文、附录全部旧label的迁移与删除对应。
- `revision_2026-10-16/validation-report.md`：实际构建、数学迁移、数值与代码语义检查。
- `revision_2026-10-16/future-work.md`：C级后续研究，仅登记，尚未执行。

主线依次为引言、联合任务、Checkpoint-UCB构造、基本维护成本、临时任务与regret权衡、数值研究、讨论。Checkpoint-UCB是现有CP构造的论文展示名；固定精度、服务规则、类接口及数据ID均未改变。原两阶段算法不是本稿的另一条方法主线。

## 构建与核验

```powershell
./build.ps1
python -X utf8 revision_2026-10-16/validate_revision.py
```

构建使用原pdfLaTeX/BibTeX体系，输出到独立的 `revision_2026-10-16/build/`，再更新上方两份PDF；日志在该目录及 `build-console.log`。正文通过真实附录label导入自动编号，不硬写旧编号。旧根目录编译中间文件属于历史产物，应使用此构建入口读取当前构建日志。

本轮 `check_experiments.py` 已核对保存的5,760条记录、主表24行、allocation全表、成对差异和数值hash，并实际运行短的逐轮代码语义诊断。它不进行新的比较实验；重新运行会重复这些诊断。历史20,000轮parity检查没有在本轮重复。`run_experiments.py` 和绘图脚本保留原版本，可用于另行授权的复现；本次没有修改或重跑它们。

## 数据与范围

四环境、九方法、每环境每方法160次、每次20,000轮的记录与图全部不变。640次细精度运行始终全未决、粗精度在稳定和突发环境的双指标劣势、改善环境中的服务量混杂均保留。模拟未证明一般最优前沿或全模型可靠性。

本地复现资源齐全；尚未指定并核验公开永久地址。该事项属于发布准备，不阻碍本轮编辑交付。一般窗口上界、暂缓端匹配converse和自动精度仍未完成。修复旧两阶段算法的重跑已经退出本稿义务。

## 历史与来源

本轮基线47份快照见 `revision_2026-10-16/baseline/`，源hash与1,025个受保护文件清单见 `input_manifest.json`。原实验仍在 `experiments/original_submission_archive/`，旧图在 `figures/original_submission/`，旧专属理论源仍保留，但均不参与当前编译。`submission_source/` 是仅含当前投稿源与必要表图的白名单副本，不自动包含历史档案。

`assessments/`、`research_report_zh.md`、旧回复信和 `audit/` 是各自注明版本的历史记录，不代表当前稿件的创新性评分。本轮没有重新打分、投稿、公开发布或向他人发送文件。

写作使用stat-journal-writing、humanizer及watermarks-remover。自然语言修改与不可见字符扫描分别记录，不声称统计水印已被验证移除或文本由人类独立撰写。未开展现行期刊格式的实时核查，也不将历史期刊指南当作当前硬性规定。
""")

write("revision_map_zh.md", """
# 2026-10-16修订对应

本轮以作者提供的删除与维护重构方案为准，替代本目录2026-10-15“恢复原算法并结合维护结果”的编辑结构。冻结基线及两份旧PDF仍在 `revision_2026-10-16/baseline/`。

| 基线内容 | 当前处理 |
|---|---|
| 原动机与基础MAB-AA模型 | 保留外生永久到达、平稳有界独立奖励、原主要记号及当前最佳比较器；直接引出报告任务 |
| 原两阶段算法与全部专属修复分析 | 正文和投稿附录整体移出，源与旧PDF归档 |
| 原纯regret下界 | 移出，保留维护证明实际使用的信息工具 |
| 原报告任务与CP构造 | 前移为新第2–3节，展示名Checkpoint-UCB，补齐伪代码，代码不变 |
| 广播、最坏面积、增长后果 | 新第4节，先最坏面积再增长，增长充分性改引一般完成界 |
| 临时任务、共享证据、两端与概率下界 | 新第5节；将既有无条件regret式与面积式共同呈现，范围不扩大 |
| 原60,000轮实验与FDA图 | 有利和不利结果一起归档，不参与当前稿件 |
| 5,760次维护比较 | 新第6节与S13，数值、图与全部重要负面解释保留 |
| 独立时间几何论文 | 只读保护，无内容迁入 |

一般信息松弛、兼容窗口、最终一致性与中间服务配置保留于扩展附录，适用边界不变。当前完整迁移表、任务状态、检查与后续研究分别见本轮工作目录中的CSV和报告。
""")

response = ROOT/"response_to_reviewers.md"
body = response.read_text(encoding="utf-8")
banner = """# 历史回复信：不对应2026-10-16当前结构

以下正文保留2026-10-15组合版本的回复记录。本轮按作者的新方案已整体移出原两阶段算法、专属分析及旧实验；下文有关保留原算法和重跑义务的文字不再代表当前稿件。当前修改说明见 `revision_2026-10-16/REVISION_REPORT.md`。未将此历史回复信纳入当前投稿源包，也未发送。

---

"""
if not body.startswith("# 历史回复信：不对应2026-10-16当前结构"):
    response.write_text(banner+body, encoding="utf-8")

cards = [
("A-00","源版本、依赖与归档","source-manifest.md；input_manifest.json；baseline/"),
("A-01","题目、摘要、关键词和元数据","manuscript.tex开头；supplement.tex开头；PDF metadata"),
("A-02","引言以维护成本为主问题","manuscript.tex sec:introduction"),
("A-03","FDA图及专属经验材料移出","活跃图仅fig_cost_area/fig_paths_pair1/fig_paths_pair2"),
("A-04","基础模型与物理顺序","sec:model；不再依赖旧轮次参数"),
("A-05","原AID/DB压缩为认证机制","sec:model末小节；全篇不使用原缩写贡献"),
("A-06","通用三项记账迁到计算附录","S13 eq:three_part；Batch100保留"),
("A-07","旧两阶段UCB-AA整体移出","活跃输入与残留搜索；原分析源归档"),
("A-08","旧纯regret专题移出，共用工具保留","S1 app:tools；theorem-migration-map.csv"),
("A-09","可靠报告与联合协议前移","sec:reporting_task；eq:area；eq:joint_protocol；参数符号表"),
("A-10","检查点展示名与正式伪代码","sec:method；alg:checkpoint-ucb；721轮语义诊断"),
("A-11","基础联合保证完整保留","prop:reporting；eq:reward_bound；S2 app:joint"),
("A-12","共同参考环境与队列下界","thm:broadcast；eq:broadcast_queue；eq:queue_area；S3"),
("A-13","最坏面积、增长量词与引用接口","thm:worst_area；cor:growth；app:completion_general；S5"),
("A-14","多次更新族与两种gap","eq:family_parameters；eq:family_means"),
("A-15","半完成逻辑与松弛迁移","eq:partial_recovery；S6 eq:allocation_lower"),
("A-16","共享证据面积与既有regret共同呈现","thm:reuse；eq:reuse_conditions；eq:reuse_area；eq:reuse_regret；S7"),
("A-17","快速与暂缓端及范围","thm:tradeoff；eq:chosen_horizon；eq:rapid_matched；粗端仅上界"),
("A-18","概率加强与q+1截断","thm:quantile_main；S8 lem:budget_completion；cor:joint_quantile"),
("A-19","旧实验整套移出","无原archive表图输入；历史文件hash不变"),
("A-20","全部维护实验与负面结果保留","tab:simulation；fig:cost-area；app:computation；experiments_validation.json"),
("A-21","讨论与未来边界","sec:discussion；future-work.md；无旧算法重跑义务"),
("A-22","数据声明、引用及复现","Data and code availability；本地资源和无公开URL说明；独立bbl仅列实际引用"),
]
write("revision_2026-10-16/edit-checklist.md", "# 编辑验收任务卡\n\n本表在validation.json通过后生成；DONE代表本轮编辑、来源及相应验收检查完成，不代表全部证明已独立验证或论文已达到投稿完成度。\n\n| 任务 | 状态 | 完成内容 | 定位与证据 |\n|---|---|---|---|\n"+"\n".join(f"| {key} | DONE | {title} | {evidence} |" for key,title,evidence in cards)+"\n\nC-01至C-05均为DEFERRED_C，只登记在future-work.md。未发现本轮BLOCKED_SOURCE、BLOCKED_MATH或BLOCKED_BUILD条目。公开发布地址未确定属于发布准备事项，不假报为本地资源缺失。")

write("revision_2026-10-16/blockers.md", """
# 本轮阻塞与待准备事项

未发现阻碍本轮编辑交付的已知BLOCKED_SOURCE、BLOCKED_MATH或BLOCKED_BUILD条目。此结论限于实际来源、迁移与构建检查，不等于所有数学结果无误。

本地运行记录、源码和表图齐全。公开永久链接尚未指定和核验；正文据实说明本地随附资源，发布前需由作者安排。现行期刊格式、提交匿名要求及声明也未在本轮作实时核查。

C级理论和机制实验未开展，不列为已完成贡献，不阻碍本轮形成结构完整的修订稿。旧两阶段算法重跑已退出本稿义务。
""")

write("revision_2026-10-16/REVISION_REPORT.md", f"""
# 本轮修改报告

执行版本：maintenance-editorial-2026-10-16-v1。按作者指定方案完成结构重构，实际入口为 `manuscript.tex` 与 `supplement.tex`。正文七节保持单文件；补充材料为S1–S13。主稿 {pages['manuscript']} 页，补充材料 {pages['supplement']} 页，均由原pdfLaTeX/BibTeX体系成功构建。

## 实际移出

原两阶段UCB-AA算法、固定预算与固定gap分析、物理时间doubling、纯regret下界，以及旧60,000轮比较和FDA图，整体退出当前正文与补充材料。有利和不利旧结果一起归档。旧版本47份快照保留，源代码和数据没有删除；独立时间几何论文未修改。当前投稿源包采用白名单，不包含上述历史专题。

## 保留与前移

保留原奖励模型、外生永久到达、物理时间顺序、主要均值与gap记号。报告可靠性、累计边界外未决量及期望regret/高概率标签—面积协议前移为第2节。广播、最坏面积、增长后果、临时任务、共享证据、两端权衡和概率加强全部保留。扩展附录仍包含兼容窗口、最终一致性、一般信息松弛和中间配置的原范围。

## 展示完善与显式接口修正

Checkpoint-UCB只替代CP构造的论文展示名。新增正式伪代码、参数表、主辅自动引用，并把既有S7的无条件期望regret式迁入共享证据proposition。没有改变公共类、函数接口、服务行为、数据方法ID或置信区间机制。

增长推论的充分性现改引一般完成引理 `app:completion_general`，不再错误地依赖参数范围更窄的最坏面积定理；原推论范围不缩、最坏定理范围不扩。一般完成界只是现有证明的具名呈现。其精度参数域显式写成模型已有的 $0<\eta<1$。原已蕴含的 $v>0$ 及规定终点关系直接写明；这些不是新增科学假设。长松弛公式仅保留在S6，完整 $a+\delta W$ 与 $q+1$ 接口保留。

## 实际检查与未做事项

全部5,760条既有维护运行、主表24行、九方法allocation表和成对差异均从真实数据核对。六个短代码场景共721轮检查动作、服务、共享计数、冻结区间、后方检查点与负报告后的收益选择；历史20,000轮parity未重复。所有现有实验、数值结果、图和受保护文件哈希不变。

未开展新比较实验，未新增理论结果，未重新评估创新性。细精度640次全未决、粗精度不利比较和服务强度混杂仍在正文。C级工作仅登记。没有向外部发送或发布材料。

编译、引用、残余叙事、数值保全、公式迁移及渲染检查见 `validation-report.md`；这里不把编辑检查描述为全部证明获独立验证。未发现本轮已知阻塞；公开永久链接和实时投稿格式仍属作者发布前准备事项。
""")

write("revision_2026-10-16/validation-report.md", f"""
# 验收记录

本文件依据实际JSON、编译日志和人工页面检查填写。验证版本为maintenance-editorial-2026-10-16-v1。

| 检查 | 实际结果 | 证据 |
|---|---|---|
| 基线身份 | M/S哈希与方案一致；47份快照 | input_manifest.json |
| 保护文件 | 1,025文件哈希不变，含独立论文与全部旧实验 | validation.json |
| 活跃结构 | 主文7节、补充13节；旧专属分析和旧图无编译输入 | validation.json actual_inputs |
| 引用与文献 | 源label/ref可解析、无重复；独立bbl只显示实际引用 | validation.json；build/*.log |
| 编译 | 两份PDF成功；最终TeX日志无未定义引用、重复citation或版面警告 | build-console.log；build/*.log |
| 保留公式 | 补充72个展示式中71个相同，另一式合并已有熵下界；正文17式规范化相同 | proof_math_preservation.json；main_theory_audit.md |
| 数值 | 5,760记录、主表24行、allocation及成对差异核对通过 | experiments_validation.json |
| 代码语义 | 六个短场景721轮；不改变代码，与原接口逐轮一致 | experiments_validation.json；check_experiments.py |
| PDF渲染 | 全部页面渲染；文本无空页、越界或未解引用 | pdf_review/render_checks.json |
| 人工视觉 | 算法、长式、两端结论、主表、九方法图及全部附录页已查看；修正三项分解被float割裂和引理跨页 | visual_review.md |
| Markdown公式 | 本轮所有新建/修改Markdown按单美元和独占行双美元检查 | validation.json markdown_checked |
| 文本清理 | humanizer复核叙事；18份活跃TeX调用技能检查，BibTeX不受工具支持并另作只读Unicode检查 | prose-edit-audit.md；watermark_inspection.json |

两份最终PDF页数分别为 {pages['manuscript']}、{pages['supplement']}。最终hash和实际输入图记录于validation.json；PDF内容与快照的差异属于本轮授权编辑。旧根目录的编译日志不代表本轮构建。

## 检查的边界

本轮未开展新比较实验、历史20,000轮parity重跑、完整独立证明复核、文献创新性重评分或现行期刊规则的实时核查。有限模拟零误报不验证全环境、全时间可靠性。统计文本水印未使用对应检测器与密钥核验；不声称已验证去除。
""")

# All old main labels receive an explicit destination or removal record.
current_inputs = {p for paths in validation["actual_inputs"].values() for p in paths}
dest = {}
for name in current_inputs:
    for label in re.findall(r"\\label\{([^}]+)\}", (ROOT/name).read_text(encoding="utf-8")):
        dest[label] = name
rows = []
oldmain = (REV/"baseline/manuscript.tex").read_text(encoding="utf-8")
for label in re.findall(r"\\label\{([^}]+)\}", oldmain):
    action = "keep" if label in dest and dest[label]=="manuscript.tex" else "move" if label in dest else "remove"
    rows.append({"source_file":"baseline/manuscript.tex", "source_section_or_label":label,
        "source_statement_name":label, "action":action, "new_file":dest.get(label,"archive only"),
        "new_label":label if label in dest else "", "proof_dependencies":"see retained supplementary inputs" if label in dest else "no active dependency", "assumption_changes":"none", "status":"DONE"})
with (REV/"theorem-map-supp.csv").open(encoding="utf-8-sig",newline="") as stream:
    source_rows = list(csv.DictReader(stream))
for row in source_rows:
    rows.append({key: row.get(key, "") for key in rows[0]})
with (REV/"theorem-migration-map.csv").open("w",encoding="utf-8-sig",newline="") as stream:
    writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)

# A portable whitelist of the active paper, not a recursive project archive.
package = REV/"submission_source"
files = current_inputs | set(validation["graphics"]) | {"references.bib", "build.ps1", "manuscript.pdf", "supplement.pdf"}
for name in sorted(files):
    target = package/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/name,target)
package_manifest = {name:sha(package/name) for name in sorted(files)}
(REV/"submission-source-manifest.json").write_text(json.dumps(package_manifest,ensure_ascii=False,indent=2),encoding="utf-8")

manifest_path = REV/"proof_reorganization_manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["new_files"] = {name:sha(ROOT/name) for name in manifest["new_files"]}
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"task_cards":len(cards),"migration_rows":len(rows),"source_package_files":len(files),"pdf_pages":pages},ensure_ascii=False))
