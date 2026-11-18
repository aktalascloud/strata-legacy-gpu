"""Prepare a user-supplied Swift IQ3_S model for the local Desktop installation.

No model is included in the installer. An already prepared Q2 MTP directory can
be selected separately; when it is absent this creates a profile without MTP.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


MODEL_ID = "swift-1.5-iq3-s"
MIN_FREE = 8 * 1024**3
MTP_EXPERT_BYTES = 512 * 3 * (2560 * 640 * 18 // 64)
MTP_FILES = ("dense.bin", "dense.txt", "experts.bin", "draft_vocab.bin")
GENERATOR_SHA256 = '39e522a03b8c95dd82bd87a0f03cd91ae660257d83ba0115a7a9a8ac297ec807'
UNIFORM_SHA256 = 'b3e62120218cd96d175a0547530158869177dd2164b22b40f32bea7d7e85fb8c'


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def regular_file(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def model_shards(folder: Path) -> tuple[Path, Path]:
    if not folder.is_dir():
        raise ValueError("Выберите существующую папку с файлами Swift IQ3_S GGUF.")
    first = [p for p in folder.iterdir() if p.is_file() and p.name.lower().endswith("-00001-of-00002.gguf")
             and "swift" in p.name.lower() and "iq3_s" in p.name.lower()]
    if len(first) != 1:
        raise ValueError("Папка должна содержать ровно одну первую часть Swift IQ3_S.")
    second = first[0].with_name(first[0].name[:-len("-00001-of-00002.gguf")] + "-00002-of-00002.gguf")
    if not regular_file(first[0]) or not regular_file(second):
        raise ValueError("Требуются обе непустые части Swift IQ3_S GGUF.")
    return first[0].resolve(strict=True), second.resolve(strict=True)


def reviewed_component(root: Path) -> Path:
    base = root / "components" / "engine"
    found = []
    for manifest in base.glob("*/engine-component.json"):
        if manifest.is_symlink() or not manifest.is_file():
            continue
        try:
            obj = json.loads(manifest.read_text(encoding="utf-8-sig"))
            if (obj.get("id") != "strata-engine" or obj.get("backend") != "cuda"
                    or obj.get("platform") != "windows-x86_64" or "sm_61" not in obj.get("archs", [])
                    or obj.get("entrypoint") != "strata.exe"):
                continue
            listed = obj.get("files")
            if not isinstance(listed, list) or {r.get("path") for r in listed} != {"strata.exe", "strata_kq.dll", "strata-vision.exe"} or len(listed) != 3:
                continue
            if any(not regular_file(manifest.parent / r["path"]) or (manifest.parent / r["path"]).is_symlink()
                   or (manifest.parent / r["path"]).stat().st_size != r.get("bytes")
                   or file_hash(manifest.parent / r["path"]) != r.get("sha256", "").lower() for r in listed):
                continue
            found.append(manifest.parent.resolve(strict=True))
        except (OSError, ValueError, TypeError, KeyError):
            continue
    if len(found) != 1:
        raise ValueError("Требуется ровно один целый компонент движка CUDA sm_61.")
    return found[0]


def validate_mtp(folder: Path | None) -> Path | None:
    if folder is None:
        return None
    folder = folder.resolve(strict=True)
    if not folder.is_dir() or any(not regular_file(folder / name) for name in MTP_FILES):
        raise ValueError("Папка MTP должна содержать dense.bin, dense.txt, experts.bin и draft_vocab.bin.")
    if (folder / "experts.bin").stat().st_size != MTP_EXPERT_BYTES or (folder / "draft_vocab.bin").stat().st_size % 4:
        raise ValueError("Выбранная папка не является подготовленным набором Q2 MTP.")
    return folder


def validate_pack(folder: Path) -> None:
    for name in ("dense.bin", "index.txt", "native_experts.txt", "tokenizer/chat_template.jinja",
                 "tokenizer/vocab.json", "tokenizer/merges.txt", "tokenizer/token_type.json"):
        if not regular_file(folder / name):
            raise ValueError(f"Подготовленный набор модели неполный: {name}")


def prepare_pack(root: Path, first_shard: Path, destination: Path) -> None:
    script = root / "app" / "control" / "tools" / "iq_pack.py"
    if not regular_file(script):
        raise ValueError("Отсутствует встроенный инструмент подготовки модели.")
    subprocess.run([sys.executable, "-B", str(script), "--gguf", str(first_shard), "--out", str(destination)],
                   cwd=str(root / "app" / "control"), check=True)


def publish_file_exclusive(path: Path, content: bytes) -> None:
    # A hard link publishes a fully written file and fails if a config appeared meanwhile.
    fd, temporary = tempfile.mkstemp(prefix=".profile-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def uniform_profile(root: Path, destination: Path) -> None:
    tool = root / 'tools' / 'make_profile.py'
    if not regular_file(tool) or tool.is_symlink() or file_hash(tool) != GENERATOR_SHA256:
        raise ValueError('Инструмент создания равномерного профиля отсутствует или изменён.')
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() or not regular_file(destination) or file_hash(destination) != UNIFORM_SHA256:
            raise FileExistsError(f'Существующий профиль экспертов сохранён: {destination}')
        return
    with tempfile.TemporaryDirectory(prefix='.uniform-profile-', dir=destination.parent) as temporary:
        generated = Path(temporary) / 'profile.bin'
        subprocess.run([sys.executable, '-B', str(tool), '--no-base', '--out', str(generated)], check=True)
        if file_hash(generated) != UNIFORM_SHA256:
            raise ValueError('Созданный равномерный профиль не прошёл проверку SHA-256.')
        publish_file_exclusive(destination, generated.read_bytes())


def configure(install_root: Path, model_dir: Path, mtp_dir: Path | None = None, *,
              build_pack=prepare_pack, disk_free=lambda p: shutil.disk_usage(p).free,
              hash_file=file_hash) -> dict:
    root = install_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Корень установки должен быть существующей папкой.")
    model_dir = model_dir.resolve(strict=True)
    shards = model_shards(model_dir)
    mtp = validate_mtp(mtp_dir)
    component = reviewed_component(root)
    control = root / "app" / "control"
    expert_profile = root / 'install' / 'uniform-expert-profile.bin'
    if not (root / "cuda").is_dir() or not (root / "vision").is_dir():
        raise ValueError("Отсутствуют папки системных DLL.")

    config_dir, data_dir = root / "install", root / "models"
    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    config = config_dir / f"strata-{MODEL_ID}.json"
    pack = data_dir / "swift-iq3_s"
    location = config_dir / 'models-directory.txt'
    chosen_path = str(model_dir) + '\n'
    if config.exists() or config.is_symlink():
        raise FileExistsError(f"Существующий профиль сохранён: {config}")
    if location.exists() or location.is_symlink():
        if location.is_symlink() or location.read_text(encoding='utf-8') != chosen_path:
            raise FileExistsError(f'Существующий путь моделей сохранён: {location}')
    required = max(MIN_FREE, (sum(p.stat().st_size for p in shards) + 9) // 10)
    if disk_free(data_dir) < required:
        raise OSError(f"Недостаточно места: требуется не менее {required} свободных байт.")

    lock_path = config_dir / ".swift-configure.lock"
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RuntimeError("Подготовка модели уже выполняется либо требуется проверить файл блокировки.") from exc
    try:
        os.close(lock_fd)
        if config.exists() or config.is_symlink():
            raise FileExistsError(f"Существующий профиль сохранён: {config}")
        print("Проверяются части модели. Это может занять несколько минут.", flush=True)
        identities = [{"path": str(p), "bytes": p.stat().st_size, "mtime_ns": p.stat().st_mtime_ns,
                       "sha256": hash_file(p)} for p in shards]
        if pack.exists() or pack.is_symlink():
            marker = pack / "local-swift-source.json"
            if pack.is_symlink() or not marker.is_file() or json.loads(marker.read_text(encoding="utf-8")) != identities:
                raise FileExistsError(f"Существующий набор сохранён: источник не совпадает: {pack}")
            validate_pack(pack)
        else:
            with tempfile.TemporaryDirectory(prefix=".swift-pack-", dir=data_dir) as temporary:
                prepared = Path(temporary) / "pack"
                print("Подготавливается локальный набор. Исходные файлы модели не изменяются.", flush=True)
                build_pack(root, shards[0], prepared)
                validate_pack(prepared)
                for p, identity in zip(shards, identities):
                    st = p.stat()
                    if st.st_size != identity["bytes"] or st.st_mtime_ns != identity["mtime_ns"]:
                        raise RuntimeError("Выбранная модель изменилась во время подготовки.")
                (prepared / "local-swift-source.json").write_text(json.dumps(identities, ensure_ascii=False), encoding="utf-8")
                if pack.exists() or pack.is_symlink():
                    raise FileExistsError(f"Существующий набор сохранён: {pack}")
                prepared.rename(pack)

        uniform_profile(root, expert_profile)
        args = ["--pack", str(pack), "--native", str(shards[0]), "--ple-gguf", str(shards[0]),
                "--expert-profile", str(expert_profile), "--expert-cache", "auto", "--max-context", "262144",
                "--kv", "q4_0", "--kv-resident", "20480", "--kv-grow", "--pool-workers", "14"]
        if mtp:
            args += ["--spec", "3", "--spec-min-p", "0.5"]
        args += ["--prompt-cache", "6", "--prompt-cache-every", "16384", "--prompt-cache-root", "2048",
                 "--ple-io", "ram", "--pool-tasks", "0"]
        if mtp:
            args += ["--mtp", str(mtp), "--suffix-draft", "3"]
        args += ["--lookup-chain", "0", "--pcie-frac", "1", "--prefill", "1536",
                 "--vram-reserve-mib", "210", "--adapt-async", "0", "--prompt-cache-tail"]
        profile = {"host": "127.0.0.1", "port": 8093, "api_key": "none", "engine_ready_s": 1200,
                   "exe": "component:strata-engine", "cwd": str(control), "log": str(root / "engine.log"),
                   "backend": "cuda", "lib_dirs": [str(root / "cuda"), str(root / "vision")],
                   "args": args, "user_args": list(args), "tokenizer": str(pack / "tokenizer"),
                   "model_name": MODEL_ID, "api_model_id": MODEL_ID, "reasoning_effort": "high",
                   "parallel": 1, "ui_resource_profile": "performance", "mtp": mtp is not None,
                   "env": {"STRATA_ROUTE_PRIOR": "0", "OMP_PROC_BIND": "FALSE", "STRATA_ARENA_RAM_FALLBACK": "0",
                           "STRATA_ROUTE_TAIL_SKIP": "0", "STRATA_ADAPT_FETCH": "2", "STRATA_DENSE_F32": "1"},
                   "sampling": {"top_k": 20, "min_p": 0.0, "repetition_penalty": 1.0, "frequency_penalty": 0.0}}
        projector = model_dir / "mmproj-Qwen3.8-Flash-Next-BF16.gguf"
        if regular_file(projector):
            profile["vision"] = {"mmproj": str(projector.resolve(strict=True)), "gpu": False,
                                 "exe": str(component / "strata-vision.exe"), "threads": 16,
                                 "model": str(shards[0]), "max_tokens": 300, "require_ram": True}
        if location.exists() or location.is_symlink():
            if location.is_symlink() or location.read_text(encoding='utf-8') != chosen_path:
                raise FileExistsError(f'Существующий путь моделей сохранён: {location}')
        else:
            publish_file_exclusive(location, chosen_path.encode('utf-8'))
        prefs = root / 'shell-prefs.json'
        if not prefs.exists() and not prefs.is_symlink():
            publish_file_exclusive(prefs, b'{"port":0,"tray":true,"language":"ru"}\n')
        publish_file_exclusive(config, (json.dumps(profile, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        return {"ok": True, "profile": str(config), "mtp": "q2" if mtp else "off",
                "vision": "cpu-16" if "vision" in profile else "off",
                "mtp_validation": "structure-only" if mtp else "not-selected",
                "expert_profile": "uniform-no-traces; measured on the original hardware; other hardware unverified"}
    finally:
        lock_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-root", required=True, type=Path)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--mtp-dir", type=Path)
    args = parser.parse_args()
    try:
        result = configure(args.install_root, args.model_dir, args.mtp_dir)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Не удалось подготовить модель: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    if result["mtp"] == "off":
        print("MTP выключен: подготовленная папка Q2 не выбрана.")
    if result["vision"] == "off":
        print("Распознавание изображений выключено: файл mmproj не найден.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
