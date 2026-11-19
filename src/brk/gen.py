# Разбор фраз по словам: fugashi + словарь курса + частицы/вспомогательные вручную
import json,re,sys
from fugashi import Tagger
T=Tagger()
C=json.load(open(sys.argv[1]))
def hira(s): return ''.join(chr(ord(c)-0x60) if 'ァ'<=c<='ヶ' else c for c in (s or ''))
def plain(s): return re.sub(r'\{([^|}]*)\|([^}]*)\}',r'\1',s or '')
def kana(s): return re.sub(r'\{([^|}]*)\|([^}]*)\}',r'\2',s or '')
KJ=re.compile(r'[一-鿿々]')
PUN=set('、。？！…「」　 ?!,.')
# --- словарь курса: plain/kana/lemma -> ru
SETP_=set('すみません ありがとう ありがとうございます おねがいします ございます しまった いってらっしゃい いってきます いらっしゃいませ いただきます ごちそうさま'.split())
PLAINS=set()
VOC={}; PK={}; KP={}; KITEM={}; VOCK={}
def addv(k,ru,lv,cid=None):
    if k: VOC.setdefault(k,[]).append((ru,lv,cid))
order=['n5','n4','n3']
for lv in order:
    for it in C[lv]['items']:
        KITEM.setdefault(hira(kana(it['jp'])).replace(' ','').replace('、','').replace('。',''),it['jp'])
        if it['kind']!='w': continue
        p=plain(it['jp']).replace(' ',''); k=hira(kana(it['jp'])).replace(' ','')
        cid=it['id'].split('|')[0]; addv(p,it['ru'],lv,cid); addv(k,it['ru'],lv,'K:'+cid if KJ.search(p) else cid); PLAINS.add(p)
        if KJ.search(p): PK.setdefault(p,k); KP.setdefault(k,it['jp'].replace(' ',''))
        toks=[w for w in T(p)]
        cont=[w for w in toks if w.feature.pos1 not in ('助動詞','助詞','補助記号')]
        rest=[w for w in toks if w.feature.pos1 in ('助動詞','助詞')]
        if len(cont)==1 and cont[0] is toks[0] and cont[0].feature.pos1 in ('動詞','形容詞') and p not in SETP_ and all((w.feature.lemma or '').split('-')[0] in ('ます','た','ない','です','だ','ず') for w in rest):
            lem=(cont[0].feature.lemma or '').split('-')[0]
            if lem: addv(lem,it['ru'],lv,cid)
            if lem and not KJ.search(lem): addv(hira(cont[0].feature.kanaBase or ''),it['ru'],lv,cid)
            if lem and KJ.search(lem): VOCK.setdefault(hira(cont[0].feature.kanaBase or ''),set()).add(lem)
