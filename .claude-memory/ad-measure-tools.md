---
name: ad-measure-tools
description: The free in-browser meters for reading a reference ad (picture cuts, brightness, sound level per second) and the snippets to read their results; the one-paste script is stored here in full so it survives a lost worktree.
metadata:
  type: reference
---

Part of [[reference-ad-framework-and-log]]. The scripts also live in the repo at `Heritage Marketing Studio/tools/adlab/` (branch `film-engagement-2`).

## How to run
1. Show the pane (`mcp__ccd_view__show_pane preview`), open a FRESH foreground tab (`tabs_create foreground:true`), `navigate` to `https://www.youtube.com/watch?v=<id>` (no `&list=`), confirm `document.hidden` is false.
2. `javascript_tool` (`javascript_exec`, with the tab id): paste the whole one-paste script below. It returns the page facts and keeps measuring in the page (about 1x the film length for the play pass, then about 0.5x for the seek pass). YouTube blocks fetching local scripts, so it must be pasted inline each time; `javascript_exec` times out at 45 s, so read results in separate calls (a `for` wait loop of at most ~42 s).
3. Read the results (snippets below), then take stills.

## Read-snippets (paste into javascript_exec on the same tab)
Hard-cut reading from the frame callbacks (use only if frames are about 24 a second):
`const R=window.__res,F=R.frames;const ds=F.map(x=>x[1]).slice(1).sort((a,b)=>a-b);const med=ds[Math.floor(ds.length/2)];const thr=Math.max(22,med*8);const cuts=[];for(let i=1;i<F.length;i++)if(F[i][1]>=thr&&(!cuts.length||F[i][0]-cuts[cuts.length-1]>0.25))cuts.push(+F[i][0].toFixed(2));` then shot lengths = successive differences with 0 and `R.meta.dur`; shots per 10 s = shots*10/dur.
Sound per second: `R.audio.map((a,s)=>a?Math.round(a.db/a.n)+'/'+(a.sp/a.n).toFixed(1):'-').join(' ')` (dB / mid-band share; a high share says the mid band is busy = speech or music, not that it is speech). Brightness per second: average of `frames[..][2]` per second.
DARK films (mean brightness under about 40): cuts are local peaks, `F[i][1]>=15 && F[i][1]>=F[i-1][1] && F[i][1]>=F[i+1][1]` merged within 0.5 s; report as "estimated".
Seek meter (`R.sk`, `[time, change, brightness]`; the time is the real landing time): use when frames are far below 24 a second; for a long film use a local rule (a change at least 2.3 x the median of its 6 neighbours each side and at least 28).
Stills: `document.querySelector('video').currentTime=T`, wait 2 s, `computer zoom region [0,50,800,490] scale 0.35`; the seek lands about 0.25 s late; for dark films first set `video.style.filter='brightness(2.4)'` (a viewing aid, remove after).

