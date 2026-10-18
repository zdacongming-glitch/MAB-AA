from exact_frontier import *
P=Path(__file__).parent
for T,arrival,a,filename in [(10,1,13,'exact-static-policy-a13.json'),(12,4,9,'exact-arrival-policy-a9.json')]:
 md=build(T=T,epsilon=.95,eta=.01,delta=.1,arrival=arrival)
 row,x=solve(md,a)
 if not row['success']:raise RuntimeError(row)
 action={}
 for e,(si,i,dest) in enumerate(md['edges']):action.setdefault(si,[]).append((i,float(x[e])))
 states=[]
 for si,actions in action.items():
  tot=sum(z for _,z in actions)
  if tot>1e-15:states.append(dict(state=list(md['states'][si]),action_probabilities={str(i):z/tot for i,z in actions}))
 obj=dict(scope='finite four-model fixed-reporter known-schedule policy',T=T,arrival=arrival,epsilon=.95,eta=.01,delta=.1,means=md['mu'].tolist(),area_budget=a,verification=row,states=states)
 (P/filename).write_text(json.dumps(obj));print(filename,len(states))
