"""
Sentiment inputs for the benchmark.

Design notes (v2, 2026-09-24):
  * Positive templates only use POS-slot fillers; negative templates only
    use NEG-slot fillers.  A previous version reused `{p1}` in both, which
    made "clear negative" items read as positive to the lexicon.
  * `_fill` samples slot words WITHOUT replacement, so each template
    contributes at least as many distinct sentiment words as the number
    of slots it declares.  A CLEAR_POS_TMPL always yields >=2 distinct
    positive words; a CLEAR_NEG_TMPL always yields >=2 distinct negative
    words.
  * `decidable_split` and `sentiment_pairs` verify `_decisive(text)`
    against the actual generated string before emitting, and re-fill on
    the (now impossible) failure.  This closes the 4/600 dataset-vs-rule
    mismatch that the earlier run reported.

Public API:
  sentiment_pairs(n)          — mixed set with ground-truth labels
  decidable_split(n, dec_frac) — same, tagged decisive/ambiguous
  lexicon_decide(text)        — the tiny rule the overlay's fast-path uses
"""
import random

POS = ["excellent", "great", "amazing", "wonderful", "love", "fantastic",
       "best", "perfect", "delightful", "brilliant", "superb", "outstanding"]
NEG = ["terrible", "awful", "worst", "hate", "horrible", "disappointing",
       "broken", "useless", "poor", "boring", "disgusting", "waste"]
NEUT = ["arrived", "package", "product", "item", "yesterday", "colour",
        "size", "shipping", "box", "instructions", "assembly", "manual",
        "okay", "adequate", "expected", "delivered", "received", "unpacked"]

# Positive templates fill POS slots only.
CLEAR_POS_TMPL = [
    "This is a {p1} product, {p2} in every way, honestly {p3}.",
    "{p1} experience, {p2} quality, absolutely {p3} — will buy again.",
]
# Negative templates fill NEG slots only.
CLEAR_NEG_TMPL = [
    "A {n1} purchase, {n2} value and {n3} performance, do not recommend.",
    "{n1} and {n2}, honestly {n3} — waste of money and time.",
]
# Ambiguous templates mix one POS and one NEG so the lexicon abstains.
AMBIG_TMPL = [
    "The {u1} {u2} yesterday, {u3} was fine but the {u4} was {p1}.",
    "Product {u1}, {p1} {u2}, but {n1} {u3} though, overall {u4}.",
    "{u1} was {p1} but the {u2} felt {n1}, {u3} anyway.",
    "It {u1}. The {u2} is {u3}. Some parts {p1}, others {n1}.",
]


def _fill(tmpl, rng):
    """Fill a template.  {p*} slots draw distinct POS words, {n*} distinct
    NEG words, {u*} distinct NEUT words."""
    p = rng.sample(POS, min(3, len(POS)))
    n = rng.sample(NEG, min(3, len(NEG)))
    u = rng.sample(NEUT, min(4, len(NEUT)))
    return tmpl.format(
        p1=p[0], p2=p[1], p3=p[2],
        n1=n[0], n2=n[1], n3=n[2],
        u1=u[0], u2=u[1], u3=u[2], u4=u[3],
    )


def _hits(text):
    t = text.lower()
    p = sum(1 for w in POS if w in t)
    n = sum(1 for w in NEG if w in t)
    return p, n


def _label(text: str) -> int:
    p, n = _hits(text)
    if p > n: return 1
    if n > p: return 0
    return 1  # break ties positive


def _decisive(text: str) -> bool:
    p, n = _hits(text)
    return (p >= 2 and n == 0) or (n >= 2 and p == 0)


def _fill_until(tmpl, rng, want_decisive: bool, max_tries: int = 20) -> str:
    for _ in range(max_tries):
        text = _fill(tmpl, rng)
        if _decisive(text) == want_decisive:
            return text
    return text  # give up; unlikely to reach here with the current templates


def sentiment_pairs(n: int, seed: int = 42) -> list[dict]:
    """40% clear-positive, 40% clear-negative, 20% ambiguous."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        r = rng.random()
        if r < 0.4:
            text = _fill_until(rng.choice(CLEAR_POS_TMPL), rng, want_decisive=True)
        elif r < 0.8:
            text = _fill_until(rng.choice(CLEAR_NEG_TMPL), rng, want_decisive=True)
        else:
            text = _fill_until(rng.choice(AMBIG_TMPL), rng, want_decisive=False)
        out.append({"text": text, "label": _label(text), "decisive": _decisive(text)})
    return out


def decidable_split(n: int, decisive_frac: float = 0.6, seed: int = 42) -> list[dict]:
    """`decisive_frac` items are guaranteed lexicon-decisive (half pos, half neg);
    the rest are guaranteed lexicon-ambiguous."""
    rng = random.Random(seed)
    n_dec = int(round(n * decisive_frac))
    n_amb = n - n_dec
    out = []
    for i in range(n_dec):
        # alternate pos/neg so both classes are represented
        tmpl = rng.choice(CLEAR_POS_TMPL) if (i % 2 == 0) else rng.choice(CLEAR_NEG_TMPL)
        text = _fill_until(tmpl, rng, want_decisive=True)
        out.append({"text": text, "label": _label(text), "decisive": True})
    for _ in range(n_amb):
        text = _fill_until(rng.choice(AMBIG_TMPL), rng, want_decisive=False)
        out.append({"text": text, "label": _label(text), "decisive": False})
    rng.shuffle(out)
    return out


def lexicon_decide(text: str) -> tuple[int | None, bool]:
    """Return (predicted_label or None, decisive).  None means abstain."""
    p, n = _hits(text)
    if p >= 2 and n == 0: return 1, True
    if n >= 2 and p == 0: return 0, True
    return None, False
