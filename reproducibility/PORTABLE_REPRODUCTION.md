# 独立目录复现

只保留当前重投稿文件夹也可以运行下面的流程，不需要同级 `proposal`、原研究目录或 `JASA-template`。当前论文的唯一编辑入口仍是 `manuscript.tex`。执行入口为根目录 `reproduce.py`；它不会更新论文、冻结策略代码或冻结结果。

## 环境

生成数值图表与模拟需要 Python、NumPy、Numba、pandas、SciPy、matplotlib。C16、P16、F17 原始数值运行采用 Python 3.13.5；五个主要库的实际版本记录在 `requirements-fccp.txt`，可在独立虚拟环境安装：

```text
python -m pip install -r reproducibility/requirements-fccp.txt
```

旧 Checkpoint 四场景实验记录的是 Windows、Python 3.11.7 和 `requirements-legacy-checkpoint.txt` 指向的版本。P16 的可选符号审计另需 `requirements-optional-proof-audit.txt`。这些是实际版本记录，不是完整传递依赖锁文件。跨操作系统、Python、Numba或随机数后端时，不承诺逐动作或输出文件字节相同。文件哈希只验证交付数据与源资料的身份。

编译论文还需要包含 pdfLaTeX、BibTeX、latexmk 的 TeX 发行版，以及论文所用的常见宏包。原始模拟不需要 GPU。

## 推荐验收顺序

在当前文件夹运行：

```text
python -B -X utf8 reproduce.py --verify
python -B -X utf8 reproduce.py --figures
python -B -X utf8 reproduce.py --smoke
python -B -X utf8 reproduce.py --build
```

也可以在其他工作目录给出 `reproduce.py` 的完整路径。每次调用都会在 `_reproduced/时间戳-随机后缀/` 新建独立目录。用 `--workspace 新的专用输出目录` 改变输出基目录；程序拒绝把工作区放进冻结输入、原稿或历史审计目录。

| 入口 | 验收范围 | 主要输出 |
|---|---|---|
| `--verify`，也是默认动作 | 数值与研究支持清单、原始包哈希、两个历史轨迹 gzip 解压流哈希、全部正文图和文献库、Python语法与本地模块依赖、原稿C/E驱动配置、F17端点数据核算 | `verification.json`、`fccp-endpoint-check.json` |
| `--figures` | 从已有端点数据重算F17表格字符串与两张正文图，并从旧CP数据重画历史图；不调用策略模拟 | `paper/revision2/generated/`、`paper/revision2/analysis/`、`paper/figures/` |
| `--smoke` | 600步兼容动作、320步指定观测API动作、10个同状态动作检查、6个非法调用检查，以及六个生产驱动的导入和命令帮助 | `paper/revision2/analysis/interface-checks.json`、`smoke-scope.json` |
| `--build` | 在隔离目录复制单文件稿件、文献和全部引用图，编译完整论文 | `paper/manuscript.pdf`、`paper/build/` |

所有动作都有 `commands.json` 和逐命令日志。程序比较执行前后冻结输入与论文源的SHA-256；有变化就报错。`--verify`读取交付清单中的本地目标路径，不访问其中作为来源说明记录的原电脑绝对路径。Numba缓存和Matplotlib缓存也写入该次工作目录。

`--figures`仅在工作副本中对旧编辑脚本做一处路径适配，把 `REPO = PROJECT.parent` 改为 `REPO = PROJECT`，并传入 `--release-only`；具体前后哈希记录在 `path-adapter.json`。这是为了禁止再探测文件夹之外的原研究资料。冻结策略和结果不变。生成的表格保存在JSON字符串中，不会把当前稿件重新拆成多个TeX文件，也不会自动替换稿件中的表格。

## 从随机数与冻结配置重新运行

这些命令会真实运行完整模拟，可能耗时较长。本次整理并未执行它们：

```text
python -B -X utf8 reproduce.py --simulate --suite fccp --workers 4
python -B -X utf8 reproduce.py --simulate --suite ccp --workers 4
python -B -X utf8 reproduce.py --simulate --suite frontier --workers 4
python -B -X utf8 reproduce.py --simulate --suite checkpoint
```

默认 `--workers 1` 串行运行。并发数只分配互不重叠的场景或分片，不改变冻结种子、策略或终点。各代代码和输出始终在独立工作副本中，原来的冻结结果不会被覆盖。

| 数据代际 | 完整驱动方式 | 预期端点记录 |
|---|---|---:|
| F17主测试及修正ALL | `study_v2.py --stage holdout`加`study_matched.py --stage matched-all`；显式跑齐全部worker，再运行`analyze.py` | 27,648 + 1,152 |
| C16 | 10场景乘4个16次分片，冻结策略表与offset为0/16/32/48，再运行`analyze.py` | 13,440 |
| P16 | 原驱动固定4个worker分片，四个全部完成后运行`analyze_holdout.py` | 12,672 |
| 旧CP | 本地`run_experiments.py`与原样`reference_cp_ucb_aa.py`，完整四场景、九方法、160次 | 5,760 |

`--suite all`只顺序运行上表四代。开发、调参、过期或无效版本保留在各包中，不和冻结测试混合。单独执行某个历史驱动的默认worker往往只能完成部分场景；统一入口已补齐全部分片。复跑结果在 `simulation-outputs.json` 列出，应按场景、重复编号、方法配对比较指标，排除运行时间列。不同环境下若出现数值路径差异，需要报告差异，不能通过调整参数强行得到原表。

原CSV中每次调用的运行时间累计：F17主测试约1,408秒，修正ALL约102秒，C16约592秒，P16约721秒，共约47.1分钟。它们来自原始机器和不同计时边界，不能解释成当前机器完整复现的墙钟时间；JIT编译、文件写入、并发、开发阶段和历史原稿实验另计。旧CP记录的13.5秒仅属于它自身的历史计时。

## 原稿C/E历史实验

原稿的100次C/E最终比较另有显式入口：

```text
python -B -X utf8 reproduce.py --simulate --suite original --workers 4
```

它使用`ce_five_algo_runner.py --R 100 --seed 20260309`，配置与归档的两份`config.json`逐项核对。原包里的`manual_ce_final.py`使用20万轮和四算法，和归档的6万轮、五算法不是同一次研究，不能拿它重跑原稿已报告的表。`--suite all`不隐式启动这批额外历史实验。

两份原始`raw_checkpoint.csv`已按gzip无损压缩保存；`--verify`会同时检验压缩文件和解压后的原始大小、SHA-256。pandas可直接读取`.csv.gz`，也可解压到工作目录读取。原稿的绘图、搜索、额外开发脚本均留在`experiments/original_submission_archive/source/`。历史调参过程、无效版本和原始图不因本次整理而改写；最终配置复跑不等于重新执行全部曾尝试过的研究路线。

## 本次检查的实际范围

本次整理实际执行了只读核验、端点再分析绘图、短API检查、驱动导入以及完整稿件编译。未重新运行任何完整性能比较，也未把历史证明或模拟诊断表述为独立形式化验证。实际命令及结果摘录保存在`reproducibility/commands.json`和`acceptance-*.json`。最终Git暂存内容的独立目录验收另由仓库发布记录给出。
