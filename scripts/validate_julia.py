#!/usr/bin/env python3
"""Cross-check the native Julia package with independent Python certificates.

Build a fresh Julia catalogue, verify every shard and summary, compare the
component/origin partitions with Python, and independently audit completeness.
No Python code is called by the Julia package itself.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hassett_lattices import intersection_components
from audit_classification import Audit
from verify_catalogue import verify_catalogue
from verify_certificates import RootVerifier, verify_result

STRESS_PAIRS = [(8, 96), (446, 494), (456, 488), (498, 500)]


def mathematical_projection(result):
    """Ignore timing and nonunique isometry/root witnesses, retain classifications."""
    return [{
        "id": c["id"], "gram": c["gram"], "determinant": c["determinant"],
        "k3": {k: v for k, v in c["k3_association"].items()
               if k not in {"criterion", "interpretation"}},
        "origins": [{k: o[k] for k in ("tau", "index", "a", "b", "base_gram", "overlattice_gram")}
                    for o in c["origins"]],
    } for c in result["components"]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--julia", default="julia")
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "julia-validation")
    parser.add_argument("--max-discriminant", type=int, default=42)
    args = parser.parse_args()
    output = args.output.resolve()
    subprocess.run([
        args.julia, f"--project={ROOT / 'julia' / 'HassettLattices'}", "-e",
        'using HassettLattices; index = build_catalogue(ARGS[1], parse(Int, ARGS[2]); '
        'resume=false, limits=Limits(timeout_seconds=180.0)); '
        'index["complete"] || error("Incomplete Julia catalogue"); '
        'for pair_string in ARGS[3:end]; pair = parse.(Int, split(pair_string,",")); '
        'r = intersection_components(pair...; limits=Limits(timeout_seconds=180.0)); '
        'write_result(joinpath(ARGS[1], "stress", join(pair,"-") * ".json.gz"), r); end',
        str(output), str(args.max_discriminant),
        *(",".join(map(str, pair)) for pair in STRESS_PAIRS),
    ], check=True)
    index_path = output / "catalogue-index.json"
    report = verify_catalogue(index_path, max_vectors=None)
    index = json.loads(index_path.read_bytes())
    audit = Audit(max_work=50_000_000)
    comparisons = []
    for entry in index["pairs"]:
        result = json.loads(gzip.decompress((output / entry["path"]).read_bytes()))
        python = intersection_components(entry["d1"], entry["d2"])
        if mathematical_projection(result) != mathematical_projection(python):
            raise AssertionError(f"Julia/Python classification mismatch: {entry['key']}")
        comparisons.append(audit.result(result))
    report["cross_language"] = {
        "passed": True, "pairs": len(comparisons),
        "components": sum(p["components"] for p in comparisons),
        "origins": sum(p["origins"] for p in comparisons),
        "classification_audit": comparisons,
    }
    stress = []
    for pair in STRESS_PAIRS:
        path = output / "stress" / ("-".join(map(str, pair)) + ".json.gz")
        result = json.loads(gzip.decompress(path.read_bytes()))
        verify_result(result, RootVerifier(None))
        if mathematical_projection(result) != mathematical_projection(intersection_components(*pair)):
            raise AssertionError(f"Julia/Python stress-case mismatch: {pair}")
        stress.append({"pair": pair, "components": result["component_count"],
                       "origins": sum(len(c["origins"]) for c in result["components"]),
                       "max_index": max(o["index"] for c in result["components"] for o in c["origins"])})
    report["cross_language"]["stress_cases"] = stress
    report["julia_source_sha256"] = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT / "julia" / "HassettLattices" / "src").glob("*.jl"))
    }
    (output / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Julia/Python agreement and independent classification audit: "
          f"{len(comparisons)} pairs, {report['cross_language']['components']} components, "
          f"{report['cross_language']['origins']} origins; "
          f"{len(stress)} larger/equal-determinant stress cases also agree and pass certificates.")


if __name__ == "__main__":
    main()
