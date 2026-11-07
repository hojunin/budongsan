"""고정 리포트 손상을 빌드 전에 차단하고 목록 캐시를 갱신한다."""
from pathlib import Path
import json
from report_package import verify_package, report_page

ROOT = Path(__file__).resolve().parents[1]


def verify_prepared(directory):
    for page in directory.glob('*.md'):
        package = directory / page.stem
        if package.is_dir() and (not verify_package(package) or page.read_text(encoding="utf-8") != report_page(page.stem, json.loads((package / "report.json").read_text(encoding="utf-8")))):
            raise ValueError(f'고정 리포트 검증 실패: {page.stem}')


if __name__ == '__main__':
    verify_prepared(ROOT / 'src' / 'reports')
    (ROOT / 'src' / '.observablehq' / 'cache' / 'data' / 'reports.json').unlink(missing_ok=True)
