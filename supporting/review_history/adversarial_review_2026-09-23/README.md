# 正式稿件独立对抗性评审

本目录仅新增评审材料，未修改正式稿、既有修订试验或原始仿真代码。

- [详细评审与评分](D:/博士学习/科研/git/MAB-AA/adversarial_review_2026-09-23/assessment.md)：最新版创新判据下的 3.6/10 暂定定位、分项评分、理论与实验证据、可辩护和不可辩护之处。
- [基线归约与边界推导](D:/博士学习/科研/git/MAB-AA/adversarial_review_2026-09-23/baseline_and_boundary_checks.md)：不预知最终臂数的 UCB 保证、Theorem 5 的可行范围、uniform goodness 的相容性及 G3 反例。
- [核验记录](D:/博士学习/科研/git/MAB-AA/adversarial_review_2026-09-23/evidence.json)：输入哈希、原存档统计量、两个新重放和确定性诊断。
- [复核脚本](D:/博士学习/科研/git/MAB-AA/adversarial_review_2026-09-23/verify_evidence.py)：只读取原数据和代码，结果写在本目录。

运行以下命令可复核数据和原算法行为：

~~~powershell
python -B "D:\博士学习\科研\git\MAB-AA\adversarial_review_2026-09-23\verify_evidence.py"
~~~

此脚本重汇总两场景各 100 次已存档重复，只重新执行 C/E 各一次原算法和一个确定性反例，不重跑全部实验。不使用独立探索的新算法，也不使用充值卡。
