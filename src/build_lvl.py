#!/usr/bin/env python3
"""Собирает данные уровня (N4/N3) из текстового исходника в JS.
Формат исходника:
  #CH id|название|описание|bg|история
  @Название урока
  слово|чтение|перевод           (чтение пустое — слово каной)
  s:фраза с пробелами|чтение без пробелов|перевод
  >вопрос|подсказка|ответ1|ответ2   (разговор, каной)
  #KANJI  затем строки k|ru|rd|ex|exr|exru
"""
import re, json, sys

KANJI = re.compile(r'[㐀-鿿々〆ヶ]')

def kata2hira(s):
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in s)

_TAGGER = None
def _tagger():
    global _TAGGER
    if _TAGGER is None:
        import fugashi
        _TAGGER = fugashi.Tagger()
    return _TAGGER

def _segs(text):
    segs = []
    for ch in text:
        k = 'K' if KANJI.match(ch) else ('S' if ch in ' 、。？！…「」・' else 'L')
        if segs and segs[-1][0] == k:
            segs[-1] = (k, segs[-1][1] + ch)
        else:
            segs.append((k, ch))
    return segs

def _simple(text, rd):
    segs = _segs(text); pat = ''
    for k, s in segs:
        if k == 'K': pat += '(.+?)'
        elif k == 'L': pat += re.escape(kata2hira(s))
    m = re.fullmatch(pat, rd)
    return [m.group(i + 1) for i in range(len([x for x in segs if x[0] == 'K']))] if m else None

def _hints(text):
    """чтение каждого кандзи-куска по морфоанализатору"""
    plain = text.replace(' ', '')
    per = [None] * len(plain)  # для каждого символа-кандзи: (id_куска, чтение куска)
    pos = 0
    try:
        toks = list(_tagger()(plain))
    except Exception:
        return None
    for t in toks:
        surf = t.surface; kana = kata2hira(t.feature.kana or '') if t.feature.kana else ''
        if KANJI.search(surf) and kana:
            r = _simple(surf, kana)
            if r:
                gi = 0; j = 0
                for k, s in _segs(surf):
                    if k == 'K':
                        for c in range(len(s)): per[pos + j + c] = (pos + j, r[gi])
                        gi += 1
                    j += len(s)
        pos += len(surf)
    # собрать по кускам исходного текста
    out = []; i = 0
    for k, s in _segs(text):
        if k == 'S' and s.strip() == '':
            continue
        if k == 'K':
            rs = []; seen = set(); ok = True
            for c in range(len(s)):
                p = per[i + c]
                if not p: ok = False; break
                if p[0] not in seen: seen.add(p[0]); rs.append(p[1])
            # кусок должен целиком состоять из целых подкусков токенов
            out.append(''.join(rs) if ok else None)
        i += len(s.replace(' ', '')) if k != 'S' else len(s.replace(' ', ''))
    return out

def align(text, reading):
    """'日本に 引っ越しました','にほんにひっこしました' -> '{日本|にほん}に {引|ひ}っ{越|こ}しました'"""
    if not reading:
        return text
    segs = _segs(text)
    rd = kata2hira(re.sub(r'[ 、。？！…「」・]', '', reading))
    nK = len([x for x in segs if x[0] == 'K'])
    hints = _hints(text) or [None] * nK
    if len(hints) != nK: hints = [None] * nK
    import itertools
    best = None
    idx = [i for i, h in enumerate(hints) if h]
    for r in range(0, len(idx) + 1):
        for rel in itertools.combinations(idx, r):
            pat = ''; gi = 0
            for k, s in segs:
                if k == 'K':
                    h = hints[gi]
                    pat += '(.+?)' if (h is None or gi in rel) else '(' + re.escape(h) + ')'
                    gi += 1
                elif k == 'L':
                    pat += re.escape(kata2hira(s))
            m = re.fullmatch(pat, rd)
            if m: best = m; break
        if best: break
    if not best:
        raise ValueError(f'не выровнялось: {text} / {reading}')
    out, gi = '', 1
    for k, s in segs:
        if k == 'K':
            r = best.group(gi); gi += 1
            if len(r) > 4 * len(s) + 1:
                raise ValueError(f'подозрительное чтение {s}={r} в {text}')
            out += '{%s|%s}' % (s, r)
        else:
            out += s
    return out

def F(text, reading=''):
    return align(text, reading) if reading else text

def parse(path):
    chapters, kanji, mode = [], [], None
    ch = les = None
    for ln, raw in enumerate(open(path, encoding='utf8'), 1):
        line = raw.rstrip('\n').strip()
        if not line or line.startswith('//'):
            continue
        try:
            if line.startswith('#KANJI'):
                mode = 'k'; continue
            if mode == 'k':
                p = line.split('|')
                assert len(p) == 6, line
                kanji.append(line); continue
            if line.startswith('#CH '):
                i, t, d, bg, story = line[4:].split('|')
                ch = {'id': i, 't': t, 'd': d, 'bg': bg, 'story': story, 'L': [], 'talk': []}
                chapters.append(ch); continue
            if line.startswith('@'):
                les = {'t': line[1:].strip(), 'it': []}
                ch['L'].append(les); continue
            if line.startswith('>'):
                ch['talk'].append(line[1:].split('|')); continue
            if line.startswith('s:'):
                k, r, ru = line[2:].split('|')
                les['it'].append([align(k, r), ru]); continue
            p = line.split('|')
            if len(p) == 3:
                w, r, ru = p
                les['it'].append([align(w, r) if r else w, ru]); continue
            raise ValueError('непонятная строка')
        except Exception as e:
            sys.exit(f'{path}:{ln}: {e}\n  {line}')
    return chapters, kanji

if __name__ == '__main__':
    print(align('日本に 引っ越しました', 'にほんにひっこしました'))
    print(align('待ち合わせ', 'まちあわせ'))
    print(align('お金を 下ろします', 'おかねをおろします'))
