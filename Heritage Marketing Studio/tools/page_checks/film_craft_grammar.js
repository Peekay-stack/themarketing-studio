// film_craft_grammar.js -- the FILM GRAMMAR on the page (craft_skill/grammars/, beauty first), driven on the REAL page with the network stubbed.
//
// Why: in craft mode the page reads GET /craft-grammar and, when the brand's category has a grammar, its concept wording ("three routes", "make each route ..."), its speech budget and its
// note follow the grammar; a category with none, the person's pick of "General", Independent work and craft OFF all keep the general wording. The Film type selector sits beside the tick.
//
// How to run: start the studio with CRAFT_BRIEF=1, open http://localhost:PORT/app, run this whole file with javascript_exec. In-memory state only; reload afterwards.
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
  const real = { fetch: window.fetch, brandName: I.brandName };
  const asked = []; let view = null;
  const BEAUTY = { id: 'beauty', label: 'Beauty and skin', why: 'the brand’s category is “Beauty”', craft_on: true, options: [{ id: 'beauty', label: 'Beauty and skin' }], vo_mult: 1.0,
    routes_stand: ' THE THREE ROUTES. BEAUTY-STAND-PLATFORM hero image', routes_stand_free: ' THE THREE ROUTES. BEAUTY-STAND-FREE hero image', routes_alive: ' MAKE EACH ROUTE BEAUTIFUL AND CLEAR, BEAUTY-ALIVE.', speech_note: 'BEAUTY-SPEECH picture and sound.' };
  const GENERAL = { id: '', label: 'General', why: 'no grammar written yet', craft_on: true, options: [{ id: 'beauty', label: 'Beauty and skin' }], routes_stand: '', routes_stand_free: '', routes_alive: '', speech_note: '', vo_mult: null };
  window.fetch = async (u) => { const url = String(u); if (url.indexOf('/craft-grammar') === 0) { asked.push(url); return new Response(JSON.stringify(view), { status: 200, headers: { 'Content-Type': 'application/json' } }); }
    return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }); };
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const reset = (brand, pick) => { I._cg = null; I._cgKey = ''; I.brandName = () => brand; I.setState({ craftOn: true, craftGrammar: null, craftGrammarKey: '', craftGrammarPick: pick || '', producerBrandMode: 'grounded' }); };
  try {
    // 1. a beauty brand
    view = BEAUTY; reset('Kumkum Beauty'); asked.length = 0;
    await I.ensureCraftGrammar(); await wait(150);
    check('the page asks the server for the grammar of the brand in play', asked.length === 1 && /brand=Kumkum%20Beauty/.test(asked[0]) && /grammar=(&|$)/.test(asked[0]), asked.join(' '));
    const withP = I.craftConceptText(true), noP = I.craftConceptText(false);
    check('beauty: the route wording is the grammar’s (platform and no-platform variants), the general "alive" wording is gone', /BEAUTY-STAND-PLATFORM/.test(withP) && /BEAUTY-STAND-FREE/.test(noP) && /BEAUTY-ALIVE/.test(withP) && !/MAKE EACH ROUTE ALIVE/.test(withP) && !/more than two people/.test(withP), withP.slice(0, 200));
    check('beauty: the five craft lines and the claim rules still ride along', /"cast_idea"/.test(withP) && /Original only/.test(withP) && /BOTH the feeling and the proof/.test(withP));
    check('beauty: the speech budget is the base 32 words (not 1.5x) with the grammar’s note', I.voWords('30s') === 32 && /NO MORE than 32 words/.test(I.voBudgetNote('30s', 5)) && /BEAUTY-SPEECH/.test(I.voBudgetNote('30s', 5)) && !/use most of it/.test(I.voBudgetNote('30s', 5)));
    check('beauty: asking again for the same brand does not fetch again', (await I.ensureCraftGrammar(), asked.length === 1));
    check('the call carries the craft flag but no grammar pick when the person has not chosen one', JSON.stringify(Object.keys(I.craftCall()).sort()) === '["craft","timeoutMs"]');

    const photoOn = JSON.stringify(I.photoCraftFields());
    I.setState({ craftOn: false }); await wait(150);
    const photoOff = JSON.stringify(I.photoCraftFields());
    I.setState({ craftOn: true }); await wait(150);
    check('still photographs: craft ON sends the craft flag (no pick yet), craft OFF sends nothing', photoOn === '{"craft":true}' && photoOff === '{}', photoOn + ' / ' + photoOff);

    // 2. the person's pick
    I.setState({ craftGrammarPick: 'beauty' });
    check('a chosen grammar rides on the call as craft_grammar', I.craftCall().craft_grammar === 'beauty' && I.craftCall().craft === true && I.photoCraftFields().craft_grammar === 'beauty');
    I.onCraftGrammar({ target: { value: 'general' } }); await wait(250);
    check('choosing a film type stores it for this browser and reads the grammar again with the pick', asked.some(a => /grammar=general/.test(a)) && (() => { try { return localStorage.getItem('tms.craftg') === 'general'; } catch (e) { return true; } })());

    // 3. a category with no grammar written yet
    view = GENERAL; reset('Heritage Dairy'); await I.ensureCraftGrammar(); await wait(150);
    const gen = I.craftConceptText(true);
    check('no grammar for the category: the general wording, the general 1.5x speech budget and the general note', /MAKE EACH ROUTE ALIVE/.test(gen) && !/BEAUTY-/.test(gen) && I.voWords('30s') === 48 && /use most of it/.test(I.voBudgetNote('30s', 5)));
    check('the general wording no longer names an elder or the dairy examples', !/an elder/.test(gen) && !/cold crate/.test(gen) && !/network of farmers/.test(gen) && /a friend, a rival, a sceptic, a witness/.test(gen));

    // 4. craft off, and the server asked for nothing
    view = BEAUTY; reset('Kumkum Beauty'); await I.ensureCraftGrammar(); await wait(150);
    I.setState({ craftOn: false });
    check('craft OFF: no craft wording, base speech budget, no flag on the call, whatever grammar was read', I.craftConceptText(true) === '' && I.voWords('30s') === 32 && JSON.stringify(I.craftCall()) === '{}' && !/BEAUTY-SPEECH/.test(I.voBudgetNote('30s', 5)));
    asked.length = 0; I._cg = null; I._cgKey = ''; await I.ensureCraftGrammar();
    check('craft OFF: the page does not ask the server for a grammar at all', asked.length === 0);

    // 5. Independent work
    I.setState({ craftOn: true, producerBrandMode: 'general' }); I._cg = null; I._cgKey = ''; asked.length = 0; await I.ensureCraftGrammar();
    check('Independent (general) mode asks without a brand and says so', asked.length === 1 && /brand=&/.test(asked[0]) && /brand_mode=general/.test(asked[0]), asked.join(' '));

    // 6. a failing server leaves the general wording
    window.fetch = async () => new Response('nope', { status: 500 });
    reset('Kumkum Beauty'); await I.ensureCraftGrammar(); await wait(150);
    check('a failed read never raises and leaves the general wording', I.craftGrammarNow() === null && /MAKE EACH ROUTE ALIVE/.test(I.craftConceptText(true)) && I.voWords('30s') === 48);

    // 7. the selector
    window.fetch = real.fetch; I.brandName = real.brandName;
    I.setState({ screen: 'video', vTab: 'film', craftOn: true, craftGrammar: BEAUTY, craftGrammarKey: 'x|', craftGrammarPick: '' }); await wait(500);
    const lab = [...document.querySelectorAll('label')].find(l => /Film type/.test(l.innerText));
    const sel = lab && lab.querySelector('select');
    check('the Film type selector shows beside Craft mode and lists Auto (with the grammar), General and the grammars', !!sel && [...sel.options].map(o => o.text).join('|') === 'Auto (Beauty and skin)|General|Beauty and skin', sel ? [...sel.options].map(o => o.text).join('|') : 'no selector');
    I.setState({ craftOn: false }); await wait(300);
    check('craft OFF hides the selector', ![...document.querySelectorAll('label')].some(l => /Film type/.test(l.innerText)));
  } catch (e) {
    check('no exception', false, String(e && e.stack || e));
  } finally {
    window.fetch = real.fetch; I.brandName = real.brandName;
    try { localStorage.removeItem('tms.craftg'); localStorage.removeItem('tms.craft'); } catch (e) {}
    I._cg = null; I._cgKey = '';
    I.setState({ craftOn: false, craftGrammar: null, craftGrammarKey: '', craftGrammarPick: '' });
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})();
