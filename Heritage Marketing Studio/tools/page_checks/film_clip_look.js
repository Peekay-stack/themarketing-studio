// film_clip_look.js -- Phase 5 of FILM_CONSOLIDATED_PLAN.md (FILM_PHASE5_AND_PLACE_PLAN.md P5.3, P5.4): the model's look at a clip now takes THREE frames, and "Look at chosen clips" runs it on every chosen clip
// that has not had one, only when asked, after one confirm that says how many and about what it costs. Driven on the REAL page with the network, the model and window.confirm stubbed.
//
// How to run: start the studio, open http://localhost:8000/app (or your port), run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 500 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.lookAllChosen === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.lookAllChosen === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const realFetch = window.fetch, realToast = I.showToast, realConfirm = window.confirm;
  const bodies = [], toasts = [], asked = []; let mode = 'clean', answer = true;
  const J = (x, status) => new Response(JSON.stringify(x), { status: status || 200, headers: { 'Content-Type': 'application/json' } });
  window.fetch = async (u, o) => { const url = String(u), body = o && o.body ? JSON.parse(o.body) : {};
    if (/\/take-look/.test(url)) {
      bodies.push(body);
      if (mode === 'fail') return J({ detail: 'The look needs the Anthropic key, which is not set on this server.' }, 503);
      const flag = mode === 'flag' && /b\.mp4/.test(body.url);
      return J({ verdict: flag ? 'check' : 'ok', checks: flag ? [{ id: 'drift', label: 'Changes between frames', verdict: 'check', note: 'The arm stretches across the face between the middle and late frames.' }] : [], seen: 'A boy lifts a glass.', frames: body.frames || 1 });
    }
    return J({}); };
  I.showToast = (m) => { toasts.push(String(m)); };
  window.confirm = (m) => { asked.push(String(m)); return answer; };
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const txt = () => document.body.innerText;
  const btn = (re) => [...document.querySelectorAll('button')].find(x => re.test(x.textContent.trim()));
  const mk = (id, url, checks) => ({ id, url, beats: [], tier: 'draft', engine: 'omni', seconds: 4, mode: 'frame', frame: '/media/f0.jpg', status: 'done', error: '', checks: checks || [], check_accepted: false, est_usd: 0.1 });
  const take = (key, id) => I.state.videoBuilder.takes[key].find(x => x.id === id);
  try {
    const rows = [{ no: 1, tc: '0–4s', visual: 'A boy drinks.' }, { no: 2, tc: '4–8s', visual: 'A mother pours.' }, { no: 3, tc: '8–12s', visual: 'The pack on the counter.' }, { no: 4, tc: '12–16s', visual: 'They smile.' }];
    const fr = {}; rows.forEach((r, i) => fr[i] = { status: 'done', url: '/media/f' + i + '.jpg' });
    const looked = [{ id: 'look', label: 'Model look', verdict: 'ok', note: 'earlier' }];
    const vb = { version: 1, frames: {}, frame_chosen: {}, takes: { '0': [mk('ta', '/media/a.mp4')], '1': [mk('tb', '/media/b.mp4')], '2': [mk('tc', '/media/c.mp4', looked)], '3': [mk('td', '/media/d.mp4')] }, chosen: { '0': 'ta', '1': 'tb', '2': 'tc' }, trim: {}, budget: { cap_usd: 0, spent_usd: 0 } };
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'shots', fullScript: rows, scriptStatus: 'approved', sceneFrames: fr, castRefUrl: '/media/c.jpg', videoCharacters: 'A boy of nine.', videoBuilder: vb, takeChecking: {}, clipBusy: {}, clipBatch: false, lookBatch: false });
    await wait(700);

    // 1. the single Look sends three frames
    await I.lookClipTake(0, 0, 'ta')(); await wait(300);
    check('Look on one take asks for THREE frames in one call, with the shot\'s words', bodies.length === 1 && bodies[0].frames === 3 && bodies[0].url === '/media/a.mp4' && bodies[0].description === 'A boy drinks.', JSON.stringify(bodies));
    check('the result is kept on the take as a model look (an ok look is stored as a note, not a flag)', take('0', 'ta').checks.some(c => c.id === 'look') && I.clipChecksOf(take('0', 'ta')).length === 0, JSON.stringify(take('0', 'ta').checks));

    // 2. which clips the batch would look at: chosen, done, not yet looked at (ta was just looked at; tc had a look; tb is the one left; td is not chosen)
    check('the batch lists only CHOSEN clips with no model look yet: here just shot 2 (shot 1 was just looked at, shot 3 has a look, shot 4 has no chosen clip)', JSON.stringify(I.chosenToLook()) === JSON.stringify([{ idx: 1, k: 0, id: 'tb' }]), JSON.stringify(I.chosenToLook()));
    check('the header offers it with the count and a cost range, and it is not offered when there is nothing to look at', !!btn(/Look at chosen clips \(1\)/) && /\$0\.02–\$0\.03/.test(btn(/Look at chosen clips/).textContent), (btn(/Look at chosen clips/) || {}).textContent);
    check('the cost text scales with the count and follows the Draft / Final choice', I.lookCostText(10) === 'about $0.20–$0.30' && I.lookCostText(0) === '');
    I.setState(s => ({ videoBuilder: { ...s.videoBuilder, chosen: { ...s.videoBuilder.chosen, '3': 'td' } } })); await wait(300);
    check('choosing shot 4\'s clip adds it to the batch (2 clips)', I.chosenToLook().length === 2 && !!btn(/Look at chosen clips \(2\)/));

    // 3. answering NO runs nothing; YES runs them one after another, flags show, the toast counts
    bodies.length = 0; asked.length = 0; answer = false; await I.lookAllChosen();
    check('answering NO to the confirm runs nothing and spends nothing; the confirm named the count and the cost', bodies.length === 0 && asked.length === 1 && /Look at 2 chosen clips/.test(asked[0]) && /about \$0\.04–\$0\.06/.test(asked[0]) && /nothing is blocked/.test(asked[0]), asked.join('|'));
    mode = 'flag'; answer = true; asked.length = 0; toasts.length = 0; bodies.length = 0; await I.lookAllChosen(); await wait(400);
    check('answering YES looks at each clip once, in script order, three frames each', bodies.length === 2 && bodies.every(b => b.frames === 3) && bodies[0].url === '/media/b.mp4' && bodies[1].url === '/media/d.mp4', JSON.stringify(bodies.map(b => b.url)));
    check('the flagged clip carries a drift note (an open check), the clean one an ok look; the toast says one clip has something to check', I.clipChecksOf(take('1', 'tb')).length === 1 && I.clipChecksOf(take('1', 'tb'))[0].id === 'drift' && I.clipChecksOf(take('3', 'td')).length === 0 && toasts.some(t => /Looked at 2 clips: 1 with something to check/.test(t)), toasts.join('|') + JSON.stringify(take('1', 'tb').checks));
    check('the flagged note shows on the take in words, and the batch button is gone now that every chosen clip has had a look', /The arm stretches across the face/.test(txt()) && !btn(/Look at chosen clips/) && !I.state.lookBatch);
    check('Approve, assemble and promote are not blocked by a flagged look (advice only)', I.clipChecksOf(take('1', 'tb')).length === 1 && typeof I.assembleStatus === 'function');

    // 4. a failing look stops the batch at the first failure (it would fail the same way for every clip) and says why once
    I.setState(s => ({ videoBuilder: { ...s.videoBuilder, takes: { ...s.videoBuilder.takes, '0': s.videoBuilder.takes['0'].map(t => ({ ...t, checks: [] })), '1': s.videoBuilder.takes['1'].map(t => ({ ...t, checks: [] })) } } })); await wait(300);
    mode = 'fail'; bodies.length = 0; toasts.length = 0; await I.lookAllChosen(); await wait(300);
    check('a failing look (no model key) stops the batch after ONE call, says why, and leaves the button free', bodies.length === 1 && toasts.some(t => /Anthropic key/.test(t)) && I.state.lookBatch === false, JSON.stringify({ n: bodies.length, t: toasts }));

    // 5. not offered while clips are being generated
    I.setState({ clipBatch: true }); await wait(300);
    check('while clips are being generated the batch look is disabled', !!btn(/Look at chosen clips/) && btn(/Look at chosen clips/).disabled === true);
    I.setState({ clipBatch: false });
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = realFetch; I.showToast = realToast; window.confirm = realConfirm;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
