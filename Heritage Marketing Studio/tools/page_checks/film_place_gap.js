// film_place_gap.js -- the "one kitchen / slow hook" gap (FILM_PHASE5_AND_PLACE_PLAN.md G1, G2), driven on the REAL page with the network and the model stubbed.
//
// G1: a script row may carry its own `place`. Its frame is drawn with `Location: <place>` INSTEAD of the film-wide line and without the film's location photo; the fingerprint and the recipe change when it
//     changes; a scene with NO place is drawn exactly as before; the writer and the rewrite are told about it; editing it is a drawing choice (an approved script stays approved); a rework keeps it only
//     while the picture is unchanged.
// G2: the director's `slow-hook` and `same-place` findings get one button each that rewrites the right scene with a direction, only when pressed.
//
// How to run: start the studio, open http://localhost:8000/app (or your port), run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 500 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.findingAction === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.findingAction === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const real = { fetch: window.fetch, toast: I.showToast, confirm: window.confirm, complete: I.complete, needBrand: I.needBrand, brandPreamble: I.brandPreamble, learningContext: I.learningContext, rewrite: I.rewriteScene };
  const J = (x) => new Response(JSON.stringify(x), { status: 200, headers: { 'Content-Type': 'application/json' } });
  window.fetch = async () => J({});
  I.showToast = () => {}; let confirmAnswer = true; const asked = []; window.confirm = (m) => { asked.push(String(m)); return confirmAnswer; };
  I.needBrand = () => true; I.brandPreamble = () => 'PREAMBLE'; I.learningContext = async () => '';
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const txt = () => document.body.innerText;
  const btn = (re) => [...document.querySelectorAll('button')].find(x => re.test(x.textContent.trim()));
  const KITCHEN = 'A small Hyderabad kitchen before dawn, a steel vessel on the stove and a milk pack on the counter.';
  const rows = [1, 2, 3, 4, 5].map(n => ({ no: n, tc: (n * 6 - 6) + '–' + (n * 6) + 's', visual: 'Scene ' + n + ' shows something different.', audio: [] }));
  try {
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'shootboard', scriptPhase: 'script', scriptStatus: 'approved', prodDuration: '30s', videoAssetsLoaded: true, castRefUrl: '/media/cast.png', videoCharacters: 'A boy of nine.',
      videoLocationLine: KITCHEN, videoPlateChoice: 'plate-1', fullScript: rows, shoot: {}, sceneFrames: {}, videoConcept: { logline: 'L', proposition: 'P', vo: '', hook: 'A drop of milk rolls down a slanted steel plate.', scenes: [] }, videoBeatMap: null, filmReview: null });
    await wait(500);

    // ---- G1: the frame machinery ----
    const base = I.frameRecipe(1, 0), baseParts = I.frameParts(1, 0), baseBody = I.frameBody(1, 0).body, base0 = I.frameRecipe(0, 0), baseParts0 = I.frameParts(0, 0);
    check('a scene with NO place is drawn with the film-wide location (pack mentions stripped as before) and the picked location photo', I.sceneLocation(rows[1]) === I.locationText() && /Location: A small Hyderabad kitchen/.test(baseBody.prompt) && !/milk pack/.test(baseBody.prompt) && baseBody.plate_id === 'plate-1' && baseBody.use_plate === undefined, JSON.stringify({ p: baseBody.prompt.slice(0, 160), plate: baseBody.plate_id }));
    const lab = rows.map((r, i) => (i === 1 ? { ...r, place: 'A gleaming Heritage dairy lab at dawn, stainless pipework and a technician in a hairnet, a milk pack on the bench.' } : r));
    I.setState({ fullScript: lab }); await wait(300);
    const lb = I.frameBody(1, 0).body;
    check('a scene WITH a place is drawn with ITS place instead of the film-wide line (pack mentions stripped), and without the film\'s location photo', /Location: A gleaming Heritage dairy lab at dawn/.test(lb.prompt) && !/Hyderabad kitchen/.test(lb.prompt) && !/milk pack/.test(lb.prompt) && lb.plate_id === undefined && lb.use_plate === false, JSON.stringify({ p: lb.prompt.slice(0, 200), plate: lb.plate_id, up: lb.use_plate }));
    check('the cast reference still anchors the faces (the place changes only the words and the photo)', lb.reference_url === '/media/cast.png');
    const sib = I.frameBody(0, 0).body;
    check('the scenes next to it are untouched: still the film-wide location and the photo', /Location: A small Hyderabad kitchen/.test(sib.prompt) && sib.plate_id === 'plate-1');
    check('the recipe and the fingerprint change for the scene with a place and ONLY for that scene (scene 1\'s recipe is what it was)', I.frameRecipe(1, 0) !== base && I.frameParts(1, 0).loc !== baseParts.loc && I.frameRecipe(0, 0) === base0 && I.frameParts(0, 0).loc === baseParts0.loc, JSON.stringify([base, I.frameRecipe(1, 0), base0, I.frameRecipe(0, 0)]));
    check('a scene with no place has exactly the same fingerprint `loc` part as before this change (frames drawn earlier keep an honest reason)', I.frameParts(0, 0).loc === (() => { let h = 5381; const t = JSON.stringify([I.locationText()]); for (let i = 0; i < t.length; i++) h = ((h * 33) ^ t.charCodeAt(i)) >>> 0; return h.toString(36); })());

    // extra shots of that scene inherit the place
    const labShots = lab.map((r, i) => (i === 1 ? { ...r, shots: [{ visual: 'Close on the vial.', secs: 2, job: 'insert', why: 'x', shot_size: 'detail' }] } : r));
    I.setState({ fullScript: labShots }); await wait(300);
    check('an extra shot of that scene is drawn in the same place', /Location: A gleaming Heritage dairy lab/.test(I.frameBody(1, 1).body.prompt) && I.frameBody(1, 1).body.use_plate === false);

    // editing the place makes the drawn frame out of date, for the right reason
    I.setState({ fullScript: lab, sceneFrames: { 1: { status: 'done', url: '/media/f1.jpg', sig: 'x', recipe: I.frameRecipe(1, 0), parts: I.frameParts(1, 0) } } }); await wait(300);
    check('a frame drawn in the lab is current', I.staleSlots().length === 0);
    I.setState({ fullScript: lab.map((r, i) => (i === 1 ? { ...r, place: 'A busy street outside the Heritage gate at dawn.' } : r)) }); await wait(400);
    check('changing that scene\'s place marks ITS frame out of date with the reason "the Location line or this scene\'s place"', I.staleSlots().length === 1 && I.staleSlots()[0].key == 1 && /the Location line or this scene.s place/.test(I.staleWhyText(1, I.staleSlots()[0].f, 0)), JSON.stringify(I.staleSlots().map(x => I.staleWhyText(x.idx, x.f, x.k))));
    I.setState({ fullScript: rows, sceneFrames: {} });

    // ---- the script table and the cards ----
    I.setState({ videoStep: 'scripting', scriptPhase: 'script', fullScript: lab }); await wait(600);
    const input = document.querySelector('input[data-cell="place"][data-row="1"]');
    check('the script table has a Place input per scene, filled for the scene that has one', !!input && /dairy lab/.test(input.value) && document.querySelectorAll('input[data-cell="place"]').length === 5, input && input.value);
    const ev = (idx, field, value) => ({ target: { getAttribute: (n) => (n === 'data-row' ? String(idx) : field), value } });
    I.editSceneChoice(ev(3, 'place', 'The street outside the gate')); await wait(300);
    check('typing a place sets it on that scene and an APPROVED script stays approved (it is a drawing choice, like the shot size)', I.state.fullScript[3].place === 'The street outside the gate' && I.state.scriptStatus === 'approved');
    I.editSceneChoice(ev(3, 'place', '')); await wait(300);
    check('emptying the place removes the key (the scene is back in the film\'s location)', !('place' in I.state.fullScript[3]));
    I.setState({ videoStep: 'shootboard' }); await wait(600);
    check('the Shoot Board card of the scene says where it is drawn', /Drawn in: A gleaming Heritage dairy lab/.test(txt()), (txt().match(/Drawn in[^\n]*/) || ['none'])[0]);

    // ---- a rework keeps a place only while the picture is unchanged ----
    const newRows = [{ no: 1, visual: 'Scene 1 shows something different.' }, { no: 2, visual: 'Scene 2 shows something different.' }, { no: 3, visual: 'CHANGED scene 3.' }, { no: 4, visual: 'Scene 4 shows something different.' }, { no: 5, visual: 'Scene 5 shows something different.' }];
    const old = lab.map((r, i) => (i === 2 ? { ...r, place: 'A school gate' } : r));
    const kept = I.keepSceneExtras(newRows, old);
    check('after a rework the place of an unchanged scene is carried over; the place of a scene whose picture changed is dropped', kept[1].place === lab[1].place && !('place' in kept[2]), JSON.stringify(kept.map(r => r.place || null)));
    check('prompts built from the script do not carry the place (it is a drawing choice, restored after a rework)', !('place' in I.scriptForPrompt(lab)[1]));

    // ---- the writer and the rewrite are told ----
    const prompts = []; I.complete = async (p) => { prompts.push(String(p)); throw new Error('stop'); };
    I.setState({ scriptWriting: false, fullScript: null, scriptStatus: 'concept', videoStep: 'scripting', scriptPhase: 'concept', videoConcept: { name: 'R', logline: 'L', proposition: 'P', vo: 'Some voiceover words here for the film.', scenes: [{ t: '0–6s', title: 'a', desc: 'b' }] } });
    await I.writeFullScript(); await wait(300);
    const w = prompts[0] || '';
    check('the full-script writer is told to give a scene OUTSIDE the main location its own place, to leave it empty otherwise and not to invent places; the JSON shape has the field', /PLACE: most scenes happen in the film.s main location and need no place/.test(w) && /a one-room film stays one room/.test(w) && /"place":"empty, or where this scene happens only when it is NOT the main location"/.test(w), w.slice(w.indexOf('PLACE'), w.indexOf('PLACE') + 300));
    prompts.length = 0; I.setState({ fullScript: lab, scriptStatus: 'drafted', rewritingScene: null });
    await I.rewriteScene(1, 'Move it to the street.')(); await wait(300);
    const rw = prompts[0] || '';
    check('a rewrite knows the scene\'s place, carries the direction, and asks for a place back', /This scene is set in "A gleaming Heritage dairy lab/.test(rw) && /DIRECTION FOR THIS REWRITE \(follow it\): Move it to the street\./.test(rw) && /"place":""/.test(rw), rw.slice(-700));
    prompts.length = 0; await I.rewriteScene(0)(); await wait(300);
    check('a rewrite of a scene with no place and no direction says neither', !/This scene is set in/.test(prompts[0] || '') && !/DIRECTION FOR THIS REWRITE/.test(prompts[0] || ''));
    // what happens to the place when the model's rewrite comes back
    const reply = (obj) => { I.complete = async () => JSON.stringify(obj); };
    I.setState({ fullScript: lab, rewritingScene: null });
    reply({ no: 2, tc: '6–12s', visual: 'A technician reads a vial in the lab.', camera: 'medium', dialogue: '', supr: '', place: 'The plant floor at dawn', audio: [] });
    await I.rewriteScene(1)(); await wait(300);
    check('a rewrite that returns a place sets it', I.state.fullScript[1].place === 'The plant floor at dawn');
    reply({ no: 2, tc: '6–12s', visual: 'Back in the kitchen the boy drinks.', camera: 'medium', dialogue: '', supr: '', place: '', audio: [] });
    await I.rewriteScene(1)(); await wait(300);
    check('a rewrite that returns an EMPTY place puts the scene back in the film\'s location', !('place' in I.state.fullScript[1]));
    I.setState({ fullScript: lab, rewritingScene: null });
    reply({ no: 2, tc: '6–12s', visual: 'A different picture entirely.', camera: 'medium', dialogue: '', supr: '', audio: [] });
    await I.rewriteScene(1)(); await wait(300);
    check('a rewrite that returns NO place field for a changed picture drops the old place (it described the old picture)', !('place' in I.state.fullScript[1]));
    I.setState({ fullScript: lab, rewritingScene: null });
    reply({ no: 2, tc: '6–12s', visual: lab[1].visual, camera: 'medium', dialogue: '', supr: '', audio: [] });
    await I.rewriteScene(1)(); await wait(300);
    check('a rewrite that returns the SAME picture and no place field keeps the place', I.state.fullScript[1].place === lab[1].place);
    I.complete = real.complete;

    // ---- G2: the findings get actions ----
    const bmOf = (places, findings) => ({ sig: I.beatSig(), summary: 's', turn_scene: 4, carrier_scene: 5, hero_object: '', time_passing: false, notes: [], transitions: [], engagement: { risk: 'high' }, findings,
      scenes: places.map((pl, i) => ({ no: i + 1, purpose: 'p', intensity: 1, time_mode: 'continuous', place: pl, energy: 1, change: 'c', beat: 'b' + i, sequence: false, actions: [] })), model: true });
    const slow = { kind: 'slow-hook', scene: 1, note: 'The film opens quietly (scene 1).' }, same = { kind: 'same-place', scene: 1, note: '5 neighbouring scenes happen in the same place (kitchen).' };
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'scripting', scriptPhase: 'script', scriptStatus: 'drafted', fullScript: rows, videoConcept: { logline: 'L', proposition: 'P', vo: '', hook: 'A drop of milk rolls down a slanted steel plate.', scenes: [] }, videoBeatMap: bmOf(['kitchen', 'kitchen', 'kitchen', 'kitchen', 'kitchen'], [slow, same]) }); await wait(600);
    const a1 = I.findingAction(slow), a2 = I.findingAction(same);
    check('slow-hook -> rewrite scene 1 with the concept\'s own hook in the direction', a1 && a1.idx === 0 && /Open the film on the concept.s own hook: "A drop of milk rolls down a slanted steel plate"/.test(a1.direction), JSON.stringify(a1));
    I.setState({ videoConcept: { logline: 'L', proposition: 'P', vo: '', scenes: [] } });
    await wait(200);
    check('(no hook in the concept -> no button)', I.findingAction(slow) === null);
    I.setState({ videoConcept: { logline: 'L', proposition: 'P', vo: '', hook: 'A drop of milk rolls down a slanted steel plate.', scenes: [] } }); await wait(200);
    check('same-place over five scenes -> the MIDDLE scene (3), never the first or the sign-off, with a direction that names the place to leave', a2 && a2.idx === 2 && /Rewrite scene 3 in a new place/.test(a2.label) && /somewhere other than "kitchen"/.test(a2.direction), JSON.stringify(a2));
    I.setState({ fullScript: rows.map((r, i) => (i === 2 ? { ...r, place: 'A lab' } : r)) }); await wait(200);
    check('a scene that already has its own place is skipped: the next nearest scene is offered (scene 2)', I.findingAction(same).idx === 1, JSON.stringify(I.findingAction(same)));
    I.setState({ fullScript: rows.map((r, i) => (i === 4 ? { ...r, beat_role: 'brand' } : (i === 1 || i === 2 || i === 3 ? { ...r, place: 'X' } : r))) }); await wait(200);
    check('when every candidate is the first scene, the sign-off or already placed, there is no button', I.findingAction(same) === null);
    I.setState({ fullScript: rows }); await wait(200);

    // the buttons are in the director's read panel and press through to the rewrite
    check('the Director\'s read panel shows both buttons beside their findings', !!btn(/Rewrite the opening on the hook/) && !!btn(/Rewrite scene 3 in a new place/), [...document.querySelectorAll('button')].map(b => b.textContent.trim()).filter(t => /Rewrite/.test(t)).join('|'));
    const rcalls = []; I.rewriteScene = (i, d) => async () => { rcalls.push([i, d]); };
    asked.length = 0; btn(/Rewrite the opening on the hook/).click(); await wait(300);
    check('pressing the hook button rewrites scene 1 with the hook direction (a DRAFT script: no confirm)', rcalls.length === 1 && rcalls[0][0] === 0 && /own hook/.test(rcalls[0][1]) && asked.length === 0, JSON.stringify(rcalls));
    I.setState({ scriptStatus: 'approved' }); await wait(300); confirmAnswer = false; rcalls.length = 0; asked.length = 0;
    btn(/Rewrite scene 3 in a new place/).click(); await wait(300);
    check('on an APPROVED script the button asks first (the frame will be out of date), and a no rewrites nothing', asked.length === 1 && /rewrites scene 3 of an approved script/.test(asked[0]) && rcalls.length === 0, asked.join('|'));
    confirmAnswer = true; btn(/Rewrite scene 3 in a new place/).click(); await wait(300);
    check('and a yes does it, with the place direction', rcalls.length === 1 && rcalls[0][0] === 2 && /somewhere other than "kitchen"/.test(rcalls[0][1]), JSON.stringify(rcalls));
    I.rewriteScene = real.rewrite;
    I.setState({ videoBeatMap: bmOf(['kitchen', 'lab', 'street', 'kitchen', 'kitchen'], [{ kind: 'flat-energy', scene: 1, note: 'Scenes 1 to 3 are all held stills.' }]) }); await wait(400);
    // the shot planner is told THIS scene's place, and the location photo does not count as locking it
    const sbodies = []; window.fetch = async (u, o) => { if (/\/scene-shots/.test(String(u))) { try { sbodies.push(JSON.parse(o.body)); } catch (e) {} return J({ shots: [], master_secs: 6, notes: [], scene_seconds: 6, reason: 'one shot' }); } return J({}); };
    I.setState({ fullScript: rows.map((r, i) => (i === 1 ? { ...r, place: 'A gleaming dairy lab at dawn.' } : r)), videoPlateChoice: 'plate-1', videoLocationLine: KITCHEN, shotsBusy: '' }); await wait(300);
    await I.breakIntoShots(1)(); await wait(300); await I.breakIntoShots(2)(); await wait(300);
    check('Break into shots sends a scene\'s own place as its location and says the location is NOT locked; a scene with no place sends the film\'s line and the lock as before',
      sbodies.length === 2 && /dairy lab/.test(sbodies[0].location_line) && sbodies[0].plate_locked === false && /Hyderabad kitchen/.test(sbodies[1].location_line) && sbodies[1].plate_locked === true, JSON.stringify(sbodies.map(b => [b.location_line.slice(0, 40), b.plate_locked])));
    window.fetch = async () => J({});
    check('a finding with nothing to fix gets no button, and the other findings render as before', !btn(/Rewrite the opening/) && !btn(/in a new place/) && /Scenes 1 to 3 are all held stills/.test(txt()));
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = real.fetch; I.showToast = real.toast; window.confirm = real.confirm; I.complete = real.complete; I.needBrand = real.needBrand; I.brandPreamble = real.brandPreamble; I.learningContext = real.learningContext; I.rewriteScene = real.rewrite;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
