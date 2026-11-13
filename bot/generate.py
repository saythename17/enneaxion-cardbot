"""Claude API로 ① 주제 선정·자료 조사(웹 검색) → ② 카드뉴스 덱(JSON) 작성."""
from __future__ import annotations

import datetime as dt
import json
import random

import anthropic
from pydantic import ValidationError

from .config import TYPES
from .schema import Deck

MODEL = "claude-opus-5-5"
BETAS = ["server-side-fallback-2026-07-01"]  # 거절(refusal) 시 서버가 다른 모델로 자동 재시도

CATEGORIES = ["연애심리", "심리학", "에니어그램"]
LENSES = [
    "최근 3년 안에 발표된 학술 연구 결과",
    "고전적인 심리학 실험이나 장기 추적 연구",
    "널리 읽힌 심리·관계 관련 책 한 권의 핵심 개념",
    "대규모 설문·통계 데이터",
    "드라마·영화·소설 속 인물이나 실제 사회 현상을 심리학으로 읽기",
    "흔한 통념을 뒤집는 반전 연구",
]

RESEARCH_SYSTEM = """\
너는 유튜브·인스타 채널 '에니어시온'(에니어그램·융 심리학·연애심리 코치 박시온)의 카드뉴스 리서처다.
매일 아침 한 편, 사람들이 '어 이거 내 얘기인데?' 하고 댓글로 자기 썰·사례·의견을 꺼내고 싶어지는 주제를 고른다.

주제 기준
- 일상의 고민·궁금증에서 출발한다 (서운함, 읽씹, 미루기, 연애 패턴, 첫인상, 질투, 이별 후 연락 등).
- 근거가 분명해야 한다: 실제 논문·책·공신력 있는 기관 자료. 블로그 재인용만 있는 숫자는 쓰지 않는다.
- 카드로 보여줄 수 있는 '숫자' 또는 '대비(A vs B)'가 하나 이상 있으면 좋다.
- 에니어그램 유형과 자연스럽게 연결할 수 있으면 연결 포인트를 1~2개 적되, 연구가 유형을 직접 다룬 게 아니면 '해석'이라고 분명히 표시한다.
- 최근에 다룬 주제와 겹치지 않는다.

조사 방법
- web_search로 후보를 찾고, 핵심 숫자는 원문(논문 초록, 기관 페이지, 출판사 페이지)을 web_fetch로 열어 확인한다.
- 확인하지 못한 숫자는 '미확인'이라고 적는다. 지어내지 않는다.

출력 (한국어, 마크다운)
1. 선정 주제 한 줄 + 왜 사람들이 댓글을 달고 싶어할지
2. 핵심 사실 목록: 각 항목마다 숫자/주장, 표본 수, 연도, 저자, 출처 URL, 확인 여부
3. 카드로 쓸 대비·반전 포인트 2~3개
4. 에니어그램 연결 포인트(있다면) — 연구 결과인지 해석인지 표시
5. 댓글 유도 질문 후보 3개
"""

