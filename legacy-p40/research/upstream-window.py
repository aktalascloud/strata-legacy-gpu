"""Inventory the two-week Strata issue/PR window from GitHub."""

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import subprocess


REPO = "Niko1221/Strata"
RELATED = re.compile(
    r"\b(?:avx[ -]?1|ivy bridge|pascal|p40|p100|sm[ _-]?6[01]|swift|iq3[_ -]?s|"
    r"pcie|ple|mmvq|mmq|numa|mtp|kv[ -]?(?:cache|stream)|prefill|decode|"
    r"resident|gguf|deadlock|race|overflow|memory leak|cuda graph)\b", re.I)


def api(route):
    return json.loads(subprocess.check_output(["gh", "api", route], encoding="utf-8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", help="ISO-8601 timestamp for the end of the 14-day window")
    args = parser.parse_args()
    end = datetime.fromisoformat(args.as_of) if args.as_of else datetime.now(timezone.utc)
    if end.tzinfo is None:
        parser.error("--as-of must include its UTC offset")
    end = end.astimezone(timezone.utc).replace(microsecond=0)
    cutoff = (end - timedelta(days=14)).isoformat().replace("+00:00", "Z")
    end = end.isoformat().replace("+00:00", "Z")
    rows = []
    for page in range(1, 101):
        items = api(f"repos/{REPO}/issues?state=all&sort=created&direction=desc&per_page=100&page={page}")
        for item in items:
            if not cutoff <= item["created_at"] < end:
                continue
            number = item["number"]
            kind = "pr" if "pull_request" in item else "issue"
            title = item["title"]
            matches = sorted(set(word.lower() for word in RELATED.findall(title)))
            body_matches = sorted(set(word.lower() for word in RELATED.findall(item.get("body") or "")))
            rows.append({"number": number, "kind": kind, "title": title, "state": item["state"],
                         "created": item["created_at"], "updated": item["updated_at"],
                         "url": item["html_url"], "title_matches": matches, "body_matches": body_matches})
        if not items or items[-1]["created_at"] < cutoff:
            break
    else:
        raise RuntimeError("GitHub pagination exceeded expected range")
    folder = Path(__file__).resolve().parents[1] / "results"
    folder.mkdir(exist_ok=True)
    output = {"repository": REPO, "created_from": cutoff, "created_before": end,
              "entries": rows}
    (folder / "upstream-window.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for kind in ("pr", "issue"):
        print(f"{kind}: {sum(row['kind'] == kind for row in rows)}")
