"""producers.py — the small generators behind the POS-material and on-ground panels.

These are the two producers in the execution envelope that were not already built: a POSM key visual,
and an on-ground activation idea with its four elements. Both are deliberately thin. The strategy has
already been settled by the house and the plan; what is left here is craft, and craft briefed by a
model is a starting point rather than an answer.

Two rules shape all three functions:

**Grounded when it can be, honest when it cannot.** Pass an execution and its brief supplies the
audience, pillar, occasion and the house's message for that medium. Without one they work from the
text alone and say so, rather than quietly inventing the context they are missing.

**They degrade to something usable, never to nothing.** With no API key the key-visual routes come
back as the declared treatment angles applied to the brief. That is the same shape the client already
falls back to on its own, which means the panel behaves identically whether or not a key is present —
the difference is only how good the routes are.
"""
from __future__ import annotations

import json
import os
import re

import brandprofile
import character
import jsonout
import posm
import strategy

# Treatment routes for a POS key visual. Real, distinct angles — a route list whose entries differ only
# in adjective gives the illusion of a choice, which is worse than offering one option honestly.
KV_TREATMENTS: list[tuple[str, str]] = [
    ("Product as hero", "The pack, lit so the product reads at two metres and the variant at one."),
    ("Proof made visible", "The demonstrable fact staged as the image — the thing you can point at."),
    ("The moment of use", "The occasion, with the pack present but not the subject."),
    ("The single claim", "Type-led. One line doing the whole job, for where a photograph will not survive."),
]

# What an on-ground activation is made of. Which of these a given idea needs depends on the idea and the
# venue — a mall atrium needs no van, a rural route needs no gondola, and every one of them needs the
# promoter to know what to say.
OG_ELEMENTS = {
    "stall": "The physical unit — footprint, what it must survive, and what it looks like from ten metres.",
    "van":   "The vehicle as the travelling version of the stall, and what it can carry.",
    "truck": "A larger rig for a roadshow that stays put for a day — its own power, its own shade, and "
             "what it takes to move it between towns.",
    "uniform": "What the promoter wears, and why it makes them approachable rather than official.",
    "education": "What the promoter knows and says. The part that decides whether any of the rest works.",
    "prop":  "The thing a person physically handles or watches — the demo itself, not its packaging.",
    "capture": "How a person who engaged becomes a number you can act on. Without one, a crowd is not a "
               "result.",
    "leave_behind": "What they take away, and why it survives the walk home rather than the bin.",
    "permissions": "Who has to say yes before this can happen, what it costs, and how long it takes.",
}

# Real shapes for the elements that are an actual physical object with a footprint — everything else
# in OG_ELEMENTS (uniform, education, prop, capture, permissions) is not a sized thing and has no entry
# here. Before this table existed, every element rendered at one flat 4:3 default regardless of whether
# it was a stall front or a van side panel, which are not remotely the same shape. `(key, label, ratio)`
# — ratio is what actually reaches the image call; these are sensible Indian-activation defaults, not
# a measured spec, so treat them the way `posm.FORMATS` treats an unmeasured bay: a starting point, not
# a fact, until someone gives a real footprint.
OG_ELEMENT_SIZES: dict[str, list[tuple[str, str, str]]] = {
    "stall": [
        ("3x3", "a 3×3 ft stall footprint — a single-promoter counter", "1:1"),
        ("6x3", "a 6×3 ft stall footprint — a two-sided counter with room for a queue", "16:9"),
    ],
    "van": [
        ("side", "a van side panel — read at a walking pace, the long way round", "16:9"),
        ("back", "a van back panel — read from behind in traffic", "4:3"),
    ],
    "truck": [
        ("side", "a truck side panel for a roadshow rig — the largest single surface", "16:9"),
        ("back", "a truck back panel", "4:3"),
    ],
    "leave_behind": [
        # "3:4", not A5's real 5:7 — this ratio reaches an image provider directly (see
        # gemini.image_from_reference's own comment), and both providers only honour a fixed five-ratio
        # set, silently coercing anything else to 16:9. 3:4 is the closest supported portrait shape;
        # real A5 proportions are a job for the print/artwork pipeline once this element has one.
        ("flyer", "an A5 flyer, handheld", "3:4"),
        ("sachet", "a sample sachet label", "1:1"),
    ],
}

