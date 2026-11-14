#!/usr/bin/env python3
"""Verify constructive K3 certificates without importing any classification engine."""

import argparse
import json
from math import gcd
from pathlib import Path

from verify_certificates import (check_k3, gram, has_arithmetic_obstruction,
                                 integer, pairing, require)


def verify_k3_certificate(g, certificate):
    g = gram(g, 'K3 certificate lattice')
    association = certificate['association']
    check_k3(g, association, 'K3 certificate')
    # check_k3 checks the invariant content/decision. Also bind the displayed
    # forms, split flag and residue obstruction to the actual input lattice.
    p, q = g[0][1], g[0][2]
    form = [3*g[1][1]-p*p, 2*(3*g[1][2]-p*q), 3*g[2][2]-q*q]
    content = gcd(gcd(form[0], form[1]), form[2])
    primitive = [x//content for x in form]
    split = gcd(gcd(3, p), q) == 3
    require(association['discriminant_form'] == form, 'Wrong discriminant form')
    require(association['primitive_form'] == primitive, 'Wrong primitive form')
    require(association['h_splits_orthogonally'] is split, 'Wrong split flag')
    residues = [[y, z] for y in range(3) for z in range(3)
                if (primitive[0]*y*y+primitive[1]*y*z+primitive[2]*z*z) % 3 == 1]
    mod3 = association['mod3_witness']
    require((mod3 in residues) if residues else mod3 is None, 'Wrong modulo-three witness')
    expected_obstructions = []
    if content % 4 == 0:
        expected_obstructions.append('divisible by 4')
    if content % 9 == 0:
        expected_obstructions.append('divisible by 9')
    remaining, prime = content, 2
    while prime*prime <= remaining:
        if remaining % prime == 0:
            if prime != 2 and prime % 3 == 2:
                expected_obstructions.append(f'divisible by the odd prime {prime}, congruent to 2 modulo 3')
            while remaining % prime == 0:
                remaining //= prime
        prime = 3 if prime == 2 else prime+2
    if remaining > 2 and remaining % 3 == 2:
        expected_obstructions.append(f'divisible by the odd prime {remaining}, congruent to 2 modulo 3')
    if split and not residues:
        expected_obstructions.append('primitive discriminant form does not represent 1 modulo 3')
    require(association['obstructions'] == expected_obstructions, 'Wrong obstruction explanation')
    witness, bound = certificate['witness'], certificate['search_bound']
    require(integer(bound) and bound >= 0, 'Invalid search bound')
    if not association['admissible']:
        require(witness is None and bound == 0, 'Negative certificate has a witness/search')
        require(bool(association['obstructions']), 'Missing obstruction explanation')
        return False
    require(isinstance(witness, dict), 'Missing positive K3 witness')
    v = witness['vector']
    require(isinstance(v, list) and len(v) == 3 and all(integer(x) for x in v), 'Invalid vector')
    require(v[0] == 0 and gcd(v[1], v[2]) == 1, 'Nonprimitive marking')
    h = [1, 0, 0]
    hv, vv = pairing(g, h, v), pairing(g, v, v)
    d = 3*vv-hv*hv
    require(witness['gram'] == [[3, hv], [hv, vv]], 'Wrong rank-two Gram')
    require(integer(witness['discriminant']) and witness['discriminant'] == d, 'Wrong label')
    require(d > 6 and d % 6 in (0, 2) and not has_arithmetic_obstruction(d), 'Inadmissible label')
    require(witness['admissible'] is True and d <= bound, 'Witness bound/decision mismatch')
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    records = json.loads(args.input.read_text())
    require(bool(records), 'No K3 certificates')
    positive = sum(verify_k3_certificate(r['gram'], r['certificate']) for r in records)
    print(f'K3 certificates passed: {len(records)} lattices, {positive} witnesses, '
          f'{len(records)-positive} obstructions.')


if __name__ == '__main__':
    main()
