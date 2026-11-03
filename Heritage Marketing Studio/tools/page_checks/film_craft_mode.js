// film_craft_mode.js -- the CRAFT MODE switch and scorecard on the page (FILM_CRAFT_LAYER_PLAN.md, Phase A), driven on the REAL page with the model (this.complete) and the network stubbed.
//
// Why: craft mode must be OFF by default and change NOTHING when off (same concept prompt, same writer prompt, no craft flag on the call, no scorecard row). When ON it must ask the concept
// writer for the five craft lines, send craft:true on the concept and script calls only, show the lines on the route card, hand them to the script writer, keep them across a refine, and show a
// scorecard row in "Before you approve" that posts the concept and script to /film-score and renders what comes back (advice only: nothing blocks).
//
// How to run: start the studio, open http://localhost:8000/app (or your port), run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 500 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.craftOpts === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.craftOpts === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance (reload the page, wait 3 s, run again)'] });
  const real = { complete: I.complete, needBrand: I.needBrand, brandPreamble: I.brandPreamble, learningContext: I.learningContext, showToast: I.showToast, fetch: window.fetch, apiCall: I.apiCall };
  const prompts = [], opts = [], calls = []; let reply = null, scoreReply = null;
  I.needBrand = () => true; I.brandPreamble = () => 'PREAMBLE'; I.learningContext = async () => ''; I.showToast = () => {};
  window.fetch = async () => new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
  I.complete = async (p, o) => { prompts.push(String(p)); opts.push(o || {}); if (reply === null) throw new Error('stop'); return reply; };
  I.apiCall = async (path, body) => { calls.push({ path, body }); if (path === '/film-score') return scoreReply; return { ok: false, data: {} }; };
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const txt = () => document.body.innerText;
  const route = (n, craft) => ({ name: 'Route ' + n, rationale: 'Why', logline: 'Logline ' + n, duration: '30s', vo: 'Voice ' + n, hook: 'HOOK-' + n, surprise: 'SURP-' + n, turn: 'TURN-' + n, memorable: 'MEM-' + n,
    ...(craft ? { message: 'MSG-' + n + ' pure milk', move: 'MOVE-' + n + ' she tests it at the door', device: 'DEV-' + n + ' the sniff', line: 'LINE-' + n + ' pehle test', cast_idea: 'CAST-' + n + ' a real dadi' } : {}),
    scenes: [{ t: '0–5s', title: 'B1', desc: 'd1' }, { t: '5–10s', title: 'B2', desc: 'd2' }, { t: '10–20s', title: 'B3', desc: 'd3' }, { t: '20–30s', title: 'B4', desc: 'd4' }] });
  const base = { screen: 'video', vTab: 'film', videoStep: 'scripting', videoObjective: 'Brand awareness', scriptVersions: [], refinePrompt: '', videoForceTyped: false, videoBrief: '', videoGenerating: false, videoConcept: null, conceptRoutes: [], conceptRoute: 0, scriptWriting: false, fullScript: null, scriptStatus: 'none' };
  try {
    // 1. OFF (the default): nothing changes
    try { localStorage.removeItem('tms.craft'); } catch (e) {}
    I.setState({ ...base, craftOn: false, craftScore: null });
    check('craft mode is off by default and sends no flag', JSON.stringify(I.craftOpts()) === '{}' && I.craftConceptText() === '' && I.craftShape() === '');
    reply = JSON.stringify({ routes: [route(1, false), route(2, false), route(3, false)] });
    await I.generateVideo(); await wait(700);
    const off = prompts[0] || '';
    check('OFF: the concept prompt has no craft lines and the call carries no craft flag', !/"cast_idea"/.test(off) && !/five craft lines/.test(off) && opts[0] && opts[0].craft === undefined && opts[0].film === true, JSON.stringify(opts[0]));
    check('OFF: no craft scorecard row in "Before you approve" and no craft toggle state', !/Craft scorecard/.test(txt()));

    // 2. ON: the concept asks for five more lines and sends craft:true
    I.toggleCraft(); await wait(200);
    check('toggling sets craftOn and remembers it in this browser', I.state.craftOn === true && (() => { try { return localStorage.getItem('tms.craft') === '1'; } catch (e) { return true; } })());
    prompts.length = 0; opts.length = 0;
    I.setState({ ...base, craftOn: true });
    reply = JSON.stringify({ routes: [route(1, true), route(2, true), route(3, true)] });
    await I.generateVideo(); await wait(700);
    const on = prompts[0] || '';
    check('ON: the concept prompt asks for message, move, device, line and cast_idea, in the JSON shape too',
      /"message" — the single thing the film says/.test(on) && /"move"/.test(on) && /"device"/.test(on) && /"cast_idea"/.test(on) && /"memorable": string, "message": string, "move": string, "device": string, "line": string, "cast_idea": string/.test(on), on.slice(-500));
    check('ON: the concept call carries craft:true (and is still a film call)', opts[0] && opts[0].craft === true && opts[0].film === true, JSON.stringify(opts[0]));
    check('ON: the rest of the concept prompt is as before (three routes, the four entertainment fields)', /Propose THREE genuinely different creative routes/.test(on) && /exactly 3 routes/.test(on) && /"hook" — what the viewer sees/.test(on));
    check('ON: the five lines survive parsing for the working concept and every route', I.state.videoConcept.device.startsWith('DEV-1') && I.state.conceptRoutes.length === 3 && I.state.conceptRoutes[2].cast_idea.startsWith('CAST-3'));
    check('ON: the route cards show the craft lines', /DEV-1/.test(txt()) && /MOVE-2/.test(txt()) && /CAST-3/.test(txt()) && /MSG-1/.test(txt()));

    // 3. switching route keeps ITS lines; a refine remembers them
    I.pickConceptRoute(1)(); await wait(400);
    check('picking another route makes ITS craft lines the concept\'s', I.state.videoConcept.line.startsWith('LINE-2'));
    prompts.length = 0; opts.length = 0; reply = JSON.stringify({ routes: [route(2, true), route(2, true), route(2, true)] });
    I.setState({ refinePrompt: 'warmer' });
    await I.generateVideo(); await wait(500);
    check('a refine hands the writer the five lines to keep', /"device":"DEV-2/.test(prompts[0] || '') && /"cast_idea":"CAST-2/.test(prompts[0] || ''), (prompts[0] || '').slice(0, 600));

    // 4. the script writer is told, and the call carries craft:true
    I.pickConceptRoute(0)(); await wait(300);
    prompts.length = 0; opts.length = 0; reply = null;
    I.setState({ scriptWriting: false, fullScript: null, scriptStatus: 'concept' });
    await I.writeFullScript(); await wait(500);
    const w = prompts[0] || '';
    check('the script writer is told the route\'s craft: device, line, casting, move, message', /This route’s craft: /.test(w) && /device: DEV-2/.test(w) && /line: LINE-2/.test(w) && /casting: CAST-2/.test(w) && /move: MOVE-2/.test(w) && /visible and audible, not described/.test(w), w.slice(0, 300));
    check('the script call carries craft:true', opts[0] && opts[0].craft === true && opts[0].film === true, JSON.stringify(opts[0]));
    check('and the craft text sits with the concept, before the length instructions', w.indexOf('This route’s craft') > 0 && w.indexOf('This route’s craft') < w.indexOf('The finished film is'));
    I.setState({ craftOn: false });
    prompts.length = 0; opts.length = 0; I.setState({ scriptWriting: false, fullScript: null });
    await I.writeFullScript(); await wait(500);
    check('OFF again: the writer prompt still carries the craft lines of a concept that has them (they are the concept\'s own) but the call sends no flag', opts[0] && opts[0].craft === undefined, JSON.stringify(opts[0]));
    I.setState({ craftOn: true });

    // 5. the scorecard row
    const rows = [{ no: 1, visual: 'Kitchen', dialogue: 'Pehle test' }, { no: 2, visual: 'Fridge', dialogue: '' }];
    I.setState({ fullScript: rows, scriptStatus: 'ready', craftScore: null, scriptPhase: 'script' }); await wait(500);
    check('ON: the "Craft scorecard" row appears in "Before you approve" with a Score button', /Craft scorecard/.test(txt()) && /Score the film/.test(txt()), txt().slice(0, 200));
    scoreReply = { ok: true, data: { model: true, total: 13, max: 21, scored: 7, strongest: 'message', weakest: 'device', summary: 'A warm clear film.', suggestion: 'Give her a repeatable gesture.',
      tests: [['message', 'One clear message', 3], ['hook', 'Attention hook', 2], ['moment', 'One memorable moment', 3], ['dramatised', 'The proposition as an event', 1], ['device', 'A memorable device', 0], ['performance', 'Performance and casting are the idea', 2], ['original', 'Original', null]].map(([id, label, score]) => ({ id, label, score, reason: 'R-' + id })), notes: [] } };
    await I.runCraftScore(); await wait(500);
    const c = calls.find(x => x.path === '/film-score');
    check('the scorecard posts the concept (with the craft lines) and the script to /film-score', c && c.body.concept && c.body.concept.device.startsWith('DEV-2') && c.body.scenes.length === 2 && c.body.film === true, JSON.stringify(c && Object.keys(c.body)));
    check('it shows the total, the summary, each test with its reason and the suggestion', /13 of 21/.test(txt()) && /A warm clear film/.test(txt()) && /R-device/.test(txt()) && /Give her a repeatable gesture/.test(txt()) && /0\/3 A memorable device/.test(txt()), txt().slice(0, 300));
    check('an unscored test shows a dash, not a zero', /–\/3 Original/.test(txt()));
    scoreReply = { ok: false, data: { detail: 'The scorecard could not be understood. Try again.' } };
    const before = I.state.craftScore; await I.runCraftScore(); await wait(300);
    check('a failed score leaves the earlier scorecard in place and does not stick the button', I.state.craftScore === before && I.state.craftBusy === false);
    // 6. the director's read: craft:true goes with it only in craft mode, quiet notes read as notes and never as the first finding
    const bmReply = { ok: true, data: { model: true, summary: 'S', time_passing: false, hero_object: '', turn_scene: 1, carrier_scene: 2, engagement: { risk: 'low' }, notes: [],
      scenes: rows.map(r => ({ no: r.no, purpose: 'p', intensity: 1, time_mode: 'continuous', marker: '', beat: 'b' + r.no, hero: false, place: 'kitchen', energy: 1, change: 'x', sequence: false, actions: [] })),
      findings: [{ kind: 'flat-energy', scene: 2, note: 'REALFINDING-x' }, { kind: 'slow-hook', scene: 1, quiet: true, note: 'QUIETNOTE-y' }] } };
    I.apiCall = async (path, body) => { calls.push({ path, body }); return path === '/film-direct' ? bmReply : { ok: false, data: {} }; };
    calls.length = 0; I.setState({ videoBeatMap: null, craftOn: true });
    await I.runBeatMap(); await wait(500);
    const bmOn = calls.find(x => x.path === '/film-direct');
    check('craft mode ON: the director read call carries craft:true', bmOn && bmOn.body.craft === true && bmOn.body.film === true, JSON.stringify(bmOn && Object.keys(bmOn.body)));
    check('"Before you approve" leads with the real finding, not the quiet note', /Boredom risk: low — REALFINDING-x/.test(txt().replace(/\s+/g, ' ')), txt().replace(/\s+/g, ' ').slice(txt().replace(/\s+/g, ' ').indexOf('Boredom') - 20, txt().replace(/\s+/g, ' ').indexOf('Boredom') + 200));
    check('the quiet note reads as a note, in the director read', /A note: QUIETNOTE-y/.test(txt()) && /• REALFINDING-x/.test(txt()));
    calls.length = 0; I.setState({ videoBeatMap: null, craftOn: false });
    await I.runBeatMap(); await wait(500);
    const bmOff = calls.find(x => x.path === '/film-direct');
    check('craft mode OFF: the director read call carries no craft flag', bmOff && bmOff.body.craft === undefined, JSON.stringify(bmOff && bmOff.body.craft));
    I.setState({ craftOn: true, videoBeatMap: null });
    // 7. W10: the learning log keeps the scorecard and the craft lines with the decision
    I.apiCall = async (path, body) => { calls.push({ path, body }); return path === '/learning-decision' ? { ok: true, data: { status: null } } : { ok: false, data: {} }; };
    I.setState({ videoConcept: { ...route(1, true) }, craftScore: { total: 13, max: 21, weakest: 'device', tests: [{ id: 'message', score: 3 }, { id: 'device', score: 0 }] } });
    const fm = I.filmDecisionMeta();
    check('the film decision meta carries the scorecard, the craft lines and the hook', fm && fm.craft_score.total === 13 && fm.craft_score.tests[1][0] === 'device' && fm.craft_lines.device.startsWith('DEV-1') && fm.entertain.hook === 'HOOK-1', JSON.stringify(fm));
    calls.length = 0;
    I.openDecision('film', 'Cut X', { body: 'SCRIPT', brief: 'B', meta: fm })(); I.setDecisionChoice('approve')(); await I.submitDecision(); await wait(200);
    const ld = calls.find(x => x.path === '/learning-decision');
    check('approving sends the meta with the decision', ld && ld.body.meta && ld.body.meta.craft_score.max === 21 && ld.body.decision === 'approve' && ld.body.body === 'SCRIPT', JSON.stringify(ld && ld.body));
    calls.length = 0;
    I.setState({ videoConcept: { logline: 'old', scenes: [] }, craftScore: null });
    check('a concept with nothing craft-related gives no meta', I.filmDecisionMeta() === null);
    I.openDecision('film', 'Cut Y', { body: 'S2', brief: 'B' })(); I.setDecisionChoice('approve')(); await I.submitDecision(); await wait(200);
    const ld2 = calls.find(x => x.path === '/learning-decision');
    check('and then the decision is exactly what it was (no meta key)', ld2 && !('meta' in ld2.body), JSON.stringify(ld2 && Object.keys(ld2.body)));
    I.setState({ craftOn: true });
    // 8. the longer page timeout belongs to craft-mode writing calls only and is never sent to the server
    I.setState({ craftOn: true });
    check('craft mode ON: the writing calls get a 120 s page limit and the craft flag', I.craftCall().craft === true && I.craftCall().timeoutMs === 120000);
    I.setState({ craftOn: false });
    check('craft mode OFF: the writing calls get nothing extra (the usual 45 s)', JSON.stringify(I.craftCall()) === '{}' && I.MODEL_TIMEOUT_MS === 45000);
    const realClaude = window.claude; let sent = null;
    window.claude = { complete: async (c) => { sent = c; return 'ok'; } };
    const got = await real.complete.call(I, 'P', { film: true, craft: true, timeoutMs: 120000 });
    window.claude = realClaude;
    check('the page-only timeoutMs is not sent to the server, the rest is', got === 'ok' && sent && sent.timeoutMs === undefined && sent.craft === true && sent.film === true && sent.messages[0].content === 'P', JSON.stringify(sent));
    I.setState({ craftOn: true });
    // 9. the three routes differ in MOVE and stand on the platform (3 Nov)
    I.setState({ craftOn: true });
    const withP = I.craftConceptText(true), noP = I.craftConceptText(false);
    check('with a platform: all three routes stand on it and the messaging house, differ ONLY in move, and replace the old angle suggestion', /stand on the idea platform named above/.test(withP) && /messaging house/.test(withP) && /differ ONLY in their "move"/.test(withP) && /REPLACES the earlier suggestion/.test(withP) && /every route uses it/.test(withP), withP.slice(600, 1100));
    check('without a platform: the same single message and the same move rule, no platform wording', /serve the same single message/.test(noP) && /differ ONLY in their "move"/.test(noP) && !/idea platform named above/.test(noP));
    check('both keep: the genre from the direction, feeling AND proof, no invented claims, cover the logo, numbers agree, original only', [withP, noP].every(x => /keep it: they differ in move, not in genre/.test(x) && /BOTH the feeling and the proof/.test(x) && /Never state or imply that the product causes growth, strength, health/.test(x) && /at its own scope/.test(x) && /Prefer proof that is SHOWN/.test(x) && /name its final number once/.test(x) && /ONE region and language/.test(x) && /Cover the logo/.test(x) && /number, age and quantity/.test(x) && /Original only/.test(x)));
    check('the five craft lines are still asked for and the text is bounded (under 3,800 characters)', /"message" \u2014 the single thing the film says/.test(withP) && /"cast_idea"/.test(withP) && withP.length < 3800, withP.length);
    I.setState({ craftOn: false });
    check('craft mode OFF: the route text is empty', I.craftConceptText(true) === '' && I.craftConceptText(false) === '');
    prompts.length = 0; opts.length = 0; reply = JSON.stringify({ routes: [route(1, true), route(2, true), route(3, true)] });
    I.setState({ ...base, craftOn: true, videoStandsOn: { text: 'The Strength Count: a running tally of the morning pour', has_platform: true }, videoForceTyped: false });
    await I.generateVideo(); await wait(600);
    check('generateVideo passes the platform flag through: the platform variant is in the prompt', /stand on the idea platform named above/.test(prompts[0] || '') && /The idea platform this film stands on: "The Strength Count/.test(prompts[0] || ''), (prompts[0] || '').slice(-900));
    prompts.length = 0; I.setState({ ...base, craftOn: true, videoStandsOn: null });
    await I.generateVideo(); await wait(600);
    check('and with no platform it is the single-message variant', /serve the same single message/.test(prompts[0] || '') && !/idea platform named above/.test(prompts[0] || ''));
    I.setState({ craftOn: true, videoStandsOn: null });
    I.toggleCraft(); await wait(300);
    check('turning craft mode off hides the row and clears the scorecard', !/Craft scorecard/.test(txt()) && I.state.craftScore === null);
  } catch (e) {
    check('no exception', false, String(e && e.stack || e));
  } finally {
    Object.assign(I, { complete: real.complete, needBrand: real.needBrand, brandPreamble: real.brandPreamble, learningContext: real.learningContext, showToast: real.showToast, apiCall: real.apiCall });
    window.fetch = real.fetch;
    try { localStorage.removeItem('tms.craft'); } catch (e) {}
    I.setState({ craftOn: false, craftScore: null });
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})();
