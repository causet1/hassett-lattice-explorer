#!/usr/bin/env python3
"""Build static Site assets from a complete, independently verified catalogue."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogue_directory", type=Path)
    parser.add_argument("--verification", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--summary-csv", type=Path)
    parser.add_argument("--source-archive", type=Path)
    args = parser.parse_args()
    catalogue = args.catalogue_directory.resolve()
    index_bytes = (catalogue / "catalogue-index.json").read_bytes()
    index = json.loads(index_bytes)
    report = json.loads(args.verification.read_bytes())
    if index.get("complete") is not True or report.get("passed") is not True:
        raise ValueError("A complete catalogue and a passing verification report are required")
    index_hash = hashlib.sha256(index_bytes).hexdigest()
    if report.get("index_sha256") != index_hash:
        raise ValueError("Verification report does not identify this exact catalogue index")
    output = args.output.resolve()
    data = output / "data"
    data.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "web" / "explorer.html", output / "index.html")
    (data / "catalogue-index.json").write_bytes(index_bytes)
    for row in index["pairs"]:
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe catalogue path")
        source = catalogue / relative
        target = data / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    shutil.copyfile(args.verification, data / "verification.json")
    if args.summary_csv:
        shutil.copyfile(args.summary_csv, data / "component-counts.csv")
    if args.source_archive:
        shutil.copyfile(args.source_archive, output / "hassett-lattice-explorer.zip")
    guide = ROOT / "docs" / "mathematics.pdf"
    if guide.is_file():
        shutil.copyfile(guide, output / "hassett-lattice-guide.pdf")
    print(json.dumps({"directory": str(output), "pairs": index["pair_count"],
                      "max_discriminant": index["max_discriminant"],
                      "index_sha256": index_hash}))


if __name__ == "__main__":
    main()
