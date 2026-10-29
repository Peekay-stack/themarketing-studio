// film_render_qc.js -- the "Render check" under a finished film (FILM_CONSOLIDATED_PLAN.md C2), driven on the REAL page with the network and the render stubbed.
//
// Why: the 29 Oct grandmother film rendered "successfully" yet ended on 6 s of a pack that barely moved and 1.7 s of near silence, and nothing said so. /film-qc (ffmpeg only, free) measures
// the file; the page must show its findings next to the film, run it by itself after a render, offer it on demand for any other film shown (an older render, a re-scored one), say plainly
// when it could not check, and never touch the film. Advice only.
//
// How to run: start the studio (the backend needs a restart after this change), open http://localhost:8000/app (or your port), run this whole file with the browser tool's javascript_exec.
// In-memory state only; reload afterwards. Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 500 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.renderQcPanel === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.renderQcPanel === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const realFetch = window.fetch, realRender = I.renderViaJob, realCut = I.startCutFromFilm, realToast = I.showToast;
  const calls = [], bodies = [];
  let mode = 'findings';
  const J = (x, status) => new Response(JSON.stringify(x), { status: status || 200, headers: { 'Content-Type': 'application/json' } });
  window.fetch = async (u, o) => { const url = String(u); calls.push(url); if (o && o.body) { try { bodies.push(JSON.parse(o.body)); } catch (e) {} }
    if (/\/film-qc/.test(url)) {
      if (mode === 'fail') return J({ detail: 'boom' }, 500);
      if (mode === 'missing') return J({ ok: false, detail: 'That film is not on the server.' });
      if (mode === 'clean') return J({ ok: true, duration: 30, scenes: [], findings: [] });
      return J({ ok: true, duration: 30, scenes: [{ no: 5, start: 24, end: 30, motion: 0.16 }], findings: [
        { kind: 'barely-moves', scene: 5, note: 'Scene 5 barely moves for 6 s (picture change 0.16; a held but alive shot is 0.5 or more).' },
        { kind: 'silent-tail', scene: null, note: 'The film ends on 1.7 s of near silence (from 28.3 s).' }] });
    }
    return J({}); };
  I.showToast = () => {}; I.startCutFromFilm = () => {};
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const txt = () => document.body.innerText;
  const btn = t => [...document.querySelectorAll('button')].find(x => x.textContent.trim() === t);
  const rows = [{ no: 1, tc: '0–4s', visual: 'a' }, { no: 5, tc: '24–30s', visual: 'b' }];
  try {
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'production', scriptStatus: 'approved', fullScript: rows, producedUrl: null, renderQc: null, renderQcBusy: false,
      production: { ...I.state.production, status: 'ready', versions: [{ v: 1, note: 'First cut', url: '/renders/a.mp4' }] } });
    await wait(600);
    check('no film shown -> no Render check panel', I.renderQcPanel() === null && !/RENDER CHECK/i.test(txt()));

    I.setState({ producedUrl: '/renders/a.mp4' }); await wait(600);
    check('a film is shown with no report yet: the panel offers a free check', /RENDER CHECK/i.test(txt()) && !!btn('Check the picture and sound (free)'), txt().match(/RENDER CHECK[^\n]*/));

    btn('Check the picture and sound (free)').click(); await wait(700);
    check('the button calls /film-qc with this film and the script timecodes', calls.some(u => /film-qc/.test(u)) && bodies.some(b => b.url === '/renders/a.mp4' && b.scenes.length === 2 && b.scenes[1].tc === '24–30s' && !('visual' in b.scenes[1])), JSON.stringify(bodies));
    check('both findings are shown in plain words, with the free/advice-only note', /Scene 5 barely moves for 6 s/.test(txt()) && /near silence/.test(txt()) && /Free: measured from the file/.test(txt()));
    check('the film itself is untouched (still the same url)', I.state.producedUrl === '/renders/a.mp4');

    mode = 'clean'; btn('Check again').click(); await wait(700);
    check('a clean film says nothing is flagged', /Nothing flagged: every scene moves/.test(txt()) && !/barely moves/.test(txt()), txt().match(/RENDER CHECK[^\n]*/));

    mode = 'fail'; btn('Check again').click(); await wait(700);
    check('a failed check says so and offers to try again, without breaking the page', /Could not check the film/.test(txt()) && !!btn('Try again'));
    mode = 'missing'; btn('Try again').click(); await wait(700);
    check('a film the server cannot find shows the server\'s own reason', /That film is not on the server/.test(txt()));

    // a re-scored film is a different url: the old report does not carry over
    mode = 'findings'; btn('Try again').click(); await wait(700);
    I.setState({ producedUrl: '/renders/a-scored.mp4' }); await wait(600);
    check('a different film (a re-score) does not show the old report: it offers a fresh check', !!btn('Check the picture and sound (free)') && !/barely moves/.test(txt()));

    // the render itself runs the check by itself
    calls.length = 0; bodies.length = 0; I.setState({ producedUrl: null, renderQc: null });
    I.renderViaJob = async () => ({ ok: true, status: 200, data: { video_url: '/renders/new.mp4', shots: 2, seconds: 30, audio: 'mixed' } });
    await I.produceVideo(); await wait(900);
    check('a finished render runs /film-qc by itself on the new film', calls.some(u => /film-qc/.test(u)) && bodies.some(b => b.url === '/renders/new.mp4'), calls.join(','));
    check('and shows its findings next to the film', I.state.producedUrl === '/renders/new.mp4' && /Scene 5 barely moves/.test(txt()), txt().match(/RENDER CHECK[^\n]*/));

    // a render that fails does not run the check
    calls.length = 0; I.renderViaJob = async () => ({ ok: false, status: 500, data: { detail: 'render failed' } });
    await I.produceVideo(); await wait(500);
    check('a failed render does not call /film-qc', !calls.some(u => /film-qc/.test(u)), calls.join(','));
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = realFetch; I.renderViaJob = realRender; I.startCutFromFilm = realCut; I.showToast = realToast;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
