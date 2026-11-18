#!/usr/bin/env python3
"""Сборка уровней N4/N3 + добор N5 по спискам JLPT (tanos), с проверкой уровня слов."""
import sys, re, json, glob, math
sys.path.insert(0, '/tmp/dl'); sys.path.insert(0, '/home/claude/altuha/src')
from build_lvl import parse, align, kata2hira
from lvlcheck import level2, above2, lemmas
from audit import forms
from lists import norm
import fugashi
TAG = fugashi.Tagger()
P = lambda x: re.sub(r'\{([^|}]*)\|[^}]*\}', r'\1', x)
R = lambda x: re.sub(r'\{[^|}]*\|([^}]*)\}', r'\1', x)
REPORT = []
REMOVED_RD = []

def tsv(globp):
    rows = []
    for f in sorted(glob.glob(globp)):
        for ln in open(f, encoding='utf8'):
            p = ln.rstrip('\n').split('|')
            if len(p) == 4: rows.append(p)
    return rows

def word_item(e, r, ru):
    e = e.replace('～', '〜') if False else e
    if r and r != e and re.search(r'[㐀-鿿々]', e):
        try:
            return [align(e.replace('～', ''), r.replace('～', '')), ru]
        except Exception:
            return [e, ru]
    return [e, ru]

def pos_of(e):
    toks = list(TAG(e.replace('～', '')))
    if not toks: return 'n'
    t = toks[0]; p = t.feature.pos1
    if len(toks) == 1 or p in ('動詞', '形容詞', '副詞', '接続詞', '感動詞'):
        if p == '動詞': return 'v'
        if p == '形容詞': return 'a'
        if p in ('副詞', '接続詞', '感動詞'): return 'r'
        if p == '形状詞': return 'a'
    # глагол-«する» и составные
    if re.search(r'(う|く|ぐ|す|つ|ぬ|ぶ|む|る)$', e) and toks[-1].feature.pos1 == '動詞': return 'v'
    if toks[-1].feature.pos1 == '形容詞': return 'a'
    return 'n'

POSNAME = {'n': 'слова', 'v': 'глаголы', 'a': 'прилагательные', 'r': 'наречия и связки'}

def chunk(lst, size=10):
    if not lst: return []
    n = max(1, math.ceil(len(lst) / size)); out = []; k = 0
    for i in range(n):
        sz = len(lst) // n + (1 if i < len(lst) % n else 0)
        out.append(lst[k:k + sz]); k += sz
    return out

def lessons_from(words, prefix):
    """words: [(e,r,ru)] → уроки, сгруппированные по части речи"""
    groups = {'n': [], 'v': [], 'a': [], 'r': []}
    for e, r, ru in words: groups[pos_of(e)].append((e, r, ru))
    # мелкие группы (<4 слов) приклеиваем к соседней
    order = ['n', 'v', 'a', 'r']
    for i, p in enumerate(order):
        if 0 < len(groups[p]) < 4:
            tgt = next((q for q in order[:i][::-1] + order[i+1:] if len(groups[q]) >= 4), None)
            if tgt: groups[tgt] += groups[p]; groups[p] = []
    out = []
    for p in order:
        parts = chunk(groups[p])
        for i, part in enumerate(parts):
            ex = '・'.join(e.replace('～', '') for e, _, _ in part[:3])
            t = f"{prefix}{POSNAME[p]}" + (f" {i+1}" if len(parts) > 1 else "") + f": {ex}…"
            out.append({'t': t, 'it': [word_item(e, r, ru) for e, r, ru in part]})
    return out

