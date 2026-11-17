import csv, json, re
def load(l):
    out=[]
    for r in csv.DictReader(open(f'/tmp/dl/jlpt/src/{l}.csv',encoding='utf8')):
        e=r['expression'].strip(); rd=r['reading'].strip()
        out.append({'e':e,'r':rd,'m':r['meaning'].strip()})
    return out
L={l:load(l) for l in ['n5','n4','n3']}
def kata2hira(s): return ''.join(chr(ord(c)-0x60) if 'ァ'<=c<='ヶ' else c for c in s)
def norm(s): return kata2hira(re.sub(r'[\s～〜・、。？！…]','',s))
