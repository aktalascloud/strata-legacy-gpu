"""Check the extracted Windows package without loading or creating a model."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from prepare_receipt import record, sha256


def verify(root, integrity_sha256):
    root = root.resolve(strict=True)
    manifest = (root / 'bundle-integrity.json').read_bytes()
    if hashlib.sha256(manifest).hexdigest() != integrity_sha256.lower():
        raise ValueError('Bundle integrity manifest hash mismatch.')
    data = json.loads(manifest)
    records = data['components'] + data['external'] + [
        {'path': 'app/strata-desktop.exe', 'sha256': data['desktop_sha256']},
    ]
    for item in records:
        path = (root / item['path']).resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f'Invalid bundle file: {item["path"]}')
        if sha256(path) != record(root, item, fresh=True)['sha256']:
            raise ValueError(f'Bundle file hash mismatch: {item["path"]}')

    engine = next(root / item['path'] for item in data['components'] if Path(item['path']).name == 'strata.exe')
    control = root / 'app/control'
    node = root / 'app/node/node.exe'
    harness = root / 'app/harness'
    entry = json.loads((harness / 'BUNDLE.json').read_text(encoding='utf-8'))['entry']
    harness_entry = harness / entry
    if not harness_entry.is_file():
        harness_entry = harness / 'lib/bin.js'
    env = {**os.environ, 'PATH': os.pathsep.join(map(str, (root / 'cuda', root / 'vision', os.environ.get('PATH', ''))))}
    for command in ([engine, '--version'], [sys.executable, '-B', control / 'strata.py', '--help'],
                    [node, '--version'], [node, harness_entry, '--version']):
        output = subprocess.check_output(command, cwd=root, env=env, timeout=90)
        if not output.strip():
            raise ValueError(f'Version or help returned no output: {Path(command[0]).name}')
    print('Verified Desktop bundle, native engine, Python Control, Node and Harness.')


if __name__ == '__main__':
    verify(Path(sys.argv[1]), sys.argv[2])
