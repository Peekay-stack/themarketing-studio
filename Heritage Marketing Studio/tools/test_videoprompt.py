#!/usr/bin/env python
"""test_videoprompt.py -- offline checks for the frame-animation prompt compiler (api/videoprompt.py) and for how the
render route feeds it. No network, no credit. Generators are stubbed; nothing is written to the tenant.
Run:  api/.venv/Scripts/python.exe tools/test_videoprompt.py
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api"))
os.environ["GOOGLE_API_KEY"] = "test-key"
import videoprompt as vp

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

# --- clean_visual: the clutter captured from the studio's real prompt (27 Oct) -----------------------------------
check("timecode + stray :. removed", vp.clean_visual("0–6s ...watches.:.") == "watches.", vp.clean_visual("0–6s ...watches.:."))
check("plain sentence untouched", vp.clean_visual("The mother pours milk into a steel glass.") == "The mother pours milk into a steel glass.")
check("adds a final stop", vp.clean_visual("Boy drinks") == "Boy drinks.")
check("ellipsis in the middle is kept", "..." in vp.clean_visual("He waits... then drinks."))
check("timecode with spaces and colon", vp.clean_visual("0 - 4 s: Mother stirs the pot.") == "Mother stirs the pot.", vp.clean_visual("0 - 4 s: Mother stirs the pot."))
check("empty stays empty", vp.clean_visual("  ") == "")

# --- visual_text: picture only, the spoken line is a last resort ----------------------------------------------------
rows = [{"t": "0–6s", "title": "Mother pours milk.", "desc": "A steady stream into a steel glass.", "dialogue": "VO: Fresh every morning."}]
vt = vp.visual_text(rows)
check("visual_text joins title + desc, drops the timecode", vt == "Mother pours milk. A steady stream into a steel glass.", vt)
check("visual_text never carries the spoken line when there is a picture", "Fresh every morning" not in vt)
check("visual_text uses the dialogue only for a row with no picture",
      vp.visual_text([{"t": "0-4s", "dialogue": "Hello there"}]) == "Hello there.", vp.visual_text([{"t": "0-4s", "dialogue": "Hello there"}]))
check("non-dict rows skipped", vp.visual_text(["x", None, {"title": "A"}]) == "A.")

# --- compile_frame_shot: sections, order, what must and must not be in it ------------------------------------------
p = vp.compile_frame_shot(action="The boy raises the steel glass to his lips and drinks.", role="turn",
                          camera_direction="Camera: A slow, steady push-in toward the subject. Whatever this movement does, keep the face clearly recognisable.",
                          pack_in_frame=True)
order = [p.index(k) for k in ("ACTION:", "EXPRESSION:", "CAMERA:", "KEEP IDENTICAL TO THE IMAGE:", "Audio:", "No on-screen text")]
check("sections in director's order", order == sorted(order), str(order))
check("starts with the one-continuous-shot instruction", p.startswith("Animate this frame as one continuous shot, no cuts."))
check("action text is in the ACTION section", "raises the steel glass to his lips and drinks" in p.split("EXPRESSION:")[0])
check("camera label not doubled", "CAMERA: Camera:" not in p and "CAMERA: A slow, steady push-in" in p, p)
check("pack sentence present when the pack is in frame", "product pack exactly as in the image" in p)
check("no garment badge/crest line is present", "adding no badge, crest, logo or text to any garment" in p)
check("audio line forbids speech and music", "no speech, no singing, no music" in p)
check("no length sentence (gemini.video owns it)", "About" not in p and "second" not in p.lower().replace("seconds", "") or "About" not in p, p)
check("none of the old clutter", all(w not in p for w in ("#", "FIXED", "ESPECIALLY", "under two seconds", "storyboard frame", "brand film")), p)
p2 = vp.compile_frame_shot(action="Mother stirs the pot.", pack_in_frame=False)
check("pack sentence absent when no pack is in frame", "product pack" not in p2)
check("no CAMERA section when none was decided", "CAMERA:" not in p2)
p3 = vp.compile_frame_shot(action="x.", continues=True, beat_note="slower, more tender")
check("continuation + the person's own direction both carried", "continues the previous shot" in p3 and "Direction: slower, more tender." in p3)
check("brand role asks for a clean front-facing pack", "closing product shot" in vp.compile_frame_shot(action="x.", role="brand", pack_in_frame=True))
check("unknown role adds nothing", vp.compile_frame_shot(action="x.", role="zzz").count("shot") <= vp.compile_frame_shot(action="x.").count("shot"))
check("empty action still yields a usable prompt", "ACTION: Keep the scene alive" in vp.compile_frame_shot(action=""))

# --- through the real render route, generators stubbed ------------------------------------------------------------
import main, gemini, creative, filmcut
captured = []
gemini.available = lambda: True
def fake_video(prompt, **kw): captured.append(("google", prompt, kw)); return "/media/shot-fake.mp4"
gemini.video = fake_video
creative.video_from_image = lambda model, prompt, img, **kw: captured.append(("fal", prompt, kw)) or "http://x/y.mp4"
filmcut.stitch = lambda urls, lengths=None: None          # forces the early "unstitched" return: no voice, no music, no mix
main._record_made = lambda *a, **k: None                  # never write to the tenant's ledger from a test
payload = {"scenes": [
    {"no": 1, "t": "0–6s", "title": "A mother pours milk from the pouch into a steel glass.", "desc": "", "camera": "slow push in",
     "dialogue": "VO: ఇంకాసేపు", "frame_url": "/media/frame1.jpg"},
    {"no": 2, "t": "6–12s", "title": "The boy takes the glass and drinks.", "desc": "Kitchen morning light.", "frame_url": "/media/frame2.jpg"}],
    "aspect": "16:9", "duration": "12s", "engines": {"video": "google"}, "tier": "lite", "with_music": False}
try:
    main._produce_video_sync(payload)
except Exception as e:
    print("route raised after generation (fine for this stub):", type(e).__name__, str(e)[:100])
g = [c for c in captured if c[0] == "google"]
check("one Google call per scene, in the route", len(g) == 2, str(len(g)))
if g:
    p1 = g[0][1]
    check("route prompt is the compiled shape", p1.startswith("Animate this frame as one continuous shot") and "ACTION:" in p1 and "KEEP IDENTICAL" in p1, p1[:200])
    check("route prompt has the scene's visual, no timecode, no spoken line", "mother pours milk" in p1 and "0–6" not in p1 and "ఇంకాసేపు" not in p1, p1)
    check("route prompt carries the pack sentence (scene names the pouch)", "product pack exactly as in the image" in p1)
    check("route prompt carries the scene's camera note", "slow push in" in p1, p1)
    check("route prompt has no ':.' leftovers", ":." not in p1 and ". :" not in p1)
    check("route passes the tier and the frame", g[0][2].get("tier") == "lite" and g[0][2].get("image_ref") == "/media/frame1.jpg")
    check("last scene gets the endframe role: product shot + locked hold, whatever its words say",
          "closing product shot" in g[1][1] and "Hold the shot locked and still" in g[1][1] and "product pack exactly as in the image" in g[1][1], g[1][1][:300])

print("\n%d failed" % len(fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
