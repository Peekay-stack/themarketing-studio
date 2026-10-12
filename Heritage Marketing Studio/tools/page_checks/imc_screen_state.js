// imc_screen_state.js -- the IMC brief screen's state lifecycle, driven on the REAL page with the network stubbed.
//
// Why: the IMC screen kept its whole brief (draft, prompt, research files, project name and the id of its library row) for
// the entire session. A brief you had saved was still on screen under "+ New brief"; a brand switch left the old brand's
// draft under the new brand's name; and the next Save wrote to the old row, overwriting it (briefstore.put replaces
// brand, title, format and fields of the row it is given). This pins the behaviour that replaced that.
//
// How to run: start the studio (preview "studio"), open http://localhost:8000/app, paste this whole file into the page
// console (or run it with the browser tool's javascript_exec). It stubs window.fetch for its own run, changes the page's
// in-memory state only, restores fetch at the end, and returns {pass, failures, results}. Reload the page afterwards.
(async () => {
  let fiber = null;
  for (const el of document.querySelectorAll('body *')) { const k = Object.keys(el).find(k => k.startsWith('__reactFiber')); if (k) { fiber = el[k]; break; } }
  let f = fiber, sc = null;
  while (f) { if (f.stateNode && f.stateNode.constructor && f.stateNode.constructor.name === 'StreamableComponent') { sc = f.stateNode; break; } f = f.return; }
  const L = sc.logic;                                   // NOT sc.state: the templates render from sc.logic.state
  const initialKeys = Object.keys(L.state.imc).sort().join(',');
  const realFetch = window.fetch, calls = [];
  const BR = [{ id:'b1', name:'Heritage Foods', category:'Dairy', active:true }, { id:'b2', name:'Sthir Cement', category:'Cement', active:false }];
  window.fetch = async (url, opts) => {
    const u = String(url); let payload = null;
    try { if (opts && opts.body && opts.body.get) payload = JSON.parse(opts.body.get('payload')); else if (opts && opts.body) payload = JSON.parse(opts.body); } catch (e) {}
    calls.push({ url:u, payload });
    let ans = {};
    if (u.includes('/brand-active')) ans = { brands: BR.map(b => ({ ...b, active: b.id === 'b2' })) };
    if (u.includes('/brand-brief-draft')) ans = { brief_id: (payload && payload.brief_id) || 'NEW1', smp:'New smp', title:'t', brand:'Heritage Foods', competitors:[], cb_ca_db_da:{}, needscope:{ pins:[] }, smp_defence:[], smp_unlocks:{} };
    if (u.includes('/brief-save')) ans = { id: (payload && payload.id) || 'SAVED1' };
    return new Response(JSON.stringify(ans), { status:200, headers:{ 'Content-Type':'application/json' } });
  };
  const wait = (ms) => new Promise(r => setTimeout(r, ms));
  const set = async (o) => { L.setState(o); await wait(60); };
  const base = L.state.imc, NOFILES = { market:[], household:[], wheel:[], cbca:[], research:[] };
  const mk = (over) => ({ ...base, prompt:'P', brand:'Heritage Foods', category:'Dairy', project:'Proj1',
    files:{ ...NOFILES, market:[{ name:'m.xlsx' }] },
    draft:{ smp:'Old SMP', competitors:[{ name:'c' }], cb_ca_db_da:{}, needscope:{ pins:[] }, smp_defence:[], smp_unlocks:{} },
    status:'ready', briefId:null, savedAt:null, ...over });
  const snap = () => { const s = L.state; return { draft: s.imc.draft ? s.imc.draft.smp : null, prompt:s.imc.prompt, project:s.imc.project, files:(s.imc.files.market||[]).length, brand:s.imc.brand, briefId:s.briefId, imcBriefId:s.imc.briefId, briefSavedAt:s.briefSavedAt }; };
  const r = {}, failures = [];
  const expect = (name, got, want) => { r[name] = got; for (const k of Object.keys(want)) if (got[k] !== want[k]) failures.push(name + '.' + k + ': got ' + JSON.stringify(got[k]) + ', want ' + JSON.stringify(want[k])); };
  try {
    const blank = Object.keys(L.blankImc()).sort().join(',');
    expect('blank_shape_matches_initial', { same: initialKeys === blank }, { same: true });
    await set({ screen:'home', producerBrandMode:'grounded', brands:BR, imc:mk({ briefId:'ID1', savedAt:'10:00' }), briefId:'ID1', briefSavedAt:'10:00' });
    L.openBuilder('imc')(); await wait(80);
    expect('new_brief_after_explicit_save_is_empty', snap(), { draft:null, prompt:'', project:'', files:0, brand:'Heritage Foods', briefId:null, imcBriefId:null, briefSavedAt:null });
    await set({ screen:'home', producerBrandMode:'grounded', imc:mk({ briefId:'ID2', savedAt:null }), briefId:'ID2', briefSavedAt:null });
    L.openBuilder('imc')(); await wait(80);
    expect('unsaved_draft_in_progress_is_kept', snap(), { draft:'Old SMP', prompt:'P', project:'Proj1', files:1, briefId:'ID2', imcBriefId:'ID2' });
    await set({ screen:'home', producerBrandMode:'grounded', imc:mk({ briefId:'X', savedAt:null }), briefId:'M', briefSavedAt:'10:05' });
    L.openBuilder('imc')(); await wait(80);
    expect('imc_uses_its_own_id_not_another_formats', snap(), { draft:'Old SMP', briefId:'X', imcBriefId:'X' });
    await set({ screen:'home', producerBrandMode:'grounded', imc:mk({ draft:null, status:'idle' }), briefId:'M', briefSavedAt:'10:05' });
    L.openBuilder('imc')(); await wait(80);
    expect('no_imc_draft_means_no_id_carried', snap(), { draft:null, briefId:null, imcBriefId:null });
    await set({ screen:'imc', producerBrandMode:'grounded', brands:BR, imc:mk({ briefId:'ID1', savedAt:'10:00' }), briefId:'ID1', briefSavedAt:'10:00' });
    await L.switchBrand('b2')(); await wait(150);
    expect('brand_switch_starts_a_new_brief_for_the_new_brand', snap(), { draft:null, prompt:'', project:'', files:0, brand:'Sthir Cement', briefId:null, imcBriefId:null, briefSavedAt:null });
    await set({ screen:'imc', producerBrandMode:'grounded', brands:BR.map(b => ({ ...b, active: b.id === 'b1' })), imc:mk({ briefId:'ID1', savedAt:'10:00' }), briefId:'ID1', briefSavedAt:'10:00' });
    await L.setProducerBrandMode('general')(); await wait(150);
    expect('mode_switch_clears_the_draft_and_its_id', snap(), { draft:null, briefId:null, imcBriefId:null, briefSavedAt:null });
    await set({ screen:'imc', producerBrandMode:'grounded', imc:mk({ files:NOFILES, briefId:'ID1', savedAt:null }), briefId:'ID1', briefSavedAt:null });
    calls.length = 0; await L.draftBrief(); await wait(150);
    const d1 = calls.find(c => c.url.includes('/brand-brief-draft'));
    expect('redraft_corrects_the_same_row', { sent: d1 && d1.payload ? d1.payload.brief_id : 'no call', briefId:L.state.briefId, imcBriefId:L.state.imc.briefId }, { sent:'ID1', briefId:'ID1', imcBriefId:'ID1' });
    await set({ screen:'imc', producerBrandMode:'grounded', imc:mk({ files:NOFILES, briefId:null, savedAt:null }), briefId:null, briefSavedAt:null });
    calls.length = 0; await L.draftBrief(); await wait(150);
    const d0 = calls.find(c => c.url.includes('/brand-brief-draft'));
    expect('first_draft_of_a_new_brief_sends_no_id', { sent: d0 && d0.payload ? d0.payload.brief_id : 'no call', briefId:L.state.briefId, imcBriefId:L.state.imc.briefId }, { sent:'', briefId:'NEW1', imcBriefId:'NEW1' });
    calls.length = 0; await L.saveImcBrief(); await wait(150);
    const sv = calls.find(c => c.url.includes('/brief-save'));
    expect('explicit_save_writes_to_that_row', { sent: sv && sv.payload ? sv.payload.id : 'no call', savedAt: !!L.state.imc.savedAt, imcBriefId:L.state.imc.briefId }, { sent:'NEW1', savedAt:true, imcBriefId:'NEW1' });
    L.openBuilder('imc')(); await wait(80);
    expect('new_brief_after_that_save_is_empty', snap(), { draft:null, prompt:'', project:'', files:0, briefId:null, imcBriefId:null });
  } catch (e) { failures.push('exception: ' + String(e && e.stack || e).slice(0, 300)); }
  window.fetch = realFetch;
  return JSON.stringify({ pass: failures.length === 0, failures, results: r }, null, 1);
})()
