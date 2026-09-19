"""prompts.py — the "master prompt" layer for The Marketing Studio.

Every AI feature calls `/complete`, and this module supplies the SYSTEM prompt so output is in the shape
each studio expects and holds to the same standards. It is additive: the caller still sends its own
per-call instruction specifying the JSON format; this layer governs craft, discipline and grounding.

**The craft is the product; the brand is data.** This file used to open by naming one dairy company, its
hero product, its master idea and its market — about fifteen more sites did the same. That text was not
decoration: it is the grounding that makes output specific rather than generic-global-FMCG. So it has not
been deleted, it has been *moved* — into a brand profile a person edits (`brandprofile.py`), and injected
here at assembly time.

What remains in this file is the part that is true for any brand in any category: one idea per asset,
never invent a statistic, obey the requested format, be concrete about the market you were told about.

`system_for(messages, brand=…)` returns: craft + the brand's own grounding + the matching surface block
(brief / social / video / insights), detected from the caller's role phrase.
"""
from __future__ import annotations

import sys

import brandprofile
import character

# ---------------------------------------------------------------- global master
# Brand-agnostic on purpose. The one thing it must NOT do is imply a category, a market or a claim the
# brand profile has not stated — a prompt that assumes dairy will write dairy for a software company.
GLOBAL_MASTER = """You are the senior AI creative & strategy partner inside The Marketing Studio.

CRAFT
- Emotionally honest and specific; avoid hype, superlatives and generic marketing filler.
- One idea per asset. Lead with a human benefit or tension, not a feature list.
- Connect a product truth to a human benefit. A benefit with no truth behind it is a slogan.
- Write like a brand people already know, not like a launch deck.

GROUNDING — the discipline that matters most
- Be concrete about the market you have been told about: real occasions, routines and idiom, in that
  market's English and its currency. Do NOT import the habits of a market you were not given.
- Do NOT invent statistics, awards, certifications, market shares or claims. Use only what is in the
  brief, the brand profile and the inputs. If a number is not given, do not state one.
- Make no medical, therapeutic or absolute health promise, and stay inside what this brand's category and
  regulator would allow. If you are unsure whether a claim is permitted, do not make it.
- Never name or disparage a competitor unless the input explicitly asks for a comparison; even then stay
  factual.
- Where the brand has a master idea, let the work ladder to it — do not force the exact phrase into
  every line.

OUTPUT DISCIPLINE (critical)
- The user's instruction specifies the exact output format. Obey it precisely.
- When JSON is requested, return ONLY valid, parseable JSON — no markdown code fences, no ```-blocks, no
  commentary, no preamble or trailing text. Use the exact keys requested, in plain double-quoted strings.
- Respect any length limit stated (e.g. "1-2 sentences each"). Keep within it.
"""

# ---------------------------------------------------------------- brief builder
BRIEF = """
TASK CONTEXT — BRIEF BUILDER
You are writing a marketing brief. Make it genuinely usable by an agency, not boilerplate.
- Each field must be distinct and non-overlapping — don't repeat the background inside the objective, etc.
- Business objective = commercial (sales, share, penetration, trial); communication objective = what the message must do (awareness, consideration, action). Keep them different.
- The single-minded proposition must be truly single-minded: one sharp thought, not a list.
- Consumer insight = a real human truth or tension, not a product feature restated.
- Reasons to believe = concrete, provable proof points from the brand's own process, sourcing or
  performance — no invented data.
- KPIs must be measurable. Mandatories should name this brand's real codes — the logo, its master line,
  its pack cues — taken from the brand profile, never invented.
- Keep each field to the requested length (typically 1-2 sentences) and specific to the market given.
"""

