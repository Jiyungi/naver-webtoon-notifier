"""
Naver Webtoon API Client
Fetches series info and episode lists from Naver Webtoon's internal API.
"""

import requests
import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Episode:
    no: int
    subtitle: str
    service_date: str
    star_score: float = 0.0
    charge: bool = False


@dataclass
class WebtoonStatus:
    title_id: int
    title_name: str
    finished: bool
    rest: bool  # on hiatus
    total_episodes: int
    publish_description: str  # e.g. "261화 완결" or "236화"
    latest_episode: Optional[Episode] = None
    completion_signals: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://comic.naver.com/api"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://comic.naver.com/",
    "Accept": "application/json",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Korean keywords that signal a final episode
FINAL_EPISODE_KEYWORDS = [
    "최종화",       # Final episode (formal)
    "마지막화",     # Last episode (colloquial)
    "마지막 화",    # Last episode (with space)
    "완결",         # Completed / The End
    "[완]",         # [Complete] tag
    "(완)",         # (Complete) tag
    "최종회",       # Final episode (variant)
    "마지막회",     # Last episode (variant)
    "THE END",      # English
    "FINAL",        # English
    "END",          # English (standalone)
    "에필로그",     # Epilogue (often the last episode)
    "후기",         # Afterword (often paired with last ep)
    "시즌 완결",    # Season complete
]

# Regex patterns for final episode detection (case-insensitive)
FINAL_EPISODE_PATTERNS = [
    r"최종화",
    r"마지막\s?화",
    r"완결",
    r"\[완\]",
    r"\(완\)",
    r"최종회",
    r"마지막\s?회",
    r"(?i)\bthe\s+end\b",
    r"(?i)\bfinal\b",
    r"(?i)\bend\b",
    r"에필로그",
    r"시즌\s*완결",
]


# ---------------------------------------------------------------------------
# API functions
# ---------------------------------------------------------------------------

def get_series_info(title_id: int) -> dict:
    """Fetch series metadata from Naver Webtoon API."""
    url = f"{BASE_URL}/article/list/info?titleId={title_id}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_episode_list(title_id: int, page: int = 1, sort: str = "DESC") -> dict:
    """Fetch episode list (newest first by default)."""
    url = f"{BASE_URL}/article/list?titleId={title_id}&page={page}&sort={sort}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def parse_latest_episode(episode_data: dict) -> Episode:
    """Parse a single episode entry from the API response."""
    return Episode(
        no=episode_data.get("no", 0),
        subtitle=episode_data.get("subtitle", ""),
        service_date=episode_data.get("serviceDateDescription", ""),
        star_score=episode_data.get("starScore", 0.0),
        charge=episode_data.get("charge", False),
    )


# ---------------------------------------------------------------------------
# Detection logic
# ---------------------------------------------------------------------------

def check_episode_title_signals(subtitle: str) -> list[str]:
    """
    Check an episode title for completion signals.
    Returns a list of matched signal descriptions.
    """
    signals = []
    for pattern in FINAL_EPISODE_PATTERNS:
        if re.search(pattern, subtitle):
            signals.append(f"Episode title matches pattern: {pattern}")
    return signals


def check_webtoon_status(title_id: int) -> WebtoonStatus:
    """
    Full status check for a webtoon.
    Combines API metadata + episode title heuristics.
    """
    # 1. Get series info
    info = get_series_info(title_id)
    finished = info.get("finished", False)
    rest = info.get("rest", False)
    title_name = info.get("titleName", f"Unknown ({title_id})")
    publish_desc = info.get("publishDescription", "")

    # 2. Get latest episodes
    ep_data = get_episode_list(title_id, page=1, sort="DESC")
    total_count = ep_data.get("totalCount", 0)
    article_list = ep_data.get("articleList", [])

    latest_episode = None
    completion_signals = []

    # Signal 1: API says finished
    if finished:
        completion_signals.append("API finished=true")

    # Signal 2: publishDescription contains "완결"
    if "완결" in publish_desc:
        completion_signals.append(f"publishDescription contains '완결': {publish_desc}")

    # Signal 3: Check latest episode titles for completion keywords
    for ep in article_list[:5]:  # Check last 5 episodes
        ep_obj = parse_latest_episode(ep)
        if latest_episode is None:
            latest_episode = ep_obj
        title_signals = check_episode_title_signals(ep_obj.subtitle)
        for sig in title_signals:
            completion_signals.append(f"Ep {ep_obj.no} ({ep_obj.subtitle}): {sig}")

    return WebtoonStatus(
        title_id=title_id,
        title_name=title_name,
        finished=finished,
        rest=rest,
        total_episodes=total_count,
        publish_description=publish_desc,
        latest_episode=latest_episode,
        completion_signals=completion_signals,
    )


def title_id_from_url(url: str) -> Optional[int]:
    """Extract titleId from a Naver Webtoon URL."""
    match = re.search(r"titleId=(\d+)", url)
    if match:
        return int(match.group(1))
    # Also handle /webtoon/detail/ID format
    match = re.search(r"/webtoon/(?:list|detail)/(\d+)", url)
    if match:
        return int(match.group(1))
    return None


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

def get_webtoon_url(title_id: int) -> str:
    return f"https://comic.naver.com/webtoon/list?titleId={title_id}"


if __name__ == "__main__":
    # Quick test
    test_ids = [703846, 783053]  # 여신강림 (completed), 김부장 (ongoing)
    for tid in test_ids:
        status = check_webtoon_status(tid)
        print(f"\n{'='*60}")
        print(f"Title: {status.title_name} (ID: {status.title_id})")
        print(f"Finished: {status.finished} | On Hiatus: {status.rest}")
        print(f"Total Episodes: {status.total_episodes}")
        print(f"Description: {status.publish_description}")
        if status.latest_episode:
            print(f"Latest Ep: #{status.latest_episode.no} - {status.latest_episode.subtitle}")
        print(f"Completion Signals ({len(status.completion_signals)}):")
        for sig in status.completion_signals:
            print(f"  ✓ {sig}")
