#!/usr/bin/env python3
r"""
census.py -- every state key a bag READS, against every key a loader WRITES.

Why this exists, in one sentence: a consumer with no producer reads as a feature that simply had
nothing to say. `og.kit` was wired into a card and fetched by nothing; the hole resolved to a bag
key, the key resolved to a real expression, and the expression resolved to {}. checkfe.py cannot
see that -- every layer was valid.

This is NOT a pass/fail gate and it should not become one. It prints a list a person reads once a
round. False positives are kept VISIBLE rather than suppressed, because `pr.sheet` (written by an
opener) and `og.kit` (written by nothing) look identical to a parser -- and a rule that hides the
second case to avoid the first is worse than a list with noise in it.

Exit code is always 0 unless the file cannot be read. Judgement stays with the reader.

Usage:  python3 tools/census.py [app.dc.html]

Written by Claude Design, round 41; pasted into the repo in round 43 because only the frontend and
the handover document cross between the two sides -- a .py file cannot travel inside app.dc.html.

Extended round 46 (backend side, since tools/ is the half that DOES cross): brace matching, the
dominant real write path, and alias tracking -- the round-43 handover named the first and third and
left them for whoever holds this file; the second was found while fixing the first.

**Brace matching was silently hiding real orphans, not being imprecise.** The old writer-finder used
`{([^}]{0,600})` (curly braces, then up to 600 non-brace characters) which stops at the FIRST closing
brace it meets. `setState(s => ({ comp:{ ...s.comp, key:'x' }, otherKey: 5 }))` has a nested object
before the true close, so the old pattern captured only `comp:{ ...s.comp, key:'x'` and never saw
`otherKey` -- it was neither counted as written nor printed as suspicious, it just vanished. Measured
against this file: 193 of 524 `setState(` call sites were truncated before their real closing brace.
`object_body()` below counts real depth, skips string/template contents so a quoted `}` cannot close
early, and has no length cap.

**The bigger find while fixing that: most namespaced bags are never written through a `set<Ns>()`
call at all.** `namespaced()`'s writer search only ever looked for `set<Ns>(` and `setNs('ns','k')`.
But this file's dominant pattern for `og`, `idea`, `soc`, `campaign` and others is a plain
`this.setState(s => ({ og: { ...s.og, ...patch } }))` -- a namespace-shaped key nested inside an
ordinary setState call, with no dedicated setter function anywhere. The old script had no way to see
that, so every namespace populated only this way looked permanently unwritten, whether or not it
actually was. `nested_writes_via_setstate()` below reads exactly that shape.

**Alias tracking answers `const o = this.og(); ... o.kit`** -- a namespace accessor result assigned
to a local name, then read off that name rather than off `this.<ns>()` directly. `namespaced()`
collects every `const/let/var X = this.<ns>()` declaration and, for each `X.key` read found
afterward, credits it to the NEAREST PRECEDING declaration of that identifier. This is a heuristic,
not a scope analyser: two functions reusing the same local name for two different namespaces will
attribute correctly as long as each read follows its own declaration before the next one, which is
how this codebase's short-lived locals are actually used -- it will not catch a stale alias read
after reassignment inside a deeply nested closure, and that stays a gap.

**Doing all three together surfaced a fourth problem: most of what `this.<name>()` reaches is not a
state bag at all.** Things like `activeBrand()`, `tiers()`, `shots()`, `prMandSet()` are plain
computed getters -- derived values, filtered lists, lookups -- with no writer contract and no reason
to have one. Grading them against "was this written by a setter" produces a wall of noise that
drowns the two or three lines that matter. So namespace findings are now split in two: namespaces
with SOME writer evidence, by any of the three mechanisms above, are real bags and get the full
og.kit-style report; namespaces read but with no writer evidence anywhere are printed as a short name
list -- visible, per this file's own rule against suppressing signal, but not exploded key by key,
because a getter having no setter is not a finding.
"""
import re, sys, pathlib

WRITERS = ("setState", "setPr", "setMedia", "setImc", "setStrat", "setSoc", "setNs",
           "setPosm", "setOg", "setIdea", "setNsDeep")

def logic_of(src):
    parts = src.split('<script type="text/x-dc"', 1)
    return parts[1] if len(parts) > 1 else src

def object_body(text, start):
    """The text strictly between a `{` and its matching `}`, searching for the opening brace from
    `start` (skipping up to 200 chars of whitespace / arrow-wrapper prefix like `s => (`). Counts
    real depth rather than stopping at the first `}`, and ignores braces inside '...', "...", `...`
    so a string or template literal cannot close the object early. Returns None if no `{` is found
    nearby, or if depth never returns to zero (a malformed or truncated file) -- never a partial,
    misleading slice.
    """
    n = len(text)
    i = start
    while i < n and text[i] != '{' and i - start < 200:
        i += 1
    if i >= n or text[i] != '{':
        return None
    depth = 0
    j = i
    in_str = None
    while j < n:
        c = text[j]
        if in_str:
            if c == '\\':
                j += 2
                continue
            if c == in_str:
                in_str = None
        else:
            if c in ('"', "'", '`'):
                in_str = c
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return text[i + 1:j]
        j += 1
    return None

def keys_written_in(text, call_prefix):
    """Every `identifier:` at any depth inside the object literal(s) passed to each call matching
    `call_prefix(` (e.g. `setState(`, `setOg(`). Keys inside a nested object count as written too --
    the old tool did the same within its 600-char window, so this is a superset, not new noise."""
    out = set()
    for m in re.finditer(re.escape(call_prefix) + r"\(", text):
        body = object_body(text, m.end())
        if body is None:
            continue
        out |= set(re.findall(r"([A-Za-z0-9_]+)\s*:", body))
    return out

