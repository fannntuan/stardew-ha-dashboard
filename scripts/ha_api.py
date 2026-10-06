#!/usr/bin/env python3
"""Home Assistant (${HA_HOST}:8123) 无头 API 客户端。

- 用账号密码走 auth flow 拿 token，并在本地缓存（~/.config/ha/creds.json）
- 支持 REST 与 WebSocket API（ha_ws 命令）
用法:
  python3 ha_api.py rest GET /api/config
  python3 ha_api.py rest POST /api/services/light/turn_on '{"entity_id":"light.x"}'
  python3 ha_api.py ws '{"id":1,"type":"get_states"}'    # 单条命令
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("HA_BASE", "http://${HA_HOST}")  # HA 实际在 80 端口
USER = os.environ.get("HA_USER", "${HA_USER}")  # 别硬编码真名
PWD = os.environ.get("HA_PWD", "")   # 必须通过环境变量/creds.json 提供，别硬编码
CACHE = os.path.expanduser("~/.config/ha/creds.json")
CLIENT_ID = BASE + "/"


def _post(url, payload, form=False):
    if form:
        data = urllib.parse.urlencode(payload).encode()
        ctype = "application/x-www-form-urlencoded"
    else:
        data = json.dumps(payload).encode()
        ctype = "application/json"
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit("HTTP %s: %s" % (e.code, e.read().decode()[:500]))


def login():
    flow = _post(BASE + "/auth/login_flow",
                 {"client_id": CLIENT_ID, "handler": ["homeassistant", None],
                  "redirect_uri": BASE + "/?auth_callback=1"})
    fid = flow["flow_id"]
    res = _post("%s/auth/login_flow/%s" % (BASE, fid),
                {"username": USER, "password": PWD, "client_id": CLIENT_ID})
    if res.get("type") != "create_entry":
        raise SystemExit("登录失败: %s" % res)
    # 注意：/auth/token 只接受 x-www-form-urlencoded（JSON 会报 unsupported_grant_type）
    tok = _post(BASE + "/auth/token",
                {"grant_type": "authorization_code", "code": res["result"],
                 "client_id": CLIENT_ID}, form=True)
    tok["obtained_at"] = int(time.time())
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w") as f:
        json.dump(tok, f)
    os.chmod(CACHE, 0o600)
    return tok


def refresh(tok):
    if not tok.get("refresh_token"):
        return login()   # 缓存里只有 access_token（过期即重登）
    try:
        new = _post(BASE + "/auth/token",
                    {"grant_type": "refresh_token", "refresh_token": tok["refresh_token"],
                     "client_id": CLIENT_ID}, form=True)
        new["obtained_at"] = int(time.time())
        with open(CACHE, "w") as f:
            json.dump(new, f)
        os.chmod(CACHE, 0o600)
        return new
    except SystemExit:
        return login()


def token(force=False):
    if not force and os.path.exists(CACHE):
        tok = json.load(open(CACHE))
        if time.time() - tok.get("obtained_at", 0) < tok.get("expires_in", 1800) - 120:
            return tok["access_token"]
        return refresh(tok)["access_token"]
    return login()["access_token"]


def rest(method, path, body=None, raw=False):
    at = token()
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + at)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            txt = r.read().decode()
    except urllib.error.HTTPError as e:
        if e.code == 401:
            at = token(force=True)
            req.add_header("Authorization", "Bearer " + at)
            with urllib.request.urlopen(req, timeout=120) as r:
                txt = r.read().decode()
        else:
            raise SystemExit("HTTP %s: %s" % (e.code, e.read().decode()[:800]))
    if raw:
        return txt
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return txt


def ws(cmds, timeout=30):
    """按顺序发多条命令，返回收到的所有消息。"""
    from websocket import create_connection
    at = token()
    c = create_connection((BASE.replace("http://", "ws://").replace("https://", "wss://")) + "/api/websocket",
                          timeout=timeout)
    out = []
    def pump():
        while True:
            m = c.recv()
            if isinstance(m, bytes):
                continue  # 二进制帧（ping/pong 等），忽略
            try:
                obj = json.loads(m)
            except json.JSONDecodeError:
                continue
            out.append(obj)
            return obj
    pump()  # auth_required
    c.send(json.dumps({"type": "auth", "access_token": at}))
    pump()  # auth_ok
    for cmd in cmds:
        c.send(json.dumps(cmd))
        while True:
            m = pump()
            if m.get("id") == cmd.get("id") and m.get("type") == "result":
                break
    c.close()
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "token":
        print(token(force="--force" in sys.argv))
    elif cmd == "rest":
        body = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
        print(json.dumps(rest(sys.argv[2].upper(), sys.argv[3], body), ensure_ascii=False, indent=1))
    elif cmd == "ws":
        cmds = [json.loads(a) for a in sys.argv[2:]]
        for m in ws(cmds):
            print(json.dumps(m, ensure_ascii=False))
    else:
        print(__doc__)
