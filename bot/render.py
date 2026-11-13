"""Deck → 1080×1080 PNG 카드 (HTML/CSS + Chromium 스크린샷)."""
from __future__ import annotations

import html
import os
import re
from pathlib import Path
from typing import List

from .config import BRAND, COLORS, FONTS_DIR, NEWSLETTER, TYPES, color_hex
from .schema import Card, Deck

C = COLORS


def _font_faces() -> str:
    base = FONTS_DIR.as_uri()
    return f"""
@font-face {{ font-family: 'BHS'; src: url('{base}/BlackHanSans-Regular.ttf'); }}
@font-face {{ font-family: 'NSK'; font-weight: 500; src: url('{base}/NotoSansKR-500.ttf'); }}
@font-face {{ font-family: 'NSK'; font-weight: 700; src: url('{base}/NotoSansKR-700.ttf'); }}
@font-face {{ font-family: 'NSK'; font-weight: 900; src: url('{base}/NotoSansKR-900.ttf'); }}
"""


CSS = f"""
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 1080px; height: 1080px; background: {C['bg']}; }}
body {{ font-family: 'NSK', 'Noto Color Emoji', sans-serif; color: {C['navy']}; word-break: keep-all; }}
.card {{ width: 1080px; height: 1080px; padding: 64px 72px 56px; display: flex; flex-direction: column; }}
.top {{ display: flex; justify-content: space-between; align-items: center; height: 56px; flex: none; }}
.brand {{ background: {C['navy']}; color: #fff; font-weight: 900; font-size: 26px; padding: 10px 24px; border-radius: 999px; }}
.page {{ font-weight: 700; font-size: 26px; color: {C['sub']}; }}
.bhs {{ font-family: 'BHS', 'Noto Color Emoji', sans-serif; font-weight: 400; }}
.title {{ font-family: 'BHS', 'Noto Color Emoji', sans-serif; font-size: 82px; line-height: 1.18; margin-top: 40px; flex: none; max-height: 200px; overflow: hidden; text-wrap: balance; }}
.hl {{ padding: 0 14px; border-radius: 14px; white-space: nowrap; -webkit-box-decoration-break: clone; box-decoration-break: clone; }}
.pill {{ display: inline-block; padding: 4px 20px 6px; border-radius: 999px; font-family: 'NSK', 'Noto Color Emoji'; font-weight: 900; font-size: .78em; vertical-align: .08em; color: {C['navy']}; white-space: nowrap; line-height: 1.25; }}
.content {{ flex: 1; display: flex; flex-direction: column; justify-content: center; min-height: 0; padding: 28px 0 20px; }}
.source {{ flex: none; font-weight: 500; font-size: 18px; color: {C['sub']}; line-height: 1.4; min-height: 25px; }}
.box {{ background: #fff; border-radius: 30px; }}
.boxtitle {{ font-family: 'BHS', 'Noto Color Emoji'; font-size: 36px; }}
.subtxt {{ font-weight: 700; font-size: 27px; color: {C['sub']}; }}

/* cover */
.cover .subtitle {{ font-weight: 900; font-size: 38px; color: {C['sub']}; margin-top: 56px; }}
.cover .title {{ font-size: 118px; line-height: 1.16; margin-top: 22px; max-height: 420px; }}
.cover .question {{ font-weight: 900; font-size: 44px; margin-top: 44px; line-height: 1.5; }}
.cover .deco {{ margin-top: auto; display: flex; gap: 14px; height: 30px; }}
.cover .deco span {{ flex: 1; border-radius: 999px; }}

/* compare */
.cmp {{ display: flex; align-items: stretch; gap: 0; }}
.cmp .box {{ flex: 1; padding: 40px 34px; display: flex; flex-direction: column; gap: 26px; }}
.cmp .swap {{ width: 76px; flex: none; display: flex; align-items: center; justify-content: center; font-size: 46px; }}
.row {{ display: flex; flex-direction: column; gap: 10px; }}
.badge {{ font-weight: 900; font-size: 26px; color: {C['sub']}; }}
.rowtext {{ font-family: 'BHS', 'Noto Color Emoji'; font-size: 44px; line-height: 1.25; }}
.cmp .big {{ font-family: 'BHS'; font-size: 64px; }}

/* vs */
.vs {{ display: flex; gap: 40px; }}
.vs .box {{ flex: 1; padding: 40px 28px 44px; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 18px; }}
.circle {{ width: 200px; height: 200px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 104px; margin: 8px 0 4px; }}
.vs .big {{ font-family: 'BHS', 'Noto Color Emoji'; font-size: 68px; line-height: 1.1; }}

/* chips */
.groups {{ display: flex; flex-direction: column; gap: 26px; }}
.group {{ border-radius: 30px; padding: 28px 32px 32px; }}
.group .boxtitle {{ margin-bottom: 20px; }}
.chips {{ display: flex; flex-wrap: wrap; gap: 14px; }}
.chip {{ background: #fff; border-radius: 999px; padding: 12px 24px; font-weight: 900; font-size: 30px; border: 4px solid transparent; white-space: nowrap; }}
.chip.on {{ border-color: {C['navy']}; }}
.chip .v {{ color: {C['sub']}; margin-left: 8px; }}

/* list */
.list {{ display: flex; flex-direction: column; gap: 26px; }}
.list .box {{ display: flex; align-items: center; gap: 32px; padding: 22px 32px 22px 22px; }}
.sq {{ width: 104px; height: 104px; border-radius: 24px; flex: none; display: flex; align-items: center; justify-content: center; font-size: 56px; }}
.list .main {{ font-family: 'BHS', 'Noto Color Emoji'; font-size: 46px; line-height: 1.2; }}
.list .subtxt {{ margin-top: 6px; }}

/* stat */
.stat {{ padding: 56px 48px; text-align: center; }}
.stat .big {{ font-family: 'BHS', 'Noto Color Emoji'; font-size: 190px; line-height: 1.05; }}
.stat .cap {{ font-family: 'BHS', 'Noto Color Emoji'; font-size: 48px; margin-top: 18px; line-height: 1.3; }}

/* term */
.term {{ padding: 48px 52px; }}
.term .tl {{ font-weight: 900; font-size: 26px; color: {C['sub']}; }}
.term .tn {{ font-family: 'BHS', 'Noto Color Emoji'; font-size: 92px; line-height: 1.15; margin-top: 8px; }}
.term .to {{ font-weight: 700; font-size: 28px; color: {C['sub']}; margin-top: 4px; }}
.term .td {{ font-family: 'BHS', 'Noto Color Emoji'; font-size: 46px; line-height: 1.35; margin-top: 30px; padding-top: 30px; border-top: 4px dashed {C['gray']}; text-wrap: pretty; }}
.term .te {{ margin-top: 26px; background: {C['bg']}; border-radius: 22px; padding: 22px 28px; font-weight: 700; font-size: 30px; line-height: 1.45; text-wrap: pretty; }}

/* conclusion */
.bars {{ padding: 34px 40px; display: flex; flex-direction: column; gap: 22px; margin-bottom: 28px; }}
.bar {{ display: flex; align-items: center; gap: 20px; }}
.bar .lb {{ width: 250px; flex: none; font-weight: 900; font-size: 28px; }}
.bar .track {{ flex: 1; height: 50px; }}
.bar .fill {{ height: 100%; border-radius: 14px; min-width: 14px; }}
.bar .dv {{ width: 120px; flex: none; text-align: right; font-family: 'BHS'; font-size: 40px; }}
.msg, .question, .rowtext, .main {{ text-wrap: pretty; }}
.msg {{ background: {C['navy']}; color: #fff; border-radius: 30px; padding: 44px 48px; font-family: 'BHS', 'Noto Color Emoji'; font-size: 54px; line-height: 1.35; }}
.msg .y {{ color: {C['yellow']}; }}
.cp {{ margin-top: 24px; text-align: center; font-family: 'BHS', 'Noto Color Emoji'; font-size: 40px; }}
.cp span {{ background: {C['yellow']}; border-radius: 999px; padding: 10px 34px 14px; display: inline-block; }}
"""

