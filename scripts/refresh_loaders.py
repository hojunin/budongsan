"""정규화 코드가 바뀐 경우 생성 캐시만 무효화한다."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def invalidate_stale(cache, sources):
    if cache.exists() and any(source.stat().st_mtime_ns > cache.stat().st_mtime_ns for source in sources):
        cache.unlink()
        return True
    return False


if __name__ == '__main__':
    data = ROOT / 'src' / 'data'
    cache = ROOT / 'src' / '.observablehq' / 'cache' / 'data'
    for name in ('trades', 'rents'):
        invalidate_stale(cache / f'{name}.parquet', [data / f'{name}.parquet.py', data / '_normalize.py', data / '_db.py'])
