#!/usr/bin/env python
"""heritage_redirect.py -- RE-DIRECT the owner's rejected 28 Oct film end to end with the film-craft framework (slices 1-5), from the script to a Draft render. Corpus case 1.

The film is read from the local dev tenant (api/tenants/default/filmscripts/<id>.json, never modified). All outputs go to Downloads\\engine-trial\\heritage_redirect\\.
Stages (each resumes from plan.json, so a failure never repeats paid work):
  plan    director's read -> shot plan per scene (Calm pace, the beat map's rules) -> flow review (apply cuts as SKIP) -> editor's notes (apply the fixes).   Claude calls only.
  frames  frame check on the existing master frames -> re-render any that fail (once) -> render the kept extra shots' frames -> frame check them (re-render once).   Image + vision calls.
  render  the Draft film through the studio's own render function (Omni 360p clips, voice, music), then a contact sheet.                                          Video + voice + music calls.
Usage: heritage_redirect.py plan | frames | render | all
"""
import base64, copy, json, os, shutil, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = os.path.join(ROOT, "api"); sys.path.insert(0, API); os.chdir(API)
from dotenv import load_dotenv
load_dotenv(os.path.join(API, ".env"), encoding="utf-8-sig", override=True)
import main, filmcut, filmdirect, flowreview, framecheck, sceneshots, soundplan, gemini

FID = "063785d77c"
OUT = os.path.join(r"C:\Users\punie\Downloads\engine-trial", "heritage_redirect"); os.makedirs(OUT, exist_ok=True)
PLAN = os.path.join(OUT, "plan.json")
PACE = "calm"
main._record_made = lambda *a, **k: None          # nothing is logged into the tenant's "made" ledger by a trial


def say(*a): print(*a, flush=True)


def load_film():
    d = json.load(open(os.path.join("tenants", "default", "filmscripts", FID + ".json"), encoding="utf-8"))
    return d


