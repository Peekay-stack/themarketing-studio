"""strategy.py — the messaging house: an option space you narrow, not a document you accept.

A house is a tree. Every node holds several genuinely different options; a person chooses; the layers
below are then generated *against that choice*. That order matters — generating the whole house at
once produces something internally consistent and strategically arbitrary, because nothing was ever
decided, only written.

Two mechanics carry the weight:

**Cascade.** Choosing at a node changes what its children should say. A child generated under a
different parent is stale — the same problem as a storyboard frame rendered for a scene that has
since been rewritten, and solved the same way: each node records the signature of the choices above
it, and any mismatch is reported rather than quietly left in place.

**Sourcing.** Every reason-to-believe and proof point is marked with where it came from. A fact from
the brief or the signed library is evidence; anything the model supplied is marked unsourced and has
to be accepted by a person before the house can be called finished. This is the difference between
a strategy document and a plausible one.

The layers are in LAYERS below. The lifestyle-and-culture layer is the expressive bridge: the signs
the brand owns and repeats, which is what keeps a film and a shelf strip recognisably the same brand.
"""
from __future__ import annotations

import hashlib
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
import tenancy

# Resolved through tenancy so one deployment can hold several companies. The name is kept
# so every reader in this module is unchanged.
HOUSE_DIR = tenancy.dir("houses")
_SKILL = os.path.join(os.path.dirname(__file__), "strategy_skill")

# The house, in order. `parents` drives the cascade: a node is stale when any parent's choice moved.
LAYERS: list[dict] = [
    {"id": "core", "label": "Core message", "parents": [], "want": 4,
     "asks": "One sayable line that carries the SMP. Not a restatement of it."},
    {"id": "emotional", "label": "Emotional message", "parents": ["core"], "want": 4,
     "asks": "What the buyer feels is true about themselves when this is true."},
    {"id": "functional", "label": "Functional message", "parents": ["core"], "want": 4,
     "asks": "What the product demonstrably does. Plain, checkable."},
    {"id": "rtb_emotional", "label": "Emotional RTBs", "parents": ["core", "emotional"], "want": 5,
     "asks": "Why the feeling is EARNED — behaviour, heritage, consistency over time."},
    {"id": "rtb_functional", "label": "Functional RTBs", "parents": ["core", "functional"], "want": 5,
     "asks": "Facts about the product, process or sourcing that make the claim true."},
    # The missing rung. Everything above is a set of truths sitting side by side with nothing joining
    # them, so nobody can say which fact licenses which feeling — and a campaign then gets built on a
    # leap no layer records. A bridge is the "so what does that mean for me" step between a product
    # fact and a feeling about oneself. One or two of them per path; more than two and the ladder has
    # stopped being an argument.
    {"id": "bridge", "label": "Bridges (functional → emotional)",
     "parents": ["functional", "rtb_functional", "emotional"], "want": 4,
     "asks": ("The step between a product fact and a feeling: what the fact MEANS for the buyer. "
              "Where a bridge divides, write the divisions after a colon — 'Complete nutrition for "
              "development: cognitive, physical, social'. Each division becomes a separate execution "
              "carrying fresh proof instead of a repeat, so the colon is what gives a campaign its "
              "grid. A bridge that does not divide still works; it just yields one column.")},
    {"id": "proof", "label": "Proof & demo propositions",
     "parents": ["core", "rtb_emotional", "rtb_functional"], "want": 5,
     "asks": "What can be SHOWN — a filmable, demonstrable or measurable act."},
    {"id": "culture", "label": "Lifestyle & culture",
     "parents": ["core", "emotional"], "want": 6,
     "asks": ("The signs the brand owns and repeats. Give a spread across occasions, rituals, "
              "codes, idiom, iconography, and what to AVOID — tag each option with which it is.")},
]
LAYER_BY_ID = {l["id"]: l for l in LAYERS}

# Layers no longer asked here, and where the question went instead. Same discipline as
# `ideas.RETIRED_TESTS`: nothing is deleted silently, and a reader of an older house can find out why a
# section they remember is no longer on screen.
#
# `medium` asked "the same message re-expressed for what each medium can actually do", and that framing
# was wrong twice over. It asked the question **before there was an idea** — so the answer was a guess —
# and then the producers resolved platform-first, which meant the seven paragraphs a person chose here
# were overridden the moment a platform was adopted. Heritage's house said POS material was *"roz taaza,
# roz shakti"* while its platform said *"500 checked this before you"*: two POS lines in one strategy,
# and only the platform's was ever read by anything.
#
# **The content is not lost.** `status()` still returns it under `retired_layers`, the stored node stays
# on disk untouched, and `campaign.jobs()` folds each chosen line onto the medium it now belongs to — so
# it appears in the jobs table beside the role that explains it, which is the only place a medium is
# named now.
RETIRED_LAYERS: dict[str, dict] = {
    "medium": {
        "label": "Message by medium",
        "went": "the jobs table — campaign.jobs(), one row per medium",
        "why": "It asked what each medium makes before there was an idea to express, and the producers "
               "then read the platform's expression instead. Asking it once, after the idea, is the "
               "whole change.",
        "asks": ("The same message re-expressed for what each medium can actually do — digital, "
                 "social, TV, OOH, POSM, on-ground. Tag each option with its medium. Not a truncation: "
                 "a shelf strip and a promoter's opening line are different acts of communication."),
    },
}


def layer_label(layer_id: str) -> str:
    """A layer's label whether it is live or retired, so old stored content can still be named."""
    lid = str(layer_id or "")
    if lid in LAYER_BY_ID:
        return LAYER_BY_ID[lid]["label"]
    return (RETIRED_LAYERS.get(lid) or {}).get("label") or lid

