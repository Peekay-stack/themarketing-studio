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
seen_prompts: list[str] = []
_CAST_ON = [False]
CAST_URL = "http://stub/cast.png"
_real_record_made = main._record_made

main._have_image = lambda: True
main._record_made = lambda *a, **k: None
main.gemini.image_from_reference = lambda prompt, refs, **k: (seen_refs.append(list(refs)) or seen_prompts.append(prompt) or "http://stub/img.png")
main.gemini.image = lambda prompt, **k: (seen_prompts.append(prompt) or "http://stub/img.png")
main.creative.image_from_reference = lambda prompt, refs, **k: (seen_refs.append(list(refs)) or seen_prompts.append(prompt) or "http://stub/img.png")
library.reference_url = lambda kind, brand="": AUTO_PACK if kind == "pack" else (CAST_URL if (kind == "cast" and _CAST_ON[0]) else "")
library.get = lambda i: ({"id": i, "url": PICKED_URL, "kind": "pack", "signed_off": True} if i == PICKED else None)
library._owned = lambda row: True

client = TestClient(main.app, raise_server_exceptions=True, headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})

NAMES_PACK = "A woman pours milk from a packet into a steel glass in a bright kitchen"
NO_PACK = "A family laughing together at the breakfast table"
POUCH = "A woman holds a pouch of milk up to the kitchen window"
SACHET = "A milk sachet resting beside a steel tumbler of filter coffee"
BAG = "She carries a bag of milk home along the street at dawn"

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
    # The 21 Sep change: Automatic (pack_mode:"auto", what Social/Carousel now send) also recognises the words a
    # milk POUCH is actually described with. Callers that send no pack_mode (Video frames, /shot-reference)
    # keep the original list, so they must NOT start attaching on these words.
    ("Automatic (pack_mode auto), scene says 'pouch'   -> attaches", POUCH, {"pack_mode": "auto"}, "grounded", True, AUTO_PACK),
    ("Automatic (pack_mode auto), scene says 'sachet'  -> attaches", SACHET, {"pack_mode": "auto"}, "grounded", True, AUTO_PACK),
    ("Automatic (pack_mode auto), scene says 'bag of milk' -> attaches", BAG, {"pack_mode": "auto"}, "grounded", True, AUTO_PACK),
    ("Automatic (pack_mode auto), unrelated scene       -> none", NO_PACK, {"pack_mode": "auto"}, "grounded", False, None),
    ("NO pack_mode (Video/shot-reference style), scene says 'pouch' -> unchanged: none", POUCH, {}, "grounded", False, None),
    ("Never beats Automatic even with pack_mode auto, scene says 'pouch' -> none", POUCH, {"pack_mode": "auto", "include_pack": False}, "grounded", False, None),
    ("Independent + Automatic (pack_mode auto), scene says 'pouch' -> stripped", POUCH, {"pack_mode": "auto"}, "general", False, None),
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


# ============================================================================================================
# 21 Sep: pack-in-scene wording (`pack_role`), and a session-only reference photo (`pack_reference`).
# Proven first on the owner's real Nourish+ photo (10 real generations); these pin what the server sends.
# ============================================================================================================
import base64  # noqa: E402
import packscene  # noqa: E402

PHOTO = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff\xe0 SESSION-ONLY PACK PHOTO MARKER").decode()
PREV = "http://stub/previous-render.png"
SCENE = "A young mother and her child laugh together at a breakfast table."


def send(extra, style="real", mode="grounded", scene=SCENE):
    seen_refs.clear(); seen_prompts.clear()
    body = {"scene_no": 1, "ratio": "1:1", "style": style, "prompt": scene, "brand_mode": mode, "use_cast": False, **extra}
    r = client.post("/scene-still", json=body)
    return r.status_code, (r.json() if r.status_code == 200 else {}), (seen_prompts[0] if seen_prompts else ""), (seen_refs[0] if seen_refs else [])


def expect(label, ok, extra=""):
    global failures
    print(f"  {'ok  ' if ok else 'FAIL'} {label}" + (f"   [{extra}]" if extra else ""))
    if not ok:
        failures += 1


