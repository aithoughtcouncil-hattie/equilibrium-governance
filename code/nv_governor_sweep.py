"""
NV governor sweep: calibrate -> freeze -> test.   SIMULATION, not hardware data.

Physics (standard, exact for a square pulse on a two-level system):
  Rabi formula  P_flip = W^2/(W^2+D^2) * sin^2( sqrt(W^2+D^2) * t / 2 ),
  with intended pi-pulse t = pi / W_nominal.
  W = drive strength (Rabi, angular), D = detuning from resonance.
  Amplitude drift: W_actual = W_nominal * (1 + eps).
Readout: Poisson photon counts, bright mean 0.12, dark mean 0.084 per shot
  (30% contrast), so population estimates carry realistic shot noise.

Question the sweep answers:
  (A) How does pi-pulse fidelity depend on drive strength under detuning drift?
  (B) Does a per-batch governor (ICE) accept fewer bad batches than periodic
      calibration, without rejecting too many good ones?
Method (gold standard):
  1. KNOWN-VALUE CHECKS on the physics model before anything else.
  2. CALIBRATE governor limits on pilot seeds only.
  3. FREEZE the limits (written to file, hashed).
  4. TEST on held-out seeds, including fault sizes never seen in calibration.
  Reference labels use a finite-shot fidelity estimate with a Wilson 95% CI;
  batches whose CI straddles the threshold are INDETERMINATE and reported.
"""
import hashlib, json, math
import numpy as np

MU_B, MU_D = 0.12, 0.084          # photons per shot, bright / dark
F_MIN = 0.95                      # operational pi-pulse fidelity threshold
REF_SHOTS = 200_000               # reference-measurement shots per batch

def p_flip(W, D, eps=0.0):
    Wa = W * (1 + eps)
    R = math.hypot(Wa, D)
    t = math.pi / W
    return (Wa / R) ** 2 * math.sin(R * t / 2) ** 2

def known_value_checks():
    ok = []
    ok.append(("on resonance, no drift -> 1", abs(p_flip(1, 0) - 1) < 1e-12))
    # D = W: P = 0.5 sin^2(pi/sqrt2)
    ok.append(("D = W -> 0.5 sin^2(pi/sqrt2)", abs(p_flip(1, 1) - 0.5 * math.sin(math.pi / math.sqrt(2)) ** 2) < 1e-12))
    ok.append(("eps = +100% (2pi pulse) -> 0", abs(p_flip(1, 0, 1.0)) < 1e-12))
    ok.append(("small eps: 1 - P ~ (pi eps / 2)^2", abs((1 - p_flip(1, 0, 0.01)) - (math.pi * 0.01 / 2) ** 2) < 1e-6))
    return ok

def estimate_pop(p, shots, rng):
    """Population estimate from Poisson counts (the actual readout model)."""
    mu = MU_B * (1 - p) + MU_D * p
    counts = rng.normal(mu, math.sqrt(mu / shots))   # mean of Poisson counts (CLT)
    return np.clip((MU_B - counts) / (MU_B - MU_D), 0, 1)

def wilson(phat, n, z=1.96):
    # effective n shrinks by readout contrast: var(p_hat) ~ mu/(n (dmu)^2)
    n_eff = n * (MU_B - MU_D) ** 2 / MU_B
    c = (phat + z*z/(2*n_eff)) / (1 + z*z/n_eff)
    h = z * math.sqrt(phat*(1-phat)/n_eff + z*z/(4*n_eff*n_eff)) / (1 + z*z/n_eff)
    return c - h, c + h

