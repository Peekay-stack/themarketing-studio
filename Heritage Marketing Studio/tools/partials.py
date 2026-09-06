#!/usr/bin/env python
"""partials.py — split app.dc.html into small files, and put it back byte-for-byte.

`app.dc.html` is one 8,300-line file. Claude Design works in it as a single Design Component and that
should not change — the file *is* their tool. But a repo holding one 661KB blob makes every diff
unreadable and every merge a guess, so this splits it for the repo and rejoins it for the app.

**It works on the comment banners the file already has.** No sentinels are inserted, nothing is
modified, and there is no marker for anyone to accidentally delete:

    markup :  ^  <!-- ===== NAME ===== -->      (exactly two spaces of indent)
    logic  :  ^  // ===== NAME =====            (inside the <script type="text/x-dc"> block only)

Deeper-indented banners are ignored, so `    <!-- ==== STEP: SCRIPTING ==== -->` inside the video
screen stays where it belongs instead of becoming a top-level file.

**The round trip is byte-identical, and there is a test that proves it** (`test_partials.py`). That
matters more than the split does: a build step that *nearly* reproduces the file is worse than no build
step, because the damage arrives later and looks like someone else's bug. Every part keeps its own
banner line, and joining is plain concatenation of bytes — no re-indentation, no newline translation, no
trailing-newline cleverness.

    python tools/partials.py split           # file  -> parts/
    python tools/partials.py join            # parts/ -> file
    python tools/partials.py verify          # round-trip and diff, changes nothing
    python tools/partials.py status          # what the parts are and how big

Everything is done on bytes. The file is LF-only today; if it ever gains CRLF this still round-trips,
because nothing here interprets a line ending.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "api", "frontend", "app.dc.html")
PARTS = os.path.join(ROOT, "api", "frontend", "parts")
MANIFEST = "manifest.json"

# The <script> that holds the component class. Split rules differ inside it.
_SCRIPT_OPEN = re.compile(rb"^<script[^>]*data-dc-script")
_SCRIPT_CLOSE = re.compile(rb"^</script>\s*$")

# Split anchors. Two spaces of indent exactly — deeper banners are sub-sections, not files.
_MARKUP_BANNER = re.compile(rb"^  <!-- =+\s*(.+?)\s*=+ -->\s*$")
_LOGIC_BANNER = re.compile(rb"^  // =+\s*(.+?)\s*=+\s*$")


def _slug(name: bytes) -> str:
    s = name.decode("utf-8", "replace").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "part"


def _lines(data: bytes) -> list[bytes]:
    """Split keeping the terminators, so joining is exact."""
    return data.splitlines(keepends=True)


def plan(data: bytes) -> list[tuple[str, int, int]]:
    """Where the file divides. Returns [(name, first_line, last_line_exclusive)].

    The region between the script open and close tags uses the JS banner; everything else uses the HTML
    banner. Doing it by region rather than by pattern-union is what stops a `//` comment inside markup —
    or a `<!--` inside a template literal — from ever becoming a split point.
    """
    lines = _lines(data)
    in_script = False
    cuts: list[tuple[int, str]] = []
    for i, raw in enumerate(lines):
        if not in_script and _SCRIPT_OPEN.match(raw):
            in_script = True
            cuts.append((i, "logic-head"))
            continue
        if in_script and _SCRIPT_CLOSE.match(raw):
            in_script = False
            cuts.append((i, "logic-close"))
            continue
        m = (_LOGIC_BANNER if in_script else _MARKUP_BANNER).match(raw)
        if m:
            cuts.append((i, _slug(m.group(1))))

    out: list[tuple[str, int, int]] = []
    if not cuts or cuts[0][0] > 0:
        out.append(("head", 0, cuts[0][0] if cuts else len(lines)))
    for n, (start, name) in enumerate(cuts):
        end = cuts[n + 1][0] if n + 1 < len(cuts) else len(lines)
        out.append((name, start, end))

    # Two banners can carry the same words. Numbering is by position anyway, but a unique name keeps the
    # filenames stable and greppable rather than silently colliding.
    seen: dict[str, int] = {}
    final = []
    for name, a, b in out:
        seen[name] = seen.get(name, 0) + 1
        final.append((f"{name}-{seen[name]}" if seen[name] > 1 else name, a, b))
    return final


def split(src: str = SRC, out_dir: str = PARTS) -> dict:
    data = open(src, "rb").read()
    lines = _lines(data)
    spec = plan(data)
    os.makedirs(out_dir, exist_ok=True)
    for stale in os.listdir(out_dir):
        if stale.endswith(".part") or stale == MANIFEST:
            os.remove(os.path.join(out_dir, stale))

    manifest = {"source": os.path.basename(src), "bytes": len(data), "parts": []}
    for idx, (name, a, b) in enumerate(spec):
        fn = f"{idx:02d}-{name}.part"
        chunk = b"".join(lines[a:b])
        with open(os.path.join(out_dir, fn), "wb") as fh:
            fh.write(chunk)
        manifest["parts"].append({"file": fn, "name": name, "lines": b - a, "bytes": len(chunk)})
    with open(os.path.join(out_dir, MANIFEST), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    return manifest


def join(in_dir: str = PARTS, dest: str | None = None) -> bytes:
    """Concatenate in manifest order. Refuses on a missing part rather than writing a short file."""
    with open(os.path.join(in_dir, MANIFEST), encoding="utf-8") as fh:
        manifest = json.load(fh)
    blobs = []
    for part in manifest["parts"]:
        path = os.path.join(in_dir, part["file"])
        if not os.path.exists(path):
            raise SystemExit(f"partials: {part['file']} is missing — refusing to write a partial file.")
        blob = open(path, "rb").read()
        # A part whose size has changed is fine (somebody edited it); a part that has been emptied
        # almost never is, and joining it silently would delete a screen.
        if not blob and part["bytes"]:
            raise SystemExit(f"partials: {part['file']} is empty but held {part['bytes']} bytes. "
                             f"Refusing — restore it or re-split.")
        blobs.append(blob)
    data = b"".join(blobs)
    if dest:
        tmp = dest + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, dest)
    return data


def verify(src: str = SRC) -> tuple[bool, str]:
    """Split to a scratch directory, rejoin, compare bytes. Touches nothing on disk."""
    original = open(src, "rb").read()
    tmp = tempfile.mkdtemp(prefix="partials_")
    try:
        split(src, tmp)
        rebuilt = join(tmp)
    finally:
        pass
    if rebuilt == original:
        return True, f"byte-identical — {len(original)} bytes through {len(plan(original))} parts"
    # Say exactly where it diverged; "not identical" is useless on a 661KB file.
    n = min(len(original), len(rebuilt))
    at = next((i for i in range(n) if original[i] != rebuilt[i]), n)
    line = original[:at].count(b"\n") + 1
    return False, (f"DIVERGED at byte {at} (line {line}); "
                   f"original {len(original)} bytes, rebuilt {len(rebuilt)}")


def status(src: str = SRC) -> None:
    data = open(src, "rb").read()
    spec = plan(data)
    lines = _lines(data)
    print(f"{os.path.relpath(src, ROOT)} — {len(data):,} bytes, {len(lines):,} lines, "
          f"{len(spec)} parts\n")
    for idx, (name, a, b) in enumerate(spec):
        size = sum(len(x) for x in lines[a:b])
        flag = "  <-- large" if (b - a) > 800 else ""
        print(f"  {idx:02d}  {name:<34} {b - a:>5} lines  {size:>7,} bytes{flag}")


def main(argv: list[str]) -> int:
    cmd = (argv[1] if len(argv) > 1 else "verify").lower()
    if cmd == "split":
        m = split()
        print(f"split into {len(m['parts'])} parts under {os.path.relpath(PARTS, ROOT)}")
        ok, msg = verify()
        print(("  round-trip OK: " if ok else "  ROUND-TRIP FAILED: ") + msg)
        return 0 if ok else 1
    if cmd == "join":
        data = join(PARTS, SRC)
        print(f"joined {len(data):,} bytes -> {os.path.relpath(SRC, ROOT)}")
        return 0
    if cmd == "status":
        status()
        return 0
    if cmd == "verify":
        ok, msg = verify()
        print(("round-trip OK: " if ok else "ROUND-TRIP FAILED: ") + msg)
        return 0 if ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
