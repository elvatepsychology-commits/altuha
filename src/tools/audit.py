import json,re,sys
sys.path.insert(0,'/tmp/dl')
from lists import L, norm
GODAN={'う':'い','く':'き','ぐ':'ぎ','す':'し','つ':'ち','ぬ':'に','ぶ':'び','む':'み','る':'り'}
def forms(w):
    out=set()
    for x in re.split(r'[;；/]',w):
        x=norm(x)
        if not x: continue
        out.add(x)
        if x.endswith('する'): out.add(x[:-2]+'します'); out.add(x[:-2])
        if x.endswith('くる') or x.endswith('来る'): out.add(x[:-1]+'ます'); out.add(x[:-2]+'きます')
        if x and x[-1] in GODAN: out.add(x[:-1]+GODAN[x[-1]]+'ます')
        if x.endswith('る'): out.add(x[:-1]+'ます')
        if x.endswith('い'): out.add(x+'です')
        if x.startswith('お') or x.startswith('ご'): out.add(x[1:])
        else: out.add('お'+x); out.add('ご'+x)
    return out
def listkeys(lv):
    m={}
    for w in L[lv]:
        for k in forms(w['e'])|forms(w['r']): m.setdefault(k,w)
    return m
K={l:listkeys(l) for l in L}
def inlist(t,levels):
    for k in (norm(t['p']),norm(t['k'])):
        for l in levels:
            if k in K[l]: return l
    return None
if __name__=='__main__':
    ci=json.load(open('/tmp/dl/course_items.json'))
    for lv,below in [('n5',['n5']),('n4',['n5','n4'])]:
        ws=[t for t in ci[lv] if t['kind']=='w']
        have=set()
        for t in ws:
            for k in (norm(t['p']),norm(t['k'])): have|=forms(k)|{k}
        miss=[w for w in L[lv] if not (forms(w['e'])|forms(w['r']))&have]
        off=[t for t in ws if not inlist(t,below)]
        hi=[(t['p'],inlist(t,['n3'])) for t in off]
        print(lv,'missing',len(miss),'| above/unlisted',len(off))
        print('  above-level (N3+):',' '.join(p for p,l in hi if l))
        print('  unlisted:',' '.join(p for p,l in hi if not l))
        json.dump(miss,open(f'/tmp/dl/miss_{lv}.json','w'),ensure_ascii=False)
