"""
Orchestrator.

  python bench/runner.py                    # full run: 60s idle, 3 reps each
  python bench/runner.py --quick            # smoke test: 20s idle, 1 rep, N=200
  python bench/runner.py --no-idle          # skip idle baseline
  python bench/runner.py --n 500 --reps 2   # override

Writes bench/results.json.  Then run:  python bench/report.py
"""
import argparse, gc, json, os, sys, time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from common import (measure, idle_baseline, summarise_reps,
                    env_fingerprint, lhm_read_once)
from dataset import sentiment_pairs, decidable_split
from workloads import (workload_A1_overlay_only, workload_A2_distilbert_only,
                       workload_B1_distilbert_alone, workload_B2_cascade)

WORKLOADS = {
    "A1_overlay_only":     ("Comparison A", workload_A1_overlay_only,     "sentiment"),
    "A2_distilbert_only":  ("Comparison A", workload_A2_distilbert_only,  "sentiment"),
    "B1_distilbert_alone": ("Comparison B", workload_B1_distilbert_alone, "mixed"),
    "B2_cascade":          ("Comparison B", workload_B2_cascade,          "mixed"),
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--idle-s", type=float, default=60.0)
    ap.add_argument("--no-idle", action="store_true")
    ap.add_argument("--decisive-frac", type=float, default=0.6)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--only", default=None, help="comma list of workload keys")
    ap.add_argument("--out", default=os.path.join(_HERE, "results.json"))
    args = ap.parse_args()

    if args.quick:
        args.n, args.reps, args.idle_s = 200, 1, 20.0

    env = env_fingerprint()
    lhm_ok = lhm_read_once() is not None
    env["lhm_available"] = lhm_ok
    if not lhm_ok:
        print("[warn] LibreHardwareMonitor not detected — energy will be CPU-time estimate only.")

    print(f"[env] {env['processor']} | {env['cpu_count_physical']}c/{env['cpu_count_logical']}t | "
          f"{env['total_ram_gb']} GB RAM | Python {env['python']}")
    print(f"[run] N={args.n}  reps={args.reps}  idle={args.idle_s}s "
          f"decisive_frac={args.decisive_frac}  LHM={'yes' if lhm_ok else 'no'}")

    # ---- idle baseline (mean package watts) ----
    idle_w = None; idle_j = None
    if not args.no_idle:
        print(f"[idle] measuring for {args.idle_s:.0f}s...")
        idle_w, idle_j = idle_baseline(args.idle_s)
        print(f"[idle] mean={idle_w} W  total={idle_j} J")

    only = set(args.only.split(",")) if args.only else set(WORKLOADS.keys())

    # ---- data ----
    items_sent  = sentiment_pairs(args.n)
    items_mixed = decidable_split(args.n, decisive_frac=args.decisive_frac)
    items_by = {"sentiment": items_sent, "mixed": items_mixed}

    results = {}
    for key, (comp, factory, ds) in WORKLOADS.items():
        if key not in only:
            continue
        reps = []
        for rep in range(args.reps):
            print(f"[run] {key}  rep {rep+1}/{args.reps} ...")
            gc.collect()
            time.sleep(2)   # short cool-down between reps
            work, n = factory(items_by[ds])
            r = measure(key, work, n, idle_mean_w=idle_w)
            reps.append(r)
            pd = r.per_decision()
            print(f"       wall={pd['wall_ms_per_decision_mean']:.3f}ms  "
                  f"cpu={pd['cpu_ms_per_decision']:.3f}ms  "
                  f"mem={pd['peak_mem_mb']:.1f}MB  "
                  f"E_est/dec={pd['energy_j_estimated_per_decision']*1000:.4f} mJ"
                  + (f"  E_meas/dec={pd['energy_j_measured_per_decision']*1000:.4f} mJ"
                     if 'energy_j_measured_per_decision' in pd else "")
                  + (f"  E_delta/dec={pd['energy_j_delta_per_decision']*1000:.4f} mJ"
                     if 'energy_j_delta_per_decision' in pd else ""))
        results[key] = {
            "comparison": comp,
            "dataset": ds,
            "reps_raw": [r.per_decision() for r in reps],
            "summary": summarise_reps(reps),
        }

    payload = {
        "env": env,
        "params": {"n": args.n, "reps": args.reps, "idle_s": args.idle_s,
                   "decisive_frac": args.decisive_frac},
        "idle_baseline": {"mean_w": idle_w, "total_j": idle_j,
                          "duration_s": args.idle_s if not args.no_idle else 0},
        "results": results,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"[done] wrote {args.out}")


if __name__ == "__main__":
    main()
