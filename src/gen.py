import json, sys, importlib
from build_lvl import parse
def gen(lvl):
    ch, kanji = parse(f'{lvl}.txt')
    ex = importlib.import_module(f'{lvl}_extra')
    seen=set(); kj=[]
    for l in kanji:
        k=l.split('|')[0]
        if k in seen: continue
        seen.add(k); kj.append(l)
    d = {"chapters": ch, "kanji": "\n".join(kj), "grams": ex.GRAMS, "para": ex.PARA, "gram": ex.GRAM, "read": ex.READ, "listen": ex.LISTEN}
    return "const %s_DATA=%s;\n" % (lvl.upper(), json.dumps(d, ensure_ascii=False, separators=(',', ':')))
if __name__ == '__main__':
    lvl = sys.argv[1]
    js = gen(lvl)
    open(f'/tmp/{lvl}_data.js', 'w', encoding='utf8').write(js)
    print(len(js))
