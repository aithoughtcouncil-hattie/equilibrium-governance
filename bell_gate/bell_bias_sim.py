"""
Bell-test detection-bias simulation (CHSH, fair-sampling loophole).

A purely LOCAL, classical hidden-variable model:
  - hidden polarisation angle lam, uniform on [0, pi)
  - each side's outcome is set locally: A = sign(cos 2(a - lam))
  - each detector fires only if |cos 2(a - lam)| >= t   (setting-dependent
    detection, i.e. biased detection; t = 0 means every event is detected)
CHSH correlations are computed on coincidences only, as in a real
experiment that discards non-detections.

With t = 0 the model obeys the classical bound S <= 2. As t rises, the
postselected S climbs past 2, past the quantum (Tsirelson) limit 2*sqrt(2),
towards 4 - with no quantum physics at all. The tell is the detection
efficiency, which falls as S rises. With conditional (coincidence) efficiency
eta, local models can reach a postselected S of up to 4/eta - 2 (Larsson 1998),
so a violation is only evidence of non-locality if S exceeds that bound.
S_quantum = 2*sqrt(2) can beat it only when eta > 2/(1+sqrt 2) ~ 0.828
(Garg-Mermin). The audit gate tests S against 4/eta - 2, not against 2.

Deterministic grid integration: reproducible, no random seed needed.
Values are exact model expectations. For measured data, S and eta carry
sampling uncertainty: a gate must compare confidence bounds, and an estimate
slightly above 2*sqrt(2) is not by itself proof of a fault.
"PASSES BOUND CHECK" means only that: passes this check under the stated
assumptions. It is not verification of entanglement.
Usage:  python bell_bias_sim.py            (prints table, writes plot)
"""
import numpy as np

N = 2_000_000                                   # grid points over lam
LAM = (np.arange(N) + 0.5) * np.pi / N
A, A2, B, B2 = np.radians([0, 45, 22.5, 67.5])  # standard CHSH angles
TSIRELSON = 2 * np.sqrt(2)
ETA_GM = 2 / (1 + np.sqrt(2))                   # Garg-Mermin threshold

def side(theta, t):
    c = np.cos(2 * (theta - LAM))
    return np.sign(c), np.abs(c) >= t           # outcome, detected?

def E(a, b, t):
    oa, da = side(a, t)
    ob, db = side(b, t)
    both = da & db
    return np.mean(oa[both] * ob[both]), both.mean()

def run(t):
    pairs = [(A, B), (A, B2), (A2, B), (A2, B2)]
    res = [E(a, b, t) for a, b in pairs]
    e = [r[0] for r in res]
    S = e[0] - e[1] + e[2] + e[3]
    # conditional efficiency: P(other side fires | this side fired), worst case
    eta = min(r[1] / side(x, t)[1].mean()
              for r, (a, b) in zip(res, pairs) for x in (a, b))
    return S, eta

def local_bound(eta):
    return min(4.0, 4 / eta - 2)               # Larsson 1998

def gate(S, eta):
    if S > TSIRELSON + 1e-9:
        return "REJECT: exceeds Tsirelson -> measurement fault or bias"
    if S <= 2 + 1e-6:
        return "NO VIOLATION"
    if S <= local_bound(eta) + 1e-6:           # tolerance for grid rounding
        return f"REJECT: S <= local bound {local_bound(eta):.3f} -> loophole open"
    return "PASSES BOUND CHECK (assumptions stated)"

if __name__ == "__main__":
    print(f"Tsirelson 2*sqrt(2) = {TSIRELSON:.4f}   Garg-Mermin eta = {ETA_GM:.4f}\n")
    print(f"{'t':>5} {'eta':>7} {'S':>7} {'4/eta-2':>8}  audit gate")
    ts = np.round(np.arange(0, 0.45, 0.05), 2)
    rows = [(t, *run(t)) for t in ts]
    for t, S, eta in rows:
        print(f"{t:5.2f} {eta:7.3f} {S:7.3f} {local_bound(eta):8.3f}  {gate(S, eta)}")

    # headline case: fools the naive S > 2 rule, stays below Tsirelson
    S, eta = run(0.20)
    print(f"\nHeadline: S = {S:.3f} at eta = {eta:.3f}")
    print(f"  naive rule (S > 2):        {'PASS' if S > 2 else 'FAIL'}  <- fooled")
    print(f"  Tsirelson check (<= 2.828): {'ok' if S <= TSIRELSON else 'fail'}")
    print(f"  detection-aware gate:      {gate(S, eta)}")
    h_S, h_eta = S, eta

    # threshold that reproduces S ~ 3.28
    from scipy.optimize import brentq
    t328 = brentq(lambda t: run(t)[0] - 3.28, 0.25, 0.39)
    S, eta = run(t328)
    print(f"\nS = {S:.3f} reached at t = {t328:.3f}, detection efficiency eta = {eta:.3f}")
    print(f"Audit gate: {gate(S, eta)}")

    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fine = np.linspace(0, 0.40, 60)
    SS, EE = zip(*[run(t) for t in fine])
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(EE, SS, lw=2, label="local model, coincidences only")
    ax.axhline(2, ls="--", c="grey", label="classical bound 2")
    ax.axhline(TSIRELSON, ls=":", c="k", label="Tsirelson 2√2")
    ax.plot(EE, [local_bound(e) for e in EE], c="r", alpha=.6, label="local bound 4/η − 2")
    ax.axvline(ETA_GM, c="r", ls="--", alpha=.4, label="Garg–Mermin η ≈ 0.828")
    ax.scatter([eta], [S], c="r", zorder=5)
    ax.annotate(f"S = {S:.2f} (rejected by Tsirelson)", (eta, S), (0.80, 3.6))
    ax.scatter([h_eta], [h_S], c="orange", zorder=5)
    ax.annotate(f"S = {h_S:.2f}: fools S>2, caught by 4/η−2", (h_eta, h_S), (0.99, 2.2))
    ax.invert_xaxis(); ax.set_xlabel("conditional detection efficiency η"); ax.set_ylabel("CHSH S")
    ax.set_title("Biased detection lets a classical model 'violate' Bell")
    ax.legend(fontsize=8, loc="upper left"); fig.tight_layout()
    fig.savefig("bell_bias_S_vs_eta.png", dpi=150)
    print("wrote bell_bias_S_vs_eta.png")
