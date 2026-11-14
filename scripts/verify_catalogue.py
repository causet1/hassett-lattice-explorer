#!/usr/bin/env python3
"""Independently verify the coverage and certificates of a sharded catalogue.

Usage:
    python scripts/verify_catalogue.py /path/to/catalogue-index.json
    python scripts/verify_catalogue.py /path/to/catalogue-index.json \
        --no-limits --report /path/to/verification.json

Supports catalogue-index schema 1.1 and raw or gzip-compressed pair files.
Hashes are checked on STORED bytes before decompression. Only one pair file
is parsed at a time, and the root-search cache is cleared between pairs.

The mathematical checks use the separate standard-library certificate checker
in verify_certificates.py. Neither script imports hassett_lattices or its
decision functions. A successful run verifies every emitted integral lattice
certificate, exact label-pair coverage through the declared bound, and complete
coverage of starting-lattice parameters. It does NOT independently re-enumerate
all admissible overlattices or prove pairwise nonisometry of distinct component
representatives. Those parts of classification completeness rely on the engine's
exhaustive algorithm, its documented proof, and the cited geometric theorems.
"""

import argparse
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re
import sys
from time import monotonic
import zlib


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from verify_certificates import (  # noqa: E402
    RootVerifier, VerificationError, integer, require, verify_result,
)


PUBLISHED_DISCRIMINANTS = {
    (8, 14): [21, 29, 32, 36, 37],
    (8, 26): [29, 36, 48, 53, 61, 64, 68, 69],
    (8, 38): [36, 45, 61, 68, 80, 85, 93, 96, 100, 101],
    (12, 20): [20, 32, 53, 68, 77, 80],
    (20, 38): [45, 77, 92, 120, 133, 157, 168, 188, 197,
               213, 220, 232, 237, 245, 248, 252, 253],
}