def campaign(seed, W, n_batches, faults, calib_every, lim, rng_shots=4_000):
    """One session. Returns per-batch (label, ICE decision, baseline decision)."""
    rng = np.random.default_rng(seed)
    D, eps = 0.0, 0.0
    out, base_ok = [], True
    fault_at = {int(b): (k, m) for b, k, m in faults}
    for j in range(n_batches):
        D += rng.normal(0, 0.004 * W); eps += rng.normal(0, 0.002)   # slow drift
        if j in fault_at:
            kind, mag = fault_at[j]
            if kind == "detune": D += mag * W
            else: eps += mag
        if j % calib_every == 0:                      # scheduled calibration (both policies)
            D, eps = D * 0.1, eps * 0.1                 # re-centres the drive
        # governor diagnostics: Ramsey-style detuning estimate + amplitude check, noisy
        D_hat = D + rng.normal(0, lim["meas_sd_D"] * W)
        e_hat = eps + rng.normal(0, lim["meas_sd_e"])
        ice = abs(D_hat) < lim["D_lim"] * W and abs(e_hat) < lim["e_lim"]
        if j % calib_every == 0:                      # baseline checks only at calibration
            base_ok = ice
        # withheld reference measurement -> label
        f_true = p_flip(W, D, eps)
        lo, hi = wilson(estimate_pop(f_true, REF_SHOTS, rng), REF_SHOTS)
        label = "bad" if hi < F_MIN else ("good" if lo >= F_MIN else "indet")
        out.append((label, ice, base_ok, f_true))
    return out

def rates(rows, idx):
    bad = [r for r in rows if r[0] == "bad"]; good = [r for r in rows if r[0] == "good"]
    baf = sum(r[idx] for r in bad) / len(bad) if bad else float("nan")
    grf = sum(not r[idx] for r in good) / len(good) if good else float("nan")
    return baf, grf, len(bad), len(good), sum(r[0] == "indet" for r in rows)

def faults_for(seed, mags):
    rng = np.random.default_rng(seed + 999)
    return [(b, rng.choice(["detune", "amp"]), rng.choice(mags) * rng.choice([-1, 1]))
            for b in sorted(rng.choice(np.arange(5, 200), 25, replace=False))]

if __name__ == "__main__":
    print("1. KNOWN-VALUE CHECKS")
    for name, ok in known_value_checks(): print(f"   {'PASS' if ok else 'FAIL'}  {name}")

    print("\n2. SWEEP (A): mean pi-pulse fidelity vs drive strength, detuning spread 0.1 MHz")
    rng = np.random.default_rng(0)
    Dspread = 2 * math.pi * 0.1                       # rad/us
    for f_rabi in (0.5, 1, 2, 5, 10, 20):            # MHz
        W = 2 * math.pi * f_rabi
        F = np.mean([p_flip(W, d) for d in rng.normal(0, Dspread, 2000)])
        print(f"   Rabi {f_rabi:>5} MHz  mean F = {F:.4f}")
    print("   -> stronger drive is more robust to detuning drift (known result);")
    print("      real limits (heating, pulse distortion) are NOT modelled.")

    W = 2 * math.pi * 5                               # choose 5 MHz, fixed before step 3
    print("\n3. CALIBRATE governor limits on pilot seeds 0-4 (fault sizes 0.05-0.15)")
    best = None
    for D_lim in (0.06, 0.10, 0.15, 0.20):
        for e_lim in (0.04, 0.07, 0.10, 0.13):
            lim = {"D_lim": D_lim, "e_lim": e_lim, "meas_sd_D": 0.02, "meas_sd_e": 0.02}
            rows = [r for s in range(5) for r in
                    campaign(s, W, 200, faults_for(s, [0.05, 0.10, 0.15]), 25, lim)]
            baf, grf, *_ = rates(rows, 1)
            score = baf + grf
            if best is None or score < best[0]: best = (score, lim, baf, grf)
    lim = best[1]
    frozen = json.dumps(lim, sort_keys=True)
    h = hashlib.sha256(frozen.encode()).hexdigest()
    open("frozen_policy.json", "w").write(frozen)
    print(f"   chosen: {frozen}")
    print(f"   pilot: BAF {best[2]:.3f}, GRF {best[3]:.3f}")
    print(f"   FROZEN. sha256 = {h[:16]}...  (any change after this point is visible)")

    print("\n4. TEST on held-out seeds 100-119, including unseen fault sizes 0.03 and 0.25")
    rows = [r for s in range(100, 120) for r in
            campaign(s, W, 200, faults_for(s, [0.03, 0.10, 0.25]), 25, lim)]
    for name, idx in (("ICE per-batch governor", 1), ("Periodic calibration", 2)):
        baf, grf, nb, ng, ni = rates(rows, idx)
        print(f"   {name:<24} BAF {baf:.3f}   GRF {grf:.3f}")
    print(f"   reference labels: {nb} bad, {ng} good, {ni} indeterminate (reported, not dropped)")
    ib, ig, *_ = rates(rows, 1); bb, bg, *_ = rates(rows, 2)
    print("\n5. PRE-STATED TARGETS (from the protocol, fixed before the test)")
    print(f"   BAF at most half of baseline:  {'MET' if ib <= bb / 2 else 'NOT MET'} ({ib:.3f} vs {bb:.3f})")
    print(f"   GRF no greater than 0.05:      {'MET' if ig <= 0.05 else 'NOT MET'} ({ig:.3f})")
    print("   Not re-tuned after seeing these results. Caveats: point estimates only;")
    print("   batches within a session are correlated, so proper CIs need a cluster-aware method.")


