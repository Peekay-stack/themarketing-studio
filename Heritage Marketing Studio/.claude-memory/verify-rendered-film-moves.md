---
name: verify-rendered-film-moves
description: "After ANY render, decode frames at many times and compare fingerprints (and look at a 1-frame-per-second contact sheet): duration/exit code can be perfect while the picture is frozen. Learned 28 Oct 2026 when a 'successful' 30.0 s render held one frame for 10 s."
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcd137c0-c85a-447d-9d35-c10659cecac7
  modified: 2026-10-27T16:54:01.547Z
---

**Rule:** a render is not verified by `status ok`, the duration, the stream list or the log. Extract one frame per second (ffmpeg `fps=1`), look at the contact sheet, and hash a tiny grey copy of mid-clip frames: the same hash in two different clips' windows = frozen picture. `filmcut.frozen_join` now does this inside `stitch` and rebuilds with the concat filter.

**Why:** the first end-to-end run of the re-directed Heritage film reported `ok`, 30.0 s, 7 shots, voices+music, and every individual clip moved — yet the stitched film showed ONE frame from 16 s to 26 s. Cause: `filmcut.stitch` joins with the concat demuxer; clips that had been trimmed (3 s -> 2 s, re-encoded) sitting between untouched ones froze the picture (stream copy AND re-encode of the demuxer join; the concat FILTER is fine). A synthetic 5-clip case reproduces it, so it is NOT specific to coverage: **this bug can exist on the live master** whenever a trimmed clip neighbours untrimmed ones (the coverage branch just makes it common). Hotfix = cherry-pick the commit "Fix: a joined film could show ONE frame for seconds" (`filmcut.py` + `tools/test_stitch_freeze.py`) to master ONLY with the owner's OK (localhost-first rule); I flagged it to them.

**How to apply:** after every render I hand over, run the contact sheet + a frozen check before claiming it works ([[judge-the-film-not-the-pipeline]]); never trust the render function's own `ok`. Related: [[measure-the-artefact-before-theorising]], [[coverage-and-film-craft-thread]].
