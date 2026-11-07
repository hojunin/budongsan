import os, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from refresh_loaders import invalidate_stale
with tempfile.TemporaryDirectory() as d:
    root=Path(d); loader=root/'loader.py'; shared=root/'shared.py'; cache=root/'data.parquet'
    for p in (loader,shared,cache): p.write_text('fixture')
    os.utime(cache,(100,100)); os.utime(loader,(200,200)); os.utime(shared,(50,50))
    assert invalidate_stale(cache,[loader,shared]) is True and not cache.exists()
    cache.write_text('fixture'); os.utime(cache,(300,300))
    assert invalidate_stale(cache,[loader,shared]) is False and cache.exists()
print('ok')
