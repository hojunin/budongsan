# 부동산 인사이트 구현 보고서

2026-11-07 · 브랜치 `codex/real-estate-content-design` · 최초 기준 `07fbae8`

구현 커밋: `1fd542f90febe37098ceab229c974a7b66c94fd4` · 이 보고서가 포함된 최종 커밋은 `git log -1`로 확인한다.

## 현재 구현

- 홈에서 매수 판단, 가격 전망, 시장 인식, 정책 반응의 네 질문으로 진입한다. 전망은 서울·6개월에 대해 판단 유보 사유, 관측과 미확인 근거, 재검토 조건을 분리한다. 정책 의견·인과효과와 미확인 전망은 만들지 않는다.
- `매매와 임대 비교`에서 같은 면적대·최근 완결 6개월의 단지별 Q25/중간/Q75, 집값 상한선·상한 이하 거래, 59/84㎡대 비교, 두 기간의 ㎡당 가격 분포와 거래수, 주소 확인 후 매매/전세 집단, 선택한 임대계약의 원값과 가정 환산 월비용을 표시한다. 단지별 n<5, 기간별 n<30은 해당 분포를 비운다. 선택은 최대3개이며 강제 초과도 차단한다. 합성·월세 미상 거래는 새 관측에서 제외한다. 날짜 경계는 서울 달력의 월을 선택한 UTC 자정이다.
- 단지 연결은 이름·동 기반으로 **탐색용**이다. 실제 동일 단지 식별과 요청 지역×월 partition 완결성은 아직 보증하지 못한다. 확인 체크는 선택 단지·면적이 바뀌면 초기화한다. 현재 매물, 승인 가능성이나 보증 안전성으로 해석하지 않는다.
- `내 조건으로 보기`는 사용자 가정의 거래 후 현금과 세후 월 잔여, 금리·소득 충격을 계산한다. 확실한 잔금 전 보증금 반환과 가격하락 평가를 선택할 수 있으며 평가는 현금 손실과 분리한다. 입력 변경 시 이전 결과를 무효화하고 극소 금리는 안정적으로 계산한다. 개인 입력은 브라우저 메모리에서만 계산하며, 결과를 내보낼 때만 선택한 최대3개 항목을 미리 보고 저장한다. 대출 승인·정책 적격 판정은 하지 않는다.
- 지역별 선 색은 선택 순서와 독립적인 이름 기반 색이며 상승·하락의 빨강/파랑은 별도 의미색으로 분리했다. Slate·Teal 토큰, 공용 필터와 다크 모드, 축 글자 및 모바일 표 대안을 적용했다. 이름이 같은 서로 다른 지역을 구분하는 **공식 지역 ID 기반 색 매핑은 남아 있다.**
- MOLIT 응답의 업무/HTTP 오류, 페이지 건수, 요청 범위와 날짜·금액·면적을 검증한다. KB는 성공한 시도 partition만, R-ONE은 응답된 지역만 원자 교체한다. 월세 미상과 직거래 미상을 0/중개로 바꾸지 않는다. 로더 코드 변경 시 오래된 정규화 캐시를 빌드에서 무효화한다. 기존 제공기관 응답의 전체 DTO·단위·범주 완결성 및 실제 운영 API 호환성은 별도 확인이 필요하다.

## 근거와 리포트

비교 화면은 선택한 매매 분포, 기간 비교, 임대계약을 근거 초안 JSON으로 저장한다. 주간 초안은 확보된 R-ONE 가격·수급, 최근 완결월 거래와 전세 분포도 출처별 날짜·범위를 유지하며 담는다. 지역의 지표가 없으면 광역 자료를 광역 배경으로 구분한다. 없는 근거는 `자료 없음`으로 남긴다.

로컬 `scripts/new_report.py`는 주간·매수·임대 템플릿의 근거 블록, 고정 숫자·단위·기간·표본·출처, 웹 HTML, 모바일 SVG, 요약 텍스트와 1080×1350/1600×900 SVG를 하나의 manifest로 고정한다. 출력 이미지는 근거별 페이지로 나누며 출처·조건·가정을 포함한다. 임대 이미지의 같은 단위 막대는 공통 척도를 쓴다. 사용자 글은 Observable 코드에 삽입하지 않고 JSON 데이터로 렌더링한다. 파일·읽기 코드 변조는 다음 빌드에서 거부한다.

고정 리포트 패키지는 합성 여부·partition 완결성·단지 식별·이용권을 검토하기 전 생성이 차단된다. 검토자는 확인 결과를 기록해야 한다. **확인 플래그는 운영자의 진술이며 권리나 데이터 완결성을 자동 증명하지 않는다.** 같은 출처의 다른 release 혼합, 미확인·합성 근거, 잘못된 표본/분위수, 중복 지표, 임대 환산 불일치는 거부한다. `prepare`는 검증된 패키지와 데이터 전용 페이지를 로컬 `src/reports`에 연결해 다음 빌드의 목록에 포함한다. 배포 자체는 하지 않는다. 공개 배포 명령에는 합성/미상 거래·임대·KB Parquet 차단 검사를 추가했다.

