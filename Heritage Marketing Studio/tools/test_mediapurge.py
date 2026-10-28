#!/usr/bin/env python
"""test_mediapurge.py -- offline checks for film-builder slice S7 retention (FILM_BUILDER_PLAN.md): mediapurge.py and the routes GET /media-usage and POST /media-purge. A delete cannot be undone, so
this pins the three safety layers: a strict allowlist of file names, everything a saved film still uses is KEPT even when named, and a dry run (the default) deletes nothing. Everything runs in temp folders;
nothing touches the tenant.
Run:  api/.venv/Scripts/python.exe tools/test_mediapurge.py
"""
import json, os, shutil, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api")); os.environ["GOOGLE_API_KEY"] = "test-key"
import mediapurge, gemini, filmscript, main

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

media, films = tempfile.mkdtemp(), tempfile.mkdtemp()
def make(name, size):
    open(os.path.join(media, name), "wb").write(b"x" * size)
    return "/media/" + name
# unchosen / chosen frames and clips of one film, plus files that must never be touched
f_ch, f_un1, f_un2 = make("frame-aaaaaaaaaa.jpg", 1000), make("frame-bbbbbbbbbb.jpg", 2000), make("frame-cccccccccc.png", 3000)
c_ch, c_un, c_src = make("shot-1111111111.mp4", 500), make("shot-2222222222.mp4", 700), make("frame-dddddddddd.jpg", 400)
chain = make("chain-3333333333.jpg", 300)
cur_frame, cast = make("frame-eeeeeeeeee.jpg", 900), make("frame-ffffffffff.jpg", 800)
other = {n: make(n, 100) for n in ("vo-4444444444.mp3", "bed-5555555555.mp3", "kv-6666666666.png", "trim-7777777777.mp4", "still-8888888888.png", "cast-9999999999.jpg")}
json.dump({"cast_ref_url": cast, "scene_frames": {"0": {"status": "done", "url": cur_frame}},
           "video_builder": {"frames": {"0": [{"id": "fr1", "url": f_ch}, {"id": "fr2", "url": f_un1}]}, "frame_chosen": {"0": "fr1"},
                             "takes": {"0": [{"id": "tk1", "url": c_ch, "frame": c_src, "beats": [{"url": c_ch, "seconds": 4}]}, {"id": "tk2", "url": c_un}]}, "chosen": {"0": "tk1"}}},
          open(os.path.join(films, "h1.json"), "w"))
json.dump({"scene_frames": {}, "video_builder": None}, open(os.path.join(films, "h2.json"), "w"))
open(os.path.join(films, "broken.json"), "w").write("{not json")
open(os.path.join(films, "notes.txt"), "w").write("ignored")

# ---- usage ----------------------------------------------------------------------------------------------------------------------------------
u = mediapurge.usage(media)
check("usage counts files and bytes, by kind (the file name's first word)", u["files"] == 15 and u["by_kind"]["frame"]["files"] == 6 and u["by_kind"]["shot"] == {"files": 2, "bytes": 1200} and "vo" in u["by_kind"] and u["bytes"] == sum(os.path.getsize(os.path.join(media, n)) for n in os.listdir(media)), str(u))
check("usage reports free disk space", u["disk_free_bytes"] > 0)
check("usage of a missing folder is empty, not an error", mediapurge.usage(os.path.join(media, "nope"))["files"] == 0)

# ---- what a film still uses ---------------------------------------------------------------------------------------------------------------------
keep = mediapurge.in_use(films)
check("in_use finds the chosen frame, the chosen clip (and its beats), the source frame of a chosen clip, the current storyboard frame and the cast reference; a broken or empty film file is ignored",
      keep == {"frame-aaaaaaaaaa.jpg", "shot-1111111111.mp4", "frame-dddddddddd.jpg", "frame-eeeeeeeeee.jpg", "frame-ffffffffff.jpg"}, str(sorted(keep)))

# ---- a dry run measures and deletes nothing ----------------------------------------------------------------------------------------------------
ask = [f_un1, f_un2, c_un, chain]
r = mediapurge.purge(media, films, ask)
check("the default is a DRY RUN: it reports what would go and how large it is, and removes nothing", r["dry_run"] is True and [d["url"] for d in r["deleted"]] == ask and r["freed_bytes"] == 2000 + 3000 + 700 + 300 and all(os.path.exists(os.path.join(media, os.path.basename(x))) for x in ask), str(r))

# ---- the safety layers ---------------------------------------------------------------------------------------------------------------------------
hostile = [f_ch, c_ch, c_src, cur_frame, cast] + list(other.values()) + ["/media/../main.py", "/media/sub/frame-aaaaaaaaaa.jpg", "/media/frame-aaaaaaaaaa.jpg/../x", "/renders/film-1.mp4", "https://x.test/media/frame-bbbbbbbbbb.jpg",
           "", None, 5, "/media/", "/media/frame-.jpg", "/media/frame-ZZZZZZ.jpg", "/media/frame-bbbbbbbbbb.exe", "C:/Windows/x.jpg", "/media/frame-aaaaaaaaaa.jpg.bak"]
