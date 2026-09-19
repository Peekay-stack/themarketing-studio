"""posm.py — point-of-sale material as a layer stack, not a photograph.

This module replaces `keyline.py` and the reserved-band vocabulary that went with it. The old
architecture assumed a POS piece is a photograph with words placed on top: the image model was asked to
hold a third of the frame open, and a translucent slab was drawn over it with real type. That produced
two failure renders, both kept in `posm_skill/references/exhibits/`, and the reason they failed is not
that the prompt was badly worded. It is that the thing being built was the wrong thing.

    Indian FMCG point-of-sale is flat-colour graphic design with cut-out photographic elements
    placed on it — a nine-layer stack. It is NOT a photograph with words on top.

Nine of the thirteen real exhibits are built exactly that way. Two consequences run through everything
below:

**You do not generate a poster. You generate assets and then lay them out.** An image model's job here is
one subject isolated on plain white, ready to cut out — a far easier job than a finished composition, and
what a studio actually does: shoot on white, mask, place. `cutout_prompt()` is the only prompt this module
builds, and it deliberately produces an asset rather than a piece.

**"Reserve empty space for the type" is a problem that should not exist.** You only need to hold space
open inside a photograph if that photograph has to be the whole poster. On a flat colour field the field
*is* the space. That is why `_KV_SPACE` and `keyline.draw_line` are gone rather than fixed — the
translucent slab was their correct output, given a wrong premise.

Almost everything here is a table or a calculation, not a prompt. Reading distance sets cap height and
word count; the printed millimetres set the aspect delta, which sets how the layers re-flow; the substrate
sets bleed. None of that is a judgement an image model should be making, and none of it was reachable
while the numbers lived in a prompt.
"""
from __future__ import annotations

import os

import jsonout
import library

_HERE = os.path.dirname(__file__)
_SKILL = os.path.join(_HERE, "posm_skill")

# The framework references the model needs in order to reason about a layer stack. `formats.md` is
# deliberately NOT loaded: its table is the `FORMATS` dict below, and shipping both invites the two
# copies to disagree — which is the same defect the spine's `stands_on` exists to prevent.
_REFS = ("key-visual.md", "failures.md", "adaptation.md", "exhibits.md")


# --- the stack ----------------------------------------------------------------------------------
#
# Bottom to top. Not every piece carries every layer, but the order never changes — that fixed order is
# what lets `drop-out` be a rule rather than eleven separate taste decisions.
LAYERS = (
    {"id": "field", "n": 1, "label": "Field",
     "what": "Flat brand colour, or two colours split by a straight, diagonal or curved edge, or a "
             "brand pattern. Never a photograph.",
     "drop": "never — it is the piece"},
    {"id": "field_graphics", "n": 2, "label": "Field graphics",
     "what": "Optional and low contrast, brand-owned: streaks, waves, doodles, splats, bokeh.",
     "drop": "second to go"},
    {"id": "hero", "n": 3, "label": "Hero cut-out",
     "what": "The subject, masked out of its background, hard-edged, with a soft drop shadow to seat "
             "it on the field.",
     "drop": "fourth to go"},
    {"id": "pack", "n": 4, "label": "Pack cut-out",
     "what": "The real pack, masked, with a shadow or reflection. From the library, never generated.",
     "drop": "never, except where the piece is not about a product (arch, fascia)"},
    {"id": "type", "n": 5, "label": "Type blocks",
     "what": "Headline in a weight hierarchy, plus support lines. Real editable type, set in the "
             "design tool.",
     "drop": "only at product-only sizes"},
    {"id": "devices", "n": 6, "label": "Devices",
     "what": "Badges, roundels, NEW flashes, highlight boxes, underline rules — what makes type read "
             "as POS rather than as a caption.",
     "drop": "first to go"},
    {"id": "brand_block", "n": 7, "label": "Brand block",
     "what": "Logo lock-up as vector artwork, cornered.",
     "drop": "never, on anything, ever"},
    {"id": "base_band", "n": 8, "label": "Base band",
     "what": "Flat strip carrying the tagline, the footnote strip, and a care or contact box.",
     "drop": "with the support items"},
    {"id": "mandatories", "n": 9, "label": "Mandatories",
     "what": "Veg mark, FSSAI, licence number. Smallest, usually inside the base band.",
     "drop": "never on print; only on environmental where it does not apply"},
)

LAYER_IDS = tuple(l["id"] for l in LAYERS)

# The two constructions. The layered graphic build is the default; the photographic build is the
# exception and has to be argued for, because "it looks better" is how you end up with a stock photo and
# a caption.
BUILDS = {
    "layered": {
        "label": "Layered graphic build",
        "what": "Flat field, cut-out hero, cut-out pack, type in devices. The default.",
        "why": "Cheaper, adapts across formats trivially, survives bad printing, and it is what the "
               "category actually looks like.",
        "exhibits": ["dabur-honey-stay-fit", "nivea-men-derma-control", "nivea-creme-soft-milk",
                     "pantene-sonakshi-broken-cycle", "motherdairy-dosti-range",
                     "nandini-kmf-dealer-board"],
    },
    "photographic": {
        "label": "Photographic build",
        "what": "A real photographic scene occupying most of the frame, with a hard split into a flat "
                "zone that carries the type. The photograph is never asked to host type.",
        "why": "Only correct when the scene itself is the argument: a demonstration whose mechanism has "
               "to be visible, a metaphor built as a real object, or an occasion whose point is the "
               "moment. Say why the scene is the argument.",
        "exhibits": ["surf-excel-matic-smart-shots", "dabur-honey-heart-health",
                     "surf-excel-holi-daag-acche-hain", "motherdairy-haldi-milk"],
    },
}

# The master is rendered at 3:4 and every format re-flows from it.
#
# Not a taste call: `gemini.image()` clamps aspect to 1:1 | 16:9 | 9:16 | 4:3 | 3:4 and silently falls
# back to 1:1 for anything else, so a 4:5 request comes back square. A master that is quietly the wrong
# shape is worse than one that is the wrong shape loudly.
MASTER_RATIO = "3:4"
RENDER_RATIOS = ("1:1", "16:9", "9:16", "4:3", "3:4")


def render_ratio(ratio: str) -> str:
    """The nearest aspect the image API will actually honour.

    Print ratios are 12:1, 5:7, 8:3 and so on; the model accepts five. Clamping here, out loud, is the
    difference between a known approximation and a square nobody ordered.
    """
    want = ratio_num(ratio)
    if not want:
        return MASTER_RATIO
    return min(RENDER_RATIOS, key=lambda r: abs((ratio_num(r) or 1.0) - want))


def ratio_num(ratio: str) -> float:
    """`"12:1"` -> 12.0. Width over height. 0.0 when it cannot be read."""
    try:
        w, h = str(ratio).replace("/", ":").split(":")[:2]
        return float(w) / float(h) if float(h) else 0.0
    except (TypeError, ValueError):
        return 0.0


