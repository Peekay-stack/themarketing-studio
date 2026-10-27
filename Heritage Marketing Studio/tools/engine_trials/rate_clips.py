#!/usr/bin/env python
"""rate_clips.py -- an independent second opinion on trial clips. Sends each clip (video + its audio) to a Gemini model that can
watch and listen, with the INTENDED action, and asks factual yes/no questions: does anyone speak, did the intended action happen,
is there a crest/badge on a shirt, is there on-screen text, any obvious artefacts. A model is an imperfect judge: use it next to
your own eyes, not instead. Pennies per clip. Scratch script. Output: Downloads\\engine-trial\\step1\\ratings.json
"""
import base64, json, os, sys
API = r"C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\api"
D = r"C:\Users\punie\Downloads\engine-trial"; S = os.path.join(D, "step1")
sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import httpx
KEY = os.environ["GOOGLE_API_KEY"].strip(); MODEL = "gemini-3.5-flash"

INTENT = {  # clip -> the action the prompt asked for (plain words)
 "A": "The mother keeps pouring milk from the orange pouch into the steel vessel with a steady stream, calm, not smiling, camera drifting slowly.",
 "B": "The boy takes the steel glass from the counter and DRINKS from it (glass raised to his lips and tilted); the mother's hand keeps holding the orange pouch steady, label facing the camera.",
 "s1": "The mother tilts the orange pouch and a thin stream of milk starts into the steel vessel, then steadies.",
 "s2": "The mother stirs milk in the steel pot with a ladle while the boy in the background steps closer holding his glass.",
 "s3": "The lab technician holds a pipette above a steel cup, lowers it into the sample, draws liquid up and lifts it to study the level.",
 "s4": "The man at the instrument presses a button while the woman writes notes on a clipboard.",
 "s5": "The boy lifts the glass of milk to his lips with both hands and drinks, then lowers it with a little milk on his lip; the mother smiles at him.",
 "s6": "The boy takes the steel glass from the counter and DRINKS from it; the mother's hand keeps holding the orange pouch steady, label facing the camera.",
}
CLIPS = {  # name -> (path, intent key)
 "OLD A 720p": (os.path.join(D, "i2v_omni.mp4"), "A"), "OLD A 360p": (os.path.join(D, "i2v_omni360.mp4"), "A"),
 "OLD B 720p": (os.path.join(D, "i2v_B_omni.mp4"), "B"),
 "A_new_1": (os.path.join(S, "A_new_1.mp4"), "A"), "A_new_2": (os.path.join(S, "A_new_2.mp4"), "A"),
 "B_old_360": (os.path.join(S, "B_old_360.mp4"), "B"), "B_new_1": (os.path.join(S, "B_new_1.mp4"), "B"), "B_new_2": (os.path.join(S, "B_new_2.mp4"), "B"),
 **{f"six_{k}": (os.path.join(S, f"six_{k}.mp4"), k) for k in ("s1", "s2", "s3", "s4", "s5", "s6")},
}
Q = ("You are checking an AI-generated video clip against what was intended. INTENDED ACTION: {intent}\n"
     "Watch the video and listen to the audio, then answer with ONLY compact JSON with these keys: "
     '"speech" (verbatim words spoken by any human voice, or "NONE"), '
     '"action" ("yes", "partly" or "no": did the intended action happen as described?), '
     '"action_note" (one short sentence: what actually happens, e.g. whether a glass is drunk from or only raised like a toast), '
     '"boy_smiles" ("yes", "no" or "n/a"), '
     '"shirt_badge" ("yes" if any badge, crest or logo appears on a child\'s shirt, else "no" or "n/a"), '
     '"text_on_screen" ("yes" if any captions or readable lettering other than the product pack appear, else "no"), '
     '"pack_shape" (if an orange milk pouch is visible: "squarish", "tall rectangle" or "wide rectangle"; else "n/a"), '
     '"artefacts" (one short phrase about warped hands, melting objects or sudden scene changes, or "none").')

def rate(name, path, key):
    if not os.path.exists(path): return {"error": "missing file"}
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "video/mp4", "data": base64.b64encode(open(path, "rb").read()).decode()}},
                                    {"text": Q.format(intent=INTENT[key])}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent", params={"key": KEY}, json=body, timeout=300)
    if r.status_code >= 400: return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    try:
        txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(txt)
    except Exception as e:
        return {"error": f"parse: {e}", "raw": r.text[:300]}

if __name__ == "__main__":
    out = {}
    for name, (path, key) in CLIPS.items():
        out[name] = rate(name, path, key)
        print(f"{name:12s}", json.dumps(out[name], ensure_ascii=False)[:420], flush=True)
    json.dump(out, open(os.path.join(S, "ratings.json"), "w"), indent=1, ensure_ascii=False)
