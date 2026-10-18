# MAB-AA：JASA 重投研究的数值复现仓库

本仓库保存 UCB-AA / F-CCP 重投研究的数值实验代码、冻结协议、逐次结果、绘图程序及研究支撑材料。GitHub 地址为 <https://github.com/zdacongming-glitch/MAB-AA>，沿用原有私有仓库及其历史，未更改可见性。

## 与 Overleaf 的分工

本地 `MAB-AA-reproducibility/` 是这个 GitHub 仓库的独立检出目录。相邻的 `ucbaa_jasa_resubmission_2026-10-15/` 供日常改稿，属于上一级 Overleaf Git 仓库；它只保留 `manuscript.tex`、`references.bib` 和稿件实际引用的五张 PDF 图。正文、补充材料、证明及表格仍在唯一的 `manuscript.tex` 中。

本仓库根目录保存同一稿件及五张图的完整快照，用于离开 Overleaf 后独立复现。请在 Overleaf 目录编辑稿件，再同步到这里。GitHub 原有的 `JASA-template/` 保留原投稿件，未被覆盖。历史稿件、审稿材料和评审记录均在本仓库归档目录中，不是当前编辑入口。

```text
MAB-AA/                                  # 上一级 Git：Overleaf
├── JASA-template/                        # 原投稿件
├── ucbaa_jasa_resubmission_2026-10-15/    # 精简稿件目录，7 个文件
└── MAB-AA-reproducibility/               # 独立 Git：本 GitHub 仓库
    ├── manuscript.tex + references.bib   # 完整稿件快照
    ├── experiments/                     # 全部实验代码、协议及结果
    ├── figures/ + revision2/             # 绘图、分析、构建及历史整合材料
    ├── supporting/                      # 理论来源、原稿与审稿材料
    ├── audit/ + assessments/            # 修改及创新性评审记录
    ├── reproducibility/                 # 来源清单、哈希及验收记录
    └── reproduce.py                     # 独立复现入口
```

## 安装与检查

在本仓库根目录运行。Python 依赖使用本轮验证的固定版本；编译论文还需 pdfLaTeX、BibTeX 和 latexmk。

```powershell
python -m pip install -r requirements-reproduce.txt
python reproduce.py --verify
python reproduce.py --figures
python reproduce.py --smoke
python reproduce.py --build
```

这四个动作分别核验冻结材料、从已有结果重绘图表、检查算法接口和编译完整论文。所有新输出写入 `_reproduced/` 的独立工作目录，不覆盖冻结数据。它们不代表重跑全部长批次数值实验。详细命令见 [PORTABLE_REPRODUCTION.md](reproducibility/PORTABLE_REPRODUCTION.md)。

```powershell
python reproduce.py --simulate --suite all --workers 4
python reproduce.py --simulate --suite original --workers 4
```

`all` 包含 F17 原测试及修正 ALL、C16、P16 和旧 Checkpoint；`original` 单独重跑原投稿 C/E 实验。也可分别选择 `fccp`、`ccp`、`frontier`、`checkpoint`。开发筛选材料保留在各研究目录，统一入口不重新选参。

新增的九类 regret 基线筛查尚未回填论文，独立入口为：

```powershell
cd experiments/regret_baseline_screen_2026-10-17
python -X utf8 validate_new.py
python -u -X utf8 runner.py --protocol protocol.json --output rerun_results --workers 8
python -X utf8 analyze.py rerun_results --protocol protocol.json
```

该研究的 `results/` 保存全部 19,584 条正式运行记录，完整说明与比较结果见其 [README](experiments/regret_baseline_screen_2026-10-17/README.md) 和 [REPORT](experiments/regret_baseline_screen_2026-10-17/REPORT.md)。重新运行请指定新的输出目录。

## 材料位置与边界

- `experiments/fccp_frozen/`、`ccp_frozen/`、`frontier_frozen/`：三轮完整代码、协议、开发及测试数据。
- `experiments/results/`：旧 Checkpoint 冻结数据；`experiments/original_submission_archive/`：原投稿 C/E 源码与结果，大型 CSV 以无损 gzip 保存。
- `supporting/`：执行方案、理论来源、原稿、审稿与回复材料，及伴随谱研究的来源档案。
- `audit/innovation_assessment_2026-10-18/`：最新创新性评审；`algorithm_guide/`：算法解释图及绘制代码。
- `reproducibility/repository-split-2026-10-18/`：本次迁移的逐文件哈希、稿件对应关系与独立验收记录。

原有 599 项数值材料和 120 项支撑材料的导入清单保持原样，原始冻结协议、算法代码和数据未因迁移修改。旧清单中的机器路径说明历史来源，当前复现入口不读取这些路径。`import_*`、历史整合及评审采集脚本属于来源档案，不应作为当前实验入口运行；历史记录中的旧目录名也保留原貌。

F17 最初未成功编译的探索版本只留下日志和引擎哈希，没有完整引擎源码，不能精确重建该失败版本；用于最终有效开发和测试的冻结源码齐备。参见 [NUMERICAL_SOURCES.md](reproducibility/NUMERICAL_SOURCES.md)。

## 稿件同步与提交

```powershell
python scripts/sync_paper.py --check
python scripts/sync_paper.py --from-overleaf --apply
```

同步只处理七个稿件文件，以双方上次一致的哈希为基线。双方各自修改且不一致时会拒绝覆盖。单独克隆本 GitHub 仓库时无需存在 Overleaf 目录，所有复现命令仍可运行；同步时可用 `--overleaf-dir` 指定作者稿件目录。

在本目录提交和推送只影响 GitHub；在上一级 `MAB-AA/` 提交和推送只影响 Overleaf。上一级忽略整个复现仓库，实验材料不会随日常改稿再次进入 Overleaf。本次调整通过普通提交完成，保留两个远程仓库的历史。
