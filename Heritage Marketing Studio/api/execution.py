"""execution.py — one envelope, several producers.

    Brief -> Messaging house -> Communication plan -> Executions

Several kinds of work come out the far end — social, video, POS material, on-ground activation, media
plan, trade incentives and PR. Building an engine per kind would produce as many drifting definitions
of "what is this ad trying to do", so there is one envelope and the kinds differ only in what they
*make*. (Deliberately not numbered here: this sentence said "six" through the addition of a seventh,
and a count written into prose is a count that goes stale silently. `MANIFEST` is the list.)

An execution is briefed by six fields, and every one of them **points at a row in the plan** rather
than holding free text:

    audience · pillar · channel · occasion · measure · message

That is the mechanism, not bookkeeping. An execution cannot say something the plan does not say, and
if it needs a field the plan has no row for, that is a gap in the plan rather than a note in a brief.

**Staleness is value-based, not hash-based.** When an execution is briefed, the resolved *values* of
those rows are copied onto it. Later the current values are compared field by field, so a stale
execution can say:

    "channel role was proof, now conversion"

rather than "something above this changed". That difference is what makes *re-brief against the new
values* a single button instead of an investigation. Hashes tell you that something moved; values tell
you what, which is the only version anybody can act on.

Producers are declared in MANIFEST rather than discovered, so the client renders a panel from data and
a new kind needs no client change. `media` is deliberately in that list with `message_required` false:
a media plan allocates weight and money, and forcing a message field onto it would only get filled with
something untrue.
"""
from __future__ import annotations

import json
import os
import time
import uuid

import briefstore
import campaign as campaign_mod
import findings as findings_mod
import ideas as ideas_mod
import media
import plan as plan_mod
import tenancy


def brief_for(p: dict | None, house: dict | None) -> dict | None:
    """The brief this execution answers to — the plan's, or the house's when the plan has none.

    The plan wins because it is the more specific document: a plan written against a revised brief is
    the newer decision, and inheriting the house's would quietly undo it.
    """
    bid = str((p or {}).get("brief_id") or "") or str((house or {}).get("brief_id") or "")
    return briefstore.load(bid) if bid else None


def platform_for(house: dict | None) -> dict | None:
    """The chosen idea platform for this house, or None. Optional throughout."""
    if not house:
        return None
    return ideas_mod.chosen_platform(ideas_mod.for_house(house.get("id", "")))

# Resolved through tenancy so one deployment can hold several companies. The name is kept
# so every reader in this module is unchanged.
EXEC_DIR = tenancy.dir("executions")
# What each kind is briefed for, and what it owes. The client renders its panel from this.
#
# `message_required` false is not a shortcut — see the module note on `media`.
# `proof_obligation.required` false means this kind is never asked to make a claim believable, so it
# cannot be caught by the proof gate. Anything that CAN carry a claim must be able to be.
MANIFEST: dict[str, dict] = {
    "social": {
        "label": "Social", "medium": "social",
        "message_required": True, "proof_obligation": {"required": True},
        "makes": ["post", "carousel", "reel"],
        "needs": ["audience", "pillar", "channel", "occasion", "measure", "message"],
    },
    "video": {
        "label": "Film", "medium": "tv",
        "message_required": True, "proof_obligation": {"required": True},
        "makes": ["script", "shoot board", "film"],
        "needs": ["audience", "pillar", "channel", "occasion", "measure", "message"],
    },
    "posm": {
        "label": "POS material", "medium": "posm",
        "message_required": True, "proof_obligation": {"required": True},
        "makes": ["key visual", "sizes", "adaptations"],
        "needs": ["audience", "pillar", "channel", "occasion", "measure", "message"],
    },
    "activation": {
        "label": "On-ground activation", "medium": "on-ground",
        "message_required": True, "proof_obligation": {"required": True},
        "makes": ["idea", "stall", "van", "promoter uniform", "promoter education"],
        "needs": ["audience", "pillar", "channel", "occasion", "measure", "message"],
    },
    # `media` is RETIRED as a producer — see RETIRED_KINDS below. It stays in MANIFEST so that
    # executions already stored against it still load, still resolve their six fields, and still
    # report their own staleness. Nothing is deleted; it is simply no longer offered.
    "media": {
        "label": "Media plan", "medium": "",
        # A media plan allocates; it does not speak. That is also why it stopped being a producer.
        "message_required": False, "proof_obligation": {"required": False},
        "makes": ["channel weights", "flighting"],
        "needs": ["audience", "channel", "occasion", "measure"],
        "retired": True,
    },
    "incentive": {
        "label": "Trade incentive", "medium": "trade",
        "message_required": True, "proof_obligation": {"required": True},
        "makes": ["scheme", "mechanic", "leakage control"],
        "needs": ["audience", "pillar", "channel", "occasion", "measure", "message"],
    },
    # PR. `proof_obligation.required` is True and that is the whole point of the kind: PR's role is
    # "the functional truth, earned" — it carries a proof somebody else vouches for, so it is exactly
    # the medium that MUST be catchable by the proof gate. A PR execution with nothing provable behind
    # it is a press release nobody runs.
    #
    # `makes` is the media map, the release and the kit rather than a piece of artwork, because the
    # deliverable here is not a thing to look at. That is why PR needed a producer of its own instead
    # of being served by the social or POSM makers.
    "pr": {
        "label": "PR", "medium": "pr",
        "message_required": True, "proof_obligation": {"required": True},
        "makes": ["media map", "press release", "media kit"],
        "needs": ["audience", "pillar", "channel", "occasion", "measure", "message"],
    },
}

