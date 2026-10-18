# 动态到达 Bandit 仿真框架（simulation20260309）

本项目用于复现实验：在有新臂持续到达的多臂老虎机环境中，比较 `custom_elim / ucb / moss / naive_elim` 四种算法的表现。

主入口：

```bash
python runner.py --help
```

## 1. 环境准备

建议 Python 版本：`3.10+`。

依赖安装：

```bash
pip install numpy pandas matplotlib tqdm
```

Windows PowerShell 进入项目目录：

```powershell
cd "D:\博士学习\科研\Bandit with Arriving Arms\simulation20260309"
```

Ubuntu 服务器示例：

```bash
cd /path/to/simulation20260309
python3 -m venv .venv
source .venv/bin/activate
pip install numpy pandas matplotlib tqdm
export MPLBACKEND=Agg
```

## 2. CLI 参数速查

- `--mode smoke|full`
- `--arrival bernoulli|poisson|burst`
- `--R`
- `--n-jobs`
- `--progress auto|on|off`
- `--verbose-progress`
- `--progress-refresh`
- `--max-checkpoints`
- `--scenarios`
- `--algos`
- `--no-plots`
- `--output-dir`
- `--grid-profile default|bcde_cover`

## 3. 当前算法实现说明

- `custom_elim`：参数 `N` 直接取总时长 `T`，淘汰精度使用 `\tilde{\Delta}_0=1`、`\tilde{\Delta}_m=1/m (m>=1)`。
- `moss`：当前实现已经改成使用“当前已知臂数” `K_t`，不再使用 `Khat`。
- `naive_elim`：当前实现已经改成与 `custom_elim` 共用同类 buffered round-elimination 框架，只保留 reference set、elimination 次序和 pre-elimination 是否可淘汰旧臂这几个差异。

## 4. Scenario C 和 Scenario E 是什么环境

这一节不只是列参数，而是先用直观语言说明这两个场景分别在模拟什么，再解释参数。

### Scenario C：系统里会不时跳出“明显更好”的新臂

可以把 Scenario C 理解成下面这个故事：

- 一开始系统里先有 `K0` 个初始臂，它们大多来自一个普通质量分布。
- 之后每一轮都有概率 `lambda` 出现一个新臂，也就是“常规到达”。
- 除了这些常规到达外，环境还会在若干预设时间点，强行插入几个质量明显更高的新臂。
- 这些“关键新臂”会逐步把当前最优均值往上抬，所以算法必须既能在旧臂中稳定筛选，也要能在关键时刻迅速识别晚到的优臂。

在代码里，Scenario C 的构造方式是：

- 初始臂与普通到达臂都先按基础混合分布采样均值。
- 然后在 `gamma` 指定的若干相对时间点 `tau_k = floor(gamma_k * T)`，额外插入均值为 `r0 + k * Delta_step` 的新臂。
- 因此，Scenario C 的核心难点是：最优臂不是一开始就出现，而是会在中后期被更强的新臂逐步替换。

#### Scenario C 主要参数含义

- `T`：总交互时长，也就是总拉臂次数上限。
- `K0`：初始时刻就已经存在的臂数。
- `arrival_mode=bernoulli`：每轮独立地按伯努利方式决定是否有新臂到达。
- `lambda`：伯努利到达概率；在这个项目里 `rho` 也同步设成相同值。
- `M`：elimination 类算法的轮数上限。
- `gamma=[g1,g2,g3,...]`：关键新臂到达的相对时间位置；例如 `0.2` 表示在 `0.2T` 左右出现。
- `r0`：第一只关键新臂的基准均值起点。
- `Delta_step`：后续关键新臂相对前一只关键臂的均值提升步长。
- `pi_good`：基础混合分布里抽到“较好臂”的概率。
- `mu_h`：较好臂均值区间的上界。
- `delta`：较好臂均值区间宽度；较好臂大致落在 `[mu_h-delta, mu_h]`。
- `mu_l`：普通臂均值区间下界。
- `mu_m`：普通臂均值区间上界。

### Scenario E：初始就有一批接近最优的好臂，后续还会继续来“近优臂”

可以把 Scenario E 理解成下面这个故事：

- 一开始系统中就有 `K0` 个初始臂。
- 其中前 `m0` 个初始臂不是普通臂，而是“接近当前最优”的高质量臂。
- 后续仍然按伯努利方式不断有新臂到达。
- 新到达的臂里，有一部分会以概率 `p_join_near` 成为“近优臂”，它们的均值非常接近 `mu_top`；其余到达臂则还是来自普通基础分布。

这意味着 Scenario E 不是“偶尔来一只特别强的臂”，而是更像：

- 初始阶段系统里就已经有一些不错的候选；
- 后续还会不断补充质量很接近最优的新臂；
- 算法需要在很多“都不差、彼此差距很小”的臂之间持续识别并跟踪好的那一批。

#### Scenario E 主要参数含义

