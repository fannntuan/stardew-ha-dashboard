#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 HA 的任意 lovelace 路径截手机版长图（用 NAS 上 fygo-browser 的 Chrome CDP）。
用法: ha_shot.py <url_path> <输出png> [宽] [高]
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


def hj(path, method="GET"):
    return json.load(urllib.request.urlopen(
        urllib.request.Request(CDP + path, method=method), timeout=15))


async def shot(url_path: str, out: str, width=402, height=1400, mobile=True):
    token = (H.login() or {}).get("access_token")
    browser_ws = hj("/json/version")["webSocketDebuggerUrl"]
    async with websockets.connect(browser_ws, max_size=200 * 1024 * 1024) as ws:
        n = 0

        async def cmd(m, **p):
            nonlocal n
            n += 1
            await ws.send(json.dumps({"id": n, "method": m, "params": p}))
            while True:
                x = json.loads(await ws.recv())
                if x.get("id") == n:
                    return x

        # 新建一个独立标签页，别打扰用户正在看的那个
        t = await cmd("Target.createTarget", url=HA + "/lovelace/0")
        target_id = t["result"]["targetId"]
        info = await cmd("Target.getTargetInfo", targetId=target_id)
        page_ws = None
        for _ in range(20):
            for x in hj("/json/list"):
                if x.get("id") == target_id:
                    page_ws = x.get("webSocketDebuggerUrl")
            if page_ws:
                break
            await asyncio.sleep(0.5)
    async with websockets.connect(page_ws, max_size=200 * 1024 * 1024) as pws:
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
                   deviceScaleFactor=2, mobile=mobile, screenWidth=width, screenHeight=height)
        await asyncio.sleep(3)
        await ev("(function(){localStorage.setItem('hassTokens', JSON.stringify({access_token:%s,"
                 " token_type:'Bearer', expires_in:315360000, hassUrl:'%s', clientId:'%s/',"
                 " expires: Date.now()+315360000000})); return 'ok';})()"
                 % (json.dumps(token), HA, HA))
        # 规范化路径：允许 "home-control/main"、"/lovelace/home-control/main" 两种写法
        path = "/" + url_path.strip().lstrip("/")
        if not path.startswith(("/lovelace/", "/home", "/config", "/hassio", "/developer-tools")):
            path = "/lovelace" + path
        target_url = HA + path
        await pcmd("Page.navigate", url=target_url)
        await asyncio.sleep(4)
        await pcmd("Page.reload", ignoreCache=True)
        await asyncio.sleep(14)
        shot_data = await pcmd("Page.captureScreenshot", format="png", captureBeyondViewport=True)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "wb").write(base64.b64decode(shot_data["result"]["data"]))
        # 顺手检查有没有坏卡片
        problems = await ev("(()=>{const t=document.body.innerText||'';"
                            "if(/无法访问此网站|ERR_|site can.t be reached|拒绝连接/.test(t))"
                            "  return '页面打不开! '+location.href;"
                            "const bad=['Unknown','not found'];"
                            "return bad.filter(b=>t.includes(b)).join(',')||'ok'})()")
        await pcmd("Target.closeTarget", targetId=target_id) if False else None
        print(f"{out} ({os.path.getsize(out)//1024} KB) 页面检查={problems}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/home-control/main"
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/shot.png"
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 402
    h = int(sys.argv[4]) if len(sys.argv) > 4 else 1400
    mob = not (len(sys.argv) > 5 and sys.argv[5] == "desktop")
    asyncio.run(shot(path, out, w, h, mob))
