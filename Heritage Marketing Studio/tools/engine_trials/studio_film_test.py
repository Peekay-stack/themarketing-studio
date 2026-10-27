#!/usr/bin/env python
"""studio_film_test.py -- a REAL film through the studio's own render function (main._produce_video_sync), no generator stubs.
Spends real credit (Gemini Omni, Draft tier ~ 0.034 USD/s). Picture only: no voice, no music, so what is tested is the engine
path, the prompt compiler, the limiter, the stitch. The ledger write is stubbed so nothing is recorded in the tenant.
Frames: the six Heritage trial frames in Downloads\\engine-trial. Output copied to Downloads\\engine-trial\\studio_run\\.
Usage: studio_film_test.py [lite|standard] [seconds]
"""
import base64, json, os, shutil, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = os.path.join(ROOT, "api"); sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
D = r"C:\Users\punie\Downloads\engine-trial"; OUT = os.path.join(D, "studio_run"); os.makedirs(OUT, exist_ok=True)
import main, gemini, filmcut

tier = sys.argv[1] if len(sys.argv) > 1 else "lite"
secs = sys.argv[2] if len(sys.argv) > 2 else "30"
def uri(p): return "data:image/jpeg;base64," + base64.b64encode(open(p, "rb").read()).decode()
S = os.path.join(D, "step1")
ROWS = [
 ("frame_s2.jpg", "The mother stirs the steaming milk in the steel pot with a ladle while the boy steps closer, holding his glass."),
 ("frame_s3.jpg", "A lab technician lowers a pipette into a steel cup of milk sample, draws the liquid up and lifts it to study the level."),
 ("frame_s4.jpg", "A man presses a button on the instrument while a woman beside him writes notes on a clipboard."),
 ("frame_s5.jpg", "The boy lifts the glass of milk to his lips with both hands and drinks; his mother smiles at him."),
 ("frame_s6.jpg", "The boy takes the steel glass from the counter and drinks, the mother's hand steadying the Heritage pouch."),
 ("../frame_first.jpg", "The mother pours a steady stream of milk from the Heritage pouch into the steel vessel."),
]
scenes = [{"no": i + 1, "t": f"{i*5}\u2013{i*5+5}s", "title": txt, "desc": "", "camera": "", "dialogue": "", "frame_url": uri(os.path.join(S, f))}
          for i, (f, txt) in enumerate(ROWS)]
payload = {"scenes": scenes, "aspect": "16:9", "duration": f"{secs}s", "engines": {"video": "google", "music": "google"},
           "tier": tier, "with_music": False, "style": "real"}

main._record_made = lambda *a, **k: None            # never write to the tenant's ledger
captured = []
_real_video = gemini.video
def spy(prompt, **kw):
    t0 = time.time(); out = _real_video(prompt, **kw)
    captured.append({"seconds_asked": kw.get("seconds"), "tier": kw.get("tier"), "ok": bool(out), "took": round(time.time() - t0, 1),
                     "error": gemini.video_error(), "url": out, "prompt": prompt})
    print(f"  shot: asked {kw.get('seconds')}s tier={kw.get('tier')} -> {'OK ' + str(out) if out else 'FAILED: ' + gemini.video_error()} ({time.time()-t0:.0f}s)", flush=True)
    return out
gemini.video = spy
t0 = time.time()
res = main._produce_video_sync(payload)
body = res if isinstance(res, dict) else json.loads(res.body)
print(f"\nTOTAL {time.time()-t0:.0f}s  status={'dict' if isinstance(res, dict) else res.status_code}")
print(json.dumps({k: body.get(k) for k in ("video_url", "model", "shots", "seconds", "audio", "detail")}, ensure_ascii=False, indent=1)[:1800])
json.dump({"captured": captured, "result": {k: body.get(k) for k in ("video_url", "model", "shots", "seconds", "detail")}}, open(os.path.join(OUT, "run.json"), "w"), indent=1, ensure_ascii=False)
vu = body.get("video_url") or ""
if vu.startswith("/renders/"):
    src = os.path.join(filmcut.RENDERS_DIR, os.path.basename(vu)); dst = os.path.join(OUT, "film.mp4"); shutil.copy(src, dst); print("film copied ->", dst)
for i, c in enumerate(captured):
    if c.get("url"):
        p = gemini.local_path(c["url"])
        if p: shutil.copy(p, os.path.join(OUT, f"shot_{i+1}.mp4"))