r = mediapurge.purge(media, films, hostile, dry_run=False)
check("naming files a film uses, files off the allowlist, other folders, traversal or junk deletes NOTHING", r["deleted"] == [] and r["freed_bytes"] == 0 and len(os.listdir(media)) == 15, str(r["deleted"]))
reasons = {s["url"]: s["reason"] for s in r["skipped"]}
check("each used file is skipped with the reason 'in use'", all("in use" in reasons[x] for x in (f_ch, c_ch, c_src, cur_frame, cast)), str({x: reasons.get(x) for x in (f_ch, c_ch, c_src, cur_frame, cast)}))
check("voice, music, key visuals, trimmed assemble clips, stills and cast files are 'not a generated frame or clip'", all("not a generated frame or clip" in reasons[x] for x in other.values()), str({x: reasons.get(x) for x in other.values()}))
check("a path outside the media folder, a full URL, an empty or non-string entry is 'not a stored media file'", all("not a stored media file" in reasons.get(x, "") for x in ("/media/../main.py", "/media/sub/frame-aaaaaaaaaa.jpg", "/renders/film-1.mp4", "https://x.test/media/frame-bbbbbbbbbb.jpg", "")), str(reasons))
check("the real main.py is still there", os.path.exists(os.path.join(ROOT, "api", "main.py")))

# ---- a saved Edit-room cut keeps the clips it plays (found in the 28 Oct wiring audit: the real tenant's cuts store names six shot clips) ----------------------------------------------
cuts = tempfile.mkdtemp()
c_cut = make("shot-cccccccc01.mp4", 400); c_cut2 = make("shot-cccccccc02.mp4", 500); c_free = make("shot-cccccccc03.mp4", 600)
json.dump([{"id": "x", "versions": [{"beats": [{"n": 1, "clip_url": c_cut}, {"n": 2, "clip_url": c_cut2}]}]}], open(os.path.join(cuts, "manifest.json"), "w"))
open(os.path.join(cuts, "notes.txt"), "w").write(c_free)
check("without the cuts folder the cut's clips look unused (the gap the audit found)", [d["url"] for d in mediapurge.purge(media, films, [c_cut, c_cut2, c_free])["deleted"]] == [c_cut, c_cut2, c_free])
r = mediapurge.purge(media, films, [c_cut, c_cut2, c_free], dry_run=False, also_dirs=[cuts])
check("with the cuts folder, the clips a saved cut plays are KEPT and only the unreferenced clip goes (a .txt in the folder is ignored)",
      [d["url"] for d in r["deleted"]] == [c_free] and os.path.exists(os.path.join(media, "shot-cccccccc01.mp4")) and os.path.exists(os.path.join(media, "shot-cccccccc02.mp4")) and not os.path.exists(os.path.join(media, "shot-cccccccc03.mp4"))
      and all("saved Edit-room cut" in s["reason"] for s in r["skipped"]), str(r))
check("a missing cuts folder is harmless", mediapurge.in_use(films, also_dirs=[os.path.join(cuts, "nope")]) == mediapurge.in_use(films))
shutil.rmtree(cuts, ignore_errors=True)

# ---- the real delete -------------------------------------------------------------------------------------------------------------------------------
r = mediapurge.purge(media, films, ask + [f_un1], dry_run=False)
check("a real purge removes exactly the unchosen, unused generated files and reports the bytes (a repeated url counts once)",
      [d["url"] for d in r["deleted"]] == ask and r["freed_bytes"] == 6000 and not any(os.path.exists(os.path.join(media, os.path.basename(x))) for x in ask), str(r))
check("every kept file is still there (chosen, current, source, cast, other kinds)", all(os.path.exists(os.path.join(media, os.path.basename(x))) for x in [f_ch, c_ch, c_src, cur_frame, cast] + list(other.values())))
r = mediapurge.purge(media, films, ask, dry_run=False)
check("asking again for files that are gone is harmless ('already gone')", r["deleted"] == [] and all(s["reason"] == "already gone" for s in r["skipped"]))
check("the request size is capped", len(mediapurge.purge(media, films, [f"/media/frame-{i:010x}.jpg" for i in range(900)])["skipped"]) == 500)

# ---- the routes (the media and film folders are the temp ones) -----------------------------------------------------------------------------------------
real_m, real_f = gemini.MEDIA_DIR, filmscript.DIR
gemini.MEDIA_DIR, filmscript.DIR = media, films
def call(fn, *a):
    res = fn(*a)
    return res if isinstance(res, dict) else {"status": res.status_code, **json.loads(res.body)}
fresh = make("frame-1212121212.jpg", 1234)
check("GET /media-usage returns the folder's totals", call(main.media_usage)["files"] == len(os.listdir(media)))
r = call(main.media_purge, {"urls": [fresh]})
check("POST /media-purge defaults to a dry run (no `dry_run` field means NOTHING is deleted)", r["dry_run"] is True and os.path.exists(os.path.join(media, "frame-1212121212.jpg")) and r["freed_bytes"] == 1234, str(r))
r = call(main.media_purge, {"urls": [fresh], "dry_run": "false"})
check("only a real boolean false deletes (the string 'false' is still a dry run)", r["dry_run"] is True and os.path.exists(os.path.join(media, "frame-1212121212.jpg")), str(r))
r = call(main.media_purge, {"urls": [fresh], "dry_run": False})
check("dry_run:false deletes it", r["dry_run"] is False and not os.path.exists(os.path.join(media, "frame-1212121212.jpg")) and r["freed_bytes"] == 1234, str(r))
check("a missing or non-list `urls` is a 400", call(main.media_purge, {}).get("status") == 400 and call(main.media_purge, {"urls": "x"}).get("status") == 400)
check("more than 500 urls is a 400", call(main.media_purge, {"urls": ["/media/a"] * 501}).get("status") == 400)
gemini.MEDIA_DIR, filmscript.DIR = real_m, real_f

shutil.rmtree(media, ignore_errors=True); shutil.rmtree(films, ignore_errors=True)
print("\nALL PASS" if not fails else f"\n{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)
