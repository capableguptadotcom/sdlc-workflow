#!/usr/bin/env python3
"""Report upstream movement without modifying the reviewed skill pack."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lock",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "repo-template"
        / ".ai"
        / "skills.lock.json",
    )
    parser.add_argument("--fail-on-update", action="store_true")
    args = parser.parse_args()

    data = json.loads(args.lock.read_text(encoding="utf-8"))
    token = os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-developer-kit-update-checker",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    changed = 0
    failed = 0
    for source in data["sources"]:
        repo = source["repository"]
        branch = urllib.parse.quote(source["default_branch"], safe="")
        url = f"https://api.github.com/repos/{repo}/commits/{branch}"
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=20) as response:
                current = json.load(response)["sha"]
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
            failed += 1
            print(f"ERROR {source['id']}: {exc}", file=sys.stderr)
            continue
        reviewed = source["reviewed_commit"]
        if current == reviewed:
            print(f"CURRENT {source['id']} {reviewed}")
        else:
            changed += 1
            compare = f"{source['url']}/compare/{reviewed}...{current}"
            print(f"UPDATE {source['id']} {reviewed} -> {current} {compare}")

    print(f"Summary: {changed} update(s), {failed} lookup failure(s).")
    if failed:
        return 1
    if changed and args.fail_on_update:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
