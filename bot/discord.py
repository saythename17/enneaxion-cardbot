"""디스코드 웹후크로 카드 이미지 + 게시글 문구 전송."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List

import requests

from .config import NEWSLETTER
from .schema import Deck


def community_post(deck: Deck) -> str:
    """핸즈오프 6. 커뮤니티 게시글 형식."""
    lines = [deck.hook_line1, deck.hook_line2, ""]
    lines += deck.summary_bullets
    lines += ["", f"💬 {deck.engagement_question}", ""]
    lines.append(f"📮 {deck.newsletter_teaser}")
    lines.append(f"👉 뉴스레터 「{NEWSLETTER}」 (프로필 링크)")
    lines.append(" ".join(deck.hashtags))
    return "\n".join(lines)


def instagram_caption(deck: Deck) -> str:
    tags = list(dict.fromkeys(deck.hashtags + deck.instagram_hashtags))
    body = community_post(deck).rsplit("\n", 1)[0]
    return body + "\n\n" + " ".join(tags)


def _post(url: str, payload: dict, files: List[Path] | None = None) -> None:
    for attempt in range(4):
        if files:
            multipart = {"payload_json": (None, json.dumps(payload), "application/json")}
            for i, p in enumerate(files):
                multipart[f"files[{i}]"] = (p.name, p.read_bytes(), "image/png")
            r = requests.post(url, files=multipart, timeout=60)
        else:
            r = requests.post(url, json=payload, timeout=30)
        if r.status_code == 429:
            time.sleep(float(r.json().get("retry_after", 2)) + 0.5)
            continue
        if r.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return
    r.raise_for_status()


def _chunks(text: str, limit: int = 1900) -> List[str]:
    out, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > limit:
            out.append(cur)
            cur = ""
        cur += line + "\n"
    if cur.strip():
        out.append(cur)
    return out


def send(webhook_url: str, deck: Deck, images: List[Path], warnings: List[str], date_str: str) -> None:
    header = (
        f"## ☀️ {date_str} 오늘의 카드뉴스\n"
        f"**[{deck.category}] {deck.topic}**\n"
        f"카드 {len(images)}장 · 아래 문구를 복사해서 올리세요"
    )
    _post(webhook_url, {"content": header, "username": "에니어시온 카드뉴스봇"}, images[:10])

    post = community_post(deck)
    _post(webhook_url, {"content": "### 📝 유튜브 커뮤니티 게시글\n```\n" + post + "\n```", "username": "에니어시온 카드뉴스봇"})
    _post(webhook_url, {"content": "### 📸 인스타그램 캡션\n```\n" + instagram_caption(deck) + "\n```", "username": "에니어시온 카드뉴스봇"})

    check = ["### ✅ 올리기 전 체크"]
    check += [f"☐ {n}" for n in deck.fact_check_notes]
    check += [f"🔗 <{s.url}> — {s.title}" for s in deck.sources]
    if warnings:
        check += ["⚠️ 레이아웃 경고: " + " / ".join(warnings)]
    for c in _chunks("\n".join(check)):
        _post(webhook_url, {"content": c, "username": "에니어시온 카드뉴스봇"})