# 렌더 후 넘침을 줄이고(글자 크기 축소), 그래도 넘치면 경고를 돌려준다.
FIT_JS = """
() => {
  const warn = [];
  const over = el => el.scrollHeight > el.clientHeight + 2 || el.scrollWidth > el.clientWidth + 2;
  // 1) 제목: 줄 수 제한
  document.querySelectorAll('.title').forEach(t => {
    let fs = parseFloat(getComputedStyle(t).fontSize);
    while (over(t) && fs > 56) { fs -= 2; t.style.fontSize = fs + 'px'; }
    if (over(t)) warn.push('제목 넘침: ' + t.innerText.slice(0, 30));
  });
  // 2) 박스 안 개별 텍스트: 한 줄 폭 초과 시 축소
  document.querySelectorAll('.fit').forEach(el => {
    let fs = parseFloat(getComputedStyle(el).fontSize);
    const min = fs * 0.6;
    while (el.scrollWidth > el.clientWidth + 2 && fs > min) { fs -= 1; el.style.fontSize = fs + 'px'; }
  });
  // 3) 본문 영역 전체: 넘치면 content 전체 zoom 축소
  const c = document.querySelector('.content');
  if (c) {
    const inner = c.firstElementChild;
    let z = 1;
    while (inner && inner.scrollHeight * z > c.clientHeight - 40 && z > 0.7) {
      z -= 0.03; inner.style.zoom = z;
    }
    if (inner && inner.getBoundingClientRect().height > c.clientHeight - 30) warn.push('본문 넘침');
    if (z < 0.97) warn.push('본문 ' + Math.round(z * 100) + '%로 축소됨');
  }
  return warn;
}
"""


