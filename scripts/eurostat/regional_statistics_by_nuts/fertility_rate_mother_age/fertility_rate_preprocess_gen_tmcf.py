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

import pandas as pd
import io
import csv

_DATA_URL = "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/demo_r_find3.tsv.gz"
_CLEANED_CSV = "./Eurostats_NUTS3_FRate_Age.csv"
_TMCF = "./Eurostats_NUTS3_FRate_Age.tmcf"

_OUTPUT_CLOUMNS = [
    'Date',
    'GeoId',
    'MeanMothersAge_BirthEvent',
    'MedianMothersAge_BirthEvent',
    'FertilityRate_Person_Female',
]


def translate_wide_to_long(data_url):
    df = pd.read_csv(data_url, delimiter='\t')
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
            'geo': new[2],
            'unit': new[1],
            'indic_de': new[0]
        }))
    df["indicator_unit"] = df["indic_de"] + "_" + df["unit"]
    df.drop(columns=[header[0]], inplace=True)

    # Remove empty rows, clean values to have all digits.
    df = df[df.value.str.contains('[0-9]')]
    possible_flags = [' ', ':']
    for flag in possible_flags:
        df['value'] = df['value'].str.replace(flag, '')

    df['value'] = pd.to_numeric(df['value'])
    df = df.pivot_table(values='value',
                        index=['geo', 'time'],
                        columns=['indicator_unit'],
                        aggfunc='first').reset_index().rename_axis(None, axis=1)
    return df


def preprocess(df, cleaned_csv):
    with open(cleaned_csv, 'w', newline='') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=_OUTPUT_CLOUMNS,
                                lineterminator='\n')
        writer.writeheader()
        for _, row in df.iterrows():
            writer.writerow({
                'Date': '%s' % (row['time'][:4]),
                'GeoId': 'dcid:nuts/%s' % row['geo'],
                'MeanMothersAge_BirthEvent': (row['AGEMOTH_YR']),
                'MedianMothersAge_BirthEvent': (row['MEDAGEMOTH_YR']),
                'FertilityRate_Person_Female': (row['TOTFERRT_NR']),
            })


def get_template_mcf():
    # Automate Template MCF generation since there are many Statistical Variables.
    TEMPLATE_MCF_TEMPLATE = """
  Node: E:Eurostats_NUTS3_FRate_Age->E{index}
  typeOf: dcs:StatVarObservation
  variableMeasured: dcs:{stat_var}
  observationAbout: C:Eurostats_NUTS3_FRate_Age->GeoId
  observationDate: C:Eurostats_NUTS3_FRate_Age->Date
  value: C:Eurostats_NUTS3_FRate_Age->{stat_var}
  measurementMethod: dcs:EurostatRegionalStatistics
  """

    stat_vars = _OUTPUT_CLOUMNS[2:]
    with open(_TMCF, 'w', newline='') as f_out:
        for i in range(len(stat_vars)):
            f_out.write(
                TEMPLATE_MCF_TEMPLATE.format_map({
                    'index': i,
                    'stat_var': _OUTPUT_CLOUMNS[2:][i]
                }))


if __name__ == "__main__":
    preprocess(translate_wide_to_long(_DATA_URL), _CLEANED_CSV)
    get_template_mcf()
