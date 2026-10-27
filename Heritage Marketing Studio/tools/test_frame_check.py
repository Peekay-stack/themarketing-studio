#!/usr/bin/env python
"""test_frame_check.py -- offline checks for craft slice 3: framecheck.py (prompt, reader, backstops, the one model call with a fake client) and POST /frame-check with a stubbed
model. No network, no credit, nothing written to the tenant. The real-model run on the owner's 15 frames is tools/engine_trials/frame_check_real.py.
Run:  api/.venv/Scripts/python.exe tools/test_frame_check.py
"""
import base64, io, json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import framecheck as fc, main, gemini

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

# ---- prompt ---------------------------------------------------------------------------------------------------------------------------
p = fc.vision_prompt(description="The boy drinks a glass of milk at the counter.", cast="Boy (8) white shirt; Mother cream saree", wardrobe="navy sweater", pack_expected=True)
check("prompt: carries what the shot should show, the cast and the wardrobe", "The boy drinks a glass of milk" in p and "Boy (8) white shirt" in p and "navy sweater" in p)
check("prompt: names every defect id and asks for JSON only", all(f"`{i}`" in p for i in fc.ISSUE_IDS) and "Return ONLY JSON" in p)
check("prompt: the collage / reference-sheet case is spelled out (the 28 Oct defect)", "pasted together" in p and "reference sheet" in p and "different scale" in p)
check("prompt: a pack is required only when expected; 'unsure is not an issue'", "SHOULD appear" in p and "is not required to" in fc.vision_prompt(description="x") and "not sure of is not an issue" in p)
check("prompt: no brand word in the rules", "heritage" not in p.lower())

# ---- parse / clean / result -----------------------------------------------------------------------------------------------------------
GOOD = {"verdict": "check", "issues": [{"id": "collage", "note": "Two panels pasted side by side at different scales."}, {"id": "anatomy", "note": "The left leg is far longer than the right."}], "seen": "A two-panel composite."}
check("parse: plain / fenced / with chatter", fc.parse(json.dumps(GOOD))["verdict"] == "check" and fc.parse("Here:\n```json\n" + json.dumps(GOOD) + "\n```")["seen"] == "A two-panel composite.")
check("parse: garbage / empty / a list -> None", fc.parse("nope") is None and fc.parse("") is None and fc.parse("[1]") is None)
r = fc.result(GOOD)
check("result: two usable issues -> check, each with its id, label, note", r["verdict"] == "check" and [c["id"] for c in r["checks"]] == ["collage", "anatomy"] and r["checks"][0]["label"] == "Pasted panels" and r["seen"] == "A two-panel composite.")
check("result: a clean reply is ok", fc.result({"verdict": "ok", "issues": [], "seen": "fine"})["verdict"] == "ok")
check("result: a reply that says check but names nothing usable is OK (an unexplained flag is not shown)", fc.result({"verdict": "check", "issues": []})["verdict"] == "ok")
check("result: unknown ids, throwaway notes and duplicates are dropped", [c["id"] for c in fc.result({"issues": [{"id": "vibes", "note": "it feels off to me somehow"}, {"id": "text", "note": "short"},
      {"id": "text", "note": "A caption reads BUY NOW across the bottom."}, {"id": "text", "note": "A second caption on the left side."}]})["checks"]] == ["text"])
check("result: ids are normalised (anatomy / extra_people)", [c["id"] for c in fc.result({"issues": [{"id": "Extra_People", "note": "A stranger stands behind the boy."}]})["checks"]] == ["extra-people"])
check("result: at most six issues; garbage never raises", len(fc.result({"issues": [{"id": i, "note": "a real sentence here"} for i in fc.ISSUE_IDS] + [{"id": "x"}]})["checks"]) <= 6 and fc.result(None)["verdict"] == "ok" and fc.result({"issues": "x"})["verdict"] == "ok")
check("media_type: by extension, jpeg by default", fc.media_type("/x/a.PNG") == "image/png" and fc.media_type("/x/a.webp") == "image/webp" and fc.media_type("/x/a") == "image/jpeg")

