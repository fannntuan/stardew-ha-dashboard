#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dump HA 页面里真实用到的自定义元素（tag/类名），用来写精准的 CSS 选择器。
用法: ha_dom.py <url_path> [宽] [高]
"""
import asyncio, json, sys, urllib.request
import websockets
sys.path.insert(0, "/vol2/@appdata/trim.hermes/workspace")
import ha_api as H

HA = "http://${HA_HOST}"
CDP = "http://127.0.0.1:16002"

JS_TAGS = """(()=>{const c={};const walk=(r)=>{for(const e of r.querySelectorAll('*')){
  if(/^(ha|hui|mwc|mdc)-/.test(e.tagName.toLowerCase())) c[e.tagName.toLowerCase()]=(c[e.tagName.toLowerCase()]||0)+1;
  if(e.shadowRoot) walk(e.shadowRoot);}};walk(document);
  return JSON.stringify(Object.entries(c).sort((a,b)=>b[1]-a[1]));})()"""

JS_NAV = """(()=>{const out=[];const walk=(r)=>{for(const e of r.querySelectorAll('*')){
  if(e.tagName==='A' && (e.getAttribute('href')||'').includes('/home-control/')){
    let p=e, chain=[]; while(p && chain.length<6){chain.push(p.tagName.toLowerCase()+(p.className&&typeof p.className==='string'?'.'+p.className.split(' ').filter(Boolean).slice(0,2).join('.'):'')); p=p.parentElement;}
    out.push({href:e.getAttribute('href'), chain:chain});}
  if(e.shadowRoot) walk(e.shadowRoot);}};walk(document);
  return JSON.stringify(out.slice(0,2));})()"""

JS_HEAD = """(()=>{const out=[];const walk=(r)=>{for(const e of r.querySelectorAll('*')){
  if(/heading|title/i.test(e.tagName) || (e.tagName==='HA-CARD' && e.className)){}
  if(e.tagName.toLowerCase().includes('heading')) {out.push(e.outerHTML.slice(0,400));}
  if(e.shadowRoot) walk(e.shadowRoot);}};walk(document);return JSON.stringify(out.slice(0,3));})()"""

JS_TILE = """(()=>{const out=[];const walk=(r)=>{for(const e of r.querySelectorAll('*')){
  if(/tile/.test(e.tagName.toLowerCase()) && e.tagName.includes('-')){out.push(e.tagName.toLowerCase()+' | class='+(typeof e.className==='string'?e.className:''));}
  if(e.shadowRoot) walk(e.shadowRoot);}};walk(document);return JSON.stringify([...new Set(out)].slice(0,12));})()"""


def hj(p):
    return json.load(urllib.request.urlopen(CDP + p, timeout=15))


async def main(url_path, width=1536, height=900):
    token = (H.login() or {}).get("access_token")
    path = "/" + url_path.strip().lstrip("/")
    if not path.startswith(("/lovelace/", "/home", "/config")):
        path = "/lovelace" + path
    bws = hj("/json/version")["webSocketDebuggerUrl"]
    async with websockets.connect(bws, max_size=100 * 1024 * 1024) as ws:
        n = 0

        async def cmd(m, **p):
            nonlocal n
            n += 1
            await ws.send(json.dumps({"id": n, "method": m, "params": p}))
            while True:
                x = json.loads(await ws.recv())
                if x.get("id") == n:
                    return x
        t = await cmd("Target.createTarget", url=HA + path)
        tid = t["result"]["targetId"]
        pu = None
        for _ in range(20):
            for x in hj("/json/list"):
                if x.get("id") == tid:
                    pu = x["webSocketDebuggerUrl"]
            if pu:
                break
            await asyncio.sleep(0.5)
    async with websockets.connect(pu, max_size=200 * 1024 * 1024) as pws:
        n = 0

        async def pcmd(m, **p):
            nonlocal n
            n += 1
            await pws.send(json.dumps({"id": n, "method": m, "params": p}))
            while True:
                x = json.loads(await pws.recv())
                if x.get("id") == n:
                    return x

        async def ev(e):
            x = await pcmd("Runtime.evaluate", expression=e, returnByValue=True, awaitPromise=True)
            return x.get("result", {}).get("result", {}).get("value")

        await pcmd("Page.enable")
        await pcmd("Runtime.enable")
        await pcmd("Emulation.setDeviceMetricsOverride", width=width, height=height,
                   deviceScaleFactor=2, mobile=False, screenWidth=width, screenHeight=height)
        await asyncio.sleep(2)
        await ev("(function(){localStorage.setItem('hassTokens', JSON.stringify({access_token:%s,"
                 " token_type:'Bearer', expires_in:315360000, hassUrl:'%s', clientId:'%s/',"
                 " expires: Date.now()+315360000000})); return 'ok';})()" % (json.dumps(token), HA, HA))
        await pcmd("Page.navigate", url=HA + path)
        await asyncio.sleep(5)
        await pcmd("Page.reload", ignoreCache=True)
        await asyncio.sleep(14)
        print("== 自定义元素统计 ==")
        for tag, cnt in json.loads(await ev(JS_TAGS) or "[]")[:40]:
            print("   %-28s %d" % (tag, cnt))
        print("\n== 导航链接的 DOM 链 ==")
        print(await ev(JS_NAV))
        print("\n== heading 元素 ==")
        print(await ev(JS_HEAD))
        print("\n== tile 相关元素 ==")
        print(await ev(JS_TILE))
        await pcmd("Target.closeTarget", targetId=tid)


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1],
                             int(sys.argv[2]) if len(sys.argv) > 2 else 1536,
                             int(sys.argv[3]) if len(sys.argv) > 3 else 900)))