# ---------------------------------------------------------------- social studio
SOCIAL = """
TASK CONTEXT — SOCIAL STUDIO
You are writing platform-native social posts. Adapt genuinely to each platform — do not reuse one caption across all.
- Facebook: warm and community-minded, a little longer; framed around the everyday moment.
- Instagram: punchy and sensory, short lines, minimal emoji (one or two at most), scroll-stopping first line.
- LinkedIn: professional and purpose-led — supply chain, quality, the people behind the product; NO
  emoji, no hashtag spam.
- Caption: open with an emotional hook or benefit, land the brand's own idea, close with a light,
  natural CTA. Never keyword-stuff.
- Hashtags: 3-6 only, blending the brand's own tags (from the brand profile) with a couple of
  category or reach tags. No walls of hashtags, and never invent a brand tag.
- "visual": exactly one concrete art-direction line an art director could shoot (subject, setting, mood) — not a sentence of adjectives.
- Keep it true to the market given and free of invented claims.
- One post per platform is a sample, not a plan. Unless you were asked for exactly one, give at least
  three per platform and make them do different jobs — the one that recruits, the one that proves, the
  one that belongs to an occasion. Three near-identical captions are one post; say so instead.
- If an idea platform is in force above, every post is one expression of it, and the set should read as
  a campaign rather than as three unrelated good posts.
- If the IMC plan above names the channels bought, write for those. A brilliant post for a platform
  nobody bought is work nobody can use.
"""

# ---------------------------------------------------------------- video studio
VIDEO = """
TASK CONTEXT — VIDEO STUDIO
You are a film director scripting a short brand film. Make it filmable and emotionally resonant, not a voiceover essay.
- logline: one evocative sentence that tells a story with a human at its centre — a scene, not a slogan.
- Structure the scenes as distinct beats that build: everyday setup -> a small tension or need -> the
  brand truth that answers it -> resolution. No repeated beats.
- Each scene: keep the time code, give it a short title and a vivid, shootable description (who, where,
  what we see), grounded in real life in the market you were given.
- vo: a single, human, spoken line — understated, never a tagline dump.
- duration: realistic for the beats (e.g. 30s / 45s).
- If revising an existing script, change ONLY what the direction asks and preserve what already works.
"""

# ---------------------------------------------------------------- insights
INSIGHTS = """
TASK CONTEXT — INSIGHTS
You are analysing campaign performance for a marketing leader.
- Ground every statement in the numbers/cohorts provided; never fabricate metrics.
- Lead with the "so what" (the decision or action), then the evidence.
- Be candid about weak spots, not just wins. Keep it crisp and executive-ready.
"""

_SURFACES = [
    (VIDEO,   ("film director", "short film script", '"scenes"', "logline", "storyboard")),
    (SOCIAL,  ("social media writer", "platform-adapted posts", "platform-native", "captions and hashtags", "instagram")),
    (BRIEF,   ("brief writer", "brief for this request", "convert the following external inputs", "structured", "single-minded")),
    (INSIGHTS,("performance", "insight", "cohort", "analyse", "analyze", "roas")),
]


def _detect(text: str) -> str:
    t = text.lower()
    for block, keys in _SURFACES:
        if any(k in t for k in keys):
            return block
    return ""


# ---------------------------------------------------------------- the spine
# The strategy that has actually been decided, injected into every client-side prompt.
#
# This exists because of a real and reasonable complaint: the executions "do not seem to be taking the
# plan, brief and platform into account". They were not, and the reason is structural rather than a bug.
# The client composes each execution's prompt itself and sends it to `/complete`; those prompts were
# written before the house, the plan and the idea platform existed, so they ask for a good post in a
# vacuum. Every one of them, though, passes through this function on the way out — which makes this the
# one place the spine can be attached without the client changing a line.
#
# It goes in as CONSTRAINT rather than context, and it goes in AFTER the caller's own instruction is
# accounted for, because the failure mode here is not omission — it is a model that reads a nice-to-have
# list of facts and writes around them.

