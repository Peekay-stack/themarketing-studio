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
