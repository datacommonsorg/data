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

_DATA_URL = "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/nama_10r_3empers.tsv.gz"
_CLEANED_CSV = "./Eurostats_NUTS3_Empers.csv"
_TMCF = "./Eurostats_NUTS3_Empers.tmcf"

_OUTPUT_CLOUMNS = [
    'Date',
    'GeoId',
    'Count_Person_Employed_NACE/A',
    'Count_Person_Employed_NACE/B-E',
    'Count_Person_Employed_NACE/C',
    'Count_Person_Employed_NACE/F',
    'Count_Person_Employed_NACE/G-I',
    'Count_Person_Employed_NACE/G-J',
    'Count_Person_Employed_NACE/J',
    'Count_Person_Employed_NACE/K',
    'Count_Person_Employed_NACE/K-N',
    'Count_Person_Employed_NACE/L',
    'Count_Person_Employed_NACE/M-N',
    'Count_Person_Employed_NACE/O-Q',
    'Count_Person_Employed_NACE/O-U',
    'Count_Person_Employed_NACE/R-U',
    'Count_Person_Employed',
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
            'geo': new[3],
            'nace_r2': new[2],
            'wstatus': new[1],
            'unit': new[0]
        }))
    df.drop(columns=[header[0]], inplace=True)

    df["wstatus-nace"] = df["wstatus"] + "_" + df["nace_r2"]

    # Remove empty rows, clean values to have all digits.
    df = df[df.value.str.contains('[0-9]')]
    possible_flags = [' ', ':', 'b', 'd', 'e', 'u', 'p']
    for flag in possible_flags:
        df['value'] = df['value'].str.replace(flag, '')

    df['value'] = pd.to_numeric(df['value'])
    df['value'] = df['value'].mul(1000)

    df = df.pivot_table(values='value',
                        index=['geo', 'time', 'unit'],
                        columns=['wstatus-nace'],
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
                'GeoId': 'dcid:nuts/%s' % (row['geo']),
                'Count_Person_Employed_NACE/A': (row['EMP_A']),
                'Count_Person_Employed_NACE/B-E': (row['EMP_B-E']),
                'Count_Person_Employed_NACE/C': (row['EMP_C']),
                'Count_Person_Employed_NACE/F': (row['EMP_F']),
                'Count_Person_Employed_NACE/G-I': (row['EMP_G-I']),
                'Count_Person_Employed_NACE/G-J': (row['EMP_G-J']),
                'Count_Person_Employed_NACE/J': (row['EMP_J']),
                'Count_Person_Employed_NACE/K': (row['EMP_K']),
                'Count_Person_Employed_NACE/K-N': (row['EMP_K-N']),
                'Count_Person_Employed_NACE/L': (row['EMP_L']),
                'Count_Person_Employed_NACE/M-N': (row['EMP_M_N']),
                'Count_Person_Employed_NACE/O-Q': (row['EMP_O-Q']),
                'Count_Person_Employed_NACE/O-U': (row['EMP_O-U']),
                'Count_Person_Employed_NACE/R-U': (row['EMP_R-U']),
                'Count_Person_Employed': (row['EMP_TOTAL']),
            })


def get_template_mcf():
    # Automate Template MCF generation since there are many Statistical Variables.
    TEMPLATE_MCF_TEMPLATE = """
  Node: E:EurostatsNUTS3_Employed_per_Sector->E{index}
  typeOf: dcs:StatVarObservation
  variableMeasured: dcs:{stat_var}
  observationAbout: C:EurostatsNUTS3_Employed_per_Sector->GeoId
  observationDate: C:EurostatsNUTS3_Employed_per_Sector->Date
  value: C:EurostatsNUTS3_Employed_per_Sector->{stat_var}
  sourceScalingFactor: 1000
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
