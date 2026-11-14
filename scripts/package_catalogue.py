#!/usr/bin/env python3
"""Package a complete expanded catalogue only after independent verification."""

import argparse
import csv
import hashlib
import io
from itertools import combinations
import json
import os
from pathlib import Path
import sys
import zipfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def json_bytes(data):
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def labels_through(bound):
    return [d for d in range(8, bound + 1) if d % 6 in (0, 2)]


def pair(row):
    return tuple(sorted((row["d1"], row["d2"])))


def brief(row):
    return {"pair": list(pair(row)), "component_count": row["component_count"],
            "max_saturation_index": row["saturation"]["max_index"],
            "distinct_determinants": row["determinants"]["distinct"]}


def package(index_path, verification_path, output):
    index_path = index_path.resolve()
    base = index_path.parent
    index_raw = index_path.read_bytes()
    index = json.loads(index_raw)
    report = json.loads(verification_path.read_bytes())
    digest = hashlib.sha256(index_raw).hexdigest()
    require(index.get("schema_version") == "1.1", "Expected catalogue schema 1.1")
    require(index.get("complete") is True and index.get("failures") == [] and
            index.get("failed_pair_count") == 0 and index.get("pending_pair_count") == 0,
            "Refusing to package an incomplete or failed catalogue")
    require(report.get("passed") is True and report.get("pair_coverage_complete") is True and
            report.get("verifier") == "scripts/verify_catalogue.py", "A successful independent catalogue-verification report is required")
    require(report.get("index_sha256") == digest, "Verification report belongs to a different index")
    bound = index["max_discriminant"]
    labels = labels_through(bound)
    rows = sorted(index["pairs"], key=pair)
    expected = list(combinations(labels, 2))
    require(index.get("discriminants") == labels and [pair(r) for r in rows] == expected,
            "Index does not contain exactly every required unordered label pair")
    require(index.get("pair_count") == index.get("expected_pair_count") == len(rows), "Index pair counts disagree")
    require(report.get("max_discriminant") == bound and report.get("discriminants_checked") == len(labels) and
            report.get("pairs_checked") == report.get("expected_pair_count") == report.get("file_hashes_checked") == len(rows),
            "Verification coverage does not match the catalogue")
    require(report.get("statistics") == index.get("statistics"), "Verification statistics do not match the catalogue")
    stats = index["statistics"]
    require(index.get("component_records") == index.get("component_count") == stats.get("total_component_records") ==
            stats.get("total_components") == sum(r["component_count"] for r in rows), "Component-record totals disagree")

    fields = ["d1", "d2", "component_count", "k3_admissible", "k3_nonadmissible",
              "components_with_saturation", "proper_overlattice_origins", "max_saturation_index",
              "determinant_min", "determinant_max", "distinct_determinants", "marked_origin_count", "duplicate_routes"]
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(fields)
    for row in rows:
        writer.writerow([*pair(row), row["component_count"], row["k3"]["admissible"], row["k3"]["nonadmissible"],
                         row["saturation"]["components"], row["saturation"]["origins"], row["saturation"]["max_index"],
                         row["determinants"]["min"], row["determinants"]["max"], row["determinants"]["distinct"],
                         row["marked_origin_count"], row["duplicate_count"]])
    csv_raw = buffer.getvalue().encode("utf-8")
    coverage = []
    for cutoff in sorted(set([b for b in (42, 100, 200, 300, 500) if b <= bound] + [bound])):
        subset = [r for r in rows if max(pair(r)) <= cutoff]
        label_count = len(labels_through(cutoff))
        coverage.append({"max_discriminant": cutoff, "label_count": label_count, "pair_count": len(subset),
                         "expected_pair_count": label_count * (label_count - 1) // 2,
                         "component_records": sum(r["component_count"] for r in subset), "complete": True})
    repeated = [r for r in rows if r["determinants"]["distinct"] < r["component_count"]]
    maximum = stats["max_saturation_index"]
    maximum_rows = [r for r in rows if r["saturation"]["max_index"] == maximum]
    summary = {
        "schema_version": "1.0", "catalogue_version": index.get("catalogue_version"),
        "max_discriminant": bound, "complete": True, "pair_count": len(rows), "label_count": len(labels),
        "index_sha256": digest, "coverage_by_bound": coverage, "statistics": stats,
        "component_total_meaning": "All aggregate component totals count records separately for each label pair; the same geometric locus may occur in several pairs.",
        "top_10_component_counts": [brief(r) for r in sorted(rows, key=lambda r: (-r["component_count"], pair(r)))[:10]],
        "maximum_saturation_index": {"index": maximum, "pair_count": len(maximum_rows), "pairs": [brief(r) for r in maximum_rows]},
        "pairs_with_same_determinant_nonisometric_components": {
            "pair_count": len(repeated), "first_20_examples": [brief(r) for r in repeated[:20]],
            "interpretation": "Distinct component representatives classified by the exact engine share a determinant. The independent certificate verifier does not itself rerun the pairwise-isometry classification."},
        "verification": {"passed": True, "verifier": report["verifier"], "index_sha256": digest,
                         "pairs_checked": report["pairs_checked"], "limitations": report.get("limitations", [])},
    }
    summary_raw = json_bytes(summary)
    # Preserve all mathematical checks while removing machine-specific path and
    # timing so rerunning verification does not change the deterministic ZIP.
    canonical_report = {k: v for k, v in report.items() if k not in {"index_file", "elapsed_seconds"}}
    readme = f"""# Hassett catalogue through discriminant {bound}

This dataset contains every unordered pair of distinct nonempty Hassett labels
with 6 < d <= {bound} and d congruent to 0 or 2 modulo 6: {len(labels)} labels,
{len(rows):,} pairs, and {stats['total_component_records']:,} component records.
This is a complete finite range. There are infinitely many valid labels overall.
Component totals count records per pair, not globally distinct geometric loci.

## Contents and integrity

catalogue-index.json lists each full pair certificate, its compression, stored
and uncompressed SHA-256 hashes, sizes, and numerical summary. pairs/ contains
the exact JSON certificates, normally compressed as .json.gz. verification.json
records the successful independent verification of this exact index. Only its
machine-specific index_file and elapsed_seconds fields were omitted to make this
archive reproducible. The CSV is one row per pair with labels sorted increasingly.
catalogue-summary-{bound}.json gives finite-range coverage and aggregate records.

The verifier checks full label-pair coverage, stored hashes, all lattice and
inclusion certificates, root exclusion, K3 arithmetic, and starting-parameter
coverage. It does not independently re-enumerate all overlattices or prove all
pairwise nonisometry decisions; those rely on the exact algorithm and its proof.

## Reproduce with the accompanying open-source Python project

Use Python 3.10+ in the matching hassett-lattice-explorer source release.
No third-party runtime packages are required. From that project's root:

```sh
python -m hassett_lattices intersect 8 26 --json
python scripts/expand_catalogue.py --max-discriminant {bound} --gzip --output /path/to/new-empty-data
python scripts/verify_catalogue.py /path/to/new-empty-data/catalogue-index.json --no-limits --report /path/to/verification.json
python scripts/package_catalogue.py /path/to/new-empty-data/catalogue-index.json --verification /path/to/verification.json --output /path/to/deliverables
```

To check this extracted dataset, point the same verify_catalogue.py command at
its catalogue-index.json. Begin a rebuild in a new empty directory; otherwise
expand_catalogue.py validates and reuses completed shards.

Mathematical reference: Song Yang and Xun Yu, On lattice polarizable cubic
fourfolds, Algorithm 7.6, https://arxiv.org/abs/2103.09132.
The source release includes the implementation proof and primary-source fixture
references. Dataset and source are distributed under the MIT license.
"""
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"hassett-catalogue-{bound}.zip"
    temporary = archive.with_name(archive.name + ".tmp")
    prefix = f"hassett-catalogue-{bound}/"
    csv_name, summary_name = f"hassett-component-counts-{bound}.csv", f"catalogue-summary-{bound}.json"
    text_files = {"README.md": readme.encode("utf-8"), "catalogue-index.json": index_raw,
                  "verification.json": json_bytes(canonical_report), csv_name: csv_raw, summary_name: summary_raw}
    text_files["LICENSE"] = (Path(__file__).resolve().parents[1] / "LICENSE").read_bytes()

    def add(z, name, payload, compressed):
        info = zipfile.ZipInfo(prefix + name, date_time=(2026, 11, 13, 0, 0, 0))
        info.compress_type = zipfile.ZIP_STORED if compressed else zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        z.writestr(info, payload, compresslevel=None if compressed else 9)

    try:
        with zipfile.ZipFile(temporary, "w", allowZip64=True) as z:
            for name in sorted(text_files):
                add(z, name, text_files[name], False)
            for row in rows:
                name = row["path"]
                key = f"{pair(row)[0]}-{pair(row)[1]}"
                compressed = row.get("compression") == "gzip"
                require(name == f"pairs/{key}.json" + (".gz" if compressed else ""), f"Unsafe or inconsistent shard path: {name}")
                stored = (base / name).read_bytes()
                require(len(stored) == row["bytes"] and hashlib.sha256(stored).hexdigest() == row["sha256"],
                        f"Shard changed after independent verification: {name}")
                add(z, name, stored, compressed)
        os.replace(temporary, archive)
    finally:
        if temporary.exists():
            temporary.unlink()
    for name, payload in ((csv_name, csv_raw), (summary_name, summary_raw)):
        destination = output / name
        temp = destination.with_name(name + ".tmp")
        temp.write_bytes(payload)
        os.replace(temp, destination)
    return [archive, output / csv_name, output / summary_name]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("--verification", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        paths = package(args.index, args.verification, args.output)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    for path in paths:
        print(f"{path.name}: {path.stat().st_size:,} bytes; SHA256 {hashlib.sha256(path.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
