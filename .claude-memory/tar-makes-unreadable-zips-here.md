---
name: tar-makes-unreadable-zips-here
description: "On this Windows machine, `tar -a -c -f x.zip` produces archives that only bsdtar can read — use Python zipfile for backup zips and CRC-test with a different tool"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-08T06:18:29.818Z
---

Making the 2026-09-08 migration backup zips (see [[account-migration-plan]]), `tar -a -c -f x.zip`
was used twice. `tar -tf` listed the contents fine both times, so it looked done. It was not:

- The filesystem archive: Python `zipfile` saw **23 of ~12,374 entries** — a truncated/absent central
  directory. Windows Explorer "Extract All" and 7-zip rely on that central directory, so they would
  have silently restored 23 files.
- The memory archive: Python `zipfile` raised `BadZipFile: File is not a zip file` outright.

The bsdtar build shipped with Git-for-Windows here does not write standard ZIP central directories
(or writes them inconsistently past some size/count threshold). An archive only the tool that wrote
it can open is not a backup.

**Why:** a backup's whole value is that a *different* program, on a *different* machine, can open it.
"`tar -tf` lists it" only proves bsdtar can read its own output.

**How to apply:**
- To make a `.zip` on this machine, use a Python `zipfile` script:
  `ZipFile(out, "w", compression=ZIP_DEFLATED, compresslevel=1, allowZip64=True)`, `os.walk` the
  tree, `z.write(fp, arcname)` with a `try/except` per file so a locked file (e.g. `heritage.db`
  while the studio server runs) is skipped/reported rather than aborting the whole archive.
- Then **verify with a different tool than the one that wrote it** — `zipfile.testzip()` (full CRC)
  plus an entry-count sanity check and a spot-check that key payload files (`.env`, `.git/objects/pack/*.pack`)
  are present. `tar -tf` alone is not verification.
- `Compress-Archive` (PowerShell 5.1) is an alternative but has a ~2GB limit and hard-fails on
  locked files — the Python script is more robust for this repo.
