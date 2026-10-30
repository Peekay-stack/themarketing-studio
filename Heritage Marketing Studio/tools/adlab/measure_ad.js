// measure_ad.js -- FREE measurements of a reference ad playing in the built-in browser (AD_REFERENCE_FRAMEWORK.md, "measured" evidence). Paste the whole file into the browser tool's
// javascript_exec on a YouTube watch page (it returns at once and keeps measuring in the page); then read `window.__ad.summary` after the film's length plus a few seconds.
//
// What it measures while the ad plays ONCE at normal speed, from the pictures and the sound the browser itself decodes (nothing is downloaded or saved, nothing leaves the page):
//   picture: the mean absolute change between consecutive frames (64x36 grey) -> hard cuts, shots, shot lengths, shots per 10 s, motion inside shots, brightness per second.
//   sound:   RMS level (dBFS) and three band energies every 50 ms from an analyser node -> loudness per second, silent stretches, where the level lifts, the first and last sound.
//            The audio goes ONLY to the analyser (it is not connected to the speakers), so the person hears nothing.
// What it cannot do: tell speech from music, hear a language, judge a voice. Those stay "not judged" in the framework.
// If YouTube plays its own advert first, it waits for it to end and says so. Reload the page afterwards (the player's audio is re-routed once).
// THE BROWSER PANE MUST BE DISPLAYED (ask the app to show it): in a hidden pane the page draws no video frames (0 frames measured) and the sound meter reads silence (30 Oct, first run).
// Cuts come in two grades: `cuts` (a frame change of at least max(22, 8x the film's median change): sure cuts) and `cutsProbable` (a change of 40 or more that did not make the first list: whips,
// fast zooms and soft cuts in high-motion footage, e.g. a cut at 42 in a film whose median is 7). Verify the probable ones by eye; the report gives both counts.
(async () => {
  const wait = (ms) => new Promise(r => setTimeout(r, ms));
  const M = window.__ad = { status: 'starting', frames: [], audio: [], info: {}, summary: null };
  const v = document.querySelector('video.html5-main-video') || document.querySelector('video');
  if (!v) { M.status = 'no video element'; return 'no video element'; }
  const player = document.querySelector('.html5-video-player');
  // switch YouTube's autoplay-next off for this tab so the page does not move on to another video while we measure
  const auto = document.querySelector('.ytp-autonav-toggle-button'); if (auto && auto.getAttribute('aria-checked') === 'true') auto.click();
  M.info.sawAdvert = false;
  for (let i = 0; i < 90 && player && player.classList.contains('ad-showing'); i++) { M.info.sawAdvert = true; await wait(500); }
  v.pause(); v.currentTime = 0; await wait(700);
  const dur = v.duration;
  M.info = { ...M.info, duration: +dur.toFixed(2), width: v.videoWidth, height: v.videoHeight };
  const cvs = document.createElement('canvas'); cvs.width = 64; cvs.height = 36; const ctx = cvs.getContext('2d', { willReadFrequently: true });
  let prev = null;
  // sound: an analyser fed from the element, NOT connected to the destination
  let an = null, td = null, fd = null, ac = null;
  try {
    ac = new (window.AudioContext || window.webkitAudioContext)(); await ac.resume();
    const src = ac.createMediaElementSource(v); an = ac.createAnalyser(); an.fftSize = 2048; an.smoothingTimeConstant = 0;
    src.connect(an); td = new Float32Array(an.fftSize); fd = new Float32Array(an.frequencyBinCount);
    M.info.audio = ac.state;
  } catch (e) { M.info.audio = 'unavailable: ' + String(e && e.message || e); an = null; }
  const binHz = ac ? ac.sampleRate / 2048 : 21.5;
  const bandOf = (a, b) => { let s = 0; const i0 = Math.max(1, Math.floor(a / binHz)), i1 = Math.min(fd.length - 1, Math.floor(b / binHz)); for (let i = i0; i <= i1; i++) s += Math.pow(10, fd[i] / 10); return s; };
  const onFrame = (now, meta) => {
    try {
      ctx.drawImage(v, 0, 0, 64, 36); const px = ctx.getImageData(0, 0, 64, 36).data; const g = new Uint8Array(64 * 36); let sum = 0;
      for (let i = 0, j = 0; i < px.length; i += 4, j++) { g[j] = (px[i] * 0.3 + px[i + 1] * 0.59 + px[i + 2] * 0.11) | 0; sum += g[j]; }
      let d = 0; if (prev) { for (let j = 0; j < g.length; j++) d += Math.abs(g[j] - prev[j]); d /= g.length; }
      M.frames.push([+meta.mediaTime.toFixed(3), +d.toFixed(2), +(sum / g.length).toFixed(1)]); prev = g;
    } catch (e) { M.info.frameErr = String(e && e.message || e); }
    if (!v.ended && v.currentTime < dur - 0.06) v.requestVideoFrameCallback(onFrame);
  };
  const tick = setInterval(() => {
    if (!an) return;
    an.getFloatTimeDomainData(td); let s = 0; for (let i = 0; i < td.length; i++) s += td[i] * td[i]; const rms = Math.sqrt(s / td.length);
    an.getFloatFrequencyData(fd);
    M.audio.push([+v.currentTime.toFixed(2), +(20 * Math.log10(rms + 1e-9)).toFixed(1), +(10 * Math.log10(bandOf(20, 250) + 1e-12)).toFixed(1), +(10 * Math.log10(bandOf(250, 4000) + 1e-12)).toFixed(1), +(10 * Math.log10(bandOf(4000, 16000) + 1e-12)).toFixed(1)]);
  }, 50);
  v.playbackRate = 1; M.status = 'playing';
  await v.play(); v.requestVideoFrameCallback(onFrame);
  const done = () => {
    clearInterval(tick); v.pause();
    const F = M.frames, cuts = []; const ds = F.map(x => x[1]).slice(1).sort((a, b) => a - b); const med = ds.length ? ds[Math.floor(ds.length / 2)] : 0;
    const thr = Math.max(22, med * 8);
    for (let i = 1; i < F.length; i++) if (F[i][1] >= thr && (!cuts.length || F[i][0] - cuts[cuts.length - 1] > 0.25)) cuts.push(+F[i][0].toFixed(2));
    const probable = []; for (let i = 1; i < F.length; i++) if (F[i][1] >= 40 && F[i][1] < thr && !cuts.some(c => Math.abs(c - F[i][0]) < 0.25) && (!probable.length || F[i][0] - probable[probable.length - 1] > 0.25)) probable.push(+F[i][0].toFixed(2));
    const edges = [0].concat(cuts, [dur]), shots = []; for (let i = 0; i < edges.length - 1; i++) shots.push(+(edges[i + 1] - edges[i]).toFixed(2));
    const perSec = []; for (let s = 0; s < Math.ceil(dur); s++) {
      const fs = F.filter(x => x[0] >= s && x[0] < s + 1 && !cuts.some(c => Math.abs(c - x[0]) < 0.05)), as = M.audio.filter(x => x[0] >= s && x[0] < s + 1);
      perSec.push({ s, motion: fs.length ? +(fs.reduce((a, x) => a + x[1], 0) / fs.length).toFixed(2) : null, luma: fs.length ? +(fs.reduce((a, x) => a + x[2], 0) / fs.length).toFixed(0) : null,
        dB: as.length ? +(as.reduce((a, x) => a + x[1], 0) / as.length).toFixed(1) : null, speechBandShare: as.length ? +(as.reduce((a, x) => a + Math.pow(10, (x[3] - Math.max(x[2], x[3], x[4])) / 10), 0) / as.length).toFixed(2) : null });
    }
    const dbs = perSec.map(p => p.dB).filter(x => x !== null), loud = dbs.length ? Math.max(...dbs) : null;
    const silent = perSec.filter(p => p.dB !== null && p.dB < -55).map(p => p.s);
    M.summary = { info: M.info, cutThreshold: +thr.toFixed(1), medianFrameChange: med, cuts, cutsProbable: probable, shots: shots.length, shotLengths: shots, avgShot: +(dur / shots.length).toFixed(2), shotsPer10s: +(shots.length * 10 / dur).toFixed(1),
      longestShot: Math.max(...shots), shortestShot: Math.min(...shots), perSecond: perSec, loudestDb: loud, quietestDb: dbs.length ? Math.min(...dbs) : null, silentSeconds: silent, framesSeen: F.length, audioSamples: M.audio.length };
    M.status = 'done'; try { sessionStorage.setItem('__ad_summary', JSON.stringify(M.summary)); } catch (e) {}      // survives a page change
  };
  const poll = setInterval(() => { if (v.ended || v.currentTime >= dur - 0.08) { clearInterval(poll); setTimeout(done, 300); } }, 200);
  return 'measuring ' + M.info.duration + ' s (' + M.info.width + 'x' + M.info.height + '), audio ' + M.info.audio + (M.info.sawAdvert ? ', waited out an advert' : '');
})()
