// film_pre_approve.js -- the "Before you approve" panel on the Scripting step (film-engagement lever #3/#5), driven on the REAL page with the two model reads stubbed.
//
// Why: the director's read, the shot plan and the flow review all work on a DRAFTED script (nothing drawn or paid for yet), but nothing told the person to use them before approving. The panel puts what they found
// next to the Approve button and offers to run each. It must be advisory only (Approve is never blocked), must say when a read is out of date, and must disappear once the script is approved.
//
// How to run: start the studio (preview "studio"), open http://localhost:8000/app, run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 500 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.preApprovePanel === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.preApprovePanel === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const realFetch = window.fetch, realToast = I.showToast;
  const calls = [], toasts = [];
  const J = (x) => new Response(JSON.stringify(x), { status: 200, headers: { 'Content-Type': 'application/json' } });
  window.fetch = async (u, o) => { const url = String(u); calls.push(url);
    if (/\/film-direct/.test(url)) return J({ summary: 'A morning.', scenes: [], findings: [], engagement: { risk: 'high', findings: [{ kind: 'slow-hook', scene: 1, note: 'The film opens quietly (scene 1: energy 0).' }, { kind: 'same-place', scene: 1, note: 'Two scenes in one room.' }] } });
    if (/\/film-review/.test(url)) return J({ verdicts: [], summary: 'Tight enough.', engagement: { risk: 'medium', why: 'The middle sags for two scenes.', fixes: [] }, notes: [] });
    return J({});
  };
  I.showToast = (m) => { toasts.push(String(m)); };
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const txt = () => document.body.innerText;
  const btn = t => [...document.querySelectorAll('button')].find(x => x.textContent.trim() === t);
  try {
    const rows = [{ no: 1, tc: '0–4s', visual: 'A woman pours milk.' }, { no: 2, tc: '4–8s', visual: 'A boy drinks.', shots: [{ visual: 'Close on the glass.', secs: 2 }] }];
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'scripting', scriptPhase: 'script', scriptStatus: 'drafted', videoObjective: 'Brand awareness', videoConcept: { logline: 'A morning.', proposition: 'Milk.', vo: '', scenes: [] },
      fullScript: rows, sceneFrames: {}, castRefUrl: null, videoBeatMap: null, filmReview: null, beatMapBusy: false, filmReviewBusy: false });
    await wait(800);
    check('on a drafted, unapproved script the panel is shown with its three rows', /BEFORE YOU APPROVE/i.test(txt()) && /Director.s read/.test(txt()) && /Shot plan/.test(txt()) && /Flow review/.test(txt()));
    check('nothing is read yet: it says so and offers to read', /Not read yet/.test(txt()) && /Not run yet/.test(txt()) && !!btn('Read the film') && !!btn('Review the flow'));
    check('the shot plan row reports how many scenes have extra angles planned (1 of 2)', /1 of 2 scenes have extra camera angles planned/.test(txt()));
    check('Approve is available and not disabled', !!btn('Approve script →') && !btn('Approve script →').disabled);

    btn('Read the film').click(); await wait(900);
    check('Read the film calls the director\'s read and the panel shows the boredom risk and the first finding', calls.some(u => /film-direct/.test(u)) && /Boredom risk: high/.test(txt()) && /The film opens quietly/.test(txt()) && /\+1 more/.test(txt()), (txt().match(/Boredom risk[^\n]*/) || [''])[0]);
    check('the button becomes Read again', !!btn('↻ Read again'));
    btn('Review the flow').click(); await wait(900);
    check('Review the flow shows "Would a viewer stay?" with its risk and reason', calls.some(u => /film-review/.test(u)) && /Would a viewer stay\? \(medium risk\)/.test(txt()) && /The middle sags/.test(txt()), (txt().match(/Would a viewer stay[^\n]*/) || [''])[0]);
    check('HIGH boredom risk does NOT block approving: Approve is still enabled', !btn('Approve script →').disabled);

    // the script changes: both reads are flagged out of date
    I.setState({ fullScript: [{ ...rows[0], visual: 'A woman pours milk, then drops the jug.' }, rows[1]] }); await wait(500);
    check('when the script changes, both reads say they are out of date', (txt().match(/the script has changed since this read/g) || []).length === 1 && /the script has changed since this review/.test(txt()), (txt().match(/Boredom risk[^\n]*/) || [''])[0]);

    // approving removes the panel
    // Phase 4: a high-risk read that matches the script makes Approve ask once; here the person answers yes.
    const realConfirm = window.confirm, asked = []; window.confirm = (m) => { asked.push(String(m)); return true; };
    I.approveScript(); await wait(700); window.confirm = realConfirm;
    check('approving works with the reads open, and the panel goes away', I.state.scriptStatus === 'approved' && !/BEFORE YOU APPROVE/i.test(txt()));
    check('the confirm was asked once, and only about the free Delivery row (this script has no speech): the two reads were out of date by then so they are not quoted', asked.length === 1 && /Only 0 spoken words/.test(asked[0]) && !/director.s read says/.test(asked[0]) && !/flow review says/.test(asked[0]), asked.join('|'));
    // no script: nothing
    I.setState({ scriptStatus: 'none', fullScript: null }); await wait(400);
    check('with no script there is no panel', !/BEFORE YOU APPROVE/i.test(txt()));
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = realFetch; I.showToast = realToast;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
