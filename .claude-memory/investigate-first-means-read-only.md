---
name: investigate-first-means-read-only
description: when the owner says check first / tell me first / do not correct yet, do read-only work and report; make no edits or commits
metadata:
  type: feedback
---

On 13 Nov the owner asked to "check the end frame in dairy first, then tell me what needs to be corrected", and during the check sent "do not correct yet". I had already committed and pushed a grammar-only fix (`1387617`) for the same problem one turn earlier, which the owner then had reverted (`f938645`).

**Why:** the owner wants the diagnosis and the choice of fix to be theirs; a fix made before they see the cause costs them a revert and trust.

**How to apply:** when a request says check/tell me first, or a hold arrives mid-turn, stay read-only: read code and saved data, view the frames, then list the causes and the candidate corrections and wait. Say plainly what is already committed. Related: [[judge-the-film-not-the-pipeline]], [[change-discipline-working-agreement]].
