"""library.py — the reference library: ground truth the studio is allowed to rely on.

Everything here was uploaded by a person and signed off. **Nothing generated ever lands in this
library.** That rule is the whole point: the moment a model's own output becomes a reference for the
next generation, errors compound silently and there is no longer anything to check against. Pack
shots, the logo, brand books, past films, research — these are facts about the brand, and facts only
enter by upload.

Two things downstream depend on it:

  * image and video work pulls the signed-off pack shot or cast frame as a *reference image*, which
    is the only thing that reliably holds identity (a description and a fixed seed do not).
  * `locked copy` strings are placed verbatim, never generated. Claims, the FSSAI line and the
    campaign lock-up are legal text; a paraphrase is a compliance failure, not a style choice.

Storage is a directory of files plus a JSON manifest — no database, matching the rest of the app.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
import uuid

import tenancy

# SECURITY / DATA INTEGRITY — found in the round-83 audit: this module hardcoded its own directory next
# to the file instead of asking `tenancy`, the only store in the app that did — every tenant on a
# deployment read and wrote the same manifest and files. `copy`-kind items are locked legal claims and
# FSSAI lines per this module's own docstring; those must never cross a brand boundary. `_LEGACY_DIR` is
# kept only so `_migrate_legacy()` can find and move real data that predates this fix — nothing reads or
# writes through it directly once that has run.
_LEGACY_DIR = os.path.join(os.path.dirname(__file__), "library")
_migrated = False


def _dir() -> str:
    """The active tenant's library directory, migrating the old shared one into it on first use."""
    global _migrated
    path = tenancy.dir("library")
    if not _migrated:
        _migrate_legacy(path)
        _migrated = True
    return path


def _migrate_legacy(dest: str) -> None:
    """Move whatever the pre-tenancy shared directory still holds into the active tenant's own.

    One top-level entry (the manifest, each kind subfolder) at a time, never overwriting something
    already at the destination — same non-destructive, idempotent rule `tenancy.migrate()` uses for
    every other store, so a second call (a second tenant, a restart) finds nothing left to move.
    """
    if not os.path.isdir(_LEGACY_DIR) or os.path.abspath(_LEGACY_DIR) == os.path.abspath(dest):
        return
    for name in os.listdir(_LEGACY_DIR):
        src = os.path.join(_LEGACY_DIR, name)
        target = os.path.join(dest, name)
        if os.path.exists(target):
            continue
        shutil.move(src, target)
    try:
        if not os.listdir(_LEGACY_DIR):
            os.rmdir(_LEGACY_DIR)
    except OSError:
        pass


def _manifest() -> str:
    return os.path.join(_dir(), "manifest.json")


# The fixed display-name prefix for anything adopted from generation — computed from `source` at the
# point of approval, not a naming habit any one caller happens to follow (the gap found this round: the
# old "AI-drafted cast #N" label was just a counter one function chose to write, not derived from the
# `source` field the manifest actually stores, so it could drift the moment a different caller adopted
# something with a different naming convention).
APPROVED_LABEL = "TMS Generated · Approved"


# What the library holds. The kind decides where an item is offered downstream, so it is a fixed
# vocabulary rather than a free-text tag.
KINDS = {
    "pack":      "Pack shot — the product as it actually looks on shelf",
    # `pack` assumes packaging — a carton, a bottle, a box. Not every category has one: a garment, an
    # accessory, a device is a `product` instead, referenced the same way (composited or held as a
    # generation reference) for the same reason — the model gets a jacket's cut, fabric and print
    # subtly wrong the same way it gets a carton's label wrong, and drawing it from a description is
    # the failure this whole library exists to prevent, category by category. Deliberately a second
    # kind rather than widening `pack`'s own wording: `pack` still means shelf packaging specifically
    # everywhere the studio already reads it (the POSM pack-gate, the pack-word detector); a fashion
    # brand's garment was never meant to satisfy a check written for a milk carton.
    "product":   "Product shot — the item exactly as it looks, for any category a shelf pack doesn't "
                "fit: a garment, an accessory, a device — anything a shoot needs to reproduce faithfully "
                "rather than describe",
    "logo":      "Logo and lock-up artwork",
    "brandbook": "Brand book, guidelines, tone of voice",
    "film":      "Past film or cutdown made for this brand",
    "graphic":   "Past key visual, print or social artwork",
    "research":  "Consumer research, NeedScope, category or household data",
    "copy":      "Locked copy — claims, mandatories, taglines. Placed verbatim, never generated",
    "cast":      "Approved cast or character reference frame",
    # Sound the brand already owns. A reference read is worth more than any adjective in a prompt:
    # "warm, unhurried" is guesswork, an approved take is the actual target.
    "voice":     "Approved voice — a reference read, or a voice the brand has cleared",
    "music":     "Approved music — a bed, a jingle, or the sonic logo",
    # The two sound kinds a generated film has no way to produce for itself, and the reason its
    # picture can be good and still read as fake. A video model returns silence or per-clip audio that
    # restarts at every cut; there is no model here that knows what a dented steel milk can sounds
    # like against a concrete floor at 5am. That is a recording somebody makes or licenses, so it
    # enters the way every other fact does — by upload.
    #
    # Split into two because they behave differently in a mix, not to be tidy: ambience is a BED that
    # runs under the whole film (room tone, a street, dawn birds), foley is a SPOT placed at one
    # moment (the clank, the pour, the lid). Merging them into one "sound" kind would mean the mixer
    # could not tell which of the two it had been handed.
    "ambience":  "Ambience bed — room tone, a street, a yard at dawn. Runs under the whole film",
    "sfx":       "Foley or spot effect — one sound at one moment: a clank, a pour, a latch",
    # Real people and real footage, which is where quality stops being a prompt problem.
    "actor":     "Actor — photos and clips of the talent, for likeness and casting",
    "plate":     "Background plate — a location or set to composite onto",
}

