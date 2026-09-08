"""tenancy.py — one place that decides where a document lives.

The portal is being productised: one deployment, several companies, several brands inside each. Nothing
here logs anybody in — that is a later job — but **the storage layout has to be right now**, because
changing it after documents exist means migrating every file and every `brief_id` / `house_id` reference
inside them. The shape is cheap today and expensive in three months.

    api/houses/abc123.json                    <- before
    api/tenants/default/houses/abc123.json    <- after

Every store asks `dir("houses")` instead of building its own path, so switching tenants later is a change
here rather than a change in seven modules.

**Loose files are migrated on first touch, not on import.** A move that happens when Python loads a
module happens during someone's first request, invisibly, and if it half-fails there is nothing to read
in the log. Doing it explicitly per kind means it is attributable and idempotent — a second call finds
nothing to move and says so.

The tenant is resolved from `STUDIO_TENANT` or falls back to `default`. That is deliberately the whole
mechanism: a per-request tenant needs auth to be trustworthy, and a tenant taken from a header without
auth is worse than one tenant, because it looks like isolation and is not.
"""
from __future__ import annotations

import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
TENANTS = os.path.join(ROOT, "tenants")
DEFAULT = "default"

# Every per-tenant document store. Listed rather than discovered so a new kind is a deliberate addition
# and a typo cannot silently create a second home for the same documents.
KINDS = ("briefs", "brands", "houses", "plans", "platforms", "trade", "executions", "shotlists",
         # `shots` was the one store that wrote to a bare `api/shots/` directory and so leaked between
         # companies on a shared deployment. It holds footage of real people with signatures against it,
         # which makes it the worst one to have left unscoped.
         "shots",
         # `cuts` — the approved-film manifest (`cut.py`). Scoped from day one, unlike `shots` above;
         # added deliberately rather than discovered as a gap later.
         "cuts",
         # `pr` — the PR sheet (`pr.py`), campaign-linked and standalone alike. Scoped from day one for
         # the same reason `shots` had to be retrofitted: it will hold named journalists and, later,
         # recall correspondence. Personal data and legally sensitive material are the last things that
         # should leak between companies on a shared deployment.
         "pr",
         # `pr_map` — the media map: outlets and journalists, per brand. A separate kind rather than a
         # field on a PR sheet because a map OUTLIVES the campaigns that use it: a campaign sheet and a
         # recall sheet reach for the same list, and rebuilding it per sheet is how two copies start
         # disagreeing about who covers dairy in Telugu.
         "pr_map",
         # `pr_framework` — what a regulator requires, per jurisdiction and category, ENTERED and
         # confirmed by a client's legal team rather than recalled by a model. Its own store because it
         # is reference data with a review date, not a document about one campaign, and because a
         # recall is run against it.
         "pr_framework",
         # `media_ci` — the competitive picture: the competitor set, what each one spends or merely
         # runs, and the brand's own market share. Per brand and not per plan, for the same reason
         # `pr_map` is: it OUTLIVES the plans built against it, and two plans reading two copies would
         # disagree about the category's size — which silently changes every share computed from it.
         # Some of it is licensed data whose terms restrict redistribution, which is another reason it
         # should never leak across companies on a shared deployment.
         "media_ci",
         # `social_plan` — the geography-wise social campaign, and the first store in this studio that
         # holds MONEY. Scoped for the obvious reason: a budget, a market list and a cost-per-action
         # benchmark are commercially sensitive in a way a vocabulary is not, and a client's CPA is
         # the last number that should be visible to another client on a shared deployment.
         "social_plan",
         # `actuals` — the measurement ledger (audit #9): market share, delivered cost-per-action, any
         # measured-after-the-fact fact a plan or campaign reads at query time. Scoped for the same
         # reason `social_plan` is: these are commercially sensitive real numbers, not vocabulary.
         "actuals",
         # `library` — signed-off ground truth: packs, logos, cast/actor references, and locked legal
         # copy (claims, FSSAI lines). Found unscoped in the round-83 audit — the one store in the whole
         # app that hardcoded its own directory next to the module file instead of asking here, so every
         # tenant on a deployment shared the same manifest and files. Retrofitted the same way `shots`
         # was: a real security/data-integrity gap for a `copy`-kind item specifically, since those are
         # locked legal claims that must never cross a brand boundary.
         "library",
         # `made` — the record of everything generated (`made.py`), the fix for "what got produced is
         # only visible while the browser tab that made it stays open." Per-tenant for the same reason
         # `actuals` is: many screens read it, no single document owns it.
         "made",
         # `learning` — corrections, promoted prompt templates, and approved-work anchors (`learning.py`).
         # Found unscoped in the save/location audit, same shape as `library` before its round-90 fix:
         # hardcoded its own directory next to the module file instead of asking here, so every tenant on
         # a deployment shared one corrections log and one set of promoted templates.
         "learning",
         # `character` — brand characters (`character.py`): the recurring, brand-owned face a
         # segmentation study does not itself settle. Scoped from day one — a character is built for
         # one brand's segments and test 6 of its own skill is "never shared across brands"; the
         # approved reference frame also lands in `library` as a `cast` item, which is already scoped.
         "character")

