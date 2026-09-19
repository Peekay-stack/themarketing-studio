"""shelf.py — the seven inputs, as one read surface.

An input is something you went and found out. A decision is something you argued for. The product has
been treating the two as the same kind of work, and it shows: *"500 dairy professionals check the milk
every single day"* is a fact somebody established, and it arrives on screen as one option among five
rephrasings of itself, each carrying its own source flag, waiting to be chosen.

That is why the house feels long. Six of its nine layers ask you to *decide* something; the rest are
inventory wearing a decision's clothes.

So this module gathers what the flow draws FROM, separately from what the flow decides:

    1. brief        the proposition, the audience, the objective, and the shift
    2. evidence     every provable fact, with its source — the one home of the sourced/unsourced flag
    3. codes        palette, idiom, occasion, ritual, iconography, and the avoid list
    4. assets       pack, logo, film, past work — signed off or not
    5. landscape    competitors, what is parity, what is available to own
    6. footprint    the trade and channel reality this brand actually has
    7. trade_econ   margin, velocity, and what unbranded competition costs the shopkeeper

**This is a read surface and nothing else.** It stores nothing, owns no files and creates no new state.
Every function here reads what `briefstore`, `library`, `brandprofile` and `strategy` already hold. That
is deliberate: a phase that adds a store is a phase that has to be migrated back out if the shape turns
out wrong, and this one is meant to be free to abandon.

Two of the seven are honestly empty today. `landscape` and `footprint` live inside brief prose rather
than as fields, and `trade_econ` does not exist anywhere — which is exactly why the sales enabler
currently asserts a trade argument with nothing behind it. They return `available: False` and say what
would fill them, rather than returning a plausible-looking blank.
"""
from __future__ import annotations

import brandprofile
import library
import strategy

# What the shelf holds, in the order the flow reaches for it. `available` is computed per brand; this is
# only the vocabulary and the reason each one exists.
INPUTS: dict[str, dict] = {
    "brief": {
        "label": "The brief",
        "what": "The proposition, the audience, the objective, and the shift from current behaviour "
                "and attitude to desired.",
        "feeds": "The campaign's tension is drawn from the shift rather than written fresh.",
        "source": "briefstore",
    },
    "evidence": {
        "label": "Evidence",
        "what": "Every provable fact, with its source attached.",
        "feeds": "The claim points at these. A claim that cannot point at one is an assertion.",
        "source": "the house's RTB layers, plus the library's locked copy",
    },
    "codes": {
        "label": "Codes & culture",
        "what": "Palette, idiom, occasion, ritual, iconography — and the avoid list.",
        "feeds": "Every execution. The avoid list is the single most operationally useful line in "
                 "the house.",
        "source": "the house's culture layer, plus the brand profile",
    },
    "assets": {
        "label": "Assets",
        "what": "Pack, logo, past film, previous work. Signed off, or not.",
        "feeds": "The library gate. A master key visual cannot be made without a signed-off pack.",
        "source": "library",
    },
    "landscape": {
        "label": "Landscape",
        "what": "Competitors, what is parity in this category, what is genuinely available to own.",
        "feeds": "The claim's gate — cover the logo and read it again.",
        "source": "the brief's competitive section",
    },
    "footprint": {
        "label": "Footprint",
        "what": "The trade and channel reality this brand actually has.",
        "feeds": "Which media get a row at all. A brand with no modern-trade listing should never be "
                 "shown a gondola header.",
        "source": "not yet a field — lives in brief prose",
    },
    "trade_econ": {
        "label": "Trade economics",
        "what": "Margin, reorder velocity, and what unbranded competition costs the shopkeeper.",
        "feeds": "The trade row, which sits off the consumer ladder and needs the retailer's "
                 "arithmetic instead of the consumer's proposition.",
        "source": "does not exist yet",
    },
}


def _house_layer(house: dict | None, layer_id: str) -> list[str]:
    """Chosen text on one house layer, or []. One read path, so a missing house is not an error."""
    if not house:
        return []
    try:
        return strategy._chosen_text(house, layer_id) or []
    except Exception:
        # A house written before this layer existed is an ordinary state of affairs, not a failure.
        return []


def brief(b: dict | None) -> dict:
    """The brief, as the shelf presents it."""
    if not b:
        return {"available": False, "why": "No brief pulled. The campaign's tension comes from the "
                                           "shift, so without one it has to be written by hand."}
    shift = b.get("cb_ca_db_da") or {}
    return {
        "available": True,
        "proposition": str(b.get("proposition") or "").strip(),
        "audience": str(b.get("audience") or "").strip(),
        "objective": str(b.get("commObjective") or b.get("businessObjective") or "").strip(),
        "shift": {
            "from": str(shift.get("shift_from") or "").strip(),
            "to": str(shift.get("shift_to") or "").strip(),
            "line": str(shift.get("shift_line") or shift.get("caption") or "").strip(),
        } if shift else None,
        "id": b.get("id", ""),
    }


