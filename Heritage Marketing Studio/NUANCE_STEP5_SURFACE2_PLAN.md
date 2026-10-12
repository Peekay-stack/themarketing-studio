# Step 5, Surface 2: exemplars, Brief worked examples, brief-format defaults. Plan for approval (12 Oct)

Status: **built and verified locally (12 Oct), approved by the owner ("go with your recommendation")**. Written as a plan first because it edits prompt text every brand's idea, campaign and Brief generation reads. Built as planned, with two corrections found while building: (1) the NeedScope row's "Heritage" (needscope-framework.md line 12) is the concept ("heritage, every-home ubiquity"), not the brand, so it was left alone; (2) the golden capture for the Plan channels rule saw nothing, because `plan.generate` refuses until its parent layers are filled, so the new `plan_channels` surface calls `plan.prompt_for` directly. Result: `golden_prompts --compare` showed exactly 4 surfaces changed for all 5 brands (20 prompts) and 55 unchanged; `tools/golden_step5` is now the post-Surface-2 baseline (75 prompts). New test `tools/test_exemplar_wording.py`. Decisions taken: replacement examples as drafted; `/brand-brief-builder` left alone (nothing says it is in use); real Brief regeneration NOT run (spends credit, not yet approved).

## What I swept
Every dairy or Heritage word in the strategy-side code, then split the hits into (A) text the model actually reads, (B) comments and docstrings it never sees, (C) text that is already neutral. Only A is a candidate.

## A. Reaches the model, dairy or Heritage specific
| # | Where | What it teaches | Who sees it |
|---|---|---|---|
| 1 | `campaign.py` `SHAPES` (lines 40-50), sent to the model at 391 and 852, shown in the page and the Word export (main.py 3903, docs.py 959, page 20931) | the four campaign shapes, each with an example: **frame** = Heritage's own tagline "{X} ki Shakti, Pure Doodh Se"; **device** = Amul's topical girl (dairy); **rule** = "Daag Acche Hain" (detergent, fine); **act** = "Meet Your Farmer" (food and farm) | every brand's campaign draft |
| 2 | `ideas_skill/SKILL.md` lines 31-33, loaded by `ideas._skill_text()` at ideas.py 1051, 1310 and 1455 | the worked mechanic "Every pack carries the name of the dairy that filled it" and what it generates | every idea platform and expression generation |
| 3 | `brief_ai.py` `_OUTPUT_CONTRACT`: line 91 `bridge_label` e.g. "Pure Doodh Ki Shakti"; lines 101-102 `shift_from`/`shift_to` e.g. "dependable purity" / "chosen family strength"; the Hatsun/Arokya aside at 106-109 | the Brief's output format | every Brief draft |
| 4 | `brief_skill/references/backgrounder-guidance.md` lines 62-76: the **worked example is Heritage Foods, dairy** (loaded through `_REFS`); (`needscope-framework.md` line 12 was first listed here; it is the concept "heritage", not the brand, so it stays) | how to write the backgrounder and the problem statement | every Brief draft |
| 5 | `plan.py` line 950, the channels rule: "('15s vertical reel, Telugu')" | what a channel row looks like | every Plan channels generation |

The rule these break is the one `execution.py` already states (comment at line 166): a worked example must be in a different category from the client's, or forty briefs come back describing the same milk. `execution.PROMPT_GUIDE` already follows it (cement, shampoo, paint, tyre).

## B. Not model-visible, leave alone
`campaign.py` docstrings (5, 15, 137, 781, 936), `ideas.py:13`, `execution.py:166`, `plan.py` 381 and 926, `strategy.py` and `brandbrief.py` comments. They explain history; changing them is noise.

## C. Already fine
`execution.PROMPT_GUIDE` examples. `brief_skill` SMP and CB/CA examples use Parle-G (biscuit): a different category from dairy, so they stay. One category will always match one of the five dev brands (Parle G is one); the fix is a visible label, not a perfect choice (see below).

