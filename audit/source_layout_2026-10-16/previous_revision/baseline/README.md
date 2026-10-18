# UCB-AA 的 JASA T&M 重投稿稿件

日期：2026-10-15。此目录以原 UCB-AA 稿件为基础修订：保留原应用动机、MAB-AA setting、regret 主问题、AID/DB 与两阶段 UCB-AA，修复证明与预算接口，并加入可靠集合维护的后续成果。CP-UCB-AA 单独提供新增报告任务的上界构造，不替代原算法。独立时间几何论文的谱 minimax、MC-MOSS、容量与随机到达成果没有并入本稿。原 PDF 与后续研究目录均保留。

## 阅读顺序

1. `manuscript.pdf`：英文主稿，29 页。保留原稿作者顺序、问题和算法主线，正文同时呈现修复后的 regret 分析与新增维护理论。
2. `supplement.pdf`：英文证明与计算补充，35 页。包含原 UCB-AA 的实际计数分析、物理时间重启、保留的 regret 下界，以及维护结果、分位数和兼容窗口下界。
3. `response_to_reviewers.md`：针对提供的五页报告逐项回复，分别说明旧证明撤回、原算法修复、新增结果及尚未完成的数值验证。
4. `revision_map_zh.md`：原稿保留范围、修复与新增内容、材料来源及独立新文边界。
5. `audit/original_numerical_preservation.md`：原两场景的数据身份、真实观察、规格差异与下一轮确认实验。
6. `research_report_zh.md` 与 `assessments/`：早先 checkpoint 中心版本的研究与冻结评审记录；其中分数不适用于本轮恢复原稿后的组合版本。

正文集中在单个 `manuscript.tex`，直接编辑这个文件。当前九节依次为引言、原 MAB-AA 模型与三项账本、UCB-AA 及修复分析、原 regret 下界、报告任务与 CP、广播与面积、任务过期权衡、两部分数值研究、讨论。新增维护结果仍是正文实质贡献。`preamble.tex` 保存公共宏包，`supplement.tex` 与 `theory/` 保存补充证明，`references.bib` 保存参考文献。

原七个分节文件及合并前主文件在 `audit/before_section_merge/`，合并记录在 `audit/section_merge.json`；它们仅供追溯。`experiments/` 保存新报告实验代码、配置和逐次结果；`experiments/original_submission_archive/` 保存原 C/E 数据、配置、代码与重算汇总；`figures/original_submission/` 保存原图。`assessments/` 的真实隔离评分、冻结材料和汇总保持历史原样。本轮内容已经改变，尚未重新评估创新性。

## 编译与复现

在本目录使用 TeX Live 及 Python：

```powershell
./build.ps1
python -X utf8 experiments/run_experiments.py
python -X utf8 figures/gen_fig_performance.py --figures-only
python -B experiments/original_submission_archive/summarize_archive.py
python -X utf8 audit/verify_delivery.py
```

`run_experiments.py` 运行新增报告研究：4 个环境、9 个方法、每环境 160 个配对重复，每次 20,000 次真实采样，共 5,760 次运行。它不运行修复后的原 UCB-AA。`summarize_archive.py` 只重算本地归档 CSV，不重新模拟原场景。归档原研究为 C/E 两场景、五个方法、每方法 100 次重复、预算 60,000；原代码、配置与结果身份见其 `metadata.json`。实际包版本见 `experiments/requirements.txt`，输入摘要见各 manifest。

重新模拟或重算会更新相应输出；作图的 `--figures-only` 模式不改数值结果与表格。历史评估包不会自动更新或改分。`audit/verify_delivery.py` 分别检查历史冻结证据及本轮源文件、PDF 和原模拟归档；本轮版本摘要在 `audit/notation_alignment.json`，排版检查在 `audit/final_revision_pdf_checks.json`。

主文新图的区间为 Monte Carlo 不确定性；主文归档表列均值和 Monte Carlo 标准误，归档汇总 CSV 另提供逐项 Student $t$ 区间。原 UCB-AA 在 C 中明显落后于 MOSS，在 E 中均值较好；两个场景相对其他归档对照的有利观察也保留。小活跃集受停止接纳混杂，不能当作所有到达均已认证筛选。

报告研究中细精度 CP 的 640 次运行始终全部未决，零误报不展示有效分类；粗精度在部分环境被强识别适配同时改善两项指标，另一些较低 regret 尚不能单独归因于任务过期。零观测误报也不验证全环境、无限时间可靠性。这些限制在正文如实呈现。

## 本稿的准确状态

本轮恢复了原稿基础，给出新的固定预算计数证明和合法物理时间重启，保留原 lower-bound 机制，新增维护证明及既有 5,760 次报告实验。旧错误证明未被重新当作有效证明。原模拟归档已保存并核对统计量。

修复后的 UCB-AA 尚未重新运行原 C/E 两场景，其匹配强对照、预筛选消融、持续接纳诊断及三项损失账本仍待确认。既有 CP 数据不能代替这项验证。一般异质、任意重叠到达和全部面积预算的最优前沿也未证明，暂缓端没有匹配的 regret 下界。固定精度程序不能继承另一可纠错构造的强一致性。历史创新性分数只属于旧冻结版本，本轮没有重评。

这是供作者审阅的重投稿研究稿，未向期刊或其他人发送。当前出版社作者页的全部格式规则未能核实，因此没有宣称满足现行页数、摘要字数或匿名要求。`manuscript.tex` 的匿名开关可以生成无作者版本。回复信也没有假造未提供的编辑决定信或早前评审原话。JASA 的计算复现要求依据当前[官方指南](https://jasa-acs.github.io/repro-guide/)准备；其余核查范围见 `audit/literature_scope.md`。

写作使用了用户指定的统计写作、证明、humanizer 与 watermarks-remover 技能。自然语言精修与不可见 Unicode 检查是不同步骤；本轮九份活跃 TeX/Bib 源文件的检查未发现目标不可见字符，结果见 `audit/notation_preservation_checks.json`。没有未知统计水印检测器或密钥，因此不声称文本水印被认证移除，也不将文本宣称为人类独立撰写。作者、引文、公式和数据来源均保留。
