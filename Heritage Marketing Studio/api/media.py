"""media.py — one vocabulary for what a medium is.

Before this file there were three, and they agreed on two names out of eight:

    strategy.MEDIA        tv, digital, social, on-ground, ooh, trade, posm          (7)
    ideas.EXPRESSIONS     video, social, posm, activation, incentive, media         (6)
    campaign.MEDIA        the strategy seven, plus influencer                       (8)

`video` and `tv` were the same thing under two names. So were `activation` and `on-ground`, and
`incentive` and `trade`. `media` was in the list at all, which is the tell: a schedule is not a medium.
The cost was not the duplication — it was that the house said POS material was *"roz taaza, roz shakti"*
while the platform said it was *"500 checked this before you"*, two different POS lines in one strategy,
only one of which any producer ever read.

**This module is the single source. Nothing else defines a medium.**

Two structural decisions are recorded here rather than left to be re-derived:

**`digital` is a parent, not a medium.** Social, influencer, owned and performance carry genuinely
different rungs — a repeatable demonstration, borrowed credibility, a place with dwell time, and an
intercept at the moment of intent. Rolling them into one row loses the only useful thing the row could
say. Digital survives as the budget line it actually is.

**`video` is an asset, not a medium.** A film is made once and delivered to tv, to social, to owned and
to performance, each at its own length and ratio. Treating it as a medium put the deliverable in the same
list as the destinations, which is why a 30-second film had nowhere to record its 6-second bumper.

Everything below the target taxonomy is the migration apparatus: the legacy vocabularies verbatim, so
the modules that used to define them can import instead, and a map from every retired key to where its
content goes. Nothing in this file changes behaviour on its own — that is deliberate, and it is what
makes phase 0 reversible.
"""
from __future__ import annotations

# --- the target taxonomy ------------------------------------------------------------------------
#
# Seven at the top, in the order a plan is usually argued rather than alphabetically. `children` is
# empty for the ones that are their own leaf.
MEDIA: dict[str, dict] = {
    "tv": {
        "label": "TV & film",
        "children": (),
        "what": "The only medium with time and narrative.",
    },
    "digital": {
        "label": "Digital",
        "children": ("social", "influencer", "owned", "performance"),
        "what": "A budget line and a planning group, not a medium. Its leaves carry the work.",
    },
    "ooh": {
        "label": "Out of home",
        "children": (),
        "what": "Three seconds at distance, often from a moving vehicle.",
    },
    "posm": {
        "label": "POS material",
        "children": (),
        "what": "The only medium where the brand and the purchase are in the same room.",
    },
    "activation": {
        "label": "Activation",
        "children": (),
        "what": "Somebody standing in a street doing a thing. Venue-bound, and not portable "
                "across venues.",
    },
    "trade": {
        "label": "Trade",
        "children": (),
        "what": "The retailer's own ladder: margin, rate of sale, working capital. Incentives are "
                "levers inside this, per channel — not a medium of their own.",
    },
    "pr": {
        "label": "PR",
        "children": (),
        "what": "Third-party and earned. Carries a proof somebody else vouches for.",
    },
    # Added because there was nowhere to put a spend line that is now ~₹4,900 crore a year in India.
    # Quick-commerce and marketplace advertising is bought FROM the retailer, priced as commission and
    # listing fees, and it decides what appears above the fold in the app where the purchase happens.
    #
    # Deliberately NOT a child of `digital`. It is the one medium that is simultaneously a media buy
    # and a trade negotiation — Blinkit's per-SKU listing fee comes back as ad-wallet credit, so the
    # same rupee is a distribution cost and a media budget depending on which desk is looking. Filing
    # it under `digital` would hide that from the trade desk; filing it under `trade` would hide it
    # from the media plan. It needs to be visible to both, which means it needs its own leaf.
    "retail_media": {
        "label": "Retail media",
        "children": (),
        "what": "Advertising inside the retailer's own surface — quick-commerce search and banners, "
                "marketplace placements. The only medium where the ad and the transaction share an "
                "interface, and the only one the retailer owns the audience for.",
    },
}

