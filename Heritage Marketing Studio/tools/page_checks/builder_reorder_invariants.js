// builder_reorder_invariants.js -- film builder slices S2b/S2c: reordering shots inside a scene and reordering scenes, driven on the REAL page with the network stubbed.
//
// Why: a shot's frames, frame variants, chosen frame, clip takes, chosen clip and trim are all keyed by its PLACE ("<scene position>" or "<scene position>.<shot place>"), and several things are keyed by a
// scene NUMBER (sound choices, a scene's "match another scene's frame" link, a signed live-action shot). A reorder that renames one and not the others files a clip under the wrong scene. Every frame and
// clip url here carries a tag naming the scene/shot it belongs to, so after a move the test reads each tag back from the place it now sits under. It also checks the refusals (a signed live-action shot,
// a frame or clip being made), the edge no-ops, and that moving a scene there and back is an exact round trip.
//
// How to run: start the studio (preview "studio"), open http://localhost:8000/app, run this whole file with the browser tool's javascript_exec (or paste it in the page console). It stubs window.fetch for
// its own run and changes in-memory state only; reload the page afterwards. Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 400 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.moveScene === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.moveScene === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return { pass: false, failures: ['could not find the app instance'], results: [] };
  const realFetch = window.fetch, realToast = I.showToast;
  let shotsReply = { shots: [] }, toasts = [];
  window.fetch = async (u) => new Response(JSON.stringify(/\/shots\?/.test(String(u)) ? shotsReply : {}), { status: 200, headers: { 'Content-Type': 'application/json' } });
  I.showToast = (m) => { toasts.push(String(m)); };
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  try {
    const ids = { '0': 'A', '1': 'B', '1.1': 'Bx1', '1.2': 'Bx2', '1.3': 'Bx3', '2': 'C' };
    const frames = {}, bf = {}, bfc = {}, bt = {}, bc = {};
    Object.keys(ids).forEach(k => { const id = ids[k];
      frames[k] = { status: 'done', url: '/media/fr-' + id + '.jpg', recipe: 'r' + id }; bf[k] = [{ id: 'f_' + id, url: '/media/fr-' + id + '.jpg' }]; bfc[k] = 'f_' + id;
      bt[k] = [{ id: 'tk_' + id, url: '/media/clip-' + id + '.mp4', status: 'done', seconds: 4, beats: [], tier: 'draft' }]; bc[k] = 'tk_' + id; });
    const rows = [{ no: 1, tc: '0–6s', visual: 'Scene A' },
                  { no: 2, tc: '6–12s', visual: 'Scene B', shots: [{ visual: 'Bx1' }, { visual: 'Bx2' }, { visual: 'Bx3' }] },
                  { no: 3, tc: '12–18s', visual: 'Scene C', match_no: 2 }];
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'shots', fullScript: rows, scriptStatus: 'approved', sceneFrames: frames, castRefUrl: '/media/cast.jpg',
      videoBuilder: { version: 1, frames: bf, frame_chosen: bfc, takes: bt, chosen: bc, trim: { '1.1': { in: 0.5, out: 2 }, '2': { in: 1, out: 3 } }, budget: { cap_usd: 0, spent_usd: 0 } },
      soundPlan: { scenes: { '1': 'on', '2': 'off', '3': 'low' }, sounds: [{ scene: 2, when: 'start', id: 'x' }] },
      videoBeatMap: { scenes: [{ no: 1 }] }, filmReview: { verdicts: [] }, editorNotes: { notes: [] }, voicePlan: { cast: [], lines: [] }, plannedSeconds: 18,
      clipBatch: false, variantBusy: {}, clipBusy: {}, production: { aspect: '16:9', music: '', voice: '', status: 'idle', versions: [] } });
    await wait(600);
    const tag = u => (String(u || '').match(/-(\w+)\.(?:jpg|mp4)/) || [])[1];
    const snap = () => { const s = I.state, b = s.videoBuilder; return JSON.stringify({ rows: s.fullScript, sf: s.sceneFrames, b: { f: b.frames, fc: b.frame_chosen, t: b.takes, c: b.chosen, tr: b.trim }, sp: s.soundPlan }); };
    const places = () => { const s = I.state, b = s.videoBuilder; return Object.keys(s.sceneFrames).sort().map(k => k + '=' + tag(s.sceneFrames[k].url) + '/' + tag(b.takes[k][0].url) + '/' + tag(b.frames[k][0].url) + '/' + b.chosen[k] + '/' + b.frame_chosen[k]).join(' '); };

    // 1. swap two extra shots inside scene B
    I.moveShot(1, 1, 1)(); await wait(200);
    let s = I.state, b = s.videoBuilder;
    check('S2b: the script order of the extras swapped', s.fullScript[1].shots.map(x => x.visual).join(',') === 'Bx2,Bx1,Bx3', s.fullScript[1].shots.map(x => x.visual).join(','));
    check('S2b: every frame, take, chosen id and chosen frame followed its shot; the master and other scenes are untouched',
      places() === '0=A/A/A/tk_A/f_A 1=B/B/B/tk_B/f_B 1.1=Bx2/Bx2/Bx2/tk_Bx2/f_Bx2 1.2=Bx1/Bx1/Bx1/tk_Bx1/f_Bx1 1.3=Bx3/Bx3/Bx3/tk_Bx3/f_Bx3 2=C/C/C/tk_C/f_C', places());
    check('S2b: the trim followed the shot it was set on (Bx1: 1.1 -> 1.2)', !b.trim['1.1'] && b.trim['1.2'] && b.trim['1.2'].out === 2 && b.trim['2'].in === 1, JSON.stringify(b.trim));
    check('S2b: the flow review (positional verdicts) was cleared', s.filmReview === null);
    const afterShot = snap();
    I.moveShot(1, 3, 1)(); await wait(150);
    check('S2b: moving the last extra down is a no-op', snap() === afterShot);
    I.moveShot(1, 1, -1)(); await wait(150);
    check('S2b: moving the first extra up is a no-op (shot 1, the scene\'s own shot, stays first)', snap() === afterShot);

    // 2. swap scene B (position 1) with scene C (position 2)
    await I.moveScene(1, 1)(); await wait(300);
    s = I.state; b = s.videoBuilder;
    check('S2c: rows reordered, numbers stay 1..N in order, and the timecodes were re-laid for the two swapped rows',
      s.fullScript.map(r => r.visual + '#' + r.no + '@' + r.tc).join(' | ') === 'Scene A#1@0–6s | Scene C#2@6–12s | Scene B#3@12–18s', s.fullScript.map(r => r.visual + '#' + r.no + '@' + r.tc).join(' | '));
    check('S2c: every frame, take, chosen id and chosen frame followed its scene (B and its three shots now live under 2 / 2.1 / 2.2 / 2.3)',
      places() === '0=A/A/A/tk_A/f_A 1=C/C/C/tk_C/f_C 2=B/B/B/tk_B/f_B 2.1=Bx2/Bx2/Bx2/tk_Bx2/f_Bx2 2.2=Bx1/Bx1/Bx1/tk_Bx1/f_Bx1 2.3=Bx3/Bx3/Bx3/tk_Bx3/f_Bx3', places());
    check('S2c: trims followed (C: 2 -> 1; B\'s shot: 1.2 -> 2.2)', JSON.stringify(b.trim) === '{"1":{"in":1,"out":3},"2.2":{"in":0.5,"out":2}}', JSON.stringify(b.trim));
    check('S2c: the sound choices followed their scene (B had off, C had low) and the key sound moved with B',
      JSON.stringify(s.soundPlan) === '{"scenes":{"1":"on","2":"low","3":"off"},"sounds":[{"scene":3,"when":"start","id":"x"}]}', JSON.stringify(s.soundPlan));
    check('S2c: C\'s "match this to scene 2" link still points at scene B (now number 3)', s.fullScript[1].match_no === 3, String(s.fullScript[1].match_no));
    check('S2c: what is derived from the order was cleared (director\'s read, flow review, editor\'s notes, voice plan, planned seconds)',
      s.videoBeatMap === null && s.filmReview === null && s.editorNotes === null && s.voicePlan === null && s.plannedSeconds === 0);
    check('S2c: a note told the person what moved and what to re-run', toasts.some(t => /swapped/.test(t) && /run them again/.test(t)), toasts.join(' | '));

    // 3. refusals
    shotsReply = { shots: [{ signed: true, scene: 1 }] }; let before = snap(); await I.moveScene(0, 1)(); await wait(200);
    check('S2c: a signed live-action shot for either scene REFUSES the move, with the reason', snap() === before && /signed live-action footage/.test(toasts[toasts.length - 1] || ''), toasts[toasts.length - 1]);
    shotsReply = { shots: [] };
    I.setState(st => ({ sceneFrames: { ...st.sceneFrames, '1': { ...st.sceneFrames['1'], status: 'rendering' } } })); await wait(150);
    before = snap(); await I.moveScene(1, 1)(); await wait(200);
    check('S2c: a frame being made in either scene REFUSES the move (it would be filed under the wrong scene)', snap() === before && /still being made/.test(toasts[toasts.length - 1] || ''), toasts[toasts.length - 1]);
    I.moveShot(1, 1, 1)(); await wait(150);
    I.setState(st => ({ sceneFrames: { ...st.sceneFrames, '1': { ...st.sceneFrames['1'], status: 'done' } }, clipBusy: { '2.1': 'tk_x' } })); await wait(150);
    before = snap(); I.moveShot(2, 1, 1)(); await wait(150);
    check('S2b: a clip being made for either shot REFUSES the shot move', snap() === before);
    I.setState({ clipBusy: {} }); await wait(100);

    // 4. round trip: B comes back, everything is as it was after step 1 (sound plan scene keys come back too)
    await I.moveScene(2, -1)(); await wait(300);
    const back = JSON.parse(snap()), ref = JSON.parse(afterShot);
    check('S2c: moving the scene back is an EXACT round trip (rows, frames, builder maps, sound plan)',
      JSON.stringify(back.rows) === JSON.stringify(ref.rows) && JSON.stringify(back.sf) === JSON.stringify(ref.sf) && JSON.stringify(back.b) === JSON.stringify(ref.b) && JSON.stringify(back.sp) === JSON.stringify(ref.sp));
    before = snap(); await I.moveScene(0, -1)(); await I.moveScene(2, 1)(); await wait(150);
    check('S2c: moving the first scene up or the last scene down is a no-op', snap() === before);
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = realFetch; I.showToast = realToast;
  }
  const failures = results.filter(r => !r.ok);
  return { pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) };
})()
