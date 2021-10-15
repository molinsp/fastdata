# AUTOGENERATED! DO NOT EDIT! File to edit: 00_core.ipynb (unless otherwise specified).

__all__ = ['is_default_index', 'is_multiindex_row_df', 'is_multiindex_col_df', 'regex_pattern',
           'FastDataDataframeUtilities', 'split_list_to_columns', 'pivot_table', 'list_length', 'clean_text_columns',
           'count_nulls', 'fill_empty', 'FastDataSeriesUtilities', 'clean_text_column', 'bin_column', 'fill_empty',
           'replace_based_on_condition', 'extract_json', 'add_timedelta']

# Cell
import pandas as pd
import numpy as np
import re
import json
from fastcore.all import *
import jmespath

# Cell
def is_default_index(df):
    # Check if the index is the same as the default index. We use the name as a proxy
    check_index = ((df.index == pd.RangeIndex(start=0,stop=df.shape[0], step=1)).all())
    return check_index

# Cell
def is_multiindex_row_df(df):
    if isinstance(df, pd.core.frame.DataFrame):
        if isinstance(df.index, pd.core.indexes.multi.MultiIndex):
            return True
    return False

# Cell
def is_multiindex_col_df(df):
    if isinstance(df, pd.core.frame.DataFrame):
        if isinstance(df.columns, pd.core.indexes.multi.MultiIndex):
            return True
    return False

# Cell
def regex_pattern(mode, **kwargs):
    if mode == 'keep_before_character':
        # keep everything before a character
        character = re.escape(kwargs['character'])
        result = '(.*)' + character + '.*'
        return result
    if mode == 'keep_after_character':
        # keep everything after a character
        character = re.escape(kwargs['character'])
        result = '.*' + character + '(.*)'
        return result
    if mode == 'email':
        return '([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)'
    if mode == 'extract_number':
        # E.g. for extracting zip codes
        return '(\d+)'
    if mode == 'n_digits':
        # E.g. for extracting zip codes
        return '(\d{' + kwargs['digits'] + '})'
    if mode == 'between':
        return re.escape(kwargs['start']) + '(.*)' + re.escape(kwargs['end'])
    if mode == 'range_start':
        return "(-?\d*[.,]?\d*) ?- ?-?\d*[.,]?\d*"
    if mode == 'range_end':
        return "-?\d*[.,]?\d* ?- ?(-?\d*[.,]?\d*)"

# Cell
@pd.api.extensions.register_dataframe_accessor('fdt')
class FastDataDataframeUtilities:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def remove_indexes(self,axis='all'):
        df = self._obj.copy()
        if is_multiindex_col_df(df) and axis in ['columns','all']:
            df.columns = df.columns.map(lambda x: '_'.join([str(i) for i in x]))
        if ((is_multiindex_row_df(df)) or (is_default_index(df) == False)) and axis in ['index','all']:
            df = df.reset_index()
        return df

# Cell
@patch_to(FastDataDataframeUtilities)
def split_list_to_columns(self, column, separator=',', list_marker=None, split_type='unique', keep_original_col=False):
    df = self._obj.copy()

    type_of_first_not_null_element = type(df[column][df[column].notnull()][0])

    # First check if it is already a list or it needs pre-processing
    if(type_of_first_not_null_element != list):
        # Remove whitespaces
        df[column] = df[column].str.replace(', ', ',')

        # If not, let's start processing it
        # First we process the surrounding brackets, if they exist
        if list_marker != 'na':
            if list_marker == 'square_brackets':
                df[column] = df[column].str.replace(r"[\[\]']","", regex=True)
            elif list_marker == 'parentheses':
                df[column] = df[column].str.replace(r'([()])','', regex=True)
        # Then we process the separator only if we take the unique
        if split_type == 'unique':
            df[column] = df[column].str.split(separator)


    if split_type == 'unique':
        exploded = df[column].explode()
        dummy_exploded = pd.crosstab(index=exploded.index, columns=exploded)
        if '' in dummy_exploded.columns:
            dummy_exploded = dummy_exploded.rename(columns={'':'blank'})

        if keep_original_col == False:
            df = df.drop(column, axis=1)

        result = df.join(dummy_exploded)
        result = result.fillna(0)
    elif split_type == 'order':
        split = df[column].str.split(separator, expand=True)

        if keep_original_col == False:
            df = df.drop(column, axis=1)

        result = df.join(split)

    result.columns = result.columns.map(str)
    return result

# Cell
@patch_to(FastDataDataframeUtilities)
def pivot_table(self, index_type='flat', **kwargs):
    df = self._obj.copy()

    df = df.pivot_table(**kwargs)

    if index_type == 'flat':
        return df.fdt.remove_indexes(axis='all')
    else:
        return df

# Cell
@patch_to(FastDataDataframeUtilities)
def list_length(self, column, separator=','):
    df = self._obj.copy()

    df['len_'+str(column)] = df[column].apply(lambda x: 0 if x == '' else len(x.split(separator)))

    return df

