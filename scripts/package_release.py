#!/usr/bin/env python3
"""Package the complete source release and the two standalone deliverables."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
from release_support import source_hashes

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT.parent/'deliverables')
    parser.add_argument('--validation-dir', type=Path,
                        help='Include fresh JSON reports after checking their source fingerprints')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    must_exist = [ROOT/'docs'/'mathematics.pdf', ROOT/'docs'/'validation.json', ROOT/'web'/'explorer.html']
    for path in must_exist:
        if not path.is_file():
            raise FileNotFoundError(f'Required validated artifact missing: {path.name}')
    allowed_roots = {'hassett_lattices', 'julia', 'macaulay2', 'tests', 'scripts', 'docs', 'web', 'references', '.github'}
    allowed_files = {'LICENSE', 'README.md', 'PROBLEM.md', 'ALGORITHM.md', 'WEBSITE.md',
                     'IMPORT-VERIFICATION.md', 'pyproject.toml', 'MANIFEST.in', 'CITATION.cff', '.gitignore'}
    excluded_suffixes = {'.pyc', '.pyo', '.log', '.aux', '.out', '.toc'}
    files = []
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if rel.parts[:2] == ('web', 'data'):
            continue
        if rel.parts[0] not in allowed_roots and str(rel) not in allowed_files:
            continue
        if any(part in {'__pycache__', 'tmp', '.pytest_cache', 'build'} for part in rel.parts):
            continue
        if path.name == 'Manifest.toml':
            continue
        if path.suffix in excluded_suffixes:
            continue
        files.append(path)
    reports = []
    if args.validation_dir:
        report = json.loads((args.validation_dir/'validation.json').read_bytes())
        hashes = report.get('source', {}).get('sha256', {})
        if report.get('passed') is not True or not hashes:
            raise ValueError('A passing current validation report with source hashes is required')
        if hashes != source_hashes(ROOT):
            raise ValueError('Source changed since validation; rerun scripts/validate_release.py')
        reports = sorted(args.validation_dir.glob('*.json'))
    manifest = {'release': '1.1.0', 'license': 'MIT',
                'license_scope': 'Implementation and original explanatory text. Supplied reference materials retain their existing terms; see references/README.md.',
                'files': []}
    archive = out/'hassett-lattice-explorer.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in files:
            rel = path.relative_to(ROOT).as_posix()
            blob = path.read_bytes()
            info = zipfile.ZipInfo('hassett-lattice-explorer/'+rel, date_time=(2026, 11, 13, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, blob)
            manifest['files'].append({'path': rel, 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()})
        for path in reports:
            rel = 'validation/'+path.name
            blob = path.read_bytes()
            info = zipfile.ZipInfo('hassett-lattice-explorer/'+rel, date_time=(2026, 11, 13, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, blob)
            manifest['files'].append({'path': rel, 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()})
        info = zipfile.ZipInfo('hassett-lattice-explorer/release-manifest.json', date_time=(2026, 11, 13, 12, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, json.dumps(manifest, indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('Archive integrity check failed')
    shutil.copyfile(ROOT/'web'/'explorer.html', out/'hassett-explorer.html')
    shutil.copyfile(ROOT/'docs'/'mathematics.pdf', out/'hassett-lattice-guide.pdf')
    names = ['hassett-lattice-explorer.zip', 'hassett-explorer.html', 'hassett-lattice-guide.pdf']
    lines = [hashlib.sha256((out/n).read_bytes()).hexdigest()+'  '+n for n in names]
    (out/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n')
    print(f'Packaged {len(files)} source/documentation/data files.')
    for name in names:
        print(f'{name}: {(out/name).stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
