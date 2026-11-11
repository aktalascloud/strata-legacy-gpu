"""Summarize the actual Swift API measurements without dropping cold runs."""

from collections import defaultdict
import json
from pathlib import Path
from statistics import median


def summarize(path):
    groups = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        groups[row["label"]].append(row)
    return [
        (label, len(rows), median(row["api_timings"]["prompt_per_second"] for row in rows),
         median(row["api_timings"]["predicted_per_second"] for row in rows),
         median(row["elapsed_s"] for row in rows))
        for label, rows in groups.items()
    ]


if __name__ == "__main__":
    results = Path(__file__).resolve().parents[1] / "results"
    print("| Build | Runs | Prefill, tok/s | Decode, tok/s | End to end, s |")
    print("| --- | ---: | ---: | ---: | ---: |")
    for label, count, prefill, decode, elapsed in summarize(results / "bench.jsonl"):
        print(f"| {label} | {count} | {prefill:.1f} | {decode:.1f} | {elapsed:.2f} |")
