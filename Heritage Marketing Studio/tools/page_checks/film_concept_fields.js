// film_concept_fields.js -- film-engagement lever #2 (FILM_ENGAGEMENT_PLAN.md section 3): each concept route also carries a HOOK, a SURPRISE, a TURN and one MEMORABLE moment. Driven on the REAL page with the model
// (this.complete) and the brand preamble stubbed. The model's real behaviour was checked separately, with two real calls (see the plan).
//
// Why: the fields must be asked for in the prompt, survive parsing and route switching, show on the route cards and under the chosen concept's logline, be handed to the script writer as scenes it MUST deliver,
// survive a refine, and an older concept without them (or a provocation route) must behave EXACTLY as before: no extra lines, no extra sentence in the writer's prompt.
//
// How to run: start the studio (preview "studio"), open http://localhost:8000/app, run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 500 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.conceptEntertainText === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.conceptEntertainText === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const real = { complete: I.complete, needBrand: I.needBrand, brandPreamble: I.brandPreamble, learningContext: I.learningContext, showToast: I.showToast, fetch: window.fetch };
  const prompts = []; let reply = null;
  I.needBrand = () => true; I.brandPreamble = () => 'PREAMBLE'; I.learningContext = async () => ''; I.showToast = () => {};
  window.fetch = async () => new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
  I.complete = async (p) => { prompts.push(String(p)); if (reply === null) throw new Error('stop'); return reply; };
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const txt = () => document.body.innerText;
  const route = (n, withFields, partial) => ({ name: 'Route ' + n, rationale: 'Why ' + n + ' works.', logline: 'Logline ' + n, duration: '30s', vo: 'Voice ' + n, scenes: [{ t: '0–5s', title: 'B1', desc: 'd' }, { t: '5–10s', title: 'B2', desc: 'd' }],
    ...(withFields ? { hook: 'HOOK-' + n + ' a girl slams a steel glass down.', surprise: 'SURP-' + n + ' she is first at the gate.', turn: 'TURN-' + n + ' she lets go of his hand.', memorable: 'MEM-' + n + ' the milk moustache.' } : {}),
    ...(partial ? { hook: 'ONLYHOOK-' + n } : {}) });
  try {
    // 1. the prompt asks for the four fields
    I.setState({ screen: 'video', vTab: 'film', videoObjective: 'Brand awareness', scriptVersions: [], refinePrompt: '', videoForceTyped: false, videoBrief: '', videoGenerating: false, videoConcept: null, conceptRoutes: [], prodDuration: '30s', scriptPhase: 'concept' });
    reply = JSON.stringify({ routes: [route(1, true), route(2, true), route(3, true)] });
    await I.generateVideo(); await wait(800);
    const p = prompts[0] || '';
    check('the concept prompt asks for hook, surprise, turn and memorable, in the JSON shape too', /"hook" — what the viewer sees in the first 3 seconds/.test(p) && /"surprise"/.test(p) && /"turn" — the moment something visibly changes/.test(p) && /"memorable" — ONE image or action/.test(p)
      && /"hook": string, "surprise": string, "turn": string, "memorable": string/.test(p), p.slice(-600));
    check('it forbids a quiet establishing hook and generic lines, and wants the four to differ', /never a quiet establishing view/.test(p) && /never a generic line such as/.test(p) && /the four must differ from each other/.test(p));
    check('the rest of the prompt is as before (three routes, the voiceover rules, the JSON beats)', /Propose THREE genuinely different creative routes/.test(p) && /exactly 3 routes/.test(p) && /ONE continuous read across the whole film/.test(p));

    // 2. parsed, kept, shown
    const s = I.state;
    check('the first route becomes the working concept WITH its four fields; all three routes keep theirs', s.videoConcept.hook === 'HOOK-1 a girl slams a steel glass down.' && s.videoConcept.memorable.startsWith('MEM-1') && s.conceptRoutes.length === 3 && s.conceptRoutes.every((r, i) => r.turn === 'TURN-' + (i + 1) + ' she lets go of his hand.'), JSON.stringify(s.videoConcept));
    check('each route card shows its own four lines', /HOOK-1/.test(txt()) && /HOOK-2/.test(txt()) && /HOOK-3/.test(txt()) && /SURP-2/.test(txt()) && /TURN-3/.test(txt()) && /MEM-1/.test(txt()));
    check('the chosen concept shows them under its logline too', (txt().match(/HOOK-1/g) || []).length >= 2, String((txt().match(/HOOK-1/g) || []).length));
    check('the four are labelled (Hook, Surprise, Turn, Remember)', /HOOK/i.test(txt()) && /SURPRISE/i.test(txt()) && /TURN/i.test(txt()) && /REMEMBER/i.test(txt()));

    // 3. switching route
    I.pickConceptRoute(1)(); await wait(600);
    check('picking another route makes ITS fields the concept\'s', I.state.videoConcept.hook.startsWith('HOOK-2') && I.state.conceptRoute === 1);

    // 4. the script writer is told to deliver them
    prompts.length = 0; reply = null;
    I.setState({ scriptWriting: false, fullScript: null, scriptStatus: 'concept' });
    await I.writeFullScript(); await wait(500);
    const w = prompts[0] || '';
    check('the full-script writer is told the concept\'s four lines MUST be delivered as scenes, and that the first scene shows the hook',
      /This concept’s own entertainment, which the script MUST deliver as scenes/.test(w) && /hook: HOOK-2/.test(w) && /surprise: SURP-2/.test(w) && /turn: TURN-2/.test(w) && /memorable moment: MEM-2/.test(w) && /The first scene must show the hook/.test(w) && !/\.\./.test(w.slice(0, w.indexOf('The finished film'))), w.slice(0, 700));
    check('and it sits with the concept (before the length and scene-count instructions)', w.indexOf('own entertainment') > 0 && w.indexOf('own entertainment') < w.indexOf('The finished film is'));

    // 5. refine keeps them
    prompts.length = 0; reply = null;
    I.setState({ scriptVersions: [{ v: 1, logline: 'x' }], refinePrompt: 'make it funnier', videoGenerating: false });
    await I.generateVideo(); await wait(500);
    check('a refine re-sends the current route WITH its four fields so they are kept', /"hook":"HOOK-2/.test(prompts[0] || '') && /"memorable":"MEM-2/.test(prompts[0] || ''), (prompts[0] || '').slice(0, 500));

    // 6. an older concept (no fields): nothing extra anywhere
    prompts.length = 0; reply = null;
    I.setState({ videoConcept: route(9, false), conceptRoutes: [route(9, false), route(8, false)], conceptRoute: 0, scriptPhase: 'concept', scriptWriting: false, fullScript: null, scriptStatus: 'concept', scriptVersions: [], refinePrompt: '' }); await wait(600);
    check('an older concept shows no Hook/Surprise/Turn/Remember lines', !/REMEMBER/i.test(txt()) && !/\bSURPRISE\b/.test(txt()));
    await I.writeFullScript(); await wait(500);
    check('and its writer prompt has NO entertainment sentence (byte-for-byte the old behaviour)', !/own entertainment/.test(prompts[0] || '') && !/must show the hook/.test(prompts[0] || '') && /Concept logline: "Logline 9"/.test(prompts[0] || ''), (prompts[0] || '').slice(0, 300));
    check('a concept with no hook never claims the first scene must show one', !/must show the hook/.test(I.conceptEntertainText({ surprise: 'only a surprise' })) && /surprise: only a surprise/.test(I.conceptEntertainText({ surprise: 'only a surprise' })));
    check('conceptEntertainText is the empty string for it', I.conceptEntertainText(route(9, false)) === '' && I.entertainLines(route(9, false)) === null);

    // 7. partial fields: only what exists
    I.setState({ videoConcept: route(7, false, true), scriptPhase: 'concept' }); await wait(500);
    check('a concept with only some of the fields shows and sends only those', /ONLYHOOK-7/.test(txt()) && I.conceptFour(route(7, false, true)).length === 1 && /hook: ONLYHOOK-7/.test(I.conceptEntertainText(route(7, false, true))) && !/surprise:/.test(I.conceptEntertainText(route(7, false, true))));
    check('whitespace is collapsed and text is shown as text, never as markup', (() => { const c = I.conceptFour({ hook: '  a\n\n b   <b>x</b> ' }); return c.length === 1 && c[0][1] === 'a b <b>x</b>'; })());
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    I.complete = real.complete; I.needBrand = real.needBrand; I.brandPreamble = real.brandPreamble; I.learningContext = real.learningContext; I.showToast = real.showToast; window.fetch = real.fetch;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
