#!/usr/bin/env python
"""omni_step1.py -- STEP 1 of the 'one engine + optimise the prompt' plan (27 Oct 2026). Scratch script; spends real credit.

PART A  does a better prompt fix what the owner saw?  Scene A (pour) and B (hold) on Gemini Omni at 360p DRAFT ($0.034/s):
        new-style prompt x2 for A, OLD prompt x1 for B (so B compares like for like at 360p), new-style prompt x2 for B.
PART B  can Omni take a whole film at once?  Six DIFFERENT frames from the 30s film, new-style prompts, all fired in PARALLEL.
        Records status codes + latency; Omni's rate limits are not published and Veo hit per-minute limits before.

The 'new style' prompt is the shape a prompt COMPILER would write: time-ordered action with explicit verbs and an end state,
camera as its own section, expression stated, a keep list (pack proportions, outfit, 'no badge'), an audio line, no text.
Output: Downloads\\engine-trial\\step1\\<name>.mp4 + results.json. Reads GOOGLE_API_KEY from api/.env.
"""
import base64, json, os, sys, threading, time
API = r"C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\api"
D = r"C:\Users\punie\Downloads\engine-trial"; S = os.path.join(D, "step1")
sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import httpx
KEY = os.environ["GOOGLE_API_KEY"].strip()
RES = "360p"

def b64(path): return base64.b64encode(open(path, "rb").read()).decode()

def compile_prompt(action, camera, keep, expression, audio="Audio: quiet room sound only, no speech, no music, no voiceover."):
    """The prompt shape under test. Action first, one idea per section."""
    return (f"Animate this frame as one continuous five-second shot, no cuts. ACTION: {action} "
            f"EXPRESSION: {expression} CAMERA: {camera} KEEP IDENTICAL TO THE IMAGE: {keep} {audio} "
            "No on-screen text, captions, subtitles or watermarks. About 5 seconds.")

PACK = ("the Heritage pouch (almost square, orange, green Heritage logo, the words 'Happy Full Cream Milk', same size and "
        "position in the hand throughout, never stretched into a taller rectangle)")

OLD_B = ("Animate this frame. The boy takes the steel glass of milk from the counter and lifts it; the mother keeps "
         "holding the Heritage pouch steady, its front label facing the camera. Camera: a slow, gentle handheld push-in, "
         "shallow depth of field. Keep the pouch, its label and colours, the boy's face, his white shirt and grey shorts, "
         "and the kitchen exactly as in the image. No on-screen text, captions or subtitles. About 5 seconds.")

NEW_A = compile_prompt(
    "0-2 s the mother keeps tilting the pouch so a steady stream of milk falls into the steel vessel; 2-5 s she keeps pouring, the stream thinning slightly as the pouch empties, her eyes following the milk.",
    "a slow, gentle handheld drift, shallow depth of field; no zoom.",
    f"{PACK}; her face; her cream saree with gold border; the window, stove and steel vessel; the warm morning light.",
    "calm and attentive; she does not smile and does not look at the camera.",
    "Audio: quiet kitchen ambience and the sound of pouring only, no speech, no music.")

NEW_B = compile_prompt(
    "0-2 s the boy takes the steel glass from the counter with one hand; 2-4 s he raises it to his lips with both hands and DRINKS, tilting the glass back, his throat moving; 4-5 s he lowers the glass, a little milk on his upper lip. The mother's hand beside him keeps holding the pouch steady with its front label facing the camera.",
    "a slow, gentle handheld push-in, shallow depth of field.",
    f"{PACK}; the boy's face; his plain white school shirt with no badge, crest or logo; his grey shorts; the mother's cream saree; the kitchen window, stove and counter.",
    "plain and absorbed, not smiling.",
    "Audio: quiet kitchen ambience and the clink of the glass only, no speech, no music.")