COMPOSE_SYSTEM = """\
너는 '에니어시온' 카드뉴스 에디터다. 리서치 노트만 근거로 1080×1080 카드뉴스 5~7장과 게시글 문구를 만든다.

[장 구성] cover 1장 → 본문 3~5장 → conclusion 1장. 본문 패턴은 내용에 맞게 고른다:
- compare(나란히 비교): 두 자료·두 반응이 다른 답을 낼 때. boxes 2개, 각 박스 rows 1~3개(badge 예: '🥇 1위', '🫥 꼴찌', '💬 대답').
- vs(VS 원형): 한 대상의 두 결과. boxes 2개, 각 박스 emoji + big(숫자/%) + sub.
- chips(그룹 칩): 항목이 많을 때. groups 1~3개, chips 각 2~6개, 주인공 항목만 highlight.
- list(아이콘 리스트): 이유·방법 3가지. items 정확히 3개.
- stat(큰 숫자): 숫자 하나가 메시지일 때. 덱에 최대 1장.
- conclusion: 마지막 장. bars(선택, 2~4개; 강조 막대만 color) + message.

[텍스트 마크업] [[핵심어]] 제목 형광펜(카드당 한 군데, highlight_color yellow/orange/green), {t4} 유형 알약, {{단어}} 결론 박스 노랑 글자, \\n 줄바꿈.

[카피 규칙]
- 한 장에는 한 메시지. 제목은 3초 안에 읽히게. cover 제목은 3줄 질문형(줄당 7자 안팎), 나머지 제목은 최대 2줄(줄당 11자 안팎).
- 제목은 질문형이나 반전형. 숫자가 있으면 제목이나 큰 글자에 올린다.
- 제목 끝에 감정 이모지 하나(😲 🤔 🤷 📏 💡 등). 박스·라벨 앞에는 의미 이모지 하나. 한 줄에 이모지 최대 2개, 문장 중간에는 넣지 않는다.
- 주어를 구체적으로("같은 질문, 정반대의 답" → "사이트마다 정반대의 결과"). 말하듯 짧게. 기호(=, →) 대신 짧은 문장.
- 단정 대신 경향("~를 고르는 경향"). 라벨은 뜻이 분명한 말로.
- 한 박스에 문장은 한 줄, 보조 설명(sub)은 15자 안팎. list의 main은 14자 이내.
- 표본 수는 '약 19만 명'처럼 둥글게, 정확한 수는 source 줄에.
- 학자 이름·전문용어는 카드 본문에 쓰지 않는다(source 줄은 예외).
- conclusion message는 '결론:'으로 열고 청유형으로 맺는다(…하자!). 핵심어만 {{ }}.
- cover question에는 관련 유형 알약 {tN}을 1~2개 넣어 에니어그램 독자를 끌어들인다. 연구가 유형을 직접 다루지 않았다면 '~일 수도?', '~는 특히 공감할지도' 같은 열린 표현으로.
- 해석·주장만 있는 카드는 source를 null로 둔다. 숫자가 있는 카드는 반드시 source.

[에니어그램 용어] 1-분노, 2-자만(교만 아님), 3-기만, 4-시기(질투 아님), 5-탐욕, 6-두려움, 7-탐닉, 8-욕망(정욕 아님), 9-나태.
유형 이름: {type_names}

[게시글] hook_line1 = 독자가 들어봤을 통념, hook_line2 = 그걸 뒤집는 숫자나 반전(더보기 전에 보이는 2줄).
summary_bullets 3~4줄(이모지 불릿). engagement_question 1개: 독자가 자기 연애·관계 썰이나 자기 유형 경험을 쉽게 꺼낼 수 있는 구체적인 질문(예/아니오로 끝나지 않게).
hashtags 3~5개, instagram_hashtags 8~12개.

[정확성] 리서치 노트에서 '확인'된 숫자만 쓴다. 미확인 숫자는 쓰지 않는다. 시온의 상담 사례나 개인 경험을 지어내지 않는다.
fact_check_notes에 올리기 전 원문과 대조할 숫자·주장을 모두 적는다.
"""


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def _text(msg) -> str:
    return "\n".join(b.text for b in msg.content if b.type == "text")


def pick_angle(history: list[dict], today: dt.date) -> tuple[str, str]:
    """카테고리는 날짜로 순환, 접근 방식은 최근 것과 겹치지 않게 무작위."""
    category = CATEGORIES[today.toordinal() % len(CATEGORIES)]
    recent_lenses = {h.get("lens") for h in history[-4:]}
    lens = random.choice([l for l in LENSES if l not in recent_lenses] or LENSES)
    return category, lens


def research(category: str, lens: str, history: list[dict], today: dt.date) -> str:
    recent = "\n".join(f"- {h['date']} [{h.get('category')}] {h['topic']}" for h in history[-60:]) or "- (없음)"
    user = (
        f"오늘 날짜: {today.isoformat()}\n"
        f"오늘 카테고리: {category}\n"
        f"오늘 접근 방식: {lens}\n\n"
        f"최근에 다룬 주제(겹치지 말 것):\n{recent}\n\n"
        "주제 후보를 넓게 훑어본 뒤 가장 댓글이 활발할 만한 하나를 골라 조사해 줘."
    )
    tools = [
        {"type": "web_search_20260209", "name": "web_search", "max_uses": 8},
        {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 6},
    ]
    messages = [{"role": "user", "content": user}]
    for _ in range(5):  # pause_turn 재개 최대 5회
        with _client().beta.messages.stream(
            model=MODEL,
            max_tokens=64000,
            system=RESEARCH_SYSTEM,
            messages=messages,
            tools=tools,
            output_config={"effort": "high"},
            betas=BETAS,
            fallbacks="default",
        ) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "refusal":
            raise RuntimeError(f"리서치 단계 거절: {msg.stop_details}")
        if msg.stop_reason != "pause_turn":
            return _text(msg)
        messages = [{"role": "user", "content": user}, {"role": "assistant", "content": msg.content}]
    raise RuntimeError("리서치가 pause_turn 한도를 넘었습니다")


