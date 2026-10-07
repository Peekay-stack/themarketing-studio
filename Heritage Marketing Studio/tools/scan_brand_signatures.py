"""scan_brand_signatures.py -- the STATIC half of the brand-agnostic audit (read only).

Every string literal (not docstrings) in every backend module, every skill file and every prompt line of the page, tagged brand / category / market.
A scan finds literal signatures, not behavioural defaults: pair it with tools/probe_brand_signatures.py. Writes a json report to %TEMP%.
See BRAND_AGNOSTIC_AUDIT_OTHER_SURFACES.md.

    python tools/scan_brand_signatures.py
"""
import ast, os, re, sys, json, collections
API = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))

BRAND = re.compile(r"\b(heritage|doodh|amul|nandini|dodla|arokya|parle|sthir|kumkum|loomwell)\b", re.I)
CATEGORY = re.compile(r"\b(milk|dairy|ghee|curd|paneer|cow|cows|cattle|fssai|pouch|sachet|kirana|tetra)\b", re.I)
MARKET = re.compile(r"\b(india|indian|hinglish|rupee|rupees|lakh|lakhs|crore|crores|saree|sari|chai|telugu|hyderabad|diwali|sankranti|kolkata|mumbai|delhi|bengaluru|bangalore|chennai|gst|upi|bharat)\b|₹", re.I)
ANY = re.compile(BRAND.pattern + "|" + CATEGORY.pattern + "|" + MARKET.pattern, re.I)

SKIP_FILES = re.compile(r"(\.bak|backup|_old|test_|selfcheck|smoke|\.venv|__pycache__|tenants|static|node_modules)", re.I)


def classify(text):
    out = []
    if BRAND.search(text): out.append("brand")
    if CATEGORY.search(text): out.append("category")
    if MARKET.search(text): out.append("market")
    return out


def py_strings(path):
    src = open(path, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    doc_nodes = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) \
                and isinstance(getattr(n.body[0], "value", None), ast.Constant) and isinstance(n.body[0].value.value, str):
            doc_nodes.add(id(n.body[0].value))
    # enclosing function per line
    spans = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            spans.append((n.lineno, getattr(n, "end_lineno", n.lineno), n.name))
    def func_at(line):
        best = None
        for a, b, nm in spans:
            if a <= line <= b and (best is None or a >= best[0]):
                best = (a, nm)
        return best[1] if best else "<module>"
    rows = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc_nodes and ANY.search(n.value):
            rows.append((n.lineno, func_at(n.lineno), tuple(classify(n.value)), n.value.strip().replace("\n", " ")[:170]))
    return sorted(set(rows))


report = collections.OrderedDict()
for fn in sorted(os.listdir(API)):
    p = os.path.join(API, fn)
    if fn.endswith(".py") and not SKIP_FILES.search(fn):
        rows = py_strings(p)
        if rows:
            report[fn] = rows
for d in sorted(os.listdir(API)):
    if d.endswith("_skill") and os.path.isdir(os.path.join(API, d)):
        f = os.path.join(API, d, "SKILL.md")
        if os.path.exists(f):
            rows = []
            for i, l in enumerate(open(f, encoding="utf-8").read().split("\n"), 1):
                if ANY.search(l):
                    rows.append((i, "SKILL.md", classify(l), l.strip()[:170]))
            if rows:
                report[d + "/SKILL.md"] = rows

# the page
html = open(os.path.join(API, "frontend", "app.dc.html"), encoding="utf-8").read().split("\n")
MEMBER = re.compile(r"^  (?:async )?([A-Za-z0-9_]+)\s*(?:=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_]+)\s*=>|\([^)]*\)\s*\{|=)")
cur = None
page = collections.defaultdict(list)
for i, l in enumerate(html, 1):
    m = MEMBER.match(l)
    if m:
        cur = m.group(1)
    st = l.strip()
    if st.startswith("//") or st.startswith("*") or st.startswith("<!--"):
        continue
    if ANY.search(l) and re.search(r"['\"`]", l):
        page[cur or "<template>"].append((i, classify(l), st[:170]))
json.dump({"py": {k: v for k, v in report.items()}, "page": page}, open(os.path.join(os.environ.get("TEMP", "."), "brand_signature_scan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("PY FILES with hits:")
for k, v in report.items():
    c = collections.Counter(x for r in v for x in r[2])
    print(f"  {k:34s} {len(v):4d}  {dict(c)}")
print("PAGE functions with hits:", len(page))
tot = collections.Counter()
for k, v in sorted(page.items(), key=lambda kv: -len(kv[1]))[:45]:
    c = collections.Counter(x for r in v for x in r[1])
    print(f"  {k:34s} {len(v):4d}  {dict(c)}")