# --- частицы: (поверхность, тип) -> (коротко, пояснение)
P={
('は','係助詞'):('частица темы','«что касается…» — о чём фраза. Читается «ва». これは… = «это — …»'),
('も','係助詞'):('тоже','«тоже, и … тоже». Встаёт вместо は/が/を'),
('こそ','係助詞'):('именно',''),
('が','格助詞'):('подлежащее','показывает, КТО/ЧТО: часто с すき, ある/いる, わかる, после だれ/なに'),
('が','接続助詞'):('но','«но» между двумя частями фразы'),
('を','格助詞'):('объект действия','ЧТО делают: パンを たべます = ем хлеб. Читается «о»'),
('に','格助詞'):('в / к / в (время) / кому','где находится (にいる/ある), куда (にいく), во сколько (7じに), кому (ともだちに)'),
('で','格助詞'):('где / чем','место действия (レストランで たべる) или средство (バスで, はしで)'),
('へ','格助詞'):('в сторону','направление «в/к». Читается «э»'),
('と','格助詞'):('и / с (кем) / (цитата)','«и» между предметами, «с кем» (ともだちと) или цитата перед いう/おもう'),
('と','接続助詞'):('если / когда','«если (всегда)…, то…»'),
('から','格助詞'):('из / от / с','откуда или с какого времени: 日本から = из Японии'),
('から','接続助詞'):('потому что','после причины: «…, потому что / так что»'),
('まで','格助詞'):('до','«до» места или времени'),
('まで','副助詞'):('даже / до',''),
('の','格助詞'):('связка «чей / какой»','わたしの ほん = моя книга. A の B = B, относящийся к A'),
('の','準体助詞'):('(то, что / объяснение)','заменяет существительное или даёт объяснение: …んです / …のです'),
('の','終助詞'):('(мягкий вопрос)','разговорный вопрос или объяснение'),
('より','格助詞'):('чем','сравнение: A より B = B больше, чем A'),
('や','副助詞'):('и (среди прочего)','перечисление не до конца: パンや ミルク = хлеб, молоко и т.п.'),
('や','格助詞'):('и (среди прочего)','перечисление не до конца'),
('か','終助詞'):('?','вопросительная частица — делает из фразы вопрос'),
('か','副助詞'):('или / что-то','«или»; после вопросительного слова — «что-то, кто-то»: なにか'),
('ね','終助詞'):('да? / же','ищет согласия: «…, да?», «…же»'),
('ねえ','終助詞'):('да? / же',''),
('よ','終助詞'):('(точно говорю)','сообщает новое: «…, вот так-то»'),
('よね','終助詞'):('же, да?',''),
('な','終助詞'):('(эмоция / не делай)','после формы словаря — запрет «не …!», иначе эмоция'),
('わ','終助詞'):('(эмоция)',''),
('ぞ','終助詞'):('(усиление)',''),
('さ','終助詞'):('(разговорное)',''),
('て','接続助詞'):('て-форма','связка: «сделал и…»; с ください — просьба, с いる — процесс/состояние'),
('で','接続助詞'):('て-форма','то же, что て (после ん/ぐ/ぶ/む)'),
('ば','接続助詞'):('если','условие «если …, то …»'),
('ても','接続助詞'):('даже если',''),
('でも','接続助詞'):('даже если',''),
('けど','接続助詞'):('но','«но, а» (разговорно)'),
('けれど','接続助詞'):('но',''),
('けれども','接続助詞'):('но',''),
('ので','接続助詞'):('так как','причина, мягче чем から'),
('のに','接続助詞'):('хотя / а ведь',''),
('し','接続助詞'):('и ещё (причины)','перечисление причин: «и …, и …»'),
('ながら','接続助詞'):('одновременно','«делая …» — два действия сразу'),
('たり','接続助詞'):('то… то…','перечисление действий: …たり …たり する'),
('たり','副助詞'):('то… то…',''),
('だり','接続助詞'):('то… то…',''),
('だけ','副助詞'):('только',''),
('しか','副助詞'):('только (с «не»)','しか + отрицание = «только»'),
('など','副助詞'):('и тому подобное',''),
('ぐらい','副助詞'):('примерно',''),
('くらい','副助詞'):('примерно',''),
('ほど','副助詞'):('примерно / настолько',''),
('ばかり','副助詞'):('только и / только что',''),
('でも','副助詞'):('хоть / даже',''),
('って','副助詞'):('мол (цитата)','разговорная цитата: «говорят, что…» / «…, это что»'),
('って','格助詞'):('мол (цитата)',''),
('とか','副助詞'):('например / или там',''),
('さえ','副助詞'):('даже',''),
('ずつ','副助詞'):('по (сколько-то)',''),
('のみ','副助詞'):('только',''),
('きり','副助詞'):('только / с тех пор',''),
('なんか','副助詞'):('какой-то / типа',''),
('なんて','副助詞'):('какой-то / такие как',''),
('に','副助詞'):('',''),
}
# вспомогательные (окончания) по лемме
AUX={'です':'вежливое «есть / является»','だ':'«есть» (просто)','ます':'вежливое окончание','た':'прошедшее время','ない':'«не»','ず':'«не»','ぬ':'«не»',
 'たい':'«хочу …»','う':'«давай …» / намерение','よう':'«давай …» / намерение','れる':'пассив / «можно»','られる':'пассив / «можно»','せる':'«заставить / дать»','させる':'«заставить / дать»',
 'らしい':'«похоже, говорят»','そう':'«похоже / говорят»','ようだ':'«кажется»','みたい':'«как будто»','べし':'«следует»','まい':'«не буду»','やす':'',
 'ちゃう':'«совсем / случайно»','じゃう':'«совсем / случайно»'}