# The things that carry a message, and therefore a role. A parent with children is not one of them:
# `digital` has no rung of its own, which is exactly why it needed splitting.
LEAVES: tuple[str, ...] = (
    "tv", "social", "influencer", "owned", "performance", "ooh", "posm", "activation", "trade", "pr",
    "retail_media",
)

PARENT: dict[str, str] = {
    child: parent for parent, spec in MEDIA.items() for child in spec["children"]
}

# Sub-media labels. Kept beside the parents rather than nested, so a lookup is one hop for either.
LEAF_LABEL: dict[str, str] = {
    "tv": "TV & film",
    "social": "Social",
    "influencer": "Influencer",
    "owned": "Owned",
    "performance": "Performance",
    "ooh": "Out of home",
    "posm": "POS material",
    "activation": "Activation",
    "retail_media": "Retail media",
    "trade": "Trade",
    "pr": "PR",
}

# `video` is not here, and that is the point. It is a deliverable that lands on several of these.
VIDEO_DELIVERS_TO: tuple[str, ...] = ("tv", "social", "owned", "performance")


# --- what each leaf is FOR ----------------------------------------------------------------------
#
# Derived from the rung of the ladder a medium can carry, not from convention. Moved here from
# `campaign.ROLE_BY_RUNG` so that the role and the vocabulary cannot drift apart.
#
# Two entries are new. `digital`'s old role read "the bridge, demonstrated, at high intent", which was
# two jobs in one sentence: a place with dwell time where a mechanism can be shown at length, and an
# intercept aimed at somebody already looking. Splitting the medium split the role, and the split is the
# argument for the split. `pr` had no entry at all, despite PR being one of the seven brief formats the
# builder already writes — you could brief it and it had no rung in the spine.
ROLE_BY_RUNG: dict[str, tuple[str, str]] = {
    "tv":          ("emotional endpoint + the turn",
                    "The only medium with time and narrative, so the only one that can RESOLVE a "
                    "tension. If the film does not turn, nothing downstream has a feeling to remind "
                    "anyone of."),
    "social":      ("the bridge, demonstrated",
                    "Enough time to show a mechanism. Proof in a format that rewards showing over "
                    "asserting."),
    "influencer":  ("emotional endpoint, third-party",
                    "Someone like the buyer saying she got there. De-risks the claim. Credibility, "
                    "never construction — an influencer cannot build a feeling the work has not made."),
    "owned":       ("the bridge, demonstrated at length",
                    "The brand's own property — site, landing page, commerce. The only medium with "
                    "real dwell time, so the one place a claim can be substantiated in full rather "
                    "than asserted. Ends in an action."),
    "performance":  ("one rung, at the moment of intent",
                     "Search, display, retargeting. It reaches somebody already looking, which means "
                     "it has to answer rather than persuade. No room to build anything — pick the rung "
                     "that closes the question she already has."),
    "posm":        ("functional truth + emotional RECALL",
                    "Two metres, two seconds. It cannot build emotion, only trigger emotion something "
                    "else built — which is why POSM without a film works on the functional truth "
                    "and the brand's codes, and why its cast and device must match the film exactly."),
    "ooh":         ("one rung, chosen",
                    "Three seconds at distance. Pick the functional truth or the code, never both."),
    "activation":  ("the bridge, experienced",
                    "She does the thing, so the bridge stops being a claim. The one medium that can "
                    "turn a meaning into a behaviour, and the only one that can capture her."),
    "trade":       ("OFF the consumer ladder entirely",
                    "The retailer has his own ladder: margin, rate of sale, working capital, and the "
                    "one line his customers will repeat. Borrowing the consumer line for him is the "
                    "most common way a good campaign dies at the counter."),
    "pr":          ("the functional truth, earned",
                    "Third-party verification of something the brand cannot say about itself without "
                    "sounding like it is selling. It carries a proof and it cannot construct a "
                    "feeling — the same limit as an influencer, without the payment."),
    "retail_media": ("the last comparison, won or lost",
                    "The buyer is already in the app with intent, looking at three products at once. "
                    "This rung builds nothing — it wins or loses the comparison at the moment money "
                    "moves. Judged on conversion and cost per order, never on reach: a retail-media "
                    "impression served to somebody who was already buying is not incremental, and "
                    "counting it as reach is how this line gets over-credited."),
}


