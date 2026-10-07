#!/usr/bin/env python
"""test_video_agnostic.py -- Video's writing prompts carry no brand's or category's signature.

The video path is meant to be brand-agnostic: everything about the brand comes from its profile. Two guards, because this is a thing that
quietly regrows:

1. The SOURCE of the Video prompt builders (the page's concept, script, rework, scene rewrite, cast-sheet and department prompts, and the
   server's film instruction blocks) must not name dairy, milk, Heritage, an Indian family, a saree, "Ammamma" or a mother-and-boy example.
2. A brand's tagline / sign-off line is NOT mandatory in a film (each film has its own payoff line), while its marks and declarations stay
   mandatory. Non-film pieces are untouched.

Known gaps that are NOT yet generic (they are paid-render, voice and music prompts, and the objective chips): see VIDEO_BRAND_AGNOSTIC_AUDIT.md.
No key, no credit, a scratch data folder.

    python tools/test_video_agnostic.py      # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import re
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="videoagn_")
os.environ["STUDIO_DATA_DIR"] = _scratch
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.abspath(os.path.join(HERE, "..", "api"))
sys.path.insert(0, API)
os.chdir(API)

import brandprofile  # noqa: E402
import prompts       # noqa: E402

fails = 0


def check(name, ok, extra=""):
    global fails
    fails += 0 if ok else 1
    print(("  ok   " if ok else "  FAIL ") + name + (f"   [{extra}]" if (extra and not ok) else ""))


# ---------------------------------------------------------------- 1. the source of the prompt builders
html = open(os.path.join(API, "frontend", "app.dc.html"), encoding="utf-8").read()
MEMBER = re.compile(r"^  (?:async )?([A-Za-z0-9_]+)\s*(?:=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_]+)\s*=>|\([^)]*\)\s*\{|=)", re.M)
heads = [(m.start(), m.group(1)) for m in MEMBER.finditer(html)]


def body_of(name: str) -> str:
    for i, (pos, nm) in enumerate(heads):
        if nm == name:
            end = heads[i + 1][0] if i + 1 < len(heads) else len(html)
            return html[pos:end]
    return ""


SIGNATURES = re.compile(r"\b(milk|doodh|dairy|heritage|ammamma|saree|boy grows up|indian crew|MOTHER|BOY)\b", re.I)
print("the page's Video prompt builders name no brand or category")
for fn in ("generateVideo", "writeProvocationRoute", "writeFullScript", "reworkScript", "rewriteScene", "deriveCharacters", "deriveLocationLine",
           "deriveLookRef", "draftDept", "VISUAL_RULES"):
    body = body_of(fn)
    # drop comment lines: a comment may explain WHY something is not said
    code = "\n".join(l for l in body.split("\n") if not l.strip().startswith("//"))
    found = sorted({m.group(0).lower() for m in SIGNATURES.finditer(code)})
    check(f"{fn} is generic", bool(body) and not found, f"{'missing' if not body else found}")

print("the server's film instructions name no brand or category")
for nm in ("VIDEO", "VIDEO_PROVOCATION"):
    block = getattr(prompts, nm)
    check(f"prompts.{nm} is generic", not SIGNATURES.search(block), str(SIGNATURES.findall(block)))

# ---------------------------------------------------------------- 2. the tagline is not mandatory in a film
print("a tagline is optional in a film, the marks are not")
HF = {"name": "Heritage Foods", "category": "Dairy", "tone": "warm", "mandatories": ["FSSAI mark", "the line 'Pure Doodh Ki Shakti'"]}
plain = brandprofile.voice_block(HF)
film = brandprofile.voice_block(HF, film=True)
check("outside a film the mandatories are exactly what they were", "MANDATORY ON EVERY PIECE: FSSAI mark; the line 'Pure Doodh Ki Shakti'" in plain and "SIGN-OFF" not in plain, plain)
check("in a film the mark stays mandatory", "MANDATORY ON EVERY PIECE: FSSAI mark" in film and "Pure Doodh Ki Shakti'" not in film.split("SIGN-OFF")[0], film)
check("in a film the tagline is on file but explicitly NOT mandatory", "SIGN-OFF LINE ON FILE (NOT mandatory in a film" in film and "Pure Doodh Ki Shakti" in film, film)
CEM = {"name": "Sthir Cement", "category": "Cement", "mandatories": ["BIS grade mark and IS number", "batch and packing date", "MRP on bag"]}
check("a brand with only marks and declarations is byte-identical in a film", brandprofile.voice_block(CEM) == brandprofile.voice_block(CEM, film=True), "")
check("a brand with a tagline only has no mandatory line left in a film", "MANDATORY" not in brandprofile.voice_block({**HF, "mandatories": ["tagline: Be bold"]}, film=True), "")
check("skip_mandatories still removes the whole line, in a film too", "SIGN-OFF" not in brandprofile.voice_block(HF, skip_mandatories=True, film=True) and "MANDATORY" not in brandprofile.voice_block(HF, skip_mandatories=True, film=True), "")
for t in ("the line 'x'", "tagline: x", "Sign-off line", "payoff line", "our slogan", "Brand tagline"):
    check(f"'{t}' is a line", bool(brandprofile.SIGNOFF_LINE_RE.match(t)), t)
for t in ("FSSAI mark", "full INCI list", "Legal Metrology declarations", "care instructions on pack", "MRP on bag", "batch and packing date"):
    check(f"'{t}' is a mark or declaration, not a line", not brandprofile.SIGNOFF_LINE_RE.match(t), t)

print("the system prompt follows")
VIDEO_MSG = [{"role": "user", "content": "You are a film director at an ad agency. Propose a short film script. Return JSON with a logline and scenes."}]
DEPT_MSG = [{"role": "user", "content": "You are the Art department head. APPROVED SCRIPT: scene one."}]
BRIEF_MSG = [{"role": "user", "content": "You are a brief writer. Write the brief for this request, single-minded."}]
sv = prompts.system_for(VIDEO_MSG, brand=HF)
check("a film surface moves the tagline out of the mandatories", "SIGN-OFF LINE ON FILE" in sv and "MANDATORY ON EVERY PIECE: FSSAI mark" in sv, "")
sd = prompts.system_for(DEPT_MSG, brand=HF)
check("a department prompt (no film surface) keeps it until it says it is a film", "SIGN-OFF" not in sd, "")
sd2 = prompts.system_for(DEPT_MSG, brand=HF, film=True)
check("...and with film=True it too moves the tagline out", "SIGN-OFF LINE ON FILE" in sd2, "")
sb = prompts.system_for(BRIEF_MSG, brand=HF)
check("a brief is untouched", "SIGN-OFF" not in sb and "the line 'Pure Doodh Ki Shakti'" in sb, "")

print("/complete passes the film flag")
from starlette.testclient import TestClient  # noqa: E402

import main            # noqa: E402
import selfcheck       # noqa: E402

os.environ.pop("ANTHROPIC_API_KEY", None)
seen = []
real_complete, real_has_key = main.completion.complete, main.completion.has_key
main.completion.has_key = lambda: True
main.completion.complete = lambda messages, **kw: (seen.append(kw), "stub")[1]
client = TestClient(main.app, raise_server_exceptions=True, headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})
client.post("/complete", json={"messages": VIDEO_MSG, "film": True})
check("film: true reaches the system prompt builder", seen and seen[-1].get("film") is True, str(seen[-1:]))
client.post("/complete", json={"messages": VIDEO_MSG})
check("without it, it is False", seen[-1].get("film") is False, str(seen[-1:]))
client.post("/complete", json={"messages": VIDEO_MSG, "film": "yes"})
check("only a real true counts", seen[-1].get("film") is False, "")
main.completion.complete, main.completion.has_key = real_complete, real_has_key

print()
print("All brand-agnostic video cases behave." if not fails else f"{fails} brand-agnostic video case(s) FAILED.")
sys.exit(1 if fails else 0)
