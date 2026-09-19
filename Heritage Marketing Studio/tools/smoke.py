#!/usr/bin/env python
"""smoke.py -- run the code that will actually DEPLOY, not the working tree, and see if it answers.

The failure this exists for: for a week the working tree was newer than what was committed. Everything
passed locally; Render ran the older committed modules under a newer `main.py`; a real user got HTTP 500s
that no local test could show, because locally the modules were the new ones.

So this exports the COMMITTED tree (`git archive <ref>`, default HEAD) into a scratch folder, starts it on
a spare port against an empty scratch data directory (the live shape: nothing but the seeded Heritage
brand -- no dummy brands, no stray settings), and checks:

  1. /selfcheck        -- every backend call matches the function it calls (selfcheck.py)
  2. /health, /app     -- it boots and serves the shell
  3. a set of read routes plus the routes that broke before, each with a signed-in test session; none may
     answer 5xx. No route here calls an AI provider, so it costs nothing and needs no API key.

It writes nothing outside the scratch folder, which is deleted afterwards. Exit 0 = safe to push.

    python tools/smoke.py                 # the committed tree (what a push would deploy)
    python tools/smoke.py --ref origin/master

It cannot prove a use case works with real data or a real model -- that is still run by hand, on live,
after the deploy. What it removes is the class of failure that never needed a person to find.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
APP_REL = "Heritage Marketing Studio/api"

# Left out of the export exactly as .dockerignore leaves them out of the image: local state, not code.
EXCLUDES = ("tenants", "media", "renders", "edits", "library", "learning", ".venv", "__pycache__")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _export(ref: str, dest: str) -> str:
    """git archive <ref> for the api folder, minus local state. Returns the exported api directory."""
    specs = [APP_REL] + [f":(exclude){APP_REL}/{x}" for x in EXCLUDES]
    proc = subprocess.run(["git", "archive", "--format=tar", ref, "--", *specs],
                          cwd=REPO_ROOT, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit("git archive failed: " + proc.stderr.decode("utf-8", "replace")[:500])
    with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as tf:
        tf.extractall(dest)
    return os.path.join(dest, *APP_REL.split("/"))


def _http(method: str, url: str, cookie: str = "", body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if cookie:
        req.add_header("Cookie", "studio_session=" + cookie)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="HEAD")
    args = ap.parse_args()

    scratch = tempfile.mkdtemp(prefix="smoke_")
    data_dir = os.path.join(scratch, "data")
    os.makedirs(data_dir)
    server = None
    failures: list[str] = []
    try:
        print(f"exporting {args.ref} ...")
        api = _export(args.ref, os.path.join(scratch, "tree"))
        env = dict(os.environ, STUDIO_DATA_DIR=data_dir, STUDIO_INSECURE_COOKIES="1", PYTHONUTF8="1",
                   PYTHONUNBUFFERED="1")
        # No provider keys: nothing here may call out, and a key would only make a mistake cost money.
        for k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
            env.pop(k, None)
        port = _free_port()
        log_path = os.path.join(scratch, "server.log")
        log = open(log_path, "w", encoding="utf-8")
        server = subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--port", str(port),
                                   "--host", "127.0.0.1"], cwd=api, env=env, stdout=log, stderr=subprocess.STDOUT)
        base = f"http://127.0.0.1:{port}"
        for _ in range(60):
            if server.poll() is not None:
                break
            try:
                if _http("GET", base + "/health")[0] == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        else:
            failures.append("server never became healthy")
        if server.poll() is not None:
            failures.append("server exited during start-up (see log below)")

        if not failures:
            # A signed-in session in the scratch database (same thing /login writes).
            mint = ("import os,auth as a\nfrom database import SessionLocal\nfrom models import User,Session as S\n"
                    "db=SessionLocal();u=db.query(User).first();n=a.utcnow();t=a.new_session_token()\n"
                    "db.add(S(token=t,user_id=u.id,created=n,expires=a.session_expiry(n)));db.commit();print(t)")
            m = subprocess.run([sys.executable, "-c", mint], cwd=api, env=env, capture_output=True, text=True)
            cookie = (m.stdout or "").strip().splitlines()[-1] if m.stdout.strip() else ""
            if not cookie:
                failures.append("could not mint a test session: " + (m.stderr or "")[-300:])

            st, body = _http("GET", base + "/selfcheck")
            try:
                sc = json.loads(body)
            except Exception:
                sc = {}
            print(f"  /selfcheck            {st}  ok={sc.get('ok')}  calls={sc.get('calls_checked')}  problems={sc.get('problems')}")
            if st != 200 or not sc.get("ok"):
                failures.append(f"/selfcheck reports {sc.get('problems')} mismatched call(s) -- run: python api/selfcheck.py")

            # The server calls its own signed-in routes (read-only, no AI) and must report all of them fine.
            st, body = _http("GET", base + "/selfcheck/deep")
            try:
                dp = json.loads(body)
            except Exception:
                dp = {}
            print(f"  /selfcheck/deep       {st}  ok={dp.get('ok')}  routes={dp.get('checked')}  failed={len(dp.get('failed') or [])}")
            if st != 200 or not dp.get("ok"):
                failures.append("/selfcheck/deep failed: " + "; ".join(dp.get("failed") or [f"HTTP {st}"]))

            # From OUTSIDE the process the door must stay shut: no key, and a guessed key, are both refused.
            for label, hdrs in (("no key", {}), ("guessed key", {"x-selfcheck-key": "guess"})):
                req = urllib.request.Request(base + "/brands")
                for k, v in hdrs.items():
                    req.add_header(k, v)
                try:
                    code = urllib.request.urlopen(req, timeout=30).status
                except urllib.error.HTTPError as e:
                    code = e.code
                print(f"  GET /brands ({label:11}) {code}  {'ok ' if code == 401 else 'FAIL'}")
                if code != 401:
                    failures.append(f"GET /brands with {label} answered {code}, expected 401")

            st, body = _http("GET", base + "/app")
            shell_ok = st == 200 and b"sc-if" in body
            print(f"  /app                  {st}  shell={'yes' if shell_ok else 'NO'}")
            if not shell_ok:
                failures.append("/app did not serve the studio shell")

            checks = [
                ("GET", "/me", None), ("GET", "/brands", None), ("GET", "/studio-settings", None),
                ("GET", "/houses", None), ("GET", "/plans", None), ("GET", "/library", None),
                ("GET", "/grounding?brand_mode=grounded", None), ("GET", "/grounding?brand_mode=general", None),
                # The routes that returned 500 to a real user on 18-19 Sep. None calls an AI provider.
                ("POST", "/producer-stands-on", {"kind": "social", "typed": "x", "brand_mode": "grounded"}),
                ("POST", "/producer-stands-on", {"kind": "social", "typed": "x", "brand_mode": "general"}),
            ]
            for method, path, payload in checks:
                st, _ = _http(method, base + path, cookie, payload)
                mark = "ok " if st < 500 else "FAIL"
                print(f"  {method:4} {path:34} {st}  {mark}")
                if st >= 500:
                    failures.append(f"{method} {path} answered {st}")
    finally:
        if server and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except Exception:
                server.kill()
        if failures:
            try:
                tail = open(os.path.join(scratch, "server.log"), encoding="utf-8", errors="replace").read()[-1800:]
                print("\n--- server log (tail) ---\n" + tail)
            except Exception:
                pass
        shutil.rmtree(scratch, ignore_errors=True)

    if failures:
        print("\nSMOKE FAILED:")
        for f in failures:
            print("  - " + f)
        return 1
    print("\nSMOKE PASSED -- the committed tree boots and answers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
