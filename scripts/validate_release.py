#!/usr/bin/env python3
"""Run the reproducible release checks and record their actual outcomes."""

import argparse
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hassett_lattices import intersection_components
from release_support import source_hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hosted-data', type=Path,
                        help='Additionally exercise the viewer with this real expanded catalogue')
    parser.add_argument('--output-dir', type=Path, default=ROOT/'build'/'validation',
                        help='Fresh reports directory; historical docs/ reports are preserved')
    args = parser.parse_args()
    if shutil.which('node') is None:
        parser.error('Node.js is required for the UI checks; install Node 22 or 24 and add it to PATH')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern='test_*.py')
    run = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    print(stream.getvalue(), end='')
    if not run.wasSuccessful():
        raise SystemExit(1)
    verifier = subprocess.run(
        [sys.executable, str(ROOT/'scripts'/'verify_certificates.py'), str(ROOT/'web'/'catalogue.json')],
        capture_output=True, text=True, cwd=ROOT,
    )
    print(verifier.stdout, end='')
    if verifier.returncode:
        print(verifier.stderr, file=sys.stderr)
        raise SystemExit(verifier.returncode)
    ui_command = ['node', str(ROOT/'tests'/'test_explorer.cjs')]
    if args.hosted_data:
        ui_command.extend(['--hosted-data', str(args.hosted_data.resolve())])
    ui = subprocess.run(ui_command,
                        capture_output=True, text=True, cwd=ROOT)
    if ui.returncode:
        print(ui.stderr, file=sys.stderr)
        raise SystemExit(ui.returncode)
    web_report = json.loads(ui.stdout)
    data = json.loads((ROOT/'web'/'catalogue.json').read_text())
    fixtures = []
    for pair in data['pairs']:
        if pair.get('validation', {}).get('status') != 'matched':
            continue
        actual = intersection_components(*pair['input_pair'])
        expected = pair['validation']['expected_discriminants']
        observed = sorted(c['determinant'] for c in actual['components'])
        if observed != expected:
            raise AssertionError(pair['input_pair'])
        fixtures.append({
            'pair': pair['input_pair'], 'published_count': len(expected),
            'computed_count': actual['component_count'],
            'published_discriminants': expected, 'computed_discriminants': observed,
            'matched': True, 'reference': pair['validation']['reference'],
            'source': pair['validation']['url'],
        })
    def git_output(*args):
        if shutil.which('git') is None:
            return None
        completed = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)
        return completed.stdout.strip() if completed.returncode == 0 else None

    git_head, git_status = git_output('rev-parse', 'HEAD'), git_output('status', '--porcelain')
    report = {
        'release': '1.1.0', 'reference_date': '2026-11-13', 'passed': True,
        'validated_at': datetime.now(timezone.utc).isoformat(),
        'source': {'commit': git_head,
                   'working_tree_dirty': bool(git_status) if git_status is not None else None,
                   'sha256': source_hashes(ROOT)},
        'runtime': {'python': platform.python_version(), 'implementation': platform.python_implementation()},
        'python_tests': {'passed': True, 'test_methods': run.testsRun, 'failures': len(run.failures),
                         'errors': len(run.errors), 'log': stream.getvalue()},
        'published_fixtures': fixtures,
        'catalogue': {'divisors': len(data['discriminants']), 'pairs': len(data['pairs']),
                      'component_records': sum(len(p['components']) for p in data['pairs']),
                      'construction_origins': sum(len(c['origins']) for p in data['pairs'] for c in p['components'])},
        'independent_verifier': {'passed': True, 'log': verifier.stdout,
                                  'scope': 'Integral certificate validation, using separate linear algebra and root enumeration. Completeness follows the documented algorithm and cited theorem, not certificates alone.'},
        'web_interaction_tests': web_report,
        'visual_browser_review': {'recorded_by_this_script': False,
                                   'reason': 'This automated script executes a DOM test double. An actual HTTPS browser review is separate.'},
        'limitations': ['No scheme-theoretic multiplicities.', 'No automatic rationality decision.',
                        'This script does not verify live browser layout, native clipboard, or actual network downloads.',
                        'This is regression-tested research software, not proof-assistant-verified code.'],
    }
    web_report['validated_at'] = report['validated_at']
    (args.output_dir/'web_validation.json').write_text(json.dumps(web_report, indent=2)+'\n', encoding='utf-8')
    out = args.output_dir/'validation.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f"PASS: {run.testsRun} Python tests, {web_report['checks']} UI assertions, {len(fixtures)} published fixtures.")
    print(f'Saved {out}.')


if __name__ == '__main__':
    main()
