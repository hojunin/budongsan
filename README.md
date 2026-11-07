# 첫 집 데이터

국토부 실거래가·KB 지표로 지역과 관심 단지를 판단하는 정적 대시보드. Observable Framework로 만들고 Cloudflare Pages에 배포한다. 설계는 [DESIGN.md](DESIGN.md).

## 로컬 실행

```bash
npm install
pip install -r requirements.txt
npm run dev          # http://127.0.0.1:3000 — 인증키가 없으면 '샘플 데이터'로 뜬다
```

실데이터로 보려면:

```bash
export MOLIT_SERVICE_KEY="공공데이터포털 일반 인증키(Decoding)"
npm run fetch        # data/cache 에 실거래·KB 저장 (첫 실행은 수십 분)
npm run clean && npm run dev
```

## 배포 (Cloudflare Pages)

1. 공공데이터포털에서 **국토교통부_아파트 매매 실거래가 상세 자료**, **국토교통부_아파트 전월세 실거래가 자료** 활용 신청 → 인증키 발급.
2. Cloudflare 대시보드 → Workers & Pages → Pages 프로젝트 `apt-insight` 생성(Direct Upload).
3. Cloudflare API 토큰 발급(권한: Account · Cloudflare Pages · Edit).
4. GitHub 저장소 Settings → Secrets 에 `MOLIT_SERVICE_KEY`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` 등록.
5. Actions 탭에서 `build-and-deploy` 를 수동 실행. 이후에는 매월 16일·매주 월요일에 자동으로 갱신된다.

빌드를 Cloudflare 쪽에서 하지 않는 이유: 데이터 수집에 파이썬과 수십 분이 필요하고, 인증키를 GitHub Secrets 에만 두기 위해서다.

## 자주 바꾸는 파일

| 파일 | 용도 |
| --- | --- |
| `src/data/watchlist.json` | 관심 단지 목록 |
| `src/data/listings.csv` | 네이버 부동산에서 본 호가를 직접 기록 |
| `src/components/budget.js` | 예산·대출 계산 가정 |
| `src/style.css` | 색·폰트·레이아웃 |

## 관련 문서

- 매수 전략 문서(대출·규제·예산·생활권·후보 단지): https://claude.ai/artifact/81CxJitG8NQEDfYGHEZK4J
- 규제지역·토지거래허가구역 지도: [docs/regulated-areas-map.png](docs/regulated-areas-map.png) (10·15 대책 기준)