FORMS={'ます':'вежливо, сейчас/будущее','ました':'вежливо, в прошлом','ません':'вежливо, «не …»','ませんでした':'вежливо, «не …» в прошлом',
 'ましょう':'«давай(те) …»','ましょうか':'«давай(те) …?» / «может, мне …?»','ませんか':'«не хочешь …?» — приглашение','た':'прошедшее','だ':'просто «есть»','だった':'«был» (просто)','でした':'вежливо «был»',
 'ない':'«не …»','なかった':'«не …» в прошлом','たい':'«хочу …»','たいです':'«хочу …» (вежливо)','たかった':'«хотел …»','たくない':'«не хочу …»',
 'て':'て-форма (и / …)','で':'て-форма (и / …)','ている':'процесс / состояние («сейчас делает»)','ています':'процесс / состояние, вежливо','ていました':'делал / было (процесс), вежливо',
 'てください':'«пожалуйста, сделай …»','ないでください':'«пожалуйста, не делай …»','てもいいですか':'«можно …?»','てはいけません':'«нельзя …»',
 'れる':'пассив / «можно»','られる':'пассив / «можно»','られます':'«можно / могу» (вежливо)','れます':'«можно / могу» (вежливо)','よう':'«давай …»','う':'«давай …»','ば':'«если …»','たら':'«если / когда …»','なければなりません':'«нужно …»',
 'そう':'«похоже, что …»','く':'наречная форма (-о)','くない':'«не …» (прилагательное)','かった':'прошедшее (прилагательное)','くなかった':'«не был …» (прилагательное)','くて':'«… и …» (прилагательное)','な':'(связка на-прилагательного)','に':'наречие («-о»)'}
PRE={'お':'вежливая приставка','ご':'вежливая приставка','御':'вежливая приставка','毎':'каждый','第':'номер (порядковый)','初':'первый','全':'весь','不':'не-','無':'без-','未':'ещё не','再':'снова','新':'новый','大':'большой','小':'маленький'}
SUF={'人':'«-ец», человек (национальность/профессия)','語':'язык','さん':'вежливое обращение (г-н/г-жа)','ちゃん':'ласковое обращение','くん':'обращение к парню','様':'очень вежливо (г-н/г-жа)','さま':'очень вежливо','屋':'магазин / продавец','中':'весь / в течение / сейчас идёт',
 '時':'час','分':'минута','円':'иена','年':'год','月':'месяц','日':'день / число','回':'раз','目':'-ый (по порядку)','達':'(мн. число)','たち':'(мн. число)','的':'-ический','者':'человек (деятель)','員':'сотрудник','会':'встреча, собрание','料':'плата','代':'плата / эпоха','方':'способ / как …',
 '後':'после','前':'до / назад','頃':'около (времени)','ごろ':'около (времени)','ぐらい':'примерно','くらい':'примерно','歳':'лет (возраст)','才':'лет (возраст)','個':'штук','つ':'штук (счёт)','本':'штук (длинных)','枚':'штук (плоских)','冊':'книг (счёт)','台':'штук (машин)','匹':'штук (животных)','杯':'стаканов','階':'этаж','番':'номер','週間':'недель','時間':'часов','ヶ月':'месяцев','か月':'месяцев',
 '屋さん':'магазин','製':'сделано в','行き':'в направлении','用':'для','式':'стиль','性':'-ость','感':'чувство','力':'сила','化':'-изация','家':'-ист, человек','室':'комната','場':'место','所':'место','館':'здание','店':'магазин','駅':'станция','線':'линия','号':'номер','度':'раз / градусы','号室':'номер комнаты',
 'ずつ':'по','ごと':'каждые','しか':'только','など':'и т.п.','がる':'(о чувствах других)','さ':'-ость','み':'-ость','め':'-оватый','っぽい':'похожий на','らしい':'настоящий / типичный','向け':'для','おき':'через (каждые)','以上':'и больше','以下':'и меньше','以内':'в пределах','中心':'центр'}
# --- чтения из разметки {漢字|かな}: посимвольная карта групп
def groups(jp):
    out=[]; pos=0
    for m in re.finditer(r'\{([^|}]*)\|([^}]*)\}',jp):
        for ch in jp[pos:m.start()]: out.append((ch,None))
        out.append((m.group(1),m.group(2))); pos=m.end()
    for ch in jp[pos:]: out.append((ch,None))
    return out  # [(текст, чтение|None)]