PICK = {"pack_id": PICKED, "include_pack": True}
print()
print("pack-in-scene wording:")
st, d, pr, rf = send({**PICK, "pack_role": "side"})
expect("side, Real: opens as a plain marketing image, not 'same people from the reference'",
       pr.startswith("Create the image for a marketing post.") and "reusing the EXACT same people" not in pr
       and "same film" not in pr)
expect("side, Real: says the reference IS the real product, front-on, never redrawn",
       "The pack in the reference image is the real product" in pr and "front-on" in pr and "Never redraw" in pr)
expect("side, Real: front only, never the back or a nutrition panel, and exactly one pack",
       "Show only the FRONT of the pack" in pr and "nutrition panel" in pr and "exactly one pack" in pr)
expect("side, Real: a crate/shelf/stack scene still gets only one sharp pack, the rest blurred",
       "crate, shelf, stack, basket" in pr and "blurred, out-of-focus or indistinct" in pr)
st2, d2, pr2, rf2 = send({**PICK, "pack_role": "in_use"}, style="vector")
expect("every role and style carries the front-only / one-pack line (photo and illustrated alike)",
       "Show only the FRONT of the pack" in pr2 and "Show only the FRONT of the pack" in pr)
expect("side, Real: places it to one side, sized to a real hand-held pack (composition-independent), not over a face",
       "Place the pack to one side of the frame" in pr and "no larger than a real pack held in the hand of an average-built adult" in pr
       and "SAME real-world size whether this shot is a wide scene or a tight close-up" in pr
       and "not overlapping anyone's face" in pr)
expect("side, Real: an absolute (hand-independent) size anchor, and a ban on hero-product posing",
       "roughly the size of a paperback book" in pr and "whether or not a hand is actually touching it" in pr
       and "Never pose it as a hero product shot" in pr and "held out at arm's length" in pr)
expect("side, Real: asks for no added marks, and replaces the generic 'no logos' tail",
       "Do not add any logos, certification marks" in pr and pr.endswith(packscene.TAIL.strip()) and "captions, logos, watermarks" not in pr)
expect("side, Real: the picked pack is the only reference; response says library / side",
       rf == [PICKED_URL] and d.get("pack_source") == "library" and d.get("pack_role") == "side" and d.get("pack_used") is True)

for style, role, needle, label in (("vector", "side", "Draw the product pack from the reference image", "Vector"),
                                   ("infographic", "corner", "Draw the product pack from the reference image", "Infographic"),
                                   ("claymation", "side", "Draw the product pack from the reference image", "any non-photo style")):
    st, d, pr, rf = send({**PICK, "pack_role": role}, style=style)
    expect(f"{label}: the pack is illustrated, and never told to be 'reproduced exactly' as a photo",
           needle in pr and "Reproduce it exactly" not in pr)
st, d, pr, rf = send({**PICK, "pack_role": "hero"}, style="product")
expect("Product only, hero: photographic pack, centred hero", "Reproduce it exactly" in pr and "is the hero of the image" in pr)
st, d, pr, rf = send({**PICK, "pack_role": "cta"})
expect("cta: upper two-thirds, sized to a real hand-held pack, true size relative to hands/people, lower third kept clear",
       "upper two-thirds" in pr and "no larger than a real pack held in the hand of an average-built adult" in pr
       and "true, real-life size" in pr and "not enlarged for effect" in pr and "lower third" in pr)
expect("cta: an absolute (hand-independent) size anchor, and a ban on freestanding hero display",
       "roughly the size of a paperback book" in pr and "whether or not a hand is actually touching it" in pr
       and "Never pose it as a freestanding display piece" in pr and "pocket-sized" in pr)
st, d, pr, rf = send({**PICK, "pack_role": "in_use"})
expect("in_use: shown in the action, label to camera", "in the action of the scene" in pr)
st, d, pr, rf = send({**PICK, "pack_role": "corner"}, style="infographic")
expect("corner: a small element in one corner", "one corner of the frame" in pr)

st, d, pr, rf = send({**PICK, "pack_role": "none"})
expect("role none: nothing pack-related attached even though a pack is picked",
       rf == [] and "pack in the reference" not in pr and not d.get("pack_source") and d.get("pack_failed") is False)
