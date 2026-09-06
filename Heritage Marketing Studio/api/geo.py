"""geo.py — where a campaign runs. States and union territories, and the cities worth naming.

Geography had no home before this module. The plan has objectives, audiences, channels, balance,
phases, measures and governance — and no layer that says *where*. `brandprofile.market` is free text,
the brief templates ask for "demographics, geography, role" in a prose box, and `pr` outlets carry a
free-text `region`. So four screens each held a different sentence about the same fact and none of them
could be counted, filtered or targeted. This is the first definition, not a second one.

Three things it is careful about, each because the alternative is a number that looks right:

**A population is not a targetable audience.** Meta's "Hyderabad" is a place entity with its own
boundary and an optional radius; the Census's Hyderabad is the Municipal Corporation. They are not the
same population and the difference is not small. So a census figure is stored for *prioritisation* —
deciding which cities are worth naming — and the platform's own estimated audience size is stored
separately as `platform_reach`, with no blended field anywhere. Same discipline as `pr.add_outlet`,
which keeps print circulation and digital visitors apart and refuses to add them up.

**Municipal and agglomeration figures must never be mixed.** Kolkata is 4.5 million inside the
Corporation and about 15.9 million as an agglomeration. A list that sorts one against the other is
nonsense that reads as a ranking, so `key_cities` requires a single declared basis and reports who
lacks a figure on it rather than quietly sorting them last.

**Census 2011 is still the only completed count.** Census 2021 was postponed — the first postponement
since 1872 — and Census 2027 enumerates on 1 March 2027. India was 1.21 billion in 2011 and is
estimated above 1.4 billion now, so every seeded figure here is roughly fifteen years and a sixth of a
country out of date. That is stated on the record rather than silently projected: see `POP_BASIS` and
`THRESHOLD_CAVEAT`. A studio may enter newer estimates, and they are labelled as estimates.
"""
from __future__ import annotations

# ISO 3166-2:IN subdivision codes, lowercased. Used rather than invented slugs because they are the
# codes that appear in every other system a client already has.
#
# ⚠ `ml` is MEGHALAYA here. In `pr.LANGUAGES` and in `languages`, `ml` is MALAYALAM — whose state is
# `kl`, Kerala. The two vocabularies are separate parameters in every function below and neither
# accepts the other's keys, so nothing can cross over silently. It is called out because it is the one
# code in this module that means two different things depending on which dictionary you are reading,
# and a future reader deserves to be warned rather than to find out.
#
# `languages` lists the codes this studio actually holds, most-spoken first, and it is the
# MACHINE-READABLE state-to-language mapping. `pr.LANGUAGES[k]["where"]` is a human sentence about the
# same fact; where they disagree, this is the one to trust, and PR should eventually read from here
# rather than keep its own prose. `language_gap` names a state's principal language when the studio has
# no code for it — which is the honest answer to "can we run creative in Manipur", not silence.
ZONES: dict[str, str] = {
    "north": "North", "south": "South", "east": "East", "west": "West",
    "central": "Central", "northeast": "North-east",
}

