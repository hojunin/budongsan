# 부동산 인사이트 — 설계서

부동산 데이터를 한곳에 모아 **조사원(리포트), 기자(기사), 인플루언서(이슈 발행)** 의 일을 하는 정적 사이트다.
실거래·공식 지수·설문 지표를 쌓아 문장형 인사이트로 바꾸고, 다른 사람이 쓴 기사와 리포트도 모아 보여 주며, 그 위에 내 리포트를 써서 발행한다.
처음에는 신혼 첫 집 매수 판단용으로 시작해서, 타겟 단지·예산 계산기는 '도구'로 남겨 두었다.

## 1. 설계 원칙

| 원칙 | 구체적으로 |
| --- | --- |
| 가볍게 | 서빙 서버 없음. 로컬 배치가 원본을 DuckDB 파일에 쌓고, 빌드 때 Parquet으로 구워서, 브라우저의 DuckDB가 그 파일을 직접 질의한다. |
| 커스텀 | 지역(서울 전체·경기 전체·경기 시 전체·시군구), 평형, 기간, 단지를 화면에서 고른다. 고를 때마다 브라우저에서 SQL이 다시 돈다. |
| 가독성 | 화면마다 핵심 숫자 4개(KPI 카드) → 큰 차트 → 보조 차트 순서. 한 차트에는 한 가지 질문만 담는다. 숫자는 `억/만` 단위로 표기한다. |
| 모던 UI | Pretendard 가변 폰트, 카드형 레이아웃, 라이트/다크 자동 전환, 차트 툴팁. |
| 모바일 | 1열 재배치(860px 이하 2열 KPI, 640px 이하 1열), 터치 타깃 44px 이상, 입력 글꼴 16px(iOS 확대 방지), 차트는 화면 폭에 맞춰 다시 그림(`resize`), 표는 가로 스크롤. |
| 정직하게 | 샘플 데이터면 배너, 최근 1개월(신고 지연)은 추세에서 제외, 해제 거래는 가격 통계에서 제외. |

## 2. 기술 선택

**Observable Framework** (정적 사이트 생성기, MIT).

- **가벼움**: 결과물이 순수 HTML/JS/Parquet. Cloudflare Pages에 그대로 올라간다.
- **라이브러리**: Observable Plot, D3, Inputs, DuckDB-wasm, Arquero, Apache Arrow를 import 없이 바로 쓴다. npm 패키지도 `npm:` 로 불러온다.
- **데이터 로더**: `src/data/*.parquet.py` 같은 파일을 빌드 때 실행해서 결과를 정적 파일로 만든다. 파이썬(PublicDataReader)을 그대로 쓸 수 있다.
- **반응형 입력**: `view(Inputs.select(...))` 값이 바뀌면, 그 값을 쓰는 쿼리와 차트만 다시 계산된다.

검토했지만 고르지 않은 것: Astro/Next(차트·데이터 계층을 직접 조립해야 함), Evidence(SQL 중심으로 좋지만 커스텀 UI 자유도가 낮음), Streamlit(서버 필요).

## 3. 아키텍처

```
로컬 Mac 배치 scripts/batch.sh (launchd, 매주 월요일 09:17)
  ├─ scripts/fetch_molit.py   국토부 매매(서울·경기 69개 시군구), 전월세(관심 단지 시군구), 최근 10년
  │                            → data/apt.duckdb (molit_trade, molit_rent, fetch_log). 받은 달은 건너뛰고 최근 3개월만 교체
  ├─ scripts/fetch_kb.py      KB 전세가율, 매수우위·거래활발지수 → kb_* 테이블(매번 교체). 가격지수는 KB가 자동 접근을 막아 R-ONE으로 대체
  ├─ scripts/fetch_rone.py    한국부동산원 R-ONE 주간·월간 지수, 수급, 중위가격, 전월세 전환율, 매입자 거주지·연령대 → rone 테이블
  │                            (첫 실행 최근 10년, 이후 표마다 마지막 4개 시점부터 다시 받음)
  ├─ scripts/fetch_news.py    Google 뉴스 RSS 검색 + 언론사 RSS → articles 테이블 (제목·언론사·날짜·링크만, url 기준 upsert)
  ├─ wrangler r2 object put   data/apt.duckdb → R2 apt-insight-backup/apt-YYYY-MM.duckdb
  ├─ observable build         src/data/*.py 로더가 DB에서 화면용 파일을 만든다
  │                            trades/rents(최근 36개월 거래), trend(10년 월별 집계), rone, kb, articles, insights(문장형 사실)
  └─ wrangler pages deploy    dist/ → Cloudflare Pages
GitHub Actions (push·PR)
  └─ 샘플 데이터로 빌드·크기 검사만 (배포하지 않음)
브라우저
  └─ DuckDBClient.of({trades, rents}) → 입력값으로 SQL → Plot 차트
```

