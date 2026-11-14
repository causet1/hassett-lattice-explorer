#!/usr/bin/env python3
"""Rebuild the offline catalogue and inject exactly those results into the UI."""

import argparse
from itertools import combinations
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hassett_lattices import intersection_components


PUBLISHED = {
    (8, 14): ('Auel et al., Theorem 4', 'https://arxiv.org/abs/1205.0237v4', [21,29,32,36,37]),
    (8, 26): ('Awada, Proposition 3.2', 'https://arxiv.org/abs/1910.10182v2', [29,36,48,53,61,64,68,69]),
    (8, 38): ('Awada, Theorem 1.1(2)', 'https://arxiv.org/abs/1910.10182v2', [36,45,61,68,80,85,93,96,100,101]),
    (12, 20): ('Yang–Yu, Theorem 7.11', 'https://arxiv.org/abs/2103.09132', [20,32,53,68,77,80]),
    (20, 38): ('Yang–Yu, Theorem 7.9', 'https://arxiv.org/abs/2103.09132', [45,77,92,120,133,157,168,188,197,213,220,232,237,245,248,252,253]),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--max-discriminant', type=int, default=42)
    ap.add_argument('--no-inject', action='store_true')
    args = ap.parse_args()
    ds = [d for d in range(8, args.max_discriminant+1) if d % 6 in (0, 2)]
    pairs = []
    for a, b in combinations(ds, 2):
        r = intersection_components(a, b)
        # Omit nondeterministic timing, preserving reproducible mathematical data.
        r['diagnostics'].pop('elapsed_seconds', None)
        if (a, b) in PUBLISHED:
            name, url, expected = PUBLISHED[a, b]
            actual = sorted(c['determinant'] for c in r['components'])
            if actual != expected:
                raise AssertionError(f'Published regression failed: {a}, {b}')
            r['validation'] = {'status': 'matched', 'reference': name, 'url': url,
                               'expected_count': len(expected), 'expected_discriminants': expected}
        else:
            r['validation'] = {'status': 'computed', 'reference': 'Exact algorithm; not an independent published fixture'}
        pairs.append(r)
    catalogue = {
        'schema_version': '1.0', 'title': 'Hassett Lattice Explorer',
        'version': '1.0.0', 'reference_date': '2026-11-12',
        'discriminants': ds, 'max_discriminant': args.max_discriminant,
        'pair_count': len(pairs), 'pairs': pairs,
        'scope': 'All pairs of distinct valid discriminants up to the indicated bound. Exact component classification, not multiplicities or rationality decisions.',
        'license': 'MIT',
    }
    target = ROOT/'web'/'catalogue.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    if not args.no_inject:
        ui = ROOT/'web'/'explorer.html'
        content = ui.read_text(encoding='utf-8')
        payload = json.dumps(catalogue, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
        pattern = r'(<script\b[^>]*\bid=["\']catalogue-data["\'][^>]*>)[\s\S]*?(</script>)'
        replaced, count = re.subn(pattern, lambda m: m.group(1)+payload+m.group(2), content, count=1)
        if count != 1:
            raise ValueError('Expected exactly one script#catalogue-data in web/explorer.html')
        ui.write_text(replaced, encoding='utf-8')
    print(f'Computed {len(pairs)} intersections for {len(ds)} divisors; saved {target.name}.')


if __name__ == '__main__':
    main()
