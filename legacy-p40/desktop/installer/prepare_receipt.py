"""Create or verify the relocation-specific receipt without reading model files."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def receipt(root, integrity, fresh=False):
    def entries(section):
        return [record(root, item, fresh) for item in integrity[section]]
    return {'version': integrity['version'], 'build_id': integrity['build_id'],
            'files': entries('components'), 'external_files': entries('external')}


def record(root, item, fresh=False):
    path = root / item['path']
    if item.get('source') == 'windows-vc-runtime':
        system = Path(os.environ['WINDIR']) / 'System32' / path.name
        if path.parent != root / 'vision' or path.name.lower() not in {
            'msvcp140_atomic_wait.dll', 'msvcp140.dll', 'vcomp140.dll', 'vcruntime140_1.dll', 'vcruntime140.dll'
        }:
            raise ValueError('Unexpected reference to a system runtime file.')
        # Setup validates Microsoft's x64 copies. Subsequent launches pin the installed
        # local copies even if Windows services the system runtime to a new version.
        digest = sha256(path)
        if fresh and digest != sha256(system):
            raise ValueError(f'Installed VC runtime copy differs from System32: {path.name}')
        return {'path': str(path), 'sha256': digest}
    return {'path': str(path), 'sha256': item['sha256']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--integrity-sha256', required=True)
    parser.add_argument('--create', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    integrity_path = root / 'bundle-integrity.json'
    if sha256(integrity_path) != args.integrity_sha256.lower():
        raise SystemExit('The installer integrity manifest changed.')
    integrity = json.loads(integrity_path.read_text(encoding='utf-8'))
    expected = (json.dumps(receipt(root, integrity, fresh=args.create), ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')
    path = root / 'dll-receipt.json'
    if args.create:
        if path.exists():
            raise SystemExit('An existing receipt is retained.')
        with path.open('xb') as stream:
            stream.write(expected)
    if path.read_bytes() != expected:
        raise SystemExit('The installed DLL receipt does not match the package.')
    print(hashlib.sha256(expected).hexdigest())


if __name__ == '__main__':
    main()
