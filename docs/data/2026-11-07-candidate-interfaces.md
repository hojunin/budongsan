# 신규 데이터 후보 인터페이스 검증

확인일: **2026-11-07**. 공식 공개 문서·HTML에 연결된 OpenAPI 명세만 확인했다. 인증키 조회·발급·실데이터 수집은 하지 않았다. `공개 명세 확인`은 응답 성공·과거 커버리지 검증을 뜻하지 않는다. 공식 SDK 실행 검증은 전 후보 **미실시**, 사용자 인증키 응답 검증도 전 후보 **미실시**다. 아래 자연키와 재수집 정책은 명세에서 도출한 구현 제안이며 기관의 유일성 보장이 아니다.

## 1. 청약홈 — 공개 OpenAPI 명세 확인

[분양정보 15098547](https://www.data.go.kr/data/15098547/openapi.do), [경쟁률 15098905](https://www.data.go.kr/data/15098905/openapi.do)의 HTML `swaggerUrl`이 각각 연결하는 [분양 명세](https://infuser.odcloud.kr/api/stages/37000/api-docs?1643022751478), [경쟁률 명세](https://infuser.odcloud.kr/api/stages/36148/api-docs?1644395106638)를 직접 읽었다. 포털 웹 리더의 content-type 오류는 공식 HTML HTTP 조회로 보완했다.

| 공통 계약 | 확인 내용 |
|---|---|
| 전송·인증 | GET, HTTPS `https://api.odcloud.kr/api`. 보안 정의는 query `serviceKey` 또는 header `Authorization`. 헤더 값의 접두사 규칙은 이 검증에서 **NOT VERIFIED**이므로 query 방식을 계약 초안으로 사용 |
| 요청·페이지 | `page`(page index), `perPage`(page size), `returnType`(기본 JSON, XML 선택). 응답 `page`, `perPage`, `totalCount`, `currentCount`, `matchCount`, `data[]`. 페이지 기본값·최대크기·정렬 안정성 **NOT VERIFIED**. 조건을 고정하고 페이지별 응답·집계값 저장, 누락/중복 확인 필요 |
| 제한·권리 | 두 포털 모두 무료, 이용허락범위 제한 없음, 개발계정 신청 가능 트래픽 40,000, 개발 자동승인/운영 심의승인. 40,000의 재설정 시간·초당 제한 수치는 **NOT VERIFIED**. 실시간은 포털 메타데이터로, 공고 변경 반영 지연 보장 아님 |
| 실패 | 명세 HTTP 401 인증 실패, 500 서버 문제. 성공 HTTP만으로 `data` 존재·완전성을 판단하지 않음 |

모든 아래 경로는 공통 base 뒤에 붙인다. 필터명은 대소문자와 `cond[...]` 그대로 URL 인코딩한다. [분양 명세](https://infuser.odcloud.kr/api/stages/37000/api-docs?1643022751478), [경쟁률 명세](https://infuser.odcloud.kr/api/stages/36148/api-docs?1644395106638).

| GET 경로 | 요청 필터(모두 선택) | 행 단위·필드·단위 | 구현 키 제안 / 주의 |
|---|---|---|---|
| `/ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancDetail` | `cond[HOUSE_MANAGE_NO::EQ]`, `cond[PBLANC_NO::EQ]`, `cond[HOUSE_NM::LIKE]`, `cond[HSSPLY_ADRES::LIKE]`, `cond[HOUSE_SECD::EQ]`, `cond[HOUSE_DTL_SECD::EQ]`, `cond[SUBSCRPT_AREA_CODE::EQ]`, `cond[SUBSCRPT_AREA_CODE_NM::EQ]`; `cond[RCRIT_PBLANC_DE::LT/LTE/GT/GTE]`의 각 개별 필터 | 공고. `HOUSE_MANAGE_NO`, `PBLANC_NO`, `HOUSE_NM`, `HSSPLY_ADRES`, `TOT_SUPLY_HSHLDCO`(공급규모 정수), `RCRIT_PBLANC_DE`, `RCEPT_BGNDE/ENDDE`, `PRZWNER_PRESNATN_DE`, `CNTRCT_CNCLS_BGNDE/ENDDE`, `MVN_PREARNGE_YM`(입주예정월), `PBLANC_URL`; 접수/발표/계약일은 문서상 YYYY-MM-DD | `(HOUSE_MANAGE_NO,PBLANC_NO)`. 공급지역코드를 법정동코드로 해석 금지. 입주예정월은 준공·입주 확정 사실 아님 |
| `/ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancMdl` | 위 주택관리번호·공고번호 EQ | 공고×모델. `MODEL_NO`, `HOUSE_TY`, `SUPLY_AR`(공급면적 문자열), `SUPLY_HSHLDCO`(일반공급세대수), `SPSPLY_HSHLDCO`(특별공급세대수), `LTTOT_TOP_AMOUNT`(분양최고금액 문자열, **만원**), 특별공급 세부 세대수 | `(HOUSE_MANAGE_NO,PBLANC_NO,MODEL_NO)`. `SUPLY_AR`의 면적단위는 공개 Swagger에 **NOT VERIFIED**; 공급면적과 실거래 전용면적 직접 비교 금지. 최고금액은 평균 분양가 아님 |
| `/ApplyhomeInfoCmpetRtSvc/v1/getAPTLttotPblancCmpet` | 주택관리번호·공고번호 EQ, `cond[RESIDE_SECD::EQ]`(01 해당/02 기타/03 기타경기) | 공고×모델×순위×거주구분. `MODEL_NO`, `HOUSE_TY`, `SUPLY_HSHLDCO`(공급세대수), `SUBSCRPT_RANK_CODE`(정수), `RESIDE_SECD`, `RESIDE_SENM`, `REQ_CNT`(접수건수 문자열), `CMPET_RATE`(경쟁률 문자열) | 위 차원을 모두 포함. 거주구분·순위 행에 반복되는 공급세대수를 단순 합산 금지. 경쟁률 문자열을 바로 float 변환하지 말고 원문 보존 |
| `/ApplyhomeInfoCmpetRtSvc/v1/getAPTSpsplyReqstStus` | 주택관리번호·공고번호 EQ | 공고×주택형. `HOUSE_TY`, `SPSPLY_HSHLDCO`; `MNYCH_HSHLDCO`, `NWWDS_NMTW_HSHLDCO`, `LFE_FRST_HSHLDCO`, `YGMN_HSHLDCO`, `OLD_PARNTS_SUPORT_HSHLDCO`, `NWBB_NWBBSHR_HSHLDCO`, `INSTT_RECOMEND_HSHLDCO`, `TRANSR_INSTT_ENFSN_HSHLDCO`는 유형별 배정세대수. `CRSPAREA_*_CNT`, `CTPRVN_*_CNT`, `ETC_AREA_*_CNT`는 해당/기타경기/기타지역 접수건수. `SUBSCRPT_RESULT_NM` | `(HOUSE_MANAGE_NO,PBLANC_NO,HOUSE_TY)` 유일성 실응답 검증 필요. **MODEL_NO가 이 응답에는 없다**. 일반공급 경쟁률의 분모로 특별공급 배정을 사용 금지 |

수정 이력: [공급 기술문서 게시물](https://www.reb.or.kr/reb/na/ntt/selectNttInfo.do?mi=10251&bbsId=1268&nttSn=79889)은 2026-01-29 주택명·공급위치 요청 추가, 2025-04-17 코드/명칭 변경 등을 기록한다. [경쟁률 기술문서 게시물](https://www.reb.or.kr/reb/na/ntt/selectNttInfo.do?mi=10251&bbsId=1268&nttSn=82345)은 2024-12-03 특별공급 항목 추가를 기록한다. 포털은 은행 전산 사정으로 접수건수가 변동되고 청약홈 최종정보와 다를 수 있다고 명시한다. 수정일 필드·취소 tombstone·변경분 전용 조회는 **NOT VERIFIED**. 최근 공고를 재조회하고 공고 원문 URL·조회시각·응답 해시를 보존하는 방식이 필요하다.

## 2. K-apt 15058453 — 현재 V5 명세 확인

[공식 포털](https://www.data.go.kr/data/15058453/openapi.do)의 HTML `swaggerJson` 확인. **현재 명세는 V5**다. 기본정보와 주차정보는 서로 다른 오퍼레이션이다.

| 계약 | 확인 내용 |
|---|---|
| 기본정보 | GET `https://apis.data.go.kr/1613000/AptBasisInfoServiceV5/getAphusBassInfoV5`, 필수 query **`serviceKey`**, `kaptCode` |
| 상세정보 | GET `https://apis.data.go.kr/1613000/AptBasisInfoServiceV5/getAphusDtlInfoV5`, 필수 query **`ServiceKey`**, `kaptCode`. 기본정보와 키 철자가 다름은 공개 명세 그대로이며 실제 서버의 case 허용 여부는 미검증 |
| 응답·페이지 | JSON. 공개 schema에 `header.resultCode`(00 성공), `header.resultMsg`, `body.item`. 단지코드 하나 조회이며 페이지 인자가 없음. 실응답의 추가 root wrapper 여부 **NOT VERIFIED** |
| 기본 필드 | `kaptCode`, `kaptName`, `kaptAddr`(법정동주소), `doroJuso`, `bjdCode`(법정동코드), `codeHeatNm`, `kaptUsedate`, `kaptDongCnt`, **`kaptdaCnt`(세대수, schema string)**, `hoCnt`(호수), `kaptTarea`(연면적), `kaptMarea`(관리비부과면적), `privArea`(단지 전용면적합), `kaptMparea60/85/135/136`(전용면적별 세대현황). 면적단위·구간 경계·날짜문자열 형식은 이 명세에서 **NOT VERIFIED** |
| 상세 필드 | `kaptdPcnt`(지상 주차대수), `kaptdPcntu`(지하 주차대수), `groundElChargerCnt`, `undergroundElChargerCnt`, `useYn`, `kaptCode`. 주차장 수가 아니라 주차 **대수** |
| 범위·키 | 관계법령 등에 따라 K-apt에 가입한 단지만. `kaptCode`를 보존하고 실거래 식별자와 별도 crosswalk 필요. 명칭 일치만으로 합치지 않음. 이 API는 코드 입력형으로, 전체 코드 목록 발견 경로는 **NOT VERIFIED** |
| 제한·권리 | 무료, 제한 없음, 개발/운영 자동승인, 개발계정 신청 가능 트래픽 5,000, 포털 갱신 실시간. reset 시간·초당 수치·변경분 조회·수정일은 **NOT VERIFIED** |

세대당 주차는 두 주차대수와 세대수의 유효성·동일 스냅샷을 검증한 뒤 계산한다. `kaptdaCnt`와 `hoCnt`를 동의어로 치환하지 않는다. 사용승인일은 연식 계산에 사용할 후보이지 실응답의 빈 값/날짜 형식이 검증된 상태가 아니다.

## 3. KOSIS — 전송 계약 확인, 후보 표 선택은 일부 미확정

[공식 통계자료 개발가이드](https://kosis.kr/openapi/devGuide/devGuide_0201List.do)의 요청·출력 정의 및 R GET 예제 확인. 특정 표의 항목·분류 코드는 별도 검증해야 한다.

| 계약 | 공개 명세 확인 내용 |
|---|---|
| 요청 | GET `https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList`. 필수 `apiKey`, `orgId`, `tblId`, `objL1`, `itmId`, `prdSe`, `format=json`; 선택 `objL2`~`objL8`, `startPrdDe/endPrdDe` 또는 `newEstPrdCnt`, `prdInterval`, `outputFields`, `smblChk`. 시점 미지정 기본값은 최근 한 시점 |
| 출력 | JSON 배열. `ORG_ID`, `TBL_ID`, `TBL_NM`, `C1`~`C8`와 분류명/값명, `ITM_ID`, `ITM_NM`, `UNIT_ID`, `UNIT_NM`, `PRD_SE`, `PRD_DE`, **`DT`(문자열)**, `LST_CHN_DE`(최종수정일). 없는 분류2~8은 생략 가능 |
| grain·키 제안 | `(ORG_ID,TBL_ID,ITM_ID,C1..C8,PRD_SE,PRD_DE)`. 단위는 `UNIT_NM`에서 확인하며 통계부호·결측을 0으로 만들지 않음 |
| 분할·제한 | 일반 통계자료 요청 정의에 page/offset 없음. 기간·분류를 분할해 조회하도록 설계. 최대 셀수·일일/초당 한도·라이선스 세부조항은 이번 검증 **NOT VERIFIED**. 다른 포털의 쿼터를 적용 금지 |
| 목록 발견 | [통계목록 가이드](https://kosis.kr/openapi/devGuide/devGuide_0101List.do). 확정한 표의 항목/분류/단위/주석/기간을 함께 저장한 뒤 어댑터 구현. `LST_CHN_DE` 보존, 과거 수치 재조회·스냅샷 버전 분리 필요 |

| 후보 | 확인 / 아직 막힌 계약 |
|---|---|
| 인허가·착공·준공 | 공식 [KOSIS 기관 답변](https://kosis.kr/civilComplaint/qnaDetail.do?boardIdx=17781)은 세움터 행정업무 기반이며 해당 표의 공표단위가 시도라고 설명(2022 답변이므로 현재 범위 보장 아님). 세 단계에 사용할 현재 `tblId`, 항목·분류코드, 월 단독/누계 구분, 아파트/전체주택, 호/동 단위 및 기간은 **NOT VERIFIED**. 과거 Q&A의 표코드만으로 운영계약 확정 금지 |
| 전체 미분양·준공 후 미분양 | 현재 표의 `orgId/tblId/itmId/objL*`, 시도/시군구 범위·단위·기간·공표지연 **NOT VERIFIED**. 이 조사에서 2차 출처에만 나온 표 ID는 채택하지 않음. 원자료 통계누리와 KOSIS 중 하나의 확정 명세를 선택해야 함 |
| 국내인구이동 | 공식 [KOSIS 검색 안내 PDF](https://kosis.kr/ext/kosisGuide/pdf/KOSIS_search.pdf) 및 [최신통계 RSS](https://kosis.kr/rss/trendRss.do)가 `orgId=101`, `tblId=DT_1B26001_A01`, ‘시군구별 이동자수’를 확인해 준다. API용 항목/분류코드·연령 차원·이동자/이동건수 단위·지역 개편 처리·수록기간은 **NOT VERIFIED**. statHtml 직접 열기는 SSO redirect로 실패했으므로 이를 완전 계약으로 표시하지 않음 |

인허가·착공·준공은 서로 다른 **기간 실적(flow)**이며 고정 시차로 입주예정으로 바꾸지 않는다. 월 누계 수치를 월별 값처럼 합산하지 않는다. 미분양은 **시점 재고(stock)**여서 월 합산 금지. 인구이동은 사람 이동 통계이지 가구·세대·매수건수와 같지 않다. 시군구명만으로 실거래 법정동과 조인하지 말고 기준일이 있는 행정/법정지역 crosswalk와 지역개편 정책을 먼저 확정한다.

## 4. ECOS 금리 — 공식 서비스 확인, series 계약 NOT VERIFIED

[ECOS API 공식 진입점](https://ecos.bok.or.kr/api/)은 JS 앱이라 이 조사에서 개발명세 본문·요청/응답 계약을 읽지 못했다. 따라서 알려진 비공식 예제의 URL·통계표코드·항목코드를 복사하지 않았다. **엔드포인트·HTTP method·인증키 인자·페이지·응답 필드·금리별 series ID·한도·재배포 조건은 모두 NOT VERIFIED**이며 구현 착수 조건이다.

[한국은행 2026년 9월 금융기관 가중평균금리 공식 발표](https://www.bok.or.kr/portal/bbs/B0000501/view.do?depth=201264&menuNo=201264&nttId=11066053&programType=newsData&relate=Y)는 금리 자료의 공식 출처이지만 API series 계약을 대신하지 않는다. 후속 확정할 series는 최소 `한국은행 기준금리`, `예금은행 가계 주택담보대출 신규취급액 기준`, `잔액 기준`을 서로 구분해야 한다. **신규취급액 기준/잔액 기준, 주담대/전체 가계대출, 기관 범위, 주기, 연율 %, 기준일**을 항목 메타데이터로 검증한다. 전월차는 %p로, 금리는 개인 대출 견적과 구분한다. 개정 이력·최신값 덮어쓰기 정책도 확정 전이다.

## 5. 서울 정비사업 15097425 — 파일 후보이며 API 계약 아님

[공공데이터포털 15097425](https://www.data.go.kr/data/15097425/fileData.do)은 CSV·수시·전체 행 200으로 표시하지만, 실제 연결된 [서울시 OA-22856](https://data.seoul.go.kr/dataList/OA-22856/S/1/datasetView.do)은 **분기 갱신 XLSX 첨부**를 제공한다. 기준시점/실제현황 차이 가능성도 원제공기관이 명시한다. 파일 제공기관 화면을 우선한다.

| 계약 항목 | 확인 / 미확인 |
|---|---|
| 실제 자산 | `★(26년 6월기준) 서울시 정비사업 추진현황.xlsx`(2026-09-10 수정), 3월 기준 파일(2026-07-15 수정) 목록 확인. 데이터 갱신일 2026-09-10, 분기, 서울특별시 저작권, 제3저작권자 없음, 이용허락범위 제한 없음 |
| 인증·엔드포인트 | 공개 파일 목록 접근 가능. 고정 다운로드 URL·HTTP 인자·파일 인증·페이지·API 서비스명 **NOT VERIFIED**. 일반 서울 OpenAPI 관례를 이 파일에 대입 금지 |
| 행·필드 | 설명상 정비구역별 추진단계·지정일·현황, 포털 설명상 자치구·구역명·주소·사업방법/유형. **실제 workbook의 sheet·header·병합셀·단위·안정 ID·날짜형식·행 수 NOT VERIFIED**. 설명을 확정 컬럼명으로 쓰지 않음 |
| 변경·활용 | 분기 스냅샷이라는 원제공기관 설명을 따른다. 기준분기+파일 해시·다운로드일 보존 필요. 사업명/주소 변경·구역분할/합병·삭제를 안정 ID 없이 확정 추적할 수 없음. 추진단계를 완공·입주시기 예측으로 해석 금지 |

## 후속 구현을 여는 최소 확인

1. 청약홈: 인증 응답에서 페이지 시작/상한, 조건필터, 키 유일성, 문자열 결측/특수 경쟁률, 변경 공고의 재조회 확인.
2. K-apt: 두 키 인자 대소문자, 실제 root envelope·빈 필드·단위/날짜, 단지코드 목록 경로·실거래 crosswalk 확인.
3. KOSIS: 각 후보 통계표·항목·모든 차원 코드와 주석·단위·갱신일·기간, 제한/활용약관 확정. 이동통계의 알려진 표 ID 외 공급/미분양 ID는 아직 차단 상태.
4. ECOS: 공식 개발명세를 열어 전송 계약부터 확정한 뒤 금리별 정확한 표·항목 ID를 선택. 현재 문서는 작동하는 ECOS adapter의 명세가 아님.
5. 서울: 실제 XLSX 한 버전의 헤더·데이터형·ID·기준일을 검증한 뒤 file adapter 결정. 포털 CSV 표기만 믿고 CSV 파서를 만들지 않음.

서버 설치·스케줄링·자동 수집·키 발급·배포는 범위에서 제외했다. 검증 전 빈칸을 관행적인 URL/코드로 채우는 것이 가장 큰 구현 위험이다.

## 6. 행정안전부 주민등록 인구·세대 — 공식 화면 확인, 파일 전송 계약 미확정

[공식 월간 조회](https://jumin.mois.go.kr/statMonth.do)에서 행정동별 주민등록 인구·세대 현황과 ‘행정기관코드 / 행정기관 / 총 인구수 / 세대수 / 세대당 인구 / 남자·여자 인구’라는 **화면 라벨**을 확인했다. 이는 CSV의 확정 헤더나 API 응답 필드명이 아니다. 단위는 인구 명, 주민등록 세대수 세대이며 통계 가구/주택수와 구분한다. 기준은 매월 말일, 안내상 다음달1일12시 이후 공표(주말·공휴일은 다음 평일). 이번 설계에서 실제 파일/인증 응답을 받지 않았다.

운영 전 확정할 계약: 공식 다운로드 URL/HTTP method/필터 파라미터/인증·자동접근 조건, 실제 CSV/XLSX 헤더·인코딩·계층합계 행, 기간/지역 분할·최대조회범위·호출한도·라이선스, 행정기관코드 유효기간과 개편 이력. **모두 NOT VERIFIED**로 남긴다. 지역 합계와 하위동을 중복 합산하지 않으며 주민등록 세대를 KOSIS 일반가구로 치환하지 않는다. 제안 내부 키는 `(source,행정기관코드,기준월,인구구분)`이지만 원본 필드/행 단위 검증 뒤 확정한다. I18은 이 계약과 KOSIS 이동 계약이 모두 통과하기 전 운영 차단이다.