def _unique_object(items):
    result = {}
    for key, value in items:
        require(key not in result, f"Duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value):
    raise VerificationError(f"Non-finite JSON number is not allowed: {value}")


def _json(payload, context):
    try:
        return json.loads(payload.decode("utf-8"),
                          object_pairs_hook=_unique_object,
                          parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, VerificationError) as exc:
        raise VerificationError(f"{context}: {exc}") from exc


def _count(actual, expected, context):
    require(integer(actual) and actual >= 0, f"{context}: expected a nonnegative integer")
    require(actual == expected, f"{context}: recorded {actual}, independently counted {expected}")


def _counts(actual, expected, context):
    require(isinstance(actual, dict), f"{context}: expected an object")
    require(set(actual) == set(expected),
            f"{context}: fields differ from the schema; expected {sorted(expected)}")
    for key, value in expected.items():
        if value is None:
            require(actual[key] is None, f"{context}.{key}: expected null")
        else:
            _count(actual[key], value, f"{context}.{key}")


def _check_starting_coverage_and_unique_origins(result):
    """Check a finite positivity interval and recorded base origins independently.

    This is deliberately separate from the engine's endpoint implementation.
    A wider elementary interval is filtered by the determinant inequality.
    """
    d1, d2 = result["d1"], result["d2"]
    from math import isqrt
    eps_product = int(d1 % 6 == 2 and d2 % 6 == 2)
    radius = isqrt(d1 * d2) // 3 + 2
    expected_taus = [
        t for t in range(-radius, radius + 1)
        if (eps_product or t >= 0)
        and (3 * t - eps_product) ** 2 < d1 * d2
    ]
    candidates = result["candidates"]
    actual_taus = [candidate["tau"] for candidate in candidates]
    require(actual_taus == expected_taus,
            f"C_{d1} intersect C_{d2}: incomplete or unordered starting-lattice parameter interval")
    expected_base_origins = {
        (candidate["tau"], 1, 0, 0)
        for candidate in candidates if candidate["root_free"]
    }
    actual_base_origins = set()
    all_origins = set()
    exact_grams = set()
    for component in result["components"]:
        gram_key = tuple(tuple(row) for row in component["gram"])
        require(gram_key not in exact_grams,
                f"C_{d1} intersect C_{d2}: repeated identical component Gram matrix")
        exact_grams.add(gram_key)
        for origin in component["origins"]:
            key = tuple(origin[field] for field in ("tau", "index", "a", "b"))
            require(key not in all_origins,
                    f"C_{d1} intersect C_{d2}: repeated construction origin {key}")
            all_origins.add(key)
            if origin["index"] == 1:
                actual_base_origins.add(key)
    require(actual_base_origins == expected_base_origins,
            f"C_{d1} intersect C_{d2}: a root-free starting lattice is missing its index-one origin")


def _summarize(result):
    components = result["components"]
    determinants = [component["determinant"] for component in components]
    indices = [origin["index"] for component in components for origin in component["origins"]]
    admissible = sum(component["k3_association"]["admissible"] for component in components)
    return {
        "component_count": len(components),
        "marked_origin_count": len(indices),
        "duplicate_count": len(indices) - len(components),
        "determinants": {
            "min": min(determinants), "max": max(determinants),
            "distinct": len(set(determinants)), "sum": sum(determinants),
        },
        "k3": {"admissible": admissible, "nonadmissible": len(components) - admissible},
        "saturation": {
            "components": sum(any(origin["index"] > 1 for origin in component["origins"])
                              for component in components),
            "origins": sum(index > 1 for index in indices),
            "max_index": max(indices),
        },
    }


def verify_catalogue(index_path, *, max_vectors=100_000_000, progress=None):
    """Return an aggregate report only after EVERY required check succeeds.

    ``progress``, if supplied, receives (completed_pairs, total_pairs). It is
    called after each pair. Memory is bounded by the index and one pair file,
    rather than the total size of the full certificate collection.
    """
    require(max_vectors is None or (integer(max_vectors) and max_vectors > 0),
            "max_vectors must be a positive integer or None")
    started = monotonic()
    index_path = Path(index_path).resolve()
    directory = index_path.parent
    index_bytes = index_path.read_bytes()
    index = _json(index_bytes, str(index_path))
    require(isinstance(index, dict), "The catalogue index must be an object")
    require(index.get("schema_version") == "1.1", "Expected catalogue-index schema_version 1.1")
    require(index.get("complete") is True, "The catalogue is not marked complete")
    _count(index.get("failed_pair_count"), 0, "failed_pair_count")
    _count(index.get("pending_pair_count"), 0, "pending_pair_count")
    require(index.get("failures") == [], "A complete catalogue must have an empty failures list")
    bound = index.get("max_discriminant")
    require(integer(bound) and bound >= 8, "max_discriminant must be an integer at least 8")
    labels = [d for d in range(8, bound + 1) if d % 6 in (0, 2)]
    require(index.get("discriminants") == labels,
            "The discriminant list does not contain exactly the sorted valid labels through the bound")
    expected_pairs = set(combinations(labels, 2))
    _count(index.get("expected_pair_count"), len(expected_pairs), "expected_pair_count")
    entries = index.get("pairs")
    require(isinstance(entries, list), "Index pairs must be a list")
    _count(index.get("pair_count"), len(entries), "pair_count")
    require(len(entries) == len(expected_pairs),
            f"Incomplete pair coverage: expected {len(expected_pairs)} records, found {len(entries)}")

    seen_pairs, expected_paths = set(), set()
    for position, entry in enumerate(entries, 1):
        require(isinstance(entry, dict), f"Index pair {position}: expected an object")
        d1, d2 = entry.get("d1"), entry.get("d2")
        require(all(integer(d) and d > 6 and d <= bound and d % 6 in (0, 2) for d in (d1, d2))
                and d1 != d2, f"Index pair {position}: invalid or out-of-range labels")
        pair = tuple(sorted((d1, d2)))
        key = f"{pair[0]}-{pair[1]}"
        require(entry.get("key") == key, f"Index pair {position}: key disagrees with labels")
        require(pair not in seen_pairs, f"Repeated label pair: {key}")
        seen_pairs.add(pair)
        compression = entry.get("compression", "none")
        require(compression in ("none", "gzip"), f"{key}: unsupported compression {compression!r}")
        expected_path = f"pairs/{key}.json" + (".gz" if compression == "gzip" else "")
        require(entry.get("path") == expected_path, f"{key}: unexpected pair-file path")
        require(expected_path not in expected_paths, f"Repeated pair-file path: {expected_path}")
        expected_paths.add(expected_path)
        require(isinstance(entry.get("sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) is not None,
                f"{key}: invalid SHA-256 value")
        require(isinstance(entry.get("uncompressed_sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", entry["uncompressed_sha256"]) is not None,
                f"{key}: invalid uncompressed SHA-256 value")
    require(seen_pairs == expected_pairs, "The manifest omits or adds label pairs")
    pair_directory = directory / "pairs"
    actual_paths = {
        path.relative_to(directory).as_posix()
        for pattern in ("*.json", "*.json.gz")
        for path in pair_directory.rglob(pattern) if path.is_file()
    }
    require(actual_paths == expected_paths,
            "Pair files do not exactly match the manifest: "
            f"missing={sorted(expected_paths - actual_paths)[:8]}, "
            f"unlisted={sorted(actual_paths - expected_paths)[:8]}")

    roots = RootVerifier(max_vectors)
    statistics = {
        "total_components": 0,
        "total_component_records": 0,
        "total_marked_origins": 0,
        "total_k3_admissible_components": 0,
        "total_k3_nonadmissible_components": 0,
        "total_components_with_saturation": 0,
        "total_proper_overlattice_origins": 0,
        "total_duplicate_routes": 0,
        "max_saturation_index": 0,
        "min_component_determinant": None,
        "max_component_determinant": None,
        "total_bytes": 0,
        "total_uncompressed_bytes": 0,
    }
    fixture_checks = []
    candidate_count = 0
    pair_files_checked = 0
    gzip_files_checked = 0
    for entry in entries:
        key = entry["key"]
        path = (directory / entry["path"]).resolve()
        require(path.is_relative_to(directory), f"{key}: pair path resolves outside the catalogue directory")
        stored = path.read_bytes()
        _count(entry.get("bytes"), len(stored), f"{key}.bytes")
        require(hashlib.sha256(stored).hexdigest() == entry["sha256"], f"{key}: stored-file SHA-256 mismatch")
        compression = entry.get("compression", "none")
        if compression == "gzip":
            try:
                raw = gzip.decompress(stored)
            except (OSError, EOFError, zlib.error) as exc:
                raise VerificationError(f"{key}: invalid gzip data: {exc}") from exc
            gzip_files_checked += 1
            _count(entry.get("uncompressed_bytes"), len(raw), f"{key}.uncompressed_bytes")
        else:
            raw = stored
            if "uncompressed_bytes" in entry:
                _count(entry["uncompressed_bytes"], len(raw), f"{key}.uncompressed_bytes")
        require(hashlib.sha256(raw).hexdigest() == entry["uncompressed_sha256"],
                f"{key}: uncompressed-file SHA-256 mismatch")
        result = _json(raw, key)
        require(isinstance(result, dict), f"{key}: pair file must contain one result object")
        require(result.get("d1") == entry["d1"] and result.get("d2") == entry["d2"],
                f"{key}: index labels disagree with pair file")

        # Clear the independently checked Gram cache here, keeping the global
        # work counter. This prevents a large catalogue growing the cache forever.
        roots.cache.clear()
        verify_result(result, roots)
        _check_starting_coverage_and_unique_origins(result)
        summary = _summarize(result)
        for name in ("component_count", "marked_origin_count", "duplicate_count"):
            _count(entry.get(name), summary[name], f"{key}.{name}")
        for name in ("determinants", "k3", "saturation"):
            _counts(entry.get(name), summary[name], f"{key}.{name}")

        pair = tuple(sorted((entry["d1"], entry["d2"])))
        expected_discriminants = PUBLISHED_DISCRIMINANTS.get(pair)
        expected_status = "matched" if expected_discriminants is not None else "computed"
        require(entry.get("validation") == expected_status, f"{key}: unexpected publication-validation status")
        validation = result.get("validation")
        require(isinstance(validation, dict) and validation.get("status") == expected_status,
                f"{key}: pair-file publication-validation status disagrees")
        if expected_discriminants is not None:
            observed = sorted(c["determinant"] for c in result["components"])
            require(observed == expected_discriminants, f"{key}: published discriminant regression failed")
            require(validation.get("expected_discriminants") == expected_discriminants,
                    f"{key}: incorrect stored published fixture")
            _count(validation.get("expected_count"), len(expected_discriminants), f"{key}.expected_count")
            fixture_checks.append({"pair": list(pair), "component_count": len(observed),
                                   "discriminants": observed, "matched": True})

        statistics["total_components"] += summary["component_count"]
        statistics["total_component_records"] += summary["component_count"]
        statistics["total_marked_origins"] += summary["marked_origin_count"]
        statistics["total_k3_admissible_components"] += summary["k3"]["admissible"]
        statistics["total_k3_nonadmissible_components"] += summary["k3"]["nonadmissible"]
        statistics["total_components_with_saturation"] += summary["saturation"]["components"]
        statistics["total_proper_overlattice_origins"] += summary["saturation"]["origins"]
        statistics["total_duplicate_routes"] += summary["duplicate_count"]
        statistics["max_saturation_index"] = max(statistics["max_saturation_index"], summary["saturation"]["max_index"])
        low, high = summary["determinants"]["min"], summary["determinants"]["max"]
        statistics["min_component_determinant"] = low if statistics["min_component_determinant"] is None else min(statistics["min_component_determinant"], low)
        statistics["max_component_determinant"] = high if statistics["max_component_determinant"] is None else max(statistics["max_component_determinant"], high)
        statistics["total_bytes"] += len(stored)
        statistics["total_uncompressed_bytes"] += len(raw)
        candidate_count += len(result["candidates"])
        pair_files_checked += 1
        if progress is not None:
            progress(pair_files_checked, len(entries))
        del result, raw, stored

    _count(index.get("component_count"), statistics["total_components"], "component_count")
    _count(index.get("component_records"), statistics["total_component_records"], "component_records")
    _counts(index.get("statistics"), statistics, "statistics")
    return {
        "schema_version": "1.0",
        "verifier": "scripts/verify_catalogue.py",
        "passed": True,
        "index_file": str(index_path),
        "index_sha256": hashlib.sha256(index_bytes).hexdigest(),
        "max_discriminant": bound,
        "discriminants_checked": len(labels),
        "expected_pair_count": len(expected_pairs),
        "pairs_checked": pair_files_checked,
        "pair_coverage_complete": True,
        "file_hashes_checked": pair_files_checked,
        "gzip_files_checked": gzip_files_checked,
        "starting_parameter_intervals_checked": pair_files_checked,
        "starting_lattices_checked": candidate_count,
        "independent_root_box_vectors_checked": roots.vectors,
        "statistics": statistics,
        "published_fixtures": fixture_checks,
        "elapsed_seconds": round(monotonic() - started, 6),
        "checks": [
            "Exact coverage of every unordered distinct valid label pair through the bound.",
            "No repeated label pairs, filenames, component ids, exact Gram matrices, or construction origins.",
            "Every stored-file hash and byte count; decompression and uncompressed byte counts.",
            "All pair files claim completed computations; no manifest failures or pending pairs.",
            "The entire positive-definite starting-parameter interval and every root-free index-one origin.",
            "All integral Gram, index, distinguished-class, primitive-label and basis-map certificates.",
            "Independent exhaustive norm-two searches and exact whole-lattice K3 admissibility checks.",
            "Per-pair statistics, aggregate statistics, and all included fixtures from the five-case published regression suite.",
        ],
        "limitations": [
            "Does not independently re-enumerate all admissible overlattices.",
            "Does not independently prove pairwise nonisometry of distinct component representatives.",
            "Classification completeness uses the documented exhaustive algorithm and cited geometric theorems; certificate checks alone do not prove it.",
            "Hashes establish consistency with this index, not external authentication of the index.",
            "Aggregate component totals count records per pair, not globally distinct geometric loci.",
            "Counts are reduced irreducible components, not scheme multiplicities or rationality decisions.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("index", type=Path)
    parser.add_argument("--max-vectors", type=int, default=100_000_000,
                        help="global budget for independent root-box vectors (default: 100000000)")
    parser.add_argument("--no-limits", action="store_true", help="remove the independent root-verification budget")
    parser.add_argument("--progress-every", type=int, default=250, help="report every N checked pairs; 0 disables progress")
    parser.add_argument("--report", type=Path, help="write the full aggregate JSON report only after success")
    args = parser.parse_args(argv)
    if args.max_vectors < 1:
        parser.error("--max-vectors must be positive")
    if args.progress_every < 0:
        parser.error("--progress-every cannot be negative")

    def progress(done, total):
        if args.progress_every and (done % args.progress_every == 0 or done == total):
            print(f"Verified {done}/{total} pair files", file=sys.stderr, flush=True)

    try:
        report = verify_catalogue(args.index,
                                  max_vectors=None if args.no_limits else args.max_vectors,
                                  progress=progress)
        if args.report is not None:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.report.with_name(args.report.name + ".tmp")
            temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temporary.replace(args.report)
    except (VerificationError, OSError, UnicodeError, TypeError, KeyError, AttributeError, ValueError) as exc:
        print(f"FAIL: {exc}\nNo new successful catalogue-verification report was produced.", file=sys.stderr)
        return 1
    stats = report["statistics"]
    print(f"PASS: all {report['pairs_checked']} distinct pairs among {report['discriminants_checked']} "
          f"valid labels through {report['max_discriminant']}.")
    print(f"Verified {stats['total_components']} component certificates and "
          f"{stats['total_marked_origins']} origins; {report['file_hashes_checked']} stored-file hashes.")
    print(f"Checked {report['independent_root_box_vectors_checked']} independent root-box vectors "
          f"in {report['elapsed_seconds']:.3f} seconds.")
    print("Certificate and pair-coverage validation passed. This does not independently prove "
          "overlattice-enumeration completeness or pairwise nonisometry.")
    if args.report is not None:
        print(f"Saved {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
