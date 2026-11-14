#!/usr/bin/env python3
"""Resume a checksum-pinned download of the published catalogue (standard library).

Transport integrity is checked here; run verify_catalogue.py afterwards for
mathematical verification. A complete index is installed only after every shard
has its expected bytes. Interrupted downloads retain verified shards for reuse.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from itertools import combinations
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = 'https://hassett-lattice-explorer.causetpatrick.chatgpt.site/data/'
DEFAULT_REPORT = ROOT/'docs'/'catalogue-verification-500.json'
MAX_BYTES = 20 * 1024 * 1024


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            name = stream.name
            stream.write(data)
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def fetch(url, limit, timeout):
    for attempt in range(3):
        try:
            request = Request(url, headers={'Accept-Encoding': 'identity',
                                            'User-Agent': 'HassettCatalogue/1.1'})
            with urlopen(request, timeout=timeout) as response:
                if urlsplit(response.url).scheme != 'https':
                    raise ValueError('Refusing an HTTPS downgrade')
                data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError(f'Response exceeds size limit: {url}')
            return data
        except (URLError, TimeoutError, ConnectionError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def validate_index(raw, expected_hash):
    if sha256(raw) != expected_hash:
        raise ValueError('Index SHA-256 differs from the pinned release; no index was installed')
    index = json.loads(raw)
    if (index.get('schema_version') != '1.1' or index.get('complete') is not True
            or index.get('failed_pair_count') != 0 or index.get('pending_pair_count') != 0
            or index.get('failures') != []):
        raise ValueError('Expected a complete schema 1.1 catalogue')
    bound = index['max_discriminant']
    if type(bound) is not int or not 8 <= bound <= 10000:
        raise ValueError('Unsupported catalogue bound')
    labels = [d for d in range(8, bound + 1) if d % 6 in (0, 2)]
    expected = set(combinations(labels, 2))
    rows = index['pairs']
    if (index['discriminants'] != labels or index['pair_count'] != len(expected)
            or index['expected_pair_count'] != len(expected) or len(rows) != len(expected)):
        raise ValueError('Catalogue coverage metadata is inconsistent')
    seen = set()
    for row in rows:
        pair = tuple(sorted((row['d1'], row['d2'])))
        if pair not in expected or pair in seen:
            raise ValueError('Unexpected or repeated label pair')
        seen.add(pair)
        key = f'{pair[0]}-{pair[1]}'
        compression = row.get('compression', 'none')
        path = f'pairs/{key}.json' + ('.gz' if compression == 'gzip' else '')
        if compression not in ('gzip', 'none') or row['path'] != path or row['key'] != key:
            raise ValueError(f'Unsafe or inconsistent shard path: {row["path"]}')
        for field in ('bytes', 'uncompressed_bytes'):
            if type(row[field]) is not int or not 0 < row[field] <= MAX_BYTES:
                raise ValueError(f'Invalid shard size: {path}')
        for field in ('sha256', 'uncompressed_sha256'):
            if not isinstance(row[field], str) or not re.fullmatch('[0-9a-f]{64}', row[field]):
                raise ValueError(f'Invalid shard checksum: {path}')
    return index


def download(output, *, expected_hash, base_url=DEFAULT_URL, workers=8, timeout=30,
             progress=None):
    parsed = urlsplit(base_url)
    if (parsed.scheme != 'https' or not parsed.netloc or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ValueError('The catalogue base URL must be HTTPS without credentials, query or fragment')
    if not re.fullmatch('[0-9a-f]{64}', expected_hash):
        raise ValueError('Expected a lowercase SHA-256 index digest')
    if not 1 <= workers <= 32 or timeout <= 0:
        raise ValueError('Use 1–32 workers and a positive timeout')
    base_url = base_url.rstrip('/') + '/'
    raw = fetch(base_url+'catalogue-index.json', MAX_BYTES, timeout)
    index = validate_index(raw, expected_hash)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    index_path = output/'catalogue-index.json'
    if index_path.exists() and index_path.read_bytes() != raw:
        raise ValueError('Output contains a different catalogue index; choose an empty directory')
    # Validate destinations before downloading; never follow a shard symlink out.
    for row in index['pairs']:
        path = output/row['path']
        if not path.resolve().is_relative_to(output) or path.is_symlink():
            raise ValueError(f'Unsafe local destination: {path}')

    def shard(row):
        path = output/row['path']
        if path.is_file() and path.stat().st_size == row['bytes']:
            if sha256(path.read_bytes()) == row['sha256']:
                return 'reused'
        data = fetch(base_url+row['path'], row['bytes'], timeout)
        if len(data) != row['bytes'] or sha256(data) != row['sha256']:
            raise ValueError(f'Shard checksum/size mismatch: {row["path"]}')
        atomic_write(path, data)
        return 'downloaded'

    counts = {'downloaded': 0, 'reused': 0}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(shard, row) for row in index['pairs']]
        try:
            for future in as_completed(futures):
                counts[future.result()] += 1
                if progress:
                    progress(sum(counts.values()), len(futures))
        except BaseException:
            for future in futures:
                future.cancel()
            raise
    atomic_write(index_path, raw)
    return {'index_sha256': expected_hash, 'pairs': len(index['pairs']), **counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT.parent/'hassett-expanded-500')
    parser.add_argument('--base-url', default=DEFAULT_URL)
    parser.add_argument('--verification', type=Path, default=DEFAULT_REPORT,
                        help='Trusted release report supplying the pinned index hash')
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--timeout', type=float, default=30)
    args = parser.parse_args()

    def progress(done, total):
        if done % 500 == 0 or done == total:
            print(f'Checked {done}/{total} downloads', flush=True)

    try:
        pin = json.loads(args.verification.read_bytes())
        if pin.get('passed') is not True:
            raise ValueError('The release verification report must have passed')
        result = download(args.output, expected_hash=pin['index_sha256'], base_url=args.base_url,
                          workers=args.workers, timeout=args.timeout, progress=progress)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Download failed: {exc}. Verified shards are retained for resumption.', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    print('Transport verified. Run scripts/verify_catalogue.py on the downloaded index for mathematical checks.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