# ------------------------------------------------------------------ N4
def build_n4(n3_sentence_sink):
    import n4_extra as X
    ch, kanji = parse('/home/claude/altuha/src/n4.txt')
    KEEP = {'失礼します', '気をつける', 'お大事に', 'お待ちください', 'かしこまりました', '頂けますか', '会社員', '駅員', '薬屋',
            'ゆっくり', '確かに', '盗まれる', '曲がる', '落とす', '治す', '怪我', '怪我する', '貯める', '朝ご飯', '点ける', '説明する',
            '紹介する', '約束する', '結婚する', '予約する', '連絡する', '試着する'}
    KEEP -= {'試着する'}  # 試着 нет в списках ≤N4
    kept_words = set()
    for c in ch:
        for l in c['L']:
            new = []
            for it in l['it']:
                jp = P(it[0]); rd = R(it[0])
                if ' ' in jp or '、' in jp:
                    bad = above2(jp, 'n4')
                    if bad:
                        n3 = [s for s, lv in bad if lv == 'n3']
                        if len(n3) == len(bad):
                            n3_sentence_sink.append((it, n3)); REPORT.append(f'N4→N3 фраза: {jp} {bad}')
                        else:
                            REPORT.append(f'N4 фраза удалена: {jp} {bad}')
                        continue
                    new.append(it)
                else:
                    lv = level2(jp, rd)
                    if jp in KEEP or (lv in ('n5', 'n4')):
                        new.append(it); kept_words.add(norm(jp)); kept_words.add(norm(rd))
                    else:
                        REPORT.append(f'N4 слово убрано ({lv}): {jp}'); REMOVED_RD.append(it[0] if '{' in it[0] else jp)
            l['it'] = new
        c['L'] = [l for l in c['L'] if l['it']]
        c['_talk'] = c['talk']
    gone = {R(x).replace(' ','') for x in REMOVED_RD} | {'おうぼ','こうさてん','まちあわせ','はなび','おんせん','つうやく','さんせい','あきらめ','ぜったい','けっきょく','むしあつい','ごうかく','めんきょ','しゅうでん','こうかん','めいわく','れいぞうこ','やちん','しょうしょう','おかけ'}
    for c in ch:
        tk = []
        for t in c.pop('_talk'):
            txt = ''.join([t[0]] + t[2:]).replace(' ', '')
            hit = [g for g in gone if g and len(g) >= 3 and g not in ('おねがい','ようび','ひっこし','のりかえ','おかけ') and g in txt]
            if hit: REPORT.append(f'N4 диалог удалён: {t[0]} / {t[2:]} {hit}')
            else: tk.append(t)
        c['talk'] = tk
    # добавить недостающие слова N4 по темам
    adds = tsv('/home/claude/altuha/src/vocab/n4_add_*.tsv')
    n5course = json.load(open('/tmp/dl/course_items.json'))['n5']
    have = set(kept_words)
    DROP5 = {norm(x) for x in ["空港","すきます","一杯","何杯","遠く","しゅみ","ピアノ","テニス","プレゼント","そんな","あんな","もちろん","ぜんぜん","たいてい","しんぱいします","一度","試験","答え","かべ","住所","パソコン","カード","げんきん","ふくろ","スリッパ","こうかんします","おかいけい","ビール","ゲーム"]}
    for t in n5course:
        if norm(t['p']) in DROP5 or norm(t['k']) in DROP5: continue
        have.add(norm(t['p'])); have.add(norm(t['k']))
    bytag = {}
    for e, r, ru, tag in adds:
        e2 = e.replace('～', ''); r2 = r.replace('～', '')
        if norm(e2) in have or (norm(r2) in have and not re.search(r'[㐀-鿿]', e2)): continue
        bytag.setdefault(int(tag), []).append((e, r, ru))
    if 15 not in bytag: bytag[15] = []
    ch.append({'id': 'n4c15', 't': 'Связки и наречия', 'd': 'Как связывать фразы: если, поэтому, наконец, почти', 'bg': 'day',
               'story': 'Последняя глава N4 — слова, которые склеивают речь. Без них ты говоришь как робот: «Я пошёл. Был дождь. Я вернулся».', 'L': [], 'talk': [
                   ['きのう、いったの？', 'Скажи: нет, не пошёл', 'いいえ、いかなかった', 'いかなかった'],
                   ['しゅくだい、おわった？', 'Скажи: почти', 'ほとんどおわった'],
                   ['あした こられる？', 'Скажи: если получится — приду', 'できればいく'],
                   ['どうして おくれたの？', 'Скажи: проспал, поэтому опоздал', 'ねぼうした。だから、おくれた']]})
    for tag, ws in sorted(bytag.items()):
        c = ch[tag - 1]
        c['L'] += lessons_from(ws, 'Ещё ' if tag != 15 else '')
    for c in ch:
        for t in c['talk']:
            if t[0].startswith('|'): t[0] = ''
    # грамматика N4: проверка уровня
    for g in X.GRAMS:
        for it in g['it']:
            b = above2(P(it[0]), 'n4')
            if b: REPORT.append(f'!! N4 грамматика {g["key"]}: {P(it[0])} {b}')
    return ch, kanji, X

