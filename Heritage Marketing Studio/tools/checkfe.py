#!/usr/bin/env python
"""checkfe.py — the check that would have caught the syntax error I shipped.

There is no Node in this environment, so `app.dc.html` cannot be parsed by a real JS engine. Once I
flattened newline escapes and broke eight string literals; the tag-balance and binding checks I was
running all passed, because neither of them looked at JavaScript at all. Claude Design found it.

This is the missing check. It is not a JS parser — it is a scanner that understands just enough lexical
structure to be certain about two things:

**Unterminated string literals.** A `'` or `"` string cannot span a line break in JavaScript. That is
exactly the damage a mangled `\\n` does, and it is the single highest-value check here.

**Bracket balance, ignoring anything quoted or commented.** A naive brace count on this file is
meaningless — the markup is full of `{{ }}` bindings and the logic is full of `${}` inside template
literals. This tracks line comments, block comments, both quote styles, template literals with nested
`${}`, and regex literals, so the count it reports is about code rather than about punctuation.

It also re-runs the structural checks that did work, so one command covers everything:
`sc-if`/`sc-for` pairing, `<div>` pairing, and the class-member census.

    python tools/checkfe.py

Exit code 0 means every check passed. Non-zero lists what failed and on which line. This does not prove
the file runs — nothing here can — but every failure it reports is a real defect, and the failure mode it
was built for is the one that has actually bitten this project.
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "api", "frontend", "app.dc.html")

OPEN, CLOSE = "([{", ")]}"
PAIR = {")": "(", "]": "[", "}": "{"}


def _regions(text: str) -> tuple[str, str, int]:
    """(markup, logic, first_logic_line). The logic is the data-dc-script block's body."""
    m = re.search(r"^<script[^>]*data-dc-script[^>]*>$", text, re.M)
    if not m:
        return text, "", 1
    start = text.index("\n", m.end()) + 1
    close = re.search(r"^</script>\s*$", text[start:], re.M)
    end = start + (close.start() if close else len(text) - start)
    return text[:m.start()], text[start:end], text[:start].count("\n") + 1