운영 예시(검토된 초안과 개인 파일은 사용자가 별도로 준비):

```bash
.venv/bin/python scripts/new_report.py create evidence-draft.json content/drafts/example
.venv/bin/python scripts/new_report.py verify content/drafts/example
.venv/bin/python scripts/new_report.py prepare content/drafts/example example-report
# 개인 결과는 기본 제외. 사용자가 도구에서 선택·미리보기 후 저장한 파일만 명시적으로 포함한다.
.venv/bin/python scripts/new_report.py preview personal-scenario.json
.venv/bin/python scripts/new_report.py create evidence-draft.json content/drafts/example-personal --include-scenario --scenario-file personal-scenario.json
```

포함한 개인 결과는 패키지와 내보낸 이미지에 기록되므로 공유 전 사용자가 내용을 확인해야 한다. 예약 발행, 자동 발송, 다중 작성자 제작실, 정정 revision/승인 이력과 실제 배포는 구현하지 않았다.

## 인사이트별 상태

`부분`은 실행 가능한 관측·도구가 있으나 설계 전체나 데이터 품질 게이트가 완성되지 않았다는 뜻이다. `보류`는 명시한 원천/이력/권리 조건이 없다는 뜻이다.

| ID | 상태 | 현재와 남은 일 |
|---|---|---|
| I01 | 부분 | 기간별 거래수·㎡당 중간값과 분포; partition 완결 및 4분면 그래픽 남음. |
| I02 | 미구현 | 식별된 고정군·가중치·매칭률 검증. |
| I03 | 부분 | 양기간 Q25/중간/Q75와 n; 상대 구간 폭 변화와 완결성 검증 남음. |
| I04 | 보류 | 기존 36개월 이력은 필요한 직전60개월을 보장하지 못함. |
| I05 | 부분 | 59/84 면적별 중간 총액·㎡당 원값·표본과 선; 동일 단지 식별 및 실제 면적 범위 검증 남음. |
| I06 | 부분 | 주소 확인 후 매매·전세 중간값/표본/비율과 그래픽; 이름 매칭 및 완결성 검증 남음. |
| I07 | 미구현 | 같은 보증금 구간의 양기간 표본·분포·구성비. |
| I08 | 부분 | 최대3건의 보증금·월세 원값, 명시 가정 환산 표·막대; 산점도와 계약군 비교 개선 남음. |
| I09 | 부분 | 같은 축의 분포·상한선·거래 비중과 표본 게이트; 지역×월 완결·단지 식별 검증 남음. |
| I10 | 미구현 | 공식 집계 분자/분모와 범주 완결성 확인. |
| I11 | 미구현 | 연령별 집계 분자/분모와 범주 완결성 확인. |
| I12 | 미구현 | 공식 조사와 실거래의 범위·시점 독립 비교. |
| I13 | 부분 | 직거래/중개/미상 보존; 민감도 비교 남음. |
| I14 | 부분 | 오류·부분 수신 방어와 지역별 보존; partition 완결 이력과 독자 상태표 남음. |
| I15 | 부분 | 사용자 금리 가정의 상환 충격; 공식 금리 원천과 독립 민감도 차트 남음. |
| I16 | 보류 | 공급 원천의 응답·범위·이용권 미확인. |
| I17 | 보류 | 미분양 원천의 응답·범위·이용권 미확인. |
| I18 | 보류 | 인구·세대 원천 및 지역 매핑 미확인. |
| I19 | 보류 | 청약 원천·단지 식별·이용권 미확인. |
| I20 | 보류 | 세대수 분모·단지 매핑 미확인. |
| I21 | 부분 | 세후 현금흐름·금리/소득 충격·보증금 반환·비현금 평가; 상환방식은 원리금균등만 제공, 실제 승인·적격은 별도. |
| I22 | 미구현 | 6/12개월 순저축과 반환 시점별 매수 대기 엔진. |
| I23 | 부분/보류 | 관측과 판단 유보를 제시; 작성자 검토 전망과 전망 조사/반대 근거는 없음. |
| I24 | 미구현 | release 이력·정정과 견해 재검토 비교. |
| I25 | 부분/보류 | 기존 R-ONE/KB 수급·조사 경로 연결; 출처별 응답대상·문항·권리와 신규 조사 검증 남음. |
| I26 | 보류 | 공통 지역·시점의 검증된 전망 및 성숙한 사후 관측 이력 부재. |
| I27 | 보류 | 외부조사 이용권과 사이트 응답 동의·보관·삭제·중복 정책 미확정. |
| I28 | 보류 | 공식 정책 버전·시행/경과조치 및 성숙 관측창 구조화 미완료. |

