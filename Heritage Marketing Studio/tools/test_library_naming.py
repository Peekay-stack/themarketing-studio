#!/usr/bin/env python
"""test_library_naming.py -- library item names, and AVIF references.

Why: on 21 Sep two real pack photos went into Memory and showed up under their FILE names
("40359965_1-heritage-noruish-milk.webp", "Heritage milk.avif"): the upload form never sent a name, and there
was no way to rename. The name matters beyond looks -- it is what the pack dropdown shows and what the writer is
told the product is. Also: "Heritage milk.avif" is a format the image API is not known to accept, so an AVIF
reference is converted to PNG on the way out (and nothing else is touched).

Runs the real routes in-process against a scratch data directory. No key, no cost, nothing real touched.

    python tools/test_library_naming.py       # exit 0 = every check behaves
"""
from __future__ import annotations

import base64
import io
import os
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="libname_")
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
import gemini        # noqa: E402
import creative      # noqa: E402
import tenancy       # noqa: E402
from PIL import Image, features  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=True,
                    headers={selfcheck.INTERNAL_HEADER: selfcheck._INTERNAL_KEY})
failures = 0


def check(label, ok, extra=""):
    global failures
    print(f"  {'ok  ' if ok else 'FAIL'} {label}" + (f"   [{extra}]" if extra else ""))
    if not ok:
        failures += 1


def png_bytes(color=(200, 30, 30), size=(8, 8)):
    b = io.BytesIO()
    Image.new("RGB", size, color).save(b, "PNG")
    return b.getvalue()


def add(kind="pack", filename="40359965_1-heritage-noruish-milk.webp", name="", note="", data=None):
    files = [("files", (filename, data or png_bytes(), "image/png"))]
    body = {"kind": kind, "note": note}
    if name:
        body["name"] = name
    r = client.post("/library-add", data=body, files=files)
    return r


# ---- naming on upload --------------------------------------------------------------------------------
r = add(filename="40359965_1-heritage-noruish-milk.webp", data=png_bytes((1, 2, 3)))
item = r.json()["added"][0]
check("no name given -> the file's own name is kept (unchanged behaviour)", item["name"] == "40359965_1-heritage-noruish-milk.webp")
r = add(filename="hm.webp", name="Heritage Nourish+ Milk 500 ml", note="18g protein pouch", data=png_bytes((9, 9, 9)))
named = r.json()["added"][0]
check("a name given -> it becomes the item's name", named["name"] == "Heritage Nourish+ Milk 500 ml")
check("...the stored file still carries its extension so it is served as an image", named["file"].endswith(".webp"))
check("...and the note stays the note", named["note"] == "18g protein pouch")

# ---- rename ------------------------------------------------------------------------------------------
client.post("/library-sign", json={"id": item["id"], "on": True, "who": "You"})
before = library.get(item["id"])
r = client.post("/library-rename", json={"id": item["id"], "name": "  Heritage   Happy Full Cream Milk  "})
row = r.json().get("item", {})
check("rename -> 200 and the name is tidied (trimmed, single spaces)", r.status_code == 200 and row.get("name") == "Heritage Happy Full Cream Milk")
after = library.get(item["id"])
check("rename changes the name and nothing else",
      all(after[k] == before[k] for k in before if k != "name") and after["name"] != before["name"])
check("rename keeps it signed off", after["signed_off"] is True and after["signed_by"] == "You")
check("the new name shows in /library", any(x["id"] == item["id"] and x["name"] == "Heritage Happy Full Cream Milk"
                                            for x in client.get("/library").json()["items"]))
check("rename of an unknown id -> 404", client.post("/library-rename", json={"id": "nope", "name": "x"}).status_code == 404)
check("rename to blank -> 400", client.post("/library-rename", json={"id": item["id"], "name": "   "}).status_code == 400)
check("rename with no name field -> 400", client.post("/library-rename", json={"id": item["id"]}).status_code == 400)
long = client.post("/library-rename", json={"id": item["id"], "name": "x" * 400}).json()["item"]["name"]
check("a very long name is capped at 120 characters", len(long) == 120)
anon = TestClient(main.app, raise_server_exceptions=True)
check("no session -> /library-rename is 401", anon.post("/library-rename", json={"id": item["id"], "name": "x"}).status_code == 401)

# re-uploading the same bytes returns the existing row (why a rename control is needed at all)
again = add(filename="another-name.webp", name="Some other name", data=png_bytes((1, 2, 3))).json()["added"][0]
check("the same bytes uploaded again come back as the existing item (not renamed by re-upload)", again["id"] == item["id"])

# ---- AVIF references ---------------------------------------------------------------------------------
media = tenancy.asset_dir("media")
if features.check("avif"):
    avif_buf = io.BytesIO()
    Image.new("RGBA", (8, 8), (10, 200, 30, 128)).save(avif_buf, "AVIF")
    avif = avif_buf.getvalue()
    with open(os.path.join(media, "pack.avif"), "wb") as fh:
        fh.write(avif)
    mime, b64 = gemini._as_base64("/media/pack.avif")
    out = Image.open(io.BytesIO(base64.b64decode(b64)))
    check("an AVIF reference is sent as PNG", mime == "image/png" and out.format == "PNG")
    check("...with its size and transparency kept", out.size == (8, 8) and "A" in out.getbands())
    mime, b64 = gemini._as_base64("data:image/avif;base64," + base64.b64encode(avif).decode())
    check("an AVIF data URI is converted too", mime == "image/png")
    fal = creative._fal_ref("/media/pack.avif")
    check("the fal path gets a PNG data URI for an AVIF reference", fal.startswith("data:image/png;base64,"))
else:
    print("  skip  AVIF encode not available in this Pillow -- conversion cases not run")

with open(os.path.join(media, "bad.avif"), "wb") as fh:
    fh.write(b"not really an avif")
mime, b64 = gemini._as_base64("/media/bad.avif")
check("an AVIF that cannot be decoded is passed through unchanged (no worse than before)",
      mime == "image/avif" and base64.b64decode(b64) == b"not really an avif")

for ext, fmt, want in (("jpg", "JPEG", "image/jpeg"), ("png", "PNG", "image/png"), ("webp", "WEBP", "image/webp")):
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (5, 5, 5)).save(buf, fmt)
    raw = buf.getvalue()
    with open(os.path.join(media, f"same.{ext}"), "wb") as fh:
        fh.write(raw)
    mime, b64 = gemini._as_base64(f"/media/same.{ext}")
    check(f"{ext.upper()} reference is byte-for-byte unchanged", mime == want and base64.b64decode(b64) == raw)

print()
if failures:
    print(f"{failures} check(s) FAILED")
    sys.exit(1)
print("Library naming and AVIF handling behave.")