NUM=dict(zip('一二三四五六七八九十百千万','1 2 3 4 5 6 7 8 9 10 100 1000 10000'.split()))
UNK={}
class U:  # единица разбора (токен или склеенное по словарю слово)
    def __init__(s,surf,rd,pos,pos2,lem,kb,merged=False):
        s.s=surf; s.rd=rd; s.pos=pos; s.pos2=pos2; s.lem=lem; s.kb=kb; s.merged=merged
def tok_readings(jp,toks):
    gs=groups(jp); flat=[]
    for gi,(t,r) in enumerate(gs):
        for ch in t: flat.append((ch,gi))
    text=''.join(c for c,_ in flat)
    spans=[]; i=0
    for w in toks:
        s=w.surface; j=text.find(s,i)
        if j<0: spans.append(None); continue
        spans.append((j,j+len(s))); i=j+len(s)
    res=[None]*len(toks)
    # группы, разрезанные на несколько токенов: делим чтение группы
    for gi,(gt,gr) in enumerate(gs):
        if gr is None: continue
        idx=[k for k,sp in enumerate(spans) if sp and any(flat[x][1]==gi for x in range(sp[0],sp[1]))]
        if len(idx)<=1: continue
        if not all(all(flat[x][1]==gi for x in range(spans[k][0],spans[k][1])) for k in idx): continue
        off=0; ok=True; parts=[]
        for n,k in enumerate(idx):
            w=toks[k]; cands=[PK.get(w.surface),hira(w.feature.kana or ''),hira(w.feature.kanaBase or '')]
            if n==len(idx)-1: parts.append(gr[off:]); break
            hit=next((c for c in cands if c and gr.startswith(c,off)),None)
            if not hit: ok=False; break
            parts.append(hit); off+=len(hit)
        if ok and len(parts)==len(idx) and all(parts):
            for k,pr in zip(idx,parts): res[k]=pr
    for k,w in enumerate(toks):
        if res[k] is not None: continue
        sp=spans[k]; fr=hira(w.feature.kana or w.surface)
        if not sp: res[k]=fr; continue
        gis=[flat[x][1] for x in range(sp[0],sp[1])]; uniq=sorted(set(gis))
        whole=all(sum(1 for g in gis if g==u)==len(gs[u][0]) for u in uniq)
        res[k]=''.join((gs[u][1] if gs[u][1] is not None else hira(gs[u][0])) for u in uniq) if whole else fr
    return res
NAMES=set('ユキ デニス ケン タナカ 田中 山田 鈴木 佐藤 高橋 マリア アンナ マイク 中村 小林 伊藤 渡辺 山本 加藤 木村 森 林 リー ジョン トム'.split())
GL={}   # ручные значения (дополняются ниже)
NOTE={} # ручные пояснения к целым фразам/словам
CTX=[None]
def pickv(lst):
    cid=CTX[0]
    direct=[x for x in lst if not (x[2] or '').startswith('K:')] or lst
    for ru,lv,c in direct:
        if cid and c==cid: return ru
    return direct[0][0]
def meaning(u):
    if u.s in NAMES or u.lem in NAMES: return 'имя'
    if u.s in GL: return GL[u.s]
    if u.lem in GL and u.pos in ('動詞','形容詞'): return GL[u.lem]
    if u.pos in ('動詞','形容詞'):
        keys=(u.lem,)+((u.kb,) if not KJ.search(u.lem) else ())
        # глагол в тексте каной (すみます), а в словаре — кандзи: берём, только если чтение однозначно
        if not KJ.search(u.s) and u.kb in VOCK and len(VOCK[u.kb])==1: keys+=tuple(VOCK[u.kb])
    else: keys=(u.s,u.lem) if KJ.search(u.s) else (u.s,u.lem,u.rd,u.kb,hira(u.lem))
    for k in keys:
        if k and k in VOC: return pickv(VOC[k])
        if k and k in GL: return GL[k]
    if u.pos2=='数詞': return NUM.get(u.s,'число')
    if u.pos2=='固有名詞': return 'имя / название'
    return None
