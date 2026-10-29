// film_phase2_prompts.js -- the Phase 2 prompt rules (FILM_CONSOLIDATED_PLAN.md C3, C4, C5), driven on the REAL page with the model stubbed so the exact prompts the page builds can be read.
//
// Why: the 29 Oct grandmother film lost its concept voiceover (13 spoken words against a 26-word concept voiceover), ended on a silent still pack, kept one kitchen, and its ritual "quick cuts" beat became
// one static shot; round 1's broken clip was an arm stretched across a face. These rules go into the writer, the single-scene rewrite and the concept prompt. This file proves the TEXT is where it should be
// and only where it should be (the shared VISUAL_RULES must stay as it was; an older concept and a wordless film must not get speech rules). Whether the model OBEYS them is a separate, real-model check.
//
// How to run: start the studio, open http://localhost:8000/app (or your port), run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 500 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.deliveryRulesText === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.deliveryRulesText === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const real = { complete: I.complete, needBrand: I.needBrand, brandPreamble: I.brandPreamble, learningContext: I.learningContext, showToast: I.showToast, fetch: window.fetch, voBudget: I.voBudget };
  const prompts = []; let reply = null;
  I.needBrand = () => true; I.brandPreamble = () => 'PREAMBLE'; I.learningContext = async () => ''; I.showToast = () => {};
  window.fetch = async () => new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
  I.complete = async (p) => { prompts.push(String(p)); if (reply === null) throw new Error('stop'); return reply; };
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const concept = (vo, noStake) => ({ name: 'R', rationale: 'Why.', logline: 'Nothing left to test.', duration: '30s', ...(noStake ? {} : { stake: 'STAKE-X she loses the one test she has trusted for fifty years.' }), hook: 'HOOK a drop rolls down a plate.', surprise: 'SURP a lifetime of tests.', turn: 'TURN she drinks it straight.', memorable: 'MEM the plate forgotten.',
    vo, scenes: [{ t: '0–6s', title: 'B1', desc: 'a drop' }, { t: '6–15s', title: 'B2', desc: 'Quick cuts: she smells it, watches it boil, holds it to light' }] });
  const VO = 'For fifty years she checked every drop, because she had to. Today her daughter simply pours. The worry is gone, so only the drinking is left.';
  const writer = async (c) => { prompts.length = 0; reply = null; I.setState({ screen: 'video', vTab: 'film', videoStep: 'scripting', prodDuration: '30s', videoConcept: c, conceptRoutes: [c], conceptRoute: 0, scriptPhase: 'concept', scriptWriting: false, fullScript: null, scriptStatus: 'concept' });
    await I.writeFullScript(); await wait(400); return prompts[0] || ''; };
  try {
    // ---- C4: the concept prompt
    prompts.length = 0; reply = JSON.stringify({ routes: [concept(VO), concept(VO), concept(VO)] });
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'scripting', videoObjective: 'Brand awareness', scriptVersions: [], refinePrompt: '', videoForceTyped: false, videoBrief: '', videoGenerating: false, videoConcept: null, conceptRoutes: [], prodDuration: '30s', scriptPhase: 'concept' });
    await I.generateVideo(); await wait(700);
    const cp = prompts[0] || '';
    check('C4: the concept prompt asks for a "stake" field (what the PEOPLE IN THE FILM win or lose), in the JSON shape too, and bans a marketing reason', /"stake": what is won or lost for the PEOPLE IN THE FILM/.test(cp) && /"stake": string, "hook": string/.test(cp) && /never a marketing reason such as/.test(cp), cp.slice(-1200));
    check('C4: the limb rule carries its examples and is aimed at the four moments (a packet or hand to a cheek)', /for example a packet or a hand pressed to a cheek/.test(cp) && /none of them may be a hand, an arm or an object touching or crossing a face/.test(cp));
    check('C4: the stake is parsed and kept on every route and the working concept, and shown first on the cards', I.state.videoConcept.stake === 'STAKE-X she loses the one test she has trusted for fifty years.' && I.state.conceptRoutes.every(r => /^STAKE-X/.test(r.stake)) && /STAKE-X/.test(document.body.innerText) && /STAKE/.test(document.body.innerText), JSON.stringify(I.state.videoConcept).slice(0, 300));
    check('C4: the turn must be a visible reversal, never something that gently stops or quietly fades', /The "turn" is a VISIBLE REVERSAL by a person or an object/.test(cp) && /never something that gently stops, quietly fades/.test(cp));
    check('C4: at least one beat is a fast visible action', /At least one of the concept beats is a fast visible action/.test(cp));
    check('C4: the limb rule is in the concept prompt (B3)', cp.indexOf(I.LIMB_RULE) > 0 && /never write an arm or a hand crossing a face/.test(cp));
    check('C4: the A5 filmable rule and the four-field ask are still there, and the JSON shape still closes the prompt', /ONE camera can film in ONE continuous shot of ONE place/.test(cp) && /"hook" — what the viewer sees/.test(cp) && /Return ONLY JSON[\s\S]*exactly 3 routes/.test(cp) && cp.indexOf('STAKE') < cp.indexOf('Return ONLY JSON'));

    // ---- C3: the full-script writer, a concept with a voiceover
    const w = await writer(concept(VO));
    check('C3: the writer is told the concept voiceover is the spine and is what the speech budget is spent on', /THE CONCEPT’S VOICEOVER IS THE FILM’S SPINE: its sentences, in their order/.test(w) && /inside the speech budget above/.test(w), w.slice(-1800));
    check('C3: the sign-off scene must speak, with the pack sharp and in the same place, and any life comes from what is IN the frame: it must NOT ask for a push-in, zoom or drift (the render holds that shot locked and still on purpose)',
      /THE SIGN-OFF SCENE SPEAKS:/.test(w) && /never write a push-in, zoom or camera drift on the pack/.test(w) && /a hand takes the pack or pours from it/.test(w) && /sharp, fully in view and in the same place/.test(w) && /"camera" cell as a locked-off hold on the pack/.test(w) && !/SPEAKS AND MOVES/.test(w)
      && !/something in its frame moves \(a hand takes or pours, a slow push-in/.test(w), w.slice(w.indexOf('THE SIGN-OFF'), w.indexOf('THE SIGN-OFF') + 700));
    check('C3: a "quick cuts" beat must name each action', /rapid sequence \(quick cuts of several different actions\), the scene’s visual must name each of those actions in order/.test(w));
    check('C3: the limb rule is in the writer prompt, with the line that a concept moment needing it keeps the moment and changes the framing', w.indexOf(I.LIMB_RULE) > 0 && /keep the moment and change the framing/.test(w));
    check('C4: the writer is told the stake as what the film must make felt, and it is NOT in the list of moments to deliver as scenes', /What is at stake for the people in this film, which it must make the viewer feel: STAKE-X she loses the one test/.test(w) && !/(^|; )stake: /.test(w) && w.indexOf('STAKE-X') > w.indexOf('memorable moment:') && w.indexOf('What is at stake') > w.indexOf('The first scene must show the hook'), w.slice(w.indexOf('own entertainment'), w.indexOf('own entertainment') + 900));
    const bi = w.indexOf('STRICT SPEECH BUDGET'), si = w.indexOf('THE CONCEPT’S VOICEOVER'), ri = w.indexOf('Return ONLY JSON');
    check('C3: the delivery rules sit AFTER the speech budget note and BEFORE the JSON shape (so the budget does not have the last word)', bi > 0 && si > bi && ri > si, [bi, si, ri]);
    check('C3: the shared VISUAL_RULES text is unchanged (no limb or voiceover rule inside it)', !/Keep limbs safe/.test(I.VISUAL_RULES) && !/SPINE/.test(I.VISUAL_RULES));
    check('C3: everything the writer was told before is still there (the entertainment lines, the pack-shot sign-off, the native-script rule)', /This concept’s own entertainment/.test(w) && /The film MUST include a pack-shot sign-off/.test(w) && /native script of its language/.test(w));

    // ---- a concept with no voiceover: no spine sentence, the rest stays
    const w1 = await writer(concept(VO, true));
    check('a concept with the four moments but NO stake gets no stake sentence (an older concept\'s prompt is as before)', !/What is at stake/.test(w1) && /own entertainment/.test(w1));
    // a refine re-sends the stake with the other fields so it is kept
    prompts.length = 0; reply = null;
    I.setState({ scriptVersions: [{ v: 1, logline: 'x' }], refinePrompt: 'funnier', videoGenerating: false, videoConcept: concept(VO), conceptRoutes: [concept(VO)], conceptRoute: 0 });
    await I.generateVideo(); await wait(500);
    check('a refine re-sends the current route WITH its stake so it is kept', /"stake":"STAKE-X she loses/.test(prompts[0] || ''), (prompts[0] || '').slice(0, 500));
    const w2 = await writer(concept(''));
    check('a concept with no voiceover gets no spine sentence but keeps the sign-off, sequence and limb rules', !/FILM’S SPINE/.test(w2) && /SIGN-OFF SCENE SPEAKS:/.test(w2) && /rapid sequence/.test(w2) && w2.indexOf(I.LIMB_RULE) > 0);

    // ---- a wordless film (budget 0): no speech rules at all
    I.voBudget = () => 0;
    const w3 = await writer(concept(VO));
    check('a wordless film gets NO voiceover-spine and NO spoken sign-off rule, and still gets the sequence and limb rules', !/FILM’S SPINE/.test(w3) && !/SIGN-OFF SCENE SPEAKS/.test(w3) && /rapid sequence/.test(w3) && w3.indexOf(I.LIMB_RULE) > 0);
    I.voBudget = real.voBudget;

    // ---- a film written from a provocation keeps the provocation's own sound language: only the two picture rules
    const realProv = I.provMode; I.provMode = () => true;
    const dp = I.deliveryRulesText(concept(VO));
    check('a provocation film gets NO voiceover-spine and NO spoken sign-off rule (its own sound language rules), only the sequence and limb rules', !/SPINE/.test(dp) && !/SIGN-OFF SCENE SPEAKS/.test(dp) && /rapid sequence/.test(dp) && dp.indexOf(I.LIMB_RULE) >= 0, dp);
    I.provMode = realProv;

    // ---- C5: the single-scene rewrite
    prompts.length = 0; reply = null;
    const row = { no: 1, tc: '0–6s', visual: 'A drop rolls down a plate.', camera: 'macro', dialogue: '', supr: '', audio: [] };
    I.setState({ fullScript: [row, { no: 2, tc: '6–15s', visual: 'She sips.', audio: [] }], scriptStatus: 'drafted', rewritingScene: null, videoConcept: concept(VO) });
    await I.rewriteScene(0)(); await wait(400);
    const rw = prompts[0] || '';
    check('C5: a rewritten scene is told the limb rule, after the shared rules', /Rewrite ONE scene/.test(rw) && rw.indexOf(I.LIMB_RULE) > rw.indexOf('One scene = one frame'), rw.slice(0, 300));
    // the whole-script rework (a note from the person) writes pictures too: it gets the limb rule, but NOT the speech rules (the person's note governs those)
    prompts.length = 0; reply = null;
    I.setState({ scriptRefine: 'make the second scene livelier', scriptReworking: false });
    await I.reworkScript(); await wait(400);
    const rk = prompts[0] || '';
    check('the whole-script rework is told the limb rule before its JSON shape, and gets no voiceover-spine or sign-off-speech rule', /Revise this/.test(rk) && rk.indexOf(I.LIMB_RULE) > rk.indexOf('STRICT SPEECH BUDGET') && rk.indexOf(I.LIMB_RULE) < rk.indexOf('Return ONLY JSON') && !/FILM’S SPINE/.test(rk) && !/SIGN-OFF SCENE SPEAKS/.test(rk), rk.slice(-700));
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    Object.assign(I, { complete: real.complete, needBrand: real.needBrand, brandPreamble: real.brandPreamble, learningContext: real.learningContext, showToast: real.showToast, voBudget: real.voBudget }); window.fetch = real.fetch;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