# --- the formats --------------------------------------------------------------------------------
#
# Real millimetres and real reading distances, from `posm_skill/references/formats.md`. These are
# sensible Indian retail defaults and a vendor's spec sheet or a measured bay always wins — which is why
# every sheet this module produces marks its dimensions `[assumed]` until someone says otherwise.
#
# The table this replaces had six entries and two of them were wrong: `shelf-strip` was recorded as 16:9
# when the real piece is about 12:1, and `poster-a3` as 3:4 when A3 is 5:7. Both errors are the kind that
# survive review, because a ratio looks like a detail until a piece is set to it.
#
#   mm       (width, height) of the printed piece, or None where it must be measured
#   ratio    the print ratio as it is written on a spec sheet
#   read_at  metres, and it drives cap height, word count and how much survives at all
#   sides    2 means the piece is seen from behind as well; a blank side B is a broken piece
#   tier     where it lands on the drop-out ladder
#   clear    what physically stands in front of the artwork; nothing that must be read goes there
FORMATS: dict[str, dict] = {
    # --- flat print ---
    "poster-a4": {
        "family": "flat", "label": "Poster A4", "mm": (210, 297), "ratio": "5:7", "read_at": 1.5,
        "sides": 1, "substrate": "130gsm art paper", "tier": "reduced", "clear": "",
        "trap": "Read close, so it gets over-filled. It is still a poster, not a leaflet."},
    "poster-a3": {
        "family": "flat", "label": "Poster A3", "mm": (297, 420), "ratio": "5:7", "read_at": 2.5,
        "sides": 1, "substrate": "130gsm art paper", "tier": "full",
        "clear": "outer 10% top and bottom",
        "trap": "The default everyone orders. Gets pasted at whatever height there is space, so the top "
                "and bottom 10% are unreliable."},
    "poster-a2": {
        "family": "flat", "label": "Poster A2", "mm": (420, 594), "ratio": "5:7", "read_at": 3.5,
        "sides": 1, "substrate": "170gsm art paper", "tier": "full", "clear": "",
        "trap": "Big enough that a soft master shows."},
    "dangler": {
        "family": "flat", "label": "Dangler", "mm": (200, 250), "ratio": "4:5", "read_at": 1.5,
        "sides": 2, "substrate": "300gsm board, matt lamination", "tier": "reduced", "clear": "",
        "trap": "It spins. A blank back means half of all encounters are with a white rectangle."},
    "dangler-round": {
        "family": "flat", "label": "Round dangler", "mm": (200, 200), "ratio": "1:1", "read_at": 1.5,
        "sides": 2, "substrate": "300gsm board, die-cut", "tier": "reduced", "clear": "",
        "trap": "Circular crop — anything in the corners of the master is gone."},
    "shelf-strip": {
        "family": "flat", "label": "Shelf strip / talker", "mm": (900, 75), "ratio": "12:1",
        "read_at": 0.4, "sides": 1, "substrate": "250gsm, adhesive back", "tier": "minimal", "clear": "",
        "trap": "Extreme letterbox. No hero survives a crop; this is a re-flow of the layers, never a "
                "crop of the artwork. Three or four words maximum."},
    "shelf-strip-short": {
        "family": "flat", "label": "Short shelf strip", "mm": (600, 70), "ratio": "8.5:1",
        "read_at": 0.4, "sides": 1, "substrate": "250gsm, adhesive back", "tier": "minimal", "clear": "",
        "trap": "As the long strip, but fits a single bay rather than a run."},
    "wobbler": {
        "family": "flat", "label": "Wobbler", "mm": (100, 100), "ratio": "1:1", "read_at": 1.0,
        "sides": 1, "substrate": "300gsm board + plastic spring", "tier": "mark-only", "clear": "",
        "trap": "Tiny. Type has to be larger than looks sane. Usually pack and brand block only."},
    "backing-sheet": {
        "family": "flat", "label": "Backing sheet", "mm": (900, 450), "ratio": "2:1", "read_at": 0.6,
        "sides": 1, "substrate": "170gsm, or vinyl on board", "tier": "minimal",
        "clear": "lower half — product stands in front of it",
        "trap": "Product stands in front of the lower half. Everything that must be read goes in the "
                "top half."},
    "gondola-header": {
        "family": "flat", "label": "Gondola / aisle header", "mm": (1200, 300), "ratio": "4:1",
        "read_at": 4.0, "sides": 1, "substrate": "3mm sunboard or ACP", "tier": "minimal", "clear": "",
        "trap": "Read across an aisle. Silhouette and one short line only."},
    "dealer-board": {
        "family": "flat", "label": "Dealer board (4×2 ft)", "mm": (1220, 610), "ratio": "2:1",
        "read_at": 6.0, "sides": 1, "substrate": "ACP or 3mm flex", "tier": "full",
        "clear": "the retailer band",
        "retailer_field": "30–40% of the board: shop name, address, phone, GSTIN",
        "trap": "Co-branded. Needs a variable field for the retailer's details, typically 30–40% of the "
                "board."},
    "dealer-board-large": {
        "family": "flat", "label": "Large dealer board (8×3 ft)", "mm": (2440, 915), "ratio": "8:3",
        "read_at": 10.0, "sides": 1, "substrate": "flex on frame, or ACP", "tier": "minimal",
        "clear": "the retailer band",
        "retailer_field": "30–40% of the board: shop name, address, phone, GSTIN",
        "trap": "Co-branded, and at 10m the brand mark plus one line is the whole content."},
    "standee": {
        "family": "flat", "label": "Roll-up standee", "mm": (600, 1800), "ratio": "1:3", "read_at": 4.0,
        "sides": 1, "substrate": "vinyl on roll-up cassette", "tier": "full",
        "clear": "bottom 200mm (cassette) and top 100mm (it curls)",
        "trap": "The bottom 200mm sits in the cassette and the top curls. Nothing important in either."},
    "tent-card": {
        "family": "flat", "label": "Tent card", "mm": (100, 150), "ratio": "2:3", "read_at": 0.5,
        "sides": 2, "substrate": "300gsm board, creased", "tier": "reduced", "clear": "",
        "trap": "Counter-top and handled. Both faces are seen and they may differ — offer on one, brand "
                "on the other."},
    "bunting": {
        "family": "flat", "label": "Bunting flag", "mm": (200, 280), "ratio": "5:7", "read_at": 3.0,
        "sides": 2, "substrate": "250gsm board, strung", "tier": "minimal", "clear": "",
        "trap": "Repeats along a string, so it is a pattern before it is a message. Brand mark and one "
                "word."},
    "tin-plate": {
        "family": "flat", "label": "Tin plate / sign board", "mm": (300, 450), "ratio": "2:3",
        "read_at": 3.0, "sides": 1, "substrate": "powder-coated tin", "tier": "minimal", "clear": "",
        "trap": "Stays up for years — no dated offer, no seasonal line. Limited colour reproduction."},

    # --- environmental: a key visual applied to an object, not cropped into a rectangle ---
    "chiller-door": {
        "family": "environmental", "label": "Chiller door decal", "mm": (600, 1400), "ratio": "3:7",
        "read_at": 2.0, "sides": 1, "substrate": "self-adhesive vinyl, die-cut", "tier": "reduced",
        "clear": "the handle, the hinge, and a viewing window onto the stock",
        "trap": "The door is glass and product is visible behind it. Either the decal frames a clear "
                "window or the shopper cannot see stock — which retailers refuse."},
    "chiller-side": {
        "family": "environmental", "label": "Chiller side panel", "mm": (600, 1400), "ratio": "3:7",
        "read_at": 3.0, "sides": 1, "substrate": "self-adhesive vinyl", "tier": "full", "clear": "",
        "trap": "Opaque, so this is the one that can carry the full visual. Often against a wall — check "
                "which side is visible before printing both."},
    "chiller-canopy": {
        "family": "environmental", "label": "Chiller header / canopy", "mm": (900, 300), "ratio": "3:1",
        "read_at": 3.0, "sides": 1, "substrate": "3mm sunboard or ACP", "tier": "minimal", "clear": "",
        "trap": "Above the unit, read across the shop. Brand block and one line."},
    "shelf-branding": {
        "family": "environmental", "label": "Shelf / rack branding", "mm": None, "ratio": "",
        "read_at": 0.6, "sides": 1, "substrate": "adhesive vinyl or printed strip", "tier": "minimal",
        "clear": "",
        "trap": "Must be measured, never assumed — bay widths differ by chain and by store. Ask for the "
                "bay dimension and the number of shelves."},
    "stall-backdrop": {
        "family": "environmental", "label": "Activation stall backdrop", "mm": (3000, 2400),
        "ratio": "5:4", "read_at": 5.0, "sides": 1, "substrate": "flex on frame", "tier": "full",
        "clear": "lower third — promoters and shoppers stand there",
        "trap": "People stand in front of the lower third. Line and brand block go in the upper half or "
                "they are behind a promoter all day."},
    "stall-fascia": {
        "family": "environmental", "label": "Stall fascia / canopy", "mm": (3000, 600), "ratio": "5:1",
        "read_at": 8.0, "sides": 1, "substrate": "flex on frame", "tier": "minimal", "clear": "",
        "trap": "Brand name and the line. Nothing else reads at 8m."},
    "stall-table": {
        "family": "environmental", "label": "Table skirt", "mm": (1800, 750), "ratio": "12:5",
        "read_at": 2.0, "sides": 1, "substrate": "printed fabric", "tier": "minimal",
        "clear": "lower two-thirds — legs, stock and crowd cross it",
        "trap": "Treat as a pattern with a centred lock-up, not a layout."},
    "stall-standee": {
        "family": "environmental", "label": "Stall standee", "mm": (850, 2000), "ratio": "2:5",
        "read_at": 4.0, "sides": 1, "substrate": "vinyl on roll-up cassette", "tier": "full",
        "clear": "bottom 200mm (cassette)",
        "trap": "Flanks the stall. Can carry the mechanic or the offer, since a person is standing there "
                "to explain it."},
    "entry-arch": {
        "family": "environmental", "label": "Entry arch / gate", "mm": (4000, 3000), "ratio": "4:3",
        "read_at": 15.0, "sides": 2, "substrate": "flex on frame", "tier": "mark-only", "clear": "",
        "trap": "People walk under it and look back, so both sides carry artwork. Silhouette only."},

    # --- out-of-home ---
    "hoarding": {
        "family": "ooh", "label": "Hoarding (20×10 ft)", "mm": (6096, 3048), "ratio": "2:1",
        "read_at": 30.0, "sides": 1, "substrate": "flex on frame", "tier": "minimal", "clear": "",
        "trap": "Three-second read. Seven words maximum. The pack must work as a colour block, not as a "
                "label."},
    "bus-shelter": {
        "family": "ooh", "label": "Bus shelter panel", "mm": (1200, 1800), "ratio": "2:3",
        "read_at": 3.0, "sides": 1, "substrate": "backlit vinyl", "tier": "full", "clear": "",
        "trap": "The one OOH format with dwell time — people wait there. It can carry a claim, a "
                "footnote, even a mechanic."},
    "unipole": {
        "family": "ooh", "label": "Unipole (40×20 ft)", "mm": (12192, 6096), "ratio": "2:1",
        "read_at": 80.0, "sides": 1, "substrate": "flex on frame", "tier": "mark-only", "clear": "",
        "trap": "Silhouette and brand mark. A line is optional and usually wasted."},
    "auto-back": {
        "family": "ooh", "label": "Auto-rickshaw back panel", "mm": (900, 600), "ratio": "3:2",
        "read_at": 5.0, "sides": 1, "substrate": "vinyl on board", "tier": "reduced",
        "clear": "lower quarter — road dirt and the bumper",
        "trap": "Moves, gets dirty, sits low in traffic. High contrast, no fine detail."},
    "wall-paint": {
        "family": "ooh", "label": "Wall painting", "mm": None, "ratio": "2:1", "read_at": 20.0,
        "sides": 1, "substrate": "hand-painted, flat spot colours", "tier": "minimal", "clear": "",
        "reflow_band": "violent",
        "trap": "Hand-painted: flat spot colours only, no photograph, no gradient, no soft shadow. The "
                "pack becomes a simplified drawing."},
}

FAMILIES = {
    "flat": "Flat print — cropped and re-flowed into a rectangle.",
    "environmental": "A key visual applied to an object. Needs a panel-by-panel spec and a mock-up in "
                     "situ, not a crop.",
    "ooh": "Out-of-home — read at distance, from a moving vehicle as often as not.",
}

