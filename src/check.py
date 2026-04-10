#!/usr/bin/env python3
"""
GitHub Actions entry point.
Checks all active webtoons and sends notifications via configured channels.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from watchlist import Watchlist
from detector import check_all, get_new_completions
from notifier import build_dispatcher_from_env


def main():
    watchlist = Watchlist()
    active = watchlist.list_active()

    if not active:
        print("No active webtoons to check.")
        return

    print(f"Checking {len(active)} webtoon(s)...\n")

    results = check_all(watchlist)
    new_completions = get_new_completions(results)

    for r in results:
        emoji = "🎉" if r.is_new_completion else ("✅" if r.is_completed else "📺")
        new_ep = " (NEW EP)" if r.has_new_episode else ""
        print(f"  {emoji} {r.title_name}: Ep {r.latest_ep_no} - {r.latest_ep_title}{new_ep}")

    if new_completions:
        print(f"\n🔔 {len(new_completions)} NEW COMPLETION(S)!")
        dispatcher = build_dispatcher_from_env()
        for r in new_completions:
            outcomes = dispatcher.notify(r)
            for channel, success in outcomes.items():
                status = "OK" if success else "FAILED"
                print(f"  [{status}] {channel} → {r.title_name}")
    else:
        print(f"\nNo new completions. All {len(results)} webtoon(s) still ongoing.")


if __name__ == "__main__":
    main()
