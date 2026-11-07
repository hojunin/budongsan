# 부동산 데이터 인터페이스 계약

2026-11-07 · 설계 문서. 실제 수집·인증키 조회·신규 API 호출은 실행하지 않았다. 현재 코드의 인터페이스와 신규 공식 명세의 확인 수준을 분리한다.

- [현재 수집기·정규화 출력 계약](2026-11-07-current-interfaces.md)
- [추가 공식 API·파일 데이터 계약](2026-11-07-candidate-interfaces.md)
- [복합 인사이트 카탈로그](../insights/2026-11-07-composite-insights.md)
- [전체 제품 설계](../superpowers/specs/2026-11-07-real-estate-content-platform-design.md)

## 1. 검증 수준과 사용 가능 판정

| 상태 | 뜻 | 운영 인사이트 허용 |
|---|---|---|
| implemented | 현재 수집/로더 코드에서 경로·필드를 확인 | 코드 존재만으로 허용하지 않음. 아래 품질 게이트 추가 필요 |
| documented | 공식 제공기관 명세·공개 메타데이터 확인 | 인증 응답·필드·커버리지 검증 전 차단 |
| discovery_required | 통계표·항목·엔드포인트 일부 미확정 | 개발 후보 목록만, 가짜 URL/필드로 대체 금지 |
| restricted_or_unknown | 사용권·접근 방법·응답 지속성이 미확인 | 자동수집 확대·공개 발행 차단 |
| retired | 서비스 종료/중단 확인 | 대체 출처 확인 전 사용 금지 |

`implemented`와 `documented`는 독립 증거다. 현재 코드가 돌아간 이력이 있어도 이번 문서 작업으로 실응답을 검증했다고 쓰지 않는다. 구현 준비도, 호출 성공, 범위 완결성, 통계 해석 적합성, 공개 이용권은 각각 구분한다.

## 2. 공통 계약 — 신규 어댑터의 내부 표준

아래는 **제안한 내부 타입**이며 제공기관의 응답 필드명이나 현재 구현 완료 타입이 아니다. 어댑터가 원본 응답과 이 계약을 연결한다. 외부 DTO는 별도 문서에 원래 필드명을 보존한다.

```ts
type ReleaseState = 'valid' | 'partial' | 'failed' | 'quarantined';
type ObservationStatus = 'provisional' | 'published' | 'revised' | 'missing';
interface DatasetRelease {
  releaseId: string; sourceId: string; schemaVersion: string;
  fetchedAt: string;              // RFC3339 UTC
  providerPublishedAt: string | null;
  observationFrom: string; observationTo: string;
  partitionKeys: string[];        // 예: 지역×계약월
  expectedPartitions: number | null; completedPartitions: number;
  state: ReleaseState; rawHash: string; adapterVersion: string;
  termsRef: string; termsCheckedAt: string; publicReuse: 'allowed' | 'limited' | 'unknown';
}
interface RegionRef {
  internalId: string; sourceCode: string; codeSystem: string;
  validFrom: string; validTo: string | null; crosswalkVersion: string;
}
interface MetricObservation {
  sourceId: string; releaseId: string; sourceSeriesId: string;
  metricId: string; metricVersion: string; region: RegionRef;
  periodStart: string; periodEnd: string; cycle: 'day' | 'week' | 'month' | 'quarter' | 'year';
  dimensions: Record<string, string>; // 주택유형, 면적, 공급구분, 신규/잔액 등
  value: number | null; unit: string; scale: number;
  status: ObservationStatus; providerPublishedAt: string | null;
}
interface AdapterPage {
  records: unknown[]; providerStatus: string; totalCount: number | null;
  nextCursor: string | null; transportOk: boolean; complete: boolean;
}
```

지역코드·단지코드·통계 ID는 문자열로 유지한다. 금액은 정규화 후 만 원, 면적은 ㎡, 금리는 연 비율로 변환하되 외부의 퍼센트 포인트 원값/단위를 함께 보존한다. `value=.04, unit=annual_ratio`와 `value=4, unit=percent`를 구분한다. UI 반올림은 계산 이후 최대2자리이며 원본 정밀도를 잘라 저장하지 않는다. 주/월을 문자열 사전순으로만 결합하지 않고 실제 기간 시작/끝과 제공기관 달력을 사용한다.

