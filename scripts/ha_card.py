#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只截 HA 页面上"含某段文字的那张卡片"（局部放大图，用来核对卡片内容）。

用法: ha_card.py <url_path> <卡片里含的文字> <输出png> [宽] [额外上下留白]
例:   ha_card.py home-control/main "今日油价" /tmp/oil.png 390 20
"""
import asyncio
import base64
import json
import os
import sys
import urllib.request

import websockets

sys.path.insert(0, "/vol2/@appdata/trim.hermes/workspace")
import ha_api as H  # noqa: E402

HA = "http://${HA_HOST}"
CDP = "http://127.0.0.1:16002"


def hj(path):
    return json.load(urllib.request.urlopen(CDP + path, timeout=15))


async def main(url_path, want, out, width=390, pad=24):
    token = (H.login() or {}).get("access_token")
    path = "/" + url_path.strip().lstrip("/")
    if not path.startswith(("/lovelace/", "/home", "/config", "/hassio")):
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
        pws_url = None
        for _ in range(20):
            for x in hj("/json/list"):
                if x.get("id") == tid:
                    pws_url = x["webSocketDebuggerUrl"]
            if pws_url:
                break
            await asyncio.sleep(0.5)
    async with websockets.connect(pws_url, max_size=200 * 1024 * 1024) as pws:
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
        await pcmd("Emulation.setDeviceMetricsOverride", width=width, height=1200,
                   deviceScaleFactor=2, mobile=True, screenWidth=width, screenHeight=1200)
        await asyncio.sleep(2)
        await ev("(function(){localStorage.setItem('hassTokens', JSON.stringify({access_token:%s,"
                 " token_type:'Bearer', expires_in:315360000, hassUrl:'%s', clientId:'%s/',"
                 " expires: Date.now()+315360000000})); return 'ok';})()"
                 % (json.dumps(token), HA, HA))
        await pcmd("Page.navigate", url=HA + path)
        await asyncio.sleep(4)
        await pcmd("Page.reload", ignoreCache=True)
        await asyncio.sleep(14)
        # HA 卡片是懒渲染的：先把页面从头滚到底，卡片才会进 DOM
        await ev("(async()=>{const H=document.body.scrollHeight;"
                 "for(let y=0;y<H;y+=600){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,150));}"
                 "window.scrollTo(0,0);return 'ok';})()")
        await asyncio.sleep(1)
        box = await ev("""(()=>{const w=%s;const cards=[...document.querySelectorAll('ha-card,hui-card')];
          const hit=cards.find(c=>{const t=c.innerText||'';return t.includes(w)&&!(c.closest('ha-card')&&c.closest('ha-card')!==c)});
          if(!hit) return null;const r=hit.getBoundingClientRect();
          return {x:r.x,y:r.y+window.scrollY,w:r.width,h:r.height};})()""" % json.dumps(want))
        await pcmd("Target.closeTarget", targetId=tid)
        if not box:
            print("没找到含 '%s' 的卡片" % want)
            return 1
        print("卡片位置:", box)
    # 用新标签页整体截图 + 裁剪，避免 clip 与长图坐标打架
    tmp = "/tmp/_full.png"
    os.system("cd /vol2/@appdata/trim.hermes/workspace && /vol2/@appcenter/trim.hermes/runtime/python/bin/python3 "
              "ha_shot.py %s %s %d 900 >/dev/null 2>&1" % (path, tmp, width))
    from PIL import Image
    im = Image.open(tmp)
    s = im.size[0] / float(width)          # 截图是 2x
    y0 = max(0, int((box["y"] - pad) * s))
    y1 = min(im.size[1], int((box["y"] + box["h"] + pad) * s))
    im.crop((0, y0, im.size[0], y1)).save(out)
    print("%s (%d KB) 卡片高度 %.0f px" % (out, os.path.getsize(out) // 1024, box["h"]))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3],
                             int(sys.argv[4]) if len(sys.argv) > 4 else 390,
                             int(sys.argv[5]) if len(sys.argv) > 5 else 24)))
