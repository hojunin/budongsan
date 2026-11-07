import pandas as pd


def direct_status(values):
    return values.astype('string').str.strip().map({'직거래': True, '중개거래': False}).astype('boolean')


def rent_status(monthly):
    return monthly.eq(0).where(monthly.notna(), pd.NA).astype('boolean')
