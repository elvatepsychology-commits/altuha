import asyncio, sys, json
sys.path.insert(0,"/home/claude/tests")
from t1 import MOCK, URL
from playwright.async_api import async_playwright
async def main():
    out={}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        for lv in ["n5","n4","n3"]:
            pg = await b.new_page(); await pg.add_init_script(MOCK); await pg.goto(URL+"?lvl="+lv); await pg.wait_for_timeout(800)
            out[lv]=await pg.evaluate("""()=>({items:N5_ALL().filter(i=>i.kind!=='k').map(i=>({id:i.id,jp:i.jp,kana:kanaOf(i.jp),ru:i.ru,kind:i.kind,ci:i.ci})),
              talk:N5C.flatMap(c=>(c.T||[]).map(t=>({id:t.id,q:t.q,ans:t.ans}))),
              gram:(typeof N5_GRAMS!=='undefined'?Object.values(N5_GRAMS):[]).map(g=>({key:g.key,ch:g.ch,ex:(g.slides||[]).map(s=>s.jp||s.ex||'').filter(Boolean)})),
              lessons:N5C.map(c=>c.L.map(l=>l.it.length))})""")
            await pg.close()
        await b.close()
    json.dump(out,open("/tmp/course2.json","w"),ensure_ascii=False)
    for lv in out: print(lv,len(out[lv]["items"]),sum(1 for i in out[lv]["items"] if i["kind"]=="s"),len(out[lv]["talk"]),len(out[lv]["gram"]), max(max(x) if x else 0 for x in out[lv]["lessons"]))
asyncio.run(main())
