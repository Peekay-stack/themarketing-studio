#!/usr/bin/env python
"""test_filmqc.py -- offline checks for the free post-render report (FILM_CONSOLIDATED_PLAN.md C2, api/filmqc.py and POST /film-qc).

Pure functions are tested on text; the ffmpeg path is tested on a tiny film made here: 4 s of moving picture then 5 s of an exactly still grey card, a tone for 7 s and then 2 s of silence. No model, no network.
Run:  api/.venv/Scripts/python.exe tools/test_filmqc.py
"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import filmqc, filmcut

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

DASH = "–"
rows = [{"no": 1, "tc": f"0{DASH}4s"}, {"no": 2, "tc": f"4{DASH}9s"}, {"no": 3}, "junk", {"no": 4, "tc": "9-9s"}]
w = filmqc.windows(rows)
check("windows: only rows with a real timecode, in order, with their own scene number", [(x["no"], x["start"], x["end"]) for x in w] == [(1, 0.0, 4.0), (2, 4.0, 9.0)], w)
check("windows: nothing in, nothing out", filmqc.windows(None) == [] and filmqc.windows([]) == [])

log = "x\nlavfi.signalstats.YAVG=200.5\nlavfi.signalstats.YAVG=0.25\nlavfi.signalstats.YAVG=3\n"
check("parse_motion: the first frame (compared with black) is dropped", filmqc.parse_motion(log) == [0.25, 3.0])
fl = "[freezedetect] lavfi.freezedetect.freeze_start: 4.04\n[freezedetect] lavfi.freezedetect.freeze_end: 9\nfreeze_start: 12"
check("parse_ranges: closed and still-open ranges", filmqc.parse_ranges(fl, "freeze_start", "freeze_end") == [(4.04, 9.0), (12.0, None)], filmqc.parse_ranges(fl, "freeze_start", "freeze_end"))

steps = [5.0] * 8 + [0.05] * 16          # 3 s at 8 fps: 1 s moving then 2 s still
sm = filmqc.scene_motion(steps, [{"no": 1, "start": 0, "end": 1}, {"no": 2, "start": 1, "end": 3}])
check("scene_motion: the last step of each window (the cut) is left out", sm[0]["motion"] == 5.0 and sm[1]["motion"] < 0.1, sm)

f1 = filmqc.findings([{"no": 5, "start": 24, "end": 30, "motion": 0.16}], [], [], 30)
check("a 6 s scene that barely moves is flagged with its number", [x["kind"] for x in f1] == ["barely-moves"] and f1[0]["scene"] == 5, f1)
check("a 2 s still beat is not flagged (too short to be a held shot)", filmqc.findings([{"no": 1, "start": 0, "end": 2, "motion": 0.0}], [], [], 30) == [])
check("a held but alive close-up (0.6) is not flagged", filmqc.findings([{"no": 1, "start": 0, "end": 4, "motion": 0.6}], [], [], 30) == [])
check("a freeze of 1.5 s or more is a defect, a shorter one is not", [x["kind"] for x in filmqc.findings([], [(4, 6)], [], 30)] == ["frozen"] and filmqc.findings([], [(4, 5)], [], 30) == [])
check("a silence that runs to the end of the film is a silent tail", [x["kind"] for x in filmqc.findings([], [], [(28.3, None)], 30.0)] == ["silent-tail"])
check("a silence in the middle, or a short one at the end, is not", filmqc.findings([], [], [(10, 12), (29.4, None)], 30.0) == [])
fs = filmqc.findings([{"no": 5, "start": 24, "end": 30, "motion": 0.16}], [], [], 30, signoff=5)
check("the SIGN-OFF scene holds still ON PURPOSE (the render locks the pack shot): it is reported in its own words, flagged as the sign-off, and says how to lift a flat ending",
      len(fs) == 1 and fs[0]["kind"] == "barely-moves" and fs[0]["signoff"] is True and "locked on purpose" in fs[0]["note"] and "payoff line" in fs[0]["note"] and "add a movement" not in fs[0]["note"], fs)
fo = filmqc.findings([{"no": 2, "start": 4, "end": 10, "motion": 0.1}], [], [], 30, signoff=5)
check("a still scene that is NOT the sign-off keeps the ordinary advice (and no sign-off flag)", len(fo) == 1 and "signoff" not in fo[0] and "add a movement" in fo[0]["note"], fo)

# ---- the real ffmpeg path on a tiny film made here -------------------------------------------------------------------------------------
exe = filmcut.ffmpeg_exe()
check("ffmpeg is available for the test", bool(exe))
if exe:
    d = tempfile.mkdtemp(); mp4 = os.path.join(d, "t.mp4")
    r = subprocess.run([exe, "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=24:d=4", "-f", "lavfi", "-i", "color=c=gray:s=320x180:r=24:d=5", "-f", "lavfi", "-i", "sine=f=440:d=7",
                        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v];[2:a]apad=whole_dur=9[a]", "-map", "[v]", "-map", "[a]", "-t", "9", "-pix_fmt", "yuv420p", mp4], capture_output=True, text=True)
    check("the test film was made", os.path.exists(mp4), r.stderr[-300:])
    rep = filmqc.report(mp4, [{"no": 1, "tc": f"0{DASH}4s"}, {"no": 2, "tc": f"4{DASH}9s"}])
    kinds = sorted(x["kind"] for x in rep.get("findings", []))
    check("report: ok, 9 s, both scenes measured, the moving one moves and the grey card does not",
          rep.get("ok") and abs(rep["duration"] - 9) < 0.2 and rep["scenes"][0]["motion"] > 1.0 and rep["scenes"][1]["motion"] < 0.05, rep)
    check("report: finds the barely-moving scene 2, the exact freeze and the 2 s silent tail", kinds == ["barely-moves", "frozen", "silent-tail"], kinds)
    check("report: the barely-moves finding names scene 2", [x["scene"] for x in rep["findings"] if x["kind"] == "barely-moves"] == [2])
    rep_so = filmqc.report(mp4, [{"no": 1, "tc": f"0{DASH}4s"}, {"no": 2, "tc": f"4{DASH}9s"}], signoff=2)
    check("report: told that scene 2 is the sign-off, its stillness is reported as the deliberate hold", [x for x in rep_so["findings"] if x["kind"] == "barely-moves"][0].get("signoff") is True)
    rep2 = filmqc.report(mp4, None)
    check("report without scenes still reports freeze and silence, with no scene list", rep2.get("ok") and rep2["scenes"] == [] and sorted(x["kind"] for x in rep2["findings"]) == ["frozen", "silent-tail"], rep2)
    check("report on a missing file says so and does not throw", filmqc.report(os.path.join(d, "nope.mp4"), None).get("ok") is False)

# ---- the route ----------------------------------------------------------------------------------------------------------------------------
import main
check("route: no url, or a url that is not a /renders/ one, is a polite not-found", main.film_qc({}).get("ok") is False and main.film_qc({"url": "/media/x.mp4"}).get("ok") is False)
check("route: a name that tries to leave the renders folder is a not-found, not a read", main.film_qc({"url": "/renders/../main.py"}).get("ok") is False and main.film_qc({"url": "/renders/..%2Fmain.py"}).get("ok") is False)
if exe:
    name = "qc-test-" + os.path.basename(d) + ".mp4"
    dst = os.path.join(filmcut.RENDERS_DIR, name)
    try:
        os.makedirs(filmcut.RENDERS_DIR, exist_ok=True)
        with open(mp4, "rb") as a, open(dst, "wb") as b: b.write(a.read())
        out = main.film_qc({"url": "/renders/" + name + "?v=2", "scenes": [{"no": 1, "tc": f"0{DASH}4s"}, {"no": 2, "tc": f"4{DASH}9s"}]})
        check("route: a real /renders/ url (with a query string) is measured", out.get("ok") and len(out.get("findings", [])) == 3, out)
    finally:
        if os.path.exists(dst): os.remove(dst)

print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)
