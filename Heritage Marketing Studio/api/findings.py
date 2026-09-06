"""findings.py — overriding a blocking finding, on the record.

A blocking finding can be **resolved** by fixing what it complains about, or **overridden** by someone
who accepts the risk and says why. It can never be dismissed. That rule existed in the handover before
this module did, and until now the client honoured it with a reason box that wrote to its own state —
which is a dismissal with better manners.

Findings are recomputed from the document on every read, so they have no stored identity. This gives
them one: a hash of `level|layer|detail`.

**The consequence of hashing the detail is the point, not a limitation.** An override is attached to
one exact sentence. When the underlying facts move, the sentence moves with them:

    "POSM is given proof work against the functional pillar, which has 0 of 2 RTBs sourced."
    "POSM is given proof work against the functional pillar, which has 1 of 2 RTBs sourced."

Those are different keys, so the second finding arrives un-overridden and has to be looked at again.
Somebody accepting a risk at nothing-sourced has not accepted it at one-of-two — the situation they
signed off no longer exists. A stored finding id would have carried the old signature forward silently,
which is exactly the failure this design refuses.

Overridden findings are never removed from the list. They are annotated, kept in place, and counted
separately, so a document with three overridden blockers reads as a document with three overridden
blockers rather than a clean one.
"""
from __future__ import annotations

import hashlib
import time

# Only these can be overridden. An `empty` or `stale` finding is not a judgement anyone needs to
# accept the risk of — it is a fact about the document that resolves itself when the document changes.
OVERRIDABLE = ("blocking", "unsourced", "open")


def key(f: dict) -> str:
    """A stable id for a finding, derived from what it says rather than when it was made."""
    basis = "|".join([str(f.get("level", "")), str(f.get("layer", "")), str(f.get("detail", ""))])
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]


def annotate(findings: list[dict], overrides: dict | None) -> list[dict]:
    """Give every finding its key, and attach the override where one is on file."""
    overrides = overrides or {}
    out = []
    for f in findings:
        k = key(f)
        rec = dict(f)
        rec["key"] = k
        rec["can_override"] = f.get("level") in OVERRIDABLE
        if k in overrides:
            rec["overridden"] = overrides[k]
        out.append(rec)
    return out


def record(doc: dict, finding_key: str, reason: str, who: str = "") -> tuple[dict, str]:
    """Accept the risk, in writing. Returns (doc, error). A reason is not optional.

    Refusing an empty reason is the whole mechanism. An override with no reason is a dismissal, and
    six months later the only difference between a considered risk and a shrug is this sentence.
    """
    reason = (reason or "").strip()
    if not reason:
        return doc, "An override needs a reason. Without one it is a dismissal, which this does not do."
    if len(reason) < 12:
        return doc, ("Give a sentence, not a word — this is what somebody reads in six months when "
                     "they ask why this shipped.")
    doc.setdefault("overrides", {})[finding_key] = {
        "reason": reason,
        "who": (who or "").strip() or "unattributed",
        "at": time.strftime("%Y-%m-%d %H:%M", time.localtime()),
    }
    return doc, ""


def clear(doc: dict, finding_key: str) -> dict:
    """Withdraw an override. The finding goes back to blocking, which is the honest default."""
    (doc.get("overrides") or {}).pop(finding_key, None)
    return doc


def live_blocking(findings: list[dict]) -> list[dict]:
    """Blocking findings that are still in force — an override is what lets work continue."""
    return [f for f in findings if f.get("level") == "blocking" and "overridden" not in f]


def overridden_count(findings: list[dict]) -> int:
    return sum(1 for f in findings if "overridden" in f)


def stranded(findings: list[dict], overrides: dict | None) -> list[dict]:
    """Overrides whose finding no longer fires — the risk was accepted and then removed.

    An override is keyed to one exact sentence. When somebody accepts a risk and *then fixes the
    underlying thing*, the sentence stops being generated and the override is left attached to nothing.
    It is invisible: it does not appear in the findings list, because there is no finding to attach it to.

    That matters more than it sounds. It happened in testing: a blocking finding was overridden with
    "I have added the numbers", the numbers were then actually added, and the override stayed on file
    against a sentence that no longer exists. The next person to read the document sees an accepted risk
    in the record with no risk behind it, and has no way to tell whether it was resolved or forgotten.

    Reported rather than deleted on sight, because removing it silently is the same class of mistake in
    the other direction.
    """
    live = {f.get("key") for f in findings}
    return [{"key": k, **(v if isinstance(v, dict) else {"reason": str(v)})}
            for k, v in (overrides or {}).items() if k not in live]


def counts(findings: list[dict], overrides: dict | None = None) -> dict:
    """The numbers a banner should show, computed once here rather than filtered on the client.

    The screen was reading the raw list and saying "2 BLOCKING FINDINGS - RESOLVE OR OVERRIDE" on a
    document with one blocking finding and one already overridden, so it went on demanding action on
    something that had been actioned. There is no version of that count worth deriving twice.
    """
    blocking = [f for f in findings if f.get("level") == "blocking"]
    open_ = [f for f in blocking if "overridden" not in f]
    over = [f for f in blocking if "overridden" in f]
    return {
        "blocking_open": len(open_),
        "blocking_overridden": len(over),
        "overridden_total": overridden_count(findings),
        "stranded": stranded(findings, overrides),
        "headline": (
            "Nothing blocking." if not blocking else
            (f"{len(open_)} blocking" if open_ else "")
            + (" · " if open_ and over else "")
            + (f"{len(over)} overridden" if over else "")),
    }