거래 원본은 출처별 레코드 ID가 있으면 보존한다. 없으면 거래를 식별할 수 있는 필드의 hash는 추적용으로만 사용하고 동일 가격·날짜·층 거래를 자동 중복 삭제하지 않는다. 서로 다른 실제 거래가 같아 보일 수 있다. 현재처럼 지역×월 스냅샷을 교체하는 방식과 관측 이력을 별도로 보존한다.

### 어댑터의 실행 계약

`discover()`는 표/항목/단위를 확인하고, `fetch(partition, cursor)`는 페이지와 상태를 반환하며, `normalize()`는 DTO→내부 타입, `validate()`는 범위·수량·단위·키를 검사한다. 이 이름의 함수를 모두 새로 만들라는 요구는 아니다. 기존 수집기도 같은 책임을 충족시키면 된다.

- HTTP 성공과 제공기관 업무 성공을 모두 확인한다. 200 응답 HTML/오류 XML도 실패다.
- 페이지 수·누적행·totalCount 일치를 확인하고, 다음 페이지 실패를 정상0건으로 기록하지 않는다.
- 정상0건은 성공 코드+정확한 요청 범위+완료된 페이지 증거가 있어야 한다.
- 페이지를 모두 검증한 partition만 원자 교체한다. 부분 수신·스키마 변경은 격리하고 마지막 유효 partition 유지.
- 크롤링·API 오류를 `missing`이나 숫자0으로 변환하지 않는다. `failed`/`partial`와 최신 유효 관측 기간을 UI까지 전달한다.
- 제공기관 quota와 우리 실행 예산은 분리한다. 재시도까지 실제 HTTP 요청을 세고, 429/Retry-After와 지속형 일일 예산을 적용한다. 구체 한도는 각 서비스 승인 내역으로 확정한다.
- raw 응답·조건·버전·hash는 private 보관 정책을 따른다. 키를 query/path에 쓰는 API는 URL/예외/로그에서도 키를 가린다.
- 최근 일부 기간 재수집만으로 오래된 정정까지 반영됐다고 보장하지 않는다. 공표 정정 알림과 주기적 과거 대조를 별도 작업으로 둔다.

## 3. API와 RSS/크롤링을 구분하는 수집 계약

| 유형 | 외부 인터페이스 | 정규화 결과 | 처리·검증 |
|---|---|---|---|
| 공식 API | 명세의 요청/페이지/인증/업무코드 | transaction 또는 metric observation | 공식 타입/단위 우선. 필드 누락·업무 오류·페이지 미완료 격리 |
| 공식 CSV/XLSX | 제공기관 다운로드 링크·공표 파일 | metric observation + 원문 버전 | 표/시트/헤더/단위 hash, footnote 검증. 동적 파일 URL을 영구 API처럼 고정하지 않음 |
| 공식 RSS/Atom | 아래 확인한 기관 피드 | source document metadata | guid/link, title, 실제 발행/수정일, 기관, 발견시각. RSS 목록 존재와 현재 정상응답은 별도 |
| 허용 확인된 공식 HTML | 허용된 목록·상세 페이지 | source document metadata | 허용/robots·약관·공공누리 항목별 확인. selector/헤더 계약과 변경 감지. 본문/첨부 사용권은 별도 |
| 언론사/검색 RSS | 현재 코드의 피드 | headline metadata | 제목·매체·날짜·링크만. 본문·이미지 복제/AI 원문 입력 권한까지 얻은 것으로 간주하지 않음 |
| 민간 서비스 비공식 API | SDK 내부 URL/수기 파일 | 조건부 observation | 공개 화면 접근 가능=API 제공/재배포 허락 아님. 현재 KB 어댑터는 공식 보장 없는 의존성으로 표시 |

### 공식 발표문 메타데이터 후보

**외부 명세가 확인된 RSS 주소(2026-11-07 공식 안내 기준, 실시간 피드 호출은 하지 않음):**

