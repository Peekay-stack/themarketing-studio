#!/usr/bin/env python
"""test_sound_plan.py -- the music bed ridden around the voice by a sound plan (soundplan.py), and "no plan = as before".

No key, no credit, nothing real touched: voices are silent generated files and the "music" is a plain sine tone, so the
level of the OUTPUT is the music bed alone and can be measured against the plan (volumedetect on windows of the mix).

    python tools/test_sound_plan.py       # exit 0 = every case behaves
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

_scratch = tempfile.mkdtemp(prefix="soundplan_")
os.environ["STUDIO_DATA_DIR"] = _scratch
os.environ["PYTHONUTF8"] = "1"
for _k in ("ANTHROPIC_API_KEY", "FAL_KEY", "GOOGLE_API_KEY", "HEYGEN_API_KEY", "NVIDIA_API_KEY"):
    os.environ.pop(_k, None)

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api")
sys.path.insert(0, os.path.abspath(API))
os.chdir(os.path.abspath(API))

import filmaudio as fa   # noqa: E402
import filmcut           # noqa: E402
import filmvoice         # noqa: E402
import soundplan as sp   # noqa: E402

EXE = filmcut.ffmpeg_exe()
fails = 0


def check(name, ok, extra=""):
    global fails
    fails += 0 if ok else 1
    print(("  ok   " if ok else "  FAIL ") + name + (f"   [{extra}]" if (extra and not ok) else ""))


def ff(*args):
    return subprocess.run([EXE, "-y", "-hide_banner", "-loglevel", "error", *args], capture_output=True, text=True)


# ---------------------------------------------------------------- synthetic inputs
DIR = tempfile.mkdtemp(prefix="sp_media_")
MUSIC = os.path.join(DIR, "bed.mp3")
VIDEO = os.path.join(DIR, "pic.mp4")
ff("-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100:duration=32", "-ac", "2", "-c:a", "libmp3lame", MUSIC)
ff("-f", "lavfi", "-i", "color=c=black:s=160x90:r=10:d=30", "-c:v", "mpeg4", "-pix_fmt", "yuv420p", VIDEO)


def silent_line(name, secs):
    p = os.path.join(DIR, name)
    ff("-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono", "-t", str(secs), "-c:a", "libmp3lame", p)
    return p


def seg(scene, start, end, secs, name):
    return filmvoice.Segment(kind="vo", text="a line", scene=scene, start=start, end=end, voice="x",
                             url=silent_line(name, secs))


def segments(line_specs):
    """[(scene, line_start, seconds)] -> segments whose scene window is the scene's own span."""
    spans = {1: (0, 8), 2: (8, 14), 3: (14, 22), 4: (22, 30)}
    out = []
    for i, (scene, at, secs) in enumerate(line_specs):
        a, b = spans[scene]
        out.append(seg(scene, max(a, at), b, secs, f"l{i}.mp3"))
    return out


# the real mixer downloads URLs; here a "URL" is just a local file
fa._download = lambda url, dest: (open(dest, "wb").write(open(url, "rb").read()) or True)

ROWS = [{"no": n, "tc": f"{a}–{b}s", "visual": f"Scene {n}.", "audio": []} for n, (a, b) in enumerate([(0, 8), (8, 14), (14, 22), (22, 30)], 1)]
LINES = [(2, 8.5, 1.5), (3, 14.4, 2.7), (4, 22.5, 2.7)]       # (scene, start, seconds): the lines of the 6 Oct film


_captured: list[str] = []
_real_run = subprocess.run


def _spy(cmd, *a, **k):
    if isinstance(cmd, list) and "-filter_complex" in cmd:
        _captured.append(cmd[cmd.index("-filter_complex") + 1])
    return _real_run(cmd, *a, **k)


fa.subprocess.run = _spy


def mix_preview(plan, lines=LINES, level="balanced", seconds=30):
    out = os.path.join(DIR, f"pv{len(_captured)}.mp3")
    segs = segments(lines)
    ok, notes = fa.preview_audio(EXE, float(seconds), out, segs, music=MUSIC, level=level, plan=plan)
    return ok, out


def mix_video(plan, lines=LINES, level="balanced"):
    out = os.path.join(DIR, f"mx{len(_captured)}.mp4")
    segs = segments(lines)
    ok, notes = fa.mix_timeline(EXE, VIDEO, out, segs, music=MUSIC, level=level, plan=plan)
    return ok, out


