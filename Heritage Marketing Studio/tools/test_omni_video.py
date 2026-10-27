#!/usr/bin/env python
"""test_omni_video.py -- offline checks for gemini.video() (the Gemini Omni path). No network, no credit: httpx.post is
stubbed. Media is written to a temp dir, never the tenant's. Run:  api/.venv/Scripts/python.exe tools/test_omni_video.py
"""
import base64, os, subprocess, sys, tempfile, types
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api"))
os.environ["GOOGLE_API_KEY"] = "test-key"
import gemini, httpx, imageio_ffmpeg

TMP = tempfile.mkdtemp(prefix="omni-test-"); gemini.MEDIA_DIR = TMP
EXE = imageio_ffmpeg.get_ffmpeg_exe()

def make_clip(with_audio=True):
    """A real 1-second mp4 (with a sine audio track) so the silencing step is exercised for real."""
    out = os.path.join(TMP, "src.mp4")
    cmd = [EXE, "-y", "-f", "lavfi", "-i", "color=c=orange:s=64x64:d=1:r=24"]
    if with_audio: cmd += ["-f", "lavfi", "-i", "sine=frequency=440:duration=1"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p"] + (["-c:a", "aac", "-shortest"] if with_audio else []) + [out]
    subprocess.run(cmd, capture_output=True, check=True)
    return open(out, "rb").read()

CLIP = make_clip()
FRAME = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff\xe0fakejpeg").decode()
calls, script = [], []

class Resp:
    def __init__(self, code, js=None, text=""): self.status_code, self._js, self.text = code, js, text or (str(js) if js else "")
    def json(self): return self._js
    def raise_for_status(self): pass

def ok_resp(): return Resp(200, {"steps": [{"content": [{"type": "video", "data": base64.b64encode(CLIP).decode(), "mime_type": "video/mp4"}]}]})

def fake_post(url, headers=None, json=None, timeout=None, **kw):
    calls.append(json); return script.pop(0)

httpx.post = fake_post
slept = []
gemini.time.sleep = lambda s: slept.append(s)       # no real waiting in tests

def reset(): calls.clear(); script.clear(); slept.clear(); gemini._QUOTA_SPENT.clear(); gemini._omni_stamps.clear()

def has_audio(path):
    return "Audio:" in subprocess.run([EXE, "-i", path], capture_output=True, text=True).stderr

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

# 1. success: request shape, resolution per tier, duration sentence owned by video(), audio stripped, stored under MEDIA_DIR
assert has_audio(os.path.join(TMP, "src.mp4")), "test clip should start with audio"
reset(); script.append(ok_resp())
url = gemini.video("Animate this frame. ACTION: he drinks. About 5 seconds.", image_ref=FRAME, seconds=6, ratio="16:9", tier="lite")
b = calls[0]
check("success returns a /media/shot- path", bool(url) and url.startswith("/media/shot-"), url)
check("model is gemini-omni-1.1-flash", b["model"] == "gemini-omni-1.1-flash")
check("lite -> 360p", b["response_format"]["resolution"] == "360p")
check("response_format type video + aspect", b["response_format"]["type"] == "video" and b["response_format"]["aspect_ratio"] == "16:9")
check("image block first, text second", [x["type"] for x in b["input"]] == ["image", "text"])
txt = b["input"][1]["text"]
check("duration sentence is 6 and appears once", txt.endswith("About 6 seconds.") and txt.lower().count("about") == 1, txt)
check("saved clip has NO audio track", url and not has_audio(os.path.join(TMP, os.path.basename(url))))
check("no error left after success", gemini.video_error() == "")
reset(); script.append(ok_resp())
gemini.video("x", image_ref=FRAME, seconds=8, ratio="9:16", tier="standard")
check("standard -> 720p, 9:16 kept", calls[0]["response_format"]["resolution"] == "720p" and calls[0]["response_format"]["aspect_ratio"] == "9:16")
reset(); script.append(ok_resp())
gemini.video("x", image_ref="", seconds=20, tier="nonsense")
check("seconds clamp to 8, unknown tier -> cheapest, no image block when no frame",
      calls[0]["input"][-1]["text"].endswith("About 8 seconds.") and calls[0]["response_format"]["resolution"] == "360p" and len(calls[0]["input"]) == 1)

# 2. 402: no retry, clear reason, benched so the next shot skips the doomed call
reset(); script.append(Resp(402, text='{"error":{"code":402,"message":"Your prepayment credits are depleted."}}'))
check("402 returns None", gemini.video("x", image_ref=FRAME, seconds=5) is None)
check("402 reason names credit + top-up", "credit" in gemini.video_error() and "top up" in gemini.video_error().lower(), gemini.video_error())
n = len(calls)
check("402 sent exactly one request", n == 1)
check("benched: next shot makes no request", gemini.video("x", image_ref=FRAME, seconds=5) is None and len(calls) == n)
check("benched reason reaches video_error", "credit" in gemini.video_error().lower(), gemini.video_error())

# 3. 429 with the API's own wording: waits the stated time, then succeeds
reset(); script.extend([Resp(429, text='{"error":{"message":"Rate limit exceeded ... limit: 8 requests per minute on Tier 2. Please retry in 15s or upgrade"}}'), ok_resp()])
check("429 then success returns a path", bool(gemini.video("x", image_ref=FRAME, seconds=5)))
check("429 waited 16 s (15 + 1) and made 2 requests", slept == [16.0] and len(calls) == 2, str(slept))
reset(); script.extend([Resp(429, text="rate limited")] * 4)
check("429 forever gives up with a plain reason", gemini.video("x", image_ref=FRAME, seconds=5) is None and "per-minute" in gemini.video_error(), gemini.video_error())
check("429 forever made 4 requests (1 + 3 retries)", len(calls) == 4, str(len(calls)))

# 4. safety block: one request, plain reason, NOT benched (it is about this shot, not the account)
reset(); script.append(Resp(400, text='{"error":{"message":"Request blocked due to safety violations (harmful content)."}}'))
check("safety 400 returns None with reason", gemini.video("x", image_ref=FRAME, seconds=8) is None and "safety" in gemini.video_error(), gemini.video_error())
check("safety 400 does not bench the engine", gemini.quota_spent("lite") == "")

# 5. server errors retry twice then stop
reset(); script.extend([Resp(503, text="busy"), Resp(503, text="busy"), ok_resp()])
check("503, 503, success -> success after 10s and 25s waits", bool(gemini.video("x", image_ref=FRAME, seconds=5)) and slept == [10.0, 25.0], str(slept))

# 6. limiter: OMNI_RPM requests go through at once, the next one waits for the oldest to age out (fake clock)
reset()
clock = [1000.0]
gemini.time = types.SimpleNamespace(time=lambda: clock[0], sleep=lambda s: (slept.append(s), clock.__setitem__(0, clock[0] + s)))
gemini.OMNI_RPM = 3
for _ in range(3): gemini._omni_slot()
check("3 slots at once, no wait", slept == [])
gemini._omni_slot()
check("4th slot waits about 60 s", len(slept) >= 1 and 59.0 <= sum(slept) <= 61.0, str(slept))

print("\n%d failed" % len(fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