# ---- look(): the one model call, with a fake client ---------------------------------------------------------------------------------------------
class Blk:  type = "text"
class Resp:
    def __init__(self, text): b = Blk(); b.text = text; self.content = [b]; u = type("U", (), {})(); u.input_tokens = 2400; u.output_tokens = 90; self.usage = u
class Msgs:
    def __init__(self, text): self.text, self.kw = text, None
    def create(self, **kw): self.kw = kw; return Resp(self.text)
class Client:
    def __init__(self, text): self.messages = Msgs(text)
cl = Client(json.dumps(GOOD))
text, usage = fc.look(b"\x89PNGfake", "image/png", "PROMPT", client=cl)
blocks = cl.messages.kw["messages"][0]["content"]
check("look: sends the frame as a base64 image block first, then the brief", blocks[0]["type"] == "image" and blocks[0]["source"]["media_type"] == "image/png" and base64.b64decode(blocks[0]["source"]["data"]) == b"\x89PNGfake" and blocks[1] == {"type": "text", "text": "PROMPT"})
check("look: returns the reply text and the measured tokens", json.loads(text)["verdict"] == "check" and usage == {"input_tokens": 2400, "output_tokens": 90})
check("look: the model is the configured one", cl.messages.kw["model"] == fc.model_name() and cl.messages.kw["max_tokens"] > 0)

# ---- the route, stubbed ----------------------------------------------------------------------------------------------------------------------------
tmp = os.path.join(tempfile.mkdtemp(), "frame-test.jpg")
from PIL import Image
Image.new("RGB", (64, 36), (120, 110, 90)).save(tmp, "JPEG")
gemini.local_path = lambda u: tmp if str(u).startswith("/media/frame-") else None
main.completion.has_key = lambda: True
seen = {}
def fake_look(data, mime, prompt, client=None):
    seen["data"], seen["mime"], seen["prompt"] = data, mime, prompt
    return seen.get("reply", ""), {"input_tokens": 2400, "output_tokens": 90}
fc.look = fake_look
def call(**over):
    r = main.frame_check({"frame_url": "/media/frame-x.jpg", "description": "The boy drinks.", "cast": "Boy (8)", **over})
    return r if isinstance(r, dict) else {"status": r.status_code, **json.loads(r.body)}
seen["reply"] = json.dumps(GOOD)
r = call()
check("route: a flagged frame comes back as check with its issues, the seen line and the token usage", r["verdict"] == "check" and len(r["checks"]) == 2 and r["usage"]["input_tokens"] == 2400 and r["seen"], str(r))
check("route: the model was given the real image bytes, its type and the shot's words and cast", seen["data"][:2] == b"\xff\xd8" and seen["mime"] == "image/jpeg" and "The boy drinks." in seen["prompt"] and "Boy (8)" in seen["prompt"])
check("route: the pack flag reaches the brief", "SHOULD appear" in (call(pack_expected=True), seen["prompt"])[1])
seen["reply"] = json.dumps({"verdict": "ok", "issues": [], "seen": "A boy drinking."})
check("route: a clean frame is ok", call()["verdict"] == "ok" and call()["checks"] == [])
seen["reply"] = "no idea"
check("route: an unreadable reply is a 502 with a plain message", call().get("status") == 502 and "could not be read" in call()["detail"])
check("route: a frame that is not stored here is a 400 (never a model call)", call(frame_url="/somewhere/else.jpg").get("status") == 400 and call(frame_url="").get("status") == 400)
main.completion.has_key = lambda: False
check("route: no Anthropic key is a 503", call().get("status") == 503)
main.completion.has_key = lambda: True
def boom(*a, **k): raise RuntimeError("upstream down")
fc.look = boom
check("route: a model error is a 502 and never crashes the page", call().get("status") == 502 and "could not run" in call()["detail"])

print("\n%d failed" % len(fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
