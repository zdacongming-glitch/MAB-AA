from study_v2 import *
TEST=[
 sc('two_close',[(1,[.493,.510])],eps=.027,eta=.006,T=12000),
 sc('few_arrivals',[(1,[.565]),(4013,[.785,.295])],eps=.18,eta=.045,T=12000),
 sc('stable',[(1,[.735,.625]),(2809,[.18,.35,.515]),(6803,[.66,.26,.43])],T=12000),
 sc('successive_improvements',[(1,[.425,.19]),(3301,[.645,.385,.51]),(7013,[.825,.615,.48]),(11003,[.955,.715,.88])],T=14000),
 sc('burst',[(1,[.635,.465]),(4219,[.915,.885,.81,.76,.675,.61,.57,.49,.41,.335,.225,.13])],T=14000),
 sc('membership_boundary',[(1,[.765,.545,.585,.66,.41,.19]),(5701,[.735,.57,.52])],eta=.035,T=14000),
 sc('many_close_means',[(1,[.615,.605,.59,.57,.55]),(4507,[.635,.60,.565,.54,.51]),(8903,[.65,.62,.585])],eps=.115,eta=.03,T=12000),
 sc('late_improvement',[(1,[.54,.445,.285]),(4201,[.35,.51]),(11701,[.935,.71,.875])],T=14000),
 sc('rare_rewards',[(1,[.035,.027,.018,.008]),(3713,[.042,.024,.009]),(8819,[.053,.031])],eps=.018,eta=.005,T=12000),
 sc('ceiling',[(1,[.977,.954,.90,.79]),(4211,[.991,.934,.825]),(9001,[.965,.865])],eps=.08,eta=.02,T=12000),
 sc('larger_pool',[(1,[.81,.73,.615,.40]),(4019,[.15,.22,.29,.36,.43,.50,.57,.64,.71,.78,.845,.89]),(10501,[.94,.91,.76,.665])],T=16000),
 sc('bounded_low_variance',[(1,[.705,.535,.395,.225]),(4703,[.845,.625,.775]),(9173,[.815,.555,.345])],T=12000,kind='two_point'),
]
P=[p('UCB1',core=10),p('UCB-conservative',core=0),p('Growing-MOSS',core=1),p('MC-MOSS',core=2),p('MC-MOSS-clipped',core=7),p('Thompson',core=3),p('KL-UCB',core=4),
 p('F-R',temperature=.5,br=16.),p('F-R-TS-exact'),p('Cold-TS-unprotected',temperature=.5),p('Warm-TS-guard',core=11,temperature=.5,br=16.),
 p('CCP-original',core=7,priority=.5,br=0.,bs=1.,scheduler=13),
]
for z in [.1,.3,.6,.9]:
 P.append(p('F-auto-'+str(z),priority=z,adaptive=True,temperature=.5,br=16.,bs=1.))
P.extend([p('F-area',priority=1.,temperature=.5,br=16.),
 p('F-all-service-budgeted',priority=1.,temperature=.5,br=16.,bs=1.),
 p('F-fixed-0.6',priority=.6,temperature=.5,br=16.,bs=1.),
 p('F-auto-0.6-no-service-cap',priority=.6,adaptive=True,temperature=.5,br=16.),
 p('F-auto-0.6-TS',priority=.6,adaptive=True,br=16.,bs=1.),
 p('ALL-auto-0.6',priority=.6,adaptive=True,temperature=.5,br=16.,bs=1.,scheduler=1),
 p('ALL-area',priority=1.,temperature=.5,br=16.,scheduler=1),
 p('ALL-original-budget',core=7,priority=.5,br=0.,bs=1.,scheduler=1),
])
if __name__=='__main__':
 freeze('holdout',TEST,P,96,117110100,117120100)
 path=ROOT/'protocols/holdout-freeze.json';cfg=json.loads(path.read_text())
 cfg.update(shuffle_within_batch=True,primary_reward='F-R',primary_joint='F-auto-0.6',pure_reward_comparators=['UCB1','Growing-MOSS','MC-MOSS','Thompson','KL-UCB'],noninferiority='Primary claim of zero excess tested descriptively. Separate pre-specified relaxed criterion: E[R_F] <= 1.05 E[R_baseline] + 2, one-sided t intervals Bonferroni over 60 per-scenario comparisons. This is NOT literal no-worse.',
 selected_before_test='Reward F-R cold Beta(1+2S,1+2(n-S)) protected by reward ledger 16*running spectrum selected by smallest development3 mean regret (42.1093); exact TS endpoint retained. Auto .6 chosen from developer sweep as moderate service, both cold and standard-TS core disclosed. All configurations including poor ones retained. No choices use holdout results.',
 comparisons='Both baselines and F modes use identical reporting. Direct TS has fractional Beta updates for bounded non-Bernoulli data and no falsely claimed posterior correctness. F-R-TS-exact should be bit-identical to Thompson. Primary F-R has no designated service. No future horizon or means reach choice routine.')
 path.write_text(json.dumps(cfg,indent=2));print(len(P))