STATES: dict[str, dict] = {
    # --- states (28) ---
    "ap": {"label": "Andhra Pradesh", "ut": False, "zone": "south", "languages": ["te", "ur", "en"]},
    "ar": {"label": "Arunachal Pradesh", "ut": False, "zone": "northeast", "languages": ["en", "hi"],
           "language_gap": "Nyishi, Adi and Nishi are the languages spoken; the studio holds none."},
    "as": {"label": "Assam", "ut": False, "zone": "northeast", "languages": ["as", "bn", "hi", "en"]},
    "br": {"label": "Bihar", "ut": False, "zone": "east", "languages": ["hi", "ur", "en"]},
    "ct": {"label": "Chhattisgarh", "ut": False, "zone": "central", "languages": ["hi", "en"],
           "language_gap": "Chhattisgarhi is the everyday language; Hindi creative reads as outside."},
    "ga": {"label": "Goa", "ut": False, "zone": "west", "languages": ["mr", "en", "hi"],
           "language_gap": "Konkani is the official language and the studio has no code for it."},
    "gj": {"label": "Gujarat", "ut": False, "zone": "west", "languages": ["gu", "hi", "en"]},
    "hr": {"label": "Haryana", "ut": False, "zone": "north", "languages": ["hi", "pa", "en"]},
    "hp": {"label": "Himachal Pradesh", "ut": False, "zone": "north", "languages": ["hi", "en"]},
    "jh": {"label": "Jharkhand", "ut": False, "zone": "east", "languages": ["hi", "bn", "ur", "en"]},
    "ka": {"label": "Karnataka", "ut": False, "zone": "south", "languages": ["kn", "ur", "en"]},
    "kl": {"label": "Kerala", "ut": False, "zone": "south", "languages": ["ml", "en"]},
    "mp": {"label": "Madhya Pradesh", "ut": False, "zone": "central", "languages": ["hi", "en"]},
    "mh": {"label": "Maharashtra", "ut": False, "zone": "west", "languages": ["mr", "hi", "ur", "en"]},
    "mn": {"label": "Manipur", "ut": False, "zone": "northeast", "languages": ["en", "hi"],
           "language_gap": "Meitei (Manipuri) is the state language; the studio holds no code for it."},
    "ml": {"label": "Meghalaya", "ut": False, "zone": "northeast", "languages": ["en", "bn", "hi"],
           "language_gap": "Khasi and Garo are the spoken languages; English is official."},
    "mz": {"label": "Mizoram", "ut": False, "zone": "northeast", "languages": ["en", "hi"],
           "language_gap": "Mizo is the state language and the studio has no code for it."},
    "nl": {"label": "Nagaland", "ut": False, "zone": "northeast", "languages": ["en", "hi"],
           "language_gap": "English is official; Nagamese is the lingua franca and is not held."},
    "or": {"label": "Odisha", "ut": False, "zone": "east", "languages": ["or", "hi", "en"]},
    "pb": {"label": "Punjab", "ut": False, "zone": "north", "languages": ["pa", "hi", "en"]},
    "rj": {"label": "Rajasthan", "ut": False, "zone": "north", "languages": ["hi", "en"]},
    "sk": {"label": "Sikkim", "ut": False, "zone": "northeast", "languages": ["en", "hi"],
           "language_gap": "Nepali is the principal language and the studio has no code for it."},
    "tn": {"label": "Tamil Nadu", "ut": False, "zone": "south", "languages": ["ta", "en"]},
    "tg": {"label": "Telangana", "ut": False, "zone": "south", "languages": ["te", "ur", "en"]},
    "tr": {"label": "Tripura", "ut": False, "zone": "northeast", "languages": ["bn", "en", "hi"]},
    "up": {"label": "Uttar Pradesh", "ut": False, "zone": "north", "languages": ["hi", "ur", "en"]},
    "uk": {"label": "Uttarakhand", "ut": False, "zone": "north", "languages": ["hi", "en"]},
    "wb": {"label": "West Bengal", "ut": False, "zone": "east", "languages": ["bn", "hi", "en"]},
    # --- union territories (8) ---
    "an": {"label": "Andaman and Nicobar Islands", "ut": True, "zone": "east",
           "languages": ["hi", "bn", "ta", "te", "en"]},
    "ch": {"label": "Chandigarh", "ut": True, "zone": "north", "languages": ["hi", "pa", "en"]},
    "dh": {"label": "Dadra and Nagar Haveli and Daman and Diu", "ut": True, "zone": "west",
           "languages": ["gu", "hi", "mr", "en"]},
    "dl": {"label": "Delhi", "ut": True, "zone": "north", "languages": ["hi", "pa", "ur", "en"],
           "note": "The NCT. Media plans usually mean the wider National Capital Region, which reaches "
                   "into Haryana and Uttar Pradesh — name those states too if that is what is meant."},
    "jk": {"label": "Jammu and Kashmir", "ut": True, "zone": "north", "languages": ["ur", "hi", "en"],
           "language_gap": "Kashmiri and Dogri are the spoken languages and are not held."},
    "la": {"label": "Ladakh", "ut": True, "zone": "north", "languages": ["hi", "ur", "en"],
           "language_gap": "Ladakhi and Balti are the spoken languages and are not held."},
    "ld": {"label": "Lakshadweep", "ut": True, "zone": "south", "languages": ["ml", "en"]},
    "py": {"label": "Puducherry", "ut": True, "zone": "south", "languages": ["ta", "ml", "te", "en"]},
}

# People type the codes they remember, and three of these have two forms in common use. Folded on read
# the way `media.ALIASES` folds legacy medium keys — so a typed `od` resolves rather than being refused
# for a reason the typist would find pedantic.
ALIASES: dict[str, str] = {
    "od": "or",     # Odisha — ISO says OR, the state government's own usage is OD
    "ts": "tg",     # Telangana — ISO says TG, almost everyone writes TS
    "ut": "uk",     # Uttarakhand — ISO says UT, which collides with "union territory"
    "ncr": "dl",    # not the same thing; resolves to Delhi and the note there says why
    "or_": "or",
}