# Producers that are no longer offered, and where their work went instead. Same shape and the same
# reasoning as `strategy.RETIRED_LAYERS`: nothing is deleted, the destination is recorded, and stored
# documents keep loading.
#
# `media.RETIRED["media"]` has said since 20 August that a schedule is not a medium and that it "has
# also left the Execution producers" — but it added that where it lands "is a separate call and has not
# been made". This is that call, recorded in the place a reader would look for it.
RETIRED_KINDS: dict[str, dict] = {
    "media": {
        "label": "Media plan",
        "went": "the Media tab — its own top-level screen, not a producer",
        "why": "A producer makes one thing that says something. A media plan is orthogonal to that: it "
               "decides how much each producer gets. Listed beside Social it read as a sibling of the "
               "channels it actually sizes, which is why this screen had to special-case it in six "
               "places — skipping the message load, exempting it from the proof requirement, and four "
               "more. `message_required: False` was the first sign; a producer that cannot carry a "
               "message is not one.",
        "also": "Cardinality differs too — four social executions across four phases, but one media "
                "plan. And competitive intelligence and the calendar have no execution analogue at "
                "all.",
    },
}


# --------------------------------------------------------------------------------------
# Prompt guides
# --------------------------------------------------------------------------------------
#
# The producers accept a typed prompt. A prompt box with no guidance produces adjectives, and adjectives
# produce generic work — so each producer gets a guide.
#
# Three rules the content follows, all of them learned the hard way elsewhere in this project:
#
# 1. **The worked example is in a DIFFERENT category from the client's.** A dairy example on a dairy
#    brand gets copy-pasted, and forty briefs come back describing the same milk. An example from
#    cement or shampoo has to be translated, and translating it is the thinking.
# 2. **The failure modes are named.** People learn faster from "this is what a bad one looks like and
#    why" than from a description of a good one. Every `avoid` line below is something a real prompt
#    has actually done.
# 3. **The prompt is ADDITIVE, never an override.** Six references to plan rows already brief the
#    execution. A prompt that could overrule the plan's message would turn the plan into decoration,
#    and the guide says so in `cannot_override` rather than leaving it to be discovered.