def _execution_block(execution_id: str) -> str:
    """The ONE briefed piece this call is for, stated above everything else.

    Without this the spine listed every audience in the plan with equal weight, and the model picked
    whichever suited the line it wanted to write. A post briefed for rival-pack buyers came back written
    for loose-milk buyers — both are in the plan, so nothing in the prompt was false, and nothing made the
    briefed one win either.

    A brief that names four audiences has named none. This names one.
    """
    if not execution_id:
        return ""
    try:
        import execution as execution_mod
    except Exception:                                        # pragma: no cover
        return ""
    e = execution_mod.load(execution_id)
    if not e:
        return ""
    b = e.get("brief") or {}
    out = []

    def cell(field, label, *, verbatim=False):
        v = b.get(field)
        if isinstance(v, dict):
            v = " · ".join(f"{k}={x}" for k, x in v.items()
                           if k not in ("id", "source", "added", "edited") and str(x or "").strip())
        v = str(v or "").strip()
        if v:
            out.append(f"{label}: {v}" + ("  — use this wording, do not paraphrase" if verbatim else ""))

    cell("audience", "WRITE FOR THIS AUDIENCE, AND NO OTHER")
    cell("channel", "In this channel")
    cell("occasion", "For this occasion")
    cell("measure", "Judged on")
    if b.get("pillar"):
        out.append(f"Serving the {b['pillar']} pillar — not the other one")
    if isinstance(b.get("message"), dict) and str(b["message"].get("text") or "").strip():
        out.append(f"The message it carries: {b['message']['text']}  — verbatim, do not paraphrase")
    # Priority geography (round 92) — the one field `execution.brief_from` attaches outside the six
    # cells above (see that function's own comment on why). Language is stated as an instruction, not
    # background: a plan naming a state whose principal language the studio holds no code for is a real
    # gap a generated piece must say out loud, not quietly write around in English/Hindi as if it fit.
    geo = b.get("geography") or {}
    if geo.get("by_state"):
        states_txt = ", ".join(x["label"] for x in geo["by_state"] if x.get("label"))
        if states_txt:
            out.append(f"Priority geography for this piece: {states_txt} — write for these places' own "
                       f"idiom and context, not a generic national one")
        gaps = geo.get("language_gaps") or []
        if gaps:
            gap_txt = "; ".join(f"{g['label']} ({g.get('gap', '')})" for g in gaps if g.get("label"))
            out.append("LANGUAGE GAP, SAY SO — do not silently write around this: " + gap_txt
                       + ". State plainly that this piece is written in a language this audience may not "
                         "speak first, rather than presenting it as though it fits.")
    if not out:
        return ""
    return ("THIS PIECE OF WORK, SPECIFICALLY\n"
            "Everything below in THE STRATEGY is the whole campaign. This is the one row of it you are "
            "writing now, and where the two differ, this wins.\n"
            + "\n".join(f"  {x}" for x in out))


def _resolve_house(brand: dict | None) -> dict | None:
    import strategy
    # Round 5 (brand-grounding, discovered live): `brand=None` reaching this function IS the
    # brand_mode="general" signal from system_for() two frames up — the caller already made the
    # disciplined choice not to invent a brand for this piece. `not want` used to treat that the same
    # as "no filter given, return whatever house is newest" — so a General-mode Social post or video
    # script silently carried the newest house in the whole tenant's real core message, RTBs and
    # avoid-list. `want` empty (whether from `brand=None` or a brand profile with no name) now means
    # "nothing to match" — no house, not every house — same discipline the rest of this project already
    # applies everywhere else a brand name gates a lookup.
    want = str((brand or {}).get("brand") or "").strip().lower()
    if not want:
        return None
    try:
        for row in strategy.houses():
            if str(row.get("brand", "")).lower() == want:
                return strategy.load(row["id"])
    except Exception as e:
        # Real bug found live (round-83 audit): this used to return "" with no trace at all —
        # indistinguishable from the normal, expected "no house for this brand yet" case, so a
        # malformed house document silently dropped every subsequent generation's brand grounding
        # with nothing in the logs pointing at why. Logging doesn't change the return value — an
        # empty block is still the right degrade — it just makes the failure findable, not invisible.
        print(f"[prompts] _resolve_house: could not read the house for {want or 'the brand'!r}: {e}",
              file=sys.stderr, flush=True)
    return None


