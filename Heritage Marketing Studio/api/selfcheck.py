"""selfcheck.py -- does every backend call match the function it calls?

Why this exists: on 18-19 Sep the deployed `main.py` called `producers.stands_on(..., brand_mode=...)`
while the deployed `producers.py` was an older file with no such parameter. Python only notices a bad
keyword when the line RUNS, so the site returned HTTP 500 to a real user for a day. `py_compile` cannot
see it, `checkfe.py` reads only the front end, and `contract.py` reads response shapes. This reads the one
thing nobody was reading: **every call from one project module into another, against the real signature
of the function it calls.**

What it checks (and only this -- it is deliberately narrow):
  * a keyword argument the callee does not accept        -> the exact 18 Sep failure
  * more positional arguments than the callee accepts
  * a required argument the call never supplies          -> only when the call has no *args/**kwargs, where
                                                            its shape is fully known
  * a project module that fails to import at all

What it does NOT check: argument VALUES or types, required arguments on calls that unpack *args/**kwargs
(their real shape only exists at run time), or anything the frontend sends. A pass means "no call is shaped
wrong", not "the app works" -- the live use case still has to be run.

Used two ways, same code: `GET /selfcheck` on the running server (login-free, returns only a summary --
the detail is printed to the log), and `tools/smoke.py` against a clean export of the committed tree.

`deep()` (`GET /selfcheck/deep`) goes one step further: the running server calls its OWN signed-in routes
against its OWN real data and reports only a status code per route. It needs no login and no credential --
requests are made in-process (no socket) carrying a random key that exists only in this process's memory
(`internal_key_ok`, checked by the login middleware). Nothing is created in the database, nothing is written
to any tenant store, no AI provider is called, and the output never contains data. It is read-only by
construction: only GET routes and one pure POST are on its list.
"""
from __future__ import annotations

import ast
import hmac
import importlib
import inspect
import os
import secrets
import sys
import threading
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_SKIP_FILES = {"selfcheck.py"}

# A random key that exists ONLY in this process's memory: made at import, never logged, never returned,
# never sent over a socket. The login middleware lets a request through when it carries this key; only
# code running in this process (deep() below) can know it, so an outside caller cannot forge it.
_INTERNAL_KEY = secrets.token_hex(24)
INTERNAL_HEADER = "x-selfcheck-key"


def internal_key_ok(value) -> bool:
    """True only for this process's own key. Empty/missing is always False; comparison is constant-time."""
    return bool(value) and hmac.compare_digest(str(value), _INTERNAL_KEY)


def _project_modules() -> set[str]:
    """Top-level .py files next to this one -- the only code whose signatures we can and should verify."""
    return {f[:-3] for f in os.listdir(_HERE)
            if f.endswith(".py") and not f.startswith(("_", "test_")) and f not in _SKIP_FILES}


def _load(name: str):
    """A project module, from sys.modules when the app already imported it (always true on a live server,
    so this never re-runs a module's start-up side effects), else imported once."""
    mod = sys.modules.get(name)
    if mod is not None:
        return mod, ""
    try:
        return importlib.import_module(name), ""
    except Exception as e:  # noqa: BLE001 -- the point is to report ANY import failure
        return None, f"{type(e).__name__}: {e}"


def _check_call(callee, call: ast.Call) -> str:
    """'' when the call's SHAPE fits the callee, else a short reason. Calls that use *args or **kwargs are
    skipped -- their real shape is only known at run time. With none of those the shape is exact, so a
    full bind (which also demands every required argument) is a real check, not a guess."""
    if any(isinstance(a, ast.Starred) for a in call.args) or any(k.arg is None for k in call.keywords):
        return ""
    try:
        sig = inspect.signature(callee)
    except (TypeError, ValueError):
        return ""
    try:
        sig.bind(*[None] * len(call.args), **{k.arg: None for k in call.keywords})
    except TypeError as e:
        return str(e)
    return ""


