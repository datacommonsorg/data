# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pandas as pd
import re

PATH = 'demo_r_mlifexp.tsv'


def nuts_to_iso(data):
    """Convert 2-letter NUTS codes for countries to ISO 3166-1 alpha-3 codes."""
    ISO_2_TO_3_PATH = ('./countries_codes_and_coordinates.csv')
    codes = pd.read_csv(ISO_2_TO_3_PATH)
    codes["Alpha-2 code"] = codes["Alpha-2 code"].str.extract(r'"([a-zA-Z]+)"')
    codes["Alpha-3 code"] = codes["Alpha-3 code"].str.extract(r'"([a-zA-Z]+)"')
    # NUTS code matches ISO 3166-1 alpha-2 with two exceptions
    codes["NUTS"] = codes["Alpha-2 code"]
    codes.loc[codes["NUTS"] == "GR", "NUTS"] = "EL"
    codes.loc[codes["NUTS"] == "GB", "NUTS"] = "UK"
    code_dict = codes.set_index('NUTS').to_dict()['Alpha-3 code']
    data.loc[data.index, 'geo'] = data['geo'].map(code_dict)
    assert (~data['geo'].isnull()).all()
    return data


def obtain_value(entry):
    """Extract value from entry. 
    The entries could be like: '81.6', ': ', '79.9 e', ': e'.
    """
    entry = entry.split(' ', maxsplit=-1)[0]  # Discard notes.
    if not entry or entry == ':':
        return None
    return float(entry)


def preprocess(filepath):
    """Preprocess the tsv file for importing into DataCommons."""
    data = pd.read_csv(filepath, sep='\t')

    # Concatenate data of different years from multiple columns into one column.
    identifier = 'unit,sex,age,geo\\time'
    assert identifier in data.columns
    years = list(data.columns.values)
    years.remove(identifier)
    data = pd.melt(data,
                   id_vars=identifier,
                   value_vars=years,
                   var_name='year',
                   value_name='life_expectancy')

    # Format string into desired format.
    data['year'] = data['year'].astype(int)  # remove spaces, e.g. "2018 "
    data['life_expectancy'] = data['life_expectancy'].apply(obtain_value)

    # Generate the statvars that each row belongs to.
    data[['unit', 'sex', 'age',
          'geo']] = data[identifier].str.split(',', expand=True)
    assert (data['unit'] == 'YR').all()
    data['sex'] = data['sex'].map({'F': '_Female', 'M': '_Male', 'T': ''})
    assert (~data['sex'].isnull()).all()
    age_except = data['age'].isin(['Y_GE85', 'Y_LT1'])
    data.loc[age_except, 'age'] = data.loc[age_except, 'age'].map({
        'Y_GE85': '85OrMoreYears',
        'Y_LT1': 'Upto1Years'
    })
    data.loc[~age_except, 'age'] = data.loc[~age_except, 'age'].str.replace(
        'Y', '') + "Years"
    data = data.drop(columns=[identifier])
    data['StatVar'] = "LifeExpectancy_Person_" + data['age'] + data['sex']
    data = data.drop(columns=['unit', 'sex', 'age'])
    statvars = data['StatVar'].unique()

    # Convert the nuts codes to dcids
    data_country = data[data['geo'].str.len() <= 2]
    data_nuts = data[~(data['geo'].str.len() <= 2)]
    data_country = nuts_to_iso(
        data_country)  # convert nuts code to ISO 3166-1 alpha-3
    data.loc[data_country.index, 'geo'] = 'dcid:country/' + data_country['geo']
    data.loc[data_nuts.index, 'geo'] = 'dcid:nuts/' + data_nuts['geo']

    # Separate data of different StatVars from one column into multiple columns
    # For example:
    # geo       year  StatVar           sv1_geo   sv1_year   sv2_geo   sv2_year
    # nuts/AT1  2018  sv1         =>    nuts/AT1  2018      nuts/AT2   2018
    # nuts/AT2  2018  sv2
    data_grouped = data.groupby('StatVar')
    subsets = []
    for _, subset in data_grouped:
        pivot = subset['StatVar'].iloc[0]  # get the statvar name
        subset = subset.rename(
            columns={
                'geo': pivot + '_geo',
                'year': pivot + '_year',
                'life_expectancy': pivot
            })
        subset = subset.drop(columns=['StatVar']).reset_index(drop=True)
        subsets.append(subset)
    data = pd.concat(subsets, axis=1, join='outer')

    # Save the processed data into CSV file.
    data.to_csv(filepath[:-4] + '_cleaned.csv', index=False)
    return


if __name__ == '__main__':
    preprocess(PATH)
