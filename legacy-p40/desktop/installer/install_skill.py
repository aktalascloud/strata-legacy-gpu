"""Install the bundled global Ponytail skill only when no user copy exists."""
import argparse
import hashlib
from pathlib import Path

SKILL_SHA256 = 'f18008471528f0adde90a560d053f85935eed5cee26c447b7177ad24472bcf32'


def is_link(path):
    return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())


def install(root: Path):
    root = root.resolve(strict=True)
    source = root / 'defaults' / 'skills' / 'ponytail' / 'SKILL.md'
    if not source.is_file() or is_link(source):
        raise ValueError('Встроенный навык Ponytail отсутствует.')
    content = source.read_bytes()
    if hashlib.sha256(content).hexdigest() != SKILL_SHA256:
        raise ValueError('Встроенный навык Ponytail не прошёл проверку SHA-256.')
    parent = root
    for name in ('home', 'data', 'skills'):
        parent = parent / name
        try:
            parent.mkdir()
        except FileExistsError:
            if is_link(parent) or not parent.is_dir():
                raise ValueError('Папка пользовательских навыков недоступна или является ссылкой.')
    target = parent / 'ponytail'
    try:
        target.mkdir()
    except FileExistsError:
        return 'retained'
    try:
        with (target / 'SKILL.md').open('xb') as output:
            output.write(content)
    except Exception:
        try:
            target.rmdir()  # Only the empty folder created above can be removed.
        except OSError:
            pass
        raise
    return 'installed'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = install(args.root)
    except (OSError, ValueError) as error:
        print(f'Не удалось подготовить навык Ponytail: {error}')
        return 1
    print('Навык Ponytail добавлен глобально.' if result == 'installed' else 'Существующий навык Ponytail сохранён без изменений.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
