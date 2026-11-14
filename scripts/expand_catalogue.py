#!/usr/bin/env python3
"""Resume an exhaustive finite catalogue, with exact certificates in small shards.

Examples:
  python scripts/expand_catalogue.py --max-discriminant 500 --gzip \
      --output /path/to/data --seed-catalogue web/catalogue.json
  python scripts/expand_catalogue.py --max-discriminant 1000 --gzip \
      --output /path/to/data --max-work 20000000 --timeout 180

Every unordered pair of distinct nonempty labels through the bound is attempted.
Only complete successful results enter catalogue-index.json. Existing shards and
seed records are independently certificate-checked before reuse. Failed pairs are
recorded and retried on a later invocation; interrupted runs keep atomic shards.
Timing/progress belongs only to run-state.json, not mathematical result files.
"""

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import io
from itertools import combinations
import json
import os
from pathlib import Path
import sys
from time import monotonic


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from hassett_lattices import Limits, intersection_components
from verify_certificates import RootVerifier, verify_result


# The same primary-source fixtures as scripts/build_catalogue.py. They are
# asserted again for reused data; a stored "matched" flag is not trusted.
PUBLISHED = {
    (8, 14): ("Auel et al., Theorem 4", "https://arxiv.org/abs/1205.0237v4", [21, 29, 32, 36, 37]),
    (8, 26): ("Awada, Proposition 3.2", "https://arxiv.org/abs/1910.10182v2", [29, 36, 48, 53, 61, 64, 68, 69]),
    (8, 38): ("Awada, Theorem 1.1(2)", "https://arxiv.org/abs/1910.10182v2", [36, 45, 61, 68, 80, 85, 93, 96, 100, 101]),
    (12, 20): ("Yang–Yu, Theorem 7.11", "https://arxiv.org/abs/2103.09132", [20, 32, 53, 68, 77, 80]),
    (20, 38): ("Yang–Yu, Theorem 7.9", "https://arxiv.org/abs/2103.09132", [45, 77, 92, 120, 133, 157, 168, 188, 197, 213, 220, 232, 237, 245, 248, 252, 253]),
}


def pair_key(a, b):
    a, b = sorted((a, b))
    return f"{a}-{b}"


def compact_json(data):
    """Stable UTF-8 representation, including a final newline."""
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def deterministic_gzip(raw):
    """No timestamp, original filename, or platform-dependent gzip OS field."""
    target = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=target, mtime=0, compresslevel=9) as stream:
        stream.write(raw)
    return target.getvalue()