# Cell
@patch_to(FastDataDataframeUtilities)
def clean_text_columns(self, columns, regex=False, keep_unmatched=False, mode='custom', **kwargs):
    df = self._obj.copy()

    for col_name in columns:

        if mode != 'custom':
            regex = regex_pattern(mode, **kwargs)

        if keep_unmatched == False:
            df[col_name] = df[col_name].str.extract(regex, expand=False)
        elif keep_unmatched == True:
            # Boolean array that tracks when there is a match, e.g. [T, F, T]
            matched = df[col_name].str.contains(regex)
            # Extract the regular expresion r for the matches with NaN for non-matches, e.g. [r, NaN, r]
            extracted = df[col_name].str.extract(regex, expand=False)
            # For the cases where matched is true, replace with the match, leaving [r, original, r]
            df[col_name] = df[col_name].mask(cond=matched, other=extracted)
    return df

# Cell
@patch_to(FastDataDataframeUtilities)
def count_nulls(self):
    df = self._obj.copy()
    null_count = df.isnull().sum()
    null_percentage = null_count / len(df) * 100.0
    return pd.DataFrame({'null_count': null_count, 'null_percent': null_percentage}).reset_index().rename(columns={'index':'column'})

# Cell
@patch_to(FastDataDataframeUtilities)
def fill_empty(self, **kwargs):
    df = self._obj.copy()
    p = kwargs
    if p['mode'] == 'function':
        if p['function'] == 'ffill':
            df = df.fillna(method='ffill')
        elif p['function'] == 'bfill':
            df = df.fillna(method='bfill')
        elif p['function'] == 'mean':
            df = df.fillna(df.mean())
        elif p['function'] == 'most_frequent':
            df = df.fillna(df.mode().iloc[0])
        elif p['function'] == 'median':
            df = df.fillna(df.median())
    elif p['mode'] == 'value':
        df = df.fillna(p['value'])

    return df

# Cell
@pd.api.extensions.register_series_accessor('fdt')
class FastDataSeriesUtilities:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

# Cell
@patch_to(FastDataSeriesUtilities)
def clean_text_column(self, regex=False, keep_unmatched = True, mode='custom', **kwargs):
    series = self._obj

    if mode != 'custom':
        regex = regex_pattern(mode, **kwargs)

    if keep_unmatched == False:
        series = series.str.extract(regex, expand=False)
    elif keep_unmatched == True:
        # Boolean array that tracks when there is a match, e.g. [T, F, T]
        matched = series.str.contains(regex)
        # Extract the regular expresion r for the matches with NaN for non-matches, e.g. [r, NaN, r]
        extracted = series.str.extract(regex, expand=False)
        # For the cases where matched is true, replace with the match, leaving [r, original, r]
        series = series.mask(cond=matched, other=extracted)

    return series

# Cell
@patch_to(FastDataSeriesUtilities)
def bin_column(self, **kwargs):
    series = self._obj
    #Parameters
    p = kwargs
    if p['mode'] == 'size':
        interval_range = pd.interval_range(start=p['start'], freq=p['size'], end=p['end'])
        #print(interval_range)
        series = pd.cut(series, bins=interval_range)
        return series

    if p['mode'] == 'number':
        series = pd.cut(series, bins=p['bin_number'])
        return series

    if p['mode'] == 'quantiles':
        series = pd.qcut(series, q=p['quantiles'])
        return series

    if p['mode'] == 'custom':
        interval_range=pd.IntervalIndex.from_breaks(p['breaks'], closed=p['closed'])
        series = pd.cut(series, bins= interval_range)
        return series

# Cell
@patch_to(FastDataSeriesUtilities)
def fill_empty(self, **kwargs):
    series = self._obj
    p = kwargs
    if p['mode'] == 'function':
        if p['function'] == 'ffill':
            series = series.fillna(method='ffill')
        elif p['function'] == 'bfill':
            series = series.fillna(method='bfill')
        elif p['function'] == 'mean':
            series = series.fillna(series.mean())
        elif p['function'] == 'most_frequent':
            series = series.fillna(series.mode()[0])
        elif p['function'] == 'median':
            series = series.fillna(series.median())
    elif p['mode'] == 'value':
        series = series.fillna(p['value'])

    return series

# Cell
@patch_to(FastDataSeriesUtilities)
def replace_based_on_condition(self, cond, when, replace_with=np.NaN):
    series = self._obj

    if when == True:
        series = series.mask(cond=cond, other=replace_with)
    elif when == False:
        series = series.where(cond=cond, other=replace_with)

    return series

# Cell
@patch_to(FastDataSeriesUtilities)
def extract_json(self, path):
    series = self._obj
    # Try to understand if it is a dict already or not
    type_of_first_not_null_element = type(series[series.notnull()][0])
    if type_of_first_not_null_element == str:
        series = series.apply(lambda x: jmespath.search(path,json.loads(x)))
    elif type_of_first_not_null_element == dict:
        series = series.apply(lambda x: jmespath.search(path,x))
    return series

# Cell
@patch_to(FastDataSeriesUtilities)
def add_timedelta(self, value, unit=None, **kwargs):
    series = self._obj
    return series + pd.Timedelta(value, unit=None, **kwargs)