- `T`：总交互时长。
- `K0`：初始臂个数。
- `arrival_mode=bernoulli`：每轮独立判断是否有新臂到达。
- `lambda`：到达概率；`rho` 在当前配置中与它相同。
- `M`：elimination 类算法的轮数上限。
- `m0`：初始 `K0` 个臂中，前 `m0` 个被强制设成近优臂。
- `mu_top`：近优臂围绕的高均值中心。
- `Delta_min`：近优臂相对 `mu_top` 的最小差距尺度；代码里近优臂大致来自 `mu_top - U(0, Delta_min)`。
- `p_join_near`：每个新到达臂成为近优臂的概率。
- `pi_good`：如果新臂没有进入近优组，那么它再从基础混合分布里抽到较好臂的概率。
- `mu_h`：基础分布中较好臂的上界。
- `delta`：较好臂区间宽度。
- `mu_l`：普通臂区间下界。
- `mu_m`：普通臂区间上界。

## 5. 本轮最终使用的 Scenario C / E 参数

### Scenario C 最终使用参数

- `T=200000`
- `K0=5`
- `arrival_mode=bernoulli`
- `lambda=rho=0.005`
- `M=6`
- `gamma=[0.2, 0.5, 0.8]`
- `Delta_step=0.05`
- `r0=0.6`
- `pi_good=0.1`
- `mu_h=0.9`
- `delta=0.1`
- `mu_l=0.1`
- `mu_m=0.5`

直观上，这表示：

- 一开始只有 5 个初始臂。
- 每轮以 `0.5%` 的概率到达一个常规新臂。
- 在总时长的 `20% / 50% / 80%` 附近，还会额外出现 3 只逐步更强的关键新臂。

### Scenario E 最终使用参数

- `T=200000`
- `K0=20`
- `arrival_mode=bernoulli`
- `lambda=rho=0.005`
- `M=6`
- `m0=5`
- `Delta_min=0.01`
- `p_join_near=0.3`
- `mu_top=0.8`
- `pi_good=0.1`
- `mu_h=0.9`
- `delta=0.1`
- `mu_l=0.1`
- `mu_m=0.5`

直观上，这表示：

- 一开始有 20 个初始臂，其中前 5 个就是接近最优的好臂。
- 后续每轮也以 `0.5%` 的概率有新臂到达。
- 每个新臂到达时，有 `30%` 的概率它会是一只“接近最优”的臂，而不是普通臂。

## 6. Scenario C/E 定向搜索结果说明

本轮专门为 `scenario C` 和 `scenario E` 新增了两个脚本：

- `scenario_ce_runner.py`：用于定向搜索和最终成图。
- `manual_ce_final.py`：基于已选配置重跑 4 个算法并输出最终图。

由于 `MOSS` 在长时长配置下运行较慢，这次实际采用了“关键参数优先”的部分网格搜索，而不是把所有环境参数完全铺开。

- Scenario C：重点搜索 `T / K0 / lambda`
- Scenario E：重点搜索 `T / K0 / lambda`，并在较小候选集上比较
- 最终成图采用 `R=12`

当前最终产物目录：

- `outputs/ce_final_manual_20260310_064732/`
- `outputs/ce_final_manual_20260310_064732/scenario_C/plots/`
- `outputs/ce_final_manual_20260310_064732/scenario_E/plots/`

## 7. 推荐命令预设

快速检查：

```bash
python runner.py --mode smoke --scenarios B,C,D,E,F --R 10 --n-jobs 4 --progress on --output-dir outputs
```

日常对比：

```bash
python runner.py --mode full --scenarios B,C,E --R 50 --n-jobs 8 --progress on --max-checkpoints 2000 --output-dir outputs
```

压缩版 BCDE：

```bash
python runner.py --mode full --grid-profile bcde_cover --R 30 --n-jobs 8 --progress on
```

当前 C/E 定向搜索命令：

```bash
python scenario_ce_runner.py --critical-only --search-r 1 --search-n-jobs 1 --final-r 12 --final-n-jobs 12 --max-checkpoints 600
```

当前 C/E 最终四算法重跑命令：

```bash
python manual_ce_final.py --final-r 12 --n-jobs 12 --max-checkpoints 600
```

## 8. 输出结构

常规运行会在 `outputs/run_时间戳/` 下生成：

- `raw_final_metrics.csv`
- `raw_checkpoint_metrics.csv`
- `agg_final_metrics.csv`
- `agg_checkpoint_metrics.csv`
- `config.json`
- `plots/`

定向 C/E 脚本会额外生成：

- `outputs/ce_final_manual_时间戳/scenario_C/`
- `outputs/ce_final_manual_时间戳/scenario_E/`
- `outputs/ce_final_manual_时间戳/search/`
- `outputs/ce_final_manual_时间戳/summary.json`

## 9. 验收清单

1. `python runner.py --help` 能正常显示参数。
2. 输出目录中包含 `raw_* / agg_* / config.json`。
3. 启用绘图后，`plots/` 中能看到结果图。
4. `scenario C / E` 的参数说明与实际 `config.json` 一致。
