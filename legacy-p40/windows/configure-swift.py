"""Prepare a local Swift IQ3_S model directory for the Pascal build."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
SOURCE = ROOT / "src"
FIRST_SHARD = "Swift-Qwen3.8-Flash-Next-GSQ-RCO-abliterated-IQ3_S-00001-of-00002.gguf"


def configure(models, mtp):
    config = RUNTIME / "strata.json"
    if config.exists():
        raise SystemExit(f"Existing profile retained: {config}")
    model = models / FIRST_SHARD
    second = models / FIRST_SHARD.replace("00001", "00002", 1)
    if not model.is_file() or not second.is_file():
        raise SystemExit(f"Swift IQ3_S needs both GGUF shards in {models}.")
    if mtp and not all((mtp / file).is_file() for file in ("dense.bin", "dense.txt", "experts.bin", "draft_vocab.bin")):
        raise SystemExit("MTP directory needs dense.bin, dense.txt, experts.bin and draft_vocab.bin.")

    data = RUNTIME / "models"
    data.mkdir(exist_ok=True)
    pack = data / "swift-iq3_s"
    fingerprint = [{"path": str(shard), "size": shard.stat().st_size, "mtime_ns": shard.stat().st_mtime_ns}
                   for shard in (model, second)]
    if pack.exists():
        marker = pack / "local-swift-source.json"
        if not marker.is_file() or json.loads(marker.read_text(encoding="utf-8")) != fingerprint:
            raise SystemExit(f"Existing pack retained: {pack}")
        check_pack(pack)
    else:
        with tempfile.TemporaryDirectory(prefix="swift-pack-", dir=data) as directory:
            prepared = Path(directory) / "pack"
            subprocess.run([sys.executable, "-B", str(SOURCE / "tools/iq_pack.py"),
                            "--gguf", str(model), "--out", str(prepared)], cwd=SOURCE, check=True)
            check_pack(prepared)
            (prepared / "local-swift-source.json").write_text(json.dumps(fingerprint), encoding="utf-8")
            prepared.rename(pack)

    args = ["--pack", str(pack), "--native", str(model), "--ple-gguf", str(model),
            "--expert-profile", str(SOURCE / "data/expert-profile.bin"), "--expert-cache", "auto",
            "--max-context", "262144", "--kv", "q4_0", "--kv-resident", "20480", "--prefill", "1024",
            "--pool-workers", "14", "--prompt-cache", "6", "--prompt-cache-every", "16384", "--prompt-cache-tail",
            "--prompt-cache-root", "2048", "--vram-reserve-mib", "210", "--ple-io", "ram",
            "--adapt-async", "0", "--pcie-frac", "1"]
    if mtp:
        args += ["--mtp", str(mtp), "--spec", "3", "--spec-min-p", "0.5", "--suffix-draft", "3", "--lookup-chain", "0"]
    profile = dict(host="127.0.0.1", port=8093, engine_ready_s=1200, backend="cuda",
                   exe=str(RUNTIME / "engine/strata.exe"), cwd=str(SOURCE), log=str(RUNTIME / "engine.log"),
                   tokenizer=str(pack / "tokenizer"), model_name="swift-1.5-iq3-s", reasoning_effort="high",
                   mtp=bool(mtp), args=args, env={"STRATA_ARENA_RAM_FALLBACK": "0", "STRATA_ROUTE_PRIOR": "0",
                                                  "STRATA_ROUTE_TAIL_SKIP": "0", "STRATA_ADAPT_FETCH": "2",
                                                  "STRATA_DENSE_F32": "1",
                                                  "OMP_PROC_BIND": "FALSE"},
                   sampling=dict(top_k=20, min_p=0.0, repetition_penalty=1.0, frequency_penalty=0.0))
    projector = models / "mmproj-Qwen3.8-Flash-Next-BF16.gguf"
    if projector.is_file():
        profile["vision"] = dict(exe=str(RUNTIME / "vision/strata-vision.exe"), model=str(model),
                                 mmproj=str(projector), gpu=False, threads=8, max_tokens=300, require_ram=True)
    with tempfile.TemporaryDirectory(prefix="swift-config-", dir=RUNTIME) as directory:
        prepared = Path(directory) / config.name
        prepared.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        prepared.rename(config)
    print(f"Configured {profile['model_name']}. Run START.cmd.")


def check_pack(pack):
    for file in ("dense.bin", "index.txt", "native_experts.txt", "tokenizer/chat_template.jinja"):
        if not (pack / file).is_file() or not (pack / file).stat().st_size:
            raise RuntimeError(f"Incomplete Swift pack: {file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", type=Path, help="directory containing both Swift IQ3_S GGUF shards")
    parser.add_argument("--mtp-dir", type=Path, help="optional directory containing the prepared Q2 MTP pack")
    args = parser.parse_args()
    configure(args.models.resolve(strict=True), args.mtp_dir.resolve(strict=True) if args.mtp_dir else None)
