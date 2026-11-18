"""Reject model weights, personal state and supplied private path prefixes in a release payload."""
import argparse
from pathlib import Path

FORBIDDEN_NAMES = {'dense.bin', 'experts.bin', 'expert-profile.bin', 'ready.json', 'native-jobs.json', 'state.json', 'app-settings.json', 'models-directory.txt', '.env'}
FORBIDDEN_SUFFIXES = {'.gguf', '.safetensors', '.ckpt', '.pth', '.pt', '.pdb', '.log', '.pyc'}


def scan(root, private_prefixes):
    needles = [variant.encode(encoding).lower() for prefix in private_prefixes for variant in {prefix, prefix.replace('\\', '/')} if prefix for encoding in ('utf-8', 'utf-16le')]
    maximum = max(map(len, needles), default=1)
    failures = []
    for path in root.rglob('*'):
        if path.is_symlink():
            failures.append((str(path.relative_to(root)), 'link'))
            continue
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        if path.name.lower() in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            failures.append((rel, 'model, state, debug or log'))
            continue
        with path.open('rb') as handle:
            tail = b''
            for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                data = (tail + chunk).lower()
                if any(needle in data for needle in needles):
                    failures.append((rel, 'private path'))
                    break
                tail = data[-maximum:]
    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('--private-prefix', action='append', required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    failures = scan(root, args.private_prefix)
    for path, reason in failures:
        print(f'{reason}: {path}')
    if failures:
        raise SystemExit(1)
    print('Payload privacy scan passed; model weights and private prefixes were not found.')


if __name__ == '__main__':
    main()
