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


def spine_block(brand: dict | None = None) -> str:
    """What has been decided upstream, as binding constraint. Empty string when nothing has been."""
    try:
        import ideas as ideas_mod
        import plan as plan_mod
        import strategy
    except Exception as e:                                   # pragma: no cover - import guard
        print(f"[prompts] spine_block: could not import ideas/plan/strategy: {e}",
              file=sys.stderr, flush=True)
        return ""

    want = str((brand or {}).get("brand") or "").strip().lower()
    house = None
    try:
        for row in strategy.houses():
            if not want or str(row.get("brand", "")).lower() == want:
                house = strategy.load(row["id"])
                break
    except Exception as e:
        # Real bug found live (round-83 audit): this used to return "" with no trace at all —
        # indistinguishable from the normal, expected "no house for this brand yet" case just below,
        # so a malformed house/plan document silently dropped every subsequent generation's brand
        # grounding (core message, RTBs, avoid-list) with nothing in the logs pointing at why. Logging
        # here doesn't change the return value — an empty spine is still the right degrade so a caller
        # never crashes on a bad document — it just makes the failure findable instead of invisible.
        print(f"[prompts] spine_block: could not read the house for {want or 'the brand'!r}: {e}",
              file=sys.stderr, flush=True)
        return ""
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

    # The idea platform, when one has been chosen. It is the strongest constraint in this block: the
    # point of adopting one is that every execution becomes a different expression of the same idea.
    plat = None
    try:
        plat = ideas_mod.chosen_platform(ideas_mod.for_house(house.get("id", "")))
    except Exception:
        plat = None
    if plat and str(plat.get("idea") or "").strip():
        out.append(f"\nTHE IDEA PLATFORM — \"{plat.get('name') or 'unnamed'}\": "
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
        out.append("\nNo idea platform has been adopted. Work from the messages above; do not invent a "
                   "campaign idea and present it as settled.")

    # The plan says where and when. A post written against a channel nobody bought is a nice post.
    try:
        pl = next((p for p in plan_mod.plans()
                   if not want or str(p.get("brand", "")).lower() == want), None)
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

    if not out:
        return ""
    return ("THE STRATEGY ALREADY DECIDED — BINDING\n"
            "These are decisions a person made in the messaging house, the idea platform and the IMC "
            "plan. They are not suggestions and they are not background. Where your instruction below "
            "and this section disagree, this section wins; where your instruction asks for something "
            "these do not cover, say what is missing rather than inventing it.\n\n"
            + "\n".join(out))


def system_for(messages: list[dict], brand: dict | None = None, execution: str = "",
              force_typed: bool = False, skip_mandatories: bool = False) -> str:
    """Craft + this brand's grounding + what has been decided + the detected surface block.

    `brand` is resolved by the caller when it knows which brand is in play; otherwise the single profile
    on file is used. With no profile at all, `voice_block` returns an explicit "you do not know the
    category — do not invent one", which produces cautious copy somebody can fix rather than a confident
    invention nobody can see.

    `spine_block` is what makes an execution written client-side still obey the house, the platform and
    the plan — see the note above it. It is empty until somebody has actually decided something, so a
    first-time user's prompt is unchanged.

    `force_typed` — round 92's cross-producer "set the platform aside for this piece" checkbox. Same
    real, deliberate-override semantics as `producers.stands_on`'s own `force_typed` (that function's
    docstring explains why this needs to be an explicit act, not a silent fallback) — this is the
    equivalent for the producers that go through `/complete` instead of a dedicated route (Social,
    later Video), so the checkbox means the same thing everywhere it appears. Skips `spine_block` only —
    the house's core/RTB/medium messaging, which is what "the platform" is standing on — never
    `_execution_block`: the plan's own audience/channel/occasion/measure/message stay binding regardless,
    exactly what every producer's own "cannot override" notice already promises on screen.

    `skip_mandatories` — separate from `force_typed`, and only meaningful combined with it: the caller's
    own read on whether none of the plan/idea/brief trio applies to this piece at all. See
    `brandprofile.voice_block`'s own docstring for exactly what this drops and why it's all-or-nothing.
    """
    text = " ".join(str(m.get("content", "")) for m in messages if m.get("role") != "assistant")
    b = brand or brandprofile.resolve()
    surface = _detect(text)
    # The spine binds executions, not briefs. A brief is upstream of the house — it is where the next
    # problem gets stated — so constraining it by the platform the LAST brief produced would quietly
    # make every brief a restatement of the current campaign, and the loop would never open again.
    spine = "" if (surface is BRIEF or force_typed) else spine_block(b)
    # The briefed piece goes LAST of the grounding blocks, closest to the instruction, because it is the
    # narrowest thing in the prompt and the one the rest has to yield to.
    this_one = "" if surface is BRIEF else _execution_block(execution)
    parts = (GLOBAL_MASTER, "THE BRAND\n" + brandprofile.voice_block(b, skip_mandatories=skip_mandatories),
             spine, this_one, surface)
    return "\n\n".join(x for x in parts if x).strip()