# --- migration ----------------------------------------------------------------------------------
#
# Every retired key has a destination. Nothing is deleted silently, following the pattern
# `ideas.RETIRED_TESTS` already set.
ALIASES: dict[str, str] = {
    "on-ground": "activation",      # renamed; the venue is an attribute, not a sibling medium
    "video": "tv",                  # and to digital's leaves, as a deliverable — see VIDEO_DELIVERS_TO
    "incentive": "trade",           # incentives are levers per channel, which sales.py already models
}

# Keys that do not survive as media at all, and where their content goes instead.
RETIRED: dict[str, str] = {
    "video": "an asset, not a medium — delivered to tv, social, owned and performance at their own "
             "lengths and ratios",
    "incentive": "trade, as a lever per channel — sales.LEVERS already carries 'display incentive', "
                 "'trade scheme', 'retailer margin' and 'loyalty programme'",
    "media": "A schedule is not a medium. Parked 2026-08-20 and landed 2026-08-25: it is its own "
             "top-level Media tab, and it is retired from the Execution producers — see "
             "execution.RETIRED_KINDS['media'] for why a producer was the wrong shape. It was NOT "
             "routed into the plan, which the parking note warned against: the plan keeps the "
             "strategy (channel roles, sides, the declared split, the phase windows) and the Media "
             "tab derives from it read-only rather than asking again.",
}

# Legacy keys whose content needs a person to look at it, because the mapping is a judgement rather
# than a rename. `digital` is the only one: its stored options could be a site, a search line or a
# social post, and only a reader can tell which.
NEEDS_REVIEW: dict[str, str] = {
    "digital": "owned",
}


def normalise(key: str) -> str:
    """A legacy key resolved to its current name. **Renames only.**

    Unknown keys come back unchanged on purpose: a key this module has not heard of is a bug somewhere
    else, and swallowing it here would hide it.

    `NEEDS_REVIEW` is deliberately NOT applied here, and the first version of this function got that
    wrong. Resolving `digital` to `owned` made `role_for("digital")` return the owned role — so a parent
    with no rung of its own answered as though it had one, which is precisely the thing splitting it was
    meant to stop. A rename and a content migration are two different operations: one is always safe,
    the other is a guess a person has to confirm. See `migrate()`.
    """
    k = str(key or "").strip().lower()
    return ALIASES.get(k, k)


# The reverse of ALIASES: for a target key, every legacy name that used to mean it. Built once at
# import time rather than inverted on every call.
_LEGACY_KEYS_FOR: dict[str, tuple[str, ...]] = {}
for _legacy, _target in ALIASES.items():
    _LEGACY_KEYS_FOR.setdefault(_target, ())
    _LEGACY_KEYS_FOR[_target] = _LEGACY_KEYS_FOR[_target] + (_legacy,)
del _legacy, _target


# Every way a leaf can be written, built once: the id, its label, and any retired name for it. Used
# only by `resolve_text` below — a lookup table, not a second taxonomy.
_TEXT_INDEX: dict[str, str] = {}
def _key_forms(s: str) -> tuple[str, ...]:
    """Every spelling of one name worth indexing or looking up. `&` both kept and dropped, because
    "TV & film" is a real label and dropping the ampersand unconditionally lost it."""
    base = " ".join(str(s or "").split()).strip().lower().rstrip(",;:-")
    amp = " ".join(base.replace("&", " ").split())
    return tuple(dict.fromkeys(f for f in (base, amp, base.replace(" ", "_"),
                                           amp.replace(" ", "_")) if f))


