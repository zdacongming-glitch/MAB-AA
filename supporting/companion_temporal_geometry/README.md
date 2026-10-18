# 时间几何论文：第二阶段补强稿

版本日期：2026-10-13。原稿和阶段评审文件保持原样，本目录独立保存此次研究与写作。

## 阅读入口

- `manuscript.pdf`：英文正文，39 页；12pt、Letter 纸张、四边 1 英寸页边距。标题摘要页单倍行距，正文 1.8 倍行距，章节标题采用正常大小写。
- `jasa_submission.tex`、`jasa-reference.bst`：正文排版和 ASA 参考文献样式；核查依据及范围见 `audit/JASA_格式调整记录_2026-10-13.md`。
- `supplement.pdf`：完整数学证明，26 页；S7 是本轮新增随机到达正面理论。
- `computational_supplement.pdf`：完整实验设计、精确 Bayes 递推、敏感性图、扩展比较及旧实验，12 页。
- `研究补强与评审回应.md`：逐条对应阶段评审，报告新增成果及限制。
- `assessment/final_innovation_report.md`：最终创新性评估；逐轮原始记录位于 `assessment/stage2`。
- `README_reproduction.md`：运行步骤、软件版本、脚本与图表映射。

正文主张的是确定到达日程下常数因子意义的精确速率；新增随机日程结果限制在固定批次模板、已知终点和首批到达揭示公共伸缩的模型。实验没有估计连续奖励环境的 minimax supremum，也没有声称 MC-MOSS 在每个环境中优于其他方法。

## 本轮实际完成

新增四组实验共 584,704 条策略轨迹、1,520,745,272 个实际模拟策略决策轮次。随机到达研究的强制单臂前缀用精确二项充分统计量生成，其轮次未计入上述数目。原有 8,192 条轨迹另行保留，不重复计入新增规模。精确 Bayes DP、软件审计与有限理论诊断也不计入此轨迹总数。

完整理论证明、新结果的隔离审查、保存数据复算、原始策略动作核对和 PDF 编译检查均已执行。有限数值诊断不代替证明，模型审查也不等于形式认证或外部同行评审。

## 复现

```text
python reproduce.py --verify
python reproduce.py --stage2
python reproduce.py --full
python reproduce.py --figures
python reproduce.py --build
```

`--verify` 验证已有结果；`--stage2` 重跑新增实验；`--full` 也重跑旧实验；`--figures` 从数据生成图表；`--build` 编译三份稿件。依赖见 `requirements.txt`；编译需要 TeX Live 或兼容环境中的 pdflatex、bibtex。数据均为模拟，无受限外部数据，不需要助手 skill 才能复现。

文风已按统计研究论文调整，移除错误机制归因和泛化措辞。三份汇编 LaTeX 经 watermarks-remover 检查和单独副本清理，未检出可删除的不可见字符，清理前后逐字节相同。此项不是对统计式文本水印的检测或清除保证。
