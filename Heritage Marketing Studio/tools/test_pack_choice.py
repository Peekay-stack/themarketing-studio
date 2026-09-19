#!/usr/bin/env python
"""test_pack_choice.py -- does /scene-still attach a pack photo exactly when the person's choice says so?

Why: on 19 Sep the Social screen's pack dropdown read "Not used in these posts" while the server still
attached the brand's signed-off pack whenever a post's own words named the product (pack, packet, pour,
FSSAI ...) -- and, the mirror image, a pack the person deliberately PICKED was ignored on any scene that
never named the product. This pins the whole matrix so neither can come back.

It calls the real `/scene-still` route in-process. The two image providers, the ledger write and the
library's file lookups are stubbed, so it needs no API key, costs nothing, writes nothing and touches no real
data (a scratch data directory is used). What it proves is the DECISION about references; it cannot prove
what an image model then draws.

    python tools/test_pack_choice.py          # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="packtest_")
os.environ["STUDIO_DATA_DIR"] = _scratch
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api")
sys.path.insert(0, os.path.abspath(API))
os.chdir(os.path.abspath(API))

import main          # noqa: E402
import selfcheck     # noqa: E402
import library       # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

AUTO_PACK = "http://stub/auto-pack.png"      # what the library would attach on its own
PICKED = "PICKED"                            # the id a person picks in the dropdown
PICKED_URL = "http://stub/picked-pack.png"

seen_refs: list[list[str]] = []

main._have_image = lambda: True
main._record_made = lambda *a, **k: None
main.gemini.image_from_reference = lambda prompt, refs, **k: (seen_refs.append(list(refs)) or "http://stub/img.png")
main.gemini.image = lambda prompt, **k: "http://stub/img.png"
main.creative.image_from_reference = lambda prompt, refs, **k: (seen_refs.append(list(refs)) or "http://stub/img.png")
library.reference_url = lambda kind, brand="": AUTO_PACK if kind == "pack" else ""
library.get = lambda i: ({"id": i, "url": PICKED_URL, "kind": "pack", "signed_off": True} if i == PICKED else None)
library._owned = lambda row: True

client = TestClient(main.app, raise_server_exceptions=True, headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})

NAMES_PACK = "A woman pours milk from a packet into a steel glass in a bright kitchen"
NO_PACK = "A family laughing together at the breakfast table"

# (label, scene, extra payload fields, brand_mode, expect pack attached?, which url expected if attached)
CASES = [
    ("Automatic, scene names the pack        -> attaches", NAMES_PACK, {}, "grounded", True, AUTO_PACK),
    ("Automatic, scene does not name it      -> none", NO_PACK, {}, "grounded", False, None),
    ("Never, scene names the pack            -> none", NAMES_PACK, {"include_pack": False}, "grounded", False, None),
    ("Pinned (pack_id + include_pack:true), scene does NOT name it -> attaches the PICKED one",
     NO_PACK, {"pack_id": PICKED, "include_pack": True}, "grounded", True, PICKED_URL),
    ("Pinned by pack_id alone (server rule), scene does NOT name it -> attaches the PICKED one",
     NO_PACK, {"pack_id": PICKED}, "grounded", True, PICKED_URL),
    ("Design one (pack_generate, include_pack:false), scene names the pack -> none, design clause",
     NAMES_PACK, {"pack_generate": True, "include_pack": False}, "grounded", False, None),
    ("Independent + Automatic, scene names the pack -> stripped (auto-picked packs never survive)",
     NAMES_PACK, {}, "general", False, None),
    ("Independent + explicit pick             -> the person's own choice survives",
     NO_PACK, {"pack_id": PICKED}, "general", True, PICKED_URL),
]

failures = 0
for label, scene, extra, mode, expect_used, expect_url in CASES:
    seen_refs.clear()
    body = {"scene_no": 1, "ratio": "1:1", "style": "real", "prompt": scene, "brand_mode": mode, "use_cast": False, **extra}
    r = client.post("/scene-still", json=body)
    data = r.json() if r.status_code == 200 else {}
    used = bool(data.get("pack_used"))
    url_ok = (expect_url in (seen_refs[0] if seen_refs else [])) if expect_used else True
    generated = bool(data.get("pack_generated"))
    ok = r.status_code == 200 and used == expect_used and url_ok
    if extra.get("pack_generate"):
        ok = ok and generated
    print(f"  {'ok  ' if ok else 'FAIL'} {label}   [status={r.status_code} pack_used={used}"
          + (f" pack_generated={generated}" if extra.get('pack_generate') else "") + "]")
    if not ok:
        failures += 1

print()
if failures:
    print(f"{failures} case(s) FAILED")
    sys.exit(1)
print("All pack-choice cases behave.")
