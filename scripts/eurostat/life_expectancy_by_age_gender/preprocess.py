import pandas as pd
import re
import sys
path = 'demo_r_mlifexp.tsv'

def group_to_wide_form(data, col):
    """reorgnize the data of each statvars into independent columns """
    data_grouped = data.groupby([col])
    subsets = []
    for _, subset in data_grouped:
        pivot = subset[col].iloc[0]
        subset = subset.rename(columns = {'geo': pivot+'_geo',
            'year': pivot + '_year', 'life_expectancy': pivot})
        subset = subset.drop(columns = [col]).reset_index(drop=True)
        subsets.append(subset)
    data = pd.concat(subsets, axis=1, join = 'outer')
    return data

def nuts_to_iso(data):
    """convert nuts code to ISO Alpha3 code"""
    # no need in the future, can be resolved through ISO Alpha 2
    codes = pd.read_csv("./ISO_NUTS_country_map.csv")
    code_dict = codes.set_index('NUTS').to_dict()['Alpha-3 code']
    data['geo'] = data['geo'].map(code_dict)
    assert (~data['geo'].isnull()).all()
    return data

def preprocess(filepath):
    """preprocess the tsv file for import into DataCommons"""

    data = pd.read_csv(filepath, sep='\t')

    # concatenate columns of different years
    identifier = 'unit,sex,age,geo\\time'
    assert identifier in data.columns
    years = list(data.columns.values)
    years.remove(identifier)
    data = pd.melt(data, id_vars=identifier, value_vars=years, 
                   var_name='year', value_name='life_expectancy')

    # convert string to numbers, drop the lables
    data['year'] = data['year'].astype(int)
    num_null = data[data['life_expectancy'].isin([': ', ': e'])].shape[0]
    data['life_expectancy'] = data['life_expectancy'].str.extract("(\d+\.\d+|\d+)")
    assert num_null == data['life_expectancy'].isnull().sum()
    
    # generate the statvars
    data[['unit','sex','age','geo']] = data[identifier].str.split(',', expand=True)
    assert (data['unit'] == 'YR').all()
    data['sex'] = data['sex'].map({'F':'_Female','M':'_Male','T':''})
    assert (~data['sex'].isnull()).all()
    age_except = data['age'].isin(['Y_GE85','Y_LT1'])
    data.loc[age_except, 'age'] = data.loc[age_except, 'age'].map({
        'Y_GE85': '85OrMoreYears', 'Y_LT1': 'Upto1Years'})
    data.loc[~age_except,'age']= data.loc[~age_except, 'age'].str.replace('Y', '') + "Years"
    data = data.drop(columns=[identifier])
    data['StatVar'] = "LifeExpectancy_Person_" + data['age'] + data['sex']
    data = data.drop(columns=['unit', 'sex', 'age'])
    statvars = data['StatVar'].unique()

    # separate the country level and NUTS2 region data
    data_country = data[data['geo'].str.len() <= 2].reset_index(drop=True)
    data = data[~(data['geo'].str.len() <= 2)].reset_index(drop=True)

    # save the NUTS2 regions data
    data['geo'] = 'nuts/' + data['geo']
    data = group_to_wide_form(data, 'StatVar')
    data.to_csv(filepath[:-4]+'_cleaned.csv',index=False)
    
    # save the country level data
    data_country = nuts_to_iso(data_country)
    data_country['geo'] = 'Country/' + data_country['geo']
    data_country = group_to_wide_form(data_country, 'StatVar')
    data_country.to_csv(filepath[:-4]+'_country_cleaned.csv', index=False)
    return statvars

if __name__ == '__main__':
    preprocess(path)