# Where an activation actually happens. This is the addition that changes the shape of the ideas: an
# activation is not portable across venues. A boil-and-check demo that works in a society courtyard is
# not permitted in a mall atrium and is pointless in an office lobby, and an idea generated without a
# venue in mind is an idea nobody can book.
#
# Each carries what the venue permits, who controls access, and the trap it sets — because the traps are
# specific and expensive. `access` is the thing people forget until three weeks before.
VENUES: dict[str, dict] = {
    "kirana": {
        "label": "Kirana / general trade",
        "who": "The daily buyer at the counter, and the shopkeeper whose goodwill you need.",
        "access": "The shopkeeper. No formal permit, but no space either — you get a corner.",
        "permits": "Small footprint, short conversations, product in hand, shopkeeper endorsement.",
        "trap": "The shopkeeper decides whether you exist. An activation he did not agree to is a "
                "promoter standing in the street.",
    },
    "modern_trade": {
        "label": "Modern trade aisle",
        "who": "The planned shopper, mid-trip, with a trolley already half full.",
        "access": "Chain head office, weeks ahead, usually paid. Store manager on the day.",
        "permits": "Sampling, demo tables, aisle-end takeovers — within the chain's rules.",
        "trap": "Chains sell the slot, not the outcome. A booked table with no offer is furniture.",
    },
    "mall_atrium": {
        "label": "Mall atrium",
        "who": "Families with time, in a leisure frame of mind rather than a buying one.",
        "access": "Mall management, licensed by the day or week, priced by footfall. Fire and safety "
                  "clearance for anything built.",
        "permits": "Built structures, demos, performance, prize mechanics. Not cooking or open flame.",
        "trap": "Footfall is not intent. An atrium crowd photographs well and buys nothing unless there "
                "is a reason to act there and then.",
    },
    "office_complex": {
        "label": "Office complex",
        "who": "Working adults in a 40-minute lunch window, alone or in twos.",
        "access": "Facilities or the park management, often free if it reads as an amenity.",
        "permits": "Sampling, quick demos, subscription sign-ups, desk drops.",
        "trap": "The window is short and it closes. Anything needing more than three minutes fails here.",
    },
    "rwa": {
        "label": "Apartment society / RWA",
        "who": "The household decider, at home, with the family present.",
        "access": "The RWA committee — a letter, sometimes a fee, usually a favour and a notice board.",
        "permits": "Morning or evening stalls, doorstep sampling, weekend demos, resident WhatsApp groups.",
        "trap": "Access is personal and slow to arrange, but it is the highest-trust room you will get. "
                "Committee goodwill is the whole asset; burn it once and the society is closed.",
    },
    "sabzi_mandi": {
        "label": "Sabzi mandi",
        "who": "The daily fresh-buyer, price-alert, early, in a hurry.",
        "access": "The mandi association or the municipal body; informal in practice.",
        "permits": "Loud, cheap, physical. Sampling and price-led messages.",
        "trap": "Nobody stops. The message has to work while somebody keeps walking.",
    },
    "haat": {
        "label": "Weekly haat",
        "who": "The rural and peri-urban buyer, on the one day the market runs.",
        "access": "The haat organiser or panchayat. Cheap, but the calendar is fixed.",
        "permits": "Demonstration, bulk sampling, local-language performance.",
        "trap": "One day a week. Miss it and you wait seven days, so the plan is a route, not a date.",
    },
    "temple_festival": {
        "label": "Temple or festival ground",
        "who": "Whole families, in a celebratory frame, at scale.",
        "access": "The temple trust or festival committee. Sensitivities apply and are not negotiable.",
        "permits": "Prasad-adjacent formats, community utility, free water, seating, shade.",
        "trap": "Commercial intrusion is punished hard. Utility is welcome; a sales pitch is not.",
    },
    "transit": {
        "label": "Transit hub",
        "who": "Commuters, daily, on a fixed route, with dead time.",
        "access": "The transport authority or a media owner holding the concession.",
        "permits": "Sampling, kiosks, digital, anything read in seconds.",
        "trap": "Everybody is going somewhere. You get their eyes, not their hands.",
    },
    "college": {
        "label": "College campus",
        "who": "Students — high trial, low loyalty, fast to share.",
        "access": "The college administration or the student union.",
        "permits": "Sampling, contests, campus ambassadors, social mechanics.",
        "trap": "Enormous trial, weak conversion to a paying habit. Judge it on what happens after.",
    },
    "doorstep": {
        "label": "Residential doorstep",
        "who": "The household, at home, one at a time.",
        "access": "Society permission for the building, then nobody — you are at the door.",
        "permits": "Sampling, subscription sign-up, demonstration in the kitchen.",
        "trap": "The most expensive contact per head there is. It has to convert or it cannot be justified.",
    },
}


def _plan_block(plan: dict | None) -> list[str]:
    """What the IMC plan has bought, for a producer that is making one piece of it.

    A producer used to see the plan only through its execution's brief — audience, channel, occasion,
    measure — which is the right slice when an execution row exists and nothing at all when one does not.
    A POS route designed for a channel nobody bought, or an activation phased against a window that
    closed, is work that has to be redone; both are cheap to prevent by naming what was decided.
    """
    if not plan:
        return []
    out = []
    for lid, label in (("channels", "Channels bought, with the job each has"),
                       ("audiences", "Audiences, in priority order"),
                       ("phases", "Phasing — the occasions this is built around"),
                       ("measures", "How this will be judged")):
        rows = ((plan.get("nodes") or {}).get(lid) or {}).get("rows", [])
        bits = []
        for r in rows[:6]:
            cells = " / ".join(str(v).strip() for k, v in r.items()
                               if k not in ("id", "source", "added", "edited") and str(v or "").strip())
            if cells:
                bits.append(cells)
        if bits:
            out.append(f"{label}: " + " | ".join(bits))
    bal = plan.get("balance") or {}
    if bal.get("brand_share") is not None:
        out.append(f"Brand / activation split: {bal['brand_share']}% brand"
                   + (f" — {bal['reason']}" if str(bal.get('reason') or '').strip() else ""))
    return out


def _ctx(house: dict | None, brief: dict | None, platform: dict | None = None,
         plan: dict | None = None, *, use_house: bool = True, use_platform: bool = True,
         use_plan: bool = True, brand_mode: str = "") -> str:
    """The strategy this is being made against, or an explicit note that there is none.

    The idea platform goes in FIRST and is labelled as binding. It sits between the house and the work,
    so once one is adopted every execution is a different expression of the same idea — that is the whole
    reason the layer exists. A producer that treats it as one more piece of context alongside the brief
    will quietly write around it.

    Round 93 — `use_house`/`use_platform`/`use_plan`: the same three independent switches `stands_on()`
    and prompts.py's `system_for()` now take, so a person can turn off just one of house/platform/plan
    without losing the others. `brief` here is the bound execution's own audience/channel/occasion/
    measure — the same thing `use_plan` gates in `system_for()` via `_execution_block`, so it is nulled
    alongside `plan` under this one flag rather than needing a fourth. Each defaults on; nulling the
    inputs before the logic below runs means the existing "no strategy attached" degrade below still
    fires correctly when everything is switched off, with no separate empty-state to maintain.

    `brand_mode` used to gate the character reference (skipped entirely for General) — Round 5 removed
    that (a character is a visual asset, not invented brand voice; see the comment on `char` below) and
    left the parameter gating nothing at all for one round. Phase 1 gives it back a real job: skipping
    `house`/`platform` — the actual brand-voice sources — when General, which `use_house`/`use_platform`
    alone never did.
    """
    # The brand's approved recurring character (empty when there is none). Resolved from the ORIGINAL
    # house/brief before the switches below can null them — a character is a brand fact, not one of
    # the house/platform/plan inputs a person turns off. POSM, POSM carousel and Onground all reach
    # generation through this one context builder.
    #
    # Round 5 (confirmed with the user): a character reference is a visual asset, not invented brand
    # voice/copy — General mode means "don't invent or state brand facts in the text," not "pretend no
    # brand exists at all." So this is NOT skipped for General any more. `brandprofile.resolve(house,
    # brief)` already falls through to whichever brand is currently ACTIVE when neither doc names one
    # (exactly the case for a General house, whose own `brand` field is blank by design) — so a General
    # piece's character reference comes from the SAME brand that's active in this session, the same
    # access boundary every other active-brand read in this tenant already respects. Nothing here
    # widens who can see which brand's character; it only stops narrowing it further than that.
    char = character.for_prompt(brandprofile.resolve(house, brief))
    # Phase 1 (brand-grounding, discovered live testing POSM): `use_house`/`use_platform` are a
    # SEPARATE, orthogonal pair of switches from `brand_mode` — a person can turn the house off while
    # still Grounded, or leave it on while Independent. Before this fix, brand_mode wasn't checked here
    # at all, so a POSM piece cold-opened onto whichever house the tenant happened to bind (Round 93's
    # step 3, "the newest house for the active brand") carried that house's real core message, RTBs and
    # avoid-list into an Independent piece's prompt regardless — confirmed live: a real "Develop key
    # visual" call came back "Standing on the house's core message" with the actual message text, while
    # Independent was selected. `_mode` falls back to the house's own stored mode only when no explicit
    # brand_mode was passed — same pattern as the character line above and every other mode check in
    # this project — but the caller's own current-session value always wins when given.
    _mode = brand_mode or (house or {}).get("brand_mode") or "grounded"
    house = house if (use_house and _mode != "general") else None
    platform = platform if (use_platform and _mode != "general") else None
    brief = brief if use_plan else None
    plan = plan if use_plan else None
    if not house and not brief and not platform and not plan:
        base = ("NO STRATEGY ATTACHED — you have only the text below. Do not invent an audience, an "
                "occasion or a claim. Work with what is given and say what is missing.")
        return base + ("\n\n" + char if char else "")
    out = []
    if platform:
        line = str(platform.get("idea") or "").strip()
        if line:
            out.append(f"THE IDEA PLATFORM (binding — every execution is one expression of this): {line}")
        for f in ("name", "mechanic", "truth"):
            v = str(platform.get(f) or "").strip()
            if v:
                out.append(f"platform {f}: {v}")
        expr = {k: str(v).strip() for k, v in (platform.get("expressions") or {}).items()
                if str(v or "").strip()}
        if expr:
            out.append("already expressed elsewhere (stay consistent with these, do not repeat them "
                       "verbatim): " + " | ".join(f"{k}: {v}" for k, v in expr.items()))
    if brief:
        for f in ("audience", "channel", "occasion", "measure"):
            v = brief.get(f)
            if isinstance(v, dict):
                out.append(f"{f}: " + ", ".join(f"{k}={x}" for k, x in v.items()
                                                if k not in ("id", "source", "added", "edited") and x))
        if brief.get("pillar"):
            out.append(f"pillar: {brief['pillar']}")
        if isinstance(brief.get("message"), dict):
            out.append(f"message (verbatim, do not paraphrase): {brief['message'].get('text','')}")
    if house:
        core = strategy._chosen_text(house, "core")
        if core:
            out.append("core message: " + "; ".join(core))
        avoid = [o["text"] for o in (house.get("nodes", {}).get("culture") or {}).get("options", [])
                 if o["id"] in set((house.get("nodes", {}).get("culture") or {}).get("chosen") or [])
                 and str(o.get("tag", "")).lower() == "avoid"]
        if avoid:
            out.append("MUST AVOID: " + "; ".join(avoid))
    out.extend(_plan_block(plan))
    if char:
        out.append(char)
    return "\n".join(out) or "NO STRATEGY ATTACHED — work from the text alone."