# The culture layer's own kinds — a spread across these is what makes it usable downstream.
CULTURE_KINDS = ("occasion", "ritual", "code", "idiom", "iconography", "avoid")
# `trade` is here because the trade is an audience, not a channel for reaching consumers. A distributor
# and a kirana owner hear an argument about margin, rate of sale and working capital; borrowing the
# consumer line for them is the most common way a good campaign dies at the counter.
# Defined in media.py, which is now the only file that says what a medium is. Identical value —
# this is a re-point, not a change. The target taxonomy lives there too, defined and not yet switched on.
MEDIA = media.LEGACY_STRATEGY_MEDIA

MIN_RTBS = 2          # a message with one reason to believe is an assertion

# Shown before anyone starts a house, and printed at the top of every download. Said plainly and once,
# because the failure it prevents is expensive and silent: somebody spends an afternoon rewriting the
# Word file, sends it back, and expects the portal to know. The portal is the document of record; the
# .docx is a copy of it and a worksheet for thinking away from the screen.
ROUND_TRIP_CAVEAT = {
    "headline": "This house lives here, not in the Word file.",
    "points": [
        "Every line is editable at any time — rewrite it, replace it, or add your own. Nothing is "
        "locked once chosen.",
        "Rewriting a model suggestion in your own words makes it yours, and clears the unsourced flag "
        "against it. You are the evidence.",
        "You can download the full house as a .docx whenever you like — as a record, or as a worksheet "
        "with space to redo the thinking.",
        "What the download cannot do is come back in. Edits written into the Word file have to be "
        "re-entered here. Nothing is lost, but nothing is imported either.",
    ],
    "worksheet": "Download the worksheet version to reflect away from the screen, then type your "
                 "revisions back in layer by layer.",
}


def split_asks(text: str) -> list[str]:
    """A layer's question, as the list of things it actually asks.

    `asks` is authored as prose here and consumed as prose by the prompts and the Word worksheet — but the
    screen renders it under "What this layer has to answer" as one line per point, and does
    `(L.asks || []).map(...)`. Sending the string meant `.map is not a function`, which is a **whitescreen**:
    the whole app died on the layer that happened to load first.

    Sentence-splitting rather than a one-element list, because the design is a checklist and these strings
    genuinely hold two thoughts — "One sayable line that carries the SMP. Not a restatement of it." reads
    better as two. `asks_text` keeps the prose for everything that wants it.
    """
    s = str(text or "").strip()
    if not s:
        return []
    # Split only where a sentence really ends: full stop, then space, then a capital or a quote. Keeps
    # "e.g." and decimals intact.
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z“\"'])", s)
    return [p.strip() for p in parts if p.strip()]


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


def _path(house_id: str) -> str:
    return os.path.join(HOUSE_DIR, f"{house_id}.json")


def load(house_id: str) -> dict | None:
    try:
        with open(_path(house_id), encoding="utf-8") as fh:
            house = json.load(fh)
    except (OSError, ValueError):
        return None
    return _backfill(house)


def _backfill(house: dict) -> dict:
    """Give an older house the keys a newer LAYERS list expects, in memory only.

    A layer added after a house was written leaves `nodes` without it, and every writer here indexes
    `nodes[layer_id]` directly — so the first person to open an existing house on a new build would
    have hit a KeyError rather than an empty layer. Nothing is saved: the shape is corrected on the
    way out, and the file gains the node the next time somebody writes to it.
    """
    nodes = house.setdefault("nodes", {})
    for l in LAYERS:
        nodes.setdefault(l["id"], {"layer": l["id"], "options": [], "chosen": [],
                                   "sig": "", "generated_under": ""})
    house.setdefault("ladders", [])
    return house


def save(house: dict) -> dict:
    os.makedirs(HOUSE_DIR, exist_ok=True)
    house["updated"] = _now()
    tmp = _path(house["id"]) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(house, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, _path(house["id"]))
    return house


def houses() -> list[dict]:
    """Every house, as the card the Strategy screen draws.

    **Carries the count under three names, and this is not belt-and-braces for its own sake.** The client
    reads `chosen_layers` and falls back to `progress`; this used to send `decided` alone, so a house with
    all eight layers settled rendered as *"0 of 8 layers decided — Not started."* Somebody looking at a
    finished house would reasonably conclude their work had been lost.

    It is the same failure as `status.layers[]` reading `null` for every layer: the client's field names
    and mine had drifted apart, and nothing compared them. `tools/contract.py` only scopes to
    `status.layers[]`, so it could not have caught this one — see the note added there.
    """
    os.makedirs(HOUSE_DIR, exist_ok=True)
    order = [l["id"] for l in LAYERS]
    out = []
    for f in sorted(os.listdir(HOUSE_DIR)):
        if not f.endswith(".json"):
            continue
        h = load(f[:-5])
        if not h:
            continue
        nodes = h.get("nodes", {})
        # Count the LIVE layers, not every node that happens to carry a choice.
        #
        # This counted `nodes.values()`, which includes retired layers — their nodes stay on disk by
        # design. The moment `medium` was retired, a house with all eight layers settled and a stored
        # medium node reported nine decided against a total of eight, so the card said "9 of 9" while the
        # house itself said "8 of 8". Two screens disagreeing about the same house is the exact failure
        # `/grounding` exists to prevent, and it was one subtraction away from being shipped.
        done = sum(1 for lid in order if (nodes.get(lid) or {}).get("chosen"))
        nxt = next((lid for lid in order if not (nodes.get(lid) or {}).get("chosen")), "")
        try:
            blocking = sum(1 for x in validate(h) if x.get("level") == "blocking")
        except Exception:
            blocking = 0
        out.append({
            "id": h["id"], "brand": h.get("brand", ""),
            "project": project_mod.of(h),
            "project_source": h.get("project_source", ""),
            "label": project_mod.label(h),
            "created": h.get("created", ""), "updated": h.get("updated", ""),
            # the count, under every name the screen has ever read it by
            "decided": done, "chosen_layers": done, "progress": done,
            "total_layers": len(order),
            # what to offer next, and what is wrong — both read straight off the card
            "next_layer": nxt, "complete": done >= len(order),
            "blocking": blocking,
            "stale": any(stale(h, lid) for lid in order),
        })
    # Newest first. The screen shows a list and the one you were last in is the one you want.
    out.sort(key=lambda r: r.get("updated", ""), reverse=True)
    return out


