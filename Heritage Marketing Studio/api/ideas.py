"""ideas.py — idea platforms: the layer between a settled message and six kinds of work.

    Brief -> Messaging house -> Idea platform -> Executions
                                (the plan decides who, where and when — not the idea)

A messaging house settles what is true and why anyone should believe it. It does not say what to make.
Without something in that gap, six producers each invent their own creative idea and the film, the shelf
strip and the promoter's opening line come back looking like three campaigns that happen to share a
message. Nothing in the portal could previously prevent that, because nothing held an idea.

**A platform is not a big concept.** The difference is a *mechanic* — a repeatable device that generates
the next execution. "Celebrate the mothers of India" is a sentiment; it yields one film and then repeats
itself. "Every pack carries the name of the dairy that filled it" is a mechanic; it yields a film, a pack
change, a shelf strip, a promoter who can point at something, and a trade argument about provenance.

**Optional, by design.** A house needs no platform. An execution can be briefed without one — it raises a
finding saying the work will not be coherent with anything else, which is true, and is a thing a person
may reasonably accept. Once a platform is chosen it becomes the default. Same pattern as a plan without a
house.

Two ways forward, and they are deliberately different calls:

    more_options()   three fresh bets — required to go somewhere earlier rounds did not
    build_on(id)     take one and deepen it: sharper mechanic, more media, harder proof

Both keep everything already written. Nothing is replaced, because the discarded round is often where
somebody finds the thing they actually wanted, and a tool that silently overwrites teaches people not to
explore.
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid

import brandprofile
import findings as findings_mod
import jsonout
import media
import project as project_mod
import strategy
import tenancy

# Resolved through tenancy so one deployment can hold several companies. The name is kept
# so every reader in this module is unchanged.
PLATFORM_DIR = tenancy.dir("platforms")
_SKILL = os.path.join(os.path.dirname(__file__), "ideas_skill")

# The media a platform is expressed in. Keys match execution.MANIFEST so an execution can collect its
# own line without a translation table.
#
# Defined in media.py, which is now the only file that says what a medium is. Identical value — this is
# a re-point, not a change. Three of these keys are retired in the target taxonomy there, each with a
# recorded destination: `video` is an asset rather than a medium, `incentive` is a lever inside trade,
# and `media` is a schedule and has been parked by decision. All three stay live here until the phase
# that folds them.
EXPRESSIONS: dict[str, str] = media.EXPRESSIONS

# A platform must reach this many media to be a platform rather than a concept.
MIN_MEDIA = 3
MIN_PLATFORMS = 3          # the house branches into at least three, or it has not branched

# Sentiments masquerading as mechanics. A mechanic answers "what rule generates the next execution?" —
# none of these does.
SENTIMENT = ("celebrate", "inspire", "empower", "connect", "engage", "delight", "honour", "honor",
             "evoke", "remind", "showcase", "highlight", "communicate", "convey", "reinforce",
             "build trust", "create awareness", "emotional connect", "feel good", "warmth")

_STOP = {"that", "this", "with", "from", "have", "been", "were", "will", "milk", "brand", "never",
         "always", "show", "showing", "shown", "about", "their", "there", "which", "would"}


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


def _path(pid: str) -> str:
    return os.path.join(PLATFORM_DIR, f"{pid}.json")


def load(pid: str) -> dict | None:
    try:
        with open(_path(pid), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def save(p: dict) -> dict:
    os.makedirs(PLATFORM_DIR, exist_ok=True)
    p["updated"] = _now()
    tmp = _path(p["id"]) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(p, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, _path(p["id"]))
    return p


def sets(house_id: str = "") -> list[dict]:
    os.makedirs(PLATFORM_DIR, exist_ok=True)
    out = []
    for f in sorted(os.listdir(PLATFORM_DIR)):
        if not f.endswith(".json"):
            continue
        p = load(f[:-5])
        if not p or (house_id and p.get("house") != house_id):
            continue
        out.append({"id": p["id"], "brand": p.get("brand", ""), "house": p.get("house", ""),
                    "project": project_mod.of(p), "project_source": p.get("project_source", ""),
                    "label": project_mod.label(p),
                    "count": len(p.get("platforms", [])), "chosen": p.get("chosen", ""),
                    "created": p.get("created", ""), "updated": p.get("updated", "")})
    return out


def for_house(house_id: str) -> dict | None:
    """The platform set belonging to a house. One per house — more than one is a second opinion, not a
    second document, and it would leave executions unable to say which set they inherited from.

    **An empty house id returns None, deliberately.** `sets("")` skips its filter and lists every set, so
    this used to answer an empty id with whichever file sorted first — meaning a client that sent
    `house: null` (which the screen does whenever no house is loaded) got a real, arbitrary, *wrong*
    platform set, and `/platform-judge` would happily write the model's verdicts into somebody else's
    brand. Nothing would have looked broken. Resolution has to be deliberate; see `resolve()`.
    """
    if not str(house_id or "").strip():
        return None
    found = sets(house_id)
    return load(found[0]["id"]) if found else None


def latest() -> dict | None:
    """The most recently updated set. Only for READS, and only when nothing narrower was asked for."""
    rows = sets()
    if not rows:
        return None
    rows.sort(key=lambda r: (r.get("updated") or r.get("created") or ""), reverse=True)
    return load(rows[0]["id"])


def set_for_item(item_id: str) -> dict | None:
    """The set that contains a given platform. The screen holds the platform's id, not its set's."""
    if not str(item_id or "").strip():
        return None
    for row in sets():
        s = load(row["id"])
        if any(x.get("id") == item_id for x in (s or {}).get("platforms", [])):
            return s
    return None


def resolve(payload: dict, *, allow_latest: bool = False) -> tuple[dict | None, str, str]:
    """Work out which set and which platform a request means. Returns `(set, item_id, detail)`.

    One resolution order, shared by every platform route, because three routes each guessing differently
    is how a request ends up mutating the wrong document:

        set  ->  house  ->  the set containing `item`  ->  (reads only) the most recent set

    The screen sends the *platform's* id as `item` and often has no set id at all, so the third step is
    what makes those requests land. `allow_latest` is off for anything that writes: a read showing the
    wrong document is a confusing screen, a write is lost work.
    """
    p = load(str(payload.get("set") or payload.get("set_id") or ""))
    if not p:
        p = for_house(str(payload.get("house") or ""))
    item = str(payload.get("item") or payload.get("platform") or "")
    if not p and item:
        p = set_for_item(item)
    if not p and allow_latest:
        p = latest()
    if not p:
        return None, "", ("No platform set to work on. Adopt a platform first, or say which house this "
                          "belongs to.")
    if item and not any(x.get("id") == item for x in p.get("platforms", [])):
        # An id that names nothing in the resolved set is more likely a stale screen than a typo, and
        # silently falling back to the chosen platform would judge one thing while reporting another.
        return p, "", "That platform is not in this set — it may have been dropped. Reload the screen."
    if not item:
        item = (chosen_platform(p) or {}).get("id", "")
    if not item:
        return p, "", ("Choose which platform leads first — its expressions are what every producer "
                       "inherits.")
    return p, item, ""


def set_steer(p: dict, steer: str) -> dict:
    """Remember what the person told the last round to do differently.

    Held on the set rather than the client, because it is the only record of *why* round four differs from
    round one — and on the screen it lived in state that a reload threw away.
    """
    text = str(steer or "").strip()
    if not text or text == str(p.get("steer") or ""):
        return p
    p["steer"] = text
    p["steer_at"] = _now()
    return save(p)


def new_set(brand: str, house_id: str) -> dict:
    # Named once at the brief, inherited by the house, and now by the platform too — same one-time
    # copy `plan.new_plan` already does, so a picker showing several platform sets for one brand can
    # tell them apart the same way houses and plans already can.
    p = {"id": uuid.uuid4().hex[:10], "brand": brand or "Brand", "house": house_id,
         "project": project_mod.of(strategy.load(house_id) if house_id else None),
         "created": _now(), "updated": _now(), "round": 0,
         "platforms": [], "chosen": ""}
    return save(p)


# --- what the house gives it -------------------------------------------------------------------

def house_basis(house: dict | None) -> dict:
    """The house decisions a platform is built on, and its fingerprint for staleness."""
    if not house:
        return {"core": [], "emotional": "", "functional": "", "codes": [], "avoid": [],
                "rtbs": [], "signature": ""}

    def chosen(layer):
        node = house.get("nodes", {}).get(layer) or {}
        picked = set(node.get("chosen") or [])
        return [o for o in node.get("options", []) if o["id"] in picked]

    culture = chosen("culture")
    rtbs = []
    for layer, pillar in (("rtb_emotional", "emotional"), ("rtb_functional", "functional")):
        for o in chosen(layer):
            rtbs.append({"id": o["id"], "text": o["text"], "pillar": pillar,
                         "source": o.get("source", "model"),
                         "sourced": str(o.get("source", "")).lower() in ("brief", "library", "user")})
    core = [o["text"] for o in chosen("core")]
    emo = next((o["text"] for o in chosen("emotional")), "")
    fun = next((o["text"] for o in chosen("functional")), "")
    avoid = [o["text"] for o in culture if str(o.get("tag", "")).lower() == "avoid"]
    codes = [{"text": o["text"], "tag": o.get("tag", "")} for o in culture
             if str(o.get("tag", "")).lower() != "avoid"]
    sig = strategy.hashlib.sha256(
        "|".join(sorted(core) + [emo, fun] + sorted(avoid)
                 + sorted(f"{r['id']}:{r['sourced']}" for r in rtbs)).encode("utf-8")
    ).hexdigest()[:16]
    return {"core": core, "emotional": emo, "functional": fun, "codes": codes, "avoid": avoid,
            "rtbs": rtbs, "signature": sig}


def claim_fact(it: dict | None, house: dict | None) -> dict:
    """The one fact this platform actually stands on, resolved to its real text and sourced-ness.

    Exists so the "could a competitor sign it" test — asked today in `JUDGED['ours']`, against the
    whole platform sentence — can instead be shown next to the SPECIFIC fact and pillar the platform
    is built from, which is a fairer and more checkable question. This does not move or rename that
    test; it supplies the fact so a screen can put the two side by side. Retiring the test itself is
    left for a later round, once a screen exists to ask it in the new place — pulling it now would
    empty the live "Two tests" panel before its replacement was built.

    Reads `rtb_id` only, never the free-text `rtb` field. `it['rtb']` is ambiguous in this codebase —
    one drafting prompt fills it with the RTB's id, a different one fills it with a paraphrase in the
    model's own words (see the two JSON contracts in `draft_ladders` and the route-drafting prompt), and
    `test_platform`'s own proof check already reads `it['rtb']` as though it were always the id, which
    is not reliably true. `rtb_id` was added later specifically to be unambiguous ("so a reader can see
    what the platform comes out of without opening the house") and is the only field this function
    trusts. That pre-existing `rtb`/`rtb_id` overlap is a real inconsistency worth a dedicated look, but
    it is not this function's job to resolve it — only to not inherit it.
    """
    rtb_id = str((it or {}).get("rtb_id") or "").strip()
    pillar = str((it or {}).get("pillar") or "").strip()
    if not rtb_id:
        return {"available": False, "text": "", "pillar": pillar, "sourced": False, "id": ""}
    basis = house_basis(house)
    row = next((r for r in basis["rtbs"] if r["id"] == rtb_id), None)
    if not row:
        # The option it pointed at was deleted or the house was replaced — reported, not guessed at.
        return {"available": False, "text": "", "pillar": pillar, "sourced": False, "id": rtb_id}
    return {"available": True, "text": row["text"], "pillar": row["pillar"] or pillar,
            "sourced": row["sourced"], "id": rtb_id}


def ready(house: dict | None) -> tuple[bool, str]:
    """A platform cannot be written before there is a message to express."""
    if not house:
        return False, "attach a messaging house first — a platform expresses a message"
    b = house_basis(house)
    if not b["core"]:
        return False, "choose the core message first — that is what a platform expresses"
    if not (b["emotional"] or b["functional"]):
        return False, "choose at least one pillar first — a platform leads with one"
    return True, ""


# --- editing ------------------------------------------------------------------------------------

_FIELDS = ("name", "idea", "mechanic", "territory", "proof", "why", "rtb")


def add(p: dict, data: dict, source: str = "user", built_from: str = "") -> dict:
    """Add one platform. A hand-written one counts as sourced — the author is the evidence for it."""
    item = {c: str(data.get(c, "") or "").strip() for c in _FIELDS}
    item.update({
        "id": uuid.uuid4().hex[:8], "source": source, "added": _now(),
        "round": p.get("round", 0),
        "built_from": built_from,
        "expressions": {k: str((data.get("expressions") or {}).get(k, "") or "").strip()
                        for k in EXPRESSIONS},
    })
    p["platforms"].append(item)
    return save(p)


def edit(p: dict, item_id: str, data: dict) -> dict | None:
    """Change a platform. Editing any authored field makes it the author's, same as everywhere else."""
    for it in p["platforms"]:
        if it["id"] != item_id:
            continue
        before = {c: it.get(c, "") for c in _FIELDS}
        for c in _FIELDS:
            if c in data:
                it[c] = str(data.get(c, "") or "").strip()
        if isinstance(data.get("expressions"), dict):
            for k, v in data["expressions"].items():
                if k in EXPRESSIONS:
                    it["expressions"][k] = str(v or "").strip()
        if {c: it.get(c, "") for c in _FIELDS} != before:
            it["source"] = "user"
            it["edited"] = _now()
        return save(p)
    return None


def express(p: dict, item_id: str, kind: str, text: str) -> tuple[dict | None, str]:
    if kind not in EXPRESSIONS:
        return None, f"Nothing to express for {kind!r}. One of: {', '.join(EXPRESSIONS)}."
    for it in p["platforms"]:
        if it["id"] == item_id:
            it["expressions"][kind] = (text or "").strip()
            it["edited"] = _now()
            return save(p), ""
    return None, "No such platform."


def express_many(p: dict, item_id: str, mapping: dict) -> tuple[dict | None, str]:
    """Store several expressions at once. One save, one response, one debounce on the screen.

    `express()` above takes one medium, which is right for a single field losing focus and wrong for the
    block of five: five requests race each other, and the last response to arrive wins with a copy of the
    set that predates the other four. Editing five slots quickly could therefore lose four of them.

    A key present with an empty value clears that slot — somebody deleting an expression means it.
    """
    for it in p["platforms"]:
        if it["id"] != item_id:
            continue
        unknown = [k for k in mapping if k not in EXPRESSIONS]
        if unknown:
            return None, (f"Nothing to express for {', '.join(sorted(unknown))}. "
                          f"One of: {', '.join(EXPRESSIONS)}.")
        it.setdefault("expressions", {k: "" for k in EXPRESSIONS})
        for k, v in mapping.items():
            it["expressions"][k] = str(v or "").strip()
        it["edited"] = _now()
        return save(p), ""
    return None, "No such platform."


def drop(p: dict, item_id: str) -> dict:
    p["platforms"] = [x for x in p["platforms"] if x["id"] != item_id]
    if p.get("chosen") == item_id:
        p["chosen"] = ""
    return save(p)


def choose(p: dict, item_id: str) -> dict:
    """One platform leads. Choosing is what makes the executions cohere; two chosen is none chosen."""
    p["chosen"] = item_id if any(x["id"] == item_id for x in p["platforms"]) else ""
    return save(p)


# --- the adopted platform (the screen's own shape) ----------------------------------------------
#
# The Idea Platform screen works a different way from the generator above, and both are kept.
#
# The screen asks a person to write ONE platform and judge it against five questions they answer
# themselves — is it true, could a competitor sign it, is there a tension in it, does every channel get
# something to do, does it survive three years. The generator offers several and scores them mechanically.
#
# Those are not the same instrument and neither replaces the other: the screen's five are judgements with
# a written reason, and a judgement with a reason attached is worth more than a keyword match. So the
# verdicts are stored **verbatim**, never recomputed, and the mechanical tests stay available beside them
# as advice. Overwriting someone's "holds, because…" with a scanner's opinion would be the whole point
# of this layer thrown away.

# The screen's route keys against the execution kinds they express into.
# DEPRECATED — kept only to read older files. `routes` and `expressions` were two stores for one thing.
#
# Four of the five routes mapped onto an expression slot under a different name (`onground`→`activation`,
# `trade`→`incentive`), so the screen showed the same field twice — once as "Expression routes" with a
# hand-off link and once as "Expression by medium" with a rewrite button — and `adopt()` carried a block
# of precedence code to stop one blanking the other. That code is where a real defect lived: an empty
# route wiped an expression somebody had written.
#
# `media` was the only route with no slot and `video` the only slot with no route, so the union is the
# six keys in EXPRESSIONS. Nothing new is written here; `_fold_routes` migrates legacy text on read and
# the merged screen writes `expressions` only.
ROUTE_TO_KIND = {"social": "social", "posm": "posm", "onground": "activation",
                 "media": "media", "trade": "incentive"}
VERDICTS = ("untested", "holds", "fails")


def _fold_routes(it: dict | None) -> dict:
    """Legacy `routes` text folded into empty `expressions` slots. Read-only, non-destructive.

    An older platform holds its per-medium lines under `routes`. Dropping that store without migrating
    would make somebody's written work disappear from the screen — so it is folded in on the way out,
    and only into slots that are still empty. `routes` is left on the record: it costs nothing and a
    silent rewrite of somebody's file is not worth the tidiness.
    """
    if not it:
        return {}
    expr = {k: str(v or "").strip() for k, v in (it.get("expressions") or {}).items()}
    for route, text in (it.get("routes") or {}).items():
        kind = ROUTE_TO_KIND.get(str(route))
        text = str(text or "").strip()
        if kind and kind in EXPRESSIONS and text and not expr.get(kind):
            expr[kind] = text
    return {k: expr.get(k, "") for k in EXPRESSIONS}


def adopt(p: dict, data: dict) -> dict:
    """Save the platform written on the screen: name, one line, five verdicts, five routes.

    Stored as the single chosen platform so everything downstream — the execution's inherited
    `brief.platform`, staleness, the expression per kind — works unchanged.
    """
    routes = data.get("routes") if isinstance(data.get("routes"), dict) else {}
    tests = data.get("tests") if isinstance(data.get("tests"), dict) else {}
    verdicts = {}
    for k, v in tests.items():
        if not isinstance(v, dict):
            continue
        verdict = str(v.get("verdict") or "untested").lower()
        verdicts[str(k)] = {"verdict": verdict if verdict in VERDICTS else "untested",
                            "note": str(v.get("note") or "").strip()}

    # What is being replaced. `prior` is read before anything is written, so every rule below can ask what
    # was there. Adopting rewrites the whole item, so anything not carried across here is
    # destroyed — and the screen calls this every time somebody presses Adopt, including long after the
    # platform was first saved.
    prior = next((x for x in p["platforms"] if x.get("adopted")), None) or {}

    # A key the payload does not carry is unchanged; a key it carries is set, even to empty. The screen
    # sends five fields and the item has eleven, so the alternative — absent means blank — meant that
    # every Adopt silently emptied `mechanic`, `territory`, `proof` and `why`, and the repeatable device
    # is the one field that separates a platform from a slogan.
    def held(key: str, *aliases: str) -> str:
        for k in (key,) + aliases:
            if k in data:
                return str(data.get(k) or "").strip()
        return str(prior.get(key) or "").strip()

    # `line` is the screen's name for it and wins where both arrive; `idea` is what it is stored as.
    _new_idea = str(data["line"] or "").strip() if "line" in data else held("idea")

    # The five expressions, in order of authority: what was already stored, then anything a route says,
    # then anything this payload carries explicitly.
    #
    # This used to start from five empty strings and fill only from `routes`, which meant generating the
    # five expressions and then pressing Adopt wiped four of them — the two features were built a round
    # apart and only the second one wrote to these slots. An empty route must never blank an expression
    # somebody wrote or generated; the routes screen and the expressions block are two ways into the same
    # field, and neither owns it.
    #
    # 23 Sep -- live bug: that "what was already stored" fallback read `prior` unconditionally, and
    # `prior` is whatever platform WAS adopted before this call -- correct when Adopt is re-saving the
    # SAME platform (the case above was written for), wrong when it is adopting a genuinely DIFFERENT one
    # (a redraft). A brand new platform ("Before The First Light") inherited the OUTGOING platform's own
    # per-medium text ("the idea platform, expressed for social" kept showing the prior platform's
    # "Ee Veedhi, Aa Chethulu" line) because nothing regenerates expressions on adopt and this fallback
    # did not check whether the idea itself had actually changed. Only inherit when it has not.
    _same_platform = bool(prior) and _new_idea == str(prior.get("idea") or "").strip()
    expressions = {k: "" for k in EXPRESSIONS}
    if _same_platform:
        expressions.update({k: str(v or "").strip()
                            for k, v in (prior.get("expressions") or {}).items() if k in EXPRESSIONS})
    for route, text in routes.items():
        kind = ROUTE_TO_KIND.get(str(route))
        if kind and kind in expressions and str(text or "").strip():
            expressions[kind] = str(text or "").strip()
    if isinstance(data.get("expressions"), dict):
        for k, v in data["expressions"].items():
            if k in EXPRESSIONS and str(v or "").strip():
                expressions[k] = str(v).strip()

    item = {
        "name": held("name"),
        "idea": _new_idea,
        "mechanic": held("mechanic"),
        "territory": held("territory"),
        "proof": held("proof"),
        "why": held("why"),
        "rtb": held("rtb"),
        # A hand-typed platform is the author's, so `user` is the right default. But a line that came
        # from `/idea-draft` and was adopted unchanged is still the model's, and marking it `user` would
        # launder it past the one discipline this whole system rests on. The client echoes back the
        # `source` it was given; anything other than `model` is treated as authored.
        "source": "model" if str(data.get("source") or "").lower() == "model" else "user",
        "adopted": True,
        # The brief this platform answers. Kept as whatever the screen had — an id when the row came from
        # the library, its title when it did not. Not resolved to a document here: a platform written
        # against a brief nobody saved should still record which words it answered.
        "brief": held("brief"),
        # Same rule again: a body with no `tests` key is not somebody withdrawing five judgements, and one
        # with no `routes` key is not somebody deleting five routes.
        "verdicts": verdicts if "tests" in data else (prior.get("verdicts") or {}),
        # `media` has no expression slot in EXPRESSIONS by design, but the screen has a media route and
        # a person wrote it. Dropping it silently would lose work, so it is kept alongside.
        "routes": ({str(k): str(v or "").strip() for k, v in routes.items()} if "routes" in data
                   else (prior.get("routes") or {})),
        "expressions": expressions,
        # The ladder to the house. `/idea-draft` works these out and puts them on every route it offers,
        # and until now adoption threw all three away — so the badge a person chose the route *by*
        # vanished the moment they adopted it, and the document had nothing to print under "which pillar
        # it comes out of". Taken from the payload when the screen sends it, otherwise held from before.
        "pillar": str(data.get("pillar") or prior.get("pillar") or "").strip(),
        "rtb_id": str(data.get("rtb_id") or prior.get("rtb_id") or "").strip(),
        "caveat": str(data.get("caveat") or prior.get("caveat") or "").strip(),
        # Which path up the house's ladder this platform stands on. This is the stronger form of the
        # `rtb_id` above — an rtb says which fact, a ladder says which fact, through which meaning, to
        # which feeling. It is what makes the retired `true` test computable.
        "ladder": str(data.get("ladder") or prior.get("ladder") or "").strip(),
        # Campaigns are children of the platform, not a separate store: a campaign is a time-bound
        # expression of exactly one platform, so nesting makes the inheritance structural instead of a
        # convention nobody enforces, and it cannot orphan itself. Never rebuilt from the payload —
        # `/campaign` owns them, and an Adopt that reset them would delete a quarter's work.
        "campaigns": (prior.get("campaigns") or []),
        # The model's reading of the five, kept across an adoption. It is stored under a different key
        # from the person's verdicts precisely so that neither overwrites the other, and dropping it here
        # would have made every save quietly undo the model's check. Each verdict remembers the sentence
        # it read, so one made against a line since rewritten can be shown as stale rather than deleted —
        # a superseded challenge is still worth reading, and deleting it is the tool taking a side.
        "judged": normalise_judged(data.get("judged") if isinstance(data.get("judged"), dict)
                                   else prior.get("judged")),
    }
    if not item["rtb"]:
        item["rtb"] = str(prior.get("rtb") or "").strip()

    existing = prior or None
    if existing:
        item["id"] = existing["id"]
        item["added"] = existing.get("added", _now())
        item["edited"] = _now()
        p["platforms"] = [item if x["id"] == existing["id"] else x for x in p["platforms"]]
    else:
        item["id"] = uuid.uuid4().hex[:8]
        item["added"] = _now()
        item["round"] = p.get("round", 0)
        item["built_from"] = ""
        p["platforms"].append(item)

    p["chosen"] = item["id"]
    # Adopting a platform normally means you are not skipping. But `skipped` now rides along on the same
    # payload, and forcing it False here would silently discard a caller that sent both — somebody who
    # writes a platform and then decides not to use it yet is making two decisions, not a contradiction.
    if "skipped" in data:
        p["skipped"] = bool(data.get("skipped"))
    else:
        p["skipped"] = False
    return save(p)


def as_read(p: dict | None, house: dict | None = None) -> dict:
    """The flat shape the Idea platform tab hydrates from: name, line, tests, routes, skipped, source.

    Returns the same keys whether or not anything has been adopted, so the screen has one code path.
    Empty strings rather than nulls: the tab writes straight into its fields, and a null would clear a
    box the author may be part-way through.

    `house` is optional and only sharpens `claim_fact` — every existing caller that does not have one
    handy keeps working exactly as before, just without that one field resolved.
    """
    it = chosen_platform(p) or {}
    if not it and p:
        # A set can exist with a platform that is skipped — the fields are still worth returning so the
        # screen can show what would come back if the skip were lifted.
        it = next((x for x in p.get("platforms", []) if x.get("adopted")), {})
    return {
        "name": it.get("name", ""),
        "line": it.get("idea", ""),
        "tests": it.get("verdicts") or {},
        "routes": it.get("routes") or {},
        "brief": it.get("brief", ""),
        "source": it.get("source") or "",
        "skipped": bool((p or {}).get("skipped")),
        "adopted": bool(it),
        "set": (p or {}).get("id", ""),
        "updated": (p or {}).get("updated", ""),
        # The producers ground themselves on the platform the screen is holding, and the screen can only
        # send back what it was given. Without these three it sent `mechanic: ''` on every request and had
        # no id to send at all, so a platform on screen could not be named to the server.
        "id": it.get("id", ""),
        "mechanic": it.get("mechanic", ""),
        # One store, six media. `routes` and `expressions` were the same field under two names; legacy
        # route text is folded into any slot still empty so nothing written before the merge disappears.
        "expressions": _fold_routes(it),
        "expression_jobs": EXPRESSIONS,
        # The ladder, so a reader can see what the platform comes out of without opening the house. On the
        # card these are a badge and a "rests on:" line; both were held only in the drafting response, so
        # they survived until the page was reloaded and no further.
        "pillar": it.get("pillar", ""),
        "rtb": it.get("rtb", ""),
        "rtb_id": it.get("rtb_id", ""),
        "caveat": it.get("caveat", ""),
        "ladder": it.get("ladder", ""),
        # The fact this platform stands on, resolved to real text — so a screen can put the "could a
        # competitor sign it" question next to the specific claim rather than the whole sentence.
        "claim_fact": claim_fact(it, house),
        # Whether the house's ladder has been revisited since this platform was adopted. False on every
        # platform adopted before this field existed, which is the honest default: none of them were
        # asked the question this flag answers.
        "ladder_confirmed": bool(it.get("ladder_confirmed")),
        # Campaigns off this platform. The screen draws them as a list under the adopted platform, so it
        # needs them on the same hydration it already makes rather than a second call.
        "campaigns": it.get("campaigns") or [],
        "retired_tests": RETIRED_TESTS,
        # The model's reading of the five, and the questions it answered. Returned beside the person's
        # `tests` rather than merged into them: the whole point of the layer is that these are two
        # readings, and a reload that dropped the model's column made the screen look like it had never
        # been asked. `disagreements` is computed here so the screen and the document cannot disagree
        # about what disagreeing means.
        "judged": normalise_judged(it.get("judged")),
        "questions": JUDGED, "ask": JUDGED_ASK, "why": JUDGED_WHY,
        "disagreements": disagreements(it),
        "judged_stale": judged_stale(it),
        # What the last round was told to do differently — the only record of why round four differs from
        # round one, and it lived in state a reload threw away.
        "steer": (p or {}).get("steer", ""),
        "house": (p or {}).get("house", ""),
    }


def disagreements(it: dict | None) -> list[str]:
    """The tests where the model and the person reached different verdicts.

    Computed in one place because the screen highlights them, the document prints them in amber and the
    judge route reports a count — three readers deriving "different" separately is three chances to
    disagree about disagreement.
    """
    if not it:
        return []
    human = it.get("verdicts") or {}
    model = normalise_judged(it.get("judged"))
    out = []
    for k, v in model.items():
        mine = str((human.get(k) or {}).get("verdict") or "").strip().lower()
        theirs = str(v.get("verdict") or "").strip().lower()
        if mine and mine not in ("untested",) and theirs and mine != theirs:
            out.append(k)
    return out


def judged_stale(it: dict | None) -> bool:
    """True when the model judged a sentence that has since been rewritten.

    Not a reason to delete its reading — a superseded challenge is still worth reading, and throwing it
    away would be the tool deciding the argument. It is a reason to say so on the page.
    """
    if not it:
        return False
    line = str(it.get("idea") or "").strip()
    for v in normalise_judged(it.get("judged")).values():
        read = str(v.get("for_line") or "").strip()
        if read and read != line:
            return True
    return False


def from_client(value) -> dict | None:
    """Accept a platform the way the client actually sends it. Returns the internal shape, or None.

    The screen hydrates from `as_read`, which renames the platform's sentence `idea` -> `line`. So the
    client correctly holds `line` and correctly sends `line` back — and every reader on this side looks
    for `idea`. An inline platform therefore arrived carrying its sentence under a key nothing read, and
    silently grounded nothing.

    Takes either an id string (looked up, so the stored platform wins and is complete) or the inline
    object the screen is holding for a platform not yet adopted. `line` and `idea` are both honoured
    in the inline case, because which one you get depends on where the object came from.
    """
    if not value:
        return None
    if isinstance(value, str):
        pl = load(value)
        if pl:
            return chosen_platform(pl)
        # An id might name the platform itself rather than its set — search the sets for it.
        for row in sets():
            s = load(row["id"])
            hit = next((x for x in (s or {}).get("platforms", []) if x.get("id") == value), None)
            if hit:
                return hit
        return None
    if isinstance(value, dict):
        idea = str(value.get("idea") or value.get("line") or "").strip()
        if not idea and not str(value.get("name") or "").strip():
            return None
        return {"id": str(value.get("id") or ""),
                "name": str(value.get("name") or "").strip(),
                "idea": idea,
                "mechanic": str(value.get("mechanic") or "").strip(),
                "expressions": value.get("expressions") or {},
                "source": str(value.get("source") or "")}
    return None


def set_skipped(p: dict, skipped: bool) -> dict:
    """Skipping the platform is a decision, not a UI preference, so it is stored.

    Kept separate from deleting the platform: somebody who skips and later un-skips should find their
    work where they left it.
    """
    p["skipped"] = bool(skipped)
    return save(p)


def set_ladder_confirmed(p: dict, on: bool = True) -> tuple[dict | None, str]:
    """Record that the house's ladder was revisited after this platform was adopted.

    A house is written before an idea exists, so its core, emotional and functional layers are a first
    pass — the best guess available with nothing yet to aim at. Once a platform is adopted, that guess
    should be returned to and re-argued now that there is a mechanic to write toward; a core line
    written before the idea is usually a summary of the category, not a carrier of it.

    This flag is the only record of whether that return trip happened. It is deliberately a plain
    boolean rather than a timestamp comparison against when the layers were last edited: this codebase
    has no "platform adopted at" timestamp today (`adopted` is a bare `True`), and inferring the return
    trip from edit times would be guessing at a signal that mostly is not there. A flag a person sets
    themselves, once, by returning to the ladder and saving it, is honest about being a decision rather
    than a computation — the same reasoning `set_skipped` already rests on.

    It does not reset on later edits to the platform's own sentence or mechanic. Resetting automatically
    risks flipping it back to provisional on an unrelated change (a typo fix, a rewritten mechanic) and
    nagging someone who already did the work. If the platform's FACT changes — a different pillar or
    RTB — that is a materially new idea and the person can confirm again; the flag is not protected
    against being left stale in that case, and that trade is deliberate rather than an oversight.
    """
    it = next((x for x in p["platforms"] if x.get("adopted")), None)
    if not it:
        return None, "No adopted platform to confirm the ladder for."
    it["ladder_confirmed"] = bool(on)
    return save(p), ""


def chosen_platform(p: dict | None) -> dict | None:
    """The platform executions inherit — None when there is none, or when it was deliberately skipped.

    Honouring `skipped` here rather than at each call site is what makes the skip real: turn it on in
    Strategy and no producer can quietly still be carrying the idea.
    """
    if not p or not p.get("chosen") or p.get("skipped"):
        return None
    return next((x for x in p["platforms"] if x["id"] == p["chosen"]), None)


# --- the five tests ----------------------------------------------------------------------------

def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{5,}", (text or "").lower()) if w not in _STOP}


def test_platform(it: dict, basis: dict) -> dict:
    """The five tests, per platform. Returns a struct the UI can draw rather than a pass/fail."""
    filled = [k for k, v in (it.get("expressions") or {}).items() if str(v).strip()]
    mech = str(it.get("mechanic") or "").strip()
    sentiment = next((w for w in SENTIMENT if w in mech.lower()), "")

    # 4. the proof must rest on a sourced RTB
    rtb_id = str(it.get("rtb") or "").strip()
    rtb = next((r for r in basis["rtbs"] if r["id"] == rtb_id), None)

    # 3. the avoid list. A heuristic, so it is reported as a question rather than a verdict — two or
    # more significant words shared with an avoid instruction is worth a person's eye, not a block.
    text = " ".join([it.get("idea", ""), mech, it.get("territory", "")]
                    + list((it.get("expressions") or {}).values()))
    tw = _words(text)
    collides = [a for a in basis["avoid"] if len(_words(a) & tw) >= 2]

    return {
        "media": {"ok": len(filled) >= MIN_MEDIA, "filled": filled, "need": MIN_MEDIA,
                  "detail": f"expressed in {len(filled)} of {len(EXPRESSIONS)} media"},
        "mechanic": {"ok": bool(mech) and not sentiment, "sentiment": sentiment,
                     "detail": "no mechanic named" if not mech
                               else f"{sentiment!r} is a sentiment, not a mechanic" if sentiment
                               else "a mechanic is named"},
        "avoid": {"ok": not collides, "collides": collides,
                  "detail": "clear of the avoid list" if not collides
                            else f"may collide with {len(collides)} avoid instruction(s)"},
        "proof": {"ok": bool(rtb and rtb["sourced"]), "rtb": rtb["text"] if rtb else "",
                  "detail": "no reason-to-believe named" if not rtb
                            else "rests on an unsourced RTB" if not rtb["sourced"]
                            else f"rests on a sourced RTB ({rtb['pillar']})"},
        # 5. media-neutral at birth: film-only is the classic failure, so it is called out by name.
        "neutral": {"ok": not (filled and set(filled) <= {"video"}),
                    "detail": "works only as film — that is a film idea, not a platform"
                              if filled and set(filled) <= {"video"} else "not film-only"},
    }


def validate(p: dict, house: dict | None = None) -> list[dict]:
    out: list[dict] = []
    basis = house_basis(house)

    def add_f(level, layer, detail):
        out.append({"level": level, "layer": layer, "detail": detail})

    items = p.get("platforms") or []
    if not items:
        add_f("empty", "", "No platforms yet. The house branches into at least three genuinely "
                           "different bets — or it has not branched.")
        return out

    # "Offer at least three and choose" belongs to the generator, where the machine is proposing bets and
    # a person picks. The Idea Platform screen asks for one platform, written by hand and judged. Raising
    # this against it would be the tool telling somebody their form is the wrong shape.
    adopted = any(x.get("adopted") for x in items)
    if len(items) < MIN_PLATFORMS and not adopted:
        add_f("open", "", f"{len(items)} platform(s). Under {MIN_PLATFORMS} there is no choice being "
                          f"made, only a line being written.")

    for it in items:
        t = test_platform(it, basis)
        name = it.get("name") or "an unnamed platform"

        # A platform adopted from the screen was judged by a person against five questions, with a
        # written reason. Those verdicts are the findings for it — the mechanical tests below would
        # otherwise raise a blocking "no mechanic named" against a platform whose form never asked for
        # one, which is a tool arguing with its own user.
        if it.get("adopted"):
            verdicts = it.get("verdicts") or {}
            failed = [(k, v) for k, v in verdicts.items() if v.get("verdict") == "fails"]
            untested = [k for k, v in verdicts.items() if v.get("verdict") != "holds"
                        and v.get("verdict") != "fails"]
            for k, v in failed:
                # Failing is allowed, in writing. Same rule as an overridden finding: a platform can run
                # with a known weakness; it cannot run with an unexamined one.
                note = (v.get("note") or "").strip()
                add_f("open" if note else "blocking", it["id"],
                      f"{name} fails the '{k}' test" + (f": {note}" if note else
                      " and no reason is written down. Say why it may still run, or change it."))
            if untested:
                add_f("open", it["id"],
                      f"{name}: {len(untested)} of {len(verdicts) or 5} tests not answered "
                      f"({', '.join(sorted(untested))}). An unanswered test is not a pass.")
            if not str(it.get("idea") or "").strip():
                add_f("blocking", it["id"], f"{name} has no sentence. The tests have nothing to test.")
            if it.get("source") == "model":
                add_f("unsourced", it["id"],
                      f"{name} is the drafted line, adopted unchanged. Rewrite it in your own words — "
                      f"a platform nobody has argued with is the model's opinion carrying your logo.")
            # The model's reading is kept when the line changes rather than deleted, so it has to be
            # labelled. Open, not blocking: a superseded challenge is worth reading and re-running the
            # check is one click.
            if judged_stale(it):
                add_f("open", it["id"],
                      f"The model's reading of {name} was written against an earlier version of the "
                      f"line. It is still worth reading, but ask it again before treating it as current.")
            continue

        if not str(it.get("name") or "").strip():
            add_f("open", it["id"], "This platform has no name. The name is what a room repeats for two "
                                    "years; an idea without one gets dropped for reasons nobody can say.")
        if not t["mechanic"]["ok"]:
            add_f("blocking", it["id"], f"{name}: {t['mechanic']['detail']}. A platform needs a "
                                        f"repeatable device — what rule generates the next execution?")
        if not t["media"]["ok"]:
            add_f("open", it["id"], f"{name}: {t['media']['detail']}. Under {MIN_MEDIA} it is a concept, "
                                    f"which is worth having — but do not brief it as a platform.")
        if not t["neutral"]["ok"]:
            add_f("open", it["id"], f"{name}: {t['neutral']['detail']}. Test it against a shelf strip "
                                    f"before a thirty-second film.")
        if not t["proof"]["ok"]:
            lvl = "blocking" if t["proof"]["rtb"] else "open"
            add_f(lvl, it["id"], f"{name}: {t['proof']['detail']}. A platform whose demonstration rests "
                                 f"on nothing sourced comes apart in legal or in market.")
        for a in t["avoid"]["collides"]:
            add_f("open", it["id"], f"{name} may collide with the house's avoid instruction "
                                    f"“{a}” — check it, this is a word-overlap hint rather "
                                    f"than a verdict.")

    if not p.get("chosen"):
        add_f("open", "", "Nothing chosen. Until one platform leads, every execution will invent its "
                          "own idea — which is the problem this layer exists to solve.")

    if stale(p, house):
        add_f("stale", "", "The messaging house has moved since these were written — the core message, "
                           "a pillar, the avoid list or the evidence behind an RTB has changed.")
    return out


def stale(p: dict, house: dict | None) -> bool:
    """Only generated platforms go stale. A hand-written idea is the author's, whatever moved above it."""
    if not p.get("generated_under"):
        return False
    return p["generated_under"] != house_basis(house)["signature"]


def status(p: dict, house: dict | None = None) -> dict:
    basis = house_basis(house)
    fs = findings_mod.annotate(validate(p, house), p.get("overrides"))
    items = []
    for it in p.get("platforms", []):
        t = test_platform(it, basis)
        items.append({**it, "tests": t,
                      "passes": sum(1 for v in t.values() if v["ok"]), "of": len(t),
                      # The model's reading travels with the platform so the screen never has to hold it
                      # in state that a reload throws away.
                      "judged": normalise_judged(it.get("judged")),
                      "disagreements": disagreements(it),
                      "judged_stale": judged_stale(it),
                      "findings": [f for f in fs if f["layer"] == it["id"]]})
    ok, why = ready(house)
    return {
        "id": p["id"], "brand": p.get("brand", ""), "house": p.get("house", ""),
        "updated": p.get("updated", ""), "round": p.get("round", 0),
        "platforms": items, "chosen": p.get("chosen", ""),
        "expressions": EXPRESSIONS, "questions": JUDGED,
        "ask": JUDGED_ASK, "why": JUDGED_WHY,
        "min_media": MIN_MEDIA, "min_platforms": MIN_PLATFORMS,
        "ready": ok, "blocked_because": why,
        "basis": {k: basis[k] for k in ("core", "emotional", "functional", "codes", "avoid")},
        "rtbs": basis["rtbs"],
        "stale": stale(p, house),
        "findings": fs, "blocking": findings_mod.live_blocking(fs),
        "overridden": findings_mod.overridden_count(fs),
    }


# --- the first line ----------------------------------------------------------------------------

def write_expressions(p: dict, item_id: str, house: dict | None = None,
                      media: list[str] | None = None, steer: str = "") -> tuple[dict, str]:
    """Write what the platform becomes in each medium. Returns (expressions, note).

    Named `write_expressions`, not `express`: `express(p, item_id, kind, text)` above is the SETTER that
    stores one, and defining a second `express` here silently replaced it — the same shadowing class as
    two routes on one path, in Python this time. Generating and storing are different verbs.

    The expression slots existed and could only be typed into. That is the wrong default: the platform
    and the house between them already decide most of what each medium has to become, and asking somebody
    to write five of them from a blank box is asking them to do the derivation by hand every time.

    Each is written *against what that medium can actually do* — `EXPRESSIONS` above says what each is
    for, and it is not the same job five times. The mechanic is what carries across; the execution is not.
    """
    it = next((x for x in p.get("platforms", []) if x["id"] == item_id), None)
    if not it:
        return {}, "No such platform in this set."
    line = str(it.get("idea") or "").strip()
    if not line:
        return {}, "Write the platform's sentence first — there is nothing yet to express."
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {}, "No ANTHROPIC_API_KEY — the five slots are yours to write."

    want = [m for m in (media or list(EXPRESSIONS)) if m in EXPRESSIONS]
    basis = house_basis(house)
    already = {k: v for k, v in (it.get("expressions") or {}).items() if str(v or "").strip()}

    prompt = "\n".join([
        _skill_text(),
        "\n\n---\nTHE BRAND\n" + brandprofile.voice_block(brandprofile.resolve(house, p)),
        "\n\n---\nTHE PLATFORM, WHICH EVERY ONE OF THESE IS ONE EXPRESSION OF",
        f"Name: {it.get('name') or '(unnamed)'}",
        f"Idea: {line}",
        (f"Mechanic: {it['mechanic']}" if str(it.get("mechanic") or "").strip() else
         "Mechanic: NOT NAMED — say in each expression what the repeatable device would have to be."),
        (f"It rests on this reason to believe: {it['rtb']}" if str(it.get("rtb") or "").strip() else ""),
        "\n\n---\nTHE HOUSE IT LADDERS TO",
        "Core: " + "; ".join(basis["core"] or ["(none chosen)"]),
        f"Emotional: {basis['emotional'] or '(none)'}",
        f"Functional: {basis['functional'] or '(none)'}",
        ("MUST NOT DO: " + "; ".join(basis["avoid"])) if basis["avoid"] else "",
        (("\n\n---\nALREADY WRITTEN, and not to be repeated or contradicted:\n"
          + "\n".join(f"  {k}: {v}" for k, v in already.items())) if already else ""),
        (f"\n\n---\nTHE PERSON ADDS\n{steer.strip()}" if str(steer or "").strip() else ""),
        "\n\n---\nNOW: WHAT IT BECOMES IN EACH MEDIUM",
        "\n".join(f"  {m} — {EXPRESSIONS[m]}" for m in want),
        "\nEach is one or two sentences describing the WORK, not the message. The same idea doing a "
        "different job, because a shelf strip and a promoter's opening line are different acts of "
        "communication. If the platform genuinely cannot survive in one of these media, say so in that "
        "slot rather than writing something thin — a platform that reaches fewer than three media is a "
        "concept, and knowing that is worth more than five paragraphs pretending otherwise.",
        'Return ONLY JSON: {"expressions":{' + ", ".join(f'"{m}":"..."' for m in want) + '}}',
    ])
    data, err = jsonout.ask_json(prompt, max_tokens=700 + 320 * len(want))
    if data is None:
        return {}, f"Generation failed: {err}"
    out = {k: str(v).strip() for k, v in (data.get("expressions") or {}).items()
           if k in EXPRESSIONS and str(v or "").strip()}
    if not out:
        return {}, "Nothing usable came back — write them yourself."
    return out, ""


# The five tests, as a person and a model both understand them. `test_platform` above answers them
# mechanically — it can count media and spot a sentiment verb, and it cannot judge whether a competitor
# could sign the line. So there are three verdicts on each: what the checker can see, what a model
# argues, and what a person decides. They are kept apart on purpose; a model's opinion overwriting
# somebody's judgement is the failure this whole layer is built to avoid.
# Keyed and ordered to match the screen's own five, so the model's answer lands on the row a person is
# reading and the document prints them in the order they were asked.
# The two questions nothing else in the system can answer.
#
# There were five. Three are now **absorbed rather than dropped**, which is a different thing: the
# house's ladder and the campaign layer answer them structurally, and a question a person is asked when
# the data already settles it teaches them the form is theatre.
#
#   `true`    — "does it stand on something in the house?" A platform bound to a ladder path stands on
#               something BY CONSTRUCTION. Now computed: see strategy.ladder_findings().
#   `elastic` — "does every channel get something to do?" Now the campaign's role-by-rung table, which
#               names what each medium DOES rather than asking whether it has anything.
#   `tension` — "is something being resolved?" Moved DOWN to the campaign, where it belongs: the
#               campaign's `insight` IS the tension, and it is a required field there. A platform lasts
#               years and does not itself argue; a campaign does.
#
# What is left are the two judgements no model and no schema can make. Both need a person, and both are
# about the platform rather than about any campaign off it.
JUDGED = {
    "ours":     "Could a competitor sign it? Cover the logo and read it again. If the nearest competitor "
                "could run it on Monday, it is a category truth, not a platform.",
    "durable":  "Does it survive three years? If it dies with the promotion that launched it, it is a "
                "campaign, not a platform — say so and build it as one. The mechanic has to survive its "
                "twentieth execution, not its first three.",
}

# The same two questions, split at the question mark into the ASK and the WHY.
#
# Both halves live here rather than only in the client because there were two consumers with two
# different needs and they collided on screen. The document prints the whole question standalone, so
# `JUDGED` has to stay whole. The card wants a short bold headline with the elaboration in grey under it,
# so the client carried its own split copy — and then took the server's whole question for the headline
# and its own elaboration for the body, printing the elaboration twice, verbatim, one line apart.
#
# Deriving both halves from the one string means the card can stop keeping a copy: there is nothing left
# to disagree with.
def _split_ask(q: str) -> tuple[str, str]:
    head, mark, rest = q.partition("?")
    return (head + mark).strip(), rest.strip() if mark else ("", q.strip())


JUDGED_ASK = {k: _split_ask(v)[0] for k, v in JUDGED.items()}
JUDGED_WHY = {k: _split_ask(v)[1] for k, v in JUDGED.items()}

# Where the retired three went, kept so a reader of an older file knows why their verdict stopped being
# asked for. A person's own `verdicts` are stored unfiltered and survive; only the model's reading of a
# question nobody asks any more falls away.
RETIRED_TESTS = {
    "true": "computed — strategy.ladder_findings()",
    "elastic": "campaign.roles — what each medium does",
    "tension": "campaign.insight — required there",
}

# The screen and this module have to name the same five tests, and they did not. The fifth was `durable`
# on the screen — *does it survive three years?* — and `repeat` here. Same question, different key, so
# every model verdict on it was written to a key no row read: the fifth test silently had no model
# column, and could never register a disagreement however far the two readings diverged.
#
# The screen's key wins. Its words are the ones a person actually answers, and a stored file is easier to
# read through a map than to rewrite. Anything already saved under the old key is translated on the way
# out rather than migrated, so nothing on disk has to be touched to become correct.
_JUDGED_ALIASES = {"repeat": "durable"}


def normalise_judged(d: dict | None) -> dict:
    """Model verdicts keyed the way the screen keys them, with unknown keys dropped."""
    out: dict[str, dict] = {}
    for k, v in (d or {}).items():
        key = _JUDGED_ALIASES.get(str(k), str(k))
        if key in JUDGED and isinstance(v, dict):
            out[key] = v
    return out


def judge(p: dict, item_id: str, house: dict | None = None) -> tuple[dict, str]:
    """A model's verdict on the five tests, with its reasoning. Returns (verdicts, note).

    **Stored separately from the person's.** A model is a fast, harsh, tireless first reader and it is
    genuinely useful here — but the five tests are judgements somebody has to own, and a verdict that
    silently replaced theirs would turn the layer into a checkbox. So this writes to `judged`, the human
    writes to `verdicts`, and where they disagree the screen can show both. Disagreement is the useful
    signal, not a problem to resolve automatically.
    """
    it = next((x for x in p.get("platforms", []) if x["id"] == item_id), None)
    if not it:
        return {}, "No such platform in this set."
    if not str(it.get("idea") or "").strip():
        return {}, "There is no platform to test yet."
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {}, "No ANTHROPIC_API_KEY — the five tests are yours to answer."

    basis = house_basis(house)
    mech = test_platform(it, basis)
    prompt = "\n".join([
        "You are the hardest reader this idea will meet, and you are on the brand's side. Be specific "
        "and be brief. A verdict with a vague reason is worth nothing.",
        "\n\n---\nTHE BRAND\n" + brandprofile.voice_block(brandprofile.resolve(house, p)),
        "\n\n---\nTHE PLATFORM",
        f"Name: {it.get('name') or '(unnamed)'}",
        f"Idea: {it.get('idea')}",
        f"Mechanic: {it.get('mechanic') or '(none named)'}",
        f"Expressed so far in: {', '.join(k for k, v in (it.get('expressions') or {}).items() if str(v or '').strip()) or 'nothing yet'}",
        "\n\n---\nTHE HOUSE IT CLAIMS TO LADDER TO",
        "Core: " + "; ".join(basis["core"] or ["(none)"]),
        f"Emotional: {basis['emotional'] or '(none)'}",
        f"Functional: {basis['functional'] or '(none)'}",
        "Reasons to believe:\n" + ("\n".join(
            f"  - {r['text']}" + ("" if r["sourced"] else "  [UNSOURCED]") for r in basis["rtbs"])
            or "  (none chosen — anything this platform claims rests on an assertion)"),
        ("MUST NOT DO: " + "; ".join(basis["avoid"])) if basis["avoid"] else "",
        "\n\n---\nWHAT THE MECHANICAL CHECK ALREADY FOUND — do not just restate it, argue with it where "
        "you disagree:\n" + "\n".join(f"  {k}: {v.get('detail','')}" for k, v in mech.items()),
        "\n\n---\nNOW JUDGE IT ON FIVE",
        "\n".join(f"  {k} — {q}" for k, q in JUDGED.items()),
        "\nFor each: a verdict of `holds`, `weak` or `fails`, and ONE clause saying why — naming the "
        "thing, not the quality. 'A competitor could say this' is useless; 'Amul could run this on "
        "Monday with the same words' is a finding.",
        "Where a test fails, say in `fix` what would have to change. Not 'make it stronger'.",
        'Return ONLY JSON: {"judged":{"' + '":{"verdict":"holds|weak|fails","note":"...","fix":"..."},"'.join(JUDGED)
        + '":{"verdict":"holds|weak|fails","note":"...","fix":"..."}}}',
    ])
    data, err = jsonout.ask_json(prompt, max_tokens=1800)
    if data is None:
        return {}, f"Judging failed: {err}"
    raw = normalise_judged(data.get("judged") or data)
    out = {}
    line = str(it.get("idea") or "").strip()
    for k in JUDGED:
        v = raw.get(k)
        if isinstance(v, dict) and str(v.get("verdict") or "").strip():
            out[k] = {"verdict": str(v["verdict"]).strip().lower(),
                      "note": str(v.get("note") or "").strip(),
                      "fix": str(v.get("fix") or "").strip(),
                      # The sentence it read. A verdict on a line that has since been rewritten is not
                      # wrong, it is about something else — and without this there is no way to know.
                      "for_line": line,
                      "by": "model", "at": _now()}
    if not out:
        return {}, "No usable verdicts came back."
    return out, ""


def _route_spread(basis: dict, n: int) -> str:
    """How the `n` routes must differ — anchored to this house's own pillars and RTBs.

    They used to differ by generic archetype: what the brand does for people, a category tension, a
    ritual it owns, a truth about how it is made, an enemy. Those are fine shapes and they produced three
    genuinely different ideas — but they float free of the house. A platform that does not obviously
    ladder to a pillar is one nobody can defend in the room, and the five tests below cannot check it
    either, because there is nothing to check it against.

    So the spread is the house's own structure: one route out of the emotional pillar, one out of the
    functional, and the rest bridging or working the core. Each names the reason-to-believe it stands on,
    **by id**, which is what makes the ladder checkable rather than asserted.

    Unsourced RTBs are named as such. A platform may dramatise one — that is often exactly the idea that
    then earns its evidence — but it has to know it is standing on something nobody has proved yet.
    """
    emo, fun = basis.get("emotional", ""), basis.get("functional", "")
    rtbs = basis.get("rtbs") or []
    e_rtbs = [r for r in rtbs if r["pillar"] == "emotional"]
    f_rtbs = [r for r in rtbs if r["pillar"] == "functional"]

    lines = [f"The {n} must differ in KIND, not in wording — and the kinds come from this house, not "
             f"from a list of archetypes. Spread them like this:\n"]
    slot = 1
    if emo:
        lines.append(f"  {slot}. Out of the EMOTIONAL message — \"{emo}\" — dramatising one of its "
                     f"reasons to believe. What the brand repeatedly DOES that earns that feeling.")
        slot += 1
    if fun:
        lines.append(f"  {slot}. Out of the FUNCTIONAL message — \"{fun}\" — dramatising one of its "
                     f"reasons to believe. The demonstrable thing, made into a repeatable act.")
        slot += 1
    while slot <= n:
        lines.append(f"  {slot}. A route that BRIDGES the two, or works the core message directly — but "
                     f"it must still name the reason to believe it rests on.")
        slot += 1

    if rtbs:
        lines.append("\nThe reasons to believe you may build on, by id. Name the one your platform "
                     "dramatises in `rtb_id`:")
        for r in rtbs:
            mark = "" if r["sourced"] else "   [UNSOURCED — you may build on it, but say so in `caveat`]"
            lines.append(f"  {r['id']} ({r['pillar']}): {r['text']}{mark}")
    else:
        lines.append("\nThis house has no reasons to believe chosen yet, so every platform here rests on "
                     "an assertion. Say that in each `caveat` — it is the thing that will be asked first.")

    lines.append("\nThree rephrasings of one idea are one platform, and offering them as three is worse "
                 "than offering one honestly — say so in `caveat` if you only really have one.\n")
    return "\n".join(lines) + "\n"


def draft_prompt(core: str, brief: dict | None, house: dict | None = None, n: int = 3,
                 build_from: dict | None = None, steer: str = "", brand_mode: str = "") -> str:
    """The instruction behind *Draft the platform* — `n` first lines from a core message and a brief.

    Narrower than `prompt_for` above, which scores platforms against the five tests. This answers the
    opening move on the Idea Platform screen, and it opens with **three**, not one.

    It used to draft one, on the reasoning that a screen asking somebody to commit to a sentence should
    not hand them a list. That was wrong in practice: a single draft becomes the answer by being the only
    thing on the page, and there is no way to tell a strong platform from a lonely one. Three that differ
    in kind make the choice visible, and `build_from` lets somebody take one further rather than
    re-rolling — the two motions asked for, iterate and generate fresh.

    What it must not do is compose. Two strings glued together would read like an idea and be nobody's —
    so it is asked for a claim about the world, and told to say when it does not have one.

    Phase 2 (BRAND_GROUNDING_MODES_PLAN.md): `brand_mode="general"` blocks BOTH unconditional pulls this
    function used to make — `brandprofile.resolve(brief, house)` (which falls back to whichever brand is
    globally ACTIVE once more than one is on file, the same footgun this project has fixed everywhere
    else) and `house_basis(house)` (the house's real pillars/RTBs/avoid-list). `core` is the caller's job
    to blank for General, same as `plan.py`'s own `prompt_for` — this function trusts what it's handed.
    """
    _general = str(brand_mode or "").strip().lower() == "general"
    b = None if _general else brandprofile.resolve(brief, house)
    basis = house_basis(None if _general else house)
    out = [_skill_text(), "\n\n---\nTHE BRAND\n" + brandprofile.voice_block(b)]

    if core:
        out.append(f"\n\n---\nTHE CORE MESSAGE THIS EXPRESSES (verbatim, chosen by a person)\n{core}")
    else:
        out.append("\n\n---\nNO CORE MESSAGE\nNo messaging house core has been chosen. Do not invent "
                   "one and do not write as though a message were settled — the platform has to stand "
                   "on the brief alone, and it should read as the narrower thing that is.")
    if basis["emotional"] or basis["functional"]:
        out.append(f"\nEmotional pillar: {basis['emotional'] or '(none)'}"
                   f"\nFunctional pillar: {basis['functional'] or '(none)'}")
    if basis["rtbs"]:
        sourced = [r for r in basis["rtbs"] if r["sourced"]]
        out.append("\nReasons to believe that are SOURCED and may be dramatised:\n"
                   + ("\n".join(f"  - {r['text']}" for r in sourced) or "  (none — nothing is sourced yet)"))
    if basis["avoid"]:
        out.append("\nMUST NOT DO:\n" + "\n".join(f"  - {a}" for a in basis["avoid"]))

    if brief:
        keep = [(k, str(v).strip()) for k, v in brief.items() if str(v or "").strip()]
        out.append("\n\n---\nTHE BRIEF IT ANSWERS\n"
                   + "\n".join(f"{k}: {v}" for k, v in keep))
    else:
        out.append("\n\n---\nNO BRIEF\nNothing was pulled from the brief library. Work from the message "
                   "above and say what the platform would need from a brief to go further.")

    n = max(1, min(6, int(n or 1)))
    # What the person asked for on this round. Placed above the instruction so it shapes the routes
    # rather than being appended as an afterthought — "make them sharper", "none of these work, go at
    # the enemy", "keep the second one's mechanic but change the territory".
    if str(steer or "").strip():
        out.append("\n\n---\nWHAT THE PERSON ASKS FOR ON THIS ROUND — this outranks the spread below "
                   "where the two disagree:\n" + str(steer).strip())
    if build_from:
        out.append(
            "\n\n---\nBUILD ON THIS ONE — DO NOT REPLACE IT\n"
            f"name: {build_from.get('name','')}\nline: {build_from.get('line','')}\n"
            f"mechanic: {build_from.get('mechanic','')}\n\n"
            f"Give {n} developments OF THIS PLATFORM. Each keeps its central idea and takes it somewhere "
            "the original did not go — a sharper mechanic, a wider territory, a different way in. Someone "
            "reading yours beside the original must be able to say what changed.\n"
            "A fresh platform is a wrong answer here. If the idea genuinely cannot be developed further, "
            "say that in `caveat` rather than quietly swapping it for a new one.")
    else:
        out.append(
            f"\n\n---\nNOW: {n} PLATFORMS, EACH AS A FIRST LINE\n"
            "A name a room can repeat in two or three words, and one sentence stating the platform.\n\n"
            + (_route_spread(basis, n) if n > 1 else ""))
    out.append(
        "Each must be a claim about what the brand DOES, not a description of how it feels. The test "
        "that matters: could a person read your sentence and know what to make next week, and the week "
        "after? If a sentence only yields one film, that is a concept — include it anyway, and say so in "
        "its `caveat`.\n\n"
        "Do not restate the core message. The core says what is true; a platform says what we do about "
        "it repeatedly.\n\n"
        'Return ONLY JSON: {"platforms":[{"name":"two or three words","line":"one sentence",'
        '"mechanic":"the repeatable device, if you can name it","kind":"which route above this is",'
        '"pillar":"emotional|functional|both","rtb_id":"the id of the RTB it dramatises",'
        '"rtb":"that RTB in your own words, one clause",'
        '"caveat":"what is thin about this, or empty"}]}'
        + (f"\nExactly {n} entries." if n > 1 else ""))
    return "\n".join(out)


def draft_lines(core: str = "", brief: dict | None = None, house: dict | None = None,
                n: int = 3, build_from: dict | None = None,
                steer: str = "", brand_mode: str = "") -> tuple[list[dict], str]:
    """Draft `n` opening platforms. Returns (ideas, note).

    **Never invents from nothing.** With neither a core message nor a brief there is no claim to make,
    and a sentence produced anyway would be a plausible-sounding platform with no source — the exact
    thing the five tests below it exist to catch, arriving pre-laundered.

    Every result is marked `source: "model"` and none is saved. Adoption goes through `/idea-platform`,
    where a person's edit re-sources it to `user` — so a drafted line that nobody rewrites stays visibly
    the model's.

    Pass `build_from` to develop an existing platform instead of opening fresh ones. `built_from` comes
    back on each result so the screen can show which one it grew out of; without that, an iteration is
    indistinguishable from a re-roll and the history of the idea is lost.
    """
    core = (core or "").strip()
    n = max(1, min(6, int(n or 3)))
    if not core and not (brief and any(str(v or "").strip() for v in brief.values())) and not build_from:
        return [], ("Nothing to draft from. Choose a messaging house with a core message, or pull a "
                    "brief — a platform is a claim about something, not a sentence about nothing.")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return [], ("No ANTHROPIC_API_KEY — the sources are held and the fields are yours to write. "
                    "A line you write yourself counts as sourced.")
    data, err = jsonout.ask_json(draft_prompt(core, brief, house, n, build_from, steer, brand_mode),
                                 max_tokens=500 + 450 * n)
    if data is None:
        return [], f"Drafting failed: {err}"
    # Tolerate the singular shape: an earlier version of this prompt asked for one object, and a model
    # that answers in that shape is not wrong, just old.
    raw = data.get("platforms")
    if not isinstance(raw, list):
        raw = [data] if data.get("line") else []
    out = []
    for i, o in enumerate(raw[:n]):
        line = str((o or {}).get("line") or "").strip()
        if not line:
            continue
        # **No `id`.** A draft is not saved anywhere, so it has no server identity, and emitting one that
        # looks like a server id is a lie the client cannot detect. It did exactly that: the screen does
        # `serverId: o.id || null` and then sends the id when it has one — so it posted `"d1"` back as
        # though the server held a platform by that name, and `build_on` 404'd on every Build-on-this.
        # `draft_id` is for React keys and nothing else; with no `id`, the client correctly falls through
        # to sending the whole object inline, which is the only thing that can reconstruct the idea.
        out.append({"draft_id": f"d{i+1}",
                    "name": str(o.get("name") or "").strip(),
                    "line": line,
                    "mechanic": str(o.get("mechanic") or "").strip(),
                    "kind": str(o.get("kind") or "").strip(),
                    # Which reason-to-believe this platform dramatises. The ladder, made checkable.
                    "rtb_id": str(o.get("rtb_id") or "").strip(),
                    "rtb": str(o.get("rtb") or "").strip(),
                    "pillar": str(o.get("pillar") or "").strip(),
                    "caveat": str(o.get("caveat") or "").strip(),
                    "source": "model",
                    "built_from": (build_from or {}).get("id", "") or "",
                    "built_from_name": (build_from or {}).get("name", "") or "",
                    "stood_on": {"core": core, "brief": bool(brief)}})
    if not out:
        return [], "No lines came back — write one yourself."
    return out, ""


def draft_line(core: str = "", brief: dict | None = None,
               house: dict | None = None) -> tuple[dict, str]:
    """The single-draft shape, kept for callers that want one. Returns (idea, note)."""
    out, note = draft_lines(core, brief, house, 1)
    return (out[0] if out else {}), note


# --- generation --------------------------------------------------------------------------------

def _skill_text() -> str:
    f = os.path.join(_SKILL, "SKILL.md")
    return open(f, encoding="utf-8").read() if os.path.exists(f) else ""


def prompt_for(p: dict, house: dict | None, build_from: dict | None = None, n: int = 3,
               extra: str = "", anchors: str = "", rules: str = "") -> str:
    basis = house_basis(house)
    out = [_skill_text(),
           "\n\n---\nTHE BRAND\n" + brandprofile.voice_block(brandprofile.resolve(house, p)),
           "\n\n---\nTHE MESSAGING HOUSE THIS EXPRESSES"]
    out.append("Core message: " + "; ".join(basis["core"]))
    out.append(f"Emotional pillar: {basis['emotional'] or '(none chosen)'}")
    out.append(f"Functional pillar: {basis['functional'] or '(none chosen)'}")
    if basis["rtbs"]:
        out.append("Reasons to believe — name which one your platform dramatises, by id:")
        for r in basis["rtbs"]:
            mark = "SOURCED" if r["sourced"] else "UNSOURCED — cannot carry a platform's proof"
            out.append(f"  [{r['id']}] ({r['pillar']}) {r['text']}  [{mark}]")
    if basis["codes"]:
        out.append("Cultural codes to use: "
                   + "; ".join(f"{c['text']} ({c['tag']})" for c in basis["codes"]))
    if basis["avoid"]:
        out.append("MUST NOT DO — a platform requiring any of these is unusable:\n"
                   + "\n".join(f"  - {a}" for a in basis["avoid"]))

    existing = p.get("platforms") or []
    if existing:
        out.append("\n\n---\nALREADY ON THE TABLE — do not repeat these or reword them")
        for it in existing:
            out.append(f"  - {it.get('name','(unnamed)')}: {it.get('idea','')} "
                       f"| mechanic: {it.get('mechanic','')}")

    if anchors:
        out.append("\n\n---\n" + anchors)
    if rules:
        out.append("\n\n---\n" + rules)
    if extra.strip():
        out.append("\n\n---\nTHE USER ADDS\n" + extra.strip())

    if build_from:
        out.append(
            f"\n\n---\nNOW: BUILD ON THIS ONE — do not replace it\n"
            f"  {build_from.get('name','(unnamed)')}: {build_from.get('idea','')}\n"
            f"  mechanic: {build_from.get('mechanic','')}\n"
            f"  territory: {build_from.get('territory','')}\n"
            f"  expressed so far: "
            f"{', '.join(k for k, v in (build_from.get('expressions') or {}).items() if v) or 'nowhere'}\n\n"
            f"Give {n} developments of THIS platform. Keep its idea recognisable — sharpen the mechanic, "
            f"reach media it has not reached, or find a harder proof. A development that is really a "
            f"different platform is not what was asked for.")
    else:
        out.append(
            f"\n\n---\nNOW: {n} PLATFORMS, and make them disagree\n"
            f"They must differ on the BET — which pillar leads, which proof is dramatised, which "
            f"cultural code is used, who the protagonist is. Three that differ by adjective are one "
            f"platform. If two could be briefed to the same director and come back similar, replace one.")

    out.append(
        "\nFor each, express it in every medium you honestly can — and write nothing rather than "
        "something invented where it has nothing to say:\n"
        + "\n".join(f"  {k}: {v}" for k, v in EXPRESSIONS.items())
        + "\n\nReturn ONLY JSON:\n"
          '{"platforms":[{"name":"two or three words a room can repeat",'
          '"idea":"one sentence","mechanic":"the repeatable device — what rule generates the next '
          'execution","territory":"the world it lives in","proof":"what it demonstrates",'
          '"rtb":"the id of the reason-to-believe it dramatises","why":"why this bet",'
          '"expressions":{'
        + ", ".join(f'"{k}":"..."' for k in EXPRESSIONS) + '}}]}')
    return "\n".join(out)


def generate(p: dict, house: dict | None, build_from_id: str = "", n: int = 3, extra: str = "",
             anchors: str = "", rules: str = "") -> tuple[dict, str]:
    """Fresh options, or developments of one. Never replaces what is already there.

    A discarded round is often where somebody finds the thing they actually wanted, and a tool that
    silently overwrites teaches people to stop exploring.
    """
    ok, why = ready(house)
    if not ok:
        return p, why
    build_from = None
    if build_from_id:
        build_from = next((x for x in p["platforms"] if x["id"] == build_from_id), None)
        if not build_from:
            return p, "No such platform to build on."
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return p, "No ANTHROPIC_API_KEY — platforms can still be written by hand, and a hand-written "\
                  "one counts as sourced."
    data, err = jsonout.ask_json(prompt_for(p, house, build_from, n, extra, anchors, rules), max_tokens=4000)
    if data is None:
        return p, f"Generation failed: {err}"

    p["round"] = p.get("round", 0) + 1
    for item in (data.get("platforms") or []):
        if isinstance(item, dict) and str(item.get("idea") or "").strip():
            p = add(p, item, source="model", built_from=build_from_id)
    p["generated_under"] = house_basis(house)["signature"]
    return save(p), ""