# A kit is a media decision, not a catalogue dump. These are the trade footprints people actually have,
# and the point of naming them is that each one also says what is deliberately left out.
KIT_PRESETS = {
    "general-trade": {
        "label": "General trade / kirana",
        "formats": ["tin-plate", "dealer-board", "poster-a3", "dangler", "shelf-strip", "wall-paint"],
        "left_out": "No gondola header — there is no gondola.",
    },
    "modern-trade": {
        "label": "Modern trade",
        "formats": ["gondola-header", "backing-sheet", "shelf-strip", "wobbler", "standee", "dangler"],
        "left_out": "No tin plate or wall paint — those are a kirana's shopfront, not a chain's aisle.",
    },
    "chiller": {
        "label": "Chiller-led (dairy, beverages, ice cream)",
        "formats": ["chiller-door", "chiller-side", "chiller-canopy", "dangler", "shelf-strip",
                    "poster-a3"],
        "left_out": "The chiller is the brand's shelf; anything competing with it is spend for nothing.",
    },
    "activation": {
        "label": "Activation-led",
        "formats": ["stall-backdrop", "stall-fascia", "stall-table", "stall-standee", "poster-a3"],
        "left_out": "The poster is for the trailing weeks after the stall comes down.",
    },
    "launch": {
        "label": "Launch",
        "formats": ["poster-a2", "poster-a3", "dangler", "shelf-strip", "wobbler", "standee",
                    "gondola-header"],
        "left_out": "OOH only if there is a media plan behind it. A hoarding in a POSM kit with no plan "
                    "is a line item, not a decision.",
    },
}


# --- what the numbers demand --------------------------------------------------------------------

# One inch of capital height per ten feet of viewing distance (United States Sign Council): 25.4mm per
# 3.05m, i.e. ~8.3mm of cap height per metre. This is trade practice, not a preference.
MM_CAP_PER_M = 8.3

# Word count is a function of reading distance and it is not negotiable. (distance ceiling, low, high)
WORDS_AT = (
    (0.6, 9, 12), (2.5, 6, 9), (6.0, 3, 6), (30.0, 0, 4), (10_000.0, 0, 2),
)


def spec(fmt: str) -> dict:
    """One format's row, or `{}`. The single read path, so a typo is empty rather than wrong."""
    return dict(FORMATS.get(fmt) or {})


def cap_height_mm(fmt: str) -> float:
    """Minimum printed cap height in millimetres, from how far away the piece is read."""
    row = FORMATS.get(fmt) or {}
    return round(MM_CAP_PER_M * float(row.get("read_at") or 2.0), 1)


def cap_fraction(fmt: str) -> float:
    """That same minimum as a fraction of the piece's own printed height.

    Returned as a fraction because the render is in pixels and the print size varies. It is a floor, not
    a target: a line can always be bigger, and may not be smaller and still be a POS piece.

    A shelf strip at 0.4m needs ~3.3mm caps on a 75mm piece — 4.4%. A gondola header at 4m needs ~33mm on
    a 300mm piece — 11%. That difference is exactly why the same line cannot simply be scaled.
    """
    row = FORMATS.get(fmt) or {}
    mm = row.get("mm")
    if not mm:
        return 0.0                       # the piece has to be measured; a made-up fraction is worse
    return round(min(0.5, cap_height_mm(fmt) / max(1.0, float(mm[1]))), 4)


def words_allowed(read_at: float) -> tuple[int, int]:
    """How many words survive at this distance. `(low, high)`."""
    for ceiling, lo, hi in WORDS_AT:
        if read_at <= ceiling:
            return lo, hi
    return 0, 2


def aspect_delta(fmt: str, master: str = MASTER_RATIO) -> float:
    """Target ratio ÷ master ratio. How hard the re-flow is, in one number."""
    row = FORMATS.get(fmt) or {}
    mm = row.get("mm")
    target = (float(mm[0]) / float(mm[1])) if mm else ratio_num(str(row.get("ratio") or ""))
    base = ratio_num(master) or 0.75
    return round(target / base, 2) if target and base else 0.0


# Bands from `references/adaptation.md`. The point of the table is that the re-flow class is decided by
# arithmetic rather than per piece by eye — which is the difference between a kit and eleven pieces.
#
# The "wider" ceiling is 2.7 and not the 2.5 the reference's band table states, because that table
# contradicts the reference's own worked example: it lists dealer board, backing sheet, hoarding and
# unipole as *wider*, and every one of them is 2:1 — which against a 3:4 master is delta 2.67. The
# adaptation sheet in the same file then says `delta 2.67 — wider; hero re-cropped` in as many words. A
# boundary that reclassifies four named examples out of the band they are named in is the boundary that
# is wrong, so the examples win.
#
# The reference's *lists* of example formats are looser than its arithmetic and do not all reconcile —
# it files the stall backdrop (5:4, delta 1.67) and the chiller door (3:7, delta 0.57) under "near"
# where the numbers put them in "wider" and "taller". The arithmetic governs, as the reference itself
# says it should; do not chase those two back into the lists.
def reflow(fmt: str, master: str = MASTER_RATIO) -> dict:
    """How this format is re-laid out of the master's layers. Never a crop of the artwork."""
    d = aspect_delta(fmt, master)
    forced = str((FORMATS.get(fmt) or {}).get("reflow_band") or "")
    if forced == "violent":
        # Not an aspect judgement. Some substrates cannot hold a photographic hero at any ratio, and a
        # band computed from the shape alone would send artwork a hand-painter cannot reproduce.
        return {"delta": d, "band": "violent",
                "what": "Violent — the substrate cannot carry a photographic hero.",
                "action": "Re-flow with the hero dropped or reduced to a flat motif. Spot colours only."}
    if not d:
        return {"delta": 0.0, "band": "unknown", "what": "The piece has to be measured first.",
                "action": "Ask for the bay or board dimension; do not assume one."}
    if 0.7 <= d <= 1.4:
        return {"delta": d, "band": "near", "what": "Near-square to moderately different.",
                "action": "Straight re-flow. Every layer keeps its role."}
    if 1.4 < d <= 2.7:
        return {"delta": d, "band": "wider", "what": "Notably wider.",
                "action": "Re-flow, and re-crop the hero cut-out — a full figure becomes upper body. "
                          "Type usually goes from stacked to beside."}
    if 0.4 <= d < 0.7:
        return {"delta": d, "band": "taller", "what": "Notably taller.",
                "action": "Re-flow, and the field gains height. Use the extra height for the brand "
                          "block and the type, not for a stretched hero."}
    return {"delta": d, "band": "violent", "what": "Violent — nothing croppable survives.",
            "action": "Re-flow with the hero dropped or reduced to a motif. Same field colour, same "
                      "logo, same typeface, three or four words. Nothing is re-rendered."}


# The drop-out ladder. Fixed order, read from the bottom up as the piece shrinks: support and devices go
# first, then the field graphics, then any secondary cut-outs, then the hero itself.
DROP_ORDER = ("devices", "field_graphics", "secondary", "hero", "type")

TIERS = {
    "full": {"label": "Full", "dropped": (),
             "what": "Everything. Poster A2/A3, standee, dealer board, stall backdrop, bus shelter, "
                     "chiller side."},
    "reduced": {"label": "Reduced", "dropped": ("devices",),
                "what": "Drop the support items; tighten the hero to head-and-pack or to the metaphor "
                        "object alone."},
    "minimal": {"label": "Minimal", "dropped": ("devices", "field_graphics", "secondary", "hero"),
                "what": "Drop the hero entirely. Pack, line and brand block on a brand colour field."},
    "mark-only": {"label": "Mark only",
                  "dropped": ("devices", "field_graphics", "secondary", "hero", "type"),
                  "what": "Pack silhouette and brand block, no line. Anything read beyond 30m, where a "
                          "line is wasted."},
}

# Never dropped, whatever the tier says. Kept as a separate rule rather than folded into the tiers,
# because "the brand block never goes" is the sort of thing a tier table quietly loses.
NEVER_DROPPED = ("field", "brand_block", "mandatories")


def tier_for(fmt: str) -> str:
    return str((FORMATS.get(fmt) or {}).get("tier") or "reduced")


def dropped_layers(fmt: str) -> list[str]:
    """Which layers leave on this piece, in ladder order."""
    keep_pack = fmt not in ("entry-arch", "stall-fascia")
    out = [d for d in TIERS.get(tier_for(fmt), TIERS["reduced"])["dropped"]]
    if not keep_pack and "pack" not in out:
        out.append("pack")
    return out


def custom_format(width: float, height: float) -> str:
    """Register (or reuse) a custom L×B shape as a synthetic format id, so it renders through the exact
    same canvas/re-flow/tier machinery as any of the 30 named formats — no second code path, and no
    second set of assumptions about what an extreme shape does to a photographic hero.

    Not a physical substrate: `mm` is left `None` (so `canvas_px`'s own dpi/print path correctly
    refuses it — a real print size cannot be claimed for a shape nobody has measured against paper),
    and its `tier` is INFERRED from `aspect_delta` alone, the same bands `reflow` already computes,
    because there is no real reading distance or substrate here to hand-curate one against the way
    every row in `FORMATS` above was. Idempotent — the same W:H always resolves to the same entry rather
    than growing a fresh row per call.
    """
    width, height = max(0.01, float(width)), max(0.01, float(height))
    ratio = f"{width:g}:{height:g}"
    key = f"custom-{width:g}x{height:g}"
    if key in FORMATS:
        return key
    delta = ratio_num(ratio) / (ratio_num(MASTER_RATIO) or 0.75)
    if not (0.4 <= delta <= 2.7):
        tier = "minimal"          # same ground `reflow`'s "violent" band names — no croppable hero
    elif not (0.7 <= delta <= 1.4):
        tier = "reduced"          # "wider"/"taller" — keep the hero, tighten the crop
    else:
        tier = "full"
    FORMATS[key] = {
        "family": "custom", "label": f"Custom {width:g}×{height:g}", "mm": None, "ratio": ratio,
        "read_at": 2.0, "sides": 1, "substrate": "digital export", "tier": tier, "clear": "",
        "trap": "A custom digital size, not a researched physical substrate — its tier is inferred from "
                "shape alone, not measured against a real reading distance the way the catalog sizes "
                "are. No print export until real mm dimensions are added.",
    }
    return key


