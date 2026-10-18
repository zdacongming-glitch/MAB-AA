# 编辑验收任务卡

本表在validation.json通过后生成；DONE代表本轮编辑、来源及相应验收检查完成，不代表全部证明已独立验证或论文已达到投稿完成度。

| 任务 | 状态 | 完成内容 | 定位与证据 |
|---|---|---|---|
| A-00 | DONE | 源版本、依赖与归档 | source-manifest.md；input_manifest.json；baseline/ |
| A-01 | DONE | 题目、摘要、关键词和元数据 | manuscript.tex开头；supplement.tex开头；PDF metadata |
| A-02 | DONE | 引言以维护成本为主问题 | manuscript.tex sec:introduction |
| A-03 | DONE | FDA图及专属经验材料移出 | 活跃图仅fig_cost_area/fig_paths_pair1/fig_paths_pair2 |
| A-04 | DONE | 基础模型与物理顺序 | sec:model；不再依赖旧轮次参数 |
| A-05 | DONE | 原AID/DB压缩为认证机制 | sec:model末小节；全篇不使用原缩写贡献 |
| A-06 | DONE | 通用三项记账迁到计算附录 | S13 eq:three_part；Batch100保留 |
| A-07 | DONE | 旧两阶段UCB-AA整体移出 | 活跃输入与残留搜索；原分析源归档 |
| A-08 | DONE | 旧纯regret专题移出，共用工具保留 | S1 app:tools；theorem-migration-map.csv |
| A-09 | DONE | 可靠报告与联合协议前移 | sec:reporting_task；eq:area；eq:joint_protocol；参数符号表 |
| A-10 | DONE | 检查点展示名与正式伪代码 | sec:method；alg:checkpoint-ucb；721轮语义诊断 |
| A-11 | DONE | 基础联合保证完整保留 | prop:reporting；eq:reward_bound；S2 app:joint |
| A-12 | DONE | 共同参考环境与队列下界 | thm:broadcast；eq:broadcast_queue；eq:queue_area；S3 |
| A-13 | DONE | 最坏面积、增长量词与引用接口 | thm:worst_area；cor:growth；app:completion_general；S5 |
| A-14 | DONE | 多次更新族与两种gap | eq:family_parameters；eq:family_means |
| A-15 | DONE | 半完成逻辑与松弛迁移 | eq:partial_recovery；S6 eq:allocation_lower |
| A-16 | DONE | 共享证据面积与既有regret共同呈现 | thm:reuse；eq:reuse_conditions；eq:reuse_area；eq:reuse_regret；S7 |
| A-17 | DONE | 快速与暂缓端及范围 | thm:tradeoff；eq:chosen_horizon；eq:rapid_matched；粗端仅上界 |
| A-18 | DONE | 概率加强与q+1截断 | thm:quantile_main；S8 lem:budget_completion；cor:joint_quantile |
| A-19 | DONE | 旧实验整套移出 | 无原archive表图输入；历史文件hash不变 |
| A-20 | DONE | 全部维护实验与负面结果保留 | tab:simulation；fig:cost-area；app:computation；experiments_validation.json |
| A-21 | DONE | 讨论与未来边界 | sec:discussion；future-work.md；无旧算法重跑义务 |
| A-22 | DONE | 数据声明、引用及复现 | Data and code availability；本地资源和无公开URL说明；独立bbl仅列实际引用 |

C-01至C-05均为DEFERRED_C，只登记在future-work.md。未发现本轮BLOCKED_SOURCE、BLOCKED_MATH或BLOCKED_BUILD条目。公开发布地址未确定属于发布准备事项，不假报为本地资源缺失。
