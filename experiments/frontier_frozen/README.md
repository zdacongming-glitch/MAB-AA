# regret—未决量前沿：本轮研究包

这是一次真实的理论与算法探索，不是已经解决一般联合最优性的发布版本。没有修改用户交给 Codex 重构的 LaTeX 稿件。

## 先读什么

- `研究报告_前沿与算法.md`：中文主要结论、实验与创新性定位。
- `theory_frontier.md`：新增定理、ABM 构造、完整证明和严格范围。
- `proof_audit.md`：有效/无效运行、证明核查与未闭合接口。
- `assessment.json`：按指定创新性规则做的一次实际评价，未完成五次独立重复。

## 代码入口

- `practical.py`：可交互 CCP/Shared/Bundle/ALLplus；默认仍是 CCP，因为本轮没有确认 Shared 的稳健联合优势。
- `abm.py`：理论上的激活预算双精度构造；不是主数值比较的 Shared 算法。
- `exact_frontier.py`、`exact_easy.py`、`exact_arrival.py`：有限候选环境、固定报告器的 chance-constrained LP。
- `engine_base.py`：上一轮冻结的 CCP 与所有收益核。
- `engine_new.py`、`new_schedulers.py`：本轮预冻结的共享证书候选与模拟引擎。
- `engine_v2.py`、`witness_scheduler.py`：后续开发探索，不属于已冻结主测试。

示例：
```python
from practical import MaintenancePlanner
policy = MaintenancePlanner(epsilon=.2, eta=.05, delta=.05,
                            beta=1., scheduler="ccp")
arm, is_service = policy.choose(new_arms=["a", "b"])
policy.observe(.7)  # 实际选中 arm 的真实观测；每次恰好一个
positive, negative, unresolved = policy.report()
```

`abm.py` 用 `ActivationBudgetedMaintenance(epsilon, delta, coarse_precision,
fine_precision, fine_candidates)`，`choose()` 输入新到达的连续正整数标签；详见类注释。

## 复现

依赖 Python 3.10+，numpy、scipy、pandas、numba；审计另用 sympy。版本记录在 `environment.json`。不要用新的运行覆盖本包冻结数据；先复制工作目录。Numba 缓存对改变的跨模块依赖可能不自动失效，修改引擎后删除复制目录的 `__pycache__`。

```bash
python test_run.py --worker 0
python test_run.py --worker 1
python test_run.py --worker 2
python test_run.py --worker 3
python analyze_holdout.py
python audit_checks.py
python verify_api.py
python exact_easy.py
python exact_arrival.py
```

四个 worker 可以顺序运行；它们仅分割场景，不改变参数。`test_protocol.py` 可读实际配置；`holdout-freeze.json` 是运行前生成的文件，不应重新生成来替换它。

## 数据

`holdout-all.csv` 共 12,672 条运行，`holdout-summary.csv` 有全部配置/场景的均值、标准误、95%经验分位与失败数；`holdout-paired.csv` 有预设主候选对 CCP/ALLplus 的配对差与逐比较 t 区间。误差区间不是跨全部比较同时有效的区间。

每个环境 T=14,000（many_new=18,000，serial_arrivals=15,000），48次配对重复。五种用户指定收益基线均有原样动作规则的全历史到达适配；仅附加报告不改变其动作。非 Bernoulli 环境的分数 Beta-TS 是启发式，不宣称是正确后验。

`exact-easy.csv` 与 `exact-arrival.csv` 为小模型全部可行整数预算（不更严格预算由单调性排除），含独立前向核验与 LP 残差。精确是优化问题的精确表述；浮点计算不是有理算术证明。`exact-*-policy-*.json` 的策略知道小模型候选集合、日程与终点，不能当作未知模型主算法。

旧的研究包仅提供必要源码与其原始归属；主测试不是旧 Table 2 的复现。
