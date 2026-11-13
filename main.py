"""에니어시온 카드뉴스 봇.

  python main.py                          # 조사 → 작성 → 렌더 → 디스코드 (매일 아침 자동 실행용)
  python main.py --deck samples/x.json    # 이미 있는 덱 JSON으로 렌더(+전송)만
  python main.py --no-discord             # 디스코드 전송 생략
  python main.py --no-discord --save-latest   # 생성 후 latest/ 에 저장 (아침 생성 단계)
  python main.py --deck latest/deck.json      # latest/ 덱으로 렌더 + 디스코드 (아침 전송 단계)

환경 변수: ANTHROPIC_API_KEY, DISCORD_WEBHOOK_URL, (선택) DESIGN_URL, CHROMIUM_PATH
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from bot.config import HISTORY_FILE, OUTPUT_DIR, ROOT
from bot.design import write_canvas
from bot.discord import community_post, instagram_caption, send
from bot.render import render_deck
from bot.schema import Deck


def load_history() -> list[dict]:
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []


def save_history(history: list[dict]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history[-365:], ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", type=Path, help="덱 JSON 경로(생성 단계 건너뜀)")
    ap.add_argument("--no-discord", action="store_true")
    ap.add_argument("--save-latest", action="store_true", help="latest/ 에 덱·캔버스 파일 저장 (Claude Design 페이지 갱신용)")
    args = ap.parse_args()

    today = dt.datetime.now(ZoneInfo("Asia/Seoul")).date()
    history = load_history()
    meta: dict = {}

    if args.deck:
        deck = Deck.model_validate_json(args.deck.read_text(encoding="utf-8"))
        notes = ""
    else:
        from bot.generate import generate
        deck, notes, meta = generate(history, today)

    out = OUTPUT_DIR / f"{today.isoformat()}_{deck.slug}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "deck.json").write_text(deck.model_dump_json(indent=1), encoding="utf-8")
    if notes:
        (out / "research_notes.md").write_text(notes, encoding="utf-8")
    (out / "community_post.txt").write_text(community_post(deck), encoding="utf-8")
    (out / "instagram_caption.txt").write_text(instagram_caption(deck), encoding="utf-8")

    images, warnings, fitted = render_deck(deck, out)
    write_canvas(deck, fitted, out / "design", today)
    print(f"렌더 완료: {out} ({len(images)}장)")
    for w in warnings:
        print("  ⚠️", w)

    webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    if not args.no_discord:
        if not webhook:
            print("DISCORD_WEBHOOK_URL 이 없어 전송을 건너뜁니다", file=sys.stderr)
        else:
            send(webhook, deck, images, warnings, today.isoformat(), os.environ.get("DESIGN_URL"))
            print("디스코드 전송 완료")

    if args.save_latest:
        latest = ROOT / "latest"
        shutil.rmtree(latest, ignore_errors=True)
        latest.mkdir()
        shutil.copy(out / "deck.json", latest / "deck.json")
        shutil.copytree(out / "design", latest / "design")
        (latest / "meta.json").write_text(
            json.dumps({"date": today.isoformat(), "topic": deck.topic, "cards": len(images)}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        print(f"latest/ 저장 완료 ({today.isoformat()})")

    if not args.deck:
        history.append({"date": today.isoformat(), "topic": deck.topic, "category": deck.category, "lens": meta.get("lens")})
        save_history(history)
    return 0


if __name__ == "__main__":
    sys.exit(main())