for _leaf in LEAVES:
    for _f in _key_forms(_leaf) + _key_forms(LEAF_LABEL.get(_leaf, _leaf)):
        _TEXT_INDEX[_f] = _leaf
    for _old in _LEGACY_KEYS_FOR.get(_leaf, ()):
        for _f in _key_forms(_old):
            _TEXT_INDEX[_f] = _leaf
del _leaf, _f


# The value a person picks when a channel row is genuinely not one medium. Stored, not blank, because
# "nobody has said" and "somebody looked and said it is several" are different facts and the second one
# is a finding: a budget line in the channels layer needs splitting before it can carry a weight.
MULTIPLE = "multiple"

MULTIPLE_WHY = ("Declared as more than one medium, so it cannot be weighted as one. Split the row into "
                "the media it actually covers and the weight becomes meaningful.")


def options() -> list[dict]:
    """The eleven leaves plus `multiple`, in the order a select should offer them.

    Served rather than left to a screen to assemble, because a list of media built on the client is
    exactly the `MEDIA_DEFS` failure this module exists to end.
    """
    return [{"key": m, "label": LEAF_LABEL.get(m, m), "parent": PARENT.get(m, "")}
            for m in LEAVES] + [
        {"key": MULTIPLE, "label": "Not one medium — needs splitting", "parent": ""}]


def resolve_text(text: str) -> dict:
    """The leaf a free-text channel name means, or an honest refusal.

    The plan's `channels` layer stores prose, not ids — "TV (regional GEC + connected TV, South)" or
    "On-ground (RWA / apartment activation, promoter)". That prose is the plan's own words for the job
    and is worth keeping, but it cannot be joined to anything: not to this taxonomy, not to the jobs
    table, and not to a second plan. Two plans that both mean `tv` produce two different media.

    So this resolves the HEAD of the string — everything before the first bracket — against leaf ids,
    leaf labels and retired names. Exact match only, after casefolding and whitespace collapse. It does
    not stem, guess from the first word of a longer phrase, or score similarity, because a medium
    filed under the wrong leaf is worse than one filed under none: the weight, the ink and the join all
    follow the id, and a wrong id is invisible while a missing one is not.

    A head that resolves to a PARENT is refused rather than pushed onto one of its children.
    `digital` is the whole reason this taxonomy split: it has four leaves with four different rungs and
    only a reader can tell which one a line means. Returning `owned` here would be `NEEDS_REVIEW`
    applied silently, which `normalise` documents as the bug it already made once.

    Returns `{medium, label, confident, why}`. `medium` is '' whenever `confident` is False, so a
    caller cannot accidentally use a hedge as an id.
    """
    raw = str(text or "").strip()
    if not raw:
        return {"medium": "", "label": "", "confident": False,
                "why": "This channel has no name, so there is nothing to resolve."}
    forms = _key_forms(raw.split("(")[0])
    head = forms[0] if forms else ""
    hit = next((_TEXT_INDEX[f] for f in forms if f in _TEXT_INDEX), "")
    if hit:
        return {"medium": hit, "label": LEAF_LABEL.get(hit, hit), "confident": True, "why": ""}
    parent = normalise(head)
    if parent in MEDIA and MEDIA[parent]["children"]:
        kids = ", ".join(MEDIA[parent]["children"])
        return {"medium": "", "label": MEDIA[parent]["label"], "confident": False,
                "why": (f"{MEDIA[parent]['label']!s} is a budget line, not a medium — it covers "
                        f"{kids}, and those carry different rungs. Which one this channel means is a "
                        f"reading of the row, not something this can infer.")}
    return {"medium": "", "label": "", "confident": False,
            "why": (f"No medium in the taxonomy is written {head!r}. The plan's channel names are "
                    f"prose, so this one carries no id to weight, colour or join on. One of: "
                    f"{', '.join(LEAVES)}.")}


