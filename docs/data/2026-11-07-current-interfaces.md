# 현재 수집기와 출력 인터페이스 — 2026-11-07

이 문서는 소스 점검 시점의 기록이며 공급자의 가용성·완전성·라이선스·서비스 수준을 보장하지 않는다. 요청 실행, 수집, 인증정보 읽기, DB 쓰기는 수행하지 않았다. 근거는 `scripts/fetch_{molit,rone,kb,news}.py`, `src/data/_db.py`, 아래 출력 로더 6개, `_insights.py`, 설치된 PublicDataReader **1.1.1.post2** 구현이다. 공급자 쿼터와 재배포 허가는 별도로 검증하지 않았다.

## 저장소와 빌드 경계

수집기는 DuckDB `data/apt.duckdb`에 쓴다. R-ONE/news와 공용 읽기 로더만 `APT_DB`를 따르며 MOLIT/KB는 고정 경로를 쓴다. `_db.query`는 읽기 전용으로 열고, DB가 없거나 DuckDB `CatalogException`이 발생할 때만 `None`을 반환한다. 다른 오류는 전파한다. `SITE_MONTHS` 기본값은 36이며 거래 원본을 `_ym >= today minus 36 months`로 월 단위 포함 필터링한다. 정확한 일수 기준 이동 구간이나 공급자의 보존 정책이 아니다.

Parquet 로더는 zstd 압축 바이트를 stdout에 쓴다. 날짜는 Parquet date32가 되며 숫자의 물리 타입은 pandas/데이터에서 추론하므로 샘플이나 빈 출력에서 달라질 수 있다. 아래 타입은 강제 스키마가 아닌 의미상 계약이다. `astype(str)`로 변환한 문자열에는 실제 null 대신 null을 나타내는 텍스트가 들어갈 수 있다. 공통 수집 감사 명세, 최신성·완전성 플래그, 행 수 검증, 정규화 출력의 강제 기본키는 없다.

## MOLIT 아파트 매매·전월세

인증: `MOLIT_SERVICE_KEY`. 키가 없으면 정상 종료하며 건너뛴다. SDK 호출: `TransactionPrice(key).get_data("아파트", "매매" | "전월세", sgg, year_month=ym, translate=False)`.

설치된 SDK의 외부 GET 요청(실제 코드는 HTTP 사용):

- 매매: `http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev`
- 전월세: `http://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent`
- 파라미터: URL 디코딩한 `serviceKey`, `numOfRows="99999"`, `LAWD_CD=<five-digit sgg>`, `DEAL_YMD=<YYYYMM>`. 이 SDK 메서드에는 명시적 `pageNo`, 페이지 순회, 타임아웃, 총 건수 확인이 없다. 요청에 `verify=False`를 전달한다(HTTP 암호화에는 의미 없음). XML `response.header.resultCode`가 `000`이어야 하며 본문 `items.item`은 단일 객체 또는 목록을 허용한다. SDK가 일부 숫자 필드를 변환한 뒤 수집기가 모든 입력 열을 nullable 문자열로 다시 바꾸므로 저장값은 바이트 단위 원본 응답이 아니다.

범위: 매매 작업은 `regions.json`의 모든 항목을 사용한다(서울·경기 최하위 구 단위 의도). 전월세는 watchlist의 고유 `sgg`를 사용하며 관심 단지 일치 여부와 무관하게 해당 구에서 반환된 모든 아파트를 수집한다. `START_YM` 기본값은 실행 10년 전 같은 달이며 이번 달까지 최신순으로 요청한다. 이는 요청 범위이며 모든 구·월 데이터가 존재한다는 증거가 아니다.

