# 时间几何主线：证明稿与可复现诊断

研究日期：2026-10-12。

本目录对应《MAB-AA：时间几何主线——完整理论与创新性评估》。解析证明是定理的依据；以下计算用于核查公式、边界、计数与实现，不是普遍最优性或覆盖概率的数值证明。

## 文件

- `theory.md`：完整研究稿，包含定义、算法、全部核心证明、扩展、文献与创新性评估。
- `mc_moss.py`：不接收终点、未来到达和真实均值的在线算法类；支持原始指数、上界裁剪，以及仅用于比较的冷重启选项。
- `geometry.py`：谱、固定点、无网格容量、精确有理数可行配置与对偶证书、时钟段和可兼容尺度抽取。
- `audit_geometry.py` / `geometry_results.json`：小规模穷举和随机日程核查。
- `policy_diagnostics.py` / `policy_results.csv` / `policy_summary.json`：确定性及 Bernoulli 模拟，公共前缀一致性核查。
- `test_online_api.py` / `api_results.json`：接口验证与奖励上界裁剪的两条实际轨迹。
- `manifest.json`：执行环境、文件哈希与说明。

## 运行

`geometry.py`、`audit_geometry.py`、`mc_moss.py`、`test_online_api.py` 只使用 Python 标准库（Python 3.10 或更新版本）。本轮实际执行环境为 Python 3.13.5。

```bash
python audit_geometry.py
python test_online_api.py
```

大规模策略模拟另需 NumPy 与 Numba。本轮运行版本为 NumPy 2.3.5、Numba 0.65.1，可按 `requirements-diagnostics.txt` 安装。首次运行含编译预热，预热不计入结果文件中的步骤总数。

```bash
python -m pip install -r requirements-diagnostics.txt
python policy_diagnostics.py
```

## 在线使用示例

```python
from mc_moss import MCMOSS

policy = MCMOSS(clip=True)  # False 使用正文 (4.2)，True 使用命题 7。
# 每轮只传本轮新出现的标签；没有新臂时传空列表。
chosen = policy.select(["incumbent", "candidate-1"])
# 在外部执行实验，只将实际观察到的 [0,1] 奖励返回给策略。
policy.update(0.7)
chosen = policy.select([])
policy.update(0.2)
chosen = policy.select(["candidate-2"])
policy.update(0.5)
```

这段示例只是 API 调用，不表示预先知道真实均值。必须交替调用 `select` 与 `update`；批内标签顺序决定平局规则。算法保留累计计数与奖励和；没有设置实际内存约束。

## 诊断范围

主策略诊断共 4,105,304 步：14 条确定性轨迹、24 条完整 Bernoulli 轨迹、24 次截断前缀复跑。在线接口核查另有 2,001 个已完成步骤，单独记录，不混入主模拟计数。

确定性主模拟采用每段 65,536 轮，是理论分离机制的有限版本；并未实际运行定理 9 中随段数增长的极大 `h=2**(16*m)`。报告中的渐近阶分离依靠解析证明。

没有进行 AUER、G-MOSS、UCB-AA 的正式比较；没有估计统计覆盖率；没有宣称这两种 MOSS 实现普遍优于全部强基线。谱和容量均由到达数据计算，不使用真实均值。

所有原上传文件保持不变。