def legacy_keys_for(leaf: str) -> tuple[str, ...]:
    """Every retired name that used to mean this leaf — `activation` -> `('on-ground',)`.

    For reading a dict that was written under the OLD key. `normalise()` translates a key going
    forward; this is the read-side mirror, needed anywhere old data is keyed by a name a rename left
    behind. Written for `campaign.jobs()`, where a role a person typed under `on-ground` before the
    rename was being silently dropped: the lookup checked `roles.get("activation")`, found nothing
    under the new name, and fell back to the computed default — the exact same failure this project
    keeps finding, just one layer further down than the JSON key names it usually bites at.
    """
    return _LEGACY_KEYS_FOR.get(normalise(leaf), ())


def migrate(key: str) -> tuple[str, bool]:
    """Where a legacy key's stored CONTENT should go. `(target, needs_review)`.

    Used when folding old data forward, never to resolve a live key. `digital` is the only entry that
    needs review: its stored options could be a site, a search line or a social post, and only a reader
    can tell which — so it lands on `owned` with the flag set rather than being silently filed.
    """
    k = str(key or "").strip().lower()
    if k in ALIASES:
        return ALIASES[k], False
    if k in NEEDS_REVIEW:
        return NEEDS_REVIEW[k], True
    return k, False


def is_leaf(key: str) -> bool:
    return normalise(key) in LEAVES


def parent_of(key: str) -> str:
    """The budget line a leaf sits under, or '' for a leaf that is its own top level."""
    return PARENT.get(normalise(key), "")


def children_of(key: str) -> tuple[str, ...]:
    return tuple((MEDIA.get(normalise(key)) or {}).get("children", ()))


def label(key: str) -> str:
    k = normalise(key)
    return LEAF_LABEL.get(k) or (MEDIA.get(k) or {}).get("label") or k


def role_for(key: str) -> tuple[str, str]:
    """`(role, why)` for a leaf, or `('', '')`. A parent has no role — that is what makes it a parent."""
    return ROLE_BY_RUNG.get(normalise(key), ("", ""))


def grouped() -> list[dict]:
    """The taxonomy as a screen would render it: top level in order, each with its leaves."""
    out = []
    for key, spec in MEDIA.items():
        kids = spec["children"]
        out.append({
            "key": key, "label": spec["label"], "what": spec["what"],
            "is_parent": bool(kids),
            "leaves": [{"key": c, "label": label(c),
                        "role": role_for(c)[0], "why": role_for(c)[1]} for c in kids]
                      or ([{"key": key, "label": spec["label"],
                            "role": role_for(key)[0], "why": role_for(key)[1]}] if key in LEAVES
                          else []),
        })
    return out


def status() -> dict:
    """Everything a screen or a check needs, from one place."""
    return {
        "media": grouped(),
        "leaves": list(LEAVES),
        "parents": {k: list(v["children"]) for k, v in MEDIA.items() if v["children"]},
        "roles": {k: {"role": v[0], "why": v[1]} for k, v in ROLE_BY_RUNG.items()},
        "aliases": dict(ALIASES),
        "retired": dict(RETIRED),
        "needs_review": dict(NEEDS_REVIEW),
        "video_delivers_to": list(VIDEO_DELIVERS_TO),
    }


# --- the legacy vocabularies, held verbatim -----------------------------------------------------
#
# These are what `strategy`, `ideas` and `campaign` used to define for themselves, character for
# character. They import from here instead, so there is one file to read and one file to change — and
# because they are identical, importing them changes nothing that a user can see.
#
# They are retired one at a time in the phases that follow, each behind a fold-on-read. Until then the
# target taxonomy above is defined and unused, which is the whole point of a phase that cannot break
# anything.
# Order matters here beyond readability: this tuple drives the medium-tag chip order in the house's
# medium layer AND (via campaign.py's `MEDIA`) the row order in the campaign grid, and until now the
# two disagreed with each other and with the frontend's own `CAMPAIGN_ROLES` list for the same seven
# names -- three screens, three orders, for one vocabulary. TV, Digital, Social, On-ground, OOH,
# Trade, POSM is now the one order; `LEGACY_CAMPAIGN_MEDIA` below inserts `influencer` into it rather
# than appending it, and `CAMPAIGN_ROLES` in app.dc.html matches this exactly.
LEGACY_STRATEGY_MEDIA: tuple[str, ...] = (
    "tv", "digital", "social", "on-ground", "ooh", "trade", "posm",
)

