# 本轮来源与工作区清单

编辑版本：maintenance-editorial-2026-10-16-v1。编辑工作目录为当前文件所在的 `revision_2026-10-16/`；实际可编辑正文入口仍为其上一级的 `manuscript.tex`，全部正文节保留在单文件内。

## 授权与基线

执行依据为仓库 `proposal/UCB-AA删除与集合维护重构_Codex执行方案_v1.0.md`。本轮遵循其删除旧两阶段算法专题、以维护任务为主线的决定，不扩展理论、不修改策略、不开展新比较实验。

实际发现的M/S源文件是 `ucbaa_jasa_resubmission_2026-10-15/manuscript.tex` 与 `supplement.tex`。对应基线PDF哈希分别为：

```text
M eeecbd9680c3f14f046e9f898379f6abbb505f5195405a144552ff207ba2386d
S f2d4ebeec121c1f7e03405da8ff4273facde5d69f48ab2cadc0af8db348d0d6e
```

二者与修改方案提供的29页、35页基线一致。方案中的上传文件名和 `/mnt/data/` 定位并非本地路径。

## 快照及历史资源

`baseline/` 保存本轮编辑前的47个文件，包括两份PDF、全部活跃TeX/Bib源、原说明文件、实验源与旧图。逐文件大小、SHA-256和方案哈希见 `input_manifest.json`。旧实验完整档案仍在上一级 `experiments/original_submission_archive/`；旧FDA图与原六图仍在上一级 `figures/original_submission/`。旧两阶段分析和纯regret证明原文件也保留，修订后的补充材料不再输入它们。

## 编译依赖

主文件输入本稿局部的 `preamble.tex`，正文表格输入 `experiments/results/table_main.tex`，图形使用 `figures/` 中现有维护实验图，文献库为本稿的 `references.bib`。补充材料输入本轮整理的维护证明文件和 `computational_details.tex`，计算表格仍读取 `experiments/results/table_allocation.tex`。完整实际输入图由 `validate_revision.py` 记录于 `validation.json`。

引擎与文献系统保持原有的 `latexmk -pdf`、pdfLaTeX与BibTeX，不更换模板或字体。独立输出目录为 `revision_2026-10-16/build/`；实际命令、退出状态与日志在该目录及 `build-record.json` 中记录。`build.ps1` 为常用构建入口。

## 受保护资源

`input_manifest.json` 冻结了1,025个受保护文件的哈希，涵盖：原JASA稿、两份独立重构论文目录、`proposal/temporal_geometry_research/`、原持续维护研究包，以及本稿现有全部实验源、逐次结果、配置和图形。验证时再次计算哈希；这些资源不因本次删稿而删除或重命名。

本稿 `.bib` 与公共宏位于本目录；独立时间几何论文使用其自身目录的资源。此次只改本稿局部入口与新维护证明，不修改独立论文。原始方法ID、`CheckpointUCBAA` 类和代码文件名保留；论文展示名改为Checkpoint-UCB。

## 当前实际可用性

本地具备完整5,760次运行记录、配置、绘图数据、九方法runner及固定精度参考源。修改方案中原参考实现SHA为 `272815cbb45e2de1a99f849bd4718892ef6bc010d081e0eaf2ec45b21c746ef9`，可与本地副本核对。尚无经本轮核验的公开发布地址；正文按本地随附材料说明，不声称已经公开发布。

本轮未向外部仓库、期刊或其他人发送材料。历史创新性评审不重算，也不用于给本轮改稿评分。

## 当前投稿源码包

`submission-source.zip` 由25个白名单文件构成，包含当前两份文档、局部宏与文献、维护证明及三幅当前图，不包含旧算法专题、旧实验、原图或历史评估。相同源在 `submission_source/` 中完成独立构建，输出文本与实际审阅稿一致；构建产物不自动进入该ZIP。
