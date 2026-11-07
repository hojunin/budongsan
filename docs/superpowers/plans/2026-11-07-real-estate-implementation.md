# Real estate content implementation plan

**Goal:** 기존 공식 데이터의 관측과 개인 가정, 고정 근거를 네 가지 독자 질문에 연결한다.

**Architecture:** 현재 Observable 정적 사이트와 로컬 Python 도구를 유지한다. 검증된 기존 데이터만 사용하고 미확정 원천과 발행 단계는 명시적으로 보류한다.

**Tech Stack:** Observable Framework, ECharts, Python, DuckDB.

**Spec:** `docs/superpowers/specs/2026-11-07-real-estate-content-platform-design.md` §14와 `2026-11-07-buyer-decisions-sentiment-policy-design.md`.

## Global constraints

실제 수집·배포·설문·외부 발송을 실행하지 않는다. 개인정보는 브라우저 메모리만 사용한다. 합성 자료는 공개 발행하지 않는다. 미확인 API, 인과 및 예측을 만들지 않는다. 스냅샷은 출처별 release를 고정한다.

## Tasks

- [ ] 기존 수집기와 테스트를 살펴 오류 응답, 불완전 페이지와 부분 성공 시 이전 데이터가 보존되게 수정하고 fixture로 검증한다.
- [ ] 네 질문 중심 진입과 세후 실수령 기반 개인 시나리오를 구현하고 산술·누락·음수 경계를 테스트한다.
- [ ] 기존 매매·임대 관측과 대표 그래픽을 연결하고 표본·기간·단위·미확인 상태를 표시한다.
- [ ] 로컬 근거·고정 스냅샷·리포트 패키지와 발행 도구를 구현하고 동일 release 및 안전한 사용자 입력을 검증한다.
- [ ] 미확정 인사이트와 기능의 게이트를 표시하고 I01–I28을 완료/보류/잔여로 보고한다.
- [ ] 기존 테스트와 빌드, 가능한 화면 및 CLS 검증을 실행하고 실제 결과와 한계를 보고서에 기록한 뒤 커밋한다.

## Review focus

빈 성공 응답과 오류 응답 구분; 중간 페이지 실패; 미입력과 0 구분; 예산선 범위 밖; 최신 데이터 변경 후 과거 보고서 불변.
