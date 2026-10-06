#!/usr/bin/env python3
"""HA /config 文件读写（走 Samba，凭据取自 ha_api.py）

用法:
  ha_file.py get  <远端相对路径> [本地输出路径]   # 不给输出路径则打印到 stdout
  ha_file.py put  <本地路径> <远端相对路径>
  ha_file.py ls   [远端目录]
  ha_file.py rm   <远端相对路径>
"""
import os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ha_api as H

HOST = os.environ.get("HA_SMB_HOST", "${HA_HOST}")
SHARE = "config"


def _run(args, timeout=120):
    p = subprocess.run(["smbclient", f"//{HOST}/{SHARE}", "-U", f"{H.USER}%{H.PWD}", "-c", args],
                       capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


def get(remote, out=None):
    if out:
        rc, o = _run(f'get "{remote}" "{out}"')
        print(o.strip()[-300:])
        return rc
    with tempfile.NamedTemporaryFile(delete=False) as f:
        tmp = f.name
    try:
        rc, o = _run(f'get "{remote}" "{tmp}"')
        print(open(tmp, encoding="utf-8", errors="replace").read())
        return rc
    finally:
        os.unlink(tmp)


def put(local, remote):
    rc, o = _run(f'put "{local}" "{remote}"')
    print(o.strip()[-300:])
    return rc


def ls(remote=""):
    rc, o = _run(f'ls "{remote}"' if remote else "ls")
    print(o)
    return rc


def rm(remote):
    rc, o = _run(f'del "{remote}"')
    print(o.strip()[-300:])
    return rc


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "get":
        sys.exit(get(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
    elif cmd == "put":
        sys.exit(put(sys.argv[2], sys.argv[3]))
    elif cmd == "ls":
        sys.exit(ls(sys.argv[2] if len(sys.argv) > 2 else ""))
    elif cmd == "rm":
        sys.exit(rm(sys.argv[2]))
    else:
        print(__doc__)
