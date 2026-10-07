# Provocation: from "breaking codes" to "breaking category beliefs and behaviours"

Drafted 7 Oct 2026. A PLAN, not a build. Nothing here is changed in the code until the owner answers the decisions at the end.

## Why

The first real run (Heritage Foods, 6 Oct) came out good but is a *treatment*: how the film is shot. Three causes, all in the build:

1. The unit is a **category code** (five kinds: verbal, visual, tonal, structural, sonic). Every spark must "break at least one code".
2. The **message is frozen** ("may break how the platform is expressed, never what it says") and appears only as a one-line "stays true". Nothing asks how the message is *dramatised*.
3. The audit screen **pre-ticks only visual and structural codes**, so sparks lean visual by default.

What the award winners do (Cannes 2025/26, see the chat write-up) is different in kind: AXA changed a policy (three words), Too Good paid sick leave to cows, Heineken bought a pub and filmed it, Claude dramatised "no ads in your private conversations" by showing the violation. They break what the category **believes** and what the category **does**, and the film is the proof.

## The idea in one paragraph

The audit stops being a list of codes and becomes a map of **what the category takes for granted (beliefs)**, **what every brand does (behaviours)**, and **how it shows up (the existing five code kinds)**. A provocation then has a spine: *the belief or behaviour it overturns, the single-minded message it stands on, the device that makes the message felt, the line a stranger could repeat, and, optionally, an act the brand would do to make it true.* The codes stay, as the third layer.

## 1. The audit: three layers

| Layer | Question | Example for everyday dairy (illustrative, my guess, not tool output) |
|---|---|---|
| **Belief** | What does every brand make the buyer take for granted? | "Goodness is proven by where the milk came from (farm, cow, village)." "Love is measured by what the mother serves." "Strength for the child is the benefit." |
| **Behaviour** | What does every brand *do*, as opposed to say? | Show the farmer as a prop. Compete on freshness stamps and price offers. Sample at schools and festivals. Tell the farmer-support story as an ad, not as a programme. |
| **Code** (existing) | How does it look, sound, feel, run? | The five kinds as today. |

- Same honesty rule as now: every item is tagged **seen** (rests on competitor evidence the person gave) or **memory**, with the same computed caveat.
- The model ranks within each layer (most shared, most breakable first). The screen pre-ticks the **top belief and top behaviour**, not visual codes.
- Per-competitor evidence gets **two new slots** beside packaging / Instagram / social video / POSM / TVC: **Claims and promises** and **What they do** (offers, programmes, partnerships, pricing, distribution). They are what beliefs and behaviours are read from.

## 2. The break: moves per layer

- Codes: remove, invert, exaggerate, relocate, reframe (as today).
- Beliefs: contradict it, show its cost, reverse who benefits, make the invisible visible, take the claim literally.
- Behaviours: do the opposite, do the thing no one does, give something away, make the brand carry a cost, put the proof in an action.

## 3. The spine of a provocation (new fields, all optional so old drafts stay valid)

Under `core`: `message` (the single-minded message, pre-filled from the platform, shown next to the platform line), `device` (one of: demonstration, absence, reversal, exaggeration, proof by doing, point of view, true story, contrast, ritual made visible) plus `device_note`, `tension` (`category_says` / `we_say`: the two-sentence test as fields, replacing the struck-through panel that is derived from codes), `repeatable` (the line a stranger could repeat, 12 words at most), `act` plus `act_note` (what the brand would DO to make it true: a proposal, flagged "needs the business to agree").
`codes_broken` keeps its name and shape; its items gain a `layer`, and the screen calls it "What it breaks".

## 4. Sparks: scored on what a creative director would argue about

Today: breaks a code, true to the platform, travels. New (six chips): **breaks** (a belief, behaviour or code), **message** (how clearly it dramatises the message), **ownable** (could another brand sign it?), **talkable** (would anyone repeat it?), **true**, **travels**. The model grades itself, and the screen says so ("the model's own read").

## 5. The honest test: "Test the message"

