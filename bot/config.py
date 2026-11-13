"""디자인 핸즈오프(에니어시온 카드뉴스 디자인 핸즈오프, 2026-11-13) 기준 상수."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "fonts"
OUTPUT_DIR = ROOT / "output"
HISTORY_FILE = ROOT / "data" / "history.json"

BRAND = "📊 에니어시온"
NEWSLETTER = "에니어 인사이트 서클"

# 2. 컬러
COLORS = {
    "bg": "#D3ECFF",
    "navy": "#13294B",
    "sub": "#3D5478",
    "white": "#FFFFFF",
    "blue": "#4DABF7",
    "purple": "#B197FC",
    "red": "#FF8787",
    "orange": "#FFA94D",
    "yellow": "#FFD43B",
    "green": "#69DB7C",
    "gray": "#C9D6E6",
    # 아래 셋은 핸즈오프 팔레트 밖의 임시색 — 1·6·8번 고정색이 확정되면 교체
    "teal": "#63E6BE",
    "pink": "#F783AC",
    "lime": "#A9E34B",
}

# 유형별 고정색·이모지. confirmed=False 는 [시온 확인: 나머지 유형 색] 대기 중인 임시값
TYPES = {
    1: {"name": "개혁가", "emoji": "⚖️", "color": "teal", "confirmed": False},
    2: {"name": "조력가", "emoji": "🤝", "color": "red", "confirmed": True},
    3: {"name": "성취가", "emoji": "🏆", "color": "orange", "confirmed": False},
    4: {"name": "개인주의자", "emoji": "🎨", "color": "purple", "confirmed": True},
    5: {"name": "탐구가", "emoji": "🔍", "color": "blue", "confirmed": True},
    6: {"name": "충실가", "emoji": "🛡️", "color": "lime", "confirmed": False},
    7: {"name": "열정가", "emoji": "🎉", "color": "yellow", "confirmed": False},
    8: {"name": "도전가", "emoji": "🦁", "color": "pink", "confirmed": False},
    9: {"name": "평화주의자", "emoji": "🕊️", "color": "green", "confirmed": True},
}

HIGHLIGHTS = ("yellow", "orange", "green")


def color_hex(name_or_type) -> str:
    """'yellow' / '#FFD43B' / 4(유형) → hex."""
    if name_or_type is None:
        return COLORS["gray"]
    if isinstance(name_or_type, int):
        return COLORS[TYPES[name_or_type]["color"]]
    s = str(name_or_type).strip()
    if s.isdigit() and int(s) in TYPES:
        return COLORS[TYPES[int(s)]["color"]]
    if s.startswith("#"):
        return s
    return COLORS.get(s, COLORS["gray"])
