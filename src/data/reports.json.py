"""데이터 로더: 발행한 리포트(src/reports/*.md)의 머리말 목록 → JSON. index.md 와 _ 로 시작하는 파일은 뺀다."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "src" / "reports"
sys.path.insert(0, str(ROOT / "scripts"))
from report_package import verify_package


def front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    head = text.split("---", 2)[1]
    meta = {}
    for line in head.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip():
            meta[key.strip()] = value.strip().strip('"')
    return meta


def list_reports(directory):
    posts = []
    for f in sorted(directory.glob("*.md"), reverse=True):
        if f.name == "index.md" or f.name.startswith("_"):
            continue
        package = directory / f.stem
        if package.is_dir():
            if not verify_package(package):
                raise ValueError(f"리포트 패키지 검증 실패: {f.stem}")
            doc = json.loads((package / "report.json").read_text(encoding="utf-8"))
            manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
            posts.append({"slug": f.stem, "title": doc["title"], "date": manifest["capture_at"][:10], "summary": doc["summary"], "tags": "고정 근거"})
        else:
            meta = front_matter(f.read_text(encoding="utf-8"))
            posts.append({"slug": f.stem, "title": meta.get("title", f.stem), "date": meta.get("date", f.stem[:10]),
                          "summary": meta.get("summary", ""), "tags": meta.get("tags", "")})
    return sorted(posts, key=lambda post: post["date"], reverse=True)


if __name__ == "__main__":
    json.dump(list_reports(DIR), sys.stdout, ensure_ascii=False)
