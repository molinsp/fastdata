# AUTOGENERATED! DO NOT EDIT! File to edit: 00_core.ipynb (unless otherwise specified).

__all__ = ['FastDataUtilities', 'FastDataUtilities', 'generate_function_call_from_form']

# Cell
import pandas as pd
import numpy as np
import re

@pd.api.extensions.register_dataframe_accessor('fdt')
class FastDataUtilities:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def flatten_multiindex(self,axis='all'):
        df = self._obj.copy()
        if 'MultiIndex' in str(type(df.columns)) and axis in ('all', 'columns'):
            df.columns = df.columns.map(lambda x: '_'.join([str(i) for i in x]))
        if 'MultiIndex' in str(type(df.index)) and axis in ('all', 'index'):
            df = df.reset_index()
        return df

# Cell
@pd.api.extensions.register_series_accessor('fdt')
class FastDataUtilities:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def find_between_text(self, start_string, end_string):
        series = self._obj
        search_expr = start_string + '(.*)' + end_string
        series = series.str.extract(search_expr)
        return series

    def extract_number_from_string(self, dtype):
        series = self._obj
        series = series.str.extract('(\d+)')
        series = series.astype(dtype)
        return series

# Cell
def generate_function_call_from_form(formReponse, dataframeSelection):
    formData = formReponse["formData"];
    transformationSelection = formReponse["schema"]["function"];
    callerObject =  formReponse["schema"]["callerObject"];
    series = ''

    if 'DataFrame' in callerObject:
        callerObject = callerObject.replace('DataFrame', dataframeSelection)
    if 'Series' in callerObject:
        seriesString = '"' + formData['column'] +'"'
        series = '[' + seriesString + ']'
        callerObject = callerObject.replace('Series',seriesString)

    formula = callerObject + '.' + transformationSelection + '('

    variable = ''
    for key in formData:
        parameterPrefix = '\n    '
        # Check for a codegen style
        if("codegenstyle" in formReponse["schema"]["properties"][key]):
            codegenstyle = formReponse["schema"]["properties"][key]['codegenstyle']
            if codegenstyle == 'variable':
                # Remove qutations
                formula = formula + parameterPrefix + key + '=' + str(formData[key]) + ', '
            elif codegenstyle == 'array':
                # Add brackets []
                formula = formula + parameterPrefix + key + '=' + str(formData[key]) + ', '
            elif codegenstyle == 'aggregation':
                # Process aggregations for function merge
                aggregationDict = '{'
                for dict in formData["aggfunc"]:
                    aggregationDict = aggregationDict + '"' + dict["column"] + '" : ' + str(dict["function"]).replace('"', '') + ', '

                aggregationDict = aggregationDict[0: len(aggregationDict) - 2];
                aggregationDict = aggregationDict + '}'
                aggregationDict = parameterPrefix + 'aggfunc=' + aggregationDict
                formula = formula + aggregationDict + ', '
        else:
            if key == 'New table':
                variable = formData[key]
            else:
                formula = formula + parameterPrefix + key + '="' + str(formData[key]) + '", '

    if(variable == '' and dataframeSelection != 'None'):
        variable = dataframeSelection
    elif(dataframeSelection == 'None'):
        variable = 'data'

    # Remove last comma and space given there are no more parameters
    formula = formula[0: len(formula) - 2];
    # Close parenthesis
    formula = formula + ')'
    # Finalize formula
    formula = variable + series + ' = ' + formula;
    return formula