def _ask(prompt: str, max_tokens: int = 1500) -> tuple[dict | None, str]:
    """One shared path to a JSON reply, with the retry. See jsonout for why the naive parse was not enough."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None, "no key"
    return jsonout.ask_json(prompt, max_tokens=max_tokens)


# What a producer stands on, in order of authority. This is the fix for a real complaint: POS material
# asked somebody to retype the proposition they had already decided twice — once in the messaging house
# and once as the platform's expression. A producer should never ask for something the spine already
# holds; asking again is how the two copies end up disagreeing.
#
#   1. the idea platform's expression for THIS medium  — the most specific thing anyone has decided
#   2. the platform's own sentence                     — when it has not been expressed here yet
#   3. the house's message for this medium             — what the brand says in this channel
#   4. the house's core message                        — the fallback that is still the brand's
#   5. whatever was typed                              — last, because it is the least considered
#
# Returns (text, source) so the screen can say where it came from rather than presenting it as neutral.
def stands_on(kind: str, house: dict | None = None, platform: dict | None = None,
              typed: str = "", *, force_typed: bool = False,
              use_house: bool = True, use_platform: bool = True,
              brand_mode: str = "") -> tuple[str, str]:
    typed = (typed or "").strip()
    # Phase 1 (brand-grounding): same fix as `_ctx()`'s own `_mode` — `use_house`/`use_platform` say
    # whether the house/platform are IN SCOPE at all, a separate question from whether this piece may
    # state their content as brand fact. Without this, an Independent POSM/Onground piece bound to any
    # house (including the Round 93 "cold open, newest house for the active brand" fallback) stood on
    # that house's real core message — confirmed live. Falls back to the house's own stored mode only
    # when the caller passed nothing explicit, same precedence as everywhere else this pattern appears.
    _mode = brand_mode or (house or {}).get("brand_mode") or "grounded"
    # `force_typed` — a real, deliberate override, not the fallback-of-last-resort the plain `typed`
    # parameter already is. Found live: the frontend told a person typing here "this box is an
    # override, not a required field," which is only true when nothing else exists — the moment a
    # platform IS attached, the platform always wins and the typed text is silently never read at all,
    # with no error and no indication anything was ignored. That's correct behaviour by default (two
    # copies of one proposition drifting apart is the real failure this ordering exists to prevent),
    # but a person choosing to set the platform aside for one specific piece needs a real way to say so
    # rather than discovering the silent precedence the hard way.
    #
    # Round 93 — `use_house`/`use_platform`: split from `force_typed` into two independent switches
    # (matching prompts.py's `spine_block`/`system_for` split), so a person can turn off just the
    # platform, or just the house, without losing the other. Deliberately NOT ANDed with `force_typed`
    # here — `force_typed` only ever acts through the early-return above, exactly as before this round:
    # forcing it on with nothing typed to replace the platform/house with must keep falling through to
    # them unchanged (a covered case — see test_stands_on_force_typed_with_no_typed_text_falls_through),
    # not go silent. `use_house`/`use_platform` are the ONLY thing that suppresses these two blocks now.
    if force_typed and typed:
        return typed, "typed here — the idea platform and house were set aside for this piece"
    if platform and use_platform and _mode != "general":
        expr = str((platform.get("expressions") or {}).get(kind, "") or "").strip()
        if expr:
            return expr, f"the idea platform, expressed for {kind}"
        line = str(platform.get("idea") or "").strip()
        if line:
            return line, "the idea platform"
    if house and use_house and _mode != "general":
        want = {"posm": "posm", "activation": "on-ground", "social": "social",
                "video": "tv", "incentive": "trade"}.get(kind, "")
        node = (house.get("nodes") or {}).get("medium") or {}
        picked = set(node.get("chosen") or [])
        for o in node.get("options", []):
            if o["id"] in picked and str(o.get("tag", "")).lower() == want and str(o.get("text") or "").strip():
                return o["text"].strip(), f"the house's {want} message"
        core = strategy._chosen_text(house, "core")
        if core:
            return "; ".join(core), "the house's core message"
    if typed:
        return typed, "typed here"
    return "", ""


# Where the type block sits. A POS route is not finished until somebody has decided where the words go —
# a key visual with an unplaced line is a photograph, and the line ends up wherever the artwork happens
# to leave room.
#
# These are `posm.TYPE_POSITIONS` and not a second copy of them. The keys are the same ones this module
# has always used; what changed is what they describe. They used to name a band reserved *inside a
# photograph* for a headline to be drawn into later. They now name the position of a type block on a
# flat colour field, which is where type on POS actually sits — the field is the space, so nothing has
# to be held open. Two copies of this vocabulary would drift the moment one side was corrected.
KV_LAYOUTS = posm.TYPE_POSITIONS


_NEGATIVE_CLAUSE = re.compile(
    r"\b(left out|leaves out|not shown|no scene|why it survives|why it works|deliberately omit\w*)\b",
    re.IGNORECASE)


def hero_subject(desc: str) -> str:
    """The positive, in-frame half of a route description — safe to hand to an image model.

    A route's `desc` is written for a person and is three things at once: what is in frame, what is
    deliberately left out, and why it survives two metres. Only the first is a subject. The other two
    are reasoning, and one of them is a list of things that must NOT appear — which an image model reads
    as a list of things to draw, because these models do not negate.

    Two real failures in one render, both from passing the whole `desc` straight through:
      * a route reading "a child cut-out mid-stride... **Left out: the breakfast table, the mother,**
        the morning kitchen" produced a photograph of a mother;
      * a route reading "**Left out:** any kitchen, table, hand or room — **no scene**, just the object
        isolated on flat colour" was handed to the backdrop generator, which produced a street scene.

    Splitting on the first negative marker keeps the subject and drops the rest. Sentence-aware so a
    subject that merely contains the word "no" survives.
    """
    text = str(desc or "").strip()
    if not text:
        return ""
    parts = re.split(r"(?<=[.;])\s+|\s+[—–-]\s+", text)
    kept = []
    for p in parts:
        if _NEGATIVE_CLAUSE.search(p):
            break
        kept.append(p)
    out = " ".join(kept).strip(" .;—–-")

    # Drop any remaining clause that puts packaging in frame. The pack is composited from the signed-off
    # library shot on every piece, so a generation prompt naming one can only produce an invented
    # carton — and an invented carton arrives wearing invented branding. Caught live: a subject reading
    # "...standing beside a carton of milk" returned a child next to an **Amul** pack, a competitor
    # named in this brand's own profile. `posm._PACK_WORDS` is the same vocabulary `looks_like_pack`
    # already uses, so the two agree on what counts as packaging.
    clauses = [c for c in re.split(r",\s*", out) if c.strip()]
    keep = [c for c in clauses if not any(w in c.lower() for w in posm._PACK_WORDS)]
    if keep:
        out = ", ".join(keep)

    # A desc whose very first clause is the negative leaves nothing; better to send the whole thing than
    # an empty subject, since an empty one is refused downstream and blocks the person entirely.
    return out or text


def key_visual(brief_text: str, house: dict | None = None,
               exec_brief: dict | None = None, platform: dict | None = None,
               plan: dict | None = None, n: int = 3, *, force_typed: bool = False,
               use_house: bool = True, use_platform: bool = True,
               use_plan: bool = True, brand_mode: str = "") -> tuple[list[dict], str]:
    """Treatment routes for a POS key visual. Returns (options, note).

    **The brief is resolved, not demanded.** This used to require typed text and offer ungrounded generic
    routes without it — so somebody who had already decided a platform and a house was asked to retype the
    proposition a third time. `stands_on` walks the spine in order of authority instead, and the note says
    which rung it landed on.

    `force_typed` — someone deliberately set the platform/house aside for this one piece; see
    `stands_on`'s own docstring for why this needs to be opt-in rather than the default. `use_house`/
    `use_platform` (round 93) — the same two independent switches `stands_on` itself now takes, forwarded
    straight through. `brand_mode` (Phase 1, brand-grounding) — forwarded to both `stands_on` and `_ctx`
    below, so an Independent piece never stands on a bound house's real core message.
    """
    text, src = stands_on("posm", house, platform, brief_text, force_typed=force_typed,
                          use_house=use_house, use_platform=use_platform, brand_mode=brand_mode)
    fallback = [{"id": f"kv{i+1}", "name": name, "desc": f"{angle} {text}".strip(),
                 "layout": list(KV_LAYOUTS)[min(i, len(KV_LAYOUTS) - 1)]}
                for i, (name, angle) in enumerate(KV_TREATMENTS[:max(1, n)])]
    if not text:
        return fallback, ("Nothing to work from — adopt an idea platform, choose a house message, or "
                          "write a line. These are the standard treatment routes, ungrounded.")

    layouts = "\n".join(f"  {k}: {v}" for k, v in KV_LAYOUTS.items())
    heroes = "\n".join(f"  {k}: {v['what']}" for k, v in posm.HERO_TYPES.items())
    prompt = (
        "You are art-directing point-of-sale material for Indian FMCG retail. POS is read at two metres "
        "by someone who is not looking for it, in bad light, next to nine other brands.\n\n"
        "HOW THIS CATEGORY IS BUILT — this governs every route below.\n"
        "Indian FMCG point-of-sale is flat-colour graphic design with cut-out photographic elements "
        "placed on it: a flat brand-colour field, a hero masked out of its background, the real pack "
        "masked, type set in badges and boxes, a brand block and a base band. It is NOT a photograph "
        "with words on top. A route that describes a scene filling the frame is describing the wrong "
        "object. The pack is always present and never the hero.\n\n"
        f"THE STRATEGY\n{_ctx(house, exec_brief, platform, plan, use_house=use_house, use_platform=use_platform, use_plan=use_plan, brand_mode=brand_mode)}\n\n"
        f"WHAT THIS STANDS ON ({src})\n{text}\n\n"
        f"Give {n} genuinely different treatment routes. They must differ in what the HERO cut-out is "
        "and what the field does — not in adjectives. For each: what is in frame, what is deliberately "
        "left out, and why it survives two metres.\n\n"
        f"Each route picks a HERO type, one of these keys:\n{heroes}\n"
        "Pick deliberately. A metaphor object reads as a silhouette at four metres where a face does "
        "not, and it is the right answer when the benefit is invisible — which is exactly when the "
        "person and endorser types fail.\n\n"
        f"Each route also picks where the TYPE BLOCK sits, one of these keys:\n{layouts}\n"
        "A route that does not place its line is a photograph, and the line ends up wherever the "
        "artwork happens to leave room.\n\n"
        "Also give `line` — the exact words that appear on the piece, short enough to read at two "
        "metres. Take it from what this stands on; do not write a new claim.\n"
        "Give `line_emphasis` — the one word or short phrase inside `line` that should be set largest. "
        "It must appear in `line` verbatim.\n"
        "Give `subject` — ONLY the physical thing to photograph, stated positively in one clause: who "
        "or what is in frame and what they are doing. No 'left out', no rationale, no negatives, and "
        "never mention anything that must NOT appear. This string is sent to an image model on its own.\n"
        "**`subject` must never mention the pack, a carton, a bottle, a pouch or any packaging**, even "
        "though the pack does appear on the finished piece. The real pack is composited from the "
        "library afterwards; anything an image model draws in its place comes back with invented brand "
        "lettering on it — in testing it drew a COMPETITOR's brand onto the carton, which is the single "
        "most expensive mistake this tool could make. Describe the person or object only.\n"
        "Do not specify a colour palette or a typeface; those are the brand's, not yours.\n"
        'Return ONLY JSON: {"options":[{"id":"kv1","name":"short route name","desc":"in frame, left out, '
        'why it survives 2m","subject":"only what is physically in frame, stated positively",'
        '"line":"the words on the piece","line_emphasis":"the word set largest",'
        '"hero":"one of the hero keys","layout":"one of the type-position keys above"}]}')
    data, err = _ask(prompt, 2200)
    if not data:
        return fallback, ("Standard treatment routes — no generation available."
                          if err == "no key" else f"Standard routes: {err}.")
    opts = []
    for i, o in enumerate((data.get("options") or [])[:max(1, n) + 1]):
        name, desc = str(o.get("name") or "").strip(), str(o.get("desc") or "").strip()
        if not (name and desc):
            continue
        lay = str(o.get("layout") or "").strip()
        # An exact-match check against the model's own returned text silently dropped a real hero type
        # to '' on nothing more than "Occasion" vs "occasion", or trailing whitespace — no logging, so it
        # was invisible. Once `hero` is '', `hero_type` reads as unrecognized downstream, the pack-word
        # bypass this exists to grant doesn't apply, and a route whose OWN description legitimately
        # mentions "the pack present but not the subject" (every route's prompt says the pack must be
        # mentioned) trips `posm.looks_like_pack()` as a false positive — the same failure class the
        # round-58 pack-gate fix closed one entry point of, re-opened through this one. Normalising
        # before the membership check (case, whitespace, spaces-for-hyphens) fixes the common ways a
        # model paraphrases an enum key without ever guessing a hero type it didn't actually name.
        hero_raw = str(o.get("hero") or "").strip()
        hero_norm = re.sub(r"[\s_]+", "-", hero_raw.lower())
        hero = hero_norm if hero_norm in posm.HERO_TYPES else ""
        opts.append({"id": str(o.get("id") or f"kv{i+1}"), "name": name, "desc": desc,
                     # The positive-only subject, for anything that hands text to an image model.
                     # Falls back to stripping `desc` for routes drafted before this field existed.
                     # Run the model's own `subject` through the same strip: the instruction not to
                     # mention packaging is followed most of the time, not all of it, and the cost of
                     # the miss is a competitor's brand on the artwork.
                     "subject": hero_subject(str(o.get("subject") or "").strip() or desc),
                     "line": str(o.get("line") or "").strip(),
                     "line_emphasis": str(o.get("line_emphasis") or "").strip(),
                     "hero": hero,
                     "hero_label": posm.HERO_TYPES.get(hero, {}).get("label", ""),
                     "layout": lay if lay in KV_LAYOUTS else "type-locked-base",
                     "layout_note": KV_LAYOUTS.get(lay, "")})
    return (opts or fallback), (f"Standing on {src}." if opts else "")


# --- carousel: alternative narrative concepts, reviewed as text before any slide is rendered ---------
#
# A carousel is an ordered, multi-part narrative — hook, then value slides that each deliver one real
# point, then a call to action — not a set of independent assets the way Social's per-platform posts
# are. That puts it in the same family as Video's beat-based concept phase, not Social's single-post
# flow: the failure mode worth catching cheaply is a sequence that doesn't cohere (slide 4 not actually
# delivering on slide 1's promise), and that is cheap to fix in text and expensive to fix after N
# images already exist.
#
# Round 93 (live feedback, second pass): returns MULTIPLE alternative routes, matching the shape
# `generateVideo`'s own three-creative-routes step and POSM's key-visual routes already use — a person
# picks one genuinely different narrative direction before anything is edited, the same discipline as
# those two, not a single draft to fix in place. Image production reuses `/scene-still` directly, once
# per slide, with the carousel's own locked pack/cast/plate references attached — no separate image
# route needed.
def carousel_concept(objective: str, house: dict | None = None, platform: dict | None = None,
                     plan: dict | None = None, exec_brief: dict | None = None,
                     n_mode: str = "manual", n: int = 5, *, use_house: bool = True,
                     use_platform: bool = True, use_plan: bool = True,
                     brand_mode: str = "") -> tuple[list[dict], str]:
    """Returns (routes, note). `routes` is a list of `{name, rationale, slides}` — up to three genuinely
    different narrative directions for the same objective, each carrying its own ordered slide list
    (`{role, headline, visual_note, shows_pack}`, role one of hook/value/cta) and its own slide count.
    `n_mode:"auto"` lets each route pick its own count (3–10) based on what that route's narrative
    actually needs; `"manual"` fixes every route to the same requested count.

    `shows_pack` — whether THIS slide's own story shows the product (a pour, a hand reaching for the pack,
    a shelf) versus a slide about the idea with nothing to show (a stat, a feeling, a before/after that
    hasn't reached the product yet). This is a narrative signal only, not tied to any real SKU — the
    person has not picked which real pack to attach yet when this route is drafted (that happens on the
    next screen), so the model is never asked to name one. The CLOSING (cta) slide always ends up
    carrying the real pack regardless of this flag — the caller (`main.scene_still`, via `packscene.py`)
    decides that structurally from slide POSITION, not from anything returned here, because a stored
    role goes stale the moment a person reorders or deletes a slide. `shows_pack` still matters for the
    cta slide's own WRITING: it is told to leave room for the pack rather than write a busy scene.
    """
    objective = (objective or "").strip()
    if not objective:
        return [], ("Write what these slides have to land first — a carousel needs an objective the "
                    "same way a single post does.")
    if n_mode == "auto":
        n_instruction = ("Each route decides its own slide count, between 3 and 10, based on what that "
                        "route's narrative actually needs — the routes do not have to agree on a count.")
    else:
        n = max(3, min(10, int(n or 5)))
        n_instruction = f"Every route uses exactly {n} slides."
    ctx = _ctx(house, exec_brief, platform, plan,
              use_house=use_house, use_platform=use_platform, use_plan=use_plan, brand_mode=brand_mode)
    prompt = (
        "You are writing narrative concepts for an Instagram/LinkedIn carousel — a swipeable, ordered "
        "set of slides read as one continuous story, not independent posts. Propose THREE genuinely "
        "different carousel concepts for the same objective — not three phrasings of one idea. Each "
        "must take a distinct narrative angle (for example: a single-story arc, a countdown/checklist "
        "structure, a before-and-after). Within any one route, every slide must earn the swipe to the "
        "next — slide 3 has to actually deliver on what slide 1 promised, not restate it. The shape a "
        "route follows: one hook slide that stops the scroll, several value slides, one closing "
        "call-to-action slide.\n\n"
        f"THE STRATEGY\n{ctx}\n\n"
        f"WHAT THESE SLIDES HAVE TO LAND\n{objective}\n\n"
        f"{n_instruction}\n"
        "For each route give a short name, a one-line rationale for why this angle could work, and its "
        "ordered slides — each with role (hook / value / cta), a short ON-SLIDE headline (the words "
        "that actually appear on the slide, not a caption), a one-line visual direction describing what "
        "the image shows, and shows_pack (true/false): would the product's pack naturally be VISIBLE "
        "somewhere in this shot at all — carried, held, handed over, set down, delivered, on a shelf, "
        "being poured — not only a deliberate close-up of it. Mark it true whenever the scene puts "
        "someone near the product, even briefly or in the middle distance; a delivery, a handoff or "
        "someone walking with it in hand all count. Mark it false only for a shot with no product "
        "anywhere in view — a face on its own, a stat, a feeling, an empty street. The studio always "
        "places the real product pack into the CLOSING (cta) "
        "slide regardless of shows_pack — so write that slide's visual_note as a calm, uncluttered scene "
        "(a counter, a table, a plain backdrop) with the product naturally the focus of its upper frame, "
        "never a busy or wide shot, since the pack will occupy that space and the slide's own headline "
        "the bottom.\n"
        'Return ONLY JSON: {"routes":[{"name":"short route name","rationale":"one line on why this '
        'works","slides":[{"role":"hook","headline":"...","visual_note":"...","shows_pack":false}, ...]}, '
        '...exactly 3 routes]}')
    data, err = _ask(prompt, 2600)
    if not data or not data.get("routes"):
        return [], ("No concepts available." if err == "no key" else f"Couldn't draft concepts: {err}.")
    routes = []
    for r in data["routes"]:
        if not isinstance(r, dict):
            continue
        slides = []
        for s in (r.get("slides") or []):
            if not isinstance(s, dict):
                continue
            visual_note = str(s.get("visual_note") or "").strip()
            # The model's own flag wins when it answered; `posm.looks_like_pack` (the same vocabulary
            # POSM already trusts — pack/carton/tetra/pouch/sachet/bottle/jar/tub...) is only the
            # fallback for a slide the model left the field off on, or a slide added by hand later
            # (`addSlide`) that never went through this prompt at all.
            shows_pack = bool(s["shows_pack"]) if "shows_pack" in s else posm.looks_like_pack(visual_note)
            slides.append({"role": (str(s.get("role") or "value").strip().lower() or "value"),
                           "headline": str(s.get("headline") or "").strip(),
                           "visual_note": visual_note, "shows_pack": shows_pack})
        slides = [s for s in slides if s["headline"] or s["visual_note"]]
        if not slides:
            continue
        routes.append({"name": str(r.get("name") or "").strip() or "Untitled route",
                       "rationale": str(r.get("rationale") or "").strip(),
                       "slides": slides})
    if not routes:
        return [], "The model returned no usable routes — try again or write the objective more specifically."
    return routes, ""


def activation_ideas(house: dict | None = None, platform: dict | None = None,
                     plan: dict | None = None, exec_brief: dict | None = None,
                     n: int = 3, steer: str = "", *, use_house: bool = True,
                     use_platform: bool = True, use_plan: bool = True,
                     brand_mode: str = "") -> tuple[list[dict], str]:
    """Two or three on-ground ideas, each built for a named venue. Returns (ideas, note).

    **This reverses an earlier rule deliberately.** On-ground used to refuse to generate an idea without
    one typed first, on the argument that a model-supplied activation is one nobody in the room believes
    in. That still holds for a *vague* idea — so the fields below make a vague one impossible to write
    rather than refusing to write anything.

    Every idea is structured as what · who · where · when · how, and two constraints come from how
    on-ground actually fails rather than from taste:

    **A crowd is not a result.** Every idea must carry a capture mechanism — the thing that turns somebody
    who engaged into a number you can act on. Footfall stunts with nothing to capture are the classic
    activation that photographs well and moves nothing.

    **Unmanned is furniture.** Every idea names what the promoter does. A booked table with no offer and
    nobody working it is the most common waste in the category.

    Ideas span more than one venue on purpose. An activation is not portable — the same demo is welcome
    in a society courtyard, forbidden in a mall atrium and pointless in an office lobby — so a set that
    is all one venue has not given anybody a choice.
    """
    n = max(2, min(4, int(n or 3)))
    text, src = stands_on("activation", house, platform, steer,
                          use_house=use_house, use_platform=use_platform, brand_mode=brand_mode)
    if not text:
        return [], ("Nothing to build on. Adopt an idea platform or choose a house message first — an "
                    "activation is an expression of an idea, and there is no idea here yet.")

    venues = "\n".join(
        f"  {k} · {v['label']} — who: {v['who']} | access: {v['access']} | "
        f"permits: {v['permits']} | the trap: {v['trap']}"
        for k, v in VENUES.items())

    prompt = (
        "You are planning consumer activations in India — real ones, that a field team has to book, "
        "staff and run.\n\n"
        f"THE STRATEGY\n{_ctx(house, exec_brief, platform, plan, use_house=use_house, use_platform=use_platform, use_plan=use_plan, brand_mode=brand_mode)}\n\n"
        f"WHAT THIS EXPRESSES ({src})\n{text}\n\n"
        + (f"THE PERSON ASKING ADDS\n{steer.strip()}\n\n" if steer.strip() else "")
        + f"VENUES YOU MAY USE — pick the right one per idea, and read its trap:\n{venues}\n\n"
        f"Give {n} DIFFERENT activation ideas. Different venues, not one idea rewritten — an activation "
        "is not portable, and a set that is all one venue has offered no choice.\n\n"
        "Two rules, both from how on-ground actually fails:\n"
        "1. A CROWD IS NOT A RESULT. Every idea must say how somebody who engaged becomes a number you "
        "can act on — a scan, a sign-up, a pack bought there, a name taken. An idea whose outcome is "
        "'awareness' or 'engagement' is one nobody can judge, and you must not write one.\n"
        "2. UNMANNED IS FURNITURE. Say what the promoter actually does and says. A table nobody is "
        "working is a table.\n\n"
        "For each idea:\n"
        "  what   — the central action, in one sentence. What a person physically DOES. Not what they "
        "feel, learn or engage with.\n"
        "  who    — who it is for, and who runs it\n"
        "  where  — the venue key from the list, and how many sites\n"
        "  when   — the daypart and the window, and why that one\n"
        "  how    — the mechanic, step by step, as a field team would run it\n"
        "  capture— how engagement becomes a measurable number\n"
        "  access — who has to say yes, from the venue's `access` above\n"
        "  risk   — the venue's trap, in this idea's terms, and what you do about it\n"
        "Do not invent costs, site counts you cannot justify, or permissions you do not know exist. "
        "Where a number is needed and unknown, say what has to be decided and by whom.\n"
        'Return ONLY JSON: {"ideas":[{"name":"three or four words","venue":"one key from the list",'
        '"what":"...","who":"...","where":"...","when":"...","how":"...","capture":"...",'
        '"access":"...","risk":"..."}]}')

    data, err = _ask(prompt, 900 + 700 * n)
    if not data:
        return [], ("No generation available — write the idea yourself and it will be sharpened."
                    if err == "no key" else f"Generation failed: {err}.")
    out = []
    for i, o in enumerate(data.get("ideas") or []):
        what = str((o or {}).get("what") or "").strip()
        if not what:
            continue
        v = str(o.get("venue") or "").strip().lower().replace(" ", "_")
        spec = VENUES.get(v, {})
        out.append({"id": f"og{i+1}", "name": str(o.get("name") or "").strip() or f"Idea {i+1}",
                    "venue": v, "venue_label": spec.get("label", v or "unnamed venue"),
                    "venue_trap": spec.get("trap", ""),
                    "what": what,
                    "who": str(o.get("who") or "").strip(),
                    "where": str(o.get("where") or "").strip(),
                    "when": str(o.get("when") or "").strip(),
                    "how": str(o.get("how") or "").strip(),
                    "capture": str(o.get("capture") or "").strip(),
                    "access": str(o.get("access") or "").strip(),
                    "risk": str(o.get("risk") or "").strip(),
                    "source": "model", "stands_on": src})
    if not out:
        return [], "Nothing usable came back. Write the idea yourself and it will be sharpened."
    return out, f"Built on {src}."


def adjust_activation_idea(idea: dict, note: str, house: dict | None = None,
                           exec_brief: dict | None = None, platform: dict | None = None,
                           plan: dict | None = None, *, use_house: bool = True,
                           use_platform: bool = True, use_plan: bool = True,
                           brand_mode: str = "") -> tuple[dict | None, str]:
    """Revise ONE already-generated activation idea per a note, keeping its structure. Returns (idea, note).

    `sharpen_idea`'s twin for the CARD shape rather than a plain string. `activation_ideas` returns a
    structured what/who/where/when/how/capture/access/risk per idea, and every element downstream reads
    those specific fields (`elements_for`, the kit sheet) — a person asking to adjust one idea ("make the
    capture a WhatsApp opt-in instead") needs the same shape back, not a paragraph that collapses them.
    Only the substantive fields go to the model; `id` is kept from the original so the card updates in
    place rather than reading as a new one, and `venue_label`/`venue_trap`/`source`/`stands_on` are
    recomputed only if the venue actually changed.
    """
    idea = idea if isinstance(idea, dict) else {}
    note = (note or "").strip()
    if not note:
        return None, "Say what to change — this adjusts the idea, it does not invent a new one."
    if not str(idea.get("what") or "").strip():
        return None, "Nothing to adjust — pick or write an idea first."
    venues = "\n".join(
        f"  {k} · {v['label']} — who: {v['who']} | access: {v['access']} | "
        f"permits: {v['permits']} | the trap: {v['trap']}"
        for k, v in VENUES.items())
    current = {k: idea.get(k, "") for k in
               ("name", "venue", "what", "who", "where", "when", "how", "capture", "access", "risk")}
    prompt = (
        "You are refining ONE consumer activation idea for India — a field team has to book, staff and "
        "run it.\n\n"
        f"THE STRATEGY\n{_ctx(house, exec_brief, platform, plan, use_house=use_house, use_platform=use_platform, use_plan=use_plan, brand_mode=brand_mode)}\n\n"
        f"THE IDEA AS IT STANDS\n{json.dumps(current)}\n\n"
        f"THE CHANGE ASKED FOR\n{note}\n\n"
        f"VENUES — pick the right one only if the venue itself has to change:\n{venues}\n\n"
        "Apply ONLY the change asked for. Keep everything else about the idea exactly as it stands — do "
        "not rewrite fields the change doesn't touch.\n"
        'Return ONLY JSON, the same shape: {"name":"...","venue":"one key from the list","what":"...",'
        '"who":"...","where":"...","when":"...","how":"...","capture":"...","access":"...","risk":"..."}')
    data, err = _ask(prompt, 900)
    if not data:
        return None, ("No generation available." if err == "no key" else f"Couldn't adjust it: {err}.")
    out = {k: str(data.get(k) or current.get(k) or "").strip() for k in current}
    if not out["what"]:
        return None, "The model's reply was missing the idea itself — unchanged."
    v = out["venue"].strip().lower().replace(" ", "_")
    venue_changed = v != str(idea.get("venue") or "").strip().lower().replace(" ", "_")
    spec = VENUES.get(v, {}) if venue_changed else {}
    out["id"] = idea.get("id", "")
    out["venue"] = v or idea.get("venue", "")
    out["venue_label"] = spec.get("label", v or "unnamed venue") if venue_changed else idea.get("venue_label", "")
    out["venue_trap"] = spec.get("trap", "") if venue_changed else idea.get("venue_trap", "")
    out["source"] = idea.get("source", "model")
    out["stands_on"] = idea.get("stands_on", "")
    return out, ""


def elements_for(idea: dict | None) -> list[dict]:
    """Which elements this idea actually needs, and why. Not a fixed four.

    A mall atrium needs no van; a haat route needs no gondola; a doorstep round needs no stall at all.
    Offering the same four regardless is how three of them end up briefed with something plausible and
    nothing gets built.
    """
    idea = idea or {}
    v = str(idea.get("venue") or "").lower()
    blob = " ".join(str(idea.get(k, "")) for k in ("what", "how", "where", "when")).lower()
    need: list[tuple[str, str]] = []

    mobile = v in ("haat", "sabzi_mandi", "doorstep") or any(
        w in blob for w in ("route", "van", "travel", "town", "village", "door to door", "doorstep"))
    # `rwa` added: it fell through all three branches and got no standing-unit element at all — no
    # stall, no prop-instead-of-a-stall (which `kirana` is explicitly given), and no van. A gap rather
    # than a decision, and this module already contradicted itself about it: VENUES["rwa"]["permits"]
    # reads "Morning or evening stalls, doorstep sampling, weekend demos", and FOOTFALL puts dwell at
    # 3-8 minutes on a 20-40% intercept, which is a place a standing unit works. Surfaced in use:
    # somebody briefed a stall for an RWA idea into a card that existed only because the screen falls
    # back to a fixed four when the served list is empty.
    if v in ("mall_atrium", "modern_trade", "office_complex", "transit", "college",
             "temple_festival", "rwa"):
        need.append(("stall", "It stands in one place all day, so the unit is what people see first."))
    if v in ("kirana",):
        need.append(("prop", "There is no room for a stall — the demo itself has to be the whole unit."))
    if mobile:
        need.append(("van", "It moves between sites, so the vehicle is the stall."))
        if "town" in blob or v == "haat":
            need.append(("truck", "A full market day in one place needs its own power, shade and rig."))
    need.append(("uniform", "What the promoter wears decides whether they are approachable or official."))
    need.append(("education", "What the promoter knows and says. The part that decides whether the rest "
                              "of it works at all."))
    if not any(k == "prop" for k, _ in need):
        need.append(("prop", "The thing a person handles or watches. Without it there is nothing to do."))
    need.append(("capture", "How somebody who engaged becomes a number. A crowd is not a result."))
    need.append(("leave_behind", "What they take home, and why it survives the walk rather than the bin."))
    if str(idea.get("access") or "").strip() or v in ("mall_atrium", "modern_trade", "rwa",
                                                      "temple_festival", "transit", "college"):
        need.append(("permissions", str(idea.get("access") or "")
                     or (VENUES.get(v, {}).get("access") or "Who has to say yes, and how long it takes.")))
    seen, out = set(), []
    for k, why in need:
        if k in seen:
            continue
        seen.add(k)
        out.append({"key": k, "label": k.replace("_", " ").title(),
                    "spec": OG_ELEMENTS.get(k, ""), "why": why})
    return out


def sharpen_idea(idea: str, house: dict | None = None,
                 exec_brief: dict | None = None,
                 platform: dict | None = None,
                 plan: dict | None = None, *, use_house: bool = True,
                 use_platform: bool = True, use_plan: bool = True,
                 brand_mode: str = "") -> tuple[str, str]:
    """Turn an activation idea into one that can be built. Returns (idea, note).

    Returns the idea unchanged rather than inventing one when there is nothing to work from. An empty
    box filled by a model is the fastest way to an activation nobody in the room believes in.
    """
    idea = (idea or "").strip()
    if not idea:
        return "", "Write the idea first — this sharpens one, it does not supply one."
    prompt = (
        "You are planning a consumer activation in India — a stall, a van, a promoter, a street.\n\n"
        f"THE STRATEGY\n{_ctx(house, exec_brief, platform, plan, use_house=use_house, use_platform=use_platform, use_plan=use_plan, brand_mode=brand_mode)}\n\n"
        f"THE IDEA AS WRITTEN\n{idea}\n\n"
        "Tighten it into something buildable in two or three sentences. Name what a person physically "
        "DOES at it — not what they feel or learn. An activation whose central action is 'engages with "
        "the brand' has no central action.\n"
        "Keep the author's idea. Do not replace it with a better one; make theirs specific.\n"
        'Return ONLY JSON: {"idea":"...","what_they_do":"the single physical action"}')
    data, err = _ask(prompt, 800)
    if not data:
        return idea, ("Recorded as written — no generation available."
                      if err == "no key" else f"Recorded as written: {err}.")
    out = str(data.get("idea") or "").strip() or idea
    doing = str(data.get("what_they_do") or "").strip()
    if doing and doing.lower() not in out.lower():
        out = f"{out}\n\nWhat a person does: {doing}"
    return out, ""


def element_brief(element: str, brief_text: str, idea: str, house: dict | None = None,
                  exec_brief: dict | None = None,
                  platform: dict | None = None,
                 plan: dict | None = None, *, use_house: bool = True,
                 use_platform: bool = True, use_plan: bool = True,
                 brand_mode: str = "") -> tuple[str, str]:
    """Brief one element of an on-ground activation against the idea. Returns (brief, note)."""
    spec = OG_ELEMENTS.get(element)
    if not spec:
        return "", f"Unknown element {element!r}."
    if not (idea or "").strip():
        return "", "Settle the activation idea first — the four elements are briefed against it."
    prompt = (
        "You are writing a production brief for one element of a consumer activation in India.\n\n"
        f"THE STRATEGY\n{_ctx(house, exec_brief, platform, plan, use_house=use_house, use_platform=use_platform, use_plan=use_plan, brand_mode=brand_mode)}\n\n"
        f"THE ACTIVATION\n{idea.strip()}\n\n"
        f"THE ELEMENT: {element} — {spec}\n"
        f"WHAT THE AUTHOR HAS WRITTEN SO FAR\n{(brief_text or '(nothing yet)').strip()}\n\n"
        "Write the brief a fabricator or a training lead could work from. Be specific about what it must "
        "survive — heat, rain, being moved daily, being unsupervised.\n"
        "Do not invent dimensions, budgets, quantities or timelines. Where one is needed and not given, "
        "say what has to be decided and by whom.\n"
        'Return ONLY JSON: {"brief":"...","needs_deciding":["..."]}')
    data, err = _ask(prompt, 2600)   # a production brief with a venue and a capture mechanism in it needs room
    if not data:
        return "", ("No generation available — write it by hand."
                    if err == "no key" else f"Generation failed: {err}.")
    out = str(data.get("brief") or "").strip()
    needs = [str(x).strip() for x in (data.get("needs_deciding") or []) if str(x).strip()]
    if needs:
        out += "\n\nStill to be decided: " + "; ".join(needs)
    return out, ""