PROMPT_GUIDE: dict[str, dict] = {
    "social": {
        "what": "What the feed does with the idea, not what it says at someone.",
        "asks": ("Name the moment somebody is scrolling in. Name the thing they SEE first, before any "
                 "words. Then say what the caption has to do that the picture cannot."),
        "example": ("A cement brand: 'Open on a mason's thumbnail running along a finished joint, close "
                    "enough to see the grit. He does it twice. The caption carries the number of hours "
                    "before it takes load — the picture cannot say a number.'"),
        "avoid": ("'Engaging post about our quality' — engaging is a hope, not an instruction, and "
                  "quality is the category's word, not this brand's. Adjectives with no camera in them "
                  "produce stock photography."),
        "cannot_override": "the audience, channel, occasion, measure or message from the plan",
    },
    "posm": {
        "what": "What survives being read in two seconds at arm's length, in bad light.",
        "asks": ("One instruction or one number, and where the eye lands first. Say what gets cut if it "
                 "does not fit — because it will not fit."),
        "example": ("A shampoo brand: 'Shelf strip. The eye lands on 3x. Everything else is smaller "
                    "than that, including the pack. If the line does not fit, the line goes, not the "
                    "number.'"),
        "avoid": ("A headline plus a subhead plus a claim plus a logo. Four things at arm's length is "
                  "zero things. Naming what to cut is the most useful sentence in a POSM prompt."),
        "cannot_override": "the format list, the ratio, or the mandatories from locked copy",
    },
    "activation": {
        "what": "What happens when somebody walks up. A venue, a person, and a thing they do.",
        "asks": ("Say what the passer-by physically does — not what they feel. Then say what they leave "
                 "holding, and what the promoter says in one sentence."),
        "example": ("A paint brand: 'A wall panel, half done. She is handed a roller and does one "
                    "stripe herself. She leaves with the shade card matching the stripe she made, and "
                    "the promoter's line is about how long that stripe will hold its colour.'"),
        "avoid": ("'An immersive brand experience.' Nobody can build that. A verb the passer-by "
                  "performs is buildable; an atmosphere is not."),
        "cannot_override": "the occasion, the measure, or the proof obligation for the channel's role",
    },
    "video": {
        "what": "The film a producer shoots. Observed behaviour in a real place, performed.",
        "asks": ("Name a behaviour you could film without asking anyone to act. Name the place and one "
                 "thing in it that would only be there in real life. Say what turns — the film has to "
                 "resolve something, or nothing downstream has a feeling to remind anyone of."),
        "example": ("A tyre brand: 'A father reverses out of a narrow gate his wife is guiding him "
                    "through, at 6am, in slippers. The turn is that he stops for the dog he cannot see "
                    "and she can. Not the tyre — the trust.'"),
        "avoid": ("Stacking adjectives — 'cinematic, emotional, heartwarming, premium'. Those describe "
                  "how you want the result judged, not what the camera does. The reference films that "
                  "work are specific about behaviour and silent about mood."),
        "cannot_override": "the beat plan's roles, the clip lengths, or the endframe's clear space",
    },
    "incentive": {
        "what": "What makes a retailer want to say it, in his terms and not the consumer's.",
        "asks": ("Say what he earns, at what volume, and when he actually sees the money. Then the one "
                 "line his customers will repeat."),
        "example": ("A biscuit brand: 'Three slabs, paid monthly, visible on the invoice. His line is "
                    "about the pack that does not sit — because what he fears is stock that does not "
                    "move, not margin he cannot get.'"),
        "avoid": ("Handing him the consumer line. It is the most common way a good campaign dies at "
                  "the counter — he will not say a sentence written for somebody else."),
        "cannot_override": "the price architecture or the trade terms already recorded",
    },
    "pr": {
        "what": "What a journalist would run without being asked twice.",
        "asks": ("Name what is verifiably new — a first, an only, a number nobody has published. Then "
                 "say who outside the company can confirm it."),
        "example": ("A steel brand: 'The plant's water recycling figure, audited, published before "
                    "anybody asked for it. The confirmer is the auditor, not the plant head.'"),
        "avoid": ("A launch with no news in it. 'We are pleased to announce' is a press release about "
                  "a company's feelings, and a desk will not run it."),
        "cannot_override": "the declared message set, or the descent gate's refusal of a row PR cannot carry",
    },
}


def prompt_guide(kind: str) -> dict:
    """The guide for one producer, or an honest empty for a kind that has none yet."""
    g = PROMPT_GUIDE.get(str(kind or "").strip().lower())
    if not g:
        return {"available": False, "kind": kind,
                "why": f"No prompt guide written for {kind!r} yet. Rather than show a generic one, this "
                       f"says so — a guide that could apply to any producer teaches nothing about this "
                       f"one."}
    return {"available": True, "kind": kind, **g,
            # Stops BEFORE the list. `cannot_override` is returned as its own field so a screen can
            # place it beside the prompt box, and interpolating it here too printed the same clause
            # twice, back to back.
            "additive": ("This prompt is added to the brief, not substituted for it. The plan's "
                         "audience, channel, occasion, measure and message still apply, and a prompt "
                         "cannot overrule them.")}


def live_kinds() -> dict[str, dict]:
    """The producers still on offer. What a client should build its tab list from."""
    return {k: v for k, v in MANIFEST.items() if not v.get("retired")}


STATUSES = ("briefed", "made", "approved", "shipped")

# Which plan layer each reference field is drawn from.
REFS = {"audience": "audiences", "channel": "channels", "occasion": "phases", "measure": "measures"}


def kind_label(kind: str) -> str:
    """A producer's label as it should read mid-sentence.

    Every call site wanted `label.lower()` — right for "Film" -> "a film", wrong the moment a label is
    an initialism: PR became "a pr needs its own line". A label carrying no lowercase letters is an
    acronym and is left alone.
    """
    label = str((MANIFEST.get(kind) or {}).get("label") or kind)
    return label if label.upper() == label else label.lower()


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


def _path(eid: str) -> str:
    return os.path.join(EXEC_DIR, f"{eid}.json")


