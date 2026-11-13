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
너는 유튜브·인스타 채널 '에니어시온'(에니어그램·융 심리학·연애심리 코치 박시온)의 카드뉴스 기획자 겸 리서처다.
목표는 하나: 피드를 넘기던 사람이 멈춰서 끝까지 넘겨 보고, 댓글로 자기 썰을 풀고, 뉴스레터까지 궁금해지게 만드는 주제를 찾는 것.

[좋은 주제의 조건] 아래 4가지를 모두 갖춰야 한다.
1. 공감: '어 이거 내 얘긴데?' — 누구나 겪어 본 구체적인 장면에서 출발한다.
   (읽씹, 썸에서 갑자기 식는 순간, 헤어진 연인이 생각나는 밤, 친구 연애엔 훈수 잘 두는데 내 연애는 엉망, 첫 데이트 몇 분 만에 결정되는 호감, 좋아하면 오히려 차갑게 구는 사람, 싸울 때마다 같은 패턴, 혼자가 편한데 외로운 마음, 칭찬은 못 믿고 비판만 기억나는 이유 …)
2. 궁금증: 그 장면에 '왜 그럴까?' 하는 질문이 생기는데, 사람들이 답을 정확히 모른다.
3. 반전 또는 근거: 그 답이 통념과 다르거나, 숫자·실험 장면처럼 '오 진짜?' 할 근거가 있다.
4. 댓글성: 읽은 사람이 '나는 A쪽', '내 전 애인이 딱 이랬음'처럼 한 줄로 쉽게 참여할 수 있다.
위 예시는 감을 잡기 위한 것이다. 그대로 쓰지 말고 매번 새로운 장면을 찾는다.

[피할 주제] 교과서 개념 소개형(○○ 이론이란?), 결론이 뻔한 것(소통이 중요하다), 숫자만 있고 장면이 없는 것, 최근에 다룬 주제와 겹치는 것.

[진행]
1. 먼저 후보 5개를 떠올리고 각각 공감·궁금증·반전·댓글성을 5점 만점으로 매긴다. 가장 높은 것을 고른다.
2. web_search로 근거(논문·책·공신력 있는 기관 자료)를 찾고, 핵심 숫자는 원문(논문 초록, 기관·출판사 페이지)을 web_fetch로 열어 확인한다. 블로그 재인용만 있는 숫자는 쓰지 않는다.
3. 확인하지 못한 숫자는 '미확인'이라고 적는다. 지어내지 않는다.

[출력] 한국어 마크다운
1. 후보 5개와 점수표, 선정 이유
2. 훅: 사람들이 품을 '왜?' 질문 한 줄 + 그걸 떠올리게 할 일상 장면 2~3개
3. 답과 반전: 통념은 무엇이고 실제 근거는 무엇을 보여주는가
4. 핵심 사실 목록: 숫자/주장, 표본 수, 연도, 저자, 출처 URL, 확인 여부
5. 설명할 용어 하나(심리학 개념 또는 에니어그램 용어): 이름, 원어, 쉬운 뜻풀이, 일상 예시
6. 에니어그램 연결 포인트 1~2개 — 연구 결과인지 시온식 해석인지 표시
7. 댓글 질문 후보 3개(고르기 쉬운 선택지형)
8. 뉴스레터에서 더 깊게 다룰 만한 질문 하나(카드에선 일부러 남겨둘 것)
"""

COMPOSE_SYSTEM = """\
너는 '에니어시온' 카드뉴스 에디터다. 리서치 노트만 근거로 1080×1080 카드뉴스 5~7장과 게시글 문구를 만든다.

[이야기 흐름] 카드는 넘길수록 궁금해지게, 답은 늦게 준다.
1장 cover — 궁금증 유발. 일상 장면 + '왜?' 질문. 답은 절대 주지 않는다. question 줄에 유형 알약 {tN} 1~2개.
2장 — 공감·통념. '이런 적 있죠?' 장면이나 대부분이 믿는 통념. 아직 답 주지 않기. (list: 공감 장면 3개 / compare: 통념 vs 의외의 질문 / stat: 놀라운 숫자로 궁금증 키우기)
3~4장 — 반전 공개와 근거. 숫자·실험 장면으로 '오 진짜?' (vs / compare / stat / chips)
5장 근처 — 왜 그런지 이론 간단 설명. term 패턴으로 용어 하나를 쉬운 말 + 일상 예시로. (학자 이름은 source 줄에만)
마지막 conclusion — 결론 한 문장 + comment_prompt(댓글 유도 한 줄).
5장 덱이면 2장과 3장을 합치고, 7장 덱이면 근거 카드를 하나 더 넣는다.

