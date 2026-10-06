#!/usr/bin/env python3
"""fnOS 虚拟机（trim.vm）快照辅助 —— HAOS 是 EFI 机，**不支持在线快照**，必须先关机。

用法:
  vm_snap.py status              # 看状态 + 现有快照
  vm_snap.py shutdown            # 优雅关机并等到 SHUTOFF
  vm_snap.py create <名字>        # 建快照并等它出现
  vm_snap.py start               # 开机并等 HA 起来
  vm_snap.py full <名字>          # 关机→快照→开机→等 HA（一条龙）
"""
import base64, json, os, sys, time, urllib.request, urllib.error

VM = os.environ.get("VM_NAME", "${VM_NAME}")          # libvirt 域名（随机串），/domain/list 里的 name
HA = os.environ.get("HA_BASE", "http://${HA_HOST}")
BASE = "http://localhost:5666/vm/api/v1"
S = os.path.expanduser("~/.config/trim-cli/secure")


def token():
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = open(S + "/master.key", "rb").read()
    j = json.load(open(S + "/active.enc"))
    pt = AESGCM(key).decrypt(base64.b64decode(j["nonce"]), base64.b64decode(j["ciphertext"]), None)
    return json.loads(pt)["token"]


def call(method, path, body=None, qs=""):
    req = urllib.request.Request(BASE + path + qs,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 method=method,
                                 headers={"Authorization": token(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return {"code": e.code, "msg": e.read().decode("utf-8", "replace")}


def state():
    d = call("GET", "/domain/list")
    for v in (d.get("data") or []):
        if v.get("name") == VM:
            return v.get("state"), v.get("title")
    return None, None


def snapshots():
    d = call("GET", "/snapshot/list", None, "?name=" + VM)
    return d.get("data") or []


def wait_state(want, limit=240):
    t0 = time.time()
    while time.time() - t0 < limit:
        st, _ = state()
        if st == want:
            return True
        time.sleep(5)
    return False


def wait_ha(limit=420):
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            with urllib.request.urlopen(HA + "/", timeout=8) as r:
                if r.status in (200, 302):
                    return time.time() - t0
        except Exception:
            pass
        time.sleep(6)
    return None


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        st, title = state()
        print("状态:", st, "| 标题:", title)
        print("快照:", json.dumps(snapshots(), ensure_ascii=False))
    elif cmd == "shutdown":
        print("关机请求:", call("POST", "/domain/shutdown", {"name": VM}))
        ok = wait_state("SHUTOFF", 240)
        print("已关机" if ok else "!! 240s 没关掉（可考虑 forceshutdown）", "| 现在:", state()[0])
    elif cmd == "create":
        nm = sys.argv[2]
        print("建快照:", call("POST", "/snapshot/create",
                              {"name": VM, "snapshotName": nm, "snapshotDesc": ""}))
        t0 = time.time()
        while time.time() - t0 < 900:
            s = snapshots()
            if any(nm == (x.get("name") or x.get("snapshotName")) for x in s):
                print("✅ 快照已生成 (%.0fs):" % (time.time() - t0), json.dumps(s, ensure_ascii=False))
                return
            time.sleep(10)
        print("!! 15 分钟没看到快照:", json.dumps(snapshots(), ensure_ascii=False))
    elif cmd == "start":
        print("开机请求:", call("POST", "/domain/start", {"name": VM}))
        sec = wait_ha()
        print("HA 已恢复 (%.0fs)" % sec if sec is not None else "!! HA 420s 没起来")
    elif cmd == "full":
        nm = sys.argv[2]
        print("① 关机");  print("  ", call("POST", "/domain/shutdown", {"name": VM}))
        print("  等关机:", wait_state("SHUTOFF", 240), state()[0])
        print("② 建快照", nm); print("  ", call("POST", "/snapshot/create",
                                              {"name": VM, "snapshotName": nm, "snapshotDesc": ""}))
        t0 = time.time()
        while time.time() - t0 < 900:
            if any(nm == (x.get("name") or x.get("snapshotName")) for x in snapshots()):
                print("  ✅ 快照完成 %.0fs" % (time.time() - t0)); break
            time.sleep(10)
        print("  ", json.dumps(snapshots(), ensure_ascii=False))
        print("③ 开机"); print("  ", call("POST", "/domain/start", {"name": VM}))
        sec = wait_ha()
        print("  HA 已恢复 (%.0fs)" % sec if sec is not None else "  !! HA 没起来")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