- 왜 로컬인가: 국토부 API가 해외 IP(GitHub 러너)의 연결을 자주 끊는다. 인증키도 로컬 `.env` 에만 둔다.
- 왜 DuckDB 파일인가: 서빙은 정적이라 DB 서버가 필요 없고, 출처가 늘어도 테이블로 한곳에 모인다. 원격 질의가 필요해지면 같은 SQL로 Postgres 로 옮긴다.
- 실거래 API 호출량: 최근 10년은 약 69 × 121 = 8,350건이라 API별 하루 9,000건(`MOLIT_DAILY_BUDGET`) 안에서 첫 실행에 다 받는다(약 45분). 이후 매 실행은 새 달과 최근 3개월만 받아 약 69 × 3 + 7 × 3 = 228건. 10년이 지난 달은 지우지 않고 그대로 둔다.
- DB에는 전 기간을 두고 화면에는 최근 36개월만 보낸다. Cloudflare Pages는 파일 하나에 25 MiB까지만 올라가서 배치와 CI가 크기를 검사한다. 넘으면 `SITE_MONTHS` 를 줄이거나 `trades` 를 시도별(`trades-11`, `trades-41`)로 나눈다.

## 4. 화면 구성

| 메뉴 | 페이지 | 독자 질문 |
| --- | --- | --- |
| 오늘의 브리핑 `/` | 핵심 KPI, 문장형 인사이트(복사 버튼), 3년 지수 흐름, 최신 기사·리포트 | 이번 주 시장에서 쓸 만한 숫자는? |
| 시장 분석 · 실거래 분석 `/trades` | 아래 '시장 한눈에' 표 참고 | 이 지역 거래와 가격은? |
| 시장 분석 · 10년 추이 `/longterm` | 지역별 10년 ㎡당 가격·84㎡ 가격·거래량, 5년·10년 변화 표 | 길게 보면 어디가 얼마나 올랐나? |
| 시장 분석 · 시장 지표 `/market` | 부동산원 주간 매매·전세 지수와 변동률, 수급지수, 중위가격, 전환율, KB 설문 | 시장 방향과 온도는? |
| 시장 분석 · 매수자 분석 `/buyers` | 외지인·2030·서울 거주자 매수 비중, 연령대 구성, 지역별 표 | 누가 사고 있나? |
| 뉴스·리포트 `/news` | 주제어별 기사 추이, 언론사별 기사 수, 기사 목록(필터·검색) | 지금 무엇이 이슈인가? |
| 내 리포트 `/reports/` | 발행한 글 목록과 작성 방법 | 내 해석은? |

아래는 처음 설계한 개별 페이지 상세다.


| 페이지 | 질문 | 입력 | 주요 차트·지표 |
| --- | --- | --- | --- |
| 시장 한눈에 `/` | 이 지역 시장이 지금 어떤가? | 지역 1개, 평형(복수), 기간 | KPI(최근 월 거래량, ㎡당 중위가, 12개월 변화, 신고가 비율) · 월별 거래량+해제+3개월 이동평균 · ㎡당 중위가+사분위 띠 · 신고가/직거래/해제 비율 · 평형별 최근 6개월 vs 이전 6개월 |
| 지역 비교 `/regions` | 후보 지역끼리 어디가 더 뜨겁나? | 지역 최대 6개, 지표, 시작=100 토글, 평형, 기간 | 지역별 선 그래프(끝에 라벨) · 요약 표(6개월·기간 변화, 거래량 1년 전 대비) |
| 타겟 단지 `/complexes` | 이 단지를 지금 이 값에 사도 되나? | 관심 단지 또는 지역+단지명 검색, 평형 | KPI(최근 3개월 중위, 1년 전 대비, 전세가율, 호가 괴리율) · 실거래 점(신고가·해제 색 구분)+월 중위 선+예산선(6억·9억)+기록 호가 · 최근 거래 표 |
| 시장 온도 `/market` | 매수자에게 유리한 때인가? | KB 지역 최대 4개, 기간 | 매매·전세 지수, 매수우위지수(100 기준선), 거래활발지수, 전세가율 |
| 예산 계산기 `/budget` | 이 가격이면 현금이 얼마나 필요하나? | 대출 종류, 매수가, 현금, 소득, 금리 | KPI(대출 가능액, 필요 현금, 여유/부족, 월 상환액) · 매수가별 필요 현금 곡선과 보유 현금선 |
| 데이터 사전 `/about` | 숫자를 믿어도 되나? | — | 출처, 지표 정의, 한계 |

