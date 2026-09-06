"""shots.py — the shot list for a live-action shoot, and the gate footage passes through.

**A shot is a row in a shot list first, and a composite second.** That is the correction this module
carries. The earlier version modelled a shot as a *composite recipe* — footage plus plate plus key
settings — because the compositor was the only thing that made one. But the screen people actually use
plans a shoot: numbered rows with a slug, an action, talent, a location and a length, which then have
real footage attached, a frame pulled, and a signature put against them. The recipe is one thing that
can happen to a row, not what a row is.

Getting that backwards cost work. `/shot-attach` took a scene *number* and threw away the uploaded take
entirely; `/shot-sign` read an `on` flag defaulting to true, so asking it to clear a signature re-signed
it. Both were shapes invented here rather than taken from the screen.

    planned  ──attach a take──►  shot  ──sign it──►  signed  ──►  the compositor
                                  │                    │
                            pull a still          a recompose clears the
                            from the take         signature, by definition

**State is derived, never stored.** `signed` makes it signed, else `take` makes it shot, else planned.
Two places computing that from one field cannot disagree; two places storing it will. The client derives
it the same way and this module deliberately does not send a `state` field for it to argue with.

**A signature is a name and a time, or it is not a signature.** This is footage of real people, usually
paid talent, and an unsigned shot cannot enter a film. So `sign` refuses an unattributable signature
rather than writing `"unattributed"` — a placeholder in that field is worse than a refusal, because it
looks like the gate was passed. The stored studio manager wins over whatever a client sends, since a
client-side name is a client-side truth and this one has to hold up later.

**Signed with no still is worth flagging.** It has passed the gate and still cannot be used: the
compositor keys against a frame, not footage.
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid

import tenancy

# Tenant-scoped, like every other store. The old module wrote to a bare `api/shots/` directory and so
# was the one store that leaked between companies on a shared deployment.
SHOTS_DIR = tenancy.dir("shots")
MANIFEST = os.path.join(SHOTS_DIR, "manifest.json")

# What the shot-list table plans, before any footage exists.
PLAN_FIELDS = ("no", "slug", "action", "talent", "location", "length")


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


def _load() -> list[dict]:
    try:
        with open(MANIFEST, encoding="utf-8") as fh:
            rows = json.load(fh)
        return [_migrate(r) for r in rows] if isinstance(rows, list) else []
    except (OSError, ValueError):
        return []


def _save(rows: list[dict]) -> None:
    os.makedirs(SHOTS_DIR, exist_ok=True)
    tmp = MANIFEST + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, MANIFEST)


def _migrate(r: dict) -> dict:
    """Bring a row written by the old model up to the current shape, without inventing anything.

    Rows from before shots were scoped to an execution get `execution: None` and
    `predates_scoping: True`. They are **not** back-filled onto whatever execution happens to be open —
    a shoot silently adopted by the wrong piece of work is worse than one sitting visibly unattached, and
    the screen can label these so somebody moves them deliberately.
    """
    r.setdefault("id", uuid.uuid4().hex[:10])
    for f in PLAN_FIELDS:
        r.setdefault(f, "" if f != "no" else 0)
    r.setdefault("filename", "")
    r.setdefault("still", "")
    r.setdefault("still_pending", False)
    r.setdefault("history", [])
    r.setdefault("recompose_note", "")
    r.setdefault("created", _now())
    r.setdefault("scene", 0)           # 0 = not standing in for any film scene
    r.setdefault("recipe", {})         # populated only once the compositor has built this shot
    r.setdefault("ref", "")            # a reference frame for the crew — never a take
    r.setdefault("takes", [])          # [{n, url, at}] the log from set
    r.setdefault("selected_take", 0)   # which take number is the keeper, 0 = none picked

    # `shotlist.py` stored `take` as a take NUMBER and `state` as a stored string. Both are folded in
    # here: an integer `take` was a count, not footage, so it becomes the selection and the log.
    if isinstance(r.get("take"), int):
        n = int(r["take"] or 0)
        r["take"] = ""
        if n:
            r["selected_take"] = r["selected_take"] or n
            if not r["takes"]:
                r["takes"] = [{"n": i, "url": "", "at": r.get("edited") or r.get("created") or _now()}
                              for i in range(1, n + 1)]
    if r.get("state") in ("selected",) and not r.get("selected_take"):
        r["selected_take"] = max([t.get("n", 0) for t in r["takes"]] or [1])
    r.pop("state", None)               # derived now — see state_of / stage_of

    if "execution" not in r:
        r["execution"] = None
        r["predates_scoping"] = True

    # The old model's `url` was the composited output and is the closest thing it had to a take.
    if "take" not in r:
        r["take"] = r.get("url") or ""

    # `signed_off`/`signed_by`/`signed_at` -> `signed: {who, at}` or None. A row that was signed with no
    # name recorded keeps its signature but is marked, rather than being silently un-signed or given a
    # fabricated author.
    if "signed" not in r:
        if r.get("signed_off"):
            r["signed"] = {"who": r.get("signed_by") or "", "at": r.get("signed_at") or "",
                           "unattributed": not (r.get("signed_by") or "").strip()}
        else:
            r["signed"] = None
    return r


def state_of(row: dict) -> str:
    """Derived, never stored. The client derives it identically and nothing sends it.

    Three values, because that is what the screen derives: `signed` → `shot` → `planned`. Kept separate
    from `stage` below on purpose — this one has to agree with the client exactly, so it does not gain
    values just because production has more of them.
    """
    if row.get("signed"):
        return "signed"
    return "shot" if str(row.get("take") or "").strip() else "planned"


# The production lifecycle, which is longer than the three states the screen shows. This is the half that
# came from `shotlist.py` when the two modules were folded together: a shoot logs take 1, take 2, take 3
# and then somebody picks one, and none of that fits in "has footage / does not".
#
# Reported as `stage`, never as `state`. The screen owns `state` and derives it itself; if this sent five
# values under that name the two would disagree the first time somebody logged a take.
STAGES = ("planned", "briefed", "shot", "selected", "signed")


def stage_of(row: dict) -> str:
    """Where this shot is in the shoot. Derived, like `state`."""
    if row.get("signed"):
        return "signed"
    if row.get("selected_take"):
        return "selected"
    if row.get("takes") or str(row.get("take") or "").strip():
        return "shot"
    # Briefed means a crew could shoot it: something happens in it, and there is a frame to match.
    if str(row.get("action") or "").strip() and str(row.get("ref") or "").strip():
        return "briefed"
    return "planned"


# --- reading ------------------------------------------------------------------------------------

def items(execution: str | None = None, signed_only: bool = False) -> list[dict]:
    """The shot list for one execution.

    `execution=None` means **the unattached shoot** — the rows that belong to no execution — not every
    row in the store. That is the answer to the scoping question: a shot list is a shoot, a shoot belongs
    to a piece of work, and "everything" is never a shoot. Pass `execution="*"` for the whole store,
    which only the migration report and the summary want.
    """
    rows = _load()
    if execution != "*":
        want = (execution or "").strip() or None
        rows = [r for r in rows if (r.get("execution") or None) == want]
    if signed_only:
        rows = [r for r in rows if r.get("signed")]
    rows = sorted(rows, key=lambda r: (int(r.get("no") or 0), r.get("created", "")))
    # `stage` on every row, computed here and not stored. The screen derives the three-value `state`
    # itself and should keep doing so, but the five-value production lifecycle has one more input than
    # `state` does — a selected take — and a row with a keeper chosen was showing as PLANNED next to a
    # strip that counted it as selected. Sending it means there is one answer rather than two.
    return [{**r, "stage": stage_of(r)} for r in rows]


def get(shot_id: str) -> dict | None:
    return next((r for r in _load() if r.get("id") == shot_id), None)


def summary(execution: str | None = None) -> dict:
    """Counts the header strip reads, so the client does not have to total them itself.

    Sent on every mutating response as well, because the client asked for one source for these — two
    places counting is two places that can disagree after a failed request.
    """
    rows = items(execution)
    signed = [r for r in rows if r.get("signed")]
    withtake = [r for r in rows if str(r.get("take") or "").strip()]
    return {
        "total": len(rows),
        "planned": sum(1 for r in rows if state_of(r) == "planned"),
        "shot": sum(1 for r in rows if state_of(r) == "shot"),
        "signed": len(signed),
        "with_take": len(withtake),
        # The two states worth surfacing rather than counting: a signature with no frame behind it, and
        # footage nobody has approved.
        "signed_without_still": sum(1 for r in signed if not str(r.get("still") or "").strip()),
        "take_unsigned": sum(1 for r in withtake if not r.get("signed")),
        "predates_scoping": sum(1 for r in rows if r.get("predates_scoping")),
    }


# --- writing ------------------------------------------------------------------------------------

def add(execution: str | None = None, **fields) -> dict:
    """A new planned row. Numbered after the last one in its own shoot."""
    rows = _load()
    mine = [r for r in rows if (r.get("execution") or None) == ((execution or "").strip() or None)]
    row = {"id": uuid.uuid4().hex[:10],
           "execution": (execution or "").strip() or None,
           "no": int(fields.get("no") or (max([int(r.get("no") or 0) for r in mine] or [0]) + 1)),
           "slug": str(fields.get("slug") or "").strip(),
           "action": str(fields.get("action") or "").strip(),
           "talent": str(fields.get("talent") or "").strip(),
           "location": str(fields.get("location") or "").strip(),
           "length": str(fields.get("length") or "").strip(),
           "take": "", "filename": "", "still": "", "still_pending": False,
           "signed": None, "history": [], "recompose_note": "",
           "created": _now()}
    rows.append(row)
    _save(rows)
    return row


def update(shot_id: str, fields: dict) -> dict | None:
    """Edit the planned columns. Cannot touch take, still or signature — those have their own doors."""
    rows = _load()
    for r in rows:
        if r.get("id") == shot_id:
            for f in PLAN_FIELDS:
                if f in fields:
                    r[f] = int(fields[f] or 0) if f == "no" else str(fields[f] or "").strip()
            _save(rows)
            return r
    return None


def attach(shot_id: str, url: str, filename: str = "") -> dict | None:
    """Attach real footage to a planned shot.

    Takes the **url and filename of the uploaded take**, which is what the screen has after the upload.
    The previous signature is the one thing this must clear: what was approved is not what is here now,
    and a signature that survives its footage being replaced approves footage nobody looked at.
    """
    url = str(url or "").strip()
    if not url:
        return None
    rows = _load()
    for r in rows:
        if r.get("id") == shot_id:
            if r.get("signed"):
                r["history"].append({"at": _now(), "what": "take replaced, signature withdrawn",
                                     "was": r.get("filename") or r.get("take") or ""})
            r["take"] = url
            r["filename"] = str(filename or "").strip() or os.path.basename(url)
            r["still"] = ""            # the old frame belonged to the old take
            r["still_pending"] = False
            r["signed"] = None
            _save(rows)
            return r
    return None


def set_still(shot_id: str, url: str, pending: bool = False) -> dict | None:
    rows = _load()
    for r in rows:
        if r.get("id") == shot_id:
            r["still"] = str(url or "").strip()
            r["still_pending"] = bool(pending)
            _save(rows)
            return r
    return None


def sign(shot_id: str, who: str = "") -> tuple[dict | None, str, int]:
    """Sign a take off. Returns (row, error, http_status).

    **Refuses rather than writing a placeholder.** An unattributable signature is not a signature, and
    `"unattributed"` in this field reads as the gate having been passed. It is also refused when there is
    no take, because a signature is against footage and there is none to be against.

    The status comes back from here rather than being reconstructed by the caller from which values are
    None — a missing shot is a 404 and an unsignable one is a 400, and working that out at the route left
    "there is no take yet" answering 404, which reads as the shot not existing.
    """
    who = str(who or "").strip()
    if not who:
        return None, ("A signature needs a name against it. Set the studio manager in Studio settings, "
                      "or say who is signing — this is footage of real people and an unattributed "
                      "sign-off is not one."), 400
    rows = _load()
    for r in rows:
        if r.get("id") == shot_id:
            if not str(r.get("take") or "").strip():
                return None, "There is no take on this shot yet, so there is nothing to sign off.", 400
            r["signed"] = {"who": who, "at": _now()}
            r["history"].append({"at": _now(), "what": f"signed off by {who}"})
            _save(rows)
            return r, "", 200
    return None, "No such shot.", 404


def unsign(shot_id: str) -> dict | None:
    """Withdraw a signature. Separate from `sign` on purpose — no flag to get the wrong way round."""
    rows = _load()
    for r in rows:
        if r.get("id") == shot_id:
            if r.get("signed"):
                r["history"].append({"at": _now(), "what": "signature withdrawn",
                                     "was": (r["signed"] or {}).get("who", "")})
            r["signed"] = None
            _save(rows)
            return r
    return None


def note_recompose(shot_id: str, note: str) -> dict | None:
    """Record a recompose direction and clear the signature it invalidates.

    The note is a direction for the rebuild — *"she is too central, give me the left third"* — so the
    caller feeds it to the compositor. It is stored as well, because a recompose nobody can explain later
    is a mystery in the file.
    """
    rows = _load()
    for r in rows:
        if r.get("id") == shot_id:
            note = str(note or "").strip()
            r["recompose_note"] = note
            r["signed"] = None
            r["still_pending"] = True
            r["history"].append({"at": _now(),
                                 "what": "recomposed" + (f": {note}" if note else ""),
                                 })
            _save(rows)
            return r
    return None


def remove(shot_id: str) -> bool:
    rows = _load()
    keep = [r for r in rows if r.get("id") != shot_id]
    if len(keep) == len(rows):
        return False
    _save(keep)
    return True


# --- on set: the take log, the selection, the reference frame -----------------------------------

def log_take(shot_id: str, n: int | None = None, url: str = "") -> tuple[dict | None, int]:
    """Record that a take was shot. Returns (row, take number).

    Takes are numbered because a shoot numbers them, and the number is what a crew says out loud. `url` is
    optional — a take can be logged on set long before the file is anywhere near this machine, and a log
    that refuses to record what happened until the footage arrives is a log nobody keeps.
    """
    rows = _load()
    for r in rows:
        if r.get("id") != shot_id:
            continue
        nums = [int(t.get("n") or 0) for t in r["takes"]]
        num = int(n) if n else (max(nums or [0]) + 1)
        hit = next((t for t in r["takes"] if int(t.get("n") or 0) == num), None)
        if hit:
            if url:
                hit["url"] = url
            hit["at"] = _now()
        else:
            r["takes"].append({"n": num, "url": str(url or ""), "at": _now()})
        r["takes"].sort(key=lambda t: int(t.get("n") or 0))
        r["edited"] = _now()
        _save(rows)
        return r, num
    return None, 0


def select_take(shot_id: str, n: int | None = None) -> tuple[dict | None, str]:
    """Mark the take that will be used, and attach its footage if the log has any.

    A shot with no logged take cannot be selected: selecting footage nobody shot is how a cut ends up
    referencing something that does not exist. Selecting also **clears any signature**, for the same
    reason attaching does — what was approved was a different take.
    """
    rows = _load()
    for r in rows:
        if r.get("id") != shot_id:
            continue
        if not r["takes"]:
            return None, ("No takes are logged on this shot, so there is nothing to select. Log a take "
                          "first — selecting footage nobody shot is how a cut references something that "
                          "does not exist.")
        num = int(n) if n else max(int(t.get("n") or 0) for t in r["takes"])
        hit = next((t for t in r["takes"] if int(t.get("n") or 0) == num), None)
        if not hit:
            return None, f"There is no take {num} on this shot."
        if r.get("selected_take") != num and r.get("signed"):
            r["history"].append({"at": _now(), "what": f"take {num} selected, signature withdrawn"})
            r["signed"] = None
            r["still"] = ""
        r["selected_take"] = num
        if hit.get("url"):
            r["take"] = hit["url"]
            r["filename"] = r.get("filename") or os.path.basename(hit["url"])
        r["edited"] = _now()
        _save(rows)
        return r, ""
    return None, "No such shot."


def set_reference(shot_id: str, url: str) -> dict | None:
    """A reference frame for the crew — what the shot should look like.

    Explicitly a *reference* and never a take. This screen films real footage; an image generated here is
    a mood-board entry, is not admissible to the library, and cannot become the thing that gets signed.
    """
    rows = _load()
    for r in rows:
        if r.get("id") == shot_id:
            r["ref"] = str(url or "")
            r["edited"] = _now()
            _save(rows)
            return r
    return None


# --- planning from the approved script ----------------------------------------------------------

def plan_from(script: list | None, idea: dict | None, execution: str | None = None) -> list[dict]:
    """Derive a first shot list. From the approved script if there is one, otherwise the platform.

    **Nothing is invented.** Talent, location and length come back empty because nobody has decided them,
    and an empty cell that says so is worth more than a plausible one somebody has to check. A fabricated
    location on a call sheet sends a crew to the wrong place.
    """
    made: list[dict] = []
    rows = [r for r in (script or []) if isinstance(r, dict)]
    if rows:
        for i, r in enumerate(rows, 1):
            visual = str(r.get("visual") or r.get("desc") or "").strip()
            made.append(add(execution, no=i,
                            slug=str(r.get("title") or "").strip() or _slug_from(visual) or f"Scene {i}",
                            action=visual, length=str(r.get("tc") or "").strip()))
        return made

    routes = (idea or {}).get("routes") or {}
    beats = [(k, str(v).strip()) for k, v in routes.items() if str(v or "").strip()]
    if beats:
        for i, (k, text) in enumerate(beats, 1):
            made.append(add(execution, no=i, slug=str(k).replace("_", " ").title(), action=text))
        return made

    line = str((idea or {}).get("line") or (idea or {}).get("idea") or "").strip()
    if line:
        return [add(execution, no=1, slug="The platform, once", action=line)]
    return []


def _slug_from(text: str) -> str:
    words = re.findall(r"[A-Za-z']+", text)[:4]
    return " ".join(words).capitalize() if words else ""


def handoff(execution: str | None = None, ids: list[str] | None = None) -> tuple[list[dict], str]:
    """What goes to the compositor. Signed takes, or the named ones if they are signed.

    Nothing is "sent" — this records that a handoff happened and returns the rows. The gate is unchanged:
    an unsigned shot cannot be handed over, because the signature is the only thing standing between
    footage of a real person and a delivered master.
    """
    rows = items(execution)
    if ids:
        want = set(ids)
        chosen = [r for r in rows if r["id"] in want]
        unsigned = [r for r in chosen if not r.get("signed")]
        if unsigned:
            names = ", ".join(f"{r.get('slug') or r.get('no')}" for r in unsigned)
            return [], (f"These are not signed off, so they cannot be handed over: {names}. "
                        f"A signature is what stands between footage of a real person and a master.")
    else:
        chosen = [r for r in rows if r.get("signed")]
    if not chosen:
        return [], ("Nothing is signed off yet. The compositor takes the signed takes, so until one is "
                    "signed there is nothing to hand over.")
    all_rows = _load()
    for r in all_rows:
        if r["id"] in {c["id"] for c in chosen}:
            r["history"].append({"at": _now(), "what": "handed to the compositor"})
    _save(all_rows)
    return for_compositor_rows(chosen), ""


def status(execution: str | None = None) -> dict:
    """The shoot's own status, in the shape every other status payload in the app uses."""
    rows = items(execution)
    return {"execution": (execution or "") or None,
            "shots": rows, "total": len(rows),
            "states": list(STAGES), "stages": list(STAGES),
            "by_stage": {s: sum(1 for r in rows if stage_of(r) == s) for s in STAGES},
            "summary": summary(execution),
            "findings": findings(execution)}


