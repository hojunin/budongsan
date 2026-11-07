"""공개 전 빌드 산출물에서 합성 거래·임대·KB 관측을 차단한다."""
from pathlib import Path
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]


def verify_public_data(directory):
    for path in directory.rglob('*.parquet'):
        if not any(path.name.startswith(prefix) for prefix in ('trades.', 'rents.', 'kb.')) and path.name not in ('trades.parquet', 'rents.parquet', 'kb.parquet'):
            continue
        schema = pq.read_schema(path)
        if 'is_sample' not in schema.names:
            raise ValueError(f'합성 여부 미상: {path.name}')
        values = pq.read_table(path, columns=['is_sample']).column('is_sample')
        if any(value is not False for value in values.to_pylist()):
            raise ValueError(f'합성 또는 미확인 관측: {path.name}')


if __name__ == '__main__':
    verify_public_data(ROOT / 'dist')
