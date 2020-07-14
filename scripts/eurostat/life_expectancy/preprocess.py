import pandas as pd
import re

PATH = 'demo_r_mlifexp.tsv'

def nuts_to_iso(data):
    """Convert nuts code to ISO Alpha3 code"""
    ISO_2_TO_3_PATH = ('https://gist.githubusercontent.com/tadast/8827699/raw/'
                       '3cd639fa34eec5067080a61c69e3ae25e3076abb/'
                       'countries_codes_and_coordinates.csv')
    codes = pd.read_csv(ISO_2_TO_3_PATH)
    codes["Alpha-2 code"] = codes["Alpha-2 code"].str.extract(r'"([a-zA-Z]+)"')
    codes["Alpha-3 code"] = codes["Alpha-3 code"].str.extract(r'"([a-zA-Z]+)"')
    codes["NUTS"] = codes["Alpha-2 code"]
    codes.loc[codes["NUTS"] == "GR", "NUTS"] = "EL"
    codes.loc[codes["NUTS"] == "GB", "NUTS"] = "UK"
    code_dict = codes.set_index('NUTS').to_dict()['Alpha-3 code']
    data.loc[data.index,'geo'] = data['geo'].map(code_dict)
    assert (~data['geo'].isnull()).all()
    return data

def preprocess(filepath):
    """Preprocess the tsv file for importing into DataCommons."""
    data = pd.read_csv(filepath, sep='\t')

    # concatenate data of different years from multiple columns into one column
    identifier = 'unit,sex,age,geo\\time'
    assert identifier in data.columns
    years = list(data.columns.values)
    years.remove(identifier)
    data = pd.melt(data, id_vars=identifier, value_vars=years, 
                   var_name='year', value_name='life_expectancy')

    # format string into desired format, drop the labels
    data['year'] = data['year'].astype(int) #remove the spaces
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

    # convert the nuts codes to dcids 
    data_country = data[data['geo'].str.len() <= 2]
    data_nuts = data[~(data['geo'].str.len() <= 2)]
    data_country = nuts_to_iso(data_country) # convert nuts code to ISO Alpha-3
    data.loc[data_country.index,'geo'] = 'country/' + data_country['geo']
    data.loc[data_nuts.index, 'geo'] = 'nuts/' + data_nuts['geo']

    # separate data of different StatVars from one column into multiple columns
    # for exmple: 
    # geo       year  StatVar           sv1_geo   sv1_year   sv2_geo   sv2_year
    # nuts/AT1  2018  sv1         =>    nuts/AT1  2018      nuts/AT2   2018
    # nuts/AT2  2018  sv2
    data_grouped = data.groupby('StatVar')
    subsets = []
    for _, subset in data_grouped:
        pivot = subset['StatVar'].iloc[0] # get the statvar name
        subset = subset.rename(columns = {'geo': pivot+'_geo',
            'year': pivot + '_year', 'life_expectancy': pivot})
        subset = subset.drop(columns = ['StatVar']).reset_index(drop=True)
        subsets.append(subset)
    data = pd.concat(subsets, axis=1, join = 'outer')

    # save the processed data
    data.to_csv(filepath[:-4]+'_cleaned.csv',index=False)
    return 

if __name__ == '__main__':
    preprocess(PATH)