# --- the compositor: a recipe is something a shot HAS ------------------------------------------
#
# This is where the two models meet. The compositor produces a keyed clip from a take, a plate and a set
# of key settings, and that recipe has to be kept: someone asks for the plate to change and you either
# have the settings or you match it again by eye against the shot next to it. But the recipe is not what a
# shot *is* — it is one thing that can happen to a row in the shot list. So it is nested under `recipe`,
# and the row stays the row.

def record(*, url: str, footage: str, plate: str, settings: dict, green_left: float,
           probe: dict | None = None, label: str = "", scene: int = 0,
           execution: str | None = None, shot_id: str = "") -> dict:
    """Keep a composited shot together with the recipe that produced it.

    Updates the existing row when `shot_id` is given — a recompose is the same shot, not a new one, and
    creating a second row would leave the old signature attached to superseded footage. Otherwise adds a
    row, for a composite built without a planned shot behind it.
    """
    recipe = {"footage": footage, "plate": plate,
              "settings": {"key": settings.get("key", ""),
                           "similarity": settings.get("similarity", 0),
                           "blend": settings.get("blend", 0)},
              "green_left": green_left, "probe": probe or {}, "at": _now()}
    rows = _load()
    for r in rows:
        if shot_id and r.get("id") == shot_id:
            r["take"] = url
            r["filename"] = label or r.get("filename") or os.path.basename(url)
            r["recipe"] = recipe
            r["still"] = ""             # the frame belonged to the previous composite
            r["still_pending"] = False
            r["signed"] = None          # a rebuild is not what was approved
            if scene:
                r["scene"] = int(scene)
            r["history"].append({"at": _now(), "what": "recomposited, signature withdrawn"})
            _save(rows)
            return r

    row = _migrate({
        "id": uuid.uuid4().hex[:10],
        "execution": (execution or "").strip() or None,
        "no": max([int(r.get("no") or 0) for r in rows] or [0]) + 1,
        "slug": label or "shot", "action": "", "talent": "", "location": "", "length": "",
        "take": url, "filename": label or os.path.basename(url),
        "still": "", "still_pending": False, "signed": None,
        "recipe": recipe, "scene": int(scene or 0),
        "history": [{"at": _now(), "what": "composited"}], "recompose_note": "",
        "created": _now(),
    })
    row.pop("predates_scoping", None)   # born scoped, even when the scope is None
    rows.append(row)
    _save(rows)
    return row


