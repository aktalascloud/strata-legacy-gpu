"""Run upstream Strata locally with an instance-scoped graceful stop file."""

import _thread
import json
import msvcrt
import os
from pathlib import Path
import sys
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
SOURCE = ROOT / "src"


def stop_when_requested(instance_id):
    request = RUNTIME / f"stop-{instance_id}"
    while not request.is_file():
        time.sleep(0.5)
    request.unlink()
    _thread.interrupt_main()


def lifecycle(kind, payload):
    if kind == "ready":
        threading.Thread(target=stop_when_requested, args=(payload["instance_id"],), daemon=True).start()


def load_server():
    os.chdir(SOURCE)
    sys.path.insert(0, str(SOURCE))
    from serve import server
    return server


def run():
    with (RUNTIME / "server.lock").open("a+b") as lock:
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            print("Strata is already running from this installation.", file=sys.stderr)
            return 1

        server = load_server()
        config = RUNTIME / "strata.json"
        settings = json.loads(config.read_text(encoding="utf-8-sig"))
        if settings.get("host") != "127.0.0.1":
            raise ValueError("This profile serves only on 127.0.0.1")
        return server.main(["--engine", "strata", "--config", str(config),
                            "--host", settings["host"], "--port", str(settings["port"]),
                            "--ready-file", str(RUNTIME / "ready.json"),
                            "--offline", "--shutdown-timeout", "300"], lifecycle_event=lifecycle)


if __name__ == "__main__":
    if sys.argv[1:] == ["--check-import"]:
        print(load_server().__file__)
        sys.exit(0)
    sys.exit(run())
