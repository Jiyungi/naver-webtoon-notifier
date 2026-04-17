#!/usr/bin/env python3
"""
GitHub Actions entry point.
Checks all active webtoons and sends notifications via configured channels.
"""

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from watchlist import Watchlist
from detector import DetectionResult, check_all, get_new_completions
from notifier import TelegramNotifier, TelegramTestNotifier, build_dispatcher_from_env


def build_test_result() -> DetectionResult:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return DetectionResult(
        title_id=0,
        title_name="텔레그램 알림 테스트",
        is_completed=True,
        is_new_completion=True,
        has_new_episode=False,
        signals=[timestamp],
        total_episodes=1,
        latest_ep_no=1,
        latest_ep_title="수동 테스트 메시지",
        webtoon_url="https://github.com",
    )


def main():
    if os.environ.get("TEST_NOTIFICATION", "").lower() == "true":
        print("Running notification test mode.\n")
        dispatcher = build_dispatcher_from_env().filter_by_type((TelegramNotifier,))
        if not dispatcher.notifiers:
            print("Telegram notifier is not configured.")
            return
        dispatcher.notifiers = [
            TelegramTestNotifier(notifier.bot_token, notifier.chat_id)
            if isinstance(notifier, TelegramNotifier) else notifier
            for notifier in dispatcher.notifiers
        ]
        result = build_test_result()
        outcomes = dispatcher.notify(result)
        for channel, success in outcomes.items():
            status = "OK" if success else "FAILED"
            print(f"  [{status}] {channel} → {result.title_name}")
        return

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