def resolve_format(fmt: str, custom_ratio: str = "") -> tuple[str, str]:
    """The one place every POSM render/artwork/print route turns a request into a format id — a named
    catalog entry, or a freshly-registered custom size — so custom-size parsing lives once instead of
    being copied into three routes and drifting. Returns `(format_id, error)`; `error` is `""` on
    success and otherwise a message safe to hand back to the caller directly.
    """
    fmt = str(fmt or "").strip()
    custom_ratio = str(custom_ratio or "").strip()
    if fmt and fmt in FORMATS:
        return fmt, ""
    if custom_ratio or fmt == "custom":
        if not custom_ratio:
            return "", "Custom size needs a ratio, e.g. '3:2' — pass it as custom_ratio."
        try:
            cw, ch = (float(x) for x in custom_ratio.replace("x", ":").replace("X", ":").split(":")[:2])
            if cw <= 0 or ch <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return "", f"Could not read {custom_ratio!r} as a W:H ratio, e.g. '3:2'."
        return custom_format(cw, ch), ""
    return "", f"Unknown format {fmt!r}."


def production_mode(fmt: str) -> dict:
    """Which generation lane this format's own production method actually allows.

    Not a style preference — a physical constraint already on file. `wall-paint`'s own `substrate`
    ("hand-painted, flat spot colours") and `trap` ("no photograph, no gradient, no soft shadow") have
    said this since the format table was written; nothing generating for it has ever read them. A
    person hand-painting a 20-foot wall cannot reproduce a photographic gradient regardless of how the
    prompt is worded — this is the same category of fact `bleed_safe`'s own `"paint" in sub` check
    already keys off, generalised into a decision the generation step can act on before rendering
    rather than after.

    Returns `{mode, why}`. `mode` is `"paintable"` (flat spot colours, no photograph, no AI backdrop)
    or `"rich"` (photographic hero and/or backdrop are fair game) — a caller-supplied override always
    wins; this is only the default a person did not already choose.
    """
    row = FORMATS.get(fmt) or {}
    sub = str(row.get("substrate") or "").lower()
    if "paint" in sub or "hand-painted" in sub:
        return {"mode": "paintable",
                "why": row.get("trap") or "Hand-painted or hand-produced at scale — flat spot colours "
                                          "only, no photograph or gradient survives reproduction."}
    return {"mode": "rich", "why": ""}


def bleed_safe(fmt: str) -> dict:
    """Bleed and safe area in millimetres, from the substrate and the size."""
    row = FORMATS.get(fmt) or {}
    sub = str(row.get("substrate") or "").lower()
    mm = row.get("mm")
    big = bool(mm and max(mm) > 594)                     # larger than A2
    if "flex" in sub or "vinyl" in sub or "fabric" in sub:
        return {"bleed_mm": 25, "safe_mm": 50,
                "why": "Flex and vinyl on a frame — the frame eats the edge."}
    if "paint" in sub:
        return {"bleed_mm": 0, "safe_mm": 0, "why": "Hand-painted; there is no trim."}
    return {"bleed_mm": 5 if big else 3, "safe_mm": 5,
            "why": "Flat print. Nothing important in the bleed, and no brand mark closer to the trim "
                   "than its own cap height."}


# --- the hero -----------------------------------------------------------------------------------
#
# Pick one deliberately and say why. The crop gate is applied FIRST, because it eliminates options before
# merit does — and the strategically strongest hero is often not the buildable one.
HERO_TYPES = {
    "person-in-benefit": {
        "label": "Person in benefit",
        "what": "The consumer visibly carrying the result. The person is the proof.",
        "works": "Where the benefit photographs — hair, skin, a clean shirt.",
        "fails": "Where it does not. A photograph cannot show immunity or digestion, and a smiling face "
                 "standing in for an invisible benefit is the most generic POS piece there is.",
        "needs": ["casting and usage rights"],
        "survives_12_1": False, "survives_1_1": True,
        "exhibits": ["pantene-sonakshi-broken-cycle", "nivea-creme-soft-milk",
                     "nivea-men-derma-control"],
    },
    "endorser-with-pack": {
        "label": "Endorser with pack",
        "what": "A known face presenting the product. Note the posture in every exhibit: the endorser "
                "holds or presents the pack, and their eyeline or gesture points at it.",
        "works": "Borrows credibility and buys stopping power.",
        "fails": "An endorser standing beside a product is a photograph of a famous person.",
        "needs": ["signed talent", "a `cast` or `actor` library reference so likeness is pinned by "
                  "image", "a territory-and-term check"],
        "survives_12_1": False, "survives_1_1": False,
        "exhibits": ["dabur-chyawanprash-100-illnesses", "surf-excel-matic-sanath",
                     "dabur-honey-stay-fit"],
    },
    "metaphor-object": {
        "label": "Metaphor object",
        "what": "The benefit made into a single object.",
        "works": "Strongest at distance and cheapest to produce. One shape, high contrast, no talent, "
                 "no rights, and it reads as a silhouette at four metres where a face does not. Use it "
                 "when the benefit is invisible — which is exactly when the first two types fail.",
        "fails": "If it takes two things to read, it is not this type.",
        "needs": ["a metaphor that is one object"],
        "survives_12_1": True, "survives_1_1": True,
        "exhibits": ["dabur-honey-heart-health"],
    },
    "occasion": {
        "label": "Occasion",
        "what": "The moment of use or celebration. Both exhibits carry a relationship, not just an event.",
        "works": "Sells relevance rather than superiority. Right for festival and seasonal kits, and for "
                 "categories where every functional claim is the same.",
        "fails": "'Family time' is not an occasion. A real one has a date.",
        "needs": ["a real occasion with a date"],
        "survives_12_1": False, "survives_1_1": False,
        "exhibits": ["surf-excel-holi-daag-acche-hain", "motherdairy-haldi-milk"],
    },
    "range-array": {
        "label": "Range array",
        "what": "The portfolio as the hero. Says 'we are a house', not 'this is better'.",
        "works": "Only when breadth is the message, and only when the array has a reason to be a group.",
        "fails": "Wrong for any single-SKU push: it splits attention across five shapes at the moment "
                 "you needed one recognised.",
        "needs": ["every pack as a library reference", "a decision about which pack leads"],
        "survives_12_1": False, "survives_1_1": False,
        "exhibits": ["motherdairy-dosti-range"],
    },
    "demonstration": {
        "label": "Product in use / demonstration",
        "what": "The product doing its work.",
        "works": "The only type that carries a functional claim without a person vouching for it.",
        "fails": "An invisible process staged as a glow is decoration pretending to be a demonstration. "
                 "The mechanism has to be visually legible — a vortex, a stain lifting, a coating.",
        "needs": ["a mechanism that shows", "a sourced RTB"],
        "survives_12_1": False, "survives_1_1": True,
        "exhibits": ["surf-excel-matic-smart-shots"],
    },
}

FIELD_DIVISIONS = {
    "horizontal-split": "The safest. Hero above, flat colour below carrying type and pack.",
    "diagonal-split": "Two type-safe zones out of one frame, with energy. Excellent on portrait formats.",
    "curved-split": "Softer and more premium than a diagonal. Needs width to read as intentional.",
    "single-flat": "One colour, everything floated on it. The most POS-looking of all, and the most "
                   "forgiving in adaptation.",
    "brand-pattern": "A brand-owned repeating graphic. Makes a fragment recognisable with no logo in it.",
    "radiating": "Streaks or a glow behind the hero, to lift it off the field and imply energy.",
}

TYPE_DEVICES = {
    "multi-weight": "One word or phrase very large, the rest smaller. Never one uniform size.",
    "shaped-badge": "A roundel, seal, starburst or object shape relevant to the claim, containing type.",
    "highlight-box": "A coloured box behind one word inside a longer line.",
    "new-flash": "Rounded rectangle or roundel, high contrast, one word. Almost every launch piece.",
    "underline": "A rule under the word doing the work.",
    "stroked": "Outlined type, where the field behind it varies.",
    "base-tagline": "The tagline in the base band, locked, same position across the kit.",
    "footnote-strip": "Smallest type on the piece, substantiating any claim above it.",
    "care-box": "A contact or care block in a contrasting colour, cornered.",
}

# `dabur-honey-heart-health.jpg` runs exactly four support items and is at the ceiling.
SUPPORT_MAX = 4

# Where the type block sits. These are the old `KV_LAYOUTS` keys, kept because the vocabulary is right
# and the screen already speaks it — but they now describe the position of a type block on a flat field,
# not a band reserved inside a photograph. That is the whole difference between this module and the one
# it replaces.
TYPE_POSITIONS = {
    "type-locked-base": "The type block locked along the base, hero above it. The safest, and the one "
                        "that survives being trimmed.",
    "type-over-top": "The type block across the top third, hero below. Reads first at distance, and "
                     "works where the shelf cuts the bottom off.",
    "type-beside": "Type block and hero side by side. Needs width — good on a header strip, wrong on a "
                   "dangler.",
    "type-only": "Type doing the whole job, pack as a small lock-up. For where a photograph will not "
                 "survive the print.",
    "product-only": "No line at all. The pack and the brand mark only, for sizes too small to read.",
}


