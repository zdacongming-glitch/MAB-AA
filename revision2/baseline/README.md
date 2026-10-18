# 稿件文件

直接编辑以下两个文件：

- `manuscript.tex`：正文、全部宏包与符号定义、算法和主表。
- `supplement.tex`：补充材料、全部宏包与符号定义、S1–S13证明和计算细节、分配表。

两份文件均已包含各自全部TeX源代码，没有外部分节、公共preamble或表格input。图片保存在 `figures/`，文献库为 `references.bib`；实验源和数据仍在 `experiments/`。

使用 `build.ps1` 编译；中间产物在 `build/`，生成的两份PDF同时更新到本目录。正文从 `build/supplement.aux` 自动读取附录编号，因此先编译补充材料，再编译正文。

原拆分TeX与上一轮编辑记录完整移至 `audit/source_layout_2026-10-16/`。它们只用于追溯，不再是编辑入口；不要运行历史整合脚本覆盖当前两个文件。合并记录及编译内容核对见该目录的 `merge_manifest.json` 和 `verification.json`。

本轮只整理文件组织，未改文章文字、公式、数字、算法代码或实验数据。绘图脚本的 `--figures-only` 模式不重建表格；默认模式仍可能生成表格快照，生成后须明确同步到上述两份TeX，当前稿件不会自动读取这些快照。
