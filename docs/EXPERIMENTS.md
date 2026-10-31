# 设计、结果与复现

## 冻结设计

在同一永久到达、有界 iid 模型下，比较 SRC 与 SRC-KL 的奖励和分类代价。45 布局保留 F17、adaptive、dense、scale 的原始到达时刻、均值、T、epsilon、eta、delta；采用新的统一种子和重复协议，不把旧结果改名回填。

`configs/protocol.json` 实际驱动分布、重复、seed、方法和 smoke 派生设置；展开计数必须匹配声明。`configs/methods.json` 与代码注册表漂移时会报错。完整设计为 540 cells、16,224 个共享潜在世界分片、374,496 条唯一方法轨迹。37 个方法配置按不同研究子集运行：奖励比较包含两种候选与 19 baseline，共 21 个配置；分类研究增加其他偏好与匹配调度控制。

小场景的 16 分布包括 Bernoulli、Beta 浓度 .2/2/20、Binomial 4/16、确定性、窄双点、Uniform、spike mixture、两种记录异方差、记录 jackpot、endpoint 双点、rare jackpot、对称截断正态。dense/scale 使用各自冻结子集。截断正态以均值为中心，不通过裁剪到 [0,1] 改变目标均值。

record 身份由整个同时到达批次及此前最佳均值确定，然后随原臂身份置换。因此逐个到达和 bursty 在异方差分布下可能同时改变部分噪声类型，不能统称为只改变到达时钟。

## 配对与诊断

- 每个分片对应一个布局、分布、rep、seed cohort。全部方法共用每臂按观测次数索引的潜在奖励，只按需缓存实际请求的前缀。
- 同批标签置换共用，随机策略使用按方法标识分离的随机流。worker 数、方法顺序及续跑不改变轨迹。
- 主研究、尾部、两 smoke 的 seed 分别是 2026103101/3102/3103/3104。稳定 SHA-256 映射不受 Python hash 随机化影响。
- reward-only 的 joint 归属仅覆盖指定分布与 rep 子集，分析归属数不等于唯一轨迹数。
- 完整研究保留所有端点；详细轨迹预先固定前 4 次重复，41 个线性加 20 个对数候选时点去重。两 reward-only 主算法另存臂计数，dense/scale 以终点为主；smoke 保存全部方法的完整诊断。图中样本数按实际诊断子集标注。
- 算法不接收真实均值、未来到达、分布名称或最终臂数；仅明确声明的 known-horizon 方法接收 T。

## 指标与统计

regret 逐轮参照当前已到达臂的最大真实均值。观察后累计分类成本：`area` 仅计真实 gap 在豁免带外的未决臂；`area_all` 计全部未决臂。两者分别以 eligible arm-time 与全部 arrived-arm-time 归一化，零分母记缺失而非零成本。

每个固定 layout-law 单元先求重复均值，再在同一 group/cohort/suite 内等权汇总。配对差异使用同一潜在世界相减，报告分层 Monte Carlo SE 与 Satterthwaite t 区间；主比较族按 `configs/analysis_plan.json` 预先声明并做 Bonferroni 校正。小试验 n=4 不支持优越性、尾部或高概率联合可行性结论。

coverage、错误标签、空交集路径全部保留。空交集后继续累计未决成本。执行异常单独记入 manifest，使批次保持未完成，不会被当成零 regret。

## 输出与恢复

| 输出 | 内容 |
| --- | --- |
| config.json | 本次方法、布局、任务映射与输入指纹 |
| manifest.json | 状态、环境版本、分片与文件哈希 |
| shards/ | 原子发布的完整潜在世界结果 |
| runs.csv.gz | 每条唯一方法轨迹的端点与科学失败旗标 |
| trajectories.csv.gz | 预定诊断子集的时间路径 |
| counts.csv.gz | 预定方法与时点的逐臂计数 |
| analysis/ | 单元、模块、密度、分布、配对比较、失败诊断及离线 HTML |
| figures/ | PNG/PDF/SVG 和说明实际样本数的图注 |

有限分类预算偏好 1 与 area 使用不同标记。理论比例只在最后到达后展示；仅对可解析的 Bernoulli/确定性固定实例画相应常数参考，短时域 smoke 不声称渐近收敛。

父进程持操作系统锁，worker 只返回结果。完整分片先验证再原子发布。续跑校验源码、配置、seed 与分片哈希，拒绝输入变化或损坏；恢复粒度为一个完整潜在世界分片，不是轨迹中途。

`verify` 检查配置、分片、聚合文件、唯一键及期望数量，`--check-current` 另外核对当前源码。`analyze` 与 `plot` 先校验数据，可在模拟完成后独立重建派生结果。

测试包括独立闭式/SciPy 信息量与 pair 优化对照、区间反演、self-exclusion、时钟、账本、零预算、失败与 checkpoint、方法顺序/多进程一致性及续跑损坏拒绝。首次 JIT 或混合负载计时不作为算法计算效率结论。
