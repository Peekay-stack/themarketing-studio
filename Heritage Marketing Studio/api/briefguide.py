"""briefguide.py — prompt guides for the brief-writing screens.

Separate from `execution.PROMPT_GUIDE` on purpose. That one describes producers: what a film or a
POSM prompt has to carry. These describe the surfaces where a BRIEF gets drafted, and the honest
content is different in one important way - a producer prompt is added to a brief that already
exists, whereas these prompts are how the brief itself comes into being. So there is no "the plan
still applies" line to give; what belongs here instead is what the draft cannot know.

The payload shape is deliberately identical to `execution.prompt_guide()` so a client can render
both through one path.
"""
from __future__ import annotations

# `builder` and `editor` are the same affordance on two screens - the AI co-writer line, same
# placeholder, same handler - so they share one guide rather than getting two that drift apart.
_COWRITER = {
    "what": "One line in, a draft of every field out. It drafts wording; the thinking stays yours.",
    "asks": ("Name the product, the occasion, and who it is for. If you know the decision this brief "
             "has to settle - which of two things you lead on - say that as well. It is what turns a "
             "description into a brief."),
    "example": ("A bank: 'Salary-account push for first-job graduates in tier-2 cities, deciding "
                "whether we lead on zero balance or on the app.'"),
    "avoid": ("'Write a brief.' With nothing named, every field comes back as a general truth about "
              "the category. Also avoid pasting a research deck into this line - it is a subject, not "
              "a source. Documents go through the import panel, which reads them as inputs."),
    "cannot_override": "the brand profile's category, market, brand codes and mandatories",
    # Says plainly what the co-writer does when the line is silent, rather than implying it leaves
    # gaps. It does not - it fills them.
    "additive": ("This drafts wording, not facts. Where your line is silent it writes something "
                 "plausible for the category rather than leaving the field empty, so every figure and "
                 "every claim in the draft is a guess until you have checked it."),
}

GUIDES: dict[str, dict] = {
    "imc": {
        "what": "The one prompt the whole brand brief is built from. It sets the subject; the files "
                "you upload set the facts.",
        "asks": ("Name the brand, the decision this brief has to settle, and the window it runs in. "
                 "Then say which upload carries which numbers - share, penetration, research - "
                 "because those are quoted from the file rather than written."),
        "example": ("A two-wheeler brand: 'Brief for the 125cc commuter launch, deciding whether we "
                    "lead on mileage or on resale value. Runs September to December. Share and "
                    "penetration are in the Nielsen deck; the resale claim is in the dealer survey.'"),
        "avoid": ("'Make a strong IMC brief for our brand' - which produces a competent brief about "
                  "nothing. And do not type figures into this line hoping they land: numbers come "
                  "from the files, so a figure typed here is one nobody can trace back."),
        "cannot_override": "the brand profile's category, market, brand codes and mandatories",
        "additive": ("The prompt sets the subject and cannot supply facts. Market share, penetration "
                     "and research come only from the files you upload, and anything you do not "
                     "supply is marked NOT SUPPLIED in the brief rather than filled in."),
    },
    "builder": _COWRITER,
    "editor": _COWRITER,
}

# The brief-writing landing screen has no prompt box on it - it is where a format gets chosen. Saying
# so is more use than a generic guide, and more honest than an empty disclosure.
NO_PROMPT_HERE = {
    "briefs": ("There is no prompt on this screen - it is where you choose a format. The guide for "
               "writing the prompt sits on the format's own screen, beside the co-writer line."),
}


def prompt_guide(surface: str) -> dict:
    """The guide for one brief surface, in the same shape `execution.prompt_guide` returns."""
    key = str(surface or "").strip().lower()
    g = GUIDES.get(key)
    if g:
        return {"available": True, "kind": key, **g}
    if key in NO_PROMPT_HERE:
        return {"available": False, "kind": key, "why": NO_PROMPT_HERE[key]}
    return {"available": False, "kind": surface,
            "why": f"No prompt guide written for the {surface!r} screen. Rather than show a generic "
                   f"one, this says so - a guide that could apply to any screen teaches nothing "
                   f"about this one."}


def surfaces() -> dict[str, dict]:
    """Every brief surface a client might render, guided or explicitly not."""
    keys = list(GUIDES) + [k for k in NO_PROMPT_HERE if k not in GUIDES]
    return {k: prompt_guide(k) for k in keys}