def newest_for(brand: str = "") -> dict | None:
    """The most recently touched house for a brand, matched tolerantly. None if there are no houses.

    **Tolerantly** because the same brand is written differently in different places: the profile is
    "Heritage Pure Milk", the house is "Heritage", the brief says "Heritage Foods". An exact match finds
    none of them, and the caller then behaves as though no house exists — which is how a screen with a
    finished house shows nothing standing behind it.

    Falls back to the newest house of any brand when nothing matches, because one house and one brand is
    the overwhelmingly common case and refusing to guess there is worse than guessing.
    """
    rows = houses()
    if not rows:
        return None
    want = str(brand or "").strip().lower()
    if want:
        exact = next((r for r in rows if str(r.get("brand", "")).strip().lower() == want), None)
        if exact:
            return load(exact["id"])
        # Either direction: "Heritage" is inside "Heritage Pure Milk", and vice versa.
        near = next((r for r in rows
                     if (b := str(r.get("brand", "")).strip().lower())
                     and (b in want or want in b)), None)
        if near:
            return load(near["id"])
    return load(rows[0]["id"])


def new_house(brand: str, brief: dict | None = None) -> dict:
    house = {
        "id": uuid.uuid4().hex[:10], "brand": brand or "Brand",
        "brief": brief or {}, "created": _now(), "updated": _now(),
        # The project comes from the brief. It is asked for once, at the earliest point in the spine,
        # and everything downstream takes it from its parent - four names for one campaign is worse
        # than none.
        "project": project_mod.clean((brief or {}).get("project") or ""),
        "nodes": {l["id"]: {"layer": l["id"], "options": [], "chosen": [],
                            "sig": "", "generated_under": ""} for l in LAYERS},
    }
    return save(house)


# --- the cascade -------------------------------------------------------------------------------

def _chosen_text(house: dict, layer_id: str) -> list[str]:
    node = house["nodes"].get(layer_id) or {}
    picked = set(node.get("chosen") or [])
    return [o["text"] for o in node.get("options", []) if o["id"] in picked]


def signature(house: dict, layer_id: str) -> str:
    """A fingerprint of every choice this layer depends on.

    Compared against what a node was generated under, this is what makes staleness detectable rather
    than something someone notices three layers later.
    """
    parents = LAYER_BY_ID[layer_id]["parents"]
    basis = "|".join(f"{p}:{'~'.join(sorted(_chosen_text(house, p)))}" for p in parents)
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def stale(house: dict, layer_id: str) -> bool:
    """Was this node GENERATED under choices that have since moved?

    Only generated content can go stale. A line someone typed themselves is theirs regardless of what
    changed above it — flagging it would nag on every hand-written house and train people to ignore
    the warning, which is the one outcome worse than not having it.
    """
    node = house["nodes"].get(layer_id) or {}
    if not node.get("options") or not node.get("generated_under"):
        return False
    return node["generated_under"] != signature(house, layer_id)


def ready(house: dict, layer_id: str) -> tuple[bool, str]:
    """Can this layer be generated yet? Parents must have been decided first."""
    for p in LAYER_BY_ID[layer_id]["parents"]:
        if not _chosen_text(house, p):
            return False, f"choose {LAYER_BY_ID[p]['label']} first — this layer is written against it"
    return True, ""


def choose(house: dict, layer_id: str, option_ids: list[str]) -> dict:
    node = house["nodes"][layer_id]
    valid = {o["id"] for o in node.get("options", [])}
    node["chosen"] = [i for i in option_ids if i in valid]
    return save(house)


def add_option(house: dict, layer_id: str, text: str, note: str = "",
               source: str = "user", tag: str = "") -> dict:
    """A person's own line. Marked `user`, which counts as sourced — they are the evidence."""
    node = house["nodes"][layer_id]
    node["options"].append({"id": uuid.uuid4().hex[:8], "text": text.strip(),
                            "note": note.strip(), "source": source, "tag": tag,
                            "added": _now()})
    return save(house)


def edit_option(house: dict, layer_id: str, option_id: str, text: str | None = None,
                note: str | None = None, tag: str | None = None) -> dict | None:
    """Change a line that already exists. Returns None if there is no such option.

    **Editing the text re-sources the option to `user`.** That is the whole point of the mechanism: a
    model suggestion someone has rewritten in their own words is now their claim, and the unsourced
    finding against it should clear. Nothing else in the system can distinguish "accepted the model's
    line" from "wrote my own" — this is where that distinction is recorded.

    Editing only the note or the tag leaves `source` alone. Tidying a rationale is not authorship, and
    if it counted as sourcing then straightening a comma would launder an invented fact into evidence.
    """
    node = house["nodes"][layer_id]
    for o in node.get("options", []):
        if o["id"] != option_id:
            continue
        if text is not None and text.strip() and text.strip() != o.get("text"):
            o["text"] = text.strip()
            o["source"] = "user"
            o["edited"] = _now()
        if note is not None:
            o["note"] = note.strip()
        if tag is not None:
            o["tag"] = tag.strip().lower()
        return save(house)
    return None


def drop_option(house: dict, layer_id: str, option_id: str) -> dict:
    node = house["nodes"][layer_id]
    node["options"] = [o for o in node["options"] if o["id"] != option_id]
    node["chosen"] = [c for c in node.get("chosen", []) if c != option_id]
    return save(house)


