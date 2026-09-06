"""sales.py — the trade sheet and the enabler the field actually carries.

    Brief -> Messaging house -> Communication plan -> Executions
                                                       |
                                                       +-- and this

**Deliberately not a kind inside the execution envelope.** Every other execution is briefed from one
audience row, one channel row and one occasion. A trade plan is briefed from the whole route to market
at once, because its central risk — channel conflict — is invisible unless every channel sits in one
view. Six documents, one per channel, cannot see the thing they exist to prevent.

Two audiences, and confusing them is the usual failure:

**The trade.** A distributor, a kirana owner, a modern-trade buyer and a q-commerce category manager
hear arguments about margin, rate of sale, working capital and listing terms. None of that is what you
say to a shopper. If the house has a `trade` message, that is the line; if it has none, this says so
rather than borrowing the consumer line and hoping.

**The person at the counter.** The trade sheet is for a sales director defending a number: payback net
of scheme, leakage controls, sell-through level. The *enabler* is for a TSI at 9am with ninety seconds,
and almost none of that belongs on it. Same facts, inverted — the retailer's arithmetic, not yours. The
two are generated from one source here so they cannot disagree.

Loyalty is present but typed as a **lever, not a channel**. It runs through general trade and q-commerce
rather than beside them, and giving it its own room is how loyalty spend stops landing against the
channel whose behaviour it is buying — which is how it escapes measurement in practice.
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
import strategy
import tenancy

# Resolved through tenancy so one deployment can hold several companies. The name is kept
# so every reader in this module is unchanged.
SALES_DIR = tenancy.dir("trade")
_SKILL = os.path.join(os.path.dirname(__file__), "sales_skill")

# What a channel can be FOR. A channel with no role does not get money.
ROLES = {
    "volume":  "Where the cases go. Judged on rate of sale and reorder rhythm.",
    "reach":   "Where distribution is won. Judged on outlets billed and coverage.",
    "premium": "Where mix improves. Judged on value per transaction, not volume.",
    "trial":   "Where new buyers start. Judged on first-time purchase.",
    "defence": "Where a competitor is held. Judged on share held, not gained.",
}

# Sell-through. Primary-only schemes produce phantom growth and a returns problem six weeks later, so
# the level is compulsory and primary is always flagged.
SELL_THROUGH = {
    "primary":   "To the distributor. Movement here is dispatch, not demand.",
    "secondary": "To the retailer. The scheme has reached the shelf.",
    "tertiary":  "To the consumer. The only level that is actually offtake.",
}

LEVERS = ("retailer margin", "trade scheme", "display incentive", "loyalty programme",
          "listing and terms of trade", "promoter or ISD", "credit terms", "platform ad spend",
          "assortment and pack architecture")

# Each channel carries its own elements. Not one kit stretched over eight rooms: what a wholesaler needs
# and what a q-commerce category manager needs have almost nothing in common.
#
# The first six keys and every element key match the built UI exactly, so the outstanding count on the
# screen and the one computed here can never disagree.
#
# `own_retail` and `home_delivery` have no tab yet. They are here because in a daily category — dairy,
# fresh, bakery — home delivery and subscription are where one decision is honoured for months, which is
# the best retention economics in the whole route to market. A trade sheet for a daily category with no
# home-delivery column is missing its most valuable channel, so the backend carries it and says so rather
# than waiting for a screen.
CHANNELS: list[dict] = [
    {"key": "trad", "label": "Traditional retail", "scope": "channel",
     "shorthand": "the kirana counter — still the large majority of Indian FMCG value",
     "rewards": "reliability and rate of sale — what turns, and what it makes per foot",
     "goes_wrong": "schemes that reward loading rather than selling",
     "elements": [
         {"key": "pitch", "label": "What the retailer hears", "asks": "The claim in the retailer's terms — what it does for their counter, not the consumer line."},
         {"key": "counter", "label": "Counter and shelf kit", "asks": "Which pieces go where, and how little space they can occupy and still work."},
         {"key": "slab", "label": "Incentive slab", "asks": "What the retailer earns, at what volume, and when they actually see it."},
         {"key": "beat", "label": "Beat plan coverage", "asks": "Which routes, how often, and who is accountable for the ones that get skipped."},
         {"key": "card", "label": "Salesman pitch card", "asks": "The one page the rep works from. It must survive being read in a doorway."}]},
    {"key": "wholesale", "label": "Wholesale", "scope": "channel",
     "shorthand": "traditional wholesale and cash & carry",
     "rewards": "price per case and credit. Almost nothing else",
     "goes_wrong": "the main engine of channel leakage — scheme goods travel and undercut your own trade",
     "elements": [
         {"key": "scheme", "label": "Scheme and margin structure", "asks": "The number that makes it worth their working capital."},
         {"key": "pack", "label": "Bulk pack and case configuration", "asks": "What ships, in what case, and whether it breaks down for the kirana below."},
         {"key": "terms", "label": "Credit and delivery terms", "asks": "Days, returns, and who carries the risk on unsold stock."},
         {"key": "meet", "label": "Wholesaler meet", "asks": "The agenda, and what is asked for by the end of it."}]},
    {"key": "modern", "label": "Modern retail", "scope": "channel",
     "shorthand": "organised chains — listing, planogram, promoters, joint business plans",
     "rewards": "category growth for the retailer, not brand growth for you. Argue in their terms",
     "goes_wrong": "margin erosion by a thousand small asks; promoter cost is fixed dressed as variable",
     "elements": [
         {"key": "plano", "label": "Planogram and shelf share", "asks": "Shelf position and facings asked for, by format."},
         {"key": "visibility", "label": "In-store visibility", "asks": "End caps, gondolas, chillers — priced, with the period."},
         {"key": "promoter", "label": "Promoter deployment", "asks": "Which outlets, on what productivity floor."},
         {"key": "offer", "label": "Chain-specific offer", "asks": "The consumer offer and who funds each part."},
         {"key": "jbp", "label": "Joint business plan", "asks": "What the chain gets in category terms, and what you get."}]},
    {"key": "ecomm", "label": "E-commerce", "scope": "channel",
     "shorthand": "Amazon, Flipkart, BigBasket — a shelf that is searched rather than walked",
     "rewards": "content quality, ratings, availability and search position",
     "goes_wrong": "treated as a shop window rather than a supply chain — out of stock is invisible to you and total to the shopper",
     "elements": [
         {"key": "listing", "label": "Listing content", "asks": "Titles, A+ content, images. What a shopper reads before deciding."},
         {"key": "search", "label": "Search and keyword plan", "asks": "Terms defended, terms attacked, and the budget."},
         {"key": "reviews", "label": "Ratings and reviews plan", "asks": "Current rating, the target, and how it is moved honestly."},
         {"key": "basket", "label": "Basket offers and combos", "asks": "Multipacks and bundles that would not exist in a kirana."},
         {"key": "banner", "label": "Platform media", "asks": "What is bought on-platform, and against which term."}]},
    {"key": "qcomm", "label": "Quick commerce", "scope": "channel",
     "shorthand": "Blinkit, Zepto, Instamart — dark stores, a few thousand SKUs each",
     "rewards": "being in the right dark stores and findable in-app. Range is narrow, so listing is the whole game",
     "goes_wrong": ("over-indexed because it is fashionable — for dairy and fresh, dark stores cannot "
                    "match an established cold chain, so weight it to the category you are in"),
     "elements": [
         {"key": "assort", "label": "Assortment for the ten-minute basket", "asks": "Which SKUs, which cities, which dark stores."},
         {"key": "avail", "label": "Dark-store availability", "asks": "Current availability and the target."},
         {"key": "price", "label": "Pack and price architecture", "asks": "Built for immediacy — and checked against the kirana who stocks you daily."},
         {"key": "ads", "label": "On-platform placement", "asks": "In-app share of category and the ad spend behind it. Decide whether this sits here or in the media plan; do not let both claim it."},
         {"key": "window", "label": "Delivery-window offers", "asks": "Which windows matter for this category, and why."}]},
    {"key": "loyalty", "label": "Loyalty programmes", "scope": "lever",
     "shorthand": "a lever that runs THROUGH the channels above, not beside them",
     "rewards": "repeat behaviour from a named person — the only mechanism here that knows who bought",
     "goes_wrong": "points farming, and cost that never lands against the channel it bought behaviour in",
     "elements": [
         {"key": "who", "label": "Who it rewards", "asks": "Retailer, salesman, or consumer. Who receives it determines who games it."},
         {"key": "earn", "label": "Earn mechanic", "asks": "What earns, at what rate, verified how."},
         {"key": "burn", "label": "Reward and burn", "asks": "What it is spent on, and the liability that creates."},
         {"key": "enrol", "label": "Enrolment route", "asks": "How someone joins, and how duplicate enrolments are prevented."},
         {"key": "data", "label": "Data captured, and what it is for", "asks": "What is captured, and what it is actually used for."}]},
    {"key": "own_retail", "label": "Own retail", "scope": "channel", "no_screen_yet": True,
     "shorthand": "brand parlours and company outlets",
     "rewards": "full margin, control of range, and a place to launch what the trade will not stock yet",
     "goes_wrong": "a property business wearing a marketing costume — rent is fixed, footfall is not",
     "elements": [
         {"key": "range", "label": "Range and exclusives", "asks": "What is here and nowhere else, and for how long."},
         {"key": "experience", "label": "Experience", "asks": "What happens in the outlet that cannot happen in a kirana."},
         {"key": "launch_window", "label": "Launch window", "asks": "What launches here first, and when it goes wider."},
         {"key": "staff_script", "label": "Staff script", "asks": "What the person behind the counter says, in their words."}]},
    {"key": "home_delivery", "label": "Home delivery & subscription", "scope": "channel",
     "no_screen_yet": True,
     "shorthand": "daily delivery, milk booths, app subscription",
     "rewards": ("habit. A subscription is one decision honoured for months, which is the opposite "
                 "economics of everything else here — in a daily cold-chain category this may be the "
                 "most valuable channel you have"),
     "goes_wrong": "churn measured badly — reports growth for a year, then reports a cliff",
     "elements": [
         {"key": "trial", "label": "Trial offer", "asks": "The first-month offer, and what it costs to acquire one subscriber."},
         {"key": "referral", "label": "Referral", "asks": "What an existing subscriber gets, and for what."},
         {"key": "reliability", "label": "Reliability promise", "asks": "The promise, and what happens when it is missed."},
         {"key": "pause_resume", "label": "Pause and resume", "asks": "How flexible, and why that is a retention lever rather than a leak."},
         {"key": "churn", "label": "Churn measurement", "asks": "How churn is defined and reported. An unmeasured subscription base is a cliff waiting."}]},
]
CHANNEL_BY_KEY = {c["key"]: c for c in CHANNELS}

ELEMENT_STATES = ("not started", "briefed", "agreed")

# "A scheme that buys visibility buys nothing you can measure." These are rejected outright.
EMPTY_BEHAVIOURS = ("visibility", "engagement", "excitement", "awareness", "presence", "mindshare",
                    "buzz", "activation", "activate", "push", "focus", "support", "momentum")

_UNKNOWN = ("unknown", "tbd", "n/a", "na", "-", "?")


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())


def _path(sid: str) -> str:
    return os.path.join(SALES_DIR, f"{sid}.json")


def load(sid: str) -> dict | None:
    try:
        with open(_path(sid), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def save(s: dict) -> dict:
    os.makedirs(SALES_DIR, exist_ok=True)
    s["updated"] = _now()
    tmp = _path(s["id"]) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, _path(s["id"]))
    return s


def sheets() -> list[dict]:
    os.makedirs(SALES_DIR, exist_ok=True)
    out = []
    for f in sorted(os.listdir(SALES_DIR)):
        if f.endswith(".json"):
            s = load(f[:-5])
            if s:
                out.append({"id": s["id"], "brand": s.get("brand", ""), "plan": s.get("plan", ""),
                            "house": s.get("house", ""), "created": s.get("created", ""),
                            "updated": s.get("updated", ""),
                            "outstanding": outstanding(s)})
    return out


def new_sheet(brand: str, plan_id: str = "", house_id: str = "") -> dict:
    """A sheet holds every channel from the start — including the ones getting nothing.

    A channel with no money is a decision, and an empty row records it. Dropping the row hides it,
    which is how a route to market quietly loses a channel nobody argued about.
    """
    s = {"id": uuid.uuid4().hex[:10], "brand": brand or "Brand",
         "plan": plan_id, "house": house_id, "created": _now(), "updated": _now(),
         "channels": {c["key"]: {
             "key": c["key"], "role": "", "owner": "", "share_now": "",
             "behaviour": "", "baseline": "", "target": "",
             "lever": "", "cost_per_unit": "", "payback": "",
             "leakage": "", "control": "", "residual_risk": "",
             "sell_through": "", "receives_money": "", "effective_price": "",
             "runs_through": [], "source": "",
             "elements": {e["key"]: {"key": e["key"], "brief": "", "status": "not started",
                                     "updated": ""} for e in c["elements"]},
         } for c in CHANNELS}}
    return save(s)


# --- editing -----------------------------------------------------------------------------------

_CH_FIELDS = ("role", "owner", "share_now", "behaviour", "baseline", "target", "lever",
              "cost_per_unit", "payback", "leakage", "control", "residual_risk",
              "sell_through", "receives_money", "effective_price", "source")


def set_channel(s: dict, ch: str, patch: dict) -> dict | None:
    if ch not in CHANNEL_BY_KEY:
        return None
    node = s["channels"][ch]
    for f in _CH_FIELDS:
        if f in patch:
            node[f] = str(patch.get(f, "") or "").strip()
    if "runs_through" in patch:
        want = patch.get("runs_through") or []
        node["runs_through"] = [k for k in want if k in CHANNEL_BY_KEY and k != ch]
    node["edited"] = _now()
    return save(s)


def set_element(s: dict, ch: str, el: str, brief: str | None = None,
                status: str | None = None) -> tuple[dict | None, str]:
    if ch not in CHANNEL_BY_KEY:
        return None, "No such channel."
    node = s["channels"][ch]
    if el not in node["elements"]:
        return None, "No such element for this channel."
    e = node["elements"][el]
    if brief is not None:
        e["brief"] = brief.strip()
        # Writing a brief IS briefing it. Leaving the badge on "not started" while the box holds three
        # paragraphs makes the state meaningless, and it is the state the right rail counts.
        if e["brief"] and e.get("status") == "not started" and status is None:
            status = "briefed"
        elif not e["brief"] and status is None:
            status = "not started"
    if status is not None:
        if status not in ELEMENT_STATES:
            return None, f"Status must be one of: {', '.join(ELEMENT_STATES)}."
        # The primary-only gate. A pitch card is the thing a TSI reads out to a retailer, and a
        # primary-only scheme is one whose movement is dispatch rather than demand. Printing that at
        # scale is how phantom growth gets sold into the field before anyone has checked it is real.
        if status == "agreed" and el in ("card", "pitch", "scheme"):
            if str(node.get("sell_through", "")).lower() == "primary":
                return None, ("This scheme is primary-only — its movement is dispatch, not demand. "
                              "A pitch card for it sells phantom growth to the field. Establish "
                              "secondary or tertiary sell-through first.")
        e["status"] = status
    e["updated"] = _now()
    return save(s), ""


# --- the message the trade hears ---------------------------------------------------------------

def trade_message(house: dict | None) -> dict:
    """The house's `trade` lines, or an honest absence.

    Returning `{"has": False}` is the useful answer. The trade hears an argument about margin and rate
    of sale; the consumer line does not convert into one, and a screen that silently substituted it
    would be the exact mistake this whole module is arranged to prevent.
    """
    if not house:
        return {"has": False, "why": "no messaging house attached", "options": []}
    node = house.get("nodes", {}).get("medium") or {}
    picked = set(node.get("chosen") or [])
    opts = [{"id": o["id"], "text": o["text"], "note": o.get("note", "")}
            for o in node.get("options", [])
            if o["id"] in picked and str(o.get("tag", "")).lower() == "trade"]
    if not opts:
        return {"has": False, "options": [],
                "why": ("the house has no trade message. Write one in message-by-medium — do not "
                        "borrow the consumer line for a distributor")}
    return {"has": True, "options": opts, "why": ""}


# --- the shopkeeper's own arithmetic ------------------------------------------------------------
#
# `pitch` (what the retailer hears) and `card` (the salesman pitch card) already exist as elements on
# the `trad` channel, and a person writes them by hand today. What was missing is the number those two
# fields are supposed to be built on: what a facing of this pack actually earns a shopkeeper in a week,
# set against the unbranded alternative he can stock instead. That is the retailer's own ladder — margin,
# rate of sale, working capital — computed rather than asserted, the same discipline `posm.py` and
# `activation.py` apply to their own mediums. A pitch card that asserts "stock the trust, not just the
# litre" with no number under it is a slogan; this is the number.


def margin_story(mrp: float, trade_price: float, *, case_size: int = 1, units_per_week: float = 0,
                 facings: int = 1, unbranded_price: float | None = None,
                 unbranded_margin_pct: float | None = None) -> dict:
    """What one facing of this pack earns a shopkeeper in a week, against the unbranded alternative.

    Refuses rather than guesses. `mrp` and `trade_price` are the two numbers every other figure here
    is built from — without both, nothing downstream is computable, and a margin story assembled from
    a guessed trade price is the exact failure this function exists to prevent.

    The unbranded comparison is optional and only computed when BOTH an unbranded price and an
    unbranded margin percentage are given — a real, sourced comparison, never invented to make the
    branded pack look better. Without it, the branded numbers still stand on their own.
    """
    if mrp is None or mrp <= 0:
        return {"available": False,
                "why": "No MRP given. The whole story is built from it — supply the pack's real MRP."}
    if trade_price is None or trade_price <= 0:
        return {"available": False,
                "why": "No trade price given — what the shopkeeper actually pays. Without it, margin "
                       "is not computable; the MRP alone tells nobody what he earns."}
    if trade_price >= mrp:
        return {"available": False,
                "why": f"Trade price ({trade_price}) is not below MRP ({mrp}) — check which number is "
                       f"which; a shopkeeper who pays MRP or more has no margin to be told about."}

    case_size = max(1, int(case_size or 1))
    facings = max(1, int(facings or 1))
    margin_per_unit = round(mrp - trade_price, 2)
    margin_pct = round((margin_per_unit / mrp) * 100, 1)
    margin_per_case = round(margin_per_unit * case_size, 2)

    weekly = None
    if units_per_week and units_per_week > 0:
        weekly = round(margin_per_unit * units_per_week, 2)
        per_facing_week = round(weekly / facings, 2)
    else:
        per_facing_week = None

    out = {
        "available": True,
        "mrp": mrp, "trade_price": trade_price,
        "margin_per_unit": margin_per_unit, "margin_pct": margin_pct,
        "case_size": case_size, "margin_per_case": margin_per_case,
        "facings": facings,
        "weekly_margin": weekly, "margin_per_facing_per_week": per_facing_week,
        "missing": [] if units_per_week else
                   ["units sold per week — without it, this stops at margin per case and cannot say "
                    "what a facing actually earns in a week, which is the number a shopkeeper weighs "
                    "a decision on"],
    }

    if unbranded_price is not None and unbranded_margin_pct is not None and unbranded_price > 0:
        unb_margin_unit = round(unbranded_price * (unbranded_margin_pct / 100.0), 2)
        out["unbranded"] = {
            "price": unbranded_price, "margin_pct": unbranded_margin_pct,
            "margin_per_unit": unb_margin_unit,
            "advantage_per_unit": round(margin_per_unit - unb_margin_unit, 2),
        }
        if per_facing_week is not None and unbranded_price > 0:
            # Same rate of sale assumed for both — the honest comparison is margin per unit at the
            # SAME volume, not a volume nobody has measured for the alternative. Said explicitly rather
            # than silently assumed, because the two products almost never sell at the same rate and
            # pretending otherwise is how a comparison quietly becomes a claim.
            out["unbranded"]["comparison_note"] = (
                "Assumes the same units sold per week for both — the real difference in rate of sale "
                "between the two is not known here and should be checked before this number is quoted.")
    elif unbranded_price is not None or unbranded_margin_pct is not None:
        out["unbranded"] = None
        out["missing"].append("the unbranded comparison needs BOTH its price and its margin percentage "
                              "— only one was given, so no comparison is drawn")

    return out


# --------------------------------------------------------------------------------------
# What a distributor and a channel actually decide on
# --------------------------------------------------------------------------------------
#
# `margin_story` answers the shopkeeper's question. These two answer the other two people in the
# chain, and both were missing.
#
# A DISTRIBUTOR does not decide on margin. He decides on return on the money he has tied up - stock at
# cost, credit he has extended to retailers, deposits, and the van and the godown. Two distributors on
# an identical margin can return wildly differently depending on how fast the stock turns and how
# quickly he collects. Selling a distributor on margin is the most common way a trade pitch misses.
#
# A CHANNEL has a cost to serve, and some channels cost more to serve than they return. Quick commerce
# is the live example: commission, listing fees, dark-store storage and fulfilment together can exceed
# the gross margin of a low-margin category, which makes every incremental order a loss. That is worth
# knowing before a listing is signed rather than after a quarter of it.

DISTRIBUTOR_ROI_BASIS: dict = {
    "claim": "Healthy annual distributor ROI in Indian FMCG runs roughly 20-35%, and 25-40% in dairy.",
    "formula": "Net profit divided by total investment, where investment is stock at cost + credit "
               "extended to retailers + deposits + infrastructure.",
    "source": "Published Indian FMCG distribution benchmarks (distributor margin and ROI guides, 2026).",
    "dispute": "A published band, not a rule. Route density, category rotation and collection terms "
               "move it more than anything a brand controls, and a distributor carrying several "
               "non-competing brands earns a blended return no single brand can see.",
    "note": "Reported as a band to sit a real figure against, never as a target to hit. The lever is "
            "usually rotation and collection, not margin.",
}

RETAIL_COST_REFERENCE: dict = {
    "what": "Published costs of listing on Indian quick-commerce platforms, for checking a real quote "
            "against. Nothing here is used as a default - the functions below refuse without entered "
            "figures, because a contribution verdict computed from a published range is a verdict "
            "about somebody else's deal.",
    "commission": "15-30% of order value, varying by category and negotiated volume.",
    "listing": {
        "blinkit": "About Rs 25,000 per SKU per state, returned as ad-wallet credit - which is why "
                   "this spend appears in both the trade budget and the media plan.",
        "instamart": "Quoted around Rs 8-10 lakh per quarter as a combined listing and ad wallet.",
        "zepto": "No separate per-SKU listing fee; onboarding and advertising bundled, around "
                 "Rs 5-6 lakh.",
    },
    "also": "Dark-store storage, fulfilment per order and inventory penalties sit on top.",
    "source": "Indian quick-commerce brand-onboarding and margin analyses, 2026.",
}


def distributor_roi(monthly_offtake: float, margin_pct: float, *, stock_at_cost: float,
                    credit_extended: float | None = None, deposits: float = 0.0,
                    infrastructure: float = 0.0, monthly_operating_cost: float = 0.0) -> dict:
    """Return on the money a distributor has tied up. Refuses rather than guesses.

    `monthly_offtake` is what he sells in a month at his selling price; `margin_pct` is his margin on
    that. Both are needed, and so is stock at cost - it is the largest part of the denominator, and an
    ROI computed without it is a different number wearing the same name.

    `credit_extended` is optional and its absence is FLAGGED rather than treated as zero. Leaving it
    out shrinks the investment base, which makes the return look better - so a missing value is
    reported as "this figure reads high" instead of quietly passing.
    """
    if not monthly_offtake or monthly_offtake <= 0:
        return {"available": False,
                "why": "No monthly offtake given - what this distributor actually sells in a month. "
                       "Every figure here is built from it."}
    if margin_pct is None or margin_pct <= 0:
        return {"available": False,
                "why": "No distributor margin given. Margin alone does not decide anything, but "
                       "without it there is no profit to divide by the investment."}
    if not stock_at_cost or stock_at_cost <= 0:
        return {"available": False,
                "why": "No stock at cost given. It is the biggest part of the money he has tied up, "
                       "and an ROI that leaves it out is not an ROI - it is a margin with extra steps."}

    annual_rev = float(monthly_offtake) * 12.0
    annual_margin = annual_rev * (float(margin_pct) / 100.0)
    annual_opex = float(monthly_operating_cost or 0.0) * 12.0
    net = annual_margin - annual_opex

    credit = float(credit_extended) if credit_extended not in (None, "") else 0.0
    investment = float(stock_at_cost) + credit + float(deposits or 0.0) + float(infrastructure or 0.0)
    roi = round(net / investment * 100.0, 1) if investment > 0 else None

    # Rotation, which is the lever. Cost of goods over stock rather than revenue over stock, or the
    # turns read high by exactly the margin.
    cogs = annual_rev * (1.0 - float(margin_pct) / 100.0)
    turns = round(cogs / float(stock_at_cost), 1) if stock_at_cost else None

    # One sentence per condition, written ONCE. The flag says a thing is wrong; this says what it
    # costs the reader. It is returned under its own key as well as in `missing`, because a screen
    # showing the flag needs the sentence beside the figure, not in a footnote - and a screen that
    # has to compose that sentence itself will get it wrong, or drift from this one.
    understated_why = ("Credit extended to retailers was not entered, so it is not in the investment "
                       "base and the return below reads HIGHER than the real one. On a slow-collecting "
                       "route this is often the largest single number in the denominator.")
    gross_only_why = ("No monthly operating cost was entered - van, salaries, godown. This is "
                      "therefore a gross return, not a net one.")

    missing = []
    if credit_extended in (None, ""):
        missing.append(understated_why)
    if not monthly_operating_cost:
        missing.append(gross_only_why)

    out = {
        "available": True,
        "annual_revenue": round(annual_rev, 2), "annual_margin": round(annual_margin, 2),
        "annual_operating_cost": round(annual_opex, 2), "annual_net_profit": round(net, 2),
        "investment": round(investment, 2),
        "investment_parts": {"stock_at_cost": round(float(stock_at_cost), 2),
                             "credit_extended": round(credit, 2),
                             "deposits": round(float(deposits or 0.0), 2),
                             "infrastructure": round(float(infrastructure or 0.0), 2)},
        "roi_pct": roi, "stock_turns_per_year": turns,
        "basis": DISTRIBUTOR_ROI_BASIS, "missing": missing,
        "gross_only": not monthly_operating_cost,
        "gross_only_why": gross_only_why if not monthly_operating_cost else "",
        "understated_investment": credit_extended in (None, ""),
        "understated_investment_why": understated_why if credit_extended in (None, "") else "",
    }
    if roi is not None:
        band = (" That sits inside the published 20-35% band." if 20 <= roi <= 40 else
                " That sits below the published 20-35% band - the lever is usually rotation or "
                "collection rather than a bigger margin." if roi < 20 else
                " That sits above the published band, which is worth checking: it usually means the "
                "investment base is understated rather than the route being exceptional.")
        out["reading"] = (f"{roi}% on {investment:,.0f} tied up, turning stock {turns} times a year."
                          + band)
    return out


def channel_contribution(consumer_price: float, *, gross_margin_pct: float, commission_pct: float,
                         fulfilment_per_unit: float = 0.0, storage_pct: float = 0.0,
                         listing_fee: float = 0.0, units_over_fee_period: float = 0.0) -> dict:
    """Whether a channel covers its own cost to serve. Computed, not borrowed.

    The widely quoted rule is that quick commerce needs a gross margin north of 65% to work. That is a
    useful warning and a bad input, because it is somebody else's deal. So this derives the break-even
    gross margin from the costs actually entered, and reports the real one alongside it.

    A listing fee is amortised over the units it buys, which is why `units_over_fee_period` matters: a
    Rs 25,000 per-SKU fee is trivial across fifty thousand units and fatal across five hundred.
    """
    if not consumer_price or consumer_price <= 0:
        return {"available": False,
                "why": "No consumer price given - every share below is a share of it."}
    if gross_margin_pct is None or gross_margin_pct <= 0:
        return {"available": False,
                "why": "No gross margin given. Without it there is nothing for the channel's costs to "
                       "be subtracted from, and the verdict would be about the costs alone."}
    if commission_pct is None:
        return {"available": False,
                "why": "No commission given. It is the largest platform cost in every quick-commerce "
                       "deal, and there is deliberately no default - enter the rate in your own "
                       "platform quote. Published rates run 15-30% of order value depending on "
                       "category and negotiated volume, which is a range for checking a quote "
                       "against rather than a figure to compute a verdict from."}

    cp = float(consumer_price)
    ful_pct = (float(fulfilment_per_unit or 0.0) / cp) * 100.0
    listing_pct = 0.0
    listing_note = ""
    if listing_fee:
        if not units_over_fee_period or units_over_fee_period <= 0:
            return {"available": False,
                    "why": f"A listing fee of {listing_fee:,.0f} was given with no unit volume to "
                           f"spread it over. The same fee is trivial across fifty thousand units and "
                           f"fatal across five hundred, so it cannot be judged without the volume."}
        listing_pct = (float(listing_fee) / (float(units_over_fee_period) * cp)) * 100.0
        listing_note = (f"{listing_pct:.1f}% of price, being {listing_fee:,.0f} spread over "
                        f"{units_over_fee_period:,.0f} units.")

    cost_to_serve = float(commission_pct) + float(storage_pct or 0.0) + ful_pct + listing_pct
    contribution = round(float(gross_margin_pct) - cost_to_serve, 1)
    breakeven_gm = round(cost_to_serve, 1)

    out = {
        "available": True,
        "consumer_price": cp, "gross_margin_pct": float(gross_margin_pct),
        "cost_to_serve_pct": round(cost_to_serve, 1),
        "parts": {"commission_pct": float(commission_pct), "storage_pct": float(storage_pct or 0.0),
                  "fulfilment_pct": round(ful_pct, 1), "listing_pct": round(listing_pct, 1)},
        "listing_note": listing_note,
        "contribution_pct": contribution,
        "contribution_per_unit": round(cp * contribution / 100.0, 2),
        "breakeven_gross_margin_pct": breakeven_gm,
        "clears": contribution > 0,
        "reference": RETAIL_COST_REFERENCE,
    }
    if contribution > 0:
        out["reading"] = (f"Every unit contributes {out['contribution_per_unit']:,.2f} after the "
                          f"channel's own costs. Break-even gross margin here is {breakeven_gm}%.")
    else:
        out["reading"] = (
            f"This channel does not cover its own cost to serve. It needs a gross margin above "
            f"{breakeven_gm}% and the pack carries {gross_margin_pct}%, so every incremental order "
            f"loses {abs(out['contribution_per_unit']):,.2f}. Volume makes that worse, not better - "
            f"the fix is a negotiated commission, a smaller pack range, or not listing.")
    return out


def talk_track(story: dict, pack_name: str = "the pack") -> str:
    """One sentence a TSI can actually say in a doorway, built from `margin_story`'s own numbers.

    Never invents a number `margin_story` did not compute. If the weekly figure is missing, the
    sentence stops at what IS known rather than filling the gap with something that sounds finished.
    """
    if not story.get("available"):
        return story.get("why", "Not enough to build a pitch from yet.")
    bits = [f"{pack_name}: {story['margin_pct']}% margin, {story['margin_per_unit']} per unit."]
    if story.get("margin_per_facing_per_week") is not None:
        bits.append(f"One facing earns roughly {story['margin_per_facing_per_week']} a week at the "
                    f"quoted rate of sale.")
    unb = story.get("unbranded")
    if unb:
        word = "more" if unb["advantage_per_unit"] >= 0 else "less"
        bits.append(f"That is {abs(unb['advantage_per_unit'])} {word} per unit than the loose or "
                   f"unbranded alternative.")
    return " ".join(bits)


# --- the reconciliation nobody draws -----------------------------------------------------------

def _price(v: str) -> float | None:
    m = re.search(r"-?\d+(?:\.\d+)?", str(v or "").replace(",", ""))
    return float(m.group()) if m else None


def price_reconciliation(s: dict) -> dict:
    """Effective consumer price in every channel, on one axis, with the collisions named.

    The single most valuable output here. The same strategy applied across channels produces stock
    imbalances and lost profitability, and it is invisible until the prices sit side by side. A channel
    whose price cannot be computed is plotted nowhere and said so — an invented price makes the whole
    strip unreliable, because nobody can then tell which marker is real.
    """
    points, missing = [], []
    for c in CHANNELS:
        if c["scope"] != "channel":
            continue
        node = s["channels"][c["key"]]
        p = _price(node.get("effective_price"))
        if p is None:
            missing.append({"channel": c["key"], "label": c["label"],
                            "why": str(node.get("effective_price") or "").strip()
                                   or "no effective price given"})
        else:
            points.append({"channel": c["key"], "label": c["label"], "price": p,
                           "role": node.get("role", "")})
    points.sort(key=lambda x: x["price"])

    collisions = []
    gt = next((p for p in points if p["channel"] == "trad"), None)
    for p in points:
        if not gt or p["channel"] == "trad":
            continue
        # A q-commerce or e-commerce price below the kirana who stocks you daily is a decision to stop
        # being stocked. It is the most expensive mistake on this page and the easiest to make quietly.
        if p["price"] < gt["price"] and p["channel"] in ("qcomm", "ecomm", "own_retail"):
            collisions.append({
                "under": p["channel"], "over": "trad",
                "gap": round(gt["price"] - p["price"], 2),
                "detail": (f"{p['label']} is {round(gt['price'] - p['price'], 2)} below "
                           f"{gt['label'].lower()}. The kirana who stocks you daily is being "
                           f"undercut — that buys volume and loses distribution.")})
    spread = round(points[-1]["price"] - points[0]["price"], 2) if len(points) > 1 else None
    return {"points": points, "missing": missing, "collisions": collisions, "spread": spread,
            "computable": len(points), "of": sum(1 for c in CHANNELS if c["scope"] == "channel")}


# --- validation: the skill's discipline, made checkable -----------------------------------------

def validate(s: dict, house: dict | None = None) -> list[dict]:
    out: list[dict] = []

    def add(level, ch, detail):
        out.append({"level": level, "layer": ch, "detail": detail})

    funded = []
    for c in CHANNELS:
        node = s["channels"][c["key"]]
        ch, label = c["key"], c["label"]
        has_any = any(str(node.get(f, "")).strip() for f in
                      ("role", "behaviour", "lever", "cost_per_unit", "effective_price"))
        if not has_any:
            continue
        funded.append(ch)

        # 1. a channel with no role does not get money
        if str(node.get("role", "")).lower() not in ROLES:
            add("open", ch, f"{label}: '{node.get('role') or 'no role'}' is not a role. One of: "
                            f"{', '.join(ROLES)} — a channel with no role does not get money.")

        # 2. name the behaviour, or drop the scheme
        beh = str(node.get("behaviour", "")).strip()
        if not beh:
            add("blocking", ch, f"{label}: no behaviour named. 'Activate {label.lower()}' is not a "
                                f"behaviour — say what someone will do differently, or drop it.")
        else:
            hit = next((w for w in EMPTY_BEHAVIOURS if re.search(rf"\b{w}\b", beh.lower())), "")
            if hit:
                add("blocking", ch, f"{label}: the behaviour is '{beh}'. {hit.capitalize()!r} buys "
                                    f"nothing you can measure. Name what the retailer or distributor "
                                    f"will DO differently — ordering weekly, two facings, adding a SKU.")
            elif not (str(node.get("baseline", "")).strip() and str(node.get("target", "")).strip()):
                add("open", ch, f"{label}: '{beh}' has no baseline and target. Without both there is "
                                f"nothing to measure the scheme against.")

        # 3. share of volume before any money
        share = str(node.get("share_now", "")).strip().lower()
        if not share or share in _UNKNOWN:
            add("open", ch, f"{label}: share of volume unknown. It is the number that makes the rest "
                            f"arguable — a confident trade plan on invented shares is worse than an "
                            f"honest gap.")

        # 4. the lever must plausibly cause the behaviour
        if not str(node.get("lever", "")).strip():
            add("open", ch, f"{label}: no lever. A behaviour with nothing behind it is a hope.")

        # 5. payback, or an explicit unknown — never a number nobody can source
        pay = str(node.get("payback", "")).strip().lower()
        if not pay:
            add("open", ch, f"{label}: no payback stated. Write the number, or write 'payback "
                            f"unknown' — an invented ROI is the most expensive sentence in a trade plan.")

        # 6. every incentive has a failure mode
        if not str(node.get("leakage", "")).strip():
            add("open", ch, f"{label}: no leakage mode named. Every trade incentive has one.")
        if not str(node.get("control", "")).strip():
            add("blocking", ch, f"{label}: no control against leakage. A scheme without one is a "
                                f"donation — 'we will monitor it' is not a control.")
        elif not str(node.get("residual_risk", "")).strip():
            add("open", ch, f"{label}: the control is named but not what it misses. Every control has "
                            f"a gap, and writing it down stops it being treated as a guarantee.")

        # 7. who receives the money determines who games it
        if not str(node.get("receives_money", "")).strip():
            add("open", ch, f"{label}: nobody named as receiving the money. Schemes paid to the person "
                            f"who reports the result are the ones gamed hardest.")

        # 8. sell-through, and primary is always flagged
        st = str(node.get("sell_through", "")).lower()
        if st not in SELL_THROUGH:
            add("open", ch, f"{label}: sell-through level not stated — primary, secondary or tertiary.")
        elif st == "primary":
            add("blocking", ch, f"{label}: primary-only. Movement here is dispatch, not demand — this "
                                f"produces phantom growth and a returns problem in six weeks. Say how "
                                f"secondary or tertiary offtake will be seen.")

        # a lever has to run through something
        if c["scope"] == "lever" and not node.get("runs_through"):
            add("blocking", ch, f"{label} is a lever, not a channel — it runs through the others. Name "
                                f"which ones, or its cost never lands against the behaviour it buys.")

    if not funded:
        add("empty", "", "Nothing filled in yet. Start with share of volume for each channel — it is "
                         "what makes every later number arguable.")

    # 9. the reconciliation
    rec = price_reconciliation(s)
    for col in rec["collisions"]:
        add("blocking", col["under"], col["detail"])
    if funded and rec["computable"] < 2:
        add("open", "", f"Effective consumer price is computable for {rec['computable']} of "
                        f"{rec['of']} channels, so the reconciliation cannot run. It is the check that "
                        f"prevents the most expensive mistake in a trade plan.")

    # 10. the message the trade hears
    tm = trade_message(house)
    if funded and not tm["has"]:
        add("open", "", f"No trade message: {tm['why']}.")

    # 11. thin data, thin plan. Expressed as the skill states it — say what share each channel holds
    # BEFORE assigning money — rather than as a count of blanks, so it stops once the shares are in
    # instead of nagging forever about channels nobody is spending on.
    known = sum(1 for c in CHANNELS
                if str(s["channels"][c["key"]].get("share_now", "")).strip().lower()
                not in ("",) + _UNKNOWN)
    if funded and known < 3:
        add("open", "", f"Money is being assigned with share of volume known for only {known} "
                        f"channel(s). Keep this plan short and say what it needs — trade money moves "
                        f"fast and quietly, so a confident plan on invented shares does more damage "
                        f"here than anywhere else.")

    # 12. the channels with no screen yet. Silence about them would read as a decision nobody made.
    for c in CHANNELS:
        if not c.get("no_screen_yet") or not funded:
            continue
        node = s["channels"][c["key"]]
        if not any(str(node.get(f, "")).strip() for f in _CH_FIELDS):
            add("open", c["key"],
                f"{c['label']} has nothing against it. {c['rewards'].split('—')[-1].strip().capitalize()}"
                f" — a route to market that omits it has made that call by accident.")
    return out


def outstanding(s: dict) -> int:
    """Elements not yet agreed. The right rail's number.

    Counts only channels that have a screen. A rail saying 34 outstanding against 28 visible rows would
    read as a bug in the rail rather than as two channels nobody has built a tab for — the un-screened
    channels are raised as their own finding instead, where the reason is legible.
    """
    n = 0
    for c in CHANNELS:
        if c.get("no_screen_yet"):
            continue
        for e in s["channels"][c["key"]]["elements"].values():
            if e.get("status") != "agreed":
                n += 1
    return n


def status(s: dict, house: dict | None = None) -> dict:
    fs = findings_mod.annotate(validate(s, house), s.get("overrides"))
    chans = []
    for c in CHANNELS:
        node = s["channels"][c["key"]]
        els = [dict(e, label=next(x["label"] for x in c["elements"] if x["key"] == e["key"]), asks=next(x["asks"] for x in c["elements"] if x["key"] == e["key"]))
               for e in node["elements"].values()]
        chans.append({
            **{k: node.get(k, "") for k in _CH_FIELDS},
            "key": c["key"], "label": c["label"], "scope": c["scope"],
            "shorthand": c["shorthand"], "rewards": c["rewards"], "goes_wrong": c["goes_wrong"],
            "runs_through": node.get("runs_through", []),
            "elements": els,
            "agreed": sum(1 for e in els if e["status"] == "agreed"),
            "of": len(els),
            "findings": [f for f in fs if f["layer"] == c["key"]],
        })
    # Sorted by share of volume descending — the biggest channel first even when it is the least
    # exciting, especially then. Unknown shares sink rather than leading.
    chans.sort(key=lambda c: (-(_price(c.get("share_now")) or -1), c["label"]))
    return {
        "id": s["id"], "brand": s.get("brand", ""), "plan": s.get("plan", ""),
        "house": s.get("house", ""), "updated": s.get("updated", ""),
        "channels": chans, "roles": ROLES, "levers": list(LEVERS),
        "sell_through": SELL_THROUGH, "states": list(ELEMENT_STATES),
        "message": trade_message(house),
        "reconciliation": price_reconciliation(s),
        "findings": fs, "blocking": findings_mod.live_blocking(fs),
        "overridden": findings_mod.overridden_count(fs),
        "outstanding": outstanding(s),
    }


# --- generation -------------------------------------------------------------------------------

def _skill_text() -> str:
    parts = []
    for rel in ("SKILL.md", os.path.join("references", "channels.md"),
                os.path.join("references", "leakage.md")):
        f = os.path.join(_SKILL, rel)
        if os.path.exists(f):
            parts.append(open(f, encoding="utf-8").read())
    return "\n\n".join(parts)


def prompt_for(s: dict, ch: str, house: dict | None = None, el: str = "", extra: str = "",
               anchors: str = "", rules: str = "") -> str:
    """The instruction for one channel, or one element of one. Inspectable, like the others."""
    c = CHANNEL_BY_KEY[ch]
    node = s["channels"][ch]
    out = [_skill_text(),
           "\n\n---\nTHE BRAND\n" + brandprofile.voice_block(brandprofile.resolve(house, s))]
    tm = trade_message(house)
    out.append("\n\n---\nTHE TRADE MESSAGE\n" + (
        "\n".join(f"  - {o['text']}" for o in tm["options"]) if tm["has"]
        else f"NONE — {tm['why']}. Say so in the output. Do NOT borrow the consumer line."))
    if house:
        out.append(f"\nConsumer core (context only, NOT for the trade): "
                   f"{'; '.join(strategy._chosen_text(house, 'core'))}")
    out.append(f"\n\n---\nTHIS CHANNEL: {c['label']}\n{c['shorthand']}\n"
               f"What it rewards: {c['rewards']}\nHow it goes wrong: {c['goes_wrong']}")
    filled = {k: v for k, v in node.items() if k in _CH_FIELDS and str(v).strip()}
    if filled:
        out.append("\n\n---\nALREADY DECIDED HERE\n"
                   + "\n".join(f"  {k}: {v}" for k, v in filled.items()))
    others = [(CHANNEL_BY_KEY[k]["label"], s["channels"][k].get("effective_price", ""))
              for k in s["channels"] if k != ch and str(s["channels"][k].get("effective_price", "")).strip()]
    if others:
        out.append("\n\n---\nEFFECTIVE CONSUMER PRICE ELSEWHERE (do not collide with these)\n"
                   + "\n".join(f"  {a}: {b}" for a, b in others))
    if anchors:
        out.append("\n\n---\n" + anchors)
    if rules:
        out.append("\n\n---\n" + rules)
    if extra.strip():
        out.append("\n\n---\nTHE USER ADDS\n" + extra.strip())

    if el:
        spec = next((x for x in c["elements"] if x["key"] == el), None)
        out.append(f"\n\n---\nNOW WRITE: {spec['label']}\n{spec['asks']}\n"
                   "Write it for the person who has to use it at the counter, not for a deck.\n"
                   'Return ONLY JSON: {"brief":"..."}')
    else:
        out.append(
            "\n\n---\nNOW: fill this channel.\n"
            "Name the BEHAVIOUR with a baseline and a target — not 'visibility', which buys nothing "
            "measurable. State payback, or the literal string 'payback unknown'. Name the leakage mode, "
            "the control, and what the control misses. State sell-through as primary, secondary or "
            "tertiary. Name who receives the money.\n"
            'Return ONLY JSON: {"role":"","share_now":"","behaviour":"","baseline":"","target":"",'
            '"lever":"","cost_per_unit":"","payback":"","leakage":"","control":"","residual_risk":"",'
            '"sell_through":"","receives_money":"","effective_price":"","owner":"","source":""}\n'
            "Leave a field empty rather than inventing a share, a margin, an outlet count or a "
            "platform fee. Those are exactly the numbers that get invented.")
    return "\n".join(out)


def generate(s: dict, ch: str, house: dict | None = None, el: str = "", extra: str = "",
             anchors: str = "", rules: str = "") -> tuple[dict, str]:
    if ch not in CHANNEL_BY_KEY:
        return s, "No such channel."
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return s, "No ANTHROPIC_API_KEY — the sheet can still be filled in by hand."
    data, err = jsonout.ask_json(prompt_for(s, ch, house, el, extra, anchors, rules), max_tokens=3000)
    if data is None:
        return s, f"Generation failed: {err}"
    if el:
        s2, err = set_element(s, ch, el, brief=str(data.get("brief") or ""), status="briefed")
        return (s2 or s), err
    data["source"] = "model"
    return set_channel(s, ch, data) or s, ""
