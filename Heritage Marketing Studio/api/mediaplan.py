"""mediaplan.py — the media desk. MP·1 the derived strategy, MP·2 the competitive picture.

MP·1 (`channels`…`strategy_view`) **stores nothing, and that is the whole point of the phase.**

Most of what a media strategy is already exists in the IMC plan. The `channels` layer carries a role
per channel (reach / proof / conversion / advocacy), which side of the brand-activation line it sits
on, a share of spend, an owner and a lead. The `balance` layer carries the declared split. The `phases`
layer carries windows, occasions and which channels each phase hands to. On the live Heritage plan
every channel has a role and a side, and the split is declared with a reason.

So a media screen that asked those questions again would be a second place to decide something already
decided — and the moment the two disagree nobody knows which is real. This project has been bitten by
that exact shape more than once: `grid()` and `jobs()` computing the same table, the house count living
in four templates, `hasCut` defined in two bags. Every time, the fix was one definition and one reader.

What the media desk owns is everything BELOW the strategy: weight, money, flighting, the competitive
picture, the campaign structure and the calendar. None of that exists yet. This module is the read-only
derivation those layers will hang from, plus an honest account of what is missing before they can.

`media` also stopped being an Execution producer in this phase — see `execution.RETIRED_KINDS`. A
producer makes one thing that says something; a media plan decides how much each producer gets, which
is a different axis entirely.

MP·2 (`ci_load`…`ci_view`) is the second half, and it DOES store: the competitor set, what each one
spends or merely runs, and the brand's own market share. It comes before the weights on purpose,
because the split is set against the category rather than in a vacuum — share of voice is only a number
once you know what everyone else is doing.

Its whole design problem is that **most studios cannot buy the data this needs**, and the tempting
failure is to produce a share-of-voice figure anyway out of whatever was free to find. That number
would be wrong in a way nobody could see, because a share is a ratio and a ratio with an incomplete
denominator does not look broken. So the module works at three declared levels and says which one it is
on — see `LEVELS` — and refuses to compute a share it cannot stand behind. "Share of voice
unavailable, and here is exactly what is missing" is the useful answer; a plausible 22% is not.
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid

import brandprofile
import media as media_mod
import plan as plan_mod
import tenancy

# What a media plan needs from the plan above it before any of it can be weighted. Each entry names the
# layer, what media takes from it, and what media adds — because the second column is the argument for
# deriving rather than re-asking, and it should be renderable rather than only written in a document.
DERIVES: dict[str, dict] = {
    "objectives": {
        "takes": "The communication-level row — what the schedule has to achieve.",
        "adds": "Nothing. Media does not set objectives, and a media plan that invents one is a plan "
                "judged on its own homework.",
    },
    "audiences": {
        "takes": "Who, ranked, and which pillar each answers to.",
        "adds": "The buyable definition — the audience as something a platform can target, which is "
                "never the same sentence.",
    },
    "channels": {
        "takes": "The strategy itself: role, side, lead and owner per channel.",
        "adds": "Weight, money, and the medium-level detail — which platforms inside 'digital', which "
                "editions, which dayparts.",
    },
    "balance": {
        "takes": "The declared brand share, and whether anybody actually declared it.",
        "adds": "What that split costs, and whether the channel weights reconcile with it.",
    },
    "phases": {
        "takes": "Windows, occasions, and which channels each phase hands to.",
        "adds": "Weight per week inside the window — the flighting shape. The skeleton is already "
                "there; this puts weight on it.",
    },
    "measures": {
        "takes": "Leading and lagging measures per role, and what would tell us it failed.",
        "adds": "The media metric that maps to each role — a reach channel judged on coverage, never "
                "on clicks.",
    },
}


# What the desk can and cannot do, as of now. Kept next to the code it describes rather than written on
# a screen, because the screen would go stale the moment a phase lands — as it already had: the Media tab
# listed competitive intelligence and money as "not yet" after both were built.
#
# The `cannot` half is the more useful one and is deliberately specific. "Not yet" is a roadmap; "there
# is no ratings currency for Indian television right now, and here is why" is a fact a planner has to
# work around today.
CAN: dict[str, dict] = {
    "strategy": {"label": "Derive the strategy from the plan",
                 "what": "Roles, sides and the brand/activation split, read from the IMC plan and never "
                         "re-asked. Read-only by design — there is one place each of those is true."},
    "competitive": {"label": "Hold the competitive picture",
                    "what": "The competitor set, activity by medium and period, share of voice and "
                            "ESOV wherever the entered data actually supports them."},
    "honest_levels": {"label": "Say what it cannot compute, and why",
                      "what": "Share of voice needs a complete denominator. Where one is missing the "
                              "desk names who is missing rather than producing a plausible share — and "
                              "it reports which of three data levels it is operating at."},
    "geography": {"label": "List states, union territories and key cities",
                  "what": "All 36 states and UTs, and cities above a population line on one declared "
                          "basis. Names, codes and old names all resolve."},
    "language": {"label": "Name the language gaps before the money is committed",
                 "what": "Ten of thirty-six states have a principal language the studio cannot write "
                         "in. Buying those in Hindi and hoping is a media cost with no message."},
    "money": {"label": "Hold a geography-wise social budget",
              "what": "One cell per geography, shaped like a Meta ad set — geography, budget and "
                      "optimisation goal on one object, because that is where all three actually live."},
    "feasibility": {"label": "Check whether a geography split can run at all",
                    "what": "A conversion ad set needs about 50 optimisation events a week and "
                            "dividing the budget does not divide the threshold. The desk computes how "
                            "many cells the money supports, before anything is spent."},
    "tradeoffs": {"label": "Name the tradeoffs rather than resolve them",
                  "what": "Pooled versus per-cell budget, how fine to split, radius against cost per "
                          "thousand, and language coverage. Each with what it buys and what it costs."},
}

CANNOT: dict[str, dict] = {
    "performance": {"label": "Say whether a campaign is working",
                    "what": "That needs delivery data. Until a platform account is connected or the "
                            "actuals are entered there are none, so nothing here ranks a geography by "
                            "performance — and a plan that implied it could would be inventing."},
    "weight": {"label": "Weight the channels",
               "what": "This is the gap the desk exists to close and it is not closed. No channel in "
                       "the live plan carries a share, so the split can only be computed on channel "
                       "count — which is a different claim from spend."},
    "flighting": {"label": "Put weight on the flighting",
                  "what": "The phase windows exist and are read. Weight per week inside them does not."},
    "calendar": {"label": "Produce a media-ready content calendar",
                 "what": "Not built. It needs the weight and the flighting under it first."},
    "tv": {"label": "Plan television against a ratings currency",
           "what": "There is not one to plan against. BARC's ratings were halted and a unified "
                   "television-plus-streaming measure is not expected before September 2026. The desk "
                   "will not emit a GRP it cannot source, so TV is planned on reach logic and spend."},
    "sov_without_spend": {"label": "Compute share of voice from free sources",
                          "what": "The free ad libraries publish creative and run dates, and spend "
                                  "only for political advertising. Presence is real and useful; a "
                                  "share of voice built on it would be a guess with a citation."},
    "platform_reach": {"label": "Read the platform's own audience estimates",
                       "what": "No API connection, so the operative number for buying — what Ads "
                               "Manager says it can actually reach — has to be read there and entered "
                               "here. A census population is not a substitute and is not treated as one."},
}


def _rows(p: dict | None, layer: str) -> list[dict]:
    return (((p or {}).get("nodes") or {}).get(layer) or {}).get("rows") or []


def _share_of(row: dict) -> float | None:
    """A channel's share of spend as a number, or None. Same parsing as `plan.actual_split`."""
    try:
        return float(str(row.get("share", "")).replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def channels(p: dict | None) -> list[dict]:
    """The plan's channels as a media strategy — role, side, weight, and where each one runs.

    `judged_on` comes from `plan.ROLES`, not from a copy. That sentence is the whole discipline of
    media measurement in one line each ("Get to people who do not yet think of us. Judged on coverage
    and cost per reach.") and it was already written; restating it here is how two definitions start.
    """
    phases = _rows(p, "phases")
    out = []
    for r in _rows(p, "channels"):
        name = str(r.get("channel") or "").strip()
        role = str(r.get("role") or "").strip().lower()
        share = _share_of(r)
        # Which phases hand to this channel. The phases layer stores `channels` as free text, so this
        # is a containment test rather than a join — reported as a hint, never as a fact to compute on.
        appears = [str(ph.get("phase") or "") for ph in phases
                   if name and name.split("(")[0].strip().lower()[:12]
                   in str(ph.get("channels") or "").lower()]
        # The channel name is prose the plan wrote, so it joins to nothing on its own. `medium` is the
        # taxonomy leaf it resolves to, and it is '' whenever that resolution is not certain — a
        # screen keying ink, weight or a join on it gets an id or gets nothing, never a guess. The
        # prose stays in `channel` because it is the plan's own word for the job.
        # `medium` is now a COLUMN on the channels layer, so the first question is what a person
        # declared. The text resolver stays only as a suggestion for rows written before the column
        # existed, and it is a weak one: across the real plans in this repo it fires on a minority of
        # rows, because a channel called "Outdoor / transit near residential clusters" leads with
        # neither an id nor a label. So a suggestion is offered and never silently adopted -
        # `medium` carries a declared id or nothing, and `medium_source` says which.
        declared = str(r.get("medium") or "").strip().lower()
        med = media_mod.resolve_text(name)
        if declared == media_mod.MULTIPLE:
            medium, source, why = "", "multiple", media_mod.MULTIPLE_WHY
        elif declared in media_mod.LEAVES:
            medium, source, why = declared, "declared", ""
        else:
            medium, source, why = "", "undeclared", (
                "No medium declared on this channel, so it cannot be weighted, coloured or joined to "
                "the jobs table. " + (f"Its name reads like {med['label']} - confirm it in the plan."
                                      if med["confident"] else med["why"]))
        out.append({
            "channel": name,
            "medium": medium,
            "medium_label": media_mod.LEAF_LABEL.get(medium, "") if medium else med["label"],
            "medium_confident": bool(medium),
            "medium_source": source,
            "medium_why": why,
            # Offered, never adopted. '' when the resolver is not sure either.
            "medium_suggested": med["medium"] if (not medium and med["confident"]) else "",
            "medium_suggested_label": med["label"] if (not medium and med["confident"]) else "",
            "role": role,
            "role_label": role or "",
            "judged_on": plan_mod.ROLES.get(role, ""),
            "side": str(r.get("side") or "").strip().lower(),
            "job": str(r.get("job") or "").strip(),
            "measure": str(r.get("measure") or "").strip(),
            "owner": str(r.get("owner") or "").strip(),
            "lead": str(r.get("lead") or "").strip(),
            "share": share,
            "has_share": share is not None,
            "phases": appears,
            "phase_hint": bool(appears),
        })
    return out


def flighting_skeleton(p: dict | None) -> list[dict]:
    """The phases as the shape a schedule will be hung on. Windows with no weight on them yet."""
    return [{
        "phase": str(r.get("phase") or "").strip(),
        "window": str(r.get("window") or "").strip(),
        "occasion": str(r.get("occasion") or "").strip(),
        "channels": str(r.get("channels") or "").strip(),
        "hands_over": str(r.get("hands_over") or "").strip(),
        "has_window": bool(str(r.get("window") or "").strip()),
    } for r in _rows(p, "phases")]


def split(p: dict | None) -> dict:
    """The declared split, the actual, and where the default's 60 comes from.

    All three from `plan`: `balance_of` folds the declared flag, `actual_split` reports its own basis,
    and `BRAND_SHARE_BASIS` carries the citation and the dispute. Nothing recomputed here.
    """
    bal = plan_mod.balance_of(p or {})
    # Same keys as a real `actual_split`, including `trusted`: a payload missing the flag makes the
    # Plan rail fall back to reading the basis prose, and "no channels yet" does not match that
    # test — so an absent flag here would have rendered as quietly trustworthy.
    act = plan_mod.actual_split(p or {}) if _rows(p, "channels") else {
        "brand": None, "activation": None, "basis": "no channels yet",
        "weighted": 0, "n_channels": 0, "sum": None, "sums_to_100": None, "trusted": False}
    gap = None
    if act.get("brand") is not None:
        gap = int(act["brand"]) - int(bal["brand_share"])
    return {
        # `brand_share`, not `declared_share`. `plan.balance_of` calls it `brand_share`, `/plan-status`
        # publishes it under that name and `/plan-balance` accepts it — so a third name here for the
        # identical fact was the exact two-definitions failure this module's own docstring complains
        # about, and it made the Media screen read the split as "not set" while the Plan screen read 60.
        "brand_share": int(bal["brand_share"]),
        "declared": bool(bal["declared"]),
        "reason": str(bal.get("reason") or ""),
        "basis": str(bal.get("basis") or "year"),
        "actual": act,
        "gap": gap,
        "gap_matters": bool(gap is not None and abs(gap) >= 10),
        "default": plan_mod.DEFAULT_BRAND_SHARE,
        "basis_of_default": plan_mod.BRAND_SHARE_BASIS,
    }


def findings(p: dict | None) -> list[dict]:
    """What is missing before a media plan can be weighted. Blocking where it genuinely blocks.

    Deliberately does not repeat what `plan.status` already reports. The plan already flags a declared
    split that the channels contradict, and an undeclared default. Saying it twice in two vocabularies
    is how the two start to disagree — so this reports only what is missing for MEDIA specifically.
    """
    out: list[dict] = []
    chans = channels(p)

    if not p:
        return [{"layer": "media", "level": "gap", "blocking": True,
                 "what": "No plan open",
                 "why": "The media desk derives its strategy from a plan. Without one there is nothing "
                        "to derive and nothing worth asking for."}]
    if not chans:
        out.append({"layer": "media", "level": "gap", "blocking": True,
                    "what": "The plan has no channels",
                    "why": "Channels carry the roles and sides that ARE the media strategy. Until they "
                           "exist there is nothing here but an empty grid."})
    no_role = [c["channel"] for c in chans if not c["role"]]
    if no_role:
        out.append({"layer": "media", "level": "gap", "blocking": True,
                    "what": f"{len(no_role)} channel(s) carry no role",
                    "why": "A role decides what a channel is judged on. Weighting a channel whose job "
                           "nobody stated means buying something with no way to tell if it worked."})
    no_side = [c["channel"] for c in chans if not c["side"]]
    if no_side:
        out.append({"layer": "media", "level": "gap", "blocking": True,
                    "what": f"{len(no_side)} channel(s) carry no brand/activation side",
                    "why": "The split cannot be reconciled against channels that have not picked a "
                           "side, so the declared share becomes unenforceable."})

    unweighted = [c["channel"] for c in chans if not c["has_share"]]
    if chans and len(unweighted) == len(chans):
        out.append({"layer": "media", "level": "gap", "blocking": False,
                    "what": "No channel carries a weight yet",
                    "why": "This is the gap the media desk exists to close, so it is expected rather "
                           "than wrong. Until it is closed the split can only be computed on channel "
                           "count, which is a different claim from spend."})
    elif unweighted:
        out.append({"layer": "media", "level": "risk", "blocking": False,
                    "what": f"{len(unweighted)} of {len(chans)} channel(s) unweighted",
                    "why": "A partly weighted plan is the worst of both: the split looks computed on "
                           "spend and is actually computed on whatever happens to be filled."})

    no_window = [f["phase"] for f in flighting_skeleton(p) if not f["has_window"]]
    if no_window:
        out.append({"layer": "media", "level": "risk", "blocking": False,
                    "what": f"{len(no_window)} phase(s) have no window",
                    "why": "Flighting is checked against the phase's own dates. A phase with no window "
                           "cannot hold weight that can be verified as inside it."})

    order = {"gap": 0, "risk": 1, "note": 2}
    out.sort(key=lambda f: (not f["blocking"], order.get(f["level"], 3)))
    return out


def strategy_view(p: dict | None, house: dict | None = None) -> dict:
    """The whole derived strategy, read-only. The Media tab's first screen.

    `derived: True` is on the payload deliberately: a screen showing this must not offer an edit, and a
    reader should be able to tell at a glance that these decisions live in the plan.
    """
    chans = channels(p)
    fs = findings(p)
    return {
        "derived": True,
        "derives_from": {"plan": (p or {}).get("id", ""), "house": (house or {}).get("id", "")},
        "channels": chans,
        "roles": plan_mod.ROLES,
        "sides": list(plan_mod.SIDES),
        "split": split(p),
        "flighting": flighting_skeleton(p),
        "derives": DERIVES,
        "counts": {
            "channels": len(chans),
            "with_role": sum(1 for c in chans if c["role"]),
            "with_side": sum(1 for c in chans if c["side"]),
            "with_weight": sum(1 for c in chans if c["has_share"]),
            "brand": sum(1 for c in chans if c["side"] == "brand"),
            "activation": sum(1 for c in chans if c["side"] == "activation"),
            "with_medium": sum(1 for c in chans if c["medium"]),
            "with_suggestion": sum(1 for c in chans if not c["medium"] and c["medium_suggested"]),
            "declared_multiple": sum(1 for c in chans if c["medium_source"] == "multiple"),
        },
        # The eleven leaves, so a screen never needs a local list to know what a medium can be, and
        # `unresolved` so it can say which of the plan's own channels this taxonomy could not place.
        # Both are here rather than left to a second call: a vocabulary fetched separately from the
        # rows it describes is how the two start to disagree.
        "leaves": [{"key": m, "label": media_mod.LEAF_LABEL.get(m, m),
                    "parent": media_mod.parent_of(m)} for m in media_mod.LEAVES],
        # Rows that cannot be weighted: no medium declared. A confident SUGGESTION does not remove a
        # row from this list, because a guess is not a declaration - it travels with the row so the
        # screen can offer it as one click rather than making somebody re-derive it.
        "unresolved": [{"channel": c["channel"], "why": c["medium_why"],
                        "suggested": c["medium_suggested"],
                        "suggested_label": c["medium_suggested_label"],
                        "source": c["medium_source"]}
                       for c in chans if not c["medium"]],
        "findings": fs,
        "blocking": [f["what"] for f in fs if f["blocking"]],
        "ready_to_weight": not any(f["blocking"] for f in fs),
        "why_read_only": ("Roles, sides and the split are decisions the plan already made. The media "
                          "desk reads them so there is one place they are true; it owns the weight, "
                          "the money, the flighting and the calendar, which the plan does not."),
    }


# ======================================================================================
# MP·2 — the competitive picture
# ======================================================================================
#
# Share of voice is a ratio, and every honest thing in here follows from that one fact. A ratio needs a
# complete denominator, and the two ways it goes wrong are both invisible on a screen:
#
#   1. A competitor in the set has no spend figure, so they contribute 0 to the total and every other
#      share is inflated. Nothing looks broken; the shares still sum to 100.
#   2. The set itself is short — three named competitors in a category with nine — so the shares are
#      real but they are shares of the wrong universe.
#
# Neither is detectable by looking at the output, so both are refused at the input. `sov` will not
# compute unless every participant carries a figure for that period, and it never claims to be a share
# of the CATEGORY unless someone has explicitly declared the set complete and said on what basis.
# Without that declaration it reports itself as a share of the listed set, which is a weaker and true
# claim rather than a stronger and unverifiable one.

CI_DIR = tenancy.dir("media_ci")

# A period must be a year, a quarter or a month. Enforced, not free text, because "Q2" and "2026-Q2"
# would be two different periods for the same three months and every share computed across them would
# quietly be computed across a subset.
_PERIOD = re.compile(r"^(20\d{2})(-(Q[1-4]|(0[1-9]|1[0-2])))?$")

# The three levels the module can operate at, and what each one licenses. This is the honest answer to
# "can we do share of voice?" — the answer is usually "at one grain and not another", and a screen that
# renders this table is telling the truth about the studio's own instrumentation.
LEVELS: dict[str, dict] = {
    "licensed": {
        "label": "Licensed measurement",
        "what": "A paid ad-spend subscription covering the category — TAM AdEx, Nielsen Ad Intel, "
                 "Pathmatics, Vivvix, SimilarWeb and the like.",
        "gives": "Spend by competitor, by medium, by period. Share of voice per medium, and ESOV.",
        "costs": "A real annual subscription. This is the level most agencies buy and most brand teams "
                 "do not.",
    },
    "disclosed": {
        "label": "Published accounts",
        "what": "A listed competitor's own annual report. Indian companies disclose advertising and "
                 "sales promotion expense as a line item, which is a citable spend figure they "
                 "published themselves.",
        "gives": "Share of voice at the annual, all-media grain only — and only against competitors "
                 "who are listed and who disclose it.",
        "costs": "Nothing. The grain is the price: it cannot tell you who outspent you on television "
                 "in the festive quarter, which is usually the question.",
    },
    "free": {
        "label": "Free ad libraries",
        "what": "Meta Ad Library, Google Ads Transparency Center, TikTok's commercial content "
                 "library, LinkedIn's ad library.",
        "gives": "Presence and creative — who is running what, in which format, from when. Genuinely "
                 "valuable, and not spend.",
        "costs": "Nothing. Share of voice is not available at this level and the module will say so "
                 "rather than estimate it. The platforms publish spend only for political and "
                 "social-issue advertising; a commercial campaign shows its creative and its run "
                 "dates, never its budget.",
    },
}

# Where a figure came from, and what it therefore licenses. `spend` is the gate the whole module turns
# on: a source that cannot carry money cannot be used to compute a share.
SOURCE_KINDS: dict[str, dict] = {
    "licensed": {
        "label": "Licensed measurement",
        "spend": True, "grain": "medium",
        "note": "A paid subscription. Name the product and the pull date — two vendors disagree on the "
                "same market and the difference has to be attributable.",
    },
    "entered": {
        "label": "Entered by a person",
        "spend": True, "grain": "medium",
        "note": "Typed from a contract, an invoice, a plan or a licensed report the client holds. "
                "Trusted because a named person is standing behind it, so it needs a source line.",
    },
    "disclosed": {
        "label": "Published accounts",
        "spend": True, "grain": "total_year",
        "note": "The competitor's own annual report. Cite the year and the line item. Annual and "
                "all-media by nature — it cannot be split across media or quarters, and a share built "
                "from it is an annual share of total advertising.",
    },
    "free_public": {
        "label": "Free ad library",
        "spend": False, "grain": "presence",
        "note": "Meta, Google, TikTok, LinkedIn. Establishes that a campaign is running, in what "
                "format and since when. Carries no commercial budget — the spend ranges these "
                "libraries publish cover political and social-issue ads only.",
    },
    "observed": {
        "label": "Seen in market",
        "spend": False, "grain": "presence",
        "note": "Somebody saw the hoarding, the spot, the shelf. The weakest evidence of presence and "
                "still worth recording, because it is often the only evidence for outdoor and trade.",
    },
}

# The free sources, catalogued so the screen can send someone to the right one instead of describing a
# capability the studio does not have. Each entry states its real limit, because every one of these has
# a limit that matters and finding it out after building a plan is expensive.
FREE_SOURCES: tuple[dict, ...] = (
    {"name": "Meta Ad Library", "covers": "Facebook and Instagram, every active ad, any advertiser",
     "url": "https://www.facebook.com/ads/library/",
     "limit": "Spend and impression ranges are published for political and social-issue ads only. A "
              "commercial advertiser's ads show creative, format, platforms and start date."},
    {"name": "Google Ads Transparency Center", "covers": "Search, Display, YouTube — verified advertisers",
     "url": "https://adstransparency.google.com/",
     "limit": "Format and date range per ad. Spend is shown for election advertising only, and the "
              "advertiser must have completed identity verification to appear at all."},
    {"name": "TikTok Commercial Content Library", "covers": "TikTok ads and paid branded content",
     "url": "https://library.tiktok.com/ads",
     "limit": "The full searchable dataset covers ads served in the EU. Creative Center is global but "
              "surfaces top-performing ads rather than one advertiser's complete set."},
    {"name": "LinkedIn Ad Library", "covers": "Ads run from any LinkedIn Page",
     "url": "https://www.linkedin.com/ad-library/",
     "limit": "Creative and run dates. No spend outside political advertising."},
    {"name": "Annual reports and investor presentations",
     "covers": "Listed competitors — advertising and sales promotion expense",
     "url": "",
     "limit": "Annual, all-media, and only for companies that both list and disclose the line "
              "separately. This is the `disclosed` source kind; it is the one free route to a real "
              "spend number."},
)

# What ESOV is associated with, kept in the same shape as `plan.BRAND_SHARE_BASIS` and for the same
# reason: the number travels, and it should not travel without the argument against it.
ESOV_BASIS: dict[str, str] = {
    # `claim` / `source` / `dispute` / `note` — the same four keys as `plan.BRAND_SHARE_BASIS`, so one
    # renderer handles both. The word "associated" stays inside the sentence rather than in the key,
    # because the caveat has to survive being read aloud.
    "claim": "An ESOV of 10 points is associated with roughly 0.5 percentage points of annual "
             "market-share growth.",
    "source": "Binet & Field, The Long and the Short of It (IPA) — drawn from the IPA Databank of "
              "advertising effectiveness cases.",
    "dispute": "Ehrenberg-Bass (Byron Sharp), who hold the underlying awards-entry data unsound as "
               "an evidence base, since cases are self-selected by agencies submitting their wins.",
    "note": "An association observed across a body of cases, not a forecast for this brand. It is "
            "reported here because a positive or negative ESOV is the reason anyone computes it, and "
            "withholding the association while showing the number would be its own kind of dishonest. "
            "It should never be presented as what this plan will deliver.",
}


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _ci_path(brand_slug: str) -> str:
    return os.path.join(CI_DIR, f"{brand_slug}.json")


def ci_load(brand: str) -> dict:
    """The brand's competitive picture, or a fresh empty one. Never None, for the same reason
    `pr.map_load` never is: to a reader, "no picture yet" and "an empty picture" are one state.

    Keyed through `brandprofile.brand_key` so one brand has one document however it was named. Reads
    fall back to the raw slug for pictures written before that existed.
    """
    slug = brandprofile.brand_key(brand)
    for key in brandprofile.brand_keys(brand):
        if os.path.isfile(_ci_path(key)):
            slug = key
            break
    try:
        with open(_ci_path(slug), encoding="utf-8") as fh:
            c = json.load(fh)
        if isinstance(c, dict):
            c["slug"] = slug
            c.setdefault("competitors", [])
            c.setdefault("observations", [])
            c.setdefault("set_complete", {"declared": False, "note": ""})
            return c
    except (OSError, ValueError):
        pass
    return {"brand": brand, "slug": slug, "created": _now(), "updated": _now(),
            "currency": "", "competitors": [], "observations": [],
            "set_complete": {"declared": False, "note": ""}, "som": None}


def ci_save(c: dict) -> dict:
    os.makedirs(CI_DIR, exist_ok=True)
    c["updated"] = _now()
    path = _ci_path(c["slug"])
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(c, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    return c


def add_competitor(c: dict, item: dict) -> tuple[dict | None, str]:
    """Add or update one competitor. Returns (record, error).

    The brand itself is a competitor row carrying `us: True`, rather than being stored separately. Share
    of voice is our spend over everyone's spend including ours, so keeping one shape for all
    participants means the denominator cannot accidentally omit us — which would put our own share above
    100 and look, on a screen, like a good quarter.
    """
    name = str(item.get("name") or "").strip()
    if not name:
        return None, "A competitor needs a name."
    us = bool(item.get("us"))
    cid = str(item.get("id") or "").strip()
    rows = c.setdefault("competitors", [])

    if us:
        other = [r for r in rows if r.get("us") and r.get("id") != cid]
        if other:
            return None, (f"{other[0]['name']} is already marked as this brand. Only one participant "
                          f"can be us — two would double-count the numerator of every share.")
    clash = [r for r in rows if r.get("name", "").strip().lower() == name.lower()
             and r.get("id") != cid]
    if clash:
        return None, (f"{name} is already in the set. Two rows for one company split its spend and "
                      f"understate its share.")

    row = {"id": cid or uuid.uuid4().hex[:8], "name": name, "us": us,
           "note": str(item.get("note") or "").strip(), "added": _now()}
    for i, r in enumerate(rows):
        if r.get("id") == row["id"]:
            row["added"] = r.get("added", row["added"])
            rows[i] = row
            return c, ""
    rows.append(row)
    return c, ""


def drop_competitor(c: dict, cid: str) -> tuple[dict | None, str]:
    """Remove a competitor and every observation against them.

    Leaving the observations would be worse than removing them: they would keep contributing to the
    category total while their owner no longer appears in the set, so the shares would stop summing to
    100 with nothing on screen to explain why.
    """
    rows = c.setdefault("competitors", [])
    hit = [r for r in rows if r.get("id") == cid]
    if not hit:
        return None, "No competitor with that id."
    obs = c.setdefault("observations", [])
    dropped = len([o for o in obs if o.get("competitor") == cid])
    c["competitors"] = [r for r in rows if r.get("id") != cid]
    c["observations"] = [o for o in obs if o.get("competitor") != cid]
    c["last_drop"] = {"name": hit[0].get("name", ""), "observations_removed": dropped}
    return c, ""


def declare_set(c: dict, complete: bool, note: str = "") -> tuple[dict | None, str]:
    """Assert whether the competitor set covers the category, and on what basis.

    This is the difference between "share of the category" and "share of the four companies somebody
    listed", and it cannot be inferred — no amount of data tells you who is missing from it. So it is
    an explicit human claim with a reason attached, and until it is made every share reports itself as a
    share of the listed set.
    """
    note = str(note or "").strip()
    if complete and not note:
        return None, ("Say on what basis the set is complete — a category report, a retail audit, a "
                      "market definition. A completeness claim with no basis behind it turns every "
                      "share into a share of the category, which is a much stronger claim.")
    c["set_complete"] = {"declared": bool(complete), "note": note, "at": _now()}
    return c, ""


def _spend_of(item: dict) -> tuple[float | None, str]:
    """Parse a spend figure. `None` means none was given; `0.0` means a measured zero.

    Those two must not collapse, and a truthiness test collapses them — `0 in (None, "", False)` is
    True in Python, because `0 == False`. That bug made the module refuse the exact remedy its own
    error message recommends: entering a measured zero is how a reader says "this competitor was
    checked and ran nothing here", which is a fact, and it is the only thing that distinguishes an
    absence of activity from an absence of data.
    """
    raw = item.get("spend", None)
    if raw is None or raw is False or (isinstance(raw, str) and not raw.strip()):
        return None, ""
    try:
        v = float(str(raw).replace(",", "").strip())
    except (TypeError, ValueError):
        return None, f"Spend {raw!r} is not a number."
    if v < 0:
        return None, "Spend cannot be negative."
    return v, ""


def add_observation(c: dict, item: dict) -> tuple[dict | None, str]:
    """Record one competitor's activity in one medium in one period. Returns (record, error).

    Every refusal here exists because the alternative is a share that is wrong and looks fine:

    * **A presence-only source cannot carry spend.** This is the spine of the module. An ad library
      proves a campaign is running; it does not disclose its budget, and a number entered against one
      is a guess wearing a citation.
    * **Grain is enforced.** An annual-report figure is annual and all-media. Allowing it against
      `tv` in `2026-Q3` would let one number be spent four times over.
    * **A competitor cannot hold both all-media and per-medium rows in one period**, because the total
      would count them twice — once whole, once in parts.
    * **One currency per record.** A rupee total with a dollar row inside it is off by a factor of
      eighty-odd, and it is the single easiest way to produce a confidently wrong share.
    """
    cid = str(item.get("competitor") or "").strip()
    who = [r for r in c.get("competitors") or [] if r.get("id") == cid]
    if not who:
        return None, "Name a competitor from the set first."

    period = str(item.get("period") or "").strip().upper()
    if not _PERIOD.match(period):
        return None, (f"Period {period!r} must be a year, a quarter or a month — 2026, 2026-Q3 or "
                      f"2026-08. A free-form period splits one span into two and every share computed "
                      f"across it silently covers only part of it.")

    kind = str(item.get("source_kind") or "").strip().lower()
    if kind not in SOURCE_KINDS:
        return None, f"Unknown source kind {kind!r}. One of: {', '.join(SOURCE_KINDS)}."
    spec = SOURCE_KINDS[kind]
    source = str(item.get("source") or "").strip()
    if not source:
        return None, (f"Name the source. {spec['label']} without a citation cannot be checked, and an "
                      f"uncheckable figure is the one thing a share must not be built from.")

    # No `media.migrate` here on purpose — its own docstring says it is for folding old data forward,
    # "never to resolve a live key". Somebody typing an observation today is entering a live key, and a
    # retired name should be corrected out loud rather than silently filed somewhere else.
    medium = str(item.get("medium") or "").strip().lower()
    if medium and medium not in media_mod.LEAVES:
        if medium in media_mod.RETIRED:
            return None, (f"{medium!r} is retired as a medium. {media_mod.RETIRED[medium]} File the "
                          f"observation against where it went, so it lands in the same bucket as "
                          f"everyone else's.")
        return None, f"Unknown medium {medium!r}. One of: {', '.join(media_mod.LEAVES)}."

    spend, err = _spend_of(item)
    if err:
        return None, err

    # The spine: a source that cannot carry money cannot carry money.
    if spend is not None and not spec["spend"]:
        return None, (f"{spec['label']} carries no spend. {spec['note']} Record this as presence and "
                      f"leave the figure out — a share of voice built on it would be a guess with a "
                      f"citation attached, which is worse than no share at all.")
    if spec["spend"] and spend is None:
        return None, (f"{spec['label']} is a spend source — give the figure, or record it under a "
                      f"presence source instead.")

    # Grain. An annual disclosure is annual and all-media, and it must not be filed against a medium.
    if spec["grain"] == "total_year":
        if medium:
            return None, (f"{spec['label']} is all-media by nature — an advertising and sales promotion "
                          f"line does not break down by medium. Leave the medium blank so this counts "
                          f"once, against the total.")
        if len(period) != 4:
            return None, (f"{spec['label']} is annual. Use the year ({period[:4]}), not {period} — the "
                          f"figure covers all four quarters and filing it against one would count it "
                          f"four times.")
    elif not medium:
        return None, (f"Name the medium. {spec['label']} reports by medium, and an unattributed total "
                      f"here cannot be reconciled against the per-medium rows beside it.")

    currency = str(item.get("currency") or c.get("currency") or "").strip().upper()
    if spend is not None:
        if not currency:
            return None, "Give the currency — a share computed across two of them is off by the rate."
        if c.get("currency") and currency != c["currency"]:
            return None, (f"This picture is in {c['currency']}. Convert to it before entering, and say "
                          f"in the source line which rate and date you used — a mixed-currency total is "
                          f"wrong by roughly the exchange rate and looks entirely normal.")

    obs = c.setdefault("observations", [])
    oid = str(item.get("id") or "").strip() or uuid.uuid4().hex[:8]
    mine = [o for o in obs if o.get("competitor") == cid and o.get("period") == period
            and o.get("id") != oid]
    if medium and any(not o.get("medium") for o in mine):
        return None, (f"{who[0]['name']} already has an all-media figure for {period}. Adding a "
                      f"per-medium row on top of it would count the same money twice — once whole and "
                      f"once in parts. Remove the all-media row first.")
    if not medium and any(o.get("medium") for o in mine):
        media_had = sorted({o["medium"] for o in mine if o.get("medium")})
        return None, (f"{who[0]['name']} already has per-medium figures for {period} "
                      f"({', '.join(media_had)}). An all-media total alongside them would double-count. "
                      f"Remove those rows first, or file this against a medium.")

    row = {
        "id": oid, "competitor": cid, "medium": medium, "period": period,
        "spend": spend, "currency": currency if spend is not None else "",
        "running": True if spend is not None else bool(item.get("running", True)),
        "creative": str(item.get("creative") or "").strip(),
        "source": source, "source_kind": kind, "grain": spec["grain"],
        "as_of": str(item.get("as_of") or "").strip()[:10], "entered": _now(),
    }
    if spend is not None and not c.get("currency"):
        c["currency"] = currency
    for i, o in enumerate(obs):
        if o.get("id") == oid:
            obs[i] = row
            return c, ""
    obs.append(row)
    return c, ""


def drop_observation(c: dict, oid: str) -> tuple[dict | None, str]:
    obs = c.setdefault("observations", [])
    if not any(o.get("id") == oid for o in obs):
        return None, "No observation with that id."
    c["observations"] = [o for o in obs if o.get("id") != oid]
    return c, ""


def set_som(c: dict, value, source: str, as_of: str = "", note: str = "") -> tuple[dict | None, str]:
    """The brand's market share, entered with its source. Never computed, never inferred.

    ESOV is share of voice minus share of MARKET, and the second term is a sales fact that lives in a
    retail audit or a sales ledger — not anything this module can see. A market share this system
    derived for itself would make ESOV a number computed from a number it invented.
    """
    try:
        v = float(str(value).replace("%", "").strip())
    except (TypeError, ValueError):
        return None, f"Market share {value!r} is not a number."
    if not 0 <= v <= 100:
        return None, "Market share is a percentage between 0 and 100."
    source = str(source or "").strip()
    if not source:
        return None, ("Name where the market share came from — Nielsen, Kantar, a retail audit, the "
                      "sales ledger. ESOV is share of voice minus this figure, so an unsourced one "
                      "makes the whole comparison unciteable.")
    c["som"] = {"value": v, "source": source, "as_of": str(as_of or "").strip()[:10],
                "note": str(note or "").strip(), "at": _now()}
    return c, ""


# --------------------------------------------------------------------------------------
# Reading it back
# --------------------------------------------------------------------------------------

def periods(c: dict) -> list[str]:
    """Every period with an observation against it, most recent first."""
    return sorted({str(o.get("period") or "") for o in c.get("observations") or [] if o.get("period")},
                  reverse=True)


def level(c: dict) -> dict:
    """Which of the three levels this picture is actually operating at, and what that licenses.

    Reported rather than assumed, because "can we do share of voice?" is the first question anyone asks
    of a competitive screen and the answer depends entirely on what has been entered. A screen that
    renders this is telling the truth about the studio's own instrumentation instead of implying a
    capability behind a disabled button.
    """
    obs = c.get("observations") or []
    grains = {str(o.get("grain") or "") for o in obs}
    if not obs:
        key, why = "empty", "Nothing recorded yet, so there is nothing to compute from."
    elif "medium" in grains:
        key = "licensed"
        why = ("Spend is present at medium grain, so share of voice can be computed per medium and "
               "ESOV can exist. Entered figures count here too — a number from a contract or a client's "
               "own licensed report gives the same grain as a subscription, and needs the same "
               "citation.")
    elif "total_year" in grains:
        key = "disclosed"
        why = ("The only spend is annual and all-media, from published accounts. Share of voice is "
               "computable for the year in total and for no single medium — which cannot answer who "
               "outspent us on television in the festive quarter.")
    else:
        key = "free"
        why = ("Only presence and creative are recorded. This is a real and useful picture of who is "
               "running what; it is not spend, so share of voice is unavailable rather than zero.")
    spec = LEVELS.get(key) or {}
    return {
        "level": key, "label": spec.get("label", "Nothing recorded"), "why": why,
        "gives": spec.get("gives", ""), "levels": LEVELS,
        "spend_rows": sum(1 for o in obs if o.get("spend") is not None),
        "presence_rows": sum(1 for o in obs if o.get("spend") is None),
        "free_sources": FREE_SOURCES,
    }


def _basis(c: dict, n: int) -> tuple[str, bool]:
    """How a share should describe itself: share of the category, or share of the listed set."""
    sc = c.get("set_complete") or {}
    if sc.get("declared"):
        return (f"Share of the category. The set of {n} is declared complete — {sc.get('note', '')}",
                True)
    return (f"Share of the {n} participants listed. The set has NOT been declared complete, so this is "
            f"not a category share — a competitor nobody listed makes every figure here too high.",
            False)


def _share_block(c: dict, parts: list[dict], spend_by: dict, what: str) -> dict:
    """One share table, or a refusal naming exactly who is missing.

    The refusal is the point. A participant with no figure contributes nothing to the denominator and
    inflates every other share, and because the shares still sum to 100 there is nothing on screen to
    show it happened. So a partial set does not produce a partial answer — it produces the list of
    names needed to make it whole.
    """
    missing = [p["name"] for p in parts if spend_by.get(p["id"]) is None]
    if missing:
        return {
            "available": False, "rows": [], "category_spend": None, "our_share": None,
            "missing": missing,
            "why": (f"No figure for {', '.join(missing)} in {what}. A missing participant contributes "
                    f"nothing to the total, which inflates everyone else's share while the shares "
                    f"still add to 100 — so there would be no sign on screen that it happened. If a "
                    f"competitor genuinely ran nothing here, enter a measured zero: that is a fact, "
                    f"and it is different from an absence."),
        }
    total = sum(spend_by[p["id"]] for p in parts)
    if total <= 0:
        return {"available": False, "rows": [], "category_spend": 0.0, "our_share": None,
                "missing": [],
                "why": f"Every measured figure in {what} is zero. There is no voice to take a share of."}
    rows = [{"competitor": p["id"], "name": p["name"], "us": bool(p.get("us")),
             "spend": spend_by[p["id"]], "share": round(spend_by[p["id"]] * 100.0 / total, 1)}
            for p in parts]
    rows.sort(key=lambda r: -r["spend"])
    ours = next((r["share"] for r in rows if r["us"]), None)
    return {"available": True, "rows": rows, "category_spend": total, "our_share": ours,
            "missing": [], "why": ""}


def sov(c: dict, period: str = "") -> dict:
    """Share of voice for one period — in total, and per medium where the grain allows it.

    Two separate questions with two separate answers, which is why they are two blocks. A competitor
    whose only figure is an annual disclosure can be counted in the total and cannot be counted in any
    medium; reporting one number for both would quietly assign their whole year to whichever medium
    happened to be on screen.
    """
    period = str(period or "").strip().upper() or (periods(c)[0] if periods(c) else "")
    parts = list(c.get("competitors") or [])
    us = [p for p in parts if p.get("us")]
    basis, category_claim = _basis(c, len(parts))
    out = {"period": period, "currency": c.get("currency", ""), "basis": basis,
           "category_claim": category_claim, "participants": len(parts),
           "total": {"available": False, "why": "", "rows": [], "missing": []},
           "by_medium": {}, "media_note": ""}

    if not parts:
        out["total"]["why"] = "No competitor set. A share needs somebody to take a share of."
        return out
    if not us:
        out["total"]["why"] = ("Nobody in the set is marked as this brand, so there is no numerator. "
                              "Mark one participant as us.")
        return out
    if not period:
        out["total"]["why"] = "Nothing recorded in any period yet."
        return out

    rows = [o for o in c.get("observations") or [] if o.get("period") == period]

    # The total. A competitor counts once — either their all-media figure or the sum of their per-medium
    # ones. `add_observation` refuses the mix, so this cannot double-count.
    tot: dict[str, float | None] = {}
    for p in parts:
        mine = [o for o in rows if o.get("competitor") == p["id"] and o.get("spend") is not None]
        tot[p["id"]] = sum(float(o["spend"]) for o in mine) if mine else None
    out["total"] = _share_block(c, parts, tot, f"{period} in total")

    # Per medium. Only competitors with per-medium rows can appear, so a set containing one
    # annual-disclosure competitor makes every medium unavailable — correctly, and it says why.
    seen = [m for m in media_mod.LEAVES if any(o.get("medium") == m for o in rows)]
    for m in seen:
        by: dict[str, float | None] = {}
        for p in parts:
            hit = [o for o in rows if o.get("competitor") == p["id"] and o.get("medium") == m
                   and o.get("spend") is not None]
            by[p["id"]] = sum(float(o["spend"]) for o in hit) if hit else None
        blk = _share_block(c, parts, by, f"{media_mod.LEAF_LABEL.get(m, m)} in {period}")
        blk["medium"] = m
        blk["label"] = media_mod.LEAF_LABEL.get(m, m)
        out["by_medium"][m] = blk

    annual_only = [p["name"] for p in parts
                   if any(o.get("competitor") == p["id"] and o.get("grain") == "total_year"
                          for o in rows)]
    if annual_only and seen:
        out["media_note"] = (f"{', '.join(annual_only)} only has an annual all-media figure, so it "
                             f"cannot appear in any per-medium share. That is why the medium tables "
                             f"below may be unavailable while the total is not.")
    return out


def esov(c: dict, period: str = "") -> dict:
    """Excess share of voice — share of voice minus share of market. Both terms, or nothing.

    ESOV is the one number on this screen a plan gets changed by, which is exactly why it is gated
    hardest. Share of market is entered with a source and is never derived here; without it there is no
    ESOV, and a share of voice presented as though it were one would invite a spend decision on a
    comparison that was never made.
    """
    s = sov(c, period)
    som = c.get("som") or None
    tot = s["total"]
    out = {"period": s["period"], "available": False, "sov": tot.get("our_share"),
           "som": (som or {}).get("value"), "esov": None, "basis": ESOV_BASIS,
           "category_claim": s["category_claim"], "why": ""}
    if not tot.get("available"):
        out["why"] = "Share of voice is not available for this period, so neither is ESOV. " + \
                     str(tot.get("why") or "")
        return out
    if not som:
        out["why"] = ("No share of market entered. ESOV is share of voice minus share of market, and "
                      "the second term is a sales fact from a retail audit or the sales ledger — "
                      "nothing this system can see. Enter it with its source.")
        return out
    val = round(float(tot["our_share"]) - float(som["value"]), 1)
    out.update({
        "available": True, "esov": val, "som_source": som.get("source", ""),
        "som_as_of": som.get("as_of", ""),
        "reading": ("Spending a larger share of the category's voice than the share of its market held. "
                    "The published association below is with growth."
                    if val > 0 else
                    "Spending a smaller share of the category's voice than the share of its market "
                    "held. The published association below is with decline." if val < 0 else
                    "Share of voice matches share of market exactly."),
        # Reported as the association it is, with the arithmetic shown so nobody has to trust it, and
        # never as a projection for this brand. `ESOV_BASIS` carries the dispute alongside the source.
        "association_says": round(val / 10.0 * 0.5, 2),
        "association_means": ("What the IPA case body associates with an ESOV of this size, in "
                              "percentage points of annual share change. An association across a "
                              "thousand other campaigns, not a forecast for this one — and disputed. "
                              "Do not put it in a plan as an expected result."),
    })
    if not s["category_claim"]:
        out["caution"] = ("The competitor set is not declared complete, so the share of voice term is a "
                          "share of the listed set. Share of market is a share of the whole category. "
                          "Subtracting one from the other compares two different universes and will "
                          "read high — declare the set before acting on this.")
    return out


def presence(c: dict, period: str = "") -> dict:
    """Who is running what — the deliverable when spend is unavailable, not a consolation prize.

    At the free level this is the entire competitive picture, and it is genuinely useful: it shows the
    creative, the formats and the start dates, which is often a better read on a competitor's intent
    than their budget. It is reported as its own answer rather than as a failed share of voice.
    """
    period = str(period or "").strip().upper() or (periods(c)[0] if periods(c) else "")
    rows = [o for o in c.get("observations") or [] if o.get("period") == period]
    names = {p["id"]: p for p in c.get("competitors") or []}
    grid = []
    for p in c.get("competitors") or []:
        mine = [o for o in rows if o.get("competitor") == p["id"]]
        grid.append({
            "competitor": p["id"], "name": p["name"], "us": bool(p.get("us")),
            "media": [{"medium": o.get("medium", ""),
                       "label": media_mod.LEAF_LABEL.get(o.get("medium", ""), "all media"),
                       "running": bool(o.get("running")), "creative": o.get("creative", ""),
                       "source": o.get("source", ""), "source_kind": o.get("source_kind", ""),
                       "has_spend": o.get("spend") is not None,
                       "as_of": o.get("as_of", "")} for o in mine],
            "media_count": len({o.get("medium") for o in mine if o.get("medium")}),
            "silent": not mine,
        })
    return {"period": period, "rows": grid, "periods": periods(c),
            "unseen": [g["name"] for g in grid if g["silent"]],
            "known": len(names),
            "note": ("A competitor with nothing recorded is one nobody has looked for, not one who is "
                     "quiet. The two are indistinguishable here and should not be read as the same "
                     "thing.")}


def ci_findings(c: dict, period: str = "") -> list[dict]:
    """What is missing before the competitive picture can carry a spend decision."""
    out: list[dict] = []
    parts = list(c.get("competitors") or [])
    obs = list(c.get("observations") or [])
    lv = level(c)

    if not parts:
        out.append({"layer": "competitive", "level": "gap", "blocking": True,
                    "what": "No competitor set",
                    "why": "Share of voice is this brand's spend over the category's. With nobody in "
                           "the set there is no denominator and nothing here can be computed."})
    elif not any(p.get("us") for p in parts):
        out.append({"layer": "competitive", "level": "gap", "blocking": True,
                    "what": "This brand is not in its own set",
                    "why": "One participant has to be marked as us, or there is no numerator. Kept as "
                           "a row like any other so the denominator cannot omit us — which would put "
                           "our share above 100 and read on screen as a good quarter."})
    elif len(parts) < 3:
        out.append({"layer": "competitive", "level": "risk", "blocking": False,
                    "what": f"Only {len(parts)} participant(s) in the set",
                    "why": "Few categories are two-horse races. A short set does not make the shares "
                           "wrong, it makes them shares of a universe smaller than the market."})

    if not obs:
        out.append({"layer": "competitive", "level": "gap", "blocking": True,
                    "what": "Nothing observed yet",
                    "why": "The set says who to watch. Until there are observations against it there "
                           "is nothing to compare."})
    if not (c.get("set_complete") or {}).get("declared") and parts:
        out.append({"layer": "competitive", "level": "risk", "blocking": False,
                    "what": "The set is not declared complete",
                    "why": "Until somebody says on what basis this covers the category, every share "
                           "here is a share of the listed set. That is the weaker and true claim, and "
                           "it is what will be reported — but ESOV against a category share of market "
                           "compares two different universes."})
    if not c.get("som"):
        out.append({"layer": "competitive", "level": "risk", "blocking": False,
                    "what": "No share of market entered",
                    "why": "ESOV needs it, and it cannot be derived here — it is a sales fact from a "
                           "retail audit or the ledger. Without it there is a share of voice and "
                           "nothing to judge it against."})
    if lv["level"] == "free" and obs:
        out.append({"layer": "competitive", "level": "note", "blocking": False,
                    "what": "Presence only — share of voice unavailable",
                    "why": lv["why"] + " This is a state to report, not a gap to fill with an "
                                       "estimate. The free libraries are listed on this screen."})
    if lv["level"] == "disclosed":
        out.append({"layer": "competitive", "level": "note", "blocking": False,
                    "what": "Annual grain only",
                    "why": lv["why"]})

    undated = [o for o in obs if not o.get("as_of")]
    if undated:
        out.append({"layer": "competitive", "level": "risk", "blocking": False,
                    "what": f"{len(undated)} observation(s) carry no as-of date",
                    "why": "Competitive data ages fast and two vendors disagree about the same market. "
                           "Without a pull date a figure cannot be reconciled against anything or "
                           "retired when it goes stale."})

    order = {"gap": 0, "risk": 1, "note": 2}
    out.sort(key=lambda f: (not f["blocking"], order.get(f["level"], 3)))
    return out


def ci_view(c: dict, period: str = "") -> dict:
    """The whole competitive screen. One payload, so nothing on it disagrees with anything else."""
    period = str(period or "").strip().upper() or (periods(c)[0] if periods(c) else "")
    fs = ci_findings(c, period)
    # Observations store `competitor` as an id, because a stored name goes stale the moment one is
    # renamed. The NAME is resolved HERE rather than left for the client to join: every other payload
    # in this codebase resolves its own labels — `state_label`, `kind_label`, `phase_label` — and a
    # screen forced to join an id to a name will eventually render the id. Design's round-31 return
    # reached for `competitor_name` defensively and got raw hex, which is the right instinct meeting a
    # gap on this side.
    _names = {x.get("id"): x.get("name", "") for x in (c.get("competitors") or [])}
    _obs = [{**o, "competitor_name": _names.get(o.get("competitor"), ""),
             "source_kind_label": (SOURCE_KINDS.get(o.get("source_kind")) or {}).get("label", "")}
            for o in (c.get("observations") or [])]
    return {
        "brand": c.get("brand", ""), "slug": c.get("slug", ""),
        "currency": c.get("currency", ""),
        "competitors": list(c.get("competitors") or []),
        "observations": _obs,
        "set_complete": c.get("set_complete") or {"declared": False, "note": ""},
        "som": c.get("som"),
        # OFFERED, not applied. The brand profile may already hold a sourced share of market, and
        # retyping it per campaign is how two campaigns end up disagreeing about the same brand. But
        # inheriting it silently would put a figure on this picture that nobody chose here — so the
        # screen gets the offer and a person accepts it.
        "som_from_brand": (brandprofile.market_share_of(c.get("brand") or "")
                           if not c.get("som") else {"available": False, "why": "already set here"}),
        "period": period, "periods": periods(c),
        "level": level(c),
        "sov": sov(c, period),
        "esov": esov(c, period),
        "presence": presence(c, period),
        "media": [{"key": m, "label": media_mod.LEAF_LABEL.get(m, m)} for m in media_mod.LEAVES],
        "source_kinds": SOURCE_KINDS,
        "findings": fs,
        "blocking": [f["what"] for f in fs if f["blocking"]],
        "why_before_the_split": ("The brand/activation split and the channel weights are set against "
                                "the category, not in a vacuum. Share of voice is the only thing that "
                                "says whether a weight is heavy — so this screen comes before them, "
                                "and it is allowed to answer 'not computable' rather than guess."),
    }
