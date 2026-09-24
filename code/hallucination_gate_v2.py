"""
Hallucination gate v2: value-aware, not string-matching.
Rules (principled, stated before testing):
 1. Parse numbers in digits, words ("six", "twelve thousand") and scale
    words ("1.2 million"); strip commas.
 2. Convert units to a base unit (length, mass, time, energy) before comparing.
 3. Precision-aware match: an answer number with k significant figures
    matches a source value if the source value rounds to it at k figures.
    Hedged numbers ("about", "around", "approximately", "~") allow one
    fewer significant figure.
 4. Derived percentages: p% matches if (b-a)/a*100 rounds to p for some
    source pair a < b.
 5. Claim binding: if content words surround the answer number, at least
    one must appear near the matched value in the source (+-12 words);
    otherwise the number is "right value, wrong claim".
 6. Citations: [n] or (Author, Year) must appear in the source.
Verdict: BLOCK if any number/citation is untraced or mis-bound, else ALLOW.
"""
import json, math, re, sys

WORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve "
         "thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split())}
WORDS.update({"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
              "seventy": 70, "eighty": 80, "ninety": 90})
SCALE = {"hundred": 1e2, "thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}
UNITS = {"km": ("L", 1e3), "m": ("L", 1), "cm": ("L", 1e-2), "mm": ("L", 1e-3),
         "mile": ("L", 1609.344), "miles": ("L", 1609.344), "mi": ("L", 1609.344),
         "ft": ("L", 0.3048), "feet": ("L", 0.3048), "metres": ("L", 1), "meters": ("L", 1),
         "kg": ("M", 1), "g": ("M", 1e-3), "t": ("M", 1e3), "tonnes": ("M", 1e3),
         "s": ("T", 1), "ms": ("T", 1e-3), "min": ("T", 60), "h": ("T", 3600),
         "day": ("T", 86400), "days": ("T", 86400), "week": ("T", 604800), "weeks": ("T", 604800),
         "month": ("T", 2629746), "months": ("T", 2629746), "year": ("T", 31556952), "years": ("T", 31556952),
         "mj": ("E", 1e6), "kj": ("E", 1e3), "j": ("E", 1), "gw": ("P", 1e9), "mw": ("P", 1e6),
         "hz": ("F", 1), "khz": ("F", 1e3), "mhz": ("F", 1e6), "ghz": ("F", 1e9), "thz": ("F", 1e12)}
HEDGE = {"about", "around", "approximately", "roughly", "nearly", "~", "circa"}
STOP = set("the a an of in on at to is was were are be this that it its and or as by for with from "
           "source sources states stated reports reported gives given shows value values measurement "
           "equals equal rise rises from about around approximately some which paper".split())
TOK = re.compile(r"~|\$|[A-Za-z]+|\d[\d,]*(?:\.\d+)?%?")
CITE = re.compile(r"\[(\d+)\]|\(([A-Z][A-Za-z\-]+(?: et al\.)?,? \d{4})\)")

def sig_figs(s):
    s = s.replace(",", "").rstrip("%").lstrip("0").replace(".", "") if "." in s else s.replace(",", "").rstrip("%").rstrip("0")
    return max(1, len(s.lstrip("0")))

def parse(text):
    """-> list of (value_base, dim, sigfigs, hedged, is_pct, token_index), tokens"""
    toks = TOK.findall(text); out = []; i = 0
    while i < len(toks):
        t = toks[i]; low = t.lower(); val = None; sf = None; pct = False; j = i + 1
        if re.match(r"\d", t):
            pct = t.endswith("%"); val = float(t.replace(",", "").rstrip("%")); sf = sig_figs(t)
        elif low in WORDS:
            val = float(WORDS[low]); sf = len(str(WORDS[low]).rstrip("0")) or 1
            if j < len(toks) and toks[j].lower() in WORDS and WORDS[toks[j].lower()] < 10 and val >= 20:
                val += WORDS[toks[j].lower()]; j += 1; sf = 2
        if val is not None:
            if j < len(toks) and toks[j].lower() in SCALE:
                val *= SCALE[toks[j].lower()]; j += 1
            dim, fac = "N", 1.0
            if j < len(toks) and toks[j].lower() in UNITS:
                dim, fac = UNITS[toks[j].lower()]; j += 1
            if j < len(toks) and toks[j] == "%": pct = True
            hedged = any(toks[k].lower() in HEDGE for k in range(max(0, i - 2), i))
            out.append((val * fac, "PCT" if pct else dim, sf, hedged, pct, i))
            i = j; continue
        i += 1
    return out, toks

def rounds_to(src, ans, sf):
    if src == 0 or ans == 0: return src == ans
    mag = math.floor(math.log10(abs(src)))
    return round(src, -int(mag - sf + 1)) == round(ans, -int(mag - sf + 1)) or \
           abs(src - ans) / abs(ans) < 1e-9

def context(toks, idx, w):
    return {t.lower() for t in toks[max(0, idx - w): idx + w + 1]
            if t.isalpha() and len(t) > 2 and t.lower() not in STOP and t.lower() not in WORDS and t.lower() not in SCALE and t.lower() not in UNITS}

def gate(source, answer):
    s_nums, s_toks = parse(source); a_nums, a_toks = parse(answer)
    problems = []
    for val, dim, sf, hedged, pct, idx in a_nums:
        k = max(1, sf - 1) if hedged else sf
        matches = [s for s in s_nums if (s[1] == dim or "N" in (s[1], dim)) and rounds_to(s[0], val, k)]
        if not matches and pct:          # derived percentage from a pair of source values
            vals = [s[0] for s in s_nums]
            if any(a > 0 and rounds_to((b - a) / a * 100, val, k) for a in vals for b in vals if b > a):
                continue
        if not matches:
            problems.append(("untraced number", val)); continue
        a_ctx = context(a_toks, idx, 6)
        if a_ctx and not any(a_ctx & context(s_toks, m[5], 12) for m in matches):
            problems.append(("number bound to a different claim", val))
    s_c = {a or b for a, b in CITE.findall(source)}
    for a, b in CITE.findall(answer):
        if (a or b) not in s_c: problems.append(("untraced citation", a or b))
    return ("BLOCK" if problems else "ALLOW"), problems

def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 2
    p = k / n; c = (p + z*z/(2*n)) / (1 + z*z/n); h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1 + z*z/n)
    return round(c - h, 3), round(c + h, 3)

if __name__ == "__main__":
    items = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8') if l.strip()]
    by = {}
    for it in items:
        v, _ = gate(it["source"], it["answer"])
        want = "BLOCK" if it["label"] == "fabricated" else "ALLOW"
        t = by.setdefault(it.get("mutation_type", "all"), [it["label"], 0, 0])
        t[1] += 1; t[2] += (v == want)
    tot = sum(t[2] for t in by.values()); n = sum(t[1] for t in by.values())
    for k, (lab, n_, ag) in by.items():
        print(f"{k:<22} {lab:<11} n={n_:<4} agree {ag/n_:.2f} {wilson(ag, n_)}")
    print(f"{'TOTAL':<34} n={n:<4} agree {tot/n:.2f} {wilson(tot, n)}")