# Basis for a population figure. The rule this vocabulary exists to enforce: a threshold or a ranking
# names ONE basis and reports who lacks a figure on it. Two bases in one list is not a list.
POP_BASIS: dict[str, dict] = {
    "census_2011_city": {
        "label": "Census 2011 — municipal",
        "what": "Population inside the Municipal Corporation boundary, Census of India 2011.",
        "official": True, "year": 2011,
        "caveat": "Fifteen years old. India counted 1.21 billion in 2011 and is estimated above 1.4 "
                  "billion now, and urban growth ran ahead of the national rate — so these figures are "
                  "low, unevenly, and by an amount nobody can state per city until Census 2027.",
    },
    "census_2011_agglomeration": {
        "label": "Census 2011 — urban agglomeration",
        "what": "The continuous built-up area, Census of India 2011. A different and usually much "
                "larger population than the municipal figure for the same city.",
        "official": True, "year": 2011,
        "caveat": "Never mix with municipal figures. Kolkata is 4.5 million municipal and about 15.9 "
                  "million as an agglomeration — a list sorting one against the other is meaningless.",
    },
    "estimate": {
        "label": "Published estimate",
        "what": "A projection from a named publisher for a named year — UN World Urbanization "
                "Prospects, a state planning department, a commercial aggregator.",
        "official": False, "year": None,
        "caveat": "Cite the publisher and the year. Estimates for the same city differ by millions "
                  "depending on whose boundary was used, so the boundary belongs in the source line.",
    },
    "platform_reach": {
        "label": "Platform estimated audience",
        "what": "What Ads Manager says it can reach for a targeted place entity.",
        "official": False, "year": None,
        "caveat": "NOT a population, and not comparable to one. It counts accounts a platform believes "
                  "are in a place it defines its own way, and it moves week to week. It is the "
                  "operative number for buying and the wrong number for prioritising.",
    },
    "entered": {
        "label": "Entered by a person",
        "what": "A figure a client holds — their own retail catchment, a licensed report.",
        "official": False, "year": None,
        "caveat": "Needs a source line naming what it counts, or it cannot be reconciled with anything.",
    },
}

THRESHOLD_CAVEAT = (
    "A 5-lakh cutoff applied to Census 2011 is a 2011 cutoff. Cities that sat below 500,000 then have "
    "very likely crossed it since — India grew from 1.21 billion to an estimated 1.4-billion-plus over "
    "the same period, with urban areas growing faster than that — so this list is short at the bottom "
    "rather than wrong. How short cannot be stated per city without projecting, which this module will "
    "not do. Census 2027 enumerates on 1 March 2027 and is the first count that will settle it. Enter "
    "an estimate for a city you believe qualifies, and it will be counted on that basis."
)

# Seeded from the Census of India 2011, municipal-corporation boundaries, via Wikipedia's compiled
# list. Every figure here is a `census_2011_city` figure.
#
# DELIBERATELY INCOMPLETE, and `SEED_GAP` says exactly where. The same stance as `pr.SEED_OUTLETS`:
# a seed carries what was actually verified, and a list that implies completeness it does not have is
# worse than a short one, because nobody checks a list that looks finished.
_SEED: tuple[tuple[str, str, int], ...] = (
    ("Mumbai", "mh", 12442373), ("Delhi", "dl", 11034555), ("Bengaluru", "ka", 8443675),
    ("Hyderabad", "tg", 6993262), ("Chennai", "tn", 6748026), ("Ahmedabad", "gj", 5577940),
    ("Kolkata", "wb", 4496694), ("Surat", "gj", 4467797), ("Pune", "mh", 3124458),
    ("Jaipur", "rj", 3046163), ("Lucknow", "up", 2817105), ("Kanpur", "up", 2765348),
    ("Nagpur", "mh", 2405665), ("Indore", "mp", 1964086), ("Thane", "mh", 1841488),
    ("Bhopal", "mp", 1798218), ("Visakhapatnam", "ap", 1728128),
    ("Pimpri-Chinchwad", "mh", 1727692), ("Patna", "br", 1684222), ("Vadodara", "gj", 1670806),
    ("Ghaziabad", "up", 1648643), ("Ludhiana", "pb", 1618879), ("Agra", "up", 1585704),
    ("Nashik", "mh", 1486053), ("Faridabad", "hr", 1414050), ("Meerut", "up", 1305429),
    ("Rajkot", "gj", 1286678), ("Kalyan-Dombivli", "mh", 1247327), ("Vasai-Virar", "mh", 1222390),
    ("Varanasi", "up", 1198491),
    # --- the 5-lakh to 9.6-lakh band ---
    ("Chandigarh", "ch", 961587), ("Guwahati", "as", 957352), ("Solapur", "mh", 951558),
    ("Hubli-Dharwad", "ka", 943788), ("Bareilly", "up", 903668), ("Mysore", "ka", 893062),
    ("Moradabad", "up", 887871), ("Gurgaon", "hr", 876969), ("Aligarh", "up", 874408),
    ("Jalandhar", "pb", 862886), ("Tiruchirappalli", "tn", 847387), ("Bhubaneswar", "or", 843402),
    ("Salem", "tn", 829267), ("Mira-Bhayandar", "mh", 809378),
    ("Thiruvananthapuram", "kl", 743691), ("Bhiwandi", "mh", 711329), ("Saharanpur", "up", 705478),
    ("Gorakhpur", "up", 673446), ("Guntur", "ap", 647508), ("Amravati", "mh", 647057),
    ("Bikaner", "rj", 644406), ("Noida", "up", 637272), ("Jamshedpur", "jh", 631364),
    ("Bhilai", "ct", 625700), ("Warangal", "tg", 615998), ("Cuttack", "or", 610189),
    ("Firozabad", "up", 604214), ("Kochi", "kl", 602046), ("Bhavnagar", "gj", 593368),
    ("Dehradun", "uk", 569578), ("Durgapur", "wb", 566517), ("Asansol", "wb", 563917),
    ("Nanded-Waghala", "mh", 550439), ("Kolhapur", "mh", 549236), ("Ajmer", "rj", 542321),
    ("Kalaburagi", "ka", 533587), ("Loni", "up", 516082), ("Ujjain", "mp", 515215),
    ("Siliguri", "wb", 513264), ("Ulhasnagar", "mh", 506098),
)