def crop_gate(hero_type: str, formats: list[str] | tuple[str, ...] = ()) -> dict:
    """Can this hero survive the kit's aspect spread? Applied before comparing types on merit.

    The kit constrains the hero, and it eliminates options that are otherwise the strongest. Saying so
    here is the point: the alternative is discovering it eleven adaptation sheets later.
    """
    h = HERO_TYPES.get(hero_type) or {}
    if not h:
        return {"ok": False, "why": "Unknown hero type.", "violent": [], "tiny": []}
    violent = [f for f in formats if reflow(f)["band"] == "violent"]
    tiny = [f for f in formats if tier_for(f) in ("mark-only",) or (FORMATS.get(f, {}).get("mm") or
                                                                    (999, 999))[0] <= 100]
    fails = []
    if violent and not h.get("survives_12_1"):
        fails.append(f"{h['label']} cannot survive the very wide formats "
                     f"({', '.join(violent)}) — the hero is dropped there and those pieces become "
                     f"field, pack, line and brand block.")
    if tiny and not h.get("survives_1_1"):
        fails.append(f"{h['label']} cannot survive the smallest formats ({', '.join(tiny)}).")
    return {"ok": not fails, "why": " ".join(fails), "violent": violent, "tiny": tiny,
            "note": ("The hero is dropped on those pieces by the ladder, which is a decision and not a "
                     "failure — but decide it now rather than at adaptation."
                     if fails else "")}


# --- the library gate ---------------------------------------------------------------------------

def gate(hero_type: str = "", brand: str = "") -> dict:
    """What the library allows to be made right now.

    `brand` scopes every count/url here to that brand's own signed-off assets (see library.py's
    brand-scoping note) — without it, a brand with zero of its own signed-off packs would still pass
    this gate as long as SOME other brand in the tenant had one.

    Two separate gates, and conflating them was costing real work. The **master key visual** is refused
    without a signed-off pack and logo: POSM's job at shelf is recognition, the shopper matches what is
    on the poster to what is in their hand, and a generated pack is always subtly wrong in the
    proportions, the cap or the label geometry — and the model draws brand lettering onto it, which is
    the one thing that must never be generated. A piece with an invented pack is not a comp with a flaw;
    it teaches the shopper the wrong shape.

    The **hero cut-out** is a different question. The hero is not the pack, so the field and the hero can
    proceed while the pack shot is being sourced — the piece is blocked at artwork stage, not at render
    stage. Three hero types are the exception, because for them the library reference *is* the subject:
    `endorser-with-pack` and `person-in-benefit` both need a cast or actor frame to pin likeness, and
    `range-array` needs the packs.

    `person-in-benefit` joined this list after a real failure, not by symmetry with the endorser case.
    The skill's own spec already said this hero type "needs: casting and usage rights" — a real person,
    not a hallucinated one — but nothing enforced it, so the render call generated an anonymous "person"
    from text same as any safe object. Asked for a photorealistic child (a real route: a school-ready
    kid, head to toe, on plain white), Google's image model didn't cleanly refuse — a documented,
    inconsistent minor-safety filter distorted the face into an unusable black mask instead. The fix
    is not a better prompt for that one case; a hallucinated identifiable person is the wrong thing to
    generate at all, the same way a hallucinated pack is. Route it through a real reference like the
    endorser case already does.
    """
    packs = library.items("pack", signed_only=True, brand=brand)
    logos = library.items("logo", signed_only=True, brand=brand)
    cast = library.items("cast", signed_only=True, brand=brand) + library.items("actor", signed_only=True, brand=brand)

    blocks, asset_blocks = [], []
    if not packs:
        blocks.append({"kind": "pack", "what": "No signed-off pack shot in the library.",
                       "do": "Upload the pack as it actually looks on shelf, under Library → Pack shot, "
                             "and sign it off. The pack is composited from that file, never described "
                             "in words."})
    if not logos:
        blocks.append({"kind": "logo", "what": "No signed-off logo artwork in the library.",
                       "do": "Upload the logo lock-up under Library → Logo and sign it off. The brand "
                             "block is vector artwork placed on the piece, never generated."})
    if hero_type in ("endorser-with-pack", "person-in-benefit") and not cast:
        asset_blocks.append({"kind": "cast",
                             "what": ("An endorser hero" if hero_type == "endorser-with-pack"
                                      else "A person-in-benefit hero")
                                     + " needs a signed-off cast or actor reference.",
                             "do": "Upload the approved frame under Library → Cast (or Actor) and sign "
                                   "it off. Likeness travels as a picture; a description redraws a "
                                   "different person every call — and for some subjects (a child, in "
                                   "particular) an image provider's own safety filtering can distort "
                                   "a purely-described face rather than refuse it cleanly."})
    if hero_type == "range-array" and len(packs) < 2:
        asset_blocks.append({"kind": "pack",
                             "what": "A range hero needs every pack in the array as a library "
                                     "reference.",
                             "do": "Upload each SKU under Library → Pack shot, sign them off, and say "
                                   "which pack leads."})

    return {
        "can_render_assets": not asset_blocks,
        "can_assemble_master": not blocks and not asset_blocks,
        "blocks": blocks + asset_blocks,
        "asset_blocks": asset_blocks,
        "pack": {"count": len(packs), "url": library.reference_url("pack", brand=brand)},
        "logo": {"count": len(logos), "url": library.reference_url("logo", brand=brand)},
        "cast": {"count": len(cast)},
        "note": ("The library has what the master needs." if not blocks and not asset_blocks else
                 "The hero cut-out can be rendered while the pack is sourced — the piece is blocked at "
                 "artwork stage, not at render stage."
                 if not asset_blocks else
                 "This hero type cannot be rendered until its library reference exists."),
    }


# --- the only prompt this module builds ---------------------------------------------------------

# The backdrop every cut-out is generated against, and the one the compositor keys back out. Mid-grey,
# and the reason is the single most useful thing learned about matting in this module.
#
# **Not white.** Cutting out on white is the default everyone reaches for and it is wrong for exactly
# the subjects this brand has. A matte is solved by separating subject from backdrop, so the backdrop
# must be a colour the subject does not contain — and half a dairy brand's subjects are white or
# near-white: milk, a glass of it, a splash, a white pack panel, a school shirt. Keying white out of
# those punches holes through the product (found live: a glass of milk came back with the field showing
# through it and the pack's white panel chewed away). The second cost is quieter and affects every
# piece: anti-aliased edge pixels keep the backdrop's colour, so a subject cut from white and placed on
# Deep Forest carries a pale halo all the way round — Adobe ships "Remove White Matte" as a named
# operation precisely because this is universal, not a fluke.
#
# **Not the brand colour either**, which was this docstring's original point and still holds: a subject
# generated already sitting on Deep Forest cannot be lifted off it cleanly, and the green in the render
# would not match the brand's green anyway.
#
# Mid-grey satisfies both. Nothing in an FMCG hero is a flat neutral 50% grey, so the separation is
# unambiguous; and grey contamination on an edge is neutral rather than a bright halo, so what little
# survives decontamination is invisible on any field colour. This is the same reasoning that makes
# chroma-key backdrops a saturated green rather than white.
CUTOUT_BACKDROP = "#808080"


