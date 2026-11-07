import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src' / 'data'))
from _normalize import direct_status, rent_status
assert direct_status(pd.Series(['직거래', '중개거래', '', None, '기타'])).tolist() == [True, False, pd.NA, pd.NA, pd.NA]
assert rent_status(pd.Series([0, 10, None])).tolist() == [True, False, pd.NA]
print('ok')