SEED_SOURCE = ("Census of India 2011, population within Municipal Corporation boundaries, via "
               "Wikipedia's compiled list of cities in India by population")

# The known hole. Two extractions were taken from the source list — the largest cities, and the band
# from 961,587 downward — and they do not meet. Roughly fifteen cities sit between them (Srinagar,
# Amritsar, Navi Mumbai, Prayagraj, Howrah, Ranchi, Coimbatore, Jabalpur, Gwalior, Vijayawada,
# Jodhpur, Madurai, Raipur, Kota and neighbours). Their names are known; their exact figures were not
# verified, and an unverified figure in a seed is indistinguishable from a fact.
#
# So they are absent and the absence is declared. `key_cities` reports `complete: False` and points
# here, rather than handing back seventy cities as though that were the whole 5-lakh-plus set.
SEED_GAP: dict = {
    "band": [961588, 1198490],
    "basis": "census_2011_city",
    "missing_about": 15,
    "names_known": ("Srinagar", "Amritsar", "Navi Mumbai", "Prayagraj", "Howrah", "Ranchi",
                    "Coimbatore", "Jabalpur", "Gwalior", "Vijayawada", "Jodhpur", "Madurai",
                    "Raipur", "Kota"),
    "why": "Two verified extractions from the source list do not meet, and the cities between them "
           "were not confirmed figure by figure. They are named so nobody thinks the list is complete "
           "and so they can be imported deliberately — not seeded from memory, which is how a "
           "plausible wrong number gets in and stays.",
    "fix": "Import them from the Census tables or enter them with a source. Every one is above 9.6 "
           "lakh, so all of them belong in any 5-lakh-plus plan.",
}


_BY_LABEL = {v["label"].lower(): k for k, v in STATES.items()}
# The names people actually type, which are not always the constitutional ones.
_BY_LABEL.update({
    "orissa": "or", "pondicherry": "py", "puducherry": "py", "uttaranchal": "uk",
    "new delhi": "dl", "nct of delhi": "dl", "delhi ncr": "dl", "bombay": "mh",
    "j&k": "jk", "jammu & kashmir": "jk", "dadra and nagar haveli": "dh",
    "daman and diu": "dh", "andaman & nicobar islands": "an", "tamilnadu": "tn",
})


def resolve_state(key: str) -> str:
    """A state code, folded through `ALIASES` and through full names. '' when it is not a state.

    Names resolve as well as codes because a person typing geography types "Maharashtra", and refusing
    that in favour of `mh` would be the interface being right at the user's expense. Old names resolve
    too — a client's own spreadsheet says Orissa and Pondicherry for another decade yet.
    """
    raw = str(key or "").strip().lower()
    if raw in _BY_LABEL:
        return _BY_LABEL[raw]
    k = raw.replace(" ", "").replace("-", "").replace(".", "")
    k = ALIASES.get(k, k)
    if k in STATES:
        return k
    return _BY_LABEL.get(raw.replace("&", "and"), "")


def principal_language_of(key: str) -> str:
    """The state's own principal language, IF the studio holds it. '' otherwise.

    Distinct from `languages_of`, which is a fallback ladder — "if you must pick a language we hold for
    this state, prefer these in this order". A state carrying a `language_gap` has no principal here by
    definition: its real principal language is one the studio cannot write in, and returning the first
    fallback instead would claim otherwise. Returning nothing is the honest answer and is what stops
    Assamese creative being filed as Meghalaya's own language.
    """
    k = resolve_state(key)
    if not k or STATES[k].get("language_gap"):
        return ""
    langs = STATES[k].get("languages") or []
    return langs[0] if langs else ""


def state_label(key: str) -> str:
    k = resolve_state(key)
    return STATES[k]["label"] if k else str(key or "")


