"""
Completion Detector
Multi-signal detection engine that combines API status + episode title patterns
to determine if a webtoon has reached its final episode.
"""

from dataclasses import dataclass
from naver_api import check_webtoon_status, WebtoonStatus
from watchlist import Watchlist, WatchEntry


@dataclass
class DetectionResult:
    title_id: int
    title_name: str
    is_completed: bool
    is_new_completion: bool   # True if this is a new completion
    has_new_episode: bool     # True if there's a new episode since last check
    signals: list             # List of signal descriptions
    total_episodes: int
    latest_ep_no: int
    latest_ep_title: str
    webtoon_url: str

    @property
    def confidence(self) -> str:
        """How confident are we this is truly completed?"""
        n = len(self.signals)
        if n == 0:
            return "none"
        elif n == 1:
            return "low"
        elif n == 2:
            return "medium"
        else:
            return "high"

    def summary(self) -> str:
        status_str = "✅ COMPLETED" if self.is_completed else "📺 Ongoing"
        lines = [
            f"📖 {self.title_name}",
            f"   Status: {status_str}",
            f"   Episodes: {self.total_episodes}",
            f"   Latest: #{self.latest_ep_no} - {self.latest_ep_title}",
            f"   Confidence: {self.confidence} ({len(self.signals)} signals)",
        ]
        if self.is_new_completion:
            lines.insert(1, "   🎉 NEW COMPLETION DETECTED!")
        if self.signals:
            lines.append("   Signals:")
            for sig in self.signals:
                lines.append(f"     • {sig}")
        return "\n".join(lines)


def detect_completion(title_id: int, watchlist: Watchlist) -> DetectionResult:
    """
    Check a single webtoon for completion.
    Compares current state against last known state in watchlist.
    """
    # Get current status from API
    status: WebtoonStatus = check_webtoon_status(title_id)

    # Get last known state
    entry: WatchEntry = watchlist.get(title_id)
    was_finished = entry.was_finished if entry else False
    last_ep_no = entry.last_episode_no if entry else 0

    # Determine if there's a new episode
    current_ep_no = status.latest_episode.no if status.latest_episode else 0
    has_new_episode = current_ep_no > last_ep_no

    # Determine if this is a new completion.
    # Episode title signals (e.g. "최종화", "에필로그") fire before the API
    # sets finished=True, which matters because Naver paywall kicks in then.
    ep_has_final_signal = bool(status.completion_signals)
    is_new_completion = (
        (status.finished and not was_finished)
        or (has_new_episode and ep_has_final_signal and not was_finished)
    )

    latest_ep_title = status.latest_episode.subtitle if status.latest_episode else ""

    result = DetectionResult(
        title_id=title_id,
        title_name=status.title_name,
        is_completed=status.finished,
        is_new_completion=is_new_completion,
        has_new_episode=has_new_episode,
        signals=status.completion_signals,
        total_episodes=status.total_episodes,
        latest_ep_no=current_ep_no,
        latest_ep_title=latest_ep_title,
        webtoon_url=f"https://comic.naver.com/webtoon/list?titleId={title_id}",
    )

    # Update watchlist with current state
    if entry:
        watchlist.update_state(
            title_id=title_id,
            last_episode_no=current_ep_no,
            last_episode_title=latest_ep_title,
            was_finished=status.finished,
            notified=is_new_completion,  # Mark notified if completion detected
        )

    return result


def check_all(watchlist: Watchlist) -> list[DetectionResult]:
    """Check all active (non-notified) webtoons in the watchlist."""
    results = []
    for entry in watchlist.list_active():
        try:
            result = detect_completion(entry.title_id, watchlist)
            results.append(result)
        except Exception as e:
            print(f"Error checking {entry.title_name} ({entry.title_id}): {e}")
    return results


def get_new_completions(results: list[DetectionResult]) -> list[DetectionResult]:
    """Filter results to only new completions."""
    return [r for r in results if r.is_new_completion]


def get_new_episodes(results: list[DetectionResult]) -> list[DetectionResult]:
    """Filter results to entries with new episodes (but not yet completed)."""
    return [r for r in results if r.has_new_episode and not r.is_completed]
