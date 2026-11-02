import json,sys,time,urllib.request
url=sys.argv[1]; rer=True; minimum=int(sys.argv[2]) if len(sys.argv)>2 else 0
qs=[json.loads(l) for l in open(__file__.rsplit('/',1)[0]+'/questions.jsonl')]
h1=h5=0;mrr=0;T=[];miss=[]
for x in qs:
    b={"question":x["q"],"top_k":5}
    if not rer:b["rerank"]=False
    r=urllib.request.Request(url+'/query',data=json.dumps(b).encode(),headers={'Content-Type':'application/json'})
    t=time.time();d=json.load(urllib.request.urlopen(r,timeout=180));T.append(time.time()-t)
    fs=[s['file'] for s in d['sources']]
    rank=next((i for i,f in enumerate(fs) if any(g.lower() in f.lower() for g in x['gold'])),None)
    if rank is None: miss.append(x['q'][:48])
    else:
        h5+=1;h1+=rank==0;mrr+=1/(rank+1)
n=len(qs);T.sort()
print(f"{url}: n={n} Treffer@1 {h1} Treffer@5 {h5} MRR {mrr/n:.3f} median {T[n//2]:.2f}s max {T[-1]:.2f}s")
print(' verfehlt:',miss)
sys.exit(0 if h5>=minimum else 1)