# ---------------------------------------------------------------------------
# VERSION 2 - a new frozen policy, not a re-tune of v1.
# Changes (stated before testing):
#   (a) gate on PREDICTED FIDELITY from the Rabi formula, not a box of limits;
#   (b) calibrate to the protocol's actual objective: minimise BAF subject to
#       pilot GRF <= 0.05;
#   (c) test on NEW held-out seeds 200-219 (v1's test seeds are now used up).
# ---------------------------------------------------------------------------
def campaign_v2(seed, W, n_batches, faults, calib_every, k, sd=0.02):
    rng = np.random.default_rng(seed)
    D, eps, out = 0.0, 0.0, []
    fault_at = {int(b): (kd, m) for b, kd, m in faults}
    for j in range(n_batches):
        D += rng.normal(0, 0.004 * W); eps += rng.normal(0, 0.002)
        if j in fault_at:
            kind, mag = fault_at[j]
            if kind == "detune": D += mag * W
            else: eps += mag
        if j % calib_every == 0:
            D, eps = D * 0.1, eps * 0.1
        D_hat = D + rng.normal(0, sd * W); e_hat = eps + rng.normal(0, sd)
        # pessimistic predicted fidelity: shift each estimate k sd away from ideal
        worst_D = abs(D_hat) + k * sd * W
        worst_e = e_hat + math.copysign(k * sd, e_hat)
        ice = p_flip(W, worst_D, worst_e) >= F_MIN
        f_true = p_flip(W, D, eps)
        lo, hi = wilson(estimate_pop(f_true, REF_SHOTS, rng), REF_SHOTS)
        label = "bad" if hi < F_MIN else ("good" if lo >= F_MIN else "indet")
        out.append((label, ice, None, f_true))
    return out

if __name__ == "__main__":
    print("\n" + "=" * 70 + "\nVERSION 2: predicted-fidelity gate, calibrated to the real objective")
    best = None
    for k in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
        rows = [r for s in range(5) for r in
                campaign_v2(s, W, 200, faults_for(s, [0.05, 0.10, 0.15]), 25, k)]
        baf, grf, *_ = rates(rows, 1)
        feasible = grf <= 0.05
        print(f"   pilot k={k:<4} BAF {baf:.3f}  GRF {grf:.3f}  {'ok' if feasible else 'GRF too high'}")
        if feasible and (best is None or baf < best[1]): best = (k, baf, grf)
    k = best[0]
    h2 = hashlib.sha256(json.dumps({"v": 2, "k": k}).encode()).hexdigest()
    print(f"   chosen k = {k} (lowest pilot BAF with GRF <= 0.05). FROZEN sha256 = {h2[:16]}...")
    rows = [r for s in range(200, 220) for r in
            campaign_v2(s, W, 200, faults_for(s, [0.03, 0.10, 0.25]), 25, k)]
    baf, grf, nb, ng, ni = rates(rows, 1)
    print(f"   TEST seeds 200-219:  BAF {baf:.3f}   GRF {grf:.3f}   ({nb} bad, {ng} good, {ni} indeterminate)")
    print(f"   BAF at most half of baseline (1.000): {'MET' if baf <= 0.5 else 'NOT MET'}")
    print(f"   GRF no greater than 0.05:             {'MET' if grf <= 0.05 else 'NOT MET'}")


