"""
Catalog fetcher for current Naver Webtoon listings.

The bot uses the mobile weekday pages as a lightweight browseable catalog.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from naver_api import HEADERS, title_id_from_url

MOBILE_BASE_URL = "https://m.comic.naver.com"
WEEKDAY_CODES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
WEEKDAY_LABELS = {
    "mon": "월요일",
    "tue": "화요일",
    "wed": "수요일",
    "thu": "목요일",
    "fri": "금요일",
    "sat": "토요일",
    "sun": "일요일",
}
STATUS_TOKENS = {
    "업데이트",
    "휴재",
    "신작",
    "청유물",
    "up",
    "new",
    "NEW",
}


@dataclass
class CatalogEntry:
    title_id: int
    title_name: str
    weekday: str
    updated_at: str
    thumbnail_url: str = ""
    webtoon_url: str = ""

    @property
    def weekday_label(self) -> str:
        return WEEKDAY_LABELS.get(self.weekday, self.weekday)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(parts: Iterable[str]) -> str:
    cleaned = []
    for part in parts:
        token = part.strip()
        if not token or token in STATUS_TOKENS:
            continue
        if token.startswith("관심 ") or token == "관심":
            continue
        if token.startswith("별점"):
            continue
        cleaned.append(token)
    return cleaned[0] if cleaned else ""


def _extract_title(anchor) -> str:
    image = anchor.find("img", alt=True)
    if image and image.get("alt"):
        return image["alt"].strip()

    for selector in ("strong", "h3", "span"):
        node = anchor.find(selector)
        if node:
            text = node.get_text(" ", strip=True)
            if text and text not in STATUS_TOKENS:
                return text

    return _normalize_text(anchor.stripped_strings)


def _extract_thumbnail(anchor) -> str:
    image = anchor.find("img")
    if not image:
        return ""
    src = image.get("src") or image.get("data-src") or ""
    if not src:
        return ""
    return urljoin(MOBILE_BASE_URL, src)


def fetch_weekday_catalog(weekday: str) -> list[CatalogEntry]:
    if weekday not in WEEKDAY_CODES:
        raise ValueError(f"Unsupported weekday: {weekday}")

    url = f"{MOBILE_BASE_URL}/webtoon/weekday?week={weekday}"
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    updated_at = _now_iso()
    entries: dict[int, CatalogEntry] = {}

    for anchor in soup.select("a[href*='titleId=']"):
        href = anchor.get("href", "")
        title_id = title_id_from_url(urljoin(MOBILE_BASE_URL, href))
        if title_id is None:
            continue

        title_name = _extract_title(anchor)
        if not title_name:
            continue

        entries[title_id] = CatalogEntry(
            title_id=title_id,
            title_name=title_name,
            weekday=weekday,
            updated_at=updated_at,
            thumbnail_url=_extract_thumbnail(anchor),
            webtoon_url=f"https://comic.naver.com/webtoon/list?titleId={title_id}",
        )

    return sorted(entries.values(), key=lambda entry: entry.title_name.casefold())


def fetch_full_catalog() -> list[CatalogEntry]:
    catalog: dict[int, CatalogEntry] = {}
    for weekday in WEEKDAY_CODES:
        for entry in fetch_weekday_catalog(weekday):
            catalog[entry.title_id] = entry
    return sorted(catalog.values(), key=lambda entry: (entry.weekday, entry.title_name.casefold()))
