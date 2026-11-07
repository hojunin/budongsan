# 매수·임대 그래픽 보완 보고서

2026-11-08 · 브랜치 `codex/real-estate-content-design` · 요청 기준 `d99a9da`

구현 커밋 `e56a5f2343ebc31ab5380a1532a542eebb7ecaf1` · 공유 브랜치의 부모 CI 변경을 보존했다.

## 구현 범위

- **I01:** 동일 지역·면적대의 전년 동기 3개월과 최근 완결 3개월을 비교하는 거래수 변화 × ㎡당 중간 거래가격 변화 4분면을 추가했다. 두 기간 각각 유효 거래 30건 미만이면 결과를 비운다. 기간·표본·두 변화율을 표에도 표시한다.
- **I03:** 두 기간의 `(Q75−Q25)/중간값`과 그 차이를 각각 `%`, `%p`로 표시한다. 반올림 전 가격·면적 원값으로 계산하며 표본 구성의 변화가 포함된다는 설명을 유지한다.
- **I05:** 선택 단지의 59·84㎡대별 실제 전용면적 최솟값과 최댓값을 표에 표시한다. 해당 집단 n<5는 범위를 비운다.
- **I08:** 선택 단지·지역·면적대·기간의 실제 계약 최대100건을 보증금 × 월세 산점도로 펼쳐 볼 수 있다. 전세(월세 0)와 월세를 구분하고 선택된 계약을 강조한다. 기존 계약 선택기와 원값 대체표를 키보드로 사용할 수 있다. 월세 미상·합성·음수/비유한 값은 제외하며 다른 계약을 동일 주택의 전환 조건으로 연결하지 않는다.

네 화면 모두 데이터 수집 완결성과 이름 기반 단지 식별이 확인되기 전까지 **탐색용**이다. 관측 변화는 매수 권고·가격 전망·보증 안전성이나 인과효과를 뜻하지 않는다. 미확인 신규 API·권리·다른 I01–I28 요구를 완료로 주장하지 않는다.

## 근거와 고정 출력

주간 근거에는 두 기간의 거래수·가격 변화, 상대 구간 폭과 그 차이, 기간·양기간 표본·계산식·4분면 축 정의를 함께 저장한다. 패키지 생성 시 고정된 두 분포에서 파생값을 재계산해 일치하지 않으면 거부하고, 세로·가로 SVG에도 4분면을 고정한다. 음수 값은 출력 축의 왼쪽으로 표시한다.

매수 근거에는 저장한 면적대의 실제 면적 최솟값·최댓값을 포함하며, 59/84 비교에 필요한 다른 면적대도 표본 조건을 만족하면 같은 출처 release의 별도 근거로 저장한다. 임대 근거에는 선택한 계약의 보증금·월세 원값과 산점도 축 정의를 고정한다. 산점도 전체 거래점을 자동 공개 패키지에 복제하지 않는다. 합성 여부·단지 식별·partition 완결성·이용권 확인 전 공개 패키지 생성이 차단되는 기존 경계는 그대로다.

## 검증

실제 수집·크롤링·원본 DB 쓰기/삭제·환경키 조회·병합·푸시·배포는 수행하지 않았다. 기존 읽기 전용 정규화 캐시를 사용했다.

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
PATH="$PWD/.venv/bin:$PATH" python scripts/test_compare_fixture.py
CLS_BASE_URL=http://127.0.0.1:8766 node scripts/test_identity_ui.mjs
CLS_BASE_URL=http://127.0.0.1:8766 node scripts/test_review_ui.mjs
```

모두 통과했다. 빌드는 15페이지이며 기존 `cleanUrls` deprecated 경고가 있다. 격리된 합성 fixture는 4분면·상대 폭·실제 면적 범위, 전세/월세 분리, 미상/합성 제외와 선택 계약 환산값, 매수·주간·임대 고정 패키지를 확인했다. 320/390/1440px의 light/dark 비교 화면 및 기존 개인·전망 화면은 가로 넘침과 Observable 런타임 오류가 없었다. 실제 iOS Safari·VoiceOver와 원격 API 응답은 확인하지 않았다.

390×844, DPR3, CPU 4배 저속, 9Mbps/50ms, 캐시 비활성 조건에서 비교 화면을 각3회 측정했다. 초기·전체 표준 CLS와 원시 초기 shift는 모두 0이었고 프로그램으로 실행한 면적 필터 변경·차트 조작의 shift도 0이었다. [측정 결과](assets/2026-11-08-compare-cls.json), [합성 데이터 화면 390px](assets/2026-11-08-synthetic-compare.png). 이 결과는 해당 화면·조건의 검증이며 사용자 테스트나 모든 기기의 접근성 인증은 아니다.