def atomic_write(path, payload):
    """Replace one completed file atomically; never expose a partial JSON/gzip."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    try:
        with temporary.open("wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def prepare_result(result, pair, check_certificates=False):
    """Check identity/completeness, apply fixtures, and remove run-only timing."""
    if not isinstance(result, dict) or result.get("complete") is not True:
        raise ValueError("A stored pair does not contain a complete result")
    if sorted((result.get("d1"), result.get("d2"))) != list(pair):
        raise ValueError("Stored result identifies a different discriminant pair")
    if result.get("schema_version") != "1.0":
        raise ValueError("Unsupported pair-result schema")
    if result.get("component_count") != len(result.get("components", [])):
        raise ValueError("Stored component count is inconsistent")
    if check_certificates:
        # Each pair gets its own cache, so a large resumed catalogue does not
        # retain every Gram matrix in memory. This proves certificate validity,
        # not independent completeness of the original enumeration.
        verify_result(result, RootVerifier(None))
    result["input_pair"] = list(pair)
    result.get("diagnostics", {}).pop("elapsed_seconds", None)
    if pair in PUBLISHED:
        reference, url, expected = PUBLISHED[pair]
        actual = sorted(c["determinant"] for c in result["components"])
        if actual != expected:
            raise ValueError(f"Published fixture mismatch for {pair}: {actual} != {expected}")
        result["validation"] = {
            "status": "matched", "reference": reference, "url": url,
            "expected_count": len(expected), "expected_discriminants": expected,
        }
    else:
        result["validation"] = {
            "status": "computed",
            "reference": "Exact algorithm; not an independent published fixture",
        }
    return result


def summary_entry(result, path, stored, raw, compressed):
    components = result["components"]
    determinants = [c["determinant"] for c in components]
    origins = [o for c in components for o in c["origins"]]
    return {
        "key": pair_key(result["d1"], result["d2"]),
        "d1": result["d1"], "d2": result["d2"],
        "component_count": len(components), "path": path,
        "compression": "gzip" if compressed else "none",
        "sha256": hashlib.sha256(stored).hexdigest(),
        "uncompressed_sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(stored), "uncompressed_bytes": len(raw),
        "determinants": {
            "min": min(determinants), "max": max(determinants),
            "distinct": len(set(determinants)), "sum": sum(determinants),
        },
        "k3": {
            "admissible": sum(c["k3_association"]["admissible"] for c in components),
            "nonadmissible": sum(not c["k3_association"]["admissible"] for c in components),
        },
        "saturation": {
            "components": sum(any(o["index"] > 1 for o in c["origins"]) for c in components),
            "origins": sum(o["index"] > 1 for o in origins),
            "max_index": max(o["index"] for o in origins),
        },
        "marked_origin_count": len(origins),
        "duplicate_count": len(origins) - len(components),
        "validation": result["validation"]["status"],
    }


def aggregate(entries):
    rows = list(entries)
    return {
        "total_components": sum(e["component_count"] for e in rows),
        "total_component_records": sum(e["component_count"] for e in rows),
        "total_marked_origins": sum(e["marked_origin_count"] for e in rows),
        "total_k3_admissible_components": sum(e["k3"]["admissible"] for e in rows),
        "total_k3_nonadmissible_components": sum(e["k3"]["nonadmissible"] for e in rows),
        "total_components_with_saturation": sum(e["saturation"]["components"] for e in rows),
        "total_proper_overlattice_origins": sum(e["saturation"]["origins"] for e in rows),
        "total_duplicate_routes": sum(e["duplicate_count"] for e in rows),
        "max_saturation_index": max((e["saturation"]["max_index"] for e in rows), default=0),
        "min_component_determinant": min((e["determinants"]["min"] for e in rows), default=None),
        "max_component_determinant": max((e["determinants"]["max"] for e in rows), default=None),
        "total_bytes": sum(e["bytes"] for e in rows),
        "total_uncompressed_bytes": sum(e["uncompressed_bytes"] for e in rows),
    }


def load_seed(path):
    if path is None:
        return {}
    payload = path.read_bytes()
    if path.suffix == ".gz":
        payload = gzip.decompress(payload)
    data = json.loads(payload)
    records = data if isinstance(data, list) else data.get("pairs", data.get("results", [data]))
    if not isinstance(records, list):
        raise ValueError("Seed catalogue must contain a result list")
    seed = {}
    for record in records:
        if not isinstance(record, dict) or "components" not in record:
            raise ValueError("Seed must contain full pair certificates, not an index")
        key = pair_key(record["d1"], record["d2"])
        if key in seed:
            raise ValueError(f"Duplicate seed pair {key}")
        seed[key] = record
    return seed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--max-discriminant", type=int, default=500)
    parser.add_argument("--output", type=Path, default=ROOT / "web" / "data")
    parser.add_argument("--gzip", action="store_true", help="store deterministic .json.gz shards")
    parser.add_argument("--seed-catalogue", type=Path, help="reuse full certificates from an earlier catalogue")
    parser.add_argument("--max-work", type=int, default=5_000_000, help="exact-engine budget per pair")
    parser.add_argument("--timeout", type=float, default=60.0, help="exact-engine seconds per pair")
    parser.add_argument("--no-limits", action="store_true", help="disable both per-pair engine budgets")
    parser.add_argument("--checkpoint-every", type=int, default=100, help="refresh the atomic index after this many processed pairs")
    parser.add_argument("--stop-after", type=int, help="stop after this many pairs this run, leaving an honest partial checkpoint")
    args = parser.parse_args(argv)
    if args.max_discriminant < 8:
        parser.error("--max-discriminant must be at least 8")
    if args.checkpoint_every < 1 or (args.stop_after is not None and args.stop_after < 1):
        parser.error("--checkpoint-every and --stop-after must be positive")
    try:
        limits = Limits(None, None) if args.no_limits else Limits(args.max_work, args.timeout)
        seed = load_seed(args.seed_catalogue)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    labels = [d for d in range(8, args.max_discriminant + 1) if d % 6 in (0, 2)]
    pairs = list(combinations(labels, 2))
    ordered_keys = [pair_key(*pair) for pair in pairs]
    expected_keys = set(ordered_keys)
    entries, failures = {}, {}
    ledger_path = output / "failures.json"
    if ledger_path.exists():
        try:
            previous = json.loads(ledger_path.read_bytes())
            failures = {r["key"]: r for r in previous.get("failures", [])}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(f"Ignoring unreadable failure ledger; pair shards will still be checked: {exc}", file=sys.stderr)

    started = monotonic()
    start_time = datetime.now(timezone.utc).isoformat()
    progress = {"processed_this_run": 0, "computed_this_run": 0, "reused_this_run": 0,
                "seeded_this_run": 0, "failed_this_run": 0, "invalid_existing_files": 0}
    last_pair = None

    def checkpoint(stage):
        rows = [entries[key] for key in ordered_keys if key in entries]
        relevant_failures = [failures[key] for key in ordered_keys if key in failures and key not in entries]
        pending = len(pairs) - len(rows) - len(relevant_failures)
        stats = aggregate(rows)
        complete = len(rows) == len(pairs) and not relevant_failures
        index = {
            "schema_version": "1.1", "title": "Hassett Lattice Explorer",
            "catalogue_version": "1.1.0", "reference_date": "2026-11-13",
            "algorithm": "Yang–Yu Algorithm 7.6",
            "reference": "https://arxiv.org/abs/2103.09132",
            "license": "MIT", "max_discriminant": args.max_discriminant,
            "discriminants": labels, "expected_pair_count": len(pairs),
            "pair_count": len(rows), "component_count": stats["total_components"],
            "component_records": stats["total_components"],
            "failed_pair_count": len(relevant_failures), "pending_pair_count": pending,
            "complete": complete,
            "scope": "All unordered pairs of distinct nonempty Hassett labels up to max_discriminant. Completeness refers to this finite range; there are infinitely many labels in total. component_count/component_records sum records across pairs, not globally distinct geometric loci. Reduced components only; no scheme multiplicities or rationality decisions.",
            "pairs": rows, "statistics": stats, "failures": relevant_failures,
        }
        atomic_write(output / "catalogue-index.json", compact_json(index))
        atomic_write(ledger_path, compact_json({"schema_version": "1.0", "failures": [failures[k] for k in sorted(failures)]}))
        operational = {
            "schema_version": "1.0", "stage": stage, "started_at": start_time,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(monotonic() - started, 3),
            "max_discriminant": args.max_discriminant, "compression": "gzip" if args.gzip else "none",
            "limits": {"max_work": limits.max_work, "timeout_seconds": limits.timeout_seconds},
            "expected_pair_count": len(pairs), "completed_pair_count": len(rows),
            "failed_pair_count": len(relevant_failures), "pending_pair_count": pending,
            "last_pair": last_pair, **progress,
        }
        atomic_write(output / "run-state.json", compact_json(operational))
        print(f"{stage}: {len(rows)}/{len(pairs)} pairs; {stats['total_components']} components; "
              f"{len(relevant_failures)} failed, {pending} pending; "
              f"{stats['total_bytes'] / 1_000_000:.2f} MB stored; "
              f"{monotonic() - started:.1f}s", flush=True)
        return index

    interrupted = False
    try:
        for pair in pairs:
            key = pair_key(*pair)
            last_pair = list(pair)
            filename = f"pairs/{key}.json" + (".gz" if args.gzip else "")
            desired_path = output / filename
            alternate = output / (f"pairs/{key}.json" if args.gzip else f"pairs/{key}.json.gz")
            result = None
            try:
                for candidate in (desired_path, alternate):
                    if not candidate.exists():
                        continue
                    try:
                        stored = candidate.read_bytes()
                        raw = gzip.decompress(stored) if candidate.suffix == ".gz" else stored
                        result = prepare_result(json.loads(raw), pair, check_certificates=True)
                        progress["reused_this_run"] += 1
                        break
                    except (ValueError, TypeError, KeyError, AttributeError, OSError, EOFError):
                        progress["invalid_existing_files"] += 1
                        result = None
                if result is None and key in seed:
                    try:
                        result = prepare_result(seed[key], pair, check_certificates=True)
                        progress["seeded_this_run"] += 1
                    except (ValueError, TypeError, KeyError, AttributeError):
                        result = None
                if result is None:
                    result = prepare_result(intersection_components(*pair, limits=limits), pair)
                    progress["computed_this_run"] += 1
                raw = compact_json(result)
                stored = deterministic_gzip(raw) if args.gzip else raw
                if not desired_path.exists() or desired_path.read_bytes() != stored:
                    atomic_write(desired_path, stored)
                entries[key] = summary_entry(result, filename, stored, raw, args.gzip)
                failures.pop(key, None)
            except Exception as exc:
                progress["failed_this_run"] += 1
                failures[key] = {
                    "key": key, "d1": pair[0], "d2": pair[1],
                    "exception_type": type(exc).__name__, "error": str(exc),
                    "limits": {"max_work": limits.max_work, "timeout_seconds": limits.timeout_seconds},
                }
                print(f"FAILED {key}: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
            progress["processed_this_run"] += 1
            if progress["processed_this_run"] % args.checkpoint_every == 0:
                checkpoint("running")
            if args.stop_after is not None and progress["processed_this_run"] >= args.stop_after:
                break
    except KeyboardInterrupt:
        interrupted = True
    final = checkpoint("interrupted" if interrupted else "complete" if len(entries) == len(pairs) else "partial")
    if interrupted:
        return 130
    return 0 if final["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