원본 테이블 `molit_trade`, `molit_rent`는 반환된 모든 열을 VARCHAR로 저장하고 `_sgg`, `_ym`을 추가한다. 새 열은 추가하지만 거래별 키·중복 제거는 없다. `fetch_log(kind,sgg,ym)`는 기본키가 있는 구·월 체크포인트이며 `rows`, `fetched_at`을 포함한다. 성공한 호출마다 해당 구·월 전체와 체크포인트를 원자적으로 삭제·교체하며 0행도 포함한다. `REFRESH_MONTHS=3`은 요청 범위의 최신 월들을 다시 받고 이전 체크포인트 구간은 건너뛰므로 범위 밖의 뒤늦은 정정·해제는 반영되지 않는다. 구·월 내부 공급자 중복 행은 유지된다. 예외 시 총 3회 시도하며 재시도 전 3/6초 대기한다. 최종 실패하면 기존 구간과 체크포인트를 유지한다. 예외 메시지의 `serviceKey`는 마스킹한다.

`MOLIT_DAILY_BUDGET=9000`은 **종류별·프로세스 실행별 로컬 호출 카운터**이며 영속 일일 사용량 장부나 검증된 공급자 쿼터가 아니다. HTTP를 3번 시도해도 논리 호출은 한 번만 증가한다. 성공 후 0.15초 대기하며 실패 후에는 이 대기가 없다. 스크립트 주석의 개발계정 10,000건/일 제한은 이 점검에서 이용 권한까지 검증한 값이 아니다.

중요한 실패 구분 문제: 설치된 SDK는 HTTP 200 이외 응답에서 항목 없음으로 반환하고 `get_data`는 이를 빈 DataFrame으로 바꾼다. 수집기가 성공으로 취급하여 기존 구간을 0행으로 교체하고 체크포인트를 남길 수 있다. 빈 오류 응답과 실제 무거래 월을 별도로 검증하지 않는다. 99,999행 요청도 완전성을 보장하지 않는다.

### `trades.parquet`

필터를 통과한 원본 매매 행마다 1행이며 해제 거래도 포함한다. 사용하는 원본 필드: `sggCd, umdNm, aptNm, jibun, excluUseAr, dealAmount, floor, buildYear, dealYear, dealMonth, dealDay`; 선택 필드 `aptSeq, cdealType, dealingGbn, buyerGbn`. `aptSeq`/`jibun`은 읽지만 출력에서는 제외한다.

| 출력 | 의미상 타입·의미 |
| --- | --- |
| `deal_date`, `ym` | date32; `YYYY-MM` 문자열 |
| `sido`, `sgg`, `sgg_name`, `umd`, `apt` | 문자열; sido는 앞 2자리, sgg는 0으로 채운 5자리, 이름 매핑이 없으면 코드 사용 |
| `complex_key` | 문자열 `sgg|umd|apt`; 이름 기반 그룹이며 공식 영속 단지 ID가 아님 |
| `area`, `price`, `ppm2` | 숫자: m², 만 원, 소수점 1자리로 반올림한 만 원/m² |
| `band` | 문자열: `[0,50)→~49`, `[50,67)→59`, `[67,80)→74`, `[80,90)→84`, `[90,115)→100`, `[115,1e9)→115+`; 나머지 `기타` |
| `floor`, `build_year` | 숫자 층·연도; 변환 실패 시 nullable |
| `canceled`, `direct`, `new_high`, `is_sample` | 불리언 |
| `buyer` | 공급자 문자열; 필드가 없으면 빈 문자열 |

파싱된 면적·가격·날짜가 없는 행은 제거한다. 날짜 구성요소의 `.astype(int)`는 `to_datetime(errors="coerce")` 이전에 예외를 낼 수 있다. 면적·가격 0이나 음수는 여기서 거부하지 않는다. `canceled`는 공백 제거 후 `cdealType == "O"`인 경우만 의미한다. direct는 `dealingGbn`에 `직거래`가 포함된 경우다. `new_high`는 동일 `complex_key,band`의 해제되지 않은 행을 **로딩된 SITE_MONTHS 구간**의 앞선 행과 비교하며 첫 관측은 false다. 같은 날짜의 행 순서가 표시 대상에 영향을 줄 수 있으며 전체 역사 신고가를 보장하지 않는다. 거래 ID나 유일성 검증은 없다.