def units(jp):
    p=plain(jp); toks=list(T(p)); rds=tok_readings(jp,toks)
    us=[U(w.surface,rd,w.feature.pos1,w.feature.pos2,(w.feature.lemma or '').split('-')[0],hira(w.feature.kanaBase or '')) for w,rd in zip(toks,rds)]
    out=[]; i=0
    while i<len(us):
        best=None
        for n in (5,4,3,2):
            seg=us[i:i+n]
            if len(seg)<n: continue
            ss=''.join(x.s for x in seg)
            if any(x.pos in ('補助記号','空白') for x in seg): continue
            if any(x.pos in ('助詞','助動詞') for x in seg) and ss not in SETP and not ((i==0) and (ss in VOC) and not any(x.pos=='動詞' for x in seg) and (n==len(us) or us[i+n].pos in ('助詞','補助記号','助動詞'))): continue
            if ss in VOC or ss in GL: best=(n,ss); break
        if best:
            n,ss=best; seg=us[i:i+n]
            uu=U(ss,''.join(x.rd for x in seg),'名詞','普通名詞',ss,''.join(x.kb for x in seg),True); uu.sub=seg; out.append(uu); i+=n; continue
        out.append(us[i]); i+=1
    return out
SETP=set('こんにちは こんばんは ありがとう おめでとう いただきます ごちそうさま ごちそうさまでした しつれいします しつれいしました いってらっしゃい いってきます ただいま おかえりなさい おやすみなさい ごめんなさい ごめんください いらっしゃいませ いらっしゃい もしもし すみません さようなら よろしく おねがいします ございます おはようございます ありがとうございます どういたしまして はじめまして おげんきですか おつかれさまです おだいじに'.split())
def kana2jp(s):
    # kana-фразу (диалоги) превращаем в разметку с кандзи по словарю курса, чтобы разбор был точнее
    out=''; i=0
    while i<len(s):
        hit=None
        for n in range(min(10,len(s)-i),2,-1):
            k=s[i:i+n]
            if k in KP: hit=(n,KP[k]); break
        if hit: out+=hit[1]; i+=hit[0]
        else: out+=s[i]; i+=1
    return out
VAUX={'居る','いる','有る','ある','下さる','くださる','見る','みる','置く','おく','仕舞う','しまう','行く','いく','来る','くる','上げる','あげる','呉れる','くれる','貰う','もらう'}
def brk(jp):
    ch=[]
    for u in units(jp):
        s=u.s; pos=u.pos; prev=ch[-1] if ch else None
        if pos in ('補助記号','空白') or s in PUN: continue
        if pos=='助詞':
            if s in ('て','で','たり','だり','ば','ても','でも') and u.pos2=='接続助詞' and prev and prev['kind']=='c':
                prev['tail'].append((s,u.rd,'て' if s in ('て','で') else s)); continue
            info=P.get((s,u.pos2)) or P.get((s,'格助詞')) or P.get((s,'副助詞')) or P.get((s,'終助詞')) or P.get((s,'接続助詞'))
            if not info: UNK['P:'+s+':'+u.pos2]=UNK.get('P:'+s+':'+u.pos2,0)+1
            ch.append({'kind':'p','s':s,'rd':u.rd,'m':info[0] if info else 'частица','n':info[1] if info else ''}); continue
        if pos=='助動詞':
            if prev and prev['kind']=='c' and not (u.lem in ('です','だ') and prev.get('pos') in ('名詞','代名詞','形状詞','接尾辞')):
                prev['tail'].append((s,u.rd,u.lem)); continue
            if prev and prev['kind']=='x': prev['tail'].append((s,u.rd,u.lem)); continue
            ch.append({'kind':'x','s':s,'rd':u.rd,'lem':u.lem,'tail':[],'pos':pos}); continue
        if pos=='接尾辞':
            m=SUF.get(s) or GL.get(s)
            if s=='人' and u.rd=='にん': m='человек (счёт людей)'
            if s=='人' and u.rd=='じん': m='«-ец», человек из … (日本人 = японец)'
            if prev and prev['kind']=='c' and not prev['tail']:
                prev.setdefault('suf',[]).append((s,u.rd,m or ''))
                if not m: UNK['S:'+s]=UNK.get('S:'+s,0)+1
                continue
            ch.append({'kind':'c','s':s,'rd':u.rd,'m':m or '','tail':[],'pos':pos,'u':u}); continue
        if pos=='接頭辞' and not (s in VOC and s not in PRE):
            ch.append({'kind':'pre','s':s,'rd':u.rd,'m':PRE.get(s,'приставка')}); continue
        if pos=='動詞' and prev and prev['kind']=='c' and prev['tail'] and prev['tail'][-1][2]=='て' and u.lem in VAUX:
            prev['tail'].append((s,u.rd,'V:'+u.lem)); continue
        if pos in ('形状詞','名詞') and u.pos2=='助動詞語幹' and s in ('よう','そう','みたい'):
            ch.append({'kind':'c','s':s,'rd':u.rd,'m':{'よう':'похоже, кажется (…ようです)','そう':'похоже, на вид (…そうです)','みたい':'как будто, похоже'}[s],'tail':[],'pos':'形状詞','u':u}); continue
        if pos=='形容詞' and u.lem in ('無い','ない') and prev and prev['kind']=='c' and prev.get('pos') in ('動詞','形容詞'):
            prev['tail'].append((s,u.rd,'ない')); continue
        m=meaning(u)
        if s=='ところ' and prev and prev['kind']=='c' and prev['tail'] and (prev['tail'][-1][2] in ('V:居る','V:いる','た','う','よう') or prev['tail'][-1][0] in ('る',)):
            m='момент: «как раз сейчас / только что / вот-вот»'
        if m is None: k=s+'|'+u.rd; UNK[k]=UNK.get(k,0)+1
        ch.append({'kind':'c','s':s,'rd':u.rd,'m':m,'tail':[],'pos':pos,'lem':u.lem,'u':u})
    return ch

