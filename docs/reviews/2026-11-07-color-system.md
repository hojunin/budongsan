# 부동산 인사이트 — 컬러·브랜드·디자인 시스템 리뷰

검토: 2026-11-07. 배포 사이트 홈·시장 지표·실거래·예산, 1440×1000 및 390×844. `agent-browser --session design-review-system` 독립 세션으로 light/dark 전환. `src/style.css`, `src/components/ui.js`, `src/components/charts.js` 직접 확인. 구현·배포·커밋 없음.

## 판단

현재 문제는 색의 취향보다 **브랜드, 조작, 방향성, 지역 구분이 같은 색을 공유하는 것**이다. 테라코타를 다른 유행색으로 일괄 치환하면 혼란이 유지된다. 권장 방향은 차분한 slate 중립면 + teal 한 가지 조작색, 상승/하락 전용 의미색, 고정된 비교 시리즈색이다. 차트 안의 필요한 다색은 유지하고 UI 장식색을 줄인다.

## 실제 관찰 8개

1. **P1 — 색의 의미가 중첩된다.** 테라코타가 로고/현재 메뉴/기간 선택/슬라이더/거래·가격 chip/상승 수치/차트 첫 시리즈에 모두 쓰인다. 홈의 하락 인사이트에는 파란 왼쪽 선과 테라코타 “거래” chip이 한 카드에 붙는다. 카테고리 chip은 중립색, 상승·하락만 독립 의미색, 선택 상태만 teal로 분리한다.
2. **P1 — 같은 지역의 색이 페이지마다 바뀐다.** 홈 3년 차트는 서울=테라코타·경기=파랑·전국=초록, 시장 지표 기본 선택은 경기=테라코타·서울=파랑·수도권=초록이다. `charts.js`가 고정 PALETTE를 순서로 배정하기 때문이다. 지역 ID→색/선형 고정 매핑을 공용으로 두고 선택 순서를 바꿔도 유지해야 한다.
3. **P1 — 출처·기준일이 너무 희미하다.** `.insight-meta`, `.article-meta`, `.as-of`에 faint가 쓰여, 실제로 가장 신뢰 판단에 필요한 기준일이 약하다. light `#8A8F98`/white는 **3.25:1**, dark `#7D838D`/card `#1C1F24`는 **4.33:1**. 일반 크기 AA 4.5에 못 미친다. 보조 정보도 본문보다 작은 경우 최소 4.5를 확보한다.
4. **P1 — light accent 자체도 소형 텍스트에 부족하다.** `#C8553D`/white는 **4.35:1**이며 옅은 accent chip 배경에서는 더 낮다. `ui.js`의 “라이트/다크 모두 대비 확인한 값” 주석이 충분한 보장이 아니다. dark 활성 pagination의 white/`#E27A62`도 **2.92:1**이므로 실제 표 해당 상태를 후속 검증해야 한다(코드 기반 위험, 해당 pagination 상태 직접 검사 안 함).
5. **P2 — KPI 위의 번갈아 나오는 24px 색 막대는 의미가 없다.** 예산에서 대출·현금·여유·상환에 동일하게 red/blue가 교대하며 실제 수치 상태와 상관없다. 실거래의 음수 변화에도 카드 상단 막대와 내용 방향은 별개다. 막대 삭제, 수치·단위·비교기간을 우선한다. 차트의 시리즈와 연결된 카드일 때만 같은 색 표식을 허용한다.
6. **P2 — dark UI와 차트 색의 조정 범위가 다르다.** CSS action은 dark에서 밝아지지만 `PALETTE` 6색은 hex 고정이다. light와 dark 사이에서 선이 상대적으로 약해진다. 원래 첫 두 선은 dark card 대비 3.79/3.01:1로 경계에 가깝고, 애니메이션·교차선·회색 그리드가 더해지면 판독이 약해진다. theme별 시리즈 토큰, 2px 이상 선, 선형/끝점 라벨을 병용한다. 3:1을 간신히 넘는 사실을 AA 위반이라고 단정하지 않는다.
7. **P2 — 모든 박스가 비슷한 강조도를 가진다.** sidebar 활성, 큰 필터 카드, 18px 둥근 KPI, chart 카드, 그 안의 insight 카드가 동시에 테두리·라운드·여백으로 강조된다. 홈은 카드 안의 카드가 길게 반복된다. 큰 분석 단위만 surface card, 인사이트는 divider row, 기간 필터는 compact toolbar로 정리한다. 모바일에서 KPI의 고정적인 높은 빈 공간도 줄인다.
8. **P2 — 장식 문구와 조작 설명이 정보 위계를 차지한다.** 매 페이지의 “부동산 인사이트 / DATA DESK”는 sidebar 브랜드와 중복된다. 삭제하고 H1→한 줄 목적→기준일/출처 순서로 만든다. `heading()`의 기존 정보 아이콘/팝오버는 재사용해 지수 정의·방법론을 옮긴다. 단, 데이터 기준일·정상거래/취소 포함 여부·예산 주요 가정은 숨기지 않는다. 긴 “복사를 누르면…” 안내는 복사 버튼 tooltip/첫 사용 안내로 축약한다.

