"""Render the evidence-based report after actual independent rounds exist."""
from pathlib import Path
import json
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

HERE=Path(__file__).resolve().parent
summary=json.loads((HERE/'assessment-summary.json').read_text(encoding='utf-8'))
batch=json.loads((HERE/'assessment-batch.json').read_text(encoding='utf-8'))
results={x['object_id']:x for x in summary['results']}

def tiers(item):
    names={'1':'一级','2':'二级','3':'三级','duplicate':'核实重复'}
    return '；'.join(f'{names.get(str(k),str(k))} {v} 次' for k,v in item['tier_counts'].items()) or '未定'

def fmt(value,n=1):
    return '未定义' if value is None else f'{value:.{n}f}'

o=results['overall']
status_line=('已完成本批预定轮次。' if summary['executed_rounds']==summary['planned_rounds']
             else f"中间汇总：已完成{summary['executed_rounds']}/{summary['planned_rounds']}轮，尚非最终报告。")
text=f'''# 当前研究成果创新性评审

评审日期：2026-10-18。评审对象为当前合并稿及已完成的新增纯收益基准筛查。仅评价创新性；不自动扩大为重要性、可靠性、表达质量或投稿契合度评分。

状态：{status_line}

整体独立评价均值为 **{fmt(o['mean'])}/10**；层级记录为 **{tiers(o)}**。这一均值由每轮对整体贡献直接评分后汇总，并非各分项的平均或最高分。具体定位须结合层级分歧与核心增量判断。

本批实际执行 **{summary['executed_rounds']} 个隔离上下文**，每轮使用相同冻结材料、规则和任务，不接收历史分数或其他轮次结果。实际执行标识见 [执行记录](execution-log.json)，全部逐项依据见 [逐轮原始记录](assessment-batch.json)。这些是同一模型默认配置下的独立上下文判断，不是不同人类专家的投票；精确部署模型、温度与seed未由运行环境暴露。

## 当前成果的评分

采用指定技能的三级标准：一级8.0—10.0为基础概念或范式创新；二级4.0—7.9为实质性方法、理论或框架创新；三级1.0—3.9为迁移、适配或组合。跨4.0和8.0有实质门槛，不能凭均值四舍五入定级。

| 对象 | 均值 /10 | 样本方差 | 标准差 | 范围 | 有效次数 | 层级计数 |
| --- | --- | --- | --- | --- | --- | --- |
'''
for item in summary['results']:
    text+='| '+' | '.join([item['label'],fmt(item['mean']),fmt(item['sample_variance'],3),
        fmt(item['standard_deviation'],2),f"{fmt(item['minimum'])}—{fmt(item['maximum'])}",
        f"{item['scored_rounds']}/{item['executed_rounds']}",tiers(item)])+' |\n'