_SAFE = re.compile(r"[^a-z0-9_-]+")


def tenant() -> str:
    """The active tenant. One, until there is auth to make more than one honest."""
    return slug(os.environ.get("STUDIO_TENANT") or DEFAULT)


def slug(name: str) -> str:
    s = _SAFE.sub("-", str(name or "").strip().lower()).strip("-")
    return s or DEFAULT


def dir(kind: str, who: str = "") -> str:
    """The directory for one kind of document, created if needed."""
    if kind not in KINDS:
        raise ValueError(f"unknown store {kind!r} — add it to tenancy.KINDS deliberately")
    path = os.path.join(TENANTS, slug(who) if who else tenant(), kind)
    os.makedirs(path, exist_ok=True)
    return path


# --------------------------------------------------------------------------------------
# Served assets — a separate vocabulary from `KINDS`, because these are different animals.
# --------------------------------------------------------------------------------------
#
# `KINDS` holds JSON documents that only this backend reads. These three hold BINARY files that a
# browser fetches by URL, and until now they lived in bare `api/renders`, `api/media` and `api/edits`
# — shared across every tenant and mounted as unauthenticated static directories. Which is the exact
# failure `shots` was retrofitted to fix, left in place for three more directories.
#
# The fix has to be non-destructive, because 208 real files already exist with their URLs written into
# stored executions, cuts, shots and platforms. Moving them would break every one of those references.
# So: **new writes are tenant-scoped, reads fall back to the legacy directory.** Same fold-on-read
# shape as `_fold_routes` and `media.migrate` — the old data stays where it is and stays readable, and
# nothing new lands in the shared space again.
#
# The URL space stays flat (`/renders/<name>`), so nothing downstream has to learn a new shape.
ASSET_KINDS = ("renders", "media", "edits")

_ASSET_WHY = {
    "renders": "Rendered films and audio. Footage of real people, cut against a real brand's strategy.",
    "media": "Generated images and video from the model providers, keyed to a brand's own packs.",
    "edits": "Composited and graded masters — the approved cut, which is the most valuable file here.",
}


def asset_dir(kind: str, who: str = "") -> str:
    """Where new assets of this kind are WRITTEN. Tenant-scoped, created if needed."""
    if kind not in ASSET_KINDS:
        raise ValueError(f"unknown asset kind {kind!r} — one of {', '.join(ASSET_KINDS)}")
    path = os.path.join(TENANTS, slug(who) if who else tenant(), kind)
    os.makedirs(path, exist_ok=True)
    return path


def legacy_asset_dir(kind: str) -> str:
    """The pre-tenancy shared directory. Read-only from here on — never written to again."""
    if kind not in ASSET_KINDS:
        raise ValueError(f"unknown asset kind {kind!r} — one of {', '.join(ASSET_KINDS)}")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), kind)


