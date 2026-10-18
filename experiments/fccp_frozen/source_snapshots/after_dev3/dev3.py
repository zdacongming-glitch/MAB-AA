from study_v2 import *
P3=[p('TS'),p('MC-MOSS',core=2),p('Growing-MOSS',core=1),p('UCB1',core=10),p('TS-cold',temperature=.5),p('F-R-cold16',temperature=.5,br=16.)]
for core in [11,12]:
 for temp in [.4,.5,.65]:
  for br in [None,16.]:P3.append(p(f'Warm{core}-temp{temp}-guard{br}',core=core,temperature=temp,br=br))
D3=D2+[sc('dev3_tinygap',[(1,[.50,.51])],eps=.025,eta=.005,T=16000)]
if __name__=='__main__':freeze('development3',D3,P3,32,104110100,104120100)
