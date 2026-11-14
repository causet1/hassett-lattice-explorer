#!/usr/bin/env python3
"""Exercise the native M2 CLI, exit statuses, and portable file contract."""

import gzip
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "macaulay2" / "HassettLattices" / "cli.m2"


def run(*args, expected=0):
    result = subprocess.run([os.environ.get("M2", "M2"), "--script", str(CLI),
                             *map(str, args)], cwd=ROOT, capture_output=True, text=True)
    if result.returncode != expected:
        raise AssertionError(f"{args}: exit {result.returncode}, expected {expected}\n"
                             f"{result.stdout}\n{result.stderr}")
    return result


def main():
    (ROOT / "build").mkdir(exist_ok=True)
    # Inside the checkout so the documented Docker wrapper can see the files.
    with tempfile.TemporaryDirectory(prefix="m2-cli-", dir=ROOT / "build") as tmp:
        directory = Path(tmp)
        filename = directory / "quote ' ; dollar $ and spaces.json.gz"
        run("intersect", 12, 20, "--output", filename)
        result = json.loads(gzip.decompress(filename.read_bytes()))
        assert result["component_count"] == 6
        assert result["input_pair"] == [12, 20]
        assert "elapsed_seconds" not in result["diagnostics"]
        checked = json.loads(run("verify", filename, "--classification").stdout)
        assert checked["passed"] and checked["classification_recomputed"]
        summary = json.loads(run("summary", filename).stdout)
        assert summary["component_count"] == 6
        markings = json.loads(run("markings", filename, result["components"][0]["id"], 100).stdout)
        assert markings and all(m["discriminant"] <= 100 for m in markings)
        assert json.loads(run("labels", 20).stdout) == [8, 12, 14, 18, 20]
        run("intersect", 14, 14, expected=2)
        failed = directory / "must-not-exist.json"
        run("intersect", 8, 14, "--max-work", 1, "--output", failed, expected=2)
        assert not failed.exists()
        # Restricted numeric parsing must not evaluate supplied M2 expressions.
        run("labels", "8; exit 0", expected=2)
        catalogue = directory / "catalogue"
        partial = json.loads(run("catalogue", 14, catalogue, "--stop-after", 1, expected=1).stdout)
        assert not partial["complete"] and partial["pair_count"] == 1
        complete = json.loads(run("catalogue", 14, catalogue).stdout)
        assert complete["complete"] and complete["pair_count"] == 3
        state = json.loads((catalogue / "run-state.json").read_text())
        assert state["reused_this_run"] == 1
    print("Macaulay2 CLI: exact JSON, quoted paths, certificates, limits, and resume passed.")


if __name__ == "__main__":
    main()
