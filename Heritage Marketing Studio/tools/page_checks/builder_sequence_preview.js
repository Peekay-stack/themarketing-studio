// builder_sequence_preview.js -- film builder slice S2d: the picture-only preview of the chosen, trimmed clips, driven on the REAL page with the network stubbed. No media files are needed (the clip urls are
// never played here); the real-playback check was done once by hand with three generated clips (it played 0-4 s, the trimmed clip from its trim start for 2 s, then 4 s, about 9.8 s of a 10 s total).
//
// Why: the Timeline line, the preview and the assembled film must agree on how long each shot is: a trimmed window, a clip cut to the shot's planned seconds, a clip shorter than its beat. The preview's total
// is checked against assembleStatus().kept, and the controls and empty states are exercised.
//
// How to run: start the studio (preview "studio"), open http://localhost:8000/app, run this whole file with the browser tool's javascript_exec. In-memory state only; reload afterwards.
// Returns {pass, failures, results}. Expected: pass === true.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const root = document.getElementById('dc-root') || document.body, ck = Object.keys(root).find(k => k.startsWith('__reactContainer'));
  let I = null; const seen = new Set();
  (function walk(f, d){ if (!f || seen.has(f) || d > 400 || I) return; seen.add(f);
    for (const k of ['stateNode', 'memoizedProps', 'memoizedState']) { const v = f[k];
      if (v && typeof v === 'object' && typeof v.setState === 'function' && v.state && 'fullScript' in v.state && typeof v.seqItems === 'function') { I = v; return; }
      if (v && v.logic && typeof v.logic.seqItems === 'function') { I = v.logic; return; } }
    walk(f.child, d + 1); walk(f.sibling, d + 1); })(root[ck], 0);
  if (!I) return JSON.stringify({ pass: false, failures: ['could not find the app instance'] });
  const results = [], check = (name, ok, extra) => results.push({ name, ok: !!ok, extra: ok ? undefined : extra });
  const mk = (id, url, secs, beats) => ({ id, url, beats: beats || [], tier: 'draft', engine: 'omni', seconds: secs, mode: 'frame', frame: '/media/f.jpg', status: 'done', error: '', checks: [], est_usd: 0.1 });
  const btn = t => [...document.querySelectorAll('button')].find(x => x.textContent.trim() === t);
  try {
    const rows = [{ no: 1, tc: '0–4s', visual: 'A' }, { no: 2, tc: '4–9s', visual: 'B' }, { no: 3, tc: '9–13s', visual: 'C' }];
    const fr = {}; rows.forEach((r, i) => fr[i] = { status: 'done', url: '/media/f' + i + '.jpg' });
    const base = { version: 1, frames: {}, frame_chosen: {}, takes: { '0': [mk('ta', '/media/a.mp4', 4)], '1': [mk('tb', '/media/b.mp4', 5)], '2': [mk('tc', '/media/c.mp4', 5)] }, chosen: { '0': 'ta', '1': 'tb', '2': 'tc' }, trim: { '1': { in: 1, out: 3 } }, budget: { cap_usd: 0, spent_usd: 0 } };
    I.setState({ screen: 'video', vTab: 'film', videoStep: 'shots', fullScript: rows, scriptStatus: 'approved', sceneFrames: fr, castRefUrl: '/media/c.jpg', seqPreview: null, videoBuilder: base });
    await wait(700);
    let q = I.seqItems();
    check('the playlist is the chosen clips in script order, each from its trim start, the trimmed one for its window only, a long clip cut to the shot\'s planned seconds',
      q.items.map(x => x.label + ' ' + x.start + '-' + x.end).join(' | ') === 'Scene 1 0-4 | Scene 2 1-3 | Scene 3 0-4', q.items.map(x => x.label + ' ' + x.start + '-' + x.end).join(' | '));
    check('the preview total EQUALS the Timeline line (10 s)', Math.abs(q.total - I.assembleStatus().kept) < 1e-9 && q.total === 10, q.total + ' vs ' + I.assembleStatus().kept);
    const b = btn('Preview sequence'); check('the strip has a Preview sequence button', !!b);
    b.click(); await wait(600);
    check('opening it shows the player on clip 1 of 3 with the fragment src (start,end)', I.state.seqPreview && I.state.seqPreview.i === 0
      && [...document.querySelectorAll('video')].some(v => /a\.mp4#t=0\.00,4\.00/.test(v.getAttribute('src') || '')));
    btn('Next →').click(); await wait(300);
    check('Next goes to clip 2, whose src starts at its trim (b.mp4#t=1.00,3.00)', I.state.seqPreview.i === 1 && [...document.querySelectorAll('video')].some(v => /b\.mp4#t=1\.00,3\.00/.test(v.getAttribute('src') || '')));
    I.seqNext(1, 3)(); await wait(200);
    check('reaching a clip\'s end moves on to the next', I.state.seqPreview.i === 2);
    I.seqNext(2, 3)(); await wait(200);
    check('reaching the last clip\'s end stops there (done), it does not wrap', I.state.seqPreview.i === 2 && I.state.seqPreview.done === true);
    check('a stale end event for a clip that is no longer playing is ignored', (() => { const before = JSON.stringify(I.state.seqPreview); I.seqNext(0, 3)(); return true; })() && I.state.seqPreview.i === 2);
    btn('↻ Replay').click(); await wait(300);
    check('Replay starts again from clip 1', I.state.seqPreview.i === 0 && I.state.seqPreview.done === false && btn('← Previous').disabled === true);
    // a clip SHORTER than its beat shrinks the beat: the preview and the Timeline agree
    I.setState({ videoBuilder: { ...base, takes: { ...base.takes, '2': [mk('tc', '/media/c.mp4', 2.5)] } } }); await wait(300);
    q = I.seqItems();
    check('a clip shorter than its beat plays only its own length, and the total still equals the Timeline line (8.5 s)', Math.abs(q.total - 8.5) < 1e-9 && Math.abs(q.total - I.assembleStatus().kept) < 1e-9, q.total + ' vs ' + I.assembleStatus().kept);
    // a multi-beat shot plays its beats in order, capped at the shot's planned seconds
    I.setState({ videoBuilder: { ...base, takes: { ...base.takes, '0': [mk('ta', '/media/a1.mp4', 6, [{ url: '/media/a1.mp4', seconds: 3 }, { url: '/media/a2.mp4', seconds: 3 }])] } } }); await wait(300);
    q = I.seqItems();
    check('a multi-beat shot plays its beats in order, capped at the shot\'s planned seconds (4 s: 3 + 1), and still equals the Timeline line',
      q.items.slice(0, 2).map(x => x.label + ' ' + x.len).join(' | ') === 'Scene 1 (part 1) 3 | Scene 1 (part 2) 1' && Math.abs(q.total - I.assembleStatus().kept) < 1e-9, q.items.map(x => x.label + ' ' + x.len).join(' | '));
    // a shot with no chosen clip is named as skipped; none at all is an honest empty state
    I.setState({ videoBuilder: { ...base, chosen: { '0': 'ta', '2': 'tc' } } }); await wait(300);
    check('a shot without a chosen clip is left out and named', I.seqItems().items.length === 2 && /Not in this preview \(no chosen clip\): Scene 2/.test(document.body.innerText));
    I.setState({ videoBuilder: { ...base, chosen: {} } }); await wait(300);
    check('with no chosen clip there is an honest empty state and the button is disabled', /nothing to preview/.test(document.body.innerText) && (btn('Restart preview') || btn('Preview sequence')).disabled === true);
    I.setState({ videoBuilder: base }); await wait(200); btn('Close') && btn('Close').click(); await wait(200);
    check('Close hides the player', I.state.seqPreview === null);
  } catch (e) {
    results.push({ name: 'the run did not throw', ok: false, extra: String(e && e.stack || e) });
  }
  const failures = results.filter(r => !r.ok);
  return JSON.stringify({ pass: failures.length === 0 && results.length > 0, count: results.length, failures, results: results.map(r => (r.ok ? 'PASS ' : 'FAIL ') + r.name) }, null, 1);
})()