def for_scene(no: int) -> dict | None:
    """The signed live-action shot standing in for this film scene, if there is one.

    Signed only, on purpose: an unsigned shot is invisible to the render rather than silently included.
    That is the gate doing its job, and it is the reason the render cannot quietly ship footage of a
    person nobody cleared.
    """
    for r in _load():
        if int(r.get("scene") or 0) == int(no) and r.get("signed"):
            return r
    return None


def set_scene(shot_id: str, scene: int) -> dict | None:
    """Point a shot at a film scene, or at 0 to detach it.

    One scene, one live-action shot: attaching a second detaches the first, because two sources for the
    same beat is the kind of ambiguity that only shows up in the finished master.
    """
    rows = _load()
    hit = None
    for r in rows:
        if r.get("id") == shot_id:
            hit = r
        elif scene and int(r.get("scene") or 0) == int(scene):
            r["scene"] = 0
    if not hit:
        return None
    hit["scene"] = int(scene or 0)
    _save(rows)
    return hit


# --- the compositor's handoff -------------------------------------------------------------------

def for_compositor_rows(rows: list[dict]) -> list[dict]:
    """The handoff shape for a given set of rows."""
    return [{"id": r["id"], "no": r.get("no"), "slug": r.get("slug", ""),
             "action": r.get("action", ""), "length": r.get("length", ""),
             "take": r.get("take", ""), "filename": r.get("filename", ""),
             "still": r.get("still", ""), "signed": r.get("signed"),
             "selected_take": r.get("selected_take") or 0, "location": r.get("location", "")}
            for r in rows]


