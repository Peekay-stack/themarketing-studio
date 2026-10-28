"""mediapurge.py -- retention for the film builder (slice S7, FILM_BUILDER_PLAN.md): how much the media folder holds, and removing the files of takes nobody chose, ON REQUEST ONLY.

Measured 28 Oct 2026 on the local tenant (648 MB): IMAGES are the bulk (`frame-*` 404 MB in 418 files, `still-*` 141 MB), the 21 video clips together are 6.7 MB. So the builder's disk cost is
frame variants first, clips second. Nothing here ever runs on its own.

Safety, in three layers (a delete is the one thing in this app that cannot be undone):
  1. an ALLOWLIST of file names: only `frame-<hex>`, `shot-<hex>` and `chain-<hex>` with an image or mp4 extension, directly inside the media folder. Voice, music, key visuals, trimmed assemble
     clips (`trim-*`, which a produced film may still use), cast references and everything else can never be named, whatever a caller sends;
  2. every saved film is read and what it still uses is KEPT: the chosen frame and clip of every shot, every current storyboard frame, the cast reference, and the source frame of a chosen clip;
  3. the caller decides what to ask for, and a dry run reports what would go and how large it is before anything is removed.
"""
from __future__ import annotations

import json
import os
import re
import shutil

SAFE = re.compile(r"^(frame|shot|chain)-[0-9a-f]{6,}\.(jpg|jpeg|png|webp|mp4)$")
MAX_URLS = 500
_MENTION = re.compile(r"/media/((?:frame|shot|chain)-[0-9a-f]{6,}\.(?:jpg|jpeg|png|webp|mp4))")


def _name(url) -> str:
    """The file name of a served '/media/<name>' path, or '' for anything else (another folder, a full URL, a path with a separator or a dot-dot)."""
    u = str(url or "").strip()
    if not u.startswith("/media/"):
        return ""
    n = u[len("/media/"):]
    return n if (n and "/" not in n and "\\" not in n and ".." not in n) else ""


def usage(media_dir: str) -> dict:
    """What the media folder holds: {files, bytes, by_kind: {kind: {files, bytes}}, disk_free_bytes}. `kind` is the file name's first word (frame, still, shot, vo, bed, kv ...)."""
    by: dict[str, dict] = {}
    files = total = 0
    try:
        names = os.listdir(media_dir)
    except OSError:
        names = []
    for n in names:
        p = os.path.join(media_dir, n)
        try:
            if not os.path.isfile(p):
                continue
            s = os.path.getsize(p)
        except OSError:
            continue
        k = n.split("-")[0].split(".")[0] or "other"
        b = by.setdefault(k, {"files": 0, "bytes": 0})
        b["files"] += 1
        b["bytes"] += s
        files += 1
        total += s
    try:
        free = shutil.disk_usage(media_dir).free
    except OSError:
        free = 0
    return {"files": files, "bytes": total, "by_kind": by, "disk_free_bytes": free}


def in_use(film_dir: str, also_dirs=()) -> set[str]:
    """The media file names that any saved film still uses and that a purge must therefore keep. `also_dirs` are other WORKING stores that point at generated files (the Edit room's saved cuts name each
    beat's clip): every file name they mention is kept too. (The `made` ledger is deliberately NOT one of them: it is a record of everything ever generated, so protecting it would keep every frame
    forever; a purge leaves its entries in place without their file, which the confirmation says.)"""
    keep: set[str] = set()
    for d in also_dirs or ():
        try:
            names = [f for f in os.listdir(d) if f.endswith((".json", ".jsonl"))]
        except OSError:
            continue
        for f in names:
            try:
                text = open(os.path.join(d, f), encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            keep.update(m.group(1) for m in _MENTION.finditer(text))

    def add(u):
        n = _name(u)
        if n:
            keep.add(n)

    try:
        files = [f for f in os.listdir(film_dir) if f.endswith(".json")]
    except OSError:
        files = []
    for f in files:
        try:
            doc = json.load(open(os.path.join(film_dir, f), encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(doc, dict):
            continue
        add(doc.get("cast_ref_url"))
        for v in (doc.get("scene_frames") if isinstance(doc.get("scene_frames"), dict) else {}).values():
            add((v or {}).get("url") if isinstance(v, dict) else None)
        b = doc.get("video_builder") if isinstance(doc.get("video_builder"), dict) else {}
        for layer, chosen in (("frames", "frame_chosen"), ("takes", "chosen")):
            for key, cid in (b.get(chosen) if isinstance(b.get(chosen), dict) else {}).items():
                for t in ((b.get(layer) or {}).get(key) or []):
                    if isinstance(t, dict) and t.get("id") == cid:
                        add(t.get("url"))
                        add(t.get("frame"))                      # the picture a chosen clip was animated from
                        for beat in (t.get("beats") if isinstance(t.get("beats"), list) else []):
                            add((beat or {}).get("url") if isinstance(beat, dict) else None)
    return keep


def purge(media_dir: str, film_dir: str, urls, dry_run: bool = True, also_dirs=()) -> dict:
    """Remove (or, with `dry_run`, only measure) the named media files. Returns {dry_run, deleted: [{url, bytes}], skipped: [{url, reason}], freed_bytes}. `deleted` lists what WAS removed, or what
    WOULD be on a dry run. Anything not on the allowlist or still used by a saved film is skipped with its reason; nothing else is touched."""
    keep = in_use(film_dir, also_dirs)
    deleted, skipped, freed = [], [], 0
    seen: set[str] = set()
    for u in list(urls if isinstance(urls, list) else [])[:MAX_URLS]:
        n = _name(u)
        if not n:
            skipped.append({"url": str(u)[:200], "reason": "not a stored media file"})
        elif n in seen:
            continue
        elif not SAFE.match(n):
            skipped.append({"url": str(u), "reason": "not a generated frame or clip (only those are ever removed)"})
        elif n in keep:
            skipped.append({"url": str(u), "reason": "in use (a film's chosen frame or clip, a current storyboard frame, the cast reference, or a saved Edit-room cut)"})
        else:
            p = os.path.join(media_dir, n)
            if not os.path.isfile(p):
                skipped.append({"url": str(u), "reason": "already gone"})
            else:
                size = os.path.getsize(p)
                if dry_run:
                    deleted.append({"url": str(u), "bytes": size})
                    freed += size
                else:
                    try:
                        os.remove(p)
                        deleted.append({"url": str(u), "bytes": size})
                        freed += size
                    except OSError as e:
                        skipped.append({"url": str(u), "reason": f"could not be removed ({type(e).__name__})"})
        seen.add(n)
    return {"dry_run": bool(dry_run), "deleted": deleted, "skipped": skipped, "freed_bytes": freed}