def load(eid: str) -> dict | None:
    try:
        with open(_path(eid), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def save(e: dict) -> dict:
    os.makedirs(EXEC_DIR, exist_ok=True)
    e["updated"] = _now()
    tmp = _path(e["id"]) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(e, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, _path(e["id"]))
    return e


def executions(plan_id: str = "", kind: str = "") -> list[dict]:
    os.makedirs(EXEC_DIR, exist_ok=True)
    out = []
    for f in sorted(os.listdir(EXEC_DIR)):
        if not f.endswith(".json"):
            continue
        e = load(f[:-5])
        if not e:
            continue
        if plan_id and e.get("plan") != plan_id:
            continue
        if kind and e.get("kind") != kind:
            continue
        out.append(e)
    return out


# --- resolving the six fields -------------------------------------------------------------------

def _row(p: dict, layer: str, row_id: str) -> dict | None:
    for r in p.get("nodes", {}).get(layer, {}).get("rows", []):
        if r.get("id") == row_id:
            return r
    return None


def message_options(house: dict | None, kind: str) -> list[dict]:
    """The lines available to this kind of execution, in `campaign.jobs()`'s order of authority.

    A film and a shelf strip are different acts of communication, so an execution picks a line written
    for its own medium rather than truncating the core line.

    **The platform's expression comes first, then the house's medium line.** Same order as
    `campaign.jobs()`, and for the same reason: the expression is the most specific thing anybody
    decided about this medium, and it was decided *after* the idea existed.

    That order is not a preference, it is a live fix. The house's `medium` layer is RETIRED (see
    `strategy.RETIRED_LAYERS`) — its successor is the jobs table. This function still read
    `nodes["medium"]` directly, so on any house created after that retirement it returned `[]` for
    every kind, and `brief_from` then refused with *"write one in the message-by-medium layer"* —
    pointing a person at a screen that no longer exists. **Every execution on a fresh house was
    unbriefable.** Reproduced with a house carrying no `medium` node: social, video, posm, activation
    and incentive all returned zero options.

    Tags are also matched through `media.migrate` rather than compared raw. `MANIFEST` still spells
    activation's medium the old way (`on-ground`), so a line tagged with the current key `activation`
    matched nothing — the same rename that bit `campaign.jobs()` once already.
    """
    want = (MANIFEST.get(kind) or {}).get("medium") or ""
    if not house or not want:
        return []
    want_leaf, _ = media.migrate(str(want).strip().lower())
    out: list[dict] = []

    # 1. The platform's expression for this kind — the successor to the retired layer.
    plat = platform_for(house)
    if plat:
        expr = str((plat.get("expressions") or {}).get(kind, "") or "").strip()
        if expr:
            out.append({"id": "platform", "text": expr,
                        "note": f"the platform's expression for {kind_label(kind)}",
                        "tag": want_leaf, "medium": want_leaf, "source": "platform",
                        "platform": plat.get("name", "")})

    # 2. The house's own line for this medium, where one was written.
    node = house.get("nodes", {}).get("medium") or {}
    picked = set(node.get("chosen") or [])
    # `medium` duplicates `tag`. The client renders "medium — text" and falls back to bare text when the
    # key is absent, so this is the difference between a legible label and a bare line. Both names are
    # sent rather than renaming `tag`, because the house's own vocabulary calls it a tag.
    for o in node.get("options", []):
        if o.get("id") not in picked:
            continue
        leaf, _review = media.migrate(str(o.get("tag") or "").strip().lower())
        if leaf == want_leaf:
            out.append({"id": o["id"], "text": o["text"], "note": o.get("note", ""),
                        "tag": o.get("tag", ""), "medium": o.get("tag", ""), "source": "house"})
    return out


def brief_from(p: dict, house: dict | None, kind: str, sel: dict) -> tuple[dict, str]:
    """Build the six-field brief, resolving every reference to a value. Returns (brief, error).

    The resolved values are stored, not just the ids. That is what lets staleness name the field that
    moved, and it is also the audit trail: an execution shipped six months ago still says what the plan
    said at the time, even after the plan has been rewritten.
    """
    man = MANIFEST.get(kind)
    if not man:
        return {}, f"Unknown execution kind {kind!r}."

    brief: dict = {"kind": kind}

    for field, layer in REFS.items():
        if field not in man["needs"]:
            continue
        rid = str(sel.get(field) or "")
        if not rid:
            return {}, f"{field} is required — pick the {layer[:-1]} row from the plan."
        row = _row(p, layer, rid)
        if not row:
            return {}, f"No {field} row {rid!r} in this plan."
        cols = plan_mod.LAYER_BY_ID[layer]["cols"]
        brief[field] = {"id": rid, **{c: row.get(c, "") for c in cols}}

    # The pillar is inherited from the audience rather than chosen again. Letting an execution pick its
    # own pillar is how a brief ends up arguing the emotional case to an audience the plan assigned to
    # the functional one, and nothing downstream would ever catch it.
    if "pillar" in man["needs"]:
        inherited = str(brief.get("audience", {}).get("pillar", "")).strip().lower()
        if inherited not in ("emotional", "functional"):
            return {}, ("That audience carries no single pillar in the plan. Fix the audiences table "
                        "first — an execution cannot choose its own pillar.")
        brief["pillar"] = inherited

    # Role and measure must agree. The plan already warns about this; here it is refused, because a
    # reach channel briefed against a conversion measure produces work that will be judged a failure
    # whatever it achieves.
    if "measure" in man["needs"] and "channel" in man["needs"]:
        ch_role = str(brief["channel"].get("role", "")).strip().lower()
        m_role = str(brief["measure"].get("role", "")).strip().lower()
        if ch_role and m_role and ch_role != m_role:
            return {}, (f"That measure is for a {m_role} channel and {brief['channel'].get('channel')} "
                        f"is a {ch_role} channel. Judged on the wrong measure it will look like a "
                        f"failure whatever it achieves — pick a {ch_role} measure.")

    # The idea platform, if one has been chosen. **Optional and inherited, never selected here.** An
    # execution choosing its own platform would defeat the point: the coherence between the film and the
    # shelf strip comes from them descending from the same one. So this reads the house's chosen platform
    # and takes its expression for this kind — a glimpse of the idea, and the input the producer works
    # from. Absent, everything below still works; a finding says the work will not cohere with anything.
    # The brief, at every execution gate. It supplies **mandatories, tone and the business objective** —
    # deliberately not the audience and not the message. Those belong to the plan and the house, and an
    # execution that could read two definitions of its audience has no way to tell which one is real.
    brief_doc = brief_for(p, house)
    if brief_doc:
        c = brief_doc.get("canon") or {}
        brief["brief"] = {"id": brief_doc["id"], "title": brief_doc.get("title", ""),
                          "brand": c.get("brand", ""),
                          "mandatories": c.get("mandatories", ""),
                          "tone": c.get("toneOfVoice", ""),
                          "business_objective": c.get("businessObjective", "")}

    plat = platform_for(house)
    if plat:
        expr = str((plat.get("expressions") or {}).get(kind, "") or "").strip()
        brief["platform"] = {"id": plat["id"], "name": plat.get("name", ""),
                            "idea": plat.get("idea", ""), "mechanic": plat.get("mechanic", ""),
                            "expression": expr}

    # The CAMPAIGN and the HOUSE'S OWN CLAIM. Both were missing: an execution could see the brief and
    # the idea platform, but not the campaign the platform was turned into, and not the checkable fact
    # underneath it — so a producer worked from the idea without the proof or the proof axis.
    #
    # Attached for every kind, not just PR. Two code paths computing inheritance differently is the
    # failure this module's own header warns about ("six drifting definitions of what this ad is trying
    # to do"), and social and POSM want the axis just as much. PR is only where the gap became obvious,
    # because PR is the one medium whose entire job is carrying the proof.
    #
    # Additive and absence-tolerant: an execution briefed before this existed simply has no `campaign`
    # or `house` key, and every reader must guard — the same contract as `platform`, which has always
    # been optional.
    if house:
        pset = ideas_mod.for_house(house.get("id", ""))
        # `sel.get("campaign_id")` is the wiring fix: a campaign PICKED for this execution, not always
        # the platform's latest. Empty string still falls through to `campaign.get`'s own "most recent"
        # default, so an execution briefed before this existed, or briefed with no explicit pick, behaves
        # exactly as it always did.
        camp = campaign_mod.get(pset, str(sel.get("campaign_id") or "")) if pset else None
        if camp:
            # `axis` resolves the proof axis from the campaign's own divisions, falling back to the
            # bridge on its ladder path. `axis_source` travels with it so a producer is never shown a
            # borrowed axis as though it were written here — the same rule as `producers.stands_on`.
            brief["campaign"] = {
                "id": camp.get("id", ""), "name": camp.get("name", ""),
                "shape": camp.get("shape", ""), "ladder": camp.get("ladder", ""),
                "axis": campaign_mod.axis(house, camp),
                "axis_source": campaign_mod.axis_source(house, camp),
                # The big idea travels WITH its parent platform, never on its own. A producer shown an
                # idea with no territory behind it will treat the idea as the strategy — which is how a
                # platform gets quietly replaced by whatever this season's idea happened to be.
                # `available: False` when none is written, which is a real state: every execution can
                # still be briefed from the platform's per-medium expression.
                "big_idea": campaign_mod.big_idea(pset, camp.get("id", "")),
                # What this campaign becomes in THIS execution's own medium — the adaptation
                # `campaign.write_expressions` writes. `producers.stands_on` and Social's
                # `_execution_block` both read this ahead of the platform's own, unadapted expression.
                "expressions": camp.get("expressions") or {},
            }
        basis = ideas_mod.house_basis(house)
        # The claim is resolved through `claim_fact`, which reads `rtb_id` only and reports
        # `available: False` rather than guessing when the option it pointed at is gone. A producer
        # seeing `available: False` knows the claim is unproven, which is the useful state to show.
        brief["house"] = {
            "id": house.get("id", ""),
            "core": basis.get("core") or [],
            "claim": ideas_mod.claim_fact(plat, house) if plat else
                     {"available": False, "text": "", "pillar": "", "sourced": False, "id": ""},
        }

    # GEOGRAPHY — the plan's priority-geography rollup, carried forward as its own field (round 92).
    # Not resolved through `REFS`/`_row()`: `plan.py` deliberately keeps `geography` outside the LAYERS
    # mechanism (see that module's own comment on `set_geography`), so there is no row id here the way
    # audience/channel/occasion/measure have one. Computed fresh from the plan every time this brief is
    # built, same "never cached" discipline `plan.geography_reach` itself already uses — a plan edited
    # after this execution was briefed should not leave a stale reach number sitting in an old file.
    # Additive and absence-tolerant, same contract as `platform`: a plan with nothing prioritized yet
    # simply has no `geography` key, and every reader must guard.
    reach = plan_mod.geography_reach(p)
    if reach.get("rows"):
        brief["geography"] = reach

    if man["message_required"]:
        mid = str(sel.get("message") or "")
        opts = {o["id"]: o for o in message_options(house, kind)}
        if not mid:
            if not opts:
                # Names the screen that EXISTS. This used to send people to the message-by-medium
                # layer, which is retired — an error that cannot be acted on is worse than no error,
                # because the reader assumes they are the one who is lost.
                return {}, (f"Nothing is written for {kind_label(kind)} yet. Express the idea "
                            f"platform for it in the jobs table — a {kind_label(kind)} needs its "
                            f"own line, not the core line truncated.")
            return {}, "Pick the message this execution carries."
        if mid not in opts:
            return {}, "That message is not one of the lines written for this medium."
        brief["message"] = {"id": mid, "text": opts[mid]["text"], "note": opts[mid].get("note", "")}

    return brief, ""


def proof_obligation(brief: dict, house: dict | None, kind: str) -> dict:
    """Does this execution have to make a claim believable, and can it?

    Carries `basis` for the same reason the balance bar does: *"no house attached"* and *"0 of 2
    sourced"* are different states, and a struct that reported only a number would flatten them into
    the same amber badge.
    """
    man = MANIFEST.get(kind) or {}
    required = bool((man.get("proof_obligation") or {}).get("required"))
    role = str(brief.get("channel", {}).get("role", "")).strip().lower()
    pillar = str(brief.get("pillar", "")).strip().lower() or "functional"

    if not required:
        return {"required": False, "pillar": "", "sourced": 0, "total": 0,
                "basis": f"a {man.get('label', kind).lower()} carries no claim"}
    if role != "proof":
        return {"required": False, "pillar": pillar, "sourced": 0, "total": 0,
                "basis": f"this channel's job is {role or 'unset'}, not proof"}
    if not house:
        return {"required": True, "pillar": pillar, "sourced": 0, "total": 0,
                "basis": "no messaging house attached — the proof gate cannot run"}
    sourced, total = plan_mod.pillar_evidence(house, pillar)
    return {"required": True, "pillar": pillar, "sourced": sourced, "total": total,
            "basis": f"{sourced} of {total} reasons-to-believe sourced"}


# --- value-based staleness ----------------------------------------------------------------------

def stale_because(e: dict, p: dict, house: dict | None) -> list[dict]:
    """Which briefed values have moved since, named one by one.

    Compares stored values against current ones. Each entry carries `field`, `col`, `was` and `now`,
    which is what turns *re-brief against the new values* into one action rather than a hunt.
    """
    out: list[dict] = []
    brief = e.get("brief") or {}

    for field, layer in REFS.items():
        held = brief.get(field)
        if not isinstance(held, dict):
            continue
        row = _row(p, layer, held.get("id", ""))
        if row is None:
            out.append({"field": field, "col": "", "was": held.get(list(held)[1], ""), "now": "",
                        "detail": f"the {field} row it was briefed against has been deleted"})
            continue
        for col in plan_mod.LAYER_BY_ID[layer]["cols"]:
            was, now = str(held.get(col, "")), str(row.get(col, ""))
            if was != now:
                out.append({"field": field, "col": col, "was": was, "now": now,
                            "detail": f"{field} {col} was {was or 'empty'!r}, now {now or 'empty'!r}"})

    # The inherited pillar needs no check of its own: `pillar` is a column on the audiences row, so the
    # loop above already compares it and says "audience pillar was 'functional', now 'emotional'". A
    # second check here reported the same drift twice under two different wordings, and a panel showing
    # one change as two is a panel people stop reading.
    #
    # What is worth catching is the brief disagreeing with *itself* — `brief.pillar` out of step with
    # the audience value stored beside it. That should be impossible, so if it ever happens the honest
    # thing is to say so rather than let a downstream producer pick whichever copy it happens to read.
    held_pillar = str(brief.get("pillar", ""))
    held_aud = str((brief.get("audience") or {}).get("pillar", ""))
    if held_pillar and held_aud and held_pillar.lower() != held_aud.lower():
        out.append({"field": "pillar", "col": "pillar", "was": held_pillar, "now": held_aud,
                    "detail": f"this brief is internally inconsistent — it carries the {held_pillar} "
                              f"pillar but its audience row says {held_aud}. Re-brief it."})

    # The platform's expression for this medium can be rewritten too, and a producer working from a stale
    # glimpse is producing to an idea that has moved.
    plat = brief.get("platform") or {}
    if plat and house:
        live = platform_for(house)
        if live is None:
            out.append({"field": "platform", "col": "chosen", "was": plat.get("name", ""), "now": "",
                        "detail": f"the platform “{plat.get('name')}” is no longer the chosen one"})
        elif live["id"] != plat.get("id"):
            out.append({"field": "platform", "col": "chosen", "was": plat.get("name", ""),
                        "now": live.get("name", ""),
                        "detail": f"platform was “{plat.get('name')}”, now “{live.get('name')}”"})
        else:
            now = str((live.get("expressions") or {}).get(e.get("kind"), "") or "")
            if now != str(plat.get("expression") or ""):
                out.append({"field": "platform", "col": "expression",
                            "was": plat.get("expression", ""), "now": now,
                            "detail": "the platform's expression for this medium has been rewritten"})

    # The bound campaign, same class of check: dropped, or its expression for this medium rewritten. A
    # producer reads this ahead of the platform's own expression (see `brief_from` above), so a stale
    # copy here is the same silent-drift risk the platform check exists to catch — not a new one.
    camp = brief.get("campaign") or {}
    if camp and house:
        pset = ideas_mod.for_house(house.get("id", ""))
        live_camp = campaign_mod.get(pset, camp.get("id", "")) if pset else None
        if live_camp is None:
            out.append({"field": "campaign", "col": "chosen", "was": camp.get("name", ""), "now": "",
                        "detail": f"the campaign “{camp.get('name')}” no longer exists"})
        else:
            now = str((live_camp.get("expressions") or {}).get(e.get("kind"), "") or "")
            was = str((camp.get("expressions") or {}).get(e.get("kind"), "") or "")
            if now != was:
                out.append({"field": "campaign", "col": "expression", "was": was, "now": now,
                            "detail": "the campaign's expression for this medium has been rewritten"})

    # And the message text can be rewritten in the house under the same id.
    msg = brief.get("message") or {}
    if msg and house:
        node = house.get("nodes", {}).get("medium") or {}
        live = next((o for o in node.get("options", []) if o["id"] == msg.get("id")), None)
        if live is None:
            out.append({"field": "message", "col": "text", "was": msg.get("text", ""), "now": "",
                        "detail": "the message it carries has been dropped from the house"})
        elif live["text"] != msg.get("text"):
            out.append({"field": "message", "col": "text", "was": msg.get("text", ""),
                        "now": live["text"], "detail": "the message has been rewritten in the house"})
    return out


def rebrief(e: dict, p: dict, house: dict | None) -> tuple[dict, str]:
    """Re-resolve every reference against the plan as it stands now — the single action.

    Returns (execution, error). **A refusal is returned, not swallowed.** The plan can have moved into a
    state this execution cannot legally be briefed from — a channel switched to `conversion` while the
    execution still points at a `proof` measure — and in that case there is nothing to re-brief *to*.
    Reporting success while leaving the old brief in place would mean the stale badge never clears and
    nobody could see why.

    Deliberately does not touch `status` or `artefacts`. Work already approved stays approved; what
    changes is what the brief says, and `rebriefed` records when and from what.
    """
    sel = {f: (e.get("brief", {}).get(f) or {}).get("id", "") for f in REFS}
    sel["message"] = (e.get("brief", {}).get("message") or {}).get("id", "")
    drift = stale_because(e, p, house)
    brief, err = brief_from(p, house, e["kind"], sel)
    if err:
        e.setdefault("notes", []).append({"at": _now(), "detail": f"re-brief refused: {err}"})
        return save(e), err
    e["brief"] = brief
    e.setdefault("rebriefed", []).append({"at": _now(), "changed": drift})
    return save(e), ""


# --- the envelope ------------------------------------------------------------------------------

def new_execution(p: dict, house: dict | None, kind: str, sel: dict) -> tuple[dict | None, str]:
    brief, err = brief_from(p, house, kind, sel)
    if err:
        return None, err
    e = {"id": uuid.uuid4().hex[:10], "plan": p["id"], "house": p.get("house", ""),
         "kind": kind, "brief": brief, "status": "briefed", "artefacts": [],
         "created": _now(), "updated": _now()}
    return save(e), ""


def set_status(e: dict, status: str) -> tuple[dict | None, str]:
    if status not in STATUSES:
        return None, f"Status must be one of: {', '.join(STATUSES)}."
    e["status"] = status
    e.setdefault("history", []).append({"at": _now(), "status": status})
    return save(e), ""


def validate(e: dict, p: dict, house: dict | None) -> list[dict]:
    out: list[dict] = []

    def add(level, detail):
        out.append({"level": level, "layer": e["kind"], "detail": detail})

    # The idea platform is optional, and "optional" has to mean something other than "silent". Briefing
    # without one is a legitimate choice — one film, now, no campaign around it — so this is an open
    # finding rather than a block. But it says what is being given up, because the alternative is six
    # producers each inventing an idea and nobody noticing until the work is side by side.
    plat = (e.get("brief") or {}).get("platform")
    if not plat:
        add("open", "No idea platform. This will be briefed from the message alone, so it will not "
                    "cohere with any other execution — each one will invent its own idea. Fine for a "
                    "one-off; a problem for a campaign.")
    elif not str(plat.get("expression") or "").strip():
        add("open", f"“{plat.get('name') or 'The platform'}” has nothing written for "
                    f"{kind_label(e['kind'])}. Either write its expression for this "
                    f"medium, or accept that the platform does not reach here — an empty expression is "
                    f"an honest answer, a borrowed one is not.")

    ob = proof_obligation(e.get("brief", {}), house, e["kind"])
    if ob["required"] and ob["sourced"] == 0:
        add("blocking",
            f"This is given proof work against the {ob['pillar']} pillar, which has {ob['basis']}. "
            f"There is nothing to prove with. Move the channel to reach, or hold this until the facts "
            f"exist.")
    for d in stale_because(e, p, house):
        add("stale", d["detail"])
    if e.get("status") in ("approved", "shipped") and stale_because(e, p, house):
        add("blocking", f"This is marked {e['status']} but the plan has moved underneath it. "
                        f"Re-brief it or take it back to made.")
    return out


def status(e: dict, p: dict, house: dict | None) -> dict:
    fs = findings_mod.annotate(validate(e, p, house), e.get("overrides"))
    drift = stale_because(e, p, house)
    man = MANIFEST[e["kind"]]
    return {
        "id": e["id"], "kind": e["kind"], "label": man["label"], "plan": e.get("plan", ""),
        "status": e.get("status", "briefed"), "statuses": list(STATUSES),
        "brief": e.get("brief", {}), "artefacts": e.get("artefacts", []),
        # Lifted out of brief.message so the header can print the sentence without digging. The client
        # prefers the server's copy when it is returned, which is what makes an id never reach a screen.
        "message_text": str((e.get("brief", {}).get("message") or {}).get("text", "") or ""),
        "producer": man,
        "proof_obligation": proof_obligation(e.get("brief", {}), house, e["kind"]),
        "stale": bool(drift), "stale_because": drift,
        "findings": fs, "blocking": findings_mod.live_blocking(fs),
        "overridden": findings_mod.overridden_count(fs),
        "updated": e.get("updated", ""),
    }


def summary(plan_id: str, p: dict, house: dict | None) -> dict:
    """What the plan can see of its own executions — the status column back on the plan."""
    by_kind: dict[str, dict] = {}
    stale = blocked = 0
    for e in executions(plan_id):
        k = by_kind.setdefault(e["kind"], {k: 0 for k in STATUSES})
        k[e.get("status", "briefed")] = k.get(e.get("status", "briefed"), 0) + 1
        st = status(e, p, house)
        stale += 1 if st["stale"] else 0
        blocked += 1 if st["blocking"] else 0
    return {"by_kind": by_kind, "stale": stale, "blocked": blocked,
            "total": sum(sum(v.values()) for v in by_kind.values())}
