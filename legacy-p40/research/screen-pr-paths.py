"""Record changed-path coverage for the PRs in the current two-week inventory."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import time


RESULTS = Path(__file__).resolve().parents[1] / "results"


def query(requests):
    query = 'query { repository(owner:"Niko1221",name:"Strata") { ' + requests + ' } }'
    for delay in (0, 1, 4):
        time.sleep(delay)
        result = subprocess.run(["gh", "api", "graphql", "-f", f"query={query}"],
                                text=True, encoding="utf-8", capture_output=True, timeout=90)
        if result.returncode == 0:
            return list(json.loads(result.stdout)["data"]["repository"].values())
    raise RuntimeError("GitHub path request failed")


def batch(numbers):
    fields = "number headRefOid changedFiles files(first:100){nodes{path} pageInfo{hasNextPage endCursor}}"
    requests = " ".join(f"p{number}:pullRequest(number:{number}){{{fields}}}" for number in numbers)
    rows = query(requests)
    for row in rows:
        if row is None:
            continue
        head = row["headRefOid"]
        page = row["files"]["pageInfo"]
        while page["hasNextPage"]:
            cursor = json.dumps(page["endCursor"])
            request = (f'pr:pullRequest(number:{row["number"]})'
                       f'{{headRefOid files(first:100,after:{cursor}){{nodes{{path}} pageInfo{{hasNextPage endCursor}}}}}}')
            following, = query(request)
            if following["headRefOid"] != head:
                raise RuntimeError(f'PR #{row["number"]} changed while fetching its paths')
            row["files"]["nodes"].extend(following["files"]["nodes"])
            page = following["files"]["pageInfo"]
    return rows


if __name__ == "__main__":
    inventory = json.loads((RESULTS / "upstream-window.json").read_text(encoding="utf-8"))
    numbers = [row["number"] for row in inventory["entries"] if row["kind"] == "pr"]
    batches = [numbers[i:i + 16] for i in range(0, len(numbers), 16)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = [row for group in pool.map(batch, batches) for row in group if row]
    if {row["number"] for row in rows} != set(numbers):
        raise RuntimeError("GitHub path coverage is incomplete")
    entries = []
    for row in rows:
        paths = [value["path"] for value in row["files"]["nodes"]]
        entries.append({"number": row["number"], "head": row["headRefOid"], "files": paths,
                        "total": row["changedFiles"], "truncated": len(paths) < row["changedFiles"]})
    (RESULTS / "upstream-pr-paths.json").write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    print(f"PRs: {len(entries)}; incomplete paths: {sum(row['truncated'] for row in entries)}")
