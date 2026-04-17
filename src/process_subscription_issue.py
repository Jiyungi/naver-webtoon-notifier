#!/usr/bin/env python3
"""
Process a GitHub issue created by the static visual picker and update watchlist.json.
"""

from __future__ import annotations

import json
import os
import re
from urllib.request import Request, urlopen

from naver_api import get_series_info
from watchlist import Watchlist

MARKER_PATTERN = re.compile(r"<!--\s*subscription-request\s*(\{.*?\})\s*-->", re.DOTALL)


def github_api_request(url: str, method: str = "GET", payload: dict | None = None):
    token = os.environ["GITHUB_TOKEN"]
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, method=method, headers=headers)
    with urlopen(request) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


def extract_request(body: str) -> tuple[str, list[int]]:
    match = MARKER_PATTERN.search(body or "")
    if not match:
        return "add", []
    payload = json.loads(match.group(1))
    action = payload.get("action", "add")
    title_ids = [int(title_id) for title_id in payload.get("title_ids", [])]
    return action, title_ids


def build_comment(action: str, changed: list[str], skipped: list[str], errors: list[str]) -> str:
    verb = "Removed" if action == "remove" else "Added"
    lines = ["Visual catalog request processed."]
    if changed:
        lines.append("")
        lines.append(f"{verb}:")
        lines.extend(f"- {item}" for item in changed)
    if skipped:
        lines.append("")
        lines.append("Skipped:")
        lines.extend(f"- {item}" for item in skipped)
    if errors:
        lines.append("")
        lines.append("Errors:")
        lines.extend(f"- {item}" for item in errors)
    return "\n".join(lines)


def main():
    event_path = os.environ["GITHUB_EVENT_PATH"]
    repo = os.environ["GITHUB_REPOSITORY"]

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    issue = event["issue"]
    issue_number = issue["number"]
    issue_body = issue.get("body", "")
    action, title_ids = extract_request(issue_body)

    if not title_ids:
        comment = "No valid title IDs were found in this request."
        github_api_request(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
            method="POST",
            payload={"body": comment},
        )
        github_api_request(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}",
            method="PATCH",
            payload={"state": "closed"},
        )
        return

    watchlist = Watchlist()
    changed: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    for title_id in title_ids:
        existing = watchlist.get(title_id)
        if action == "remove":
            if not existing:
                skipped.append(f"{title_id} is not currently tracked")
                continue
            watchlist.remove(title_id)
            changed.append(f"{existing.title_name} ({title_id})")
            continue

        if existing:
            skipped.append(f"{existing.title_name} ({title_id}) already tracked")
            continue
        try:
            info = get_series_info(title_id)
        except Exception as exc:
            errors.append(f"{title_id}: {exc}")
            continue

        title_name = info.get("titleName", f"Unknown ({title_id})")
        if info.get("finished", False):
            skipped.append(f"{title_name} ({title_id}) is already completed")
            continue

        watchlist.add(title_id, title_name)
        changed.append(f"{title_name} ({title_id})")

    comment = build_comment(action, changed, skipped, errors)
    github_api_request(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
        method="POST",
        payload={"body": comment},
    )
    github_api_request(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}",
        method="PATCH",
        payload={"state": "closed"},
    )


if __name__ == "__main__":
    main()