def isk(c): return 'ぁ'<=c<='ゖ' or 'ァ'<=c<='ヺ' or c=='ー'
def mk(s,rd):
    if not (KJ.search(s) and rd and rd!=s): return s
    pre=suf=''
    while len(s)>1 and isk(s[-1]) and rd and hira(s[-1])==rd[-1] and KJ.search(s[:-1]): suf=s[-1]+suf; s=s[:-1]; rd=rd[:-1]
    while len(s)>1 and isk(s[0]) and rd and hira(s[0])==rd[0] and KJ.search(s[1:]): pre+=s[0]; s=s[1:]; rd=rd[1:]
    if not KJ.search(s) or not rd: return pre+s+suf
    if all(KJ.search(c) for c in s): return pre+'{%s|%s}'%(s,rd)+suf
    return pre+'{%s|%s}'%(s,rd)+suf
def clean_ru(m):
    return (m or '').strip()
def row(c):
    if c['kind']=='p': return [mk(c['s'],c['rd']),c['m'],c['n'],'p']
    if c['kind']=='pre': return [mk(c['s'],c['rd']),c['m'],'','x']
    if c['kind']=='x':
        tail=c['s']+''.join(t[0] for t in c['tail']); return [tail,FORMS.get(tail) or AUX.get(c['lem'],'окончание'),'','x']
    base=mk(c['s'],c['rd']); sufs=c.get('suf',[])
    uu=c.get('u')
    txt=base+''.join(mk(s,r) for s,r,_ in sufs)+''.join(t[0] for t in c['tail'])
    m=clean_ru(c['m']) if c['m'] else ''
    notes=[]
    if uu is not None and getattr(uu,'merged',False) and len(getattr(uu,'sub',[]))>=2 and KJ.search(uu.s) and all(x.pos in ('名詞','接尾辞','接頭辞','代名詞') for x in uu.sub):
        parts=[]
        for x in uu.sub:
            xm=(SUF.get(x.s) if x.pos=='接尾辞' else None) or (PRE.get(x.s) if x.pos=='接頭辞' else None) or meaning(x)
            if x.s=='人' and x.rd=='じん': xm='«-ец», человек из …'
            if x.s=='人' and x.rd=='にん': xm='человек (счёт)'
            if x.s=='語' and x.rd=='ご': xm='язык'
            parts.append((f'{mk(x.s,x.rd)} {xm}' if xm.startswith('«') else f'{mk(x.s,x.rd)} «{xm}»') if xm else mk(x.s,x.rd))
        if all('«' in p for p in parts): notes.append('из частей: '+' + '.join(parts))
    for s,r,sm in sufs:
        if sm: notes.append(f'{mk(s,r)} — {sm}')
    if uu is not None and uu.pos=='形容詞' and not c['tail'] and c.get('lem') and c['s']!=c['lem']:
        end={'く':'наречная форма («-о») / перед なる','かっ':'прошедшее','くて':'«… и …»','けれ':'условная форма'}
        e=next((v for k,v in end.items() if c['s'].endswith(k)),'')
        if e: notes.append(f"словарная форма: {mk(c['lem'],uu.kb) if c['lem'] in PLAINS else (uu.kb or c['lem'])} · {e}")
    if c['tail']:
        tail=''.join(t[0] for t in c['tail'])
        lab=FORMS.get(tail)
        if not lab:
            parts=[]
            for s,r,l in c['tail']:
                if l.startswith('V:'): v=l[2:]; parts.append({'居る':'(процесс/состояние)','いる':'(процесс/состояние)','有る':'(состояние)','ある':'(состояние)','下さる':'«пожалуйста»','くださる':'«пожалуйста»','見る':'«попробовать»','みる':'«попробовать»','置く':'«заранее»','おく':'«заранее»','仕舞う':'«до конца / нечаянно»','しまう':'«до конца / нечаянно»','行く':'«(уходя) дальше»','いく':'«(уходя) дальше»','来る':'«(приходя) сюда»','くる':'«(приходя) сюда»','上げる':'«для кого-то»','あげる':'«для кого-то»','呉れる':'«для меня»','くれる':'«для меня»','貰う':'«мне сделали»','もらう':'«мне сделали»'}.get(v,''))
                elif l=='て': parts.append('て-форма')
                else: parts.append(AUX.get(l) or FORMS.get(s) or s)
            lab=' + '.join(x for x in parts if x)
        lem=c.get('lem') or ''
        u=c.get('u')
        if u is not None and u.pos in ('動詞','形容詞') and lem and lem!=c['s']:
            kb=u.kb
            notes.insert(0,f'словарная форма: {mk(lem,kb) if (KJ.search(lem) and lem in PLAINS) else (kb or lem)}')
        notes.append(f'{tail} — {lab}')
    return [txt,m,' · '.join(notes),'c']
