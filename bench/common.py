"""
Shared benchmark plumbing.

Timing:         time.perf_counter (wall), time.process_time (CPU seconds).
Memory:         psutil RSS sampled by a background thread at 20 Hz.
Energy (LHM):   LibreHardwareMonitor Remote Web Server (Options → Remote
                Web Server → Run), default http://localhost:8085/data.json.
                CPU Package power sensor polled at 1 Hz in a background
                thread.  Energy = integral(power dt).  If LHM is not
                running, this collector returns None and the run continues
                without it.
Energy (est):   cpu_seconds_used * (TDP / physical_cores).  Labelled clearly
                as an estimate everywhere.  For an i7-8700, TDP=65W, cores=6,
                so ~10.83 W per fully-busy core-second.
"""
import json, os, subprocess, sys, threading, time, urllib.request
from dataclasses import dataclass, field, asdict
from statistics import mean, median, stdev
from typing import Optional

import psutil

CPU_TDP_W = 65.0            # i7-8700 nominal TDP
CPU_PHYS_CORES = 6
W_PER_CORE_SEC = CPU_TDP_W / CPU_PHYS_CORES  # ~10.83 J per core-second at TDP


# -------------------- LibreHardwareMonitor package-power poller --------------------

LHM_URL = os.environ.get("LHM_URL", "http://localhost:8085/data.json")
LHM_SENSOR_MATCH = ("CPU Package",)   # first Text match in the sensor tree

def _walk_find_power(node) -> Optional[float]:
    """Depth-first search for a Power sensor whose Text starts with 'CPU Package'.
    Returns watts as a float, or None if not found."""
    if node.get("Type") == "Power" and node.get("Text", "").startswith(LHM_SENSOR_MATCH):
        val = node.get("Value", "")
        try:
            return float(val.split()[0])
        except (ValueError, IndexError):
            return None
    for c in node.get("Children", []):
        r = _walk_find_power(c)
        if r is not None:
            return r
    return None


def lhm_read_once() -> Optional[float]:
    """Return CPU Package power in watts, or None if LHM's web server is unavailable."""
    try:
        with urllib.request.urlopen(LHM_URL, timeout=2) as resp:
            data = json.load(resp)
        return _walk_find_power(data)
    except Exception:
        return None


class PowerPoller:
    """Poll package power every `interval` seconds; integrate to energy (J)."""
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.samples: list[tuple[float, float]] = []   # (t, watts)
        self._stop = threading.Event()
        self._thr: Optional[threading.Thread] = None
        self.available = lhm_read_once() is not None

    def _run(self):
        while not self._stop.is_set():
            t = time.perf_counter()
            w = lhm_read_once()
            if w is not None:
                self.samples.append((t, w))
            self._stop.wait(self.interval)

    def start(self):
        if not self.available:
            return
        self._stop.clear()
        self.samples = []
        self._thr = threading.Thread(target=self._run, daemon=True)
        self._thr.start()

    def stop(self):
        if self._thr is None:
            return
        self._stop.set()
        self._thr.join()

    def integrate_j(self) -> Optional[float]:
        if len(self.samples) < 2:
            return None
        j = 0.0
        for (t0, w0), (t1, w1) in zip(self.samples[:-1], self.samples[1:]):
            j += 0.5 * (w0 + w1) * (t1 - t0)
        return j

    def mean_w(self) -> Optional[float]:
        if not self.samples:
            return None
        return mean(w for _, w in self.samples)


# -------------------- memory poller --------------------

class MemPoller:
    """Sample this process's RSS at 20 Hz; keep the peak."""
    def __init__(self):
        self.peak_mb = 0.0
        self._stop = threading.Event()
        self._thr: Optional[threading.Thread] = None
        self._p = psutil.Process(os.getpid())

    def _run(self):
        while not self._stop.is_set():
            try:
                rss = self._p.memory_info().rss / (1024 * 1024)
                if rss > self.peak_mb:
                    self.peak_mb = rss
            except Exception:
                pass
            self._stop.wait(0.05)

    def start(self):
        self.peak_mb = self._p.memory_info().rss / (1024 * 1024)
        self._stop.clear()
        self._thr = threading.Thread(target=self._run, daemon=True)
        self._thr.start()

    def stop(self):
        self._stop.set()
        if self._thr:
            self._thr.join()


# -------------------- one-run result --------------------