# Kinds whose value is the media itself rather than a description of it. Used to decide what can be
# handed to a generator as a reference and what can only be read by a person.
MEDIA_KINDS = ("pack", "product", "logo", "graphic", "cast", "actor", "plate", "film", "voice", "music",
               "ambience", "sfx")

# Generated assets live here; anything under these paths is refused on the way in.
_GENERATED = ("/media/", "/renders/", "\\media\\", "\\renders\\")


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


def _safe(name: str) -> str:
    """A filename that survives every filesystem, without losing what the file was called."""
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", (name or "file").strip())[:70].strip("-.")
    return stem or "file"


def _load() -> list[dict]:
    try:
        with open(_manifest(), encoding="utf-8") as fh:
            rows = json.load(fh)
        return rows if isinstance(rows, list) else []
    except (OSError, ValueError):
        return []


def _save(rows: list[dict]) -> None:
    manifest = _manifest()
    os.makedirs(os.path.dirname(manifest), exist_ok=True)
    tmp = manifest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, manifest)          # never leave a half-written manifest behind


# SECURITY — found in the backend audit: `add()` used to keep whatever extension an upload's filename
# carried, with no check at all — `.html`, `.svg`, `.js`, anything — and `/library-file/<kind>/<name>`
# (main.py) serves it back with `FileResponse`, which sets the Content-Type by guessing from that same
# extension. A file uploaded as `x.html` would be served as `text/html` at this app's own origin: a
# stored-XSS path, worse now that real per-user login sessions are the plan for the beta (an XSS here
# can steal that session cookie). This is deliberately an ALLOWLIST of real media/document types this
# library actually needs to hold, not a denylist of "known bad" ones — a denylist only blocks the
# extensions somebody thought of. `.svg` is left out on purpose, unlike `/brand-logo`'s own list: SVG
# can carry an embedded `<script>`, and this function's callers include less-trusted uploads
# (`research`, `brandbook`) that `/brand-logo` never has to accept.
_SAFE_UPLOAD_EXT = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif", ".heic", ".heif", ".bmp", ".ico",
    ".mp4", ".mov", ".webm", ".m4v",
    ".mp3", ".wav", ".m4a", ".ogg", ".aac", ".flac",
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".csv", ".txt",
}


def _bucket(source: str) -> str:
    """Which physical subfolder a row's bytes live under — a permanent classification set once, at
    write time, never moved again. `uploaded` is a person handing the studio a fact from outside;
    everything else (adopted from generation) is `tms-approved` — by the time anything reaches `add()`
    with a non-upload source, a human has already deliberately approved it (see the `/library-adopt`
    route, which is the only other caller). A candidate that is not approved never calls `add()` at
    all — it lives in the `made` ledger instead — so there is no third, in-between bucket to model.
    """
    return "uploaded" if source == "upload" else "tms-approved"