A button, on demand (one extra model call, cents). It gives a second model call ONLY the one-line provocation, the film brief and the expressions, **without** the message or the platform, and asks: what does a viewer take away, would they say it to a friend, could another brand sign it, what would a sceptical creative director cut. The screen puts the stranger's reading next to the intended message. A mismatch is the finding. This is the one check that does not let the model mark its own homework.

## 6. Guardrails (no model)

Existing five stay. Added: a provocation with no message or no device warns. An `act` adds a manual line ("needs the business to agree; check it against the approved claims list") and the claims-wording check runs over it too (an act that implies "antibiotic-free", for example, is a claim). Approval requires **message and device** (decision 1).

## 7. Skill file and prompts

`provocation_skill/SKILL.md` is rewritten: the three layers, the moves, the devices with the award precedents (AXA, Too Good, Heineken's pub, Claude, "Got Milk?"), the marketer-and-creative-director test, and the rules that an act is a proposal (never invent a programme the brand does not run) and that hard limits and the claims list stay in force. The audit, spark, develop and push prompts change with it. Develop and push both receive message + device + belief so every medium's line dramatises the same message the same way.

## Blast radius (swept)

- `provocation.py`: `normalise` (new optional fields; old records pass through), `_content`, `approval_problems`, `CHANNELS` and the evidence strength figure (the slots total grows by two per competitor; nothing else reads it).
- `provocation_gen.py`: `_evidence_block`, `_clean_codes` (allowed-channel check reads `CHANNELS`), `audit_codes`, `spark`, `develop`, `push_further`, `_RECORD_SHAPE`, `check_guardrails`, a new `message_test`.
- `main.py`: `/provocation-codes` (same `codes` key, items gain `layer`), `_evidence_read` (channels list is already dynamic), one new route `/provocation-test`.
- Frontend (`app.dc.html`): the audit section (three groups, new pre-tick rule, `pickedCodes`), spark cards (six chips), section 4 form (spine block, tension panel from fields), evidence slots (already driven by the channels list), a "Test the message" button and result.
- Tests: `test_provocation_gen.py` has 45 cases touching codes; `test_provocation.py` 4. Both updated, plus new cases for each new rule.
- **Not touched:** `producers.stands_on` and everything that reads only `core.line` / `expressions` (Video's card, the quote box, other producers), `filmscript`, the hard limits, the competitor-name rules, the stale-fingerprint logic.
- Live data: the saved drafts keep working (`The Ritual, Multiplied` / `No One` have no spine until filled). Rolling back is a revert of the commit; a rolled-back server would drop the new fields on the next save of such a record (normalise ignores unknown keys), so roll back before anyone fills the spine, or accept losing it.

## Phasing (each shipped and live-checked on its own)

- **A. Backend:** layers in the audit, the two evidence slots, the spine fields, the prompts and skill, the guardrail additions, `message_test`, tests. No screen change. Verified with stubbed model tests (no real model call from here, as before).
- **B. Screen:** grouped audit with the new pre-tick, spark chips, the spine in the form, "Test the message". Driven on the real page with stubs.
- **C. A real run by the owner** on the same Heritage Foods house through the live tab, to compare against the 6 Oct drafts and the award frame. Only then P2 (the writer and departments reading the spine, which is a much stronger instruction than "break these codes").

## Decisions for the owner

1. **Approval requires message and device?** Recommended: yes (an approval without them hides the one thing a reviewer needs). Old drafts must have them filled before approval.
2. **Include `act` (what the brand would do)?** Recommended: yes, optional and flagged "needs the business to agree". It is the AXA / Too Good level; it also costs money and needs the client, so it must never read as a given.
3. **Pre-tick the top belief and top behaviour** (recommended) instead of nothing or the old visual-and-structural rule.
4. **Message: pre-filled from the platform and editable** (recommended, with the platform line shown beside it so a drift is visible) or locked.
5. **"Test the message" on demand** (recommended: visible cost, approval does not depend on it) or automatic after every develop.
6. **Two new evidence slots** (claims; what they do): recommended yes.

## What it costs and what it does not fix

Cents per run (the audit, spark and develop calls are the same count; develop is slightly longer; the test is one more, on demand). It does not make the model creative: it makes the brief it works from point at ideas, and it gives the owner a way to catch a treatment dressed as an idea. The quality still has to be judged by a person, which is the point of approval.
