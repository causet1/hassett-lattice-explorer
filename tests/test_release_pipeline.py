"""Exercise actual release commands, including interruption and corrupt assets."""

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from download_catalogue import download, validate_index
from release_support import source_hashes


def run(script, *args, expected=0):
    result = subprocess.run([sys.executable, str(ROOT/'scripts'/script), *map(str, args)],
                            cwd=ROOT, capture_output=True, text=True)
    if result.returncode != expected:
        raise AssertionError(f'{script}: expected exit {expected}, got {result.returncode}\n'
                             f'{result.stdout}\n{result.stderr}')
    return result


class ReleasePipelineTests(unittest.TestCase):
    def test_resume_verify_package_build_and_reject_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data, out = root/'data', root/'out'
            args = ('--max-discriminant', 44, '--gzip', '--output', data)
            run('expand_catalogue.py', *args, '--stop-after', 2, expected=1)
            partial = json.loads((data/'catalogue-index.json').read_bytes())
            self.assertFalse(partial['complete'])
            self.assertEqual(partial['pair_count'], 2)
            run('verify_catalogue.py', data/'catalogue-index.json', expected=1)
            run('expand_catalogue.py', *args)
            state = json.loads((data/'run-state.json').read_bytes())
            self.assertEqual(state['reused_this_run'], 2)
            report = root/'verification.json'
            run('verify_catalogue.py', data/'catalogue-index.json', '--report', report)
            run('package_catalogue.py', data/'catalogue-index.json', '--verification', report, '--output', out)
            archive = out/'hassett-catalogue-44.zip'
            original_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
            run('package_catalogue.py', data/'catalogue-index.json', '--verification', report, '--output', out)
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), original_hash)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(len([n for n in z.namelist() if '/pairs/' in n]), 78)
            run('build_hosted_site.py', data, '--verification', report, '--output', root/'site')
            self.assertEqual((root/'site/index.html').read_bytes(), (ROOT/'web/explorer.html').read_bytes())
            if shutil.which('node'):
                ui = subprocess.run(['node', str(ROOT/'tests/test_explorer.cjs'), '--hosted-data', str(data)],
                                    cwd=ROOT, capture_output=True, text=True, check=True)
                self.assertTrue(json.loads(ui.stdout)['real_hosted_data']['complete'])
            row = json.loads((data/'catalogue-index.json').read_bytes())['pairs'][0]
            shard = data/row['path']
            shard.write_bytes(shard.read_bytes()+b'corruption')
            run('verify_catalogue.py', data/'catalogue-index.json', expected=1)
            run('package_catalogue.py', data/'catalogue-index.json', '--verification', report,
                '--output', out, expected=1)
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), original_hash)
            run('build_hosted_site.py', data, '--verification', report,
                '--output', root/'bad-site', expected=1)
            self.assertFalse((root/'bad-site/index.html').exists())
            run('expand_catalogue.py', *args)
            state = json.loads((data/'run-state.json').read_bytes())
            self.assertEqual(state['invalid_existing_files'], 1)
            run('verify_catalogue.py', data/'catalogue-index.json')

    def test_source_archive_resolves_readme_links_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            run('package_release.py', '--output', tmp)
            with zipfile.ZipFile(Path(tmp)/'hassett-lattice-explorer.zip') as z:
                prefix = 'hassett-lattice-explorer/'
                names = set(z.namelist())
                readme = z.read(prefix+'README.md').decode()
                for target in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', readme):
                    if '://' not in target:
                        self.assertTrue(prefix+target in names or any(n.startswith(prefix+target.rstrip('/')+'/') for n in names), target)
                manifest = json.loads(z.read(prefix+'release-manifest.json'))
                for entry in manifest['files']:
                    payload = z.read(prefix+entry['path'])
                    self.assertEqual(len(payload), entry['bytes'])
                    self.assertEqual(hashlib.sha256(payload).hexdigest(), entry['sha256'])
                self.assertIn(prefix+'references/problem-statement.png', names)
                self.assertFalse(any('/build/' in n or '/.git/' in n for n in names))

    def test_pinned_download_resume_and_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root/'source'
            run('expand_catalogue.py', '--max-discriminant', 14, '--gzip', '--output', data)
            raw = (data/'catalogue-index.json').read_bytes()
            pin = hashlib.sha256(raw).hexdigest()
            index = json.loads(raw)
            calls = []

            def fetch(url, limit, timeout):
                relative = url.split('/data/', 1)[1]
                calls.append(relative)
                return (data/relative).read_bytes()

            with patch('download_catalogue.fetch', side_effect=fetch):
                with self.assertRaisesRegex(ValueError, 'SHA-256'):
                    download(root/'wrong', expected_hash='0'*64)
                self.assertFalse((root/'wrong').exists())
                first = download(root/'target', expected_hash=pin)
                self.assertEqual(first['downloaded'], 3)
                calls.clear()
                second = download(root/'target', expected_hash=pin)
                self.assertEqual(second['reused'], 3)
                self.assertEqual(calls, ['catalogue-index.json'])
                path = root/'target'/index['pairs'][0]['path']
                path.write_bytes(b'corrupt')
                self.assertEqual(download(root/'target', expected_hash=pin)['downloaded'], 1)
            unsafe = json.loads(raw)
            unsafe['pairs'][0]['path'] = '../escape.json'
            unsafe_raw = json.dumps(unsafe).encode()
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                validate_index(unsafe_raw, hashlib.sha256(unsafe_raw).hexdigest())
            with patch('download_catalogue.fetch', side_effect=lambda url, limit, timeout: raw if url.endswith('catalogue-index.json') else b'bad'):
                with self.assertRaisesRegex(ValueError, 'mismatch'):
                    download(root/'failed', expected_hash=pin)
                self.assertFalse((root/'failed/catalogue-index.json').exists())

    def test_source_packaging_rejects_stale_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports, out = root/'reports', root/'out'
            reports.mkdir()
            report = {'passed': True, 'source': {'sha256': source_hashes(ROOT)}}
            path = reports/'validation.json'
            path.write_text(json.dumps(report))
            run('package_release.py', '--output', out, '--validation-dir', reports)
            archive = out/'hassett-lattice-explorer.zip'
            original = archive.read_bytes()
            with zipfile.ZipFile(archive) as z:
                self.assertIn('hassett-lattice-explorer/validation/validation.json', z.namelist())
            # A modified or newly unrecorded source cannot inherit old evidence.
            for mutation in ('digest', 'missing'):
                changed = json.loads(json.dumps(report))
                if mutation == 'digest':
                    changed['source']['sha256']['hassett_lattices/core.py'] = '0'*64
                else:
                    changed['source']['sha256'].pop('hassett_lattices/core.py')
                path.write_text(json.dumps(changed))
                run('package_release.py', '--output', out, '--validation-dir', reports, expected=1)
                self.assertEqual(archive.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