# --- the ladder: which fact licenses which feeling ---------------------------------------------
#
# Stored as ONE array of paths on the house — `ladders: [{id, f, b1, b2, e}]`. That is the whole
# structure. There is no graph object and no second store, because the interesting properties are all
# emergent from a list of paths:
#
#   * many-to-many        — two entries sharing an `e` are two routes to the same feeling
#   * robustness          — count the distinct `f` reaching an `e`; one is fragile
#   * the proof axis      — read the enumeration off the bridge the path goes through
#
# `f` may name an option in either functional layer and `e` in either emotional layer, because the rung
# a person starts from is their judgement, not ours: some ladders start at the hard fact
# (rtb_functional) and some at the claim built on it (functional).

LADDER_FROM = ("rtb_functional", "functional")
LADDER_TO = ("emotional", "rtb_emotional")

# A bridge is a rung, not a paragraph. Enforced on the way out of the drafter rather than left to the
# prompt, which reliably overspends once it is also being asked for a proof axis.
BRIDGE_MAX_WORDS = 12


def find_option(house: dict, option_id: str, layers: tuple = ()) -> tuple[str, dict] | None:
    """(layer_id, option) for an option id anywhere in the house, or None."""
    if not option_id:
        return None
    for lid in (layers or tuple(l["id"] for l in LAYERS)):
        for o in ((house.get("nodes") or {}).get(lid) or {}).get("options", []):
            if o.get("id") == option_id:
                return lid, o
    return None


def enumerated(text: str) -> list[str]:
    """The divisions a bridge names, or [].

    A bridge that enumerates is worth more than one that does not: each division becomes an execution
    carrying fresh evidence instead of a restatement.

    **The divisions are declared, not inferred from prose, and that is a deliberate retreat.** Parsing
    them out of a sentence looked easy and was wrong in both directions: given *"complete nutrition for
    cognitive, physical and social development"* a plain comma split loses `cognitive` into the lead-in
    clause and returns `social development` with the head-noun still attached — two divisions instead of
    three, both misnamed. The axis decides the whole campaign grid, so a parser that is usually right is
    worse than one that asks.

    So: write the divisions after a **colon or dash** and they are read exactly as given —
    *"Complete nutrition for development: cognitive, physical, social"*. A bare comma list is also read
    (`"cognitive, physical, social"`). Anything else returns [], and the finding says the bridge does
    not divide, which is the honest answer rather than a confident wrong one.
    """
    t = (text or "").strip()
    for sep in ("—", "–", ":", " - "):
        if sep in t:
            t = t.split(sep, 1)[1]
            break
    t = t.replace(" and ", ", ").replace(" & ", ", ")
    parts = [f.strip(" .;:—-") for f in t.split(",")]
    parts = [f for f in parts if f]
    # Every fragment has to be a division. One clause among them means this is prose with commas in it,
    # not a list — so the whole thing is refused rather than partially harvested.
    if len(parts) >= 2 and all(1 <= len(f.split()) <= 2 for f in parts):
        return parts
    return []


def link(house: dict, f: str, e: str, b1: str = "", b2: str = "") -> tuple[dict | None, str]:
    """Record one path from a functional truth to an emotional one. Returns (house, error)."""
    if not find_option(house, f, LADDER_FROM):
        return None, "That functional truth is not in this house."
    if not find_option(house, e, LADDER_TO):
        return None, "That emotional truth is not in this house."
    for b in (b1, b2):
        if b and not find_option(house, b, ("bridge",)):
            return None, "That bridge is not in this house."
    if b2 and not b1:
        b1, b2 = b2, ""
    rows = house.setdefault("ladders", [])
    if any(r.get("f") == f and r.get("e") == e and r.get("b1", "") == b1 and r.get("b2", "") == b2
           for r in rows):
        return house, "That path is already recorded."
    rows.append({"id": uuid.uuid4().hex[:8], "f": f, "b1": b1, "b2": b2, "e": e, "added": _now()})
    return save(house), ""


def unlink(house: dict, ladder_id: str) -> dict:
    house["ladders"] = [r for r in house.get("ladders", []) if r.get("id") != ladder_id]
    return save(house)


def link_with_bridge(house: dict, f: str, e: str, bridge_text: str,
                     source: str = "model") -> tuple[dict | None, str]:
    """Create a bridge from text and link the path in one step. Returns (house, error).

    The accept half of `draft_ladders`. A drafted path proposes bridge *words*, not an id, because the
    rung usually does not exist yet — so accepting one has to write the option and the edge together or
    the person is left doing the second half by hand.
    """
    text = (bridge_text or "").strip()
    if not text:
        return link(house, f, e)
    if not find_option(house, f, LADDER_FROM):
        return None, "That functional truth is not in this house."
    if not find_option(house, e, LADDER_TO):
        return None, "That emotional truth is not in this house."
    node = house["nodes"]["bridge"]
    existing = next((o for o in node.get("options", []) if o.get("text", "").strip() == text), None)
    if existing:
        bid = existing["id"]
    else:
        bid = uuid.uuid4().hex[:8]
        node.setdefault("options", []).append({
            "id": bid, "text": text, "note": "", "source": source, "tag": "", "added": _now()})
    if bid not in (node.get("chosen") or []):
        node.setdefault("chosen", []).append(bid)
    return link(house, f, e, bid)


