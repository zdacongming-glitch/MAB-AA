"""One small usage demonstration, not an empirical superiority test."""
import json
import numpy as np
from flexible_ccp import FlexibleCCP

if __name__=='__main__':
    alg=FlexibleCCP.preset('balanced',epsilon=.20,eta=.05,seed=21)
    rng=np.random.default_rng(710)
    values={'A':.65,'B':.42,'C':.81,'D':.35}
    for t in range(1,2001):
        arrivals=['A','B'] if t==1 else (['C','D'] if t==1001 else [])
        arm,service=alg.choose(arrivals)
        # Evaluator's mean is used only after selection to generate one reward.
        alg.observe(float(rng.random()<values[arm]))
    print(json.dumps(alg.diagnostics(),ensure_ascii=False,indent=2))
    print('reports:',alg.report())