캐시가 없거나 비었거나, 로딩된 모든 행이 필터에서 제거되면 실행 날짜 기준 고정 RNG의 합성 매매 데이터를 만들고 `is_sample=True`로 표시한다. 실제 데이터는 `False`다.

### `rents.parquet`

원본 전월세 행마다 1행이며 해제·갱신 필터와 행 중복 제거는 없다. 사용 필드: `sggCd,umdNm,aptNm,excluUseAr,deposit,monthlyRent,dealYear,dealMonth,dealDay`.

출력: 문자열 `sgg,umd,apt,ym,band,complex_key`(같은 이름 키·면적 구간), date32 `deal_date`, 숫자 `area` m²·`deposit` 만 원·`monthly` 만 원/월, 불리언 `jeonse`(`monthly==0`)·`is_sample`. 월세가 없거나 파싱 불가하면 **0**으로 바꾸므로 미상 값을 전세로 오분류할 수 있다. 잘못된 면적·보증금·날짜 행은 제거하지만 날짜 정수 변환이 먼저 예외를 낼 수 있다. 매매와 달리 음수·범위 밖 band는 pandas 결측 범주를 문자열화한다. 원본 캐시가 비면 관심 단지의 36개월 합성 전월세를 만들지만, 원본이 존재하고 모든 행이 필터에서 제거되면 빈 출력을 유지한다. 안정적인 임대차 계약 ID는 노출하지 않는다.

### `trend.parquet`와 거래 인사이트

Trend는 설명 주석과 달리 명시적 10년 필터 없이 **저장된 전체** 매매를 조회한다. `trim(cdealType)=="O"`를 제외하고 파싱된 `price>0,area>0`을 요구한다. 행 단위는 `(ym,code,level)`이며 출력 `ym`은 `YYYY-MM`, `level`은 `sgg` 또는 `sido`, code는 5자리 또는 2자리, `name`은 매핑 실패 시 코드다. `n,n84`는 정수 행 수, `ppm2_med`는 개별 가격/면적의 중위값(만 원/m²), `price_med`는 가격 중위값(만 원), `price84_med`는 `[80,90)` m² 가격의 nullable 중위값이다. 시도 통계도 원본 행에서 직접 집계한다. 데이터가 없으면 타입을 지정한 빈 파일을 내며 샘플은 없다. `cdealType` 열이 없으면 쿼리의 카탈로그 오류로 빈 출력이 된다.

`_insights.monthly`는 같은 유효성·해제 정책과 그룹을 사용하며 원래 `YYYYMM`, `code,n,ppm2,p84`를 반환한다. 거래 문장은 `max(stored month)-2`를 기준으로 전월·전년 대비를 계산하고 비교하는 두 달 모두 ≥30행인 구를 순위화한다. 이 지연은 구현상 휴리스틱이며 신고 완료의 증거가 아니다. 중위값에는 거래 구성 변화가 반영된다. 인사이트 항목은 문자열 중심의 `id,group,title,value,sub,tone,as_of,source,detail`을 가진다. 없는 출처는 건너뛰고 `build`가 출처별 예외를 잡으므로 구조화된 상태 정보 없이 일부 목록만 반환할 수 있다.

## R-ONE

인증 `REB_API_KEY`; 없으면 정상 종료하며 건너뛴다. GET `https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do`, 파라미터 `KEY,Type=json,pIndex`(1부터), `pSize=1000,STATBL_ID,DTACYCLE_CD,START_WRTTIME`, 선택 `GRP_ID`. 타임아웃 60초, 페이지당 총 3회 시도하며 재시도 전 3/6초 대기한다. `SttsApiTblData[0].head[0].list_total_count`와 `[1].row`를 읽고 누적 건수가 총 건수에 도달하거나 빈 페이지가 올 때까지 진행한다. HTTP `raise_for_status`, API 결과 코드 검증, 명시적 속도 제한 처리, 페이지 간 스냅샷 일관성 검사는 없다. 로컬 일일 예산과 성공 후 대기가 없으며 공급자 쿼터는 미검증이다.