SIX = {
 "s1": ("frame_s1.jpg", compile_prompt(
    "0-2 s the mother tilts the pouch and a thin stream of milk starts into the steel vessel; 2-5 s the stream steadies as she pours, her eyes on the vessel.",
    "a slow, gentle push-in, shallow depth of field.",
    f"{PACK}; her face; her cream saree; the window, stove and vessel.", "calm and attentive.")),
 "s2": ("frame_s2.jpg", compile_prompt(
    "0-2 s the mother stirs the steaming milk in the steel pot with the ladle; 2-5 s the boy in the background steps a little closer, holding his glass and looking at the pot.",
    "a gentle handheld drift from behind the mother's shoulder; keep her in the foreground.",
    "the mother's cream saree and hair; the boy's white school shirt and his glass; the pot, ladle, granite counter and window.", "the boy curious, the mother absorbed in stirring.")),
 "s3": ("frame_s3.jpg", compile_prompt(
    "0-2 s the lab technician holds the pipette above the steel cup; 2-4 s she carefully lowers it into the sample and draws liquid up; 4-5 s she lifts it and studies the level.",
    "a slow, gentle handheld drift, shallow depth of field.",
    "her blue gloves; her white coat with green trim and the Heritage logo; the instrument display and the test-tube rack.", "focused and careful, no smile.")),
 "s4": ("frame_s4.jpg", compile_prompt(
    "0-2 s the man at the instrument presses a button; 2-5 s the woman writes notes on the clipboard while the man watches the screen.",
    "a slow, gentle handheld drift.",
    "both white coats with green trim and the Heritage logo; the blue gloves; the tray of milk sample tubes; the instrument.", "serious and professional, no smiling.")),
 "s5": ("frame_s5.jpg", compile_prompt(
    "0-2 s the boy lifts the glass of milk to his lips with both hands and drinks, tilting it back; 2-4 s he lowers it, a little milk on his upper lip; 4-5 s the mother, smiling, watches him.",
    "a slow, gentle handheld push-in, warm window light.",
    "the boy's school uniform with the tie; the mother's blue saree; the steel jug; the kitchen and the wooden table.", "the boy absorbed in drinking; the mother warm and smiling.",
    "Audio: quiet kitchen ambience only, no speech, no music.")),
 "s6": ("frame_s6.jpg", NEW_B),
}
FRAMES_AB = {"A": os.path.join(D, "frame_first.jpg"), "B": os.path.join(D, "cand_B_28.5.jpg")}
RESULTS = {}

def omni(name, frame_path, prompt, results):
    t0 = time.time()
    body = {"model": "gemini-omni-1.1-flash",
            "input": [{"type": "image", "data": b64(frame_path), "mime_type": "image/jpeg"}, {"type": "text", "text": prompt}],
            "response_format": {"type": "video", "aspect_ratio": "16:9", "resolution": RES}}
    rec = {"name": name, "started": round(t0, 1)}
    try:
        r = httpx.post("https://generativelanguage.googleapis.com/v1beta/interactions", params={"key": KEY}, json=body, timeout=900)
        rec["status"] = r.status_code; rec["seconds"] = round(time.time() - t0, 1)
        if r.status_code >= 400:
            rec["error"] = r.text[:300]
        else:
            d = r.json(); vid = None
            for st in d.get("steps", []):
                for c in st.get("content", []) or []:
                    if c.get("type") == "video": vid = c
            u = d.get("usage", {}); rec["video_tokens"] = sum(m["tokens"] for m in u.get("output_tokens_by_modality", []) if m.get("modality") == "video")
            if vid and vid.get("data"):
                dest = os.path.join(S, f"{name}.mp4"); open(dest, "wb").write(base64.b64decode(vid["data"])); rec["file"] = dest
            else:
                rec["error"] = "no inline video: " + json.dumps({k: str(v)[:100] for k, v in (vid or {}).items()})
    except Exception as e:
        rec["status"] = "EXC"; rec["seconds"] = round(time.time() - t0, 1); rec["error"] = f"{type(e).__name__}: {str(e)[:200]}"
    results[name] = rec
    print(json.dumps({k: rec.get(k) for k in ("name", "status", "seconds", "video_tokens", "error")}), flush=True)

def stage(label, jobs):
    print(f"\n=== {label}: {len(jobs)} requests fired at once ===", flush=True)
    res = {}; t0 = time.time()
    ts = [threading.Thread(target=omni, args=(n, f, p, res)) for n, f, p in jobs]
    [t.start() for t in ts]; [t.join() for t in ts]
    ok = [r for r in res.values() if r.get("status") == 200]
    print(f"{label}: {len(ok)}/{len(jobs)} OK, wall time {time.time()-t0:.0f}s, statuses {sorted(set(str(r.get('status')) for r in res.values()))}", flush=True)
    RESULTS.update(res)

if __name__ == "__main__":
    which = sys.argv[1:] or ["A", "B"]
    if "A" in which:
        stage("PART A (prompt test)", [("A_new_1", FRAMES_AB["A"], NEW_A), ("A_new_2", FRAMES_AB["A"], NEW_A),
                                       ("B_old_360", FRAMES_AB["B"], OLD_B), ("B_new_1", FRAMES_AB["B"], NEW_B), ("B_new_2", FRAMES_AB["B"], NEW_B)])
    if "B" in which:
        stage("PART B (six-shot concurrency test)", [(f"six_{k}", os.path.join(S, v[0]), v[1]) for k, v in SIX.items()])
    json.dump(RESULTS, open(os.path.join(S, "results.json"), "w"), indent=1)
    tot = sum(r.get("video_tokens", 0) for r in RESULTS.values())
    print(f"\nTOTAL video tokens {tot}  ->  about ${tot*17.5/1e6:.2f} (+ input tokens)")