def house_block(brand: dict | None = None) -> str:
    """The messaging house's own words: core/emotional/functional message, sourced RTBs, the avoid-list,
    per-medium message. Split out (round 93) from what used to be one inseparable `spine_block()` so a
    person can switch the house's grounding off independently of the idea platform's — see
    `spine_block()`, which composes this with `platform_block()`/`plan_channels_block()` per three
    independently switchable flags rather than one."""
    try:
        import strategy
    except Exception as e:                                   # pragma: no cover - import guard
        print(f"[prompts] house_block: could not import strategy: {e}", file=sys.stderr, flush=True)
        return ""
    house = _resolve_house(brand)
    if not house:
        return ""

    out = []
    core = strategy._chosen_text(house, "core")
    if core:
        out.append("Core message (chosen by a person — every execution expresses THIS): "
                   + "; ".join(core))
    for lid, label in (("emotional", "Emotional message"), ("functional", "Functional message")):
        v = strategy._chosen_text(house, lid)
        if v:
            out.append(f"{label}: " + "; ".join(v))
    rtb = [t for lid in ("ertb", "frtb") for t in strategy._chosen_text(house, lid)]
    if rtb:
        out.append("Reasons to believe — the ONLY things you may offer as proof: " + "; ".join(rtb))

    node = (house.get("nodes") or {}).get("medium") or {}
    picked = set(node.get("chosen") or [])
    by_medium = [f"{o.get('tag') or 'general'!s}: {o['text'].strip()}"
                 for o in node.get("options", [])
                 if o["id"] in picked and str(o.get("text") or "").strip()]
    if by_medium:
        out.append("What the brand says in each medium — use the one for the medium you are writing:\n"
                   + "\n".join(f"  - {x}" for x in by_medium))

    avoid = [o["text"] for o in ((house.get("nodes") or {}).get("culture") or {}).get("options", [])
             if o["id"] in set(((house.get("nodes") or {}).get("culture") or {}).get("chosen") or [])
             and str(o.get("tag", "")).lower() == "avoid"]
    if avoid:
        out.append("MUST NOT DO: " + "; ".join(avoid))
    return "\n".join(out)


def platform_block(brand: dict | None = None) -> str:
    """The idea platform's own detail: insight, mechanic, territory, proof, the reason-to-believe it
    dramatises, and how it is already expressed elsewhere. It is the strongest constraint in the spine:
    the point of adopting a platform is that every execution becomes a different expression of the same
    idea. Returns the "no platform adopted" guidance sentence when none is chosen for this house — that
    sentence is about the platform's own absence, so it only appears when a caller actually asks for this
    block, never when one has switched it off entirely."""
    try:
        import ideas as ideas_mod
    except Exception as e:
        print(f"[prompts] platform_block: could not import ideas: {e}", file=sys.stderr, flush=True)
        return ""
    house = _resolve_house(brand)
    if not house:
        return ""

    out = []
    plat = None
    try:
        plat = ideas_mod.chosen_platform(ideas_mod.for_house(house.get("id", "")))
    except Exception:
        plat = None
    if plat and str(plat.get("idea") or "").strip():
        out.append(f"THE IDEA PLATFORM — \"{plat.get('name') or 'unnamed'}\": "
                   f"{str(plat['idea']).strip()}")
        # Round 92: the platform is saved with seven fields (`ideas._FIELDS`), and this block used to
        # surface only two of them (`idea`, `mechanic`) — every generator wrote from the platform's
        # headline sentence with none of its own supporting insight, proof or territory behind it. Found
        # live, asking specifically about video: "even before channels, we need the film grounded in the
        # SMP/house/platform big idea with insights pooled in from the platform" — traced to this exact
        # gap, shared by every producer that goes through `system_for()`, not video-specific.
        if str(plat.get("why") or "").strip():
            out.append(f"Why this bet — the insight it's built on: {plat['why'].strip()}")
        if str(plat.get("mechanic") or "").strip():
            out.append(f"Its repeatable device: {plat['mechanic'].strip()}")
        if str(plat.get("territory") or "").strip():
            out.append(f"The world it lives in: {plat['territory'].strip()}")
        if str(plat.get("proof") or "").strip():
            out.append(f"What it demonstrates: {plat['proof'].strip()}")
        # `plat['rtb']` is meant to hold an RTB's id (the platform-draft prompt asks for exactly that),
        # but `ideas.py`'s own comments flag `rtb`/`rtb_id` as an inconsistent field across this codebase
        # — confirmed live: the real platform checked here has free TEXT in `rtb`, not an id. Handle
        # both rather than silently dropping the honest case: resolve against the house's sourced RTBs
        # when it matches an id, otherwise the field's own text is already the claim.
        rtb_raw = str(plat.get("rtb") or "").strip()
        if rtb_raw:
            try:
                basis_rtbs = ideas_mod.house_basis(house).get("rtbs", [])
            except Exception:
                basis_rtbs = []
            row = next((r for r in basis_rtbs if r.get("id") == rtb_raw), None)
            rtb_text = row["text"].strip() if (row and str(row.get("text") or "").strip()) else rtb_raw
            out.append(f"The reason-to-believe it dramatises: {rtb_text}")
        expr = {k: str(v).strip() for k, v in (plat.get("expressions") or {}).items()
                if str(v or "").strip()}
        if expr:
            out.append("How it is already expressed elsewhere — be consistent with these and do not "
                       "repeat them verbatim:\n"
                       + "\n".join(f"  - {k}: {v}" for k, v in expr.items()))
        out.append("Everything you write is one expression of that platform. If what you are asked for "
                   "cannot be an expression of it, say so rather than writing around it.")
    else:
        out.append("No idea platform has been adopted. Work from the messages above; do not invent a "
                   "campaign idea and present it as settled.")
    return "\n".join(out)