def audit() -> dict:
    """Walk every project module's calls into other project modules. Returns
    {"checked": int, "problems": [{"file","line","call","why"}], "import_failures": [{"module","why"}]}."""
    names = _project_modules()
    problems: list[dict] = []
    import_failures: list[dict] = []
    loaded: dict[str, object] = {}
    checked = 0

    def module(name):
        if name not in loaded:
            mod, why = _load(name)
            loaded[name] = mod
            if why:
                import_failures.append({"module": name, "why": why})
        return loaded[name]

    for fname in sorted(names):
        path = os.path.join(_HERE, fname + ".py")
        try:
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=path)
        except SyntaxError as e:
            problems.append({"file": fname + ".py", "line": e.lineno or 0, "call": "(parse)", "why": f"SyntaxError: {e.msg}"})
            continue

        # alias -> project module, for `import x` / `import x as y` anywhere in the file (this codebase
        # imports lazily inside functions a lot, so a top-level-only scan would miss most of them).
        alias_to_module: dict[str, str] = {}
        # local name -> (module, attribute), for `from x import f [as g]`
        from_names: dict[str, tuple[str, str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name in names:
                        alias_to_module[a.asname or a.name] = a.name
            elif isinstance(node, ast.ImportFrom) and node.module in names and node.level == 0:
                for a in node.names:
                    from_names[a.asname or a.name] = (node.module, a.name)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = attr = None
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) \
                    and node.func.value.id in alias_to_module:
                target, attr = alias_to_module[node.func.value.id], node.func.attr
            elif isinstance(node.func, ast.Name) and node.func.id in from_names:
                target, attr = from_names[node.func.id]
            if not target or target == fname:
                continue
            mod = module(target)
            callee = getattr(mod, attr, None) if mod is not None else None
            if callee is None or not callable(callee) or isinstance(callee, type):
                continue  # a constant, a class, or something that is not a plain function -- out of scope
            checked += 1
            why = _check_call(callee, node)
            if why:
                problems.append({"file": fname + ".py", "line": node.lineno,
                                 "call": f"{target}.{attr}", "why": why})
    return {"checked": checked, "problems": problems, "import_failures": import_failures}


def summary() -> dict:
    """What the login-free route returns: enough to know pass/fail and which deploy answered, and nothing
    that maps the internals to an anonymous caller. The detail goes to the log instead."""
    r = audit()
    ok = not r["problems"] and not r["import_failures"]
    if not ok:
        for p in r["problems"]:
            print(f"[selfcheck] {p['file']}:{p['line']} {p['call']} -- {p['why']}")
        for f in r["import_failures"]:
            print(f"[selfcheck] import failed: {f['module']} -- {f['why']}")
    return {"ok": ok, "commit": (os.environ.get("RENDER_GIT_COMMIT") or "")[:10],
            "calls_checked": r["checked"], "problems": len(r["problems"]),
            "import_failures": len(r["import_failures"])}


_deep_lock = threading.Lock()
_deep_cache: dict = {"t": 0.0, "result": None}
DEEP_MIN_INTERVAL = 60  # seconds -- the route is public, so it must not be a way to make the server work


def deep(app) -> dict:
    """Call the app's own signed-in routes, in-process, on its real data. Returns
    {"ok", "commit", "checked", "failed": [route...], "routes": [{"route","status","ms"}], "seconds", "cached"}.

    Read-only and data-free by construction: GET routes plus one pure POST, cost-free (no AI call), and the
    result carries route TEMPLATES and status codes only -- never an id or a body. A route passes on any
    status below 400. It also proves the door is still shut: the same route with no key, and with a wrong
    key, must answer 401.
    """
    with _deep_lock:
        now = time.time()
        if _deep_cache["result"] is not None and now - _deep_cache["t"] < DEEP_MIN_INTERVAL:
            return dict(_deep_cache["result"], cached=True)

        from starlette.testclient import TestClient
        started = time.time()
        signed_in = TestClient(app, raise_server_exceptions=False, headers={INTERNAL_HEADER: _INTERNAL_KEY})
        anonymous = TestClient(app, raise_server_exceptions=False)
        wrong_key = TestClient(app, raise_server_exceptions=False, headers={INTERNAL_HEADER: "not-the-key"})
        routes: list[dict] = []

        def hit(client, method, path, label, expect=None, **kw):
            t0 = time.time()
            try:
                r = client.request(method, path, **kw)
                status = r.status_code
            except Exception:  # noqa: BLE001 -- a transport-level failure is a failure to report, not a crash
                r, status = None, 0
            ok = (status == expect) if expect else (0 < status < 400)
            routes.append({"route": label, "status": status, "ms": int((time.time() - t0) * 1000), "ok": ok})
            return r

        def rows(r, key):
            try:
                v = r.json().get(key) if r is not None else None
                return v if isinstance(v, list) else []
            except Exception:  # noqa: BLE001
                return []

        # The door must stay shut to everyone who does not hold the key.
        hit(anonymous, "GET", "/brands", "GET /brands (no key) -> must be 401", expect=401)
        hit(wrong_key, "GET", "/brands", "GET /brands (wrong key) -> must be 401", expect=401)

        # Read routes on real data.
        hit(signed_in, "GET", "/brands", "GET /brands")
        hit(signed_in, "GET", "/studio-settings", "GET /studio-settings")
        hit(signed_in, "GET", "/library", "GET /library")
        hit(signed_in, "GET", "/pr-sheets", "GET /pr-sheets")
        hit(signed_in, "GET", "/grounding?brand_mode=grounded", "GET /grounding (grounded)")
        hit(signed_in, "GET", "/grounding?brand_mode=general", "GET /grounding (general)")
        houses = rows(hit(signed_in, "GET", "/houses", "GET /houses"), "houses")
        plans = rows(hit(signed_in, "GET", "/plans", "GET /plans"), "plans")
        sets = rows(hit(signed_in, "GET", "/idea-platform-sets", "GET /idea-platform-sets"), "sets")
        # The routes that returned HTTP 500 on 18-19 Sep. Pure: no AI call, nothing written.
        for mode in ("grounded", "general"):
            hit(signed_in, "POST", "/producer-stands-on", f"POST /producer-stands-on ({mode})",
                json={"kind": "social", "typed": "x", "brand_mode": mode})

        # Real objects, opened and exported as documents -- this is the "real data shape" check. Two of each
        # at most: an export builds a temp file, so the count is bounded on purpose.
        for h in houses[:2]:
            hid = str(h.get("id") or "")
            if hid:
                hit(signed_in, "GET", f"/house/{hid}", "GET /house/{id}")
                hit(signed_in, "GET", f"/house-docx/{hid}", "GET /house-docx/{id}")
        for pl in plans[:2]:
            pid = str(pl.get("id") or "")
            if pid:
                hit(signed_in, "GET", f"/plan/{pid}", "GET /plan/{id}")
                hit(signed_in, "GET", f"/plan-docx/{pid}", "GET /plan-docx/{id}")
        for st in sets[:2]:
            sid = str(st.get("id") or "")
            if sid:
                hit(signed_in, "GET", f"/platform-docx/{sid}", "GET /platform-docx/{id}")

        failed = [f"{r['route']} -> {r['status']}" for r in routes if not r["ok"]]
        for f in failed:
            print(f"[selfcheck/deep] FAILED {f}")
        result = {"ok": not failed, "commit": (os.environ.get("RENDER_GIT_COMMIT") or "")[:10],
                  "checked": len(routes), "failed": failed,
                  "routes": [{k: r[k] for k in ("route", "status", "ms")} for r in routes],
                  "seconds": round(time.time() - started, 2), "cached": False}
        _deep_cache["t"], _deep_cache["result"] = time.time(), result
        return result


if __name__ == "__main__":
    res = audit()
    for p in res["problems"]:
        print(f"PROBLEM  {p['file']}:{p['line']}  {p['call']}  ->  {p['why']}")
    for f in res["import_failures"]:
        print(f"IMPORT   {f['module']}  ->  {f['why']}")
    print(f"{res['checked']} cross-module calls checked, {len(res['problems'])} problem(s), "
          f"{len(res['import_failures'])} import failure(s)")
    sys.exit(1 if (res["problems"] or res["import_failures"]) else 0)