## D. Looked at, deliberately NOT in this commit
- Page placeholders that show Heritage: `app.dc.html` 1641 and 6886 ("Heritage Nourish+ Milk 500 ml"), 7766 and 7872 (milk splash), 23472-23505 (Sales examples: dairy bay, kirana, curd). They are example text in empty boxes, not prompt text, and belong to plan item 6 (page strings).
- `api/static/brand-brief-builder.html` (the standalone Brief intake page at `/brand-brief-builder`): Heritage is pre-filled everywhere, 26 hits, including JS seed arrays. It is its own small job; **question for you below**.

## Proposed change, one commit
1. **`SHAPES`**: keep the four shapes and the structure; swap the two dairy-flavoured examples and Heritage's tagline for examples from other categories, and add one clause to each, "an example from another category: translate the structure, do not copy it". Draft wording for you to veto: frame = "Share a Coke with {name}"; device = the Duracell bunny; rule = "Daag Acche Hain" (kept); act = a brand staging a new stunt each year (Red Bull). The page's `frame` help text (20931) and placeholder (4937) follow, so the screen and the prompt agree.
2. **`ideas_skill/SKILL.md`**: replace the dairy mechanic with the same mechanic in another category, same structure (a film, a pack change, a shelf strip, a promoter, a listing, a trade argument), labelled as another category. Draft: "Every shirt carries the name of the mill that wove it."
3. **`brief_ai.py` contract**: `bridge_label` and `shift_from`/`shift_to` lose the dairy examples and say what they are in plain words ("the platform name as the brand has named it"). No replacement example, so nothing is there to copy. The competitor aside becomes category-neutral.
4. **`backgrounder-guidance.md`**: rewrite the worked example for a non-dairy category with the same four-row table, problem statement and "notice what it does NOT do" lesson. This is the one with the most weight, because it is the Brief's example. Also the two "Heritage needs to…" stand-ins in the pitfalls list became "The brand needs to…". (`needscope-framework.md` line 12 unchanged: see the status note.)
5. **`plan.py` 950**: "('15s vertical reel, Telugu')" becomes "('15s vertical reel, in the audience's language')".

## What I will NOT touch
`voice_block`, producers, Video, POSM, Onground, the Brief profile wiring (Step 6, needs your explicit OK), the stored Heritage campaign "Pure Doodh Ki Shakti" (it is Heritage's own data and stays), and anything Heritage's saved answers depend on. None of A is a Heritage behaviour: they are teaching examples, so the "answers saved on live" gate does not apply to this surface.

## Verification
- `tools/golden_prompts.py --compare` against `golden_step5`: surfaces `idea_platform_draft`, `campaign_draft`, `brief_draft` change for **all five brands, identically**, and nothing else changes (`voice_block*`, `carousel`, `posm`, `onground`, `social_system`, `video_system`, `house_core`, `sales_trad` must show 0 changed). I read the three diffs line by line; they should differ only by the exemplar text.
- `plan_objectives` does not exercise the channels rule, so I add one surface, `plan_channels`, to the golden set (additive; the existing 70 prompts stay byte-identical).
- New test `tools/test_exemplar_wording.py` (stubbed model): no dairy or Heritage word and no `ki Shakti` in the idea, campaign, Brief or channels prompt for a cement, beauty, apparel and biscuit brand; the four shapes and the skill structure are all still present; Heritage's own stored campaign and answers are untouched.
- The Heritage checklist (22 behaviours) must still pass; `test_pack_wording`, `selfcheck`, `smoke`, `checkfe` and `partials verify` (the page string edits), the tenant-snapshot compare, then the real page for the campaign frame help text and placeholder.
- Live: push, wait for deploy, `/selfcheck` commit match, Render log scan.
- **Not coverable without a login or a model:** whether the model's real output improves. One real check is worth doing and **needs your go-ahead (spends credit)**: regenerate the Brief for the same uploaded Heritage research and compare the problem statement and bridge label with the Heritage test 3 brief you already have.

## Rollback
Revert the commit. No data changes.

## Decisions I need from you
1. **Replacement examples** (shirt and mill, Share a Coke, Duracell bunny, Red Bull stunt): go with them, or name your own.
2. **Brief builder page** (`/brand-brief-builder`, Heritage pre-filled): is anyone still using it? If not, I leave it alone; if yes, I blank its defaults in its own commit.
3. **Real Brief regeneration** after the change: yes or no.
