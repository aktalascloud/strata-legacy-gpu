"""Hold the legacy launcher's existing Windows byte lock until the host exits."""
import msvcrt
import json
import math
import os
import sys
import psutil

path = sys.argv[1]
if not os.path.isabs(path) or os.path.islink(path) or not os.path.isfile(path):
    sys.exit(1)
try:
    with open(path, 'r+b') as lock:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        ready = os.path.join(os.path.dirname(path), 'ready.json')
        if os.path.islink(ready):
            sys.exit(1)
        if os.path.exists(ready):
            if not os.path.isfile(ready) or os.path.getsize(ready) > 65536:
                sys.exit(1)
            with open(ready, encoding='utf-8-sig') as handle:
                state = json.load(handle)
            pid, created = state.get('pid'), state.get('created_at')
            if (type(pid) is not int or pid <= 0 or type(created) not in (int, float)
                    or not math.isfinite(created) or state.get('bound_host') != '127.0.0.1'
                    or state.get('bound_port') != 8093 or not isinstance(state.get('instance_id'), str)):
                sys.exit(1)
            try:
                if psutil.Process(pid).create_time() <= created + 1:
                    sys.exit(1)
            except psutil.NoSuchProcess:
                pass
        print('locked', flush=True)
        sys.stdin.buffer.read()
except OSError:
    sys.exit(1)
