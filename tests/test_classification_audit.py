"""Adversarial cases that ordinary certificate checks cannot settle."""

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from audit_classification import Audit
from verify_certificates import RootVerifier, VerificationError, congruence, verify_result
from hassett_lattices import intersection_components, lattice_k3_association


class ClassificationAuditTests(unittest.TestCase):
    def test_published_and_equal_determinant_cases(self):
        for pair in ((8, 14), (8, 26), (8, 38), (20, 12), (20, 38), (8, 24), (8, 96)):
            with self.subTest(pair=pair):
                result = intersection_components(*pair)
                self.assertEqual(Audit().result(result)['components'], result['component_count'])

    def test_missing_saturation_passes_certificates_but_fails_audit(self):
        result = deepcopy(intersection_components(20, 12))
        removed = next(c for c in result['components'] if c['determinant'] == 20)
        result['components'].remove(removed)
        result['component_count'] -= 1
        for origin in removed['origins']:
            next(c for c in result['candidates'] if c['tau'] == origin['tau'])['accepted_overlattices'] -= 1
        result['diagnostics']['accepted_marked_lattices'] -= len(removed['origins'])
        result['diagnostics']['duplicate_count'] = result['diagnostics']['accepted_marked_lattices']-result['component_count']
        verify_result(result, RootVerifier(100000))
        with self.assertRaisesRegex(VerificationError, 'Saturation origin coverage'):
            Audit().result(result)

    def test_independent_isometry_search_finds_basis_change(self):
        g = intersection_components(8, 14)['components'][0]['gram']
        changed = congruence(g, [[1, 1, 0], [0, 1, 1], [0, 0, 1]])
        self.assertNotEqual(g, changed)
        self.assertTrue(Audit().isometric(g, changed))
        same_det = [c['gram'] for c in intersection_components(8, 96)['components'] if c['determinant'] == 64]
        self.assertEqual(len(same_det), 2)
        self.assertFalse(Audit().isometric(*same_det))

    def test_audit_budget_is_not_partial_success(self):
        with self.assertRaises(VerificationError):
            Audit(max_work=1).result(intersection_components(8, 14))

    def test_split_isometry_class_passes_certificates_but_fails_audit(self):
        result = deepcopy(intersection_components(8, 24))
        component = next(c for c in result['components'] if len(c['origins']) > 1)
        origin = component['origins'].pop()
        n, a, b = (origin[k] for k in ('index', 'a', 'b'))
        g = origin['overlattice_gram']
        self.assertNotEqual(g, component['gram'])
        origin['basis_map_to_representative'] = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        origin['embedding'] = [[1, 0, -a], [0, 1, -b], [0, 0, n]]
        result['components'].append({**component, 'id': 'deliberate-duplicate', 'gram': g,
                                     'origins': [origin], 'tau': origin['tau'], 'index': n,
                                     'k3_association': lattice_k3_association(g)})
        result['component_count'] += 1
        result['diagnostics']['duplicate_count'] -= 1
        verify_result(result, RootVerifier(100000))
        with self.assertRaisesRegex(VerificationError, 'Duplicate h-fixed isometry'):
            Audit().result(result)


if __name__ == '__main__':
    unittest.main()
