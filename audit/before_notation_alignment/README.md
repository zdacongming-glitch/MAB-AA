# UCB-AA 的 JASA T&M 重投稿稿件

日期：2026-10-15。此目录服务于原 UCB-AA 的实质修订。独立时间几何论文的谱 minimax、MC-MOSS、容量与随机到达成果没有并入本稿。原 PDF 与后续研究目录均保留。

## 阅读顺序

1. `manuscript.pdf`：英文主稿，18 页。保留原稿作者顺序，重写问题、方法、理论与实验；主要贡献是可靠集合维护的成本。
2. `supplement.pdf`：完整英文证明与计算补充，18 页，包含本轮新增分位数下界及兼容窗口截断下界。
3. `response_to_reviewers.md`：针对提供的五页审稿报告逐项回复；明确撤回有实质错误的旧证明结论，并对应本轮结果。
4. `revision_map_zh.md`：原稿、研究材料、导师一致性问题与独立新文之间的边界映射。
5. `research_report_zh.md`：本轮新增结果、实际实验、前后两轮创新性评估及尚未解决的问题。

主稿七个章节已按原顺序合并到 `manuscript.tex`，直接在这个文件中编辑正文。`preamble.tex` 保存公共宏包与命令，`supplement.tex`、`theory/` 保存补充材料，`references.bib` 保存参考文献。原分节文件及合并前主文件备份在 `audit/before_section_merge/`，仅供追溯；合并记录见 `audit/section_merge.json`。本次只调整源文件组织，未改论文内容，也未重新评估创新性。`experiments/` 保存自包含代码、固定配置、逐次结果和软件版本；`figures/` 保存作图代码与矢量图。`assessments/` 保存真实隔离评估轮次、冻结材料、执行标识和统计汇总；其中的分数不属于论文正文。

## 编译与复现

在本目录使用 TeX Live 及 Python：

```powershell
./build.ps1
python -X utf8 experiments/run_experiments.py
python -X utf8 figures/gen_fig_performance.py
python -X utf8 audit/verify_delivery.py
```

实际 Python 包版本见 `experiments/requirements.txt`。实验共 4 个环境、9 个方法、每环境 160 个配对重复，每次 20,000 次真实采样，共 5,760 次运行。重新运行会更新实验输出；评估证据包是冻结副本，不会随之自动改分。完整路径、配置和输入源的字节摘要见各 manifest。

主文图中的区间为 Monte Carlo 不确定性。零观测误报不构成对所有环境和无限时间的可靠性验证。检查点策略在若干场景被保留历史的强识别适配同时改善两项指标；稿件明确报告这一负面结果。

## 本稿的准确状态

已完成全文、完整证明、可复现实验和逐项回复草稿；核心数学接口经过额外独立审计。一般异质、任意重叠到达和所有面积预算的最优前沿仍未证明，暂缓端也没有匹配的 regret 下界。固定精度程序不能继承附录中另一种可纠错构造的强一致性。

这是供作者审阅的重投稿研究稿，未向期刊或其他人发送。当前出版社作者页的全部格式规则未能核实，因此没有宣称满足现行页数、摘要字数或匿名要求。`manuscript.tex` 的匿名开关可以生成无作者版本。回复信也没有假造未提供的编辑决定信或早前评审原话。JASA 的计算复现要求依据当前[官方指南](https://jasa-acs.github.io/repro-guide/)准备；其余核查范围见 `audit/literature_scope.md`。

写作使用了用户指定的统计写作、证明、humanizer 与 watermarks-remover 技能。自然语言精修和不可见 Unicode 检查是不同步骤；后者没有发现可清除字符。没有未知统计水印检测器或密钥，因此不声称文本水印被认证移除，也不将文本宣称为人类独立撰写。作者、引文、公式和数据来源均保留。