def scan_js(code: str, first_line: int) -> list[str]:
    """Lexical scan. Returns a list of problems, each naming a line."""
    problems: list[str] = []
    stack: list[tuple[str, int]] = []
    i, line, n = 0, first_line, len(code)
    # Template-literal interpolation nesting. Each entry is the stack DEPTH at which that `${` sits.
    #
    # Depth, not merely a count: `${JSON.stringify({ a:1 })}` contains a brace of its own, and treating
    # the first `}` as the end of the interpolation puts the scanner back into template mode halfway
    # through an expression — which then reports three confident errors in correct code. A lint with
    # false positives is worse than no lint, because the next real one gets waved through too.
    tmpl: list[int] = []
    prev_sig = ""          # last significant char, to tell division from a regex literal

    while i < n:
        c = code[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        # comments
        if c == "/" and i + 1 < n and code[i + 1] == "/":
            i = code.find("\n", i)
            if i < 0:
                break
            continue
        if c == "/" and i + 1 < n and code[i + 1] == "*":
            j = code.find("*/", i + 2)
            if j < 0:
                problems.append(f"line {line}: block comment is never closed")
                break
            line += code.count("\n", i, j)
            i = j + 2
            continue
        # regex literal — only where a value may begin, otherwise it is division
        if c == "/" and prev_sig in "" "(,=:[!&|?{};+-*%~^<>" and prev_sig != "":
            j, cls = i + 1, False
            while j < n and code[j] not in "\n":
                if code[j] == "\\":
                    j += 2
                    continue
                if code[j] == "[":
                    cls = True
                elif code[j] == "]":
                    cls = False
                elif code[j] == "/" and not cls:
                    break
                j += 1
            if j < n and code[j] == "/":
                i = j + 1
                prev_sig = "/"
                continue
        # quoted strings — THE check: these may not cross a line break
        if c in "'\"":
            j = i + 1
            while j < n:
                if code[j] == "\\":
                    j += 2
                    continue
                if code[j] == "\n":
                    problems.append(
                        f"line {line}: unterminated {c!r} string — a quoted string cannot span a line "
                        f"break. This is what a mangled newline escape looks like.")
                    break
                if code[j] == c:
                    break
                j += 1
            if j >= n:
                problems.append(f"line {line}: {c!r} string runs to end of file")
                break
            i = j + 1
            prev_sig = c
            continue
        # template literal
        if c == "`":
            j = i + 1
            while j < n:
                if code[j] == "\\":
                    j += 2
                    continue
                if code[j] == "\n":
                    line += 1
                    j += 1
                    continue
                if code[j] == "$" and j + 1 < n and code[j + 1] == "{":
                    stack.append(("{", line))
                    tmpl.append(len(stack))
                    i = j + 2
                    prev_sig = "{"
                    break
                if code[j] == "`":
                    i = j + 1
                    prev_sig = "`"
                    break
                j += 1
            else:
                problems.append(f"line {line}: template literal runs to end of file")
                break
            continue
        if c in OPEN:
            stack.append((c, line))
        elif c in CLOSE:
            if not stack:
                problems.append(f"line {line}: stray {c!r} — nothing open to close")
            elif stack[-1][0] != PAIR[c]:
                op, ol = stack[-1]
                problems.append(f"line {line}: {c!r} closes {op!r} opened on line {ol}")
                stack.pop()
            else:
                closed_depth = len(stack)
                stack.pop()
                # Only the brace at the interpolation's own depth ends it. Anything deeper is an object
                # literal, a function body or a nested template inside the expression.
                if c == "}" and tmpl and closed_depth == tmpl[-1]:
                    tmpl.pop()
                    j = i + 1
                    while j < n:
                        if code[j] == "\\":
                            j += 2
                            continue
                        if code[j] == "\n":
                            line += 1
                        elif code[j] == "$" and j + 1 < n and code[j + 1] == "{":
                            stack.append(("{", line))
                            tmpl.append(len(stack))
                            j += 1
                            break
                        elif code[j] == "`":
                            break
                        j += 1
                    i = j + 1
                    prev_sig = "`"
                    continue
        if not c.isspace():
            prev_sig = c
        i += 1

    for op, ol in stack:
        problems.append(f"line {ol}: {op!r} is never closed")
    return problems


def check(path: str = SRC) -> int:
    text = open(path, encoding="utf-8").read()
    markup, logic, first = _regions(text)
    fails = 0

    def report(label: str, problems: list[str]) -> None:
        nonlocal fails
        if problems:
            fails += len(problems)
            print(f"  FAIL  {label} — {len(problems)} problem(s)")
            for p in problems[:12]:
                print(f"          {p}")
            if len(problems) > 12:
                print(f"          ... and {len(problems) - 12} more")
        else:
            print(f"  ok    {label}")

    # Characters and bytes are not the same number here — this file carries a few thousand
    # multi-byte characters, so `len(text)` is about 2,100 short of the file size. That was a
    # mislabel nobody paid for until the byte count became the check against a truncated
    # transfer: Design quoted this number as bytes, and a real byte count is what the check
    # needs. Both are printed now, because the character count is what the pairing checks below
    # operate on and the two disagreeing is worth seeing.
    _bytes = os.path.getsize(path)
    print(f"{os.path.relpath(path, ROOT)} — {_bytes:,} bytes — {len(text):,} chars, "
          f"{text.count(chr(10)) + 1:,} lines\n")

    report("JavaScript lexical structure", scan_js(logic, first))

    # The structural checks that did work, kept so one command covers everything.
    for tag in ("sc-if", "sc-for"):
        o = len(re.findall(rf"<{tag}[\s>]", markup))
        c = len(re.findall(rf"</{tag}>", markup))
        report(f"<{tag}> pairing ({o} open / {c} close)",
               [] if o == c else [f"{abs(o - c)} unmatched <{tag}>"])
    o, c = markup.count("<div"), markup.count("</div>")
    report(f"<div> pairing ({o} / {c})", [] if o == c else [f"{abs(o - c)} unmatched <div>"])

    # A ternary written directly inside a `{{ }}` interpolation hole. This file's own comments already
    # name two prior sightings of this exact class of bug (round 44/49's style-attribute ternary that
    # "renders once and never updates", round 93's `carouselManualBg`) — and a third, worse-symptomed
    # one (an EMPTY string, not a stale one) was found live on 22 Sep in an element's own text content,
    # invisible for weeks with a fully working click handler underneath it. Three sightings of the same
    # root cause is a pattern, not a coincidence — this is the fix for it not needing a fourth. The
    # remedy every time has been the same: precompute the value in the bag, bind a plain `{{ name }}`.
    # HTML comments are stripped first — two of them literally read `{{ x ? a : b }}` as a worked
    # example of the pattern to avoid, which is not a real occurrence.
    markup_no_comments = re.sub(r"<!--.*?-->", "", markup, flags=re.S)
    ternary_holes = re.findall(r"\{\{[^{}]*\?[^{}:]*:[^{}]*\}\}", markup_no_comments)
    report(f"no inline ternaries inside {{{{ }}}} holes ({len(ternary_holes)} found)",
           [f"a `{{{{ ... ? ... : ... }}}}` hole — precompute it in the bag instead: {t[:90]}"
            for t in ternary_holes])

    members = re.findall(r"^  ([A-Za-z_$][\w$]*)\s*[=(]", logic, re.M)
    dupes = sorted({m for m in members if members.count(m) > 1})
    report(f"class members unique ({len(members)} declared)",
           [f"{d!r} is declared more than once — the later one silently wins" for d in dupes])

    # Any argument list, not just `(s)`. A bag method may legitimately take more — `bagBriefs(s, imcBrief)`
    # does — and requiring a single argument reported it as never spread when it was spread on the very
    # next screen. A lint that raises a phantom failure is worse than no lint: the next real one gets
    # waved through with it.
    bag = re.findall(r"\.\.\.this\.(bag[A-Za-z]+)\s*\(", logic)
    defined = set(re.findall(r"^  (bag[A-Za-z]+)\s*\(", logic, re.M))
    report(f"bag methods composed ({len(bag)} spread in)",
           [f"{b}() is spread into the bag but never defined" for b in bag if b not in defined]
           + [f"{d}() is defined but never spread into the bag" for d in sorted(defined - set(bag))])

    # Every event handler the markup names has to reach the bag.
    #
    # `onChange="{{ onIdeaExpression }}"` on five textareas, with the method defined on the class and never
    # put in the bag. It resolves to undefined, so React gets a controlled field with no handler: it cannot
    # be typed into at all, and whatever is typed is reset by the next render. Nothing throws, nothing
    # looks wrong, and the field is simply dead — which is the worst kind of failure this file produces.
    #
    # The check above cannot see it: that one counts `...this.bagX()` spreads, not the keys inside them.
    # A dotted name (`{{ ex.rewrite }}`) belongs to a list item and is skipped — its shape is contract.py's
    # job. A bag key can be written `name:` or shorthand `name,`, and both count.
    handlers = sorted({m.group(1) for m in
                       re.finditer(r'on[A-Z][A-Za-z]*\s*=\s*"\{\{\s*([A-Za-z_$][\w$.]*)\s*\}\}"', markup)
                       if "." not in m.group(1)})
    unbagged = [h for h in handlers
                if not re.search(r"(?:^|[\s{,])" + re.escape(h) + r"\s*[:,]", logic, re.M)]
    report(f"template handlers reach the bag ({len(handlers)} named)",
           [f"{h!r} is used as a handler in the markup but is not a bag key — the control is dead"
            for h in unbagged])

    # 8. fixes that have been lost to a later round, and must not be lost again
    #
    # Three hunks have now been re-applied after a round was built on an older base: COL_HINT/pCols,
    # balBasisFg, and the H_LIVE Next pointer (that one twice, and it was a defect a person reported in
    # testing). A comment at the site did not stop it, because the site is not where a merge looks.
    #
    # So each entry is a sentinel a lost hunk cannot survive: the pattern that MUST be present, and the
    # pattern that must NOT be, which is the reverted form. Both directions matter — a file can carry
    # the new comment and the old code if a merge went line by line.
    #
    # Add to this only for a fix that has ACTUALLY been lost. A list of everything anyone ever wanted
    # would fail on legitimate rewrites and get deleted wholesale, which is worse than not having it.
    SENTINELS = [
        ("the house Next pointer reads the live layer list",
         r"const hIdx = H_LIVE\.findIndex",
         r"const hIdx = this\.H_LAYERS\.findIndex",
         "reverts to H_LAYERS and Next offers 'By medium', a retired layer the server does not serve"),
        ("the share column carries its rule (COL_HINT)",
         r"COL_HINT\s*=", r"hint:\s*c === 'role' \?",
         "reverts to the inline ternary and only `role` gets a header rule"),
        ("the actual-split warning colour reads the served flag",
         r"act\.trusted", r"balBasisFg:\s*\(act\.basis &&",
         "reverts to pattern-matching prose and the sum-mismatch warning renders grey"),
        ("the POS piece's line is editable",
         r"posmLineValue", r"line:kv\.line \|\| '', style",
         "reverts and a tagline settled after the key visual cannot reach the piece"),
    ]
    lost = []
    for label, must, must_not, why in SENTINELS:
        if not re.search(must, text):
            lost.append(f"{label}: gone — {why}")
        elif re.search(must_not, text):
            lost.append(f"{label}: the reverted form is also present — {why}")
    report(f"fixes lost before are still applied ({len(SENTINELS)} sentinels)", lost)

    print()
    if fails:
        print(f"{fails} problem(s). This does not prove the file runs, but each of these is real.")
    else:
        print("All checks passed. (Not proof it runs — no JS engine here — but the failure mode "
              "that has actually bitten this project is covered.)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(check(sys.argv[1] if len(sys.argv) > 1 else SRC))
