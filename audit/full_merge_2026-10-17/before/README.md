# JASA T&M 重投稿件：第二轮整合

本轮按 `proposal/第二轮稿件修改_FCCP整合_Codex执行方案_v2.0.md` 整合 C16、P16、F17 三轮成果。正文以 F-CCP 为主算法；Checkpoint-UCB 保留为原上界的解析见证，ABM 保留为指定重复更新族的中间预算见证。一般维护成本理论与原统计问题保留。

## 日常编辑与阅读

- `manuscript.tex` / `manuscript.pdf`：完整正文，7节。
- `supplement.tex` / `supplement.pdf`：完整补充材料，S1—S17。
- `references.bib`：参考文献数据库。

全部导言、宏、算法、公式、证明和表格代码已经内联到这两个 `.tex` 文件。没有 `input` / `include` 子文件依赖；平时直接修改这两个文件即可。图片仍作为独立资源文件引用。`revision2/` 的 JSON 是本轮修订记录，不是 TeX 编译依赖，也不要求日后通过它们改稿。

## 编译

在本目录运行：

```powershell
python revision2/build_papers.py
```

使用现有 pdfLaTeX、BibTeX 和 latexmk，往返编译补充与正文以收敛交叉引用；中间产物在 `build/`，最终两份 PDF 更新到本目录。`build.ps1` 提供相同的构建顺序。没有修改 PowerShell 执行策略。

## 数据、图表与复现

- `experiments/fccp_frozen/README_release.md`：生产代码入口、接口、三代数据身份、依赖和复现命令。
- `revision2/generated/`：由冻结端点数据重绘的两张正文图；表格代码已经内联。
- `revision2/analysis/`：只读再分析、方法映射、完整逐场景结果和核验报告。
- `revision2/claim-map.csv`、`notation-map.md`、`task-status.md`、`change-log.md`：数学归属、记号与逐项修改记录。
- `revision2/blocked-items.md`、`future-research.md`：书目信息限制及本轮未授权开展的后续研究。

本轮使用已有冻结模拟结果，不新增性能实验或定理。F17 主测试为27,648条，ALL修正为1,152条；修正后的主分析替换旧ALL配置，仍为27,648条。失败路径和不利尾部均保留。原四场景Checkpoint实验完整迁至S17，不与F17合并。

## 可恢复的旧版与输入

`revision2/baseline/` 保存本轮修改前的两份源码、两份20页PDF、文献库和构建入口。`revision2/source-map.json` 记录原件与研究包哈希。`audit/source_layout_2026-10-16/` 是更早的拆分源码及第一轮修订档案，不是当前编译入口。三轮完整原ZIP保存在 `experiments/fccp_frozen/original-archives/`。

署名、作者次序、通信信息、稿件日期及匿名设置沿用本轮基线。当前本地发行不等于公开仓库或永久存档；没有擅自提交、推送或上传。
