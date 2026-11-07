import sys, tempfile
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).parent))
from verify_public_data import verify_public_data
with tempfile.TemporaryDirectory() as d:
    p=Path(d)/'trades.parquet'
    pd.DataFrame({'is_sample':[False,False]}).to_parquet(p)
    verify_public_data(Path(d))
    pd.DataFrame({'is_sample':[False,True]}).to_parquet(p)
    try: verify_public_data(Path(d))
    except ValueError: pass
    else: raise AssertionError('synthetic public data accepted')
    pd.DataFrame({'is_sample':[None]}).to_parquet(p)
    try: verify_public_data(Path(d))
    except ValueError: pass
    else: raise AssertionError('unknown sample status accepted')
print('ok')