## 하나의 권장 시스템: Slate + Teal

| 역할 | Light | Dark | 적용 |
|---|---|---|---|
| 대표/브랜드 | #0F766E | #5EEAD4 | 브랜드명, 현재 위치의 작은 표시 |
| action | #0F766E | #5EEAD4 | primary button, 링크, 선택, 슬라이더 |
| on-action | #FFFFFF | #102A2A | 채운 action 위 텍스트 |
| action subtle | #E6F4F1 | #163B38 | 선택 배경; 텍스트는 action |
| secondary action | #475569 | #CBD5E1 | 중립 outline 버튼/복사/초기화; 제2의 브랜드색 추가 안 함 |
| focus | #0F766E | #5EEAD4 | 3px ring + 2px offset, 선택 border와 구별 |
| 상승 | #B42336 | #FF9AA5 | ▲, +%, “상승” 함께 표기 |
| 하락 | #1D4ED8 | #93C5FD | ▼, −%, “하락” 함께 표기 |
| 경고/오류 | #B45309 | #FBBF24 | 주의 아이콘 + 설명. 취소/검증오류는 label로 명확히 구분 |
| 긍정/충족 | #15803D | #86EFAC | 체크 + “가능/조건 충족”; 가격 상승과 구분 |
| canvas | #F8FAFC | #10181C | 페이지 바닥 |
| surface | #FFFFFF | #172125 | 카드/팝오버 |
| surface inset | #F1F5F9 | #1D2B30 | 필드/표 header |
| text primary | #0F172A | #F1F5F9 | 제목/핵심 수치 |
| text secondary | #475569 | #CBD5E1 | 본문/라벨 |
| text meta | #64748B | #A5B4BE | 출처/기준일/축 |
| border decorative | #E2E8F0 | #31434A | 카드/표 divider; 상태 구분 수단으로 단독 사용 금지 |
| border control | #64748B | #708C99 | 입력/드롭다운 경계, 3:1 검증 대상으로 별도 관리 |

색 사용량 목표: 분석면적 기준 중립 85–90%, action ≤5%, semantic은 변화값/상태에만, 나머지 시리즈색은 plot 영역에 한정. 비율은 지침이며 차트 정보를 억지로 단색화하지 않는다. 모든 링크에 무조건 teal을 쓰지 말고 뉴스 제목은 primary text + hover underline을 유지한다.

### 비교 데이터 팔레트

범주 비교는 semantic red/blue와 별도 역할이다. 6색 상한은 장식 목적이 아니라 동시에 비교할 범주의 수를 제어하기 위한 기본값이다.

| 시리즈 | Light | Dark | 보조 구분 |
|---|---|---|---|
| 서울 / series 1 | #4F46E5 | #A5B4FC | solid + circle |
| 경기 / series 2 | #0E7490 | #67E8F9 | dashed + square |
| 수도권 / series 3 | #A16207 | #FCD34D | dotted + triangle |
| 전국 / series 4 | #475569 | #CBD5E1 | dash-dot + diamond |
| 기타 1 / series 5 | #A21CAF | #F0ABFC | solid + square |
| 기타 2 / series 6 | #4D7C0F | #BEF264 | dashed + triangle |

지역색은 공용 ID mapping으로 고정. 면적대는 별도 domain의 고정 순서 매핑. 선택 항목이 빠졌다고 다음 색을 당겨 쓰지 않는다. 예산은 지역색 대신 필요 현금=series1, 대출=series2, 월 상환=series3로 명시하고 다른 축 단위도 선 끝/축명으로 구분한다. 단일 핵심 지표 선은 action teal, 여러 지역 비교에서는 action teal을 강조 선택색으로 재사용하지 않는다. Tooltip은 이름·값·단위·기준일을 문자로 제공한다. 가능하면 선 끝 이름, 범례 marker, 선형, 키보드 접근 가능한 데이터 표를 함께 제공한다. 색만으로 상승/하락/선택/충족을 전달하지 않는다.