# ------------------------------------------------------------------ N3
def build_n3(moved):
    import n3_extra as X
    from n3_meta import CH
    rows = tsv('/home/claude/altuha/src/vocab/n3_*.tsv')
    cour = json.load(open('/tmp/dl/course_items.json'))
    have = set()
    for lv in ('n5',):
        for t in cour[lv]: have.add(norm(t['p']))
    bytag = {}; seen = set()
    for e, r, ru, tag in rows:
        key = (norm(e), norm(r))
        if key in seen: continue
        seen.add(key)
        bytag.setdefault(int(tag), []).append((e, r, ru))
    chapters = []
    for tag in range(1, 21):
        t, d, bg, story, talk = CH[tag]
        L = lessons_from(bytag.get(tag, []), '')
        chapters.append({'id': f'n3c{tag}', 't': t, 'd': d, 'bg': bg, 'story': story, 'L': L,
                         'talk': [[(q if not q.startswith('|') else ''), h, *a] for q, h, *a in talk]})
    # фразы, перенесённые из N4 (там слова N3) — в урок, где живёт это слово
    idx = {}
    for c in chapters:
        for l in c['L']:
            for it in l['it']:
                for k in forms(P(it[0])) | {norm(R(it[0]))}: idx.setdefault(k, l)
    for it, n3words in moved:
        dest = None
        for s in n3words:
            for k in [norm(s)] + [norm(lm) for _, lm, _ in lemmas(s)]:
                if k in idx: dest = idx[k]; break
            if dest: break
        if dest is None:
            for s, lm, k in lemmas(P(it[0])):
                for kk in (norm(lm), norm(s), k):
                    if kk in idx: dest = idx[kk]; break
                if dest: break
        if dest: dest['it'].append(it)
        else: REPORT.append(f'N3: некуда положить фразу {P(it[0])}')
    for g in X.GRAMS:
        for it in g['it']:
            b = above2(P(it[0]), 'n3')
            if b: REPORT.append(f'!! N3 грамматика {g["key"]}: {P(it[0])} {b}')
    # грамматику ставим перед уроком номер at
    for g in X.GRAMS:
        c = next(c for c in chapters if c['id'] == g['ch'])
        at = min(g['at'], len(c['L']) - 1)
        g['before'] = c['L'][at]['t'] if c['L'] else ''
    return chapters, X

def kanji_n3():
    kd = json.load(open('/tmp/dl/kd/kanji.json', encoding='utf8'))
    ru = dict(l.rstrip('\n').split('|', 1) for l in open('/home/claude/altuha/src/vocab/n3_kanji_ru.txt', encoding='utf8') if '|' in l)
    vocab = tsv('/home/claude/altuha/src/vocab/n3_*.tsv') + tsv('/home/claude/altuha/src/vocab/n4_add_*.tsv')
    out = []
    for k, v in kd.items():
        if v.get('jlpt_new') != 3: continue
        kun = [x.split('.')[0].replace('-', '') for x in (v.get('readings_kun') or []) if x]
        on = [kata2hira(x) for x in (v.get('readings_on') or [])]
        rd = (kun or on or [''])[0]
        ex = sorted([w for w in vocab if k in w[0] and len(w[0]) >= 2 and '～' not in w[0]], key=lambda w: len(w[0]))
        if not ex: ex = sorted([w for w in vocab if k in w[0] and '～' not in w[0]], key=lambda w: len(w[0]))
        e = ex[0] if ex else [k, rd, ru.get(k, ''), '']
        out.append('|'.join([k, ru.get(k, ','.join(v['meanings'][:2])), rd, e[0], e[1], e[2]]))
    return out

