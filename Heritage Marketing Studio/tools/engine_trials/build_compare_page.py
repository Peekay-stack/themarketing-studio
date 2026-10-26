#!/usr/bin/env python
"""build_compare_page.py -- writes video_engine_comparison.html from the measured metrics. Numbers come from metrics_A/B.json;
only the judgements (grades, one-line reads), prices and render times are written here, each labelled as such on the page."""
import html, json, os
SC = r"C:\Users\punie\AppData\Local\Temp\claude\C--Users-punie-Heritage-Marketing-Studio-OPUS\fcd137c0-c85a-447d-9d35-c10659cecac7\scratchpad"
V = os.path.join(SC, "video_compare")
M = {s: json.load(open(os.path.join(V, f"metrics_{s}.json"), encoding="utf-8")) for s in "AB"}
e = html.escape

# key, name, route, audio, render seconds A/B, price text, risk text, grades A, grades B, read A, read B   (grades: pack, people, scene, motion)
ENG = [
 ("veo31_fast_control", "Veo 3.1 Fast", "fal, our current path", "no", (98, 51), "$0.10 per second, the rate our code records. Not re-checked.", "fal deprecates this endpoint on 17 November 2026.",
  "GGGG", "GGGG", "Held the pouch, face and kitchen. Gentle, restrained motion. A slight plastic sheen on the pouch late in the clip.", "Held everything and followed the prompt. The boy drinks at the end. The smallest camera move of the group."),
 ("kling30", "Kling 3.0 Standard", "fal", "no", (69, 127), "Pro is $0.112 per second without audio on fal's list. Standard, which we ran, is not shown.", "Current model, no deprecation notice seen.",
  "GGGG", "GGGG", "Very stable and crisp. The least motion of the group.", "Held the scene and the label, and followed the slow push-in."),
 ("kling40", "Kling 4.0", "fal", "yes", (248, 355), "Not shown on fal. Reports say from about $0.11 per second, or $0.157 via fal.", "Newest Kling, launched 15 October. Slowest of the Klings to render.",
  "GGGG", "GGPP", "The steadiest pouch colour and size of all seven.", "The label held, but the camera swings around the kitchen more than the prompt asked, and the pouch colour moved the most."),
 ("omni", "Gemini Omni 1.1 Flash", "Google Interactions API, our existing key", "yes", (37, 65), "About $0.10 per second at 720p on Google's pricing page. Measured here: 28,960 video tokens, about $0.51 per clip.", "Google's own replacement for Veo. Image editing of minors is not supported in the EEA, Switzerland or the UK.",
  "GGGG", "GPXP", "Held everything. Softer label detail. Fastest of the Google and fal group.", "Drifted the most. The window and stove were replaced by a plain background, the pouch grew, and a school crest appeared on the shirt."),
 ("minimax_h3max", "MiniMax H3 Max", "fal", "yes", (11, 11), "Not shown on fal.", "Released 27 August 2026. Price unknown until we check the fal dashboard.",
  "GGGG", "GGGG", "Held everything. The pouch turns upright as the pour ends.", "Held everything and followed the prompt. Rendered in 11 seconds."),
 ("wan30", "Wan 3.0", "fal", "no", (102, 101), "Not shown on fal. Alibaba's own API reportedly charges about $0.10 per second at 720p.", "Closed weights. The open Wan line stops at 2.2.",
  "XGPX", "GGGG", "Zoomed in to a blurry orange macro by the last second, which the prompt did not ask for.", "Held everything. The glass fills with milk and the boy smiles."),
 ("seedance20", "Seedance 2.0", "fal", "no", (512, 348), "Billed by token on fal at $0.014 per 1,000 tokens. Reported about $0.30 per second.", "Refuses photoreal faces in reference mode. Slowest by far.",
  "GGGG", "GPGG", "Crisp label and skin detail. Very stable.", "Held well, but invented a crest on the shirt."),
]
GL = {"G": ("Good", "good"), "P": ("Partly", "part"), "X": ("Poor", "poor")}
CRIT = ["Pack label", "People and outfit", "Scene", "Follows the motion"]
def dots(g):
    return "".join(f'<span class="dot {GL[c][1]}" title="{CRIT[i]}: {GL[c][0]}">{GL[c][0][0]}</span>' for i, c in enumerate(g))
