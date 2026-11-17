import sys,re,csv; sys.path.insert(0,'/tmp/dl')
from lists import norm
from audit import forms
LV={}
for l in ['n5','n4','n3','n2','n1']:
    for r in csv.DictReader(open(f'/tmp/dl/jlpt/src/{l}.csv',encoding='utf8')):
        for k in forms(r['expression'])|forms(r['reading']):
            LV.setdefault(k,l)   # lowest level first since order n5..n1
ORDER={'n5':5,'n4':4,'n3':3,'n2':2,'n1':1}
def level(word, reading=''):
    best=None
    for k in [norm(word),norm(reading)]:
        if not k: continue
        l=LV.get(k)
        if l and (best is None or ORDER[l]>ORDER[best]): best=l
    return best
_T=None
def lemmas(text):
    global _T
    import fugashi
    if _T is None: _T=fugashi.Tagger()
    out=[]
    for t in _T(re.sub(r'\s','',text)):
        f=t.feature
        if f.pos1 in ('助詞','助動詞','補助記号','記号','接尾辞','接頭辞'): continue
        lem=(f.lemma or t.surface).split('-')[0]
        out.append((t.surface,lem,kata(f.kana or '')))
    return out
def kata(s): return ''.join(chr(ord(c)-0x60) if 'ァ'<=c<='ヶ' else c for c in s)
def above(text, maxlv):
    """content words in text whose lowest JLPT level is harder than maxlv"""
    bad=[]
    for s,lem,k in lemmas(text):
        l=level(lem) or level(s,k)
        if l and ORDER[l]<ORDER[maxlv]: bad.append((s,l))
    return bad

BASE_OK={'わり','割り','割','為る','呉れる','因る','仕舞う','付く','付ける','居る','有る','成る','遣る','貰う','上げる','置く','見る','出来る','無い','する','します','いい','良い','日本','しまう','くれる','よる','つく','つける','まだ','ござる','ございます','いる','ある','なる','くる','来る','やる','もらう','あげる','おく','みる','いく','行く','ない','そう','よう','こと','もの','ところ','とき','時','方','人','中','今','日','様','さん','君','くん','ちゃん'}
_V=None
def vocab_le(maxlv):
    """все выражения из списков уровня <= maxlv (для проверки составных слов)"""
    out=set()
    for l in ['n5','n4','n3','n2','n1']:
        if ORDER[l]<ORDER[maxlv]: break
        for r in csv.DictReader(open(f'/tmp/dl/jlpt/src/{l}.csv',encoding='utf8')):
            for x in re.split(r'[;；/]',r['expression']):
                x=norm(x)
                if len(x)>=2: out.add(x)
    return out
_VC={}
def level2(w,rd=''):
    cands=[w]
    x=re.sub(r'(する|します|しました|して)$','',w)
    if x!=w and x: cands.append(x)
    if w[:1] in 'おご' and len(w)>1: cands.append(w[1:])
    best=None
    for c in cands:
        l=level(c, rd if c==w else '')
        if l and (best is None or ORDER[l]>ORDER[best]): best=l
    return best
def above2(text,maxlv,extra_ok=()):
    if maxlv not in _VC: _VC[maxlv]=vocab_le(maxlv)
    V=_VC[maxlv]; plain=norm(text)
    bad=[]
    for s,lem,k in lemmas(text):
        if lem in BASE_OK or s in BASE_OK or lem in extra_ok or s in extra_ok: continue
        ls=[x for x in (level2(lem),level(s,k),level2(s)) if x]
        l=max(ls,key=lambda x:ORDER[x]) if ls else None
        if l and ORDER[l]<ORDER[maxlv]:
            # часть более длинного слова нужного уровня?
            if any(s in v and v in plain and len(v)>len(s) for v in V): continue
            bad.append((s,l))
    return bad