def draft_ladders(house: dict, n: int = 4) -> tuple[list[dict], str]:
    """Candidate paths for somebody to confirm or reject. Returns (candidates, note).

    **Why paths and not bridges.** Asking the generic layer generator for "four bridges" produces rungs
    that read well and connect nothing — measured on the Heritage house it returned four thirty-word
    paragraphs, each one already containing both the fact and the feeling, and none of them dividing. A
    bridge is meaningless on its own: it is the step between two named things, so the unit of generation
    has to be the whole triple.

    It also fixes the screen this layer shipped with. Nobody should be asked to draw a graph from an
    empty three-column panel; the tool knows the truths already and can propose the edges.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return [], "No ANTHROPIC_API_KEY — paths can still be built by hand from the columns."

    def picked(layers):
        out = []
        for lid in layers:
            node = (house.get("nodes") or {}).get(lid) or {}
            chosen = set(node.get("chosen") or [])
            out += [(o["id"], o.get("text", "")) for o in node.get("options", []) if o["id"] in chosen]
        return out

    F, E = picked(LADDER_FROM), picked(LADDER_TO)
    if not F or not E:
        return [], ("Choose at least one functional and one emotional truth first — a path needs two "
                    "ends before it can have a middle.")

    have = {(r.get("f"), r.get("e")) for r in house.get("ladders", [])}
    fl = "\n".join(f"  {i} · {t}" for i, t in F)
    el = "\n".join(f"  {i} · {t}" for i, t in E)
    already = ("\nAlready recorded, do not repeat these pairings:\n"
               + "\n".join(f"  {a} -> {b}" for a, b in sorted(have)) if have else "")

    prompt = (
        f"You are laddering a brand's messaging house for {house.get('brand') or 'this brand'}.\n\n"
        "A LADDER PATH joins one functional truth to one emotional truth through a BRIDGE — the step "
        "that says what the fact MEANS for the buyer. Means-end laddering: attribute, consequence, "
        "value.\n\n"
        f"FUNCTIONAL TRUTHS (the `f` end — use the id exactly):\n{fl}\n\n"
        f"EMOTIONAL TRUTHS (the `e` end — use the id exactly):\n{el}\n"
        f"{already}\n\n"
        f"Propose {n} paths. Rules, and each one is a rejection condition:\n"
        "1. THE BRIDGE IS AT MOST 12 WORDS. It is a rung, not a paragraph.\n"
        "2. THE BRIDGE MUST NOT RESTATE EITHER END. If it contains the fact or the feeling it is a "
        "compressed summary of the ladder, not a step inside it, and it connects nothing. Write only "
        "the middle.\n"
        "3. PREFER A BRIDGE THAT DIVIDES, and write the divisions after a COLON — "
        "'Complete nutrition for development: cognitive, physical, social'. Two to four divisions.\n"
        "   THE TEST FOR A DIVISION IS EVIDENCE, NOT WORDS: each one must be provable by DIFFERENT "
        "evidence from the others, because each becomes a separate execution that has to say something "
        "new. 'cognitive, physical, social' passes — three different studies, three different "
        "demonstrations. These all FAIL and will be rejected:\n"
        "     · synonyms — 'no surprises, no doubts' is one division written twice\n"
        "     · alliteration for its own sake — 'cold, checked, controlled'\n"
        "     · restating the mechanism — 'eyes, hands, standards' describes how the check happens, "
        "not different things it proves\n"
        "   If the bridge has no genuine axis, DO NOT invent one to satisfy this rule. Write the bridge "
        "with no colon. One honest column beats three fake ones.\n"
        "4. SPREAD THE PAIRINGS. Do not send the same functional truth four times. Where one emotional "
        "truth can honestly be reached from two different functional truths, show both — that is what "
        "makes a campaign survive a competitor matching one of its facts.\n"
        "5. Do not invent a truth that is not in the lists above.\n\n"
        'Return ONLY JSON: {"paths":[{"f":"<id>","e":"<id>","bridge":"the rung, <=12 words, '
        'divisions after a colon","why":"one sentence on what this path lets the brand argue"}]}')

    data, err = jsonout.ask_json(prompt, max_tokens=1800)
    if data is None:
        return [], f"Generation failed: {err}"

    ftext, etext = dict(F), dict(E)
    out = []
    for p in (data.get("paths") or []):
        f, e = str(p.get("f") or "").strip(), str(p.get("e") or "").strip()
        bridge = str(p.get("bridge") or "").strip()
        if f not in ftext or e not in etext or not bridge:
            continue                      # a hallucinated id is dropped, not repaired
        words = len(bridge.split())
        out.append({"f": f, "f_text": ftext[f], "e": e, "e_text": etext[e],
                    "bridge": bridge, "divides": enumerated(bridge),
                    "words": words,
                    # Length is checked here rather than trusted to the prompt. Tightening the axis rule
                    # made the model spend its words on the divisions and quietly blow the 12-word
                    # budget — flagged, not dropped, because an over-long bridge is usually one edit
                    # away from a good one and throwing it out loses the pairing too.
                    "long": words > BRIDGE_MAX_WORDS,
                    "why": str(p.get("why") or "").strip(),
                    "already": (f, e) in have})
    if not out:
        return [], "Nothing usable came back — every path named a truth that is not in this house."
    n_div = sum(1 for p in out if p["divides"])
    n_long = sum(1 for p in out if p["long"])
    bits = [f"{len(out)} path(s); {n_div} carry a proof axis."]
    if n_long:
        bits.append(f"{n_long} run over {BRIDGE_MAX_WORDS} words — trim before recording.")
    # The axis is the part a person has to judge, and the tool cannot. Measured on this house the
    # generator will satisfy the colon rule with synonyms ('no surprises, no doubts') or alliteration
    # ('cold, checked, controlled') that read like an axis and prove nothing new. The only real test is
    # whether each division needs DIFFERENT evidence, and that is a judgement.
    bits.append("Check each axis yourself: if two divisions would be proved by the same evidence, it is "
                "one division written twice, and the campaign grid built on it will repeat itself.")
    bits.append("A generated ladder is a hypothesis — laddering is properly done by asking a real buyer "
                "'why does that matter to you?' five times.")
    return out, " ".join(bits)


def path(house: dict, ladder_id: str) -> dict | None:
    """One path, hydrated with the text at each rung. None if it no longer resolves."""
    row = next((r for r in house.get("ladders", []) if r.get("id") == ladder_id), None)
    return _hydrate(house, row) if row else None


def _hydrate(house: dict, row: dict) -> dict | None:
    got = find_option(house, row.get("f"), LADDER_FROM)
    end = find_option(house, row.get("e"), LADDER_TO)
    if not got or not end:
        return None                      # an option was deleted under it; the finding reports this
    rungs = []
    for key in ("b1", "b2"):
        b = find_option(house, row.get(key), ("bridge",))
        if b:
            rungs.append({"id": row[key], "text": b[1].get("text", ""),
                          "divides": enumerated(b[1].get("text", ""))})
    return {"id": row.get("id"), "f": {"id": row["f"], "layer": got[0], "text": got[1].get("text", "")},
            "bridges": rungs,
            "e": {"id": row["e"], "layer": end[0], "text": end[1].get("text", "")},
            # The axis is the LAST bridge's enumeration — the rung nearest the feeling is the one whose
            # divisions a campaign actually splits its executions across.
            "axis": (rungs[-1]["divides"] if rungs else [])}


def paths(house: dict) -> list[dict]:
    """Every path that still resolves, hydrated."""
    return [p for p in (_hydrate(house, r) for r in house.get("ladders", [])) if p]


def routes_to(house: dict, emotional_id: str) -> list[str]:
    """The distinct functional truths that reach one emotional truth. One route is fragile."""
    return sorted({r["f"] for r in house.get("ladders", []) if r.get("e") == emotional_id})


# --- validation: the discipline, made checkable ------------------------------------------------

def validate(house: dict) -> list[dict]:
    """Everything wrong with this house, as findings a person can act on.

    Deliberately blunt. A house that looks finished and is not is worse than one that admits it,
    because the first one stops being checked.
    """
    out: list[dict] = []

    def add(level, layer, msg):
        out.append({"level": level, "layer": layer, "detail": msg})

    for l in LAYERS:
        node = house["nodes"].get(l["id"]) or {}
        picked = node.get("chosen") or []
        # "N options generated, none chosen" was a finding here and it should not have been. The layer
        # rail already says it, the option cards show it, and `n_options`/`n_chosen` carry it for any
        # reviewer view — so as a finding it was pure duplication, and it arrived as a band above the
        # layer somebody was in the middle of working on. Findings are for things a person has to act
        # on, not for narrating the screen back to them.
        if stale(house, l["id"]):
            add("stale", l["id"],
                f"{l['label']} was written under different choices above it — regenerate or re-pick")

    # Proof before claim: each side needs its RTBs.
    for msg_layer, rtb_layer in (("emotional", "rtb_emotional"), ("functional", "rtb_functional")):
        if _chosen_text(house, msg_layer):
            n = len(_chosen_text(house, rtb_layer))
            if n < MIN_RTBS:
                add("blocking", rtb_layer,
                    f"{LAYER_BY_ID[msg_layer]['label']} has {n} reason(s) to believe. "
                    f"Under {MIN_RTBS} it is an assertion, not a claim.")

    # Sourced, not invented.
    for l in ("rtb_emotional", "rtb_functional", "proof"):
        node = house["nodes"].get(l) or {}
        picked = {o["id"] for o in node.get("options", [])} & set(node.get("chosen") or [])
        unsourced = [o for o in node.get("options", [])
                     if o["id"] in picked and o.get("source") == "model"]
        if unsourced:
            add("unsourced", l,
                f"{len(unsourced)} chosen item(s) in {LAYER_BY_ID[l]['label']} came from the model "
                f"and trace to nothing in the brief or library — accept them explicitly or drop them")

    # The culture layer earns its place only if it spreads.
    culture = house["nodes"].get("culture") or {}
    tags = {o.get("tag") for o in culture.get("options", []) if o["id"] in set(culture.get("chosen") or [])}
    if culture.get("chosen"):
        missing = [k for k in ("occasion", "ritual", "avoid") if k not in tags]
        if missing:
            add("open", "culture",
                f"Lifestyle & culture has nothing chosen for: {', '.join(missing)}. "
                f"Occasions say when, rituals are the most ownable, and 'avoid' saves the most work.")

    # The two medium findings are gone with the layer they judged.
    #
    # They asked whether every medium had a message and whether each named its occasion — both worth
    # asking, and both now unanswerable here: the layer is retired, so a person reading "no message yet
    # for: influencer" on the house screen has no field to type it into. **A finding nobody can act on is
    # worse than no finding**, because it teaches people to ignore the findings list.
    #
    # `campaign.jobs_findings()` asks the coverage question properly instead — against all ten leaves
    # rather than the old seven, beside the row you would fill in, and reporting an empty cell as the
    # decision nobody has taken rather than as a house defect.

    out.extend(ladder_findings(house))
    return out


def ladder_findings(house: dict) -> list[dict]:
    """What the ladder says is wrong. Separate so the campaign layer can ask for these alone.

    All five are computed from the paths — there is no new judgement to collect, which is the point.
    Three of the idea platform's five hand-answered tests are absorbed here: *is it true* becomes
    structural (a platform on a path stands on something by construction) and *does every channel get
    something to do* becomes the campaign's role table.
    """
    out: list[dict] = []

    def add(level, msg):
        out.append({"level": level, "layer": "bridge", "detail": msg})

    rows = house.get("ladders", [])
    chosen_f = {o["id"] for lid in LADDER_FROM
                for o in ((house.get("nodes") or {}).get(lid) or {}).get("options", [])
                if o["id"] in set(((house.get("nodes") or {}).get(lid) or {}).get("chosen") or [])}
    chosen_e = {o["id"] for lid in LADDER_TO
                for o in ((house.get("nodes") or {}).get(lid) or {}).get("options", [])
                if o["id"] in set(((house.get("nodes") or {}).get(lid) or {}).get("chosen") or [])}
    if not (chosen_f and chosen_e):
        return out                        # nothing to ladder between yet; the rail already says so

    # A path whose rungs were deleted under it. Reported rather than silently dropped, because the
    # person who deleted the option has no idea a campaign was standing on it.
    dead = [r for r in rows if _hydrate(house, r) is None]
    if dead:
        add("blocking", f"{len(dead)} ladder path(s) point at options that have been deleted — "
                        f"relink or remove them")

    linked_e = {r["e"] for r in rows}
    linked_f = {r["f"] for r in rows}

    # An emotional truth nothing reaches is the claim this whole discipline exists to catch.
    orphan_e = chosen_e - linked_e
    if orphan_e:
        add("blocking", f"{len(orphan_e)} chosen emotional truth(s) have no functional route to them — "
                        f"unlicensed, and a campaign built on one is a leap with nothing under it")

    # A functional truth nothing ladders up from is a spec-sheet line.
    orphan_f = chosen_f - linked_f
    if orphan_f:
        add("open", f"{len(orphan_f)} chosen functional truth(s) ladder up to nothing — true, and "
                    f"nobody will care until it means something to the buyer")

    # One route is fragile: match the claim or challenge it and the campaign dies with it.
    fragile = [e for e in linked_e if len(routes_to(house, e)) == 1]
    if fragile:
        add("open", f"{len(fragile)} emotional truth(s) are reached by ONE functional route only — "
                    f"a competitor matching that one fact takes the whole campaign with it")

    # No bridge, or a bridge that will not divide: the campaign gets slots but no proof axis, so every
    # execution restates the same evidence.
    for p in paths(house):
        if not p["bridges"]:
            add("open", f"Path to “{p['e']['text'][:48]}…” has no bridge — the jump from "
                        f"fact to feeling is unstated, so nobody can check it")
        elif not p["axis"]:
            add("open", f"The bridge on the path to “{p['e']['text'][:40]}…” does not "
                        f"divide, so a campaign off it has no proof axis and every execution will "
                        f"repeat the same evidence")
    return out


def status(house: dict) -> dict:
    """The house's own account of itself — what is decided, what is open, what is stale."""
    layers = []
    for l in LAYERS:
        node = house["nodes"].get(l["id"]) or {}
        ok, why = ready(house, l["id"])
        # `options` and `chosen` carry the actual items, not counts.
        #
        # They used to be integers, and that single decision cost a day: the screen reads
        # `L.options` to draw the option cards and `(ls.options||[]).length` for the rail, so an integer
        # rendered no cards *and* made the rail say "nothing offered yet" — while the findings, which
        # counted the same node directly, correctly reported four options. A layer that has generated
        # work and claims to be empty is the worst kind of wrong, because it looks like data loss.
        #
        # Counts are still available as `n_options` / `n_chosen` for anything that wants them cheaply.
        # `id`, `layer` and `key` all carry the layer's name.
        #
        # The screen finds a layer with `ls.find(x => (x.layer || x.name || x.key) === key)`. Sending only
        # `id` meant that returned null for **every layer of every house and plan** — so no option card
        # could render, the rail said "nothing offered yet" over nine saved options, and no click could
        # resolve which layer it belonged to. The whole screen was inert while the data was intact.
        #
        # One alias is cheaper than a contract argument, and this is the third time a single-name field
        # has cost a day: `id`/`brief_id`, `brand`/`name`, and now this.
        layers.append({
            "id": l["id"], "layer": l["id"], "key": l["id"],
            "label": l["label"], "name": l["label"],
            "asks": split_asks(l["asks"]), "asks_text": l["asks"],
            "options": node.get("options", []),
            "chosen": node.get("chosen", []),
            "n_options": len(node.get("options", [])),
            "n_chosen": len(node.get("chosen", [])),
            "stale": stale(house, l["id"]),
            "ready": ok, "blocked_because": why,
            "parents": l["parents"],
        })
    # Retired layers, with whatever this house stored under them. Kept OUT of `layers` so no screen
    # renders them as something still to decide, and kept IN the payload so the content is reachable —
    # the .docx prints it, and a person who chose seven medium lines can still see them.
    retired = []
    for lid, spec in RETIRED_LAYERS.items():
        node = house["nodes"].get(lid) or {}
        if not (node.get("options") or node.get("chosen")):
            continue
        retired.append({
            "id": lid, "layer": lid, "key": lid,
            "label": spec["label"], "name": spec["label"],
            "went": spec["went"], "why": spec["why"],
            "options": node.get("options", []),
            "chosen": node.get("chosen", []),
            "n_options": len(node.get("options", [])),
            "n_chosen": len(node.get("chosen", [])),
        })

    findings = findings_mod.annotate(validate(house), house.get("overrides"))
    live = findings_mod.live_blocking(findings)
    return {
        "id": house["id"], "brand": house.get("brand", ""),
        "updated": house.get("updated", ""),
        "layers": layers,
        "retired_layers": retired,
        "findings": findings,
        "blocking": live,
        "overridden": findings_mod.overridden_count(findings),
        **findings_mod.counts(findings, house.get("overrides")),
        # The ladder, hydrated, so the screen can draw the paths without resolving option ids itself —
        # and `ladder_ends` tells it which options are legal at each end of a new link, so it cannot
        # offer a pairing the backend will refuse.
        "ladders": paths(house),
        "ladder_ends": {"from": list(LADDER_FROM), "to": list(LADDER_TO), "bridge": "bridge"},
        "ladder_fragile": [e for e in {r["e"] for r in house.get("ladders", [])}
                           if len(routes_to(house, e)) == 1],
        # "Finished" means every layer decided AND nothing blocking left standing. Said plainly so
        # nobody has to infer it from a screen full of green ticks. An override counts as cleared
        # because somebody signed for it — and `overridden` above says how many times.
        "complete": all(x["chosen"] for x in layers) and not live,
    }


