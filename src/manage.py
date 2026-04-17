#!/usr/bin/env python3
"""
CLI tool to manage the watchlist locally.

Usage:
  python src/manage.py browse <weekday> [page]  # Browse weekday titles
  python src/manage.py search <query>           # Search titles and choose one
  python src/manage.py add <title_id_or_url>    # Add a webtoon directly
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
from catalog import WEEKDAY_CODES, WEEKDAY_LABELS, CatalogEntry, fetch_full_catalog, fetch_weekday_catalog

PAGE_SIZE = 20


def add_title(watchlist, tid):
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

    existing = watchlist.get(tid)
    watchlist.add(tid, title_name)
    if existing:
        print(f"Already in watchlist: {title_name} (ID: {tid})")
    else:
        print(f"Added: {title_name} (ID: {tid})")
    print(f"  URL: {get_webtoon_url(tid)}")
    print("\nCommit and push watchlist.json to activate monitoring.")


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

    add_title(watchlist, tid)


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


def prompt_select_and_add(watchlist, entries: list[CatalogEntry]):
    if not entries or not sys.stdin.isatty():
        return

    try:
        choice = input("\nAdd one now? Enter number or press Enter to skip: ").strip()
    except EOFError:
        return

    if not choice:
        return

    try:
        index = int(choice)
    except ValueError:
        print("Invalid selection.")
        return

    if index < 1 or index > len(entries):
        print("Selection out of range.")
        return

    add_title(watchlist, entries[index - 1].title_id)


def cmd_browse(watchlist, weekday: str, page_raw: str | None = None):
    weekday = weekday.lower()
    if weekday not in WEEKDAY_CODES:
        labels = ", ".join(f"{code}({WEEKDAY_LABELS[code]})" for code in WEEKDAY_CODES)
        print(f"Invalid weekday. Use one of: {labels}")
        return

    try:
        page = int(page_raw) if page_raw else 1
    except ValueError:
        print(f"Invalid page number: {page_raw}")
        return

    if page < 1:
        print("Page must be 1 or greater.")
        return

    entries = fetch_weekday_catalog(weekday)
    total_pages = max(1, (len(entries) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page, total_pages)
    start = (page - 1) * PAGE_SIZE
    visible = entries[start:start + PAGE_SIZE]

    print(f"\n{WEEKDAY_LABELS[weekday]} 웹툰 ({len(entries)} titles, page {page}/{total_pages})")
    print("-" * 60)
    for index, entry in enumerate(visible, start=1):
        print(f"{index:>2}. {entry.title_name} (ID: {entry.title_id})")

    if page < total_pages:
        print(f"\nNext page: python src/manage.py browse {weekday} {page + 1}")

    prompt_select_and_add(watchlist, visible)


def cmd_search(watchlist, query: str):
    query = query.strip()
    if not query:
        print("Usage: python src/manage.py search <query>")
        return

    entries = [entry for entry in fetch_full_catalog() if query.casefold() in entry.title_name.casefold()]
    if not entries:
        print(f"No webtoons found for: {query}")
        return

    visible = entries[:15]
    print(f"\nSearch results for '{query}' ({len(entries)} match(es))")
    print("-" * 60)
    for index, entry in enumerate(visible, start=1):
        print(f"{index:>2}. {entry.title_name} ({entry.weekday_label}) - ID: {entry.title_id}")

    if len(entries) > len(visible):
        print(f"\nShowing first {len(visible)} results.")

    prompt_select_and_add(watchlist, visible)


def main():
    watchlist = Watchlist()
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()
    if cmd == "browse" and len(sys.argv) >= 3:
        cmd_browse(watchlist, sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else None)
    elif cmd == "search" and len(sys.argv) >= 3:
        cmd_search(watchlist, " ".join(sys.argv[2:]))
    elif cmd == "add" and len(sys.argv) >= 3:
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
