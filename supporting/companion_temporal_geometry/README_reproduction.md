# 复现说明

所有命令在本文件所在的重构目录运行。Python 包的实测版本列在 `requirements.txt`；记录环境是 Python 3.11.7。编译 PDF 另需 TeX Live 或等价安装提供 `pdflatex` 和 `bibtex`。旧版代码副本和已有原始结果均包含在本目录，运行不依赖目录外的原论文材料。

## 推荐核查

```text
python -m pip install -r requirements.txt
python reproduce.py --verify --build
```

不带参数的 `python reproduce.py` 等同于 `--verify`。核查会执行原有整数容量等有限诊断、新随机到达定理的有限诊断、八组有理数精确 Bayes 动态规划与独立奖励树核对，以及实验 A、B、C、多批次伸缩实验的原始数据验证和部分逐动作重放。B 还检查 KL 根求解、TS 后验抽样、隐藏未来的前缀不变性、两因素公式及原始 MC 实现一致性。核查不重跑全部 Monte Carlo 轨迹。

`--build` 编译三份文档：`manuscript.pdf`、`supplement.pdf`、`computational_supplement.pdf`。每份文档先建立辅助文件，再运行所需的 BibTeX 和三轮交叉引用编译；未解决引用、引文或溢出版面等问题会使命令报错。汇总见 `audit/build_report.json`。该检查不能替代人工阅读 PDF 图表。

## 全部重跑

```text
python reproduce.py --full --build
```

这会重跑保留的第一阶段研究，以及第二阶段 A（相容困难族）、B（机制消融和基线）、C（随机日程与共同环境）、多批次公共伸缩实验和精确 Bayes 基准，重建图表后执行全部核查。参数和种子固定在脚本中；B 的开发运行与最终运行分开，C 和伸缩实验亦使用独立开发／评估随机流。重跑会更新本目录的计算输出，保留的阶段一原文材料不受影响。

若只重跑新增研究，可用：

```text
python reproduce.py --stage2 --build
```

若仅从已保存的数据重绘图表，可用：

```text
python reproduce.py --figures --build
```

A、B、C 的生产重复数均按原始协议保留；伸缩研究用 64 个开发重复和 128 个独立评估重复。具体参数、分层加权方式、共同随机数、种子与解释限制分别见 `experiments_v2/geometry_protocol.md`、`experiments_v2/mechanisms_reproducibility.md`、`experiments_v2/random_appendix.tex` 和 `experiments_v2/stretch_reproducibility.md`。各实验 manifest 报告实测耗时；完整重跑涉及超过十亿个策略轮次，实际耗时随硬件和 Numba 编译缓存变化。

每条子命令的输出保存在 `audit/execution_logs`。命令失败时入口程序会停止，并给出对应日志路径。数值有限诊断和程序核查不替代论文中的证明；模拟中的有限先验或有限 gap 网格也不等同于完整 minimax 风险。
