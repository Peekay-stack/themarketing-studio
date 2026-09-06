"""main.py — The Marketing Studio API.

Run:  uvicorn main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

import json
import os
import re
import sys
import uuid

# Load environment keys robustly: read the .env that sits NEXT TO this file (api/.env) by
# absolute path (independent of the working directory), and use utf-8-sig so a BOM written
# by Notepad does not corrupt the first key name. Fall back to the studio-root .env and the
# default search too.
try:
    from dotenv import load_dotenv
    _API_DIR = os.path.dirname(os.path.abspath(__file__))
    for _p in (os.path.join(_API_DIR, ".env"), os.path.join(_API_DIR, os.pardir, ".env")):
        if os.path.exists(_p):
            load_dotenv(_p, encoding="utf-8-sig", override=True)
    load_dotenv(encoding="utf-8-sig")  # default search as a last resort
except Exception:
    pass
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

import activation
import actuals
import auth as auth_mod
import brandprofile
import briefguide
import briefstore
import campaign as campaign_mod
import catalog
import complete as completion
import composite
import continuity
import creative
import cut
import docs
import domain
import execution
import filmaudio
import filmcut
import filmvoice
import findings
import gemini
import generation
import geo
import heygen
import ideas
import keyvisual
import learning
import library
import made
import media
import mediaplan
import plan

# `/executions?plan=` takes a query parameter called `plan`, which would shadow the module inside that
# handler. The alias is what the execution endpoints use so the shadowing can never bite.
import plan as plan_mod
import posm
import pr
import producers
import project
import roundtrip
import sales
import schemas
import shelf
import shots
import socialplan
import strategy
import tenancy
from database import get_db, init_db
import people
from models import Brief, ChatMessage, Deliverable, User
from models import Session as SessionRow

app = FastAPI(title="The Marketing Studio API")
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/health")
def health():
    """Quick wiring check — open http://127.0.0.1:8000/health in the browser.

    Each flag is simply "can the app see this key". A `false` here is why a feature falls back to
    placeholders, so check this first before assuming something is broken.
    """
    def seen(*names: str) -> bool:
        return any((os.environ.get(n) or "").strip() for n in names)
    return {"ok": True,
            "anthropic": seen("ANTHROPIC_API_KEY"),
            "fal": seen("FAL_KEY"),
            # Gemini/Veo/Imagen. The google-genai SDK accepts either name, so both are honoured.
            "google": seen("GEMINI_API_KEY", "GOOGLE_API_KEY"),
            "heygen": seen("HEYGEN_API_KEY"),
            "sarvam": seen("SARVAM_API_KEY"),
            "nvidia": seen("NVIDIA_API_KEY"),
            "model": os.environ.get("GEN_MODEL", "claude-opus-4-8")}


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


# --- round 46: real sign-in, replacing the X-User-Id header default ----------------------------
#
# The old `current_user` trusted a caller-supplied header and defaulted to "puneet" when it was
# absent -- meaning any request with no header at all was silently treated as a specific real user
# with no check whatsoever. Nothing in the live product ever called it (0 references to /briefs,
# /users or /me in app.dc.html), so the blast radius of fixing it was zero, but it was the only
# auth-shaped code in the whole backend and it was fabricating an identity by default. Fixed here
# rather than left for whenever the rest of the product grows a login screen.
#
# Contract, as agreed with Design in ASK_DESIGN_45_REPLY / the round-46 handover:
#   POST /login {username, password} -> 200 {user:{id,name,role,tenant}}, sets an httpOnly session
#   cookie. No token in the response body -- the cookie IS the session, so there is nothing for the
#   frontend to store or attach itself. 401 on bad credentials, same shape as every other refusal in
#   this API ({"detail": "..."}).
#   POST /logout -> deletes the session row server-side (real revocation, not a client-side forget)
#   and clears the cookie. 200 whether or not a session existed -- logging out twice is not an error.
#   Any route using `current_user` now returns 401 with that same shape when the cookie is missing,
#   unknown, or expired. Design's plan is a global "401 anywhere means signed out" redirect on the
#   frontend rather than a per-route toast; this is what makes that consistent to build against.


def current_user(studio_session: str | None = Cookie(default=None),
                  db: Session = Depends(get_db)) -> User:
    if not studio_session:
        raise HTTPException(401, "Not signed in.")
    row = db.get(SessionRow, studio_session)
    if not row or row.expires < auth_mod.utcnow():
        raise HTTPException(401, "Session expired or not recognised.")
    user = db.get(User, row.user_id)
    if not user:
        raise HTTPException(401, "Session refers to no user.")
    return user


def _brief_attrs(b: Brief) -> dict:
    return {"campaign_objective": b.campaign_objective, "budget_value": b.budget_value}


# ----------------------------------------------------------------------------- #
# Sign-in
# ----------------------------------------------------------------------------- #
@app.post("/login", response_model=schemas.LoginOut)
def login(payload: schemas.LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.get(User, payload.username)
    if not user or not auth_mod.verify_password(payload.password, user.password_hash):
        # Same message for "no such user" and "wrong password" -- distinguishing them tells a caller
        # which usernames exist.
        raise HTTPException(401, "Incorrect username or password.")
    now = auth_mod.utcnow()
    token = auth_mod.new_session_token()
    db.add(SessionRow(token=token, user_id=user.id, created=now,
                       expires=auth_mod.session_expiry(now)))
    db.commit()
    response.set_cookie(auth_mod.COOKIE_NAME, token, httponly=True, samesite="lax",
                         secure=auth_mod.COOKIE_SECURE, max_age=int(auth_mod.SESSION_LIFETIME.total_seconds()))
    # `{"user": ...}` -- not `/me`'s bare shape. The documented contract said `{user:{...}}` and
    # Design built `doLogin` to read `r.data.user`; this was shipped unwrapped by mistake and it took
    # a live browser test against Design's actual code to catch it, not my own curl-only pass earlier.
    return {"user": user}


@app.post("/logout")
def logout(response: Response, studio_session: str | None = Cookie(default=None),
           db: Session = Depends(get_db)):
    if studio_session:
        row = db.get(SessionRow, studio_session)
        if row:
            db.delete(row); db.commit()
    response.delete_cookie(auth_mod.COOKIE_NAME)
    return {"detail": "Signed out."}


# ----------------------------------------------------------------------------- #
# Users & catalog
# ----------------------------------------------------------------------------- #
@app.get("/me", response_model=schemas.UserOut)
def me(user: User = Depends(current_user)):
    return user


@app.get("/users", response_model=list[schemas.UserOut])
def users(db: Session = Depends(get_db)):
    return list(db.scalars(select(User)))


@app.get("/creative-models")
def creative_models(kind: str | None = None):
    return creative.list_models(kind)


@app.get("/avatar-options")
def avatar_options():
    """Presenters, voices and aspect ratios for HeyGen avatar video. When HEYGEN_API_KEY is
    set these come from the account; otherwise a curated default set is returned."""
    return {"avatars": heygen.list_avatars(), "voices": heygen.list_voices(),
            "ratios": heygen.RATIOS, "live": heygen.has_key()}


@app.get("/platforms")
def platforms():
    return catalog.PLATFORMS


@app.get("/catalog")
def get_catalog():
    return {
        "brief_types": catalog.BRIEF_TYPES,
        "content_types": catalog.CONTENT_TYPES,
        "campaign_objectives": catalog.CAMPAIGN_OBJECTIVES,
        "platforms": catalog.PLATFORMS,
    }


# --- powers the front end's window.claude.complete() ---------------------------
@app.post("/complete")
def complete_endpoint(payload: dict):
    """The bridge every AI feature in the browser goes through.

    **Returns 503 rather than an empty 200 when there is no key.** It used to answer
    `{"completion": "", "live": false}` with a 200, and the client never reads `live` — so every generator
    rendered a blank and the user was left guessing whether the model had refused, returned nothing, or
    silently done nothing. A non-200 makes `window.claude.complete` throw, which is what each caller's
    own fallback path is already written to catch: the Social Studio, the script writer and the concept
    routes all produce their documented placeholder instead of nothing at all.
    """
    if not completion.has_key():
        return JSONResponse(status_code=503,
                            content={"detail": "No ANTHROPIC_API_KEY on the server — AI drafting is "
                                               "unavailable. Everything can still be written by hand.",
                                     "completion": "", "live": False})
    # `execution` binds the spine to ONE briefed piece of work. Without it the spine sends every audience
    # in the plan with equal weight, and the model picks whichever fits its instinct — which is how a
    # social post briefed for rival-pack buyers came back written for loose-milk buyers. Optional, so a
    # caller that does not have one is unaffected.
    out = completion.complete(payload.get("messages", []),
                              execution=str(payload.get("execution") or ""),
                              force_typed=bool(payload.get("force_typed")),
                              skip_mandatories=bool(payload.get("skip_mandatories")))
    if not str(out or "").strip():
        # A live key that returns nothing is a failure too, and an empty string dressed as success is the
        # version of it nobody can debug.
        return JSONResponse(status_code=502,
                            content={"detail": "The model returned nothing. Try again, or write it by "
                                               "hand.", "completion": "", "live": True})
    return {"completion": out, "live": True}


# --- video production: render the film from the approved script + shoot board ----
# Script rows mix spoken lines with speaker labels and production cues — e.g.
# "Girl: Bye Amma!  VO: The strength in your family." Everything here is about getting ONLY the
# words a voice artist would actually say into the text-to-speech call.
_CUE_LABELS = {"sfx", "music", "super", "supr", "title", "text", "card", "logo", "on screen",
               "on-screen", "graphic", "vfx", "sound", "ambience", "ambient", "note", "camera"}
# A speaker/cue label: up to three capitalised words (or ALL CAPS) before a colon.
_LABEL_RE = re.compile(r"(?:(?<=^)|(?<=[\s.!?…—–-]))"
                       r"([A-Z][\w.'’]*(?:\s+[A-Z][\w.'’]*){0,2})\s*:\s*")
_EMPTY = {"", "-", "–", "—", "n/a", "na", "none", "silence", "no dialogue", "nil"}


def _spoken_only(line: str) -> str:
    """Strip speaker labels and drop non-spoken cues, keeping just the words to be read aloud."""
    line = line.strip()
    if line.lower() in _EMPTY:
        return ""
    # Dash-separated narration labels ("Voiceover – …", "VO - …") as well as colons.
    line = re.sub(r"^\s*(?:v\.?\s?o\.?|voice\s*over|voiceover|narrator)\s*[-–—]\s*", "",
                  line, flags=re.IGNORECASE)
    # Split into (label, text) runs so a cue's text can be dropped along with its label.
    parts, pos, current = [], 0, None
    for m in _LABEL_RE.finditer(line):
        if m.start() > pos:
            parts.append((current, line[pos:m.start()]))
        current = m.group(1).strip().lower().rstrip(".")
        pos = m.end()
    parts.append((current, line[pos:]))
    kept = [text for label, text in parts
            if text.strip() and (label is None or label not in _CUE_LABELS)]
    out = re.sub(r"\s{2,}", " ", " ".join(kept)).strip(" ;,")
    return "" if out.lower() in _EMPTY else out


def _engine(payload: dict, kind: str) -> str:
    """Which engine to use for `kind` ("image" | "video" | "music"): auto | google | fal.

    An explicit choice is honoured exactly — no silent fallback — because a fallback that spends a
    different provider's credit than the price quoted is worse than a clear failure.
    """
    prefs = payload.get("engines") or {}
    want = str(prefs.get(kind) or payload.get("engine") or "auto").strip().lower()
    return want if want in ("auto", "google", "fal") else "auto"


def _use(engine: str, provider: str) -> bool:
    """Should `provider` be attempted under this engine preference?"""
    return engine == "auto" or engine == provider


# Image quality tiers. `gemini.image()` has always accepted `model=` and `size=`; no route passed either,
# so `IMAGE_MODEL_PRO` was defined and unreachable and every render in the product was flash at 1K. A
# key visual is the one artefact that goes to a printer, so the ceiling being invisible was a real cost.
#
# Named tiers rather than raw model ids, because the id is a deployment detail and the choice a person
# is making is "draft or final".
_IMG_TIERS = {
    "draft": (gemini.IMAGE_MODEL_LITE, "1K", "lite, 1K — cheapest, for looking at"),
    "standard": (None, "1K", "flash, 1K — the balanced default"),
    "pro": (gemini.IMAGE_MODEL_PRO, "2K", "pro, 2K — for the master and anything going to print"),
    "pro-4k": (gemini.IMAGE_MODEL_PRO, "4K", "pro, 4K — large-format print"),
}


def _img_tier(payload: dict, default: str = "standard") -> tuple[str | None, str, str]:
    """`(model, size, label)` for this request. Unknown names fall back rather than 400."""
    want = str(payload.get("tier") or payload.get("quality") or default).strip().lower()
    model, size, label = _IMG_TIERS.get(want, _IMG_TIERS[default])
    # `size` alone is a legitimate ask — "the same model, bigger" — so honour it over the tier's own.
    asked = str(payload.get("size") or "").strip().upper()
    if asked in gemini.IMAGE_SIZES:
        size = asked
    return model, size, label


# Images go to Google (Imagen/Gemini) first and fal only as the fallback — fal's budget is for video.
# The guard below used to test FAL_KEY alone, which meant a deployment with a Google key and no fal key
# refused every image with "set FAL_KEY" while holding a perfectly good image provider. That is how
# "POS material cannot generate an image" looked like a POS bug when it was a guard.
_NO_IMAGE = ("No image provider configured. Set GEMINI_API_KEY (or GOOGLE_API_KEY) for Imagen, "
             "or FAL_KEY as a fallback.")


def _have_image() -> bool:
    return gemini.available() or bool(os.environ.get("FAL_KEY"))


@app.get("/engines")
def engines():
    """Which engine each capability can use, and which are actually configured."""
    have_google, have_fal = gemini.available(), bool(os.environ.get("FAL_KEY"))
    def opts(kinds):
        return [{"id": "auto", "label": "Auto (Google, then fal)", "ready": have_google or have_fal},
                {"id": "google", "label": kinds[0], "ready": have_google},
                {"id": "fal", "label": kinds[1], "ready": have_fal}]
    return {"image": opts(["Google · Imagen / Nano Banana", "fal.ai"]),
            "video": opts(["Google · Veo 3.1", "fal.ai · Veo 3.1"]),
            "music": opts(["Google · Lyria 3", "fal.ai · ElevenLabs Music"]),
            "voice": [{"id": "fal", "label": "fal.ai · ElevenLabs", "ready": have_fal}],
            "google_ready": have_google, "fal_ready": have_fal}


def _music_bed(mood, seconds, engine: str = "auto") -> tuple[str, str]:
    """(url, provider) for one instrumental bed. Google first; fal only if Google can't serve."""
    if _use(engine, "google"):
        url = gemini.music(filmaudio.music_prompt(mood), seconds)
        if url:
            return url, "google"
    if _use(engine, "fal"):
        url = filmaudio.synth_music(mood, seconds)
        if url:
            return url, "fal"
    return "", ""


def _next_scored_name(master: str) -> str:
    """`film-x.mp4` -> `...-scored.mp4`, then `-scored-2.mp4`, `-scored-3.mp4` …

    Every score is kept so two music takes can be compared instead of one silently replacing
    the other.
    """
    base = master[:-4] if master.lower().endswith(".mp4") else master
    for n in range(1, 100):
        name = f"{base}-scored.mp4" if n == 1 else f"{base}-scored-{n}.mp4"
        if not os.path.exists(os.path.join(filmcut.RENDERS_DIR, name)):
            return name
    return f"{base}-scored-{uuid.uuid4().hex[:6]}.mp4"


def _voice_setup(payload: dict):
    """Shared by the voice plan, the audio preview and the real render, so what you approve in the
    review panel is exactly what gets rendered."""
    scenes = payload.get("scenes") or []
    total = filmcut.parse_seconds(payload.get("duration"))
    typed = str(payload.get("voice") or "")
    accent = str(payload.get("accent") or filmvoice.INDIAN)
    _, lang = filmaudio.pick_voice(typed)
    # The studio's free-text "Voiceover" field ("Warm female (Telugu-accented English)") describes
    # a voice rather than naming one. Only treat it as a specific casting choice if it actually
    # names a voice we have; otherwise honour the accent choice and read gender/age off the text.
    narrator = ""
    if filmvoice.resolve(typed):
        narrator = filmvoice.resolve(typed).id
    else:
        gender, age = filmvoice._band(typed).split("_")
        narrator = filmvoice.pool(accent, gender, age)[0].id
    # Scene lengths come from the dialogue, not the other way round: retime rewrites each row's
    # timecode from its spoken words so nothing has to be cut to fit a fixed grid.
    total, time_notes = filmvoice.retime(scenes, target_total=total)
    segs, notes = filmvoice.build_segments(scenes, float(total))
    notes = list(time_notes) + list(notes)
    filmvoice.cast(segs, narrator, lang, str(payload.get("characters") or ""), accent=accent)
    narrator = filmvoice.apply_overrides(segs, payload.get("voices") or {}, narrator)
    return segs, narrator, total, notes


@app.get("/voices")
def voices():
    """Voices the studio can cast, for the picker."""
    return filmvoice.voice_catalog()


@app.get("/music-styles")
def music_styles():
    """Named music styles for the picker."""
    return [{"id": m["id"], "label": m["label"]} for m in filmaudio.MUSIC_STYLES]


@app.post("/music-options")
def music_options(payload: dict):
    """Generate a few short candidate beds to audition.

    Short samples on purpose: judging a bed needs ~15 seconds, not the whole film, and the
    full-length version is only generated once you've chosen one.
    """
    if not os.environ.get("FAL_KEY"):
        return JSONResponse(status_code=501, content={"detail": "No provider key configured (set FAL_KEY)."})
    style = str(payload.get("style") or "warm-strings")
    label = next((m["label"] for m in filmaudio.MUSIC_STYLES if m["id"] == style), style)
    count = max(1, min(4, int(payload.get("count") or 3)))
    seconds = max(8, min(30, int(payload.get("seconds") or 15)))
    with ThreadPoolExecutor(max_workers=count) as pool:
        made = list(pool.map(lambda _: _music_bed(style, seconds,
                                                 _engine(payload, "music")), range(count)))
    options = [{"n": i + 1, "style": style, "label": f"{label} · take {i + 1}",
                "audio_url": u, "provider": prov}
               for i, (u, prov) in enumerate(made) if u]
    if not options:
        return JSONResponse(status_code=500, content={
            "detail": "Music generation failed — see render-log.txt."})
    return {"style": style, "label": label, "seconds": seconds, "options": options}


@app.post("/rescore")
def rescore(payload: dict):
    """Re-mix an existing cut with different music, WITHOUT re-rendering any video.

    Picture and soundtrack are separate layers, so swapping the bed only costs the audio. Each
    re-score writes a new file so takes can be compared rather than overwritten.
    """
    exe = filmcut.ffmpeg_exe()
    master = os.path.basename(str(payload.get("master") or ""))
    master_path = os.path.join(filmcut.RENDERS_DIR, master) if master else ""
    if not exe or not master or not os.path.exists(master_path):
        return JSONResponse(status_code=400, content={
            "detail": "The silent master for this cut is no longer on disk — render the film again."})
    segs, narrator, total, notes = _voice_setup(payload)
    if segs:
        made, voice_notes = filmvoice.synth(segs)
        notes = list(notes) + voice_notes
    _secs = filmcut.parse_seconds(payload.get("duration"))
    music_url, music_provider = (str(payload["music_url"]), "locked") \
        if str(payload.get("music_url") or "") \
        else _music_bed(payload.get("music", ""), _secs, _engine(payload, "music"))
    out_name = _next_scored_name(master)
    ok, mix_notes = filmaudio.mix_timeline(exe, master_path,
                                           os.path.join(filmcut.RENDERS_DIR, out_name), segs,
                                           music=music_url, level=payload.get("music_level"))
    if not ok:
        return JSONResponse(status_code=500, content={
            "detail": "; ".join(dict.fromkeys(notes + mix_notes)) or "Re-score failed."})
    out = {"video_url": f"/renders/{out_name}", "url": f"/renders/{out_name}",
           "master": master, "seconds": total,
           "audio": "voices+music" if segs else "music",
           "providers": {"music": music_provider, "voice": "fal" if segs else "", "video": "reused"},
           "cast": [{"speaker": "Narration", "voice": filmvoice.voice_label(narrator)}]}
    if notes + mix_notes:
        out["detail"] = "; ".join(dict.fromkeys(notes + mix_notes))
    _record_made("video_rescore", f"Re-scored — {master}", url=out["video_url"], payload=payload,
                 route="/rescore")
    return out


# --- the editable cut: an approved film as a manifest, not a rendered file ----------------------
#
# `/rescore` above already proves the shape: a silent master, re-mixed rather than replaced, a new
# file per take. `cut.py` generalises that to every kind of edit and writes down that a version exists
# at all — today a "master" is a filename a payload happens to carry, and it is lost the moment that
# file leaves disk. These routes are bookkeeping only; they never call ffmpeg or a video model
# themselves. `/cut-propose` answers what an edit would cost; the caller does whatever rendering that
# answer calls for with the existing `filmcut` / `filmaudio` functions, then `/cut-commit` records it.

@app.post("/cut")
def cut_start(payload: dict):
    """Start a cut's version history. `{execution, beats:[{n,role,shot_id,clip_url,seconds,super}],
    tracks?, grade?, master_url?}`.

    Refuses if this execution already has a cut — editing one is `/cut-propose` + `/cut-commit`, not a
    second start quietly abandoning its history.
    """
    execution = str(payload.get("execution") or "")
    beats = payload.get("beats") if isinstance(payload.get("beats"), list) else []
    row, err = cut.start(execution, beats, tracks=payload.get("tracks"),
                         grade=str(payload.get("grade") or ""),
                         master_url=str(payload.get("master_url") or ""))
    if not row:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"cut": row, "summary": cut.summary(row)}


@app.get("/cut/{execution}")
def cut_get(execution: str):
    """The cut for one execution — its whole version history. 404 if it has never been started."""
    row = cut.for_execution(execution)
    if not row:
        return JSONResponse(status_code=404, content={
            "detail": "No cut started for this execution yet."})
    return {"cut": row, "summary": cut.summary(row)}


@app.post("/cut-propose")
def cut_propose(payload: dict):
    """What an edit WOULD cost. `{execution, beats, tracks?, grade?, trigger?}`. Nothing is written —
    this is the whole point of the manifest: the cost is visible before anyone renders anything.

    `trigger` names an edit the beat/track diff cannot see for itself — `"cast"`, `"location"` or
    `"plate"` — because changing who or where touches every clip's content without necessarily
    changing the manifest's shape.
    """
    row = cut.for_execution(str(payload.get("execution") or ""))
    if not row:
        return JSONResponse(status_code=404, content={
            "detail": "No cut started for this execution yet."})
    beats = payload.get("beats") if isinstance(payload.get("beats"), list) else cut.latest(row)["beats"]
    info = cut.propose_edit(row, beats, new_tracks=payload.get("tracks"),
                            grade=payload.get("grade"), trigger=str(payload.get("trigger") or ""))
    return {"edit": info, "cut": {"id": row["id"], "execution": row["execution"],
                                  "latest_version": cut.latest(row)["version"]}}


@app.post("/cut-commit")
def cut_commit(payload: dict):
    """Create the next version. `{execution, beats, tracks?, grade?, master_url?, scored_url?,
    trigger?}`.

    `master_url` / `scored_url` are supplied already rendered — by `filmcut.stitch()` or
    `filmaudio.mix_timeline()`, chosen according to what `/cut-propose` said this edit costs. Left
    blank, each carries forward from the parent version, which is correct whenever the edit did not
    touch that layer at all.
    """
    row = cut.for_execution(str(payload.get("execution") or ""))
    if not row:
        return JSONResponse(status_code=404, content={
            "detail": "No cut started for this execution yet."})
    beats = payload.get("beats") if isinstance(payload.get("beats"), list) else None
    if beats is None:
        return JSONResponse(status_code=400, content={"detail": "No beats given to commit."})
    new_row, info, err = cut.commit(row, beats, new_tracks=payload.get("tracks"),
                                    grade=payload.get("grade"),
                                    master_url=str(payload.get("master_url") or ""),
                                    scored_url=str(payload.get("scored_url") or ""),
                                    trigger=str(payload.get("trigger") or ""))
    if not new_row:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"cut": new_row, "edit": info, "summary": cut.summary(new_row)}


@app.post("/cut-approve")
def cut_approve(payload: dict):
    """Sign off a version — by default the latest. `{execution, who, version?}`."""
    row = cut.for_execution(str(payload.get("execution") or ""))
    if not row:
        return JSONResponse(status_code=404, content={
            "detail": "No cut started for this execution yet."})
    new_row, err = cut.approve(row, str(payload.get("who") or ""),
                               version=payload.get("version"))
    if not new_row:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"cut": new_row, "summary": cut.summary(new_row)}


@app.get("/grade-status")
def grade_status():
    """The named grades — a screen renders its choices from this, not a hard-coded list."""
    return {"grades": {k: {"label": v["label"], "what": v["what"]} for k, v in composite.GRADES.items()}}


@app.get("/beat-plan")
def beat_plan(seconds: int = 30):
    """What each beat of a `seconds`-long film is FOR, and how long it runs.

    Pure arithmetic — `filmcut._beat_lengths()` already solved how long a beat may be (Veo takes 4, 6
    or 8 and nothing else); this says what each one does. The difference between eight clips and a film
    is that every beat can be briefed against a job rather than "shot 3 of 4".

    Reports honestly where the length does not divide: 15s cannot be built from 4/6/8-second clips, so
    the plan says it runs 18s rather than quietly returning something that does not add up.
    """
    return filmcut.plan_beats(seconds)


@app.post("/cut-down")
def cut_down(payload: dict):
    """Plan a cutdown of a cut to `seconds`. `{execution, seconds}` or `{beats:[…], seconds}`.

    Plans, does not render — which is the point: a cutdown is a re-cut of clips already on disk, so
    `cut.classify()` calls it free, and what a person needs first is which beats survive. Beats drop in
    `filmcut.DROP_ORDER` (world, then mechanism) and never by feel; hook, turn and brand never drop,
    because a cutdown without the turn is a different film rather than a shorter one.
    """
    try:
        seconds = int(payload.get("seconds") or 15)
    except (TypeError, ValueError):
        seconds = 15
    beats = payload.get("beats") if isinstance(payload.get("beats"), list) else None
    if beats is None:
        row = cut.for_execution(str(payload.get("execution") or ""))
        if not row:
            return JSONResponse(status_code=404, content={
                "detail": "No cut started for this execution yet, and no beats given to plan from."})
        beats = (cut.latest(row) or {}).get("beats") or []
    return {**filmcut.cutdown_plan(beats, seconds),
            "drop_order": list(filmcut.DROP_ORDER),
            "never_dropped": list(filmcut.NEVER_DROPPED)}


@app.get("/continuity-status")
def continuity_status():
    """What the library holds for holding a film together across shots — cast, and place.

    Two channels, both reference images, both proven to work the same way: identity travels as a
    picture and so does location. Reported together because a film missing either will not cut, and
    which one is missing changes what a person should go and do about it.
    """
    return library.shot_references()


@app.get("/continuity-metrics")
def continuity_metrics():
    """What the continuity checker measures, and what it refuses to claim.

    Rendered as a panel rather than hard-coded, for the same reason the grades and the POSM formats
    are: the list of what a check does NOT cover is the part worth reading, and it changes.
    """
    return continuity.status()


@app.post("/continuity-check")
def continuity_check(payload: dict):
    """Does this film read as one film? Two halves, the certain one first.

    Post the shots — `[{n, role, clip_url|path, seconds, refs?, provider?, from_frame?}]`, which is
    the shape a cut's `beats` already has. Reference provenance is exact and free; the measured look
    drift is advisory and says so. Nothing here refuses a film.
    """
    shots = payload.get("shots") or payload.get("beats") or []
    if not isinstance(shots, list) or not shots:
        return JSONResponse(status_code=400, content={
            "detail": "Send `shots` (or a cut's `beats`) — a list of {n, role, clip_url, seconds}."})
    return continuity.check(shots, use_plate=payload.get("use_plate", True))


# The shots a generative model reliably gets wrong. Not a style opinion — each of these is a specific,
# repeatable failure mode, and every one of them is cheaper to refuse at the shot-list stage than to
# generate, review, and re-render. Phrase matched loosely: this is a prompt for a person's judgement,
# not a filter that blocks work.
_SHOT_RISKS = {
    "lip sync": (("says", "speaks", "speaking", "talks", "talking", "dialogue", "to camera",
                  "piece to camera", "mouths", "sings"),
                 "Spoken dialogue on camera. Lip sync is the single most reliable tell in generated "
                 "film — the mouth never quite matches. Shoot it as voiceover over other action, or "
                 "keep the speaker off-camera or turned away."),
    "fine hand work": (("hands", "fingers", "typing", "writing", "unwraps", "unwrapping", "threading",
                        "buttons", "chopping", "counting notes", "handshake"),
                       "Close fine hand work. Hands are the second tell — count and articulation both "
                       "go wrong. Frame wider, cut away at the moment of contact, or let the result "
                       "carry the shot rather than the doing."),
    "crowd of faces": (("crowd", "crowds", "many people", "queue", "line of people", "audience",
                        "gathering", "village", "market crowd", "hundreds"),
                       "A crowd of individual faces. Each face is generated separately and none of "
                       "them holds — the eye reads the whole shot as false. Use depth of field, "
                       "backs of heads, silhouettes, or one face against an implied many."),
    "on-screen text": (("sign", "signage", "label", "poster", "newspaper", "headline", "banner",
                        "writing on", "logo", "packaging text", "menu"),
                       "Lettering in frame. Generated type is never real writing — in Devanagari or "
                       "Telugu it is not writing at all. Keep text out of frame and add it in post, "
                       "where it is real editable type."),
    "complex camera move": (("crane", "dolly zoom", "orbit", "360", "whip pan", "drone sweep",
                             "tracking through", "long take"),
                            "A complex camera move. Generated motion drifts and warps geometry across "
                            "a move. Prefer a static frame with movement inside it, or a slow push."),
}


@app.post("/shot-viability")
def shot_viability(payload: dict):
    """Flag shots that ask a generative model for what it reliably gets wrong. `{shots:[str]|str}`.

    A gate in the `posm.py` sense: it refuses nothing and blocks nothing, it says what will go wrong
    and what to shoot instead. Cheaper to read at the shot-list stage than to discover after paying
    for the render and the review — which is the whole reason it exists at this end of the pipeline
    rather than as a note in a style guide.
    """
    raw = payload.get("shots")
    shots = raw if isinstance(raw, list) else ([raw] if raw else [])
    out = []
    for i, s in enumerate(shots):
        text = str(s or "").strip()
        if not text:
            continue
        low = text.lower()
        hits = [{"risk": name, "advice": advice}
                for name, (words, advice) in _SHOT_RISKS.items()
                if any(w in low for w in words)]
        out.append({"n": i + 1, "shot": text, "risks": hits, "ok": not hits})
    flagged = [r for r in out if r["risks"]]
    return {
        "shots": out, "count": len(out), "flagged": len(flagged),
        "risks": {k: v[1] for k, v in _SHOT_RISKS.items()},
        "summary": (f"{len(flagged)} of {len(out)} shot(s) ask for something a model reliably gets "
                    f"wrong." if flagged else
                    f"{len(out)} shot(s), none of them in the known failure modes."
                    if out else "No shots given."),
        "note": "Advice, not a refusal — a flagged shot may still be the right shot. It is cheaper to "
                "know now than after the render.",
    }


@app.get("/sound-status")
def sound_status():
    """What the sound layer offers, and what the library actually holds for it.

    The counts matter as much as the level names: this is the one department a generated film cannot
    produce for itself, so a screen should be able to say "no ambience on file" rather than offering a
    picker with nothing behind it.
    """
    amb = library.items("ambience", signed_only=True)
    sfx = library.items("sfx", signed_only=True)
    return {
        "music_levels": filmaudio.MUSIC_LEVELS,
        "ambience_levels": filmaudio.AMBIENCE_LEVELS,
        "ambience_default": filmaudio.AMBIENCE_DEFAULT,
        "sfx_gain": filmaudio.SFX_GAIN,
        "library": {
            "ambience": [{"id": r["id"], "name": r["name"], "url": r["url"]} for r in amb],
            "sfx": [{"id": r["id"], "name": r["name"], "url": r["url"]} for r in sfx],
        },
        "why": ("Ambience and foley are uploads, not generations — no model here knows what a dented "
                "steel can sounds like on concrete at 5am. Sign one off in the library and it becomes "
                "available to every film."
                if not (amb or sfx) else ""),
    }


@app.post("/cut-sound")
def cut_sound(payload: dict):
    """Lay an ambience bed and/or foley spots over a cut's master, and commit it as the next version.
    `{execution, ambience?, ambience_level?, music?, music_level?, spots?:[{url|id, at, gain?}]}`.

    Sound is the department a generated film is worst at and that carries the most of what "real"
    feels like — a video model returns silence or per-clip audio that restarts at every cut, so this
    is the layer that makes several separate renders sound like one place. Every asset is a library
    reference resolved to a real file, never a generated one.

    Runs over the cut's current master. `cut.classify()` already treats a tracks change as an audio
    pass, which is exactly what this is: the picture is untouched.
    """
    row = cut.for_execution(str(payload.get("execution") or ""))
    if not row:
        return JSONResponse(status_code=404, content={
            "detail": "No cut started for this execution yet."})
    cur = cut.latest(row)
    src = _resolve_media(cur.get("master_url", ""))
    if not src or not os.path.exists(src):
        return JSONResponse(status_code=400, content={
            "detail": "This cut's master is no longer on disk — render the film again."})

    # Two different resolutions of the same reference, kept apart deliberately.
    #
    # The MIXER needs a disk path: `filmaudio._download` falls through to `gemini.local_path`, which
    # knows `/media/…` and real paths and nothing about `/library-file/…`, so handing it a library URL
    # failed every fetch with "could not be fetched" — which is what the first run of this route did
    # for all three assets.
    #
    # The MANIFEST needs the servable, portable reference. Storing the disk path this machine happened
    # to resolve would put `C:\Users\…` inside a document whose whole purpose is to describe the film
    # reproducibly — the same class of mistake as storing a filename and calling it a version.
    def as_url(ref) -> str:
        """The portable reference to store: a library item's own URL, or the ref as given."""
        ref = str(ref or "").strip()
        if not ref:
            return ""
        item = library.get(ref)
        return item["url"] if item else ref

    def as_path(ref) -> str:
        """The local path to hand the mixer. An http(s) URL passes through for it to fetch itself."""
        ref = str(ref or "").strip()
        if not ref:
            return ""
        if ref.lower().startswith(("http://", "https://")):
            return ref
        return _resolve_media(ref) or ref

    amb_ref = str(payload.get("ambience") or "").strip()
    music_ref = str(payload.get("music") or "").strip()
    amb_url = as_url(amb_ref)
    music_url = as_url(music_ref) or (cur.get("tracks") or {}).get("music_url", "")
    spots, spot_paths = [], []
    for s in (payload.get("spots") or []):
        if not isinstance(s, dict):
            continue
        ref = s.get("url") or s.get("id")
        u, pth = as_url(ref), as_path(ref)
        if not u:
            continue
        gain = {"gain": s["gain"]} if s.get("gain") not in (None, "") else {}
        spots.append({"url": u, "at": s.get("at") or 0, **gain})
        spot_paths.append({"url": pth, "at": s.get("at") or 0, **gain})
    if not (amb_url or spots or music_ref):
        return JSONResponse(status_code=400, content={
            "detail": "Nothing to lay over the picture. Name an ambience bed, some foley spots, or a "
                      "music bed — all three are library uploads, not generations."})

    exe = filmcut.ffmpeg_exe()
    if not exe:
        return JSONResponse(status_code=501, content={"detail": "ffmpeg is not available here."})
    os.makedirs(composite.EDITS_DIR, exist_ok=True)
    out_name = composite.new_grade_name("sound")
    out_path = os.path.join(composite.EDITS_DIR, out_name)
    # Voice segments are deliberately not re-synthesised here: this route lays sound over an existing
    # master, and that master already carries whatever narration it was scored with. Re-reading the
    # lines would be a different, more expensive operation than the one being asked for.
    ok, notes = filmaudio.mix_timeline(
        exe, src, out_path, [], music=as_path(music_ref or music_url) or None,
        level=payload.get("music_level"), ambience=as_path(amb_ref) or None,
        ambience_level_name=payload.get("ambience_level"), spots=spot_paths)
    if not ok:
        return JSONResponse(status_code=500, content={
            "detail": "; ".join(notes) or "The sound mix failed."})

    tracks = {**(cur.get("tracks") or {}), "ambience_url": amb_url,
              "music_url": music_url, "spots": spots}
    new_row, info, cerr = cut.commit(row, cur["beats"], new_tracks=tracks,
                                     scored_url=f"/edits/{out_name}")
    if not new_row:
        return JSONResponse(status_code=400, content={"detail": cerr})
    _record_made("cut_sound", "Sound pass over the cut", url=f"/edits/{out_name}", payload=payload,
                 ref_kind="cut", ref_id=str(new_row.get("id") or ""), route="/cut-sound")
    return {"cut": new_row, "edit": info, "summary": cut.summary(new_row),
            "scored_url": f"/edits/{out_name}",
            "detail": "; ".join(notes) if notes else ""}


@app.post("/cut-grade")
def cut_grade(payload: dict):
    """Apply one named grade to a cut's current master and commit it as the next version.
    `{execution, grade}`.

    One ffmpeg pass over the whole assembled master — "one look applied across every clip" means
    exactly that, a single correction over the finished film, not a per-clip adjustment repeated
    however many times a clip happens to have been regenerated. `cut.classify()` already recognises a
    grade-only change as free to re-render: no clip is touched, only the picture layer of the master
    the cut already points at.
    """
    row = cut.for_execution(str(payload.get("execution") or ""))
    if not row:
        return JSONResponse(status_code=404, content={
            "detail": "No cut started for this execution yet."})
    name = str(payload.get("grade") or "").strip()
    if name not in composite.GRADES:
        return JSONResponse(status_code=400, content={
            "detail": f"'{name}' is not a grade this module knows. Choices: "
                      f"{', '.join(composite.GRADES)}."})
    cur = cut.latest(row)
    src = _resolve_media(cur.get("master_url", ""))
    if not src or not os.path.exists(src):
        return JSONResponse(status_code=400, content={
            "detail": "This cut's master is no longer on disk — render the film again."})
    os.makedirs(composite.EDITS_DIR, exist_ok=True)
    out_name = composite.new_grade_name(name)
    out_path = os.path.join(composite.EDITS_DIR, out_name)
    ok, err = composite.grade(src, out_path, name)
    if not ok:
        return JSONResponse(status_code=500, content={"detail": f"Grading failed: {err}"})
    new_row, info, cerr = cut.commit(row, cur["beats"], grade=name,
                                     master_url=f"/edits/{out_name}")
    if not new_row:
        return JSONResponse(status_code=400, content={"detail": cerr})
    return {"cut": new_row, "edit": info, "summary": cut.summary(new_row),
            "master_url": f"/edits/{out_name}"}


@app.post("/voice-check")
def voice_check(payload: dict):
    """Is this voice usable on this account? Pasted ElevenLabs IDs often are not — a voice in the
    public library has to be added to the account before the API can use it. One tiny call is far
    cheaper than discovering it mid-render."""
    name = str(payload.get("voice") or "").strip()
    v = filmvoice.resolve(name)
    if not v:
        return {"ok": False, "detail": "That doesn't look like a voice id or an ElevenLabs voice ID."}
    if v.provider != "elevenlabs" or v.ref in {x.ref for x in filmvoice.VOICES}:
        return {"ok": True, "label": v.label, "detail": ""}   # a stock voice; nothing to check
    if not os.environ.get("FAL_KEY"):
        return {"ok": False, "detail": "No provider key configured (set FAL_KEY)."}
    url = filmaudio.run_fal(filmvoice.EL_MODEL, {"text": "Testing one two.", "voice": v.ref})
    if url:
        return {"ok": True, "label": v.label, "sample_url": url, "detail": ""}
    return {"ok": False, "label": v.label,
            "detail": f"ElevenLabs voice '{v.ref}' isn't available to this account. "
                      "Add it to your ElevenLabs voice library (My Voices), then paste the ID again."}


@app.post("/voice-plan")
def voice_plan(payload: dict):
    """Exactly what will be spoken, by whom, in which voice and when — no generation, no cost."""
    segs, narrator, total, notes = _voice_setup(payload)
    out = filmvoice.plan(segs, narrator)
    out["seconds"] = total
    out["budget"] = int(total * filmvoice.WORDS_PER_SEC)
    # The rows were retimed from their dialogue — hand the timecodes back so the script table and
    # storyboard show the timings the render will actually use.
    out["timecodes"] = [{"no": r.get("no"), "tc": r.get("tc")}
                        for r in (payload.get("scenes") or []) if isinstance(r, dict)]
    if notes:
        out["detail"] = "; ".join(dict.fromkeys(notes))
    return out


@app.post("/voice-preview")
def voice_preview(payload: dict):
    """Synthesise and mix the soundtrack ONLY — hear the cut's audio without rendering video."""
    exe = filmcut.ffmpeg_exe()
    if not exe:
        return JSONResponse(status_code=501, content={"detail": "ffmpeg unavailable — cannot mix a preview."})
    segs, narrator, total, notes = _voice_setup(payload)
    if not segs:
        return JSONResponse(status_code=400, content={
            "detail": "No spoken lines in this script yet — nothing to preview."})
    made, voice_notes = filmvoice.synth(segs)
    notes = list(notes) + voice_notes
    if not made:
        return JSONResponse(status_code=500, content={
            "detail": "; ".join(dict.fromkeys(voice_notes)) or
                      "Voice generation failed — see render-log.txt."})
    # Reuse the bed already chosen — regenerating on every preview was wasteful and meant you
    # never heard twice what you would actually get.
    music_url, music_provider = str(payload.get("music_url") or ""), "locked"
    if not music_url and payload.get("with_music", True):
        music_url, music_provider = _music_bed(payload.get("music", ""), total,
                                              _engine(payload, "music"))
    os.makedirs(filmcut.RENDERS_DIR, exist_ok=True)
    name = f"voice-preview-{uuid.uuid4().hex[:8]}.mp3"
    ok, mix_notes = filmaudio.preview_audio(exe, float(total),
                                            os.path.join(filmcut.RENDERS_DIR, name),
                                            segs, music=music_url,
                                            level=payload.get("music_level"))
    if not ok:
        return JSONResponse(status_code=500, content={
            "detail": "; ".join(dict.fromkeys(notes + mix_notes)) or "Preview mix failed."})
    out = filmvoice.plan(segs, narrator)
    out.update({"audio_url": f"/renders/{name}", "seconds": total,
                "music": bool(music_url), "music_url": music_url or "",
                "providers": {"voice": "fal" if made else "", "music": music_provider}})
    if notes + mix_notes:
        out["detail"] = "; ".join(dict.fromkeys(notes + mix_notes))
    return out


@app.post("/produce-video")
def produce_video(payload: dict):
    # New frontend sends {scenes, aspect, duration, music, voice, note} and reads {video_url};
    # the legacy caller sent {script, board, ...} and read {url}. Support both.
    aspect = payload.get("aspect") or "16:9"
    if not os.environ.get("FAL_KEY"):
        # no provider -> 501 so the new UI runs its own simulated render
        return JSONResponse(status_code=501, content={"detail": "No video provider configured (set FAL_KEY)."})
    script = payload.get("script") or {}
    board = payload.get("board") or {}
    # Fast tier by default: a full film is several clips, so the standard tier gets expensive quickly.
    model_id = payload.get("model") or "veo-3.1-fast"
    revise = str(payload.get("revise") or payload.get("note") or "").strip()
    scenes = payload.get("scenes") or script.get("scenes") or []
    # COST GUARD (round-83 audit): every other generation route in this file caps its own fan-out
    # (/posm-image at 4 candidates, /posm-scamps at 5 layouts) — this one didn't, and each scene below
    # becomes one paid Veo call (~$0.05-0.40/second). A malformed or oversized payload had no ceiling.
    # Refused rather than silently truncated, matching this app's "offer, never silently apply" rule.
    _MAX_SCENES = 24
    if len(scenes) > _MAX_SCENES:
        return JSONResponse(status_code=400, content={
            "detail": f"{len(scenes)} scenes is more than one film needs — capped at {_MAX_SCENES} to "
                      "avoid an unbounded paid render. Split this into more than one film."})

    def scene_text(items) -> str:
        return " ".join(
            (f"{s.get('t','') or s.get('tc','')} {s.get('title','') or s.get('visual','')}: "
             f"{s.get('desc','') or s.get('dialogue','')}").strip()
            for s in items if isinstance(s, dict))

    def voiceover_text() -> str:
        """The VO to perform over the whole film.

        The studio posts the approved script as `scenes` and does NOT send a `script.vo`, so fall
        back to stitching the rows' spoken lines into one continuous read. Stage directions like
        "VO:" / "Voiceover –" are stripped so they aren't read aloud.
        """
        vo = str(script.get("vo") or "").strip()
        if vo:
            return vo
        lines = []
        for s in scenes:
            if not isinstance(s, dict):
                continue
            line = _spoken_only(str(s.get("dialogue") or s.get("vo") or ""))
            if line:
                lines.append(line)
        return " ".join(lines)

    music = payload.get("music", "") or board.get("music", "") or script.get("music", "")
    chosen = filmcut.parse_seconds(payload.get("duration"))
    # The film stays the length that was chosen — that's a media constraint, not a preference. What
    # the dialogue decides is how those seconds are split between scenes: talky scenes hold, quiet
    # ones cut away sooner, and the beats still add up to `chosen`.
    total, retime_notes = filmvoice.retime(scenes, target_total=chosen)
    per_scene = filmvoice.scene_seconds(scenes, target_total=chosen)
    segments = filmcut.plan_by_scene(scenes, per_scene)

    style = str(payload.get("style") or "real").lower()
    look = _VID_STYLES.get(style, _VID_STYLES["real"])

    def frame_for(seg) -> str:
        """The approved storyboard frame for this beat, if one was rendered."""
        for sc in seg["scenes"]:
            for key in ("frame_url", "image_url", "still_url"):
                if isinstance(sc, dict) and sc.get(key):
                    return str(sc[key])
        return ""

    # What each beat's ROLE asks of the shot, phrased as direction rather than as a label.
    #
    # `brand` is the one that needs care: the endframe's job is the pack and the mnemonic, but every
    # prompt here correctly forbids lettering because type is set in post — in Devanagari and Telugu a
    # generated headline is not writing at all. So this asks for the pack presented cleanly WITH SPACE
    # for type, and never for the logo or the line. Asking a role to produce what the rest of the
    # prompt forbids is how the plate nearly ended up fighting the "change the setting" instruction.
    _ROLE_DIRECTION = {
        "hook": "This is the HOOK — the opening shot. One arresting image that reads in under two "
                "seconds and earns the rest of the film. Simple, high contrast, no set-up.",
        "world": "This beat ESTABLISHES the place and the person: where we are and whose story this "
                 "is. Wider, unhurried, legible.",
        "mechanism": "This beat SHOWS the mechanism — the process, the proof, the routine actually "
                     "happening. The thing being demonstrated has to be visible, not implied.",
        "turn": "This is the TURN — the moment something changes. The shot the whole film exists to "
                "deliver, so it carries the recognition rather than more information.",
        "brand": "This is the ENDFRAME beat: the pack, presented clean and front-facing, with calm "
                 "uncluttered space around it for the line and the logo to be set in artwork "
                 "afterwards. Leave that space empty — put no lettering, logo or type in the frame.",
    }

    def segment_prompt(seg, from_frame: bool = False) -> str:
        beat = scene_text(seg["scenes"]) or scene_text(scenes)
        # The beat's job, from `filmcut.assign_roles`. Briefing a shot as "shot 3 of 4" tells the model
        # nothing about what the shot is for; the role grammar existed and nothing read it, which is
        # the same shape `plate` was in before it was wired up.
        role_note = _ROLE_DIRECTION.get(str(seg.get("role") or ""), "")
        if role_note:
            role_note = " " + role_note
        cont = ("This shot CONTINUES the same beat as the previous shot — carry the action forward "
                "with a fresh camera angle rather than repeating it. " if seg.get("continues") else "")
        if from_frame:
            # Animating an approved frame: the picture already fixes cast, wardrobe and set, so the
            # prompt only has to describe the MOVEMENT.
            p = (f"Animate this storyboard frame as shot {seg['index'] + 1} of {len(segments)} of a "
                 f"{_brand_line()} brand film. Keep the people, wardrobe, set and colour grade "
                 f"exactly as they appear in the image — do not redesign anything. {cont}"
                 f"Bring it to life for this beat: {beat}.{role_note} "
                 f"{look} Natural, restrained camera movement. Mood: {music}. "
                 "No on-screen text or logos. No dialogue or music in the clip — the soundtrack is "
                 "added in the edit.")
        else:
            p = (f"Cinematic {aspect} brand film for {_brand_line()}. This is shot {seg['index'] + 1} of {len(segments)} in one "
                 f"continuous film — keep the characters, wardrobe, location and grade IDENTICAL to "
                 f"the other shots so the parts cut together seamlessly. {cont}"
                 f"Film logline: {script.get('logline','')}. "
                 f"Depict ONLY this beat: {beat}.{role_note} "
                 f"{look} Mood: {music}. "
                 "Authentic Indian family setting, warm natural light, premium and wholesome; "
                 "no on-screen text or logos. No spoken dialogue and no music in the clip itself — "
                 "the soundtrack is added in the edit.")
        return p + f" Revision note: {revise}." if revise else p

    # Render the picture SILENT and in parallel: a 2-minute film is 15 shots, which would take far
    # too long one at a time. Audio is added once, over the whole cut, so it stays continuous.
    errors: list[str] = list(retime_notes)
    slots: list[str | None] = [None] * len(segments)
    used_providers: set[str] = set()

    # Draft -> Veo 3.1 Lite (image-to-video capable, ~half the price of Fast at the same speed);
    # Final -> Standard. An explicit `tier` wins if the UI sends one.
    tier = str(payload.get("tier") or
               ("standard" if str(payload.get("model") or "").strip() == "veo-3.1" else "lite"))
    video_engine = _engine(payload, "video")
    # Google publishes Lite and Standard on this API and nothing in between. Resolve a middle tier
    # DOWN to Lite rather than up: fal has a Fast model, Google does not, and quietly promoting to
    # Standard would bill 8x what was quoted.
    if tier not in gemini.VIDEO_MODELS:
        if _use(video_engine, "google"):
            errors.append(f"Google has no '{tier}' Veo tier on this API — rendering the Google shots "
                          f"on Veo 3.1 Lite. Pick Final for Standard, or switch the engine to fal, "
                          f"which does have a Fast model")
        tier = "lite"

    def render(seg):
        # A scene with a signed-off live-action shot is NOT generated. Real footage of real people
        # beats anything a model can invent about a specific face, so the shot is trimmed to the
        # beat and dropped straight into the timeline. One timeline, one approval, and the voice and
        # music path downstream never knows the difference.
        scene_no = int(((seg["scenes"] or [{}])[0] or {}).get("no") or (seg["index"] + 1))
        live = shots.for_scene(scene_no)
        if live:
            src = _resolve_media(live.get("url"))
            if src and os.path.exists(src):
                os.makedirs(composite.EDITS_DIR, exist_ok=True)
                cut = composite.new_edit_name(f"scene{scene_no}-live")
                out_path = os.path.join(composite.EDITS_DIR, cut)
                # fit_to_beat, not edit: a take shorter than its beat must still fill the beat, or
                # the film stops adding up to the slot it was sold into.
                ok, note = composite.fit_to_beat(src, out_path, float(seg["seconds"]))
                if ok:
                    return seg["index"], {"url": f"/edits/{cut}", "provider": "live-action",
                                          "model": f"shot {live['id']}", "kind": "video",
                                          "from_frame": False,
                                          "note": f"scene {scene_no}: {note}" if note else ""}
                print(f"[main] live-action shot for scene {scene_no} could not be cut to "
                      f"{seg['seconds']}s ({note[:120]}); generating instead",
                      file=sys.stderr, flush=True)
        # Animating the approved frame is what makes the film match the board AND keeps the cast
        # identical from shot to shot; text-to-video reinvents people every call.
        frame = frame_for(seg)
        if _use(video_engine, "google") and gemini.available():
            url = gemini.video(segment_prompt(seg, from_frame=bool(frame)), image_ref=frame,
                               seconds=seg["seconds"], ratio=aspect, tier=tier)
            if url:
                return seg["index"], {"url": url, "provider": "google", "model": tier,
                                      "kind": "video", "from_frame": bool(frame)}
            if not _use(video_engine, "fal"):
                return seg["index"], {"url": "", "provider": "google", "kind": "video"}
            print(f"[main] Google video failed for shot {seg['index'] + 1}; trying fal",
                  file=sys.stderr, flush=True)
        if not _use(video_engine, "fal"):
            return seg["index"], {"url": "", "provider": "google", "kind": "video"}
        if frame:
            url = creative.video_from_image(model_id, segment_prompt(seg, from_frame=True), frame,
                                           seconds=seg["seconds"], ratio=aspect)
            if url:
                return seg["index"], {"url": url, "provider": "fal", "model": model_id,
                                      "kind": "video", "from_frame": True}
            print(f"[main] image-to-video failed for shot {seg['index'] + 1}; using text-to-video",
                  file=sys.stderr, flush=True)
        return seg["index"], creative.generate_creative(
            model_id, segment_prompt(seg), ratio=aspect, duration=seg["seconds"], with_audio=False)

    # Veo's per-minute allowance is small, and four shots in flight blew straight through it: two of
    # six came back 429 and the film shipped 14 seconds short. Google gets two at a time and each
    # shot retries with backoff (see gemini.video); fal has no such limit.
    lanes = 2 if _use(video_engine, "google") else 4
    with ThreadPoolExecutor(max_workers=max(1, min(lanes, len(segments)))) as pool:
        for fut in as_completed([pool.submit(render, s) for s in segments]):
            try:
                idx, res = fut.result()
            except Exception as e:
                errors.append(str(e))
                continue
            if res.get("url"):
                slots[idx] = res["url"]
                used_providers.add(str(res.get("provider") or "fal"))
                if res.get("note"):          # e.g. a live-action take shorter than its beat
                    errors.append(res["note"])
            else:
                errors.append(f"shot {idx + 1}: no URL returned")
    clips = [u for u in slots if u]          # keep script order, drop failed shots
    beats = [segments[i]["seconds"] for i, u in enumerate(slots) if u]
    # Which SCENES survived. A dropped shot used to vanish quietly: the film was joined from what came
    # back, trimmed to that shorter length, and handed over looking finished — a 16s cut of a 30s
    # script with two scenes simply absent. The soundtrack was still laid out on the 30s plan, so the
    # closing narration was placed past the end of the picture and never heard.
    missing = sorted({int((segments[i]["scenes"] or [{}])[0].get("no") or (i + 1))
                      for i, u in enumerate(slots) if not u})
    incomplete = bool(missing)
    if incomplete:
        errors.insert(0, f"INCOMPLETE CUT — {len(slots) - len(clips)} of {len(slots)} shots did not "
                         f"render, so scene(s) {', '.join(str(n) for n in missing)} are missing and "
                         f"this film is {sum(beats)}s of the {chosen}s you asked for. The usual cause "
                         f"is Veo's per-minute quota; re-render to complete it")
    video_provider = "+".join(sorted(used_providers)) if used_providers else ""
    # Say who actually rendered it. Reporting the requested model meant the UI could show "Veo 3.1
    # Lite" while fal had quietly done the work at its own rate — the exact thing that made the
    # last invoice a surprise.
    if used_providers == {"live-action"}:
        real_model = "live-action (composited, not generated)"
    elif used_providers == {"google"}:
        real_model = f"Veo 3.1 {tier}"
    elif "google" in used_providers:
        real_model = f"Veo 3.1 {tier} + fal {model_id}"
    else:
        real_model = f"fal {model_id}"
    if "fal" in used_providers and _use(video_engine, "google"):
        errors.append(f"Google was unavailable, so {'some shots' if len(used_providers) > 1 else 'this film'} "
                      f"rendered on fal ({model_id}) and is billed at fal's rate, not the Veo 3.1 "
                      f"{tier} price quoted. Pin the video engine to Google to make that fail "
                      f"instead of falling back")

    # A shot that failed shortens the film, so the length the soundtrack and the response quote has
    # to be the length that was actually rendered — not the length that was ordered.
    if beats:
        total = sum(beats)

    if not clips:
        # Name the actual wall. "produced no clips" sent people to the log to find a quota message
        # they could have been shown directly, along with what to switch to.
        spent = gemini.quota_spent(tier) if _use(video_engine, "google") else ""
        return JSONResponse(status_code=500 if errors else 501, content={
            "detail": (f"No shots rendered — {spent}" if spent else
                       f"Video render via '{model_id}' produced no clips. "
                       + ("; ".join(errors) if errors else
                          "See render-log.txt for the provider response; the model may be gated "
                          "on your account."))})

    rendered = filmcut.stitch(clips, beats)
    if not rendered:
        # Couldn't join (no ffmpeg, or a download failed): hand back the first clip so the user
        # still sees something, and say so.
        url = clips[0]
        if len(clips) > 1:
            errors.append("clips could not be joined into one file — showing the first shot only")
        out = {"video_url": url, "url": url, "live": True, "model": real_model, "clips": clips,
               "shots": len(segments), "seconds": total, "audio": "none"}
        out["detail"] = "; ".join(errors)
        _record_made("produced_film", "Produced film (unstitched)", url=url, payload=payload,
                     route="/produce-video")
        return out

    # --- soundtrack: cast voice segments placed on a timeline, plus a music bed --------
    audio_kinds, exe = [], filmcut.ffmpeg_exe()
    # Same setup the review panel used, plus any voices the user picked there — but timed against the
    # picture that EXISTS. Retiming to the ordered length while the render came up short is what put
    # the closing narration at 24s of a 16s film, where it could never be heard. When shots are
    # missing, the scenes that survived are re-timed into the real length and the rest are dropped
    # rather than crammed in.
    voice_payload = payload
    if incomplete:
        kept = {int((segments[i]["scenes"] or [{}])[0].get("no") or (i + 1))
                for i, u in enumerate(slots) if u}
        voice_payload = {**payload, "duration": f"{total}s",
                         "scenes": [r for r in scenes
                                    if isinstance(r, dict) and int(r.get("no") or 0) in kept]}
    voice_segments, narrator, _, budget_notes = _voice_setup(voice_payload)
    errors.extend(budget_notes)
    casting = {s.speaker: s.voice for s in voice_segments if s.kind == "dialogue" and s.speaker}
    if voice_segments:
        spoken, voice_notes = filmvoice.synth(voice_segments)
        errors.extend(voice_notes)
        if spoken:
            audio_kinds.append("vo" if all(s.kind == "vo" for s in voice_segments) else "voices")
        else:
            errors.append("voice generation failed — see render-log.txt")
    else:
        errors.append("no spoken lines found in the script — film has music only")
    if str(payload.get("music_url") or ""):
        music_url, music_provider = str(payload["music_url"]), "locked"
    else:
        music_url, music_provider = _music_bed(music, total, _engine(payload, "music"))
    if music_url:
        audio_kinds.append("music")
    else:
        errors.append("music generation failed — see render-log.txt")

    silent_master = ""
    if exe and (any(s.url for s in voice_segments) or music_url):
        silent = os.path.join(filmcut.RENDERS_DIR, rendered)
        silent_master = silent
        scored_name = _next_scored_name(rendered)
        scored = os.path.join(filmcut.RENDERS_DIR, scored_name)
        ok, mix_notes = filmaudio.mix_timeline(exe, silent, scored, voice_segments,
                                               music=music_url,
                                               level=payload.get("music_level"))
        errors.extend(mix_notes)
        if ok:
            # Keep the SILENT master: picture and soundtrack are separate layers, so the music
            # can be changed later for the price of the audio alone — no new video render.
            rendered = scored_name
        else:
            errors.append("soundtrack could not be mixed — film is silent")
            audio_kinds = []

    url = f"/renders/{rendered}"
    out = {"video_url": url, "url": url, "live": True, "model": real_model, "clips": clips,
           "shots": len(segments), "seconds": total, "chosen_seconds": chosen,
           "timecodes": [{"no": r.get("no"), "tc": r.get("tc")}
                         for r in scenes if isinstance(r, dict)],
           "audio": "+".join(audio_kinds) if audio_kinds else "none",
           # who spoke, and in which voice — so the UI can show the casting
           "master": os.path.basename(silent_master) if silent_master else "",
           "music_url": music_url or "",
           # which engine produced each layer — the fallback used to be invisible
           "providers": {"video": video_provider or "", "music": music_provider,
                         "voice": "fal" if any(v.url for v in voice_segments) else ""},
           "cast": [{"speaker": "Narration", "voice": narrator}]
                   + [{"speaker": k, "voice": v} for k, v in casting.items()],
           "lines": len([s for s in voice_segments if s.url])}
    if errors:
        out["detail"] = "; ".join(dict.fromkeys(errors))     # de-duplicate, keep order
    _record_made("produced_film", "Produced film", url=url, payload=payload, route="/produce-video")
    return out


# --- image generation (storyboard frames AND social-post visuals) ----------------
# {prompt, ratio, style, characters, seed} -> {image_url}. Needs FAL_KEY (real images).
# Without it we return 501 so the UI keeps its clean branded placeholder.
#
#   style      : "real" (photo w/ people) | "product" | "infographic" | "vector"
#   characters : a shared character sheet to keep the SAME people across a film's frames
#   seed       : fixed integer per film/set -> visual consistency across images
_IMG_STYLES = {
    "real": ("High-resolution, photorealistic advertising photograph. Professional commercial food & "
             "lifestyle photography: full-frame DSLR, 50mm lens, shallow depth of field, crisp sharp "
             "focus, soft warm natural light, true-to-life colours, realistic textures and condensation "
             "on fresh milk. Authentic contemporary Indian home, kitchen, or dawn dairy-farm setting with "
             "real people and natural expressions. Ultra-detailed and realistic — NOT illustrated, NOT "
             "cartoon, NOT 3D/CGI; no plastic skin, no distorted hands, no extra fingers."),
    "product": ("High-end product photograph: the brand's hero pack as the "
                "hero on a clean minimal surface. Studio lighting, soft reflections, condensation, crisp "
                "focus, appetising and premium. NO people, NO hands. Photorealistic, not illustrated."),
    "infographic": ("Clean modern infographic / data-visualisation graphic. Flat design, generous "
                    "whitespace, simple line icons, clear visual hierarchy, in the brand palette named in the "
                    "prompt. Editorial and professional. No photographic imagery."),
    "vector": ("Flat vector illustration: bold clean shapes, smooth gradients, friendly modern style in the "
               "the brand's own palette as given in the prompt. Warm and premium. Not photoreal, not 3D."),
    "claymation": ("Stop-motion claymation still: characters and props sculpted from modelling clay with "
                   "visible fingerprints and tool marks, slightly uneven handmade surfaces, miniature "
                   "practical set, soft studio lighting with real shadows, shallow tabletop depth of field. "
                   "Charming and tactile, in the brand palette. Not CGI-smooth, not photoreal."),
    "animation-3d": ("Modern 3D animated film still, premium feature-animation quality: appealing stylised "
                     "characters with expressive faces, soft global illumination, subsurface skin, rich "
                     "materials, cinematic depth of field. Warm and family-friendly in the brand palette. "
                     "Stylised — not photoreal, not live action."),
    "animation-2d": ("Hand-drawn 2D animation still: clean confident line art, flat cel-shaded colour with "
                     "soft gradients, painted background, warm Indian storybook feel in the brand palette. "
                     "Traditional animation look — not 3D, not photoreal."),
    "watercolour": ("Hand-painted watercolour illustration: soft washes, visible paper grain, gentle bleeding "
                    "edges, delicate ink linework, warm Indian folk-art sensibility in the brand palette. "
                    "Artisanal and premium. Not photoreal, not vector."),
}

# The same look, phrased for a moving image.
_VID_STYLES = {
    "real": "Live-action photoreal cinematography, shot on a cinema camera with warm natural light.",
    "product": "Live-action tabletop product cinematography: macro pack and pouring shots, studio lighting, no people.",
    "infographic": "Animated flat infographic motion-graphics: clean shapes and simple line icons in the brand palette, no live action.",
    "vector": "Flat vector motion-graphics animation: bold clean shapes and smooth gradients in the brand palette.",
    "claymation": "Stop-motion claymation, shot frame by frame: clay characters with visible fingerprints on a miniature practical set, charming slightly imperfect movement.",
    "animation-3d": "Premium 3D animated film: stylised appealing characters, soft global illumination, cinematic camera moves. Stylised, not photoreal.",
    "animation-2d": "Hand-drawn 2D animation: cel-shaded characters over painted backgrounds, warm Indian storybook feel.",
    "watercolour": "Animated watercolour illustration: soft painted washes and paper texture, gentle hand-made motion.",
}


@app.get("/image-styles")
def image_styles():
    """The looks a frame or film can be rendered in, for the style picker."""
    labels = {"real": "Real life (photoreal)", "product": "Product only",
              "infographic": "Infographic", "vector": "Vector illustration",
              "claymation": "Claymation (stop-motion)", "animation-3d": "3D animation",
              "animation-2d": "2D animation", "watercolour": "Watercolour"}
    return [{"id": k, "label": labels.get(k, k), "video": k in _VID_STYLES}
            for k in _IMG_STYLES]


# Real failure, caught live while verifying the cast fix: asked for "a calm school child in uniform...
# standing beside a carton of milk", the model returned the child correctly AND a photorealistic carton
# carrying **Amul** branding — a named competitor in this very brand's own profile. `posm_skill` states
# the rule outright ("the model draws brand lettering onto it, which is the one thing that must never be
# generated"), and a competitor's mark on a brand's own POS artwork is the most expensive defect this
# tool could ship. The pack is ALWAYS composited from the signed-off library shot, so no generation
# route ever has a reason to draw packaging — this clause says so in the one place every such prompt
# passes through.
_NO_PACKAGING = ("Absolutely no product packaging of any kind in frame — no carton, bottle, pouch, "
                 "tub, tetra pak, can or labelled container, and no branded object of any kind. "
                 "The product is added separately afterwards.")


@app.post("/cast-reference")
def cast_reference(payload: dict):
    """One reference image of the film's cast — the anchor every frame is generated against.

    Character identity cannot be carried by words. However precise the description and however
    fixed the seed, text-to-image redraws a different person each call. So the cast is rendered
    ONCE as a picture, and every later frame is generated *from that picture*.

    **`cast_id`/`plate_id` — real photos in, not just words.** Until now this route was pure
    text-to-image regardless of what the library held: a signed-off cast/actor frame or location plate
    sat unread while every film's "identity anchor" was hallucinated fresh from a description, the exact
    failure this whole mechanism exists elsewhere to prevent (see `library.shot_references`'s docstring
    — the same gap `/posm-image` had for the pack until this session's earlier fix). When either id
    resolves to a real signed-off item, this becomes an image-to-image call: the real face/wardrobe or
    the real room and light is reproduced rather than redrawn from a paragraph, and only what the
    description adds beyond the photo (the OTHER people, an action) is actually generated. Absent
    either, this falls back to the original pure-text render — a person with nothing uploaded yet is
    not blocked, just not anchored to anything real.
    """
    if not _have_image():
        return JSONResponse(status_code=501, content={"detail": _NO_IMAGE})
    characters = str(payload.get("characters", "")).strip()
    if not characters:
        return JSONResponse(status_code=400, content={"detail": "Describe the cast first."})
    style = str(payload.get("style") or "real").lower()
    craft = _IMG_STYLES.get(style, _IMG_STYLES["real"])
    # The route's own hero type (`posm.HERO_TYPES`), e.g. "person-in-benefit" — carries WHO this is
    # meant to be (the consumer, a known endorser) into the actual words the model reads, which used to
    # stop at `characters`' free text alone. Same fix as `/posm-image`'s `cutout_prompt`.
    type_brief = posm.hero_type_brief(str(payload.get("hero_type") or ""))
    characters_brief = f"{type_brief}. {characters}" if type_brief else characters
    # Several candidates in one call rather than one draft repeatedly overwritten — see /posm-image's
    # matching comment for why comparison, not a single accepted draft, is the point.
    n = max(1, min(4, int(payload.get("n") or 1)))
    # Optional: the Scripting department's Location draft. Undescribed, this stays a plain neutral
    # backdrop -- described, the cast is anchored in the actual setting instead of a studio void, which
    # is what every later frame (also generated against this same picture) then inherits too.
    location = str(payload.get("location", "")).strip()
    backdrop = f"in this setting: {location}" if location else "against a plain neutral background"

    cast_url = ""
    cast_id = str(payload.get("cast_id") or "")
    if cast_id:
        row = library.get(cast_id)
        cast_url = row["url"] if row and row.get("kind") in ("cast", "actor") and row.get("signed_off") else ""
    plate_url = ""
    plate_id = str(payload.get("plate_id") or "")
    if plate_id:
        row = library.get(plate_id)
        plate_url = row["url"] if row and row.get("kind") == "plate" and row.get("signed_off") else ""

    refs, roles = [], []
    if cast_url:
        refs.append(cast_url)
        roles.append("real people to anchor identity from — reproduce these exact faces, hair, skin "
                     "tone and build for whichever of them the cast list below names again; anyone else "
                     "the list names is a new person, not shown here")
    if plate_url:
        refs.append(plate_url)
        roles.append("the real location and its light — reproduce this exact room or place, faithfully, "
                     "never redrawn or replaced with an invented setting")
    # The approved layout sketch, layout only — same refusal-of-style framing as /studio-shot's own
    # `sketch_url` handling, and the same reasoning: a scamp is a rough pencil drawing, and without an
    # explicit refusal a reference image's own visual register tends to leak into the generation.
    sketch_url = str(payload.get("sketch_url") or "").strip()
    if sketch_url:
        refs.append(sketch_url)
        roles.append("the approved layout sketch — a rough pencil drawing showing WHERE the cast "
                     "stands and how they're grouped, nothing more. Match that arrangement; ignore its "
                     "pencil linework, monochrome tone and paper texture entirely")

    eng = _engine(payload, "image")
    model, size, tier = _img_tier(payload)

    def _variation(i: int) -> str:
        return (f" Candidate {i + 1} of {n} — a distinct pose or expression for the SAME people; same "
                f"identity, age, build and wardrobe, not different people.") if n > 1 else ""

    if refs:
        role_note = "; ".join(f"reference image {i + 1} shows {r}" for i, r in enumerate(roles))
        candidates = []
        for i in range(n):
            prompt = (
                "Character reference sheet for a film cast, for continuity across shots. "
                f"Show these people together, full body, standing side by side, facing camera, evenly "
                f"lit, {backdrop if not plate_url else 'in the real location shown in the reference images'}"
                f": {characters_brief}. Each face clearly visible and unobscured; complete wardrobe "
                f"visible head to toe. {craft} {_NO_PACKAGING} No text, labels, captions, logos or "
                f"borders.{_variation(i)}")
            u, prov = "", ""
            if _use(eng, "google"):
                prov = "google"
                u = gemini.image_from_reference(f"{role_note}. " + prompt, refs, ratio="16:9",
                                                model=model, size=size)
            if not u and _use(eng, "fal"):
                prov = "fal"
                u = creative.image_from_reference(f"{role_note}. " + prompt, refs, ratio="16:9")
            if u:
                candidates.append({"image_url": u, "provider": prov})
        if candidates:
            _record_made("cast_reference", "Cast reference candidate", payload=payload,
                         urls=[c["image_url"] for c in candidates], route="/cast-reference")
            return {"image_url": candidates[0]["image_url"], "images": candidates, "style": style,
                    "provider": candidates[0]["provider"], "tier": tier, "from_reference": True,
                    "cast_used": bool(cast_url), "plate_used": bool(plate_url)}
        print("[main] cast-reference failed on both providers with real references; falling back to "
              "text-to-image", file=sys.stderr, flush=True)

    candidates = []
    for i in range(n):
        prompt = (
            "Character reference sheet for a film cast, for continuity across shots. "
            f"Show these people together, full body, standing side by side, facing camera, evenly lit, "
            f"{backdrop}: {characters_brief}. "
            "Each face clearly visible and unobscured; complete wardrobe visible head to toe. "
            f"{craft} {_NO_PACKAGING} No text, labels, captions, logos or borders.{_variation(i)}")
        u, prov = "", ""
        if _use(eng, "google"):
            u, prov = gemini.image(prompt, ratio="16:9", model=model, size=size), "google"
        if not u and _use(eng, "fal"):
            prov = "fal"
            u = creative.text_to_image(prompt, ratio="16:9")["url"]
        if u:
            candidates.append({"image_url": u, "provider": prov})
    if not candidates:
        return JSONResponse(status_code=500, content={
            "detail": "Couldn't render the cast reference. Both image providers refused — check "
                      "credits for your Google and fal keys (see render-log.txt)."})
    _record_made("cast_reference", "Cast reference candidate", payload=payload,
                 urls=[c["image_url"] for c in candidates], route="/cast-reference")
    return {"image_url": candidates[0]["image_url"], "images": candidates, "style": style,
            "provider": candidates[0]["provider"], "tier": tier, "from_reference": False}


@app.post("/scene-still")
def scene_still(payload: dict):
    if not _have_image():
        return JSONResponse(status_code=501, content={"detail": _NO_IMAGE})
    ratio = payload.get("ratio") or "1:1"
    style = str(payload.get("style") or "real").lower()
    craft = _IMG_STYLES.get(style, _IMG_STYLES["real"])
    subject = str(payload.get("prompt", "")).strip() or "brand key visual"
    characters = str(payload.get("characters", "")).strip()
    # A cast reference image pins identity in a way text never can — use it when we have one.
    refs = [u for u in (payload.get("reference_urls") or
                        ([payload["reference_url"]] if payload.get("reference_url") else [])) if u]
    # Signed-off library references are added automatically — cast AND plate — because continuity is
    # the library's job and the client has no reason to know what it holds. Anything the caller sent
    # explicitly comes FIRST and is never displaced: a named reference for a named character is more
    # specific than the library's default, and the APIs cap the count at three.
    #
    # Both channels, not just the plate: the first version of this added the plate alone, so a person
    # with a signed cast frame and no explicit refs got a frame where the location held and the face
    # did not — half the feature, and it left `shot_references()`'s ordering unused, which was the
    # smell that surfaced it. `use_plate:false` opts the plate out for the deliberate case, a shot
    # meant to be somewhere else.
    #
    # `want_pack` — opt-in, matching `shot_references`'s own reasoning: most shots (a classroom, a
    # bedroom) show no product, so it should not eat a reference slot or nudge a pack into a frame that
    # never called for one. `include_pack` lets a caller force it either way; absent that, a shot whose
    # own description names the product decides for itself — this is exactly the case that was missing
    # before: asking twice for "the pack shot from ground truth" changed nothing, because nothing ever
    # read the shot's own words to decide whether to attach the pack photograph at all.
    want_pack = payload.get("include_pack")
    if want_pack is None:
        want_pack = bool(re.search(
            r"\bpack(et|s|-shot)?\b|\bcarton\b|\btetra\b|\bfssai\b|\bpour(ing|ed|s)?\b|\bbottle\b|"
            r"\bglass of milk\b|\blabel\b", subject, re.IGNORECASE))
    lib_refs = library.shot_references(want_pack=want_pack, pack_id=str(payload.get("pack_id") or ""),
                                       cast_id=str(payload.get("cast_id") or ""),
                                       plate_id=str(payload.get("plate_id") or ""))
    want = [u for u in lib_refs["refs"]
            if not (u == lib_refs["plate"] and payload.get("use_plate") is False)]
    for u in want:
        if len(refs) >= 3:
            break
        if u not in refs:
            refs.append(u)
    plate_used = bool(lib_refs["has_plate"] and lib_refs["plate"] in refs)
    pack_used = bool(lib_refs["has_pack"] and lib_refs["pack"] in refs)
    if refs:
        # The instruction changes when a plate is in the reference set, and this is not cosmetic. The
        # original line said "Change only the action, SETTING and camera" — an explicit instruction to
        # invent a new location, which is the exact opposite of what a plate is for. Supplying a plate
        # under that wording would have had the two fighting, and the words would have won: the same
        # failure as the POSM style strings overriding the isolation clauses. So the sentence is
        # rewritten rather than the plate simply bolted on.
        #
        # Clothing is deliberately no longer an unconditional "identical... down to colour and detail".
        # That wording won every time regardless of what the shot's own description asked for, which is
        # exactly why a 5:45am bedroom shot came back in the same outfit as the exam hall: the fixed
        # clause and the shot's own words were never actually competing, the clause always won. Face,
        # hair, skin tone, body type and age still lock unconditionally — that is the identity a
        # reference image exists to hold — but clothing now follows the new shot's own description when
        # it says something about it, and only defaults to matching the reference when it does not.
        clothing = ("their clothing as described for this new shot if it says anything about what "
                    "they are wearing, and otherwise identical clothing to the reference")
        pack_clause = (" Reuse the EXACT product pack from the reference images — same label, colours, "
                       "type and proportions, down to the fine print — never redrawn or reimagined."
                       if pack_used else "")
        if plate_used:
            prompt = (
                "Generate the next shot of the same film. Reuse the EXACT same people from the "
                f"reference images: identical faces, hair, skin tone, body type and ages, and {clothing}."
                f"{pack_clause} Reuse the SAME location and the same light from the reference images: "
                "the same room or place, the same time of day, the same quality and direction of "
                "light. If this shot continues the same scene as the reference, also keep people in "
                "the same seats/positions and facing the same direction as in the reference — change "
                "blocking only if this shot's own description calls for it. Change only the action and "
                "the camera otherwise. "
                f"New shot: {subject}. {craft} "
                "No on-screen text, captions, logos, watermarks or borders.")
        else:
            prompt = (
                "Generate the next shot of the same film, reusing the EXACT same people from the "
                f"reference image: identical faces, hair, skin tone, body type and ages, and {clothing}."
                f"{pack_clause} Change only the action, setting and camera. "
                f"New shot: {subject}. {craft} "
                "No on-screen text, captions, logos, watermarks or borders.")
        eng = _engine(payload, "image")
        model, size, _tier = _img_tier(payload)
        url, provider = "", ""
        if _use(eng, "google"):
            url, provider = gemini.image_from_reference(prompt, refs, ratio=ratio, model=model,
                                                        size=size), "google"
        if not url and _use(eng, "fal"):
            provider = "fal"
            url = creative.image_from_reference(prompt, refs, ratio=ratio,
                                               seed=payload.get("seed"))
        if url:
            # `plate_used`/`pack_used` are reported rather than inferred: "did this frame carry the
            # location" and "did this frame carry the real pack photo" are the questions a person asks
            # when two shots do not match, and they should be answerable from the response instead of
            # by re-reading the library.
            _record_made("scene_still", subject[:80] or "Scene still", url=url, payload=payload,
                         route="/scene-still")
            return {"image_url": url, "from_reference": True, "provider": provider,
                    "plate_used": plate_used, "pack_used": pack_used, "references": len(refs)}
        print("[main] reference frame failed on both providers; falling back to text-to-image",
              file=sys.stderr, flush=True)
    parts = [f"Marketing image for {_brand_line()}."]
    if characters:
        parts.append(f"Keep these characters identical and consistent across every frame: {characters}.")
    parts.append(f"Subject: {subject}.")
    parts.append(craft)
    parts.append(f"Framed for a {ratio} composition with tasteful negative space. "
                 "No on-screen text, captions, typography, logos, watermarks or borders.")
    prompt = " ".join(parts)
    eng = _engine(payload, "image")
    model, size, tier = _img_tier(payload)
    if _use(eng, "google"):
        url = gemini.image(prompt, ratio=ratio, model=model, size=size)
        if url:
            _record_made("scene_still", subject[:80] or "Scene still", url=url, payload=payload,
                         route="/scene-still")
            return {"image_url": url, "from_reference": False, "provider": "google", "tier": tier}
    if not _use(eng, "fal"):
        return JSONResponse(status_code=502, content={
            "detail": "Google image generation failed and the engine is pinned to Google — "
                      "check Google credits, or switch the Images engine to fal."})
    try:
        res = creative.generate_creative("imagen-4-ultra", prompt, ratio=ratio, seed=payload.get("seed"))
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
    if not res.get("url"):
        return JSONResponse(status_code=501, content={
            "detail": "Image generation failed on both providers — check credits for your Google "
                      "and fal keys (see render-log.txt)."})
    _record_made("scene_still", subject[:80] or "Scene still", url=res["url"], payload=payload,
                 route="/scene-still")
    return {"image_url": res["url"], "from_reference": False, "provider": "fal"}


@app.post("/production-bible-docx")
def production_bible_docx(payload: dict):
    """The whole production as one Word document: script table, storyboard images, department notes."""
    try:
        out = docs.build_production_bible(
            payload.get("title") or "Production Bible",
            payload.get("logline", ""),
            payload.get("scenes") or [],
            payload.get("departments") or [],
            frames=payload.get("frames") or [],
            meta=payload.get("meta") or {},
            cast_sheet=payload.get("characters", ""),
            cast_reference=payload.get("cast_reference", ""))
    except Exception as e:
        raise HTTPException(500, f"Production bible build failed: {e}")
    base = (payload.get("title") or "Production_Bible").replace(" ", "_")
    return FileResponse(out, filename=f"{base}.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# --- guided brief (Media/Digital/Pack/Product/PR) -> .docx -----------------------
@app.post("/brief-docx")
def brief_docx(payload: dict):
    # Keep it on the way past. A brief good enough to export is a brief worth having downstream, and a
    # store that waits for somebody to press Save is empty at the moment it is needed.
    try:
        fields = dict(payload.get("fields") or {})
        if payload.get("objective"):
            fields.setdefault("commObjective", payload["objective"])
        briefstore.put(fields, brand=str(payload.get("brand") or ""),
                       title=str(payload.get("title") or ""),
                       fmt=str(payload.get("format") or ""),
                       source="brief-docx", brief_id=str(payload.get("id") or ""))
    except Exception:
        pass          # never let keeping a copy stop somebody getting their document
    try:
        out = docs.build_brief_docx(payload.get("title", "Brief"),
                                    payload.get("objective", ""), payload.get("fields", {}) or {})
    except Exception as e:
        raise HTTPException(500, f"Brief document build failed: {e}")
    base = (payload.get("title") or "Brief").replace(" ", "_")
    return FileResponse(out, filename=f"{base}.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# --- film shooting script -> .docx -----------------------------------------------
@app.post("/video-script-docx")
def video_script_docx(payload: dict):
    try:
        out = docs.build_script_docx(payload.get("title", "Film Script"),
                                     payload.get("logline", ""), payload.get("scenes", []) or [])
    except Exception as e:
        raise HTTPException(500, f"Script document build failed: {e}")
    return FileResponse(out, filename="Film_Script.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# --- /shot-still does two different jobs, and the payload says which ------------------------------
#
# This path had one meaning and now has two, so it branches here rather than being registered twice.
# FastAPI matches the FIRST route for a path, so a second `@app.post("/shot-still")` further down the
# file is not an override — it is dead code that looks live. That is exactly what happened: the shot-list
# screen's `{id}` request reached the *generator* below, which spent a real image credit inventing a
# storyboard frame instead of pulling one out of the footage.
#
#   { id }            the shot list — pull a real frame OUT of the attached take
#   { shot, look }    the shoot board — GENERATE a storyboard still from a description
#
# They are not variants of one idea. The first is evidence, the second is a sketch, and a signed take
# whose still was generated is a shot that passed the gate on evidence it does not have.

@app.post("/shot-still")
def shot_still(payload: dict):
    if str(payload.get("id") or "").strip():
        return _shot_still_from_take(payload)

    shot = str(payload.get("shot", "")).strip()
    look = str(payload.get("look", "")).strip()
    if not shot and not look:
        return JSONResponse(status_code=400, content={
            "detail": "Send `id` to pull a frame from a shot's take, or `shot` and `look` to generate a "
                      "storyboard still from a description."})
    model_id = payload.get("model") or "imagen-4-ultra"
    prompt = (
        f"Cinematic storyboard still, photorealistic, for a {_brand_line()} brand film. "
        f"Shot: {shot}. Look: {look}. Authentic setting for that market, warm natural light, no text or logos."
    )
    try:
        res = creative.generate_creative(model_id, prompt)
        return {"url": res.get("url") or "", "live": res.get("provider") == "fal",
                "generated": True}
    except Exception as e:
        return {"url": "", "live": False, "error": str(e)}


# =====================================================================================
# Reference library — ground truth. Uploaded and signed off; nothing generated goes in.
# =====================================================================================

@app.get("/library")
def library_list(kind: str = "", signed: int = 0):
    return {"kinds": [{"id": k, "label": v} for k, v in library.KINDS.items()],
            "items": library.items(kind, signed_only=bool(signed)),
            "summary": library.summary()}


@app.post("/library-add")
async def library_add(kind: str = Form(...), name: str = Form(""), note: str = Form(""),
                      tags: str = Form(""), who: str = Form(""),
                      files: list[UploadFile] = File(default=[])):
    """Take files into the library. Copy-only items (a locked claim, say) need no file."""
    added, errors = [], []
    for f in files or []:
        try:
            data = await f.read()
            added.append(library.add(data, name or f.filename or "file", kind,
                                     filename=f.filename or "", note=note, tags=tags, added_by=who))
        except Exception as e:
            errors.append(f"{f.filename}: {e}")
    if not files and kind == "copy" and note.strip():
        # Locked copy is the string itself, so store it as its own tiny record.
        added.append(library.add(note.strip().encode("utf-8"), name or note.strip()[:60],
                                 "copy", note=note.strip(), tags=tags, added_by=who))
    if not added:
        return JSONResponse(status_code=400, content={
            "detail": "; ".join(errors) or "Nothing to add — choose a file, or write the copy."})
    return {"added": added, "detail": "; ".join(errors), "summary": library.summary()}


@app.post("/library-sign")
def library_sign(payload: dict):
    row = library.sign_off(str(payload.get("id") or ""), str(payload.get("who") or ""),
                           bool(payload.get("on", True)))
    if not row:
        return JSONResponse(status_code=404, content={"detail": "No such item."})
    return {"item": row, "summary": library.summary()}


@app.post("/library-remove")
def library_remove(payload: dict):
    ok = library.remove(str(payload.get("id") or ""))
    return {"ok": ok, "summary": library.summary()}


@app.post("/library-adopt")
def library_adopt(payload: dict):
    """Approve a generated candidate into Ground Truth, in one step. `{url, kind, name?, note?,
    made_id?}` -> `{item, summary}`.

    **Approval and sign-off are now the same act, not a default that could go either way.** This used
    to default `sign` to `True` but let a caller override it — a dormant finding from the round-83
    audit (the route's own docstring insisted sign-off "is a person's deliberate choice, not a
    default," while the code let it be skipped anyway). Under the corrected model there is no
    in-between state to model: a candidate that isn't approved never calls this route at all — it lives
    in the `made` ledger instead (see `made.py`) — so calling this route IS the deliberate choice, and
    the item always lands signed.

    `made_id`, when given, is the ledger row this candidate came from — `made.approve()` marks it
    promoted so it drops out of "What it has made"'s default listing (one home at a time, not shown
    pending *and* live at once). Optional because not every adopted asset started life as a tracked
    `made.py` row (older callers, or a future direct-upload-style adoption).
    """
    url = str(payload.get("url") or "").strip()
    kind = str(payload.get("kind") or "").strip()
    if kind not in library.KINDS:
        return JSONResponse(status_code=400, content={"detail": f"Unknown kind {kind!r}."})
    if not url:
        return JSONResponse(status_code=400, content={"detail": "No image to adopt."})
    data = keyvisual._resolve_bytes(url)
    if not data:
        return JSONResponse(status_code=400, content={
            "detail": "Could not read that image — render it again and retry."})
    ext = os.path.splitext(url.split("?")[0])[1][:10] or ".jpg"
    descriptor = str(payload.get("name") or kind).strip()
    who = str(payload.get("who") or "")
    try:
        item = library.add(data, f"{library.APPROVED_LABEL} — {descriptor}", kind,
                           filename=f"draft{ext}", note=str(payload.get("note") or ""),
                           added_by=who, source="generated")
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    item = library.sign_off(item["id"], who, True) or item
    made_id = str(payload.get("made_id") or "")
    if made_id:
        made.approve(made_id, item["id"], who)
    return {"item": item, "summary": library.summary()}


@app.get("/made")
def made_list(kind: str = "", include_approved: bool = False):
    """"What it has made" — the real backend listing behind the Memory tab's third room. `{items, kinds}`.

    Replaces `s.created`, the client-only array capped at 16 items that only ever tracked 5 of the
    dozens of things this app actually generates. Every generation route now calls `made.record()` at
    the moment it produces something (see `_record_made()`), so this is a real, persisted, unbounded
    history — pending candidates by default, `include_approved` to see the ones already promoted into
    Ground Truth too (kept for the audit trail, never shown as the primary listing once approved).
    """
    return {"items": made.list_entries(kind, include_approved), "kinds": made.kinds()}


@app.get("/library-file/{rel:path}")
def library_file(rel: str):
    # `{rel:path}` rather than `{kind}/{fname}` — same reason `/renders`, `/media` and `/edits` already
    # use it (main.py, `_serve_asset` call sites): a plain `{fname}` segment does not cross `/`
    # boundaries, so a `file` value with a bucket subfolder (`cast/tms-approved/<id>-<name>.jpg`) would
    # 404 at the router before `library.local_path()`'s own containment check ever ran.
    path = library.local_path(rel)
    if not path or not os.path.exists(path):
        return JSONResponse(status_code=404, content={"detail": "Not in the library."})
    return FileResponse(path)


# =====================================================================================
# Round trip — a document that left as Word, edited, coming back in
# =====================================================================================

@app.post("/import-doc")
async def import_doc(what: str = Form("script"), file: UploadFile = File(...)):
    """Read an edited brief or script back into the studio's own structure.

    `how` says whether it was read from the document's structure (exact) or interpreted by the
    model (a best effort) — the person approving it needs to know which.
    """
    name = (file.filename or "").lower()
    if not name.endswith(".docx"):
        return JSONResponse(status_code=400, content={
            "detail": "Upload the .docx you downloaded and edited. .doc and PDF can't be read back."})
    data = await file.read()
    try:
        out = roundtrip.import_brief(data) if what == "brief" else roundtrip.import_script(data)
    except Exception as e:
        return JSONResponse(status_code=400, content={
            "detail": f"Couldn't read that document: {type(e).__name__}: {e}"})
    if not out.get("ok"):
        return JSONResponse(status_code=422, content={"detail": out.get("detail", "Nothing read.")})
    return out


# =====================================================================================
# Learning log — retrieval, scored prompts and recorded corrections. No weights change.
# =====================================================================================

@app.get("/learning")
def learning_status():
    out = learning.status()
    out["templates_list"] = learning.templates()
    out["recent"] = learning.decisions(40)
    # Kept briefs, surfaced where somebody goes looking for what the studio has held on to. They are not
    # a learning tier — nothing is scored or retrieved from them — so they sit alongside the three
    # rather than inside them, and `brands` is what makes a second brand visible at all.
    out["briefs"] = briefstore.briefs()
    out["brands"] = briefstore.brands()
    return out


@app.post("/learning-decision")
def learning_decision(payload: dict):
    """Record an approval or a rejection. A rejection without a reason teaches nothing, so ask."""
    decision = str(payload.get("decision") or "").lower()
    if decision not in ("approve", "reject"):
        return JSONResponse(status_code=400, content={"detail": "decision must be approve or reject"})
    if decision == "reject" and not str(payload.get("reason") or "").strip():
        return JSONResponse(status_code=400, content={
            "detail": "Give a reason for the rejection — that reason is the only part that "
                      "improves the next round."})
    row = learning.record(str(payload.get("kind") or "work"), decision,
                          subject=str(payload.get("subject") or ""),
                          reason=str(payload.get("reason") or ""),
                          template=str(payload.get("template") or ""),
                          who=str(payload.get("who") or ""),
                          meta=payload.get("meta") if isinstance(payload.get("meta"), dict) else {})
    if decision == "approve" and str(payload.get("body") or "").strip():
        learning.keep_example(str(payload.get("kind") or "work"),
                              title=str(payload.get("subject") or "approved"),
                              body=str(payload.get("body") or ""),
                              brief=str(payload.get("brief") or ""))
    return {"recorded": row, "status": learning.status()}


@app.post("/learning-context")
def learning_context(payload: dict):
    """What the studio would put in front of the model for this brief, and why.

    Exposed as its own endpoint so the anchors can be shown on screen BEFORE generating — "what
    informed these takes" should be inspectable, not a claim.
    """
    kind = str(payload.get("kind") or "script")
    brief = str(payload.get("brief") or "")
    block, names = learning.anchor_block(kind, brief, int(payload.get("n") or 3))
    return {"anchors": names, "anchor_text": block, "rules": learning.house_rules(),
            "rules_text": learning.rules_block(),
            "locked_copy": library.locked_copy(),
            "references": {k: library.reference_url(k) for k in ("pack", "logo", "cast")}}


# =====================================================================================
# Real footage: green screen over a plate, and edits derived from an approved master
# =====================================================================================

def _resolve_media(ref: str) -> str:
    """A library id, a /library-file URL, a /media or /renders URL -> a path on disk."""
    ref = str(ref or "").strip()
    if not ref:
        return ""
    item = library.get(ref)
    if item:
        return library.local_path(item["file"])
    if "/library-file/" in ref:
        return library.local_path(ref.split("/library-file/", 1)[1])
    if "/renders/" in ref:
        return os.path.join(filmcut.RENDERS_DIR, ref.rsplit("/", 1)[1])
    # Composited shots and derived edits live here. Without this a live-action shot could be keyed,
    # attached and signed off, and then silently fail to reach the film it was made for.
    if "/edits/" in ref:
        return os.path.join(composite.EDITS_DIR, ref.rsplit("/", 1)[1])
    local = gemini.local_path(ref)
    return local or ""


@app.post("/composite")
def composite_shot(payload: dict):
    """Key green-screen footage over a plate. Both sides come from the reference library.

    This is the route to a film with real people in it: the model never has to invent or hold a
    face, because the performance is real footage and only the location is generated.
    """
    fg = _resolve_media(payload.get("footage") or payload.get("fg"))
    bg = _resolve_media(payload.get("plate") or payload.get("bg"))
    if not fg or not os.path.exists(fg):
        return JSONResponse(status_code=400, content={
            "detail": "Green-screen footage not found. Add the clip to the library first (kind: actor)."})
    if not bg or not os.path.exists(bg):
        return JSONResponse(status_code=400, content={
            "detail": "Background plate not found. Add a plate to the library (kind: plate), or "
                      "pass a generated still."})
    os.makedirs(composite.EDITS_DIR, exist_ok=True)
    name = composite.new_edit_name(str(payload.get("label") or "composite"))
    out = os.path.join(composite.EDITS_DIR, name)
    ok, err = composite.key_over_plate(
        fg, bg, out,
        key=str(payload.get("key") or composite.GREEN),
        similarity=float(payload.get("similarity") or 0.18),
        blend=float(payload.get("blend") or 0.08),
        seconds=float(payload.get("seconds") or 0))
    if not ok:
        return JSONResponse(status_code=500, content={"detail": f"Composite failed: {err[:300]}"})
    # Measure rather than assert. A key that half-worked looks fine in a thumbnail and terrible on
    # a big screen, so the number goes back with the result.
    left = composite.green_ratio(out)
    notes = []
    if left > 0.02:
        notes.append(f"{left:.0%} of the frame is still green — the key colour or the tolerance is "
                     f"off. Try a higher similarity, or pass the screen's actual colour.")
    # Keep the recipe, not just the result. A shot whose settings are lost cannot survive a revision:
    # change the plate and you are re-deriving the key by eye against the take beside it.
    settings = {"key": str(payload.get("key") or composite.GREEN),
                "similarity": float(payload.get("similarity") or 0.18),
                "blend": float(payload.get("blend") or 0.08)}
    probe = composite.probe_video(out)
    shot = shots.record(url=f"/edits/{name}",
                        footage=str(payload.get("footage") or payload.get("fg") or ""),
                        plate=str(payload.get("plate") or payload.get("bg") or ""),
                        settings=settings, green_left=left, probe=probe,
                        label=str(payload.get("label") or "shot"),
                        scene=int(payload.get("scene") or 0))
    notes += composite.match_warnings(composite.probe_video(fg))
    return {"url": f"/edits/{name}", "green_left": left, "shot": shot, "probe": probe,
            "settings": settings, "detail": " ".join(notes),
            "clean": left >= 0 and left <= 0.02}


@app.post("/composite-upload")
async def composite_upload(kind: str = Form("actor"), name: str = Form(""),
                           who: str = Form(""), shot: str = Form(""),
                           files: list[UploadFile] = File(default=[]),
                           file: UploadFile | None = File(default=None)):
    """Take footage straight off a shoot into the library, and say how it will cut.

    Design asked for upload inside `/composite` so there is no library detour after a shoot. This
    does the same job but still lands the file IN the library, because footage of real people has to
    be signable and reusable — a transient upload could be neither. The Compositor can call this and
    then `/composite` without the user ever leaving the screen.
    """
    if kind not in ("actor", "plate"):
        return JSONResponse(status_code=400, content={
            "detail": "Upload green-screen footage as 'actor' or a background as 'plate'."})
    # `file` singular as well as `files`: the shot-list screen sends one take under `file` alongside the
    # `shot` it belongs to, and only accepting the plural form meant every take upload arrived as an empty
    # list and 400'd with "No files received" — which read as the file being rejected.
    incoming = list(files or [])
    if file is not None:
        incoming.append(file)
    added, warnings = [], []
    for f in incoming:
        data = await f.read()
        try:
            row = library.add(data, name or f.filename or "clip", kind,
                              filename=f.filename or "", added_by=who)
        except ValueError as e:
            # `library.add` now refuses a file type it can't safely serve back (see its own
            # comment) — this call site never wrapped that in a try/except, so an otherwise-clean
            # 400 rejection would have surfaced as an unhandled 500 instead.
            return JSONResponse(status_code=400, content={"detail": f"{f.filename}: {e}"})
        added.append(row)
        # Warn while someone is still holding the file, rather than in the delivered master.
        path = library.local_path(row["file"])
        clip = composite.probe_video(path) if path else {}
        if clip.get("width"):
            row["probe"] = clip
            for w in composite.match_warnings(clip):
                warnings.append(f"{row['name']}: {w}")
    if not added:
        return JSONResponse(status_code=400, content={"detail": "No files received."})

    # `url` at the top level, for the caller that uploaded ONE thing and now needs to point at it. The
    # shot-list screen reads `u.url || u.path` and this response carried neither, so a take uploaded
    # successfully still could not be attached to the shot it was uploaded for.
    first = added[0]
    url = f"/library-file/{first['file']}" if first.get("file") else ""
    out = {"added": added, "detail": " · ".join(warnings), "warnings": warnings,
           "summary": library.summary(), "url": url, "path": url, "file": first.get("file", ""),
           "name": first.get("name", "")}

    # Uploaded for a specific shot: attach it here rather than making the caller do a second round trip
    # it cannot recover from if it fails. The response still carries `url`, so a caller that wants to
    # attach it itself is unaffected.
    if shot.strip() and url:
        row = shots.attach(shot.strip(), url, first.get("name") or "")
        if row:
            out["shot"] = row
            out["summary_shots"] = shots.summary(row.get("execution") or "")
    return out


@app.get("/shots")
def list_shots(execution: str = "", scene: int = 0, all: bool = False):
    """The shot list for one shoot. `?execution=<id>`; absent means **the unattached shoot**.

    Absent is not "everything" — a shot list is a shoot, a shoot belongs to a piece of work, and
    "everything" is never a shoot. `?all=true` returns the whole store, which only a migration view
    wants. `?scene=` is the film render path's older lookup and is kept working.
    """
    ex = "*" if all else (execution or "")
    rows = shots.items(ex)
    if scene:
        rows = [r for r in rows if int(r.get("scene") or 0) == int(scene)]
    st = shots.status(ex)
    # `status` rides along, carrying `by_stage`, because this is the call the board actually makes.
    # The five-stage strip was reading `status.by_stage` off this response and this response did not have
    # one — so the strip silently never rendered. Making the board call a second route instead would have
    # been the same information behind one more round trip.
    return {"shots": rows, "summary": shots.summary(ex),
            "findings": shots.findings(ex), "execution": execution or None,
            "status": st}


@app.post("/shot-attach")
def shot_attach(payload: dict):
    """Attach uploaded footage to a shot. `{id, url, filename}`.

    This used to read `{id, scene}` and **drop the url and filename entirely**, so the take a person had
    just uploaded was thrown away and the shot was attached to scene 0. The shape now matches what the
    screen has after the upload.

    Attaching clears any existing signature, and the response says so. What was approved is not what is
    here now, and a signature that survives its own footage being replaced approves footage nobody looked
    at. `{id, scene}` still works for the film render path, which is a different job.
    """
    sid = str(payload.get("id") or "")
    if "scene" in payload and not payload.get("url"):
        row = shots.set_scene(sid, int(payload.get("scene") or 0))
        if not row:
            return JSONResponse(status_code=404, content={"detail": "No such shot."})
        note = ("" if row.get("signed") else
                "Attached to the scene, but this shot is not signed off — Production will still "
                "generate it until someone signs it.")
        return {"shot": row, "detail": note, "summary": shots.summary(row.get("execution") or "")}

    was_signed = bool((shots.get(sid) or {}).get("signed"))
    row = shots.attach(sid, str(payload.get("url") or ""), str(payload.get("filename") or ""))
    if not row:
        return JSONResponse(status_code=404, content={
            "detail": "No such shot, or no url was sent with the take."})
    ex = row.get("execution") or ""
    return {"shot": row,
            "detail": ("Take attached. The previous signature has been withdrawn — this is not the "
                       "footage that was approved." if was_signed else
                       "Take attached. Pull a still, then sign it off."),
            "summary": shots.summary(ex), "findings": shots.findings(ex)}


def _shot_still_from_take(payload: dict):
    """Pull the still **from the attached take**. `{id, at?}`. Reached via /shot-still — see the note there.

    Not to be confused with generating an image of a described look — that is `/scene-still`. The
    compositor keys against a frame, and a frame invented from a description is not the footage. A signed
    take whose still came from somewhere else is a shot that passed the gate on evidence it does not have.
    """
    sid = str(payload.get("id") or "")
    row = shots.get(sid)
    if not row:
        return JSONResponse(status_code=404, content={"detail": "No such shot."})
    take = str(row.get("take") or "").strip()
    if not take:
        return JSONResponse(status_code=400, content={
            "detail": "There is no take on this shot yet, so there is no frame to pull."})
    src = _resolve_media(take)
    if not src or not os.path.exists(src):
        return JSONResponse(status_code=400, content={
            "detail": "The take is no longer on disk, so a frame cannot be pulled from it."})

    os.makedirs(gemini.MEDIA_DIR, exist_ok=True)
    name = f"still-{row['id']}-{uuid.uuid4().hex[:6]}.jpg"
    out = os.path.join(gemini.MEDIA_DIR, name)
    try:
        at = float(payload.get("at", -1))
    except (TypeError, ValueError):
        at = -1.0
    ok, err = composite.still_from(src, out, at)
    if not ok:
        return JSONResponse(status_code=502, content={"detail": err[:300] or
                            "A frame could not be pulled from that take."})
    row = shots.set_still(sid, f"/media/{name}")
    ex = (row or {}).get("execution") or ""
    return {"shot": row, "still": f"/media/{name}",
            "detail": "Still pulled from the take. Sign the shot off to hand it to the compositor.",
            "summary": shots.summary(ex), "findings": shots.findings(ex)}


@app.post("/shot-sign")
def shot_sign(payload: dict):
    """Sign a take off, or `{id, clear:true}` to withdraw. Signature is `{who, at}` or null.

    **The stored studio manager wins over the posted name.** A client-side name is a client-side truth
    and a sign-off on footage of real people has to hold up later, so the server's own record is the
    authority and the posted value is only the fallback.

    **An unattributable signature is refused, not written as "unattributed".** A placeholder in that
    field reads as the gate having been passed. This used to read an `on` flag defaulting to true, so
    asking it to clear a signature re-signed it — the exact opposite of the request.
    """
    sid = str(payload.get("id") or "")
    if payload.get("clear"):
        row = shots.unsign(sid)
        if not row:
            return JSONResponse(status_code=404, content={"detail": "No such shot."})
        ex = row.get("execution") or ""
        return {"shot": row, "detail": "Signature withdrawn.",
                "summary": shots.summary(ex), "findings": shots.findings(ex)}

    stored = str((brandprofile.studio_settings() or {}).get("manager_name") or "").strip()
    posted = str(payload.get("who") or "").strip()
    who = stored or ("" if posted.lower() in ("", "unattributed") else posted)
    row, err, code = shots.sign(sid, who)
    if err:
        return JSONResponse(status_code=code, content={"detail": err})
    ex = row.get("execution") or ""
    return {"shot": row, "detail": f"Signed off by {who}.",
            "summary": shots.summary(ex), "findings": shots.findings(ex)}


@app.post("/shot-remove")
def shot_remove(payload: dict):
    ex = str(payload.get("execution") or "")
    ok = shots.remove(str(payload.get("id") or ""))
    return {"ok": ok, "summary": shots.summary(ex), "findings": shots.findings(ex)}


@app.get("/shots-compositor")
def shots_compositor(execution: str = ""):
    """Signed takes only, each carrying its still. The whole compositor handoff, in one response."""
    rows = shots.for_compositor(execution or "")
    return {"shots": rows, "summary": shots.summary(execution or ""),
            "findings": [f for f in shots.findings(execution or "")
                         if f["level"] == "blocking"]}


@app.post("/shot-recompose")
def shot_recompose(payload: dict):
    """Rebuild a shot from its stored recipe — optionally against a different plate.

    This is what the recipe is for: swap the location for a different market or season and get the
    same key, the same take, the same result, rather than matching it again by eye.
    """
    sid = str(payload.get("id") or "")
    old = shots.get(sid)
    if not old:
        return JSONResponse(status_code=404, content={"detail": "No such shot."})

    # The note is a direction for the rebuild — "she is too central, give me the left third" — so it is
    # recorded and acted on rather than filed. Recording happens first and unconditionally: it clears the
    # signature, which must hold even if the rebuild below fails, because the moment somebody asks for a
    # recompose the approved version is no longer what anyone wants.
    note = str(payload.get("note") or "").strip()
    shots.note_recompose(sid, note)

    recipe = old.get("recipe") or {}
    fg = _resolve_media(recipe.get("footage") or old.get("footage") or old.get("take"))
    if not fg or not os.path.exists(fg):
        row = shots.set_still(sid, "", pending=False)
        return JSONResponse(status_code=400, content={
            "detail": "The original footage is no longer on disk, so this shot cannot be rebuilt. The "
                      "signature has been withdrawn because the recompose was asked for. Re-attach the "
                      "take.",
            "shot": row})
    bg = _resolve_media(payload.get("plate") or recipe.get("plate") or old.get("plate"))
    if not bg or not os.path.exists(bg):
        row = shots.set_still(sid, "", pending=False)
        return JSONResponse(status_code=400, content={
            "detail": "That plate is not in the library, so there is nothing to key over.", "shot": row})

    st = recipe.get("settings") or old.get("settings") or {}
    os.makedirs(composite.EDITS_DIR, exist_ok=True)
    name = composite.new_edit_name(old.get("slug") or old.get("label") or "shot")
    out = os.path.join(composite.EDITS_DIR, name)
    ok, err = composite.key_over_plate(fg, bg, out, key=st.get("key") or composite.GREEN,
                                       similarity=float(st.get("similarity") or 0.18),
                                       blend=float(st.get("blend") or 0.08))
    if not ok:
        row = shots.set_still(sid, "", pending=False)
        return JSONResponse(status_code=500, content={"detail": err[:300], "shot": row})

    left = composite.green_ratio(out)
    # Same shot, rebuilt — not a new row. A second row would leave the old signature attached to
    # superseded footage, which is the thing the whole gate exists to prevent.
    row = shots.record(url=f"/edits/{name}",
                       footage=recipe.get("footage") or old.get("footage", ""),
                       plate=str(payload.get("plate") or recipe.get("plate") or ""),
                       settings=st, green_left=left, probe=composite.probe_video(out),
                       label=old.get("filename") or old.get("slug") or "shot",
                       scene=int(old.get("scene") or 0),
                       execution=old.get("execution"), shot_id=sid)
    ex = row.get("execution") or ""
    return {"shot": row, "green_left": left, "from": sid, "note": note,
            "detail": ("Rebuilt with the original key settings"
                       + (f", against: {note}" if note else "")
                       + ". The signature was withdrawn — pull a still and sign it again."),
            "summary": shots.summary(ex), "findings": shots.findings(ex)}


@app.post("/edit-master")
def edit_master(payload: dict):
    """Cut down or reframe an approved master. Trim and crop only — nothing is re-generated.

    That is deliberate: a 9:16 cutdown of a signed-off film is the same footage, so it inherits the
    sign-off. Re-rendering it would produce a different film that merely resembles the approved one.
    """
    src = _resolve_media(payload.get("master"))
    if not src or not os.path.exists(src):
        return JSONResponse(status_code=400, content={"detail": "That master is no longer on disk."})
    os.makedirs(composite.EDITS_DIR, exist_ok=True)
    label = str(payload.get("label") or "edit")
    name = composite.new_edit_name(label)
    out = os.path.join(composite.EDITS_DIR, name)
    ok, err = composite.edit(src, out,
                             seconds=float(payload.get("seconds") or 0),
                             aspect=str(payload.get("aspect") or ""),
                             start=float(payload.get("start") or 0),
                             mute=bool(payload.get("mute")))
    if not ok:
        return JSONResponse(status_code=400, content={"detail": err[:300]})
    exe = filmcut.ffmpeg_exe()
    return {"url": f"/edits/{name}", "label": label,
            "seconds": round(filmcut.probe_seconds(exe, out), 2) if exe else 0,
            "aspect": str(payload.get("aspect") or "16:9"),
            "from_master": os.path.basename(src)}


@app.get("/edits")
def list_edits():
    os.makedirs(composite.EDITS_DIR, exist_ok=True)
    exe = filmcut.ffmpeg_exe()
    out = []
    for f in sorted(os.listdir(composite.EDITS_DIR)):
        if not f.lower().endswith(".mp4"):
            continue
        p = os.path.join(composite.EDITS_DIR, f)
        out.append({"name": f, "url": f"/edits/{f}", "bytes": os.path.getsize(p),
                    "seconds": round(filmcut.probe_seconds(exe, p), 2) if exe else 0})
    return {"edits": out, "aspects": list(composite.ASPECTS)}


# =====================================================================================
# Messaging house — an option space you narrow, not a document you accept
# =====================================================================================

@app.get("/houses")
def houses_list():
    # `caveat` is served here because this is the screen someone is on before they start a house. It
    # says what the portal is and is not: everything editable here, downloadable as a record or a
    # worksheet, and not importable back. Better said once up front than discovered by someone who has
    # spent an afternoon rewriting the Word file.
    cards = strategy.houses()
    # `claim_state` per card, composed here for the same reason it is composed in `GET /house/{id}`
    # rather than inside `strategy.status()`: `ideas.py` already imports `strategy`, so the reverse
    # would be circular, and this route is the one place both are safely in scope. Design's own
    # round-22 return flagged real uncertainty about whether the list carries this field at all — it
    # did not, so the badge on every house CARD (as opposed to the opened house) would have read
    # undefined. One lookup per card; the house list is short enough that this is not worth caching.
    for c in cards:
        pl = ideas.for_house(c.get("id", ""))
        it = ideas.chosen_platform(pl) if pl else None
        c["claim_state"] = ("settled" if it.get("ladder_confirmed") else "provisional") if it else None
    return {"houses": cards, "layers": strategy.LAYERS,
            "culture_kinds": list(strategy.CULTURE_KINDS), "media": list(strategy.MEDIA),
            "caveat": strategy.ROUND_TRIP_CAVEAT,
            "downloads": {"record": "/house-docx/{id}", "worksheet": "/house-docx/{id}?mode=worksheet"}}


@app.post("/house-new")
def house_new(payload: dict):
    """A house is written against a brief. `brief` may be an id, a dict of fields, or typed text.

    All three are kept. The previous behaviour type-checked for a dict, failed on the string the screen
    actually sends, and substituted an empty brief — so every house was generated against "(no brief
    attached)" while the screen showed the words somebody had typed. Free text now becomes a real
    stored brief rather than disappearing.

    The brand comes from the brief when there is one. Typing it separately here is what let a brief for
    one brand and a house for another sit side by side looking related.
    """
    b = briefstore.resolve(payload.get("brief"))
    # A house needs something to be about. Without this an empty POST created a house called "Brand"
    # with nothing in it, and the strategy index filled with them — four had already accumulated before
    # anybody noticed, and they are indistinguishable from real work that has not been started.
    if not str(payload.get("brand") or "").strip() and not b:
        return JSONResponse(status_code=400,
                            content={"detail": "A house needs a brand, or a brief to take one from."})
    brand = str(payload.get("brand") or "").strip() or (b or {}).get("brand") or "Brand"
    # The project rides in with the brief. `canon` is the brief's FIELDS and the project is not one of
    # them — it names the piece of work, not a section of the document — so it has to be carried across
    # explicitly. Without this the whole inheritance chain began at step two and every house was unnamed.
    _brief_for_house = dict((b or {}).get("canon") or {})
    _proj = project.clean(payload.get("project") or (b or {}).get("project") or "")
    if _proj:
        _brief_for_house["project"] = _proj
    h = strategy.new_house(brand, _brief_for_house)
    if _proj:
        h["project_source"] = "inherited" if not payload.get("project") else "named"
        strategy.save(h)
    if b and b.get("id"):
        h["brief_id"] = b["id"]
        h["brief_title"] = b.get("title", "")
        h = strategy.save(h)
    # `claim_state` is always `None` here — a brand-new house has no adopted platform yet, by
    # construction. Sent explicitly rather than left absent so this route's shape matches
    # `GET /house/{id}` and the `/houses` list exactly; the client's own fallback would resolve the
    # same value either way, but three routes serving one field two different ways is exactly the
    # class of drift this project keeps finding.
    return {"house": h, "status": strategy.status(h), "claim_state": None,
            "brief": briefstore.snapshot(b) if (b and b.get("id")) else None,
            "brief_unsaved": bool(b and not b.get("id"))}


# =====================================================================================
# Tenancy and brand profiles — the brand as data, so it stops being code
# =====================================================================================

# Loose pre-tenancy directories are moved into the active tenant once, at startup, and the result is
# logged. Doing it on import would hide a half-finished move inside somebody's first request.
_MIGRATION = tenancy.migrate_all()

# Fold any pre-existing shot-list documents into flat shot rows. Idempotent, and it leaves the original
# renamed rather than deleted — somebody's shoot is not worth a tidy, unreviewable migration.
try:
    _folded = shots.migrate_shotlists()
    if _folded.get("documents"):
        print(f"[shots] {_folded['note']}", file=sys.stderr, flush=True)
except Exception as _e:                                          # never block startup on a migration
    print(f"[shots] fold-in skipped: {_e}", file=sys.stderr, flush=True)
for _m in _MIGRATION:
    if _m.get("moved") or _m.get("skipped"):
        print(f"[tenancy] {_m['kind']}: {_m['note']}", flush=True)
# Seeded only when no profile exists, so the values that used to be hardcoded are preserved on the day
# this lands and can never reappear over somebody else's brand.
_SEEDED = brandprofile.seed()
if _SEEDED:
    print(f"[brand] seeded the first profile: {_SEEDED['name']}", flush=True)


def _brand_line() -> str:
    """One phrase naming the brand for an image or video prompt — "Name (category, market, #tag)".

    Built from the profile so the same call works for any brand. With no profile it returns a neutral
    "a brand", which produces a generic frame rather than a confidently wrong one: an image model given
    an invented category will render it, and nobody reviewing the picture can tell it was invented.
    """
    b = brandprofile.resolve()
    if not b:
        return "a brand"
    bits = [x for x in (b.get("category"), b.get("market")) if x]
    tags = " ".join(b.get("hashtags") or [])
    name = b.get("hero_product") or b.get("name") or "a brand"
    inner = ", ".join(bits)
    return f"{name} ({inner}{'. ' + tags if tags else ''})" if inner else name


@app.get("/tenants")
def tenants_list():
    return {"tenants": tenancy.tenants(), "active": tenancy.tenant(),
            "kinds": list(tenancy.KINDS), "migration": _MIGRATION}


def _brand_rows() -> list[dict]:
    """Brand profiles with `voice` on each — the shape the switcher reads, used by every route that
    returns a list so /brands, /brand-save and /brand-active can never disagree about it."""
    return [dict(b, voice=brandprofile.voice_block(b)) for b in brandprofile.profiles()]


@app.get("/brands")
def brands_list():
    """Every brand profile. `voice` is exactly what a generator will be told about it, so the grounding
    is inspectable rather than something the prompts do privately."""
    # `voice` sits on each brand object AND in a top-level map keyed by name.
    #
    # The switcher's "what the model is told about this brand" panel reads the per-brand key, and a
    # missing one means it does not render the toggle at all — so keying it only by id, as this used to,
    # showed no way to inspect the grounding on the one screen built to expose it. The top-level map is
    # kept for anything that already looks there.
    out = _brand_rows()
    return {"brands": out, "fields": list(brandprofile.FIELDS),
            "list_fields": list(brandprofile.LIST_FIELDS),
            "voice": {b["name"]: b["voice"] for b in out},
            "voice_by_id": {b["id"]: b["voice"] for b in out}}


@app.get("/brand/{brand_id}")
def brand_get(brand_id: str):
    b = brandprofile.load(brand_id)
    if not b:
        return JSONResponse(status_code=404, content={"detail": "No such brand profile."})
    return {"brand": b, "voice": brandprofile.voice_block(b)}


@app.post("/brand-save")
def brand_save(payload: dict):
    """Create or update a brand. Upserts on `id`, or on the name when no id is given, so saving the same
    brand twice corrects it rather than making a second one."""
    if not str(payload.get("name") or "").strip() and not payload.get("id"):
        return JSONResponse(status_code=400, content={"detail": "A brand needs a name."})
    b = brandprofile.put(payload, brand_id=str(payload.get("id") or ""))
    return {"brand": dict(b, voice=brandprofile.voice_block(b)), "brands": _brand_rows(),
            "voice": brandprofile.voice_block(b)}


@app.post("/brand-logo")
async def brand_logo(brand: str = Form(...), file: UploadFile = File(...)):
    """Store a brand's logo and return a URL that survives a reload.

    The settings screen used `URL.createObjectURL(file)` — a blob URL that lives in one browser tab and
    dies with it. It looked like an upload, was never sent anywhere, and the logo vanished on refresh.
    This writes the bytes next to the brand profile and puts the served path on `profile.logo`.
    """
    b = brandprofile.load(brand) or brandprofile.by_name(brand)
    if not b:
        return JSONResponse(status_code=404, content={"detail": "No such brand profile."})
    data = await file.read()
    if not data:
        return JSONResponse(status_code=400, content={"detail": "The file was empty."})
    if len(data) > 4 * 1024 * 1024:
        return JSONResponse(status_code=413,
                            content={"detail": "Logos over 4MB are almost always the wrong file — an "
                                               "SVG or a trimmed PNG is what belongs here."})
    # Accept every raster format a browser will actually render, plus SVG.
    #
    # This list used to stop at WebP, and the message said the file was "not an image the browser can
    # show" — which was false. A real logo, `Heritage-Foods-logo-770x435.avif`, was refused with a reason
    # that was wrong twice over: browsers render AVIF perfectly well, and the check was on the extension,
    # not on anything's ability to decode it. Somebody with a valid file was told it was invalid.
    #
    # The client now converts exotic formats to PNG before sending, so this is the second line of defence
    # rather than the first — but a wrong error message is worse than a strict one, because it sends the
    # person looking for a problem with their file.
    ALLOWED = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif",
               ".heic", ".heif", ".bmp", ".ico"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED:
        return JSONResponse(status_code=400,
                            content={"detail": f"{ext or 'That file type'} is not one this can store. "
                                               f"Use any of: "
                                               f"{', '.join(sorted(e[1:] for e in ALLOWED))}."})
    d = tenancy.dir("brands")
    # The id is the filename, so a re-upload replaces rather than accumulating.
    for stale in os.listdir(d):
        if stale.startswith(b["id"] + "-logo"):
            try:
                os.remove(os.path.join(d, stale))
            except OSError:
                pass
    name = f"{b['id']}-logo{ext}"
    with open(os.path.join(d, name), "wb") as fh:
        fh.write(data)
    b["logo"] = f"/brand-logo/{b['id']}"
    b["logo_file"] = name
    b = brandprofile.save(b)
    return {"brand": dict(b, voice=brandprofile.voice_block(b)), "brands": _brand_rows(),
            "logo": b["logo"], "bytes": len(data)}


@app.get("/brand-logo/{brand_id}")
def brand_logo_get(brand_id: str):
    b = brandprofile.load(brand_id)
    name = (b or {}).get("logo_file") or ""
    path = os.path.join(tenancy.dir("brands"), name) if name else ""
    if not b or not name or not os.path.exists(path):
        return JSONResponse(status_code=404, content={"detail": "No logo for that brand."})
    media = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
             ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
             ".avif": "image/avif", ".heic": "image/heic", ".heif": "image/heif",
             ".bmp": "image/bmp", ".ico": "image/x-icon"}.get(
                 os.path.splitext(name)[1].lower(), "application/octet-stream")
    return FileResponse(path, media_type=media)


@app.post("/brand-logo-clear")
def brand_logo_clear(payload: dict):
    b = brandprofile.load(str(payload.get("brand") or ""))
    if not b:
        return JSONResponse(status_code=404, content={"detail": "No such brand profile."})
    name = b.pop("logo_file", "")
    b.pop("logo", None)
    if name:
        try:
            os.remove(os.path.join(tenancy.dir("brands"), name))
        except OSError:
            pass
    b = brandprofile.save(b)
    return {"brand": dict(b, voice=brandprofile.voice_block(b)), "brands": _brand_rows()}


@app.get("/studio-settings")
def studio_settings_get():
    """Theme, accent and client name — kept server-side so they survive a reload and a different browser.

    They were held in client state only, which meant every setting on that screen was a preference for
    one tab rather than a decision about the studio.

    `readiness` rides along because this is the payload the settings screen already loads, and the brand
    form lives on that screen. It saves a second round trip before the form can say anything useful.
    """
    b = brandprofile.resolve()
    return {"settings": brandprofile.studio_settings(),
            "readiness": brandprofile.readiness(b),
            "brand": b}


@app.post("/studio-settings")
def studio_settings_set(payload: dict):
    return {"settings": brandprofile.set_studio_settings(payload)}


@app.post("/project-name")
def project_name(payload: dict):
    """Name the piece of work. `{house?, plan?, platform?, brief?, name}` -> what was renamed.

    Two houses both called "Heritage", both "8 of 8 layers decided", and nothing to tell them apart. The
    brand is not the unit of work: a brand has many projects and every document belongs to exactly one.

    Renaming a house renames the plans and platforms that descend from it **unless they have been named
    separately** — inheritance is a default, not a rule, and somebody who renamed a plan meant it.
    """
    name = project.clean(payload.get("name") or "")
    if not name:
        return JSONResponse(status_code=400, content={
            "detail": "A project needs a name — that is the whole point of it. Something you would say "
                      "out loud: 'the Diwali same-day push'."})
    touched = []
    hid = str(payload.get("house") or "")
    if hid:
        h = strategy.load(hid)
        if not h:
            return JSONResponse(status_code=404, content={"detail": "No such house."})
        h["project"], h["project_source"] = name, "named"
        strategy.save(h)
        touched.append({"kind": "house", "id": hid, "project": name})
        for row in plan_mod.plans():
            if row.get("house") == hid:
                p = plan_mod.load(row["id"])
                if p and not project.of(p):
                    p["project"], p["project_source"] = name, "inherited"
                    plan_mod.save(p)
                    touched.append({"kind": "plan", "id": p["id"], "project": name})
        pl = ideas.for_house(hid)
        if pl and not project.of(pl):
            pl["project"], pl["project_source"] = name, "inherited"
            ideas.save(pl)
            touched.append({"kind": "platform", "id": pl["id"], "project": name})

    for key, loader, saver in (("plan", plan_mod.load, plan_mod.save),
                               ("platform", ideas.load, ideas.save)):
        did = str(payload.get(key) or "")
        if not did:
            continue
        d = loader(did)
        if not d:
            return JSONResponse(status_code=404, content={"detail": f"No such {key}."})
        d["project"], d["project_source"] = name, "named"
        saver(d)
        touched.append({"kind": key, "id": did, "project": name})

    if not touched:
        return JSONResponse(status_code=400, content={
            "detail": "Nothing to name — send a house, plan or platform id."})
    return {"project": name, "renamed": touched,
            "detail": f"Named '{name}'" + (f", and {len(touched) - 1} document(s) that descend from it"
                                           if len(touched) > 1 else "") + "."}


@app.get("/project-suggest")
def project_suggest(house: str = "", plan: str = ""):
    """A name for a document that predates projects. A suggestion, never written.

    Returned rather than saved because a derived name written straight to disk is indistinguishable from
    one a person chose, and somebody would find their work quietly named by the studio.
    """
    if house:
        d, kind = strategy.load(house), "house"
    elif plan:
        d, kind = plan_mod.load(plan), "plan"
    else:
        return JSONResponse(status_code=400, content={"detail": "Send a house or plan id."})
    if not d:
        return JSONResponse(status_code=404, content={"detail": f"No such {kind}."})
    if project.of(d):
        return {"project": project.of(d), "already_named": True,
                "project_source": d.get("project_source", "")}
    return {**project.derive(d, kind), "already_named": False,
            "detail": "A suggestion. Nothing is saved until you accept it."}


@app.get("/brand-fields")
def brand_fields(brand: str = "", house: str = "", brief: str = ""):
    """The brand-profile form, as data. `{spec, fields, core, derivable, ready, summary, …}`.

    The Studio Settings form is rendered from `spec` rather than hardcoded, so adding a field is a backend
    change and the two sides cannot drift. Each entry carries:

        key · label · kind (text|textarea|list|choice|rows) · options · cols · required
        ask           the question in a person's words, not the field name
        why           what changes in the output if they answer it
        derives_from  where it can be pre-filled from (brief | house | plan)

    `fields[]` is the same list with this brand's `value`, a `state` of set / derivable / missing, and a
    `suggestion` where one can be derived. **Suggestions are never saved** — a derived value nobody looked
    at is still a guess, and once stored it is indistinguishable from an answer.

    `why` is not decoration. A form that cannot say why it wants something gets filled in with whatever
    makes the asterisk go away, and this one is asking for the material that decides whether the studio
    writes category-native work or competent wallpaper.
    """
    # `brand` may be an id or a name. The settings screen has the client NAME and nothing else, so an
    # id-only lookup returned None, readiness was computed against an empty profile, and the form opened
    # saying "0 of 5" on a brand with two of the five already answered — while the card that sent you
    # there said "2 of 5". Falling back to the active profile matters as much: a name that matches nothing
    # should not silently become no brand at all.
    b = None
    if brand:
        b = brandprofile.load(brand) or brandprofile.by_name(brand)
    b = b or brandprofile.resolve()
    h = strategy.load(house) if house else None
    br = briefstore.load(brief) if brief else None
    if not h:
        # This brand's newest house, so the derivations are available on a first visit. Matched tolerantly
        # — the profile, the house and the brief spell the same brand differently.
        h = strategy.newest_for(str((b or {}).get("name") or ""))
    r = brandprofile.readiness(b, h, br)
    # The same document, grouped by what each answer UNLOCKS rather than by form section. Folded in here
    # rather than given a route of its own: `/brand-fields` already owns this form, and a second endpoint
    # returning an overlapping view of one document is how two screens start disagreeing about it.
    return {**r, "brand": b, "voice": brandprofile.voice_block(b) if b else "",
            "setup": brandprofile.setup_view(b, h, br)}


@app.post("/brand-fields")
def brand_fields_save(payload: dict):
    """Save any subset of the brand profile. `{brand?, …fields}` -> the profile, its voice and readiness.

    Returns the voice block so the form can show what the model will actually be told — the whole point
    of these fields is that they change the output, and a form that cannot show its own effect is asking
    somebody to take that on faith.
    """
    bid = str(payload.get("brand") or payload.get("id") or "")
    data = {k: v for k, v in payload.items() if k not in ("brand", "id")}
    if not data:
        return JSONResponse(status_code=400, content={"detail": "Nothing to save."})
    # Same as the GET: a name is as valid an identifier here as an id, because that is what the screen
    # holds. Without this a save keyed by name created a SECOND profile of the same name.
    if bid and not brandprofile.load(bid):
        byname = brandprofile.by_name(bid)
        bid = byname["id"] if byname else ""
    if not bid and not str(data.get("name") or "").strip():
        active = brandprofile.resolve()
        if not active:
            return JSONResponse(status_code=400, content={
                "detail": "No brand to save against. Give a name, or create the brand first."})
        bid = active["id"]
    b = brandprofile.put(data, bid)
    # `setup` on the save response too, so the form can redraw its own groups without a second call.
    # A save that returns a different shape from the GET is a form that has to guess what changed.
    return {"brand": b, "voice": brandprofile.voice_block(b), "brands": _brand_rows(),
            **brandprofile.readiness(b), "setup": brandprofile.setup_view(b)}


@app.post("/brand-active")
def brand_active(payload: dict):
    """Which brand the studio is working on. Exactly one, so nothing has to guess.

    Needed the moment a second brand exists: with two on file and no brief attached, a screen would
    otherwise lose its grounding entirely — the tool getting worse for using the multi-brand feature.
    """
    b = brandprofile.set_active(str(payload.get("id") or ""))
    if not b:
        return JSONResponse(status_code=404, content={"detail": "No such brand profile."})
    return {"brand": dict(b, voice=brandprofile.voice_block(b)), "brands": _brand_rows(),
            "voice": brandprofile.voice_block(b)}


@app.post("/brand-remove")
def brand_remove(payload: dict):
    ok = brandprofile.remove(str(payload.get("id") or ""))
    return JSONResponse(status_code=200 if ok else 404,
                        content={"ok": ok, "brands": _brand_rows()})


@app.get("/brief-list")
def brief_list(brand: str = ""):
    """Every kept brief, newest first, optionally for one brand. This is the picker's source."""
    return {"briefs": briefstore.briefs(brand), "brands": briefstore.brands()}


@app.get("/brief/{brief_id}")
def brief_get(brief_id: str):
    b = briefstore.load(brief_id)
    if not b:
        return JSONResponse(status_code=404, content={"detail": "No such brief."})
    return {"brief": b, "snapshot": briefstore.snapshot(b), "text": briefstore.as_text(b)}


@app.post("/brief-save")
def brief_save(payload: dict):
    """Keep a brief. Upserts on `id`, so redrafting does not litter the store with near-copies."""
    fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else payload
    # Refuse an empty save. Without this a double-clicked Save draft left a row called "Untitled — brief"
    # with no brand, and three clicks left three — the library filling with rows nobody wrote, which is
    # exactly what makes a picker useless. An existing id is exempt: correcting a saved brief down to
    # nothing is a legitimate edit.
    if not str(payload.get("id") or payload.get("brief_id") or "").strip():
        meaningful = any(str(v).strip() for k, v in (fields or {}).items()
                         if k not in ("status", "format") and not isinstance(v, (dict, list)))
        if not (str(payload.get("brand") or "").strip()
                or str(payload.get("title") or "").strip() or meaningful):
            return JSONResponse(status_code=400,
                                content={"detail": "Nothing to save yet — a brief needs at least a "
                                                   "brand, a title or one filled field."})
    # Accept `id` OR `brief_id` as the upsert key. `/brand-brief-draft` hands back `brief_id`, so a client
    # that echoes the name it was given is doing the obvious thing — and if only `id` were honoured the
    # upsert would silently become an insert and every redraft would leave another near-copy in the
    # library. Taking both costs one line and removes a whole class of duplicate.
    b = briefstore.put(fields, brand=str(payload.get("brand") or ""),
                       title=str(payload.get("title") or ""),
                       fmt=str(payload.get("format") or ""),
                       source=str(payload.get("source") or "saved"),
                       brief_id=str(payload.get("id") or payload.get("brief_id") or ""),
                       # Named once, here, and inherited by the house, the plan and the platform.
                       project=str(payload.get("project") or ""))
    # `brief_id` echoed back under both names for the same reason.
    return {"brief": b, "snapshot": briefstore.snapshot(b), "id": b["id"], "brief_id": b["id"]}


@app.post("/brief-remove")
def brief_remove(payload: dict):
    ok = briefstore.remove(str(payload.get("id") or ""))
    return JSONResponse(status_code=200 if ok else 404,
                        content={"ok": ok, "briefs": briefstore.briefs()})


@app.get("/house/{house_id}")
def house_get(house_id: str):
    h = strategy.load(house_id)
    if not h:
        return JSONResponse(status_code=404, content={"detail": "No such messaging house."})
    # Whether an idea has been tested against this house, and if so, whether the ladder was written
    # again once there was something to write it toward. Composed HERE rather than inside
    # `strategy.status()`, because `ideas.py` already imports `strategy` — `strategy` importing `ideas`
    # back would be circular, and this is the one place both are already in scope safely.
    pl = ideas.for_house(house_id)
    it = ideas.chosen_platform(pl) if pl else None
    claim_state = ("settled" if it.get("ladder_confirmed") else "provisional") if it else None
    return {"house": h, "status": strategy.status(h), "claim_state": claim_state}


@app.post("/house-generate")
def house_generate(payload: dict):
    """Fill one layer with options. Deliberately one layer at a time: generating the whole house at
    once produces something internally consistent and strategically arbitrary, because nothing was
    ever decided — only written."""
    h = strategy.load(str(payload.get("id") or ""))
    if not h:
        return JSONResponse(status_code=404, content={"detail": "No such messaging house."})
    layer = str(payload.get("layer") or "")
    if layer not in strategy.LAYER_BY_ID:
        return JSONResponse(status_code=400, content={"detail": f"Unknown layer {layer!r}."})
    # The same grounding the film gets: approved work to match, corrections already given, and copy
    # that must be placed verbatim.
    brief_text = " ".join(str(v) for v in (h.get("brief") or {}).values())[:2000]
    anchors, _names = learning.anchor_block("strategy", brief_text, 3)
    h, note = strategy.generate(h, layer,
                                extra=str(payload.get("note") or ""),
                                anchors=anchors, rules=learning.rules_block(),
                                locked=library.locked_copy(),
                                replace=bool(payload.get("replace")))
    if note:
        return JSONResponse(status_code=400, content={"detail": note})
    return {"house": h, "status": strategy.status(h)}


@app.post("/house-choose")
def house_choose(payload: dict):
    h = strategy.load(str(payload.get("id") or ""))
    if not h:
        return JSONResponse(status_code=404, content={"detail": "No such messaging house."})
    h = strategy.choose(h, str(payload.get("layer") or ""), payload.get("options") or [])
    return {"house": h, "status": strategy.status(h)}


@app.post("/house-ladder")
def house_ladder(payload: dict):
    """Link a functional truth to an emotional one, or drop a link.

    `{id, f, e, b1?, b2?}` to link · `{id, drop}` to remove. Returns the house status, which carries
    the hydrated paths.

    This is the edge the house never had. Eight layers of truths sat side by side with nothing joining
    them, so nobody could say which fact licensed which feeling — and the campaign that got briefed then
    stood on a leap no layer recorded. Heritage is the live case: its whole house is about process
    (daily checks, cold chain) while the campaign that ran stands on composition (nutrition for a
    developing child), and no part of the system noticed the truth was missing.
    """
    h = strategy.load(str(payload.get("id") or ""))
    if not h:
        return JSONResponse(status_code=404, content={"detail": "No such messaging house."})
    if payload.get("drop"):
        h = strategy.unlink(h, str(payload.get("drop")))
        return {"house": h, "status": strategy.status(h), "detail": "Path removed."}
    # Accepting a drafted path: the bridge arrives as WORDS, not an id, because the rung does not exist
    # yet. Create it and link in one step, or the person does the second half by hand.
    if str(payload.get("bridge_text") or "").strip():
        h2, err = strategy.link_with_bridge(h, str(payload.get("f") or ""), str(payload.get("e") or ""),
                                            str(payload.get("bridge_text")),
                                            str(payload.get("source") or "model"))
        if not h2:
            return JSONResponse(status_code=400, content={"detail": err})
        return {"house": h2, "status": strategy.status(h2),
                "detail": err or "Path recorded, and the bridge added to the house."}
    h2, err = strategy.link(h, str(payload.get("f") or ""), str(payload.get("e") or ""),
                            str(payload.get("b1") or ""), str(payload.get("b2") or ""))
    if not h2:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"house": h2, "status": strategy.status(h2),
            "detail": err or "Path recorded — that feeling now has a fact under it."}


@app.post("/ladder-draft")
def ladder_draft(payload: dict):
    """Candidate ladder paths for somebody to confirm or reject. `{id, n}` → `{paths:[…], note}`.

    Generates the WHOLE TRIPLE — functional truth, bridge, emotional truth — rather than a column of
    bridges. Asking the generic layer generator for bridges alone produced thirty-word rungs that each
    contained both ends and divided into nothing; a bridge means nothing except between two named things.

    Nothing is written. Accept a path with `POST /house-ladder {f, e, bridge_text}`.
    """
    h = strategy.load(str(payload.get("id") or ""))
    if not h:
        return JSONResponse(status_code=404, content={"detail": "No such messaging house."})
    try:
        n = max(2, min(6, int(payload.get("n") or 4)))
    except (TypeError, ValueError):
        n = 4
    paths, note = strategy.draft_ladders(h, n)
    if not paths:
        return JSONResponse(status_code=400, content={"detail": note})
    return {"paths": paths, "note": note,
            "accept_with": "POST /house-ladder {id, f, e, bridge_text}"}


@app.post("/campaign-draft")
def campaign_draft(payload: dict):
    """Draft a campaign from the platform and a ladder path. `{house|set, ladder, shift?}`.

    Returns `{draft:{insight, resolution, shape, frame, slots, why}, note}` — nothing is saved. The
    blank form stays available; this exists because everything a first draft needs has already been
    decided one or two layers up, and asking somebody to retype it is how the copies drift apart.
    """
    pl, _item, why = ideas.resolve(payload, allow_latest=True)
    if not pl:
        return JSONResponse(status_code=404, content={"detail": why})
    h = _platform_house(pl)
    draft, note = campaign_mod.draft(pl, h, str(payload.get("ladder") or ""),
                                     shift=payload.get("shift") or {})
    if not draft:
        return JSONResponse(status_code=400, content={"detail": note})
    return {"draft": draft, "note": note, "set": pl.get("id", ""),
            "save_with": "POST /campaign {…draft fields}"}


@app.post("/campaign")
def campaign_save(payload: dict):
    """Create or update a campaign under the adopted platform. `{house|set, …campaign fields}`.

    A campaign is the time-bound expression of a platform: one route up the ladder, one tension, one
    resolution, between two dates. Stored as a child of the platform so the inheritance is structural
    and a campaign cannot orphan itself from the idea it expresses.

    `{drop}` removes one.
    """
    pl, _item, why = ideas.resolve(payload)
    if not pl:
        return JSONResponse(status_code=404, content={"detail": why})
    h = _platform_house(pl)
    if payload.get("drop"):
        ok = campaign_mod.drop(pl, str(payload.get("drop")))
        return {"ok": ok, "status": campaign_mod.status(pl, h),
                "detail": "Campaign removed." if ok else "No such campaign on this platform."}
    c, err = campaign_mod.save(pl, payload)
    if not c:
        return JSONResponse(status_code=400, content={"detail": err})
    st = campaign_mod.status(pl, h)
    return {"campaign": c, "status": st, "grid": campaign_mod.grid(h, c),
            "axis": campaign_mod.axis(h, c),
            # Returned as a pair with its parent platform, never alone — an idea shown without the
            # territory it expresses gets treated as the strategy, which is how a platform gets
            # quietly replaced by whatever this season's idea was.
            "big_idea": campaign_mod.big_idea(pl, c.get("id", "")),
            "detail": (f"Saved. {len(st['blocking'])} thing(s) still block this campaign."
                       if st["blocking"] else "Saved.")}


@app.get("/campaign")
def campaign_read(house: str = "", set: str = "", id: str = "", execution: str = ""):
    """The campaigns on the adopted platform, the role defaults, the grid and the findings.

    Answers with no arguments, resolving the way every other platform route does. The screen calls it
    bare on load, and a route that demanded a set id would simply never have hydrated.
    """
    pl, _it, why = ideas.resolve({"house": house, "set": set, "execution": execution},
                                 allow_latest=True)
    if not pl:
        return {"platform": "", "count": 0, "campaigns": [], "findings": [],
                "blocking": [], "shapes": campaign_mod.SHAPES,
                "media": list(campaign_mod.MEDIA),
                "role_defaults": {m: {"role": v[0], "why": v[1]}
                                  for m, v in campaign_mod.ROLE_BY_RUNG.items()},
                "grid": campaign_mod.grid(None, None),
                "detail": why or "No platform set for this brand yet."}
    h = _platform_house(pl)
    st = campaign_mod.status(pl, h)
    if id:
        st["campaign"] = campaign_mod.get(pl, id)
        st["grid"] = campaign_mod.grid(h, st["campaign"])
    st["set"] = pl.get("id", "")
    st["house"] = pl.get("house", "")
    return st


@app.get("/campaign-grid")
def campaign_grid(house: str = "", set: str = "", id: str = ""):
    """The campaign on a page: proof axis across, media down. Computed, never stored.

    The axis is read off the bridge on the ladder path — so the grid a campaign gets is decided by the
    house, not invented here. A bridge that does not divide yields one undivided column, and the finding
    beside it says why every execution will then repeat the same evidence.
    """
    pl, _it, why = ideas.resolve({"house": house, "set": set}, allow_latest=True)
    if not pl:
        return JSONResponse(status_code=404, content={"detail": why})
    h = _platform_house(pl)
    c = campaign_mod.get(pl, id)
    if not c:
        return JSONResponse(status_code=404, content={
            "detail": "No campaign on this platform yet."})
    return {"campaign": {k: c.get(k) for k in ("id", "name", "shape", "frame", "insight",
                                               "resolution", "ladder", "from", "to")},
            "grid": campaign_mod.grid(h, c), "axis": campaign_mod.axis(h, c),
            "path": strategy.path(h, c.get("ladder", "")) if h else None,
            "findings": [f for f in campaign_mod.validate(pl, h)
                         if f.get("campaign") in ("", c["id"])]}


@app.get("/jobs")
def jobs(house: str = "", set: str = "", id: str = ""):
    """The jobs table: one row per medium, the role computed and the expression resolved beside it.

    Replaces three screens that asked the same question at three altitudes — the house's
    message-by-medium, the platform's expression-by-medium and the campaign's roles-by-medium. Those
    three vocabularies shared two names out of eight, which is how a house came to say POS material was
    *"roz taaza, roz shakti"* while the platform said it was *"500 checked this before you"*, with only
    the platform's line ever read by a producer.

    **The role explains the expression, in the same row.** A medium carrying a computed role with
    nothing written for it comes back as an empty cell rather than as a screen nobody built — and an
    empty cell is a decision somebody has not taken, which is worth being able to see.

    Runs alongside `/campaign-grid` and the existing expression and role panels rather than replacing
    them: for this phase the same data is visible two ways, so the two can be checked against each
    other. A campaign is optional — without one the roles are the computed defaults, which is the
    honest answer to "what could each medium do for this platform".
    """
    pl, _it, why = ideas.resolve({"house": house, "set": set}, allow_latest=True)
    if not pl:
        return JSONResponse(status_code=404, content={"detail": why})
    h = _platform_house(pl)
    # `get` with no id returns the most recent campaign, so a set with none yields None and the roles
    # come back as the computed defaults — which is the honest answer to "what could each medium do for
    # this platform" before anybody has written a campaign.
    c = campaign_mod.get(pl, id)
    # The plan the campaign points at, so the table can join on the declared medium. Optional: without
    # one the rows still answer "what could each medium do for this platform", which is what they did
    # before the join existed.
    pln = plan_mod.load(str((c or {}).get("plan") or "")) if (c or {}).get("plan") else None
    table = campaign_mod.jobs(h, pl, c, plan=pln)
    return {**table,
            "campaign": ({"id": c.get("id", ""), "name": c.get("name", "")} if c else None),
            "house": ({"id": h.get("id", ""), "brand": h.get("brand", "")} if h else None),
            "taxonomy": media.status()}


@app.get("/shelf")
def shelf_status(house: str = "", brief: str = ""):
    """The seven inputs, and how much of the shelf is actually filled.

    An input is something somebody went and found out; a decision is something somebody argued for. The
    product has been treating both as the same kind of work, which is why *"500 dairy professionals
    check the milk every single day"* — a fact — arrives on screen as one option among five rephrasings
    of itself, each carrying its own source flag.

    Read-only, and it stores nothing. Two of the seven come back `available: false` with a sentence
    saying what would fill them, and one (`trade_econ`) does not exist anywhere yet — which is exactly
    why the trade expression currently asserts an argument about the shopkeeper's arithmetic with
    nothing behind it.
    """
    h = strategy.load(house) if house else None
    b = briefstore.load(brief) if brief else None
    if not h:
        prof = brandprofile.resolve() or {}
        h = strategy.newest_for(str(prof.get("name") or prof.get("brand") or ""))
    return shelf.status(house=h, b=b)


@app.post("/house-option")
def house_option(payload: dict):
    """Add or drop a line by hand. A person's own words count as sourced — they are the evidence."""
    h = strategy.load(str(payload.get("id") or ""))
    if not h:
        return JSONResponse(status_code=404, content={"detail": "No such messaging house."})
    layer = str(payload.get("layer") or "")
    if layer not in strategy.LAYER_BY_ID:
        return JSONResponse(status_code=400, content={"detail": f"Unknown layer {layer!r}."})
    if payload.get("drop"):
        h = strategy.drop_option(h, layer, str(payload.get("drop")))
    elif payload.get("option_id") or payload.get("option"):
        # Upsert on an existing id. Without this, an edit applied in the client and was never
        # stored — the field changed on screen, the reload put the old text back, and nothing said so.
        #
        # Two names for one thing, and both are honoured on purpose. `option` is what this route
        # shipped with and nothing ever called it; `option_id` is what the house sheet sends, and it
        # is the better name because `drop` next to it also takes an id. Reading only one of them is
        # worse than it looks: an unrecognised key does not fail, it falls through to the add branch
        # below, so an edit becomes a SECOND line and the screen shows the new text as though it had
        # worked. Silent duplication is the failure mode this route exists to prevent.
        edited = strategy.edit_option(h, layer, str(payload.get("option_id") or payload.get("option")),
                                      text=payload.get("text"), note=payload.get("note"),
                                      tag=payload.get("tag"))
        if edited is None:
            return JSONResponse(status_code=404,
                                content={"detail": "No such option — it may have been dropped."})
        h = edited
    else:
        text = str(payload.get("text") or "").strip()
        if not text:
            return JSONResponse(status_code=400, content={"detail": "Nothing to add."})
        h = strategy.add_option(h, layer, text, note=str(payload.get("note") or ""),
                                source="user", tag=str(payload.get("tag") or ""))
    return {"house": h, "status": strategy.status(h)}


@app.get("/house-prompt/{house_id}/{layer}")
def house_prompt(house_id: str, layer: str):
    """Exactly what would be sent for this layer. Inspectable on purpose — a strategy tool that
    cannot show its own instructions is asking to be trusted rather than checked."""
    h = strategy.load(house_id)
    if not h or layer not in strategy.LAYER_BY_ID:
        return JSONResponse(status_code=404, content={"detail": "Not found."})
    return {"prompt": strategy.prompt_for(h, layer, locked=library.locked_copy())}


# =====================================================================================
# Communication plan — bound to a messaging house, and answerable to it
# =====================================================================================

def _house_for(p: dict):
    return strategy.load(p.get("house") or "") if p.get("house") else None


@app.get("/plans")
def plans_list():
    return {"plans": plan.plans(), "layers": plan.LAYERS, "roles": plan.ROLES,
            "sides": list(plan.SIDES), "default_brand_share": plan.DEFAULT_BRAND_SHARE,
            "caveat": strategy.ROUND_TRIP_CAVEAT,
            "downloads": {"record": "/plan-docx/{id}", "worksheet": "/plan-docx/{id}?mode=worksheet"}}


@app.post("/plan-new")
def plan_new(payload: dict):
    """A plan takes **both** the brief and the house — the brief for what the business needs, the house
    for what may be said. Without a house the proof gate cannot run, and it says so.

    When the plan's brief and the house's brief are different documents, that is recorded rather than
    resolved. It is usually a mistake and occasionally deliberate, and the two cases look identical from
    here — so it becomes a finding a person answers instead of a silent choice made for them.
    """
    house_id = str(payload.get("house") or "")
    h = strategy.load(house_id) if house_id else None
    b = briefstore.resolve(payload.get("brief")) or (
        briefstore.load((h or {}).get("brief_id") or "") if h else None)
    brand = str(payload.get("brand") or "").strip() or (b or {}).get("brand") \
        or (h or {}).get("brand") or "Brand"
    p = plan.new_plan(brand, house_id)
    if b and b.get("id"):
        p["brief_id"] = b["id"]
        p["brief_title"] = b.get("title", "")
        p = plan.save(p)
    return {"plan": p, "status": plan.status(p, h),
            "brief": briefstore.snapshot(b) if b else None}


@app.get("/plan/{plan_id}")
def plan_get(plan_id: str):
    p = plan.load(plan_id)
    if not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    return {"plan": p, "status": plan.status(p, _house_for(p))}


@app.post("/plan-generate")
def plan_generate(payload: dict):
    p = plan.load(str(payload.get("id") or ""))
    if not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    layer = str(payload.get("layer") or "")
    if layer not in plan.LAYER_BY_ID:
        return JSONResponse(status_code=400, content={"detail": f"Unknown layer {layer!r}."})
    house = _house_for(p)
    brief = " ".join(str(v) for v in ((house or {}).get("brief") or {}).values())[:2000]
    anchors, _n = learning.anchor_block("plan", brief, 3)
    p, note = plan.generate(p, layer, house=house, extra=str(payload.get("note") or ""),
                            anchors=anchors, rules=learning.rules_block(),
                            locked=library.locked_copy(),
                            replace=bool(payload.get("replace")))
    if note:
        return JSONResponse(status_code=400, content={"detail": note})
    return {"plan": p, "status": plan.status(p, house)}


def _locked_refusal(p: dict):
    """409 while a plan is pending approval — the freeze `plan.is_locked` exists to enforce. One
    helper, called from every mutating plan route, rather than four copies of the same check."""
    if plan.is_locked(p):
        pa = p.get("pending_approval") or {}
        return JSONResponse(status_code=409, content={
            "detail": f"This plan is pending approval ({pa.get('title', 'an approver')}) — no edits "
                     f"until it is approved or rejected back to draft."})
    return None


@app.post("/plan-row")
def plan_row(payload: dict):
    """Add or drop one row by hand. A person's own row counts as sourced — they are the evidence."""
    p = plan.load(str(payload.get("id") or ""))
    if not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    refused = _locked_refusal(p)
    if refused:
        return refused
    layer = str(payload.get("layer") or "")
    if layer not in plan.LAYER_BY_ID:
        return JSONResponse(status_code=400, content={"detail": f"Unknown layer {layer!r}."})
    if payload.get("drop"):
        p = plan.drop_row(p, layer, str(payload.get("drop")))
    elif isinstance(payload.get("row"), dict):
        row = payload["row"]
        # The client sends the row's own id when a cell was edited. An add and an edit arrive on the
        # same endpoint, so the id is what tells them apart — without the upsert every cell edit was
        # applied on screen and thrown away, which is the quietest way to lose someone's work.
        row_id = str(row.get("id") or "")
        if row_id:
            edited = plan.edit_row(p, layer, row_id, row)
            if edited is None:
                return JSONResponse(status_code=404,
                                    content={"detail": "No such row — it may have been dropped."})
            p = edited
        else:
            p = plan.add_row(p, layer, row, source="user")
    else:
        return JSONResponse(status_code=400, content={"detail": "Nothing to add or drop."})
    return {"plan": p, "status": plan.status(p, _house_for(p))}


@app.post("/plan-balance")
def plan_balance(payload: dict):
    """Set the brand/activation split. Yours to change; moving off the default asks for a reason."""
    p = plan.load(str(payload.get("id") or ""))
    if not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    refused = _locked_refusal(p)
    if refused:
        return refused
    p = plan.set_balance(p, int(payload.get("brand_share") or plan.DEFAULT_BRAND_SHARE),
                         str(payload.get("reason") or ""), str(payload.get("basis") or "year"))
    return {"plan": p, "status": plan.status(p, _house_for(p))}


@app.post("/plan-geography")
def plan_geography(payload: dict):
    """Replace the plan's priority-geography selection and return the recomputed reach in one call —
    same "resend the whole list" shape as the picker itself, see `plan.set_geography`'s own docstring."""
    p = plan.load(str(payload.get("id") or ""))
    if not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    refused = _locked_refusal(p)
    if refused:
        return refused
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return JSONResponse(status_code=400, content={"detail": "rows must be a list."})
    p = plan.set_geography(p, rows)
    return {"plan": p, "status": plan.status(p, _house_for(p))}


def _brand_for(p: dict) -> dict | None:
    b = str(p.get("brand") or "")
    return brandprofile.load(b) or brandprofile.by_name(b) if b else None


@app.post("/plan-submit-approval")
def plan_submit_approval(payload: dict):
    """Send the plan to its brand's first approval level. See `plan.submit_for_approval`'s own note
    on what this freeze does and does not enforce."""
    p = plan.load(str(payload.get("id") or ""))
    if not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    b = _brand_for(p)
    hierarchy = brandprofile.approval_hierarchy(b) if b else []
    p, err = plan.submit_for_approval(p, hierarchy, str(payload.get("who") or "Someone"))
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"plan": p, "status": plan.status(p, _house_for(p))}


@app.post("/plan-approve")
def plan_approve(payload: dict, db: Session = Depends(get_db)):
    """Approve at the plan's current pending level. `user_id` is checked against that level's real
    primary/backup assignment — see `plan.approve`'s own note on what this gate is and is not."""
    p = plan.load(str(payload.get("id") or ""))
    if not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    b = _brand_for(p)
    hierarchy = brandprofile.approval_hierarchy(b) if b else []
    user_id = str(payload.get("user_id") or "")
    u = people.get(db, user_id)
    p, err = plan.approve(p, hierarchy, user_id, u.name if u else "")
    if err:
        return JSONResponse(status_code=403, content={"detail": err})
    return {"plan": p, "status": plan.status(p, _house_for(p))}


@app.post("/plan-reject")
def plan_reject(payload: dict, db: Session = Depends(get_db)):
    """Send it back to draft. Requires a reason — see `plan.reject`'s own note."""
    p = plan.load(str(payload.get("id") or ""))
    if not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    user_id = str(payload.get("user_id") or "")
    u = people.get(db, user_id)
    p, err = plan.reject(p, user_id, u.name if u else "", str(payload.get("reason") or ""))
    if err:
        return JSONResponse(status_code=403, content={"detail": err})
    return {"plan": p, "status": plan.status(p, _house_for(p))}


@app.get("/people")
def people_list(db: Session = Depends(get_db)):
    """The user directory + org chart, for the approval-hierarchy picker and admin screen."""
    return {"people": [people.snapshot(u) for u in people.list_users(db)],
            "org_chart": people.org_chart(db)}


@app.post("/brand-approval-hierarchy")
def brand_approval_hierarchy_set(payload: dict):
    """Replace one brand's whole approval hierarchy — see `brandprofile.set_approval_hierarchy`'s own
    docstring on why this is a whole-list replace, not a per-level endpoint."""
    b = brandprofile.load(str(payload.get("brand_id") or ""))
    if not b:
        return JSONResponse(status_code=404, content={"detail": "No such brand profile."})
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return JSONResponse(status_code=400, content={"detail": "rows must be a list."})
    b = brandprofile.set_approval_hierarchy(b, rows)
    return {"brand": b, "approval_hierarchy": brandprofile.approval_hierarchy(b)}


# =====================================================================================
# Idea platforms — the layer between a settled message and six kinds of work
#
# Lives beside the messaging house rather than in Plan or Execution: a platform is built from the house's
# core message and pillars and has no plan dependency at all, and putting it inside Execution would make
# it look per-execution — which is the exact incoherence it exists to prevent.
# =====================================================================================

def _platform_house(pl: dict):
    return strategy.load(pl.get("house") or "") if pl.get("house") else None


@app.get("/idea-platform-sets")
def platforms_list(house: str = ""):
    # Not `/platforms`: that path already means the SOCIAL platforms in `catalog.PLATFORMS`, registered
    # far earlier in this file, so this one never ran. Two meanings for one word — social platform, idea
    # platform — became two meanings for one path, and the newer one lost silently.
    return {"sets": ideas.sets(house), "expressions": ideas.EXPRESSIONS,
            "min_media": ideas.MIN_MEDIA, "min_platforms": ideas.MIN_PLATFORMS,
            "optional": True,
            "why": ("Optional. Without one, every execution invents its own creative idea and the film, "
                    "the shelf strip and the promoter's line come back looking like three campaigns.")}


@app.get("/platforms-for/{house_id}")
def platforms_for_house(house_id: str):
    """The set belonging to a house, or an honest empty with the reason it cannot start yet."""
    h = strategy.load(house_id)
    if not h:
        return JSONResponse(status_code=404, content={"detail": "No such messaging house."})
    pl = ideas.for_house(house_id)
    ok, why = ideas.ready(h)
    if not pl:
        return {"set": None, "status": None, "ready": ok, "blocked_because": why,
                "basis": ideas.house_basis(h)}
    return {"set": pl, "status": ideas.status(pl, h), "ready": ok, "blocked_because": why}


@app.post("/platform-new")
def platform_new(payload: dict):
    h = strategy.load(str(payload.get("house") or ""))
    if not h:
        return JSONResponse(status_code=404, content={"detail": "No such messaging house."})
    existing = ideas.for_house(h["id"])
    if existing:
        return {"set": existing, "status": ideas.status(existing, h)}
    pl = ideas.new_set(str(payload.get("brand") or h.get("brand") or "Brand"), h["id"])
    return {"set": pl, "status": ideas.status(pl, h)}


@app.post("/platform-generate")
def platform_generate(payload: dict):
    """Two different calls on one endpoint.

    Without `build_on`: fresh bets, told what is already on the table and required to go elsewhere.
    With `build_on`: developments of that one platform, keeping its idea recognisable.

    Neither replaces anything. A discarded round is often where somebody finds the thing they actually
    wanted, and a tool that silently overwrites teaches people to stop exploring.
    """
    pl = ideas.load(str(payload.get("id") or ""))
    if not pl:
        return JSONResponse(status_code=404, content={"detail": "No such platform set."})
    h = _platform_house(pl)
    brief = " ".join(str(v) for v in ((h or {}).get("brief") or {}).values())[:2000]
    anchors, _n = learning.anchor_block("platform", brief, 3)
    pl, note = ideas.generate(pl, h,
                                 build_from_id=str(payload.get("build_on") or ""),
                                 n=max(1, min(5, int(payload.get("n") or 3))),
                                 extra=str(payload.get("note") or ""),
                                 anchors=anchors, rules=learning.rules_block())
    if note:
        return JSONResponse(status_code=400, content={"detail": note})
    return {"set": pl, "status": ideas.status(pl, h)}


@app.post("/platform-item")
def platform_item(payload: dict):
    """Add, edit or drop one platform by hand. A hand-written platform counts as sourced — the author
    is the evidence for it, and this is where the good ones usually come from."""
    pl = ideas.load(str(payload.get("id") or ""))
    if not pl:
        return JSONResponse(status_code=404, content={"detail": "No such platform set."})
    h = _platform_house(pl)
    if payload.get("drop"):
        pl = ideas.drop(pl, str(payload.get("drop")))
    elif payload.get("item"):
        edited = ideas.edit(pl, str(payload.get("item")), payload)
        if edited is None:
            return JSONResponse(status_code=404, content={"detail": "No such platform."})
        pl = edited
    else:
        if not str(payload.get("idea") or "").strip():
            return JSONResponse(status_code=400,
                                content={"detail": "Write the idea — one sentence is enough to start."})
        pl = ideas.add(pl, payload, source="user")
    return {"set": pl, "status": ideas.status(pl, h)}


@app.post("/platform-express")
def platform_express(payload: dict):
    """What the platform becomes in each medium, as a person wrote it. The execution inherits this.

    Two shapes, because there are two ways a person edits these:

        { kind, text }              one slot, on blur
        { expressions:{k:v, …} }    several, debounced — one save rather than five racing

    Five separate saves is not a tidiness problem: each one writes a whole copy of the set, so the last
    response to land wins carrying a version that predates the other four, and four edits vanish.

    A key present with an empty value clears that slot. Somebody deleting an expression means it.

    Resolves the set the way its two siblings do — `set`, `house`, or the set holding `item` — because the
    screen holds the platform's id and often has no set id at all. `id` is still read as the set id for
    callers written against the older shape.
    """
    pl, item, why = ideas.resolve({**payload, "set": payload.get("set") or payload.get("id")})
    if not item:
        return JSONResponse(status_code=404 if not pl else 400, content={"detail": why})
    mapping = payload.get("expressions")
    if isinstance(mapping, dict):
        out, err = ideas.express_many(pl, item, {str(k): v for k, v in mapping.items()})
    else:
        out, err = ideas.express(pl, item, str(payload.get("kind") or ""),
                                 str(payload.get("text") or ""))
    if err or out is None:
        return JSONResponse(status_code=400 if err else 404,
                            content={"detail": err or "No such platform."})
    return {"set": out, "item": item, "saved": True,
            "status": ideas.status(out, _platform_house(out))}


@app.post("/platform-choose")
def platform_choose(payload: dict):
    """One platform leads. Two chosen is none chosen — the coherence comes from there being one."""
    pl = ideas.load(str(payload.get("id") or ""))
    if not pl:
        return JSONResponse(status_code=404, content={"detail": "No such platform set."})
    pl = ideas.choose(pl, str(payload.get("item") or ""))
    return {"set": pl, "status": ideas.status(pl, _platform_house(pl))}


@app.get("/platform-prompt/{set_id}")
def platform_prompt(set_id: str, build_on: str = ""):
    pl = ideas.load(set_id)
    if not pl:
        return JSONResponse(status_code=404, content={"detail": "Not found."})
    h = _platform_house(pl)
    src = next((x for x in pl["platforms"] if x["id"] == build_on), None) if build_on else None
    return {"prompt": ideas.prompt_for(pl, h, src)}


@app.post("/idea-draft")
def idea_draft(payload: dict):
    """Draft platforms from the messaging house's core message and the pulled brief.

    `{ house, core, brief:{title, proposition, audience, objective}, n, build_on }`

    **Opens with three, not one.** Three that differ in kind make the choice visible; one draft becomes
    the answer by being the only thing on the page, and there is no way to tell a strong platform from a
    lonely one.

    Returns `{ options:[…], count, build_on }` — plus the first option's fields flat and under `idea`, so
    a client written against the single-draft shape keeps working unchanged and simply shows the first of
    the three.

    `build_on: "<item id>"` develops an existing platform in this house's set instead of opening fresh
    ones. Each result carries `built_from`, so an iteration is distinguishable from a re-roll and the
    history of the idea survives. That is the difference between the two motions asked for — iterate the
    one you have, and generate genuinely fresh alternatives.

    Nothing is saved. A draft is a starting point that a person then edits and adopts through
    `/idea-platform`, where editing re-sources it from `model` to `user`. A draft nobody rewrites stays
    visibly the model's, which is the whole point of the five tests underneath it.
    """
    house_id = str(payload.get("house") or "")
    h = strategy.load(house_id) if house_id else None
    core = str(payload.get("core") or "")
    if h and not core:
        # Trust the house over the posted string: the client sends what it last read, and the chosen core
        # may have moved since.
        core = "; ".join(strategy._chosen_text(h, "core"))
    brief = payload.get("brief") if isinstance(payload.get("brief"), dict) else None
    try:
        n = max(1, min(6, int(payload.get("n") or 3)))
    except (TypeError, ValueError):
        n = 3

    # Iterating on one that already exists — look it up in this house's set, or accept it inline for a
    # draft the client is holding but has not adopted.
    # `build_on` arrives as an id when the server holds the platform, or as the whole object when the
    # screen is holding a draft nobody has adopted. `from_client` takes either, and searches both the
    # platform sets and the individual platforms inside them.
    raw = payload.get("build_on") or payload.get("build_from")
    src = ideas.from_client(raw)
    build_on = (raw if isinstance(raw, str) else str((raw or {}).get("id") or "inline")) if raw else ""
    if raw and not src:
        if isinstance(raw, str):
            return JSONResponse(status_code=404, content={
                "detail": "No such platform to build on — it may have been dropped. Try again for "
                          "fresh routes instead."})
        # An object with neither a name nor a line is nothing to build on. Say so rather than quietly
        # generating fresh routes, which would make Build-on-this indistinguishable from Try-again —
        # the exact ambiguity the two controls exist to remove.
        return JSONResponse(status_code=400, content={
            "detail": "Nothing to build on — the platform sent had no line."})

    # What the person asks for on this round — "sharper", "go at the enemy", "none of these, try the
    # trade angle". Rounds after the first are where a platform actually gets found, and until now every
    # round was identical to the first with no way to say what was wrong with it.
    steer = str(payload.get("steer") or payload.get("note") or "")
    options, note = ideas.draft_lines(core=core, brief=brief, house=h, n=n, build_from=src, steer=steer)
    if note:
        return JSONResponse(status_code=400, content={"detail": note})
    # Remember what this round was told to do differently. The screen keeps it in state so the box stays
    # filled between rounds, which is right — but state does not survive a reload, and the steer is the
    # only record of why round four looks nothing like round one.
    if steer.strip() and house_id:
        existing = ideas.for_house(house_id)
        if existing:
            ideas.set_steer(existing, steer)
    first = options[0]
    return {**first, "idea": first, "options": options, "count": len(options),
            "build_on": build_on, "building_on": src or None}


@app.post("/platform-express-draft")
def platform_express_draft(payload: dict):
    """DRAFT what the platform becomes in each medium. `{house|set, item?, media?, steer?}`.

    Named `-draft` because `POST /platform-express` already exists and STORES one expression a person
    wrote. Registering a second handler on that path would have replaced the setter silently — the same
    shadowing that has bitten this file three times. Writing and storing are different verbs.

    The five expression slots could only be typed into. The platform and the house already decide most of
    what each medium has to become, so making somebody derive all five by hand from a blank box was
    asking them to do the work the studio is for. Generated, then editable — same as everywhere else.
    """
    pl, item, why = ideas.resolve(payload)
    if not item:
        return JSONResponse(status_code=404 if not pl else 400, content={"detail": why})
    h = _platform_house(pl)
    media = payload.get("media") if isinstance(payload.get("media"), list) else None
    out, note = ideas.write_expressions(pl, item, h, media, str(payload.get("steer") or ""))
    if not out:
        return JSONResponse(status_code=400, content={"detail": note})
    updated, err = ideas.express_many(pl, item, out)       # one save, not five racing each other
    if updated:
        pl = updated
    elif err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"expressions": out, "set": ideas.as_read(pl, h), "item": item, "note": note,
            "status": ideas.status(pl, h),
            "detail": f"Written for {len(out)} medium(s). Every one is editable — rewriting it makes it "
                      f"yours."}


@app.post("/platform-judge")
def platform_judge(payload: dict):
    """A model's verdict on the five tests. `{house|set, item?}` -> `{judged:{…}}`.

    **Kept apart from the person's verdicts.** The five tests are judgements somebody has to own; a model
    verdict that overwrote theirs would turn the layer into a checkbox. This writes `judged`, the person
    writes `verdicts`, and where they disagree the screen shows both — the disagreement is the useful
    signal, not something to resolve automatically.
    """
    pl, item, why = ideas.resolve(payload)
    if not item:
        return JSONResponse(status_code=404 if not pl else 400, content={"detail": why})
    h = _platform_house(pl)
    out, note = ideas.judge(pl, item, h)
    if not out:
        return JSONResponse(status_code=400, content={"detail": note})
    it = None
    for x in pl.get("platforms", []):
        if x["id"] == item:
            x["judged"] = out
            it = x
    ideas.save(pl)
    disagree = ideas.disagreements(it)
    return {"judged": out, "questions": ideas.JUDGED, "ask": ideas.JUDGED_ASK,
            "why": ideas.JUDGED_WHY, "disagreements": disagree, "item": item,
            "status": ideas.status(pl, h),
            "detail": (f"The model disagrees with you on {len(disagree)}: {', '.join(disagree)}. "
                       f"That is the part worth reading." if disagree else
                       "A first reading. Yours is the one that counts — answer them yourself beside it.")}


@app.get("/idea-platform")
def idea_platform_get(house: str = "", id: str = ""):
    """Hydrate the Idea platform tab: `{name, line, tests, routes, judged, pillar, rtb, brief, source…}`.

    Same keys whether or not anything has been adopted, so the screen has one code path. `source` is
    honoured on the way back out — a drafted line read from the server still shows as the model's until
    somebody edits it, which is the whole reason the field is stored rather than inferred.

    The client treats anything unsaved on screen as winning, so this can be called on entering the tab
    without any risk of overwriting a sentence somebody is mid-way through.

    **Answers with no arguments at all.** The screen calls this as a bare `GET /idea-platform`, and with
    neither `house` nor `id` this used to resolve nothing and report `exists: false` — so hydration never
    once ran, and a platform that was safely on disk came back to a blank screen. That is the same
    "everything I did is gone" the plan screen was reported for, arrived at a different way. A read with
    nothing specified falls back to the most recently updated set, which is the one somebody was working
    on; `resolved_by` says which route was taken so the screen can show whose platform it is opening.
    """
    # `id` may name the set or the platform inside it. The screen holds the platform's id — that is what
    # it sends everywhere else — so reading it as a set id only meant `?id=` resolved nothing and fell
    # through to the `latest` guess. A guess is fine when nothing was specified and wrong when something
    # was: with two brands in one tenant it opens the other one's platform.
    pl = (ideas.load(id) or ideas.set_for_item(id)) if id else ideas.for_house(house)
    by = ("id" if (id and pl) else "house" if pl else "")
    if not pl:
        pl = ideas.latest()
        by = "latest" if pl else ""
    if not pl:
        return {**ideas.as_read(None), "exists": False, "resolved_by": ""}
    h = _platform_house(pl)
    return {**ideas.as_read(pl, h), "exists": True, "resolved_by": by, "status": ideas.status(pl, h)}


@app.post("/idea-platform")
def idea_platform(payload: dict):
    """Adopt the platform written on the Idea Platform screen.

    The screen's five tests are judgements a person makes with a written reason. They are stored
    **verbatim and never recomputed** — the mechanical tests in `ideas.py` stay available beside them as
    advice, because a judgement with a reason attached is worth more than a keyword match, and
    overwriting somebody's "holds, because…" with a scanner's opinion would throw away the point of the
    layer.

    `{ house, plan, name, line, tests:{key:{verdict,note}}, routes:{key:text} }`
    `{ house, skipped:true }` records the skip — a decision, not a UI preference.
    `{ house, confirm_ladder:true }` records the return trip to the ladder — see `set_ladder_confirmed`.
    """
    house_id = str(payload.get("house") or "")
    h = strategy.load(house_id) if house_id else None
    if not h:
        return JSONResponse(status_code=404,
                            content={"detail": "No messaging house — a platform stands on one."})
    pl = ideas.for_house(house_id) or ideas.new_set(
        str(payload.get("brand") or h.get("brand") or "Brand"), house_id)

    # A body carrying only `skipped` is the skip toggle. One that also carries a line is an adoption that
    # happens to record a skip decision too — `adopt()` handles that, so it must not be short-circuited
    # here or the platform would be thrown away by the toggle.
    if "skipped" in payload and not str(payload.get("line") or payload.get("idea") or "").strip():
        pl = ideas.set_skipped(pl, bool(payload.get("skipped")))
        return {"ok": True, "skipped": pl.get("skipped", False), "set": pl,
                **ideas.as_read(pl, h), "status": ideas.status(pl, h)}

    # Same shape of short-circuit, for the return trip. `confirm_ladder` alone is a person saying "I have
    # been back to the ladder", not a rewrite of the platform — it must not require re-sending the whole
    # form, or the two actions (confirm, and edit-then-adopt) collapse into needing the same payload.
    if "confirm_ladder" in payload and not str(payload.get("line") or payload.get("idea") or "").strip():
        pl2, err = ideas.set_ladder_confirmed(pl, bool(payload.get("confirm_ladder")))
        if not pl2:
            return JSONResponse(status_code=400, content={"detail": err})
        pl = pl2
        return {"ok": True, "set": pl, **ideas.as_read(pl, h), "status": ideas.status(pl, h)}

    if not str(payload.get("line") or payload.get("idea") or "").strip():
        return JSONResponse(status_code=400,
                            content={"detail": "Write the platform in one sentence first — the tests "
                                               "have nothing to test otherwise."})
    pl = ideas.adopt(pl, payload)
    return {"ok": True, "set": pl, "status": ideas.status(pl, h),
            "platform": ideas.chosen_platform(pl), **ideas.as_read(pl, h)}


# =====================================================================================
# The shoot - one shot list, from planning to the compositor's gate.
#
# `shotlist.py` used to own this half and `shots.py` the other, which meant two stores, two findings
# lists and two ideas of what a shot is. One planned a shoot and logged takes by number; the other
# attached footage and put a signature against it. They are the same object at different points in its
# life, and the screen could only ever see one of them. Folded into `shots.py`.
#
#   planned -> briefed -> shot -> selected -> signed -> the compositor
#              (ref)      (takes) (a keeper)  (a name)
# =====================================================================================

@app.get("/shotlist")
def shotlist_get(execution: str = ""):
    """The whole shoot for one execution. `list` is kept as a key for callers that read it."""
    st = shots.status(execution)
    return {"list": {"execution": execution or None, "shots": st["shots"]}, "status": st}


@app.post("/shots-plan")
def shots_plan(payload: dict):
    """Derive a first shot list from the approved script, or from the idea platform's routes.

    Nothing is invented - talent, location and length come back empty because nobody has decided them.
    An empty cell that says so beats a plausible one somebody has to check, and a fabricated location on
    a call sheet sends a crew to the wrong place.
    """
    ex = str(payload.get("execution") or "")
    if shots.items(ex):
        st = shots.status(ex)
        return {"shots": st["shots"], "status": st,
                "detail": "This shoot already has shots - they were kept."}
    rows = shots.plan_from(payload.get("script"), payload.get("idea"), ex)
    if not rows:
        return JSONResponse(status_code=400,
                            content={"detail": "Nothing to plan from. Approve a script, or write the "
                                               "platform's routes first."})
    st = shots.status(ex)
    return {"shots": st["shots"], "status": st,
            "detail": f"{len(rows)} shot(s) planned from "
                      f"{'the approved script' if payload.get('script') else 'the idea platform'}."}


@app.post("/shot-row")
def shot_row(payload: dict):
    """Upsert one row on `shot.id`, or drop it with `{drop}`. Also accepts flat fields.

    Only the planned columns. The take, the still and the signature each have their own door, so a table
    edit can never quietly approve footage.
    """
    ex = str(payload.get("execution") or "")
    if payload.get("drop"):
        if not shots.remove(str(payload.get("drop"))):
            return JSONResponse(status_code=404, content={"detail": "No such shot."})
    else:
        shot = payload.get("shot") if isinstance(payload.get("shot"), dict) else payload
        sid = str(shot.get("id") or "")
        if sid:
            if not shots.update(sid, shot):
                return JSONResponse(status_code=404, content={"detail": "No such shot."})
        elif any(str(shot.get(f) or "").strip() for f in shots.PLAN_FIELDS):
            shots.add(ex, **{k: v for k, v in shot.items() if k != "execution"})
        else:
            return JSONResponse(status_code=400, content={"detail": "Nothing to add or drop."})
    st = shots.status(ex)
    return {"list": {"execution": ex or None, "shots": st["shots"]}, "shots": st["shots"], "status": st}


@app.post("/shot-reference")
def shot_reference(payload: dict):
    """A reference frame for one shot - what it should look like, for the crew.

    Explicitly a *reference*, not the shot: this screen films real footage, and an image generated here
    is a mood board entry. It is not admissible to the library and never becomes a take.
    """
    sid = str(payload.get("id") or "")
    row = shots.get(sid) or {}
    subject = " ".join(x for x in (str(payload.get("slug") or row.get("slug") or ""),
                                   str(payload.get("action") or row.get("action") or "")) if x).strip()
    if not subject:
        return JSONResponse(status_code=400,
                            content={"detail": "Write what happens in the shot first."})
    try:
        res = scene_still({"prompt": subject, "ratio": payload.get("ratio") or "16:9",
                           "style": payload.get("style") or "real"})
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    if isinstance(res, JSONResponse):
        return res
    url = (res or {}).get("image_url") or ""
    if not url:
        return JSONResponse(status_code=502, content={"detail": "No reference came back."})
    out = shots.set_reference(sid, url)
    ex = (out or {}).get("execution") or ""
    st = shots.status(ex)
    return {"url": url, "shot": out, "list": {"execution": ex or None, "shots": st["shots"]},
            "status": st,
            "detail": "A reference for the crew to match. It is not a take and cannot be signed off."}


@app.post("/shot-take")
def shot_take(payload: dict):
    """Log that a take was shot. `{id, take?, url?}` -> the take number.

    `url` is optional: a take gets logged on set long before the file is near this machine, and a log
    that refuses to record what happened until the footage arrives is a log nobody keeps.
    """
    out, n = shots.log_take(str(payload.get("id") or ""), payload.get("take"),
                            str(payload.get("url") or ""))
    if out is None:
        return JSONResponse(status_code=404, content={"detail": "No such shot."})
    ex = out.get("execution") or ""
    st = shots.status(ex)
    return {"take": n, "shot": out, "list": {"execution": ex or None, "shots": st["shots"]},
            "status": st, "detail": f"Take {n} logged."}


@app.post("/shot-select")
def shot_select(payload: dict):
    """Choose the take that will be used. `{id, take?}`.

    A shot with no logged take cannot be selected - selecting footage nobody recorded is how a cut ends
    up referencing something that does not exist. Selecting a different take clears the signature.
    """
    out, err = shots.select_take(str(payload.get("id") or ""), payload.get("take"))
    if out is None:
        return JSONResponse(status_code=404 if err == "No such shot." else 400,
                            content={"detail": err})
    ex = out.get("execution") or ""
    st = shots.status(ex)
    return {"shot": out, "list": {"execution": ex or None, "shots": st["shots"]}, "status": st,
            "detail": f"Take {out.get('selected_take')} selected."}


@app.post("/shots-callsheet")
def shots_callsheet(payload: dict):
    """The shot list as a .docx call sheet. Nothing is filled in: unknowns print as unknowns.

    `idea` is `{name, line}`. An empty `name` is not an error - a platform can be written as a line
    before anyone names it, and a shoot can happen with no platform at all.
    """
    idea = payload.get("idea")
    if isinstance(idea, str):
        idea = {"name": "", "line": idea}
    rows = payload.get("shots")
    if not rows:
        rows = shots.items(str(payload.get("execution") or ""))
    try:
        out = docs.build_callsheet_docx(rows or [], idea or {})
    except Exception as e:
        raise HTTPException(500, f"Call sheet build failed: {e}")
    return FileResponse(out, filename="Call_sheet.docx", media_type=_DOCX)


@app.post("/shots-handoff")
def shots_handoff(payload: dict):
    """Hand the signed takes to the compositor. Refuses anything unsigned.

    The gate is the point: a signature is the only thing standing between footage of a real person and a
    delivered master, so an unsigned shot cannot be handed over even when it is named explicitly.
    """
    ex = str(payload.get("execution") or "")
    ids = [str(x) for x in (payload.get("shots") or [])]
    rows, err = shots.handoff(ex, ids or None)
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    st = shots.status(ex)
    return {"handed": len(rows), "shots": rows, "status": st,
            "detail": f"{len(rows)} signed take(s) handed to the compositor."}

# =====================================================================================
# Sales enabler — the trade sheet, and the enabler the field carries
#
# Deliberately NOT a kind inside the execution envelope. Every other execution is briefed from one
# audience row and one channel row; a trade plan is briefed from the whole route to market at once,
# because channel conflict is invisible unless every channel sits in one view.
# =====================================================================================

def _sales_sheet(payload: dict) -> dict:
    """Resolve the sheet being edited, creating one if this is the first touch.

    The built UI holds its trade briefs locally and posts `{channel, element, brief}` with no sheet id.
    Rather than make it 501 until the client is changed, an id-less call lands on the most recently
    updated sheet, or opens one bound to the newest plan. Passing `id` always wins, so the id-based flow
    works today and the bridge can be removed without touching the backend.
    """
    sid = str(payload.get("id") or "")
    if sid:
        s = sales.load(sid)
        if s:
            return s
    existing = sales.sheets()
    if existing:
        newest = max(existing, key=lambda x: x.get("updated", ""))
        s = sales.load(newest["id"])
        if s:
            return s
    ps = plan_mod.plans()
    newest_plan = max(ps, key=lambda x: x.get("updated", "")) if ps else {}
    return sales.new_sheet(str(payload.get("brand") or newest_plan.get("brand") or "Brand"),
                           newest_plan.get("id", ""), newest_plan.get("house", ""))


def _sales_house(s: dict):
    if s.get("house"):
        return strategy.load(s["house"])
    p = plan_mod.load(s.get("plan", "")) if s.get("plan") else None
    return _house_for(p) if p else None


@app.get("/trade")
def trade_list():
    return {"sheets": sales.sheets(), "channels": sales.CHANNELS, "roles": sales.ROLES,
            "levers": list(sales.LEVERS), "sell_through": sales.SELL_THROUGH,
            "states": list(sales.ELEMENT_STATES)}


@app.post("/trade-new")
def trade_new(payload: dict):
    """Every channel exists from the start, including the ones getting nothing. A channel with no money
    is a decision, and an empty row records it — dropping the row hides it."""
    s = sales.new_sheet(str(payload.get("brand") or "Brand"),
                        str(payload.get("plan") or ""), str(payload.get("house") or ""))
    return {"sheet": s, "status": sales.status(s, _sales_house(s))}


@app.get("/trade/{sheet_id}")
def trade_get(sheet_id: str):
    s = sales.load(sheet_id)
    if not s:
        return JSONResponse(status_code=404, content={"detail": "No such trade sheet."})
    return {"sheet": s, "status": sales.status(s, _sales_house(s))}


@app.post("/trade-margin-story")
def trade_margin_story(payload: dict):
    """What one facing of this pack earns a shopkeeper in a week, against the unbranded alternative.
    `{mrp, trade_price, case_size?, units_per_week?, facings?, unbranded_price?,
    unbranded_margin_pct?, pack_name?}`.

    Computed, never asked of a model — the only two required numbers are the MRP and the trade price,
    because every figure here is built from those two. Missing either, or a trade price that is not
    below MRP, is refused rather than guessed at.
    """
    def num(key):
        v = payload.get(key)
        try:
            return float(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    story = sales.margin_story(
        num("mrp"), num("trade_price"),
        case_size=int(num("case_size") or 1), units_per_week=num("units_per_week") or 0,
        facings=int(num("facings") or 1),
        unbranded_price=num("unbranded_price"), unbranded_margin_pct=num("unbranded_margin_pct"))
    if not story["available"]:
        return JSONResponse(status_code=400, content={"detail": story["why"]})
    return {**story, "talk_track": sales.talk_track(story, str(payload.get("pack_name") or "the pack"))}


def _num(payload: dict, key: str):
    v = payload.get(key)
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


@app.post("/trade-distributor-roi")
def trade_distributor_roi(payload: dict):
    """Return on the money a distributor has tied up. `{monthly_offtake, margin_pct, stock_at_cost,
    credit_extended?, deposits?, infrastructure?, monthly_operating_cost?}`.

    A distributor does not decide on margin — he decides on return on the capital he has tied up, and
    two distributors on an identical margin can return very differently depending on how fast the stock
    turns and how quickly he collects. Selling one on margin is the most common way a trade pitch
    misses, and until now this desk could only talk about margin.

    `credit_extended` is optional and its absence is reported rather than treated as zero: leaving it
    out shrinks the denominator and makes the return read high, so the payload says so.
    """
    r = sales.distributor_roi(
        _num(payload, "monthly_offtake"), _num(payload, "margin_pct"),
        stock_at_cost=_num(payload, "stock_at_cost"),
        credit_extended=payload.get("credit_extended"),
        deposits=_num(payload, "deposits") or 0.0,
        infrastructure=_num(payload, "infrastructure") or 0.0,
        monthly_operating_cost=_num(payload, "monthly_operating_cost") or 0.0)
    if not r["available"]:
        return JSONResponse(status_code=400, content={"detail": r["why"]})
    return r


@app.post("/trade-contribution")
def trade_contribution(payload: dict):
    """Whether a channel covers its own cost to serve. `{consumer_price, gross_margin_pct,
    commission_pct, fulfilment_per_unit?, storage_pct?, listing_fee?, units_over_fee_period?}`.

    The quoted rule is that quick commerce needs a gross margin above about 65%. That is a useful
    warning and a bad input, because it is somebody else's deal — so the break-even gross margin is
    derived from the costs actually entered and reported alongside the real one.

    A listing fee with no unit volume to spread it over is refused: the same fee is trivial across
    fifty thousand units and fatal across five hundred, and a verdict that ignores which one it is
    would be a verdict about nothing.
    """
    r = sales.channel_contribution(
        _num(payload, "consumer_price"),
        gross_margin_pct=_num(payload, "gross_margin_pct"),
        commission_pct=_num(payload, "commission_pct"),
        fulfilment_per_unit=_num(payload, "fulfilment_per_unit") or 0.0,
        storage_pct=_num(payload, "storage_pct") or 0.0,
        listing_fee=_num(payload, "listing_fee") or 0.0,
        units_over_fee_period=_num(payload, "units_over_fee_period") or 0.0)
    if not r["available"]:
        return JSONResponse(status_code=400, content={"detail": r["why"]})
    return r


@app.post("/sales-channel")
def sales_channel(payload: dict):
    """Set a channel's role, share, behaviour, economics, leakage control and effective price."""
    s = _sales_sheet(payload)
    ch = str(payload.get("channel") or "")
    out = sales.set_channel(s, ch, payload)
    if out is None:
        return JSONResponse(status_code=400,
                            content={"detail": f"No such channel {ch!r}.",
                                     "channels": [c["key"] for c in sales.CHANNELS]})
    return {"sheet": out, "status": sales.status(out, _sales_house(out))}


@app.post("/sales-element")
def sales_element(payload: dict):
    """Brief or agree one element of one channel.

    Marking a pitch card `agreed` against a primary-only scheme is refused: primary movement is dispatch
    rather than demand, and a pitch card is how that gets sold into the field at scale before anyone has
    checked it is real.
    """
    s = _sales_sheet(payload)
    out, err = sales.set_element(s, str(payload.get("channel") or ""),
                                str(payload.get("element") or ""),
                                brief=payload.get("brief"),
                                status=payload.get("status"))
    if err or out is None:
        return JSONResponse(status_code=400 if err else 404,
                            content={"detail": err or "No such channel or element."})
    return {"sheet": out, "status": sales.status(out, _sales_house(out))}


@app.post("/sales-generate")
def sales_generate(payload: dict):
    """Fill a channel, or write one element, from the vendored trade-activation skill.

    The skill ships inside the portal exactly as the brief and house skills do, so this works for every
    user without anybody uploading anything.
    """
    s = _sales_sheet(payload)
    ch = str(payload.get("channel") or "")
    if ch not in sales.CHANNEL_BY_KEY:
        return JSONResponse(status_code=400, content={"detail": f"No such channel {ch!r}."})
    house = _sales_house(s)
    brief_text = " ".join(str(v) for v in ((house or {}).get("brief") or {}).values())[:2000]
    anchors, _n = learning.anchor_block("trade", brief_text, 3)
    s, note = sales.generate(s, ch, house=house, el=str(payload.get("element") or ""),
                             extra=str(payload.get("note") or ""),
                             anchors=anchors, rules=learning.rules_block())
    if note:
        return JSONResponse(status_code=400, content={"detail": note})
    return {"sheet": s, "status": sales.status(s, house)}


@app.get("/sales-prompt/{sheet_id}/{channel}")
def sales_prompt(sheet_id: str, channel: str, element: str = ""):
    s = sales.load(sheet_id)
    if not s or channel not in sales.CHANNEL_BY_KEY:
        return JSONResponse(status_code=404, content={"detail": "Not found."})
    return {"prompt": sales.prompt_for(s, channel, _sales_house(s), el=element)}


# =====================================================================================
# Executions — one envelope, several producers
# =====================================================================================

@app.get("/producers/{kind}")
def producer_manifest(kind: str):
    """What this kind of execution is briefed for and what it makes.

    Declared rather than discovered, so a new kind of work needs no client change — the panel renders
    from this. `media` reports `message_required: false` because a media plan allocates weight and
    money; a message field on it would only ever be filled with something untrue.
    """
    man = execution.MANIFEST.get(kind)
    guide = execution.prompt_guide(kind)
    if not man:
        return JSONResponse(status_code=404,
                            content={"detail": f"No producer for {kind!r}.",
                                     "kinds": list(execution.MANIFEST)})
    # The prompt guide travels with the manifest so a producer panel renders both from one call.
    # `available: false` for a kind with no guide written yet — a generic guide that could apply to any
    # producer teaches nothing about this one, so there isn't one.
    return {"kind": kind, **man, "statuses": list(execution.STATUSES), "prompt_guide": guide}


@app.get("/producers")
def producer_list():
    """Every producer, plus which are still offered and which retired and where they went.

    `live` is the list a client should build its tab strip from. `producers` keeps every kind including
    the retired ones, so an execution already stored against one still renders its label rather than a
    bare key — the same reason `strategy.H_LAYERS` keeps the retired medium layer.
    """
    return {"producers": [{"kind": k, **v, "prompt_guide": execution.prompt_guide(k)}
                          for k, v in execution.MANIFEST.items()],
            "live": [{"kind": k, **v} for k, v in execution.live_kinds().items()],
            "retired": execution.RETIRED_KINDS,
            "statuses": list(execution.STATUSES)}


@app.get("/brief-prompt-guides")
def brief_prompt_guides():
    """Prompt guides for the brief-writing screens, keyed by surface.

    Same payload shape as a producer's `prompt_guide`, so one renderer serves both. Returned as a map
    rather than one-per-request because a screen carries several of these disclosures at once and
    fetching them separately is four calls for four paragraphs.

    `briefs` comes back `available: false` on purpose: that screen has no prompt on it, and saying so
    is more use than a generic guide behind a disclosure that opens onto nothing.
    """
    return {"guides": briefguide.surfaces()}


@app.get("/brief-prompt-guide/{surface}")
def brief_prompt_guide(surface: str):
    """One brief surface's prompt guide."""
    return briefguide.prompt_guide(surface)


# --- the media desk ------------------------------------------------------------------------------

@app.get("/media-status")
def media_status():
    """The media desk's vocabulary, and what it derives from the plan rather than asking again.

    `brand_share_basis` carries the citation for the 60 and the dispute against it. A screen showing a
    bare "60" is showing arithmetic; one showing who says so and who disagrees is showing a position.
    """
    return {
        # What the desk can and cannot do yet. The `cannot` half is the more useful one, and it is
        # served rather than written on the screen because a screen goes stale the moment a phase lands
        # — as it already had: the Media tab listed competitive intelligence as "not yet" after it
        # shipped. One place says what is true, and the screen renders it.
        "can": mediaplan.CAN,
        "cannot": mediaplan.CANNOT,
        "roles": plan_mod.ROLES,
        "sides": list(plan_mod.SIDES),
        "derives": mediaplan.DERIVES,
        "brand_share_basis": plan_mod.BRAND_SHARE_BASIS,
        "retired_producer": execution.RETIRED_KINDS.get("media"),
        # The competitive vocabulary. `levels` is the honest answer to "can we do share of voice?" —
        # it depends on what the studio can buy, and a screen that renders this says so rather than
        # implying a capability behind a disabled button.
        "ci_levels": mediaplan.LEVELS,
        "ci_source_kinds": mediaplan.SOURCE_KINDS,
        "ci_free_sources": mediaplan.FREE_SOURCES,
        "esov_basis": mediaplan.ESOV_BASIS,
        "media": [{"key": m, "label": media.LEAF_LABEL.get(m, m)} for m in media.LEAVES],
    }


@app.get("/media-strategy")
def media_strategy(plan: str = ""):
    """The media strategy, derived read-only from the plan. The Media tab's first screen.

    Nothing here is editable and the payload says so: roles, sides and the split are decisions the plan
    already made. What the media desk owns — weight, money, flighting, the calendar — does not exist
    yet, and `findings` says which of it is blocked and why.
    """
    p = plan_mod.load(plan) if plan else None
    if plan and not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    house = strategy.load(p.get("house") or "") if (p and p.get("house")) else None
    return mediaplan.strategy_view(p, house)


# --- the competitive picture (MP·2) ---------------------------------------------------------------
#
# Per brand, not per plan: the category's size outlives the plans built against it, and two copies of
# it would disagree about the denominator of every share.

def _ci_apply(brand: str, fn, *a):
    """Load, mutate, save. Returns `(record, error_response)` — exactly one is None.

    `mediaplan`'s mutators are deliberately pure, unlike `pr`'s, which save themselves. That divergence
    is on purpose: it means the competitive gates can be exercised without writing a tenant file, and
    this module is almost entirely gates. The risk it creates is a route that mutates and forgets to
    save, so every route goes through here and there is one place that writes.
    """
    if not brand:
        return None, JSONResponse(status_code=400,
                                  content={"detail": "Name the brand this picture belongs to."})
    c, err = fn(mediaplan.ci_load(brand), *a)
    if err:
        return None, JSONResponse(status_code=400, content={"detail": err})
    return mediaplan.ci_save(c), None


@app.get("/media-competitive")
def media_competitive(brand: str = "", period: str = ""):
    """The competitive picture for one brand. `level` says what it can actually compute.

    A share of voice this could not stand behind is reported as unavailable, with the list of names
    needed to make it whole — never estimated. A missing participant contributes nothing to the
    denominator and inflates every other share while they still sum to 100, so there would be no sign
    on screen that it happened.
    """
    if not brand:
        return JSONResponse(status_code=400, content={"detail": "Name a brand."})
    return mediaplan.ci_view(mediaplan.ci_load(brand), period)


@app.post("/media-competitor")
def media_competitor(payload: dict):
    """Add or update one participant. `{brand, competitor: {name, us?, note?, id?}}`.

    The brand itself is a row here carrying `us: true`, rather than being stored apart — so the
    denominator of a share cannot omit its own numerator.
    """
    c, bad = _ci_apply(str(payload.get("brand") or ""), mediaplan.add_competitor,
                       payload.get("competitor") or {})
    return bad or mediaplan.ci_view(c, str(payload.get("period") or ""))


@app.post("/media-competitor-drop")
def media_competitor_drop(payload: dict):
    """Remove a participant and every observation against them. `{brand, id}`.

    Both, together: orphaned observations would keep contributing to the category total while their
    owner no longer appeared in the set, so the shares would stop summing to 100 with nothing on screen
    to explain it.
    """
    c, bad = _ci_apply(str(payload.get("brand") or ""), mediaplan.drop_competitor,
                       str(payload.get("id") or ""))
    return bad or mediaplan.ci_view(c, str(payload.get("period") or ""))


@app.post("/media-competitive-set")
def media_competitive_set(payload: dict):
    """Declare whether the set covers the category. `{brand, complete: bool, note}`.

    This is the difference between a share of the category and a share of the companies somebody
    happened to list, and no amount of data can infer it — so it is an explicit claim with a basis
    attached. Until it is made, every share reports itself as a share of the listed set.
    """
    c, bad = _ci_apply(str(payload.get("brand") or ""), mediaplan.declare_set,
                       bool(payload.get("complete")), str(payload.get("note") or ""))
    return bad or mediaplan.ci_view(c, str(payload.get("period") or ""))


@app.post("/media-observation")
def media_observation(payload: dict):
    """Record one competitor's activity. `{brand, observation: {competitor, period, medium?,
    source_kind, source, spend?, currency?, running?, creative?, as_of?}}`.

    `source_kind` decides what the row may carry: a free ad library establishes presence and never
    spend, and published accounts are annual and all-media. Enter a measured **zero** where a
    competitor was checked and ran nothing — that is a fact, and it is what makes a share computable.
    """
    c, bad = _ci_apply(str(payload.get("brand") or ""), mediaplan.add_observation,
                       payload.get("observation") or {})
    return bad or mediaplan.ci_view(c, str(payload.get("period") or ""))


@app.post("/media-observation-drop")
def media_observation_drop(payload: dict):
    """Remove one observation. `{brand, id}`."""
    c, bad = _ci_apply(str(payload.get("brand") or ""), mediaplan.drop_observation,
                       str(payload.get("id") or ""))
    return bad or mediaplan.ci_view(c, str(payload.get("period") or ""))


# --- geography, and the social campaign that holds money (MP·3) -----------------------------------

@app.get("/geo-status")
def geo_status():
    """States, UTs, zones, and what a population figure is allowed to mean.

    Geography had no home in this system before now — the plan has no geography layer, brand profile
    keeps a free-text `market`, and PR outlets carry a free-text `region`. This is the first definition
    rather than a second one, which is why it is a vocabulary route and not a document.
    """
    return geo.status()


@app.get("/geo-cities")
def geo_cities(min_pop: int = 500000, basis: str = "census_2011_city", states: str = ""):
    """Cities at or above a population line, on ONE declared basis.

    Defaults to 5 lakh. `complete` is false whenever the line sits below the seed's known gap, and
    `gap` then names what is missing — the seeded list is deliberately short rather than quietly
    passing itself off as the whole set. `threshold_caveat` says why a 2011 figure tested against a
    2026 intention produces a list that is short at the bottom.
    """
    want = [s for s in (states or "").split(",") if s.strip()]
    return geo.key_cities(int(min_pop), basis, want)


def _sp_apply(sid: str, fn, *a, **kw):
    """Load, mutate, save one social plan. `(plan, error_response)` — exactly one is None.

    Same shape and same reason as `_ci_apply`: the module's mutators are pure so the gates can be
    tested without writing a tenant file, and one helper owns every write so a route cannot mutate and
    forget to save. That matters more here than anywhere else in the codebase, because what would go
    missing is a budget.
    """
    d = socialplan.load(str(sid or ""))
    if not d:
        return None, JSONResponse(status_code=404, content={"detail": "No such social campaign."})
    d2, err = fn(d, *a, **kw)
    if err:
        return None, JSONResponse(status_code=400, content={"detail": err})
    return socialplan.save(d2), None


@app.get("/social-plans")
def social_plans():
    return {"plans": socialplan.listing()}


@app.post("/social-plan")
def social_plan_new(payload: dict):
    """Start a geography-wise social campaign. `{brand, name?, plan?}`."""
    d, err = socialplan.new_plan(str(payload.get("brand") or ""), str(payload.get("name") or ""),
                                 str(payload.get("plan") or ""))
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return socialplan.view(d)


@app.get("/social-plan/{sid}")
def social_plan_get(sid: str):
    d = socialplan.load(sid)
    if not d:
        return JSONResponse(status_code=404, content={"detail": "No such social campaign."})
    return socialplan.view(d)


@app.post("/social-plan-frame")
def social_plan_frame(payload: dict):
    """The frame. `{id, objective?, budget?, currency?, days?, budget_mode?, split_level?}`.

    `objective` comes from `plan.ROLES`, and it decides which feasibility rule applies: a conversion
    cell is bound by the learning-phase event threshold and a reach cell is not. Guessing it would mean
    applying a conversion rule to a reach campaign, so it is asked for rather than defaulted.
    """
    d, bad = _sp_apply(payload.get("id"), socialplan.set_frame,
                       objective=payload.get("objective"), budget=payload.get("budget"),
                       currency=payload.get("currency"), days=payload.get("days"),
                       budget_mode=payload.get("budget_mode"),
                       split_level=payload.get("split_level"))
    return bad or socialplan.view(d)


@app.post("/social-plan-benchmark")
def social_plan_benchmark(payload: dict):
    """The cost benchmark. `{id, kind, source, cpa?, cpm?, as_of?}`.

    There is deliberately no default CPA anywhere in this module. Every feasibility number divides by
    this figure, so an assumed one would produce a confident verdict about whether a geography split
    can run — computed from a number nobody chose, and acted on as though it meant something.
    """
    d, bad = _sp_apply(payload.get("id"), socialplan.set_benchmark,
                       kind=str(payload.get("kind") or ""), source=str(payload.get("source") or ""),
                       cpa=payload.get("cpa"), cpm=payload.get("cpm"),
                       as_of=str(payload.get("as_of") or ""))
    return bad or socialplan.view(d)


@app.post("/social-plan-import")
async def social_plan_import(id: str = Form(""), level: str = Form(""),
                             file: UploadFile = File(...)):
    """Read a spreadsheet of geographies into PROPOSED cells. Writes nothing.

    A person planning fifty cells has them in a sheet already, and retyping them into a form is the
    kind of work this studio exists to remove. What it does not do is write them: every row is checked
    by `socialplan.add_cell` against a scratch copy of the plan, so a refusal here is the refusal the
    form would have given, and an import cannot become the way around a validator.

    A spreadsheet gets rows. A deck or a PDF gets its text handed back with a note saying why there are
    no cells in it — columns are what carry the meaning, and one row per paragraph is not a table.
    """
    d = socialplan.load(str(id or "")) if id else None
    if id and not d:
        return JSONResponse(status_code=404, content={"detail": "No such social plan."})

    import tempfile

    import research_parse
    name = os.path.basename(file.filename or "upload")
    suffix = os.path.splitext(name)[1].lower()
    if suffix not in (".xlsx", ".xls", ".csv", ".pptx", ".pdf", ".docx", ".txt", ".md"):
        return JSONResponse(status_code=400, content={
            "detail": (f"{suffix or 'That file'} is not a format this reads. Spreadsheets (.xlsx, .csv) "
                       f"become cells; decks and documents (.pptx, .pdf, .docx) are read as text.")})
    data = await file.read()
    tmp = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as fh:
            fh.write(data)
            tmp = fh.name
        table = research_parse.table_rows(tmp)
    except Exception as e:
        return JSONResponse(status_code=400, content={
            "detail": f"Could not read {name}: {type(e).__name__}: {e}"})
    finally:
        if tmp:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    if table["kind"] != "table":
        return {"ok": False, "kind": "text", "filename": name, "text": table.get("text", ""),
                "why": table.get("why", ""), "proposed": [], "refused": [], "writes_nothing": True}

    out = socialplan.propose_cells(d or {"cells": [], "split_level": level or "state"},
                                  table["rows"], level_hint=level)
    return {"kind": "table", "filename": name, "sheet": table.get("sheet", ""), **out}


@app.post("/social-cell")
def social_cell(payload: dict):
    """Add or update one geography that holds money. `{id, cell: {level, state?, name?, radius_km?,
    budget?, floor?, phase?, priority?, note?}}`.

    A cell is deliberately the shape of a Meta ad set — geography, budget and optimisation goal on one
    object — because that is where all three actually live, and a studio unit that does not match the
    platform unit has to be translated by hand every time either changes.
    """
    d, bad = _sp_apply(payload.get("id"), socialplan.add_cell, payload.get("cell") or {})
    return bad or socialplan.view(d)


@app.post("/social-cell-drop")
def social_cell_drop(payload: dict):
    """Remove one cell. `{id, cell_id}`."""
    d, bad = _sp_apply(payload.get("id"), socialplan.drop_cell, str(payload.get("cell_id") or ""))
    return bad or socialplan.view(d)


@app.post("/media-market-share")
def media_market_share(payload: dict):
    """The brand's share of market, entered with its source. `{brand, value, source, as_of?, note?}`.

    Never derived here. ESOV is share of voice minus this figure, and a market share the system
    computed for itself would make ESOV a number built from a number it invented.
    """
    c, bad = _ci_apply(str(payload.get("brand") or ""), mediaplan.set_som,
                       payload.get("value"), str(payload.get("source") or ""),
                       str(payload.get("as_of") or ""), str(payload.get("note") or ""))
    return bad or mediaplan.ci_view(c, str(payload.get("period") or ""))


# --- Actuals: the measurement ledger (audit #9) --------------------------------------------------
#
# A general, flat, per-tenant store for anything measured after the fact — see `actuals.py` for the
# shape agreed in ASK_DESIGN_46_REPLY.md. Additive only: nothing existing reads from this yet, so these
# routes cannot change what any current screen shows. `esov()`/the social benchmark repointing onto
# this ledger is deliberately a separate, later step.

@app.get("/actuals")
def actuals_list(metric: str = "", geography: str = "", period: str = ""):
    """Entries matching the given filters, most recent first. Any filter left blank matches everything."""
    return {"entries": actuals.list_entries(metric=metric, geography=geography, period=period),
            "metrics": actuals.metrics()}


@app.post("/actuals")
def actuals_add(payload: dict):
    """Record one measured fact. `{metric, value, period, source, geography?, date?, note?}`.

    `metric` is free text, not a fixed vocabulary — this is the general store for facts with no
    existing field of their own. `geography` defaults to 'national' when the fact genuinely is not
    geography-specific, rather than being left blank.
    """
    entry, err = actuals.add(
        metric=str(payload.get("metric") or ""), value=payload.get("value"),
        geography=str(payload.get("geography") or ""), period=str(payload.get("period") or ""),
        source=str(payload.get("source") or ""), date=str(payload.get("date") or ""),
        note=str(payload.get("note") or ""))
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return entry


@app.post("/actuals-remove")
def actuals_remove(payload: dict):
    """Delete one entry, for correcting a mis-entered fact. `{id}`."""
    doc, err = actuals.remove(str(payload.get("id") or ""))
    if err:
        return JSONResponse(status_code=404, content={"detail": err})
    return {"entries": doc["entries"]}


# --- PR: the sheet, the objectives funnel, the message set --------------------------------------
#
# Two modes on one store. Every route resolves the plan and house itself rather than trusting the
# client to send them, so a sheet's descent and its proof options are always read from the documents
# the sheet actually points at.

def _pr_context(s: dict) -> tuple[dict | None, dict | None]:
    """The plan and house a PR sheet points at. Either may be absent — standalone PR needs neither."""
    p = plan_mod.load(s.get("plan") or "") if s.get("plan") else None
    house = strategy.load(s.get("house") or "") if s.get("house") else None
    if p and not house and p.get("house"):
        house = strategy.load(p["house"])          # inherit the plan's house when none was named
    return p, house


def _pr_objective_rows(p: dict | None) -> list[dict]:
    return ((p or {}).get("nodes", {}).get("objectives", {}) or {}).get("rows", []) or []


@app.get("/pr-status")
def pr_status():
    """The PR vocabulary — modes, standalone kinds, phases, the descent and the five PR jobs.

    Rendered as a panel rather than hard-coded, for the same reason the grades and POSM formats are:
    what PR *cannot* carry is the part worth reading, and it is per-rung.
    """
    return {
        "modes": {k: v for k, v in pr.MODES.items()},
        "standalone_kinds": pr.STANDALONE_KINDS,
        "phases": pr.PHASES,
        "descent": pr.DESCENT,
        "rungs": {k: {kk: vv for kk, vv in v.items() if kk != "cues"} for k, v in pr.PR_RUNGS.items()},
        "message_cap": pr.MESSAGE_MAX,
        "role": media.role_for("pr")[0],
        "role_why": media.role_for("pr")[1],
    }


@app.get("/pr-sheets")
def pr_sheets(plan: str = "", mode: str = ""):
    return {"sheets": pr.sheets(plan_id=plan, mode=mode)}


@app.post("/pr-sheet")
def pr_sheet_new(payload: dict):
    """Start a PR sheet. `{brand, mode: campaign|standalone, plan?, house?, kind?, phase?}`.

    When a campaign sheet names a plan but no house, the plan's house is inherited and STORED. Found by
    walking a real sheet: proof options resolved correctly either way, because `_pr_context` inherits at
    read time — but the stored document carried an empty `house`, so nothing recorded which house its
    messages were written against. A plan that later switches house would leave the sheet's proof text
    in place with no way to say where it came from.
    """
    house_in = str(payload.get("house") or "")
    plan_in = str(payload.get("plan") or "")
    if plan_in and not house_in:
        _p = plan_mod.load(plan_in)
        house_in = str((_p or {}).get("house") or "")
    s, err = pr.new_sheet(
        str(payload.get("brand") or ""), str(payload.get("mode") or "campaign"),
        plan_id=plan_in, house_id=house_in,
        kind=str(payload.get("kind") or ""), phase=str(payload.get("phase") or ""),
        execution_id=str(payload.get("execution") or ""))
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"sheet": s, "status": pr.status(s)}


@app.get("/pr-sheet/{sheet_id}")
def pr_sheet_get(sheet_id: str):
    s = pr.load(sheet_id)
    if not s:
        return JSONResponse(status_code=404, content={"detail": "No such PR sheet."})
    p, house = _pr_context(s)
    return {"sheet": s, "status": pr.status(s),
            "funnel": pr.funnel(_pr_objective_rows(p)),
            "proof_options": pr.proof_options(house)}


@app.get("/pr-funnel")
def pr_funnel(plan: str = ""):
    """Marketing objectives in, PR objectives out — with the rows PR cannot carry refused.

    Read straight off the plan's objectives ladder: `level` already says business / marketing /
    communication, so the refusal is stored data rather than a guess about a sentence.
    """
    p = plan_mod.load(plan) if plan else None
    if plan and not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    return pr.funnel(_pr_objective_rows(p))


@app.post("/pr-objectives")
def pr_objectives(payload: dict):
    """Write a sheet's PR objectives. `{id, objectives: [{statement, statement_id?, rung?, proof?}]}`."""
    s = pr.load(str(payload.get("id") or ""))
    if not s:
        return JSONResponse(status_code=404, content={"detail": "No such PR sheet."})
    p, _house = _pr_context(s)
    s2, err = pr.set_objectives(s, payload.get("objectives") or [], _pr_objective_rows(p))
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"sheet": s2, "status": pr.status(s2)}


@app.post("/pr-messages")
def pr_messages(payload: dict):
    """Write the declared message set. `{id, messages: [{text, proof_id?, proof?}]}`.

    Capped at three and gated on the cap, because message pull-through is measured per message.
    """
    s = pr.load(str(payload.get("id") or ""))
    if not s:
        return JSONResponse(status_code=404, content={"detail": "No such PR sheet."})
    _p, house = _pr_context(s)
    s2, err = pr.set_messages(s, payload.get("messages") or [], house)
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"sheet": s2, "status": pr.status(s2)}


@app.post("/pr-sheet-drop")
def pr_sheet_drop(payload: dict):
    sid = str(payload.get("id") or "")
    if not pr.load(sid):
        return JSONResponse(status_code=404, content={"detail": "No such PR sheet."})
    return {"dropped": pr.drop(sid)}


# --- the media map: brand-level, outlets suggested, people never invented ------------------------

@app.get("/pr-map-status")
def pr_map_status():
    """The map's vocabulary — languages, tiers, the categories the studio works in, and the two
    regulators that apply. Rendered from data so a screen never hard-codes a language list.

    `claims_authority` is separate from `trade_categories` on purpose: the product regulator differs
    per category, the misleading-advertising one does not.
    """
    return {
        "languages": pr.LANGUAGES,
        "tiers": pr.TIERS,
        "trade_categories": pr.TRADE_CATEGORIES,
        "claims_authority": pr.CLAIMS_AUTHORITY,
        "freshness": {"fresh_days": pr.FRESH_DAYS, "ageing_days": pr.AGEING_DAYS},
        "seed_languages": sorted(pr.SEED_OUTLETS),
        "seed_source": pr.SEED_SOURCE,
    }


@app.get("/pr-map")
def pr_map_get(brand: str = ""):
    if not brand:
        return JSONResponse(status_code=400, content={"detail": "Name the brand this map belongs to."})
    m = pr.map_load(brand)
    return {"map": m, "status": pr.map_status(m),
            "freshness": {r["id"]: pr.freshness(r)
                          for r in (m.get("outlets") or []) + (m.get("journalists") or [])}}


@app.get("/pr-map-suggest")
def pr_map_suggest(languages: str = "", tier: str = "language"):
    """Titles worth considering, per language. Suggestions only — every one comes back unconfirmed,
    and a market with no seed says so rather than returning a plausible guess."""
    langs = [x.strip() for x in (languages or "").split(",") if x.strip()]
    out = pr.suggest_outlets(langs, tier=tier)
    if out.get("unknown"):
        return JSONResponse(status_code=400, content={"detail": out["note"]})
    return out


@app.get("/pr-message-suggest")
def pr_message_suggest(id: str = ""):
    """Starting text for the declared message set, each claim paired with its own proof.

    The panel offered an empty box and a proof picker, so a person with nothing typed declared nothing
    — and the release, the plan and coverage all sit behind a declared set. Same block the objectives
    had, same fix.

    Composes nothing: a proposal is one of the house's own messages verbatim, pointed at one of the
    house's own reasons to believe, also verbatim. `parts` carries the two halves so a screen can show
    where each came from. Writes nothing.
    """
    s = pr.load(str(id or ""))
    if not s:
        return JSONResponse(status_code=404, content={"detail": "No such PR sheet."})
    _p, house = _pr_context(s)
    return pr.message_suggestions(s, house)


@app.get("/pr-release-suggest")
def pr_release_suggest(id: str = ""):
    """What a release can be filled in with from what is already declared, and what must be written.

    Splits the form in two rather than demanding all of it: `fill` and `five_w` are assembled from the
    brand profile, the house and the sheet's own message set, each field naming its source. `write` is
    the prose, and this returns no text for any of it — `source_material` hands over what a headline
    would be written FROM instead. Writes nothing; a person applies it field by field.
    """
    s = pr.load(str(id or ""))
    if not s:
        return JSONResponse(status_code=404, content={"detail": "No such PR sheet."})
    p, house = _pr_context(s)
    return pr.release_suggestions(s, p, house)


@app.get("/pr-map-derive")
def pr_map_derive(brand: str = ""):
    """A starting media map for a brand, derived rather than asked for.

    `/pr-map-suggest` needs languages named before it will suggest a title, which the brand profile has
    already answered: `languages` is declared in setup and `states` implies more through `geo`. This
    composes the two and then asks `suggest_outlets` for the ones there is a seed for.

    Declared and implied languages are kept apart, and unseeded ones are named rather than dropped. A
    language with no seed is a hole in this module's list, not an absence of press in that language, and
    a map that quietly covered four of six languages would read as complete.

    Nothing is written. This is a proposal; every outlet still arrives unconfirmed and is added by hand
    through `/pr-outlet`, because a map that seeded itself is a map nobody checked.
    """
    langs = pr.derive_map_languages(brand)
    seeded = langs["seeded"]
    suggestions = pr.suggest_outlets(seeded, tier="language") if seeded else {}
    return {
        **langs,
        "suggestions": suggestions,
        "writes_nothing": True,
        "what_this_cannot_do": (
            "Confirm a masthead, a circulation figure or a person. Every suggestion here is a title "
            "worth considering, and a title becomes part of the map only when somebody adds it."),
    }


@app.post("/pr-outlet")
def pr_outlet(payload: dict):
    """Add or update an outlet. `{brand, outlet: {name, language, tier, category?, edition?, region?,
    circulation?, circulation_source?, digital?, digital_source?, confirmed?, verified?}}`.

    Circulation and digital audience stay two separate fields with their own sources. There is no
    blended reach field, and that is deliberate — see `pr.reach_by_language`.
    """
    brand = str(payload.get("brand") or "")
    if not brand:
        return JSONResponse(status_code=400, content={"detail": "Name the brand this map belongs to."})
    m, err = pr.add_outlet(pr.map_load(brand), payload.get("outlet") or {})
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"map": m, "status": pr.map_status(m)}


@app.post("/pr-journalist")
def pr_journalist(payload: dict):
    """Add or update a journalist. `{brand, journalist: {name, outlet, beat?, contact?, recent?,
    origin: entered|imported, verified?}}`.

    `origin` is required and refuses anything else. A generated name, beat and contact would be an
    invention about a real person that no reader could tell from a fact.
    """
    brand = str(payload.get("brand") or "")
    if not brand:
        return JSONResponse(status_code=400, content={"detail": "Name the brand this map belongs to."})
    m, err = pr.add_journalist(pr.map_load(brand), payload.get("journalist") or {})
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"map": m, "status": pr.map_status(m)}


@app.post("/pr-map-drop")
def pr_map_drop(payload: dict):
    """Remove an outlet (and the people filed under it) or one journalist.
    `{brand, outlet?}` or `{brand, journalist?}`."""
    brand = str(payload.get("brand") or "")
    if not brand:
        return JSONResponse(status_code=400, content={"detail": "Name the brand this map belongs to."})
    m = pr.map_load(brand)
    oid, jid = str(payload.get("outlet") or ""), str(payload.get("journalist") or "")
    if oid:
        m, gone = pr.drop_outlet(m, oid)
        return {"map": m, "status": pr.map_status(m), "journalists_removed": gone}
    if jid:
        m = pr.drop_journalist(m, jid)
        return {"map": m, "status": pr.map_status(m), "journalists_removed": 0}
    return JSONResponse(status_code=400,
                        content={"detail": "Name an `outlet` or a `journalist` to remove."})


# --- the release and the media kit ---------------------------------------------------------------

def _pr_locked() -> list[dict]:
    """Signed-off locked copy — the strings a release must place verbatim."""
    return library.locked_copy()


def _pr_or_404(sheet_id: str):
    s = pr.load(sheet_id)
    return s, (None if s else JSONResponse(status_code=404,
                                           content={"detail": "No such PR sheet."}))


@app.get("/pr-release-status")
def pr_release_status():
    """The release's parts, the five questions its lead must answer, the word band, and the kit's
    elements — rendered from data so a screen never hard-codes the structure.

    `skill` reports whether `pr_skill` is on disk, the same way the POSM and sales screens report it.
    """
    return {
        "parts": {k: {"label": v["label"], "required": v["required"], "what": v["what"]}
                  for k, v in pr.RELEASE_PARTS.items()},
        "five_w": pr.FIVE_W,
        "words": {"min": pr.WORDS_MIN, "max": pr.WORDS_MAX},
        "kit": {k: v for k, v in pr.KIT_ELEMENTS.items()},
        "languages": pr.LANGUAGES,
        "skill": pr.skill_present(),
    }


@app.post("/pr-release")
def pr_release_new(payload: dict):
    """Start a release on a sheet. `{id, language?}`."""
    s, missing = _pr_or_404(str(payload.get("id") or ""))
    if missing:
        return missing
    s2, err = pr.new_release(s, str(payload.get("language") or "en"))
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"release": s2["release"], "gate": pr.release_gate(s2, _pr_locked())}


@app.post("/pr-release-write")
def pr_release_write(payload: dict):
    """Write release fields. `{id, ...fields}` — `five_w`, `carries` and `mandatories` accepted too.

    Unknown field names are refused rather than stored, so a typo cannot create a field the gate then
    never checks.
    """
    s, missing = _pr_or_404(str(payload.get("id") or ""))
    if missing:
        return missing
    patch = {k: v for k, v in payload.items() if k != "id"}
    s2, err = pr.set_release(s, patch)
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"release": s2["release"], "gate": pr.release_gate(s2, _pr_locked())}


@app.get("/pr-release/{sheet_id}")
def pr_release_get(sheet_id: str):
    s, missing = _pr_or_404(sheet_id)
    if missing:
        return missing
    return {"release": s.get("release") or None,
            "gate": pr.release_gate(s, _pr_locked()),
            "kit": pr.kit_status(s),
            "locked_copy": _pr_locked(),
            "messages": s.get("messages") or []}


@app.post("/pr-translate")
def pr_translate(payload: dict):
    """Add or update a translation. `{id, language, fields:{...}}`.

    It arrives unchecked, and editing it clears any previous check — a translated legal claim that
    ships because a flag stayed true is the accident this split exists to prevent.
    """
    s, missing = _pr_or_404(str(payload.get("id") or ""))
    if missing:
        return missing
    s2, err = pr.add_translation(s, str(payload.get("language") or ""), payload.get("fields") or {})
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"release": s2["release"], "gate": pr.release_gate(s2, _pr_locked())}


@app.post("/pr-translation-check")
def pr_translation_check(payload: dict):
    """A named person signs off one language. `{id, language, who}`."""
    s, missing = _pr_or_404(str(payload.get("id") or ""))
    if missing:
        return missing
    s2, err = pr.check_translation(s, str(payload.get("language") or ""),
                                   str(payload.get("who") or ""))
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"release": s2["release"], "gate": pr.release_gate(s2, _pr_locked())}


@app.post("/pr-kit")
def pr_kit(payload: dict):
    """Attach media-kit elements. `{id, soundbite?:{url,who}, broll?:{url}, stills?, profile?, release?}`.

    A scored master is refused as b-roll: it carries music and voice, so a newsroom cannot cut under it.
    """
    s, missing = _pr_or_404(str(payload.get("id") or ""))
    if missing:
        return missing
    patch = {k: v for k, v in payload.items() if k != "id"}
    s2, err = pr.set_kit(s, patch)
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"kit": pr.kit_status(s2)}


# --- the coverage log and the measures ------------------------------------------------------------

@app.get("/pr-coverage-status")
def pr_coverage_status():
    """The log's vocabulary — where a mention can appear, the three sentiments, and why no AVE."""
    return {"prominence": pr.PROMINENCE, "sentiment": pr.SENTIMENT,
            "ave": None, "why_no_ave": pr.AVE_REFUSAL}


@app.post("/pr-coverage")
def pr_coverage_log(payload: dict):
    """Log one published item. `{id, item:{outlet|outlet_name, language?, tier?, date, prominence,
    sentiment?, messages?, spokesperson_quoted?, from_wire?, url?, headline?}}`.

    The outlet resolves against the brand's media map so language, tier and the audience figure come
    from one place. A title not in the map is allowed and marked `off_map` — an unpitched pickup is
    real coverage.
    """
    s, missing = _pr_or_404(str(payload.get("id") or ""))
    if missing:
        return missing
    s2, err = pr.log_coverage(s, payload.get("item") or {}, pr.map_load(s.get("brand", "")))
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"coverage": s2.get("coverage") or [],
            "report": pr.coverage_report(s2, pr.map_load(s2.get("brand", "")))}


@app.post("/pr-coverage-drop")
def pr_coverage_drop(payload: dict):
    """Remove an item, and any pickups logged against it. `{id, item}`."""
    s, missing = _pr_or_404(str(payload.get("id") or ""))
    if missing:
        return missing
    s2, pickups = pr.drop_coverage(s, str(payload.get("item") or ""))
    return {"coverage": s2.get("coverage") or [], "pickups_removed": pickups,
            "report": pr.coverage_report(s2, pr.map_load(s2.get("brand", "")))}


@app.get("/pr-report/{sheet_id}")
def pr_report(sheet_id: str):
    """Every measure, computed from the one log — so no two panels can disagree about how much
    coverage there was. Leads with message pull-through; carries no advertising value."""
    s, missing = _pr_or_404(sheet_id)
    if missing:
        return missing
    return {"report": pr.coverage_report(s, pr.map_load(s.get("brand", ""))),
            "messages": s.get("messages") or [],
            "coverage": s.get("coverage") or []}


# --- crisis and recall -----------------------------------------------------------------------------
#
# The routes that refuse are the ones that matter. This studio drafts and checks; it does not determine
# a risk class, does not state what a regulation requires, and does not send.

@app.get("/pr-crisis-status")
def pr_crisis_status():
    """What a crisis response needs, and the limits of what this studio may do.

    `limits` is meant to be rendered on the screen, not buried here — it is the sentence that stops the
    module being mistaken for a compliance authority.
    """
    return {
        "notice_elements": pr.NOTICE_ELEMENTS,
        "roles": pr.SIGNOFF_ROLES,
        "categories": pr.TRADE_CATEGORIES,
        "frameworks": pr.frameworks(),
        "limits": ("This studio drafts and checks. It does not determine the risk class, does not "
                   "state what a regulation requires, and does not send. Those are the client's "
                   "quality, legal and executive functions."),
    }


@app.get("/pr-framework")
def pr_framework_get(jurisdiction: str = "", category: str = ""):
    """What has been confirmed for one jurisdiction and category — or an honest empty shell saying
    nothing has, which never falls back on another category's framework."""
    if not (jurisdiction and category):
        return {"frameworks": pr.frameworks()}
    return pr.framework(jurisdiction, category)


@app.post("/pr-framework")
def pr_framework_set(payload: dict):
    """Enter or replace a framework. `{jurisdiction, category, confirmed_by, classes:[…],
    obligations:[{what, source, within_hours?, form?, who?, classes?}], review_by?}`.

    Refuses an obligation with no source and a framework with no named confirmer. Obligations entered
    by nobody in particular are a recollection, and this is the document a recall is run against.
    """
    doc, err = pr.set_framework(str(payload.get("jurisdiction") or ""),
                                str(payload.get("category") or ""), payload)
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return doc


@app.post("/pr-standby")
def pr_standby(payload: dict):
    """Holding statements, written in calm. `{id, statements:[{situation, text, approved_by?}]}`."""
    s, missing = _pr_or_404(str(payload.get("id") or ""))
    if missing:
        return missing
    s2, err = pr.set_standby(s, payload.get("statements") or [])
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"standby": s2.get("standby") or [], "status": pr.crisis_status(s2)}


@app.post("/pr-incident")
def pr_incident(payload: dict):
    """Open an incident on a prepared crisis sheet.
    `{id, jurisdiction, category, discovered_at?, summary?}` — the clock runs from `discovered_at`."""
    s, missing = _pr_or_404(str(payload.get("id") or ""))
    if missing:
        return missing
    s2, err = pr.open_incident(s, payload)
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"status": pr.crisis_status(s2)}


@app.post("/pr-risk-class")
def pr_risk_class(payload: dict):
    """Quality records the risk class. `{id, risk_class, who}`.

    The valid classes come from the entered framework, so cosmetics is never graded on food's scale.
    With no framework entered this refuses rather than supplying a scale from memory.
    """
    s, missing = _pr_or_404(str(payload.get("id") or ""))
    if missing:
        return missing
    s2, err = pr.set_class(s, str(payload.get("risk_class") or ""), str(payload.get("who") or ""))
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"status": pr.crisis_status(s2)}


@app.post("/pr-notice")
def pr_notice(payload: dict):
    """Write the notice's three elements and the statement. `{id, product?, risk?, action?, statement?}`.

    Any edit clears every signature — what was signed is no longer what is on the page.
    """
    s, missing = _pr_or_404(str(payload.get("id") or ""))
    if missing:
        return missing
    s2, err = pr.set_notice(s, {k: v for k, v in payload.items() if k != "id"})
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"status": pr.crisis_status(s2)}


@app.post("/pr-sign")
def pr_sign(payload: dict):
    """One named person signs one role. `{id, role: qa|legal|ceo, who}`."""
    s, missing = _pr_or_404(str(payload.get("id") or ""))
    if missing:
        return missing
    s2, err = pr.sign(s, str(payload.get("role") or ""), str(payload.get("who") or ""))
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"status": pr.crisis_status(s2)}


@app.get("/pr-crisis/{sheet_id}")
def pr_crisis(sheet_id: str):
    s, missing = _pr_or_404(sheet_id)
    if missing:
        return missing
    return pr.crisis_status(s)


@app.get("/pr-reach")
def pr_reach(brand: str = ""):
    """Circulation and digital audience by language — two figures, never blended, with what is
    missing named. There is no readership currency to fill a gap with: IRS has been suspended since
    2019, so an unpriced title is reported unpriced."""
    if not brand:
        return JSONResponse(status_code=400, content={"detail": "Name the brand this map belongs to."})
    return pr.reach_by_language(pr.map_load(brand))


@app.get("/executions")
def executions_list(plan: str = "", kind: str = ""):
    p = plan_mod.load(plan) if plan else None
    if plan and not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    house = _house_for(p) if p else None
    out = []
    for e in execution.executions(plan, kind):
        ep = p if p else plan_mod.load(e.get("plan", ""))
        if not ep:
            continue
        out.append(execution.status(e, ep, house if p else _house_for(ep)))
    return {"executions": out,
            "summary": execution.summary(plan, p, house) if p else {},
            "kinds": list(execution.MANIFEST)}


@app.get("/execution/{exec_id}")
def execution_get(exec_id: str):
    e = execution.load(exec_id)
    if not e:
        return JSONResponse(status_code=404, content={"detail": "No such execution."})
    p = plan_mod.load(e.get("plan", ""))
    if not p:
        return JSONResponse(status_code=409,
                            content={"detail": "The plan this was briefed from no longer exists."})
    return {"execution": e, "status": execution.status(e, p, _house_for(p))}


@app.get("/execution-options/{plan_id}/{kind}")
def execution_options(plan_id: str, kind: str):
    """Everything the six-field brief can be filled from, so the client never invents a choice.

    Measures are returned grouped by role: the channel's role decides which are offerable, and
    constraining at the point of choice is better than a 400 after the fact.
    """
    p = plan_mod.load(plan_id)
    if not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    if kind not in execution.MANIFEST:
        return JSONResponse(status_code=404, content={"detail": f"No producer for {kind!r}."})
    house = _house_for(p)
    rows = {f: p["nodes"][layer]["rows"] for f, layer in execution.REFS.items()}
    by_role: dict[str, list] = {}
    for r in rows["measure"]:
        by_role.setdefault(str(r.get("role", "")).strip().lower(), []).append(r)
    return {"kind": kind, "producer": execution.MANIFEST[kind],
            "audiences": rows["audience"], "channels": rows["channel"],
            "occasions": rows["occasion"], "measures": rows["measure"],
            "measures_by_role": by_role,
            "messages": execution.message_options(house, kind),
            "house": p.get("house", "")}


@app.post("/execution-new")
def execution_new(payload: dict):
    """Brief one execution off the plan. Every field points at a plan row — an execution cannot say
    something the plan does not say, and if it needs a field the plan has no row for, that is a gap in
    the plan rather than a note in a brief."""
    p = plan_mod.load(str(payload.get("plan") or ""))
    if not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    kind = str(payload.get("kind") or "")
    if kind not in execution.MANIFEST:
        return JSONResponse(status_code=400,
                            content={"detail": f"Unknown kind {kind!r}.",
                                     "kinds": list(execution.MANIFEST)})
    e, err = execution.new_execution(p, _house_for(p), kind, payload)
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"execution": e, "status": execution.status(e, p, _house_for(p))}


@app.post("/execution-rebrief")
def execution_rebrief(payload: dict):
    """Re-resolve the brief against the plan as it stands. Status and artefacts are left alone —
    approved work stays approved; what changes is what the brief says."""
    e = execution.load(str(payload.get("id") or ""))
    if not e:
        return JSONResponse(status_code=404, content={"detail": "No such execution."})
    p = plan_mod.load(e.get("plan", ""))
    if not p:
        return JSONResponse(status_code=409, content={"detail": "The plan no longer exists."})
    house = _house_for(p)
    e, err = execution.rebrief(e, p, house)
    if err:
        # The plan has moved somewhere this execution cannot legally be briefed from. Returning 200
        # here would leave a stale badge that never clears and no way to find out why.
        return JSONResponse(status_code=409,
                            content={"detail": f"Cannot re-brief: {err}",
                                     "status": execution.status(e, p, house)})
    return {"execution": e, "status": execution.status(e, p, house)}


@app.post("/execution-recompose")
def execution_recompose(payload: dict):
    """Alias for `/execution-rebrief`.

    The screen calls it `recompose` and the backend called it `rebrief`; they are the same act — resolve
    every reference against the plan as it stands. Renaming either side would have broken the other for
    no gain, so both names answer. The 409 body is identical, and it is the one the red band prints.
    """
    return execution_rebrief(payload)


@app.post("/execution-status")
def execution_set_status(payload: dict):
    e = execution.load(str(payload.get("id") or ""))
    if not e:
        return JSONResponse(status_code=404, content={"detail": "No such execution."})
    e, err = execution.set_status(e, str(payload.get("status") or ""))
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    p = plan_mod.load(e.get("plan", ""))
    return {"execution": e,
            "status": execution.status(e, p, _house_for(p)) if p else {}}


@app.post("/execution-produce")
def execution_produce(payload: dict):
    """Hand off to the kind's producer.

    Blocking findings stop this. An execution with an unmet proof obligation is one whose whole job is
    to make a claim believable with nothing to make it believable from, and producing it anyway is how
    that reaches a shelf. Override it on the record if the risk is accepted.
    """
    e = execution.load(str(payload.get("id") or ""))
    if not e:
        return JSONResponse(status_code=404, content={"detail": "No such execution."})
    p = plan_mod.load(e.get("plan", ""))
    if not p:
        return JSONResponse(status_code=409, content={"detail": "The plan no longer exists."})
    house = _house_for(p)
    st = execution.status(e, p, house)
    if st["blocking"]:
        return JSONResponse(status_code=409,
                            content={"detail": st["blocking"][0]["detail"],
                                     "findings": st["blocking"]})
    return {"execution": e, "status": st, "brief": e["brief"],
            "producer": execution.MANIFEST[e["kind"]],
            "detail": f"Briefed. {execution.MANIFEST[e['kind']]['label']} producer takes it from here."}


# --- recording what got made (made.py) -----------------------------------------------------------

def _made_brand_project(payload: dict, house: dict | None = None) -> tuple[str, str]:
    """Best-effort brand/project for a made.record() call. Never blocks generation — a route calling
    this already has everything it needs to render; this only adds context to the ledger entry.

    Reuses `_exec_ctx()`'s own house resolution when a caller hasn't already resolved one, rather than
    asking every one of the 15 generation routes to plumb brand/project through separately — most of
    them never took a brand/project field from `payload` at all before this existed.
    """
    brand = str(payload.get("brand") or "").strip()
    proj = str(payload.get("project") or "").strip()
    if (not brand or not proj) and house is None:
        try:
            house = _exec_ctx(payload)[0]
        except Exception:
            house = None
    if house:
        brand = brand or str(house.get("brand") or "")
        proj = proj or project.of(house)
    if not brand:
        try:
            prof = brandprofile.resolve() or {}
            brand = str(prof.get("name") or prof.get("brand") or "")
        except Exception:
            pass
    return brand, proj


def _record_made(kind: str, title: str, *, url: str = "", urls: list[str] | None = None,
                  payload: dict | None = None, house: dict | None = None, ref_kind: str = "",
                  ref_id: str = "", route: str = "", note: str = "") -> None:
    """Record one generation event — one `made.py` row per candidate URL, never one row per call (see
    `made.py`'s own docstring on why). Best-effort: a ledger-write failure must never fail the actual
    generation response a person is waiting on, so every exception here is swallowed and logged rather
    than raised.
    """
    try:
        payload = payload or {}
        brand, proj = _made_brand_project(payload, house)
        targets = [u for u in (urls or [url]) if u] or [""]
        for u in targets:
            made.record(kind, title, url=u, ref_kind=ref_kind, ref_id=ref_id, brand=brand,
                        project=proj, made_by=str(payload.get("who") or ""), route=route, note=note)
    except Exception as e:
        print(f"[made] record failed for {route!r}: {e}", file=sys.stderr, flush=True)


# --- the two producers that were not already built ---------------------------------------------

def _exec_ctx(payload: dict):
    """Ground a producer in the spine, so it is not writing into the dark.

    Returns `(house, exec_brief, platform, plan)`. Every one may be None; a producer must work with
    nothing, because somebody can legitimately open POS material before they have built anything.

    **Resolution is widened deliberately.** It used to take the execution row and stop, which meant a
    producer opened outside the plan tab had no house, no platform and no plan — so it asked the person
    to retype a proposition they had already decided twice. Now, in order:

      1. the execution row named in the payload    — the strongest link, an actual briefed piece of work
      2. `house` / `platform` / `plan` ids posted directly — for producers opened off the house
      3. the newest house for the active brand     — so a producer opened cold is still this brand's

    Step 3 is the one that earns its keep. It is a guess, but it is a guess at the only house there is,
    and the alternative is a blank prompt box.
    """
    e = execution.load(str(payload.get("execution") or "")) if payload.get("execution") else None
    house = brief = plan = None
    if e:
        plan = plan_mod.load(e.get("plan", ""))
        house = _house_for(plan) if plan else None
        brief = e.get("brief")
    if not plan and payload.get("plan"):
        plan = plan_mod.load(str(payload["plan"]))
        house = house or (_house_for(plan) if plan else None)
    if not house and payload.get("house"):
        house = strategy.load(str(payload["house"]))
    if not house:
        # Cold open. The newest house belonging to the active brand.
        #
        # This read `.get("brand")` off the profile, which stores the brand under `name` — so the wanted
        # name was always empty, and the "no preference" branch picked the newest house of any brand. It
        # gave the right answer on a single-brand install and the wrong one the moment there were two.
        prof = brandprofile.resolve() or {}
        house = strategy.newest_for(str(prof.get("name") or prof.get("brand") or ""))
    # The screen sends the platform it is holding — as an id when the server owns it, or inline when it
    # is a draft that has not been adopted. `ideas.from_client` takes either and normalises the sentence,
    # which the screen calls `line` and everything on this side calls `idea`.
    platform = ideas.from_client(payload.get("platform"))
    if not platform:
        platform = execution.platform_for(house)
    return house, brief, platform, plan


@app.post("/producer-stands-on")
def producer_stands_on(payload: dict):
    """What one piece stands on, for any producer kind — the generic form of what POSM/Onground's own
    routes each compute inline. Built so Social (and later Video) can show and use the same real quote
    + real override `producers.stands_on()` already supports, instead of each producer re-deciding this
    independently. `force_typed` is real here too: see `producers.stands_on`'s own docstring on why a
    typed override has to be a deliberate, explicit act rather than a silent fallback.
    """
    kind = str(payload.get("kind") or "")
    house, _brief, platform, _plan = _exec_ctx(payload)
    typed = str(payload.get("typed") or "")
    force_typed = bool(payload.get("force_typed"))
    text, src = producers.stands_on(kind, house, platform, typed, force_typed=force_typed)
    return {"text": text, "source": src, "has_platform": bool(platform), "has_house": bool(house)}


@app.post("/posm-keyvisual")
def posm_keyvisual(payload: dict):
    """Treatment routes for a POS key visual.

    Returns `{options:[{id,name,desc,line,layout,layout_note}], note, stands_on:{text,source},
    layouts:{…}}`.

    **The brief is optional.** POS material used to demand a typed proposition, which is wrong twice:
    the person has already decided one in the messaging house, and if they typed it again the two
    copies would drift. `producers.stands_on` walks the spine — the platform's POSM expression, then the
    platform's line, then the house's POSM message, then the house's core — and only then what was
    typed. `stands_on.source` says which rung it landed on, so the screen can show it rather than
    presenting a borrowed line as a neutral default.

    Always returns usable routes; with no API key they are the declared treatment angles. `note` says
    which happened, so a quiet degradation is never mistaken for a considered answer.
    """
    house, brief, platform, plan = _exec_ctx(payload)
    typed = str(payload.get("brief") or "")
    force_typed = bool(payload.get("ignore_platform"))
    text, src = producers.stands_on("posm", house, platform, typed, force_typed=force_typed)
    try:
        n = max(1, min(6, int(payload.get("n") or 3)))
    except (TypeError, ValueError):
        n = 3
    options, note = producers.key_visual(typed, house, brief, platform, plan, n, force_typed=force_typed)
    return {"options": options, "note": note, "layouts": producers.KV_LAYOUTS,
            "stands_on": {"text": text, "source": src},
            "default_brief": text, "default_source": src}


@app.post("/posm-image")
def posm_image(payload: dict):
    """Render the HERO CUT-OUT for a POS key visual: an isolated subject on plain white, ready to mask.

    `{route|prompt|subject, hero_type, format, style, tier, line, layout, cast_id?, pack_id?,
      pack_ids?:[]}` -> `{image_url, asset_url, is_asset, provider, prompt, hero_type, layout,
      layout_note, placement, pack_used, format, ratio, read_at_m, min_cap_height_pct, gate, note}`.

    **References are attached by hero type, matching `posm.HERO_TYPES`'s own stated `needs`** —
    `endorser-with-pack`/`person-in-benefit` get cast, `endorser-with-pack`/`demonstration` also get one
    pack, `range-array` gets every signed-off pack (or an explicit `pack_ids` list) up to the reference
    cap. `person-in-benefit` and `metaphor-object` stay reference-free for the pack specifically — the
    former isolates the person on purpose, the latter's object usually isn't the pack at all. An
    explicit `cast_id`/`pack_id`/`pack_ids` always wins over the default for its hero type.

    **This returns an asset, not a finished piece, and that is the whole correction.** The route used to
    ask an image model for a composed poster with a third of the frame held open, then draw the headline
    into that space on a translucent slab. It produced both of the failure renders kept in the skill's
    exhibits, and the reason is not the wording of the prompt. Indian FMCG point-of-sale is flat-colour
    graphic design with cut-out photographic elements placed on it — a nine-layer stack. A photograph
    with words on top is a different object, and it is not what the category looks like.

    So the model is asked for the one thing it does well: a subject isolated on plain white, no
    environment, no floor line, nothing cropped by the frame, and no lettering anywhere including on
    clothing. That asset is masked and placed on a flat brand-colour field in the design tool, where the
    field *is* the space the type sits in — which is why no space is reserved here and why
    `keyline.draw_line` is gone rather than fixed.

    **The line comes back beside the picture, never inside it.** Image models garble letterforms, and
    they garble Devanagari and Telugu far worse than Latin. Every word on a POS piece is set as real
    editable type.

    **The library gate is a refusal, not a warning** — but only the refusal the medium actually
    justifies. The hero is not the pack, so an absent pack shot blocks the piece at artwork stage, not
    this render; the hero and the field can proceed while the pack is sourced. Three hero types are the
    exception, because for them the library reference *is* the subject: an endorser and a
    person-in-benefit both need an approved cast frame to pin likeness (a hallucinated person is the
    wrong thing to generate — see `posm.gate`'s docstring for the real failure that made this a rule
    rather than a suggestion), and a range array needs the packs.
    """
    if not _have_image():
        return JSONResponse(status_code=501, content={"detail": _NO_IMAGE})
    house, brief, platform, plan = _exec_ctx(payload)

    hero_type = str(payload.get("hero_type") or "").strip()
    gate = posm.gate(hero_type)
    if not gate["can_render_assets"]:
        blocked = gate["asset_blocks"][0]
        return JSONResponse(status_code=409, content={
            "detail": f"{blocked['what']} {blocked['do']}", "gate": gate})

    # `route` is last and is checked for being text at all. The POS panel sends `route: kv.id` — the
    # string "kv1" — alongside `prompt: kv.desc`, and the old ordering took `route` first, so every
    # render this route ever made was briefed on a two-character identifier. It survived review because
    # the model always returns *something* for any input.
    subject = str(payload.get("hero_brief") or payload.get("subject") or
                  payload.get("prompt") or "").strip()
    route_txt = str(payload.get("route") or "").strip()
    if not subject and " " in route_txt and len(route_txt) > 12:
        subject = route_txt
    stood, src = producers.stands_on("posm", house, platform, str(payload.get("brief") or ""))

    # **The proposition is not a subject, and falling back to it is not a kindness.** This route used to
    # drop `stands_on` text in when nothing else was given, which was survivable while it was generating
    # a scene and is not survivable now. Asked to cut out "before a mother makes the first cup, 500
    # people have already checked the milk that morning", the model illustrated the sentence literally —
    # tiny figurines with magnifying glasses standing on a carton. A cut-out brief has to describe
    # something physical, and what the piece is *about* is a different question from what is *in frame*.
    if not subject:
        return JSONResponse(status_code=400, content={
            "detail": ("Nothing physical to cut out. A hero brief describes a subject — a person, an "
                       "object, a demonstration — not the proposition. Draft the key visual first so "
                       "there is a hero, or pick a treatment route." +
                       (f' This piece stands on: "{stood}" ({src}) — that is what it is about, not '
                        f'what is in frame.' if stood else "")),
            "stands_on": {"text": stood, "source": src}})

    # The pack is composited from the library, never described in words — but only check for that
    # against an UNSTRUCTURED subject. A route drafted by `key_visual()` already picked a real hero
    # type from `posm.HERO_TYPES`, and the prompt that drafted it says "the pack is always present and
    # never the hero" — so its `desc` correctly mentions the pack being masked and locked at the base
    # on almost every route, describing the STANDARD LAYOUT, not naming the pack as the subject. A blind
    # word-match against that full description refused nearly every real route this endpoint ever saw.
    # `hero_type` in `posm.HERO_TYPES` means this subject came from a vetted route; the library
    # requirement for the two pack-centric types (`endorser-with-pack`, `range-array`) is already
    # enforced above, by `posm.gate(hero_type)` — this check is only for a raw, routeless override.
    if hero_type not in posm.HERO_TYPES and posm.looks_like_pack(subject):
        return JSONResponse(status_code=409, content={
            # Was four sentences of reasoning with the action buried in the third. A refusal a person
            # meets mid-task needs the next step first; the why can follow and be skipped. The
            # sign-off is named because uploading alone is not enough — generation only reads
            # signed-off items, so a person who uploads and retries hits a second refusal.
            "detail": ("Upload the pack shot in Memory, sign it off, and select it — then it is "
                       "composited onto the piece rather than drawn. Make the hero something that is "
                       "not the pack: the pack is always present on a POS piece and never the subject. "
                       "A generated pack comes back with the proportions, the cap and the label "
                       "geometry subtly wrong, and brand lettering drawn on."),
            "gate": gate})
    src_note = "the chosen route"

    position = str(payload.get("layout") or payload.get("type_position") or "type-locked-base")
    if position not in posm.TYPE_POSITIONS:
        position = "type-locked-base"
    fmt = str(payload.get("format") or "")
    spec = posm.spec(fmt)
    line = str(payload.get("line") or "").strip()

    # The asset is generated at the master ratio, not the piece's. A 12:1 shelf strip is a re-flow of the
    # master's layers into a wider canvas — the cut-out inside it is the same cut-out. Rendering one
    # subject per format is how eleven pieces end up looking like eleven brands.
    ratio = posm.MASTER_RATIO
    style = str(payload.get("style") or "").lower()

    # `mode` is a production constraint, not a style preference — see `posm.production_mode`'s own
    # docstring. A caller can override it (`payload["mode"]`), but the format's own substrate decides by
    # default, so a wall painting cannot silently come back photographic just because nobody remembered
    # to ask for the flat-colour register. `paintable` forces the vector/flat register regardless of
    # what `style` asked for — a photograph is not a style choice on a substrate that cannot hold one.
    mode = str(payload.get("mode") or "").strip().lower()
    prod = posm.production_mode(fmt) if fmt else {"mode": "rich", "why": ""}
    if mode not in ("paintable", "rich"):
        mode = prod["mode"]
    if mode == "paintable":
        style = "vector"

    # **`_IMG_STYLES` is deliberately not used here.** Those strings describe whole scenes — "an
    # authentic contemporary Indian home, kitchen or dawn dairy-farm setting", "on a clean minimal
    # surface, soft reflections" — and a cut-out is the absence of a scene. Injecting one fought the
    # isolation clauses and the scene won: the first render came back on a graduated backdrop with a
    # cast shadow and a floor line, all three of which the prompt explicitly forbids.
    #
    # `cutout_prompt` already specifies the lighting, the focus and the background, because for this job
    # those are not style choices. Only a non-photographic register is worth carrying, and then as one
    # clause rather than a paragraph.
    _REGISTERS = {
        "vector": "Rendered as flat spot-colour vector artwork — bold flat shapes, hard edges, no "
                  "gradient, no soft shadow, no photographic texture anywhere. Reproducible by a sign "
                  "painter or a screen print, not a photograph.",
        "infographic": "Rendered as a simple flat graphic rather than a photograph.",
        "claymation": "Sculpted from modelling clay with visible fingerprints and tool marks, shot as a "
                      "miniature practical object.",
        "animation-3d": "Rendered as a stylised 3D animation asset rather than a photograph.",
    }
    prompt = posm.cutout_prompt(subject, style_note=_REGISTERS.get(style, ""),
                                type_brief=posm.hero_type_brief(hero_type))

    # An approved cast or actor frame pins likeness in a way no description can. This is the path proven
    # to work: a film frame in, an isolated cut-out on white out, same face, same clothing, no text.
    # `person-in-benefit` joined `endorser-with-pack` here after a real failure (see posm.gate's
    # docstring): a purely-described person is a hallucinated one, and for some subjects — a child was
    # the actual case — an image provider's own safety filtering distorts the face rather than refusing
    # cleanly. `posm.gate()` already refuses both hero types at render time without this reference, so
    # reaching this line means one exists.
    #
    # Real bug found live, found by a user directly comparing this route's output against `/studio-shot`:
    # this only ever attached the CAST reference — never the pack, for ANY hero type, including the ones
    # `posm.HERO_TYPES` itself already says need it. `endorser-with-pack`'s own `needs` is cast AND the
    # pack it holds; `range-array`'s is "every pack as a library reference"; `demonstration` needs the
    # mechanism to actually show. All three were generating the product from a text description alone —
    # hallucinated, unbranded, exactly the failure this whole reference mechanism exists to prevent —
    # while the REAL pack only ever reached the piece via `/posm-assemble`'s small corner card, completely
    # disconnected from the "hero". `person-in-benefit` and `metaphor-object` are correctly left alone:
    # the first isolates the person on purpose (the pack is a separate element by design), the second's
    # object usually isn't the pack at all.
    refs, roles = [], []
    if hero_type in ("endorser-with-pack", "person-in-benefit") or payload.get("cast_id"):
        cast_id = str(payload.get("cast_id") or "")
        if cast_id:
            row = library.get(cast_id)
            u = row["url"] if row and row.get("kind") in ("cast", "actor") and row.get("signed_off") else ""
            if u:
                refs.append(u)
                roles.append("the exact person — identical face, hair, skin tone, age and build")
        if not refs:
            # Pre-existing bug found while touching this block: an unconditional `break` at the end of
            # the loop body exited after checking only 'cast', never falling back to 'actor' when 'cast'
            # came up empty. Fixed — the break now only fires once a reference is actually found. Runs
            # whenever no cast landed yet — whether none was requested, or an explicit `cast_id` failed
            # to resolve — so a bad id degrades to "use the most recent" rather than "use nothing".
            for kind in ("cast", "actor"):
                u = library.reference_url(kind)
                if u:
                    refs.append(u)
                    roles.append("the exact person — identical face, hair, skin tone, age and build")
                    break

    want_multi_pack = hero_type == "range-array"
    want_one_pack = hero_type in ("endorser-with-pack", "demonstration") or bool(payload.get("pack_id"))
    pack_ids = [str(p) for p in (payload.get("pack_ids") or []) if p]
    if not pack_ids and payload.get("pack_id"):
        pack_ids = [str(payload["pack_id"])]
    if want_multi_pack:
        if not pack_ids:
            pack_ids = [r["id"] for r in library.items("pack", signed_only=True)]
        for pid in pack_ids:
            if len(refs) >= 3:
                break
            row = library.get(pid)
            u = row["url"] if row and row.get("kind") == "pack" and row.get("signed_off") else ""
            if u and u not in refs:
                refs.append(u)
                # Named per pack, not the same generic sentence repeated — found live: giving every
                # pack reference in a range-array shot the identical unnamed role ("one of the real
                # packs...") produced two structurally-correct pouches with GENERIC label art on both,
                # neither matching either real product. Naming which reference is which is a real
                # fidelity attempt at telling two distinct labels apart, not proven fixed by itself —
                # holding fine label detail across multiple simultaneous references may simply be
                # past what this model does reliably, same as it is for most image models today.
                pname = str(row.get("name") or "this pack").strip()
                roles.append(f"the real {pname!r} pack, exactly as shown — reproduce ITS OWN label, "
                             f"colours, type and proportions faithfully, distinct from any other pack "
                             f"reference here, never redrawn or merged with another")
    elif want_one_pack and len(refs) < 3:
        pid = pack_ids[0] if pack_ids else ""
        u = ""
        if pid:
            row = library.get(pid)
            u = row["url"] if row and row.get("kind") == "pack" and row.get("signed_off") else ""
        if not u:
            u = library.reference_url("pack")
        if u:
            refs.append(u)
            roles.append("the exact product pack — reproduce it faithfully, same label, colours, type "
                         "and proportions, never redrawn")
    pack_used = any("pack" in r or "range" in r for r in roles)

    eng = _engine(payload, "image")
    model, size, tier = _img_tier(payload, "pro")

    # Several candidates in one call, not one draft repeatedly overwritten — a route can name a hero
    # type correctly and the model can still draw the wrong build/age/pose for it on any single try, and
    # the only real check on that is comparing options, the same way a route or a scamp is compared
    # rather than accepted on the first draft. Capped at 4: real generation cost per candidate.
    n = max(1, min(4, int(payload.get("n") or 1)))

    def _gen_one(idx: int) -> tuple:
        p = prompt
        if n > 1:
            p += (f" Candidate {idx + 1} of {n} — a distinct pose, expression or framing of the SAME "
                  f"subject; same identity, age, build and setting, not a different person.")
        u, prov = "", ""
        role_note = "; ".join(f"reference image {i + 1} shows {r}" for i, r in enumerate(roles))
        if _use(eng, "google"):
            prov = "google"
            if refs:
                u = gemini.image_from_reference(f"{role_note}. " + p, refs, ratio=ratio, model=model,
                                                size=size)
            if not u:
                u = gemini.image(p, ratio=ratio, model=model, size=size)
        if not u and _use(eng, "fal"):
            prov = "fal"
            # SECURITY/QUALITY audit (round 83, confirmed independently twice): this used to call plain
            # text_to_image on the fal fallback, silently dropping every cast/pack reference collected
            # above while the response still reported the reference as "used" — a route that explicitly
            # exists to hold identity/pack fidelity regenerating from a blind text description one
            # fallback hop later. Try the reference-aware fal call first when references exist.
            if refs:
                u = creative.image_from_reference(f"{role_note}. " + p, refs, ratio=ratio) or ""
            if not u:
                u = creative.text_to_image(p, ratio=ratio)["url"]
        return u, prov

    candidates, url, provider = [], "", ""
    for i in range(n):
        u, prov = _gen_one(i)
        if u:
            candidates.append({"image_url": u, "provider": prov})
            if not url:
                url, provider = u, prov
    if not url:
        return JSONResponse(status_code=502, content={
            "detail": "Both image providers refused this cut-out — check credits for your Google and "
                      "fal keys (see render-log.txt)."})

    sheet = posm.adaptation(fmt, line=line, type_position=position) if spec else {}
    note = ("This is the hero cut-out, not the finished piece: mask it out of the white and place it on "
            "the flat brand-colour field with the pack, the type and the brand block. "
            + (gate["note"] if not gate["can_assemble_master"] else ""))

    _record_made("posm_hero", f"{hero_type or 'POSM'} hero cut-out", payload=payload, house=house,
                 urls=[c["image_url"] for c in candidates], route="/posm-image")
    return {
        "image_url": url, "images": candidates, "asset_url": url, "is_asset": True,
        "asset": "hero cut-out",
        "plate_url": "", "typeset": False, "provider": provider, "prompt": prompt, "tier": tier,
        "from_reference": bool(refs), "hero_type": hero_type,
        # `pack_used` here means the hero itself already carries a faithful pack — /posm-assemble's
        # corner card is insurance for the hero types that DON'T show the pack (person-in-benefit,
        # metaphor-object), and redundant clutter for the ones that now do. Reported so the caller can
        # skip it, same reasoning as `plate_used` already being reported for continuity elsewhere.
        "pack_used": pack_used,
        "line": line, "layout": position, "layout_note": posm.TYPE_POSITIONS[position],
        "placement": posm.TYPE_POSITIONS[position],
        "mode": mode, "mode_why": prod["why"] if mode == "paintable" else "",
        "format": fmt, "ratio": ratio, "print_ratio": spec.get("ratio", ""), "style": style,
        "subject": subject, "stands_on": {"text": stood, "source": src_note},
        "read_at_m": spec.get("read_at", 0.0),
        "min_cap_height_pct": sheet.get("cap_height_pct", 0.0),
        "cap_height_mm": sheet.get("cap_height_mm", 0.0),
        "words_allowed": sheet.get("words_allowed", []),
        "adaptation": sheet, "gate": gate, "note": note,
    }


@app.post("/posm-backdrop")
def posm_backdrop(payload: dict):
    """Render a PLAIN ENVIRONMENT for the assembled piece to sit on — a green backdrop, a home kitchen,
    whatever the route calls for. `{brief, format?, style?}` -> `{image_url, provider, prompt}`.

    Generated with nothing in it — no person, no product, no pack, no text — same isolation discipline
    as `posm.cutout_prompt`, in the opposite direction: that asks for a subject with no environment,
    this asks for an environment with no subject. Asking one call for both together is the documented
    failure `posm.py`'s own history already has on record (a graduated backdrop with a cast shadow and
    a floor line, fighting the isolation clauses) — generating them apart and compositing in
    `keyvisual.assemble` is what avoids repeating it.
    """
    if not _have_image():
        return JSONResponse(status_code=501, content={"detail": _NO_IMAGE})
    fmt = str(payload.get("format") or "")
    if fmt and posm.production_mode(fmt)["mode"] == "paintable":
        return JSONResponse(status_code=409, content={
            "detail": f"{posm.spec(fmt).get('label', fmt)} is hand-produced at scale — "
                      f"{posm.production_mode(fmt)['why']} A photographic backdrop cannot survive that; "
                      f"use a flat field colour instead (pass field_hex to /posm-assemble, no backdrop)."})
    brief = str(payload.get("brief") or "").strip()
    if not brief:
        return JSONResponse(status_code=400, content={
            "detail": "Describe the environment — 'a green studio backdrop', 'a home kitchen counter "
                      "at dawn'. This generates the backdrop alone; the hero is composited onto it "
                      "afterwards, never generated into the same image."})
    style = str(payload.get("style") or "").lower()
    _REGISTERS = {"vector": "Rendered as a flat vector illustration with bold clean shapes.",
                  "infographic": "Rendered as a simple flat graphic rather than a photograph."}
    prompt = keyvisual.backdrop_prompt(brief, style_note=_REGISTERS.get(style, ""))
    eng = _engine(payload, "image")
    model, size, _tier = _img_tier(payload)
    url, provider = "", ""
    if _use(eng, "google"):
        url, provider = gemini.image(prompt, ratio=posm.MASTER_RATIO, model=model, size=size), "google"
    if not url and _use(eng, "fal"):
        provider = "fal"
        url = creative.text_to_image(prompt, ratio=posm.MASTER_RATIO)["url"]
    if not url:
        return JSONResponse(status_code=502, content={
            "detail": "Both image providers refused the backdrop — check credits (see render-log.txt)."})
    _record_made("posm_backdrop", brief[:80], url=url, payload=payload, route="/posm-backdrop")
    return {"image_url": url, "provider": provider, "prompt": prompt}


@app.post("/studio-shot")
def studio_shot(payload: dict):
    """The shared photoshoot primitive. Every "shoot this differently" need this studio has —
    a model at another angle, a pack in a styled context, a model and a pack together in one
    consumption shot — is the same request shape: which locked references to combine, what is
    happening, how it is framed. One route rather than three, because they are one thing wearing
    different clothes. Category-agnostic on purpose: `pack_id` covers shelf packaging, `product_id`
    covers everything a "pack" doesn't fit — a garment, an accessory, a device — so the same primitive
    that shoots a milk carton also shoots a jacket, without either category's wording leaking into
    the other's.

    `{cast_id?, pack_id?, product_id?, plate_id?, sketch_url?, base_image_url?, extra_refs?:[],
      recompose?, action, angle?, mode?, isolate_kind?, ratio?, style?}` ->
    `{image_url, provider, mode, refs_used, prompt, base_used, sketch_used, recomposed}`.

    `sketch_url` is a layout-only reference to the approved composition scamp (never library-gated —
    scamps aren't library items). `base_image_url` plus `mode='cutout'` isolates one named element out
    of a prior shot; plus `mode='scene'` (default) adjusts one named thing in it; `recompose=True` with
    `base_image_url` and/or `extra_refs` composes a locked family of elements into a NEW shape instead
    of editing or isolating — three distinct jobs sharing one mechanism, told apart explicitly rather
    than inferred, because getting this wrong sends the model an isolation instruction dressed as an
    edit or vice versa.

    **At least one locked reference is required.** A request naming none of `cast_id`/`pack_id`/
    `product_id`/`plate_id` is not this route's job — that is `/posm-image` (a hallucinated hero) or
    `/posm-backdrop` (a hallucinated environment), both cheaper and already honest about producing an
    invented subject. Answering it here anyway would silently reintroduce the exact fidelity problem
    locked references exist to prevent.

    **`mode` decides what kind of shot this is, not a style preference.** `'cutout'` (default) isolates
    the result on plain white, ready to mask and place — same discipline as `posm.cutout_prompt`, so a
    model's photoshoot angle feeds `/posm-assemble` exactly like today's hero cut-out does. `'scene'`
    renders a complete photographic moment with real context (a splash, a table, a hand) — for a styled
    pack shot or a consumption shot, which ARE the finished visual, not a layer for further compositing.

    **This is deliberately not POSM-specific.** The same combination — a locked cast reference, a locked
    pack reference, an action — is exactly what a video frame sometimes needs too (a scene calling for
    "the mother pouring the pack into a glass"), so this is a shared building block `/scene-still` can
    also call, not a second implementation of the same idea.

    A combined shot (more than one reference) is the hardest case for fidelity — both subjects have to
    survive the same generation call, and pack fidelity specifically is the one thing already proven
    fragile in this app. Expect it to need more retries than a solo angle shot; nothing here pretends
    otherwise.

    **`isolate_kind='text'` is the one exception to cutout mode's own "no text" rule.** Every other
    cutout call means the isolated subject should have no on-screen lettering — but isolating the
    headline TEXT itself has that instruction fighting the action in the same prompt otherwise. Naming
    it explicitly switches the framing to a typographic reproduction instead of a photograph.
    """
    if not _have_image():
        return JSONResponse(status_code=501, content={"detail": _NO_IMAGE})
    action = str(payload.get("action") or "").strip()
    if not action:
        return JSONResponse(status_code=400, content={
            "detail": "Describe what's happening in the shot — an angle, a pose, an action."})
    mode = str(payload.get("mode") or "cutout").strip().lower()
    if mode not in ("cutout", "scene"):
        mode = "cutout"

    refs, roles = [], []

    def _add(field, kinds, role_text):
        rid = str(payload.get(field) or "")
        if not rid:
            return
        row = library.get(rid)
        if row and row.get("kind") in kinds and row.get("signed_off") and row.get("url"):
            refs.append(row["url"])
            roles.append(role_text)

    _add("cast_id", ("cast", "actor"),
         "the exact person — identical face, hair, skin tone, body type, age, and clothing unless the "
         "action below changes it")
    _add("pack_id", ("pack",),
         "the exact product pack — reproduce it faithfully, same label, colours, type and proportions, "
         "never redrawn or reimagined")
    # `product_id` is `pack_id`'s category-agnostic sibling — a garment, an accessory, a device, any
    # item a "pack" kind doesn't fit. Same mechanism, same fidelity reasoning, wording that doesn't
    # assume packaging: an image model gets a jacket's cut and fabric wrong the same way it gets a
    # carton's label wrong, for the same reason (drawn from a description, not a real photo).
    _add("product_id", ("product",),
         "the exact product — reproduce it faithfully, same colours, materials, shape and proportions, "
         "never redrawn or reimagined")
    _add("plate_id", ("plate",),
         "the location — reuse the same room or place, the same time of day and light")

    # The approved composition sketch — layout only, never style. Scamps are deliberately rough
    # graphite pencil drawings (`posm.scamp_prompt`), and a reference image's own visual register
    # tends to leak into a generation unless explicitly refused — the risk named out loud before this
    # was built: the model reading "match this reference" as "render in pencil" rather than "stand the
    # subject here, put the pack there". The role text below exists specifically to refuse that.
    sketch_url = str(payload.get("sketch_url") or "").strip()
    if sketch_url:
        refs.append(sketch_url)
        roles.append("the approved layout sketch — a rough pencil drawing showing WHERE things go "
                     "only: where the subject stands, where the pack sits, where the headline area "
                     "is. Match that arrangement. Ignore its pencil linework, monochrome tone and "
                     "paper texture entirely — none of that belongs in a photograph")

    # The drafted location backdrop, as a raw URL — never a library item (nothing here gets signed
    # off), so it needs its own field rather than `plate_id`. Real gap found live: this backdrop has
    # always been generated as its own asset and previewed, but nothing ever sent it here — the studio
    # shot hallucinated its own setting from the action text regardless of what had been drafted.
    plate_url = str(payload.get("plate_url") or "").strip()
    if plate_url:
        refs.append(plate_url)
        roles.append("the drafted location — reuse this exact room or place, faithfully, its light and "
                     "surfaces unchanged, never redrawn or replaced with an invented setting")

    # `recompose` — a locked family of elements re-laid into a NEW shape, not an edit and not an
    # isolation. `base_image_url` here is a style/identity anchor for the whole family, and
    # `extra_refs` are the individually-isolated elements (see /studio-shot's `mode='cutout'` +
    # `base_image_url` combination, used to produce them in the first place) composed together fresh.
    recompose = bool(payload.get("recompose"))
    # An adjustment to an EXISTING shot, or an isolation of ONE element out of it — two different
    # jobs sharing one mechanism (a prior image as a locked reference), told apart by `mode`: `'scene'`
    # keeps the whole picture and changes one named thing; `'cutout'` discards everything except the
    # one element the action names. Neither is `recompose` — a fresh composition, not an edit of this
    # exact picture.
    # Real defect found live: cutout mode unconditionally told the model "no text, lettering, logos" —
    # right, discarding stray on-pack type is exactly what isolating a PACK or a PERSON should do, but
    # isolating the headline TEXT itself is the one case where that blanket instruction directly
    # contradicts the action in the same prompt ("isolate: just the headline text") and the model had
    # no way to tell which one to believe. `isolate_kind` says which ELEMENT_KINDS entry this call is
    # isolating, so the text-specific branches below can stop refusing the very thing being asked for.
    isolate_kind = str(payload.get("isolate_kind") or "").strip().lower()
    base_url = str(payload.get("base_image_url") or "").strip()
    # `keep_same` — a chained edit of an ALREADY-isolated element (mode stays 'cutout' so it's still
    # keyed onto a clean backdrop), told apart from a fresh isolation out of a busy scene. Without this
    # flag, adjusting an isolated pack cutout ("add the splash back") got the ISOLATE role text instead
    # — "discard everything else" — which fights an adjustment that wants to keep what's already there.
    keep_same = bool(payload.get("keep_same"))
    if base_url:
        refs.append(base_url)
        if recompose:
            roles.append("the approved family's master shot — same subject, same styling, same mood. "
                         "Recompose them into the NEW shape this call asks for; this is not a crop or "
                         "an edit of this exact picture")
        elif mode == "cutout" and not keep_same and isolate_kind == "text":
            roles.append("the approved scene to isolate ONE element from — reproduce ONLY the "
                         "lettering/headline text exactly as it appears here (same letterforms, "
                         "spacing, weight and colour, not redrawn or reworded), discarding everything "
                         "else in this reference — the background, the pack, any person, any other "
                         "object")
        elif mode == "cutout" and not keep_same:
            roles.append("the approved scene to isolate ONE element from — reproduce ONLY the element "
                         "the action below names, exactly as it appears here (same identity, same "
                         "lighting, same colour), discarding everything else in this reference — the "
                         "background, any other object, any text")
        else:
            roles.append("the exact shot to adjust — keep the framing, subject, pose, lighting and "
                         "background identical to this image except for what the adjustment note "
                         "below changes")

    # The individually-isolated elements a `recompose` call composes together — each already carries
    # its own identity/fidelity from however it was produced, so the role here is deliberately plain:
    # reproduce it, don't reinterpret it.
    extra_refs = [str(u).strip() for u in (payload.get("extra_refs") or []) if str(u).strip()]
    for u in extra_refs:
        refs.append(u)
        roles.append("a locked element from the same approved family — reproduce it faithfully, "
                     "unchanged, composed into the new shape")

    # Most image providers cap references at three total (noted elsewhere in this file for Gemini
    # specifically) — silently sending more risks the provider ignoring some of them with no error, a
    # failure mode worse than refusing here. Priority follows build order above: identity/pack/location
    # first (the fidelity this route exists for), then the sketch, then the base/isolation image, then
    # any extra elements — in practice a single call only ever populates two or three of these at once.
    if len(refs) > 3:
        refs, roles = refs[:3], roles[:3]

    if not refs:
        return JSONResponse(status_code=400, content={
            "detail": "No locked reference to shoot from — give at least one of cast_id, pack_id, "
                      "product_id or plate_id. Use /posm-image or /posm-backdrop for a hallucinated "
                      "subject instead."})

    ANGLES = {
        "full-body": "Full-body shot, standing, feet visible, facing camera or turned slightly.",
        "three-quarter": "Three-quarter / waist-up shot.",
        "tight-crop": "Tight crop — head and shoulders, or hands and product close up.",
    }
    angle = str(payload.get("angle") or "").strip().lower()
    style = str(payload.get("style") or "").lower()

    # **`_IMG_STYLES` is deliberately not used here** — the same correction `/posm-image` already
    # carries in its own comments, which this route was written without. Those strings describe whole
    # SCENES: the "real" one ends "Authentic contemporary Indian home, kitchen, or dawn dairy-farm
    # setting **with real people and natural expressions**". A studio shot's entire point is that the
    # CALLER says what is in the frame, so injecting a cast and a location fights the brief instead of
    # serving it — and the brief loses, exactly as it did for POSM's scene strings.
    #
    # Found live, and it cost a person five regenerations: asked for "heritage daily health packet,
    # glass of milk by its side and splash below it. No human, no backdrop, no background. Nothing
    # else", the route kept returning a woman in a kitchen — because while the action said no human and
    # no backdrop, the style string appended immediately after was asking for both. The registers below
    # carry photographic craft and say nothing about setting or cast.
    _SHOT_REGISTERS = {
        "real": "Photorealistic commercial photography: full-frame DSLR, 50mm lens, shallow depth of "
                "field, crisp sharp focus, soft directional light, true-to-life colour and texture. "
                "Not illustrated, not cartoon, not CGI.",
        "product": "High-end tabletop product photography: controlled studio lighting, clean surface, "
                   "gentle reflections, no people.",
        "vector": "Flat spot-colour vector artwork — bold flat shapes, hard edges, no gradient, no soft "
                  "shadow, no photographic texture.",
        "infographic": "Rendered as a simple flat graphic rather than a photograph.",
        "claymation": "Sculpted from modelling clay with visible tool marks, shot as a miniature "
                      "practical object.",
        "animation-3d": "Rendered as a stylised 3D asset rather than a photograph.",
    }
    craft = _SHOT_REGISTERS.get(style, _SHOT_REGISTERS["real"])

    role_lines = "; ".join(f"reference image {i + 1} shows {r}" for i, r in enumerate(roles))
    parts = [f"{role_lines}."]
    if recompose:
        parts.append(f"Recompose this same approved family into a new layout: {action}.")
    elif base_url and mode == "cutout" and not keep_same:
        parts.append(f"Isolate from the reference: {action}.")
    elif base_url:
        parts.append(f"Adjustment to the reference shot above — change only this: {action}.")
    else:
        parts.append(f"Action: {action}.")
    if angle in ANGLES:
        parts.append(ANGLES[angle])
    # No real pack among the references means any packaging in this frame would be invented — and an
    # invented carton comes back wearing somebody's brand, a competitor's as often as not. With a pack
    # or product reference attached the opposite is true: the packaging is the point, and it is real.
    # Real bug found live, twice — first on `recompose`, then again on a plain adjust of a new-shape
    # image that already had a pack baked into it: the note said "add a milk splash below the pack"
    # and the very next sentence told the model there must be no packaging anywhere in frame. Both are
    # the same root cause — a call whose base image already established what's in frame (adjusting it,
    # or recomposing a locked family into a new shape) had this appended regardless, fighting whatever
    # packaging that base image already carries. `mode == 'scene' and base_url` covers the adjust case
    # generally rather than patching each caller with its own `pack_id`; `mode == 'cutout'` (isolate) is
    # deliberately excluded — pulling just the person out of a scene still wants packaging refused so it
    # can't leak into that one element.
    if not (payload.get("pack_id") or payload.get("product_id") or recompose
            or (base_url and (mode == "scene" or keep_same))):
        parts.append(_NO_PACKAGING)
    # Real defect found live, first time this rendered end to end: `/posm-typeset` reserves a type
    # zone purely from canvas geometry, with no idea where the pack or the subject actually sit in the
    # photo — a headline landed set squarely across the pack's own label. The photo is the one place
    # that CAN leave room, since it's composed before the type is; this is that instruction.
    ZONE_ROOM = {
        "type-locked-base": "the bottom third of the frame",
        "type-over-top": "the top third of the frame",
        "type-beside": "the left third of the frame",
        "type-only": "the middle of the frame",
        "product-only": "",
    }
    type_position = str(payload.get("type_position") or "").strip()
    if mode == "scene" and type_position in ZONE_ROOM and ZONE_ROOM[type_position]:
        parts.append(f"Leave {ZONE_ROOM[type_position]} visually clear and uncluttered — plain surface "
                     f"or soft out-of-focus background there, nothing crossing through it. Real type "
                     f"will be set into that space afterward; do not put the pack, a hand, or anything "
                     f"else important there.")
    if mode == "cutout":
        # Mid-grey, not white — same backdrop `posm.cutout_prompt` asks for and the compositor keys
        # back out. See `posm.CUTOUT_BACKDROP`: a matte needs a backdrop the subject does not contain,
        # and a dairy brand's subjects are white about half the time. Shared by every cutout kind,
        # including text — a flat grey field is still the right ground to key it off of.
        parts.append(
            f"Isolated on a plain flat mid-grey ({posm.CUTOUT_BACKDROP}, 50% grey) seamless background "
            "— an even studio backdrop of that one colour, edge to edge.")
        if isolate_kind != "text":
            # Real bug found live, on top of the first one: the trailing sentence below already told
            # the model this was a typographic reproduction, not a photograph — but everything in THIS
            # block still described a physical object under studio lights ("floats", "cast shadow", "no
            # reflection", "no mirrored floor") one sentence earlier in the SAME prompt. A headline has
            # no shadow to cast and nothing to float — asking for both readings back to back is the
            # same class of self-contradiction the isolate_kind fix was supposed to remove, just moved
            # one sentence over rather than actually removed. Gated out for text; unchanged for
            # everything else a cutout call isolates.
            parts.append(
                "Even, soft, directional studio lighting. Sharp focus, no environment, no set, no props "
                "beyond what the action names, no floor line, no cast shadow on the background. The "
                "subject FLOATS on the flat backdrop: no surface or table under it, no reflection, no "
                "mirrored floor, no gradient — a reflective surface survives the key as grey debris "
                "under the subject.")
        if isolate_kind == "text":
            # The opposite framing from every other element: this is the one call where the thing
            # being kept IS text, so the register is typographic reproduction, not a photograph of an
            # object. Asking for "Photorealistic" here is itself a mismatch — there is no photorealistic
            # rendering of a headline, only a faithful or unfaithful one — which is likely why this kind
            # kept coming back as the whole scene: the model had nothing photographic to isolate.
            parts.append(
                "Reproduce the lettering exactly as it appears in the reference — same letterforms, "
                "spacing, weight, size, colour and any casing or accents, not redrawn, not reworded, "
                "not re-lettered in a different font. Flat, crisp typographic reproduction, not a "
                "photograph. No object, pack, person, logo, or background detail of any kind — only "
                "the text.")
        else:
            parts.append("Photorealistic. No text, lettering, logos or watermarks.")
    else:
        parts.append(craft)
        # The frame is closed by default. Without this the model treats the action as a starting point
        # and fills the rest of the picture with whatever the category suggests — a kitchen, a family.
        parts.append(
            "Include ONLY the subjects named above and in the action. Do NOT add any person, model, "
            "hands, room, furniture, or props that were not named. If the action names no environment, "
            "use a plain seamless studio background.")
        parts.append("No on-screen text, captions, logos or watermarks.")
    prompt = " ".join(p for p in parts if p)

    eng = _engine(payload, "image")
    model, size, tier = _img_tier(payload, "pro")
    ratio = str(payload.get("ratio") or posm.MASTER_RATIO)
    url, provider = "", ""
    if _use(eng, "google"):
        url, provider = gemini.image_from_reference(prompt, refs, ratio=ratio, model=model,
                                                     size=size), "google"
    if not url and _use(eng, "fal"):
        provider = "fal"
        url = creative.image_from_reference(prompt, refs, ratio=ratio, seed=payload.get("seed"))
    if not url:
        return JSONResponse(status_code=502, content={
            "detail": "Both image providers refused this shot — check credits (see render-log.txt)."})
    _record_made("studio_shot", f"Studio shot — {action[:60]}" if action else "Studio shot", url=url,
                 payload=payload, route="/studio-shot")
    return {"image_url": url, "provider": provider, "tier": tier, "mode": mode,
            "refs_used": roles, "prompt": prompt, "base_used": bool(base_url),
            "sketch_used": bool(sketch_url), "recomposed": recompose}


@app.post("/posm-scene")
def posm_scene(payload: dict):
    """The other lane: one generated image, everything baked in — people, environment, product,
    headline and logo together. `{brief, format, headline?, cast_ids?:[], pack_id?, product_id?, style?}`
    (`product_id` is `pack_id`'s category-agnostic sibling — a garment, an accessory, anything a "pack"
    kind doesn't fit) ->
    `{image_url, provider, refs_used, has_cast, note}`.

    This is the opposite choice from `/posm-image` + `/posm-assemble` on purpose, for the creative this
    codebase's cutout approach cannot produce: several real people composed naturally together in an
    environment — a family, a classroom, a handover — where a flat field with one cutout on it reads as
    the wrong object entirely. Baking the headline and logo into the one generation (rather than
    compositing them afterward) was a deliberate choice made with the risk named out loud: this is
    closer to the single-prompt approach `posm.py` was rewritten away from once already, because a
    model draws garbled letterforms (worse in Devanagari and Telugu than Latin) and a redrawn logo is
    never the real lock-up. Nothing here pretends otherwise — check the rendered type and mark before
    using this at scale, the same way any AI-drawn text needs checking anywhere else in this studio.

    **Identity needs a real photo to pin to, same as `/cast-reference` already requires for film.**
    `cast_ids` lets several named library entries stand for several different people (Gemini caps
    references at three total, shared with the pack) — pass none and the single most-recently-signed-off
    cast frame is used, same default as `library.shot_references`. With zero signed-off cast/actor
    entries in the library (true on this account today), every person in the scene is hallucinated, not
    referenced, and `has_cast` comes back false so the caller can say so rather than imply otherwise.

    The logo is described in text, not passed as a fourth reference image — a real photo of a real
    person is the harder thing to get right and the more valuable use of a scarce reference slot; a
    text-described logo is approximate on purpose, a trade made visibly rather than silently.
    """
    if not _have_image():
        return JSONResponse(status_code=501, content={"detail": _NO_IMAGE})
    fmt = str(payload.get("format") or "")
    if fmt and posm.production_mode(fmt)["mode"] == "paintable":
        return JSONResponse(status_code=409, content={
            "detail": f"{posm.spec(fmt).get('label', fmt)} is hand-produced at scale — a baked-in "
                      f"photographic scene cannot survive that. Use /posm-image with mode=paintable and "
                      f"a flat field instead."})
    brief = str(payload.get("brief") or "").strip()
    if not brief:
        return JSONResponse(status_code=400, content={
            "detail": "Describe the scene — who is in it, where, doing what. This is the one image "
                      "that has to carry the whole piece, so it needs more than a hero brief does."})

    cast_ids = [str(c) for c in (payload.get("cast_ids") or []) if c]
    refs, kinds = [], []
    if cast_ids:
        for cid in cast_ids[:2]:
            row = library.get(cid)
            if row and row.get("kind") in ("cast", "actor") and row.get("signed_off"):
                refs.append(row["url"])
                kinds.append(f"cast:{cid}")
    else:
        cast = library.reference_url("cast") or library.reference_url("actor")
        if cast:
            refs.append(cast)
            kinds.append("cast")
    # `product_id` is `pack_id`'s category-agnostic sibling (a garment, an accessory, a device) —
    # tried first since a caller naming it explicitly means the piece isn't packaging at all.
    prod_id = str(payload.get("product_id") or payload.get("pack_id") or "")
    prod_row = library.get(prod_id) if prod_id else None
    prod_kind = prod_row.get("kind") if prod_row else ""
    pack = (prod_row["url"] if prod_row and prod_kind in ("pack", "product") and prod_row.get("signed_off")
            else (library.reference_url("pack") or library.reference_url("product")))
    if pack and len(refs) < 3:
        refs.append(pack)
        kinds.append(prod_kind or "pack")

    headline = str(payload.get("headline") or payload.get("line") or "").strip()
    style = str(payload.get("style") or "").lower()
    _REGISTERS = {"vector": "Rendered as a flat vector illustration.",
                  "infographic": "Rendered as a simple flat graphic rather than a photograph."}
    parts = [f"{brief.rstrip('.')}."]
    if refs:
        role_note = " and ".join(
            (["the exact people shown, identical faces and clothing"] if kinds and kinds[0].startswith("cast")
             else []) +
            (["the exact product pack shown, same label and proportions, never redrawn"]
             if "pack" in kinds else []) +
            (["the exact product shown, same colours, materials and proportions, never redrawn"]
             if "product" in kinds else []))
        parts.append(f"Reference images show {role_note} — reproduce them faithfully, changing only "
                     f"the setting, pose and action as this scene needs.")
    parts.append(_REGISTERS.get(style, "Photorealistic."))
    if headline:
        parts.append(f'Include the line "{headline}" set as clean, legible, correctly-spelled real '
                     f"typography, prominent but not covering any face or the product.")
    parts.append(f"Include {_brand_line()}'s logo, small, in a natural position such as a corner or on "
                 f"signage in the scene — do not invent a different brand mark.")
    prompt = " ".join(parts)

    ratio = posm.MASTER_RATIO
    eng = _engine(payload, "image")
    model, size, tier = _img_tier(payload, "pro")
    url, provider = "", ""
    if _use(eng, "google"):
        provider = "google"
        if refs:
            url = gemini.image_from_reference(prompt, refs, ratio=ratio, model=model, size=size)
        if not url:
            url = gemini.image(prompt, ratio=ratio, model=model, size=size)
    if not url and _use(eng, "fal"):
        provider = "fal"
        if refs:
            url = creative.image_from_reference(prompt, refs, ratio=ratio, seed=payload.get("seed"))
        if not url:
            url = creative.text_to_image(prompt, ratio=ratio, seed=payload.get("seed"))["url"]
    if not url:
        return JSONResponse(status_code=502, content={
            "detail": "Both image providers refused this scene — check credits (see render-log.txt)."})

    has_cast = any(k.startswith("cast") for k in kinds)
    note = ("Text and logo were drawn by the model, not composited — check both before using this at "
            "scale; letterforms and brand marks are exactly what image models get subtly wrong. ")
    if not has_cast:
        note += ("No signed-off cast/actor reference was available, so every person in this scene was "
                 "hallucinated, not referenced — upload and sign off a real photo under Library → Cast "
                 "for a specific person's likeness to hold across renders.")
    _record_made("posm_scene", headline[:80] if headline else f"POSM scene — {fmt}", url=url,
                 payload=payload, route="/posm-scene")
    return {"image_url": url, "provider": provider, "tier": tier, "prompt": prompt,
            "refs_used": kinds, "has_cast": has_cast, "format": fmt, "note": note.strip()}


@app.post("/posm-assemble")
def posm_assemble(payload: dict):
    """The step `/posm-image`'s own response has always said still needs doing: mask the hero cut-out
    and place it on the field with the pack, the type and the brand block. `{hero_url, format,
    headline?, type_position?, backdrop_url?, field_hex?, pack_url?, pack_id?, logo_url?, brand?,
    custom_ratio?}` -> `{image_url}`.

    `format` can also be `'custom'` (or omitted) with `custom_ratio` set to a `"W:H"` string — see
    `posm.resolve_format`/`posm.custom_format` for why a shape outside the 30-format catalog still goes
    through this exact same layout engine instead of a separate code path.

    Everything here is a real Pillow composite (`keyvisual.assemble`) — pixels moved and drawn, not a
    second model call. The pack and logo default to whatever is signed off/on file for the brand so a
    caller only has to pass them explicitly to override; the whole point of a signed-off library asset
    is that generation (and now assembly) reads it without being told to every time.
    """
    hero_url = str(payload.get("hero_url") or "").strip()
    if not hero_url:
        return JSONResponse(status_code=400, content={
            "detail": "No hero cut-out to assemble. Render one with /posm-image first."})
    fmt, _fmt_err = posm.resolve_format(payload.get("format"), payload.get("custom_ratio"))
    if _fmt_err:
        return JSONResponse(status_code=400, content={"detail": _fmt_err})

    position = str(payload.get("type_position") or payload.get("layout") or "type-locked-base")
    if position not in posm.TYPE_POSITIONS:
        position = "type-locked-base"
    # The chosen scamp's own split, carried forward — see keyvisual.assemble's matching comment. Absent
    # (no scamp was adjusted, or one wasn't picked at all) this is None and assemble() falls back to its
    # long-standing default, so nothing changes for a piece that never touched the scamp step.
    type_pct = payload.get("type_pct")
    type_pct = float(type_pct) if isinstance(type_pct, (int, float)) else None

    # `product_id` is `pack_id`'s category-agnostic sibling — the same composited card, for whatever a
    # "pack" kind doesn't fit (a garment, an accessory, a device). Resolved into the same `pack_url`
    # slot rather than a second layer, since the composite doesn't care what the object IS, only that
    # it's a real photo placed on the piece.
    # `skip_pack` — explicit, not inferred from an absent pack_id. Omitting pack_id has always meant
    # "use the default signed-off pack", so a caller with a real reason to have NONE composited (the
    # hero already carries it faithfully — /posm-image's `pack_used`) needs a real way to say so, not
    # rely on a fallback that would just silently re-add the default anyway.
    pack_url = ""
    if not payload.get("skip_pack"):
        pack_url = str(payload.get("pack_url") or "").strip()
        # LOGIC BUG (round-83 audit): this used to assign the raw manifest id string here as if it were
        # already a URL — `library.get(...)` was never called, so `_open_image()` silently failed to
        # decode the bogus "URL" and the piece shipped with no pack layer at all while the response still
        # reported `pack_used: true`. Resolve the id to its real signed-off URL, same as every other
        # `pack_id`/`product_id` call site in this file.
        if not pack_url and (payload.get("pack_id") or payload.get("product_id")):
            pid = str(payload.get("pack_id") or payload.get("product_id"))
            row = library.get(pid)
            pack_url = row["url"] if row and row.get("kind") in ("pack", "product") \
                and row.get("signed_off") else ""
        if not pack_url:
            pack_url = library.reference_url("pack") or library.reference_url("product")

    prof = brandprofile.resolve() if not payload.get("brand") else brandprofile.by_name(
        str(payload["brand"]))
    prof = prof or {}
    logo_url = str(payload.get("logo_url") or "").strip() or prof.get("logo") or ""

    # The field is the brand's colour, and it has to be a real hex — `brandprofile`'s own `palette`
    # docstring makes the point ("a colour NAME on its own is not enough... 'Ghee gold' tells a model
    # nothing and renders no swatch"). `colours` holds names; `palette` holds hexes. Prefer a palette row
    # whose role mentions background/field, else the first row, else fall back to the neutral and SAY SO
    # rather than inventing a hex for a name — a wrong brand colour printed at scale is expensive.
    field_hex = str(payload.get("field_hex") or "").strip()
    field_source = "caller"
    if not field_hex:
        rows = [r for r in (prof.get("palette") or []) if isinstance(r, dict) and r.get("hex")]
        pick = next((r for r in rows if re.search(r"background|field|primary",
                                                  str(r.get("role") or ""), re.IGNORECASE)), None) or \
            (rows[0] if rows else None)
        if pick:
            field_hex, field_source = str(pick["hex"]), f"brand palette ({pick.get('name') or 'unnamed'})"
        else:
            # No declared palette — MEASURE the brand's colour off its own signed-off logo or pack
            # rather than falling back to a neutral. A piece for a brand whose field is Deep Forest
            # coming out cream is not a "safe default", it is the wrong artwork: the field IS the brand
            # on a POS piece, and it was the single most visible thing wrong with a real render. The
            # measurement is the same one `/posm-palette` offers; doing it here means a person who never
            # opened that panel still gets a branded piece instead of a beige one.
            _src = library.reference_url("logo") or library.reference_url("pack") \
                or library.reference_url("product")
            _sw = keyvisual.palette_from(_src) if _src else []
            # Skip anything too pale to knock type out of, and anything nearly black.
            _usable = [s for s in _sw if 0.06 < s["luminance"] < 0.62]
            if _usable:
                field_hex = _usable[0]["hex"]
                field_source = ("measured from the brand's own signed-off artwork — no palette is "
                                "declared in the brand profile, so this is the dominant colour of the "
                                "logo/pack, not a declared brand value. Confirm it before printing.")
            else:
                field_source = ("no brand palette on file and none could be measured — this is a "
                                "neutral stand-in, not the brand's colour. Add the palette with hex "
                                "values in the brand profile.")

    # Layer 8's tagline is real supplied copy: the brand's own locked line. `mandatories` in the profile
    # is a CHECKLIST of what must appear ("FSSAI mark", "the line 'Pure Doodh Ki Shakti'"), not the text
    # to print — setting the words "FSSAI mark" on a poster is exactly the "every word is supplied,
    # never generated" failure the skill warns about, so the quoted line is lifted out and the rest is
    # reported as still-needed rather than typeset.
    declared = [str(m) for m in (prof.get("mandatories") or []) if str(m).strip()]
    support_line = str(payload.get("support_line") or "").strip()
    if not support_line:
        quoted = next((m for m in declared if "'" in m or '"' in m), "")
        hit = re.search(r"['\"]([^'\"]{3,60})['\"]", quoted) if quoted else None
        support_line = hit.group(1) if hit else ""
    # Only ever printed when the caller supplies the real strings — a licence number is a legal
    # identifier and there is nothing here that could know it.
    marks = [str(m).strip() for m in (payload.get("mandatories") or []) if str(m).strip()]
    outstanding = [m for m in declared
                   if not re.search(r"['\"]", m) and not any(m.lower() in x.lower() for x in marks)]

    craft: dict = {}
    try:
        url = keyvisual.assemble_and_store(
            report=craft,
            hero_url=hero_url, fmt=fmt, headline=str(payload.get("headline") or payload.get("line") or ""),
            type_position=position, backdrop_url=str(payload.get("backdrop_url") or ""),
            field_hex=field_hex, pack_url=pack_url, logo_url=logo_url,
            # A scene shot is a finished photograph; a cut-out is a subject on white. Keying the first
            # one destroys it (see keyvisual.assemble's docstring), so the caller says which it has.
            hero_is_cutout=payload.get("hero_is_cutout", True) is not False,
            headline_emphasis=str(payload.get("headline_emphasis") or ""),
            device=str(payload.get("device") or "rule"),
            support_line=support_line, mandatories=tuple(marks),
            field_hex_2=str(payload.get("field_hex_2") or ""), type_pct=type_pct)
    except ValueError as e:
        # The headline-fit refusal is a legibility verdict, not a crash — 409 so the UI can tell the two
        # apart and show it as "this line does not fit" rather than "the server broke".
        return JSONResponse(status_code=409, content={"detail": str(e), "fit": False})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Assembly failed: {e}"})
    _record_made("posm_assemble", f"Assembled key visual — {fmt}", url=url, payload=payload,
                 route="/posm-assemble")
    return {"image_url": url, "format": fmt, "type_position": position,
            "pack_used": bool(pack_url), "logo_used": bool(logo_url),
            "field_hex": field_hex, "field_source": field_source,
            "support_line": support_line, "mandatories": marks,
            "mandatories_outstanding": outstanding,
            # The craft read on the finished piece: measured headline contrast against WCAG's 3:1 floor
            # for large type, and the squint test the skill has always asked a person to do by eye.
            # Reported, not enforced — see `keyvisual.squint`.
            "craft": craft}


@app.post("/posm-scamps")
def posm_scamps(payload: dict):
    """Layout scamps. `{format, subject?, line?, field_hex?, positions?[], drawn?, only?, adjust?,
      type_pct?, with_pack?}` -> `{scamps:[]}`.

    **`only` + `adjust` is a revision to ONE pinned-up scamp, not a redraw of the set.** Pass `only` as
    a single `type_position` and this regenerates just that one — `adjust` is the art director's note
    on it (folded into `posm.scamp_prompt`), `type_pct`/`with_pack` are the two structural knobs the
    block-diagram/`assemble()` geometry actually shares (see `keyvisual.scamp`'s docstring). Without
    `only`, behaviour is unchanged — the full comparison set, exactly as before.

    The step between "a route is chosen" and "render it". A studio settles composition on thumbnails
    first, because deciding layout with finished artwork is slow and expensive — and here it was worse
    than slow: comparing two layouts meant paying for two image generations, so in practice nobody
    compared.

    **Two kinds, and the drawn one is the point.** `drawn=False` gives the instant block diagram: pure
    Pillow, no model call, the whole set in about ten milliseconds — useful as an immediate skeleton
    while the real ones generate. `drawn=True` (the default when a subject is supplied) gives what an
    art director actually pins up: a pencil sketch of the route's own scene with the headline lettered
    into the type area. Boxes are honest about geometry and useless for the decision they serve —
    whether the picture and the words hold together cannot be judged from two rectangles, because
    neither the picture nor the words are in them.
    """
    fmt = str(payload.get("format") or "").strip()
    if fmt not in posm.FORMATS:
        return JSONResponse(status_code=400, content={"detail": f"Unknown format {fmt!r}."})
    only = str(payload.get("only") or "").strip()
    if only and only in posm.TYPE_POSITIONS:
        positions = (only,)
    else:
        positions = tuple(p for p in (payload.get("positions") or []) if p in posm.TYPE_POSITIONS) \
            or tuple(posm.TYPE_POSITIONS.keys())
    subject = str(payload.get("subject") or "").strip()
    line = str(payload.get("line") or "").strip()
    adjust = str(payload.get("adjust") or "").strip()
    type_pct = payload.get("type_pct")
    type_pct = float(type_pct) if isinstance(type_pct, (int, float)) else None
    with_pack = payload.get("with_pack", True) is not False
    drawn = payload.get("drawn")
    drawn = bool(subject) if drawn is None else bool(drawn)

    if not drawn or not _have_image():
        try:
            scamps = keyvisual.scamp_set(fmt, str(payload.get("field_hex") or ""), positions,
                                         type_pct=type_pct, with_pack=with_pack)
        except Exception as e:
            return JSONResponse(status_code=500, content={"detail": f"Scamps failed: {e}"})
        return {"format": fmt, "scamps": scamps, "drawn": False,
                "note": "Block layouts — geometry only. Supply the route's subject for drawn scamps."}

    eng = _engine(payload, "image")
    model, size, _tier = _img_tier(payload)
    out = []
    for p in positions:
        prompt = posm.scamp_prompt(subject, line, p, fmt=fmt, adjust=adjust)
        url = ""
        if _use(eng, "google"):
            url = gemini.image(prompt, ratio=posm.MASTER_RATIO, model=model, size=size)
        if not url and _use(eng, "fal"):
            url = creative.text_to_image(prompt, ratio=posm.MASTER_RATIO)["url"]
        if url:
            out.append({"id": p, "type_position": p, "url": url, "drawn": True,
                        "note": posm.TYPE_POSITIONS.get(p, ""), "type_pct": type_pct})
        else:
            # One layout failing is not a reason to lose the set — fall back to its block diagram so
            # the comparison stays complete.
            try:
                data = keyvisual.scamp(fmt, p, str(payload.get("field_hex") or ""),
                                       with_pack=with_pack, type_pct=type_pct)
                os.makedirs(keyvisual.MEDIA_DIR, exist_ok=True)
                name = f"scamp-{uuid.uuid4().hex[:10]}.png"
                with open(os.path.join(keyvisual.MEDIA_DIR, name), "wb") as fh:
                    fh.write(data["bytes"])
                out.append({"id": p, "type_position": p, "url": f"/media/{name}", "drawn": False,
                            "note": posm.TYPE_POSITIONS.get(p, ""), "type_pct": data["type_pct"]})
            except Exception:
                continue
    if not out:
        return JSONResponse(status_code=502, content={
            "detail": "No scamp could be drawn — check image provider credits (see render-log.txt)."})
    _record_made("posm_scamps", f"Layout scamps — {fmt}", payload=payload,
                 urls=[o["url"] for o in out], route="/posm-scamps")
    return {"format": fmt, "scamps": out, "drawn": True,
            "note": "Pencil scamps of this route, one per layout. Judge the arrangement and the line "
                    "together — the rendering is deliberately rough."}


@app.post("/posm-typeset")
def posm_typeset(payload: dict):
    """Real type over a finished photograph — `keyvisual.type_over_photo`, the one piece of the
    layered compositor kept once the picture itself is a baked studio shot (or a recomposed new
    layout) rather than a separately-composited hero/pack/field. `{photo_url, format, headline?,
    type_position?, type_pct?, field_hex?, support_line?, mandatories?:[]}` -> `{image_url,
    type_position, mandatories_outstanding, craft}`.

    Deliberately not `/posm-assemble` — no `pack_url`, no `hero_is_cutout`, no keying, because there
    is nothing left to composite: the photo already carries the hero, the pack and the field. This
    route's whole job is the type, and only the type.
    """
    photo_url = str(payload.get("photo_url") or "").strip()
    fmt = str(payload.get("format") or "").strip()
    if not photo_url:
        return JSONResponse(status_code=400, content={
            "detail": "No photo to set type on — pass the approved studio shot or new-layout image."})
    if fmt not in posm.FORMATS:
        return JSONResponse(status_code=400, content={"detail": f"Unknown format {fmt!r}."})

    position = str(payload.get("type_position") or payload.get("layout") or "type-locked-base")
    if position not in posm.TYPE_POSITIONS:
        position = "type-locked-base"
    type_pct = payload.get("type_pct")
    type_pct = float(type_pct) if isinstance(type_pct, (int, float)) else None

    prof = brandprofile.resolve() if not payload.get("brand") else brandprofile.by_name(
        str(payload["brand"]))
    prof = prof or {}
    field_hex = str(payload.get("field_hex") or "").strip() or str(prof.get("field_hex") or "")

    # Same mandatories/support-line resolution `/posm-assemble` already does — see that route's own
    # comment for why the quoted brand line is lifted out and the rest reported as still-needed rather
    # than typeset verbatim.
    declared = [str(m) for m in (prof.get("mandatories") or []) if str(m).strip()]
    support_line = str(payload.get("support_line") or "").strip()
    if not support_line:
        quoted = next((m for m in declared if "'" in m or '"' in m), "")
        hit = re.search(r"['\"]([^'\"]{3,60})['\"]", quoted) if quoted else None
        support_line = hit.group(1) if hit else ""
    marks = [str(m).strip() for m in (payload.get("mandatories") or []) if str(m).strip()]
    outstanding = [m for m in declared
                   if not re.search(r"['\"]", m) and not any(m.lower() in x.lower() for x in marks)]

    craft: dict = {}
    try:
        url = keyvisual.type_over_photo_and_store(
            report=craft, photo_url=photo_url, fmt=fmt,
            headline=str(payload.get("headline") or payload.get("line") or ""),
            type_position=position, type_pct=type_pct,
            headline_emphasis=str(payload.get("headline_emphasis") or ""),
            device=str(payload.get("device") or "rule"),
            support_line=support_line, mandatories=tuple(marks), field_hex=field_hex)
    except ValueError as e:
        return JSONResponse(status_code=409, content={"detail": str(e), "fit": False})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Typesetting failed: {e}"})
    _record_made("posm_typeset", f"Typeset — {fmt}", url=url, payload=payload, route="/posm-typeset")
    return {"image_url": url, "format": fmt, "type_position": position,
            "field_hex": field_hex, "support_line": support_line, "mandatories": marks,
            "mandatories_outstanding": outstanding, "craft": craft}


@app.get("/posm-mandatories")
def posm_mandatories(brand: str = ""):
    """The brand's declared mandatories (`prof.get("mandatories")`) — the same list `/posm-assemble`
    already checks a render against, surfaced ahead of render so the checklist can offer them as real
    choices instead of the render always sending an empty list and every one coming back "outstanding".
    `{mandatories:[str], quoted_line:str}` — `quoted_line` is the one entry (if any) that names an exact
    printed line, split out the same way `/posm-assemble` already does, since that one is copy to
    include verbatim rather than a box to tick.
    """
    prof = brandprofile.by_name(brand) if brand else brandprofile.resolve()
    prof = prof or {}
    declared = [str(m) for m in (prof.get("mandatories") or []) if str(m).strip()]
    quoted = next((m for m in declared if "'" in m or '"' in m), "")
    hit = re.search(r"['\"]([^'\"]{3,60})['\"]", quoted) if quoted else None
    return {"mandatories": declared, "quoted_line": hit.group(1) if hit else ""}


@app.post("/posm-palette")
def posm_palette(payload: dict):
    """The brand's real colours, measured off its own signed-off assets. `{ids?[]}` -> `{swatches:[]}`.

    The mood-board step, done the one way this studio can do honestly. A creative team curates imagery,
    textures and colour swatches to fix a visual vocabulary before anything is made; the equivalent here
    is not a collage of borrowed pictures — it is establishing what the brand's colours actually ARE,
    because right now nothing knows. `brandprofile.colours` for this brand holds three NAMES ("Deep
    Forest", "Cream", "Ghee gold") and `palette`, the field that holds hexes, is empty — so every render
    has been falling back to a neutral stand-in and saying so.

    The pack shot and the logo are signed-off ground truth and the colours are provably in them, so they
    are measured rather than guessed. Returned as candidates to choose from, not written to the profile:
    a brand's palette is a decision somebody makes, and `library.py`'s own rule is that facts enter by a
    person's action, never by inference.
    """
    ids = [str(i) for i in (payload.get("ids") or []) if str(i).strip()]
    refs = []
    if ids:
        for i in ids:
            row = library.get(i)
            if row and row.get("url"):
                refs.append((row.get("name") or i, row["url"], row.get("kind") or ""))
    else:
        for kind in ("logo", "pack", "product"):
            for row in library.items(kind, signed_only=True):
                if row.get("url"):
                    refs.append((row.get("name") or row["id"], row["url"], kind))
    if not refs:
        return JSONResponse(status_code=409, content={
            "detail": "No signed-off logo, pack or product to read colours from. Upload one in Memory "
                      "and sign it off — a brand's colours are measured from its own artwork here, "
                      "never guessed from a colour name."})
    sources = []
    for name, url, kind in refs[:6]:
        sw = keyvisual.palette_from(url)
        if sw:
            sources.append({"name": name, "kind": kind, "url": url, "swatches": sw})
    prof = brandprofile.resolve() or {}
    return {"sources": sources,
            "declared_names": prof.get("colours") or {},
            "declared_palette": prof.get("palette") or [],
            "note": ("Measured from signed-off artwork. Choose the field colour from these and save it "
                     "into the brand profile's palette — nothing is written there automatically.")}


@app.get("/posm-input-spec")
def posm_input_spec():
    """Every input that goes into a piece, declared. -> `{groups:[{group, inputs:[...]}]}`.

    `posm.RENDER_INPUTS` is the single source of truth; this just groups it for display. The list
    exists because the inputs were real but scattered across the route, the assets panel, the format
    table and compositor constants, and nothing ever named them together — which is how a route
    describing a mother produced a poster with no person in it and nobody could point at which input
    had been dropped.
    """
    groups: list[dict] = []
    for row in posm.RENDER_INPUTS:
        g = next((x for x in groups if x["group"] == row["group"]), None)
        if not g:
            g = {"group": row["group"], "inputs": []}
            groups.append(g)
        g["inputs"].append(row)
    return {"groups": groups, "count": len(posm.RENDER_INPUTS)}


@app.post("/posm-artwork")
def posm_artwork(payload: dict):
    """The piece as an editable vector document. Same payload as `/posm-assemble` -> `{url, layers}`.

    **The PNG is a preview; this is the artwork.** A key visual is a master that gets adapted eleven
    times, and if adapting it means regenerating it then the studio is doing the exact thing the
    skill's governing rule forbids. Baked pixels cannot be adapted: nobody can move the headline two
    millimetres, change a word or swap the field colour without a fresh render.

    So this builds the piece the way a designer would — named layers matching the nine-layer stack,
    live `<text>` that can be retyped and rekerned, photographs embedded and masked inside vector
    frames, geometry in real millimetres at trim size, and bleed/safe guides on their own hideable
    layer. It opens in Illustrator (or Affinity, or Inkscape) as a working file.
    """
    fmt, _fmt_err = posm.resolve_format(payload.get("format"), payload.get("custom_ratio"))
    if _fmt_err:
        return JSONResponse(status_code=400, content={"detail": _fmt_err})
    prof = brandprofile.resolve() or {}
    pack_url = ""
    if not payload.get("skip_pack"):
        pack_url = str(payload.get("pack_url") or "").strip() or str(payload.get("pack_id") or "") \
            or str(payload.get("product_id") or "") or library.reference_url("pack") \
            or library.reference_url("product")
    position = str(payload.get("type_position") or payload.get("layout") or "type-locked-base")
    if position not in posm.TYPE_POSITIONS:
        position = "type-locked-base"
    try:
        meta = keyvisual.artwork_svg_and_store(
            fmt=fmt, headline=str(payload.get("headline") or payload.get("line") or ""),
            hero_url=str(payload.get("hero_url") or ""), pack_url=pack_url,
            logo_url=str(payload.get("logo_url") or "").strip() or prof.get("logo") or "",
            field_hex=str(payload.get("field_hex") or ""),
            headline_emphasis=str(payload.get("headline_emphasis") or ""),
            type_position=position, support_line=str(payload.get("support_line") or ""),
            mandatories=tuple(str(m).strip() for m in (payload.get("mandatories") or []) if str(m).strip()),
            device=str(payload.get("device") or "rule"),
            hero_is_cutout=payload.get("hero_is_cutout"))
    except ValueError as e:
        return JSONResponse(status_code=409, content={"detail": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Artwork build failed: {e}"})
    _record_made("posm_artwork", f"Editable artwork — {fmt}", url=str(meta.get("url") or ""),
                 payload=payload, route="/posm-artwork")
    return meta


@app.post("/posm-print")
def posm_print(payload: dict):
    """Print-ready artwork. Same payload as `/posm-assemble` plus `{dpi?, colour?}` -> file + spec.

    What `/posm-assemble` produces is a comp: `keyvisual.canvas_px`'s own docstring called it "a preview
    render, not a print file", and a 1600px RGB PNG is not something a printer can set an A3 poster
    from. This is the export that closes the gap the whole skill is pointed at — "something a printer
    can produce" — at real trim size and resolution, with the bleed and crop marks `posm.bleed_safe`
    has been computing all along with nothing applying them to a file.
    """
    hero_url = str(payload.get("hero_url") or "").strip()
    if not hero_url:
        return JSONResponse(status_code=400, content={"detail": "No hero to lay out."})
    fmt, _fmt_err = posm.resolve_format(payload.get("format"), payload.get("custom_ratio"))
    if _fmt_err:
        return JSONResponse(status_code=400, content={"detail": _fmt_err})
    dpi = int(payload.get("dpi") or 300)
    if dpi < 72 or dpi > 1200:
        return JSONResponse(status_code=400, content={"detail": "dpi must be between 72 and 1200."})
    colour = "rgb" if str(payload.get("colour") or "").lower() == "rgb" else "cmyk"

    position = str(payload.get("type_position") or payload.get("layout") or "type-locked-base")
    if position not in posm.TYPE_POSITIONS:
        position = "type-locked-base"
    prof = brandprofile.resolve() if not payload.get("brand") else brandprofile.by_name(
        str(payload["brand"]))
    prof = prof or {}
    pack_url = ""
    if not payload.get("skip_pack"):
        pack_url = str(payload.get("pack_url") or "").strip() or str(payload.get("pack_id") or "") \
            or str(payload.get("product_id") or "") \
            or library.reference_url("pack") or library.reference_url("product")
    try:
        meta = keyvisual.assemble_print_and_store(
            fmt=fmt, dpi=dpi, colour=colour,
            hero_url=hero_url, headline=str(payload.get("headline") or payload.get("line") or ""),
            type_position=position, backdrop_url=str(payload.get("backdrop_url") or ""),
            field_hex=str(payload.get("field_hex") or ""), pack_url=pack_url,
            logo_url=str(payload.get("logo_url") or "").strip() or prof.get("logo") or "",
            hero_is_cutout=payload.get("hero_is_cutout", True) is not False,
            headline_emphasis=str(payload.get("headline_emphasis") or ""),
            device=str(payload.get("device") or "rule"),
            support_line=str(payload.get("support_line") or ""),
            mandatories=tuple(str(m).strip() for m in (payload.get("mandatories") or []) if str(m).strip()),
            field_hex_2=str(payload.get("field_hex_2") or ""),
            type_pct=(float(payload["type_pct"]) if isinstance(payload.get("type_pct"), (int, float))
                     else None))
    except ValueError as e:
        return JSONResponse(status_code=409, content={"detail": str(e), "fit": False})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Print export failed: {e}"})
    _record_made("posm_print", f"Print-ready artwork — {fmt}", url=str(meta.get("url") or ""),
                 payload=payload, route="/posm-print")
    return meta


@app.post("/posm-spec")
def posm_spec(payload: dict):
    """Draft the key visual as a nine-layer spec. `{formats:[], steer, brief}` -> `{spec, findings}`.

    The layer stack is the deliverable, approved on its own before any format exists — skipping to
    "give me a dangler" is how a kit of eleven pieces arrives looking like eleven brands.

    This is the first thing in the product that loads `posm_skill`. The skill existed and only a person
    typing `/posm` could reach it, so the nine-layer insight was in the repository and in none of the
    generations the product itself made.
    """
    house, brief, platform, plan = _exec_ctx(payload)
    text, src = producers.stands_on("posm", house, platform, str(payload.get("brief") or ""))
    formats = [f for f in (payload.get("formats") or []) if f in posm.FORMATS]
    if not formats:
        formats = posm.KIT_PRESETS.get(str(payload.get("kit") or ""), {}).get("formats", [])

    prof = brandprofile.resolve() or {}
    palette = ", ".join(str(v) for v in (prof.get("colours") or {}).values() if v)
    spec, note = posm.draft(
        text, src, brand=_brand_line(), house_ctx=producers._ctx(house, brief, platform, plan),
        formats=formats, palette=palette, steer=str(payload.get("steer") or ""))
    if not spec:
        return JSONResponse(status_code=400, content={"detail": note, "stands_on":
                                                      {"text": text, "source": src}})
    return {"spec": spec, "note": note, "findings": spec.get("findings", []),
            "stands_on": {"text": text, "source": src}, "formats": formats,
            "gate": posm.gate(spec.get("hero_type", "")),
            "cutout_prompt": posm.cutout_prompt(spec.get("hero_brief", ""))}


@app.post("/posm-adapt")
def posm_adapt(payload: dict):
    """Adaptation sheets for a kit. `{formats|kit, line, line_short, field, hero, layout}`.

    Every number is computed from the format's own millimetres and reading distance — cap height, word
    count, aspect delta, which layers drop, bleed, safe area, what stands in front of the artwork. None
    of it is a judgement, so none of it is asked of a model.
    """
    formats = [f for f in (payload.get("formats") or []) if f in posm.FORMATS]
    preset = str(payload.get("kit") or "")
    if not formats and preset in posm.KIT_PRESETS:
        formats = posm.KIT_PRESETS[preset]["formats"]
    if not formats:
        return JSONResponse(status_code=400, content={
            "detail": "Name the formats this kit is made of, or pick a trade footprint. A kit is a "
                      "media decision, not a catalogue dump."})
    position = str(payload.get("layout") or payload.get("type_position") or "")
    out = posm.kit(formats, line=str(payload.get("line") or ""),
                   short_line=str(payload.get("line_short") or ""),
                   field=str(payload.get("field") or ""), hero=str(payload.get("hero") or ""),
                   type_position=position if position in posm.TYPE_POSITIONS else "")
    if preset in posm.KIT_PRESETS:
        out["kit"] = preset
        out["left_out"] = posm.KIT_PRESETS[preset]["left_out"]
    return out


@app.get("/grounding")
def grounding(house: str = "", plan: str = "", execution: str = ""):
    """What the backend will actually ground the next generation on. Returns the truth, not a guess.

    Built because two screens disagreed in the same app at the same moment: POS material said *"from the
    idea platform"* while Social said *"no platform adopted"*. Both were honest about what they could
    see — the client knows only what the open plan or execution binds, and the backend also falls back to
    the newest house for the active brand and to its chosen platform. So the backend was grounding more
    than the client could report, and the screen understated its own work.

    A grounding line that says "nothing" while the output is in fact grounded teaches somebody to retype
    a brief on top of work that did not need it. That is worse than no line at all, so the resolution is
    published rather than inferred twice.

    `{ platform:{name,line,source}|null, house:{id,brand,core}|null, plan:{id,channels,audiences}|null,
       grounded:bool, summary:"one sentence for the screen" }`
    """
    house_obj, _brief, platform, plan_obj = _exec_ctx(
        {"house": house, "plan": plan, "execution": execution})

    core = "; ".join(strategy._chosen_text(house_obj, "core")) if house_obj else ""
    n_ch = len((((plan_obj or {}).get("nodes") or {}).get("channels") or {}).get("rows", []))
    n_au = len((((plan_obj or {}).get("nodes") or {}).get("audiences") or {}).get("rows", []))

    bits = []
    if platform and str(platform.get("idea") or "").strip():
        bits.append(f'"{platform.get("name") or "the idea platform"}"')
    elif core:
        bits.append("the house's core message")
    if n_ch:
        bits.append(f"the {n_ch} channel{'s' if n_ch != 1 else ''} in the plan")
    summary = ("Written against " + ", ".join(bits) + "."
               if bits else
               "Nothing is grounding this yet — no platform adopted, no house chosen, no plan bound. "
               "It will read competent and could be any brand in the category.")

    return {
        "grounded": bool(bits),
        "summary": summary,
        "platform": ({"id": platform.get("id", ""), "name": platform.get("name", ""),
                      "line": platform.get("idea", ""), "mechanic": platform.get("mechanic", ""),
                      "source": platform.get("source", "")} if platform else None),
        "house": ({"id": house_obj.get("id", ""), "brand": house_obj.get("brand", ""),
                   "core": core} if house_obj else None),
        "plan": ({"id": plan_obj.get("id", ""), "brand": plan_obj.get("brand", ""),
                  "channels": n_ch, "audiences": n_au} if plan_obj else None),
    }


@app.get("/posm-formats")
def posm_formats():
    """Everything a POS screen needs to render its choices from data rather than a hard-coded list.

    Thirty formats with real millimetres, reading distances, substrates and the trap in each, plus the
    layer stack, the hero types, the field and type vocabularies, the drop-out tiers, the trade
    footprints and the library's own honest status.

    The six-entry table this replaces had two errors in it: `shelf-strip` was recorded as 16:9 when the
    real piece is about 12:1, and `poster-a3` as 3:4 when A3 is 5:7. Both are the kind that survive
    review, because a ratio looks like a detail right up until a piece is set to it.

    `formats`, `layouts` and `styles` keep the names the existing panel reads.
    """
    st = posm.status()
    return {**st, "layouts": posm.TYPE_POSITIONS, "styles": list(_IMG_STYLES),
            "tiers_image": {k: v[2] for k, v in _IMG_TIERS.items()}}


@app.post("/posm-custom-format")
def posm_custom_format(payload: dict):
    """Register a custom L×B shape so it becomes a real, renderable format id. `{ratio: "3:2"}` ->
    `{key, label, ratio, tier, band, note}`.

    A separate, cheap call rather than an inline field on `/posm-adapt`/`/posm-assemble` because those
    take (or return) a format by KEY, and a key has to already exist in `posm.FORMATS` before either can
    resolve it — this is the one place that creates it, so a screen calls it once when a custom size is
    typed in, then treats the returned key exactly like any of the 30 named ones from then on.
    """
    key, err = posm.resolve_format("custom", str(payload.get("ratio") or ""))
    if err:
        return JSONResponse(status_code=400, content={"detail": err})
    row = posm.FORMATS[key]
    return {"key": key, "label": row["label"], "ratio": row["ratio"], "tier": row["tier"],
            "band": posm.reflow(key).get("band", ""), "note": row.get("trap", "")}


@app.post("/activation-idea")
def activation_idea(payload: dict):
    """Sharpen an activation idea into one that can be built. Returns `{idea}`.

    **Never invents an idea from an empty box** — 400, with the sentence to show. This is asked for
    explicitly and it is also right: on-ground is the one execution where the idea is somebody standing
    in a street doing a thing, and a model that supplies it supplies something nobody in the room
    believes in. The platform and the plan are grounding for sharpening what a person wrote; they are
    not a substitute for their having written it.
    """
    house, brief, platform, plan = _exec_ctx(payload)
    typed = str(payload.get("idea") or "").strip()

    # Three requests arrive here and they are told apart by whether `idea` is present at all:
    #
    #   no `idea` key      -> GENERATE. This is the "Generate ideas for me" button.
    #   `idea: ""`         -> just say what it would stand on. Cheap, no model call.
    #   `idea: "..."`      -> sharpen what was written.
    #
    # The middle case matters more than it looks. The screen asks it on every visit to the tab, to show
    # the platform above the empty box — and when "empty means generate" it meant opening the tab fired a
    # forty-second generation nobody asked for. That was my doing: I widened the route without checking
    # who was already calling it with an empty idea.
    if "idea" in payload and not typed:
        stood, src = producers.stands_on("activation", house, platform, "")
        return {"stands_on": {"text": stood, "source": src}, "ideas": [], "count": 0,
                "venues": producers.VENUES,
                "detail": "Nothing generated — send no `idea` key at all to generate ideas."}

    # **No typed idea now GENERATES rather than refusing.** This reverses the earlier rule deliberately,
    # at the client's instruction. The original argument — that a model-supplied activation is one nobody
    # in the room believes in — was about *vague* ideas, and the structure below is what actually answers
    # it: what · who · where · when · how · capture · access · risk cannot be filled in with
    # "engages with the brand". A vague idea is now impossible to write rather than refused.
    if not typed:
        try:
            n = max(2, min(4, int(payload.get("n") or 3)))
        except (TypeError, ValueError):
            n = 3
        ideas, note = producers.activation_ideas(house, platform, plan, brief, n,
                                                 str(payload.get("steer") or ""))
        if not ideas:
            stood, src = producers.stands_on("activation", house, platform, "")
            return JSONResponse(status_code=400, content={
                "detail": note, "stands_on": {"text": stood, "source": src}})
        return {"ideas": ideas, "count": len(ideas), "note": note,
                "venues": producers.VENUES,
                "stands_on": {"text": producers.stands_on("activation", house, platform, "")[0],
                              "source": producers.stands_on("activation", house, platform, "")[1]}}

    idea, note = producers.sharpen_idea(typed, house, brief, platform, plan)
    if not idea:
        stood, src = producers.stands_on("activation", house, platform, "")
        return JSONResponse(status_code=400,
                            content={"detail": note, "stands_on": {"text": stood, "source": src}})
    return {"idea": idea, "note": note}


@app.post("/activation-idea-adjust")
def activation_idea_adjust(payload: dict):
    """Adjust ONE already-generated activation idea card per a note, keeping its structure.

    `{idea:{...}, note:"..."}` -> `{idea:{...}}` on success, 400 `{detail}` on refusal. The per-card
    twin of `/activation-idea`'s sharpen mode: that one collapses to a plain string, this one keeps the
    what/who/where/when/how/capture/access/risk shape every idea card and downstream element already
    reads. See `producers.adjust_activation_idea`'s own docstring for what's preserved vs re-derived.
    """
    house, brief, platform, plan = _exec_ctx(payload)
    idea = payload.get("idea") if isinstance(payload.get("idea"), dict) else {}
    note = str(payload.get("note") or "")
    out, err = producers.adjust_activation_idea(idea, note, house, brief, platform, plan)
    if not out:
        return JSONResponse(status_code=400, content={"detail": err})
    return {"idea": out}


@app.post("/activation-elements")
def activation_elements(payload: dict):
    """Which elements the CHOSEN idea needs, and why. `{idea:{…}}` or `{venue, what, how}`.

    Not a fixed four. A mall atrium needs no van, a haat route needs no gondola, a doorstep round needs
    no stall — and offering the same four regardless is how three of them get briefed with something
    plausible and nothing gets built.
    """
    idea = payload.get("idea") if isinstance(payload.get("idea"), dict) else payload
    els = producers.elements_for(idea)
    return {"elements": els, "keys": [e["key"] for e in els],
            "venue": (idea or {}).get("venue", ""),
            "all": producers.OG_ELEMENTS,
            "detail": f"{len(els)} elements for this idea"
                      + (f" at a {producers.VENUES.get(str((idea or {}).get('venue') or ''), {}).get('label', 'venue')}"
                         if (idea or {}).get("venue") else "")}


@app.post("/activation-element")
def activation_element(payload: dict):
    """Brief one element against the CHOSEN idea. `{element, idea:{…}|"…", brief?}`.

    **`idea` may be the whole chosen idea object**, not just a sentence. That is the fix for "Develop"
    answering *"brief it first"* when an idea had already been chosen two panels above: the route only
    ever accepted a string, so a chosen idea arriving as an object read as no idea at all. The venue,
    the capture mechanism and the access constraint all come with it, and an element briefed without
    them is briefed against half the idea.
    """
    house, brief, platform, plan = _exec_ctx(payload)
    raw = payload.get("idea")
    chosen = raw if isinstance(raw, dict) else None
    if chosen:
        v = producers.VENUES.get(str(chosen.get("venue") or ""), {})
        idea_text = "\n".join(x for x in [
            str(chosen.get("what") or "").strip(),
            f"Venue: {v.get('label') or chosen.get('venue') or 'unspecified'}"
            + (f" — {v['trap']}" if v.get("trap") else ""),
            f"Who: {chosen.get('who')}" if chosen.get("who") else "",
            f"Where: {chosen.get('where')}" if chosen.get("where") else "",
            f"When: {chosen.get('when')}" if chosen.get("when") else "",
            f"How it runs: {chosen.get('how')}" if chosen.get("how") else "",
            f"How engagement is captured: {chosen.get('capture')}" if chosen.get("capture") else "",
            f"Access: {chosen.get('access')}" if chosen.get("access") else "",
            # WIRING GAP (round-83 audit): every idea card shows a risk callout, but it never reached
            # this construction block — an element could be briefed with no knowledge of the one thing
            # the card itself flagged as needing care. Named as a constraint to design around, same
            # framing `access` already gets, not just appended as trivia.
            f"Risk to design around: {chosen.get('risk')}" if chosen.get("risk") else "",
        ] if x)
    else:
        idea_text = str(raw or "")

    out, note = producers.element_brief(str(payload.get("element") or ""),
                                        str(payload.get("brief") or ""),
                                        idea_text, house, brief, platform, plan)
    if not out:
        return JSONResponse(status_code=400, content={"detail": note})
    return {"brief": out, "note": note,
            "elements": [e["key"] for e in producers.elements_for(chosen)] if chosen
                        else list(producers.OG_ELEMENTS),
            "all": list(producers.OG_ELEMENTS)}


@app.post("/activation-element-image")
def activation_element_image(payload: dict):
    """Render one on-ground element. `{element, idea:{venue,...}, kv_url?, cast_id?, pack_id?,
    product_id?, size_key?, brief?, ratio?}`.

    This is the producer the on-ground screen has been telling people does not exist — "briefed, no
    producer is wired for onground artwork yet" was true. What decides HOW it renders is
    `activation.kv_role(element, venue)`, which was built for exactly this and is derived from the
    element and the venue's own intercept and dwell rather than a table somebody wrote:

      source     the element IS the key visual re-staged — the KV is passed as a reference image and
                 the prompt says to keep it. A van, a truck, a leave-behind, and a stall at any venue
                 read at a distance.
      reference  the demonstration leads and the KV only has to agree — rendered from the brief, with
                 the KV as a reference so codes and palette carry without the composition being copied.
                 A stall at an RWA or a college, where people stop and talk.
      none       refused, and this is the useful half. Promoter training, permissions and a capture
                 mechanism are not artwork, and a render of them would be a picture of a form.

    A `source` element with no `kv_url` is refused rather than invented: the whole point of that role is
    that the piece is made of the visual, so making one up would defeat it.

    **`cast_id`/`pack_id`/`product_id` are the same fidelity mechanism `/studio-shot` already uses** —
    without them a promoter's face or a pack in a stall photo was always invented from a word, which is
    a real fidelity gap on exactly the elements (uniform, stall, van) where getting the pack or the
    person wrong is the most visible.

    **`size_key` picks the real shape** from `producers.OG_ELEMENT_SIZES` for elements that are an
    actual physical object with a footprint (stall, van, truck, leave_behind) — without it this always
    rendered at a flat 4:3 regardless of whether the element was a stall front or a van side panel,
    which are not the same shape.
    """
    element = str(payload.get("element") or "").strip().lower()
    idea = payload.get("idea") if isinstance(payload.get("idea"), dict) else {}
    venue = str(idea.get("venue") or "").strip().lower()
    kv_url = str(payload.get("kv_url") or "").strip()
    brief = str(payload.get("brief") or "").strip()

    role = activation.kv_role(element, venue)
    if not role["role"]:
        return JSONResponse(status_code=400, content={"detail": role["why"], "kv": role})
    if role["role"] == "none":
        return JSONResponse(status_code=409, content={
            "detail": role["why"] + " Brief it in words instead — there is nothing here to render.",
            "kv": role})
    if role["role"] == "source" and not kv_url:
        return JSONResponse(status_code=409, content={
            "detail": ("This element is made from the key visual, and none has been rendered yet. "
                       "Draft the key visual on the POS material screen first — rendering this from "
                       "the brief alone would invent the artwork the piece is supposed to carry."),
            "kv": role})

    v = producers.VENUES.get(venue) or {}
    spec = producers.OG_ELEMENTS.get(element, "")

    # Size/type — a real shape for a physical element, not one flat default asked to stand in for a
    # stall front, a van side panel and a leaflet alike. `producers.OG_ELEMENT_SIZES` only has entries
    # for elements that ARE a sized object; everything else keeps the 4:3 default unchanged.
    size_opts = producers.OG_ELEMENT_SIZES.get(element) or []
    size_key = str(payload.get("size_key") or "").strip()
    size_row = next((s for s in size_opts if s[0] == size_key), size_opts[0] if size_opts else None)
    ratio = str(payload.get("ratio") or (size_row[2] if size_row else "4:3"))

    lead = ("Re-stage the supplied key visual as" if role["role"] == "source"
            else "A photograph of")
    # Real gap found live: this prompt had no brand grounding at all — no name, no palette, no
    # mandatories, nothing from the brand profile every other generation route in this app already
    # reads. A `reference` element with no `kv_url` (the common case — see below) had NOTHING tying it
    # to the brand beyond whatever word happened to be in the free-text brief, which is what "random
    # generation" actually meant: not that the model was ungrounded on purpose, but that this one route
    # never wired the grounding every sibling route already has.
    prof = brandprofile.resolve() or {}
    brand_lines = []
    if prof.get("name") or prof.get("category"):
        brand_lines.append(f"Brand: {prof.get('name') or 'the brand'}"
                            + (f", {prof['category']}" if prof.get("category") else "") + ".")
    if prof.get("tone"):
        brand_lines.append(f"Tone: {prof['tone']}.")
    palette_rows = [r for r in (prof.get("palette") or []) if isinstance(r, dict) and r.get("hex")]
    if palette_rows:
        brand_lines.append("Brand colours to reflect in signage, uniforms and props: "
                           + ", ".join(f"{r.get('name') or r['hex']} ({r['hex']})" for r in palette_rows)
                           + ".")
    if prof.get("hero_product"):
        brand_lines.append(f"Hero product on display: {prof['hero_product']}.")
    declared = [str(m) for m in (prof.get("mandatories") or []) if str(m).strip()]
    if declared:
        brand_lines.append("Visible somewhere in frame: " + "; ".join(declared) + ".")
    if prof.get("avoid"):
        brand_lines.append("Avoid: " + "; ".join(str(a) for a in prof["avoid"]) + ".")
    brand_ctx = " ".join(brand_lines) or (
        "No brand profile is filled in — do not invent a category, palette or brand codes; keep this "
        "generic and say so plainly rather than guessing a look.")

    # Locked references — cast/pack/product, built the same way `/studio-shot` builds them, so a
    # promoter's face or a pack on this element is the REAL one rather than redrawn from a word. The KV
    # (if any) goes first since it already decided the role text above.
    refs, ref_roles = [], []
    if kv_url:
        refs.append(kv_url)
        ref_roles.append(
            "the approved key visual — re-stage it faithfully, same composition, colours and lettering"
            if role["role"] == "source" else
            "the approved key visual — use only for palette and brand codes, do NOT reproduce its "
            "layout or copy; the demonstration is the subject, the branding is on it")

    def _add(field, kinds, role_text):
        rid = str(payload.get(field) or "")
        if not rid:
            return
        row = library.get(rid)
        if row and row.get("kind") in kinds and row.get("signed_off") and row.get("url"):
            refs.append(row["url"])
            ref_roles.append(role_text)

    _add("cast_id", ("cast", "actor"),
         "the exact promoter — identical face, hair, skin tone, body type and age, in the uniform "
         "described unless the brief changes it")
    _add("pack_id", ("pack",),
         "the exact product pack — reproduce it faithfully, same label, colours, type and proportions, "
         "never redrawn or reimagined")
    _add("product_id", ("product",),
         "the exact product — reproduce it faithfully, same colours, materials, shape and proportions, "
         "never redrawn or reimagined")
    if len(refs) > 3:
        refs, ref_roles = refs[:3], ref_roles[:3]
    ref_lines = ("; ".join(f"reference image {i + 1} shows {r}" for i, r in enumerate(ref_roles)) + ". "
                 if ref_roles else "")

    prompt = (
        f"{lead} a {element.replace('_', ' ')} for an Indian consumer activation at "
        f"{v.get('label', venue)}. {spec} {brand_ctx} "
        + (f"Built as {size_row[1]}. " if size_row else "")
        + ref_lines
        + (f"What it has to do: {brief} " if brief else "")
        + (f"The setting: {v.get('who', '')} " if v.get("who") else "")
        + (""
           if refs else
           "No key visual, pack or cast reference is available — build this from the brand profile and "
           "the brief above alone, not from an invented layout.")
        + " Photographic, real Indian location, natural light, no text overlays or captions added."
    )

    eng = _engine(payload, "image")
    model, size, tier = _img_tier(payload, "pro")
    url, provider = "", ""
    # Tracked separately from `bool(refs)` on purpose: a reference call that comes back empty falls
    # through to a plain text render right below, and the caller still had `refs` non-empty at that
    # point — `used_refs` has to say whether the picture that actually shipped came from the references,
    # not whether some were merely offered, or the note keeps claiming a grounding that silently failed.
    used_refs = False
    if _use(eng, "google"):
        provider = "google"
        if refs:
            url = gemini.image_from_reference(prompt, refs, ratio=ratio, model=model, size=size)
            used_refs = bool(url)
        if not url:
            url = gemini.image(prompt, ratio=ratio, model=model, size=size)
    if not url and _use(eng, "fal"):
        # Round-83 audit, "fal-fallback-drops-references" — fixed alongside the identical bug in
        # /posm-image. Try the reference-aware fal call first when references exist, same as Google's
        # own branch above; only fall through to a blind text render when there's nothing to hold onto.
        provider = "fal"
        if refs:
            url = creative.image_from_reference(prompt, refs, ratio=ratio) or ""
            used_refs = bool(url)
        if not url:
            url = creative.text_to_image(prompt, ratio=ratio)["url"]
    if not url:
        return JSONResponse(status_code=502, content={
            "detail": "Both image providers refused this element — check credits for your Google and "
                      "fal keys (see render-log.txt).", "kv": role})
    # The note now says what actually happened, not what the role wanted to happen — a `source`
    # element whose reference call quietly fell through to a plain render used to still claim "Rendered
    # from the key visual", which is exactly the "quiet degradation mistaken for a considered answer"
    # this app's own routes elsewhere refuse to do.
    used_names = []
    if used_refs:
        if kv_url:
            used_names.append("the key visual")
        if payload.get("cast_id"):
            used_names.append("a locked cast reference")
        if payload.get("pack_id") or payload.get("product_id"):
            used_names.append("a locked pack/product reference")
    if role["role"] == "source":
        note = ("Rendered from the key visual." if used_refs else
                "The key visual reference did not come back from the provider — this is a plain render "
                "from the brief instead, not the artwork this element is supposed to be made of. Try "
                "rendering again.")
    elif used_refs:
        note = "Rendered from the brief, with " + " and ".join(used_names) + " as reference."
    else:
        note = ("Rendered from the brief and the brand profile — no key visual, pack or cast reference "
                "was available, so nothing but the brand grounding above shaped this.")
    _record_made("activation_element", f"{element.replace('_', ' ').title()} — {venue}", url=url,
                 payload=payload, route="/activation-element-image")
    return {"image_url": url, "provider": provider, "element": element, "venue": venue,
            "kv": role, "used_kv": used_refs, "refs_used": ref_roles, "ratio": ratio,
            "size_key": size_row[0] if size_row else "", "prompt": prompt, "tier": tier,
            "note": note}


@app.post("/activation-kit")
def activation_kit(payload: dict):
    """Everything a person needs to decide whether to book this idea. `{idea:{…venue…}, scale?,
    total_cost?, days?, start_by?}`.

    Reach, intercepted, cost-per-contact and the permission timeline — every number computed from a
    table, on the `posm.py` pattern: none of it is asked of a model, because none of it is a
    judgement. Only `total_cost` is ever required from a person, and its absence is a clean refusal
    rather than a guess wearing a decimal point.

    The chosen idea must already name its venue — an activation is not portable across venues, and a
    kit sheet is meaningless for the wrong one.
    """
    idea = payload.get("idea") if isinstance(payload.get("idea"), dict) else {}
    scale = str(payload.get("scale") or "single-site")
    try:
        days = max(0.5, float(payload.get("days") or 1))
    except (TypeError, ValueError):
        days = 1.0
    cost = payload.get("total_cost")
    try:
        cost = float(cost) if cost not in (None, "") else None
    except (TypeError, ValueError):
        cost = None
    out = activation.kit_sheet(idea, scale=scale, total_cost=cost, days=days,
                               start_by=str(payload.get("start_by") or ""))
    if not out["available"]:
        return JSONResponse(status_code=400, content={"detail": out["why"]})
    return out


@app.get("/activation-status")
def activation_status():
    """The venues, their footfall and permission numbers, and the scale ladder — so a screen renders
    its choices from data rather than a hard-coded list."""
    return activation.status()


# --- the two strategy documents, out to Word ---------------------------------------------------

_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@app.get("/house-docx/{house_id}")
def house_docx(house_id: str, mode: str = "record"):
    """The messaging house as a .docx — every layer, what was chosen, where it came from.

    `?mode=worksheet` returns the same content with each layer's question and ruled space to answer it
    again. That variant exists because the portal cannot import a Word file: if somebody is going to
    redo the exercise away from the screen, the paper should ask them the same questions in the same
    order, or they come back with answers that map onto no layer.

    Both modes carry the findings. A house that looks finished and is not is worse than one that admits
    it, and the export is exactly where that pretence usually happens: the blocking findings stay on the
    screen and the clean-looking Word file goes to the client.
    """
    h = strategy.load(house_id)
    if not h:
        return JSONResponse(status_code=404, content={"detail": "No such messaging house."})
    mode = "worksheet" if str(mode).lower() == "worksheet" else "record"
    try:
        out = docs.build_house_docx(h, strategy.status(h), mode=mode)
    except Exception as e:
        raise HTTPException(500, f"Messaging house document build failed: {e}")
    # The project is in the filename, because a folder of these was four files with the same name and
    # a (1), (2), (3) after it — and the project was the only thing that made them distinguishable.
    name = project.filename(h, h.get("brand") or "brand",
                            "messaging-house" + ("-worksheet" if mode == "worksheet" else ""))
    return FileResponse(out, filename=name, media_type=_DOCX)


@app.get("/platform-docx/{set_id}")
def platform_docx(set_id: str, mode: str = "record"):
    """The idea platform as a .docx — the idea, its mechanic, the five tests, each expression.

    The one document in the spine that did not exist. A platform is what every execution is an expression
    of, so it is the page most likely to be circulated, and there was no way to take it off the screen.
    """
    # Tolerant on what `set_id` is, because the screen holds three ids at once and picking the wrong one
    # is a 404 with nothing to debug. `/idea-platform` returns `set` (the set) AND `id` (the adopted
    # platform inside it), and the obvious guess is `id`. Accept a set id, a house id, or a platform id.
    pl = ideas.load(set_id) or (ideas.for_house(set_id) if set_id else None)
    if not pl and set_id:
        pl = next((s for row in ideas.sets()
                   if (s := ideas.load(row["id"]))
                   and any(x.get("id") == set_id for x in s.get("platforms", []))), None)
    if not pl:
        return JSONResponse(status_code=404, content={
            "detail": "No such idea platform. Send the set id (`set` on /idea-platform), the house id, "
                      "or the adopted platform's id — any of the three works."})
    mode = "worksheet" if str(mode).lower() == "worksheet" else "record"
    h = _platform_house(pl)
    try:
        out = docs.build_platform_docx(pl, ideas.status(pl, h), mode=mode, house=h)
    except Exception as e:
        raise HTTPException(500, f"Idea platform document build failed: {e}")
    name = project.filename(pl if project.of(pl) else dict(pl, project=project.of(h)),
                            pl.get("brand") or "brand",
                            "idea-platform" + ("-worksheet" if mode == "worksheet" else ""))
    return FileResponse(out, filename=name, media_type=_DOCX)


@app.get("/plan-docx/{plan_id}")
def plan_docx(plan_id: str, mode: str = "record"):
    """The communication plan as a .docx. Layers are tables, so these are real Word tables.

    `?mode=worksheet` adds each layer's question and three blank rows in the same table, so the columns
    of what you write line up with the columns of what is already there.
    """
    p = plan_mod.load(plan_id)
    if not p:
        return JSONResponse(status_code=404, content={"detail": "No such plan."})
    mode = "worksheet" if str(mode).lower() == "worksheet" else "record"
    try:
        h = _house_for(p)
        out = docs.build_plan_docx(p, plan_mod.status(p, h), mode=mode, house=h)
    except Exception as e:
        raise HTTPException(500, f"Communication plan document build failed: {e}")
    name = project.filename(p if project.of(p) else dict(p, project=project.of(h)),
                            p.get("brand") or "brand",
                            "comm-plan" + ("-worksheet" if mode == "worksheet" else ""))
    return FileResponse(out, filename=name, media_type=_DOCX)


@app.post("/finding-override")
def finding_override(payload: dict):
    """Accept the risk on a finding, in writing — or withdraw an acceptance.

    `{ doc: "house"|"plan", id, finding, reason, who }`, and `{ clear: true }` to withdraw.

    A blocking finding is resolved or overridden with a recorded reason, never closed. Until this
    existed the client had an override button writing to its own state, which is a dismissal wearing a
    reason box. An empty or one-word reason is refused: the sentence is the entire artefact here.
    """
    which = str(payload.get("doc") or "").lower()
    doc_id = str(payload.get("id") or "")
    fkey = str(payload.get("finding") or "")
    if which not in ("house", "plan"):
        return JSONResponse(status_code=400,
                            content={"detail": "doc must be 'house' or 'plan'."})
    if not fkey:
        return JSONResponse(status_code=400, content={"detail": "Which finding? Pass its key."})

    mod = strategy if which == "house" else plan
    doc = mod.load(doc_id)
    if not doc:
        return JSONResponse(status_code=404, content={"detail": f"No such {which}."})

    if payload.get("clear"):
        doc = mod.save(findings.clear(doc, fkey))
    else:
        doc, err = findings.record(doc, fkey, str(payload.get("reason") or ""),
                                   str(payload.get("who") or ""))
        if err:
            return JSONResponse(status_code=400, content={"detail": err})
        doc = mod.save(doc)

    if which == "house":
        return {"house": doc, "status": strategy.status(doc)}
    return {"plan": doc, "status": plan.status(doc, _house_for(doc))}


@app.get("/plan-prompt/{plan_id}/{layer}")
def plan_prompt(plan_id: str, layer: str):
    p = plan.load(plan_id)
    if not p or layer not in plan.LAYER_BY_ID:
        return JSONResponse(status_code=404, content={"detail": "Not found."})
    return {"prompt": plan.prompt_for(p, layer, _house_for(p), locked=library.locked_copy())}


# --- serve the front end (Claude Design build) ---------------------------------
_STATIC = os.path.join(os.path.dirname(__file__), "static")
_FE = os.path.join(os.path.dirname(__file__), "frontend")
from fastapi.staticfiles import StaticFiles

if os.path.isdir(os.path.join(_FE, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(_FE, "assets")), name="assets")

# --- served assets: routes, not static mounts ---------------------------------------------------
#
# These three were `app.mount(..., StaticFiles(...))` over the bare `api/renders`, `api/media` and
# `api/edits` directories — shared by every tenant and served to anybody holding a filename. A mount
# has nowhere to put a check, which is why this is a route now: `tenancy.asset_path` resolves
# tenant-first then legacy, refuses anything that escapes its directory, and there is one function to
# add an authentication check to when auth lands.
#
# The URL space is deliberately unchanged (`/renders/<name>`), because those URLs are written into
# stored executions, cuts and shots. Old files keep resolving from the legacy directory; new ones are
# written tenant-scoped. Nothing is moved — moving it would break the references.
#
# `{name:path}` rather than `{name}` so a name containing a slash reaches the containment check and is
# refused there, instead of 404-ing at the router and looking like a missing file.

def _serve_asset(kind: str, name: str):
    path = tenancy.asset_path(kind, name)
    if not path:
        # One answer for "not there" and "tried to escape", so the difference cannot be probed.
        return JSONResponse(status_code=404, content={"detail": "No such file."})
    return FileResponse(path)


# Joined film cuts (/produce-video writes here) so the player and MP4 download get one file.
@app.get("/renders/{name:path}")
def serve_render(name: str):
    return _serve_asset("renders", name)


# Google returns generated assets as bytes rather than hosted URLs, so they are written here and
# served back — everything downstream in this app passes URLs around.
@app.get("/media/{name:path}")
def serve_media(name: str):
    return _serve_asset("media", name)


# Cutdowns, reframes and green-screen composites. Kept apart from /renders because these are
# DERIVED from an approved master rather than generated — the distinction is what lets a
# cutdown inherit the master's sign-off.
@app.get("/edits/{name:path}")
def serve_edit(name: str):
    return _serve_asset("edits", name)


@app.get("/asset-state")
def asset_state():
    """What is tenant-scoped and what is still sitting in the shared directories.

    Reported rather than assumed. New writes are scoped; the files written before that are not, and a
    screen claiming isolation while 208 of them sit in a shared folder would be exactly the kind of
    unearned claim this codebase refuses everywhere else. `what_is_not_done` says so in words.
    """
    return tenancy.asset_state()

# The .dc.html source assumes its host provides React + ReactDOM (the Claude artifact sandbox
# does) and a window.claude.complete() bridge. Served standalone, we inject both BEFORE
# support.js (the dc-runtime) runs. React/ReactDOM 18.3.1 UMD match the standalone build.
_BRIDGE_MARK = "HF_HEAD_INJECT"
_HEAD_INJECT = """
<!-- HF_HEAD_INJECT -->
<script crossorigin src="https://unpkg.com/react@18.3.1/umd/react.production.min.js"></script>
<script crossorigin src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js"></script>
<script>
window.claude = window.claude || {};
window.claude.complete = async function(arg){
  var messages = (arg && arg.messages) ? arg.messages
    : [{role:'user', content:(typeof arg==='string'?arg:JSON.stringify(arg||''))}];
  var r = await fetch('/complete',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({messages:messages})});
  if(!r.ok) throw new Error('complete '+r.status);
  var j = await r.json();
  return j.completion || '';
};
</script>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    # Primary front end = the Claude Design build (Design Component + dc-runtime).
    html = open(os.path.join(_FE, "app.dc.html"), encoding="utf-8").read()
    if _BRIDGE_MARK not in html:
        html = html.replace("<head>", "<head>" + _HEAD_INJECT, 1) if "<head>" in html else _HEAD_INJECT + html
    return HTMLResponse(html)


@app.get("/support.js")
def dc_support():
    return FileResponse(os.path.join(_FE, "support.js"), media_type="application/javascript")


@app.get("/image-slot.js")
def dc_imageslot():
    return FileResponse(os.path.join(_FE, "image-slot.js"), media_type="application/javascript")


@app.get("/studio")
def studio():
    # legacy original bundle, kept for reference
    return FileResponse(os.path.join(_STATIC, "index.html"))


@app.get("/bridge.js")
def bridge():
    return FileResponse(os.path.join(_STATIC, "bridge.js"), media_type="application/javascript")


@app.get("/brand-brief-builder")
def brand_brief_builder():
    return FileResponse(os.path.join(_STATIC, "brand-brief-builder.html"))


@app.get("/builder")
def builder():
    return FileResponse(os.path.join(_STATIC, "builder.html"))


@app.get("/brief-schema")
def brief_schema_endpoint():
    """Section/sub-section schema per format. Comms/IMC follow the builder format;
    Media/Digital/Packaging/Product/PR follow the front end; brand routes to the skill."""
    import brief_schema as bs
    out = [{"id": "brand", "name": bs.BRAND_BRIEF["name"], "uses_skill": True, "source": "skill",
            "sections": [{"title": s, "fields": []} for s in bs.BRAND_BRIEF["sections"]]}]
    for fid in bs.ORDER:
        f = bs.FRONTEND_FORMATS[fid]
        out.append({"id": fid, "name": f["name"], "uses_skill": False, "source": f["source"],
                    "sections": [{"title": t, "fields": flds} for t, flds in f["sections"]]})
    return out


def _has_brief_input(data: dict, research=None) -> bool:
    """Is there anything to write a brief FROM?

    An empty payload produced a confident, complete brief about **Amul** — a named competitor the user
    never mentioned. That is the invented-brand failure at its worst: not a generic output but a specific
    wrong one, in a document designed to be shared. The model has to be given a subject or refused.
    """
    if research:
        try:
            if any(getattr(f, "filename", "") for f in research):
                return True
        except TypeError:
            pass
    for k in ("brand", "prompt", "category", "title", "ask", "objective", "brand_name"):
        if str((data or {}).get(k) or "").strip():
            return True
    # Any nested block with real content also counts — the builder posts several.
    for v in (data or {}).values():
        if isinstance(v, dict) and any(str(x).strip() for x in v.values()):
            return True
        if isinstance(v, list) and v:
            return True
    return False


@app.post("/brand-brief")
def brand_brief(payload: str = Form(...), research: list[UploadFile] = File(default=[])):
    """Builder payload (+ optional research files) -> the skill's .docx brand brief.

    Uploaded research is parsed (PDF/DOCX/PPTX/XLSX/CSV/TXT) and, when ANTHROPIC_API_KEY is
    set, mined into the brief's narrative sections; otherwise deterministic synthesis is used.
    """
    import tempfile

    import brief_render
    import research_parse
    data = json.loads(payload)
    data.setdefault("research_files", [f.filename for f in research])
    # See the guard on /brand-brief-draft: an empty payload here would build a document about a brand
    # nobody named.
    if not _has_brief_input(data, research):
        raise HTTPException(400, "Nothing to build from — name the brand, write a prompt, or attach "
                                 "research. An empty brief would be about a brand nobody named.")
    # Keep the brand brief too. This is the one with the brand on it, so it is the one that makes a
    # second brand visible to the house and plan screens at all.
    try:
        briefstore.put(data, brand=str(data.get("brand") or ""),
                       title=str(data.get("title") or ""), fmt="Brand",
                       source="brand-brief", brief_id=str(data.get("brief_id") or ""))
    except Exception:
        pass
    blobs = []
    if research:
        tmp = tempfile.mkdtemp(prefix="research_")
        paths = []
        for f in research:
            dest = os.path.join(tmp, os.path.basename(f.filename or "file"))
            with open(dest, "wb") as out:
                out.write(f.file.read())
            paths.append(dest)
        blobs = research_parse.parse_paths(paths)
    try:
        # Pure-Python renderer (Pillow figures + python-docx) — no Node / cairosvg needed.
        out = brief_render.generate(data, research_blobs=blobs)
    except Exception as e:
        raise HTTPException(500, f"Brief generation failed: {e}")
    return FileResponse(
        out, filename=os.path.basename(out),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


_IMAGE_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "gif": "image/gif", "webp": "image/webp"}


@app.post("/brand-brief-draft")
def brand_brief_draft(payload: str = Form(...), research: list[UploadFile] = File(default=[])):
    """Run the brand-brief SKILL to DRAFT the whole brief from a prompt + files.

    Returns the builder payload (competitors, NeedScope pins, CB/CA, SMP, defence, unlocks)
    for the front end to populate its editors so the user can review/edit before generating
    the Word document via /brand-brief. Requires ANTHROPIC_API_KEY.
    """
    import base64
    import tempfile

    import brief_ai
    import research_parse
    if not brief_ai.has_key():
        raise HTTPException(
            400, "AI drafting needs an Anthropic API key. Add ANTHROPIC_API_KEY to api/.env "
                 "and restart the server, or fill the brief in manually.")
    base = json.loads(payload)
    blobs, images, doc_paths = [], [], []
    tmp = tempfile.mkdtemp(prefix="draft_")
    for f in research:
        ext = os.path.splitext(f.filename or "")[1].lower().lstrip(".")
        raw = f.file.read()
        if ext in _IMAGE_TYPES:
            images.append({"filename": f.filename, "media_type": _IMAGE_TYPES[ext],
                           "data_b64": base64.b64encode(raw).decode("ascii")})
        else:
            dest = os.path.join(tmp, os.path.basename(f.filename or "file"))
            with open(dest, "wb") as out:
                out.write(raw)
            doc_paths.append(dest)
    if doc_paths:
        blobs = research_parse.parse_paths(doc_paths)
    if not _has_brief_input(base, research):
        raise HTTPException(400, "Nothing to draft from — name the brand, write a prompt, or attach "
                                 "research. Given nothing, the model writes a confident brief about a "
                                 "brand nobody named.")
    try:
        draft = brief_ai.draft_brief(base, blobs=blobs, images=images)
    except brief_ai.NoApiKey:
        raise HTTPException(400, "ANTHROPIC_API_KEY is not set.")
    except Exception as e:
        raise HTTPException(500, f"AI draft failed: {e}")
    # Keep the draft the moment it exists.
    #
    # Saving only on export was the wrong event: somebody writes a brief, moves on to the messaging
    # house, and it was never kept — because they had no reason to download a Word file first. A brief
    # that has been drafted is a brief worth having downstream, whether or not anybody prints it.
    try:
        saved = briefstore.put(draft, brand=str(draft.get("brand") or base.get("brand") or ""),
                               title=str(draft.get("title") or base.get("title") or ""),
                               fmt="Brand", source="brand-brief-draft",
                               brief_id=str(base.get("brief_id") or ""))
        if isinstance(draft, dict):
            draft["brief_id"] = saved["id"]
        # Already a real, tracked document via briefstore — reference it rather than creating a second,
        # untracked ledger row for the same event (see made.py's docstring on why this is the one route
        # in the wiring list that already has an id to point at instead of minting its own).
        _record_made("brief_draft", saved.get("title") or "AI-drafted brief",
                     payload={"brand": saved.get("brand", ""), "project": saved.get("project", "")},
                     ref_kind="brief", ref_id=saved.get("id", ""), route="/brand-brief-draft")
    except Exception:
        pass          # never let keeping a copy cost somebody their draft
    return draft


# ----------------------------------------------------------------------------- #
# Briefs
# ----------------------------------------------------------------------------- #
@app.get("/briefs", response_model=list[schemas.BriefOut])
def list_briefs(db: Session = Depends(get_db)):
    return list(db.scalars(select(Brief).order_by(Brief.created_at.desc())))


@app.post("/briefs", response_model=schemas.BriefOut)
def create_brief(payload: schemas.BriefIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    data = payload.model_dump()
    override = data.pop("required_levels", None)
    attrs = {"campaign_objective": data["campaign_objective"], "budget_value": data["budget_value"]}
    if override:
        attrs["required_levels"] = override
    b = Brief(id=_id("brief"), creator_id=user.id, status="Draft",
              required_levels=domain.required_levels("Brief", attrs),
              approvals=[], history=[], **data)
    db.add(b); db.commit(); db.refresh(b)
    return b


@app.get("/briefs/{brief_id}", response_model=schemas.BriefOut)
def get_brief(brief_id: str, db: Session = Depends(get_db)):
    b = db.get(Brief, brief_id)
    if not b: raise HTTPException(404, "Brief not found")
    return b


@app.put("/briefs/{brief_id}", response_model=schemas.BriefOut)
def update_brief(brief_id: str, payload: schemas.BriefIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    b = db.get(Brief, brief_id)
    if not b: raise HTTPException(404, "Brief not found")
    if b.status != "Draft":
        raise HTTPException(409, "Only a Draft brief can be edited.")
    data = payload.model_dump()
    override = data.pop("required_levels", None)
    for k, v in data.items():
        setattr(b, k, v)
    attrs = _brief_attrs(b)
    if override: attrs["required_levels"] = override
    b.required_levels = domain.required_levels("Brief", attrs)
    db.commit(); db.refresh(b)
    return b


def _transition(item, op, *args):
    try:
        op(item, *args)
    except ValueError as e:
        raise HTTPException(409, str(e))


@app.post("/briefs/{brief_id}/submit", response_model=schemas.BriefOut)
def submit_brief(brief_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    b = db.get(Brief, brief_id) or _404()
    _transition(b, domain.submit, user.id); db.commit(); db.refresh(b); return b


@app.post("/briefs/{brief_id}/approve", response_model=schemas.BriefOut)
def approve_brief(brief_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    b = db.get(Brief, brief_id) or _404()
    _transition(b, domain.approve, user.id, user.role); db.commit(); db.refresh(b); return b


@app.post("/briefs/{brief_id}/request-changes", response_model=schemas.BriefOut)
def request_changes_brief(brief_id: str, payload: schemas.ApproveIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    b = db.get(Brief, brief_id) or _404()
    _transition(b, domain.request_changes, user.id, payload.note); db.commit(); db.refresh(b); return b


def _404():
    raise HTTPException(404, "Not found")


# ----------------------------------------------------------------------------- #
# Generation — gated on the brief being Approved
# ----------------------------------------------------------------------------- #
@app.post("/briefs/{brief_id}/generate", response_model=list[schemas.DeliverableOut])
def generate(brief_id: str, payload: schemas.GenerateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    b = db.get(Brief, brief_id) or _404()
    if not domain.can_generate(b):
        raise HTTPException(409, f"Brief is '{b.status}'. Generation is blocked until the brief is Approved.")
    brief_dict = {c.name: getattr(b, c.name) for c in Brief.__table__.columns}
    out: list[Deliverable] = []
    for t in payload.targets:
        meta = catalog.platform_meta(t.platform)
        copy = generation.generate_copy(brief_dict, meta["name"], t.format)
        flags = generation.brand_check(copy["caption"], b.mandatories_brand_codes)
        d = Deliverable(
            id=_id("post"), brief_id=b.id, platform=meta["id"], format=t.format,
            content_type=t.content_type,
            caption=copy["caption"], hashtags=copy["hashtags"], rationale=copy["rationale"],
            brand_flags=flags, creator_id=user.id, status="Draft",
            required_levels=domain.required_levels("Deliverable", {"brief_required_levels": b.required_levels}),
            approvals=[], history=[],
        )
        if payload.creative_model:
            if creative.model_provider(payload.creative_model) == "heygen":
                # avatar video: the script is the post copy itself
                res = creative.generate_creative(
                    payload.creative_model, copy["caption"],
                    avatar=payload.avatar, voice=payload.voice, ratio=payload.ratio)
            else:
                prompt = f"{b.single_minded_proposition}. {t.platform} {t.format}. {b.tone_personality}"
                res = creative.generate_creative(payload.creative_model, prompt)
            d.creative_kind = res["kind"]; d.creative_model = res["model"]; d.creative_url = res["url"]
        db.add(d); out.append(d)
    db.commit()
    for d in out: db.refresh(d)
    return out


# ----------------------------------------------------------------------------- #
# Deliverables
# ----------------------------------------------------------------------------- #
@app.get("/deliverables", response_model=list[schemas.DeliverableOut])
def list_deliverables(brief_id: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    q = select(Deliverable)
    if brief_id: q = q.where(Deliverable.brief_id == brief_id)
    if status: q = q.where(Deliverable.status == status)
    return list(db.scalars(q.order_by(Deliverable.created_at.desc())))


@app.get("/deliverables/{did}", response_model=schemas.DeliverableOut)
def get_deliverable(did: str, db: Session = Depends(get_db)):
    return db.get(Deliverable, did) or _404()


@app.put("/deliverables/{did}", response_model=schemas.DeliverableOut)
def edit_deliverable(did: str, payload: schemas.EditDeliverableIn, db: Session = Depends(get_db)):
    d = db.get(Deliverable, did) or _404()
    if d.status not in ("Draft", "Changes"):
        raise HTTPException(409, "Only a Draft/Changes post can be edited.")
    if payload.caption is not None: d.caption = payload.caption
    if payload.hashtags is not None: d.hashtags = payload.hashtags
    b = db.get(Brief, d.brief_id)
    d.brand_flags = generation.brand_check(d.caption, b.mandatories_brand_codes if b else "")
    db.commit(); db.refresh(d); return d


@app.post("/deliverables/{did}/submit", response_model=schemas.DeliverableOut)
def submit_deliverable(did: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    d = db.get(Deliverable, did) or _404()
    _transition(d, domain.submit, user.id); db.commit(); db.refresh(d); return d


@app.post("/deliverables/{did}/approve", response_model=schemas.DeliverableOut)
def approve_deliverable(did: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    d = db.get(Deliverable, did) or _404()
    _transition(d, domain.approve, user.id, user.role); db.commit(); db.refresh(d); return d


@app.post("/deliverables/{did}/request-changes", response_model=schemas.DeliverableOut)
def request_changes_deliverable(did: str, payload: schemas.ApproveIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    d = db.get(Deliverable, did) or _404()
    _transition(d, domain.request_changes, user.id, payload.note); db.commit(); db.refresh(d); return d


@app.post("/deliverables/{did}/publish", response_model=schemas.DeliverableOut)
def publish_deliverable(did: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    d = db.get(Deliverable, did) or _404()
    _transition(d, domain.publish, user.id); db.commit(); db.refresh(d); return d


@app.post("/deliverables/{did}/creative", response_model=schemas.DeliverableOut)
def set_creative(did: str, payload: schemas.CreativeIn, db: Session = Depends(get_db)):
    d = db.get(Deliverable, did) or _404()
    if d.status not in ("Draft", "Changes"):
        raise HTTPException(409, "Creatives can only change while the post is editable (Draft/Changes).")
    b = db.get(Brief, d.brief_id)
    is_avatar = creative.model_provider(payload.model_id) == "heygen"
    if is_avatar:
        # script = explicit prompt, else the post's own caption
        prompt = payload.prompt or d.caption or (b.single_minded_proposition if b else "")
        res = creative.generate_creative(payload.model_id, prompt,
                                         avatar=payload.avatar, voice=payload.voice, ratio=payload.ratio)
    else:
        prompt = payload.prompt or f"{b.single_minded_proposition}. {d.platform} {d.format}. {b.tone_personality}"
        res = creative.generate_creative(payload.model_id, prompt)
    d.creative_kind = res["kind"]; d.creative_model = res["model"]; d.creative_url = res["url"]
    db.commit(); db.refresh(d); return d


# ----------------------------------------------------------------------------- #
# Per-post chat studio — iterate copy (and optionally creative) by chatting
# ----------------------------------------------------------------------------- #
@app.get("/deliverables/{did}/chat", response_model=list[schemas.ChatMessageOut])
def get_chat(did: str, db: Session = Depends(get_db)):
    d = db.get(Deliverable, did) or _404()
    return d.messages


@app.post("/deliverables/{did}/chat", response_model=schemas.DeliverableOut)
def post_chat(did: str, payload: schemas.ChatIn, db: Session = Depends(get_db)):
    d = db.get(Deliverable, did) or _404()
    if d.status not in ("Draft", "Changes"):
        raise HTTPException(409, "You can only refine an editable post (Draft/Changes) in the studio.")
    b = db.get(Brief, d.brief_id)
    brief_dict = {c.name: getattr(b, c.name) for c in Brief.__table__.columns}
    db.add(ChatMessage(id=_id("msg"), deliverable_id=d.id, role="user", content=payload.message))
    prior = {"caption": d.caption, "hashtags": d.hashtags, "rationale": d.rationale}
    revised = generation.generate_copy(brief_dict, d.platform, d.format,
                                        instruction=payload.message, prior=prior)
    d.caption = revised["caption"]; d.hashtags = revised["hashtags"]; d.rationale = revised["rationale"]
    d.brand_flags = generation.brand_check(d.caption, b.mandatories_brand_codes if b else "")
    assistant = (f"Updated the {d.platform} {d.format} copy. "
                 + ("Heads up — " + "; ".join(d.brand_flags) if d.brand_flags else "All brand mandatories present."))
    db.add(ChatMessage(id=_id("msg"), deliverable_id=d.id, role="assistant", content=assistant))
    db.commit(); db.refresh(d); return d