st, d, pr, rf = send({**PICK, "pack_role": "sideways"})
expect("an unknown role is ignored: today's wording, unchanged",
       pr.startswith("Generate the next shot of the same film") and "Reuse the EXACT product pack" in pr and d.get("pack_role") == "")
st, d, pr, rf = send(PICK)
expect("no pack_role (Video frames, shot-reference, every other caller): today's prompt, unchanged in shape",
       pr.startswith("Generate the next shot of the same film, reusing the EXACT same people")
       and "Reuse the EXACT product pack from the reference images" in pr
       and pr.endswith("No on-screen text, captions, logos, watermarks or borders.")
       and "The pack in the reference image is the real product" not in pr)

print()
print("when other references are present:")
_CAST_ON[0] = True
st, d, pr, rf = send({**PICK, "pack_role": "side", "use_cast": True})
expect("with a cast frame: keeps the 'same people' opening (there ARE people to reuse) + the new pack wording",
       pr.startswith("Generate the next shot of the same film, reusing the EXACT same people")
       and "The pack in the reference image is the real product" in pr and pr.endswith(packscene.TAIL.strip()) and rf == [CAST_URL, PICKED_URL])
_CAST_ON[0] = False
st, d, pr, rf = send({**PICK, "pack_role": "side", "reference_url": PREV})
expect("with a previous render for continuity: keeps the old opening, still gets the new pack wording, pack kept",
       pr.startswith("Generate the next shot of the same film") and "The pack in the reference image is the real product" in pr
       and rf == [PREV, PICKED_URL])

print()
print("session-only reference photo (pack_reference):")
st, d, pr, rf = send({"pack_reference": PHOTO, "include_pack": False, "pack_role": "side"})
expect("a session photo is attached as the pack, with the new wording",
       rf == [PHOTO] and pr.startswith("Create the image for a marketing post.") and "The pack in the reference image is the real product" in pr)
expect("...and reported as a reference (not a library pack)",
       d.get("pack_source") == "reference" and d.get("pack_used") is False and d.get("pack_role") == "side")
st, d, pr, rf = send({"pack_reference": PHOTO, "include_pack": False, "pack_role": "side"}, mode="general")
expect("Independent mode keeps the person's own reference photo", rf == [PHOTO] and d.get("pack_source") == "reference")
st, d, pr, rf = send({"pack_reference": PHOTO, "include_pack": False})
expect("a reference photo with no role defaults to 'side'", d.get("pack_role") == "side" and "Place the pack to one side" in pr)
_CAST_ON[0] = True
st, d, pr, rf = send({"pack_reference": PHOTO, "include_pack": False, "pack_role": "side", "use_cast": True, "reference_url": PREV})
expect("previous render + reference photo + cast = 3 references; the pack photo is never the one dropped",
       rf == [PREV, PHOTO, CAST_URL], str(len(rf)))
_CAST_ON[0] = False
st, d, pr, rf = send({"pack_reference": PHOTO, "pack_role": "none"})
expect("role none beats a reference photo: nothing attached", rf == [] and not d.get("pack_source"))
st, d, pr, rf = send({"pack_reference": "http://evil/x.png", "pack_role": "side"})
expect("a non-data reference is refused (400) before any image call", st == 400 and not seen_prompts)
st, d, pr, rf = send({"pack_reference": "data:image/png;base64," + "A" * 8_000_001, "pack_role": "side"})
expect("an oversized reference is refused (400) before any image call", st == 400 and not seen_prompts)

print()
print("scene text that asks for the pack's back / nutrition panel (trial T9-T11):")
NUTR = ("Close-up of the pack on a kitchen counter, with its nutrition panel visible so a shopper can read it; "
        "a woman is blurred in the background. Square social image for Facebook.")
st, d, pr, rf = send({**PICK, "pack_role": "hero"}, scene=NUTR)
expect("the request for the nutrition panel is taken out of the scene before it is sent",
       "so a shopper can read it" not in pr and "nutrition panel visible" not in pr and d.get("scene_cleaned") is True)
expect("...the rest of the scene survives",
       "Close-up of the pack on a kitchen counter" in pr and "a woman is blurred in the background" in pr)
expect("...and the wording still forbids a nutrition panel / other pack / printed facts",
       "never its back, its sides, a nutrition panel" in pr and "exactly one pack" in pr and "no nutrition table" in pr.lower())