def name_of(k): return next(x[1] for x in ENG if x[0] == k)

def scoreboard():
    rows = ""
    for k, nm, route, audio, rt, price, risk, gA, gB, rA, rB in ENG:
        a, b = M["A"]["engines"][k], M["B"]["engines"][k]
        rows += (f'<tr><th scope="row"><b>{e(nm)}</b><small>{e(route)}</small></th>'
                 f'<td class="num">{rt[0]} / {rt[1]} s</td>'
                 f'<td>{dots(gA)}</td><td>{dots(gB)}</td>'
                 f'<td class="num">{a["color_dist"]} / {b["color_dist"]}</td>'
                 f'<td class="num">{a["area_cv"]} / {b["area_cv"]}</td>'
                 f'<td>{e(price)}<small>{e(risk)}</small></td></tr>')
    return rows

def players(scene):
    cards = (f'<figure class="card start"><img src="img/start_{scene}.jpg" alt="Starting frame, scene {scene}" loading="lazy">'
             f'<figcaption><b>Starting frame</b><span>Every engine begins here.</span></figcaption></figure>')
    for k, nm, route, audio, rt, price, risk, gA, gB, rA, rB in ENG:
        g, read = (gA, rA) if scene == "A" else (gB, rB)
        info = M[scene]["engines"][k]
        cards += (f'<figure class="card"><video class="vid" data-scene="{scene}" src="clips/{scene}_{k}.mp4" muted loop playsinline preload="metadata" controls></video>'
                  f'<figcaption><b>{e(nm)}</b><span class="dots">{dots(g)}</span><span class="read">{e(read)}</span>'
                  f'<span class="meta">{rt[0 if scene == "A" else 1]} s to render · {info["size"]} · {info["seconds"]} s{" · audio stripped here" if audio == "yes" else ""}</span>'
                  f'<a href="img/pouch_{scene}_{k}.jpg" target="_blank" rel="noopener"><img class="strip" src="img/pouch_{scene}_{k}.jpg" alt="Pouch close-ups over time, {e(nm)}, scene {scene}" loading="lazy"></a></figcaption></figure>')
    return cards

NOT_TESTED = [
 ("Runway Gen-4.5 and Gen-4 Turbo", "Official: 12 credits per second for Gen-4.5 and 5 for Gen-4 Turbo, at $0.01 per credit. That is $0.12 and $0.05 per second. Runway also resells Omni at 10 credits per second.", "Needs its own Runway account and key. Not on fal."),
 ("Luma Ray 3.2", "Reported $0.06 for a 5 second 360p clip, up to $1.20 at 1080p.", "Needs its own Luma key. Not on fal's list."),
 ("LTX-2.5 (open weights)", "Free commercial use under $10 million revenue, per third-party summaries of the licence.", "Needs a GPU with 32 GB or more to self-host. Not on fal's list."),
 ("HunyuanVideo (open weights)", "Free to download.", "The licence excludes the EU, UK and South Korea, and bars using outputs to train rival models."),
 ("Higgsfield", "Credit-priced subscription platform. Hosts Kling, Veo, Seedance and its own models.", "No public developer API on its homepage, so nothing we can call."),
 ("Google Flow", "Pro $20 and Ultra $50 per month.", "A workspace for people. No API."),
 ("OpenAI Sora", "Gone. The app closed on 26 April 2026 and the API on 24 September 2026.", "Nothing to build on."),
 ("Seedance 2.5", "Listed on fal.", "Not tested. Seedance 2.0 was already the slowest."),
]
def not_tested():
    return "".join(f'<tr><th scope="row">{e(a)}</th><td>{e(b)}</td><td>{e(c)}</td></tr>' for a, b, c in NOT_TESTED)

PAGE = open(os.path.join(SC, "compare_template.html"), encoding="utf-8").read()
for token, val in (("__SCOREBOARD__", scoreboard()), ("__PLAYERS_A__", players("A")), ("__PLAYERS_B__", players("B")), ("__NOT_TESTED__", not_tested())):
    assert token in PAGE, token
    PAGE = PAGE.replace(token, val)
open(os.path.join(V, "video_engine_comparison.html"), "w", encoding="utf-8", newline="").write(PAGE)
print("page written,", len(PAGE) // 1024, "KB")