text+='''
样本方差使用分母R−1；均值一位小数、方差三位、标准差两位。评分波动只描述固定证据下判断的稳定性，不是“真实创新性”的置信区间，也不是录用概率。不同贡献的分数不能相加，实证分低也不表示算法性能差。

## 与最邻近工作的实际差别

| 近邻 | 已解决或已有的思想 | 当前成果需要承担的额外内容 |
| --- | --- | --- |
| [Mason等，ALL-epsilon，NeurIPS2020](https://arxiv.org/abs/2006.08850) | 相对未知最优均值识别全部近优臂，含全局参考不确定性与分类复杂度 | 持续到达轴上全时刻可靠报告、累计未决成本，以及同一环境中的累计阻碍 |
| [Zhong等，TMLR2023](https://arxiv.org/abs/2110.08627) | 累计regret与末端BAI错误率的可调近匹配权衡 | 全臂持续成员报告和任务过期；不能把“双目标＋单参数”本身计新 |
| [Simchi-Levi与Wang，AISTATS2023](https://proceedings.mlr.press/v206/simchi-levi23a.html) | regret与均值差估计精度的阶意义minimax Pareto前沿 | 固定置信下的维护等待成本，而非终点数值估计误差 |
| [Qin与Russo，2024工作论文](https://arxiv.org/abs/2402.10592) | 特定模型下实验长度与总regret的精确渐近前沿，cost-aware top-two分配 | 移动相对边界、全部臂报告与新增臂引起的重判；其渐近Gaussian保证不能直接移植 |
| [Yang等，JMLR2026](https://www.jmlr.org/papers/v27/24-1612.html) | 固定置信BAI停止前regret的精确渐近最优端点 | 临时分类任务的持续服务成本与共享证据机制 |
| [Cho等，AISTATS2025](https://proceedings.mlr.press/v258/cho25a.html) | 收益核与anytime有效检验结合，固定绝对阈值的好臂识别 | 参考均值随到达移动、已有臂不永久剔除、全部报告的维护成本 |
| [Li等，sleeping公平性，INFOCOM2019](https://arxiv.org/abs/1901.04891) | 可用集变化时收益与第二约束的联合控制，UCB＋虚拟队列 | 分类证书的统计需求与未决面积；公平率和本文动态oracle不是同一目标 |

上述比较没有证明不存在其他先作。它表明一般双目标、可调偏好、证据共享和收益核外加服务控制均有邻近基础；目标不同本身不能免除创新性比较。

## 各项贡献如何理解

**问题与框架。** 当前研究对象有清楚的联合约束：一个全时刻正确事件，加上边界带外未决面积和动态regret。它区别于一次性BAI，但仍需由新结论说明为何不是把成熟静态分类器按到达重新运行。不能将“永久到达”作为新模型，也不能把相对近优集合本身记作新目标。

**广播下界。** 最可具体指认的增量是，在同一个低均值基准环境中，对给定到达轴将信息欠账与受影响报告数相乘并累积，避免把不同环境各时刻最坏例直接相加。静态ALL-epsilon已包含共享参考不确定性，因此“一个未知参考影响很多标签”不是本文独占的新机制。评价要落在累计队列、量词和可推导后果上。见 [广播定理](../../manuscript.tex:738)。

**最坏面积与增长边界。** 有终点截断和上下界，也有固定无限轴与随终点变化的最坏轴的明确区分。最坏面积下界在第一轮静态批次就成立，统计log K有同时恢复先例；不能把整个K平方结论都解释为持续到达独有。多项式增长有1/2指数边界，一般临界轴仍有对数间隙。见 [面积与增长结论](../../manuscript.tex:812)。

**任务过期、端点分离与ABM。** 这是当前稿件中最直接体现到达机制改变信息需求的部分：臂不消失，但识别其旧符号的必要性消失。快速端有匹配成本与固定环境概率加强，暂缓端仅有上界；指定窗口与精度一起变化，不能推广任意长窗口。ABM又给更加分离实例族上的中间预算区间，并保留加性普通收益代价。它是受限族上的真实区间成果，不能扩写为一般重叠到达或F-CCP偏好参数的完整前沿。见 [端点结果](../../manuscript.tex:1003)、[ABM区间](../../manuscript.tex:3500)。

**F-CCP程序。** 局部pair证书规划、一步重规划、边界暂停和双账本组成了完整可运行程序。其两坐标优化精确解的是固定中心与逆平方根半径的代理问题，不能叫真实最优统计分配。当前可靠性和保守完成定理并不依赖这个规划器准确预测成本；更简单的合法服务选择也可以拥有这些保证。因此算法创新仍需由规划原则修复的具体障碍和相称证据支持，不能由定理数量或局部优化的闭式解替代。

**桥接与双预算。** 本文给任意实际动作的证明接口，并分别控制收益动作和分类动作的可观测指数差；这避免把只对最大指数策略成立的结论直接套给任意动作。谱尺度、到达时钟和其minimax下界来自独立companion，不能重复算入本稿。默认Balanced有regret保护、含拒绝项的面积界及有限臂最终完成；Classification才无拒绝并匹配最坏面积阶，却多出Qcap收益代价。同一算法配置没有被证明同时达到完整联合前沿。见 [直接保证](../../manuscript.tex:637)。

**数值成果。** 新增19584次运行补强了比较广度。F-R场景等权均值最低，但稀有奖励与低方差有经校正的劣势，尾部也不占优；并且分类服务关闭，收益优势不能归给证书规划。联合比较已有修正后的同价格模型、收益核与双预算ALL对照，不能再泛称“完全缺少匹配对照”。但它们是保留历史的适配，并非原始FAREAST或(ST)^2的忠实实现；新增9族又只覆盖纯regret，不能替代联合维护比较。新增筛查是对已看过测试集的回顾扩展，不是新holdout。见 [实验报告](../../experiments/regret_baseline_screen_2026-10-17/REPORT.md)。

## 一项优先验证

用相同信息、报告证据、收益核和双预算，将F-CCP规划器与一个更强的成熟分类/成本敏感识别分配适配作比较；已有costmatched ALL应保留，不能把它说成尚未完成。对未看过的到达环境，预先固定可靠性及面积目标，再比较达到目标所需regret，并检查临时任务过期场景是否产生系统差距。也可通过严格映射或反例先判断现成规则能否得到相同保证。这项验证能区分“有用的组合程序”和“解决新障碍的分配原则”，比只增加重复次数更能改变方法创新定位。它不是本次已完成成果，不计入当前分数。

## 核验状态与判断边界

已读取当前主文、关键证明接口、算法实现及实验审计；未逐行独立重证全部附录，也未证明全部最邻近理论均不可归约。没有把“未发现反例”写为完整正确性认证。本次新颖性判断置信度为中等：近邻目标和主要定理范围可具体核查，但算法不可替代性、一般到达前沿及对全部近邻的最强适配比较仍不充分。低评分波动不能弥补这种共同材料边界。

如某项有二/三级分歧，分歧针对的是是否真正跨过“解决新核心障碍”的门槛，不应靠均值强行归到二级。10轮后按规则保留分歧，不为得到一致结果继续追加。
'''

text+='\n## 逐轮总体记录与追加规则\n\n'
for rec in batch['rounds']:
    point=rec['scores']['overall']['innovation']
    text+=f"- {rec['context_id']}：{fmt(point.get('score'))}/10；{point['rationale']}\n"
text+='\n'
text+='汇总建议状态：'+summary['recommendation']['action']+'。\n\n'
for flag in summary['recommendation']['repeat_flags']+summary['recommendation']['review_flags']:
    text+='- '+flag+'\n'
text+='\n固定材料标识：`'+summary['packet_id']+'`。协议标识：`'+summary['protocol_id']+'`。\n'
text+='\n所有快照与当前研究源文件的一致性见 [完整性检查](integrity-check.json)。\n'

(HERE/'REVIEW.md').write_text(text,encoding='utf-8')
violations=[]
for path in HERE.rglob('*.md'):
    content=path.read_text(encoding='utf-8')
    if any(x in content for x in ('\\(','\\)','\\[','\\]')):
        violations.append(path.relative_to(HERE).as_posix())
if violations:
    raise ValueError('Markdown math delimiter violations: '+str(violations))
print(json.dumps({'report':str(HERE/'REVIEW.md'),'markdown_math_check':'passed',
    'rounds':summary['executed_rounds']},ensure_ascii=False))
