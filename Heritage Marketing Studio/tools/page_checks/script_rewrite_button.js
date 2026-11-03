// script_rewrite_button.js -- the "Rewrite scene" button on the full-script table, and the "Direction for this beat" box beside it. Driven on the REAL page with the model stubbed.
//
// Why: on 3 Nov the button did nothing. It bound to `r.rewriteScene`, a row property nobody set (dead since the first commit), and the Direction box was never read by a rewrite. Now the button rewrites
// THAT scene, follows that scene's direction text when there is one, leaves the other scenes alone, and never starts a second rewrite while one is running.
//
// How to run: start the studio, open http://localhost:8000/app, run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 500 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.rewriteScene === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.rewriteScene === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance (reload the page, wait 3 s, run again)'] });
  const real = { claude: window.claude, showToast: I.showToast };
  const prompts = []; let gate = null;
  I.showToast = () => {};
  window.claude = { complete: async (c) => { prompts.push(c.messages[0].content); if (gate) await gate; return JSON.stringify({ no: 2, tc: '5-15s', visual: 'REWRITTEN visual', camera: 'cam', dialogue: '', supr: '', place: '', audio: [] }); } };
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const rows = (note) => [1, 2, 3].map(n => ({ no: n, tc: (n * 5 - 5) + '-' + (n * 5) + 's', visual: 'Visual ' + n + ' kitchen', camera: 'cam ' + n, dialogue: '', supr: '', audio: [], beat_note: n === 2 ? note : '' }));
  const buttons = () => [...document.querySelectorAll('button')].filter(b => /Rewrite scene/.test(b.innerText) && !/in a new place|\d/.test(b.innerText));
  try {
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'scripting', videoObjective: 'Brand awareness', videoConcept: { logline: 'L', scenes: [], vo: '' }, fullScript: rows('MY DIRECTION TEXT'), scriptStatus: 'ready', scriptPhase: 'script', rewritingScene: null, prodDuration: '30s' });
    await wait(900);
    check('each scene row has a Rewrite scene button', buttons().length === 3, buttons().length);
    buttons()[1].click(); await wait(900);
    check('clicking the button for scene 2 runs ONE model call', prompts.length === 1, prompts.length);
    check('the call carries scene 2’s direction text as the direction to follow', /DIRECTION FOR THIS REWRITE \(follow it\): MY DIRECTION TEXT/.test(prompts[0] || ''), (prompts[0] || '').slice(-400));
    check('only scene 2 is replaced; scenes 1 and 3 are untouched', I.state.fullScript[1].visual === 'REWRITTEN visual' && I.state.fullScript[0].visual === 'Visual 1 kitchen' && I.state.fullScript[2].visual === 'Visual 3 kitchen');
    check('the direction text stays in the box afterwards', I.state.fullScript[1].beat_note === 'MY DIRECTION TEXT');
    check('the button is idle again afterwards', I.state.rewritingScene === null);

    prompts.length = 0; I.setState({ fullScript: rows(''), rewritingScene: null }); await wait(700);
    buttons()[1].click(); await wait(900);
    check('with no direction text the rewrite still runs and adds no direction sentence', prompts.length === 1 && !/DIRECTION FOR THIS REWRITE/.test(prompts[0] || ''), prompts.length);

    prompts.length = 0; let open; gate = new Promise(r => { open = r; }); I.setState({ fullScript: rows('SLOW'), rewritingScene: null }); await wait(700);
    buttons()[1].click(); await wait(300); buttons()[0].click(); await wait(300);
    check('while one rewrite is running a second click starts nothing', prompts.length === 1, prompts.length);
    open(); gate = null; await wait(700);
    check('and it finishes', I.state.rewritingScene === null && I.state.fullScript[1].visual === 'REWRITTEN visual');
  } catch (e) {
    check('no exception', false, String(e && e.stack || e));
  } finally {
    window.claude = real.claude; I.showToast = real.showToast;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})();