| 지표 | STATBL_ID | 주기 |
| --- | --- | --- |
| `wk_sale_index` | T244183132827305 | WK |
| `wk_jeonse_index` | T247713133046872 | WK |
| `wk_sale_supply` | T248163133074619 | WK |
| `wk_jeonse_supply` | T245423133086632 | WK |
| `mm_sale_index` | A_2024_00178 | MM |
| `mm_jeonse_index` | A_2024_00182 | MM |
| `mm_sale_median` | A_2024_00189 | MM |
| `mm_jeonse_median` | A_2024_00193 | MM |
| `mm_conversion` | A_2024_00156 | MM |
| `mm_buyer_residence` | A_2024_00609 | MM |
| `mm_buyer_age` | A_2024_00610 | MM |

사용 원본 필드: `GRP_ID,GRP_FULLNM,GRP_NM,CLS_FULLNM,CLS_NM,ITM_FULLNM,ITM_NM,WRTTIME_IDTFR_ID,WRTTIME_DESC,UI_NM,DTA_VAL`. `GRP_FULLNM`이 nonnull이면 그룹을 지역 계층으로, 아니면 분류를 사용한다. 매입자 항목은 `CLS_NM`, 나머지는 전체 항목명이며 없으면 짧은 항목명을 쓴다. 계층 첫 부분이 정확히 `전국,수도권,서울,경기`인 행만 유지한다. 매입자 표는 먼저 최근 약 120일에서 그룹 ID를 찾고 유지할 그룹마다 요청한다. 이 발견 구간에 없는 그룹은 과거 데이터도 누락될 수 있다.

DB `rone` 열: VARCHAR `metric,cycle,period,period_desc,region,region_full,item,unit`; 변환한 nullable DOUBLE `value`. 의도한 행 단위는 `(metric,cycle,period,region_full,item)`이지만 키·중복 제거 제약은 없다. 단위는 변환 없이 `UI_NM`을 전달한다. 지수 기준, 중위가격 금액 단위, 백분율·거래 단위를 일률적으로 가정하지 말고 원천 메타데이터로 해석해야 한다. 첫 요청 시작은 `(current year-10)01`, 이후 시작은 저장된 고유 시점 중 네 번째 최신 시점이다. 수집 후 해당 지표의 시작 시점 이상을 원자적으로 삭제·교체하며 유효한 형태의 빈 결과도 해당 범위를 삭제한다. 수집 예외는 기존 지표를 유지하고 다음으로 진행한다. 겹치는 갱신 구간 밖의 과거 정정은 반영되지 않으며 삽입 실패를 감싸는 rollback 핸들러는 없다.

`rone.parquet`: 문자열 `metric,cycle,region,region_full,item,unit`, nonnull 숫자 `value`; date32 `date`는 주간 `TRY_CAST(period_desc AS DATE)` 또는 월간 period에서 파싱한 월 첫날이다. 최근 10년 날짜로 필터하며 파싱 불가한 주간 날짜는 제거된다. 잘못된 월간 period는 예외를 낼 수 있다. 샘플은 없고 테이블이 없으면 빈 출력이다. 시점 식별자·설명은 내보내지 않는다. 인사이트는 주간 지수 증감률, 수급지수 기준 100, 매입자 거주지·연령 비중, 서울 전환율을 사용한다. 해당 항목명과 예상 단위를 가정하며 지수 기준 변경 보정이나 분모 0 검증은 없다.

## SDK를 통한 KB 공개 웹 데이터

수집기에 인증 환경변수나 API 키는 없다. 설치된 `Kbland`는 공개 웹 데이터 리더이며 공식 지원 연동의 근거는 아니다. GET 엔드포인트 계약 두 가지:

