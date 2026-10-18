# 可靠近优集合维护稿件

当前编辑版本：2026-10-16。题目为 *The Cost of Reliable Near-Optimal Set Maintenance with Arriving Arms*。本轮按作者指定修改方案，将原两阶段UCB-AA、其专属regret分析和旧实验整体移出投稿稿件，以可靠集合维护的成本与收益权衡为主线。原始文稿、代码、数据与图保留归档；独立时间几何论文未修改。

## 阅读与编辑入口

- `manuscript.tex`：单文件英文正文，全部七节直接在此编辑；`manuscript.pdf` 为 20 页。
- `supplement.tex`：补充材料入口；`supplement.pdf` 为 20 页，按S1–S13组织维护证明与计算细节。
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