def plan_channels_block(brand: dict | None = None) -> str:
    """Channels bought/audiences/phasing/measures from ANY plan matching the brand — the ambient signal,
    not a specific bound execution (that is `_execution_block()`, gated in `system_for()` by the SAME
    `use_plan` flag as this function, so "Plan" reads on screen as one switch, not two)."""
    try:
        import plan as plan_mod
    except Exception as e:
        print(f"[prompts] plan_channels_block: could not import plan: {e}", file=sys.stderr, flush=True)
        return ""
    # Same fix as _resolve_house() above, same reason: `brand=None` (General mode) must mean "no plan
    # matches", not "any plan matches" — `not want` used to hand the newest plan in the tenant to a
    # General-mode prompt, real channels/audiences/phasing/measures included.
    want = str((brand or {}).get("brand") or "").strip().lower()
    out = []
    if not want:
        return ""
    try:
        pl = next((p for p in plan_mod.plans() if str(p.get("brand", "")).lower() == want), None)
        p = plan_mod.load(pl["id"]) if pl else None
    except Exception:
        p = None
    if p:
        for lid, label in (("channels", "Channels bought"), ("audiences", "Audiences"),
                           ("phases", "Phasing"), ("measures", "How it is measured")):
            rows = [r for r in ((p.get("nodes") or {}).get(lid) or {}).get("rows", [])]
            bits = [" / ".join(str(v).strip() for k, v in r.items()
                               if k not in ("id", "source", "added", "edited") and str(v or "").strip())
                    for r in rows]
            bits = [b for b in bits if b][:6]
            if bits:
                out.append(f"{label} (from the IMC plan): " + " | ".join(bits))
    return "\n".join(out)


def spine_block(brand: dict | None = None, *, use_house: bool = True,
                use_platform: bool = True, use_plan: bool = True) -> str:
    """What has been decided upstream, as binding constraint — composed from three independently
    switchable pieces. Empty string when nothing has been decided, or when a caller has switched all
    three off.

    Round 93: split from one inseparable function into three (`house_block`/`platform_block`/
    `plan_channels_block`), after a live ask specifically about video: "if all three (plan/idea/brief)
    are switched off, only the prompt and the brand profile should be the input; the user should have a
    choice of choosing brief, messaging house, idea platform and the plan independently." Before this,
    turning the idea platform off silently also dropped the house's core message/RTBs/avoid-list,
    because both lived in one function gated by one flag — a real gap between what the on-screen copy
    promised ("the idea platform is set aside") and what actually left the prompt.
    """
    out = []
    if use_house:
        h = house_block(brand)
        if h:
            out.append(h)
    if use_platform:
        p = platform_block(brand)
        if p:
            out.append(p)
    if use_plan:
        pc = plan_channels_block(brand)
        if pc:
            out.append(pc)
    if not out:
        return ""
    return ("THE STRATEGY ALREADY DECIDED — BINDING\n"
            "These are decisions a person made in the messaging house, the idea platform and the IMC "
            "plan. They are not suggestions and they are not background. Where your instruction below "
            "and this section disagree, this section wins; where your instruction asks for something "
            "these do not cover, say what is missing rather than inventing it.\n\n"
            + "\n\n".join(out))


