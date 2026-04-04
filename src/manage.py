#!/usr/bin/env python3
"""
CLI tool to manage the watchlist locally.

Usage:
  python src/manage.py add <title_id_or_url>   # Add a webtoon
  python src/manage.py remove <title_id>        # Remove a webtoon
  python src/manage.py list                     # Show watchlist
  python src/manage.py status <title_id>        # Check a webtoon's status
  python src/manage.py check                    # Run a manual check
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from naver_api import check_webtoon_status, get_series_info, title_id_from_url, get_webtoon_url
from watchlist import Watchlist
from detector import check_all, get_new_completions


def cmd_add(watchlist, identifier):
    if identifier.startswith("http"):
        tid = title_id_from_url(identifier)
        if tid is None:
            print(f"Could not extract title ID from URL: {identifier}")
            return
    else:
        try:
            tid = int(identifier)
        except ValueError:
            print(f"Invalid title ID: {identifier}")
            return

    try:
        info = get_series_info(tid)
        title_name = info.get("titleName", f"Unknown ({tid})")
        finished = info.get("finished", False)
    except Exception as e:
        print(f"Could not fetch info for title ID {tid}: {e}")
        return

    if finished:
        print(f"{title_name} (ID: {tid}) is already completed — nothing to watch for.")
        return

    watchlist.add(tid, title_name)
    print(f"Added: {title_name} (ID: {tid})")
    print(f"  URL: {get_webtoon_url(tid)}")
    print(f"\nCommit and push watchlist.json to activate monitoring.")


def cmd_remove(watchlist, identifier):
    try:
        tid = int(identifier)
    except ValueError:
        tid = title_id_from_url(identifier)
        if tid is None:
            print(f"Invalid identifier: {identifier}")
            return

    entry = watchlist.get(tid)
    if entry:
        watchlist.remove(tid)
        print(f"Removed: {entry.title_name} (ID: {tid})")
        print(f"\nCommit and push watchlist.json to apply.")
    else:
        print(f"Title ID {tid} not in watchlist.")


def cmd_list(watchlist):
    entries = watchlist.list_all()
    if not entries:
        print("Watchlist is empty. Add with: python src/manage.py add <title_id>")
        return

    print(f"\nWatchlist ({len(entries)} webtoons):")
    print("-" * 60)
    for e in entries:
        status = "Completed" if e.was_finished else ("Notified" if e.notified else "Watching")
        last_ep = f"Ep {e.last_episode_no}: {e.last_episode_title}" if e.last_episode_no else "Not checked yet"
        print(f"  {e.title_name} (ID: {e.title_id})")
        print(f"    Status: {status} | Last: {last_ep}")
        print(f"    URL: {get_webtoon_url(e.title_id)}")
        print()


def cmd_status(identifier):
    try:
        tid = int(identifier)
    except ValueError:
        tid = title_id_from_url(identifier)
    if not tid:
        print(f"Invalid: {identifier}")
        return

    status = check_webtoon_status(tid)
    print(f"\n{status.title_name} (ID: {status.title_id})")
    print(f"  Finished: {status.finished}")
    print(f"  On Hiatus: {status.rest}")
    print(f"  Total Episodes: {status.total_episodes}")
    print(f"  Description: {status.publish_description}")
    if status.latest_episode:
        print(f"  Latest: #{status.latest_episode.no} - {status.latest_episode.subtitle} ({status.latest_episode.service_date})")
    print(f"  Signals: {len(status.completion_signals)}")
    for sig in status.completion_signals:
        print(f"    - {sig}")


def cmd_check(watchlist):
    active = watchlist.list_active()
    if not active:
        print("No active webtoons.")
        return

    print(f"Checking {len(active)} webtoon(s)...\n")
    results = check_all(watchlist)
    new_completions = get_new_completions(results)

    for r in results:
        emoji = "NEW" if r.is_new_completion else ("done" if r.is_completed else "   ")
        print(f"  [{emoji}] {r.title_name}: Ep {r.latest_ep_no} - {r.latest_ep_title}")

    if new_completions:
        print(f"\n{len(new_completions)} new completion(s) detected!")
    else:
        print(f"\nAll {len(results)} webtoon(s) still ongoing.")


def main():
    watchlist = Watchlist()
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()
    if cmd == "add" and len(sys.argv) >= 3:
        cmd_add(watchlist, sys.argv[2])
    elif cmd == "remove" and len(sys.argv) >= 3:
        cmd_remove(watchlist, sys.argv[2])
    elif cmd == "list":
        cmd_list(watchlist)
    elif cmd == "status" and len(sys.argv) >= 3:
        cmd_status(sys.argv[2])
    elif cmd == "check":
        cmd_check(watchlist)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