- `https://data-api.kbland.kr/bfmstat/weekMnthlyHuseTrnd/dealCntstTnantRato`: `매물종별구분=01`, `지역코드=11|41` → `kb_jeonse_ratio`.
- `https://data-api.kbland.kr/bfmstat/weekMnthlyHuseTrnd/maktTrnd`: `메뉴코드=01|02`, `월간주간구분코드=01`, `지역코드=11|41` → `kb_buyer_index` 또는 `kb_trade_activity`.

SDK는 `dataBody.resultCode==11000`을 확인하고 `dataBody.data.날짜리스트`와 `지역코드,지역명,dataList`가 있는 `데이터리스트`를 사용하여 날짜(`YYYYMM` 또는 `YYYYMMDD`)를 긴 형식으로 변환한다. 시장동향은 중첩 값을 `매수자많음,비슷함,매도자많음,매수우위지수` 또는 `활발함,보통,한산함,매매거래지수`로 펼치고 메뉴·주기 라벨을 추가한다. 비율은 `전세가격비율`과 매물 종류 라벨을 만든다. GET에는 타임아웃·페이지 순회·재시도가 없고 `verify=False`를 사용한다. 요청·JSON 실패를 잡으면 `None`을 반환할 수 있다. 명시적 기간 없이 제공되는 전체 시계열을 요청하며 지역적 완전성은 미검증이다. 응답에 하위 지역이 포함될 수 있다. 공급자 쿼터 검증과 로컬 속도 제한은 없고 가격지수 엔드포인트는 의도적으로 호출하지 않는다.

지표마다 성공한 비어 있지 않은 지역 프레임을 합쳐 전체 지표를 `CREATE OR REPLACE TABLE`로 교체한다. **한 지역 실패·다른 지역 성공**이면 실패한 지역의 기존 이력이 사라진다. 모든 결과가 비거나 실패한 지표만 기존 테이블을 유지한다. 원본 응답 보관, 거래 키, 정정 이력, 중복 제거는 없다.

`kb.parquet`의 의도한 행 단위는 `(metric,region_code,date)`다. 필드는 문자열 `metric,region_code,region`, date32 `date`, 숫자 `value`, 불리언 `is_sample`. 사용하는 SDK 열은 `지역코드,지역명,날짜`; 매수 지표 값은 `매수우위지수`, 거래활동 값은 `매매거래지수`다. 비율은 **지역코드를 제외한 마지막 숫자 열**을 선택하며 다른 지표도 예상 열이 없으면 이 규칙을 사용한다. 스키마 순서에 의존하므로 다른 수치를 선택할 수 있다. 비율은 백분율, 나머지는 지수로 해석하지만 정규화나 단위·기준 메타데이터는 없다. null 값은 제거하고 잘못된 날짜는 예외를 낼 수 있다. 프레임이 하나라도 있으면 없는 지표에 샘플을 채우지 않는다. 하나도 없으면 지정된 네 지역·전체 지표의 60개월 합성 관측값을 생성한다. 날짜 구간은 SITE_MONTHS로 제한하지 않는다. KB 인사이트는 별도로 정확한 매수 지표 열과 지역명 `서울`을 요구한다.

## 뉴스/RSS

인증 없음. 피드마다 타임아웃 20초의 GET을 수행하며 재시도·페이지 순회·명시적 user agent·HTTP 상태 확인·속도 제한 처리는 없다. 응답을 feedparser로 파싱하므로 차단·잘못된 응답이 예외 없이 0개 항목이 될 수 있다. 피드 예외를 로그에 남기고 다른 피드는 계속 수집한다. 공급자 보존 정책, 재배포 권리, RSS 이용 조건, 기사 본문 권리는 **미상·미검증**이다. 현재 코드는 본문·요약 없이 헤드라인 메타데이터만 저장·표시하지만 이 설계만으로 이용 허가가 성립하지 않는다.

정확한 Google 템플릿(`quote`는 Python `urllib.parse.quote`):

`https://news.google.com/rss/search?q={quote(q)}+when:30d&hl=ko&gl=KR&ceid=KR:ko`

