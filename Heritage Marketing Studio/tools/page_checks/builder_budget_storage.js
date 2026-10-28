// builder_budget_storage.js -- film builder slice S7 (budget cap, batch + compare, retention) on the Shots step, driven on the REAL page with the network, the render job and window.confirm stubbed (the
// server side of retention is tested in tools/test_mediapurge.py).
//
// Why: spend must have a limit the person sets (a batch STOPS at it, a single clip asks first), a delete cannot be undone so the page must only ever ASK for takes nobody chose, must keep everything a
// produced film or the storyboard still shows, must ask first with the size, and must drop from the page only what the server really removed.
//
// How to run: start the studio (preview "studio"), open http://localhost:8000/app, run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 400 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.purgeCandidates === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.purgeCandidates === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const realFetch = window.fetch, realToast = I.showToast, realJob = I.renderViaJob, realConfirm = window.confirm;
  const jobs = [], toasts = [], confirms = [], purgeCalls = []; let n = 0, answer = true, serverKeep = new Set(), usage = { files: 665, bytes: 648e6, by_kind: { frame: { files: 418, bytes: 404e6 }, still: { files: 148, bytes: 141e6 }, kv: { files: 31, bytes: 122e6 } }, disk_free_bytes: 155e9 };
  window.confirm = (m) => { confirms.push(String(m)); return answer; };
  I.showToast = (m) => { toasts.push(String(m)); };
  I.renderViaJob = async (body) => { jobs.push(body); n++; return { ok: true, status: 200, data: { ok: true, mode: 'frame', clips: [{ ok: true, url: '/media/shot-new' + n + '.mp4', seconds: 4, frame_url: '' }], errors: [] } }; };
  window.fetch = async (u, o) => {
    const url = String(u), body = o && o.body ? JSON.parse(o.body) : {}, J = (x, s) => new Response(JSON.stringify(x), { status: s || 200, headers: { 'Content-Type': 'application/json' } });
    if (/\/media-usage/.test(url)) return J(usage);
    if (/\/media-purge/.test(url)) { purgeCalls.push(body);
      const del = [], skip = []; let freed = 0;
      body.urls.forEach(x => { if (serverKeep.has(x)) skip.push({ url: x, reason: 'in use by a film (a chosen frame or clip, a current storyboard frame, or the cast reference)' }); else { del.push({ url: x, bytes: 1000000 }); freed += 1000000; } });
      return J({ dry_run: body.dry_run !== false, deleted: del, skipped: skip, freed_bytes: freed }); }
    return J({ checks: [] });
  };
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const mk = (id, url, secs, o) => ({ id, url, beats: [], tier: 'draft', engine: 'omni', seconds: secs, mode: 'frame', frame: '/media/frame-' + id + '.jpg', chain_from: '', status: 'done', error: '', checks: [], check_accepted: false, est_usd: 0.14, ...(o || {}) });
  const txt = () => document.body.innerText;
  const bld = () => I.state.videoBuilder;
  const rows = [{ no: 1, tc: '0–4s', visual: 'A' }, { no: 2, tc: '4–8s', visual: 'B' }, { no: 3, tc: '8–12s', visual: 'C' }];
  const frames = () => { const f = {}; rows.forEach((r, i) => f[i] = { status: 'done', url: '/media/frame-cur' + i + '.jpg' }); return f; };
  const base = (extra) => I.setState({ screen: 'video', vTab: 'film', videoStep: 'shots', fullScript: rows, scriptStatus: 'approved', sceneFrames: frames(), castRefUrl: '/media/cast-1.jpg', takeChecking: {}, clipBusy: {}, clipBatch: false, chainOn: {}, cmpTakes: null, storage: null,
    production: { aspect: '16:9', music: '', voice: '', status: 'idle', versions: [] }, videoBuilder: { version: 1, frames: {}, frame_chosen: {}, takes: {}, chosen: {}, trim: {}, budget: { cap_usd: 0, spent_usd: 0 }, ...(extra || {}) } });
  try {
    // ---------------- BUDGET ----------------
    base(); await wait(600);
    const one = I.clipEstimate(0, 0, 'draft');
    check('a Draft clip has a measured estimate (the 3 s floor and the rate)', typeof one === 'number' && one > 0.1 && one < 0.2, String(one));
    check('with no cap nothing is limited', I.budgetCap() === 0 && !I.capWouldExceed(5));
    I.setBudgetCap('0.30'); await wait(250);
    check('the cap is saved on the film (budget.cap_usd) and shown in the header input', bld().budget.cap_usd === 0.3 && [...document.querySelectorAll('input[type=number]')].some(x => x.placeholder === 'none' && x.value === '0.3'), JSON.stringify(bld().budget));
    check('junk or negative input is cleaned to a number (0 = no cap)', (I.setBudgetCap('abc'), true) && bld().budget.cap_usd === 0 && (I.setBudgetCap('-5'), true) && bld().budget.cap_usd === 0);
    I.setBudgetCap('0.30'); await wait(200);

    // a batch stops at the cap
    jobs.length = 0; toasts.length = 0; confirms.length = 0; answer = true;
    await I.generateMissingClips(); await wait(900);
    check('"Generate all missing" mentions the cap in its confirm', confirms.length === 1 && /Your cap is \$0\.30/.test(confirms[0]), confirms[0]);
    check('the batch made 2 clips (about $0.27) and STOPPED before the third, which would have gone past $0.30', jobs.length === 2 && Object.keys(bld().takes).length === 2 && /Stopped at your \$0\.30 cap/.test(toasts.join(' ')), JSON.stringify({ jobs: jobs.length, toasts }));
    check('spent counts every finished take (about $0.27) and the header says how much of the cap is used', Math.abs(I.clipSpent() - 0.272) < 0.001 && /9\d% used/.test(txt()), txt().match(/\d+% used[^\n]*/));

    // a single clip asks before going over
    jobs.length = 0; confirms.length = 0; answer = false;
    await I.generateClipTake(2, 0)(); await wait(400);
    check('a single clip that would go over the cap ASKS first, and declining makes nothing', confirms.length === 1 && /over your \$0\.30 cap/.test(confirms[0]) && jobs.length === 0 && !bld().takes['2'], confirms[0]);
    answer = true; await I.generateClipTake(2, 0)(); await wait(500);
    check('accepting makes it (one clip may go past the cap if you say so)', jobs.length === 1 && bld().takes['2'].length === 1 && I.clipSpent() > 0.3, String(I.clipSpent()));
    check('the header now says over', /over/i.test(txt().match(/\d+% used[^\n]*/)[0]), txt().match(/\d+% used[^\n]*/));

    // x3 batch for one shot, with a cap
    base(); await wait(400); I.setBudgetCap('0.30');
    const b0 = bld(); I.setState({ videoBuilder: { ...b0, takes: { '0': [mk('t0', '/media/shot-t0.mp4', 4)] }, chosen: { '0': 't0' } } }); await wait(300);
    jobs.length = 0; confirms.length = 0; toasts.length = 0; answer = true;
    await I.generateClipTakes(0, 0, 3)(); await wait(900);
    check('x3 asks with the total and the cap, then stops at the cap (0.14 spent + 1 more = 0.28; a second would be 0.41)', confirms.length === 1 && /about \$0\.41/.test(confirms[0]) && /Your cap is/.test(confirms[0]) && jobs.length === 1 && /Stopped at your/.test(toasts.join(' ')), JSON.stringify({ c: confirms[0], jobs: jobs.length, t: toasts }));
    base(); await wait(400);
    const b1 = bld(); I.setState({ videoBuilder: { ...b1, takes: { '0': [mk('t0', '/media/shot-t0.mp4', 4)] }, chosen: { '0': 't0' } } }); await wait(300);
    jobs.length = 0; confirms.length = 0; answer = true; await I.generateClipTakes(0, 0, 3)(); await wait(1200);
    check('with no cap x3 makes three more takes', jobs.length === 3 && bld().takes['0'].length === 4 && bld().chosen['0'] === 't0', JSON.stringify({ jobs: jobs.length, takes: bld().takes['0'].length }));
    answer = false; jobs.length = 0; await I.generateClipTakes(0, 0, 3)(); await wait(300);
    check('declining the x3 confirm makes nothing', jobs.length === 0);
    answer = true;

    // promote stops at the cap
    base(); await wait(400);
    const b2 = bld(); const dr = (id, k) => mk(id, '/media/shot-' + id + '.mp4', 4, { est_usd: 0 });
    I.setState({ videoBuilder: { ...b2, takes: { '0': [dr('p0')], '1': [dr('p1')], '2': [dr('p2')] }, chosen: { '0': 'p0', '1': 'p1', '2': 'p2' }, budget: { cap_usd: 0.5, spent_usd: 0 } } }); await wait(300);
    jobs.length = 0; toasts.length = 0; answer = true; await I.promoteToFinal(); await wait(1200);
    check('Promote to Final stops at the cap too (Final is about $0.40 a clip: one fits under $0.50, the second would not)', jobs.length === 1 && /promoted to Final\. Stopped at your \$0\.50 cap/.test(toasts.join(' ')), JSON.stringify({ jobs: jobs.length, toasts }));

    // ---------------- COMPARE ----------------
    base(); await wait(400);
    const b3 = bld(); I.setState({ videoBuilder: { ...b3, takes: { '0': [mk('c1', '/media/shot-c1.mp4', 4), mk('c2', '/media/shot-c2.mp4', 4)], '1': [mk('d1', '/media/shot-d1.mp4', 4)] }, chosen: { '0': 'c1', '1': 'd1' } } }); await wait(400);
    const cmpBtns = () => [...document.querySelectorAll('button')].filter(x => /Compare takes|Stop compare/.test(x.textContent));
    check('Compare is offered only for a shot with two or more finished takes', cmpBtns().length === 1);
    cmpBtns()[0].click(); await wait(400);
    const vids = [...document.querySelectorAll('video')].filter(v => /shot-c[12]\.mp4/.test(v.getAttribute('src') || ''));
    check('Compare plays every take of that shot together, muted and looping, and the other shots are untouched', vids.length >= 2 && vids.every(v => v.loop && v.muted && v.autoplay) && ![...document.querySelectorAll('video')].some(v => /shot-d1/.test(v.getAttribute('src') || '') && v.loop), vids.map(v => [v.loop, v.muted, v.autoplay].join()).join(' | '));
    check('and the button becomes Stop compare', cmpBtns()[0].textContent === 'Stop compare');
    cmpBtns()[0].click(); await wait(300);
    check('Stop compare returns the cards to normal', I.state.cmpTakes === null && ![...document.querySelectorAll('video')].some(v => v.loop));

    // ---------------- STORAGE / RETENTION ----------------
    base(); await wait(400);
    const sb = bld();
    I.setState({ videoBuilder: { ...sb,
      frames: { '0': [{ id: 'f1', url: '/media/frame-f1.jpg' }, { id: 'f2', url: '/media/frame-f2.jpg' }, { id: 'f3', url: '/media/frame-f3.jpg' }, { id: '__current', url: '/media/frame-cur0.jpg', virtual: true }], '1': [{ id: 'g1', url: '/media/frame-g1.jpg' }] }, frame_chosen: { '0': 'f1', '1': 'g1' },
      takes: { '0': [mk('k1', '/media/shot-k1.mp4', 4), mk('k2', '/media/shot-k2.mp4', 4), mk('k3', '/media/shot-k3a.mp4', 8, { beats: [{ url: '/media/shot-k3a.mp4', seconds: 4 }, { url: '/media/shot-k3b.mp4', seconds: 4 }] }), mk('kx', '/media/shot-kx.mp4', 4, { status: 'error' })] }, chosen: { '0': 'k1' } },
      production: { aspect: '16:9', music: '', voice: '', status: 'done', versions: [{ v: 1, url: '/media/film-1.mp4', shot_clips: [{ no: 1, url: '/media/shot-k2.mp4' }] }] } });
    await wait(400);
    const c = I.purgeCandidates();
    check('candidates are the UNCHOSEN frame variants and clip takes only (not chosen, not the virtual current one, not a failed take)', c.frames === 2 && c.clips === 1 && c.urls.length === 4 && !c.urls.includes('/media/frame-f1.jpg') && !c.urls.includes('/media/frame-cur0.jpg') && !c.urls.includes('/media/shot-k1.mp4') && !c.urls.includes('/media/shot-kx.mp4'), JSON.stringify(c));
    check('a clip a PRODUCED VERSION still uses (k2) is never a candidate even though it is not chosen', !c.urls.includes('/media/shot-k2.mp4'));
    check('a multi-part unchosen take contributes all its parts', c.urls.includes('/media/shot-k3a.mp4') && c.urls.includes('/media/shot-k3b.mp4') && c.clips === 1);
    check('the storage strip says what can be removed and that storage is not checked yet', /Not checked yet/.test(txt()) && /2 unchosen frame variants and 1 unchosen clip take can be removed/.test(txt()), (txt().match(/This film:[^\n]*/) || [''])[0]);
    await I.checkStorage(); await wait(300);
    check('Check storage shows the media folder size, the biggest kinds and free disk', /Media folder 648 MB in 665 files \(frame 404 MB, still 141 MB, kv 122 MB\) · disk free 155\.0 GB/.test(txt()), (txt().match(/Media folder[^\n]*/) || [''])[0]);

    // decline: nothing is removed
    purgeCalls.length = 0; confirms.length = 0; answer = false;
    await I.purgeUnchosen(); await wait(400);
    check('the purge first MEASURES (dry run), asks with the size, and declining removes nothing', purgeCalls.length === 1 && purgeCalls[0].dry_run === true && /Remove 4 files \(4\.0 MB\)/.test(confirms[0]) && /cannot be undone/.test(confirms[0]) && /Made keeps its entry|keeps its entry/.test(confirms[0]) && Object.keys(bld().frames).length === 2 && bld().frames['0'].length === 4, JSON.stringify({ calls: purgeCalls.map(x => x.dry_run), c: confirms[0] }));
    check('the request names only the candidates, never a chosen or used file', purgeCalls[0].urls.length === 4 && purgeCalls[0].urls.every(u => /frame-f2|frame-f3|shot-k3a|shot-k3b/.test(u)), JSON.stringify(purgeCalls[0].urls));

    // accept: the server keeps one of them (in use elsewhere): the page drops only what was removed
    purgeCalls.length = 0; confirms.length = 0; answer = true; serverKeep = new Set(['/media/frame-f3.jpg']); toasts.length = 0;
    await I.purgeUnchosen(); await wait(600);
    check('accepting sends the real delete after the dry run', purgeCalls.length === 2 && purgeCalls[0].dry_run === true && purgeCalls[1].dry_run === false);
    const fr0 = bld().frames['0'].map(x => x.id), tk0 = bld().takes['0'].map(x => x.id);
    check('the page drops only what the server REALLY removed: f2 and the multi-part take k3 go; f3 (kept by the server) stays; chosen, virtual, produced-version and failed takes stay',
      fr0.join() === 'f1,f3,__current' && tk0.join() === 'k1,k2,kx' && bld().chosen['0'] === 'k1' && bld().frame_chosen['0'] === 'f1', JSON.stringify({ fr0, tk0 }));
    check('the person is told how much was freed and that one file was kept', /Removed 3 files, freeing 3\.0 MB\./.test(toasts.join(' ')) && /1 kept \(still in use\)/.test(toasts.join(' ')), toasts.join(' | '));

    // nothing to do
    base(); await wait(300); purgeCalls.length = 0; await I.purgeUnchosen(); await wait(200);
    check('with nothing unchosen the purge does not even call the server', purgeCalls.length === 0 && /nothing unchosen to remove/.test(txt()));
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = realFetch; window.confirm = realConfirm; I.showToast = realToast; I.renderViaJob = realJob;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