def db(path, t0, t1):
    r = subprocess.run([EXE, "-hide_banner", "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", path, "-af", "volumedetect",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"mean_volume:\s*(-?[\d.]+|-inf) dB", r.stderr)
    return -91.0 if (not m or m.group(1) == "-inf") else float(m.group(1))


def plan_for(**kw):
    base = {"duck": "normal", "ending": "stop", "carve": False}
    base.update(kw)
    return sp.resolve(base, [dict(r) for r in ROWS], 30)


# ---------------------------------------------------------------- 1. no plan = as before (golden, captured from the
# code as it stood before the sound plan existed)
print("no plan: the mix is exactly what it was")
GOLDEN_PREVIEW = '[1:a]adelay=8500:all=1[p0];[2:a]adelay=14400:all=1[p1];[3:a]adelay=22500:all=1[p2];[4:a]volume=0.18,afade=t=in:st=0:d=1.2[bed];[0:a][p0][p1][p2][bed]amix=inputs=5:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.95[aout]'
GOLDEN_MIX = '[1:a]adelay=8500:all=1[v0];[2:a]adelay=14400:all=1[v1];[3:a]adelay=22500:all=1[v2];[4:a]volume=0.18,afade=t=in:st=0:d=1.2[bed];[v0][v1][v2][bed]amix=inputs=4:duration=longest:dropout_transition=0:normalize=0,alimiter=limit=0.95[aout]'


def graphs(module):
    module.subprocess.run = _spy
    _captured.clear()
    segs = segments(LINES)
    module.preview_audio(EXE, 30.0, os.path.join(DIR, "g_pv.mp3"), segs, music=MUSIC, level="balanced")
    pv = _captured[-1]
    segs = segments(LINES)
    module.mix_timeline(EXE, VIDEO, os.path.join(DIR, "g_mx.mp4"), segs, music=MUSIC, level="balanced")
    mx = _captured[-1]
    return pv, mx


if __name__ == "__main__":
    pv, mx = graphs(fa)
    if os.environ.get("PRINT_GOLDEN"):
        print("PREVIEW=" + repr(pv))
        print("MIX=" + repr(mx))
        sys.exit(0)
    check("preview graph with no plan is unchanged", pv == GOLDEN_PREVIEW, pv)
    check("render graph with no plan is unchanged", mx == GOLDEN_MIX, mx)

    # ------------------------------------------------------------ 2. the pure pieces
    print("the plan itself")
    check("no plan -> nothing to apply", sp.resolve(None, ROWS, 30) is None and sp.resolve({}, ROWS, 30) is None, "")
    d = sp.derive([dict(r) for r in ROWS])
    check("derived states: hook open, world/mechanism open, turn and sign-off swell",
          [d[1], d[2], d[3], d[4]] == ["open", "open", "swell", "swell"], str(d))
    d2 = sp.derive([dict(r) for r in ROWS] + [{"no": 5, "tc": "30-34s", "visual": "x", "audio": [], "beat_role": "button"}])
    check("a Button drops out; the sign-off is still the last Auto scene", d2[5] == "out" and d2[4] == "swell", str(d2))
    r0 = sp.resolve({"duck": "bogus", "ending": "bogus", "scenes": [{"no": 2, "music": "under"}, {"no": 3, "music": "nonsense"}]}, [dict(r) for r in ROWS], 30)
    check("unknown values fall back to defaults", r0["duck_db"] == 8.0 and r0["ending"] == "fade", str(r0))
    check("a person's state wins, an invalid one is ignored", [s["state"] for s in r0["scenes"]] == ["open", "under", "swell", "swell"], str([s["state"] for s in r0["scenes"]]))
    check("scene spans come from the timecodes", [(s["start"], s["end"]) for s in r0["scenes"]] == [(0, 8), (8, 14), (14, 22), (22, 30)], "")
    check("a numeric duck is honoured and clamped", sp.normalise({"duck": 99})["duck_db"] == 24.0 and sp.normalise({"duck": 6})["duck_db"] == 6.0, "")

    knots = sp.envelope(plan_for(), [(a, a + s) for _n, a, s in LINES], 0.18, 30)
    check("the envelope is a handful of knots, in time order", 3 < len(knots) <= sp.MAX_KNOTS and all(knots[i][0] < knots[i + 1][0] for i in range(len(knots) - 1)), str(len(knots)))
    expr = sp.gain_expression(knots)

    def eval_expr(t):
        py = re.sub(r"clip\(", "_clip(", expr).replace("t-", f"{t}-")
        return eval(py, {"_clip": lambda x, lo, hi: max(lo, min(hi, x))})

    worst = max(abs(eval_expr(t) - g) for t, g in knots)
    check("the ffmpeg expression reproduces every knot", worst < 2e-3, f"{worst:.4f}")

    # ------------------------------------------------------------ 3. what the listener hears (preview)
    print("the preview mix follows the plan")
    plan = plan_for()
    ok, out = mix_preview(plan)
    check("the preview renders", ok and os.path.exists(out), "")
    line1, gap1 = db(out, 8.8, 9.8), db(out, 3.0, 6.0)
    check("in a line the music is at its 'under' level; in a pause it lifts by the duck depth (8 dB)", 6.5 <= gap1 - line1 <= 9.5, f"{gap1 - line1:.1f}")
    line2 = db(out, 14.8, 16.8)
    check("every line gets the same under level", abs(line2 - line1) <= 1.0, f"{line2 - line1:.1f}")
    open_gap, swell_gap = db(out, 11.0, 13.5), db(out, 19.5, 21.5)
    check("a Turn swells 3 dB above an open pause", 1.8 <= swell_gap - open_gap <= 4.2, f"{swell_gap - open_gap:.1f}")
    check("the music is back up well within a second of a line ending", db(out, 10.7, 11.2) - line1 >= 5.5, f"{db(out, 10.7, 11.2) - line1:.1f}")
    check("and already down by the time a line starts", abs(db(out, 14.45, 14.7) - line1) <= 1.5, f"{db(out, 14.45, 14.7) - line1:.1f}")

    print("states and endings")
    ok, out = mix_preview(plan_for(ending="fade"))
    check("a fade ending dies away over the last seconds", db(out, 29.6, 30.0) <= db(out, 26.5, 27.5) - 15, f"{db(out, 29.6, 30.0):.1f} vs {db(out, 26.5, 27.5):.1f}")
    ok, out_stop = mix_preview(plan_for(ending="stop"))
    check("a hard stop does not", abs(db(out_stop, 29.6, 30.0) - db(out_stop, 26.5, 27.5)) <= 1.0, "")
    ok, out_o = mix_preview(sp.resolve({"duck": "normal", "ending": "stop", "carve": False, "scenes": [{"no": 2, "music": "out"}]}, [dict(r) for r in ROWS], 30))
    check("an Out scene drops the music away between its lines", db(out_o, 11.5, 13.5) <= -40, f"{db(out_o, 11.5, 13.5):.1f}")
    ok, out_u = mix_preview(sp.resolve({"duck": "normal", "ending": "stop", "carve": False, "scenes": [{"no": 1, "music": "under"}]}, [dict(r) for r in ROWS], 30))
    check("an Under scene stays low in its pauses", abs(db(out_u, 3.0, 6.0) - db(out_u, 8.8, 9.8)) <= 1.2, f"{db(out_u, 3.0, 6.0) - db(out_u, 8.8, 9.8):.1f}")
    short = [(2, 8.5, 1.0), (2, 9.7, 1.0)]
    ok, out_s = mix_preview(plan, lines=short)
    check("a breath between two lines does not lift the music", db(out_s, 9.52, 9.66) - db(out_s, 8.8, 9.3) <= 1.5, f"{db(out_s, 9.52, 9.66) - db(out_s, 8.8, 9.3):.1f}")
    ok, out_strong = mix_preview(plan_for(duck="strong"))
    check("a Strong duck lifts 12 dB", 10.0 <= db(out_strong, 3.0, 6.0) - db(out_strong, 8.8, 9.8) <= 13.5, f"{db(out_strong, 3.0, 6.0) - db(out_strong, 8.8, 9.8):.1f}")
    check("the carve is a filter in the bed's chain only when asked for", "equalizer=f=2000" in sp.bed_filter(sp.resolve({"carve": True}, [dict(r) for r in ROWS], 30), [(8.5, 10)], 0.18, 30)
          and "equalizer" not in sp.bed_filter(plan, [(8.5, 10)], 0.18, 30), "")
    ok, out_none = mix_preview(None)
    check("no plan keeps the old static level everywhere", abs(db(out_none, 3.0, 6.0) - db(out_none, 8.8, 9.8)) <= 0.5, "")

    # ------------------------------------------------------------ 4. the real render uses the same envelope
    print("the render matches the preview")
    ok_v, out_v = mix_video(plan)
    check("the video mix renders", ok_v and os.path.exists(out_v), "")
    ok, out_p = mix_preview(plan)
    pairs = [(8.8, 9.8), (3.0, 6.0), (14.8, 16.8), (19.5, 21.5)]
    diffs = [abs(db(out_v, a, b) - db(out_p, a, b)) for a, b in pairs]
    check("preview and render sound the same at every probe point", max(diffs) <= 1.0, str([round(x, 2) for x in diffs]))
    ok_n, out_n = mix_video(None)
    check("a render without a plan still has the static bed", ok_n and abs(db(out_n, 3.0, 6.0) - db(out_n, 8.8, 9.8)) <= 0.5, "")

    # ------------------------------------------------------------ 5. only when somebody speaks
    ok_a, out_alone = fa.preview_audio(EXE, 30.0, os.path.join(DIR, "alone.mp3"), [], music=MUSIC, level="balanced", plan=plan)
    check("with no voice at all the plan does nothing (the bed is the film, at its own level)",
          ok_a and abs(db(os.path.join(DIR, "alone.mp3"), 3.0, 6.0) - db(os.path.join(DIR, "alone.mp3"), 11.0, 13.0)) <= 0.5, "")

    print()
    print("All sound-plan cases behave." if not fails else f"{fails} sound-plan case(s) FAILED.")
    sys.exit(1 if fails else 0)