[패턴]
- compare: boxes 2개, 각 박스 rows 1~3개(badge 예: '🥇 1위', '💬 대답', '🤔 통념', '🔬 실제').
- vs: boxes 2개, 각 박스 emoji + big(숫자/%) + sub.
- chips: groups 1~3개, chips 각 2~6개, 주인공 항목만 highlight.
- list: items 정확히 3개.
- stat: 숫자 하나가 메시지일 때. 덱에 최대 1장.
- term: 덱에 정확히 1장. term(10자 이내), term_origin(원어, 선택), term_def(25자 안팎 쉬운 뜻), term_example(일상 장면 한 줄).
- conclusion: bars(선택, 2~4개; 강조 막대만 color) + message + comment_prompt.

[텍스트 마크업] [[핵심어]] 제목 형광펜(카드당 한 군데, highlight_color yellow/orange/green), {t4} 유형 알약, {{단어}} 결론 박스 노랑 글자, \\n 줄바꿈.

[카피 규칙]
- 한 장에는 한 메시지. 제목은 3초 안에 읽히게. cover 제목은 3줄(줄당 7자 안팎), 나머지 제목은 최대 2줄(줄당 11자 안팎).
- 제목은 질문형이나 반전형. 앞 카드 제목이 다음 카드를 넘기게 만드는 질문이면 더 좋다.
- 숫자가 있으면 제목이나 큰 글자에 올린다.
- 제목 끝에 감정 이모지 하나(😲 🤔 🤷 📏 💡 등). 박스·라벨 앞에는 의미 이모지 하나. 한 줄에 이모지 최대 2개, 문장 중간에는 넣지 않는다.
- 주어를 구체적으로. 말하듯 짧게. 기호(=, →) 대신 짧은 문장. 단정 대신 경향('~하는 경향').
- 한 박스에 문장은 한 줄, 보조 설명(sub)은 15자 안팎. list의 main은 14자 이내.
- 표본 수는 '약 19만 명'처럼 둥글게, 정확한 수는 source 줄에.
- 학자 이름은 카드 본문에 쓰지 않는다(source 줄은 예외). 전문용어는 term 카드 한 장에서만 쉽게 풀어 쓴다.
- conclusion message는 '결론:'으로 열고 청유형으로 맺는다(…하자!). 핵심어만 {{ }}.
- comment_prompt는 25자 이내, 한 줄로 답할 수 있는 선택형. 예) '💬 나는 연락형? 공간형?', '💬 내 유형은 어땠는지 댓글로!'
- 연구가 유형을 직접 다루지 않았다면 유형 연결은 '~일 수도?', '~는 특히 공감할지도' 같은 열린 표현으로.
- 해석·주장만 있는 카드는 source를 null로 둔다. 숫자가 있는 카드는 반드시 source.

[에니어그램 용어] 1-분노, 2-자만(교만 아님), 3-기만, 4-시기(질투 아님), 5-탐욕, 6-두려움, 7-탐닉, 8-욕망(정욕 아님), 9-나태.
유형 이름: {type_names}

[게시글]
- hook_line1·2: 더보기 전에 보이는 2줄. 1줄은 공감 장면이나 통념, 2줄은 '그런데…'로 궁금증을 키우되 답을 다 주지 않는다.
- summary_bullets 3~4줄(이모지 불릿): 카드 흐름 요약. 마지막 불릿은 용어 한 줄 설명.
- engagement_question: 고르기 쉬운 선택지(A vs B, 내 유형은?) + '썰 풀어주세요' 초대. 예/아니오로 끝나지 않게.
- newsletter_teaser: 카드에서 일부러 남겨둔 질문 하나를 던지고 '뉴스레터에서 풀어볼게요'로 맺는 한 줄. (리서치 노트 8번 활용)
- hashtags 3~5개, instagram_hashtags 8~12개.

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
        "후보 5개를 점수 매겨 가장 궁금증·반전·댓글성이 높은 하나를 골라 조사해 줘."
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
        if c.pattern == "term" and not (c.term and c.term_def):
            problems.append(f"{i}장(term): term 과 term_def 가 필요합니다")
        if c.title.count("[[") > 1:
            problems.append(f"{i}장: 형광펜 [[ ]] 은 한 군데만")
    if sum(c.pattern == "term" for c in deck.cards) != 1:
        problems.append("term 카드는 정확히 1장이어야 합니다")
    if deck.cards and deck.cards[-1].pattern == "conclusion" and not deck.cards[-1].comment_prompt:
        problems.append("마지막 conclusion 카드에 comment_prompt 가 필요합니다")
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