## The one-paste script (`measure_ad_all.js`)
```js
// measure_ad_all.js -- the ONE-PASTE meter for a reference ad on a YouTube watch page (AD_REFERENCE_FRAMEWORK.md section 6). Paste the whole file into the browser tool's javascript_exec,
// in a VISIBLE foreground tab (check `document.hidden` is false; a fresh tab opened with foreground:true works). It returns the page facts at once and keeps measuring in the page:
//   1. waits out a YouTube advert, switches autoplay off, reads title / channel / views / description / duration / picture size;
//   2. plays the ad once at normal speed and records, per video frame (requestVideoFrameCallback), the grey 64x36 frame change and brightness -> window.__res.frames [time, change, brightness];
//      and, per 0.1 s, the sound level (dB) and the mid-band share -> window.__res.audio[second] = {n, db, sp} (the sound goes to a meter only, never to the speakers);
//   3. then seeks through the film (every 0.1 s, or 0.25 s for a film over 120 s) -> window.__res.sk [time, change, brightness], the fallback when the frame callbacks were throttled.
// Read it with the snippets in the memory note `ad-measure-tools`: cuts = frame changes of at least max(22, 8 x the median); in a DARK film use local peaks of 15 or more and say "estimated";
// a frame count far below 24 a second means the tab was throttled (use `sk`, or a fresh foreground tab). Cards, fades and dissolves are not cuts. The seek lands about 0.25 s late.
(async () => {
  const wait = (ms) => new Promise(r => setTimeout(r, ms));
  await wait(3000);
  const g = s => document.querySelector(s);
  const R = window.__res = { stage: 'start', meta: {}, audio: [], frames: [], sk: [] };
  const pl = g('.html5-video-player'); for (let i = 0; i < 30 && pl && pl.classList.contains('ad-showing'); i++) { const sk = g('.ytp-skip-ad-button, .ytp-ad-skip-button-modern'); if (sk && sk.offsetParent) sk.click(); await wait(1000); }
  const v = g('video'); const dur = v.duration;
  R.meta = { title: document.title, channel: (g('ytd-channel-name a') || {}).textContent, info: (g('#info-container') || {}).innerText, desc: ((g('#description-inner') || {}).innerText || '').slice(0, 500), dur, w: v.videoWidth, h: v.videoHeight, hidden: document.hidden };
  const auto = g('.ytp-autonav-toggle-button'); if (auto && auto.getAttribute('aria-checked') === 'true') auto.click();
  (async () => {
    v.pause(); v.currentTime = 0; await wait(700);
    const ac = new (window.AudioContext || window.webkitAudioContext)(); await ac.resume();
    const src = ac.createMediaElementSource(v); const an = ac.createAnalyser(); an.fftSize = 2048; an.smoothingTimeConstant = 0; src.connect(an);
    const td = new Float32Array(2048), fd = new Float32Array(1024); const binHz = ac.sampleRate / 2048;
    const band = (a, b) => { let s = 0; for (let i = Math.max(1, Math.floor(a / binHz)); i <= Math.min(1023, Math.floor(b / binHz)); i++) s += Math.pow(10, fd[i] / 10); return s; };
    const cvs = document.createElement('canvas'); cvs.width = 64; cvs.height = 36; const ctx = cvs.getContext('2d', { willReadFrequently: true }); let prev = null;
    const onF = (n, m) => { try { ctx.drawImage(v, 0, 0, 64, 36); const px = ctx.getImageData(0, 0, 64, 36).data; const gg = new Uint8Array(2304); let sum = 0; for (let i = 0, j = 0; i < px.length; i += 4, j++) { gg[j] = (px[i] * .3 + px[i + 1] * .59 + px[i + 2] * .11) | 0; sum += gg[j]; } let d = 0; if (prev) { for (let j = 0; j < 2304; j++) d += Math.abs(gg[j] - prev[j]); d /= 2304; } R.frames.push([+m.mediaTime.toFixed(2), +d.toFixed(1), +(sum / 2304).toFixed(0)]); prev = gg; } catch (e) {} if (!v.ended && v.currentTime < dur - 0.06) v.requestVideoFrameCallback(onF); };
    const tick = setInterval(() => { an.getFloatTimeDomainData(td); let s = 0; for (let i = 0; i < 2048; i++) s += td[i] * td[i]; an.getFloatFrequencyData(fd); const t = Math.floor(v.currentTime); const e = R.audio[t] || (R.audio[t] = { n: 0, db: 0, sp: 0 }); const rms = Math.sqrt(s / 2048); const lo = band(20, 250), mid = band(250, 4000), hi = band(4000, 16000); e.n++; e.db += 20 * Math.log10(rms + 1e-9); e.sp += mid / Math.max(lo, mid, hi); }, 100);
    R.stage = 'playing'; await v.play(); v.requestVideoFrameCallback(onF);
    while (!v.ended && v.currentTime < dur - 0.1) await wait(300);
    clearInterval(tick); v.pause(); R.stage = 'seeking';
    const c2 = document.createElement('canvas'); c2.width = 64; c2.height = 36; const x2 = c2.getContext('2d', { willReadFrequently: true }); let p2 = null;
    const seek = t => new Promise(r => { let d = false; const f = () => { if (d) return; d = true; v.removeEventListener('seeked', f); setTimeout(r, 20); }; v.addEventListener('seeked', f); v.currentTime = t; setTimeout(f, 400); });
    const step = dur > 120 ? 0.25 : 0.1;
    for (let t = 0; t < dur - 0.05; t += step) { await seek(t); x2.drawImage(v, 0, 0, 64, 36); const p = x2.getImageData(0, 0, 64, 36).data; const gg = new Uint8Array(2304); let s = 0; for (let i = 0, j = 0; i < p.length; i += 4, j++) { gg[j] = (p[i] * .3 + p[i + 1] * .59 + p[i + 2] * .11) | 0; s += gg[j]; } let d = 0; if (p2) { for (let j = 0; j < 2304; j++) d += Math.abs(gg[j] - p2[j]); d /= 2304; } R.sk.push([+v.currentTime.toFixed(2), +d.toFixed(1), +(s / 2304).toFixed(0)]); p2 = gg; }
    R.stage = 'done';
  })();
  return R.meta;
})()
```

## The seek-only fallback (`measure_ad_seek.js`)
```js
// measure_ad_seek.js -- the FALLBACK picture meter for a reference ad (AD_REFERENCE_FRAMEWORK.md section 6). Use it when measure_ad.js reports far fewer frames than about 24 a second
// (it gave 24 frames for a 43 s, 320x240 upload on 30 Oct) or cuts about once a second: the page was not delivering every frame, so a "cut" was just the next frame.
// It seeks to every 0.1 s, waits for the frame, and records the grey-frame change and brightness, so it does not depend on playback. Paste it whole into the browser tool's javascript_exec on a
// YouTube watch page (the browser pane must be displayed). It returns at once; read `window.__sk` ([time, change, brightness]) when `window.__skdone` is true (about 40 s for a 43 s film).
// Treat a change of 28 or more as a CANDIDATE cut, not a cut: in handheld, low-resolution footage ordinary motion reaches 15-20 per 0.1 s. Check each candidate by eye before counting shots.
// It does not measure sound (use measure_ad.js for that, once).
(async () => {
  const v = document.querySelector('video'); v.pause();
  const c = document.createElement('canvas'); c.width = 64; c.height = 36; const x = c.getContext('2d', { willReadFrequently: true });
  let prev = null; const F = []; window.__sk = F; window.__skdone = false;
  const seek = t => new Promise(r => { let done = false; const f = () => { if (done) return; done = true; v.removeEventListener('seeked', f); setTimeout(r, 30); }; v.addEventListener('seeked', f); v.currentTime = t; setTimeout(f, 400); });
  for (let t = 0; t < v.duration - 0.05; t += 0.1) {
    await seek(t);
    try {
      x.drawImage(v, 0, 0, 64, 36); const p = x.getImageData(0, 0, 64, 36).data; const g = new Uint8Array(2304); let s = 0;
      for (let i = 0, j = 0; i < p.length; i += 4, j++) { g[j] = (p[i] * .3 + p[i + 1] * .59 + p[i + 2] * .11) | 0; s += g[j]; }
      let d = 0; if (prev) { for (let j = 0; j < 2304; j++) d += Math.abs(g[j] - prev[j]); d /= 2304; }
      F.push([+t.toFixed(2), +d.toFixed(1), +(s / 2304).toFixed(0)]); prev = g;
    } catch (e) {}
  }
  window.__skdone = true;
})(); 'started'
```