# --- generation ---------------------------------------------------------------------------------

def _skill_text() -> str:
    parts = []
    for name in ("SKILL.md",):
        p = os.path.join(_SKILL, name)
        if os.path.exists(p):
            parts.append(open(p, encoding="utf-8").read())
    return "\n\n".join(parts)


def _brief_text(house: dict) -> str:
    b = house.get("brief") or {}
    if not b:
        return "(no brief attached — say so in the output rather than inventing one)"
    # ROUND-83 AUDIT: `commObjective`, `competition`, `deliverables`, `budget` and `timeline` are real,
    # correctly-saved brief fields on every format — `keep` simply never asked for them, so the House
    # (the only place a brief becomes prompt text) was generated with no knowledge of any of the five.
    keep = ("businessObjective", "marketingObjective", "commObjective", "background", "targetAudience",
            "consumerInsight", "currentBelief", "desiredBelief", "smp", "rtbs",
            "toneOfVoice", "mandatories", "packHierarchy", "successMetrics",
            "competition", "deliverables", "budget", "timeline",
            "needscopeAnalysis", "smpDefence", "smpUnlocks")
    lines = [f"{k}: {b[k]}" for k in keep if str(b.get(k) or "").strip()]
    return "\n".join(lines) or "(brief is empty)"


def prompt_for(house: dict, layer_id: str, extra: str = "",
               anchors: str = "", rules: str = "", locked: list[dict] | None = None) -> str:
    """The full instruction for one node. Kept as its own function so it can be inspected."""
    l = LAYER_BY_ID[layer_id]
    above = []
    for p in l["parents"]:
        picked = _chosen_text(house, p)
        if picked:
            above.append(f"{LAYER_BY_ID[p]['label']} (CHOSEN — everything you write must serve this):\n"
                         + "\n".join(f"  - {t}" for t in picked))
    # Which tags are already covered, so pressing "Offer options" a second time fills the gaps instead of
    # producing six more of what is already there.
    #
    # `medium` had this and `culture` did not, which is the whole of the reported problem: choose "ritual"
    # in the dropdown, press Offer options, get more occasions. (The dropdown was never wired to
    # generation either — it tags the line *you* write — but even wired it would not have helped, because
    # the model was never told what it had already covered.)
    def _covered(lid: str) -> set[str]:
        node = (house.get("nodes") or {}).get(lid) or {}
        picked = set(node.get("chosen") or [])
        return {str(o.get("tag", "")).lower() for o in node.get("options", [])
                if o["id"] in picked and str(o.get("tag") or "").strip()}

    tag_note = ""
    if layer_id == "culture":
        have = _covered("culture")
        gaps = [k for k in CULTURE_KINDS if k not in have]
        tag_note = (f"\nTag every option with exactly one of: {', '.join(CULTURE_KINDS)}. "
                    f"Give a spread — do not return six occasions.")
        if have:
            tag_note += (f"\nALREADY CHOSEN, so do not offer more of these: {', '.join(sorted(have))}."
                         + (f"\nWRITE FOR THESE KINDS, which have nothing yet: {', '.join(gaps)}. "
                            f"One option each at least, and say in `note` what makes it ownable rather "
                            f"than merely true of the category."
                            if gaps else
                            "\nEvery kind already has something. Offer genuinely better alternatives to "
                            "what is there, and say in `note` what each would replace and why."))
    # The `medium` branch that used to sit here is gone with its layer. It was already unreachable —
    # every caller guards on `layer not in LAYER_BY_ID` first — so this is dead code removed rather than
    # behaviour changed.
    parts = [
        _skill_text(),
        "\n\n---\nTHE BRAND\n" + brandprofile.voice_block(
            brandprofile.resolve(house.get("brief"), house)),
        "\n\n---\nTHE BRIEF\n" + _brief_text(house),
    ]
    if above:
        parts.append("\n\n---\nDECIDED ABOVE\n" + "\n\n".join(above))
    if anchors:
        parts.append("\n\n---\n" + anchors)
    if rules:
        parts.append("\n\n---\n" + rules)
    if locked:
        parts.append("\n\n---\nLOCKED COPY — place verbatim, never paraphrase:\n"
                     + "\n".join(f"  - {c['text']}" for c in locked))
    if extra.strip():
        parts.append("\n\n---\nTHE USER ADDS\n" + extra.strip())
    parts.append(
        f"\n\n---\nNOW WRITE: {l['label']}\n{l['asks']}\n"
        f"Give {l['want']} options that differ on the STRATEGIC BET — what is claimed and to whom — "
        f"not on wording.{tag_note}\n\n"
        'Return ONLY JSON: {"options":[{"text":"...","note":"why this bet, in one line",'
        '"tag":"","source":"brief|library|model"}]}\n'
        'Set source to "brief" or "library" only when it genuinely traces to something given above. '
        'Otherwise "model" — that is not a failure, it is how a person knows what to check.'
    )
    return "\n".join(parts)