## 5. 데이터 모델 (Parquet)

| 파일 | 한 행 | 컬럼 |
| --- | --- | --- |
| `trades.parquet` | 매매 1건 | deal_date, ym, sido, sgg, sgg_name, umd, apt, complex_key, area, band, price(만 원), ppm2(만 원/㎡), floor, build_year, canceled, direct, buyer, new_high, is_sample |
| `rents.parquet` | 전월세 1건 | deal_date, ym, sgg, umd, apt, complex_key, area, band, deposit, monthly, jeonse, is_sample |
| `kb.parquet` | 지표 × 지역 × 월 | metric, region_code, region, date, value, is_sample |
| `regions.json` | 시군구 1곳 | code(LAWD_CD), sido, sidoName, name, city — `scripts/make_regions.py` 로 재생성 |
| `watchlist.json` | 관심 단지 1곳 | id, name, match(단지명 일부), sgg, umd, track(A/B), station, commute |
| `listings.csv` | 호가 기록 1회 | date, complex_id, area_band, listing_count, min_ask, median_ask, note |

평형 구간(band): `~49`, `59`(50~66㎡), `74`(67~79㎡), `84`(80~89㎡), `100`(90~114㎡), `115+`.

## 6. 내 콘텐츠 발행

- `scripts/new_report.py "제목"` → `content/drafts/날짜-제목.md` 초안. 그 시점 인사이트(출처·기준일 포함), 최근 2주 리포트 기사 링크, 부동산원 주간 지수 차트, 내 해석·SNS 요약 자리를 채운다.
- 초안은 `src` 밖이라 사이트에 올라가지 않는다. 다 쓰면 `git mv content/drafts/x.md src/reports/` 로 옮겨 발행한다.
- 인사이트 계산(`src/data/_insights.py`)은 브리핑 화면과 초안 생성기가 같이 쓴다. 새 지표를 넣으면 두 곳에 함께 나온다.

## 7. 커스터마이즈

- **관심 단지 추가**: `src/data/watchlist.json` 에 한 줄 추가 → 다음 배치부터 그 시군구 전월세도 수집된다.
- **호가 기록**: `src/data/listings.csv` 에 날짜·단지 id·평형·호가를 적는다. 네이버 부동산은 자동 수집하지 않는다(법적 위험).
- **기간**: 수집 시작 `START_YM`(기본 실행일 기준 10년 전), 화면에 보낼 기간 `SITE_MONTHS`(기본 36) 환경변수.
- **지표 추가**: 각 페이지의 SQL에 집계 컬럼 하나를 더하고 Plot 마크를 하나 더한다.

## 8. 알려진 한계와 다음 단계

- 최근 1개월 실거래는 신고 지연으로 적게 잡힌다 → 추세에서 제외.
- KB는 공식 API가 아니어서 형식이 바뀌면 수집이 멈춘다 → 마지막 `kb_*` 테이블 유지.
- 배치는 Mac이 켜져 있어야 돈다(잠들어 있었으면 깨어난 뒤 실행). DB 파일이 약 300MB를 넘으면 R2 백업을 wrangler 대신 S3 API로 올려야 한다.
- 행정구역 변경(예: 화성시 구 신설)은 `make_regions.py` 재실행이 필요하다.
- 다음 단계 후보: ① Cloudflare Pages Functions 로 미리 굽지 않은 지역을 즉석 조회하는 프록시(인증키는 서버에만), ② 한국은행 ECOS 기준금리·주담대 금리 보조지표, ③ 관심 단지 신규 거래 알림.