def evidence(house: dict | None = None, brand: str = "") -> dict:
    """Every provable fact the brand has, each with where it came from.

    **The one home of the sourced flag.** Today the same 500-checks fact carries a source marker in five
    places — on the functional message, on the functional RTB, on the proof proposition, on the medium
    lines that quote it and on the platform that dramatises it. One fact, one flag: everything else
    points here. `brand` — see library.py's brand-scoping note: without it, this reports another
    brand's locked claims as if they were this shelf's own provable facts.
    """
    facts = []
    for layer in ("rtb_functional", "rtb_emotional"):
        for text in _house_layer(house, layer):
            facts.append({"text": text, "from": f"house · {layer}", "provable": True})
    for row in library.locked_copy(brand=brand):
        facts.append({"text": row["text"], "from": f"library · {row.get('name') or 'locked copy'}",
                      "provable": True})
    return {
        "available": bool(facts),
        "facts": facts,
        "count": len(facts),
        "why": "" if facts else "Nothing provable on file. A claim with no evidence behind it is an "
                                "assertion, and the house will say so.",
    }


def codes(house: dict | None = None, profile: dict | None = None) -> dict:
    """Palette, idiom, ritual, iconography, and what to avoid."""
    prof = profile or brandprofile.resolve() or {}
    culture = _house_layer(house, "culture")
    # The avoid line is pulled out rather than left in the list. It is the one code that says what NOT
    # to do, which makes it the most useful and the easiest to lose in a list of six.
    avoid = [c for c in culture if c.lower().startswith("avoid")]
    return {
        "available": bool(culture or prof),
        "culture": [c for c in culture if c not in avoid],
        "avoid": avoid,
        "palette": prof.get("colours") or {},
        "hashtags": prof.get("hashtags") or [],
        "brand": str(prof.get("name") or prof.get("brand") or "").strip(),
        "why": "" if culture else "No culture layer decided. Executions will invent their own codes, "
                                  "which is how eleven pieces end up looking like eleven brands.",
    }


def assets(brand: str = "") -> dict:
    """The library, and what it is missing. Read straight through — the library owns its own truth."""
    s = library.summary()
    return {
        "available": s["signed"] > 0,
        "signed": s["signed"], "total": s["total"], "unsigned": s["unsigned"],
        "missing": s["missing"],
        "pack": library.reference_url("pack", brand=brand),
        "logo": library.reference_url("logo", brand=brand),
        "why": "" if s["signed"] else "Nothing signed off. A signature is a decision, not an upload — "
                                      "until one exists, nothing here counts as ground truth.",
    }


def landscape(b: dict | None = None) -> dict:
    """Competitors and what is parity. Not a field yet, so this reports honestly rather than guessing."""
    text = str((b or {}).get("competition") or "").strip()
    return {
        "available": bool(text),
        "text": text,
        "why": "" if text else "Competitive context lives in brief prose rather than as a field, so "
                               "the claim's ownability gate has nothing structured to read. Filling "
                               "this is what lets 'cover the logo' be checked rather than asked.",
    }


def footprint(b: dict | None = None) -> dict:
    """The trade and channel reality. Also not a field yet."""
    text = str((b or {}).get("deliverables") or (b or {}).get("channelMix") or "").strip()
    return {
        "available": bool(text),
        "text": text,
        "why": "" if text else "No stated trade footprint, so every medium gets a row whether or not "
                               "this brand has that channel at all.",
    }


def trade_econ() -> dict:
    """Margin and velocity. The seventh input, and the one that genuinely does not exist yet."""
    return {
        "available": False,
        "why": "Not modelled anywhere. This is why the trade expression asserts an argument about what "
               "the shopkeeper earns with nothing behind it: margin, case size, reorder cycle and "
               "facings are arithmetic, and none of the numbers are on file.",
        "wants": ["MRP and trade margin", "case size and reorder cycle", "facings per bay",
                  "what the loose or unbranded alternative earns him"],
    }


def status(house: dict | None = None, b: dict | None = None,
           profile: dict | None = None) -> dict:
    """The whole shelf, and how much of it is actually filled.

    `filled` is reported as a fraction rather than a pass mark on purpose. A shelf is never finished —
    evidence accumulates, codes get added — and a green tick would imply otherwise.
    """
    _brand = str((profile or {}).get("name") or "")
    got = {
        "brief": brief(b),
        "evidence": evidence(house, brand=_brand),
        "codes": codes(house, profile),
        "assets": assets(brand=_brand),
        "landscape": landscape(b),
        "footprint": footprint(b),
        "trade_econ": trade_econ(),
    }
    filled = [k for k, v in got.items() if v.get("available")]
    return {
        "inputs": {k: {**INPUTS[k], **got[k]} for k in INPUTS},
        "filled": len(filled), "of": len(INPUTS),
        "empty": [k for k in INPUTS if k not in filled],
        "summary": (f"{len(filled)} of {len(INPUTS)} inputs on the shelf."
                    + (f" Missing: {', '.join(INPUTS[k]['label'] for k in INPUTS if k not in filled)}."
                       if len(filled) < len(INPUTS) else "")),
    }
