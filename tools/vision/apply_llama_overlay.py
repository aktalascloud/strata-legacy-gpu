"""Apply only the checked CPU-vision dependency delta to a selected local source tree."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import tempfile


def digest(path):
    if not path.is_file():
        return None
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            value.update(block)
    return value.hexdigest()


def local(root, relative):
    parts = PurePosixPath(relative).parts
    if not parts or PurePosixPath(relative).is_absolute() or '\\' in relative or ':' in relative or '..' in parts:
        raise ValueError('invalid overlay path')
    path = root.joinpath(*parts)
    if not path.resolve().is_relative_to(root):
        raise ValueError('overlay path leaves the selected source tree')
    for current in [path, *path.parents]:
        if current == root:
            break
        if current.exists():
            info = current.lstat()
            if current.is_symlink() or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError('overlay source path contains a link or reparse point')
    return path


def apply(root, package, check_only=False):
    root = root.resolve(strict=True)
    package = package.resolve(strict=True)
    manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
    closure_path = package / 'used-inputs.json'
    if digest(closure_path) != manifest['used_input_manifest_sha256']:
        raise ValueError('used-input manifest changed')
    closure = json.loads(closure_path.read_text(encoding='utf-8'))['files']
    overlay = {entry['path']: entry for entry in manifest['overlay_files']}
    if len(overlay) != len(manifest['overlay_files']):
        raise ValueError('duplicate overlay target')
    expected = {entry['path']: entry['sha256'] for entry in closure}
    if len(expected) != len(closure):
        raise ValueError('duplicate compiled dependency input')
    if not overlay.keys() <= expected.keys():
        raise ValueError('overlay file absent from compiled input closure')
    pending = []
    # Check the entire actual-used dependency before changing any file. Mixed old/new
    # overlay files are valid after an interrupted application; unknown edits are not.
    for relative, final_sha in expected.items():
        target = local(root, relative)
        actual = digest(target)
        entry = overlay.get(relative)
        if entry is None:
            if actual != final_sha:
                raise ValueError('unrecognized compiled dependency input: ' + relative)
            continue
        source = local(package, 'overlay-files/' + relative)
        if digest(source) != entry['sha256'] or entry['sha256'] != final_sha:
            raise ValueError('immutable overlay payload changed: ' + relative)
        if actual == final_sha:
            continue
        if actual != entry['base_sha256']:
            raise ValueError('unrecognized dependency edit: ' + relative)
        pending.append((entry, source, target))
    if not check_only:
        for entry, source, target in pending:
            current = digest(target)
            if current == entry['sha256']:
                continue
            if current != entry['base_sha256']:
                raise ValueError('dependency changed during application: ' + entry['path'])
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=target.parent, prefix=target.name + '.strata-', delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(source.read_bytes())
                temporary.replace(target)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        for relative, final_sha in expected.items():
            if digest(local(root, relative)) != final_sha:
                raise ValueError('final compiled dependency input differs: ' + relative)
    return {'status': 'checked' if check_only else 'applied' if pending else 'already_applied',
            'checked_inputs': len(expected), 'overlay_files': len(overlay), 'pending_before': len(pending)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--llama-dir', required=True, type=Path)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    package = Path(__file__).resolve().parents[2] / 'third_party/llama-cpu-vision'
    print(json.dumps(apply(args.llama_dir, package, args.check_only)))


if __name__ == '__main__':
    main()
