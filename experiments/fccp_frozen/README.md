# F-CCP：可调目标版本（2026-10-17 项目标识）

本包是对既有 CCP 的参数化扩展，不修改 Codex 正在处理的稿件。默认纯收益候选 F-R 不是标准 Thompson 的重命名：它使用 temperature=0.5 的 Beta 动作评分和独立的 MC-MOSS 指数差预算保护。`compatibility` 模式才是与指定基线完全等价的配置。

## 文件

- `研究报告_FCCP可调版本.md`：主要结论、全部基线比较、负面结果、适用范围。
- `theory.md`：六个编号结论的合同与证明；前沿最优性和普遍零余项基线支配不在成果内。
- `src/flexible_ccp.py`：面向真实交互的接口；只接受当轮新臂与已采样奖励。
- `src/flexible_v2.py`：冻结的主实验引擎；不可为让结果更漂亮而修改后覆盖原实验。
- `src/flexible_matched.py`、`src/matched_all.py`：仅修正 ALL 适配对照的经验成本输入；不改 F-CCP。
- `src/ccp_primitives.py`：原 CCP 的置信区间、检查点、比较规则、两端点规划和谱工具。
- `protocols/*-freeze.json`：每轮开发与测试的环境、参数、种子及哈希。
- `results/holdout-all.csv`：27,648 条原始主测试记录。
- `results/matched-all-all.csv`：1,152 条修正 ALL 对照记录。
- `results/holdout-summary.csv`：包括修正对照、每场景均值/标准误/95%经验分位/最大值/失败次数。
- `results/pure-regret-paired.csv`：F-R 对五个指定基线的配对差与区间。
- `results/joint-paired.csv`：联合目标的配对比较。
- `results/*paths.npz`：各场景前四个重复、间隔200轮的诊断路径；不是全部逐轮路径。
- `audit.md`、`results/implementation-audit.json`：数值与实现审计；无独立外部复核或形式化验证。
- `assessment.json`：仅本轮新增贡献的单次创新性评价。
- `dependencies/ccp_theory_20261016.md`：原 CCP 理论的原样副本，注明证明依赖，非本轮新增结果。

## 运行环境

实际使用 Python 3.13.5、NumPy 2.3.5、Numba 0.65.1；另需 pandas、SciPy、matplotlib。环境版本详见审计 JSON。Numba 缓存禁用以避免跨模块旧缓存。

```bash
python -m pip install numpy numba pandas scipy matplotlib
PYTHONPATH=src python src/demo.py
PYTHONPATH=src python src/audit.py
python src/analyze.py
```

复跑前复制本研究包到新的目录，避免覆盖归档数据。四个独立进程（可顺序运行）重现主测试：

```bash
python src/study_v2.py --stage holdout --worker 0 --workers 4
python src/study_v2.py --stage holdout --worker 1 --workers 4
python src/study_v2.py --stage holdout --worker 2 --workers 4
python src/study_v2.py --stage holdout --worker 3 --workers 4
```

修正的 ALL 对照：把上面的 `study_v2.py` 换成 `study_matched.py`、`holdout` 换成 `matched-all`。数值随机流只保证相同版本/同一后端的复现，不承诺所有平台位级一致。四个 worker 写互不重叠的场景文件。

## API 使用

```python
from flexible_ccp import FlexibleCCP

# epsilon 与 eta 是任务参数，不能为提高成绩在评估中随意改变。
alg = FlexibleCCP.preset("balanced", epsilon=0.2, eta=0.05, delta=0.05, seed=7)
arm, is_service = alg.choose(new_arms=["A", "B"])
alg.observe(0.7)  # 必须是刚选择的 arm 的一个真实奖励
positive, negative, unresolved = alg.report()

# 只能在 observe 后改变偏好；保留全部计数、区间、相位和两个账本。
alg.set_priority(1.0)
```

`set_priority(1.0)` 并不取消已有认证预算限制。真正的分类优先预设 `classification` 从开始就使用 `service_budget=None`。已消费账本不能清零后假装重新获得理论额度。

| 预设 | priority | adaptive | temperature | reward_budget | service_budget |
|---|---:|---|---:|---:|---:|
| reward | 0 | False | 0.5 | 16 | 0 |
| balanced | 0.6 | True | 0.5 | 16 | 1 |
| classification | 1 | False | 0.5 | 16 | None |
| compatibility | 0 | False | 1 | None | 0 |

`base="thompson"` 是默认收益核；可改为 `ucb1`、`growing_moss`、`mc_moss`、`mc_moss_clipped`、`kl_ucb`。兼容模式等价于所选基线，不能事后把它解释成自动知道哪个基线最好。

## 必须保留的边界

主结论是：可调节偏好、有效报告、双预算的 regret 阶保护、明确服务率条件下的面积界。纯收益版本在新测试中59/60个“场景×基线”的均值对比更低，不是全部环境上的支配保证。分类模式最坏阶匹配也不是逐实例最短识别。尾部风险、置信失败、无标签与全部未决路径均未删除。
