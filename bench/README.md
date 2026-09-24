# bench/

Energy-per-decision benchmark harness. See [BENCH_ECOCHIP.md](BENCH_ECOCHIP.md)
for the run report.

## Files

- `common.py` — timing, memory, LHM package-power poller, CPU-time energy estimate
- `dataset.py` — deterministic sentiment templates (seeded)
- `workloads.py` — four workloads (A1/A2/B1/B2)
- `runner.py` — orchestrator; writes `results.json`
- `report.py` — reads `results.json`, writes `BENCH_ECOCHIP.md`

## Run

```bash
python bench/runner.py           # 60s idle, N=1000, 3 reps
python bench/report.py            # regenerate the report
```

Options: `--quick`, `--n`, `--reps`, `--no-idle`, `--decisive-frac`,
`--only A1_overlay_only,B2_cascade`.

## Energy measurement

For measured package-power energy: install
[LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor),
launch it **as administrator** (required to read CPU sensors), then
**Options → Remote Web Server → Run** (default port 8085). The harness
polls `http://localhost:8085/data.json` at 1 Hz and integrates the
`CPU Package` sensor. Override the URL with `LHM_URL=...` in the env if
you moved the port. Without LHM running the harness still reports the
CPU-time-based energy estimate.

The most honest energy source on this hardware would be Linux
`perf stat -e power/energy-pkg/`. Not attempted from Windows.