def _pill(n: int) -> str:
    t = TYPES[n]
    return f'<span class="pill" style="background:{color_hex(n)}">{t["emoji"]} {n}번</span>'


def fmt(text: str | None, hl_color: str = "yellow") -> str:
    if not text:
        return ""
    s = html.escape(text)
    s = re.sub(r"\{t([1-9])\}", lambda m: _pill(int(m.group(1))), s)
    s = re.sub(r"\[\[(.+?)\]\]", lambda m: f'<span class="hl" style="background:{color_hex(hl_color)}">{m.group(1)}</span>', s)
    s = re.sub(r"\{\{(.+?)\}\}", r'<span class="y">\1</span>', s)
    return s.replace("\\n", "<br>").replace("\n", "<br>")


def _box_color(obj) -> str:
    if getattr(obj, "type", None):
        return color_hex(obj.type)
    return color_hex(getattr(obj, "color", None) or "gray")


def _content(card: Card) -> str:
    p = card.pattern
    if p == "compare":
        boxes = card.boxes or []
        parts = []
        for b in boxes[:2]:
            rows = "".join(
                f'<div class="row"><div class="badge">{fmt(r.badge)}</div><div class="rowtext">{fmt(r.text)}</div></div>'
                for r in (b.rows or [])
            )
            big = f'<div class="big fit">{fmt(b.big)}</div>' if b.big else ""
            sub = f'<div class="subtxt">{fmt(b.sub)}</div>' if b.sub else ""
            parts.append(f'<div class="box"><div class="boxtitle">{fmt(b.label)}</div>{big}{rows}{sub}</div>')
        return '<div class="cmp">' + '<div class="swap emo">🔄</div>'.join(parts) + "</div>"
    if p == "vs":
        parts = []
        for b in (card.boxes or [])[:2]:
            parts.append(
                f'<div class="box"><div class="boxtitle">{fmt(b.label)}</div>'
                f'<div class="circle emo" style="background:{_box_color(b)}">{html.escape(b.emoji or "")}</div>'
                f'<div class="big fit">{fmt(b.big)}</div><div class="subtxt">{fmt(b.sub)}</div></div>'
            )
        return '<div class="vs">' + "".join(parts) + "</div>"
    if p == "chips":
        gs = []
        for g in card.groups or []:
            chips = "".join(
                f'<span class="chip{" on" if ch.highlight else ""}">{html.escape(ch.icon)} {fmt(ch.name)}'
                + (f'<span class="v">{fmt(ch.value)}</span>' if ch.value else "")
                + "</span>"
                for ch in g.chips
            )
            gs.append(f'<div class="group" style="background:{_box_color(g)}"><div class="boxtitle">{fmt(g.label)}</div><div class="chips">{chips}</div></div>')
        return '<div class="groups">' + "".join(gs) + "</div>"
    if p == "list":
        its = "".join(
            f'<div class="box"><div class="sq emo" style="background:{color_hex(it.color)}">{html.escape(it.emoji)}</div>'
            f'<div style="min-width:0;flex:1"><div class="main fit">{fmt(it.main)}</div><div class="subtxt">{fmt(it.sub)}</div></div></div>'
            for it in (card.items or [])[:3]
        )
        return f'<div class="list">{its}</div>'
    if p == "stat":
        return f'<div class="box stat"><div class="big fit">{fmt(card.stat_big)}</div><div class="cap">{fmt(card.stat_caption)}</div></div>'
    if p == "term":
        origin = f'<div class="to">{fmt(card.term_origin)}</div>' if card.term_origin else ""
        ex = f'<div class="te">💬 {fmt(card.term_example)}</div>' if card.term_example else ""
        return (f'<div class="box term"><div class="tl">📖 오늘의 용어</div><div class="tn fit">{fmt(card.term)}</div>{origin}'
                f'<div class="td">{fmt(card.term_def)}</div>{ex}</div>')
    if p == "conclusion":
        out = ""
        if card.bars:
            mx = max((b.value for b in card.bars), default=1) or 1
            rows = "".join(
                f'<div class="bar"><div class="lb">{fmt(b.label)}</div><div class="track">'
                f'<div class="fill" style="width:{max(b.value / mx, 0.02) * 100:.1f}%;background:{_box_color(b)}"></div></div>'
                f'<div class="dv">{fmt(b.display)}</div></div>'
                for b in card.bars
            )
            out += f'<div class="box bars">{rows}</div>'
        out += f'<div class="msg">{fmt(card.message)}</div>'
        if card.comment_prompt:
            out += f'<div class="cp"><span>{fmt(card.comment_prompt)}</span></div>'
        return f"<div>{out}</div>"
    return ""


