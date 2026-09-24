#!/usr/bin/env bash
# Reproduce the ANALYTIC_ECOCHIP.md numbers.
# Windows: run via Git Bash or WSL, or just: python harness/model.py
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/.."
echo "=== Analytic model output ==="
python harness/model.py
echo
echo "=== JSON dump ==="
python harness/model.py --json
