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
  * a project module that fails to import at all

What it does NOT check: missing required arguments (a call may fill them via *args/**kwargs, which a
static read cannot see), argument VALUES or types, or anything the frontend sends. A pass means "no call is
shaped wrong", not "the app works" -- the live use case still has to be run.

Used two ways, same code: `GET /selfcheck` on the running server (login-free, returns only a summary --
the detail is printed to the log), and `tools/smoke.py` against a clean export of the committed tree.
"""
from __future__ import annotations

import ast
import importlib
import inspect
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SKIP_FILES = {"selfcheck.py"}


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
    skipped -- their real shape is only known at run time."""
    if any(isinstance(a, ast.Starred) for a in call.args) or any(k.arg is None for k in call.keywords):
        return ""
    try:
        sig = inspect.signature(callee)
    except (TypeError, ValueError):
        return ""
    try:
        sig.bind_partial(*[None] * len(call.args), **{k.arg: None for k in call.keywords})
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


if __name__ == "__main__":
    res = audit()
    for p in res["problems"]:
        print(f"PROBLEM  {p['file']}:{p['line']}  {p['call']}  ->  {p['why']}")
    for f in res["import_failures"]:
        print(f"IMPORT   {f['module']}  ->  {f['why']}")
    print(f"{res['checked']} cross-module calls checked, {len(res['problems'])} problem(s), "
          f"{len(res['import_failures'])} import failure(s)")
    sys.exit(1 if (res["problems"] or res["import_failures"]) else 0)
