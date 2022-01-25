# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''
gets population (age 0 to 25) data for all world bank countries, and makes a csv acording to TMCF
'''

import requests
import pandas as pd
from absl import app
from absl import flags
from util import statvar_dcid_generator

FLAGS = flags.FLAGS
flags.DEFINE_integer("age", 2, "Age to which this program is run, max value 26")
flags.DEFINE_list("gender", ["FE", "MA"], "Gender: FE for female, MA for male")
flags.DEFINE_string("country", "USA", "Country codes")
#maximum the API Can display is 32767
flags.DEFINE_integer("per_page", 32, "rows per page")
flags.DEFINE_string("output_csv", "WorldBankHNP_Population_Tests",
                    "Path of final csv")


def get_df(serieses, per_page, country):
    '''
    gets df by iteratively running code for each country + series
    '''
    df2 = pd.DataFrame
    df2 = pd.DataFrame(columns=[
        'Series Name', 'Series Code', 'Country Code', 'Country', 'Year', 'Value'
    ])
    for current_series in serieses:
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{current_series}?"
        url = url + f"format=JSON&per_page={per_page}"
        response = requests.get(url)
        response = response.json()
        for counter in range(len(response[1])):
            row = 0
            val = response[1][counter]['value']
            if val is None:
                val = "unavaliable"
            row = {
                "Series Name": response[1][counter]['indicator']['value'],
                "Series Code": response[1][counter]['indicator']['id'],
                "Country Code": response[1][counter]['countryiso3code'],
                "Country": response[1][counter]['country']['value'],
                "Year": response[1][counter]['date'],
                'Value': val
            }
            df2.loc[len(df2)] = row
    return df2


def get_statvars(gender, age):
    property_dict = {
        'typeOf': 'dcs:StatisticalVariable',
        'description': f'Age population, {gender}, Age {age}, interpolated',
        'populationType': 'dcs:Person',
        'measuredProperty': 'dcs:count',
        'gender': f'dcs:{gender}',
        'statType': 'dcs:measuredValue',
        'age': f'[Years {age}]'
    }
    dcid = statvar_dcid_generator.get_statvar_dcid(property_dict)
    return (dcid)


def get_csv(df_in, df_out_path):
    """Creation of csv according to tmcf:"""
    df2 = pd.DataFrame(columns=[
        'observationAbout', 'observationDate', "StatisticalVariable", 'value'
    ])
    for line in range(len(df_in)):
        gender, statvar = '', ''
        gender = df_in['Series Name'][line].split(',')[-2].strip()
        gender = gender[0].upper() + gender[1:]
        age = df_in['Series Name'][line].split(',')[-3].strip().split()[-1]
        statvar = get_statvars(gender, age)
        addto_df2 = [
            "country/" + df_in['Country Code'][line], df_in['Year'][line],
            statvar, df_in['Value'][line]
        ]
        df2.loc[len(df2.index)] = addto_df2
    df2.to_csv(df_out_path)
    print(df2.head())


def get_mcf(series_lst, path="World_bank_hnp_population.mcf"):
    '''
    gets mcf by splitting description and using fstrings
    '''
    nodes = []
    with open(path, 'w', encoding='utf-8') as file:
        mcf = ''
        for current_series in series_lst:
            print('\n' + current_series)
            node, age, gender = '', '', ''
            age = current_series[9:11]
            gender = ''
            if 'MA' in current_series:
                gender = 'Male'
            else:
                gender = 'Female'
            property_dict = {
                'typeOf':
                    'dcs:StatisticalVariable',
                'description':
                    f'Age population, {gender}, Age {age}, interpolated',
                'populationType':
                    'dcs:Person',
                'measuredProperty':
                    'dcs:count',
                'gender':
                    f'dcs:{gender}',
                'statType':
                    'dcs:measuredValue',
                'age':
                    f'[Years {age}]'
            }
            node = get_statvars(gender, age)
            desc = f'Age population, age {age}, {gender.lower()}, interpolated'
            nodes.append(node)
            property_dict['node'] = node

            for i in property_dict:
                mcf = mcf + f'{i}:' + f' {property_dict[i]}\n'
        file.write(mcf)


def main(argv):
    series = [
        f"SP.POP.AG{age:02d}.{gender}.IN" for age in range(FLAGS.age)
        for gender in (FLAGS.gender)
    ]
    get_mcf(series)
    df = get_df(series, FLAGS.per_page, FLAGS.country)
    get_csv(df, FLAGS.output_csv)


def process(max_age, out_file, per_page=17, country='USA'):
    series = [
        f"SP.POP.AG{age:02d}.{gender}.IN" for age in range(max_age)
        for gender in ['FE', 'MA']
    ]
    print(series)
    get_mcf(series, "WorldBankHNP_Population_Tests.mcf")
    df = get_df(series, per_page, country)
    get_csv(df, out_file)


if __name__ == '__main__':
    app.run(main)
