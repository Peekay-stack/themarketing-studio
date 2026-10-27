#!/usr/bin/env python
"""test_film_edit.py -- offline checks for craft slice 5: filmedit.py (the editor's notes on sound and rhythm) and POST /editor-notes. No model, no network, nothing written to the tenant.
Run:  api/.venv/Scripts/python.exe tools/test_film_edit.py
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import filmedit as fe, soundplan, main

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

def vo(t, **k): return {"kind": "vo", "text": t, **k}
def film():
    return [
        {"no": 1, "visual": "A mother measures a boy's trousers.", "audio": [vo("Every day he grew.")]},
        {"no": 2, "visual": "Months earlier, the boy drinks milk.", "audio": [vo("Glass by glass.")]},
        {"no": 3, "visual": "Closer on the boy drinking.", "audio": [vo("Month after month.")]},
        {"no": 4, "visual": "The mother lets the hem down.", "audio": [vo("And one morning.")]},
        {"no": 5, "visual": "The boy stands tall; they fit.", "audio": [vo("It fit.")]},
        {"no": 6, "visual": "The pack beside a glass.", "beat_role": "brand", "audio": [vo("One glass at a time.")]},
    ]
SECS = [6, 6, 6, 6, 6, 6]
BM = {"turn_scene": 4, "carrier_scene": 6, "scenes": [{"no": 1, "intensity": 1, "beat": "b1"}, {"no": 2, "intensity": 1, "beat": "b2"}, {"no": 3, "intensity": 1, "beat": "b2"},
                                                   {"no": 4, "intensity": 3, "beat": "b3"}, {"no": 5, "intensity": 2, "beat": "b4"}, {"no": 6, "intensity": 3, "beat": "b5"}]}
def ids(r): return [n["id"] for n in r["notes"]]
def note(r, i): return next((n for n in r["notes"] if n["id"] == i), None)

rows = film()
derived = soundplan.derive(rows)
turn_role = [d["no"] for d in soundplan.describe(rows) if d["role"] == "turn"]

# ---- music lifts on the director's turn -----------------------------------------------------------------------------------------------------------------
r = fe.notes(rows, SECS, BM, {"scenes": [{"no": 4, "music": "open"}]})
n = note(r, "music-turn")
check("music: the turn is set to 'open' -> a note and a one-click fix to swell it", n is not None and n["scene"] == 4 and n["fix"] == {"type": "music", "scene": 4, "value": "swell", "label": "Lift the music on scene 4"}, str(r["notes"]))
check("music: the turn already swells -> no note", note(fe.notes(rows, SECS, BM, {"scenes": [{"no": 4, "music": "swell"}]}), "music-turn") is None)
check("music: the effective state is the person's choice, else the derived one", fe.effective_music(rows, {"scenes": [{"no": 4, "music": "under"}]})[4] == "under" and fe.effective_music(rows, None) == derived)
if turn_role and turn_role[0] != 4:
    r2 = fe.notes(rows, SECS, BM, None)
    nm = note(r2, "music-misplaced")
    check("music: the planner's guessed turn swells but the director's turn is elsewhere -> a note to keep that scene level", nm is not None and nm["scene"] == turn_role[0] and nm["fix"]["value"] == "open", str(r2["notes"]))
else:
    print("SKIP planner's turn equals the director's turn in this fixture")
check("music: sound design switched off -> no music notes at all", not any(i.startswith("music") for i in ids(fe.notes(rows, SECS, BM, {"scenes": [{"no": 4, "music": "open"}]}, sound_off=True))))

# ---- a beat of silence before the message line ----------------------------------------------------------------------------------------------------------
r = fe.notes(film(), SECS, BM, None)
n = note(r, "silence-before-message")
check("silence: the message line starts at the scene's start -> a note with a 1 s lead-in fix", n is not None and n["scene"] == 6 and n["fix"] == {"type": "line_lead", "scene": 6, "value": 1.0, "label": "Start the line 1 s in"}, str(r["notes"]))
led = film(); led[5]["audio"][0]["timing_at"] = 1.2
check("silence: a line already starting 1.2 s in -> no note", note(fe.notes(led, SECS, BM, None), "silence-before-message") is None)
mid = film(); mid[5]["audio"][0]["timing"] = "middle"
check("silence: a line placed in the middle of the shot -> no note", note(fe.notes(mid, SECS, BM, None), "silence-before-message") is None)
tight = fe.notes(film(), [6, 6, 6, 6, 6, 3], BM, None)
nt = note(tight, "silence-before-message")
check("silence: a scene with no spare time says so and offers NO fix", nt is not None and "fix" not in nt and "fills the scene" in nt["note"], str(nt))
sl = film(); sl[5]["audio"] = [vo("One glass at a time please now.")]
shortlead = fe.notes(sl, [6, 6, 6, 6, 6, 4], BM, None)
check("silence: a scene with a little spare time gets a short 0.5 s lead", (note(shortlead, "silence-before-message") or {}).get("fix", {}).get("value") == 0.5, str(note(shortlead, "silence-before-message")))
prose = film(); prose[5] = {"no": 6, "visual": "The pack.", "beat_role": "brand", "dialogue": "One glass at a time."}
check("silence: a scene written as prose (no per-line timing) gets no fix and no crash", "fix" not in (note(fe.notes(prose, SECS, BM, None), "silence-before-message") or {"x": 1}) and True)
check("silence: a silent carrier scene -> no note", note(fe.notes([{"no": 1, "visual": "a", "audio": [vo("Hello there friend.")]}, {"no": 2, "visual": "b", "audio": []}], [6, 6], {"carrier_scene": 2}, None), "silence-before-message") is None)

# ---- a line must fit its scene -----------------------------------------------------------------------------------------------------------------------
long_ = film(); long_[1]["audio"] = [vo("This is a very long line that needs a great many more seconds to say than the scene was ever given in the first place by anyone.")]
r = fe.notes(long_, SECS, BM, None)
check("fit: a line that needs more seconds than its scene holds is flagged (and only that scene)", [n["scene"] for n in r["notes"] if n["id"] == "line-overruns"] == [2], str(r["notes"]))
check("fit: ordinary lines are not flagged", "line-overruns" not in ids(fe.notes(film(), SECS, BM, None)))

# ---- length follows intensity, end on the message, cut on the action --------------------------------------------------------------------------------------
r = fe.notes(film(), [6, 6, 6, 2, 6, 6], BM, None)
check("rhythm: the turn holds less than the average scene -> a note (no fix)", (note(r, "short-turn") or {}).get("scene") == 4 and "fix" not in note(r, "short-turn"), str(r["notes"]))
check("rhythm: an even film has no short-turn / short-message note", not any(i.startswith("short-") for i in ids(fe.notes(film(), SECS, BM, None))))
r = fe.notes(film(), SECS, {**BM, "carrier_scene": 3}, None)
check("ending: the message lands in scene 3 of 6 -> 'end on the message carrier'", (note(r, "end-on-message") or {}).get("scene") == 3 and "3 more scenes" in note(r, "end-on-message")["note"], str(r["notes"]))
check("ending: the message in the last scene -> no note", "end-on-message" not in ids(fe.notes(film(), SECS, BM, None)))
r = fe.notes(film(), SECS, BM, None)
check("transition: scenes of one beat get a 'cut on the action' note", (note(r, "cut-on-action") or {}).get("scene") == 3 and "2, 3" in note(r, "cut-on-action")["note"], str(r["notes"]))

# ---- no director's read: the planner's roles are used ----------------------------------------------------------------------------------------------------
r = fe.notes(film(), SECS, None, {"scenes": [{"no": 6, "music": "open"}]})
check("no beat map: the carrier defaults to the sign-off scene and the turn to the planner's turn", r["carrier_scene"] == 6 and (r["turn_scene"] in (None, *[d["no"] for d in soundplan.describe(film()) if d["role"] == "turn"])))
check("garbage never raises; empty script -> nothing", fe.notes([], [], None, None)["notes"] == [] and fe.notes(None, None, None, None)["notes"] == [] and isinstance(fe.notes([None, "x", {}], [3], "x", "y")["notes"], list))
check("facts are reported", fe.notes(film(), SECS, BM, None)["facts"] == {"scenes": 6, "seconds": 36, "average_scene": 6.0})

# ---- the route --------------------------------------------------------------------------------------------------------------------------------------------
rr = main.editor_notes({"scenes": film(), "seconds": SECS, "beat_map": BM, "sound_plan": {"scenes": [{"no": 4, "music": "open"}]}})
check("route: returns the notes, the turn and the carrier", isinstance(rr, dict) and "music-turn" in ids(rr) and rr["turn_scene"] == 4 and rr["carrier_scene"] == 6)
check("route: sound_off drops the music notes", not any(i.startswith("music") for i in ids(main.editor_notes({"scenes": film(), "seconds": SECS, "beat_map": BM, "sound_off": True}))))
rb = main.editor_notes({"scenes": []})
check("route: no scenes is a 400", getattr(rb, "status_code", 0) == 400)
check("route: with no seconds sent they are worked out from the words (never crashes)", isinstance(main.editor_notes({"scenes": film(), "beat_map": BM}), dict))

print("\n%d failed" % len(fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
