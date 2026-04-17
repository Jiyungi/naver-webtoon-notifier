#!/usr/bin/env python3
"""
Poll Telegram bot updates and reply to simple text commands.

Designed for GitHub Actions polling, not a long-running bot server.
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests

from naver_api import get_webtoon_url
from watchlist import Watchlist

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "telegram_state.json")


def load_state() -> dict[str, Any]:
    if not os.path.exists(STATE_PATH):
        return {"last_update_id": 0}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict[str, Any]):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def telegram_request(token: str, method: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        f"https://api.telegram.org/bot{token}/{method}",
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram {method} failed: {data}")
    return data


def get_updates(token: str, offset: int) -> list[dict[str, Any]]:
    payload = {
        "offset": offset,
        "timeout": 0,
        "allowed_updates": ["message"],
    }
    data = telegram_request(token, "getUpdates", payload)
    return data.get("result", [])


def send_text(token: str, chat_id: str, text: str):
    telegram_request(
        token,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
    )


def build_watchlist_text(watchlist: Watchlist) -> str:
    entries = sorted(watchlist.list_all(), key=lambda entry: entry.title_name.casefold())
    if not entries:
        return "현재 워치리스트가 비어 있습니다."

    lines = [f"현재 워치리스트 {len(entries)}개", ""]
    for entry in entries[:20]:
        status = "완결 알림 완료" if entry.notified else "감시 중"
        latest = (
            f"#{entry.last_episode_no} {entry.last_episode_title}"
            if entry.last_episode_no else "아직 점검 전"
        )
        lines.append(f"- {entry.title_name}")
        lines.append(f"  상태: {status}")
        lines.append(f"  최신: {latest}")
        lines.append(f"  링크: {get_webtoon_url(entry.title_id)}")
        lines.append("")

    if len(entries) > 20:
        lines.append(f"... 외 {len(entries) - 20}개")

    return "\n".join(lines).strip()


def build_help_text() -> str:
    return (
        "사용 가능한 명령어\n\n"
        "/watchlist - 현재 워치리스트 보기\n"
        "/help - 도움말 보기"
    )


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    allowed_chat_id = str(os.environ["TELEGRAM_CHAT_ID"])
    watchlist = Watchlist()
    state = load_state()
    offset = int(state.get("last_update_id", 0)) + 1
    updates = get_updates(token, offset)

    if not updates:
        print("No Telegram commands to process.")
        return

    max_update_id = state.get("last_update_id", 0)

    for update in updates:
        max_update_id = max(max_update_id, update["update_id"])
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        text = (message.get("text") or "").strip()
        chat_id = str(chat.get("id", ""))

        if chat_id != allowed_chat_id or not text.startswith("/"):
            continue

        command = text.split()[0].lower()
        if command == "/watchlist":
            send_text(token, allowed_chat_id, build_watchlist_text(watchlist))
        elif command == "/help":
            send_text(token, allowed_chat_id, build_help_text())

    state["last_update_id"] = max_update_id
    save_state(state)
    print(f"Processed updates through {max_update_id}.")


if __name__ == "__main__":
    main()
