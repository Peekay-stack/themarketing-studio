#!/usr/bin/env python
"""test_tools.py — proof that the two build tools do what they claim.

    python tools/test_tools.py

Two things are being proved, and both are load-bearing:

**The partial round trip is byte-identical.** A build step that nearly reproduces a 661KB file is worse
than no build step: the damage surfaces later and looks like somebody else's bug.

**checkfe actually catches the failure it was built for.** A green lint that cannot fail is a worse
liability than no lint, because it launders the next real defect through. So each check is fed a file
containing exactly the damage it is supposed to find, and is required to report it — including the
false-positive regression, where correct code with a nested `${JSON.stringify({...})}` must come back
clean. That one is not hypothetical: the first version of the scanner failed it and reported three
confident errors in working code.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "api", "frontend", "app.dc.html")

import checkfe
import partials

PASS, FAIL = [], []


def ok(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(name)
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))


def _wrap(js: str) -> str:
    """Minimal file with the same region markers as the real one, so _regions() finds the logic."""
    return ('<div>\n  <!-- ===== A ===== -->\n  <p>x</p>\n</div>\n'
            '<script type="text/x-dc" data-dc-script>\n'
            'class Component extends DCLogic {\n' + js + '\n}\n</script>\n')


def _scan(js: str) -> list[str]:
    markup, logic, first = checkfe._regions(_wrap(js))
    return checkfe.scan_js(logic, first)


# --- partials -----------------------------------------------------------------------------------
print("\npartials.py")

original = open(SRC, "rb").read()
good, msg = partials.verify(SRC)
ok("round trip on the real file is byte-identical", good, msg)

spec = partials.plan(original)
ok("split produces more than a handful of parts", len(spec) > 30, f"{len(spec)} parts")
ok("no part is empty", all(b > a for _, a, b in spec))
# Contiguity has to be checked pairwise. Comparing the flattened bounds to their own sorted order
# catches an overlap but not a gap — a dropped line would still be in ascending order.
nlines = len(original.splitlines(keepends=True))
contiguous = (spec[0][1] == 0 and spec[-1][2] == nlines
              and all(spec[i][2] == spec[i + 1][1] for i in range(len(spec) - 1)))
ok("parts cover every line with no gap or overlap", contiguous,
   f"lines 0..{nlines} across {len(spec)} parts")

# The workflow that matters: edit one part, rejoin, and get that edit and nothing else. The marker is
# appended so it cannot depend on the part happening to contain any particular text — an earlier version
# of this test searched for a string that was not there, "changed" nothing, and passed.
tmp = tempfile.mkdtemp(prefix="tt_")
partials.split(SRC, tmp)
target = sorted(f for f in os.listdir(tmp) if f.endswith(".part"))[3]
MARK = b"<!-- round-trip marker -->\n"
path = os.path.join(tmp, target)
open(path, "ab").write(MARK)
rejoined = partials.join(tmp)
ok("editing one part changes only that part",
   len(rejoined) == len(original) + len(MARK) and rejoined.count(MARK) == 1
   and rejoined.replace(MARK, b"", 1) == original,
   f"{target} grew by {len(MARK)} bytes, rest untouched")
open(path, "wb").write(open(path, "rb").read()[:-len(MARK)])   # put it back

# An emptied part must refuse rather than silently delete a screen.
open(os.path.join(tmp, target), "wb").write(b"")
try:
    partials.join(tmp)
    ok("an emptied part is refused", False, "it joined anyway")
except SystemExit as e:
    ok("an emptied part is refused", "empty" in str(e).lower())

# --- checkfe ------------------------------------------------------------------------------------
print("\ncheckfe.py")

ok("the real file passes every check", checkfe.check(SRC) == 0)

# THE regression: correct code with a brace inside an interpolation must come back clean.
nested = _scan("""  m = () => {
    const r = ` a ${JSON.stringify({ logline:1, scenes:[{t:'0-5s'}] })} b ${x.trim()} c `;
    return r;
  };""")
ok("nested ${JSON.stringify({...})} is NOT flagged", not nested, "; ".join(nested[:2]))

# Template holding a brace-looking string, and a regex with a slash in a class.
tricky = _scan("""  m = () => {
    const a = `sizes {1:2} and ${'}'} done`;
    const b = 'a }{ b';
    const c = raw.replace(/^```json/i, '').replace(/[/\\]]/g, '');
    const d = 10 / 2 / 1;
    return [a, b, c, d];
  };""")
ok("braces in strings, regex literals and division are NOT flagged", not tricky,
   "; ".join(tricky[:2]))

# The damage I actually shipped: a real newline inside a quoted string.
broken = _scan("""  m = () => {
    const msg = 'Briefed. No producer is wired
 for onground artwork yet.';
    return msg;
  };""")
ok("a newline inside a quoted string IS caught",
   any("unterminated" in p for p in broken), broken[0] if broken else "nothing reported")

ok("an unclosed brace IS caught",
   any("never closed" in p for p in _scan("  m = () => {\n    if (x) {\n    return 1;\n  };")))
ok("a mismatched closer IS caught",
   any("closes" in p for p in _scan("  m = () => { return foo(1]; };")))
ok("an unterminated block comment IS caught",
   any("block comment" in p for p in _scan("  /* nope\n  m = () => 1;")))

# The whole-file checks, driven through check() on a written temp file.
def _file_check(body: str) -> str:
    p = os.path.join(tmp, "t.html")
    open(p, "w", encoding="utf-8").write(_wrap(body))
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        checkfe.check(p)
    return buf.getvalue()

out = _file_check("  foo = () => 1;\n  foo = () => 2;")
ok("a duplicate class member IS caught", "declared more than once" in out)

out = _file_check("  renderVals() {\n    return { ...this.bagGhost(s) };\n  }")
ok("a bag method spread but never defined IS caught", "never defined" in out)

out = _file_check("  bagOrphan(s){ return {}; }\n  renderVals() { return {}; }")
ok("a bag method defined but never spread IS caught", "never spread" in out)

# --- the banner insertion did nothing but add banners -------------------------------------------
print("\nthe banner insertion")
pre = SRC + ".pre-banners"
if os.path.exists(pre):
    before = open(pre, encoding="utf-8").read().split("\n")
    after = open(SRC, encoding="utf-8").read().split("\n")
    added = [l for l in after if l not in before or after.count(l) > before.count(l)]
    banners = [l for l in added if l.strip().startswith("// =====")]
    stripped = [l for l in after if not re.match(r"^  // ===== .+ =====$", l)]
    ok("every added line is a banner", len(added) == len(banners), f"{len(added)} added")
    ok("removing the banners restores the previous file exactly",
       "\n".join(stripped) == "\n".join(before),
       f"{len(after) - len(stripped)} banners inserted")
else:
    print("  skip  no .pre-banners backup to compare against")

# --- no two routes may claim the same (method, path) --------------------------------------------
#
# FastAPI matches the FIRST route registered for a path, so a second `@app.post("/x")` lower down the
# file is not an override — it is dead code that reads as live. Nothing warns. In one file this long,
# two people (or one person twice) reaching for the same obvious name is close to inevitable.
#
# It has now happened three times, and the expensive one: the shot-list screen's `/shot-still {id}`
# request reached a *generator* registered 400 lines earlier and spent a real image credit inventing a
# storyboard frame, instead of pulling a frame out of the footage that was already on disk. The other two
# were `/shot-row` (shadowing `shotlist.py`'s) and `/platforms` (social platforms vs idea platforms —
# one word with two meanings in the product, which became one path with two meanings in the API).
#
# Every one was invisible in review and none was catchable by `checkfe` or `contract.py`.
print("\nno duplicate routes")
import subprocess as _sp

# Importing the app needs fastapi, which lives in the api venv rather than whatever interpreter is
# running this file. Run it there. A check that quietly downgrades to "skip" on the machine where it
# matters is the failure mode this whole file exists to avoid, so an unusable venv is a FAIL and says why.
_API = os.path.join(ROOT, "api")
_VENV = os.path.join(_API, ".venv", "Scripts", "python.exe")
if not os.path.exists(_VENV):
    _VENV = os.path.join(_API, ".venv", "bin", "python")
_PROG = (
    "import sys; sys.path.insert(0,'.');"
    "from collections import Counter; import main;"
    "p=[(m,r.path) for r in main.app.routes if hasattr(r,'methods') and hasattr(r,'path')"
    " for m in (r.methods or []) if m in ('GET','POST','PUT','PATCH','DELETE')];"
    "d=sorted(f'{m} {q}' for (m,q),n in Counter(p).items() if n>1);"
    "print(len(p)); print('|'.join(d))"
)
if not os.path.exists(_VENV):
    ok("every (method, path) is registered exactly once", False,
       "no api/.venv — run run-local.bat once so this check can import the app")
else:
    _r = _sp.run([_VENV, "-c", _PROG], capture_output=True, text=True, cwd=_API)
    _out = (_r.stdout or "").strip().splitlines()
    if _r.returncode != 0 or not _out:
        ok("every (method, path) is registered exactly once", False,
           ((_r.stderr or "").strip().splitlines() or ["the app would not import"])[-1][:80])
    else:
        _n = _out[0].strip()
        _dups = [x for x in (_out[1] if len(_out) > 1 else "").split("|") if x]
        ok("every (method, path) is registered exactly once", not _dups,
           f"{_n} routes" + (f" — SHADOWED: {', '.join(_dups)}" if _dups else ""))

# --- the contract check runs here too, so a shape mismatch cannot ship quietly ------------------
print("\ncontract.py")
import subprocess
_r = subprocess.run([sys.executable, os.path.join(HERE, "contract.py")],
                    capture_output=True, text=True)
_last = [l for l in ((_r.stdout or "") + (_r.stderr or "")).splitlines() if l.strip()]
ok("backend shapes match what the frontend iterates", _r.returncode == 0,
   _last[-1].strip()[:88] if _last else "")

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
for f in FAIL:
    print(f"  failed: {f}")
raise SystemExit(1 if FAIL else 0)
