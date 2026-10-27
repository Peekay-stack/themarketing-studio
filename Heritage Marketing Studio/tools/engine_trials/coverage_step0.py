#!/usr/bin/env python
"""coverage_step0.py -- STEP 0 trials for the video-coverage plan (VIDEO_COVERAGE_PLAN.md, 27 Oct 2026). Spends real credit.

(a) Does Omni obey "About 2 seconds."?  (360p, two requests)
(b) From a MASTER frame, can /scene-still make other ANGLES (close-up, over-the-shoulder, detail / wide, medium, detail) that keep
    the pack, faces, outfits and kitchen?  Driven through the real route function (main.scene_still) exactly as the studio sends a
    frame, with the real Heritage pack photo injected as the library pack and the master frame as the sibling reference.
    packqa.check() is run on every frame.
(c) Do 3 short shots of one scene, stitched, read as cutting between angles?  Prompts from videoprompt.compile_frame_shot, clips
    from gemini.video (Draft/360p), joined by filmcut.stitch with each shot trimmed to 2 s.

Usage: coverage_step0.py a | b | c | all     Output: Downloads\\engine-trial\\coverage_step0\\
"""
import base64, json, os, re, shutil, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = os.path.join(ROOT, "api"); sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
D = r"C:\Users\punie\Downloads\engine-trial"; OUT = os.path.join(D, "coverage_step0"); os.makedirs(OUT, exist_ok=True)
import main, gemini, library, filmcut, videoprompt, packqa
import imageio_ffmpeg
EXE = imageio_ffmpeg.get_ffmpeg_exe()

def uri(path, mime=None):
    mime = mime or ("image/png" if path.endswith(".png") else "image/jpeg")
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()

PACK_PHOTO = os.path.join(D, "ref1_pack.png")
MASTERS = {"B": os.path.join(D, "cand_B_28.5.jpg"), "A": os.path.join(D, "frame_first.jpg")}
SHOTS = {  # scene -> [(label, shot_size, text, include_pack)]  (the master is shot 1 and already exists)
 "B": [("close", "close", "Close-up on the boy's face and shoulders as he looks down at the steel glass he holds in both hands; at the edge of the frame his mother's hand holds the Heritage pouch.", True),
       ("over", "medium", "Over-the-shoulder shot from behind the mother's shoulder: the boy stands at the kitchen counter taking the steel glass, the Heritage pouch in the mother's hand in the foreground.", True),
       ("detail", "close", "Detail insert: the mother's hand holding the Heritage pouch front-on beside the steel glass, label facing the camera, the boy's blurred face behind.", True)],
 "A": [("detail", "close", "Detail insert: the corner of the Heritage pouch tilted over the steel vessel, a thin stream of milk pouring in.", True),
       ("medium", "medium", "Medium shot of the mother from the waist up, looking down as she pours milk from the Heritage pouch into the steel vessel.", True),
       ("wide", "wide", "Wide shot of the whole kitchen: the mother at the counter by the window pouring milk from the Heritage pouch into a steel vessel.", True)],
}
MOVES = {"close": "A slow, gentle push-in.", "medium": "A gentle handheld drift.", "wide": "A slow, steady pull-out.", "detail": "A slow rack of focus, nearly static."}

def dur(path):
    t = subprocess.run([EXE, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", t)
    return round(int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)), 2) if m else -1

# ---------------------------------------------------------------- (a) 2-second request
def part_a():
    import httpx
    print("== (a) Omni and a 2-second request", flush=True)
    frame = os.path.join(D, "step1", "frame_s1.jpg")
    for n in (2, 2, 1):
        body = {"model": "gemini-omni-1.1-flash",
                "input": [{"type": "image", "data": base64.b64encode(open(frame, "rb").read()).decode(), "mime_type": "image/jpeg"},
                          {"type": "text", "text": "Animate this frame as one continuous shot, no cuts. ACTION: the mother keeps pouring a steady stream of milk into the steel vessel. CAMERA: a slow gentle push-in. KEEP IDENTICAL TO THE IMAGE: her face, saree, pack, kitchen. Audio: quiet room sound only; no speech, no music. No on-screen text. " + f"About {n} second{'s' if n != 1 else ''}."}],
                "response_format": {"type": "video", "aspect_ratio": "16:9", "resolution": "360p"}}
        r = httpx.post(gemini.INTERACTIONS, headers=gemini._headers(), json=body, timeout=300)
        if r.status_code >= 400:
            print(f"  asked {n}s -> HTTP {r.status_code} {r.text[:200]}"); time.sleep(9); continue
        raw = gemini._video_bytes(r.json()); p = os.path.join(OUT, f"a_{n}s_{int(time.time()) % 1000}.mp4"); open(p, "wb").write(raw)
        print(f"  asked {n}s -> got {dur(p)}s", flush=True); time.sleep(9)

