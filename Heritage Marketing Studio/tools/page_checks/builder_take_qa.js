// builder_take_qa.js -- film builder slice S5: take QC on the Shots step, driven on the REAL page with the network stubbed (the routes themselves are tested in tools/test_takeqa.py).
//
// Why: the checks must run on their own when a clip finishes, send the right things (the clip, what was ordered, the PREVIOUS shot's chosen clip for the repeat check), merge into the take without losing an
// earlier model look, show as chips and notes, be dismissible, and never block anything (Use, assemble and Promote stay available).
//
// How to run: start the studio (preview "studio"), open http://localhost:8000/app, run this whole file with the browser tool's javascript_exec. It stubs window.fetch and the instance's renderViaJob for its
// own run; in-memory state only; reload afterwards. Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 400 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.checkClipTake === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.checkClipTake === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const realFetch = window.fetch, realToast = I.showToast, realJob = I.renderViaJob;
  const calls = [], toasts = []; let qaFail = false, lookReply = null;
  const ok = id => ({ id, label: id, verdict: 'ok', note: '' });
  window.fetch = async (u, o) => {
    const url = String(u), body = o && o.body ? JSON.parse(o.body) : {};
    if (/\/take-check/.test(url)) {
      calls.push(['check', body]);
      if (qaFail) return new Response(JSON.stringify({ detail: 'No video tool (ffmpeg) is available on this server.' }), { status: 503, headers: { 'Content-Type': 'application/json' } });
      const flagged = /b\.mp4|p2\.mp4/.test(body.url);
      return new Response(JSON.stringify({ checks: [ok('readable'), { id: 'still', label: 'Barely moves', verdict: flagged ? 'check' : 'ok', note: flagged ? 'The picture barely moves: the frames looked at are almost identical.' : '' }, ok('black'), ok('short')], measured: {} }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }
    if (/\/take-look/.test(url)) { calls.push(['look', body]); return new Response(JSON.stringify(lookReply), { status: 200, headers: { 'Content-Type': 'application/json' } }); }
    return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
  };
  I.showToast = (m) => { toasts.push(String(m)); };
  const results = [], check = (name, okk, extra) => results.push({ name, ok: !!okk, extra: okk ? undefined : extra });
  const mk = (id, url, secs, beats) => ({ id, url, beats: beats || [], tier: 'draft', engine: 'omni', seconds: secs, mode: 'frame', frame: '/media/f0.jpg', status: 'done', error: '', checks: [], check_accepted: false, est_usd: 0.1 });
  const take = (key, id) => I.state.videoBuilder.takes[key].find(x => x.id === id);
  try {
    const rows = [{ no: 1, tc: '0–4s', visual: 'A' }, { no: 2, tc: '4–9s', visual: 'B' }, { no: 3, tc: '9–13s', visual: 'C' }];
    const fr = {}; rows.forEach((r, i) => fr[i] = { status: 'done', url: '/media/f' + i + '.jpg' });
    const vb = { version: 1, frames: {}, frame_chosen: {}, takes: { '0': [mk('ta', '/media/a.mp4', 4)], '1': [mk('tb', '/media/b.mp4', 5)], '2': [mk('tc', '/media/c.mp4', 5)] }, chosen: { '0': 'ta', '1': 'tb', '2': 'tc' }, trim: {}, budget: { cap_usd: 0, spent_usd: 0 } };
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'shots', fullScript: rows, scriptStatus: 'approved', sceneFrames: fr, castRefUrl: '/media/c.jpg', videoCharacters: 'A boy of nine.', videoBuilder: vb, takeChecking: {}, clipBusy: {}, clipBatch: false });
    await wait(700);
    const txt = () => document.body.innerText;

    // 1. Check sends the clip, what was ordered and the PREVIOUS shot's chosen clip
    await I.checkClipTake(1, 0, 'tb')(); await wait(300);
    check('Check sends the clip, the ordered seconds and the previous shot\'s chosen clip (for the repeat check)', calls.length === 1 && calls[0][1].url === '/media/b.mp4' && calls[0][1].seconds === 5 && calls[0][1].prev_url === '/media/a.mp4', JSON.stringify(calls));
    check('the first shot has no previous shot, so no prev_url is sent', (calls.length = 0, true) && (await I.checkClipTake(0, 0, 'ta')(), await wait(300), calls[0][1].prev_url === undefined), JSON.stringify(calls));
    let t = take('1', 'tb');
    check('the result is stored on the take: all four checks, the flagged one is "Barely moves"', t.checks.length === 4 && t.checks.filter(c => c.verdict === 'check').map(c => c.id).join() === 'still', JSON.stringify(t.checks));
    check('a flagged take shows a "! 1" chip, its note, and Check became Re-check', /! 1/.test(txt()) && /Barely moves: The picture barely moves/.test(txt()) && [...document.querySelectorAll('button')].some(b => b.textContent === 'Re-check'));
    check('a clean take shows "✓ checked" and no note', /✓ checked/i.test(txt()) && take('0', 'ta').checks.every(c => c.verdict === 'ok'));
    check('the assemble strip lists the flagged chosen clip as advisory', /Checks on chosen clips \(advisory, you decide\): scene 2, shot 1 — Barely moves/.test(txt()), (txt().match(/Checks on chosen[^\n]*/) || [''])[0]);
    check('NOTHING IS BLOCKED: the film is still assemblable and Assemble film is enabled', I.assembleStatus().complete === true && ![...document.querySelectorAll('button')].find(b => b.textContent === 'Assemble film').disabled);

    // 2. Accept dismisses; re-check resets
    [...document.querySelectorAll('button')].find(b => b.textContent === 'Accept').click(); await wait(300);
    check('Accept dismisses the notes on that take (chip and strip line go), the checks themselves are kept', take('1', 'tb').check_accepted === true && !/Barely moves: The picture/.test(txt()) && !/Checks on chosen clips/.test(txt()) && take('1', 'tb').checks.length === 4);
    await I.checkClipTake(1, 0, 'tb')(); await wait(300);
    check('a re-check puts the notes back (accepted resets)', take('1', 'tb').check_accepted === false && /Checks on chosen clips/.test(txt()));

    // 3. the model look: stored beside the deterministic checks and kept through a re-check
    calls.length = 0; lookReply = { verdict: 'check', checks: [{ id: 'anatomy', label: 'Anatomy', verdict: 'check', note: 'The boy has three arms in the middle of the clip.' }], seen: 'a boy' };
    await I.lookClipTake(1, 0, 'tb')(); await wait(300);
    check('Look sends the clip, the shot\'s own words and the film\'s cast note', calls.length === 1 && calls[0][0] === 'look' && calls[0][1].url === '/media/b.mp4' && calls[0][1].description === 'B' && calls[0][1].cast === 'A boy of nine.', JSON.stringify(calls));
    t = take('1', 'tb');
    check('the model\'s issue is added to the take\'s checks and shows as a note', t.checks.some(c => c.id === 'anatomy') && t.checks.length === 5 && /three arms/.test(txt()));
    await I.checkClipTake(1, 0, 'tb')(); await wait(300);
    check('a later deterministic re-check KEEPS the model look (it is not wiped)', take('1', 'tb').checks.some(c => c.id === 'anatomy') && take('1', 'tb').checks.length === 5);
    lookReply = { verdict: 'ok', checks: [], seen: 'A boy at a table.' };
    await I.lookClipTake(1, 0, 'tb')(); await wait(300);
    check('a clean look replaces the earlier issue with an ok "look" entry', !take('1', 'tb').checks.some(c => c.id === 'anatomy') && take('1', 'tb').checks.some(c => c.id === 'look' && c.verdict === 'ok'));

    // 4. a multi-beat take: one request per beat, notes say which part, prev_url only on the first
    calls.length = 0;
    const b0 = I.state.videoBuilder;
    I.setState({ videoBuilder: { ...b0, takes: { ...b0.takes, '2': [mk('tm', '/media/p1.mp4', 8, [{ url: '/media/p1.mp4', seconds: 5 }, { url: '/media/p2.mp4', seconds: 3 }])] }, chosen: { ...b0.chosen, '2': 'tm' } } }); await wait(300);
    await I.checkClipTake(2, 0, 'tm')(); await wait(400);
    check('a multi-beat clip is checked beat by beat, with prev_url only on the first beat', calls.length === 2 && calls[0][1].url === '/media/p1.mp4' && calls[0][1].seconds === 5 && calls[0][1].prev_url === '/media/b.mp4' && calls[1][1].url === '/media/p2.mp4' && calls[1][1].prev_url === undefined, JSON.stringify(calls));
    check('and the note names the part that was flagged', /Part 2: The picture barely moves/.test(take('2', 'tm').checks.find(c => c.id === 'still').note) && take('2', 'tm').checks.find(c => c.id === 'still').verdict === 'check');

    // 5. a failed check leaves the take alone and says why
    qaFail = true; const before = JSON.stringify(take('0', 'ta')); toasts.length = 0;
    await I.checkClipTake(0, 0, 'ta')(); await wait(300);
    check('a check that fails (server says no ffmpeg) leaves the take as it was and tells the person why', JSON.stringify(take('0', 'ta')) === before && toasts.some(m => /ffmpeg/.test(m)), toasts.join('|'));
    qaFail = false;

    // 6. a new clip is checked at once, on its own
    calls.length = 0;
    I.renderViaJob = async () => ({ ok: true, status: 200, data: { ok: true, clips: [{ ok: true, url: '/media/new.mp4', seconds: 3 }], errors: [] } });
    I.setState({ videoBuilder: { ...I.state.videoBuilder, takes: { ...I.state.videoBuilder.takes, '0': [mk('ta', '/media/a.mp4', 4)] }, chosen: { ...I.state.videoBuilder.chosen, '0': 'ta' } } }); await wait(200);
    await I.generateClipTake(0, 0)(); await wait(700);
    const made = I.state.videoBuilder.takes['0'].find(x => x.url === '/media/new.mp4');
    check('a finished clip is checked automatically (one /take-check call for the new url)', calls.some(c => c[0] === 'check' && c[1].url === '/media/new.mp4'), JSON.stringify(calls.map(c => [c[0], c[1].url])));
    check('and the take carries its checks without anyone pressing a button', !!made && made.checks.length === 4, JSON.stringify(made && made.checks));

    // 7. checks survive the server's normalisation of the take: check_accepted is a plain boolean on the take
    check('check_accepted is a boolean field on every take', Object.values(I.state.videoBuilder.takes).every(l => l.every(x => typeof x.check_accepted === 'boolean' || x.check_accepted === undefined)));
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = realFetch; I.showToast = realToast; I.renderViaJob = realJob;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
