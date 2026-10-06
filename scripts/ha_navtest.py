#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 HA 里"自绘导航链接"能不能真的跳转：打开页面 → 点某个链接 → 看 location.href。
用法: ha_navtest.py <url_path> <链接文字> [宽] [高] [输出png]
"""
import asyncio, base64, json, os, sys, urllib.request
import websockets
sys.path.insert(0, "/vol2/@appdata/trim.hermes/workspace")
import ha_api as H

HA = "http://${HA_HOST}"
CDP = "http://127.0.0.1:16002"

FIND = """(()=>{const w=%s;const out=[];
const walk=(root)=>{for(const el of root.querySelectorAll('*')){
  if(el.tagName==='A'&&(el.innerText||'').trim()===w){const r=el.getBoundingClientRect();
    out.push({x:r.x+r.width/2,y:r.y+r.height/2,html:el.outerHTML.slice(0,120)});}
  if(el.shadowRoot) walk(el.shadowRoot);}};
walk(document);return JSON.stringify(out);})()"""


def hj(p):
    return json.load(urllib.request.urlopen(CDP + p, timeout=15))


async def main(url_path, want, width, height, out):
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
        await asyncio.sleep(13)
        print("起始 URL:", await ev("location.href"))
        print("侧边栏存在:", await ev("!!document.querySelector('ha-sidebar') && getComputedStyle(document.querySelector('ha-sidebar')).display!=='none'"))
        boxes = json.loads(await ev(FIND % json.dumps(want)) or "[]")
        print("找到链接 %r 个数:" % want, len(boxes))
        if not boxes:
            await pcmd("Page.captureScreenshot", format="png", captureBeyondViewport=True)
            await pcmd("Target.closeTarget", targetId=tid)
            return 1
        x, y = boxes[0]["x"], boxes[0]["y"]
        for t_ in ("mousePressed", "mouseReleased"):
            await pcmd("Input.dispatchMouseEvent", type=t_, x=x, y=y, button="left", clickCount=1)
        await asyncio.sleep(6)
        print("点击后 URL:", await ev("location.href"))
        shot = await pcmd("Page.captureScreenshot", format="png", captureBeyondViewport=True)
        open(out, "wb").write(base64.b64decode(shot["result"]["data"]))
        print("截图:", out, os.path.getsize(out) // 1024, "KB")
        await pcmd("Target.closeTarget", targetId=tid)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1], sys.argv[2],
                             int(sys.argv[3]) if len(sys.argv) > 3 else 1536,
                             int(sys.argv[4]) if len(sys.argv) > 4 else 900,
                             sys.argv[5] if len(sys.argv) > 5 else "/tmp/nav.png")))
