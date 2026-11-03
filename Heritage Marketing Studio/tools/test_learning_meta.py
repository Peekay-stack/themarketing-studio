#!/usr/bin/env python
"""test_learning_meta.py -- offline checks for workstream W10 of FILM_CRAFT_LAYER_PLAN.md: an approved film is kept as an anchor WITH what was known about it (the craft scorecard, the concept's craft
lines), bounded, and an approval without `meta` is stored exactly as before. Runs against a throw-away data directory, so no tenant file is touched.
Run:  api/.venv/Scripts/python.exe tools/test_learning_meta.py
"""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix="tms-learn-")
os.environ["STUDIO_DATA_DIR"] = TMP; os.environ["GOOGLE_API_KEY"] = "test-key"
sys.path.insert(0, os.path.join(ROOT, "api")); os.chdir(os.path.join(ROOT, "api"))
import learning, main

fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if (extra and not cond) else ""))
    if not cond: fails.append(name)

check("the data directory is the throw-away one (no tenant file can be touched)", os.path.realpath(learning._examples()).startswith(os.path.realpath(TMP)), learning._examples())

META = {"craft_score": {"total": 15, "max": 21, "weakest": "device", "tests": [["message", 3], ["device", 1]]}, "craft_lines": {"device": "the sniff"}, "entertain": {"hook": "h", "memorable": "m"}}
r = main.learning_decision({"kind": "film", "decision": "approve", "subject": "Cut A", "body": "SCRIPT TEXT", "brief": "A grandmother tests milk.", "meta": META})
ex = [e for e in learning._read(learning._examples()) if e["title"] == "Cut A"]
check("an approval with meta keeps the example WITH the meta", len(ex) == 1 and ex[0]["meta"] == META, ex)
dec = [d for d in learning._read(learning._decisions()) if d["subject"] == "Cut A"]
check("the decision row carries the same meta (it already did)", len(dec) == 1 and dec[0]["meta"] == META)

main.learning_decision({"kind": "film", "decision": "approve", "subject": "Cut B", "body": "SCRIPT B", "brief": "b"})
b = [e for e in learning._read(learning._examples()) if e["title"] == "Cut B"][0]
check("an approval without meta is stored as before (meta is an empty object)", b["meta"] == {} and b["body"] == "SCRIPT B")

main.learning_decision({"kind": "film", "decision": "approve", "subject": "Cut C", "body": "SCRIPT C", "meta": {"junk": "x" * 5000}})
c = [e for e in learning._read(learning._examples()) if e["title"] == "Cut C"][0]
check("oversized meta is not kept with the example (bounded at 4000 characters)", c["meta"] == {} and c["body"] == "SCRIPT C")

main.learning_decision({"kind": "film", "decision": "approve", "subject": "Cut D", "body": "SCRIPT D", "meta": "not a dict"})
d = [e for e in learning._read(learning._examples()) if e["title"] == "Cut D"][0]
check("meta that is not an object is ignored", d["meta"] == {})

rej = main.learning_decision({"kind": "film", "decision": "reject", "subject": "Cut E", "reason": "flat", "body": "SCRIPT E", "meta": META})
check("a rejection records its meta in the decision log and keeps no example", not [e for e in learning._read(learning._examples()) if e["title"] == "Cut E"]
      and [x for x in learning._read(learning._decisions()) if x["subject"] == "Cut E"][0]["meta"] == META)

blk, names = learning.anchor_block("film", "grandmother tests milk", 3)
check("retrieval still works and shows the body, not the meta", "SCRIPT TEXT" in blk and "craft_score" not in blk, blk[:200])

print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)