def states(zone: str = "", ut: bool | None = None) -> list[dict]:
    """States and UTs as rows, optionally filtered. Alphabetical by label, which is how a person scans
    a list of thirty-six things they are choosing from."""
    out = []
    for k, v in STATES.items():
        if zone and v["zone"] != zone:
            continue
        if ut is not None and bool(v["ut"]) != ut:
            continue
        out.append({
            "key": k, "label": v["label"], "ut": bool(v["ut"]),
            "zone": v["zone"], "zone_label": ZONES.get(v["zone"], v["zone"]),
            "languages": list(v.get("languages") or []),
            "language_gap": v.get("language_gap", ""),
            "has_language_gap": bool(v.get("language_gap")),
            "note": v.get("note", ""),
        })
    out.sort(key=lambda r: r["label"])
    return out


def languages_of(key: str) -> list[str]:
    """The language codes this studio holds for a state, most-spoken first."""
    k = resolve_state(key)
    return list(STATES[k].get("languages") or []) if k else []


def states_for(lang: str, principal_only: bool = False) -> list[str]:
    """Every state where a language code applies. The inverse of `languages_of`, computed rather than
    written down twice — `pr.LANGUAGES[x]["where"]` is the prose version and will drift from this.

    `principal_only` matters more than it looks. Bengali appears in the fallback ladder for six states,
    but it is the principal language of two — and a planner reading the unfiltered list could buy
    Bengali creative for Meghalaya, where it is present and is not what people speak first. The wide
    list answers "where would this creative be understood"; the narrow one answers "where does this
    language belong", and media money should be spent against the second.
    """
    code = str(lang or "").strip().lower()
    if principal_only:
        return sorted(k for k in STATES if principal_language_of(k) == code)
    return sorted(k for k, v in STATES.items() if code in (v.get("languages") or []))


def language_codes() -> tuple[str, ...]:
    """Every language code the studio holds, derived from the state map rather than listed twice.

    `pr.LANGUAGES` carries the same thirteen with their labels and native names. This returns the codes
    only, computed from `STATES`, so a language added to a state cannot go missing from the list of what
    the studio can write — the two cannot drift because only one of them is written down.
    """
    return tuple(sorted({c for v in STATES.values() for c in (v.get("languages") or [])}))


def language_gaps(keys: list[str] | None = None) -> list[dict]:
    """States in scope whose principal language the studio cannot write in.

    Worth its own function because it is the answer to a question a plan should have to face before it
    buys a state: creative in a language nobody there speaks first is a media cost with no message
    behind it, and the gap is knowable in advance rather than after the posts underperform.
    """
    scope = [resolve_state(k) for k in (keys or list(STATES))]
    return [{"state": k, "label": STATES[k]["label"], "gap": STATES[k]["language_gap"],
             "can_offer": list(STATES[k].get("languages") or [])}
            for k in scope if k and STATES[k].get("language_gap")]


def seed_cities() -> list[dict]:
    """The seeded cities, each carrying its basis. Nothing here is stored — this is reference data."""
    return [{"name": n, "state": s, "state_label": STATES[s]["label"],
             "zone": STATES[s]["zone"], "pop": p, "basis": "census_2011_city",
             "source": SEED_SOURCE, "languages": list(STATES[s].get("languages") or [])}
            for n, s, p in _SEED]


def key_cities(min_pop: int = 500000, basis: str = "census_2011_city",
               states_in: list[str] | None = None) -> dict:
    """Cities at or above a population line, on ONE declared basis.

    `min_pop` defaults to 5 lakh because that is the line a media plan usually draws, and the default
    is not the point — `caveat` is. A 2011 figure tested against a 2026 intention is a comparison
    across fifteen years, and the list it produces is short at the bottom in a way no arithmetic here
    can fix. Reported, not silently corrected.
    """
    spec = POP_BASIS.get(basis)
    if not spec:
        return {"available": False, "rows": [], "count": 0,
                "why": f"Unknown basis {basis!r}. One of: {', '.join(POP_BASIS)}."}
    if basis != "census_2011_city":
        return {"available": False, "rows": [], "count": 0, "basis": basis,
                "why": (f"Nothing is seeded on the {spec['label']} basis, so there is no list to filter. "
                        f"The seed is Census 2011 municipal only. Import or enter figures on this basis "
                        f"first — mixing them into the census list is the one thing that must not "
                        f"happen, because a ranking across two bases is not a ranking."),
                "caveat": spec["caveat"]}

    want = [resolve_state(s) for s in (states_in or [])]
    want = [s for s in want if s]
    rows = [c for c in seed_cities() if c["pop"] >= int(min_pop)]
    if want:
        rows = [c for c in rows if c["state"] in want]
    rows.sort(key=lambda c: -c["pop"])
    return {
        "available": True, "basis": basis, "basis_label": spec["label"],
        "min_pop": int(min_pop), "rows": rows, "count": len(rows),
        "states_covered": sorted({c["state"] for c in rows}),
        "source": SEED_SOURCE,
        "caveat": spec["caveat"],
        "threshold_caveat": THRESHOLD_CAVEAT,
        # The seed's hole only matters when the line sits below the band it covers, which for any
        # 5-lakh plan it does. Said plainly rather than left for someone to notice.
        "complete": not (int(min_pop) <= SEED_GAP["band"][1]),
        "gap": SEED_GAP if int(min_pop) <= SEED_GAP["band"][1] else None,
        "language_gaps": language_gaps(sorted({c["state"] for c in rows})),
    }


