#!/usr/bin/env python3
"""Compare every current-engine component/certificate with a complete catalogue.

This is a regression comparison, not independent geometric certification.
Shard SHA-256 hashes are checked before parsing. Diagnostics are excluded:
optimizations intentionally change work counts and residue-candidate counts.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
from time import monotonic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hassett_lattices import Limits, intersection_components


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    index_bytes = args.index.read_bytes()
    index = json.loads(index_bytes)
    if index.get("complete") is not True or index.get("pair_count") != len(index["pairs"]):
        parser.error("A complete catalogue index is required")
    started = monotonic()
    components = origins = 0
    for i, entry in enumerate(index["pairs"], 1):
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe shard path")
        stored = (args.index.parent / relative).read_bytes()
        if hashlib.sha256(stored).hexdigest() != entry["sha256"]:
            raise ValueError(f"Hash mismatch: {relative}")
        raw = gzip.decompress(stored) if entry["compression"] == "gzip" else stored
        old = json.loads(raw)
        fresh = intersection_components(entry["d1"], entry["d2"], limits=Limits(None, None))
        if fresh["components"] != old["components"] or fresh["candidates"] != old["candidates"]:
            raise AssertionError(f"Components or certificates changed: {entry['key']}")
        components += len(fresh["components"])
        origins += sum(len(c["origins"]) for c in fresh["components"])
        if i % 1000 == 0:
            print(f"Compared {i}/{len(index['pairs'])} pairs", flush=True)
    report = {
        "passed": True, "pairs": len(index["pairs"]),
        "component_records": components, "origins": origins,
        "comparison": "Exact equality of all components (including every origin and certificate) and starting candidates; excludes diagnostics/work counts.",
        "catalogue_index_sha256": hashlib.sha256(index_bytes).hexdigest(),
        "core_sha256": hashlib.sha256((ROOT / "hassett_lattices" / "core.py").read_bytes()).hexdigest(),
        "elapsed_seconds": monotonic() - started,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS: {len(index['pairs'])} pairs, {components} component records, {origins} origins")


if __name__ == "__main__":
    main()
