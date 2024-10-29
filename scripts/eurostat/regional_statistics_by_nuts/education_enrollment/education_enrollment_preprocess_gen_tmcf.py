# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys

sys.path.insert(1, '../../../../util')
from six.moves import urllib
from alpha2_to_dcid import COUNTRY_MAP
from nuts_codes_names import NUTS1_CODES_NAMES
import numpy as np
import pandas as pd
import io
import csv

_OUTPUT_COLUMNS = [
    'Date',
    'GeoId',
    'Count_Person_25To64Years_EnrolledInEducationOrTraining_Female_AsAFractionOfCount_Person_25To64Years_Female',
    'Count_Person_25To64Years_EnrolledInEducationOrTraining_Male_AsAFractionOfCount_Person_25To64Years_Male',
    'Count_Person_25To64Years_EnrolledInEducationOrTraining_AsAFractionOfCount_Person_25To64Years',
]


def download_data(download_link):
    """Downloads raw data from Eurostat website and stores it in instance
    data frame.
    """

    urllib.request.urlretrieve(download_link, "trng_lfse_04.tsv.gz")
    raw_df = pd.read_table("trng_lfse_04.tsv.gz")

    raw_df = raw_df.rename(columns=({
        'freq,unit,sex,age,geo\TIME_PERIOD': 'unit,sex,age,geo\\time'
    }))
    raw_df['unit,sex,age,geo\\time'] = raw_df[
        'unit,sex,age,geo\\time'].str.slice(2)
    return raw_df


def translate_wide_to_long(data_url):
    # df = pd.read_csv(data_url, delimiter='\t')
    raw_df = download_data(_DATA_URL)
    df = raw_df
    assert df.head

    header = list(df.columns.values)
    years = header[1:]

    # Pandas.melt() unpivots a DataFrame from wide format to long format.
    df = pd.melt(df,
                 id_vars=header[0],
                 value_vars=years,
                 var_name='time',
                 value_name='value')

    # Separate geo and unit columns.
    new = df[header[0]].str.split(",", n=-1, expand=True)
    df = df.join(
        pd.DataFrame({
            'geo': new[3],
            'age': new[2],
            'sex': new[1],
            'unit': new[0]
        }))

    df.drop(columns=[header[0]], inplace=True)
    print(df.head())

    df['geo'] = df['geo'].apply(lambda geo: f'nuts/{geo}' if any(
        geo.isdigit() for geo in geo) or ('nuts/' + geo in NUTS1_CODES_NAMES)
                                else COUNTRY_MAP.get(geo, f'{geo}'))
    df = df[df.value.str.contains('[0-9]')]
    possible_flags = [' ', ':', 'b', 'e', 'u']
    for flag in possible_flags:
        df['value'] = df['value'].str.replace(flag, '')
    df['value'] = pd.to_numeric(df['value'])
    df = df.pivot_table(values='value',
                        index=['geo', 'time', 'unit', 'age'],
                        columns=['sex'],
                        aggfunc='first').reset_index().rename_axis(None, axis=1)
    return df


def preprocess(df, cleaned_csv):
    df = df.replace(np.NaN, '', regex=True)
    with open(cleaned_csv, 'w', newline='') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=_OUTPUT_COLUMNS,
                                lineterminator='\n')
        writer.writeheader()
        for _, row in df.iterrows():
            writer.writerow({
                'Date':
                    '%s' % (row['time'][:4]),
                'GeoId':
                    '%s' % row['geo'],
                'Count_Person_25To64Years_EnrolledInEducationOrTraining_Female_AsAFractionOfCount_Person_25To64Years_Female':
                    (row['F']),
                'Count_Person_25To64Years_EnrolledInEducationOrTraining_Male_AsAFractionOfCount_Person_25To64Years_Male':
                    (row['M']),
                'Count_Person_25To64Years_EnrolledInEducationOrTraining_AsAFractionOfCount_Person_25To64Years':
                    (row['T']),
            })


def get_template_mcf(output_columns):
    # Automate Template MCF generation since there are many Statistical Variables.
    TEMPLATE_MCF_TEMPLATE = """
    Node: E:EurostatsNUTS2_Enrollment->E{index}
    typeOf: dcs:StatVarObservation
    variableMeasured: dcs:{stat_var}
    observationAbout: C:EurostatsNUTS2_Enrollment->GeoId
    observationDate: C:EurostatsNUTS2_Enrollment->Date
    value: C:EurostatsNUTS2_Enrollment->{stat_var}
    scalingFactor: 100
    measurementMethod: dcs:EurostatRegionalStatistics
    """

    stat_vars = output_columns[2:]
    with open(_TMCF, 'w', newline='') as f_out:
        for i in range(len(stat_vars)):
            f_out.write(
                TEMPLATE_MCF_TEMPLATE.format_map({
                    'index': i,
                    'stat_var': output_columns[2:][i]
                }))


if __name__ == "__main__":
    _DATA_URL = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/trng_lfse_04/?format=TSV&compressed=true"
    _CLEANED_CSV = "./Eurostats_NUTS2_Enrollment.csv"
    _TMCF = "./Eurostats_NUTS2_Enrollment.tmcf"

    preprocess(translate_wide_to_long(_DATA_URL), _CLEANED_CSV)
    get_template_mcf(_OUTPUT_COLUMNS)