def nk(jp): return re.sub(r'[\s　、。？！?!…,.「」]','',plain(jp))
def post(rows):
    out=[]; i=0
    while i<len(rows):
        r=rows[i]
        if i+2<len(rows) and r[0] in ('で','じゃ') and r[3]=='p' and rows[i+1][0]=='は' and re.match(r'^(ありません|ない|なかった|ありませんでした)',rows[i+2][0]):
            t=r[0]+'は'+rows[i+2][0]; out.append([t,'«не является / не …» (отрицание после существительного)',f'{r[0]}は + {rows[i+2][0]}: вежливо — ではありません, по-простому — じゃない','x']); i+=3; continue
        if i+1<len(rows) and r[0] in ('じゃ',) and re.match(r'^(ありません|ない|なかった)',rows[i+1][0]):
            out.append([r[0]+rows[i+1][0],'«не является / не …»','じゃ = では (разговорно)','x']); i+=2; continue
        out.append(r); i+=1
    return out
def breakdown(jp,cid=None):
    CTX[0]=cid
    if not KJ.search(jp) and '{' not in jp:
        raw=jp.replace(' ','')
        if raw in KITEM: jp=KITEM[raw]
        else:
            best=None
            for cand in (jp,kana2jp(raw)):
                saved=dict(UNK); c=brk(cand); bad=sum(1 for x in c if x['kind']=='c' and not x['m'])
                UNK.clear(); UNK.update(saved)
                sc=bad*10+len(c)
                if best is None or sc<best[0]: best=(sc,cand)
            jp=best[1]
    ch=brk(jp); r=post([row(c) for c in ch])
    k=plain(jp).replace(' ','')
    if k in NOTE: r.append(['💡',NOTE[k],'','n'])
    return r
