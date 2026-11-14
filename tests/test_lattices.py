"""Regression tests from primary papers, plus independent certificate checks.

Run without third-party packages: python -m unittest discover -s tests -v
"""

from collections import Counter
from functools import lru_cache
from math import gcd
from pathlib import Path
import json
import random
import subprocess
import sys
import tempfile
import unittest

from hassett_lattices import (
    Limits, ResourceLimitError, admissible_discriminant, determinant,
    h_fixed_isometry, intersection_components, lattice_k3_association,
    norm_two_vector,
)


PUBLISHED = {
    (8, 14): [21, 29, 32, 36, 37],
    (8, 26): [29, 36, 48, 53, 61, 64, 68, 69],
    (8, 38): [36, 45, 61, 68, 80, 85, 93, 96, 100, 101],
    (20, 12): [20, 32, 53, 68, 77, 80],
    (20, 38): [45, 77, 92, 120, 133, 157, 168, 188, 197, 213, 220, 232, 237, 245, 248, 252, 253],
}


def det3(a):
    # Independent Leibniz expansion, not the engine's determinant routine.
    return (a[0][0]*a[1][1]*a[2][2] + a[0][1]*a[1][2]*a[2][0]
            + a[0][2]*a[1][0]*a[2][1] - a[0][2]*a[1][1]*a[2][0]
            - a[0][1]*a[1][0]*a[2][2] - a[0][0]*a[1][2]*a[2][1])


def congruence(g, e):
    return [[sum(e[k][i]*g[k][l]*e[l][j] for k in range(3) for l in range(3))
             for j in range(3)] for i in range(3)]


def primitive_columns(e, i, j):
    return gcd(*(abs(e[r][i]*e[s][j]-e[s][i]*e[r][j])
                 for r, s in [(0, 1), (0, 2), (1, 2)])) == 1


@lru_cache(None)
def result(a, b):
    return intersection_components(a, b)


class PublishedCases(unittest.TestCase):
    def test_all_five_published_counts_and_discriminants(self):
        for pair, expected in PUBLISHED.items():
            with self.subTest(pair=pair):
                r = result(*pair)
                self.assertTrue(r['complete'])
                self.assertEqual(r['component_count'], len(expected))
                self.assertEqual(sorted(c['determinant'] for c in r['components']), expected)

    def test_abbva_geometric_basis(self):
        for c in result(8, 14)['components']:
            tau = c['tau'] + 1
            e = [[1, 0, 1], [0, 1, 0], [0, 0, 1]]
            self.assertEqual(congruence(c['gram'], e), [[3, 1, 4], [1, 3, tau], [4, tau, 10]])
        self.assertEqual([c['tau'] + 1 for c in result(8, 14)['components']], [-1, 0, 1, 2, 3])

    def test_awada_geometric_basis(self):
        for c in result(8, 26)['components']:
            tau = c['tau'] + 2
            e = [[1, 0, 2], [0, 1, 0], [0, 0, 1]]
            self.assertEqual(congruence(c['gram'], e), [[3, 1, 7], [1, 3, tau], [7, tau, 25]])
        self.assertEqual([c['tau'] + 2 for c in result(8, 26)['components']], list(range(-1, 7)))

    def test_yang_yu_index_two_component(self):
        matches = [c for c in result(20, 12)['components'] if c['determinant'] == 20]
        self.assertEqual(len(matches), 1)
        c = matches[0]
        self.assertTrue(any(o['index'] == 2 and o['tau'] == 0 for o in c['origins']))
        u = [[1, 0, 0], [0, -1, 1], [0, 1, 0]]
        self.assertEqual(congruence(c['gram'], u), [[3, 1, 1], [1, 3, -3], [1, -3, 7]])


