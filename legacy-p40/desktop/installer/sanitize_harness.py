"""Remove private build paths only from JavaScript region comments in a staging copy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sanitize(root: Path, prefixes: list[str]):
    needles = tuple(value.lower() for prefix in prefixes for value in (prefix, prefix.replace('\\', '/'), prefix.replace('\\', '\\\\')) if prefix)
    if not needles:
        raise ValueError('At least one private prefix is required.')
    pending = []
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('The staging tree contains a symbolic link.')
        if not path.is_file() or path.suffix.lower() not in {'.js', '.mjs'}:
            continue
        before = path.read_bytes()
        text = before.decode('utf-8')
        output, changed = [], 0
        for line in text.splitlines(keepends=True):
            if any(needle in line.lower() for needle in needles):
                match = re.fullmatch(r'([ \t]*//\s*#region)\b[^\r\n]*(\r?\n|\r)?', line)
                if not match:
                    raise ValueError(f'Private path outside a region comment: {path.relative_to(root)}')
                line = match.group(1) + ' [build path removed]' + (match.group(2) or '')
                changed += 1
            output.append(line)
        if changed:
            after = ''.join(output).encode('utf-8')
            if any(needle.encode('utf-8') in after.lower() for needle in needles):
                raise ValueError(f'A private path remains in {path.relative_to(root)}')
            pending.append((path, before, after, changed))
    records = []
    for path, before, after, changed in pending:
        fd, tmp = tempfile.mkstemp(prefix='.sanitize-', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as output:
                output.write(after)
            os.replace(tmp, path)
        finally:
            Path(tmp).unlink(missing_ok=True)
        records.append({'file': str(path.relative_to(root)).replace('\\', '/'),
                        'before_sha256': sha(before), 'after_sha256': sha(after), 'comments': changed})
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', required=True, type=Path)
    parser.add_argument('--private-prefix', action='append', required=True)
    args = parser.parse_args()
    stage = args.stage.resolve(strict=True)
    if (args.stage.is_symlink() or not re.fullmatch(r'payload(?:-[a-zA-Z0-9_-]+)?', stage.name)
            or not (stage / 'bundle-integrity.json').is_file()):
        raise SystemExit('Select an assembled payload staging directory.')
    root = stage / 'app' / 'harness'
    if root.is_symlink() or not root.is_dir():
        raise SystemExit('The staging Harness directory is invalid.')
    report = stage / 'licenses' / 'harness-sanitization.json'
    if report.exists() or report.is_symlink():
        raise SystemExit('This payload already has a sanitation receipt.')
    records = sanitize(root, args.private_prefix)
    with report.open('x', encoding='utf-8') as output:
        json.dump({'schema': 1, 'changes': records}, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print(f'Sanitized region comments in {len(records)} staged files.')


if __name__ == '__main__':
    main()
