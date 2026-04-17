#!/usr/bin/env python3
"""
Export catalog and tracked titles for the static visual picker.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone

from catalog import fetch_full_catalog
from watchlist import Watchlist

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
CATALOG_PATH = os.path.join(DOCS_DIR, "catalog.json")
TRACKED_PATH = os.path.join(DOCS_DIR, "tracked.json")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)

    catalog = fetch_full_catalog()
    watchlist = Watchlist()

    catalog_payload = {
        "generated_at": now_iso(),
        "count": len(catalog),
        "webtoons": [asdict(entry) for entry in catalog],
    }
    tracked_payload = {
        "generated_at": now_iso(),
        "count": len(watchlist.list_all()),
        "title_ids": [entry.title_id for entry in watchlist.list_all()],
    }

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog_payload, f, ensure_ascii=False, indent=2)

    with open(TRACKED_PATH, "w", encoding="utf-8") as f:
        json.dump(tracked_payload, f, ensure_ascii=False, indent=2)

    print(f"Exported {len(catalog)} catalog entries to {CATALOG_PATH}")
    print(f"Exported {tracked_payload['count']} tracked entries to {TRACKED_PATH}")


if __name__ == "__main__":
    main()
