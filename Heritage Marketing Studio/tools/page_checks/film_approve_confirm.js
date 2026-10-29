// film_approve_confirm.js -- the ONE confirm on "Approve script" (FILM_CONSOLIDATED_PLAN.md C8), driven on the REAL page with the network and window.confirm stubbed.
//
// Why: the checks (the director's read, the flow review, the free Delivery row) are advice, and the 29 Oct film passed them all by being ignored. Approving locks the script and starts the paid steps, so when
// the checks found something serious Approve asks ONCE, listing it, and the person can still approve. It must ask only for a read that matches the script as it is now, only for serious findings
// (a high-risk read, a concept promise flattened or left out, a thin or silent script), never for a clean script, never twice, and a "no" must leave the script as it was.
//
// How to run: start the studio, open http://localhost:8000/app (or your port), run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 500 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.approvalConcerns === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.approvalConcerns === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const realFetch = window.fetch, realConfirm = window.confirm, realToast = I.showToast, realBudget = I.voBudget;
  window.fetch = async () => new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
  I.showToast = () => {};
  let asked = [], answer = true;
  window.confirm = (m) => { asked.push(String(m)); return answer; };
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const txt = () => document.body.innerText;
  const btn = t => [...document.querySelectorAll('button')].find(x => x.textContent.trim() === t);
  const aud = (type, text, lang) => ({ type, language: lang || 'en', text });
  // a well-voiced script: 35 spoken words, the sign-off speaks
  const good = [1, 2, 3, 4, 5].map(n => ({ no: n, tc: (n * 6 - 6) + '–' + (n * 6) + 's', visual: 'Scene ' + n + ' shows something different.', audio: [aud('vo', 'one two three four five six seven')] }));
  const thin = good.map((r, i) => ({ ...r, audio: i === 0 ? [aud('dialogue', 'two words')] : [] }));
  const fresh = (over) => ({ sig: I.beatSig(), summary: 's', scenes: [], findings: [], engagement: { risk: 'low' }, model: true, ...over });
  const setup = (rows, extra) => I.setState({ screen: 'video', vTab: 'film', videoStep: 'scripting', scriptPhase: 'script', scriptStatus: 'drafted', prodDuration: '30s', videoObjective: 'Brand awareness',
    videoConcept: { logline: 'L', proposition: 'P', vo: '', scenes: [] }, fullScript: rows, sceneFrames: {}, castRefUrl: null, videoBeatMap: null, filmReview: null, ...(extra || {}) });
  const reset = () => { asked = []; answer = true; I.setState({ scriptStatus: 'drafted', videoStep: 'scripting' }); };
  try {
    // 1. a clean script, no reads: no confirm, approved at once
    setup(good); await wait(600); reset();
    check('a well-voiced script with no reads has no concerns', I.approvalConcerns().length === 0, JSON.stringify(I.approvalConcerns()));
    I.approveScript(); await wait(500);
    check('a clean script is approved with NO confirm', asked.length === 0 && I.state.scriptStatus === 'approved', asked.join('|'));

    // 2. a thin script: one confirm that names it; "no" leaves the script as it was; "yes" approves
    setup(thin); await wait(600); reset(); answer = false;
    I.approveScript(); await wait(500);
    check('a thin script asks once, naming the problem, and offers a way back', asked.length === 1 && /Before you approve, the checks found/.test(asked[0]) && /Only 2 spoken words/.test(asked[0]) && /sign-off scene/.test(asked[0]) && /Cancel to change it first/.test(asked[0]), asked.join('|'));
    check('answering NO leaves the script a draft (nothing was approved, no step changed)', I.state.scriptStatus === 'drafted' && I.state.videoStep === 'scripting', I.state.scriptStatus + '/' + I.state.videoStep);
    answer = true; asked = [];
    I.approveScript(); await wait(500);
    check('answering YES approves it (never blocked), after exactly one confirm', asked.length === 1 && I.state.scriptStatus === 'approved');

    // 3. the Approve BUTTON goes through the same confirm
    setup(thin); await wait(600); reset(); answer = false;
    btn('Approve script →').click(); await wait(500);
    check('the Approve button asks the same question and a no keeps the draft', asked.length === 1 && I.state.scriptStatus === 'drafted');

    // 4. a fresh high-risk read with flattened and missing promises is quoted; a stale one is not
    setup(good); await wait(600); reset();
    I.setState({ videoBeatMap: fresh({ engagement: { risk: 'high' }, findings: [
      { kind: 'concept-flattened', scene: 2, note: 'The concept’s beat 2 is flattened in the script: three actions shown as one still shot.' },
      { kind: 'concept-missing', scene: null, note: 'The concept’s surprise is missing in the script.' },
      { kind: 'concept-flattened', scene: 3, note: 'The concept’s turn is flattened.' }, { kind: 'concept-flattened', scene: 4, note: 'The concept’s memorable moment is flattened.' },
      { kind: 'same-place', scene: 1, note: 'Five scenes in one kitchen.' }] }) }); await wait(400);
    const c4 = I.approvalConcerns();
    check('a fresh high-risk read is quoted, with its first three concept findings and a count of the rest, and NOT the engagement-only findings', c4.length === 5 && /director.s read says the film risks being boring/.test(c4[0]) && /three actions shown as one still shot/.test(c4[1]) && /1 more of the concept/.test(c4[4]) && !c4.some(x => /one kitchen/.test(x)), JSON.stringify(c4));
    asked = []; answer = true; I.approveScript(); await wait(400);
    check('and that makes Approve ask once, listing them as bullets', asked.length === 1 && /• The director.s read says/.test(asked[0]) && /• The concept.s surprise is missing/.test(asked[0]), asked.join('|'));
    reset(); I.setState({ fullScript: good.map((r, i) => (i === 1 ? { ...r, visual: 'The script was edited after the read.' } : r)) }); await wait(400);
    check('once the script is edited the read no longer matches and is NOT quoted', I.approvalConcerns().length === 0, JSON.stringify(I.approvalConcerns()));

    // 5. a medium read, or only delivered promises, does not ask; the flow review counts only at high risk and only when fresh
    reset(); I.setState({ fullScript: good, videoBeatMap: fresh({ engagement: { risk: 'medium' }, findings: [{ kind: 'slow-hook', scene: 1, note: 'quiet open' }] }) }); await wait(400);
    check('a MEDIUM read does not make Approve ask', I.approvalConcerns().length === 0, JSON.stringify(I.approvalConcerns()));
    I.setState({ filmReview: { sig: I.flowReviewSig(), engagement: { risk: 'high', why: 'sags' }, verdicts: [], notes: [] } }); await wait(400);
    check('a fresh HIGH flow review is quoted', I.approvalConcerns().length === 1 && /flow review says a viewer would probably leave/.test(I.approvalConcerns()[0]), JSON.stringify(I.approvalConcerns()));
    I.setState({ filmReview: { sig: 'old', engagement: { risk: 'high' }, verdicts: [], notes: [] } }); await wait(400);
    check('a flow review for an older script is not quoted', I.approvalConcerns().length === 0);

    // 6. soft notes (silent scenes that may be meant to breathe) never make it ask; a wordless film is not asked about speech
    const breathe = good.map((r, i) => ({ ...r, audio: i === 1 || i === 2 ? [] : [aud('vo', 'one two three four five six seven eight')] }));
    I.setState({ fullScript: breathe, videoBeatMap: null, filmReview: null }); await wait(500);
    check('two silent scenes in a voiced film are a soft note in the panel, not a reason to ask', /have no speech/.test(txt()) && I.approvalConcerns().length === 0, JSON.stringify(I.approvalConcerns()));
    I.voBudget = () => 0; I.setState({ fullScript: thin }); await wait(500);
    check('a wordless film (budget 0) is not asked about speech', I.approvalConcerns().length === 0, JSON.stringify(I.approvalConcerns()));
    I.voBudget = realBudget;

    // 7. with no window.confirm at all, approving still works (a host that cannot ask never blocks)
    setup(thin); await wait(600); reset(); const keep = window.confirm; window.confirm = undefined;
    I.approveScript(); await wait(500); window.confirm = keep;
    check('with no way to ask, Approve simply approves', I.state.scriptStatus === 'approved');
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = realFetch; window.confirm = realConfirm; I.showToast = realToast; I.voBudget = realBudget;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
