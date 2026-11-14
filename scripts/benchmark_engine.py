#!/usr/bin/env python3
"""Reproducible warm-engine medians; optionally compare an explicit git revision.

Example: python scripts/benchmark_engine.py --baseline d3a365b --repeat 7
Reports elapsed time, work units, residue candidates, and exact output agreement.
For profiling: python -m cProfile -s cumulative scripts/benchmark_engine.py
"""

import argparse
import hashlib
import json
from pathlib import Path
import platform
from statistics import median
import subprocess
import sys
from time import perf_counter
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import hassett_lattices.core as current

PAIRS = [(8, 26), (8, 96), (446, 494), (456, 488), (498, 500)]


def measure(engine, pair, repeat):
    limits = engine.Limits(max_work=None, timeout_seconds=None)
    engine.intersection_components(*pair, limits=limits)
    timings = []
    for _ in range(repeat):
        start = perf_counter()
        result = engine.intersection_components(*pair, limits=limits)
        timings.append(perf_counter() - start)
    return result, {"median_seconds": median(timings), "samples_seconds": timings,
                    "work_units": result["diagnostics"]["work_units"],
                    "residue_candidates": result["diagnostics"]["overlattice_parameter_candidates"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", help="Trusted git revision containing the previous engine")
    parser.add_argument("--repeat", type=int, default=7)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be positive")
    baseline = None
    revision = None
    if args.baseline:
        revision = subprocess.check_output(["git", "rev-parse", "--verify", args.baseline + "^{commit}"], cwd=ROOT, text=True).strip()
        code = subprocess.check_output(["git", "show", revision + ":hassett_lattices/core.py"], cwd=ROOT)
        baseline = types.ModuleType("benchmark_baseline")
        sys.modules[baseline.__name__] = baseline
        exec(compile(code, "baseline/core.py", "exec"), baseline.__dict__)
    rows = []
    for pair in PAIRS:
        result, measurements = measure(current, pair, args.repeat)
        row = {"pair": pair, "components": result["component_count"], "current": measurements}
        if baseline:
            previous, old_measurements = measure(baseline, pair, args.repeat)
            if previous["components"] != result["components"] or previous["candidates"] != result["candidates"]:
                raise AssertionError(f"Mathematical outputs changed for {pair}")
            row.update(baseline=old_measurements, exact_output_agreement=True,
                       speedup=old_measurements["median_seconds"] / measurements["median_seconds"])
        rows.append(row)
    report = {"python": sys.version, "platform": platform.platform(),
              "baseline_commit": revision, "repeats": args.repeat,
              "core_sha256": hashlib.sha256((ROOT / "hassett_lattices" / "core.py").read_bytes()).hexdigest(),
              "scope": "Warm Python engine only; excludes serialization, startup and Julia compilation.",
              "measurements": rows}
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
