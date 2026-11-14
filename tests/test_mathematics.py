"""Mathematical certificate and independently generated saturation checks."""

from copy import deepcopy
from itertools import product
import json
from math import gcd, isqrt
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from hassett_lattices import (Limits, ResourceLimitError, intersection_components,
                             k3_certificate, k3_witness, primitive_markings)
from audit_hnf import HnfAudit, row_hermite_forms
from verify_certificates import VerificationError, congruence
from verify_k3_certificates import verify_k3_certificate


class MathematicsTests(unittest.TestCase):
    def test_all_embedded_k3_certificates(self):
        pairs = json.loads((ROOT/'web/catalogue.json').read_text())['pairs']
        decisions = set()
        for r in pairs:
            for c in r['components']:
                certificate = k3_certificate(c['gram'])
                decision = verify_k3_certificate(c['gram'], certificate)
                self.assertEqual(decision, c['k3_association']['admissible'])
                decisions.add(decision)
        self.assertEqual(decisions, {False, True})

    def test_split_obstruction_and_bounded_search_are_distinct(self):
        bad = [[3, 0, 0], [0, 4, 0], [0, 0, 6]]
        good = [[3, 0, 0], [0, 4, 0], [0, 0, 10]]
        self.assertFalse(verify_k3_certificate(bad, k3_certificate(bad)))
        self.assertIsNone(k3_witness(good, 7))
        cert = k3_certificate(good)
        self.assertTrue(verify_k3_certificate(good, cert))
        self.assertEqual(cert['witness']['discriminant'], 42)
        with self.assertRaises(ResourceLimitError):
            k3_certificate(good, limits=Limits(max_work=1))
        with self.assertRaises(ValueError):
            primitive_markings(good, True)
        with self.assertRaises(ValueError):
            primitive_markings([[3, 0, 0], [0, 3, 0], [0, 0, 4]], 20)

    def test_markings_match_independent_rectangles_after_basis_changes(self):
        rng = random.Random(20261115)
        base = [[3, 1, 0], [1, 3, 1], [0, 1, 4]]
        for _ in range(25):
            e = [[1, rng.randrange(-3, 4), rng.randrange(-3, 4)],
                 [0, 1, rng.randrange(-6, 7)], [0, 0, 1]]
            g = congruence(base, e)
            p, q = g[0][1:]
            a, b, c = 3*g[1][1]-p*p, 3*g[1][2]-p*q, 3*g[2][2]-q*q
            bound = 100
            delta = a*c-b*b
            expected = set()
            for y, z in product(range(-isqrt(bound*c//delta), isqrt(bound*c//delta)+1),
                                range(-isqrt(bound*a//delta), isqrt(bound*a//delta)+1)):
                d = a*y*y+2*b*y*z+c*z*z
                if gcd(y, z) == 1 and (y > 0 or y == 0 and z > 0) and 6 < d <= bound and d % 6 in (0, 2):
                    expected.add((d, y, z))
            observed = {(m['discriminant'], *m['vector'][1:]) for m in primitive_markings(g, bound)}
            self.assertEqual(observed, expected)
            self.assertTrue(verify_k3_certificate(g, k3_certificate(g)))

    def test_tampered_k3_certificates_fail(self):
        g = [[3, 1, 0], [1, 3, 1], [0, 1, 4]]
        original = k3_certificate(g)
        for mutate in (
            lambda c: c['witness'].update(vector=[0, 2, 2]),
            lambda c: c['witness'].update(discriminant=42),
            lambda c: c.update(search_bound=1),
            lambda c: c['association'].update(admissible=False),
            lambda c: c['association'].update(content=4),
            lambda c: c['association'].update(obstructions=['unsupported claim']),
        ):
            c = deepcopy(original)
            mutate(c)
            with self.assertRaises(VerificationError):
                verify_k3_certificate(g, c)

    def test_general_hermite_forms_and_saturation_coverage(self):
        self.assertEqual(len(list(row_hermite_forms(2))), 7)
        self.assertEqual(len(list(row_hermite_forms(4))), 35)
        self.assertIn([[1, 0, 0], [0, 2, 0], [0, 0, 2]], list(row_hermite_forms(4)))
        audit = HnfAudit(500000)
        r = intersection_components(12, 20)
        self.assertEqual(audit.result(r)['components'], 6)
        actual = {(o['tau'], o['index'], o['a'], o['b'])
                  for c in r['components'] for o in c['origins']}
        self.assertEqual(audit.origins(r), actual)
        self.assertIn((0, 2, 1, 1), actual)


if __name__ == '__main__':
    unittest.main()
