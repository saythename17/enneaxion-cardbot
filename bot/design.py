"""렌더된 카드를 Claude Design 캔버스 파일(project/canvas.json + project/CardNN.dc.html)로 변환.

카드 문구는 HTML 안에 그대로 들어가 있어서 캔버스에서 글자를 클릭해 바로 고칠 수 있다.
게시글 문구와 인스타 캡션은 캔버스 오른쪽 메모(스티커)로 들어간다.
"""
from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path
from typing import List

from .discord import community_post, instagram_caption
from .render import CSS
from .schema import Deck

MAX_CARDS = 7
CARD = 1080
GAP = 80
FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&amp;family=Noto+Sans+KR:wght@500;700;900&amp;display=swap">'
)


def card_file(i: int) -> str:
    """첫 장은 캔버스 진입 아트보드 이름 규칙(Main.dc.html)을 따른다."""
    return "Main.dc.html" if i == 1 else f"Card{i:02d}.dc.html"


def _css() -> str:
    css = CSS.replace("'BHS'", "'Black Han Sans'").replace("'NSK'", "'Noto Sans KR'")
    return css + "\n.card { background: #D3ECFF; }\n"


def dc_html(fitted_card: str, idx: int, total: int, topic: str) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{idx} / {total} · {html.escape(topic)}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
{FONTS_LINK}
<style>
body{{margin:0}}
{_css()}
</style>
</helmet>
{fitted_card}
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{CARD},"height":{CARD}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
"""


def write_canvas(deck: Deck, fitted_cards: List[str], root: Path, date: dt.date) -> Path:
    """root/project/ 아래에 캔버스 파일을 쓰고 project 폴더 경로를 돌려준다."""
    project = Path(root) / "project"
    project.mkdir(parents=True, exist_ok=True)
    for old in project.glob("*.dc.html"):
        old.unlink()

    total = len(fitted_cards)
    boards, order = {}, []
    for i, fc in enumerate(fitted_cards, 1):
        name = card_file(i)
        (project / name).write_text(dc_html(fc, i, total, deck.topic), encoding="utf-8")
        boards[name] = {"x": (i - 1) * (CARD + GAP), "y": 0, "w": CARD, "h": CARD, "title": f"{i} / {total}"}
        order.append(name)

    notes_x = total * (CARD + GAP)
    canvas = {
        "v": 3,
        "createdOnFiles": {"v": 1, "at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
        "title": "에니어시온 카드뉴스",
        "launch": {"view": "canvas"},
        "pages": [],
        "boards": boards,
        "order": order,
        "notes": {
            "heading": {
                "x": 0, "y": -300, "kind": "title1", "maxW": notes_x - GAP,
                "text": f"{date.isoformat()} · [{deck.category}] {deck.topic}",
            },
            "post": {
                "x": notes_x, "y": 0, "w": 760, "size": "m", "fill": "blue",
                "text": "📝 유튜브 커뮤니티 게시글\n\n" + community_post(deck),
            },
            "insta": {
                "x": notes_x + 840, "y": 0, "w": 760, "size": "m", "fill": "pink",
                "text": "📸 인스타그램 캡션\n\n" + instagram_caption(deck),
            },
            "check": {
                "x": notes_x, "y": 1160, "w": 1600, "size": "s", "fill": "orange",
                "text": "✅ 올리기 전 체크\n" + "\n".join(f"☐ {n}" for n in deck.fact_check_notes)
                + "\n\n🔗 원문\n" + "\n".join(f"{s.title} — {s.url}" for s in deck.sources),
            },
        },
        "designSystems": [],
    }
    (project / "canvas.json").write_text(json.dumps(canvas, ensure_ascii=False, indent=1), encoding="utf-8")
    return project
