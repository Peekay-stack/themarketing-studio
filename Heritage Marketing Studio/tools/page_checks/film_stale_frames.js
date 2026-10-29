// film_stale_frames.js -- out-of-date frames: the banner, the reason, "Re-render out-of-date", the two department nudges, the kept shot-plan reason, the scene-length note and the lock wording
// (FILM_LOCALHOST_FINDINGS.md items A1-A4, A6, A7, A8), driven on the REAL page with the network, the model and window.confirm stubbed.
//
// Why: in the owner's first localhost test every frame went "out of date" after the department notes were drafted, with no reason, no banner and no way to re-render only those. A frame now remembers
// a fingerprint of each KIND of thing it was drawn from (words, department notes, Location, look, cast, pack, location photo, brand mode, matched shot), so the page can say what changed.
//
// How to run: start the studio from the worktree, open http://localhost:8001/app, run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 500 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.staleFramesPanel === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.staleFramesPanel === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const real = { fetch: window.fetch, toast: I.showToast, confirm: window.confirm };
  const calls = [], toasts = [], confirms = []; let confirmAnswer = true, n = 0, shotsReply = { shots: [], reason: 'Hold the one crane.' };
  const J = (x) => new Response(JSON.stringify(x), { status: 200, headers: { 'Content-Type': 'application/json' } });
  const tcNew = [{ no: 1, tc: '0–4s' }, { no: 2, tc: '4–10s' }, { no: 3, tc: '10–16s' }];
  window.fetch = async (u, o) => { const url = String(u); calls.push(url);
    if (/\/scene-still/.test(url)) { n++; return J({ image_url: '/media/frame-' + String(n).padStart(6, '0') + 'aa.png', provider: 'stub' }); }
    if (/\/scene-shots/.test(url)) return J(shotsReply);
    if (/\/voice-plan/.test(url)) return J({ lines: [], cast: [], seconds: 16, timecodes: tcNew });
    return J({});
  };
  I.showToast = (m) => { toasts.push(String(m)); };
  window.confirm = (m) => { confirms.push(String(m)); return confirmAnswer; };
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const txt = () => document.body.innerText;
  const btn = t => [...document.querySelectorAll('button')].find(x => x.textContent.trim().indexOf(t) === 0);
  const stillCalls = () => calls.filter(u => /scene-still/.test(u)).length;
  try {
    const rows = [
      { no: 1, tc: '0–5s', visual: 'A boy drains a glass of milk.', camera: 'Close' },
      { no: 2, tc: '5–11s', visual: 'A lab, a woman checks a sample.', shots: [{ id: 'a', job: 'insert', visual: 'Close on the sample.', shot_size: 'close', secs: 2 }] },
      { no: 3, tc: '11–14s', visual: 'A hand sets the pack on a table.' }];
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'scripting', scriptPhase: 'script', scriptStatus: 'approved', videoObjective: 'Brand awareness', videoConcept: { logline: 'A morning.', proposition: 'Milk.', vo: 'Hi.', scenes: [] },
      fullScript: rows, sceneFrames: {}, videoBuilder: null, castRefUrl: '/media/cast-000000aa.png', videoAssetsLoaded: true, shoot: {}, framesBatch: false, staleBusy: '', retimeNote: '', shotsDeclined: {}, videoLookRef: '', frameNote: '' });
    await wait(900);

    // ---- A4: the nudge before the first frames are drawn with every crew note empty
    confirmAnswer = false; confirms.length = 0; calls.length = 0;
    await I.generateAllFrames();
    check('A4 nudge (approved script): empty DoP/lighting/props/wardrobe notes -> a confirm that says to write them first, and Cancel draws nothing', confirms.length === 1 && /still empty/.test(confirms[0]) && /write the notes first, on the Shoot Board/.test(confirms[0]) && stillCalls() === 0 && !I.state.framesBatch, confirms[0]);
    I.setState({ scriptStatus: 'drafted' }); confirms.length = 0;
    await I.generateAllFrames();
    check('A4 nudge (script not approved yet): the message says the notes live on the Shoot Board, which opens on approval', confirms.length === 1 && /approve the script/i.test(confirms[0]) && /Shoot Board/.test(confirms[0]) && stillCalls() === 0, confirms[0]);
    I.setState({ scriptStatus: 'approved' }); confirmAnswer = true; confirms.length = 0;
    await I.generateAllFrames();
    const fr = I.state.sceneFrames;
    check('OK on the nudge draws all 4 frames (3 scenes + 1 extra angle)', confirms.length === 1 && stillCalls() === 4 && ['0', '1', '1.1', '2'].every(k => fr[k] && fr[k].status === 'done'), JSON.stringify(Object.keys(fr)) + ' calls ' + stillCalls());
    check('every drawn frame remembers its fingerprints (recipe + parts: words, dept, loc, look, cast, pack, plate, mode, match)', ['0', '1', '1.1', '2'].every(k => fr[k].recipe && fr[k].parts && ['words', 'dept', 'loc', 'look', 'cast', 'pack', 'plate', 'mode', 'match'].every(p => typeof fr[k].parts[p] === 'string')), JSON.stringify(fr['0']));
    confirms.length = 0; calls.length = 0;
    await I.generateAllFrames();
    check('the nudge does NOT repeat once frames exist (re-rendering all asks nothing)', confirms.length === 0 && stillCalls() === 4, 'confirms ' + confirms.length + ' calls ' + stillCalls());
    await wait(500);
    check('with nothing stale there is no banner', I.staleSlots().length === 0 && !/frames are out of date/.test(txt()) && !btn('↻ Re-render out-of-date'), String(I.staleSlots().length));

    // ---- A4: confirm before drafting a frame-feeding note when frames exist
    confirmAnswer = false; confirms.length = 0;
    await I.draftDept('lighting')();
    check('A4 confirm: drafting the Lighting plan with 4 frames drawn asks first, names the count, and Cancel leaves the note untouched', confirms.length === 1 && /Lighting plan/.test(confirms[0]) && /4 frames already drawn/.test(confirms[0]) && !((I.state.shoot || {}).lighting), confirms[0] + ' ' + JSON.stringify(I.state.shoot));
    confirms.length = 0;
    await I.draftDept('music')();
    check('a department that does not feed the frames (Music) asks nothing', confirms.length === 0, confirms[0]);
    confirmAnswer = true;

    // ---- A1-A3: writing a note after the frames makes them all stale, and the page says why
    I.setState({ shoot: { dop: { status: 'done', text: 'Handheld, low angle, shallow focus.' } } }); await wait(700);
    check('all 4 frames are stale after a DoP note', I.staleSlots().length === 4, String(I.staleSlots().length));
    check('the banner says "4 of 4 frames are out of date" and names the cause with its count', /4 of 4 frames are out of date/.test(txt()) && /a department note \(DoP, lighting, props or wardrobe\) \(4\)/.test(txt()), txt().slice(txt().indexOf('frames are out'), txt().indexOf('frames are out') + 200));
    check('the banner explains that crew notes are part of every frame and offers "Re-render out-of-date (4)"', /part of every frame.s recipe/.test(txt()) && !!btn('↻ Re-render out-of-date (4)'));
    check('the scene card says why, in words', /Out of date — changed since it was drawn: a department note/.test(txt()), '');
    calls.length = 0; toasts.length = 0;
    btn('↻ Re-render out-of-date (4)').click(); await wait(1500);
    check('the button re-renders exactly the 4 stale frames, then nothing is stale and the banner is gone', stillCalls() === 4 && I.staleSlots().length === 0 && !/frames are out of date/.test(txt()) && !I.state.framesBatch && I.state.staleBusy === '', 'calls ' + stillCalls() + ' stale ' + I.staleSlots().length);
    check('and it says so in a toast', toasts.some(t => /Re-rendered 4 frames/.test(t) && /all frames are current/.test(t)), JSON.stringify(toasts));
    const fr2 = I.state.sceneFrames;
    check('re-rendered frames carry the new fingerprints (so a later change is explained correctly)', fr2['0'].parts.dept === fr['0'].parts.dept ? false : (fr2['0'].parts.dept !== undefined), '');

    // ---- only what changed
    I.setState({ fullScript: I.state.fullScript.map((r, i) => i === 2 ? { ...r, visual: 'A hand sets the pack on a wooden table.' } : r) }); await wait(600);
    check('editing one scene’s words flags only that frame, and says "the scene’s words"', I.staleSlots().length === 1 && /1 of 4 frames are out of date/.test(txt()) && /the scene.s words or the extra direction \(1\)/.test(txt()), txt().slice(txt().indexOf('frames are out') - 5, txt().indexOf('frames are out') + 200));
    calls.length = 0; btn('↻ Re-render out-of-date (1)').click(); await wait(900);
    check('one stale frame -> one render (not all of them)', stillCalls() === 1 && I.staleSlots().length === 0, String(stillCalls()));
    I.setState({ fullScript: I.state.fullScript.map((r, i) => i === 1 ? { ...r, visual: 'A lab, a woman checks a blue sample.' } : r) }); await wait(600);
    check('editing a scene that has an extra angle flags its own frame first', I.staleSlots().length === 1 && String(I.staleSlots()[0].key) === '1', JSON.stringify(I.staleSlots().map(x => x.key)));
    calls.length = 0; btn('↻ Re-render out-of-date (1)').click(); await wait(1500);
    check('re-rendering that scene’s own frame pulls its extra angle in (it is matched to it): 2 renders, nothing stale after', stillCalls() === 2 && I.staleSlots().length === 0, 'calls ' + stillCalls() + ' stale ' + JSON.stringify(I.staleSlots().map(x => x.key)));
    I.setState({ videoLookRef: 'warm window light, 35mm grain' }); await wait(600);
    check('changing the look flags all four and names "the look"', I.staleSlots().length === 4 && /the look \(4\)/.test(txt()), txt().slice(txt().indexOf('What changed'), txt().indexOf('What changed') + 160));
    I.setState({ videoStep: 'shots' });
    await wait(700);
    check('...on the Shots step too', /4 of 4 frames are out of date/.test(txt()) && !!btn('↻ Re-render out-of-date (4)'));
    I.setState({ videoStep: 'shootboard' }); await wait(700);
    check('...and on the Shoot Board, with the card reason under the picture', /4 of 4 frames are out of date/.test(txt()) && /Out of date — changed since it was drawn: the look/.test(txt()));
    I.setState({ videoStep: 'scripting' });
    // a frame drawn before fingerprints existed still gets a sensible, honest line
    const old = { ...I.state.sceneFrames['2'] }; delete old.parts;
    I.setState({ sceneFrames: { ...I.state.sceneFrames, '2': old } }); await wait(500);
    check('a frame with no fingerprints says "something it was drawn from has changed" and the banner counts it as an earlier version', /something it was drawn from has changed since/.test(txt()) && /an earlier version of the script or the look \(1\)/.test(txt()), '');
    // lock gate
    I.setState({ castRefUrl: null }); await wait(300); calls.length = 0; toasts.length = 0;
    await I.rerenderStale();
    check('with no locked cast the button refuses the same way Generate all does (no renders)', stillCalls() === 0 && toasts.some(t => /Lock location and cast first/.test(t)), JSON.stringify(toasts));
    // A8 wording
    await wait(400);
    check('A8: the lock hint points to the real button in the Scripting step and no longer to "Live action"', /(Frames need a locked location and cast\. Press|Lock location and cast first: press) .✦ Lock location and cast. in the panel above/.test(txt()) && !/in Live action/.test(txt()), txt().slice(txt().indexOf('locked location and cast') - 40, txt().indexOf('locked location and cast') + 200));
    I.setState({ castRefUrl: '/media/cast-000000aa.png' });

    // ---- A6: the shot planner's reason stays on the card
    shotsReply = { shots: [], reason: 'Hold the one crane.' }; toasts.length = 0;
    await I.breakIntoShots(0)(); await wait(500);
    check('A6: when the planner keeps a scene as one shot, the reason stays on the card', /The shot planner kept this as one shot: Hold the one crane\./.test(txt()), '');
    shotsReply = { shots: [{ id: 'x', job: 'insert', visual: 'Close on the glass.', shot_size: 'close', secs: 2, camera: '', movement_class: '' }], notes: [], master_secs: 3, why: 'A beat of detail.' };
    await I.breakIntoShots(0)(); await wait(500);
    check('A6: a later successful proposal replaces it (no stale decline next to a proposal)', !/The shot planner kept this as one shot/.test(txt()) && /Proposed coverage/i.test(txt()), '');

    // ---- A7: the voice plan re-times the scenes, and now says so
    I.setState({ retimeNote: '', fullScript: rows.map(r => ({ ...r })) }); await wait(300);
    await I.loadVoicePlan(); await wait(700);
    check('A7: loading the voice plan changes 3 scene lengths and a note says which, by how much', /The spoken script set the scene lengths/.test(txt()) && /scene 1: 5 s → 4 s/.test(txt()) && /scene 3: 3 s → 6 s/.test(txt()), I.state.retimeNote);
    check('...and the cards now show the new timings', I.state.fullScript[2].tc === '10–16s', I.state.fullScript[2].tc);
    const dismiss = [...document.querySelectorAll('span')].find(x => x.title === 'Dismiss'); dismiss && dismiss.click(); await wait(400);
    check('the note can be dismissed', !/The spoken script set the scene lengths/.test(txt()) && I.state.retimeNote === '', I.state.retimeNote);
    await I.loadVoicePlan(); await wait(500);
    check('loading the same plan again changes nothing, so there is no new note', I.state.retimeNote === '', I.state.retimeNote);
    I.setState({ retimeNote: 'x' }); I.setState({ fullScript: null }); await wait(500);
    check('the note goes with the script', I.state.retimeNote === '', I.state.retimeNote);
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = real.fetch; I.showToast = real.toast; window.confirm = real.confirm;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0, total: results.length, failures, results: results.map(r => (r.ok ? 'ok   ' : 'FAIL ') + r.name) }, null, 1);
})()