# NOT legacy, despite sitting among the legacy vocabularies — and renamed from `LEGACY_EXPRESSIONS`
# to say so. Its neighbours above are lists of MEDIA awaiting retirement. This is keyed by PRODUCER
# KIND, and producers are the live consumers: `execution.brief_from` reads
# `platform["expressions"][kind]`, not `[medium]`. Keying by kind is correct rather than historical,
# because an expression is what a maker works from — a film and a shelf strip are different acts even
# when they carry the same medium's message.
#
# `_expression_slots_by_leaf` maps each key here onto a leaf through `normalise`, so a key whose
# normalised form is not in LEAVES (e.g. `media`) simply has no leaf and is reported as parked.
EXPRESSIONS: dict[str, str] = {
    "video":      "The situation, and what turns in it.",
    "social":     "The repeatable unit. Social is a format problem before it is an idea problem.",
    "posm":       "What a shopper sees at two metres, in bad light, next to nine other brands.",
    "activation": "What a person physically does — not what they feel.",
    "incentive":  "What the retailer gets out of it, in their arithmetic. Not the consumer line.",
    # Added round 53, when the frontend's Expression-by-medium screen moved from six producer-kind
    # rows to the eight-medium vocabulary and stopped treating `digital` as a row at all (it has no
    # rung of its own -- see LEGACY_STRATEGY_MEDIA above -- and its content is `influencer` and
    # `social`, not a slot of its own). Both are real LEAVES already; this just gives the jobs-table
    # cross-check something to say about them instead of reporting them as parked.
    "influencer": "What a creator says in their own words, not a script read at camera.",
    "ooh":        "The one thing read in three seconds from a moving vehicle.",
    # PR's slot. Added because the jobs table has always shown a `pr` row whose expression cell was
    # structurally incapable of holding anything — `pr` was a leaf with a role and no slot, so the
    # cell could only ever be empty. The wording follows `ROLE_BY_RUNG["pr"]`: PR carries a proof
    # somebody else vouches for, so what it needs from the platform is the checkable fact, not the
    # feeling. A platform expression here that reads like a tagline is the tell that it is wrong.
    "pr":         "The one checkable fact a journalist could stand behind — not the line.",
    # `media` used to exist only as a "route" and had no expression slot, which was the seam that split
    # this layer in two. See ideas._fold_routes.
    "media":      "What the platform demands of the schedule — a shape, not a spend.",
}

# `influencer` inserted after `social`, where the campaign role table and execution screens put it --
# not appended at the end, which is what `LEGACY_STRATEGY_MEDIA + ("influencer",)` used to do.
LEGACY_CAMPAIGN_MEDIA: tuple[str, ...] = (
    "tv", "digital", "social", "influencer", "on-ground", "ooh", "trade", "posm",
)

# The role table as `campaign.py` held it, for the same reason: identical values, one definition. The
# target `ROLE_BY_RUNG` above differs from this in exactly three ways — `on-ground` is now `activation`,
# `digital` has become `owned` plus `performance`, and `pr` exists.
LEGACY_ROLE_BY_RUNG: dict[str, tuple[str, str]] = {
    "tv":         ROLE_BY_RUNG["tv"],
    "influencer": ROLE_BY_RUNG["influencer"],
    "on-ground":  ROLE_BY_RUNG["activation"],
    "social":     ROLE_BY_RUNG["social"],
    "digital":    ("the bridge, demonstrated, at high intent",
                   "The same job as social, aimed at somebody already looking. Ends in an action."),
    "posm":       ROLE_BY_RUNG["posm"],
    "ooh":        ROLE_BY_RUNG["ooh"],
    "trade":      ROLE_BY_RUNG["trade"],
}
