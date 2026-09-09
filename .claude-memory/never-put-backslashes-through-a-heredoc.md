---
name: never-put-backslashes-through-a-heredoc
description: "A quoted bash heredoc on this machine still eats one backslash level, so \\u00b7 anchors miss and \\\\ in JSON silently corrupts the file"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5e956381-ce19-4f83-93e1-71a73ced8b2b
  modified: 2026-08-26T14:20:17.431Z
---

Writing patch scripts with `python - <<'PYEOF'` here, a **quoted** heredoc still strips one backslash
level. It has now cost four separate failures:

- `—` in an anchor arrived as a real em dash, so the match failed
- `\\u00b7` arrived as `·`, which Python then read as a middot character, so an anchor against
  the literal six characters in `app.dc.html` matched zero times
- `\\n` inside a replacement became a real newline and **broke a Python string literal** in `plan.py`
- `\\Scripts\\` in a `launch.json` heredoc became `\Scripts\` — invalid JSON escapes that would have
  broken the one working dev-server config

The last two are the dangerous ones: they wrote successfully and produced a broken file. A failed
anchor is loud; a corrupted escape is not.

**Why:** the shell layer is invisible in the diff. What you wrote and what Python received differ, and
only the file shows it.

**How to apply:** never let a backslash travel through the shell. Build it in Python with
`BS = chr(92)` and concatenate, use `chr(10)` for newlines, and anchor on substrings that contain no
escapes at all — split the line and match the escape-free part. For structured files use a real
serialiser (`json.dumps`) and read the file back to prove the value survived. For long prose files
(a handover .md) use the Write tool instead: the heredoc also broke on ordinary punctuation. Always
`ast.parse` a patched .py and diff the target before trusting the write. Related:
[[app-dc-html-is-lf-not-crlf]], [[launch-json-lives-at-opus-root]].
