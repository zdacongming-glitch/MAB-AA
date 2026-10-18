# 本稿研究支撑档案

本目录将原来分散在仓库根目录、proposal及另一篇伴随稿目录中的支撑材料，原样收进当前resubmission目录。原件未删除或修改。逐文件来源、字节数和SHA-256见 [support-import-manifest.json](../reproducibility/support-import-manifest.json)。

- `proposal/`：完整保留本地proposal目录的40个非缓存文件（原目录另有1个Python缓存），包括两轮执行方案、10月14日完整维护理论/证明/诊断、早期理论记录及原研究ZIP。它记录研究与修订过程，不能把全部探索记录视为当前稿件主张。
- `original_submission/`：原UCB-AA投稿的TeX、PDF、文献库、样式和图片，以及原审稿报告。保留main、mab_aa_main及preprint不同历史入口；本次重投稿仍只编辑resubmission根目录的 `manuscript.tex`。
- `review_history/`：旧审稿分析、内部技术审计和工作回复草稿。只有原审稿PDF是收到的逐字报告；内部审查及作者草稿的身份不作更改。旧回复不自动等同于当前稿件的可提交回复。
- `research_input_pdfs/`：C16来源清单中的 `manuscript(2).pdf` 和 `supplement(2).pdf`。已按SHA-256找到其本地历史稿件副本并原样保存；原清单中的 `(1)` 两PDF则对应下述G伴随稿。这些是输入身份档案，不是当前编辑入口。
- `companion_temporal_geometry/`：正文引用的 *The Temporal Geometry of Bandits With Arriving Arms* 当前匿名未公开伴随稿。包含完整原复现ZIP、可读正文/补充PDF、所有数学section，以及三份伴随文档的TeX/文献/图资源依赖闭包。完整可执行代码和原始计算结果在该ZIP中，独立解压后按包内README运行。不要把伴随稿的实验计成本稿新增实验；其谱结论和概率工具仍是明确引用的既有输入。

C16、P16、F17三轮研究的完整原ZIP另已保存在 `../experiments/fccp_frozen/original-archives/`；当前主数值实验的可运行发行代码与冻结结果在 `../experiments/fccp_frozen/`。两处共同构成研究来源和计算材料，不需要父目录中的展开研究包。

伴随稿的公开作者清单、DOI或arXiv编号尚未取得，仍应由作者在正式发行前确认。此处按实际匿名稿和项目版本保存，没有假设它已经发表。

原稿使用biblatex/Biber；伴随稿有自己的构建和计算入口。它们是来源档案，不应与当前根目录单文件稿的pdfLaTeX/BibTeX构建混用。本次复制未重跑这些历史性能实验。
