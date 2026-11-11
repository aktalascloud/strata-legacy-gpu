"""Compare Swift on a fixed long API request, recording timings and output hashes."""

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path


def api(base, path, payload=None):
    return urllib.request.urlopen(urllib.request.Request(
        base + path, data=None if payload is None else json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}), timeout=900)


def socket_monitor():
    import ctypes as c
    from ctypes import wintypes as w
    import psutil

    class GroupAffinity(c.Structure):
        _fields_ = [("mask", c.c_size_t), ("group", w.USHORT), ("reserved", w.USHORT * 3)]

    kernel = c.WinDLL("kernel32", use_last_error=True)
    highest = w.ULONG()
    if not kernel.GetNumaHighestNodeNumber(c.byref(highest)):
        raise c.WinError(c.get_last_error())
    nodes = {}
    for node in range(highest.value + 1):
        mask = GroupAffinity()
        if not kernel.GetNumaNodeProcessorMaskEx(node, c.byref(mask)):
            raise c.WinError(c.get_last_error())
        if mask.group != 0:
            raise RuntimeError("Socket timing expects a single Windows processor group")
        nodes[str(node)] = [i for i in range(c.sizeof(c.c_size_t) * 8) if mask.mask & (1 << i)]

    def snapshot():
        counters = psutil.cpu_times(percpu=True)
        return {node: (sum(counters[i].user + counters[i].system for i in ids),
                       sum(counters[i].idle for i in ids)) for node, ids in nodes.items()}

    return snapshot


def socket_percent(before, after):
    result = {}
    for node, (busy, idle) in after.items():
        active = busy - before[node][0]
        total = active + idle - before[node][1]
        result[node] = round(100 * active / total, 1) if total > 0 else None
    return result


def measure(base, model, index, row_count, reuse_prefix, cpu_snapshot=None):
    rows = "\n".join(
        f"{i:04d} region-{i % 29:02d} rack-{i % 13:02d} latency={19 * i % 300} "
        f"queue={i * i % 71} retries={23 * i % 8} payload={13 * i % 937}"
        for i in range(row_count))
    task = "Analyze this synthetic latency trace."
    sample = f"Report variant {index}."
    prompt = f"{task}\n{rows}\n\n{sample}" if reuse_prefix else f"{task} {sample}\n{rows}"
    payload = {
        "model": model, "temperature": 0, "seed": 42, "max_tokens": 768,
        "stream": True, "stream_options": {"include_usage": True},
        "chat_template_kwargs": {"enable_thinking": False},
        "messages": [{"role": "user", "content": (
            f"{prompt}\n\n"
            "Write a detailed 1,500-word engineering review with a measurement plan, "
            "sample queries, three confounders, experiment design and rollback criteria. "
            "Tie each proposal to the trace. Begin with a numbered list of hypotheses.")}],
    }
    cpu_start = cpu_snapshot() if cpu_snapshot else None
    started = time.perf_counter()
    first = usage = timings = finish = None
    output = hashlib.sha256()
    with api(base, "/v1/chat/completions", payload) as response:
        for line in response:
            if not line.startswith(b"data:"):
                continue
            body = line[5:].strip()
            if body == b"[DONE]":
                break
            chunk = json.loads(body)
            if chunk.get("error"):
                raise RuntimeError(chunk["error"])
            usage = chunk.get("usage") or usage
            timings = chunk.get("timings") or timings
            for choice in chunk.get("choices", []):
                finish = choice.get("finish_reason") or finish
                delta = choice.get("delta", {})
                for field in ("reasoning_content", "reasoning", "content"):
                    if delta.get(field):
                        if first is None:
                            first = time.perf_counter() - started
                            if cpu_snapshot:
                                cpu_first = cpu_snapshot()
                        output.update(delta[field].encode())
    elapsed = time.perf_counter() - started
    if first is None or not usage or usage["prompt_tokens"] < 4096 or usage["completion_tokens"] < 512:
        raise RuntimeError(f"Insufficient work for long comparison: {usage}, {finish}")
    result = {"case": index, "elapsed_s": elapsed, "ttft_s": first, "usage": usage,
              "api_timings": timings, "finish": finish, "text_sha256": output.hexdigest(),
              "end_to_end_tps": usage["completion_tokens"] / elapsed}
    if cpu_snapshot:
        result["host_numa_busy_pct"] = {"prefill": socket_percent(cpu_start, cpu_first),
                                       "decode": socket_percent(cpu_first, cpu_snapshot())}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("--base", default="http://127.0.0.1:8093")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--rows", type=int, default=315)
    parser.add_argument("--reuse-prefix", action="store_true")
    parser.add_argument("--socket-load", action="store_true", help="record system CPU utilization by Windows NUMA node")
    args = parser.parse_args()
    if not 1 <= args.runs <= 20 or not 160 <= args.rows <= 5000:
        parser.error("Use 1–20 runs and 160–5000 trace rows.")
    with api(args.base, "/v1/models") as response:
        model = json.load(response)["data"][0]["id"]
    path = Path(__file__).resolve().parents[1] / "results" / "bench.jsonl"
    path.parent.mkdir(exist_ok=True)
    cpu_snapshot = socket_monitor() if args.socket_load else None
    for index in range(args.runs):
        row = {"label": args.label, "model": model,
               **measure(args.base, model, index, args.rows, args.reuse_prefix, cpu_snapshot)}
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)
