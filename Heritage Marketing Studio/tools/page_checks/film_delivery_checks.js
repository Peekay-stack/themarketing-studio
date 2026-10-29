// film_delivery_checks.js -- the free "Delivery" row of the "Before you approve" panel (FILM_CONSOLIDATED_PLAN.md C1), driven on the REAL page with the network stubbed.
//
// Why: the 28 Oct grandmother film passed the director's read and the flow review, yet spoke 13 words against a budget of 32, had two silent scenes and a silent pack shot, and its concept voiceover
// (26 words) never reached the script. Nothing said so. The Delivery row counts words only (no model, no language reading) and must: flag a thin script, flag a silent sign-off, mention a dropped concept
// voiceover, stay quiet on a well-voiced film, skip a wordless film, count rows that have only a dialogue string, update when the script is edited, and never block Approve.
//
// How to run: start the studio, open http://localhost:8000/app (or the port you started), run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
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
  const realFetch = window.fetch, realBudget = I.voBudget;
  const J = (x) => new Response(JSON.stringify(x), { status: 200, headers: { 'Content-Type': 'application/json' } });
  window.fetch = async () => J({});
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const txt = () => document.body.innerText;
  const delivery = () => (txt().match(/DELIVERY[\s\S]*?(?=Each read is one model call)/i) || [''])[0];
  const btn = t => [...document.querySelectorAll('button')].find(x => x.textContent.trim() === t);
  const aud = (type, text, lang) => ({ type, language: lang || 'te', text });
  try {
    // the real saved grandmother film: 13 spoken words, scenes 2 and 5 silent, the sign-off (scene 5) silent
    const thin = [
      { no: 1, tc: '0–4s', visual: 'A drop of milk rolls down a steel plate.', audio: [aud('dialogue', 'ఇంకా చూడాలి')] },
      { no: 2, tc: '4–10s', visual: 'She sips and smells it.', audio: [] },
      { no: 3, tc: '10–16s', visual: 'Her daughter-in-law pours.', audio: [aud('dialogue', 'అవసరం లేదు, అత్తయ్యా')] },
      { no: 4, tc: '16–24s', visual: 'A close-up of her smile.', audio: [aud('dialogue', 'సరే మరి'), aud('vo', 'Now, only the drinking is left.', 'en')] },
      { no: 5, tc: '24–30s', visual: 'The pack on the table.', supr: 'Heritage Foods — Nothing left to test.', audio: [] }];
    const conceptVo = 'For fifty years she checked every drop, because she had to. Today her daughter simply pours. The worry is gone, so only the drinking is left.';
    const voWords = conceptVo.split(/\s+/).length;
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'scripting', scriptPhase: 'script', scriptStatus: 'drafted', prodDuration: '30s', videoObjective: 'Brand awareness',
      videoConcept: { logline: 'Nothing left to test.', proposition: 'Milk.', vo: conceptVo, scenes: [] }, fullScript: thin, sceneFrames: {}, castRefUrl: null, videoBeatMap: null, filmReview: null });
    await wait(800);
    check('the Delivery row is on the panel of a drafted script', /DELIVERY/i.test(txt()) && /BEFORE YOU APPROVE/i.test(txt()));
    const d1 = delivery();
    check('counts 13 spoken words against a budget of 32 and says the script is thin', /Only 13 spoken words for a 30s film \(the budget is about 32\)/.test(d1), d1);
    check('says the concept voiceover (' + voWords + ' words) did not reach the script', new RegExp('concept.s own voiceover runs ' + voWords + ' words').test(d1), d1);
    check('flags the silent sign-off and names scene 5', /sign-off scene \(scene 5\) has no spoken line/.test(d1), d1);
    check('does not list scene 5 again among the silent scenes (a single other silent scene is not a finding)', !/Scenes .* have no speech/.test(d1), d1);
    check('Approve is available and not disabled with every finding showing', !!btn('Approve script →') && !btn('Approve script →').disabled);

    // two more silent scenes: the soft note appears, in plain words
    I.setState({ fullScript: thin.map((r, i) => (i === 2 ? { ...r, audio: [] } : r)) }); await wait(500);
    check('with scenes 2 and 3 silent the soft note names them', /Scenes 2, 3 have no speech \(2 of 5 scenes\)/.test(delivery()), delivery());

    // a well-voiced film: 6 scenes' worth of speech, the sign-off speaks
    const good = thin.map((r, i) => ({ ...r, audio: [aud('vo', 'one two three four five six seven')] }));
    I.setState({ fullScript: good }); await wait(500);
    const d2 = delivery();
    check('a well-voiced film is not flagged: it says so with the count and the budget', /Nothing flagged: 35 spoken words \(budget about 32\) and the sign-off speaks/.test(d2), d2);

    // a script whose words are fine but whose concept voiceover is mostly gone
    I.setState({ fullScript: good.map((r, i) => (i < 2 ? r : { ...r, audio: i === 4 ? [aud('vo', 'a b c')] : [] })), videoConcept: { logline: 'x', proposition: 'y', vo: conceptVo + ' ' + conceptVo, scenes: [] } }); await wait(500);
    const d3 = delivery();
    check('17 words (over half the budget) against a 52-word concept voiceover is flagged as not carried, without the thin-script line', /concept.s voiceover runs 52 words but the script speaks only 17/.test(d3) && !/Only 17 spoken/.test(d3), d3);

    // a wordless film by design (budget 0): speech is not checked
    I.voBudget = () => 0; I.setState({ fullScript: thin }); await wait(500);
    check('a wordless film (budget 0) is not checked and says so', /wordless film by design/.test(delivery()) && !/spoken word/.test(delivery()), delivery());
    I.voBudget = realBudget;

    // rows that carry only a dialogue string (older scripts): labels and glosses are not counted
    const old = [{ no: 1, tc: '0–5s', visual: 'a', dialogue: 'Boy (sleepy): Mummy, milk! (a gloss in brackets)' }, { no: 2, tc: '5–10s', visual: 'b', dialogue: 'VO: One glass a day.' }];
    check('a dialogue-only row counts the spoken words, not the label or the bracketed gloss', I.spokenWordsOf(old[0]) === 2 && I.spokenWordsOf(old[1]) === 4, [I.spokenWordsOf(old[0]), I.spokenWordsOf(old[1])]);
    check('a row with neither audio nor dialogue has no words', I.spokenWordsOf({ no: 1 }) === 0 && I.spokenWordsOf(null) === 0);

    // editing the script updates the row and approving removes the panel
    I.setState({ fullScript: thin, videoConcept: { logline: 'x', proposition: 'y', vo: conceptVo, scenes: [] } }); await wait(500);
    check('back to the thin script the finding returns', /Only 13 spoken words/.test(delivery()), delivery());
    I.approveScript(); await wait(700);
    check('approving works with findings showing and the panel goes away', I.state.scriptStatus === 'approved' && !/BEFORE YOU APPROVE/i.test(txt()));
    I.setState({ scriptStatus: 'none', fullScript: null }); await wait(400);
    check('with no script there is no panel and the check returns nothing', !/BEFORE YOU APPROVE/i.test(txt()) && I.deliveryChecks().items.length === 0);
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = realFetch; I.voBudget = realBudget;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
