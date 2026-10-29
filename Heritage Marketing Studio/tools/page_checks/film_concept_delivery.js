// film_concept_delivery.js -- the director's read now says what the script KEPT of the concept, and flags a scene that is a RUN of quick actions (FILM_CONSOLIDATED_PLAN.md C6, C7), driven on the
// REAL page with the network stubbed.
//
// Why: the 29 Oct grandmother film's pitched "quick cuts" ritual became one static shot and nothing said so. The page must send the concept with the read, show how many promises were kept (and what
// was flattened), mark a run-of-actions scene on its card, in the director's read and in "Before you approve", and send the beat map to the shot planner so it can plan one shot per action. It also
// pins a defect found on the way: the real read carries its findings at the TOP level (engagement holds only the risk), so "Before you approve" never showed the first finding of a real read.
//
// How to run: start the studio, open http://localhost:8000/app (or your port), run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 500 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.sequenceOf === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.sequenceOf === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const realFetch = window.fetch, realToast = I.showToast;
  const bodies = {};
  const J = (x, status) => new Response(JSON.stringify(x), { status: status || 200, headers: { 'Content-Type': 'application/json' } });
  const MAP = { summary: 'A grandmother retires her tests.', turn_scene: 3, carrier_scene: 3, hero_object: '', time_passing: false, notes: [], transitions: [], engagement: { risk: 'high' },
    scenes: [{ no: 1, purpose: 'the verdict', intensity: 1, time_mode: 'continuous', place: 'kitchen', energy: 1, change: 'x', beat: 'b1', sequence: false, actions: [] },
             { no: 2, purpose: 'the tests', intensity: 2, time_mode: 'continuous', place: 'kitchen', energy: 1, change: 'y', beat: 'b2', sequence: true, actions: ['smells the milk', 'watches it boil', 'holds it to the light'] },
             { no: 3, purpose: 'the turn', intensity: 3, time_mode: 'continuous', place: 'kitchen', energy: 2, change: 'z', beat: 'b3', sequence: false, actions: [] }],
    findings: [{ kind: 'concept-flattened', scene: 2, note: 'The concept’s beat 2 (6-15s) (“The tests — Quick cuts”) is flattened in the script: three actions shown as one still shot.' },
               { kind: 'concept-missing', scene: null, note: 'The concept’s surprise (“a lifetime of tests”) is missing in the script.' },
               { kind: 'same-place', scene: 1, note: '3 neighbouring scenes happen in the same place.' }],
    concept_delivery: [{ id: 'hook', label: 'Hook', text: 'h', status: 'delivered', scene: 1, note: '' }, { id: 'surprise', label: 'Surprise', text: 's', status: 'missing', scene: null, note: 'only one test' },
                       { id: 'turn', label: 'Turn', text: 't', status: 'delivered', scene: 3, note: '' }, { id: 'memorable', label: 'Memorable moment', text: 'm', status: 'delivered', scene: 3, note: '' },
                       { id: 'beat1', label: 'Beat 1', text: 'b', status: 'delivered', scene: 1, note: '' }, { id: 'beat2', label: 'Beat 2', text: 'c', status: 'flattened', scene: 2, note: 'one still shot' }], model: true };
  let mapReply = MAP;
  window.fetch = async (u, o) => { const url = String(u); try { bodies[url] = o && o.body ? JSON.parse(o.body) : null; } catch (e) {}
    if (/\/film-direct/.test(url)) return J(mapReply);
    if (/\/scene-shots/.test(url)) return J({ shots: [{ id: 'sh1', job: 'insert', why: 'the second action', visual: 'The milk climbs to the rim.', shot_size: 'detail', camera: 'locked-off', movement_class: 'static', secs: 2, warnings: [] }], master_secs: 4, notes: [], scene_seconds: 6, pace: 'calm', needs_coverage: true, why: 'a run' });
    return J({}); };
  I.showToast = () => {};
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const txt = () => document.body.innerText;
  const btn = t => [...document.querySelectorAll('button')].find(x => x.textContent.trim() === t);
  try {
    const rows = [{ no: 1, tc: '0–6s', visual: 'A drop rolls down a plate.' }, { no: 2, tc: '6–12s', visual: 'She sips and smells the milk.' }, { no: 3, tc: '12–18s', visual: 'Her daughter lowers the plate.' }];
    const concept = { logline: 'Nothing left to test.', proposition: 'Milk.', vo: '', hook: 'HOOK drop', surprise: 'SURP lifetime of tests', turn: 'TURN plate down', memorable: 'MEM laughs', stake: 'STK trusted test',
      scenes: [{ t: '0-6s', title: 'The verdict', desc: 'a drop' }, { t: '6-15s', title: 'The tests', desc: 'Quick cuts: smell, boil, light' }] };
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'scripting', scriptPhase: 'script', scriptStatus: 'drafted', prodDuration: '30s', videoObjective: 'Brand awareness', videoConcept: concept,
      fullScript: rows, sceneFrames: {}, castRefUrl: null, videoBeatMap: null, filmReview: null, beatMapBusy: false, filmReviewBusy: false, shotsProposal: {}, shotsDeclined: {} });
    await wait(700);
    check('before any read nothing mentions a run of quick actions or the concept’s promises', !/run of quick actions/.test(txt()) && !/promises kept/.test(txt()));

    btn('Read the film').click(); await wait(900);
    const b = bodies['/film-direct'] || {};
    check('the read is sent WITH the concept (moments, stake and beats)', b.concept && b.concept.hook === 'HOOK drop' && b.concept.turn === 'TURN plate down' && b.concept.stake === 'STK trusted test' && b.concept.scenes.length === 2, JSON.stringify(b.concept));
    check('Before you approve: the first finding of a REAL read is shown (it sits at the top level, not under engagement) with "+2 more"', /Boredom risk: high/.test(txt()) && /beat 2 \(6-15s\)/.test(txt()) && /\+2 more/.test(txt()), (txt().match(/Boredom risk[^\n]*/) || [''])[0]);
    check('Before you approve: says how many of the concept’s promises were kept (4 of 6)', /The concept.s promises kept: 4 of 6/.test(txt()), (txt().match(/promises kept[^\n]*/) || [''])[0]);
    check('Before you approve: the shot plan row names scene 2 as a run of quick actions with its three actions', /Scene 2 is a run of quick actions \(smells the milk · watches it boil · holds it to the light\)/.test(txt()) && /plans one shot per action/.test(txt()));
    check('Before you approve: only scene 2 is named (scene 1 and 3 are not runs)', !/Scene 1 is a run/.test(txt()) && !/Scene 3 is a run/.test(txt()));
    check('the Director’s read panel shows the kept count, the flattened and missing findings, and marks scene 2 as a run of quick actions', /what was flattened or left out is listed below, first/.test(txt()) && /three actions shown as one still shot/.test(txt()) && /lifetime of tests/.test(txt()) && /a run of quick actions: smells the milk/.test(txt()));
    check('the concept findings are listed BEFORE the engagement findings in the panel', txt().indexOf('three actions shown as one still shot') < txt().indexOf('3 neighbouring scenes happen in the same place'));
    check('scene 2’s card says it is one shot today but a run of quick actions, and offers to plan one shot per action', /One shot today, but the director reads this scene as a run of quick actions/.test(txt()) && !!btn('＋ Break into shots'), (txt().match(/One shot today[^\n]*/g) || []).join(' | '));
    check('Approve is still allowed with all of this showing', !btn('Approve script →').disabled);

    // the planner is sent the beat map, so it can plan one shot per action
    const breakBtns = [...document.querySelectorAll('button')].filter(x => x.textContent.trim() === '＋ Break into shots');
    breakBtns[0].click(); await wait(900);
    const sb = bodies['/scene-shots'] || {};
    check('Break into shots on a scene sends the director’s read with the run marked (scene 2 sequence + 3 actions), so the planner can use it', sb.beat_map && sb.beat_map.scenes[1].sequence === true && sb.beat_map.scenes[1].actions.length === 3, JSON.stringify(sb.beat_map && sb.beat_map.scenes && sb.beat_map.scenes[1]));
    // once the scene has extra shots the "run" nag leaves the panel
    I.setState(s => ({ fullScript: s.fullScript.map(r => (r.no === 2 ? { ...r, shots: [{ visual: 'The milk climbs to the rim.', secs: 2, job: 'insert', why: 'x', shot_size: 'detail' }] } : r)) })); await wait(600);
    check('after the scene has its extra shots, "Before you approve" no longer nags about it', !/Scene 2 is a run of quick actions/.test(txt()));

    // a montage is never a run
    I.setState({ fullScript: rows.map(r => ({ ...r })), videoBeatMap: { ...MAP, sig: I.beatSig(), scenes: MAP.scenes.map(s => (s.no === 2 ? { ...s, time_mode: 'montage' } : s)) } }); await wait(600);
    check('a montage scene is not shown as a run of quick actions', I.sequenceOf(1) === null && !/Scene 2 is a run of quick actions/.test(txt()));

    // a film with no concept sends none; an older read without delivery shows no promise line
    mapReply = { ...MAP, concept_delivery: undefined, scenes: MAP.scenes.map(s => ({ ...s, sequence: false, actions: [] })), findings: [] };
    I.setState({ videoConcept: { logline: 'An older film.', proposition: 'Milk.', vo: '', scenes: [] }, videoBeatMap: null, fullScript: rows.map(r => ({ ...r })) }); await wait(600);
    delete bodies['/film-direct'];
    btn('Read the film').click(); await wait(900);
    const ob = (bodies['/film-direct'] || {}).concept;
    check('an older concept (no moments, no beats) sends nothing to promise: no hook, surprise, turn, memorable or stake, and no beats', ob && !('hook' in ob) && !('turn' in ob) && !('stake' in ob) && (ob.scenes || []).length === 0, JSON.stringify(ob));
    check('a read with no promise answers shows no "promises kept" line and no run marker', !/promises kept/.test(txt()) && !/run of quick actions/.test(txt()));
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  } finally {
    window.fetch = realFetch; I.showToast = realToast;
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