def asset_path(kind: str, name: str, who: str = "") -> str:
    """Resolve one asset name to a path on disk. Tenant first, then the legacy shared directory.

    Returns '' when the file does not exist OR when the name tries to escape its directory. Both are
    the same answer to a caller — the file is not available — and collapsing them means a traversal
    attempt cannot be distinguished from a miss by probing.

    The containment check is the one in `continuity._resolve`, which had it right: normalise, then
    require the result to still sit under the root. `..`, absolute paths and Windows separators are all
    caught by it.
    """
    if kind not in ASSET_KINDS or not name:
        return ""
    rel = str(name).replace("/", os.sep).replace("\\", os.sep).lstrip(os.sep)
    for root in (asset_dir(kind, who), legacy_asset_dir(kind)):
        p = os.path.normpath(os.path.join(root, rel))
        r = os.path.normpath(root)
        if p.startswith(r + os.sep) and os.path.isfile(p):
            return p
    return ""


def asset_state() -> dict:
    """What is scoped and what is still sitting in the shared directories.

    Reported rather than assumed, because the legacy count only goes down when somebody deliberately
    migrates — and a screen that says "isolated" while 208 files sit in a shared folder would be the
    kind of claim this codebase refuses everywhere else.
    """
    out = {"kinds": {}, "legacy_total": 0, "scoped_total": 0}
    for k in ASSET_KINDS:
        legacy = legacy_asset_dir(k)
        scoped = asset_dir(k)
        n_legacy = len([f for f in os.listdir(legacy)
                        if os.path.isfile(os.path.join(legacy, f))]) if os.path.isdir(legacy) else 0
        n_scoped = len([f for f in os.listdir(scoped)
                        if os.path.isfile(os.path.join(scoped, f))]) if os.path.isdir(scoped) else 0
        out["kinds"][k] = {"why_sensitive": _ASSET_WHY[k], "legacy_shared": n_legacy,
                           "tenant_scoped": n_scoped}
        out["legacy_total"] += n_legacy
        out["scoped_total"] += n_scoped
    out["tenant"] = tenant()
    out["all_new_writes_scoped"] = True
    out["legacy_still_shared"] = out["legacy_total"] > 0
    out["what_is_not_done"] = (
        "Files written before this change still sit in the shared directories and are still served "
        "from them, because their URLs are recorded inside stored documents and moving them would "
        "break those references. They are readable by any tenant that knows a filename. Serving now "
        "goes through a route rather than a blind static mount, so an authentication check has "
        "somewhere to live — but there is no authentication yet, and until there is, isolation is "
        "by path only.")
    return out


def tenants() -> list[dict]:
    """Every tenant with anything stored, and how much."""
    out = []
    if not os.path.isdir(TENANTS):
        return out
    for name in sorted(os.listdir(TENANTS)):
        base = os.path.join(TENANTS, name)
        if not os.path.isdir(base):
            continue
        counts = {}
        for kind in KINDS:
            d = os.path.join(base, kind)
            if os.path.isdir(d):
                n = len([f for f in os.listdir(d) if f.endswith(".json")])
                if n:
                    counts[kind] = n
        out.append({"tenant": name, "documents": counts,
                    "total": sum(counts.values()), "active": name == tenant()})
    return out


def migrate(kind: str, legacy: str | None = None) -> dict:
    """Move a pre-tenancy directory into the active tenant. Idempotent.

    Only moves `.json` files, and **never overwrites**: a name that already exists in the destination is
    left alone and reported. Silently clobbering somebody's house because two files share an id is the
    one outcome worth writing extra code to avoid.
    """
    src = legacy or os.path.join(ROOT, kind)
    dest = dir(kind)
    if not os.path.isdir(src) or os.path.abspath(src) == os.path.abspath(dest):
        return {"kind": kind, "moved": 0, "skipped": 0, "note": "nothing to migrate"}
    moved = skipped = 0
    for f in sorted(os.listdir(src)):
        if not f.endswith(".json"):
            continue
        target = os.path.join(dest, f)
        if os.path.exists(target):
            skipped += 1
            continue
        shutil.move(os.path.join(src, f), target)
        moved += 1
    # Remove the old directory only when it is genuinely empty, so a partial migration stays visible.
    try:
        if not os.listdir(src):
            os.rmdir(src)
    except OSError:
        pass
    return {"kind": kind, "moved": moved, "skipped": skipped,
            "note": f"{moved} moved, {skipped} left in place (name already taken)" if skipped
                    else f"{moved} moved"}


def migrate_all() -> list[dict]:
    """Called once at startup. Reports per kind so a half-done move is attributable."""
    return [migrate(k) for k in KINDS]
