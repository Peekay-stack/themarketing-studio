#!/usr/bin/env python
"""test_library_dedupe.py -- the same file uploaded under a different kind must not come back as the old kind.

Why: 12 Nov, Kumkum pack photos had been filed under Logo; uploading them again as a Pack shot matched the old
Logo row by content, returned it (toast "Pack uploaded and signed off") and the pack picker, which lists only
kind pack, never showed it. Runs library.add against a scratch folder (its directory functions are pointed
there), no key, nothing real touched.

    python tools/test_library_dedupe.py       # exit 0 = every check behaves
"""
from __future__ import annotations

import os
import sys
import tempfile

API = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
sys.path.insert(0, API)
os.chdir(API)

import library  # noqa: E402

scratch = tempfile.mkdtemp(prefix="libdedupe_")
library._dir = lambda: scratch
library._manifest = lambda: os.path.join(scratch, "manifest.json")

fails = []


def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


data = b"\x89PNG\r\n\x1a\n-pretend-pack-photo-"
a = library.add(data, "range", "logo", filename="range.png")
b = library.add(data, "range", "logo", filename="range.png")
check("same bytes, same kind: stored once, the first row comes back", a["id"] == b["id"] and len(library._load()) == 1)
c = library.add(data, "range", "pack", filename="range.png")
check("same bytes, a different kind: a row of the requested kind", c["kind"] == "pack" and c["id"] != a["id"])
check("both rows exist, one per kind", sorted(r["kind"] for r in library._load()) == ["logo", "pack"])
d = library.add(data, "range", "pack", filename="range.png")
check("the pack row is not stored twice either", d["id"] == c["id"] and len(library._load()) == 2)
library.sign_off(c["id"], "t", True)
check("the pack picker's kind sees it once signed off", [r["id"] for r in library.items("pack", signed_only=True)] == [c["id"]])

e = library.add(data, "range", "pack", filename="range.png", brand="Kumkum Beauty")
check("brand A uploading a file already stored for nobody gets its own row, tagged to A", e["brand"] == "Kumkum Beauty" and e["id"] not in (a["id"], c["id"]))
f = library.add(data, "range", "pack", filename="range.png", brand="Other Brand")
check("brand B uploading the SAME file gets its own row, not A's", f["brand"] == "Other Brand" and f["id"] != e["id"])
g = library.add(data, "range", "pack", filename="range.png", brand="Kumkum Beauty")
check("the same brand uploading it again gets its own row back (stored once)", g["id"] == e["id"])
library.sign_off(e["id"], "t", True); library.sign_off(f["id"], "t", True)
check("each brand's picker lists only its own (plus brand-agnostic) pack", {r["id"] for r in library.items("pack", signed_only=True, brand="Other Brand")} == {c["id"], f["id"]})

print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)