def add(data: bytes, name: str, kind: str, *, filename: str = "", note: str = "", tags: str = "",
        added_by: str = "", source: str = "upload") -> dict:
    """Take a file into the library. Returns the manifest row.

    `source` is recorded rather than assumed: if a generated asset is ever admitted deliberately,
    it is visible as such instead of quietly passing as ground truth — both in the manifest field and
    in which physical bucket (`uploaded/` vs `tms-approved/`) the file lands under, see `_bucket()`.
    """
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r} — expected one of {', '.join(sorted(KINDS))}")
    if not data:
        raise ValueError("empty file")
    lib_dir = _dir()
    bucket = _bucket(source)
    os.makedirs(os.path.join(lib_dir, kind, bucket), exist_ok=True)
    digest = hashlib.sha256(data).hexdigest()
    rows = _load()
    for r in rows:                      # same bytes already here: don't store it twice
        if r.get("sha256") == digest:
            return r
    item_id = uuid.uuid4().hex[:10]
    # Keep the uploaded file's extension even when the display name doesn't carry one — a pack shot
    # stored as "Pure-Milk-500ml-v3" with no .jpg is served without a usable content type and the
    # browser shows a download prompt instead of the image.
    stem = _safe(name)
    ext = os.path.splitext(filename or name)[1][:10]
    # `kind == "copy"` is text (claims, mandatories, taglines) with no real uploaded file behind it —
    # `filename` is never passed for it, so `ext` here is whatever `os.path.splitext` finds in the
    # NOTE TEXT itself, which was never meant to be a file extension and shouldn't be checked as one.
    if kind != "copy" and ext and ext.lower() not in _SAFE_UPLOAD_EXT:
        raise ValueError(f"{ext} is not a file type this library can store.")
    if ext and not stem.lower().endswith(ext.lower()):
        stem += ext
    fname = f"{item_id}-{stem}"
    with open(os.path.join(lib_dir, kind, bucket, fname), "wb") as fh:
        fh.write(data)
    row = {
        "id": item_id, "name": name or fname, "kind": kind, "file": f"{kind}/{bucket}/{fname}",
        "url": f"/library-file/{kind}/{bucket}/{fname}", "bytes": len(data), "sha256": digest,
        "note": note, "tags": [t.strip() for t in (tags or "").split(",") if t.strip()],
        "added": _now(), "added_by": added_by, "source": source,
        # Ground truth is a decision, not an upload. Nothing counts until someone signs it off.
        "signed_off": False, "signed_by": "", "signed_at": "",
    }
    rows.append(row)
    _save(rows)
    return row


def items(kind: str = "", signed_only: bool = False) -> list[dict]:
    rows = _load()
    if kind:
        rows = [r for r in rows if r.get("kind") == kind]
    if signed_only:
        rows = [r for r in rows if r.get("signed_off")]
    return sorted(rows, key=lambda r: (not r.get("signed_off"), r.get("added", "")), reverse=False)


def get(item_id: str) -> dict | None:
    return next((r for r in _load() if r.get("id") == item_id), None)


def sign_off(item_id: str, who: str = "", on: bool = True) -> dict | None:
    rows = _load()
    for r in rows:
        if r.get("id") == item_id:
            r["signed_off"] = bool(on)
            r["signed_by"] = who if on else ""
            r["signed_at"] = _now() if on else ""
            _save(rows)
            return r
    return None


def remove(item_id: str) -> bool:
    rows = _load()
    keep = [r for r in rows if r.get("id") != item_id]
    if len(keep) == len(rows):
        return False
    gone = next(r for r in rows if r.get("id") == item_id)
    try:
        os.remove(os.path.join(_dir(), gone["file"].replace("/", os.sep)))
    except OSError:
        pass                            # the manifest is the record; a missing file is not fatal
    _save(keep)
    return True


def reference_url(kind: str) -> str:
    """The signed-off reference of this kind to hand a generator, or ''.

    Most recent wins: a pack refresh should take over from the version it replaced without anyone
    having to delete the old one.
    """
    rows = [r for r in items(kind, signed_only=True)]
    return rows[-1]["url"] if rows else ""