GL.update({'痛い':'больно, болит','住む':'жить (где-то)','徐々':'постепенно','常':'всегда, обычно','要する':'требовать (要するに — «короче говоря»)','知れる':'(かもしれない = «может быть»)','けれど':'но','けれども':'но','ほんの':'всего лишь','頂く':'получать (скромно); いただきます — «приятного аппетита»'});
GL.update({'とおり':'как, согласно (…のとおり); ещё — улица'});
GL.update({'時給':'почасовая оплата','残業':'сверхурочная работа','終電':'последняя электричка','口座':'банковский счёт','試着':'примерка','動画':'видео','画面':'экран','救急':'экстренная (помощь)','救急車':'скорая помощь (машина)','びっくり':'испуг, удивление','ご覧':'смотреть (уважительно)','寿司':'суши','納豆':'натто (бродившие соевые бобы)','カラオケ':'караоке','メール':'сообщение, e-mail','ごめん':'прости','ちょっと':'немного, минутку («ちょっと…» с паузой — мягкий отказ)','違う':'отличаться; «не так»','時':'время, когда'})
SUF.update({'車':'машина','国':'страна','違い':'разница','にくい':'трудно (делать)','やすい':'легко (делать)','やすかっ':'легко (делать)','ら':'(мн. число)'})
P[('ん','準体助詞')]=('= の (объяснение)','разговорное の: …んです = «дело в том, что …»')
P[('ん','格助詞')]=('= の','разговорное の')
P[('い','終助詞')]=('(разговорное)','')
P[('つつ','接続助詞')]=('продолжая / хотя','')
P[('とも','接続助詞')]=('даже если','')
NOTE.update({
 'ちがいます':'Буквально «отличается». Так отвечают «нет, не так / вы ошиблись». いいえ — просто «нет», а ちがいます — «не то, неверно».',
 'ちがう':'Буквально «отличаться». ちがう / ちがいます = «не так, неверно». いいえ — просто «нет».',
 '方':'かた — вежливое «человек»: あの方 = «тот человек» (с уважением). Обычное слово — 人 (ひと). Про себя かた не говорят.',
 'さようなら':'Прощание надолго или официально. С друзьями говорят じゃあ また / またね.',
 'じゃあまた':'«Ну, до встречи» — с друзьями, когда скоро увидитесь. さようなら — надолго/официально.',
 'ありがとうございます':'ありがとう + ございます (вежливое «есть»). Друзьям можно просто ありがとう.',
 'すみません':'«Извините»: позвать официанта, протиснуться, извиниться перед чужим. Ещё значит «спасибо (простите за беспокойство)».',
 'ごめんなさい':'«Прости, я виноват» — когда реально накосячил. С чужими чаще すみません.',
 'おねがいします':'お + ねがい («просьба») + します («делаю») = «прошу». Ставится после того, что просишь: みずを おねがいします.',
 'よろしくおねがいします':'よろしく («хорошо, благосклонно») + おねがいします («прошу») = «прошу любить и жаловать / рассчитываю на вас».',
 'いいえ':'Просто «нет». Если человек ошибся — говорят ちがいます («не так»).',
 'こんにちは':'Читается «конничи ВА» — は здесь частица (буквально «что касается сегодняшнего дня…»).',
 'こんばんは':'Читается «конбан ВА» — は здесь частица («что касается вечера…»).',
 'わたし':'«Я» — нейтрально, подходит всем. Мужчины в разговоре говорят ぼく/おれ.',
 'です':'Вежливая связка «есть, является». Сама по себе не переводится: がくせいです = «(я) студент».',
})
if __name__=='__main__':
    out={}; srcs=[]
    for lv in order:
        for it in C[lv]['items']:
            p=plain(it['jp'])
            cid=it['id'].split('|')[0]
            if it['kind']=='s': srcs.append((it['jp'],cid,'s'))
            else:
                toks=[w for w in T(p.replace(' ','')) if w.feature.pos1 not in ('補助記号',)]
                if len(toks)>=2 or p.replace(' ','') in NOTE: srcs.append((it['jp'],cid,'w'))
        for t in C[lv]['talk']:
            cid=t['id'].split('|')[0]
            for a in [t['q']]+t['ans'][:1]: srcs.append((re.sub(r'（[^）]*）|\([^)]*\)','',a).strip(),cid,'s'))
    seen=set()
    for jp,cid,kind in srcs:
        k=nk(jp)
        if not k or k in seen: continue
        seen.add(k); r=breakdown(jp,cid)
        if kind=='w' and len([x for x in r if x[3]!='n'])>1 and k not in NOTE: continue
        if any((x[3]=='c' and not x[1]) or (x[3]=='p' and x[1]=='частица') for x in r): continue
        if len(r)>=2 or (len(r)==1 and r[0][2]): out[k]=r
    pj={}
    for (sf,t),(a,b) in P.items():
        if sf not in pj or t in ('格助詞','係助詞'): pj[sf]=[a,b]
    json.dump({'b':out,'p':pj},open(sys.argv[2],'w'),ensure_ascii=False,separators=(',',':'))
    unk=sorted(UNK.items(),key=lambda x:-x[1])
    print(len(out),'phrases;',len(unk),'unknown')
    open('/tmp/unk.txt','w').write('\n'.join(f'{k}\t{v}' for k,v in unk))
