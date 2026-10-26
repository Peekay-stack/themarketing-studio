"""omni_draft_test.py -- measure Omni's billed tokens at 360p (draft) vs the 720p we already measured (28,960 tokens / 5.0 s).
Same frame and prompt as scene A. Scratch script. Saves Downloads\\engine-trial\\i2v_omni360.mp4."""
import base64, json, os, sys, time
API = r"C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\api"
OUT = r"C:\Users\punie\Downloads\engine-trial"
sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import httpx
B64 = base64.b64encode(open(os.path.join(OUT, "frame_first.jpg"), "rb").read()).decode()
PROMPT = ("Animate this frame. The mother keeps pouring the milk from the Heritage pouch into the steel vessel, the milk "
          "stream falling steadily; her head and hands move naturally. Camera: a slow, gentle handheld drift, shallow depth "
          "of field. Keep the pouch, its label and colours, her face, her saree and the kitchen exactly as in the image. "
          "No on-screen text, captions or subtitles. About 5 seconds.")
key = os.environ["GOOGLE_API_KEY"].strip()
for res in sys.argv[1:] or ["360p"]:
    body = {"model": "gemini-omni-1.1-flash",
            "input": [{"type": "image", "data": B64, "mime_type": "image/jpeg"}, {"type": "text", "text": PROMPT}],
            "response_format": {"type": "video", "aspect_ratio": "16:9", "resolution": res}}
    t0 = time.time()
    r = httpx.post("https://generativelanguage.googleapis.com/v1beta/interactions", params={"key": key}, json=body, timeout=900)
    if r.status_code >= 400:
        print(res, "HTTP", r.status_code, r.text[:500]); continue
    d = r.json(); vid = None
    for st in d.get("steps", []):
        for c in st.get("content", []) or []:
            if c.get("type") == "video": vid = c
    usage = d.get("usage", {})
    vt = sum(m["tokens"] for m in usage.get("output_tokens_by_modality", []) if m.get("modality") == "video")
    dest = os.path.join(OUT, f"i2v_omni{res.replace('p','')}.mp4")
    if vid and vid.get("data"): open(dest, "wb").write(base64.b64decode(vid["data"]))
    cost = vt * 17.5 / 1e6 + usage.get("total_input_tokens", 0) * 1.5 / 1e6
    print(f"{res}: {time.time()-t0:.0f}s | video tokens {vt} | input tokens {usage.get('total_input_tokens')} | est. cost ${cost:.3f} | file {dest if vid else 'NO VIDEO'}")
