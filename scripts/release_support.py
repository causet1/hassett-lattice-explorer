"""Shared source fingerprint for fresh validation and release packaging."""

import hashlib


def source_hashes(root):
    paths = [root/'pyproject.toml', root/'MANIFEST.in']
    for directory in ('hassett_lattices', 'scripts', 'tests', 'web', '.github/workflows'):
        paths.extend(path for path in (root/directory).rglob('*')
                     if path.is_file() and path.suffix in ('.py', '.cjs', '.html', '.json', '.yml', '.yaml')
                     and not path.relative_to(root).parts[:2] == ('web', 'data'))
    paths.extend(path for path in (root/'julia').rglob('*')
                 if path.is_file() and path.suffix in ('.jl', '.toml', '.md')
                 and path.name != 'Manifest.toml'
                 and 'build' not in path.relative_to(root).parts)
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}