def _extract_json(text: str) -> str:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("응답에서 JSON 객체를 찾지 못했습니다")
    return text[start : end + 1]


def _check_deck(deck: Deck) -> list[str]:
    """스키마로는 못 거르는 핸즈오프 규칙 검사."""
    problems = []
    n = len(deck.cards)
    if not 5 <= n <= 7:
        problems.append(f"카드는 5~7장이어야 하는데 {n}장입니다")
    if deck.cards and deck.cards[0].pattern != "cover":
        problems.append("첫 장은 cover 여야 합니다")
    if deck.cards and deck.cards[-1].pattern != "conclusion":
        problems.append("마지막 장은 conclusion 이어야 합니다")
    for i, c in enumerate(deck.cards, 1):
        if c.pattern in ("compare", "vs") and len(c.boxes or []) != 2:
            problems.append(f"{i}장({c.pattern}): boxes 는 정확히 2개")
        if c.pattern == "list" and len(c.items or []) != 3:
            problems.append(f"{i}장(list): items 는 정확히 3개")
        if c.pattern == "chips" and not c.groups:
            problems.append(f"{i}장(chips): groups 가 비었습니다")
        if c.pattern == "stat" and not c.stat_big:
            problems.append(f"{i}장(stat): stat_big 이 비었습니다")
        if c.pattern == "conclusion" and not c.message:
            problems.append(f"{i}장(conclusion): message 가 비었습니다")
        if c.title.count("[[") > 1:
            problems.append(f"{i}장: 형광펜 [[ ]] 은 한 군데만")
    return problems


def compose(notes: str, category: str, today: dt.date) -> Deck:
    """구조화 출력 대신 JSON 텍스트를 받아 pydantic 으로 검증하고, 틀리면 이유를 알려 최대 2번 다시 쓰게 한다.
    (덱 스키마가 커서 구조화 출력의 문법 크기 제한에 걸림)"""
    type_names = ", ".join(f"{n}번 {t['name']}" for n, t in TYPES.items())
    schema = json.dumps(Deck.model_json_schema(), ensure_ascii=False)
    system = (
        COMPOSE_SYSTEM.replace("{type_names}", type_names)
        + "\n[출력 형식] 아래 JSON 스키마를 따르는 JSON 객체 하나만 출력한다. 설명·코드블록 없이 JSON만.\n"
        + schema
    )
    messages = [{
        "role": "user",
        "content": f"날짜: {today.isoformat()} / 카테고리: {category}\n\n<research_notes>\n{notes}\n</research_notes>\n\n이 노트로 카드뉴스 덱을 만들어 줘.",
    }]
    last_error = ""
    for _ in range(3):
        with _client().beta.messages.stream(
            model=MODEL,
            max_tokens=32000,
            system=system,
            messages=messages,
            output_config={"effort": "high"},
            betas=BETAS,
            fallbacks="default",
        ) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "refusal":
            raise RuntimeError(f"작성 단계 거절: {msg.stop_details}")
        try:
            deck = Deck.model_validate_json(_extract_json(_text(msg)))
            problems = _check_deck(deck)
            if not problems:
                return deck
            last_error = "규칙 위반:\n- " + "\n- ".join(problems)
        except (ValidationError, ValueError) as e:
            last_error = f"JSON 검증 실패:\n{e}"
        messages += [
            {"role": "assistant", "content": msg.content},
            {"role": "user", "content": f"{last_error}\n\n고쳐서 전체 JSON을 다시 출력해 줘."},
        ]
    raise RuntimeError(f"카드 작성이 3번 모두 검증에 실패했습니다. 마지막 오류: {last_error[:500]}")


def generate(history: list[dict], today: dt.date) -> tuple[Deck, str, dict]:
    category, lens = pick_angle(history, today)
    notes = research(category, lens, history, today)
    deck = compose(notes, category, today)
    return deck, notes, {"category": category, "lens": lens}


if __name__ == "__main__":  # 리서치만 단독 테스트
    print(research("연애심리", LENSES[0], [], dt.date.today()))