class CertificateTests(unittest.TestCase):
    def test_root_bound_keeps_the_equality_case(self):
        g = [[3, 0, 0], [0, 2, 0], [0, 0, 4]]
        root = norm_two_vector(g)
        self.assertIsNotNone(root)
        self.assertEqual(sum(root[i]*g[i][j]*root[j] for i in range(3) for j in range(3)), 2)
        self.assertIsNone(norm_two_vector([[3, 0, 0], [0, 3, 0], [0, 0, 3]]))

    def test_congruence_sieve_matches_exhaustive_residues(self):
        from hassett_lattices.core import _Budget, _normalize, _saturation_residues
        budget = _Budget(Limits(max_work=None, timeout_seconds=None))
        # All three normalization cases, noninvertible coefficients, negative
        # parameters, and indices divisible by 3 (the extra equation matters).
        for pair in [(8, 14), (8, 12), (12, 18), (20, 42), (30, 54)]:
            d1, d2 = _normalize(*pair)
            p, q = int(d1 % 6 == 2), int(d2 % 6 == 2)
            aa = (d1+p)//3
            for tau in range(-12, 13):
                for n in range(1, 41):
                    expected = [(a, b) for a in range(n) for b in range(n)
                                if gcd(b, n) == 1 and (3*a+p*b+q) % n == 0
                                and (p*a+aa*b+tau) % n == 0]
                    self.assertEqual(_saturation_residues(d1, p, q, aa, tau, n, budget), expected)

    def test_every_origin_in_published_cases(self):
        checked = 0
        for pair in PUBLISHED:
            r = result(*pair)
            for c in r['components']:
                g = c['gram']
                self.assertEqual(det3(g), c['determinant'])
                self.assertGreater(det3(g), 0)
                self.assertTrue(all((g[i][i]-g[0][i]) % 2 == 0 for i in range(3)))
                self.assertIsNone(norm_two_vector(g))
                for o in c['origins']:
                    e, s = o['embedding'], o['basis_map_to_representative']
                    self.assertEqual(congruence(g, e), o['base_gram'])
                    self.assertEqual(congruence(g, s), o['overlattice_gram'])
                    self.assertEqual(abs(det3(e)), o['index'])
                    self.assertEqual(abs(det3(s)), 1)
                    self.assertEqual([e[i][0] for i in range(3)], [1, 0, 0])
                    self.assertTrue(primitive_columns(e, 0, 1))
                    self.assertTrue(primitive_columns(e, 0, 2))
                    b = congruence(g, e)
                    self.assertEqual(3*b[1][1]-b[0][1]**2, r['d1'])
                    self.assertEqual(3*b[2][2]-b[0][2]**2, r['d2'])
                    self.assertEqual(det3(b), o['index']**2*det3(g))
                    checked += 1
        self.assertGreaterEqual(checked, 46)

    def test_rejected_roots_have_actual_square_two(self):
        count = 0
        for pair in PUBLISHED:
            for c in result(*pair)['candidates']:
                v = c['root_witness']
                if not c['root_free']:
                    self.assertIsNotNone(v)
                    self.assertEqual(sum(v[i]*c['gram'][i][j]*v[j]
                                         for i in range(3) for j in range(3)), 2)
                    count += 1
        self.assertGreater(count, 0)

    def test_distinct_routes_are_merged(self):
        r = result(8, 24)
        self.assertEqual(r['component_count'], 5)
        self.assertEqual(r['diagnostics']['duplicate_count'], 1)
        c = next(c for c in r['components'] if c['determinant'] == 16)
        self.assertEqual({(o['tau'], o['index']) for o in c['origins']}, {(4, 1), (0, 2)})

    def test_equal_determinants_are_not_identified(self):
        r = result(8, 96)
        self.assertEqual(r['component_count'], 11)
        c = [c for c in r['components'] if c['determinant'] == 64]
        self.assertEqual(len(c), 2)
        self.assertIsNone(h_fixed_isometry(c[0]['gram'], c[1]['gram']))

    def test_swapping_divisors(self):
        for pair in PUBLISHED:
            r, s = result(*pair), result(*pair[::-1])
            self.assertEqual(r['components'], s['components'])


class K3Tests(unittest.TestCase):
    def test_label_arithmetic(self):
        for d in [14, 26, 38, 42, 62, 74, 78]:
            self.assertTrue(admissible_discriminant(d), d)
        for d in [2, 6, 8, 12, 18, 20, 24, 30, 44, 50, 54, 66, 90]:
            self.assertFalse(admissible_discriminant(d), d)

    def test_all_components_with_an_admissible_input(self):
        for pair in [(8, 14), (8, 26), (8, 38), (20, 38)]:
            self.assertTrue(all(c['k3_association']['admissible'] for c in result(*pair)['components']))

    def test_component_test_uses_the_lattice_not_its_determinant(self):
        r = result(8, 12)
        decisions = {c['tau']: c['k3_association']['admissible'] for c in r['components']}
        self.assertEqual(decisions, {0: False, 1: True, 2: False})

    def test_split_congruence_is_required(self):
        no = lattice_k3_association([[3, 0, 0], [0, 4, 0], [0, 0, 6]])
        yes = lattice_k3_association([[3, 0, 0], [0, 4, 0], [0, 0, 10]])
        self.assertEqual(no['content'], 6)
        self.assertEqual(yes['content'], 6)
        self.assertFalse(no['admissible'])
        self.assertTrue(yes['admissible'])

    def test_sixty_basis_changes(self):
        rng = random.Random(20261112)
        grams = [
            [[3, 0, 0], [0, 4, 0], [0, 0, 6]],
            [[3, 0, 0], [0, 4, 0], [0, 0, 10]],
            *[c['gram'] for c in result(8, 12)['components']],
        ]
        for g in grams:
            expected = lattice_k3_association(g)['admissible']
            for _ in range(12):
                a, b, c, d = [rng.randint(-2, 2) for _ in range(4)]
                # Product of two elementary shears has determinant one.
                u = [[1, a, b], [0, 1, c], [0, d, 1+c*d]]
                new = congruence(g, u)
                self.assertEqual(lattice_k3_association(new)['admissible'], expected)
                iso = h_fixed_isometry(new, g)
                self.assertIsNotNone(iso)
                self.assertEqual(congruence(g, iso), new)
                self.assertEqual(abs(det3(iso)), 1)
                self.assertIsNone(norm_two_vector(new))


class InputAndCliTests(unittest.TestCase):
    def test_invalid_inputs(self):
        for a, b in [(8, 8), (6, 14), (7, 14), (8, 9), (8.0, 14), (True, 14), (-8, 14)]:
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                intersection_components(a, b)

    def test_work_limit_never_returns_partial_success(self):
        with self.assertRaises(ResourceLimitError):
            intersection_components(8, 14, limits=Limits(max_work=1))

    def test_json_roundtrip(self):
        self.assertEqual(json.loads(json.dumps(result(20, 12))), result(20, 12))

    def test_cli_success_and_failure(self):
        ok = subprocess.run([sys.executable, '-m', 'hassett_lattices', 'intersect', '8', '26', '--json'],
                            capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(ok.stdout)['component_count'], 8)
        bad = subprocess.run([sys.executable, '-m', 'hassett_lattices', 'intersect', '8', '14', '--max-work', '1'],
                             capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertIn('no complete result', bad.stderr)
        self.assertEqual(bad.stdout, '')

    def test_cli_writes_an_importable_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'result.json'
            subprocess.run([sys.executable, '-m', 'hassett_lattices', 'intersect', '20', '12', '--output', str(path)],
                           capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(path.read_text())['component_count'], 6)


if __name__ == '__main__':
    unittest.main()