# Everything that goes into a piece, declared in one place.
#
# This exists because the inputs were real but scattered — some on the route, some in the assets panel,
# some derived from the format table, some constants in the compositor — and nothing ever listed them
# together. The cost was not theoretical: a route describing "a mother mid-motion setting a glass down"
# was chosen and the finished poster had no person in it, because the hero was shot from an unrelated
# free-text box and nothing compared the two. When the inputs are not enumerated, "was this one used?"
# is not a question anybody can answer.
#
# `source` is where the value legitimately comes from, and it is the useful column: an input sourced
# from the library must never be typed, and one sourced from the route must never be re-invented at
# render time. `missing` says what actually happens when it is absent — the honest version, not a
# warning label.
RENDER_INPUTS = (
    # --- what the piece is arguing, before anything is drawn -------------------------------------
    {"key": "stands_on", "group": "Strategy", "label": "What it stands on", "required": True,
     "source": "idea platform, else the messaging house, else the brief",
     "why": "The proposition the piece expresses. Not printed — it is what the route is judged against.",
     "missing": "Refused. POS is an expression of an idea and there is no idea yet."},
    {"key": "brand", "group": "Strategy", "label": "Brand profile", "required": True,
     "source": "brand profile",
     "why": "Name, category, positioning, tone, master idea, competitors, banned words.",
     "missing": "Generated copy reads as any brand in the category."},

    # --- the route: one decision that fixes five things --------------------------------------------
    {"key": "route", "group": "Route", "label": "Chosen route", "required": True,
     "source": "/posm-keyvisual, chosen by a person",
     "why": "Fixes the hero type, the layout, the line and the subject together. Choosing a route is "
            "the design decision; everything downstream is execution of it.",
     "missing": "Nothing to execute."},
    {"key": "subject", "group": "Route", "label": "Hero subject", "required": True,
     "source": "the route's own `subject` — positive, in-frame only",
     "why": "The brief for whatever is shot as the hero. Must never mention packaging (composited "
            "separately) and must never carry the route's 'left out' clause (models do not negate).",
     "missing": "The hero is shot from whatever text happens to be in the box, which is how a piece "
                "ends up contradicting its own route."},
    {"key": "hero_type", "group": "Route", "label": "Hero type", "required": True,
     "source": "the route, one of HERO_TYPES",
     "why": "Decides which references the hero generation must carry, and whether a person is needed.",
     "missing": "Reference attachment falls back to guesswork."},
    {"key": "line", "group": "Route", "label": "The line", "required": True,
     "source": "the route, or typed to override",
     "why": "The exact words on the piece. Set as real type, never generated into the picture.",
     "missing": "A piece with no message."},
    {"key": "line_emphasis", "group": "Route", "label": "Word set largest", "required": False,
     "source": "the route's `line_emphasis`",
     "why": "Multi-weight headline — one phrase very large, the rest smaller. Never one uniform size.",
     "missing": "Falls back to a heuristic (clause before the comma, else the longest word)."},

    # --- ground truth: things that must be real ----------------------------------------------------
    {"key": "pack_id", "group": "Ground truth", "label": "Pack shot", "required": True,
     "source": "library, signed off",
     "why": "Composited from the real photograph. A generated pack has the proportions, cap and label "
            "geometry subtly wrong and arrives with invented brand lettering on it.",
     "missing": "Master render refused."},
    {"key": "logo", "group": "Ground truth", "label": "Logo", "required": True,
     "source": "library or brand profile",
     "why": "Placed as artwork. The brand block is the one layer that is never dropped, at any size.",
     "missing": "A piece nobody can attribute."},
    {"key": "cast_id", "group": "Ground truth", "label": "Cast / model", "required": False,
     "source": "library, signed off",
     "why": "Required by the three hero types built on a person. A described person is a different "
            "person every render.",
     "missing": "Refused for person-led hero types; irrelevant for object-led ones."},
    {"key": "plate_id", "group": "Ground truth", "label": "Location plate", "required": False,
     "source": "library, signed off, or an AI backdrop draft",
     "why": "Only for the minority photographic build. A photograph never hosts type — it is bounded "
            "into a hard split and the type sits on the flat half.",
     "missing": "The field is flat brand colour, which is the category default anyway."},
    {"key": "mandatories", "group": "Ground truth", "label": "Mandatories", "required": True,
     "source": "typed — the real strings",
     "why": "FSSAI mark and licence number, veg mark, statutory lines. Legal identifiers.",
     "missing": "Left off the piece and reported outstanding. Never invented — a licence number is not "
                "something this tool can know."},

    # --- design decisions -------------------------------------------------------------------------
    {"key": "field_hex", "group": "Design", "label": "Field colour", "required": True,
     "source": "brand palette, else measured from the signed-off logo/pack",
     "why": "The field IS the brand on a POS piece, and it is the space the type sits in.",
     "missing": "A neutral stand-in, which is the wrong artwork rather than a safe default."},
    {"key": "type_position", "group": "Design", "label": "Layout", "required": True,
     "source": "the route, overridable by picking a scamp",
     "why": "Where the type block sits and therefore where the hero can go.",
     "missing": "Defaults to type-locked-base, the safest."},
    {"key": "device", "group": "Design", "label": "Type device", "required": False,
     "source": "chosen — rule, highlight box, or none",
     "why": "Type on POS is built, not set on a background. A headline floating alone reads as a slide.",
     "missing": "Defaults to an underline rule."},
    {"key": "support_line", "group": "Design", "label": "Base band tagline", "required": False,
     "source": "the brand's locked line",
     "why": "Locked copy, same position across the kit.",
     "missing": "No base band, and the mandatories lose their home."},

    # --- the format decides the numbers, not taste -------------------------------------------------
    {"key": "format", "group": "Format", "label": "Format", "required": True,
     "source": "chosen from FORMATS",
     "why": "Carries the real millimetres, reading distance, substrate, sides and traps — from which "
            "cap height, bleed, safe area, re-flow band and the drop-out ladder all follow.",
     "missing": "Nothing can be sized."},
    {"key": "dpi", "group": "Format", "label": "Output resolution", "required": False,
     "source": "300 for print, preview otherwise",
     "why": "A screen comp and a print file are different artefacts.",
     "missing": "Preview only — not something a printer can set from."},
)


def scamp_prompt(subject: str, line: str, type_position: str, *, fmt: str = "", adjust: str = "") -> str:
    """A hand-drawn layout scamp: the route's actual idea, sketched, with the headline lettered in.

    Replaces a wireframe of grey boxes. The boxes were honest about geometry and useless for the
    decision they existed to serve — you cannot tell whether an arrangement WORKS from two rectangles
    and a diagonal, because the thing being judged is whether the picture and the words hold together,
    and neither was present. An art director's scamp is a drawing: the scene, roughly, with the line
    lettered where it goes. That is what gets pinned up and argued over.

    Deliberately pencil and deliberately rough. A scamp that looks finished invites a verdict on the
    rendering — the wrong conversation at this stage — and the only question here is whether the
    composition and the line work together. Graphite on paper says "not decided yet" in a way no amount
    of caveat text does.

    The headline is asked for as hand lettering rather than set type on purpose: nobody mistakes
    hand-drawn words for final typography, so the model garbling a letterform costs nothing here, where
    on a finished piece it would be the most expensive defect this tool can produce.
    """
    zone = {
        "type-locked-base": "the headline hand-lettered across the BOTTOM third, the drawing filling "
                            "the upper two thirds above it",
        "type-over-top": "the headline hand-lettered across the TOP third, the drawing filling the "
                         "lower two thirds below it",
        "type-beside": "the headline hand-lettered down the LEFT side, the drawing occupying the right "
                       "two thirds beside it",
        "type-only": "the headline hand-lettered large in the middle, with only a small drawing below",
        "product-only": "no headline at all — just the drawing, centred, with a small brand mark",
    }.get(type_position, "the headline hand-lettered across the bottom third, the drawing above it")

    subject = str(subject or "").strip().rstrip(".") or "the product"
    line = str(line or "").strip()
    label = (FORMATS.get(fmt) or {}).get("label", "")
    return " ".join(p for p in [
        "A rough layout scamp for a poster, drawn by an art director on paper — a thumbnail sketch used "
        "to decide the arrangement before any artwork is made.",
        f"Portrait format{f' ({label})' if label else ''}. Composition: {zone}.",
        f"The drawing shows: {subject}.",
        (f'Hand-lettered in rough capitals in the type area, spelled exactly: "{line}".' if line
         else "No headline."),
        # A director's revision to a specific pinned-up scamp, not a re-ask of the whole brief — kept
        # last and named as a note so it reads as "change this about the sketch above" rather than
        # competing with the composition/subject clauses for the model's attention.
        (f"Revision note from the art director on this sketch — apply it: {str(adjust).strip()}"
         if str(adjust or "").strip() else ""),
        "Loose graphite pencil sketch on off-white paper. Visible construction lines and light grid, "
        "hatching and cross-hatching for shading, confident gestural line work, some lines left open. "
        "Monochrome pencil only — no colour, no flat fills, no digital rendering, no photorealism.",
        "It must read as a hand-drawn sketch on paper, not as a finished poster.",
    ] if p)


def hero_type_brief(hero_type: str) -> str:
    """What `HERO_TYPES[hero_type]["what"]` says this hero IS, as one imperative sentence for a
    generation prompt — not the label, the actual casting instruction.

    `cutout_prompt` and the cast/studio-shot routes used to hand the model a route's free-text subject
    alone. `hero_type` (e.g. `person-in-benefit` vs `endorser-with-pack`) was resolved and gated on but
    never reached the words the model reads — so a route correctly typed as a child-led benefit shot
    could still come back drawn as an adult, because nothing in the prompt said which of the two the
    subject even was. This is that missing sentence.
    """
    info = HERO_TYPES.get(str(hero_type or "").strip())
    return str(info["what"]).strip() if info and info.get("what") else ""


def cutout_prompt(subject: str, *, style_note: str = "", type_brief: str = "") -> str:
    """An isolated subject on a plain mid-grey backdrop, ready to cut out. Not a composition.

    Three clauses here are load-bearing and all three were learned the expensive way.

    **Mid-grey, never white and never the brand colour** — see `CUTOUT_BACKDROP` above for the full
    reasoning; briefly, a matte needs a backdrop the subject does not contain, and this brand's
    subjects are frequently white.

    **"No floor line."** A horizon or surface edge is a second element that has to be masked out, and
    models put one in by default unless told not to.

    The no-lettering clause reaches objects and garments deliberately: the model will put brand-like
    marks on a shirt or a crate, and every word on a POS piece is set in artwork.
    """
    subject = str(subject or "").strip().rstrip(".")
    type_brief = str(type_brief or "").strip().rstrip(".")
    return " ".join(p for p in [
        f"{type_brief}." if type_brief else "",
        f"{subject}.",
        "Isolated on a plain flat mid-grey (50% grey, #808080) seamless background — an even studio "
        "backdrop of that one colour, edge to edge, nothing else. The entire subject is visible with "
        "clear space around it. Even, soft, directional studio lighting. Sharp focus throughout, deep "
        "depth of field, no background blur. No environment, no set, no props, no furniture, no floor "
        "line, no cast shadow on the background. The subject FLOATS on the flat backdrop: no surface or "
        "table under it, no reflection, no mirrored floor, no gradient, no vignette — models add a "
        "glossy reflective surface by default and its broken-up tones survive the key as grey debris "
        "under the subject. Nothing cropped by the frame edge. Photorealistic.",
        style_note.strip(),
        "Absolutely no text, lettering, logos, watermarks, borders or branding of any kind anywhere in "
        "the image, including on any object or garment in frame.",
    ] if p)


# Words that mean the subject IS the pack. Crude on purpose, and it earns the crudeness: the first
# render made with this module came back as an invented white gable-top carton with invented label marks
# on it, because the subject handed in named the product. That is the single most expensive output this
# tool can produce — a piece that teaches the shopper the wrong shape — and it is worth a false positive
# to stop, because the false positive costs one sentence saying which library file to use instead.
#
# The word list is deliberately not narrowed to "the pack is the *subject*". The pack is layer 4 and the
# hero is layer 3 — two separately sourced assets — so a pack appearing anywhere in a hero brief is a
# category error, not a matter of emphasis. `tin` and `can` are left out as too ambiguous in English
# ("a tin roof"); every remaining word names packaging and almost nothing else.
_PACK_WORDS = ("pack", "packet", "carton", "tetra", "bottle", "pouch", "sachet", "jar", "tub",
               "wrapper", "label", "sku", "packshot")


