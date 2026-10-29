// film_audit_wiring.js -- the wiring checks from the 29 Oct blast-radius audit of A1-A8 (out-of-date frames, reasons, confirms, the kept shot-plan reason, the re-time note), driven on the REAL page with
// the network stubbed. What the audit added to film_stale_frames.js: a failing frame must not leave the bulk buttons locked, the new shots of Phase 3 must not be counted as out of date until they have a
// frame, a frame's fingerprint must survive a save and a load, the re-time note must not follow a film the person has moved away from, and the banner must stay cheap to draw.
//
// How to run: start the studio, open http://localhost:8000/app (or your port), run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 500 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.staleSlots === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.staleSlots === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const realFetch = window.fetch, realToast = I.showToast, realGen = I.generateFrame, realConfirm = window.confirm;
  let film = null;
  window.fetch = async (u) => new Response(/\/video-script/.test(String(u)) ? JSON.stringify(film) : '{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
  I.showToast = () => {}; window.confirm = () => true;
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const txt = () => document.body.innerText;
  const rows = [1, 2, 3, 4].map(n => ({ no: n, tc: (n * 6 - 6) + '–' + (n * 6) + 's', visual: 'Scene ' + n + ' shows something different.', audio: [] }));
  const withShots = rows.map((r, i) => (i === 1 ? { ...r, shots: [{ visual: 'The milk climbs the pot.', secs: 2, job: 'insert', why: 'boil', shot_size: 'detail' }, { visual: 'She holds the glass to the window.', secs: 2, job: 'reveal', why: 'light', shot_size: 'over' }] } : r));
  try {
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'shootboard', scriptPhase: 'script', scriptStatus: 'approved', prodDuration: '30s', videoAssetsLoaded: true, castRefUrl: '/media/cast.png', framesBatch: false, staleBusy: '',
      fullScript: withShots, shoot: {}, videoConcept: { logline: 'L', proposition: 'P', vo: '', scenes: [] }, videoBeatMap: null, filmReview: null, sceneFrames: {} });
    await wait(500);
    // frames drawn for the four masters only, each stamped with today's recipe and fingerprint (as renderFrameResult does)
    const stamp = () => { const fr = {}; for (let i = 0; i < 4; i++) fr[i] = { status: 'done', url: '/media/f' + i + '.jpg', sig: 'x', recipe: I.frameRecipe(i, 0), parts: I.frameParts(i, 0) }; return fr; };
    I.setState({ sceneFrames: stamp() }); await wait(500);
    check('the frame slots are the 4 scenes plus the 2 new extra shots; only the 4 drawn frames exist, and none is out of date', I.frameTotal() === 6 && I.framesDoneCount() === 4 && I.staleSlots().length === 0, [I.frameTotal(), I.framesDoneCount(), I.staleSlots().length]);

    // a department note written afterwards: exactly the DRAWN frames are stale, the 2 shots with no frame yet are not counted; the reasons name the department
    I.setState(s => ({ shoot: { ...(s.shoot || {}), lighting: { text: 'Soft east window light.' } } })); await wait(500);
    const st = I.staleSlots();
    check('after a department note, the 4 drawn frames are out of date and the 2 undrawn extra shots are NOT counted', st.length === 4 && st.every(x => x.k === 0), st.map(x => x.key).join(','));
    check('the banner counts them against all 6 frames and names the department note as the reason', /4 of 6 frames are out of date/.test(txt()) && /a department note \(DoP, lighting, props or wardrobe\) \(4\)/.test(txt()), (txt().match(/\d of \d frames are out of date[^\n]*/) || [''])[0] + ' | ' + (txt().match(/What changed[^\n]*/) || [''])[0]);

    // 1. a frame that throws must not leave both bulk buttons locked
    let calls = 0; I.generateFrame = () => async () => { calls++; throw new Error('the image service fell over'); };
    let threw = false; try { await I.rerenderStale(); } catch (e) { threw = true; }
    check('when a frame throws, the re-render stops, the error is not swallowed, and the bulk buttons are NOT left locked', threw && calls === 1 && I.state.framesBatch === false && I.state.staleBusy === '', JSON.stringify({ threw, calls, fb: I.state.framesBatch, sb: I.state.staleBusy }));
    I.generateFrame = realGen;

    // 2. a normal re-render touches only the stale, drawn frames (never the undrawn shots) and re-stamps them current
    calls = 0; const order = [];
    I.generateFrame = (idx, k = 0) => async () => { calls++; order.push(idx + '.' + k); I.setState(s => ({ sceneFrames: { ...s.sceneFrames, [I.frameKey(idx, k)]: { status: 'done', url: '/media/n' + idx + '.jpg', sig: 'x', recipe: I.frameRecipe(idx, k), parts: I.frameParts(idx, k) } } })); await wait(20); };
    await I.rerenderStale(); await wait(400);
    check('re-render-out-of-date redraws exactly the 4 stale frames, in film order, and nothing for the 2 undrawn shots', calls === 4 && order.join(' ') === '0.0 1.0 2.0 3.0', order.join(' '));
    check('afterwards nothing is out of date, the buttons are free, and the banner is gone', I.staleSlots().length === 0 && !I.state.framesBatch && !/frames are out of date/.test(txt()));
    I.generateFrame = realGen;

    // 3. a frame re-drawn after the shot it is matched to changes goes stale again, with its own reason (an extra angle follows its master)
    I.setState(s => ({ sceneFrames: { ...s.sceneFrames, [I.frameKey(1, 1)]: { status: 'done', url: '/media/x1.jpg', sig: 'x', recipe: I.frameRecipe(1, 1), parts: I.frameParts(1, 1) } } })); await wait(300);
    check('an extra shot that has a frame counts as a frame and is current while its master is unchanged', I.framesDoneCount() === 5 && I.staleSlots().length === 0, [I.framesDoneCount(), I.staleSlots().length]);
    I.setState(s => ({ sceneFrames: { ...s.sceneFrames, 1: { ...s.sceneFrames[1], url: '/media/master-new.jpg' } } })); await wait(300);
    check('re-drawing the master makes its extra angle out of date, for the reason "the shot it is matched to"', I.staleSlots().length === 1 && I.staleSlots()[0].k === 1 && /the shot it is matched to/.test(I.staleWhyText(1, I.staleSlots()[0].f, 1)), JSON.stringify(I.staleSlots().map(x => x.key + ':' + I.staleWhyText(x.idx, x.f, x.k))));

    // 4. save and load keep a frame's fingerprint, so the reason survives a reload
    const saved = I.settledFrames(stamp());
    check('settledFrames (used for the save and the load) keeps every field of a drawn frame, including its fingerprint, and drops only a frame mid-render', saved[0].parts && saved[0].parts.dept && saved[0].recipe && Object.keys(I.settledFrames({ 0: { status: 'rendering' }, 1: saved[1] })).join() === '1');
    film = { house: 'h1', video_concept: { logline: 'L', proposition: 'P', vo: '', scenes: [] }, script_status: 'approved', script_phase: 'script', full_script: rows, scene_frames: stamp(), shoot: {}, video_beat_map: null };
    I.setState({ house: { id: 'h1' }, retimeNote: 'scene 3: 3 s → 6 s (an earlier film)', staleBusy: '2 of 5' });
    await I.loadVideoScript(); await wait(500);
    check('loading a film brings its frames back WITH their fingerprints, and clears the re-time note and the re-render counter of whatever was open before', Object.values(I.state.sceneFrames).every(f => f.parts && f.parts.words) && I.state.retimeNote === '' && I.state.staleBusy === '', JSON.stringify({ n: I.state.retimeNote, b: I.state.staleBusy }));

    // 5. the banner stays cheap: 12 drawn frames, 40 renders of the banner and the counts
    const many = Array.from({ length: 12 }, (_x, i) => ({ no: i + 1, tc: (i * 3) + '–' + (i * 3 + 3) + 's', visual: 'Scene ' + (i + 1) + ' differs.', audio: [] }));
    I.setState({ fullScript: many, shoot: {}, sceneFrames: {} }); await wait(300);
    const fr12 = {}; for (let i = 0; i < 12; i++) fr12[i] = { status: 'done', url: '/media/m' + i + '.jpg', sig: 'x', recipe: I.frameRecipe(i, 0), parts: I.frameParts(i, 0) };
    I.setState({ sceneFrames: fr12, shoot: { dop: { text: 'Handheld, shallow focus.' } } }); await wait(300);
    const t0 = performance.now(); for (let n = 0; n < 40; n++) { I.staleSlots(); I.staleFramesPanel(); } const ms = performance.now() - t0;
    check('40 draws of the banner over 12 stale frames take under 1.5 s (' + Math.round(ms) + ' ms)', ms < 1500 && I.staleSlots().length === 12, ms);
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = realFetch; I.showToast = realToast; I.generateFrame = realGen; window.confirm = realConfirm;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
