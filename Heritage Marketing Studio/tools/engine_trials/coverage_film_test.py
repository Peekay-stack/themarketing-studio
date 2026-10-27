#!/usr/bin/env python
"""coverage_film_test.py -- STEP 2 proof: a REAL 30 s Draft film with COVERAGE through the studio's own render function
(main._produce_video_sync), no generator stubs. Spends real credit (Omni 360p clips >= 3 s each, voice, music).
Hand-written payload, no UI: six Heritage scenes; scene 4 (boy drinks) has 3 shots and scene 5 (the pour) has 2, built from the frames made in
coverage_step0; the sign-off has an extra shot that must be IGNORED. Output -> Downloads\\engine-trial\\coverage_step2\\
Usage: coverage_film_test.py
"""
import base64, json, os, re, shutil, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = os.path.join(ROOT, "api"); sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
D = r"C:\Users\punie\Downloads\engine-trial"; OUT = os.path.join(D, "coverage_step2"); os.makedirs(OUT, exist_ok=True)
S1 = os.path.join(D, "step1"); S0 = os.path.join(D, "coverage_step0")
import main, gemini, filmcut, filmvoice
import imageio_ffmpeg
EXE = imageio_ffmpeg.get_ffmpeg_exe()

def uri(p): return "data:image/jpeg;base64," + base64.b64encode(open(p, "rb").read()).decode()
def vo(t): return {"kind": "vo", "text": t}

scenes = [
 {"no": 1, "tc": "", "visual": "The mother stirs the steaming milk in the steel pot with a ladle while the boy steps closer, holding his glass.",
  "audio": [vo("Mornings begin the same way.")], "frame_url": uri(os.path.join(S1, "frame_s2.jpg"))},
 {"no": 2, "tc": "", "visual": "A lab technician lowers a pipette into a steel cup of milk sample, draws the liquid up and lifts it to study the level.",
  "frame_url": uri(os.path.join(S1, "frame_s3.jpg"))},
 {"no": 3, "tc": "", "visual": "A man presses a button on the instrument while a woman beside him writes notes on a clipboard.",
  "audio": [vo("Behind every glass, a test, and then another.")], "frame_url": uri(os.path.join(S1, "frame_s4.jpg"))},
 {"no": 4, "tc": "", "visual": "The boy takes the steel glass from the counter; his mother stands beside him holding the Heritage pouch.",
  "audio": [vo("Every glass is tasted, tested and checked twice before it ever reaches your family's door.")],
  "camera": "slow push-in", "shot_size": "medium", "frame_url": uri(os.path.join(D, "cand_B_28.5.jpg")),
  "shots": [{"visual": "Close-up on the boy's face and shoulders as he looks down at the steel glass in both hands; at the edge of the frame his mother's hand holds the Heritage pouch.",
             "shot_size": "close", "camera": "slow push-in", "secs": 2, "frame_url": uri(os.path.join(S0, "frame_B_close.jpg"))},
            {"visual": "Detail insert: the mother's hand holding the Heritage pouch front-on beside the steel glass, label facing the camera.",
             "shot_size": "detail", "camera": "slow rack of focus", "secs": 2, "frame_url": uri(os.path.join(S0, "frame_B_detail.jpg"))}]},
 {"no": 5, "tc": "", "visual": "The mother tilts the Heritage pouch and pours a steady stream of milk into the steel vessel.",
  "camera": "gentle drift", "frame_url": uri(os.path.join(D, "frame_first.jpg")),
  "shots": [{"visual": "Detail insert: the corner of the Heritage pouch tilted over the steel vessel, a thin stream of milk pouring in.",
             "shot_size": "detail", "camera": "slow push-in", "secs": 2, "frame_url": uri(os.path.join(S0, "frame_A_detail.jpg"))}]},
 {"no": 6, "tc": "", "visual": "The Heritage pouch on the counter, front-on, in warm morning light.", "audio": [vo("Heritage. Health and happiness.")],
  "frame_url": uri(os.path.join(S1, "frame_s1.jpg")), "shots": [{"visual": "Another angle of the pouch.", "secs": 2}]},
]
payload = {"scenes": scenes, "aspect": "16:9", "duration": "30s", "engines": {"video": "google", "music": "google"}, "tier": "lite",
           "style": "real", "script": {"logline": "A morning with Heritage."}}

main._record_made = lambda *a, **k: None
log = []
_real_video = gemini.video
def spy(prompt, **kw):
    t0 = time.time(); out = _real_video(prompt, **kw)
    log.append({"seconds": kw.get("seconds"), "ok": bool(out), "took": round(time.time() - t0, 1), "err": gemini.video_error(), "url": out, "prompt": prompt[:160]})
    print(f"  clip: asked {kw.get('seconds')}s -> {'OK' if out else 'FAILED ' + gemini.video_error()} ({time.time()-t0:.0f}s)", flush=True)
    return out
gemini.video = spy
_real_synth = filmvoice.synth; voice_windows = []
def synth_spy(segs, *a, **k):
    r = _real_synth(segs, *a, **k)
    for s in segs: voice_windows.append({"scene": s.scene, "start": round(s.start, 2), "end": round(s.end, 2), "text": s.text[:50], "has_audio": bool(s.url)})
    return r
filmvoice.synth = synth_spy

t0 = time.time(); res = main._produce_video_sync(payload)
body = res if isinstance(res, dict) else json.loads(res.body)
print(f"\nTOTAL {time.time()-t0:.0f}s  status={'ok' if isinstance(res, dict) else res.status_code}")
print(json.dumps({k: body.get(k) for k in ("video_url", "model", "shots", "seconds", "audio", "lines", "detail")}, ensure_ascii=False, indent=1)[:1500])
sc = body.get("shot_clips") or []
print("\nshot_clips:")
t = 0.0
for c in sc:
    print(f"  scene {c['no']} shot {c['shot']}  {c['seconds']}s  t={t:.0f}-{t + c['seconds']:.0f}  ok={c['ok']} role={c['role']} cont={c['continues']}"); t += c["seconds"]
print("\nvoice windows (after re-window onto the real picture):")
for w in voice_windows: print("  ", w)
json.dump({"result": {k: body.get(k) for k in ("video_url", "model", "shots", "seconds", "audio", "lines", "detail")}, "shot_clips": sc, "voice": voice_windows, "clips": log},
          open(os.path.join(OUT, "run.json"), "w"), indent=1, ensure_ascii=False)
vu = body.get("video_url") or ""
if vu.startswith("/renders/"):
    shutil.copy(os.path.join(filmcut.RENDERS_DIR, os.path.basename(vu)), os.path.join(OUT, "film.mp4")); print("film ->", os.path.join(OUT, "film.mp4"))