def card_html(card: Card, idx: int, total: int, is_last: bool) -> str:
    top = f'<div class="top"><span class="brand">{BRAND}</span><span class="page">{idx} / {total}</span></div>'
    hl = card.highlight_color or "yellow"
    if card.pattern == "cover":
        deco = "".join(f'<span style="background:{C[k]}"></span>' for k in ("blue", "purple", "red", "orange", "yellow", "green"))
        body = (
            f'<div class="card cover">{top}'
            f'<div class="subtitle">{fmt(card.subtitle)}</div>'
            f'<div class="title">{fmt(card.title, hl)}</div>'
            f'<div class="question">{fmt(card.question)}</div>'
            f'<div class="deco">{deco}</div></div>'
        )
    else:
        src = card.source or ""
        if is_last:
            nl = f"📮 더 깊은 이야기는 뉴스레터 「{NEWSLETTER}」에서"
            src = f"{src} · {nl}" if src else nl
        body = (
            f'<div class="card">{top}<div class="title">{fmt(card.title, hl)}</div>'
            f'<div class="content">{_content(card)}</div>'
            f'<div class="source">{html.escape(src)}</div></div>'
        )
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{_font_faces()}{CSS}</style></head><body>{body}</body></html>"


def _launch(p):
    exe = os.environ.get("CHROMIUM_PATH")
    return p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()


def render_deck(deck: Deck, out_dir: Path) -> tuple[List[Path], List[str], List[str]]:
    """PNG 경로, 넘침 경고, 자동 축소가 반영된 카드 HTML(.card 요소, Claude Design 캔버스용)을 돌려준다."""
    from playwright.sync_api import sync_playwright

    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    total = len(deck.cards)
    paths, warnings, fitted = [], [], []
    with sync_playwright() as p:
        browser = _launch(p)
        page = browser.new_page(viewport={"width": 1080, "height": 1080}, device_scale_factor=1)
        for i, card in enumerate(deck.cards, 1):
            html_path = out_dir / f"card_{i:02d}.html"
            html_path.write_text(card_html(card, i, total, i == total), encoding="utf-8")
            page.goto(html_path.as_uri())
            page.evaluate("document.fonts.ready")
            for w in page.evaluate(FIT_JS):
                warnings.append(f"{i}장: {w}")
            fitted.append(page.evaluate("document.querySelector('.card').outerHTML"))
            png = out_dir / f"card_{i:02d}.png"
            page.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": 1080, "height": 1080})
            paths.append(png)
        browser.close()
    return paths, warnings, fitted