def system_for(messages: list[dict], brand: dict | None = None, brand_mode: str = "grounded",
              execution: str = "", force_typed: bool = False, skip_mandatories: bool = False,
              use_house: bool = True, use_platform: bool = True, use_plan: bool = True) -> str:
    """Craft + this brand's grounding + what has been decided + the detected surface block.

    `brand` is resolved by the caller when it knows which brand is in play; otherwise the single profile
    on file is used. With no profile at all, `voice_block` returns an explicit "you do not know the
    category — do not invent one", which produces cautious copy somebody can fix rather than a confident
    invention nobody can see.

    `brand_mode="general"` — SECURITY / DATA INTEGRITY, the root of the whole grounding-modes project
    (see BRAND_GROUNDING_MODES_PLAN.md): every caller of `/complete` used to reach this function with no
    way to say "this piece is deliberately not tied to a brand." `brand or brandprofile.resolve()` then
    ALWAYS fell to whichever brand was active — the shared chokepoint behind nearly every text generation
    in the app, silently grounding General-mode work in whatever happened to be active. `general` skips
    resolution entirely, same honest `voice_block(None)` treatment as a Grounded piece with no profile
    at all, but chosen on purpose rather than landed on by accident.

    `spine_block` is what makes an execution written client-side still obey the house, the platform and
    the plan — see the note above it. It is empty until somebody has actually decided something, so a
    first-time user's prompt is unchanged.

    Round 93 — `use_house` / `use_platform` / `use_plan`: three independent switches, one per input a
    person can see on screen (Brief is a fourth, handled entirely client-side by the caller — it never
    reaches this function). Each defaults on; a caller can drop any one without losing the others, which
    `force_typed` alone could never do (it dropped house and platform together, because they used to
    live in one inseparable function). Live ask this came from: "if all three (plan/idea/brief) are
    switched off, only the prompt and the brand profile should be the input" — turning all three off,
    plus not linking a brief client-side, reaches exactly that state.

    `force_typed` — round 92's original cross-producer "set the platform aside" checkbox, kept for
    callers not yet updated to the three-flag model above. Composes with the new flags rather than
    fighting them: it forces house/platform/the ambient plan-channels signal off regardless of what
    `use_house`/`use_platform`/`use_plan` say, exactly as it always did, but leaves `_execution_block`
    (the plan's own bound audience/channel/occasion/measure/message) alone — that one only responds to
    `use_plan` now, never to `force_typed`, matching what every producer's "cannot override" notice
    already promised on screen before this round existed.

    `skip_mandatories` — separate again: the caller's own read on whether none of the plan/idea/brief
    trio applies to this piece at all. See `brandprofile.voice_block`'s own docstring for exactly what
    this drops and why it's all-or-nothing.
    """
    text = " ".join(str(m.get("content", "")) for m in messages if m.get("role") != "assistant")
    b = None if brand_mode == "general" else (brand or brandprofile.resolve())
    surface = _detect(text)
    eff_house = use_house and not force_typed
    eff_platform = use_platform and not force_typed
    eff_plan_channels = use_plan and not force_typed
    # The spine binds executions, not briefs. A brief is upstream of the house — it is where the next
    # problem gets stated — so constraining it by the platform the LAST brief produced would quietly
    # make every brief a restatement of the current campaign, and the loop would never open again.
    spine = "" if surface is BRIEF else spine_block(b, use_house=eff_house, use_platform=eff_platform,
                                                     use_plan=eff_plan_channels)
    # The briefed piece goes LAST of the grounding blocks, closest to the instruction, because it is the
    # narrowest thing in the prompt and the one the rest has to yield to. Gated on `use_plan` only — the
    # "Plan" switch a person actually sees on screen ("Briefed from the plan") — independent of
    # `force_typed`, which never touched it before this round and still doesn't.
    this_one = "" if (surface is BRIEF or not use_plan) else _execution_block(execution)
    # The brand's approved recurring character, when it has one. A brand fact, not a campaign
    # decision, so it sits with the voice block — but suppressed on a BRIEF, which is upstream of any
    # casting. Social posts, carousels and video scripts all reach this function through /complete.
    character_block = "" if surface is BRIEF else character.for_prompt(b)
    parts = (GLOBAL_MASTER, "THE BRAND\n" + brandprofile.voice_block(b, skip_mandatories=skip_mandatories),
             character_block, spine, this_one, surface)
    return "\n\n".join(x for x in parts if x).strip()