def kanji_fix(n4k):
    """N5: только jlpt5 (+分); остальное из N5 уходит в N4"""
    kd = json.load(open('/tmp/dl/kd/kanji.json', encoding='utf8'))
    h = open('/home/claude/altuha/index.html', encoding='utf8').read()
    i = h.index('const N5K_RAW=`') + 15; j = h.index('`', i)
    lines = [l for l in h[i:j].split('\n') if l]
    n5 = [l for l in lines if kd.get(l.split('|')[0], {}).get('jlpt_new') == 5 or l.startswith('分|')]
    moved = [l for l in lines if l not in n5]
    if not any(l.startswith('間|') for l in n5): n5.append('間|промежуток, между|あいだ|時間|じかん|время')
    n4set = {l.split('|')[0] for l in n4k}
    n4 = list(n4k) + [l for l in moved if kd.get(l.split('|')[0], {}).get('jlpt_new') == 4 and l.split('|')[0] not in n4set]
    seen=set(); n4 = [l for l in n4 if kd.get(l.split('|')[0], {}).get('jlpt_new') == 4 and not (l.split('|')[0] in seen or seen.add(l.split('|')[0]))]
    REPORT.append(f'Кандзи: N5 {len(n5)}, N4 {len(n4)} (перенесено из N5: {"".join(l[0] for l in moved)})')
    return n5, n4

if __name__ == '__main__':
    moved = []
    n4ch, n4k, X4 = build_n4(moved)
    n3ch, X3 = build_n3(moved)
    n5k, n4k2 = kanji_fix(n4k)
    n3k = kanji_n3()
    n5add = tsv('/home/claude/altuha/src/vocab/n5_add.tsv')
    TT = {'c': 'Цвета', 'd': 'Туда-сюда (こっち・そっち)', 'a': 'Глаголы', 'p': 'Люди и места', 't': 'Вещи', 'x': 'Разное'}
    plus = {'id': 'cplus', 't': 'Ещё слова N5', 'd': 'То, что есть в списке N5, но не влезло в главы', 'bg': 'home',
            'story': 'Последний добор N5: цвета, «сюда-туда», пара глаголов и старые слова, которые до сих пор встречаются в тестах.', 'L': [], 'talk': [
                ['なにいろが すき？', 'Скажи: синий', 'あおがすき', 'あおです'],
                ['どっちが いい？', 'Скажи: вот этот (сюда)', 'こっちがいい'],
                ['えきまで どのくらい かかる？', 'Скажи: десять минут', 'じゅっぷんかかる', 'じゅっぷんです']]}
    for tg in ['c', 'd', 'a', 'p', 't', 'x']:
        ws = [(e, r, ru) for e, r, ru, t in n5add if t == tg]
        if ws: plus['L'].append({'t': TT[tg], 'it': [word_item(e, r, ru) for e, r, ru in ws]})
    def data(ch, kj, X):
        return {"chapters": ch, "kanji": "\n".join(kj), "grams": X.GRAMS, "para": X.PARA, "gram": X.GRAM, "read": X.READ, "listen": X.LISTEN}
    js = ("const N4_DATA=%s;\nconst N3_DATA=%s;\nconst N5_PLUS=%s;\nconst N5K_FIX=%s;\n" % (
        json.dumps(data(n4ch, n4k2, X4), ensure_ascii=False, separators=(',', ':')),
        json.dumps(data(n3ch, n3k, X3), ensure_ascii=False, separators=(',', ':')),
        json.dumps(plus, ensure_ascii=False, separators=(',', ':')),
        json.dumps("\n".join(n5k), ensure_ascii=False)))
    open('/tmp/lvl_data.js', 'w', encoding='utf8').write(js)
    open('/tmp/lvl_report.txt', 'w', encoding='utf8').write('\n'.join(REPORT))
    cnt = lambda ch: (len(ch), sum(len(c['L']) for c in ch), sum(1 for c in ch for l in c['L'] for it in l['it'] if ' ' not in P(it[0])), sum(1 for c in ch for l in c['L'] for it in l['it'] if ' ' in P(it[0])))
    print('N4 (главы, уроки, слова, фразы):', cnt(n4ch), 'грамматика', len(X4.GRAMS), 'кандзи', len(n4k2))
    print('N3:', cnt(n3ch), 'грамматика', len(X3.GRAMS), 'кандзи', len(n3k))
    print('N5+:', len(plus['L']), 'уроков', sum(len(l['it']) for l in plus['L']), 'слов; кандзи N5', len(n5k))
    print('js', len(js))
