#!/usr/bin/env python
"""test_beat_roles.py -- which narrative job each scene's shot is briefed for, with and without a person's own choice.

Why: until 6 Oct every film's roles were purely positional (hook, world, mechanism, turn, brand by position), so the LAST
scene was always the endframe -- even when the concept wanted a comeback after the pack shot. A scene can now carry its own
`beat_role` (Auto when empty). The rule this pins: a film with NO explicit roles is planned exactly as it always was; where
a role is set, it is honoured, the scenes left on Auto are planned among themselves, and Auto never makes a second
sign-off beside an explicit one.

    python tools/test_beat_roles.py       # exit 0 = every case behaves   (no key, no cost, nothing real touched)
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
import filmcut as fc  # noqa: E402

fails = 0


def check(name, got, want):
    global fails
    ok = got == want
    fails += 0 if ok else 1
    print(("  ok   " if ok else "  FAIL ") + name + ("" if ok else f"   got {got!r}, want {want!r}"))


def film(roles_by_scene, continues=()):
    """One segment per scene (a scene in `continues` is a second beat of the scene before it)."""
    segs, scene_no = [], 0
    for i, r in enumerate(roles_by_scene):
        cont = i in continues
        if not cont:
            scene_no += 1
        segs.append({"index": i, "seconds": 6, "continues": cont,
                     "scenes": [{"no": scene_no, "visual": f"scene {scene_no}", **({"beat_role": r} if r else {})}]})
    return segs


def roles(roles_by_scene, continues=()):
    return [s["role"] for s in fc.assign_roles(film(roles_by_scene, continues))]


print("no explicit roles: exactly the old positional plan")
for n in range(1, 9):
    check(f"{n} scenes", roles([""] * n), fc.roles_for(n))
four = fc.roles_for(4)
check("a beat that continues a scene shares its role", roles([""] * 5, continues=(2,)), [four[0], four[1], four[1], four[2], four[3]])
check("an unknown role is ignored (treated as Auto)", roles(["", "", "banana", "", ""]), fc.roles_for(5))

print("a closing button after the sign-off")
check("4 auto scenes + a button: the sign-off stays on the last AUTO scene", roles(["", "", "", "", "button"]), fc.roles_for(4) + ["button"])
check("two buttons", roles(["", "", "", "button", "button"]), fc.roles_for(3) + ["button", "button"])
check("button is honoured even when it is not last", roles(["", "button", "", "", ""])[1], "button")

print("a sign-off that is not the last scene")
r = roles(["", "", "brand", "", ""])
check("the explicit sign-off is kept", r[2], "brand")
check("Auto never makes a second sign-off", r.count("brand"), 1)
check("the other scenes are planned among themselves", [r[i] for i in (0, 1, 3, 4)], fc.roles_for(5)[:4])
check("explicit sign-off + button: one sign-off", roles(["", "", "brand", "button"]).count("brand"), 1)
check("every scene explicit", roles(["hook", "world", "turn", "brand", "button"]), ["hook", "world", "turn", "brand", "button"])

print("cutdown and the role catalogue")
check("button is a known role with a job and a failure", sorted(k for k in ("what", "fails") if fc.BEAT_ROLES["button"].get(k)), ["fails", "what"])
check("button is not in the automatic plan", "button" not in fc.plan_beats(30)["roles"], True)
check("the automatic plan is unchanged for 30s", fc.plan_beats(30)["roles"], fc.roles_for(len(fc.plan_beats(30)["beats"])))
check("button leaves a cutdown first", fc.DROP_ORDER[0], "button")
beats = [{"n": 1, "seconds": 6, "role": "hook"}, {"n": 2, "seconds": 6, "role": "world"}, {"n": 3, "seconds": 6, "role": "turn"},
         {"n": 4, "seconds": 6, "role": "brand"}, {"n": 5, "seconds": 3, "role": "button"}]
cd = fc.cutdown_plan(beats, 24)
check("a cutdown that only needs 3s drops just the button", [b["role"] for b in cd["dropped"]], ["button"])
check("and keeps the rest untouched", [b["role"] for b in cd["beats"]], ["hook", "world", "turn", "brand"])
check("short films still shed the middle (roles_for does not trip on button)", fc.roles_for(3), ["hook", "turn", "brand"])
check("never-dropped roles are unchanged", fc.NEVER_DROPPED, ("hook", "turn", "brand"))

print()
print("All beat-role cases behave." if not fails else f"{fails} beat-role case(s) FAILED.")
sys.exit(1 if fails else 0)
