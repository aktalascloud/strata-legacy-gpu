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


def measure(base, model, index, row_count, reuse_prefix):
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
                        output.update(delta[field].encode())
    elapsed = time.perf_counter() - started
    if first is None or not usage or usage["prompt_tokens"] < 4096 or usage["completion_tokens"] < 512:
        raise RuntimeError(f"Insufficient work for long comparison: {usage}, {finish}")
    return {"case": index, "elapsed_s": elapsed, "ttft_s": first, "usage": usage,
            "api_timings": timings, "finish": finish, "text_sha256": output.hexdigest(),
            "end_to_end_tps": usage["completion_tokens"] / elapsed}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("--base", default="http://127.0.0.1:8093")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--rows", type=int, default=315)
    parser.add_argument("--reuse-prefix", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.runs <= 20 or not 160 <= args.rows <= 5000:
        parser.error("Use 1–20 runs and 160–5000 trace rows.")
    with api(args.base, "/v1/models") as response:
        model = json.load(response)["data"][0]["id"]
    path = Path(__file__).resolve().parents[1] / "results" / "bench.jsonl"
    path.parent.mkdir(exist_ok=True)
    for index in range(args.runs):
        row = {"label": args.label, "model": model,
               **measure(args.base, model, index, args.rows, args.reuse_prefix)}
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)
