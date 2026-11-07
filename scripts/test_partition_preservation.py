import sys
from pathlib import Path
import duckdb
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from fetch_kb import save_partition
from fetch_rone import save_regions

con = duckdb.connect()
con.execute('CREATE TABLE kb_buyer_index ("지역코드" VARCHAR, "값" INTEGER)')
con.execute("INSERT INTO kb_buyer_index VALUES ('11', 1), ('41', 2)")
save_partition(con, 'buyer_index', '11', pd.DataFrame({'지역코드':['11'], '값':[3]}))
assert con.execute('SELECT * FROM kb_buyer_index ORDER BY 1').fetchall() == [('11',3),('41',2)]
con.execute('CREATE TABLE rone (metric VARCHAR, cycle VARCHAR, period VARCHAR, period_desc VARCHAR, region VARCHAR, region_full VARCHAR, item VARCHAR, unit VARCHAR, value DOUBLE)')
con.execute("INSERT INTO rone VALUES ('m','MM','202601','', '서울','서울','합계','건',1), ('m','MM','202601','', '경기','경기','합계','건',2)")
df = pd.DataFrame([['m','MM','202601','', '서울','서울','합계','건',3]], columns=['metric','cycle','period','period_desc','region','region_full','item','unit','value'])
save_regions(con, 'm', '202601', df)
assert con.execute('SELECT region,value FROM rone ORDER BY region').fetchall() == [('경기',2),('서울',3)]
print('ok')
# Discovery contains two groups; a successful empty group must not erase its old rows.
import fetch_rone as rone
from unittest.mock import patch
base = {'WRTTIME_IDTFR_ID':'202601','WRTTIME_DESC':'2026년 1월','GRP_NM':'서울','GRP_FULLNM':'서울','CLS_NM':'합계','CLS_FULLNM':'합계','ITM_NM':'건','ITM_FULLNM':'건','UI_NM':'건','DTA_VAL':7}
def fetch(_key, _table, _cycle, **kw):
    if 'GRP_ID' not in kw: return [{'GRP_ID':'seoul','GRP_FULLNM':'서울'}, {'GRP_ID':'gyeonggi','GRP_FULLNM':'경기'}]
    return [base] if kw['GRP_ID'] == 'seoul' else []
with patch.object(rone, 'fetch_rows', side_effect=fetch):
    part = rone.fetch_table('key','table','MM','202601',True)
part.insert(0,'cycle','MM'); part.insert(0,'metric','m')
save_regions(con, 'm', '202601', part)
assert con.execute('SELECT region,value FROM rone ORDER BY region').fetchall() == [('경기',2),('서울',7)]
try: save_partition(con, 'buyer_index', '41', pd.DataFrame())
except ValueError: pass
else: raise AssertionError('empty KB region accepted')
assert con.execute('SELECT * FROM kb_buyer_index ORDER BY 1').fetchall() == [('11',3),('41',2)]
