# 첫 집 데이터

국토부 실거래가·KB 지표로 지역과 관심 단지를 판단하는 정적 대시보드. 로컬 배치가 데이터를 DuckDB 파일(`data/apt.duckdb`)에 쌓고, Observable Framework로 빌드해 Cloudflare Pages에 올린다. 설계는 [DESIGN.md](DESIGN.md).

## 로컬 실행

Python은 3.12를 쓴다. Homebrew 기본 3.15에서는 pandas 2.2.3(PublicDataReader가 고정)이 죽는다.

```bash
npm install
uv venv -p 3.12 .venv && VIRTUAL_ENV=.venv uv pip install -r requirements.txt
PATH="$PWD/.venv/bin:$PATH" npm run dev   # http://127.0.0.1:3000 — DB가 없으면 '샘플 데이터'로 뜬다
```

## 데이터 수집과 배포 (로컬 배치)

1. 공공데이터포털에서 **국토교통부_아파트 매매 실거래가 상세 자료**, **국토교통부_아파트 전월세 실거래가 자료** 활용신청(자동승인).
2. 저장소 루트에 `.env` 를 만든다(Git에 올라가지 않는다).
   ```bash
   MOLIT_SERVICE_KEY=공공데이터포털 일반 인증키(Decoding)
   # 선택: 무인 실행에서 wrangler 로그인이 만료될 때를 대비한 API 토큰(Account · Cloudflare Pages · Edit, R2 · Edit)
   # CLOUDFLARE_API_TOKEN=...
   # CLOUDFLARE_ACCOUNT_ID=...
   ```
3. `npx wrangler login` (Cloudflare Pages 프로젝트 `apt-insight`, R2 버킷 `apt-insight-backup` 은 만들어져 있다).
4. 배치를 한 번 돌린다. 수집 → R2 백업 → 빌드 → 배포 순서다.
   ```bash
   scripts/batch.sh
   ```
   첫 수집은 최근 10년(매매 약 8,350건)이라 약 1시간 걸린다. 하루 9,000건 한도에 걸려 멈추면 다음 날 다시 돌리면 이어서 받는다.

### 주간 배치 등록 (launchd, 매주 월요일 09:17)

```bash
sed "s#__ROOT__#$PWD#g" scripts/com.apt-insight.batch.plist > ~/Library/LaunchAgents/com.apt-insight.batch.plist && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.apt-insight.batch.plist
```

로그는 `data/batch.log`. 해제: `launchctl bootout gui/$(id -u)/com.apt-insight.batch`.

GitHub Actions(`build-check`)는 push·PR마다 샘플 데이터로 빌드만 확인하고 배포하지 않는다.

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