| 피드명 | 정확한 `q` | 초기 분류 |
| --- | --- | --- |
| Google 뉴스: 아파트 시장 | 아파트 매매 시장 | news |
| Google 뉴스: 전세 | 아파트 전세 시장 | news |
| Google 뉴스: 부동산 정책 | 부동산 대책 OR 부동산 정책 | news |
| Google 뉴스: 청약·분양 | 청약 OR 분양 아파트 | news |
| Google 뉴스: 재건축·재개발 | 재건축 OR 재개발 | news |
| Google 뉴스: 시장 전망 리포트 | 부동산 전망 보고서 OR 리포트 | report |
| Google 뉴스: 한국부동산원 동향 | 한국부동산원 주간 아파트 가격 동향 | report |
| Google 뉴스: KB 시장동향 | KB부동산 주택가격동향 OR KB경영연구소 부동산 | report |
| Google 뉴스: 국토연구원·주산연 | 국토연구원 OR 주택산업연구원 주택시장 | report |

다른 피드: `서울경제 부동산` → `https://www.sedaily.com/rss/realestate`; `아시아경제 부동산` → `https://www.asiae.co.kr/rss/realestate.htm`. 둘 다 초기 분류는 `news`다.

사용 필드: entry의 `link,title,source.title,published_parsed,updated_parsed`. 링크·제목을 요구하고 일치하는 ` - source` 접미부(출처가 없으면 짧은 끝부분)를 제거한 뒤 코드의 부동산 주제 정규식에 맞는 제목만 유지한다. report 분류는 피드 분류 또는 제목의 `보고서|리포트|전망|동향|브리핑|연구원|통계|지수` 일치로 결정한다. 이는 휴리스틱이며 원문 연구 출처 확인이 아니다. 게시 시각은 published 우선·updated 대체이며 UTC를 서울 현지 시각으로 변환한 **시간대 정보 없는** timestamp로 저장한다. 날짜가 없으면 NULL이다.

DB `articles`: 기본키 VARCHAR `url`; VARCHAR `title,source,category,feed`; nullable TIMESTAMP `published`; 현지 `Timestamp.now()`의 TIMESTAMP `fetched_at`. URL은 피드 링크로 Google 리디렉션일 수 있으며 발행사 URL 정규화는 없다. 실행 내 `drop_duplicates(url)`은 첫 피드 항목을 유지한다. 주석과 달리 뒤의 report 중복이 첫 항목을 승격하지 않는다. 기존 URL 충돌은 title/source/category만 갱신하며 기존 `report`를 유지한다. **published,feed,fetched_at은 갱신하지 않는다.** 삭제·보존기간 정리는 없으며 Google `when:30d`는 검색 힌트로 DB 30일 보존 보장이 아니다. 같은 기사의 다른 URL은 유지된다.

`articles.json`: 문자열 `{title,source,published,category,feed,url}`의 배열이며 `published` 형식은 `YYYY-MM-DD HH:MM`이다. DB timestamp가 DB `now()-60 days` 이상인 것만 최신순으로 최대 1500개 포함한다. published null 행은 제외한다. 시간대 없는 서울 시각과 DB 시계 의미를 비교하여 경계 오차가 생길 수 있다. 샘플 출력은 없다. 뉴스 인사이트는 최근 7일 저장 행과 제목 키워드 등장을 세며 발행사별 고유 기사 수나 전체 시장 보도량을 뜻하지 않는다.

## 현재 한계와 가능한 변경의 구분

앞의 모든 절은 구현된 동작이다. 이 문서는 제안 스키마·추가 출처·수집 변경·쿼터나 권리 보장을 구현하지 않는다. 출력을 신뢰 가능한 계약으로 취급하려면 다음 추가 여부를 별도로 결정해야 한다: 무데이터·오류 구분과 페이지 완전성 검증, 실제 요청량의 영속 예산, 지역 일부 성공의 안전한 병합, 명시적 단위·지수 기준, 안정적 식별자와 정정 출처, 최신성·범위 플래그, 공급자 허가·보존 정책 검증. 이들은 미결 설계 사항이며 현재의 보장이 아니다.
