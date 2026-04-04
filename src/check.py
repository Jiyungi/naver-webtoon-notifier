#!/usr/bin/env python3
"""
GitHub Actions entry point.
Checks all active webtoons and outputs results for the workflow.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from naver_api import check_webtoon_status, get_webtoon_url
from watchlist import Watchlist
from detector import check_all, get_new_completions


def main():
    watchlist = Watchlist()
    active = watchlist.list_active()

    if not active:
        print("No active webtoons to check.")
        _set_output("has_completions", "false")
        _set_output("summary", "Watchlist is empty.")
        return

    print(f"Checking {len(active)} webtoon(s)...\n")

    results = check_all(watchlist)
    new_completions = get_new_completions(results)

    # Print summary to logs
    for r in results:
        emoji = "🎉" if r.is_new_completion else ("✅" if r.is_completed else "📺")
        new_ep = " (NEW EP)" if r.has_new_episode else ""
        print(f"  {emoji} {r.title_name}: Ep {r.latest_ep_no} - {r.latest_ep_title}{new_ep}")

    if new_completions:
        print(f"\n🔔 {len(new_completions)} NEW COMPLETION(S)!")
        _set_output("has_completions", "true")

        # Build email body
        body_parts = []
        for r in new_completions:
            body_parts.append(
                f"📖 {r.title_name}\n"
                f"   Total Episodes: {r.total_episodes}\n"
                f"   Final Episode: #{r.latest_ep_no} - {r.latest_ep_title}\n"
                f"   Read it: {r.webtoon_url}\n"
                f"   Confidence: {r.confidence} ({len(r.signals)} signals)\n"
            )

        titles = ", ".join(r.title_name for r in new_completions)
        _set_output("completed_titles", titles)
        _set_output("email_body", "\n".join(body_parts))

        # Also build a summary of ALL webtoons for the log
        summary_parts = []
        for r in results:
            status = "COMPLETED 🎉" if r.is_new_completion else ("Completed" if r.is_completed else "Ongoing")
            summary_parts.append(f"{r.title_name} ({status}) - Ep {r.latest_ep_no}")
        _set_output("summary", "\n".join(summary_parts))
    else:
        print(f"\nNo new completions. All {len(results)} webtoon(s) still ongoing.")
        _set_output("has_completions", "false")
        _set_output("summary", f"All {len(results)} webtoon(s) still ongoing.")


def _set_output(name: str, value: str):
    """Set a GitHub Actions output variable."""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            # Handle multiline values
            if "\n" in value:
                import uuid
                delimiter = uuid.uuid4().hex
                f.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                f.write(f"{name}={value}\n")
    # Also print for local testing
    print(f"[OUTPUT] {name}={value[:100]}{'...' if len(value) > 100 else ''}")


if __name__ == "__main__":
    main()