## 검증과 증거

실제 API 수집·크롤링·배치·원본 DB 쓰기/삭제·외부 발송·배포는 수행하지 않았다. 부모 세션이 원본 DB를 읽기 전용으로 실행한 정규화 결과(매매 597,180행, 임대 248,775행, 샘플 0)를 로컬 생성 캐시에 복사해 최종 빌드했다. 이 검사는 원격 응답·이용권·수집 완결성을 검증하지 않는다.

```bash
PATH="$PWD/.venv/bin:$PATH" python scripts/test_fetch_molit.py
PATH="$PWD/.venv/bin:$PATH" python scripts/test_fetch_rone.py
PATH="$PWD/.venv/bin:$PATH" python scripts/test_partition_preservation.py
PATH="$PWD/.venv/bin:$PATH" python scripts/test_normalization.py
PATH="$PWD/.venv/bin:$PATH" python scripts/test_loader_cache.py
PATH="$PWD/.venv/bin:$PATH" python scripts/test_public_data.py
PATH="$PWD/.venv/bin:$PATH" python scripts/test_report_package.py
node scripts/test_personal.mjs
node scripts/test_graphics.mjs
node scripts/test_colors.mjs
node scripts/test_format.mjs
PATH="$PWD/.venv/bin:$PATH" OBSERVABLE_TELEMETRY_DISABLE=true npm run build
PATH="$PWD/.venv/bin:$PATH" python scripts/verify_public_data.py
PATH="$PWD/.venv/bin:$PATH" python scripts/test_report_site.py
CLS_BASE_URL=http://127.0.0.1:8766 node scripts/test_personal_export_ui.mjs
CLS_BASE_URL=http://127.0.0.1:8766 node scripts/test_identity_ui.mjs
CLS_BASE_URL=http://127.0.0.1:8766 node scripts/test_review_ui.mjs
AGENT_BROWSER_SESSION=terra-implementation CLS_BASE_URL=http://127.0.0.1:8766 node scripts/check_ui.mjs
AGENT_BROWSER_SESSION=terra-implementation CLS_BASE_URL=http://127.0.0.1:8766 node scripts/check_chips.mjs
node scripts/check_cls_report.mjs docs/reports/assets/2026-11-07-cls.json
```

위 테스트와 15페이지 빌드가 통과했다. 빌드에 기존 `cleanUrls` deprecated 경고가 있다. `test_report_site.py`는 격리 임시 사이트에서 합성 주간/매수/임대 fixture의 생성→검증→준비→목록/빌드→브라우저 읽기, null 표본 표시, 사용자 입력 `${1+1}`의 비실행, 이미지/내보내기를 확인한다. 이 fixture는 공개 발행물이 아니다. UI 테스트는 320/390/1440 × light/dark의 개인·비교·전망 18조합과 키보드 설명/계산, 입력 무효화, 명시적 시나리오 미리보기, 단지 확인 초기화·선택 상한을 확인했다. 기존 6개 화면의 18개 너비 검사와 일반·reduced-motion 상태의 칩 삭제 검사도 통과했다.

390×844, DPR3, CPU 4배 저속, 9Mbps/50ms, 브라우저 캐시 비활성 조건에서 15개 공개 경로를 각3회 측정했다. 입력 영향이 남지 않도록 각 이동 전 빈 페이지에서 800ms 대기했으며 필터 변경·칩 삭제도 프로그램으로 실행했다. [측정 수치](assets/2026-11-07-cls.json)를 `check_cls_report.mjs`로 검사한 결과 표준 초기/전체 CLS의 최대값은 **0.00358258**로 로컬 기준 0.01 이하였다. 최종 빌드의 개인·비교·리포트 화면은 각3회 표준 초기 CLS 0이다. 개인 화면은 최근 입력으로 제외된 원시 layout-shift 0.0019407이 각1회 있었고, 비교·리포트는 초기 원시 shift가 없었다. 나머지 12개 경로는 부모 세션의 직전 빌드 측정치를 사용했으며, 최종 정규화 캐시 교체 후 전체 12개를 반복하지는 않았다. CLS는 390px 조건의 결과이며 320/1440px의 CLS 수치는 측정하지 않았다.

스크린샷: [다크 비교 화면](assets/2026-11-07-compare-dark-390.png), [개인 도구](assets/2026-11-07-personal-390.png), [합성 출력물 390px 미리보기](assets/2026-11-07-synthetic-exports-390.png). 스크린샷은 실제 사용자 테스트나 접근성 인증이 아니다. 실제 iOS Safari·VoiceOver, 전체 키보드 경로, 신규 원천의 실응답/권리, 운영 데이터 partition 완결성은 확인하지 않았다.