def generate(house: dict, layer_id: str, extra: str = "", anchors: str = "",
             rules: str = "", locked: list[dict] | None = None,
             replace: bool = False) -> tuple[dict, str]:
    """Fill a node with options. Returns (house, note). Requires ANTHROPIC_API_KEY."""
    ok, why = ready(house, layer_id)
    if not ok:
        return house, why
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return house, "No ANTHROPIC_API_KEY — the house can still be written by hand."
    prompt = prompt_for(house, layer_id, extra, anchors, rules, locked)
    data, err = jsonout.ask_json(prompt, max_tokens=4000)
    if data is None:
        return house, f"Generation failed: {err}"
    node = house["nodes"][layer_id]
    if replace:
        node["options"], node["chosen"] = [], []
    for o in (data.get("options") or []):
        text = str(o.get("text") or "").strip()
        if not text:
            continue
        src = str(o.get("source") or "model").lower()
        node["options"].append({
            "id": uuid.uuid4().hex[:8], "text": text,
            "note": str(o.get("note") or "").strip(),
            "tag": str(o.get("tag") or "").strip().lower(),
            "source": src if src in ("brief", "library", "user") else "model",
            "added": _now()})
    # Remember what was decided above when this was written — that is what makes staleness visible.
    node["generated_under"] = signature(house, layer_id)
    return save(house), ""