# --- priority geography: state x urban/rural x town class, for a plan's own targeting (round 92) ----
#
# Built for plan.py's "priority geography" panel. One real number this module did not carry before: a
# state's TOTAL/URBAN/RURAL/MALE/FEMALE population. Everything else here is computed from what already
# exists — `_SEED`'s city list, split into the two geographies an Indian media buyer actually recognises:
#
# **"Metro" is a named list, not a population threshold.** Industry usage (and the 74th Constitutional
# Amendment's own definition of a metropolitan area) means eight specific cities, not "everything above
# X population" — a ninth Class-I city crossing a line does not make it a metro the way media buyers use
# the word. Named here rather than derived.
#
# **Below Tier 1, this cannot offer individual cities.** `_SEED` stops at roughly five lakh (its own
# named gap, `SEED_GAP`) — there is no verified, individually-sourced population for India's several
# thousand smaller towns on file, and inventing one would be exactly the "plausible wrong number"
# `SEED_GAP`'s own docstring warns against. So below Tier 1, this returns one honest aggregate per state
# — "the rest of this state's urban population" — never a fabricated city list.
METRO_CITIES: frozenset[str] = frozenset({
    "Mumbai", "Delhi", "Kolkata", "Chennai", "Bengaluru", "Hyderabad", "Pune", "Ahmedabad",
})

