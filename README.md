# 에니어시온 카드뉴스 봇

매일 아침 9시(KST)에 에니어그램·심리학·연애심리 주제를 하나 골라 근거 자료(논문·책·통계)를 조사하고,
「에니어시온 카드뉴스 디자인 핸즈오프」 규격의 1080×1080 카드 5~7장과 게시글 문구를 만들어 디스코드로 보냅니다.

## 흐름

```
GitHub Actions (매일 00:00 UTC = 09:00 KST)
  └ main.py
     ① 주제 선정 + 자료 조사   Claude(웹 검색·원문 확인)  → research_notes.md
     ② 카드·문구 작성          Claude(구조화 출력)         → deck.json
     ③ 카드 렌더링             HTML/CSS → Chromium → PNG  → card_01~07.png
     ④ 디스코드 전송           카드 이미지 + 커뮤니티 게시글 + 인스타 캡션 + 팩트체크 목록
     ⑤ data/history.json 에 오늘 주제 기록 (다음 날 중복 방지)
```

- **카드 흐름**: 1장 궁금증(답 안 줌) → 2장 공감·통념 → 3~4장 반전과 근거(숫자·실험) → 용어 카드 1장(쉬운 뜻 + 일상 예시) → 결론 + 댓글 질문. 게시글 끝에는 카드에서 남겨둔 질문으로 뉴스레터 예고.
- **주제 고르기**: 매번 후보 5개를 공감·궁금증·반전·댓글성으로 점수 매겨 가장 높은 것을 고름.
- **주제 다양화**: 카테고리는 날짜로 연애심리 → 심리학 → 에니어그램 순환, 접근 방식(최신 연구 / 고전 실험 / 책 / 통계 / 작품·현상 읽기 / 통념 뒤집기)은 최근 4번과 겹치지 않게 무작위. 최근 60개 주제는 피하도록 지시.
- **댓글 유도**: 게시글 마지막에 자기 썰·유형 경험을 꺼내게 하는 질문 1개, 표지에 유형 알약으로 에니어그램 독자 끌어들이기.
- **정확성**: 원문에서 확인한 숫자만 쓰고, 디스코드 마지막 메시지에 대조할 숫자·원문 링크 목록을 같이 보냅니다. 올리기 전 확인은 사람이 합니다(자동 업로드 없음).

## 설치 (한 번만)

1. 이 폴더를 GitHub 저장소로 올립니다(비공개 권장).
2. 디스코드 채널 → 채널 편집 → 연동 → 웹후크 → 새 웹후크 → **웹후크 URL 복사**.
3. [Claude Console](https://platform.claude.com) 에서 **API 키** 발급.
4. GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret
   - `ANTHROPIC_API_KEY`
   - `DISCORD_WEBHOOK_URL`
5. Actions 탭 → 「매일 아침 카드뉴스」 → **Run workflow** 로 한 번 시험 실행.

이후 매일 자동 실행됩니다. GitHub 예약 실행은 서버 사정으로 몇 분~수십 분 늦을 수 있어요.

## 로컬 실행

```bash
pip install -r requirements.txt
python -m playwright install chromium
python main.py --deck samples/sample_deck.json --no-discord   # 샘플 덱 렌더만
python main.py                                                 # 전체 (API 키·웹후크 필요)
```

결과는 `output/날짜_주제/` 에 저장됩니다 (`card_*.png`, `deck.json`, `community_post.txt`, `instagram_caption.txt`, `research_notes.md`).
카드 문구를 손보고 싶으면 `deck.json` 을 고친 뒤 `python main.py --deck output/…/deck.json` 으로 다시 렌더하면 됩니다.

## 디자인 수정 위치

| 바꾸고 싶은 것 | 파일 |
|---|---|
| 색·유형 고정색·유형 이모지 | `bot/config.py` (`COLORS`, `TYPES`) |
| 카드 레이아웃·글자 크기 | `bot/render.py` (`CSS`) |
| 카피 규칙·톤·주제 기준 | `bot/generate.py` (`RESEARCH_SYSTEM`, `COMPOSE_SYSTEM`, `LENSES`) |
| 게시글 형식 | `bot/discord.py` (`community_post`) |

**아직 확정 안 된 유형색 (1·3·6·7·8번)** 은 `bot/config.py` 에 임시값(`confirmed: False`)으로 들어 있습니다:
1번 청록 `#63E6BE`, 3번 주황, 6번 연두 `#A9E34B`, 7번 노랑, 8번 분홍 `#F783AC`. 확정되면 그 표만 바꾸면 모든 카드에 반영돼요.

## 텍스트 마크업 (deck.json)

| 표기 | 결과 |
|---|---|
| `[[단어]]` | 제목 형광펜 (카드당 한 군데, `highlight_color`: yellow/orange/green) |
| `{t4}` | 「🎨 4번」 유형 알약 (배경 = 4번 고정색) |
| `{{단어}}` | 결론 네이비 박스 안 노랑 글자 |
| `\n` | 줄바꿈 |

카드 패턴: `cover`(표지) · `compare`(나란히 비교) · `vs`(VS 원형) · `chips`(그룹 칩) · `list`(아이콘 리스트) · `stat`(큰 숫자) · `term`(용어 설명) · `conclusion`(결론 + 댓글 질문).
글자가 박스를 넘치면 자동으로 줄이고, 그래도 넘치면 디스코드에 ⚠️ 경고를 같이 보냅니다.

## 비용

하루 1회, Claude Opus 5.5 (웹 검색 최대 8회 + 원문 확인 최대 6회) 기준 대략 하루 몇백 원 수준입니다. 정확한 금액은 Console 사용량에서 확인하세요.

## 폰트

`fonts/` 의 검은고딕(Black Han Sans)·본고딕(Noto Sans KR)은 SIL Open Font License 로 배포되는 Google Fonts 입니다.
