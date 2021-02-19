# AUTOGENERATED! DO NOT EDIT! File to edit: 01_integrations.ipynb (unless otherwise specified).

__all__ = ['airtable_base_to_df', 'df_to_airtable_base', 'update_airtable_records', 'cast_for_gsheets', 'gsheet_to_df',
           'df_to_gsheet']

# Cell
from airtable import Airtable
import pandas as pd
import gspread
from gspread_pandas import Spread
from pathlib import Path
import numpy as np

# Cell
def airtable_base_to_df(base, table, key, include_id=False):
    airtable_base = Airtable(base, table, key)
    records = airtable_base.get_all()

    if include_id == True:
        records_with_id = []
        for r in records:
            record_with_id = {'id': r['id']}
            fields = r['fields']
            record_with_id.update(fields)
            records_with_id.append(record_with_id)
        return pd.DataFrame.from_records(records_with_id)
    else:
        return pd.DataFrame.from_records((r['fields'] for r in records))

# Cell
def df_to_airtable_base(data, base, table, key):
    airtable_base = Airtable(base, table, key)
    airtable_base.batch_insert(data.fillna('').to_dict(orient='records'))

# Cell
def update_airtable_records(base, table, key, df, record_id_col='id'):
    airtable_base = Airtable(base, table, key)
    records = df.to_dict(orient='records')
    for r in records:
        record_id = r[record_id_col]
        del r[record_id_col]
        airtable_base.update(record_id, r)

# Cell
def cast_for_gsheets(df):
    # casting as string if not serializable
    for column, dt in zip(df.columns, df.dtypes):
        if dt.type not in [
            np.int64,
            np.float_,
            np.bool_,
        ]:
            df.loc[:, column] = df[column].astype(str)
    return df

# Cell
def gsheet_to_df(url, index=None, header_rows=1, start_row=1, unformatted_columns=None,
                 formula_columns=None, sheet=None, creds=None):
    gsheet = Spread(url, sheet=sheet, creds=creds)
    return gsheet.sheet_to_df(index, header_rows, start_row, unformatted_columns, formula_columns, sheet)

# Cell
def df_to_gsheet(url, df, append=False, index=True, headers=True, start=(1, 1), replace=False, sheet=None,
                 raw_column_names=None, raw_columns=None, freeze_index=False, freeze_headers=False,
                 fill_value='', add_filter=False, merge_headers=False, flatten_headers_sep=None, creds=None):
    if append==False:
        gsheet = Spread(url, sheet=sheet, creds=creds)
        gsheet.df_to_sheet(df, index, headers, start, replace, sheet,
                     raw_column_names, raw_columns, freeze_index, freeze_headers,
                     fill_value, add_filter, merge_headers, flatten_headers_sep)
    elif append==True:
        # Fall-back to gspread given there is no high-level function available in gspread pandas
        if creds==None:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            home = str(Path.home())
            gc = gspread.service_account(filename= home + '/.config/gspread_pandas/google_secret.json',  scopes=scopes)
        else:
            gc = gspread.authorize(creds)
        ws = gc.open_by_url(url)
        df = cast_for_gsheets(df)
        df = df.fillna('')
        values = df.values.tolist()
        #
        if type(sheet) == int:
            ss = ws.get_worksheet(sheet)
        elif type(sheet) == str:
            ss = ws.worksheet(sheet)

        if ss == None:
            raise Exception('Could not find sheet (tab). Check the sheet number exists (first sheet is 0).')
        else:
            ss.append_rows(values, value_input_option='USER_ENTERED', insert_data_option='INSERT_ROWS')