@dataclass
class RunResult:
    label: str
    n: int
    wall_s_total: float
    cpu_s_total: float
    latencies_s: list  # per-decision wall clock
    peak_mem_mb: float
    energy_j_measured: Optional[float]   # from LHM integral
    mean_w_measured: Optional[float]
    energy_j_estimated: float            # CPU-time * W_PER_CORE_SEC
    idle_mean_w: Optional[float]
    idle_delta_j: Optional[float]        # energy - (idle_mean_w * wall)

    def per_decision(self) -> dict:
        n = max(1, self.n)
        d = {
            "label": self.label,
            "n_decisions": n,
            "wall_ms_per_decision_mean": 1000 * self.wall_s_total / n,
            "wall_ms_per_decision_median": 1000 * median(self.latencies_s),
            "wall_ms_per_decision_p95": 1000 * sorted(self.latencies_s)[int(0.95 * n)],
            "cpu_ms_per_decision": 1000 * self.cpu_s_total / n,
            "peak_mem_mb": self.peak_mem_mb,
            "energy_j_estimated_total": self.energy_j_estimated,
            "energy_j_estimated_per_decision": self.energy_j_estimated / n,
        }
        if self.energy_j_measured is not None:
            d["energy_j_measured_total"] = self.energy_j_measured
            d["energy_j_measured_per_decision"] = self.energy_j_measured / n
            d["mean_w_measured"] = self.mean_w_measured
        if self.idle_delta_j is not None:
            d["energy_j_delta_total"] = self.idle_delta_j
            d["energy_j_delta_per_decision"] = self.idle_delta_j / n
            d["idle_mean_w"] = self.idle_mean_w
        return d


# -------------------- run harness --------------------

def measure(label: str, work_fn, n: int, idle_mean_w: Optional[float] = None) -> RunResult:
    """
    Run `work_fn(i)` for i in range(n).  Records per-call wall latency,
    total wall/CPU time, RSS peak, LHM package-power integral (if available),
    and a CPU-time-based energy estimate.  Optionally subtracts idle baseline.
    """
    mem = MemPoller(); pw = PowerPoller(interval=1.0)
    mem.start(); pw.start()
    latencies = []
    t_cpu0 = time.process_time()
    t0 = time.perf_counter()
    try:
        for i in range(n):
            s = time.perf_counter()
            work_fn(i)
            latencies.append(time.perf_counter() - s)
    finally:
        wall = time.perf_counter() - t0
        cpu = time.process_time() - t_cpu0
        pw.stop(); mem.stop()

    meas_j = pw.integrate_j()
    delta_j = None
    if meas_j is not None and idle_mean_w is not None:
        delta_j = meas_j - idle_mean_w * wall

    return RunResult(
        label=label, n=n,
        wall_s_total=wall, cpu_s_total=cpu, latencies_s=latencies,
        peak_mem_mb=mem.peak_mb,
        energy_j_measured=meas_j,
        mean_w_measured=pw.mean_w(),
        energy_j_estimated=cpu * W_PER_CORE_SEC,
        idle_mean_w=idle_mean_w,
        idle_delta_j=delta_j,
    )


def idle_baseline(duration_s: float = 60.0) -> tuple[Optional[float], Optional[float]]:
    """Return (mean package watts, total energy in J) over `duration_s` of doing nothing."""
    pw = PowerPoller(interval=1.0)
    if not pw.available:
        time.sleep(duration_s)
        return None, None
    pw.start()
    time.sleep(duration_s)
    pw.stop()
    return pw.mean_w(), pw.integrate_j()


# -------------------- reps aggregation --------------------

def summarise_reps(results: list[RunResult]) -> dict:
    per = [r.per_decision() for r in results]
    keys = [k for k in per[0].keys() if isinstance(per[0][k], (int, float))]
    agg = {"label": results[0].label, "reps": len(results)}
    for k in keys:
        vals = [p[k] for p in per if k in p]
        if len(vals) >= 2:
            agg[k + "_mean"] = mean(vals)
            agg[k + "_std"] = stdev(vals)
        elif vals:
            agg[k + "_mean"] = vals[0]
            agg[k + "_std"] = 0.0
    return agg


# -------------------- environment fingerprint --------------------

def env_fingerprint() -> dict:
    import platform
    fp = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "total_ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 1),
        "assumed_tdp_w": CPU_TDP_W,
    }
    try:
        import torch, transformers
        fp["torch"] = torch.__version__
        fp["transformers"] = transformers.__version__
        fp["torch_threads"] = torch.get_num_threads()
    except Exception:
        pass
    try:
        import cryptography
        fp["cryptography"] = cryptography.__version__
    except Exception:
        pass
    return fp