# ---------------------------------------------------------------------------
# VERSION 3 - two-system double check. New frozen policies; new test seeds 300-319.
#   single : one diagnostic (v2)
#   AND    : two diagnostics, batch passes only if BOTH predict F >= F_MIN
#   AVG    : average the two diagnostics, then one prediction
# "shared" = fraction of diagnostic error common to both checks (e.g. same
# calibration reference). 0 = fully independent, 1 = the checks are the same.
# ---------------------------------------------------------------------------
def campaign_v3(seed, W, n_batches, faults, calib_every, k, mode, shared, sd=0.02):
    rng = np.random.default_rng(seed)
    D, eps, out = 0.0, 0.0, []
    fault_at = {int(b): (kd, m) for b, kd, m in faults}
    a, b = math.sqrt(shared), math.sqrt(1 - shared)   # keeps each check's total sd = sd
    def predicted_ok(Dh, eh, s):
        return p_flip(W, abs(Dh) + k * s * W, eh + math.copysign(k * s, eh)) >= F_MIN
    for j in range(n_batches):
        D += rng.normal(0, 0.004 * W); eps += rng.normal(0, 0.002)
        if j in fault_at:
            kind, mag = fault_at[j]
            if kind == "detune": D += mag * W
            else: eps += mag
        if j % calib_every == 0:
            D, eps = D * 0.1, eps * 0.1
        cD, ce = rng.normal(0, sd * W), rng.normal(0, sd)          # shared error
        est = [(D + a*cD + b*rng.normal(0, sd*W), eps + a*ce + b*rng.normal(0, sd)) for _ in range(2)]
        if mode == "single":
            ok = predicted_ok(*est[0], sd)
        elif mode == "AND":
            ok = all(predicted_ok(Dh, eh, sd) for Dh, eh in est)
        else:  # AVG: error of the mean shrinks only by the independent part
            s_avg = sd * math.sqrt(shared + (1 - shared) / 2)
            ok = predicted_ok((est[0][0] + est[1][0]) / 2, (est[0][1] + est[1][1]) / 2, s_avg)
        f_true = p_flip(W, D, eps)
        lo, hi = wilson(estimate_pop(f_true, REF_SHOTS, rng), REF_SHOTS)
        out.append(("bad" if hi < F_MIN else ("good" if lo >= F_MIN else "indet"), ok, None, f_true))
    return out

def calibrate_and_test(mode, shared):
    best = None
    for k in (0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0):
        rows = [r for s in range(5) for r in
                campaign_v3(s, W, 200, faults_for(s, [0.05, 0.10, 0.15]), 25, k, mode, shared)]
        baf, grf, *_ = rates(rows, 1)
        if grf <= 0.05 and (best is None or baf < best[1]): best = (k, baf)
    k = best[0]
    rows = [r for s in range(300, 320) for r in
            campaign_v3(s, W, 200, faults_for(s, [0.03, 0.10, 0.25]), 25, k, mode, shared)]
    baf, grf, *_ = rates(rows, 1)
    return k, baf, grf

if __name__ == "__main__":
    print("\n" + "=" * 70 + "\nVERSION 3: two-system double check (test seeds 300-319)")
    print(f"   {'mode':<7} {'shared err':>10} {'k':>5} {'BAF':>7} {'GRF':>7}  targets")
    for mode, shared in (("single", 0.0), ("AND", 0.0), ("AVG", 0.0), ("AND", 0.8), ("AVG", 0.8)):
        k, baf, grf = calibrate_and_test(mode, shared)
        met = "both met" if (baf <= 0.5 and grf <= 0.05) else "NOT met"
        print(f"   {mode:<7} {shared:>10.1f} {k:>5} {baf:>7.3f} {grf:>7.3f}  {met}")
    print("   Two checks cost twice the diagnostic time; that cost is not yet counted.")
