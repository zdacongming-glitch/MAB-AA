from exact_frontier import *
P=Path(__file__).parent
md=build(T=10,epsilon=.95,eta=.01,delta=.1,arrival=1)
rows=[]
for a in [20,19,18,17,16,15,14,13,12,11,10]:
 st=time.time();row,x=solve(md,a)
 print(a,row,round(time.time()-st,1),flush=True);rows.append(row)
 pd.DataFrame(rows).to_csv(P/'exact-easy.csv',index=False)
 if row['status']==2:break