- 국토교통부 보도자료: `GET https://www.molit.go.kr/dev/board/board_rss.jsp?rss_id=NEWS` — [공식 RSS 안내](https://www.molit.go.kr/USR/p_etc_rsssvc/m_123/ers.jsp).
- 한국은행 경제통계 보도자료: `GET https://www.bok.or.kr/portal/bbs/B0000501/news.rss?menuNo=201264` — [공식 RSS 목록](https://www.bok.or.kr/static/guide/portal/popup/rss_popup.html).
- 행정안전부 보도자료: `GET https://www.mois.go.kr/gpms/view/jsp/rss/rss.jsp?ctxCd=1012` — [공식 RSS 안내](https://www.mois.go.kr/frt/sub/a08/rss/screen.do).
- **정책브리핑 RSS는 후보에서 제외:** 공식 [공지 목록](https://www.korea.kr/etc/noticeList.do)에 2026-07-01 RSS 중단 안내가 있어 현행 RSS로 전제하지 않는다. 대체 공식 HTML/API는 이용 조건과 명세를 따로 확인한다.

저장할 내부 문서 필드: `documentId, providerId, canonicalUrl, title, publishedAt|null, modifiedAt|null, firstSeenAt, documentType, affectedRegions[], effectiveFrom|null, attachmentRefs[], rightsRef, releaseId`. `effectiveFrom`·영향 지역은 제목 키워드로 확정하지 않고 본문/공고의 검증된 근거가 있는 경우만 채운다. 없으면 null/빈 배열이다. 발표일≠시행일이며 날짜 누락은 발견시각으로 대체 발행하지 않는다.

HTML 수집 설계: allowlist 도메인/경로, 식별 가능한 User-Agent, timeout·바이트 상한·속도 제한, 조건부 GET(지원 시 ETag/Last-Modified), parser 변경 경보, 마지막 정상 응답 유지. robots 허용만으로 이용권이 확보됐다고 보지 않는다. 로그인/CAPTCHA/차단을 우회하지 않는다. URL 입력을 받는 구현에서는 private IP·임의 리다이렉트·비허용 첨부 실행을 차단한다. 이 절은 정책의 자동 동의나 새 수집기 설치를 의미하지 않는다.

## 4. 복합 인사이트를 위한 결합 규칙

1. **공간**: 제공기관 지역코드→유효기간 있는 공통 ID. 법정동=행정동으로 문자열 join하지 않는다. 전국과 서울/경기 일부 커버리지를 혼용하지 않는다.
2. **기간**: `observation period`, `publishedAt`, `fetchedAt`, `cutoff` 네 시점을 구분한다. 과거시점 분석은 그때 공개된 release로만 구성한다. 최신값을 과거에 알았던 것처럼 소급 사용하지 않는다.
3. **대상**: 아파트/전체주택/공동주택, 신규계약/전체계약, 전용/공급면적을 차원으로 가진다. 다른 대상의 병렬 관찰은 가능하나 동일 지표 비율로 결합하지 않는다.
4. **모수/분모**: 사람·세대·가구·주택·거래 건수·호수를 구분한다. 같은 source의 ‘합계’와 하위항목을 중복 합산하지 않는다.
5. **흐름/재고**: 거래·착공은 기간 흐름, 미분양은 기말 재고. 재고의 12개월 합계를 ‘연간 미분양’으로 만들지 않는다.
6. **구성 변화**: 지역 중간가격의 변화와 같은 집 가격 변화를 구분한다. 고정 구성 지표는 매칭/가중치/잔존 표본의 범위를 밝힌다.
7. **동일 스냅샷**: 보고서 release_manifest에 출처별 release를 고정한다. 자료별 관측일은 달라도 되지만 같은 출처 버전 혼합은 차단한다.
8. **사용권**: 공개 가능한 집계/메타데이터만 출력한다. 기사 이미지·전문·지도 타일은 별도 권리 없이 패키지에 포함하지 않는다.

## 5. 공통 품질·발행 게이트

인사이트 생성기는 조건을 못 채우면 문장을 지어내지 않고 `blocked_reason`을 반환한다. 조건이 맞아도 ‘검증된 인과/매수추천’으로 승격하지 않는다.

```ts
interface InsightEvidence {
  insightId: string; definitionVersion: string; releaseManifestId: string;
  scope: {regionIds: string[]; housingType: string; areaSpec: string};
  observedPeriods: Record<string, string>; cutoff: string;
  facts: {metricId: string; rawValue: number | null; unit: string; n: number | null}[];
  quality: {coverageOk: boolean; sampleOk: boolean; periodOk: boolean; rightsOk: boolean};
  eligibility: 'eligible' | 'blocked'; blockedReasons: string[];
  claimType: 'descriptive' | 'scenario'; limitations: string[];
  chartSpecId: string; sourceLinks: string[];
}
```

최소 표본은 시안 시작값일 뿐 통계적 충분성 보장이 아니다. **아래 ID별 정책을 최종 기준으로 사용**하며 모순되는 공통 규칙을 따로 적용하지 않는다. 이 기준을 통과해도 편향/조건 불균형은 추가 차단 사유다.

| ID/유형 | 표본·경고·차단 정책 |
|---|---|
| I01/I03/I12/I13 지역·기간 통계 | 각 비교 집단 양기간 n≥30. 미달은 수치 비교 차단 |
| I02 고정 비교군 | 각 단지×면적군 양기간 n≥5, 공통군≥5, 합계 양기간 n≥30, 매칭률 각70% 이상. 셀5–19는 적은 표본임을 명시, n5 자체를 대표성/정밀성 근거로 삼지 않음 |
| I04 경신 | 현재 평가가능 거래≥30, 각 거래 과거비교≥3 및 필요한 전체60개월 이력 완결. 비교가능 비중 표시, 추정 모집단 경신률로 승격 금지 |
| I05/I06/I09 단지 분포·집단 수준 | 해당 각 집단 n≥5, 5–19 주의. 부족하면 범위/비율 비움. 지역순위/동일집 가치변화로 승격 금지 |
| I07 기간별 보증금 구간 | 각 단지/면적/보증금 구간 셀 양기간 n≥30. 보증금 원분포도 표시 |
| I08/I15 개인 선택 시나리오 | 모집단 최소n 대상 아님. 유효한 실제 선택계약 또는 명시적 가정 입력 필요, 근거 없는 대표성 주장 금지 |
| I10/I11 제공기관 구성비 | 공식 집계의 유효 합계>0, 필수 범주 완결/배타 확인. 분모·분자 기준0 및 비공개/미상 처리 확인 |
| I14 품질 | 표본 기준이 아닌 partition 완료 증거. 과거 성공로그를 페이지완결 검증으로 소급 인정 금지 |
| I16–I20 신규 소스 | 원천 응답·모수/단위/범위·사용권 확정 전 보류. 거래 분포와 기간 변화는 위 기본단위 정책, 청약/재고/세대수는 공식 집계·분모 정합 게이트 적용 |

현재 `trades.parquet`의 1자리 반올림 ppm2, 이름 기반 complex_key, 미상을 false로 합친 direct, 임대 로더의 미상월세→0을 신규 계약의 검증된 원값으로 재사용하지 않는다. 새 계산은 유효 price/area 원값에서 하고 synthetic is_sample은 공개 관측에서 명시적으로 거부한다.

`coverageOk`는 요청한 지역×월×주택유형 partition의 완료 증거다. 전체행이 많다는 이유로 완결로 판정하지 않는다. 정상 거래0건의 완료 partition은 사용할 수 있지만 통계 추정치는 표본 게이트에 따라 비운다. 결측과0을 구분한다. source간 공동 관측 기간을 계산하고 허용한 유효기간을 넘긴 과거값은 `stale`로 표시/차단한다.

최신 ‘완료월’도 최종 확정은 아니다. 계약월 말부터 최소30일이 지나고 기준일까지 완전 수집된 월을 기본 후보로 삼되, 수집일과 잠정/정정 상태를 표시한다. 더 보수적인 시차를 쓰면 정책 버전을 기록한다. 취소·정정 반영 후에도 소급 변동 가능성이 있다.

## 6. 현재 코드에서 먼저 해결할 위험

수집기 감사에서 현재 구현의 비성공 응답→빈 데이터 오인 가능성, 페이지 완결성 확인 부족, 호출 예산의 지속성 부족, KB 부분 성공 시 범위 축소 가능성을 확인했다. 상세 근거는 현재 인터페이스 문서에 있다. **현재 데이터가 실제로 손상됐다고 판정한 것은 아니다.** 인사이트 공개 자동화 전, 실패 응답을 정상0건과 구분하고 원본 partition 보존·완결성 기록을 먼저 보완해야 한다.

이번 문서는 수집 동작을 수정하거나 새 수집을 실행하지 않는다. 신규 제공기관 인증 응답/사용권·정확한 통계 코드가 미확정이면 해당 인사이트는 후보 상태로 남긴다.
