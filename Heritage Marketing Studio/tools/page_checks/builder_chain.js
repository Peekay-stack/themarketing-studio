// builder_chain.js -- film builder slice S4 (chain continuity) on the Shots step, driven on the REAL page with the network and the render job stubbed (the server side is tested in tools/test_builder_s4.py).
//
// Why: "Continue" must only be offered where it makes sense (the previous shot of the SAME scene with a chosen clip, or the parts of a long shot), must send exactly the right fields (chain_from = the previous
// shot's chosen clip; chain_beats for a shot over 8 s), must be OFF by default (a normal take is made from its approved frame, as before), must be remembered on the take, must keep a re-roll in the same mode, and a
// chained take must not be called "older frame" just because its start picture is not the storyboard frame.
//
// How to run: start the studio (preview "studio"), open http://localhost:8000/app, run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 400 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.chainWanted === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.chainWanted === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const realFetch = window.fetch, realToast = I.showToast, realJob = I.renderViaJob;
  const bodies = [], toasts = []; let n = 0;
  window.fetch = async (u) => new Response(JSON.stringify(/\/shots\?/.test(String(u)) ? { shots: [] } : { checks: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
  I.showToast = (m) => { toasts.push(String(m)); };
  I.renderViaJob = async (body) => { bodies.push(body); n++; const chained = !!(body.chain_from || body.chain_beats);
    return { ok: true, status: 200, data: { ok: true, mode: chained ? 'chain' : 'frame', clips: [{ ok: true, url: '/media/new' + n + '.mp4', seconds: 4, frame_url: body.chain_from ? '/media/chain-' + n + '.jpg' : '' }], errors: [] } }; };
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const mk = (id, url, secs, o) => ({ id, url, beats: [], tier: 'draft', engine: 'omni', seconds: secs, mode: 'frame', frame: '/media/fr-' + id + '.jpg', chain_from: '', status: 'done', error: '', checks: [], check_accepted: false, est_usd: 0.1, ...(o || {}) });
  const txt = () => document.body.innerText;
  const state = () => I.state.videoBuilder;
  try {
    // A (4 s) | B (6 s, master 4 s + one 2 s extra) | C (12 s: a long shot)
    const rows = [{ no: 1, tc: '0–4s', visual: 'A' }, { no: 2, tc: '4–10s', visual: 'B', shots: [{ visual: 'Bx1', secs: 2 }] }, { no: 3, tc: '10–22s', visual: 'C' }];
    const fr = { '0': 'A', '1': 'B', '1.1': 'Bx1', '2': 'C' }, frames = {};
    Object.keys(fr).forEach(k => frames[k] = { status: 'done', url: '/media/fr-' + (k === '0' ? 'ta' : k === '1' ? 'tb' : k === '2' ? 'tc' : 'tx') + '.jpg' });
    const vb = { version: 1, frames: {}, frame_chosen: {}, takes: { '0': [mk('ta', '/media/a.mp4', 4)], '1': [mk('tb', '/media/b.mp4', 4)] }, chosen: { '0': 'ta', '1': 'tb' }, trim: {}, budget: { cap_usd: 0, spent_usd: 0 } };
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'shots', fullScript: rows, scriptStatus: 'approved', sceneFrames: frames, castRefUrl: '/media/c.jpg', videoBuilder: vb, takeChecking: {}, clipBusy: {}, clipBatch: false, chainOn: {} });
    await wait(700);

    // eligibility
    check('the first shot of a scene has nothing to continue from (no previous shot in its scene), and is not long', !I.chainEligible(0, 0) && I.chainSource(0, 0) === '');
    check('a scene\'s master shot does not continue from the PREVIOUS SCENE (a new scene is a new place)', !I.chainEligible(1, 0) && I.chainSource(1, 0) === '');
    check('an extra shot continues from the previous shot of the SAME scene once that has a chosen clip', I.chainEligible(1, 1) && I.chainSource(1, 1) === '/media/b.mp4');
    check('a shot over 8 s can continue between its own parts (no previous clip needed)', I.chainBeatsPossible(2, 0) && I.chainEligible(2, 0) && I.chainSource(2, 0) === '');
    const b0 = state(); I.setState({ videoBuilder: { ...b0, chosen: { '0': 'ta' } } }); await wait(200);
    check('with no chosen clip on the previous shot there is nothing to continue from', I.chainSource(1, 1) === '' && !I.chainEligible(1, 1));
    I.setState({ videoBuilder: { ...b0, takes: { ...b0.takes, '1': [mk('tb', '/media/b1.mp4', 8, { beats: [{ url: '/media/b1.mp4', seconds: 5 }, { url: '/media/b2.mp4', seconds: 3 }] })] } } }); await wait(200);
    check('after a multi-part clip it continues from its LAST part', I.chainSource(1, 1) === '/media/b2.mp4');
    I.setState({ videoBuilder: b0 }); await wait(300);

    // the control
    check('the control is shown with the right words on each shot', /Continue from the previous shot/.test(txt()) && /Continue between this shot’s parts/.test(txt()));
    check('it is OFF by default', I.chainWanted(1, 1) === false && [...document.querySelectorAll('input[type=checkbox]')].filter(x => x.parentElement && /Continue/.test(x.parentElement.textContent)).every(x => !x.checked));

    // an ordinary take: exactly as before
    await I.generateClipTake(1, 1)(); await wait(500);
    check('an ordinary take sends no chain fields and is recorded as mode frame', bodies.length === 1 && bodies[0].only_shot === '1.1' && bodies[0].chain_from === undefined && bodies[0].chain_beats === undefined && state().takes['1.1'][0].mode === 'frame' && state().takes['1.1'][0].chain_from === '', JSON.stringify(bodies[0]));

    // switch it on by clicking the real checkbox
    const box = () => [...document.querySelectorAll('input[type=checkbox]')].filter(x => x.parentElement && /Continue from the previous shot/.test(x.parentElement.textContent))[0];
    box().click(); await wait(300);
    check('clicking the box switches Continue on for that shot only', I.chainWanted(1, 1) === true && I.state.chainOn['1.1'] === true && I.chainWanted(2, 0) === false);
    bodies.length = 0; await I.generateClipTake(1, 1)(); await wait(500);
    const t = state().takes['1.1'][state().takes['1.1'].length - 1];
    check('a chained take sends chain_from = the previous shot\'s chosen clip (and no chain_beats for a short shot)', bodies.length === 1 && bodies[0].chain_from === '/media/b.mp4' && bodies[0].chain_beats === undefined, JSON.stringify(bodies[0]));
    check('the take records how it was made: mode chain, the clip it continued from, and the extracted start picture as its frame', t.mode === 'chain' && t.chain_from === '/media/b.mp4' && /^\/media\/chain-/.test(t.frame), JSON.stringify(t));
    check('the take shows a "chained" chip', /chained/i.test(txt()));
    check('it is NOT called "older frame" (its start picture is the extracted frame, not the storyboard frame)', !/older frame/i.test(txt()) && !/older clip/i.test(txt()));

    // a re-roll keeps the mode of the latest take unless the person switches it
    I.setState({ chainOn: {} }); await wait(200);
    check('with no explicit choice a re-roll keeps the way the latest take was made (chained)', I.chainWanted(1, 1) === true);
    I.setChain(1, 1, false); await wait(200); bodies.length = 0; await I.generateClipTake(1, 1)(); await wait(500);
    check('switching it off makes the next take an ordinary one again', bodies[0].chain_from === undefined && state().takes['1.1'][state().takes['1.1'].length - 1].mode === 'frame');

    // a long shot sends chain_beats
    I.setChain(2, 0, true); await wait(200); bodies.length = 0; await I.generateClipTake(2, 0)(); await wait(500);
    check('a long shot with Continue on sends chain_beats (and no chain_from: nothing precedes it in its scene)', bodies.length === 1 && bodies[0].chain_beats === true && bodies[0].chain_from === undefined && state().takes['2'][0].mode === 'chain' && state().takes['2'][0].chain_from === '', JSON.stringify(bodies[0]));

    // staleness: the previous clip changed
    I.setChain(1, 1, true); await wait(150); await I.generateClipTake(1, 1)(); await wait(500);
    const chainTake = state().takes['1.1'][state().takes['1.1'].length - 1];
    I.chooseClipTake(1, 1, chainTake.id)(); await wait(300);          // the assemble strip only judges CHOSEN takes
    check('a chained take is current while the previous shot\'s chosen clip is the one it continued from', I.clipIsOlder(1, 1, chainTake, I.state.sceneFrames['1.1']) === false);
    const b1 = state(); I.setState({ videoBuilder: { ...b1, takes: { ...b1.takes, '1': [...b1.takes['1'], mk('tb2', '/media/b-new.mp4', 4)] }, chosen: { ...b1.chosen, '1': 'tb2' } } }); await wait(400);
    check('when the previous shot\'s chosen clip changes, the chained take is "older clip" (and the assemble strip warns)', I.clipIsOlder(1, 1, chainTake, I.state.sceneFrames['1.1']) === true && /older clip/i.test(txt()) && I.assembleStatus().older.some(x => x.key === '1.1'), txt().slice(0, 0));
    const plain = mk('tp', '/media/p.mp4', 4, { frame: '/media/fr-old.jpg' });
    check('an ordinary take is still "older frame" when its storyboard frame has changed', I.clipIsOlder(0, 0, plain, { url: '/media/fr-new.jpg' }) === true && I.clipIsOlder(0, 0, mk('tq', '/media/q.mp4', 4, { frame: '/media/fr-new.jpg' }), { url: '/media/fr-new.jpg' }) === false);

    // reorder clears the per-place switches
    I.setState({ chainOn: { '1.1': true, '2': true } }); await wait(150);
    await I.moveScene(0, 1)(); await wait(400);
    check('moving a scene clears the Continue switches (they are keyed by place)', Object.keys(I.state.chainOn).length === 0, JSON.stringify(I.state.chainOn));
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = realFetch; I.showToast = realToast; I.renderViaJob = realJob;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