def for_compositor(execution: str | None = None) -> list[dict]:
    """Signed takes only, each carrying the frame the compositor keys against.

    Signed-only is the gate doing its job: an unsigned shot is invisible here rather than silently
    included. `still` comes with it because the compositor keys against a frame, not footage, and
    `slug`, `action` and `length` because somebody keying needs to know what they are looking at and how
    long it runs.
    """
    return for_compositor_rows(items(execution, signed_only=True))


def findings(execution: str | None = None) -> list[dict]:
    """What is wrong with this shoot, in the same shape as every other findings list in the app."""
    out = []
    for r in items(execution):
        name = f"Shot {r.get('no') or '?'}" + (f" — {r['slug']}" if r.get("slug") else "")
        if r.get("signed") and not str(r.get("still") or "").strip():
            out.append({"level": "blocking", "layer": "shots", "id": r["id"],
                        "detail": f"{name} is signed off but has no still. It has passed the gate and "
                                  f"still cannot be used — the compositor keys against a frame, not "
                                  f"footage. Pull a still from the take."})
        if (r.get("signed") or {}).get("unattributed"):
            out.append({"level": "blocking", "layer": "shots", "id": r["id"],
                        "detail": f"{name} carries a signature with no name against it, from before "
                                  f"sign-offs were attributed. Withdraw it and sign it again."})
        if str(r.get("take") or "").strip() and not r.get("signed"):
            out.append({"level": "open", "layer": "shots", "id": r["id"],
                        "detail": f"{name} has footage nobody has approved, so the render will skip it."})
        if r.get("predates_scoping"):
            out.append({"level": "open", "layer": "shots", "id": r["id"],
                        "detail": f"{name} predates shot lists belonging to an execution. Move it to "
                                  f"the shoot it was part of."})
        # Carried over from the shot-list half: these are about the shoot rather than the gate.
        if not str(r.get("action") or "").strip():
            out.append({"level": "open", "layer": "shots", "id": r["id"],
                        "detail": f"{name}: nothing happens in it yet."})
        if r.get("selected_take") and not str(r.get("location") or "").strip():
            out.append({"level": "open", "layer": "shots", "id": r["id"],
                        "detail": f"{name} has a selected take with no location recorded — the edit will "
                                  f"not know where it came from."})
        if r.get("takes") and not r.get("selected_take"):
            n = len(r["takes"])
            out.append({"level": "open", "layer": "shots", "id": r["id"],
                        "detail": f"{name} has {n} take{'s' if n != 1 else ''} logged and none selected. "
                                  f"Pick the keeper before the shoot is struck and nobody remembers."})
    if not items(execution):
        out.append({"level": "empty", "layer": "shots", "detail": "No shots planned yet."})
    elif not [r for r in items(execution) if r.get("signed")]:
        out.append({"level": "open", "layer": "shots",
                    "detail": "Nothing is signed off yet. The compositor takes the signed takes, so "
                              "until one is signed there is nothing to hand over."})
    return out