# ---------------------------------------------------------------- (b) other angles from the master
def part_b():
    print("== (b) angles from the master frame", flush=True)
    pack_uri = uri(PACK_PHOTO)
    def fake_refs(max_refs=3, want_pack=False, pack_id="", want_cast=True, cast_id="", plate_id="", brand=""):
        refs = [pack_uri] if want_pack else []
        return {"refs": refs, "kinds": ["pack"] * len(refs), "cast": "", "pack": pack_uri if want_pack else "", "plate": "",
                "has_cast": False, "has_pack": bool(want_pack), "has_plate": False, "dropped": [], "why": ""}
    library.shot_references = fake_refs                      # the real pack photo plays the signed-off library pack
    main._record_made = lambda *a, **k: None                 # nothing recorded in the tenant
    ref_bytes = open(PACK_PHOTO, "rb").read(); results = {}
    for scene, shots in SHOTS.items():
        master = MASTERS[scene]; results[scene] = {"master": packqa.check(open(master, "rb").read(), ref_bytes)}
        print(f" scene {scene} master: {results[scene]['master'].get('verdict')} ratio={results[scene]['master'].get('ratio')}", flush=True)
        for label, size, text, pack in shots:
            payload = {"scene_no": 1, "prompt": text, "ratio": "16:9", "style": "real", "video_frame": True, "shot_size": size,
                       "include_pack": pack, "engines": {"image": "google"}, "use_cast": False,
                       "reference_urls": [uri(master)]}      # the master carries cast + place: the "match this shot" channel
            t0 = time.time(); res = main.scene_still(payload)
            body = res if isinstance(res, dict) else json.loads(res.body)
            url = body.get("image_url")
            if not url:
                print(f"  {scene}/{label}: FAILED {str(body)[:200]}"); results[scene][label] = {"error": str(body)[:200]}; continue
            p = gemini.local_path(url); dst = os.path.join(OUT, f"frame_{scene}_{label}.jpg")
            shutil.copy(p, dst)
            chk = body.get("pack_check") or packqa.check(open(dst, "rb").read(), ref_bytes)
            results[scene][label] = {"verdict": chk.get("verdict"), "ratio": chk.get("ratio"), "note": chk.get("note"),
                                     "pack_used": body.get("pack_used"), "refs": body.get("references"), "secs": round(time.time() - t0, 1)}
            print(f"  {scene}/{label}: ok {results[scene][label]['secs']}s pack_check={chk.get('verdict')} ratio={chk.get('ratio')} refs={body.get('references')}", flush=True)
    json.dump(results, open(os.path.join(OUT, "part_b.json"), "w"), indent=1)

# ---------------------------------------------------------------- (c) 3 shots of one scene, stitched
def part_c():
    print("== (c) three shots, stitched", flush=True)
    gemini.available = lambda: True
    for scene in ("B", "A"):
        shots = [("master", "wide" if scene == "A" else "medium", MASTERS[scene], None)]
        order = ["close", "detail"] if scene == "B" else ["detail", "wide"]     # the angles that actually differ from the master (see part b)
        for label in order:
            f = os.path.join(OUT, f"frame_{scene}_{label}.jpg")
            if os.path.exists(f): shots.append((label, label, f, None))
        # cut order for the film: master first, then the angles as they come (max 3 shots)
        shots = shots[:3]; clips = []
        for k, (label, size, frame, _) in enumerate(shots):
            text = {"master": ("The boy takes the steel glass from the counter." if scene == "B" else "The mother tilts the pouch and milk pours in a steady stream.")}.get(label)
            if not text:
                text = [t for (l, s, t, p) in SHOTS[scene] if l == label][0]
            prompt = videoprompt.compile_frame_shot(action=text, continues=(k > 0), camera_direction="Camera: " + MOVES.get(size, MOVES["close"]), pack_in_frame=True)
            t0 = time.time(); url = gemini.video(prompt, image_ref=uri(frame), seconds=2, ratio="16:9", tier="lite")   # a data URI: gemini only reads media-folder paths
            print(f"  {scene} shot {k+1} ({label}): {'OK' if url else 'FAILED ' + gemini.video_error()} {time.time()-t0:.0f}s", flush=True)
            if url: clips.append(url)
        if len(clips) >= 2:
            name = filmcut.stitch(clips, [2] * len(clips))
            if name:
                src = os.path.join(filmcut.RENDERS_DIR, name); dst = os.path.join(OUT, f"cut_{scene}.mp4"); shutil.copy(src, dst)
                print(f"  {scene}: stitched {len(clips)} shots -> {dur(dst)}s  ({dst})", flush=True)
        for i, u in enumerate(clips):
            p = gemini.local_path(u)
            if p: shutil.copy(p, os.path.join(OUT, f"shot_{scene}_{i+1}.mp4"))

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("a", "all"): part_a()
    if which in ("b", "all"): part_b()
    if which in ("c", "all"): part_c()