# Census of India 2011 — total / rural / urban / male / female / population aged 0-6, per state and
# union territory. `pop_0_6` is stored but not yet surfaced anywhere — the fuller working-age/senior
# bands a plan might eventually want (15-59, 60+) are not in this seed: the only cross-state compilation
# found used non-standard age bands that straddle those lines, and re-aggregating them would invent
# precision that was never measured. Real 15-59/60+ figures would need each state's own C-13/C-14
# single-year-age table from censusindia.gov.in — a real next import, not done here.
#
# Two real complications, both handled explicitly rather than silently smoothed over:
#
# Telangana/Andhra Pradesh split in 2014, after this count — the census counted them as one state.
# Both rows below are the now-standard bifurcated figures (Telangana as usually republished; Andhra
# Pradesh as the remainder). Andhra Pradesh's `pop_0_6` is a subtraction (undivided AP minus Telangana)
# rather than a directly-published figure — every other cell in both rows is either independently
# published or internally consistent (male+female=total, rural+urban=total).
#
# Jammu & Kashmir/Ladakh split in 2019, also after this count. Ladakh has no official 2011-basis
# figure at all — it is reconstructed here from its own two former districts (Leh + Kargil), which is
# exactly what Ladakh has always been. Jammu & Kashmir's row is the undivided total minus that
# reconstruction; its rural/urban split carries a known ~19-person rounding mismatch against the total
# (two different secondary compilations, not a contradiction worth chasing further at this scale).
#
# Manipur has two different 2011 totals in real circulation — a March-2011 provisional count and a
# later, larger final count. The final count (which virtually every secondary source now uses) is what
# is seeded here; the provisional figure is named so nobody re-imports it as a second, disagreeing fact.
URBAN_RURAL: dict[str, dict] = {
    "ap": {"total": 49577103, "rural": 34966693, "urban": 14610410, "male": 24830513, "female": 24746590, "pop_0_6": 5243636},
    "ar": {"total": 1383727, "rural": 1066358, "urban": 317369, "male": 713912, "female": 669815, "pop_0_6": 212188},
    "as": {"total": 31205576, "rural": 26807034, "urban": 4398542, "male": 15939443, "female": 15266133, "pop_0_6": 4638130},
    "br": {"total": 104099452, "rural": 92341436, "urban": 11758016, "male": 54278157, "female": 49821295, "pop_0_6": 19133964},
    "ct": {"total": 25545198, "rural": 19607961, "urban": 5937237, "male": 12832895, "female": 12712303, "pop_0_6": 3661689},
    "ga": {"total": 1458545, "rural": 551731, "urban": 906814, "male": 739140, "female": 719405, "pop_0_6": 144611},
    "gj": {"total": 60439692, "rural": 34694609, "urban": 25745083, "male": 31491260, "female": 28948432, "pop_0_6": 7777262},
    "hr": {"total": 25351462, "rural": 16509359, "urban": 8842103, "male": 13494734, "female": 11856728, "pop_0_6": 3380721},
    "hp": {"total": 6864602, "rural": 6176050, "urban": 688552, "male": 3481873, "female": 3382729, "pop_0_6": 777898},
    "jh": {"total": 32988134, "rural": 25055073, "urban": 7933061, "male": 16930315, "female": 16057819, "pop_0_6": 5389495},
    "ka": {"total": 61095297, "rural": 37469335, "urban": 23625962, "male": 30966657, "female": 30128640, "pop_0_6": 7161033},
    "kl": {"total": 33406061, "rural": 17471135, "urban": 15934926, "male": 16027412, "female": 17378649, "pop_0_6": 3472955},
    "mp": {"total": 72626809, "rural": 52557404, "urban": 20069405, "male": 37612306, "female": 35014503, "pop_0_6": 10809395},
    "mh": {"total": 112374333, "rural": 61556074, "urban": 50818259, "male": 58243056, "female": 54131277, "pop_0_6": 13326517},
    "mn": {"total": 2855794, "rural": 2021640, "urban": 834154, "male": 1438586, "female": 1417208, "pop_0_6": 375357,
           "note": "The Final Population Totals figure. A March-2011 Provisional count (2,570,390, rural "
                   "1,736,236) circulates too — do not re-import it as a second, disagreeing figure."},
    "ml": {"total": 2966889, "rural": 2371439, "urban": 595450, "male": 1491832, "female": 1475057, "pop_0_6": 568536},
    "mz": {"total": 1097206, "rural": 525435, "urban": 571771, "male": 555339, "female": 541867, "pop_0_6": 168531},
    "nl": {"total": 1978502, "rural": 1407536, "urban": 570966, "male": 1024649, "female": 953853, "pop_0_6": 291071},
    "or": {"total": 41974218, "rural": 34970562, "urban": 7003656, "male": 21212136, "female": 20762082, "pop_0_6": 5273194},
    "pb": {"total": 27743338, "rural": 17344192, "urban": 10399146, "male": 14639465, "female": 13103873, "pop_0_6": 3076219},
    "rj": {"total": 68548437, "rural": 51500352, "urban": 17048085, "male": 35550997, "female": 32997440, "pop_0_6": 10649504},
    "sk": {"total": 610577, "rural": 456999, "urban": 153578, "male": 323070, "female": 287507, "pop_0_6": 64111},
    "tn": {"total": 72147030, "rural": 37229590, "urban": 34917440, "male": 36137975, "female": 36009055, "pop_0_6": 7423832},
    "tg": {"total": 35003674, "rural": 21395009, "urban": 13608665, "male": 17611633, "female": 17392041, "pop_0_6": 3899166},
    "tr": {"total": 3673917, "rural": 2712464, "urban": 961453, "male": 1874376, "female": 1799541, "pop_0_6": 458014},
    "up": {"total": 199812341, "rural": 155317278, "urban": 44495063, "male": 104480510, "female": 95331831, "pop_0_6": 30791331},
    "uk": {"total": 10086292, "rural": 7036954, "urban": 3049338, "male": 5137773, "female": 4948519, "pop_0_6": 1355814},
    "wb": {"total": 91276115, "rural": 62183113, "urban": 29093002, "male": 46809027, "female": 44467088, "pop_0_6": 10581466},
    "an": {"total": 380581, "rural": 237093, "urban": 143488, "male": 202871, "female": 177710, "pop_0_6": 40878},
    "ch": {"total": 1055450, "rural": 28991, "urban": 1026459, "male": 580663, "female": 474787, "pop_0_6": 119434},
    "dh": {"total": 586956, "rural": 243510, "urban": 343446, "male": 344061, "female": 242895, "pop_0_6": 77829,
           "note": "The former Dadra & Nagar Haveli and Daman & Diu were two separate UTs in 2011, merged "
                   "in 2020. This is their computed sum — no single already-merged 2011 figure is published."},
    "dl": {"total": 16787941, "rural": 419042, "urban": 16368899, "male": 8987326, "female": 7800615, "pop_0_6": 2012454},
    "jk": {"total": 12267013, "rural": 9064220, "urban": 3202812, "male": 6483906, "female": 5783107, "pop_0_6": 1986961,
           "note": "Post-2019 (excludes Ladakh), reconstructed as undivided J&K minus Ladakh. The "
                   "rural+urban here sums to 12,267,032 against a total of 12,267,013 — a ~19-person gap "
                   "between two secondary compilations, not a contradiction worth chasing at this scale."},
    "la": {"total": 274289, "rural": 212280, "urban": 62009, "male": 156756, "female": 117533, "pop_0_6": 31944,
           "note": "No official 2011-basis figure exists — Ladakh did not exist as a unit in 2011. "
                   "Reconstructed by summing its two former districts, Leh and Kargil."},
    "ld": {"total": 64473, "rural": 14141, "urban": 50332, "male": 33123, "female": 31350, "pop_0_6": 7255},
    "py": {"total": 1247953, "rural": 395200, "urban": 852753, "male": 612511, "female": 635442, "pop_0_6": 132858},
}
URBAN_RURAL_SOURCE = ("Census of India 2011, Primary Census Abstract — via census2011.co.in and "
                      "Wikipedia's compiled state population list, cross-checked against each other; "
                      "state-specific derivation notes are on the rows that needed one")
