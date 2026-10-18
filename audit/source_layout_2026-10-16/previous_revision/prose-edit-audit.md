# 文字编辑与文本清理记录

本轮使用stat-journal-writing先修论证顺序，再按humanizer检查叙事与句子；watermarks-remover用于活跃源的确定性检查和用户授权的自然语言修改。三个步骤不改变数学风险协议、数值、作者或文献来源。

## 草稿、检查与定稿示例

冻结原稿句子：

> We now supplement the allocation objective with an explicit reporting objective.

检查：这句话讲述旧稿扩写过程，无法直接说明当前论文的主任务。按本轮授权，报告任务应在模型中独立定义。

定稿：

> The question is how much regret is necessary, and how much is attainable, under this reporting requirement.

冻结原稿句子：

> These are substantive extensions of the original regret question, rather than guarantees inferred from the size of UCB-AA's active set.

检查：句子需要读者知道旧稿，且以修订历史代替贡献的具体内容。

定稿在引言直接陈述共同参考下界、最坏日程面积和规定更新族上的两端权衡，并把方法定位为可达性构造。没有用新的优越性措辞替换旧算法故事。

中间草稿句子：

> The finer choice satisfies the precision condition, so completed checkpoints resolve every separated arm on the coverage event.

检查：单臂完成检查点不保证立刻分类，其他竞争臂仍可能未成熟。应明说全体当前检查点已完成。

最终源句子：

> Once every currently available arm has completed its checkpoint, all η-separated arms are resolved on the coverage event.

正文实际使用LaTeX参数记法；这里用Unicode转述以便阅读。

## 其余复核

删去修复过程、年代式扩写、修订指令及与旧实现比较的自述。定理附近保留范围限制，数值节保留全部关键不利结果。算法计数、固定区间、收益可选集合、24行主表及概率常数均按源检查，未以同义改写掩盖定义变化。

文字精修只涉及作者授权的读者可见叙述。数学关系、连字符方法名、文献标题与必要符号受保护，不为消除表面风格特征而破坏它们。

## watermarks-remover实际范围

活跃TeX/Bib逐份调用技能提供的inspect入口，实际JSON见watermark_inspection.json。原稿在编辑前检查未发现可疑不可见字符；修订稿的检查在最终源确定后运行。未对完整目录实施批量清洗，未删除作者、出处、声明或数学控制符。

没有统计文本水印检测器、配置或密钥可供核验。自然语言修改不构成“统计水印已认证移除”的证明；不声称文本不可检测或由人类独立撰写。PDF元数据清理未执行，当前元数据只按新题名同步，作者身份保留。

技能工具原生支持18份活跃TeX检查，均无可疑项；它不支持BibTeX文件格式。未绕过该限制进行清洗，另对未修改的文献库作只读Unicode格式与控制字符检查，结果见同一JSON的manual_fallback字段。未发现需删除字符，实际删除数为0。
