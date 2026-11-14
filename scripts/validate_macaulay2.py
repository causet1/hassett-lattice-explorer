#!/usr/bin/env python3
"""Audit native Macaulay2 classifications with independent Python algorithms.

No Python or Julia code is called by the Macaulay2 package. This development
tool supplies a separate certificate/coverage verifier, exhaustive small-case
classification audit, and comparison with the existing engine.
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
from validate_julia import STRESS_PAIRS, mathematical_projection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2", default="M2")
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "macaulay2-validation")
    parser.add_argument("--max-discriminant", type=int, default=42)
    args = parser.parse_args()
    output = args.output.resolve()
    subprocess.run([args.m2, "--script", str(ROOT / "macaulay2" / "validate.m2"),
                    str(output), str(args.max_discriminant)], check=True, cwd=ROOT)
    index_path = output / "catalogue-index.json"
    report = verify_catalogue(index_path, max_vectors=None)
    index = json.loads(index_path.read_bytes())
    audit = Audit(max_work=50_000_000)
    comparisons = []
    for entry in index["pairs"]:
        result = json.loads(gzip.decompress((output / entry["path"]).read_bytes()))
        expected = intersection_components(entry["d1"], entry["d2"])
        if mathematical_projection(result) != mathematical_projection(expected):
            raise AssertionError(f"Macaulay2/Python mismatch: {entry['key']}")
        comparisons.append(audit.result(result))
    stress = []
    for pair in STRESS_PAIRS:
        path = output / "stress" / ("-".join(map(str, pair)) + ".json.gz")
        result = json.loads(gzip.decompress(path.read_bytes()))
        verify_result(result, RootVerifier(None))
        if mathematical_projection(result) != mathematical_projection(intersection_components(*pair)):
            raise AssertionError(f"Macaulay2/Python stress-case mismatch: {pair}")
        stress.append({"pair": pair, "components": result["component_count"],
                       "origins": sum(len(c["origins"]) for c in result["components"]),
                       "max_index": max(o["index"] for c in result["components"] for o in c["origins"])})
    report["cross_language"] = {
        "passed": True, "pairs": len(comparisons),
        "components": sum(p["components"] for p in comparisons),
        "origins": sum(p["origins"] for p in comparisons),
        "classification_audit": comparisons, "stress_cases": stress,
    }
    report["macaulay2_source_sha256"] = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT / "macaulay2").rglob("*.m2"))
    }
    (output / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Macaulay2/Python agreement and independent classification audit: "
          f"{len(comparisons)} pairs, {report['cross_language']['components']} components, "
          f"{report['cross_language']['origins']} origins; "
          f"{len(stress)} larger/equal-determinant stress cases pass.")


if __name__ == "__main__":
    main()
