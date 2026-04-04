"""
Watchlist Manager
Persists tracked webtoons and their last-known state to a JSON file.
"""

import json
import os
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional

# Default path: watchlist.json at the repo root (one level up from src/)
DEFAULT_WATCHLIST_PATH = os.path.join(os.path.dirname(__file__), "..", "watchlist.json")


@dataclass
class WatchEntry:
    title_id: int
    title_name: str
    added_at: str              # ISO format
    last_checked: Optional[str] = None
    last_episode_no: int = 0
    last_episode_title: str = ""
    was_finished: bool = False  # Last known finished state
    notified: bool = False      # Whether we already sent completion notification


class Watchlist:
    def __init__(self, path: str = DEFAULT_WATCHLIST_PATH):
        self.path = path
        self.entries: dict[int, WatchEntry] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("webtoons", []):
                entry = WatchEntry(**item)
                self.entries[entry.title_id] = entry

    def save(self):
        data = {
            "webtoons": [asdict(e) for e in self.entries.values()],
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, title_id: int, title_name: str) -> WatchEntry:
        if title_id in self.entries:
            return self.entries[title_id]
        entry = WatchEntry(
            title_id=title_id,
            title_name=title_name,
            added_at=datetime.now(timezone.utc).isoformat(),
        )
        self.entries[title_id] = entry
        self.save()
        return entry

    def remove(self, title_id: int) -> bool:
        if title_id in self.entries:
            del self.entries[title_id]
            self.save()
            return True
        return False

    def get(self, title_id: int) -> Optional[WatchEntry]:
        return self.entries.get(title_id)

    def list_all(self) -> list[WatchEntry]:
        return list(self.entries.values())

    def list_active(self) -> list[WatchEntry]:
        """Return entries not yet marked as finished/notified."""
        return [e for e in self.entries.values() if not e.notified]

    def update_state(
        self,
        title_id: int,
        last_episode_no: int,
        last_episode_title: str,
        was_finished: bool,
        notified: bool = False,
    ):
        entry = self.entries.get(title_id)
        if entry:
            entry.last_checked = datetime.now(timezone.utc).isoformat()
            entry.last_episode_no = last_episode_no
            entry.last_episode_title = last_episode_title
            entry.was_finished = was_finished
            if notified:
                entry.notified = True
            self.save()
