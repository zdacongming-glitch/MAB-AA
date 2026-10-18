# JASA T&M 重投稿件：独立复现包

本目录收齐重投稿件使用的源码、冻结模拟结果、绘图程序、理论来源和审稿修改材料，可独立从Git取出使用，无需作者机器上的 `proposal/` 或其他研究目录。第二轮执行方案已保存在 `supporting/proposal/`。正文以F-CCP为主算法，Checkpoint-UCB和ABM分别保留其解析见证身份。

## 日常编辑与阅读

- `manuscript.tex`：唯一可编辑的TeX入口，包含正文7节、补充材料S1—S17及统一参考文献。
- `manuscript.pdf`：与该源码对应的完整PDF。
- `references.bib`：参考文献数据库。

全部导言、宏、算法、公式、证明和表格代码都在 `manuscript.tex` 中，没有 `input` / `include` 或外部TeX文档引用。正文之后有明显的 `BEGIN MERGED SUPPLEMENTARY MATERIAL` 注释分界；补充部分保留S节号和S页码，其公式、表、图、算法也使用S前缀。所有交叉引用在同一PDF内跳转。图片和文献库仍为独立资源。

此前的 `supplement.tex`、独立PDF和编译产物已经归档，不再是编辑入口。`revision2/` 的JSON及审核记录保留为第二轮合并前的历史材料；旧整合脚本已加保护，不能覆盖当前完整稿件。

## 安装与复现

在本目录运行。`requirements-reproduce.txt` 固定了本轮实际验证所用的Python 3.11依赖；每代研究的原生成环境另存于各自材料中。构建PDF还需要pdfLaTeX、BibTeX和latexmk。

```powershell
python -m pip install -r requirements-reproduce.txt
python reproduce.py --verify
python reproduce.py --figures
python reproduce.py --smoke
python reproduce.py --build
```

四个动作依次检查包内哈希及冻结数据、从已有结果重绘图表、运行短接口检查、构建完整论文。它们在 `_reproduced/` 下各建独立工作区，记录实际命令和结果，保护原稿和冻结数据。`--figures`不会重新模拟，`--smoke`也不是完整性能试验。详细操作见 `reproducibility/PORTABLE_REPRODUCTION.md`。

2026年10月17日已从Git暂存内容导出独立副本，在不含本地其他研究目录的环境中通过上述四项检查，并构建88页完整PDF。共599项数值材料和120项支撑材料通过导入哈希核对；Git导出前后冻结文件字节一致。验收记录见 `reproducibility/release-validation.json` 及同目录的 `release-*.json`。本次验收没有重跑全部长批次随机模拟。

完整重跑测试集使用：

```powershell
python reproduce.py --simulate --suite all --workers 4
python reproduce.py --simulate --suite original --workers 4
```

`all` 包括F17原测试及修正ALL、C16、P16和旧Checkpoint测试；`original` 单独重跑原投稿C/E的五算法实验。也可用 `--suite fccp|ccp|frontier|checkpoint` 单独选择。开发筛选的代码与结果全部归档，统一入口不重新选参。完整模拟在新工作区运行，耗时与JIT、并发和机器有关；新结果不承诺跨版本逐字节相同。

日常改稿后若要更新本目录的 `manuscript.pdf`，仍可运行 `python revision2/build_papers.py` 或 `build.ps1`，只构建唯一的 `manuscript.tex`。

## 数据、图表与复现

- `experiments/fccp_frozen/`：完整F17代码、协议、开发及测试结果、修正ALL和理论材料。
- `experiments/ccp_frozen/`、`experiments/frontier_frozen/`：完整C16、P16代码与冻结结果。
- `experiments/results/`：旧Checkpoint四场景结果；对应驱动和参考实现位于 `experiments/`。
- `experiments/regret_baseline_screen_2026-10-17/`：独立的纯regret扩展比较，包含九类新增基线、冻结参数、19,584条运行记录、配对分析和报告；结果尚未回填论文，重跑见该目录的 `README.md`。
- `experiments/original_submission_archive/`：原投稿C/E源码、配置、终点及检查点记录；大型原始CSV以无损gzip保存。
- `supporting/`：两轮计划、10月14日理论包、原稿、审稿及回复材料，以及伴随谱论文的完整来源档案。
- `reproducibility/`：来源盘点、导入哈希、独立目录验收和复现操作文档。
- `revision2/generated/`：由冻结端点数据重绘的两张正文图；表格代码已经内联。
- `revision2/analysis/`：只读再分析、方法映射、完整逐场景结果和核验报告。
- `revision2/claim-map.csv`、`notation-map.md`、`task-status.md`、`change-log.md`：第二轮内容整合时的数学归属、记号与逐项修改记录。
- `audit/full_merge_2026-10-17/`：本次单文件合并记录、内容保留核对和编译／版面检查。
- `revision2/blocked-items.md`、`future-research.md`：书目信息限制及本轮未授权开展的后续研究。

F17原测试27,648条，ALL修正1,152条，共28,800条；替换旧ALL后的主分析仍为27,648条。C16有13,440条，P16有12,672条，旧Checkpoint有5,760条。原投稿C/E另行保留，所有代际的失败记录均保留，不跨研究合并计算胜率。

原投稿两份检查点CSV合计约380MB，以约18MB的gzip收录，解压字节数和SHA-256均已与原件核对。可以直接用支持gzip的CSV读取器分析。逐文件映射见 `reproducibility/numerical-import-manifest.json` 和 `support-import-manifest.json`。

用于有效开发及测试结果的冻结源码均已齐备。一个历史局限是：F17最初未成功编译的探索版本仅留有日志和引擎哈希，没有对应完整引擎源码。该失败记录不支持精确重建，其边界保留在 `reproducibility/NUMERICAL_SOURCES.md` 中。

## 可恢复的旧版与输入

`audit/full_merge_2026-10-17/before/` 保存本次合并前完整的两份TeX、25页正文PDF、64页补充PDF、文献库和构建入口。归档目录仅供恢复，日常只编辑根目录的 `manuscript.tex`。

`revision2/baseline/` 是更早的20页稿件基线；`revision2/source-map.json` 记录第二轮内容整合时的研究输入。`audit/source_layout_2026-10-16/` 为更早的拆分源码及第一轮修订档案。三轮完整原ZIP保存在 `experiments/fccp_frozen/original-archives/`。本次只调整文件组织和编号，研究内容、原始数据与算法代码未改变。

Git仅收录原来的 `JASA-template/` 与本目录两套稿件，以及根目录忽略规则。生成缓存、TeX中间文件和复现工作区不入库；所需源文件、最终结果和原始压缩档案入库，少量历史版面检查图随审计档案保留。目录内的 `.gitattributes` 保留原始换行字节，避免Windows自动转换破坏冻结哈希。

署名、作者次序、通信信息、稿件日期及匿名设置沿用当前稿件。Git版本管理不等于公开发布或永久存档；没有为本研究虚构公开URL或DOI。
