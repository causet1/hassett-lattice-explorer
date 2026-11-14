"""Command-line interface: python -m hassett_lattices intersect 8 14 --json."""

import argparse
import json
from pathlib import Path
import sys

from .core import Limits, ResourceLimitError, admissible_discriminant, intersection_components, valid_discriminant


def main(argv=None):
    parser = argparse.ArgumentParser(description="Exact irreducible components of intersections of two Hassett divisors")
    sub = parser.add_subparsers(dest="command", required=True)
    intersect = sub.add_parser("intersect", help="run Yang–Yu Algorithm 7.6")
    intersect.add_argument("d1", type=int)
    intersect.add_argument("d2", type=int)
    intersect.add_argument("--json", action="store_true", help="print full exact certificates as JSON")
    intersect.add_argument("--output", type=Path, help="write full JSON certificates to this file")
    intersect.add_argument("--max-work", type=int, default=5_000_000)
    intersect.add_argument("--timeout", type=float, default=60.0, help="seconds; no partial results are returned")
    intersect.add_argument("--no-limits", action="store_true", help="disable both work and time limits")
    admissible = sub.add_parser("admissible", help="check nonemptiness and Hassett's untwisted K3 criterion")
    admissible.add_argument("d", type=int)
    args = parser.parse_args(argv)
    if args.command == "admissible":
        print(json.dumps({"d": args.d, "nonempty": valid_discriminant(args.d), "untwisted_k3": admissible_discriminant(args.d)}, indent=2))
        return 0
    try:
        limits = Limits(None, None) if args.no_limits else Limits(args.max_work, args.timeout)
        result = intersection_components(args.d1, args.d2, limits=limits)
    except (ValueError, ResourceLimitError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"C_{args.d1} ∩ C_{args.d2}: {result['component_count']} irreducible components (complete).")
        print("  component       det   tau  index  generic untwisted K3")
        for c in result["components"]:
            print(f"  {c['id']:<15} {c['determinant']:>5} {c['tau']:>5} {c['index']:>6}  {'yes' if c['k3_association']['admissible'] else 'no'}")
        print(f"Exact integer arithmetic; {result['diagnostics']['work_units']} work units.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