### 대비 검증

WCAG 상대휘도 공식으로 hex 쌍 계산, 일반 텍스트 4.5:1 / 큰 글자 3:1 / 의미 있는 비텍스트 3:1 기준. 제안 light action/white **5.47**, secondary/white **7.58**, meta/white **4.76**, meta/canvas **4.55**. 제안 dark action/surface **11.08**. 상승·하락·경고·긍정은 light white 배경에서 각각 **6.49 / 6.70 / 5.02 / 5.02**, dark surface에서 **8.13 / 9.09 / 9.82 / 11.68**. 이는 단색 pair 계산이며 opacity·tint·disabled·hover·focus와 실제 브라우저 전수 접근성 검증은 후속 작업이다.

## 최소 토큰과 적용 범위

- Typography: 기존 Pretendard 유지. body 14px/1.6 desktop, 14px/1.6 mobile. H1 32/40 desktop·28/36 mobile, section 20/28, card title 16/24, label/meta 12/18, KPI 28/34·24/30. 숫자 tabular-nums 유지. 축 11–12px; 현재 10px 축/11px 범례보다 읽기 쉽게. 조작 input은 16px 유지해 iOS 확대 방지.
- Weight: body 400, label 500, title 650, KPI 700. 촘촘한 본문 전체 semibold를 피한다.
- Spacing: 4, 8, 12, 16, 24, 32, 48. desktop card 24, mobile 16, card gap 24/16, 필터 내 gap 12, label→input 8. KPI 높이는 내용과 padding으로 정하고 숫자 대비 불필요한 180px 최소높이는 재검토한다.
- Radius: field/button 8, card 12, pill 999(선택 chip에만). 폼·표·KPI마다 5/6/7/9/10/12/14/18이 혼재하는 현재 상태를 축소한다.
- Border/shadow: 1px; 기본 card shadow 없음, popover만 `0 8px 24px #0002`. dark도 같은 정보 위계로 surface contrast를 사용한다.
- Touch: 주요 버튼/필드 hit area 44px. 차트 info 시각 아이콘 16px 유지하되 hit area 44px; 현 summary 28/32px은 확대. tooltip만으로 의미 제공하지 않고 accessible name과 펼침 상태 제공.
- 적용 범위: style.css tokens→ui.js card/heading/chip→charts.js axes/legend/tooltip/series→공용 table/filter controls→개별 페이지에서 직접 지정한 series/semantic 색 순서. 토큰 교체만 하면 PALETTE와 개별 옵션은 남으므로 반드시 함께 감사해야 한다.

## 우선순위와 증거

1. P1: 출처·기준일·작은 accent 문자 대비, action/상승/하락 분리, 지역색 mapping 고정.
2. P2: 의미 없는 KPI 막대·DATA DESK 삭제, 카드 계층과 type/spacing/radius 정규화.
3. P2: theme별 시리즈 + 선형/라벨, 상태 전체와 keyboard/색각 확인.

확정 시각 증거: `docs/reviews/evidence-color-system/home-desktop-light.png`, `/tmp/ds-home-light.png`(이름과 달리 초기 시스템 dark), `/tmp/ds-home-mobile-light.png`, `/tmp/ds-home-mobile-dark.png`, `/tmp/ds-market-mobile-light.png`, `/tmp/ds-market-mobile-dark.png`, `/tmp/ds-budget-ready.png`, `/tmp/ds-budget-mobile-light.png`. 시장·실거래·예산의 일부 초기 desktop 캡처는 reactive/animation 도중이므로 빈 카드나 흐림을 제품 결함으로 세지 않았다. `/tmp/ds-*-ready.png`도 DOM 생성 직후 애니메이션이 남을 수 있어 opacity 판정에는 쓰지 않았다. 구조·색의 매핑은 안정된 home/market mobile 캡처와 소스에서 확인했다.

미실시: DS 구현, 배포, 전체 hover/disabled/표 pagination 직접 검사, 색각 시뮬레이션, 실제 모바일 기기. 위험: hex 대비값만 통과해도 얇은 교차선·opacity·렌더링의 실제 가독성이 보장되지는 않는다.
