// builder_state_leaks.js -- the film builder's per-film TRANSIENT state (the Continue ticks `chainOn`, the compare mode `cmpTakes`, the open preview `seqPreview`) must not survive the builder being wiped or
// another film being loaded: they are keyed by place and would act on the NEXT film's shots. Found in the 28 Oct wiring audit (they used to survive all of: a new objective, a brand-mode switch, an image-engine
// change, a cast re-lock); fixed with one choke point in componentDidUpdate plus the film loader. Also pins that ordinary edits do NOT clear them.
//
// How to run: start the studio (preview "studio"), open http://localhost:8000/app (hard reload after any frontend edit), run this whole file with the browser tool's javascript_exec. In-memory state only.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 500 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.chainWanted === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.chainWanted === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const realFetch = window.fetch, realToast = I.showToast;
  window.fetch = async (u) => new Response(JSON.stringify(/video-script/.test(String(u)) ? { video_objective: 'Loaded', video_concept: null, full_script: [{ no: 1, tc: '0–4s', visual: 'L' }], scene_frames: {}, video_builder: null, shoot: {} } : {}), { status: 200, headers: { 'Content-Type': 'application/json' } });
  I.showToast = () => {};
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const plant = () => I.setState({ chainOn: { '1.1': true }, cmpTakes: { key: '0', run: 3 }, seqPreview: { i: 2, done: false, run: 1 }, clipBusy: {}, variantBusy: {},
    fullScript: [{ no: 1, tc: '0–4s', visual: 'A' }], sceneFrames: { '0': { status: 'done', url: '/media/frame-x.jpg' } }, scriptStatus: 'approved', house: { id: 'h1' },
    videoBuilder: { version: 1, frames: {}, frame_chosen: {}, takes: { '0': [{ id: 't', url: '/media/shot-a.mp4', status: 'done', seconds: 4, beats: [], checks: [], est_usd: 0.1 }] }, chosen: { '0': 't' }, trim: {}, budget: { cap_usd: 5, spent_usd: 0 } } });
  const left = () => ({ chainOn: Object.keys(I.state.chainOn || {}).length, cmpTakes: !!I.state.cmpTakes, seqPreview: !!I.state.seqPreview, builder: !!I.state.videoBuilder });
  const clear = (l) => l.chainOn === 0 && !l.cmpTakes && !l.seqPreview;
  try {
    const wipes = {
      'a new objective (pickVideoObjective)': async () => { const f = I.pickVideoObjective('Another objective'); if (typeof f === 'function') await f(); },
      'a brand-mode switch (setProducerBrandMode)': async () => { const f = I.setProducerBrandMode('general'); if (typeof f === 'function') await f(); },
      'an image-engine change (setEngine)': async () => { const f = I.setEngine('image', 'google'); if (typeof f === 'function') await f(); },
      'a cast re-lock pick (pickCastOption)': async () => { const f = I.pickCastOption('/media/x.jpg'); if (typeof f === 'function') await f(); },
    };
    for (const [name, fn] of Object.entries(wipes)) {
      plant(); await wait(200); await fn(); await wait(350);
      const l = left();
      check('after ' + name + ' the builder is wiped AND the Continue ticks, compare mode and open preview are cleared', !l.builder && clear(l), JSON.stringify(l));
    }
    plant(); await wait(200);
    try { await I.loadVideoScript(); } catch (e) {}
    await wait(400);
    const l2 = left();
    check('loading a saved film replaces the builder and clears them too', clear(l2), JSON.stringify(l2));

    // ordinary edits must NOT clear them
    plant(); await wait(200);
    I.setBudgetCap('3'); await wait(250);
    check('an ordinary edit (setting the budget cap) leaves them alone', I.state.chainOn['1.1'] === true && !!I.state.cmpTakes && !!I.state.seqPreview && !!I.state.videoBuilder, JSON.stringify(left()));
    const b = I.state.videoBuilder; I.setState({ videoBuilder: { ...b, trim: { '0': { in: 0.5, out: 3 } } } }); await wait(250);
    check('so does changing a trim (the builder changes but is not wiped)', I.state.chainOn['1.1'] === true && !!I.state.cmpTakes && !!I.state.seqPreview, JSON.stringify(left()));
    I.setState({ videoBuilder: null }); await wait(300);
    check('and wiping the builder directly is enough to clear them (the choke point, not a per-site edit)', clear(left()), JSON.stringify(left()));
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = realFetch; I.showToast = realToast;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
