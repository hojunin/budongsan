#!/bin/sh
# 주간 배치: 수집 → DB 백업(R2) → 빌드 → 배포. launchd(scripts/com.apt-insight.batch.plist)가 실행한다.
# 수동 실행: scripts/batch.sh
# 첫 수집은 API별 하루 9,000건씩 최신 달부터 과거로 채운다. 다 채울 때까지 하루 한 번씩 돌리면 된다.
set -eu
cd "$(dirname "$0")/.."
export PATH="$PWD/.venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
if [ -f .env ]; then set -a; . ./.env; set +a; fi
# 키 없이 돌면 샘플 데이터로 빌드돼 실데이터 사이트를 덮어쓴다.
: "${MOLIT_SERVICE_KEY:?.env 에 MOLIT_SERVICE_KEY 가 없습니다}"

mkdir data/.batch.lock 2>/dev/null || { echo "다른 배치가 실행 중입니다 (아니라면 data/.batch.lock 폴더를 지우세요)"; exit 1; }
trap 'rmdir data/.batch.lock' EXIT

echo "== $(date '+%F %T') 시작"
python scripts/fetch_molit.py
python scripts/fetch_kb.py
# ponytail: 월별 키로 덮어써서 1년에 12개가 쌓인다. wrangler 업로드는 파일당 약 300MB 까지라, DB 가 그보다 커지면 S3 API(rclone 등)로 바꾼다.
npx wrangler r2 object put "apt-insight-backup/apt-$(date +%Y-%m).duckdb" --file data/apt.duckdb --remote
npm run clean
npm run build
find dist -type f -size +24M -print -exec false {} +  # Cloudflare Pages 파일당 25 MiB
npm run deploy -- --branch=main
echo "== $(date '+%F %T') 완료"
