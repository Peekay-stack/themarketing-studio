---
name: check-skill-md-before-craft-changes
description: "Read the matching *_skill/SKILL.md and its references/ before proposing any craft or quality change in this repo — it usually already contains the rule, and it may contradict both the web consensus and the user's own suggestion"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2992e305-436f-4002-a763-1671cfdf2a8a
  modified: 2026-09-03T05:14:38.472Z
---

Before proposing craft/quality changes to a generation or compositing area, read that domain's
`api/<domain>_skill/SKILL.md` **and its `references/` files**. CLAUDE.md says this outright and it has
now paid off at full strength: in the round-75 POSM compositor work, **six of seven defects were rules
the repository had already written down and never enforced in code**.

**It can override the obvious answer, the web, and the user.** Asked to research how a senior art
director builds POSM and fix an unreadable headline, the web sources recommended a **scrim** (a
translucent gradient behind type) and the user independently suggested the same thing — "vignette or
some other solution... adjusting font color or background color". `posm_skill/SKILL.md` explicitly
refuses it:

> "Any technique that drops a translucent band over a full-bleed image to make room for a headline is a
> symptom of building the wrong thing... A line dropped onto a full-bleed image inside a translucent
> slab is not a layout; it is a subtitle."

It is backed by 13 real Indian FMCG pieces in `references/exhibits/`, nine of them built as a
flat-colour field with masked cut-outs. The correct fix was structural (build the layer stack; a photo
becomes a bounded panel and never hosts type), not a contrast treatment. Saying so plainly — "your
suggested fix is the wrong one, and here is the cited reason" — was accepted immediately.

**How to apply:** grep the SKILL.md and `references/*.md` for the concept before designing anything
(`scrim`, `contrast`, `hierarchy`, `layer`, `device`). Quote the rule and its exhibit when explaining
the recommendation. Treat a generation route producing bad output as "which written rule is not being
enforced?" before "what new rule do I need?".

Related: [[studio-work-inventory]], [[browser-verification-available]],
[[prefer-cited-estimates-over-blocking]].