def save(plan): json.dump(plan, open(PLAN, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def secs_of(rows):
    out = []
    for r in rows:
        a, _, b = str(r.get("tc") or "").replace("\u2013", "-").replace("s", "").partition("-")
        try: out.append(max(4, round(float(b) - float(a))))
        except ValueError: out.append(4)
    return out


def says(r):
    return " ".join(str((a or {}).get("text") or "") for a in (r.get("audio") or []) if isinstance(a, dict))


def stage_plan():
    d = load_film(); vc = d["video_concept"]
    rows = copy.deepcopy(d["full_script"])
    for r in rows:
        r.pop("shots", None); r.pop("signoff_shots", None)          # a fresh shot plan: the old extras had no job and no reason
    secs = secs_of(rows)
    common = {"logline": vc.get("logline", ""), "message": vc.get("rationale", ""), "tone": " ".join(str(vc.get(k, "")) for k in ("name", "rationale", "logline"))[:300],
              "characters": d.get("video_characters", ""), "film": True}
    say("== 1. the director's read")
    bm = main.film_direct({"scenes": rows, "seconds": secs, "hero": "the product pack", **common})
    assert isinstance(bm, dict), bm
    say("  summary:", bm["summary"]); say("  turn", bm["turn_scene"], "carrier", bm["carrier_scene"], "time_passing", bm["time_passing"])
    for s in bm["scenes"]: say(f"  scene {s['no']} [{s['beat']}] {s['time_mode']:12} i{s['intensity']}  {s['purpose']}")
    nc = filmdirect.no_coverage(bm); say("  no-coverage rule:", nc)
    roles = main._scene_roles(rows, secs)
    say("== 2. the shot plan (Calm pace; the beat map's rules; zero is valid)")
    loc = d.get("video_location_line", "")
    for i, row in enumerate(rows):
        outline = [{"no": r["no"], "secs": secs[j], "visual": r.get("visual", ""), "says": says(r), "shots": [{"job": x.get("job", ""), "visual": x.get("visual", "")} for x in (r.get("shots") or [])]} for j, r in enumerate(rows)]
        res = main.scene_shots({"scene": {k: v for k, v in row.items() if k != "shots"}, "scene_seconds": secs[i], "pace": PACE, "role": roles.get(int(row["no"]), ""), "beat_map": bm, "outline": outline,
                                "scene_index": i, "is_signoff": roles.get(int(row["no"])) == "brand", "plate_locked": False, "characters": d.get("video_characters", ""), "location_line": loc,
                                "prev_visual": rows[i - 1].get("visual", "") if i else "", "next_visual": rows[i + 1].get("visual", "") if i + 1 < len(rows) else "", **common})
        if not isinstance(res, dict):
            say(f"  scene {row['no']}: ERROR {res.status_code} {res.body[:160]}"); continue
        shots = res.get("shots") or []
        say(f"  scene {row['no']} ({secs[i]} s, budget {res.get('budget')}): {len(shots)} extra  -- {res.get('why') or res.get('reason') or ''}")
        if shots:
            row["shots"] = [{k: x[k] for k in ("id", "job", "why", "visual", "shot_size", "camera", "movement_class", "secs")} for x in shots]
            for x in shots: say(f"      + {x['job']:11} {x['shot_size']:7} {x['secs']} s  {x['why']}")
    say("== 3. the flow review")
    rv = main.film_review({"scenes": rows, "seconds": secs, "pace": PACE, "beat_map": bm, **common})
    assert isinstance(rv, dict), rv
    say("  summary:", rv["summary"])
    for f in rv["stats"]["findings"]: say("  finding:", f["note"])
    for v in rv["verdicts"]: say(f"  scene {v['scene']} shot {v['shot']}: {v['verdict'].upper()} {v['reason']}")
    for sk in rv["skips"]:
        for i, r in enumerate(rows):
            if int(r["no"]) == sk["scene"] and r.get("shots"): r["shots"][sk["place"]]["skip"] = True
    live = sum(1 + len([x for x in (r.get("shots") or []) if not x.get("skip")]) for r in rows)
    say(f"  applied {len(rv['skips'])} skip(s): {live} shots left in {sum(secs)} s ({live * 10 / sum(secs):.1f} per 10 s; Calm band 2-2.5)")
    say("== 4. the editor's notes")
    sound = {"duck": "normal", "ending": "fade", "carve": True, "scenes": []}
    en = main.editor_notes({"scenes": rows, "seconds": secs, "beat_map": bm, "sound_plan": sound})
    for n in en["notes"]:
        say(f"  [{n['kind']}] {n['note']}" + (f"   -> FIX: {n['fix']['label']}" if n.get("fix") else ""))
        f = n.get("fix")
        if not f: continue
        if f["type"] == "music": sound["scenes"] = [x for x in sound["scenes"] if x["no"] != f["scene"]] + [{"no": f["scene"], "music": f["value"]}]
        if f["type"] == "line_lead":
            for r in rows:
                if int(r["no"]) == f["scene"]:
                    j = next(k for k, a in enumerate(r["audio"]) if str((a or {}).get("text") or "").strip()); r["audio"][j] = {**r["audio"][j], "timing": "", "timing_at": f["value"]}
    save({"film": FID, "pace": PACE, "rows": rows, "seconds": secs, "beat_map": bm, "review": rv, "editor_notes": en, "sound_plan": sound, "common": common, "cast": d.get("cast_ref_url", ""),
          "frames": {str(i): d["scene_frames"][str(i)]["url"] for i in range(len(rows)) if str(i) in d["scene_frames"]}, "location": loc, "characters": d.get("video_characters", ""),
          "mood": (d.get("sound_plan") or {}).get("mood", "")})
    say("plan saved ->", PLAN)


def still_body(plan, i, k, master_url=None):
    rows = plan["rows"]; row = rows[i]
    sh = [x for x in (row.get("shots") or [])][k - 1] if k else None
    r = {**row, **{kk: sh[kk] for kk in ("visual", "camera", "shot_size") if sh and sh.get(kk)}} if sh else row
    prompt = " ".join(x for x in [r.get("visual", ""), ("Camera: " + r["camera"] + ".") if r.get("camera") else "", ("Location: " + plan["location"]) if plan["location"] else ""] if x)
    body = {"scene_no": int(row["no"]), "prompt": prompt, "ratio": "16:9", "style": "real", "engines": {"image": "google"}, "video_frame": True, "characters": plan["characters"],
            "use_cast": False, "use_plate": False, "brand_mode": "grounded"}
    if r.get("shot_size"): body["shot_size"] = r["shot_size"]
    if k and master_url:
        body["reference_urls"] = [plan["cast"], master_url]; body["compare_to"] = master_url
    else:
        body["reference_url"] = plan["cast"]
    pack = any(w in (r.get("visual") or "").lower() for w in ("the pack", "pouch"))
    body["include_pack"] = bool(pack)
    return body


def check(plan, url, desc):
    res = main.frame_check({"frame_url": url, "description": desc, "cast": plan["characters"], "pack_expected": any(w in desc.lower() for w in ("the pack", "pouch"))})
    return res if isinstance(res, dict) else {"verdict": "error", "checks": [], "seen": str(getattr(res, "body", ""))[:100]}


def stage_frames():
    plan = json.load(open(PLAN, encoding="utf-8")); rows = plan["rows"]; frames = plan.setdefault("frame_log", {})
    spent = {"images": 0, "checks": 0}
    def render(i, k, master=None):
        res = main.scene_still(still_body(plan, i, k, master)); spent["images"] += 1
        if not isinstance(res, dict) or not res.get("image_url"): say("   render failed:", getattr(res, "body", res)); return None
        return res["image_url"]
    say("== frames: check the masters")
    for i, row in enumerate(rows):
        url = plan["frames"].get(str(i)); desc = row.get("visual", "")
        ck = check(plan, url, desc) if url else {"verdict": "missing", "checks": []}; spent["checks"] += 1
        say(f"  scene {row['no']} master: {ck['verdict']} " + "; ".join(f"{c['label']}: {c['note']}" for c in ck["checks"]))
        frames[f"{i}"] = {"url": url, "checks": ck["checks"]}
        if ck["verdict"] in ("check", "missing"):
            for attempt in (1, 2):
                new = render(i, 0)
                if not new: break
                ck2 = check(plan, new, desc); spent["checks"] += 1
                say(f"     re-render {attempt}: {ck2['verdict']} " + "; ".join(f"{c['label']}: {c['note']}" for c in ck2["checks"]))
                plan["frames"][str(i)] = new; frames[f"{i}"] = {"url": new, "checks": ck2["checks"], "rerendered": attempt}
                if ck2["verdict"] == "ok": break
        save(plan)
    say("== frames: the kept extra shots")
    for i, row in enumerate(rows):
        for k, sh in enumerate(row.get("shots") or [], start=1):
            if sh.get("skip"): continue
            master = plan["frames"].get(str(i)); desc = sh["visual"]
            for attempt in (1, 2):
                new = render(i, k, master)
                if not new: break
                ck = check(plan, new, desc); spent["checks"] += 1
                say(f"  scene {row['no']} shot {k + 1} try {attempt}: {ck['verdict']} " + "; ".join(f"{c['label']}: {c['note']}" for c in ck["checks"]))
                sh["frame_url"] = new; frames[f"{i}.{k}"] = {"url": new, "checks": ck["checks"], "attempts": attempt}
                if ck["verdict"] == "ok": break
            save(plan)
    say("spent:", spent)


def stage_render():
    plan = json.load(open(PLAN, encoding="utf-8")); rows = copy.deepcopy(plan["rows"])
    for i, r in enumerate(rows):
        if plan["frames"].get(str(i)): r["frame_url"] = plan["frames"][str(i)]
    payload = {"scenes": rows, "aspect": "16:9", "duration": "30s", "engines": {"video": "google", "music": "google"}, "tier": "lite", "style": "real", "music": plan.get("mood") or "warm tender score",
               "characters": plan["characters"], "brand_mode": "grounded", "sound_plan": plan["sound_plan"], "script": {"logline": plan["common"]["logline"]}}
    log = []
    real = gemini.video
    if "--reuse" in sys.argv:                  # re-use the clips of the previous render (same pictures, no new video spend): look each clip up by the frame it was made from
        old = (plan.get("render") or {}).get("shot_clips") or []
        frames = []
        for i, r in enumerate(rows):
            frames.append(plan["frames"].get(str(i)))
            frames += [x.get("frame_url") for x in (r.get("shots") or []) if not x.get("skip")]
        reuse = {os.path.basename(f): c["url"] for f, c in zip(frames, old) if f}
        say(f"  re-using {len(reuse)} clips from the previous render")
        def real(prompt, **kw):                # noqa: F811
            ref = str(kw.get("image_ref") or "")
            for base, url in reuse.items():
                if base in ref: return url
            say("   no clip to reuse for", ref[:80]); return None
    def spy(prompt, **kw):
        t0 = time.time(); out = real(prompt, **kw)
        log.append({"seconds": kw.get("seconds"), "ok": bool(out), "took": round(time.time() - t0, 1), "err": gemini.video_error()})
        say(f"  clip asked {kw.get('seconds')}s -> {'OK' if out else 'FAILED ' + gemini.video_error()} ({time.time() - t0:.0f}s)")
        return out
    gemini.video = spy
    t0 = time.time(); res = main._produce_video_sync(payload)
    body = res if isinstance(res, dict) else json.loads(res.body)
    say(f"TOTAL {time.time() - t0:.0f}s status={'ok' if isinstance(res, dict) else res.status_code}")
    say(json.dumps({k: body.get(k) for k in ("video_url", "model", "shots", "seconds", "audio", "lines", "detail")}, ensure_ascii=False, indent=1)[:1500])
    plan["render"] = {"result": {k: body.get(k) for k in ("video_url", "model", "shots", "seconds", "audio", "lines", "detail")}, "shot_clips": body.get("shot_clips"), "clips": log}
    save(plan)
    vu = body.get("video_url") or ""
    if vu.startswith("/renders/"):
        dest = os.path.join(OUT, "film.mp4"); shutil.copy(os.path.join(filmcut.RENDERS_DIR, os.path.basename(vu)), dest); say("film ->", dest)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if what in ("plan", "all"): stage_plan()
    if what in ("frames", "all"): stage_frames()
    if what in ("render", "all"): stage_render()