# --- folding the old shot-list documents in -----------------------------------------------------

def migrate_shotlists() -> dict:
    """Fold `shotlists/*.json` documents into flat rows. Idempotent; never runs twice on a document.

    The two modules modelled the same thing from opposite ends — one planned a shoot and logged takes by
    number, the other attached footage and put a signature against it. Keeping both meant two stores, two
    findings lists and two ideas of what a shot is, and the screen could only ever see one of them.

    A document becomes rows carrying its `execution`, and is left on disk renamed `.folded` rather than
    deleted: this is somebody's shoot, and an unreviewable migration of it is not worth the tidiness.
    """
    src = tenancy.dir("shotlists")
    moved = docs = 0
    if not os.path.isdir(src):
        return {"documents": 0, "rows": 0, "note": "no shot-list documents"}
    existing = {r.get("folded_from") for r in _load() if r.get("folded_from")}
    for f in sorted(os.listdir(src)):
        if not f.endswith(".json"):
            continue
        path = os.path.join(src, f)
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        if not isinstance(doc, dict) or doc.get("id") in existing:
            continue
        ex = (doc.get("execution") or "").strip() or None
        rows = _load()
        for s in doc.get("shots") or []:
            row = _migrate(dict(s))
            row["execution"] = ex
            row["folded_from"] = doc.get("id")
            row.pop("predates_scoping", None)   # it had an execution, so it was scoped
            rows.append(row)
            moved += 1
        _save(rows)
        docs += 1
        try:
            os.replace(path, path + ".folded")
        except OSError:
            pass
    return {"documents": docs, "rows": moved,
            "note": f"{docs} shot-list document(s) folded into {moved} row(s)" if docs
                    else "nothing to fold"}
