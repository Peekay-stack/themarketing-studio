#!/usr/bin/env python
"""test_pack_in_scene.py -- 1b: /scene-still's auto pack-attach respects the brand's pack_in_scene answer.

A brand that answered \"not a packed product\" must not get a real pack photo auto-attached just because a scene says
\"pack\"/\"bottle\"/\"pour\"; an explicit pick still attaches; every other answer keeps the noun heuristic; Heritage is unchanged.
Image and library.reference_url are stubbed, so no model or network is touched and the ONLY thing that can suppress an
attach is the policy (every test brand has a pack available).

    python tools/test_pack_in_scene.py          # exit 0 = behaves
"""
import os, sys, tempfile
os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="v1b_")
os.environ["PYTHONUTF8"] = "1"
for k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(k, None)
API = r"C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\api"
sys.path.insert(0, API); os.chdir(API)
import brandprofile as bp, main, selfcheck, library
from starlette.testclient import TestClient

os.environ["GOOGLE_API_KEY"] = "stub"
CAP = {"refs": None}
main._have_image = lambda: True
main.gemini.available = lambda: True
main.gemini.image = lambda prompt, **k: "https://x/still.png"
main.gemini.image_from_reference = lambda prompt, refs, **k: (CAP.__setitem__("refs", list(refs)) or "https://x/still.png")
main._record_made = lambda *a, **k: None
# Every brand in this test has a signed-off pack available, so the ONLY thing that can suppress the attach is the policy.
main.library.reference_url = lambda kind, brand="": ("https://x/pack.png" if kind == "pack" else ("https://x/plate.png" if kind == "plate" else ""))
main.library.shot_references = __import__("library").shot_references  # real logic, stubbed reference_url underneath

C = TestClient(main.app, raise_server_exceptions=True, headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})
fails = 0


def ck(label, cond, detail=""):
    global fails
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond else f"  -> {detail}"))
    fails += 0 if cond else 1


def still(scene="the pack sits on the counter", **extra):
    body = {"prompt": scene, "style": "real", "ratio": "3:4", "brand_mode": "grounded", "pack_mode": "auto", **extra}
    r = C.post("/scene-still", json=body)
    return r.json() if r.status_code == 200 else {"_status": r.status_code, "_text": r.text[:160]}


def mkbrand(name, pack_in_scene):
    b = bp.put({"name": name, "category": "Test", "pack_in_scene": pack_in_scene})
    bp.set_active(b["id"])
    return b


print("A 'not a packed product' brand: a scene that names a pack does NOT auto-attach one")
mkbrand("Servico", "not a packed product")
j = still("the pack sits on the counter, a bottle beside it")
ck("pack_used is false (policy suppresses the auto-attach)", j.get("pack_used") is False, j)
print("  ...but an explicit pack pick still attaches")
j2 = still("a plain scene", pack_id="")  # no real id; use include_pack to force instead
j2 = still("a plain scene", include_pack=True)
ck("include_pack:true still attaches for the same brand", j2.get("pack_used") is True, j2)

print("A normal brand ('only when it is in use'): a pack scene still auto-attaches (unchanged)")
mkbrand("Normco", "only when it is in use")
j3 = still("the pack sits on the counter")
ck("pack_used is true on a pack scene", j3.get("pack_used") is True, j3)
j4 = still("a child runs across a field")  # no pack noun
ck("pack_used is false on a non-pack scene", j4.get("pack_used") is False, j4)

print("An 'always' brand keeps the noun heuristic (not forced here); a pack scene attaches")
mkbrand("Alwaysco", "always")
j5 = still("the pack on the shelf")
ck("pack_used is true on a pack scene", j5.get("pack_used") is True, j5)

print("Heritage ('only when it is in use') is unchanged: its milk scenes still attach")
h = bp.put({"name": "Heritage Foods", "category": "Dairy", "pack_in_scene": "only when it is in use"})
bp.set_active(h["id"])
j6 = still("a pouch of milk is poured into a glass")
ck("pack_used is true (Heritage milk-pour scene attaches)", j6.get("pack_used") is True, j6)

print()
if fails:
    print(f"{fails} case(s) FAILED"); sys.exit(1)
print("All pack_in_scene cases behave.")