def nested_writes_via_setstate(logic):
    """ns -> written keys, for the `<ns>: { key: val, ... }` shape nested inside any `setState(...)`
    body -- the way this file actually populates most namespaced bags. Only descends into a key's
    value when the very next non-whitespace character is `{`; anything else (a call, a spread, a
    plain value) is left alone rather than guessed at."""
    out = {}
    for m in re.finditer(r"\bsetState\(", logic):
        body = object_body(logic, m.end())
        if body is None:
            continue
        for km in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*", body):
            ns = km.group(1)
            pos = km.end()
            if pos >= len(body) or body[pos] != '{':
                continue
            nested = object_body(body, pos)
            if nested is None:
                continue
            keys = set(re.findall(r"([A-Za-z0-9_]+)\s*:", nested))
            if keys:
                out.setdefault(ns, set()).update(keys)
    return out

def top_level(logic):
    """(read, written, declared) for this.state.X"""
    read = set(re.findall(r"this\.state\.([A-Za-z0-9_]+)", logic))
    read |= set(re.findall(r"\bs\.([A-Za-z0-9_]+)", logic))
    written = keys_written_in(logic, "setState")
    block = re.search(r"\n  state\s*=\s*\{([\s\S]{0,20000}?)\n  \};", logic)
    declared = set(re.findall(r"^\s{4}([A-Za-z0-9_]+)\s*:", block.group(1), re.M)) if block else set()
    return read, written, declared

def namespace_aliases(logic):
    """[(position, varname, ns), ...] for every `const/let/var X = this.<ns>()`, in source order."""
    out = []
    for m in re.finditer(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*this\.([a-z][A-Za-z0-9_]*)\(\)",
                          logic):
        out.append((m.start(), m.group(1), m.group(2)))
    return out

def namespaced(logic):
    """Returns (bags, getters):
      bags    -- ns -> (read, written) for namespaces with SOME writer evidence: a real state bag,
                 reported key by key exactly like the top-level orphan list.
      getters -- sorted list of namespace names read (directly or via an alias) with NO writer
                 evidence found by any of the three mechanisms -- plain computed accessors, kept
                 visible as names only rather than exploded into noise.
    """
    read = {}
    for ns, key in re.findall(r"this\.([a-z][A-Za-z0-9_]*)\(\)\s*\.\s*([A-Za-z0-9_]+)", logic):
        read.setdefault(ns, set()).add(key)

    aliases = namespace_aliases(logic)
    by_var = {}
    for pos, var, ns in aliases:
        by_var.setdefault(var, []).append((pos, ns))
    for var, decls in by_var.items():
        decls.sort()
        for m in re.finditer(r"\b" + re.escape(var) + r"\.([A-Za-z0-9_]+)\b", logic):
            if m.start() <= decls[0][0]:
                continue  # a read before any declaration of this name is not an alias read
            ns = None
            for pos, cand_ns in decls:
                if pos <= m.start():
                    ns = cand_ns
                else:
                    break
            if ns:
                read.setdefault(ns, set()).add(m.group(1))

    written = {}
    for fn in sorted(set(re.findall(r"\bset([A-Z][A-Za-z0-9_]*)\(", logic))):
        ns = fn[0].lower() + fn[1:]
        found = keys_written_in(logic, "set" + fn)
        if found:
            written.setdefault(ns, set()).update(found)
    for ns, key in re.findall(r"setNs\(\s*'([a-z]+)'\s*,\s*'([A-Za-z0-9_]+)'", logic):
        written.setdefault(ns, set()).add(key)
    for ns, keys in nested_writes_via_setstate(logic).items():
        written.setdefault(ns, set()).update(keys)

    bags = {ns: (read[ns], written.get(ns, set())) for ns in read if ns in written}
    getters = sorted(ns for ns in read if ns not in written)
    return bags, getters

def routes(src):
    return sorted(set(re.findall(r"api(?:Get|Call|Json)\('(/[a-z0-9\-/]+)", src)))

def main():
    path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "app.dc.html")
    src = path.read_text(encoding="utf-8")
    logic = logic_of(src)

    print(f"census of {path} -- {len(src)} bytes, {len(routes(src))} distinct routes")
    print()

    read, written, declared = top_level(logic)
    orphan = sorted(k for k in read if k not in written and k not in declared)
    print("TOP-LEVEL keys read but never written and never declared in initial state")
    print("  (each one is either dead code, a server-hydrated key, or the og.kit bug)")
    for k in orphan:
        print(f"    {k}")
    if not orphan:
        print("    none")
    print()

    bags, getters = namespaced(logic)
    print("NAMESPACE BAGS -- read through an accessor (or an alias of one), with a writer found")
    print("  somewhere (set<Ns>, setNs, or a same-named key nested in setState). A missing key here")
    print("  is dead code, a field hydrated wholesale from a server response this script cannot see")
    print("  inside (setState({ ns: apiResponse }) -- the common case), or the og.kit bug; skim for")
    print("  the third kind rather than expecting the list to be short")
    any_hit = False
    for ns in sorted(bags):
        rd, wr = bags[ns]
        miss = sorted(k for k in rd if k not in wr)
        if miss:
            any_hit = True
            print(f"    {ns}: {', '.join(miss)}")
    if not any_hit:
        print("    none")
    print()

    print("ACCESSORS with no writer evidence found by any mechanism -- likely plain getters")
    print("  (computed values, filtered lists) rather than state bags; named, not exploded, because")
    print("  a getter having no setter is not itself a finding")
    print(f"    {', '.join(getters)}" if getters else "    none")
    print()
    print("Read each line and decide which of the three it is. Do not suppress the noise -- the")
    print("noise and the bug are indistinguishable to this script, which is the point.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