st, d, pr, rf = send({**PICK, "pack_role": "side"}, scene=SCENE)
expect("a scene that asks for nothing risky is sent exactly as written", SCENE in pr and d.get("scene_cleaned") is False)
st, d, pr, rf = send({**PICK, "pack_role": "in_use"}, scene=NUTR)
expect("pack in use: the scene is not touched", "nutrition panel visible" in pr and d.get("scene_cleaned") is False)
POUR = "A mother opens a pouch of milk and pours it into a glass for her child at the breakfast table."
st, d, pr, rf = send({**PICK, "pack_role": "side"}, scene=POUR)
expect("opening/pouring a pouch is deliberately NOT rewritten (known limit: a second drawn pouch can still appear)",
       POUR in pr and d.get("scene_cleaned") is False)
st, d, pr, rf = send(PICK, scene=NUTR)
expect("no pack_role (every other caller): the scene text is untouched", "nutrition panel visible" in pr and d.get("scene_cleaned") in (None, False))
cs, ch = packscene.clean_scene("A backdrop of rolling fields, with a farmer.", "side")
expect("'backdrop' is not mistaken for 'back of the pack'", ch is False and cs == "A backdrop of rolling fields, with a farmer.")
cs, ch = packscene.clean_scene("Show the ingredients list.", "side")
expect("a scene that is ONLY a risky request falls back to a neutral scene", ch is True and cs == "a bright, uncluttered everyday scene")
cs, ch = packscene.clean_scene("She flips the pack over to show the back of the pouch, smiling.", "hero")
expect("flipping the pack / showing its back is removed too", "back" not in cs and "flips" not in cs and "smiling" in cs)

print()
print("scene text that personalises the pack's own printed artwork (22 Sep, both real carousel concepts):")
FACE1 = ("Present-day close-up of the woman holding the pack, Ramesh's face and '31 years on this street' "
         "printed on it, her expression shifting.")
st, d, pr, rf = send({**PICK, "pack_role": "side"}, scene=FACE1)
expect("a face + text 'printed on it' is taken out of the scene before it is sent",
       "Ramesh's face" not in pr and "printed on it" not in pr and d.get("scene_cleaned") is True)
expect("...the rest of that scene survives", "close-up of the woman holding the pack" in pr.lower())
FACE2 = "A row of three named delivery personnel standing on their own streets, each holding a pack that carries their own face."
cs, ch = packscene.clean_scene(FACE2, "side")
expect("'a pack that carries their own face' is removed too", "face" not in cs and ch is True)
expect("...the setup survives", "A row of three named delivery personnel" in cs)
cs, ch = packscene.clean_scene(FACE1, "in_use")
expect("personalisation is stripped even for role 'in_use' (unlike back/nutrition, this fidelity clash "
       "does not depend on how the pack is held)", "printed on it" not in cs and ch is True)
cs, ch = packscene.clean_scene("A close-up of her smiling face as she holds the pack.", "side")
expect("an ordinary face in the scene (not printed ON the pack) is left alone", ch is False and "smiling face" in cs)

# The photo must go to the model and nowhere else: not the library, not the made ledger, not the disk.
main._record_made = _real_record_made
send({"pack_reference": PHOTO, "include_pack": False, "pack_role": "side"})
main._record_made = lambda *a, **k: None
import made  # noqa: E402
expect("...(the real ledger write really happened, so the scan below is not vacuous)", any(r.get("kind") == "scene_still" for r in made.list_entries()))
_marker_b64 = base64.b64encode(b"SESSION-ONLY PACK PHOTO MARKER")[:16]
leaked = []
for root, _d, names in os.walk(_scratch):
    for n in names:
        try:
            blob = open(os.path.join(root, n), "rb").read()
        except OSError:
            continue
        if b"SESSION-ONLY PACK PHOTO MARKER" in blob or _marker_b64 in blob:
            leaked.append(os.path.join(root, n))
expect("the session photo is not stored anywhere (library, made ledger, disk) -- with the real ledger write on", not leaked, str(leaked))

print()
if failures:
    print(f"{failures} case(s) FAILED")
    sys.exit(1)
print("All pack-choice cases behave.")
