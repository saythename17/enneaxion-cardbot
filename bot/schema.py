"""카드뉴스 덱 구조 (Claude 구조화 출력 + 렌더러 공용).

텍스트 마크업 (title/question/main/big/message 등에서 사용)
  [[단어]]   제목 형광펜 (카드당 한 군데만)
  {t4}       유형 알약  → 「🎨 4번」 (배경 = 4번 고정색)
  {{단어}}   결론 네이비 박스 안 노랑 글자
  \n         줄바꿈
"""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

ColorName = Literal["blue", "purple", "red", "orange", "yellow", "green", "gray"]


class Row(BaseModel):
    badge: str = Field(description="행 앞 라벨. 예) '🥇 1위', '🫥 꼴찌', '📚 논문'")
    text: str = Field(description="한 줄. {t4} 유형 알약 사용 가능")


class Box(BaseModel):
    """compare(나란히 비교) / vs(VS 원형) 패턴의 흰 박스."""
    label: str = Field(description="박스 제목. 앞에 의미 이모지 하나. 예) '📚 논문 연구'")
    emoji: Optional[str] = Field(None, description="vs 패턴: 원 안 큰 이모지")
    type: Optional[int] = Field(None, description="vs 패턴: 원 색을 정할 유형 번호(1~9). 유형과 무관하면 null")
    color: Optional[ColorName] = Field(None, description="type 이 null 일 때 원 색")
    big: Optional[str] = Field(None, description="큰 글자(숫자/% 등, 10자 이내)")
    sub: Optional[str] = Field(None, description="보조 한 줄(15자 안팎)")
    rows: Optional[List[Row]] = Field(None, description="compare 패턴: 1~3행")


class Chip(BaseModel):
    icon: str = Field(description="국기 또는 이모지 하나")
    name: str
    value: Optional[str] = Field(None, description="예) '23%'")
    highlight: bool = Field(False, description="주인공 항목이면 true (네이비 테두리)")


class Group(BaseModel):
    label: str = Field(description="그룹 제목. {t4} 가능")
    type: Optional[int] = None
    color: Optional[ColorName] = None
    chips: List[Chip]


class Item(BaseModel):
    emoji: str
    color: ColorName
    main: str = Field(description="큰 한 줄 (14자 이내)")
    sub: str = Field(description="보조 한 줄 (15자 안팎)")


class Bar(BaseModel):
    label: str
    value: float = Field(description="막대 길이 비교용 수치")
    display: str = Field(description="막대 끝에 표시할 텍스트. 예) '12%'")
    color: Optional[ColorName] = Field(None, description="강조 막대만 색, 나머지는 gray")
    type: Optional[int] = None


class Card(BaseModel):
    pattern: Literal["cover", "compare", "vs", "chips", "list", "stat", "conclusion"]
    title: str = Field(description="cover: 3줄(\\n 구분) 질문형. 그 외: 최대 2줄. [[핵심어]] 형광펜 한 군데 + 끝에 감정 이모지 하나")
    highlight_color: Optional[Literal["yellow", "orange", "green"]] = "yellow"
    subtitle: Optional[str] = Field(None, description="cover 전용 작은 부제. 예) '💘 연애심리 연구'")
    question: Optional[str] = Field(None, description="cover 전용 한 줄 질문. 유형 알약 {t4} 넣기 권장")
    boxes: Optional[List[Box]] = Field(None, description="compare / vs: 정확히 2개")
    groups: Optional[List[Group]] = Field(None, description="chips: 1~3개 그룹")
    items: Optional[List[Item]] = Field(None, description="list: 정확히 3개")
    stat_big: Optional[str] = Field(None, description="stat: 큰 숫자. 예) '5:1'")
    stat_caption: Optional[str] = Field(None, description="stat: 숫자 아래 한 줄")
    bars: Optional[List[Bar]] = Field(None, description="conclusion: 막대 비교 2~4개 (선택)")
    message: Optional[str] = Field(None, description="conclusion: 네이비 박스 핵심 한 문장. '결론:'으로 시작, 청유형 마무리, 핵심어 {{ }}")
    source: Optional[str] = Field(None, description="출처 한 줄(저자, 연도, 매체/책). 해석만 있는 카드는 null")


class SourceRef(BaseModel):
    title: str
    url: str


class Deck(BaseModel):
    topic: str = Field(description="오늘 주제 한 줄 (기록용)")
    category: Literal["에니어그램", "심리학", "연애심리"]
    slug: str = Field(description="영문 소문자-하이픈 파일명용 짧은 이름")
    cards: List[Card] = Field(description="5~7장: cover 1 + 본문 3~5 + conclusion 1")
    hook_line1: str = Field(description="게시글 1줄: 독자가 들어봤을 통념")
    hook_line2: str = Field(description="게시글 2줄: 그걸 뒤집는 숫자나 반전")
    summary_bullets: List[str] = Field(description="본문 3~4줄, 각 줄 이모지로 시작")
    engagement_question: str = Field(description="댓글로 자기 사례·썰·의견을 나누게 만드는 질문 1개")
    hashtags: List[str] = Field(description="해시태그 3~5개, # 포함")
    instagram_hashtags: List[str] = Field(description="인스타용 추가 해시태그 8~12개, # 포함")
    sources: List[SourceRef] = Field(description="카드에 쓴 자료의 원문 링크")
    fact_check_notes: List[str] = Field(description="시온이 올리기 전 원자료와 대조할 숫자·주장 목록")