def looks_like_pack(subject: str) -> bool:
    """Does this cut-out brief put the product's own packaging in frame?

    The pack is composited from the library reference and never described in words — the model gets the
    proportions, the cap and the label geometry subtly wrong and then draws brand lettering onto it,
    which is the one thing that must never be generated.
    """
    s = f" {str(subject or '').lower()} "
    return any(w in s for w in _PACK_WORDS)


# --- the adaptation sheet -----------------------------------------------------------------------

def adaptation(fmt: str, *, line: str = "", short_line: str = "", field: str = "",
               hero: str = "", type_position: str = "") -> dict:
    """One format's sheet: everything a studio needs and nothing it has to guess.

    Every number here is computed from the format's own millimetres and reading distance. Nothing is
    asked of a model, because none of it is a judgement — which is the point of the table existing at
    all.
    """
    row = FORMATS.get(fmt)
    if not row:
        return {"format": fmt, "error": "unknown format"}
    mm = row.get("mm")
    read_at = float(row.get("read_at") or 2.0)
    lo, hi = words_allowed(read_at)
    flow = reflow(fmt)
    drops = dropped_layers(fmt)
    bs = bleed_safe(fmt)

    words = len([w for w in str(line or "").split() if w])
    short_words = len([w for w in str(short_line or "").split() if w])
    # Which line this piece actually uses. A truncated long line loses the verb and becomes a label, so
    # the short version is written from the same proposition rather than cut down — and if it is missing
    # this says so instead of silently shipping nine words onto a gondola header.
    fits = words and lo <= words <= hi
    use_short = bool(words and not fits)
    used = short_line if (use_short and short_line) else line

    missing = []
    if not mm:
        missing.append("the piece's real dimensions — this one must be measured, never assumed")
    if use_short and not short_line:
        missing.append(f"a {lo}–{hi} word version of the line for this distance, written from the same "
                       f"proposition rather than truncated from the {words}-word one")
    if row.get("retailer_field"):
        missing.append("the retailer's name, address, phone and GSTIN for the variable field")
    if row.get("sides", 1) == 2:
        missing.append("side B artwork — it is seen from behind, and a blank back is a broken piece")

    return {
        "format": fmt,
        "label": row.get("label", fmt),
        "family": row.get("family", ""),
        "mm": list(mm) if mm else None,
        "ratio": row.get("ratio", ""),
        "read_at_m": read_at,
        "sides": row.get("sides", 1),
        "substrate": row.get("substrate", ""),
        "source": "re-flow of the master's layers" + (f" (delta {flow['delta']} — {flow['band']})"
                                                      if flow["delta"] else ""),
        "reflow": flow,
        "field": field,
        "hero": hero,
        "tier": tier_for(fmt),
        "tier_note": TIERS.get(tier_for(fmt), {}).get("what", ""),
        "type_position": type_position,
        "type_position_note": TYPE_POSITIONS.get(type_position, ""),
        "line": used,
        "line_words": len([w for w in str(used or "").split() if w]),
        "words_allowed": [lo, hi],
        "uses_short_line": use_short,
        "cap_height_mm": cap_height_mm(fmt),
        "cap_height_pct": round(cap_fraction(fmt) * 100, 1),
        "dropped": drops,
        "dropped_labels": [next((l["label"] for l in LAYERS if l["id"] == d), d) for d in drops],
        "never_dropped": list(NEVER_DROPPED),
        "clear": row.get("clear", ""),
        "bleed_mm": bs["bleed_mm"], "safe_mm": bs["safe_mm"], "bleed_why": bs["why"],
        "retailer_field": row.get("retailer_field", ""),
        "trap": row.get("trap", ""),
        "dimensions_source": "vendor" if not mm else "assumed",
        "missing": missing,
        "short_words": short_words,
    }


def kit(formats: list[str] | tuple[str, ...], *, line: str = "", short_line: str = "",
        field: str = "", hero: str = "", type_position: str = "") -> dict:
    """Adaptation sheets for a whole kit, plus the checks that only make sense across pieces."""
    known = [f for f in formats if f in FORMATS]
    unknown = [f for f in formats if f not in FORMATS]
    sheets = [adaptation(f, line=line, short_line=short_line, field=field, hero=hero,
                         type_position=type_position) for f in known]

    findings = []
    two_sided = [s["format"] for s in sheets if s["sides"] == 2]
    if two_sided:
        findings.append({"id": "sides", "level": "ask",
                         "what": f"{len(two_sided)} piece(s) are seen from two directions: "
                                 f"{', '.join(two_sided)}.",
                         "why": "A spinning dangler with a white back is broken half the time. Side B "
                                "may be simplified — brand block and line, no hero — but it may not be "
                                "blank."})
    needs_short = [s["format"] for s in sheets if s["uses_short_line"] and not short_line]
    if needs_short:
        findings.append({"id": "short-line", "level": "block",
                         "what": f"{', '.join(needs_short)} cannot carry the {len(line.split())}-word "
                                 f"line at their reading distance.",
                         "why": "Write the short version from the same proposition. A truncated line "
                                "usually loses the verb and becomes a label."})
    unmeasured = [s["format"] for s in sheets if not s["mm"]]
    if unmeasured:
        findings.append({"id": "measure", "level": "ask",
                         "what": f"{', '.join(unmeasured)} has no standard size.",
                         "why": "Bay widths differ by chain and by store. Ask for the dimension and say "
                                "who measures it; do not invent one."})
    occluded = [s["format"] for s in sheets if s["clear"]]
    if occluded:
        findings.append({"id": "occlusion", "level": "note",
                         "what": f"Something physical stands in front of {', '.join(occluded)}.",
                         "why": "Artwork that puts the line where a body, a leg or a cassette goes has "
                                "no line."})
    if hero:
        cg = crop_gate(hero, known)
        if not cg["ok"]:
            findings.append({"id": "crop-gate", "level": "ask", "what": cg["why"], "why": cg["note"]})

    return {"formats": sheets, "unknown": unknown, "findings": findings,
            "count": len(sheets),
            "families": sorted({s["family"] for s in sheets if s["family"]})}


# --- checking a key visual before it is offered --------------------------------------------------

def spec_findings(kv: dict) -> list[dict]:
    """The eight checks from `references/key-visual.md`, computed rather than remembered.

    These are the questions that separate a POS piece from a slide, and every one of them has a real
    failure behind it. They are findings and not a schema: a piece that trips one may still be right,
    and the person deciding that should see the question rather than have it silently enforced.
    """
    out = []
    build = str(kv.get("build") or "layered")
    field = str(kv.get("field") or "")
    hero = str(kv.get("hero_type") or "")
    devices = [d for d in (kv.get("devices") or []) if d]
    support = [s for s in (kv.get("support") or []) if s]

    if build == "photographic" and not str(kv.get("why_photographic") or "").strip():
        out.append({"id": "build", "level": "block",
                    "what": "A photographic build with no argument for it.",
                    "why": "The photographic build is only correct when the scene itself is the "
                           "argument. 'It looks better' is how you end up with a stock photo and a "
                           "caption."})
    if build == "layered" and field and field not in FIELD_DIVISIONS:
        out.append({"id": "field", "level": "ask",
                    "what": f"'{field}' is not one of the field division devices.",
                    "why": "The field is flat colour, divided by a straight, diagonal or curved edge, "
                           "or a brand pattern. Never a photograph."})
    if not hero:
        out.append({"id": "hero", "level": "block", "what": "No hero chosen.",
                    "why": "If the pack is the only subject this is a pack shot — useful for a listing, "
                           "useless as POS. The pack is always present and never the subject."})
    if not devices:
        out.append({"id": "devices", "level": "ask",
                    "what": "No type device — no badge, box, flash or rule.",
                    "why": "A headline floating alone on a field reads as a slide. Type on POS is built, "
                           "not set."})
    if len(support) > SUPPORT_MAX:
        out.append({"id": "support", "level": "ask",
                    "what": f"{len(support)} support items; the ceiling is {SUPPORT_MAX}.",
                    "why": "The busiest exhibit in the reference set runs exactly four and is at the "
                           "limit."})
    if not str(kv.get("base_band") or "").strip():
        out.append({"id": "base-band", "level": "ask",
                    "what": "No base band — no tagline, footnote or care box.",
                    "why": "The base band is where the tagline locks and where the mandatories live. "
                           "Its position is the same on every piece in the kit."})
    if not str(kv.get("mandatories") or "").strip():
        out.append({"id": "mandatories", "level": "block",
                    "what": "No mandatories named.",
                    "why": "Veg mark, FSSAI and the licence number are statutory, and every claim above "
                           "them needs its footnote. POS is the piece that gets photographed and "
                           "complained about."})
    for claim in (kv.get("claims") or []):
        if isinstance(claim, dict) and not str(claim.get("source") or "").strip():
            out.append({"id": "claim", "level": "block",
                        "what": f"'{str(claim.get('text') or '')[:60]}' has no source.",
                        "why": "A percentage, a 'No. 1', a clinical claim or a comparison goes on POS "
                               "only with its source and its footnote."})
    return out


# --- drafting the layer spec ---------------------------------------------------------------------

