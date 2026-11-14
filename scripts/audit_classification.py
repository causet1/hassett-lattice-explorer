#!/usr/bin/env python3
"""Independently re-enumerate saturation origins and check h-fixed nonisometry.

This deliberately slower audit uses Fraction matrix multiplication and full
three-coordinate vector boxes, rather than the engine's congruence formulas and
binary Schur search. It imports no engine code. It shares the documented finite
parameterization and the independent certificate checker, not a new geometric
proof. Intended for regression-sized catalogues, not the full range through 500.
"""

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from itertools import combinations, product
import json
from math import gcd, isqrt
from pathlib import Path
import sys

from verify_certificates import (RootVerifier, VerificationError, congruence, det,
                                 pairing, require, unpack, verify_result)
from verify_catalogue import _check_starting_coverage_and_unique_origins


class Audit:
    def __init__(self, max_work=5_000_000):
        require(type(max_work) is int and max_work > 0, 'max_work must be positive')
        self.max_work = max_work
        self.work = 0
        self.roots = RootVerifier(max_work)

    def tick(self):
        self.work += 1
        require(self.work <= self.max_work, 'Classification audit work budget exhausted; no complete audit')

    def origins(self, result):
        d1, d2 = result['d1'], result['d2']
        p, q = int(d1 % 6 == 2), int(d2 % 6 == 2)
        radius = isqrt(d1*d2) + 1
        found = set()
        for tau in range(-radius, radius + 1):
            self.tick()
            if not p*q and tau < 0:
                continue
            g = [[3, p, q], [p, (d1+p)//3, tau], [q, tau, (d2+q)//3]]
            determinant = det(g)
            if determinant <= 0 or self.roots.find_root(g) is not None:
                continue
            for n in range(1, isqrt(determinant) + 1):
                self.tick()
                if determinant % (n*n):
                    continue
                for a, b in product(range(n), repeat=2):
                    self.tick()
                    if gcd(b, n) != 1:
                        continue
                    basis = [[1, 0, Fraction(a, n)], [0, 1, Fraction(b, n)],
                             [0, 0, Fraction(1, n)]]
                    rational = congruence(g, basis)
                    if any(Fraction(x).denominator != 1 for row in rational for x in row):
                        continue
                    lattice = [[int(x) for x in row] for row in rational]
                    if any((lattice[i][i]-lattice[0][i]) % 2 for i in range(3)):
                        continue
                    if self.roots.find_root(lattice) is None:
                        found.add((tau, n, a, b))
        return found

    def vectors(self, g, norm, h_pairing):
        determinant = det(g)
        cofactors = [g[1][1]*g[2][2]-g[1][2]**2,
                     g[0][0]*g[2][2]-g[0][2]**2,
                     g[0][0]*g[1][1]-g[0][1]**2]
        bounds = [isqrt(norm*c//determinant) for c in cofactors]
        found = []
        for v in product(*(range(-b, b+1) for b in bounds)):
            self.tick()
            if sum(g[0][i]*v[i] for i in range(3)) == h_pairing and pairing(g, v, v) == norm:
                found.append(v)
        return found

    def isometric(self, source, target):
        if det(source) != det(target):
            return False
        first = self.vectors(target, source[1][1], source[0][1])
        second = self.vectors(target, source[2][2], source[0][2])
        for u, v in product(first, second):
            self.tick()
            change = [[1, u[0], v[0]], [0, u[1], v[1]], [0, u[2], v[2]]]
            if abs(det(change)) == 1 and congruence(target, change) == source:
                return True
        return False

    def result(self, result):
        verify_result(result, self.roots)
        _check_starting_coverage_and_unique_origins(result)
        actual = {tuple(o[k] for k in ('tau', 'index', 'a', 'b'))
                  for c in result['components'] for o in c['origins']}
        expected = self.origins(result)
        require(actual == expected,
                f'Saturation origin coverage differs: missing={sorted(expected-actual)[:8]}, '
                f'extra={sorted(actual-expected)[:8]}')
        comparisons = 0
        for left, right in combinations(result['components'], 2):
            if left['determinant'] == right['determinant']:
                comparisons += 1
                require(not self.isometric(left['gram'], right['gram']),
                        f'Duplicate h-fixed isometry classes: {left["id"]}, {right["id"]}')
        self.roots.cache.clear()
        return {'pair': [result['d1'], result['d2']], 'components': result['component_count'],
                'origins': len(expected), 'equal_determinant_comparisons': comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='Full JSON result or embedded catalogue')
    parser.add_argument('--max-work', type=int, default=5_000_000,
                        help='Separate limits for audit iterations and independent root vectors')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        raw = args.input.read_bytes()
        audit = Audit(args.max_work)
        results = unpack(json.loads(raw))
        require(bool(results), 'No pair results to audit')
        pairs = [audit.result(result) for result in results]
        report = {'passed': True, 'validated_at': datetime.now(timezone.utc).isoformat(),
                  'input_sha256': hashlib.sha256(raw).hexdigest(), 'pairs': pairs,
                  'work_units': audit.work, 'root_vectors': audit.roots.vectors,
                  'scope': 'Independent finite saturation-origin enumeration and h-fixed nonisometry for these inputs only; shares the documented parameterization and certificate checker. Not a proof of the geometric theorems or an audit of other inputs.'}
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2)+'\n')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Audit failed: {exc}', file=sys.stderr)
        return 1
    print(f'PASS: {len(pairs)} pairs, {sum(p["origins"] for p in pairs)} saturation origins; '
          f'{sum(p["equal_determinant_comparisons"] for p in pairs)} nonisometry comparisons.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
