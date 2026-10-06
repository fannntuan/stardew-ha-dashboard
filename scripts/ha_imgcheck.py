#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在指定宽度下打开 HA 页面，dump 出 /local/stardew/img/ 所有图片的"声明样式 vs 实际渲染尺寸"。
用法: ha_imgcheck.py <url_path> [宽] [高]
"""
import asyncio, base64, json, os, sys, urllib.request
import websockets
sys.path.insert(0, "/vol2/@appdata/trim.hermes/workspace")
import ha_api as H

HA = "http://${HA_HOST}"
CDP = "http://127.0.0.1:16002"
JS = """(()=>{const out=[];
const seen=new Set();
const collect=(root)=>{ for(const el of root.querySelectorAll('*')){
    if(el.tagName==='IMG' && el.currentSrc && el.currentSrc.includes('/local/stardew/img/') && !seen.has(el)){seen.add(el);
      const r=el.getBoundingClientRect(); const c=getComputedStyle(el);
      out.push({src:(el.getAttribute('src')||'').split('/').pop(),
                attr_style:el.getAttribute('style'),
                w:Math.round(r.width), h:Math.round(r.height),
                css_h:c.height, css_w:c.width,
                natural:el.naturalWidth+'x'+el.naturalHeight});
    }
    if(el.shadowRoot) collect(el.shadowRoot);
  }};
collect(document); return JSON.stringify(out);})()"""


def hj(p):
    return json.load(urllib.request.urlopen(CDP + p, timeout=15))


async def main(url_path, width=768, height=1024):
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
                   deviceScaleFactor=2, mobile=True, screenWidth=width, screenHeight=height)
        await asyncio.sleep(2)
        await ev("(function(){localStorage.setItem('hassTokens', JSON.stringify({access_token:%s,"
                 " token_type:'Bearer', expires_in:315360000, hassUrl:'%s', clientId:'%s/',"
                 " expires: Date.now()+315360000000})); return 'ok';})()" % (json.dumps(token), HA, HA))
        await pcmd("Page.navigate", url=HA + path)
        await asyncio.sleep(4)
        await pcmd("Page.reload", ignoreCache=True)
        await asyncio.sleep(12)
        await ev("(async()=>{const H=document.body.scrollHeight;"
                 "for(let y=0;y<H;y+=500){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,120));}"
                 "window.scrollTo(0,0);})()")
        await asyncio.sleep(2)
        data = json.loads(await ev(JS) or "[]")
        for d in data:
            print("%-22s 渲染=%sx%s  css=%s/%s  原始=%s  style=%s" %
                  (d["src"], d["w"], d["h"], d["css_w"], d["css_h"], d["natural"], (d["attr_style"] or "")[:60]))
        await pcmd("Target.closeTarget", targetId=tid)


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1],
                             int(sys.argv[2]) if len(sys.argv) > 2 else 768,
                             int(sys.argv[3]) if len(sys.argv) > 3 else 1024)))