def shot_references(max_refs: int = 3, want_pack: bool = False, pack_id: str = "",
                    cast_id: str = "", plate_id: str = "") -> dict:
    """The signed-off references a generated shot should carry, in priority order.

    **Identity first, then the product, then place.** A cast or actor frame is the proven channel — it
    holds a face, hair, skin tone and wardrobe across shots in a way no description does. `pack` does
    the same job for the product: this module's own docstring has claimed since it was written that
    "image and video work pulls the signed-off pack shot... as a reference image" — true for the POSM
    cutout path, never true for a storyboard shot until now. Without it, a pack redraws slightly
    differently every render, because a fixed seed and a careful text description still do not hold a
    label's exact type, colour and proportions the way a photograph does. A `plate` does the same job
    for the location and its light, and it is the reason a film shot in one place reads as one place:
    without it, every beat invents its own room and the cut looks like six unrelated films.

    `want_pack` is opt-in, not automatic like cast/plate: most shots in a film do not show the product
    (a classroom, a bedroom), and forcing a pack reference into every one of them would spend a share
    of a three-image cap on shots that have no use for it, and could nudge the model to work a pack
    into a frame that was never meant to have one. The caller decides per shot — see `/scene-still`'s
    keyword check on the shot's own description — or a person names one explicitly via `pack_id`.

    `cast_id`/`plate_id` are `pack_id`'s siblings, added for the same reason `pack_id` was: "most
    recently signed off" is a fine default until a film has more than one cast take or more than one
    location plate on file (a farm-montage beat needs a different plate than the kitchen scenes), at
    which point silently always picking the newest one is wrong for every shot that isn't it, with no
    way to say otherwise. An explicit id wins; either falls back to the same "most recent signed-off"
    default as before when not given, so no existing caller's behaviour changes.

    Ordered because the underlying APIs cap the reference count (Google takes three), so when
    something has to be dropped it should be the least load-bearing thing, not whatever happened to be
    last in a list.

    `plate` has been a library kind since the library existed and **no code path had ever read it**
    until this function was written; the same was true of `pack` for shot generation specifically.
    """
    cast = ""
    if cast_id:
        row = get(cast_id)
        cast = row["url"] if row and row.get("kind") in ("cast", "actor") and row.get("signed_off") else ""
    if not cast:
        cast = reference_url("cast") or reference_url("actor")
    pack = ""
    if want_pack:
        if pack_id:
            row = get(pack_id)
            pack = row["url"] if row and row.get("kind") == "pack" and row.get("signed_off") else ""
        else:
            pack = reference_url("pack")
    plate = ""
    if plate_id:
        row = get(plate_id)
        plate = row["url"] if row and row.get("kind") == "plate" and row.get("signed_off") else ""
    if not plate:
        plate = reference_url("plate")
    refs, kinds = [], []
    if cast:
        refs.append(cast)
        kinds.append("cast")
    if pack:
        refs.append(pack)
        kinds.append("pack")
    if plate:
        refs.append(plate)
        kinds.append("plate")
    dropped = kinds[max_refs:]
    return {
        "refs": refs[:max_refs], "kinds": kinds[:max_refs],
        "cast": cast, "pack": pack, "plate": plate,
        "has_cast": bool(cast), "has_pack": bool(pack), "has_plate": bool(plate),
        "dropped": dropped,
        "why": ("" if (cast and plate and (pack or not want_pack)) else
                "; ".join(x for x in [
                    "" if cast else "no signed-off cast or actor frame — each shot will invent its "
                                    "own face, and the cut will not match",
                    "" if (pack or not want_pack) else
                        (f"no signed-off pack matching id {pack_id!r}" if pack_id else
                         "no signed-off pack shot — this shot's product will be drawn from "
                         "description alone and will drift between renders"),
                    "" if plate else "no signed-off plate — each shot will invent its own location "
                                     "and light, which is what makes separate renders read as "
                                     "separate films",
                ] if x)),
    }


def locked_copy() -> list[dict]:
    """Strings that must be placed exactly as written. Read by the script and super generators."""
    out = []
    for r in items("copy", signed_only=True):
        text = (r.get("note") or "").strip() or r.get("name", "")
        if text:
            out.append({"id": r["id"], "text": text, "name": r.get("name", "")})
    return out


def local_path(rel: str) -> str:
    """Absolute path for a manifest `file` value, refusing anything outside the library."""
    lib_dir = _dir()
    full = os.path.normpath(os.path.join(lib_dir, rel.replace("/", os.sep)))
    root = os.path.normpath(lib_dir)
    return full if full.startswith(root + os.sep) else ""


def summary() -> dict:
    """Counts per kind plus what is missing — the library's own honest status."""
    rows = _load()
    per = {}
    for k in KINDS:
        of_kind = [r for r in rows if r.get("kind") == k]
        per[k] = {"label": KINDS[k], "total": len(of_kind),
                  "signed": sum(1 for r in of_kind if r.get("signed_off"))}
    return {
        "kinds": per,
        "total": len(rows),
        "signed": sum(1 for r in rows if r.get("signed_off")),
        "unsigned": sum(1 for r in rows if not r.get("signed_off")),
        # Said plainly so the gap is visible rather than inferred from empty lists.
        "missing": [KINDS[k] for k, v in per.items() if v["signed"] == 0],
        "generated_admitted": sum(1 for r in rows if r.get("source") != "upload"),
    }
