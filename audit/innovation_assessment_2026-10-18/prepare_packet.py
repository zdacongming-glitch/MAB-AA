"""Freeze current research and a common, score-free evidence packet."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DEST = Path(__file__).resolve().parent
PROJECT = DEST.parents[1]
SKILL = Path('C:/Users/12701/.codex/skills/statistical-innovation-assessment')
if (DEST / 'evidence-manifest.json').exists():
    raise RuntimeError('This evidence packet is frozen. Create a separate batch for changed evidence.')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

sources = [
    'manuscript.tex', 'references.bib',
    'experiments/fccp_frozen/src/flexible_ccp.py',
    'experiments/fccp_frozen/src/flexible_engine.py',
    'experiments/fccp_frozen/src/flexible_v2.py',
    'experiments/fccp_frozen/src/ccp_primitives.py',
    'experiments/regret_baseline_screen_2026-10-17/REPORT.md',
    'experiments/regret_baseline_screen_2026-10-17/results/suite-summary.csv',
    'experiments/regret_baseline_screen_2026-10-17/results/paired-vs-FR.csv',
    'experiments/regret_baseline_screen_2026-10-17/results/analysis-audit.json',
]
manifest = []
for rel in sources:
    src = PROJECT / rel
    target = DEST / 'snapshot' / (rel + '.snapshot')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, target)
    manifest.append({'source': rel, 'snapshot': target.relative_to(DEST).as_posix(),
                     'sha256': sha(src), 'bytes': src.stat().st_size})

rules = []
for rel in ['SKILL.md', 'references/rubric.md', 'references/repeated-assessment.md']:
    src = SKILL / rel
    target = DEST / 'rules' / (rel + '.snapshot')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, target)
    rules.append({'source': str(src), 'snapshot': target.relative_to(DEST).as_posix(),
                  'sha256': sha(src)})

# Numbered excerpts preserve original line numbers; the complete frozen source is also available.
lines = (PROJECT / 'manuscript.tex').read_text(encoding='utf-8').splitlines()
ranges = [(1,166),(177,340),(341,733),(735,1111),(1112,1278),
          (1426,1538),(1586,1809),(1840,2005),(2237,2311),
          (2404,2494),(2574,2755),(2811,2930),(2935,3559)]
excerpt = []
for lo, hi in ranges:
    excerpt.append(f'=== manuscript.tex original lines {lo}-{hi} ===')
    excerpt.extend(f'{i}: {lines[i-1]}' for i in range(lo, min(hi,len(lines))+1))
(DEST / 'manuscript-excerpts.txt').write_text('\n'.join(excerpt)+'\n', encoding='utf-8')

packet = r'''# 当前成果创新性评审：固定证据包

评估日期：2026-10-18。范围：只评价当前成果的创新性，不作四维审稿、期刊排名、契合度或录用概率评价。不得读取旧 assessment、旧评分、历史对话及其他轮次输出。以下不含预设分数；各轮自行按固定判据定位。

## 版本与研究边界

实际当前稿为 snapshot/manuscript.tex.snapshot；主文与补充已合为一个文件。manuscript-excerpts.txt 保留有关段落和证明的原始行号。另含当前算法实现与新增纯收益筛查的快照。研究对象是一篇已有定义、证明、实现和数值结果的稿件。评的是当前贡献，不把未来完整前沿等目标算作已完成成果。

companion temporal-geometry/MC-MOSS 研究计划作为另一篇文章；其到达谱、时钟、谱 minimax 下界不是本稿新增贡献。本文任意动作接口的证明可以单独判断其增量。原始 UCB-AA 及历史计划用于理解沿革，不另计独立得分。

模型：臂在外生时刻到达后一直可用；各臂有独立平稳 iid 的 [0,1] 奖励流；每轮只能真实抽一次。每个确定终点下，到达轴固定。目标成员集合为所有相对当前最大均值相差不超过 epsilon 的已到达臂；每轮输出正、负、未决报告。一个概率至少 1-delta 的共同事件上，所有轮次所有确定标签都正确。累计未决面积只收费于距离分类边界超过 eta 而仍未决的臂时间。比较 regret 与高概率维护面积；不是向量奖励的 Pareto 臂识别。

## 固定评价对象及相互关系

- c1「持续可靠集合维护问题与联合成本框架」：完整报告协议、相对当前最优的成员变化、累计未决臂时间与 regret。建模/框架贡献，按全部机制而非单独双目标命名判断。
- c2「广播不确定性的累计信息队列下界」：核心理论之一，评价固定环境、给定到达轴上的累计阻碍及概率加强。
- c3「最坏维护面积与到达增长边界」：核心理论之一；区分静态最坏批次、任意批到达上界和固定无限轴的增长条件。
- c4「任务过期与快速/暂缓成本分离及 ABM 区间」：核心理论之一。包含指定族的两个服务端点、一个固定环境的概率下界、更加分离族上的中间区间；不能将重叠部分重复计新。
- c5「F-CCP 的证书规划与自适应服务算法」：方法贡献；将局部连续代理规划、参考选择、单步重规划、边界暂停、服务控制及共享统计作为具体程序评价。
- c6「F-CCP 的任意动作桥接、双预算与完成保证」：方法的理论接口；和 c5 有联系但不把 companion 的谱刻画重复算入。只有同一配置实际拥有的保证才能一起宣称。
- c7「冻结实验和扩展基准成果」：实证/验证贡献；评价是否增加新的统计认识，不能按运行规模、软件投入自动升档。
- overall「当前成果整体」：由支撑主结论的核心贡献独立判断，不平均或累加 c1-c7，也不直接取最高项。

## 本稿结果事实及限定范围

c2：主文约738-798，证明2237-2311。同一个基准环境中候选为低均值，各替代环境只提高一个候选。信息队列每到达一个候选加入 q 单位、每轮服务一单位；面积按当时受影响报告数加权。对任意可靠策略，固定基准环境中的期望面积有常数倍下界，且以至少1/4概率达到队列面积的1/4。策略即使知道整张到达表、终点和参考分布仍受限制。证明按期望样本数选困难标签，在同一环境沿时间累积。最优参考的未知性会同时影响全部成员，已经见于静态 ALL-epsilon；本稿需比较其沿到达轴累积的额外内容。

c3：主文802-894，证明2404-2494。在 K>=2、epsilon<=1/8、eta<=epsilon/32、delta<=1/16 等范围，最坏高概率面积的上下阶为 min(KT, K^2 eta^-2 log(K/delta))。下界所有臂第一轮到达，log K 的同时恢复代价已有先例；上界由固定检查点 witness 给出。单条无限到达轴上，次线性面积包络必要 K_t=o(sqrt(t))，充分 K_T^2 log(eK_T)=o(T)；多项式到达 K_t~t^alpha 的指数边界为 alpha<1/2。一般临界轴仍有对数间隙。允许最坏到达轴随终点变的总数类，和固定一条无限轴的量词不同，原文有稀疏大突发反例。

c4：主文902-1111，补充2574-2755、2811-2930、2935-3559。重复更新族中，候选出生时与旧边界相距 d，新参考提高 v 后旧符号问题过期，臂本身不消失。固定 J,M,epsilon,v,delta 且 d趋零、eta=d/2，窗口 H 特选为 d^-2 量级。面积预算 V/8 时最优 regret 有匹配 d^-2 阶；放宽至9V/8有 O(log(1/d)) 上界，暂缓端没有匹配下界。快速上界使用指定终点下的粗路径上界，不能自动推任意长窗口。概率加强在一个固定符号环境上以至少11/80概率承担快速同阶成本。旧候选上界与新参考下界复用需要出生窗口内满足检查点，非任意重叠到达保证。

ABM 的中间区间另用更强分离族 Theta_H，并有任意子集同时恢复工具。对 A_min<=a<V，regret 在 epsilon*k(a)*d^-2*log(k(a)/delta) 的上下常数阶匹配，明确保留加性 R0(T)；更小预算、a>=V附近及一般重叠到达未覆盖。ABM用激活秩分配置信度、激活后新样本块，避免事后给旧样本前缀分配误差预算。给定候选预算 s 不需未来，但由面积目标 a 校准 s 用到性能族的 m,H。不是 F-CCP 的最优性定理。另有早/晚改善的 schedule-information separation，排除对每条分别优化到达轴前沿的统一常数比较，不排除共同 causal minimax 最优。

c5：主文341-632及源代码。beta-mixture置信序列与固定检查点交集，自排除的 gap 区间给正负标签；未决但已证在边界带的臂暂停专门服务。为每个任务选择一个参考，按 price=nu+(1-lambda)*observable-index-gap 构造两坐标规划，约束半径按样本量的逆平方根下降，连续代理问题有闭式解。挑最便宜 pair、执行一个可用端点观测后重算；有配额内最宽区间后备。规划器只对固定中心的连续代理最优，不是统计信息复杂度或全局最优分配。服务相位及自适应 rate 控制实际服务尝试；服务预算可能拒绝，拒绝不退回相位。奖励部分使用温度化Beta分数与虚拟MC-MOSS保护，长期统计不重置。可靠性及保守完成证明并不要求代理预测真实采样成本准确。

c6：主文637-731，补充1586-2005。共同事件上所有标签全时刻可靠。若从开始lambda=0、关闭收益保护且完整状态/RNG相同，可逐路径恢复指定奖励核；默认F-R不是此兼容端点。任意合法动作的桥接把期望regret分解为300*S_T加实际选臂的可观测指数差之和；补充明确重证潜在前缀、实际选择计数及到达时钟收费。有限双账本给无条件 E R_T<=min(T,(300+2beta_R+2beta_C)S_T)。F-R为332*S_T，Balanced为334*S_T；Classification无认证cap时多出Qcap。预算对指数差记账，不等于相对于独立运行TS的真实额外regret。S_T及其 minimax 谱尺度来自companion；常数保守，有限实验规模可能退化为T。

若busy服务率有正下界，面积在共同置信事件上<=K_T min(T,(Qcap+D_srv+1)/p_min)。Balanced须保留拒绝项；有限臂且最终停止到达时、beta_C>0，边界带外任务最终完成，并有保守非饥饿前缀界。Classification的p_min=1且无拒绝，在共同参数范围达到最坏面积阶，但其regret多Qcap。不是默认Balanced同时达到两个指标的最优前沿，没有一般支配或proxy最优信息分配结论。

c7：稿中主冻结实验12场景、24配置、每格96配对（27648有效主分析记录）；ALL comparator输入修正另存1152条。Balanced与修正ALL使用相同价格模型、奖励核、双预算；均值regret/面积为392.99/31.70千，对435.68/36.72千。匹配配置并非每轮服务pull强制相等。F-area为1210.02/27.12千，ALL-area为1581.72/36.81千。F-auto-0.6有1/1152次错误确定标签；覆盖失败和空交集均保留，失败后持续未决，不能解释为完成。原场景并非一般满足理论的窄参数区间。

新增纯regret筛查：12原场景*96配对*17配置=19584次；9新增算法族中BL-MOSS有3固定版本。6原方法6912终点与冻结结果相符。场景等权原始regret均值：F-R60.73，IMED71.67，TS75.43，KL-UCB+76.49，Bayes-UCB82.23。F-R不逐场景、也不尾部支配；192项比较Bonferroni校正后，rare-rewards的IMED/KL-UCB+及bounded-low-variance的IMED/empirical-KL-UCB仍优于F-R。F-R与IMED各场景95分位数平均132.22/105.95，最差10次均值平均149.31/109.96。全部认证服务关闭，故这些增益不来自证书调度。新增筛查用已观察的原测试场景，是独立执行的回顾扩展，不是新holdout；新增9族尚未写入稿件。BL两个参数版本动作相同不是独立证据。

## 已核查最邻近原始工作：只比较其实际目标与保证

L1 Mason/Jain/Tripathy/Nowak, NeurIPS2020, Finding All epsilon-Good Arms in Stochastic Bandits。固定臂、相对未知最大均值的全体近优集合；(ST)^2与FAREAST及复杂度上下界，含容忍度。纯探索终点任务，没有本文持续到达的累计报告面积目标。未知最大参考及多臂同时分类不是本文独占的新对象。https://arxiv.org/abs/2006.08850

L2 Degenne etal, AISTATS2019, Bridging the gap between regret minimization and best arm identification, with application to A/B tests。UCB_alpha调节regret与固定置信决策时间，有二者上界；不能因此称完整匹配前沿。https://proceedings.mlr.press/v89/degenne19a.html

L3 Zhong/Cheung/Tan, TMLR2023, Achieving the Pareto Frontier of Regret Minimization and Best Arm Identification in Multi-Armed Bandits。BoBW-lil'UCB(gamma)固定期限，累计regret与末端BAI错误率。原文4.1、4.2、5.1、5.4给可调上下界；特定实例族/参数范围内近匹配，仍有对数及hardness差距，不是任意有限实例精确全前沿。https://arxiv.org/html/2110.08627

L4 Simchi-Levi/Wang, AISTATS2023, Multi-armed Bandit Experimental Design: Online Decision-making and Adaptive Inference。EXP3E/EXP3EG累计regret与所有两两均值差最大平均绝对估计误差；在固定K、gap充分分离类，乘积误差*sqrt(regret)上下达到忽略常数/对数的minimax前沿，Definition3按n阶比较。已判次优臂仍保留随时间衰减的强制采样。非未决面积；shrinking-gap范围有未匹配区域。后有ManagementScience版，但这里精确核验范围依据会议版。https://proceedings.mlr.press/v206/simchi-levi23a/simchi-levi23a.pdf

L5 Qin/Russo, Optimizing Adaptive Experiments, 2024工作论文。Top-two TS配合停止/部署规则；大总体n趋无穷、Length/log(n)与总Regret/log(n)的精确渐近前沿（5.6及附录K）。总regret含实验与后续部署。直接cost-aware TTTS算法定理为共同已知方差Gaussian及相应正成本条件；一般指数族有优化理论延伸，简单自适应coin rule通用收敛仍有缺口。https://arxiv.org/html/2402.10592

L6 Yang/Tan/Jin, JMLR2026, Best Arm Identification with Minimal Regret。Double KL-UCB在一参数指数族、delta-PAC BAI中，停止前regret达到log(1/delta)首阶精确最优常数。达到该端点必须让样本量比log(1/delta)更大；非完整regret-时间前沿。https://www.jmlr.org/papers/v27/24-1612.html

L7 Cho/Meier/Gan/Kallus, AISTATS2025, Reward Maximization for Pure Exploration。regret-minimizing sampling+nonparametric anytime-valid e-process，实现固定绝对阈值的好臂识别/分类停止时间渐近minimax；停止时间严格证明用阶段重置修改版，实验版不reset。寻找第一个好臂时与收益目标兼容，但不宣称相对原best的全臂分类regret-面积前沿。https://proceedings.mlr.press/v258/cho25a.html

L8 Li/Liu/Ji, INFOCOM2019, Combinatorial Sleeping Bandits with Fairness Constraints。LFG=UCB+virtualqueue；固定N，iid可用集合，每轮最多m臂，收益最大化受每臂最低长期选择率约束。证明可行性和regret上界，非收益-识别前沿。regret相对同公平约束oracle，非每轮最佳可用臂。https://kevinliu-osu.github.io/publications/Sleeping_Bandit_INFOCOM19.pdf

L9 Huang etal2020, Thompson Sampling for Combinatorial Semi-bandits with Sleeping Arms and Long-Term Fairness Constraints。TSCSF-B同样收益+公平约束；不能当regret+推断已解决或完整Pareto结论。https://arxiv.org/abs/2005.06725

L10 Shao/Fang, AAAI2025, Linear Streaming Bandit: Regret Minimization and Fixed-Budget Epsilon-Best Arm Identification。可观察线性特征、有限内存、流式臂；分别给regret与BAI算法，不是同一算法联合保证。https://ojs.aaai.org/index.php/AAAI/article/view/34242

Kleinberg等sleeping与Ghalme等ballooning已给可用集变化/永久到达及当前最好臂比较先例。混合置信序列、单臂固定精度Hoeffding、同时恢复及换测度工具均已有来源（本稿references）。不能将这些基础工具或一般双目标/调参数/共享样本想法全部计新。不能因使用成熟工具就自动否定新增相互作用；也不能因目标名称不同就认定有实质创新。

## 最强合理既有工具基线及核验限度

可考虑：用全部历史的有效置信序列，每次到达后重新计算ALL-epsilon式标签，并将收益核与有正份额的分类服务混合；或用经典成本敏感识别/统计实验设计规则替换局部规划器。保留真实信息约束，不给未来到达、真实均值、额外观察。上述构造可直接提供标签有效性和保守采样完成；是否得到本稿同一个环境的广播队列下界、临时任务成本分离、激活区间或相同有限预算权衡须具体论证，不能直接假设能或不能。

核验状态：定义、主定理、关键证明接口及实验报告已实际读取；任意动作桥接有逐项论证，没有确认新的核心反例。没有进行全部证明逐行独立验算，也没有完成所有近邻原文在全部推广范围上的不可归约证明；本轮搜索未找到直接覆盖完整组合不等于证明不存在先作。对这些未知分别说明，不以低分代替材料不足，不把未完成未来结果算入当前。

本批不重新模拟，不修改论文。仅 innovation 一维评分，重要性/可靠性/表达可作为解释但不能给其分数或补偿创新。总体由核心贡献独立判定，不从分项算均分。每项先定级再一位小数，边界有争议可明确未定并给原因；没有依据时不强行点分。
'''
(DEST / 'evidence-packet.md').write_text(packet, encoding='utf-8')
objects = [
    ('c1','持续可靠集合维护问题与联合成本框架'),
    ('c2','广播不确定性的累计信息队列下界'),
    ('c3','最坏维护面积与到达增长边界'),
    ('c4','任务过期、服务成本分离与ABM中间区间'),
    ('c5','F-CCP证书规划与自适应服务算法'),
    ('c6','任意动作桥接、双预算与完成保证'),
    ('c7','冻结实验和扩展基准成果'),
    ('overall','当前成果整体'),
]
objects = [{'id':i,'label':label,'kind':'overall' if i=='overall' else 'contribution',
            'basis':'current','dimensions':['innovation']} for i,label in objects]
prompt = '''你执行一次独立创新性评价。工作目录 D:/博士学习/科研/git/MAB-AA。仅使用目录 ucbaa_jasa_resubmission_2026-10-15/audit/innovation_assessment_2026-10-18 内冻结材料。先读 rules/SKILL.md.snapshot、rules/references/rubric.md.snapshot、rules/references/repeated-assessment.md.snapshot，再读 evidence-packet.md、evidence-manifest.json 和 protocol.json。读 manuscript-excerpts.txt 的全部主文及与分项有关的证明接口；有疑问可读完整 snapshot/manuscript.tex.snapshot 和已列明的源代码/实验快照。不得读同目录 rounds/ 中他人文件、历史assessment、旧评审、聊天或其他轮次结果，不联网补充材料，不写稿件。仅评价 protocol 的 c1-c7 和 overall 的 innovation 一维，当前贡献不是未来潜力；每项先定层级再给一位小数，遵守4.0/8.0硬门槛。总体由支撑主要结论的核心贡献独立判断，不能平均、累加或机械取最大分项。不要求算法必须有完整Pareto最优定理才具实质创新，也不能把已有双目标与基础工具计新。若核验不足可显式undetermined，不以0或低分替代。请在 rounds/ 下写一个以你真实canonical task name最后一段为名的JSON（例如任务名abc则abc.json）；包含 canonical_task_name、packet_id、protocol_id、scores（键覆盖c1-c7/overall，每键为{innovation:{status,score,tier,rationale}}，rationale用2-3句给近邻差异、跨4门槛依据或未跨原因、限制）、verification_scope、confidence、priority_validation。status=scored时score数值tier正确；未定则score/tier为null。另给简短执行回报，只列总体定位、主要分歧点和写入路径。不要输出隐藏思维过程。'''
(DEST / 'evaluation-task.txt').write_text(prompt, encoding='utf-8')
wrapper = '请执行 D:/博士学习/科研/git/MAB-AA/ucbaa_jasa_resubmission_2026-10-15/audit/innovation_assessment_2026-10-18/evaluation-task.txt 中的一次独立创新性评价任务。严格使用指定固定证据与规则，读取全部相关材料；不要继承、查找历史评分或其他轮次结果。按任务要求保存你本轮的JSON并简短回报。'
(DEST / 'agent-invocation.txt').write_text(wrapper, encoding='utf-8')
identity = {'files':manifest, 'rules':rules,
            'packet_sha256':sha(DEST/'evidence-packet.md'),
            'excerpts_sha256':sha(DEST/'manuscript-excerpts.txt')}
packet_id = 'sha256:' + hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
protocol = {'rubric_version':'skill/rubric frozen SHA256 in manifest',
            'model_id':'parent_default: Codex/GPT-6 family; exact deployment ID not exposed',
            'model_snapshot':None,
            'settings':{'fork_turns':'none','model_override':None,'reasoning_override':None,
                        'temperature':'not exposed','seed':'not exposed',
                        'task_sha256':sha(DEST/'evaluation-task.txt'),
                        'invocation_sha256':sha(DEST/'agent-invocation.txt')},
            'execution_method':'isolated_agents',
            'scope':'innovation only, current results',
            'initial_rounds':5, 'maximum_rounds':10,
            'append_rule':'any sample SD>=0.4 or any cross-tier disagreement => investigate and append to 10 without changing evidence',
            'objects':objects}
protocol_id = 'sha256:' + hashlib.sha256(json.dumps(protocol,sort_keys=True).encode()).hexdigest()
(DEST/'protocol.json').write_text(json.dumps({'protocol_id':protocol_id,**protocol},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(DEST/'evidence-manifest.json').write_text(json.dumps({'packet_id':packet_id,'protocol_id':protocol_id,
    'frozen_at_utc':datetime.now(timezone.utc).isoformat(),**identity},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(DEST/'rounds').mkdir(exist_ok=True)
print(json.dumps({'packet_id':packet_id,'protocol_id':protocol_id,'frozen_sources':len(manifest),
                  'excerpts_lines':len(excerpt)},ensure_ascii=False))