def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def _skill_instructions() -> str:
    """SKILL.md plus the framework references, the way `brief_ai` loads the brief skill.

    Nothing in the codebase loaded this until now — the skill existed and only a person invoking `/posm`
    could reach it, which meant the nine-layer insight was not in any generation the product itself made.
    """
    parts = [_read(os.path.join(_SKILL, "SKILL.md"))]
    for r in _REFS:
        txt = _read(os.path.join(_SKILL, "references", r))
        if txt:
            parts.append(f"\n\n===== reference: {r} =====\n{txt}")
    return "\n".join(p for p in parts if p)


def skill_present() -> bool:
    return os.path.exists(os.path.join(_SKILL, "SKILL.md"))


_OUTPUT_CONTRACT = """
=====  YOUR OUTPUT  =====
Return ONLY a single JSON object, no prose and no markdown fences:

{
  "build": "layered" | "photographic",
  "why_photographic": string,        // required and only if build is photographic; why the SCENE is the argument
  "hero_type": one of: {heroes},
  "why_hero": string,                // why this type, and what it rules out
  "field": one of: {fields},
  "field_note": string,              // which colours, which zone carries type
  "hero_brief": string,              // the subject described PHYSICALLY, for an isolated cut-out on white.
                                     // No environment, no set, no floor, no lettering on anything.
  "hero_crop": "head-and-shoulders" | "three-quarter" | "full-figure" | "object",
  "pack_note": string,               // angle, size as a % of frame height, position, how it overlaps the hero
  "type_position": one of: {positions},
  "headline": string,                // THE EXACT WORDS SUPPLIED BELOW. Do not rewrite them.
  "headline_emphasis": string,       // which word or phrase is set large; the rest is smaller
  "devices": [ up to 3 of: {devices} ],
  "support": [ up to 4 strings, three words or fewer each ],
  "base_band": string,               // tagline, footnote strip, care or contact box
  "mandatories": string,             // veg mark, FSSAI, licence number, and the footnote for any claim
  "line_short": string,              // 3-6 words for the distant formats, WRITTEN FROM THE SAME
                                     // PROPOSITION, not truncated from the headline
  "claims": [ { "text": string, "source": string } ],   // [] if the piece makes no claim
  "missing": [ string ]              // every dimension, mandatory or claim source you had to assume
}
""".strip()


def _word(w: str) -> str:
    """One word, stripped of the punctuation that makes a comparison lie."""
    return "".join(c for c in str(w).lower() if c.isalnum())


def _ask(prompt: str, max_tokens: int = 3000) -> tuple[dict | None, str]:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None, "no key"
    return jsonout.ask_json(prompt, max_tokens=max_tokens)


def draft(stands_on_text: str, source: str = "", *, brand: str = "", house_ctx: str = "",
          formats: list[str] | tuple[str, ...] = (), palette: str = "",
          steer: str = "") -> tuple[dict | None, str]:
    """Draft the key visual as a layer spec. Returns `(spec, note)`.

    **Refuses on an empty proposition rather than inventing one.** POS is an expression of an idea, and
    if there is no idea there is nothing to express — the honest answer is to say what has to be settled
    first, not to produce a competent piece that could be any brand in the category.

    **The words are supplied, never generated.** The headline is passed in from the spine — the
    platform's POSM expression, then its line, then the house's POSM message, then the core — and the
    model is told to place it, not to write it. That rule is stronger than typography: a design tool sets
    Devanagari correctly and will still happily invent a third line that is not a word in any language.
    Every word on the returned spec is checked back against what went in.
    """
    text = str(stands_on_text or "").strip()
    if not text:
        return None, ("Nothing to express. Adopt an idea platform, choose a house message, or write a "
                      "line — POS is an expression of an idea and there is no idea yet.")
    if not skill_present():
        return None, "The POSM skill is not installed on this server."

    fmt_lines = "\n".join(
        f"  {f}: {FORMATS[f]['label']} · {FORMATS[f].get('ratio') or 'measured'} · read at "
        f"{FORMATS[f]['read_at']}m · tier {tier_for(f)} · re-flow {reflow(f)['band']}"
        for f in formats if f in FORMATS)

    # Token replacement rather than `%` or `.format()`: the contract is prose containing literal braces
    # and a literal per-cent sign ("size as a % of frame height"), and both formatting styles choke on
    # their own punctuation appearing in the text. This one cannot.
    contract = _OUTPUT_CONTRACT
    for token, value in (("{heroes}", " | ".join(HERO_TYPES)),
                         ("{fields}", " | ".join(FIELD_DIVISIONS)),
                         ("{positions}", " | ".join(TYPE_POSITIONS)),
                         ("{devices}", " | ".join(TYPE_DEVICES))):
        contract = contract.replace(token, value)

    prompt = "\n\n".join(p for p in [
        _skill_instructions(),
        f"=====  THE BRAND  =====\n{brand or 'this brand'}" + (f"\nPalette: {palette}" if palette else ""),
        f"=====  THE STRATEGY  =====\n{house_ctx}" if house_ctx else "",
        f"=====  WHAT THIS STANDS ON ({source or 'the spine'})  =====\n{text}\n\n"
        "These are THE EXACT WORDS for the headline. Place them; do not rewrite, extend or improve "
        "them. If they are too long for a distant format, write `line_short` from the same proposition "
        "— a truncated line loses the verb and becomes a label.",
        f"=====  THE KIT  =====\n{fmt_lines}\n\nApply the crop gate before choosing the hero: a hero "
        "that cannot survive the widest and smallest formats in this list is dropped on those pieces, "
        "and that is a decision to make now rather than at adaptation." if fmt_lines else "",
        f"=====  STEER  =====\n{steer}" if str(steer or "").strip() else "",
        contract,
    ] if p)

    data, err = _ask(prompt, 3000)
    if not data:
        return None, ("No generation available — add ANTHROPIC_API_KEY." if err == "no key"
                      else f"The key visual could not be drafted: {err}.")

    hero = str(data.get("hero_type") or "").strip()
    field = str(data.get("field") or "").strip()
    pos = str(data.get("type_position") or "").strip()
    out = {
        "build": "photographic" if str(data.get("build")) == "photographic" else "layered",
        "why_photographic": str(data.get("why_photographic") or "").strip(),
        "hero_type": hero if hero in HERO_TYPES else "",
        "why_hero": str(data.get("why_hero") or "").strip(),
        "field": field if field in FIELD_DIVISIONS else "",
        "field_note": str(data.get("field_note") or "").strip(),
        "hero_brief": str(data.get("hero_brief") or "").strip(),
        "hero_crop": str(data.get("hero_crop") or "").strip(),
        "pack_note": str(data.get("pack_note") or "").strip(),
        "type_position": pos if pos in TYPE_POSITIONS else "type-locked-base",
        "headline": str(data.get("headline") or "").strip(),
        "headline_emphasis": str(data.get("headline_emphasis") or "").strip(),
        "devices": [d for d in (data.get("devices") or []) if d in TYPE_DEVICES][:3],
        "support": [str(s).strip() for s in (data.get("support") or []) if str(s).strip()][:SUPPORT_MAX],
        "base_band": str(data.get("base_band") or "").strip(),
        "mandatories": str(data.get("mandatories") or "").strip(),
        "line_short": str(data.get("line_short") or "").strip(),
        "claims": [{"text": str((c or {}).get("text") or "").strip(),
                    "source": str((c or {}).get("source") or "").strip()}
                   for c in (data.get("claims") or []) if isinstance(c, dict)],
        "missing": [str(m).strip() for m in (data.get("missing") or []) if str(m).strip()],
        "stands_on": {"text": text, "source": source},
    }

    # Read every word back against what was supplied.
    #
    # The check is for words ADDED, not for the text differing. A platform sentence is thirty words long
    # and a headline is nine, so any usable draft selects from it — flagging that would fire on every
    # draft and be ignored within a day. What must never happen is a word appearing on the piece that
    # nobody wrote, which is the failure the supplied-words rule exists to prevent: a design tool sets
    # Devanagari perfectly and will still extend a headline with a third line that is not a word in any
    # language. So the defect is `returned - supplied`, and it is reported rather than corrected,
    # because which wording is right is not ours to decide.
    if out["headline"]:
        supplied = {_word(w) for w in text.split()}
        added = [w for w in out["headline"].split() if _word(w) and _word(w) not in supplied]
        if added:
            out["headline_added_words"] = {"supplied": text, "returned": out["headline"],
                                           "added": added}

    findings = spec_findings(out)
    if formats:
        findings += kit(list(formats), line=out["headline"], short_line=out["line_short"],
                        field=out["field"], hero=out["hero_type"],
                        type_position=out["type_position"])["findings"]
    out["findings"] = findings
    return out, f"Drafted against {source or 'the spine'}."


def status() -> dict:
    """Everything a screen needs to render its choices from data rather than from a hard-coded list."""
    return {
        "layers": list(LAYERS),
        "builds": BUILDS,
        "formats": {k: {**v, "mm": list(v["mm"]) if v.get("mm") else None,
                        "note": v.get("trap", ""),
                        "cap_height_mm": cap_height_mm(k),
                        "cap_height_pct": round(cap_fraction(k) * 100, 1),
                        "words": list(words_allowed(float(v.get("read_at") or 2.0))),
                        "delta": aspect_delta(k), "reflow": reflow(k)["band"]}
                    for k, v in FORMATS.items()},
        "families": FAMILIES,
        "kits": KIT_PRESETS,
        "hero_types": HERO_TYPES,
        "field_divisions": FIELD_DIVISIONS,
        "type_devices": TYPE_DEVICES,
        "type_positions": TYPE_POSITIONS,
        "tiers": {k: {**v, "dropped": list(v["dropped"])} for k, v in TIERS.items()},
        "drop_order": list(DROP_ORDER),
        "never_dropped": list(NEVER_DROPPED),
        "support_max": SUPPORT_MAX,
        "master_ratio": MASTER_RATIO,
        "skill": skill_present(),
        "library": gate(),
    }
