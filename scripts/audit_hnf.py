#!/usr/bin/env python3
"""Audit saturation coverage by general row Hermite forms of inclusion matrices.

Unlike audit_classification.py, this does not assume that the extension quotient
is cyclic or use the (a*h+b*u+v)/n parametrization. All index-n row Hermite forms
are enumerated, then both primitive-label conditions are tested by minors.
It reuses the independent Fraction linear algebra, root and isometry checks.
"""

import argparse
from fractions import Fraction
import hashlib
import json
from math import isqrt
from pathlib import Path

from audit_classification import Audit
from verify_certificates import congruence, det, primitive_pair, require, unpack


def inverse(a):
    rows = [[Fraction(x) for x in row] + [Fraction(i == j) for j in range(3)]
            for i, row in enumerate(a)]
    for j in range(3):
        pivot = next(i for i in range(j, 3) if rows[i][j])
        rows[j], rows[pivot] = rows[pivot], rows[j]
        scale = rows[j][j]
        rows[j] = [x/scale for x in rows[j]]
        for i in range(3):
            if i != j:
                scale = rows[i][j]
                rows[i] = [x-scale*y for x, y in zip(rows[i], rows[j])]
    return [row[3:] for row in rows]


def row_hermite_forms(n):
    for a in range(1, n+1):
        if n % a:
            continue
        for b in range(1, n//a+1):
            if n % (a*b):
                continue
            c = n//(a*b)
            for x in range(b):
                for y in range(c):
                    for z in range(c):
                        yield [[a, x, y], [0, b, z], [0, 0, c]]


class HnfAudit(Audit):
    def origins(self, result):
        d1, d2 = result['d1'], result['d2']
        p, q = int(d1 % 6 == 2), int(d2 % 6 == 2)
        radius = isqrt(d1*d2)+1
        found = set()
        for tau in range(-radius, radius+1):
            self.tick()
            if not p*q and tau < 0:
                continue  # proved sign symmetry of a normalized generator
            g = [[3, p, q], [p, (d1+p)//3, tau], [q, tau, (d2+q)//3]]
            determinant = det(g)
            if determinant <= 0 or self.roots.find_root(g) is not None:
                continue
            for n in range(1, isqrt(determinant)+1):
                if determinant % (n*n):
                    continue
                for e in row_hermite_forms(n):
                    self.tick()
                    if not primitive_pair(e, 1) or not primitive_pair(e, 2):
                        continue
                    h = congruence(g, inverse(e))
                    if any(x.denominator != 1 for row in h for x in row):
                        continue
                    h = [[int(x) for x in row] for row in h]
                    # The minors force a=b=1, so the first column is h.
                    require(e[0][0] == e[1][1] == 1, 'Hermite primitive labels')
                    if any((h[i][i]-h[0][i]) % 2 for i in range(3)):
                        continue
                    if self.roots.find_root(h) is None:
                        # Translate the independently generated lattice into
                        # the engine's residue convention for comparison only.
                        found.add((tau, n, (-e[0][2]) % n, (-e[1][2]) % n))
        return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--max-work', type=int, default=50_000_000)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    results = unpack(json.loads(raw))
    require(bool(results), 'No results to audit')
    audit = HnfAudit(args.max_work)
    pairs = [audit.result(r) for r in results]
    report = {'passed': True, 'input_sha256': hashlib.sha256(raw).hexdigest(),
              'pairs': pairs, 'work_units': audit.work,
              'scope': 'All row Hermite inclusion forms; independent root and marked-isometry checks. '
                       'Finite inputs only; geometric theorems are reviewed in docs/math-audit.md.'}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(f'Hermite audit passed: {len(pairs)} pairs, '
          f'{sum(p["origins"] for p in pairs)} origins, {audit.work} work units.')


if __name__ == '__main__':
    main()