CENSUS_2011_CAVEAT = (
    "Every figure here is Census of India 2011 — the last completed count. India was 1.21 billion then "
    "and is estimated above 1.4 billion now, and urban areas grew faster than the national rate, so "
    "these numbers are stale by roughly fifteen years, unevenly, and low rather than high. Census 2027 "
    "enumerates on 1 March 2027 and is the next real count."
)


def state_population(key: str) -> dict:
    """One state's total/rural/urban/male/female, on the Census 2011 basis. `{}` if not on file."""
    k = resolve_state(key)
    if not k or k not in URBAN_RURAL:
        return {}
    return {"state": k, "label": STATES[k]["label"], **URBAN_RURAL[k],
            "source": URBAN_RURAL_SOURCE, "basis": "census_2011"}


def town_class_cities(key: str) -> dict:
    """This state's seeded cities, split metro vs. tier 1. Empty lists, not an error, for a state or UT
    with nothing seeded — most of the smaller states and every UT but Delhi and Chandigarh."""
    k = resolve_state(key)
    metro, tier1 = [], []
    for name, s, pop in _SEED:
        if s != k:
            continue
        (metro if name in METRO_CITIES else tier1).append({"name": name, "pop": pop})
    metro.sort(key=lambda c: -c["pop"])
    tier1.sort(key=lambda c: -c["pop"])
    return {"metro": metro, "tier1": tier1}


def town_class_breakdown(key: str) -> dict:
    """Population by town class for one state: named metro/tier-1 cities, one honest 'rest of urban'
    aggregate (urban total minus every seeded city), and the rural total. `{}` when the state has no
    population figure on file.

    The seeded city list and the state's own urban total are two separate Census extractions (a city
    list built by hand from a compiled source, a state total that should already include every one of
    those cities). If the city list ever drifts ahead of the state total — the seed grows without the
    total being re-checked — the subtraction below would go negative and silently look like a small,
    valid answer. Clamped to zero and flagged instead, the same "report the gap, don't hide it" stance
    `SEED_GAP` already takes.
    """
    pop = state_population(key)
    if not pop:
        return {}
    k = pop["state"]
    cities = town_class_cities(k)
    metro_pop = sum(c["pop"] for c in cities["metro"])
    tier1_pop = sum(c["pop"] for c in cities["tier1"])
    rest = pop["urban"] - metro_pop - tier1_pop
    return {
        "state": k, "label": pop["label"],
        "metro": {"pop": metro_pop, "cities": cities["metro"]},
        "tier1": {"pop": tier1_pop, "cities": cities["tier1"]},
        "restofurban": {"pop": max(rest, 0)},
        "rural": {"pop": pop["rural"]},
        "urban_total": pop["urban"], "total": pop["total"],
        "male": pop.get("male"), "female": pop.get("female"),
        "data_quality_flag": rest < 0,
        "source": URBAN_RURAL_SOURCE, "seed_source": SEED_SOURCE, "caveat": CENSUS_2011_CAVEAT,
    }


def town_classes() -> dict:
    """Every state's town-class breakdown that has a population figure on file, keyed by state code —
    for a picker to load once rather than round-trip per state chosen."""
    return {k: town_class_breakdown(k) for k in STATES if k in URBAN_RURAL}


def status() -> dict:
    """The whole vocabulary, for a screen that has to offer it."""
    return {
        "states": states(), "zones": ZONES, "aliases": ALIASES,
        "pop_basis": POP_BASIS, "threshold_caveat": THRESHOLD_CAVEAT,
        "seed": {"source": SEED_SOURCE, "count": len(_SEED), "gap": SEED_GAP},
        "counts": {"states": sum(1 for v in STATES.values() if not v["ut"]),
                   "uts": sum(1 for v in STATES.values() if v["ut"]),
                   "cities_seeded": len(_SEED),
                   "language_gaps": len(language_gaps())},
        "why_population_is_not_reach": POP_BASIS["platform_reach"]["caveat"],
        # Priority-geography vocabulary (round 92) — one state->breakdown map, loaded once by whichever
        # screen offers the picker, same reasoning as everything else already in this one status route.
        "town_classes": town_classes(),
        "town_classes_source": URBAN_RURAL_SOURCE, "town_classes_caveat": CENSUS_2011_CAVEAT,
        "town_classes_states_covered": sorted(URBAN_RURAL),
    }
