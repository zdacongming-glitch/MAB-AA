from exact_frontier import *
P=Path(__file__).parent
md=build(T=12,epsilon=.95,eta=.01,delta=.1,arrival=4)
rows=[]
for a in range(18,-1,-1):
 st=time.time();row,x=solve(md,a)
 print(a,row,round(time.time()-st,1),flush=True);rows.append(row)
 pd.DataFrame(rows).to_csv(P/'exact-arrival.csv',index=False)
 if row['status']==2:break
 if row['status']!=0:break
 if a in [14,13,12,11]:
  action={}
  for e,(si,i,dest) in enumerate(md['edges']):
   action.setdefault(si,[]).append((i,float(x[e])))
  policy=[]
  for si,actions in action.items():
   tot=sum(z for _,z in actions)
   if tot>1e-15:policy.append(dict(state=list(md['states'][si]),action_probabilities={str(i):z/tot for i,z in actions}))
  (P/f'exact-arrival-policy-a{a}.json').write_text(json.dumps(dict(scope='finite four-model fixed-reporter known-schedule policy',T=12,arrival=4,epsilon=.95,eta=.01,delta=.1,means=md['mu'].tolist(),area_budget=a,states=policy)))
