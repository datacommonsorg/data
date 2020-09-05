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

_DATA_URL = "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/edat_lfse_04.tsv.gz"
_CLEANED_CSV = "./Eurostats_NUTS2_Edat.csv"
_TMCF = "./Eurostats_NUTS2_Edat.tmcf"

_OUTPUT_COLUMNS = [
    'Date',
    'GeoId',
    'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_AsAFractionOfCount_Person_25To64Years',
    'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_AsAFractionOfCount_Person_25To64Years',
    'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_AsAFractionOfCount_Person_25To64Years',
    'Count_Person_25To64Years_TertiaryEducation_AsAFractionOfCount_Person_25To64Years',
    'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female',
    'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_Female_AsAFractionOfCount_Person_25To64Years_Female',
    'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female',
    'Count_Person_25To64Years_TertiaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female',
    'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male',
    'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_Male_AsAFractionOfCount_Person_25To64Years_Male',
    'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male',
    'Count_Person_25To64Years_TertiaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male',
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
            'geo': new[4],
            'unit': new[3],
            'age': new[2],
            'level': new[1],
            'sex': new[0]
        }))
    df.drop(columns=[header[0]], inplace=True)

    df["sex-level"] = df["sex"] + "_" + df["level"]

    # Remove empty rows, clean values to have all digits.
    df = df[df.value.str.contains('[0-9]')]
    possible_flags = [' ', ':', 'b', 'd', 'e', 'u']
    for flag in possible_flags:
        df['value'] = df['value'].str.replace(flag, '')

    df['value'] = pd.to_numeric(df['value'])
    df = df.pivot_table(values='value',
                        index=['geo', 'time', 'unit', 'age'],
                        columns=['sex-level'],
                        aggfunc='first').reset_index().rename_axis(None, axis=1)
    return df


def preprocess(df, cleaned_csv):
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
                    'dcid:nuts/%s' % (row['geo']),
                'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_AsAFractionOfCount_Person_25To64Years':
                    (row['T_ED0-2']),
                'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_AsAFractionOfCount_Person_25To64Years':
                    (row['T_ED3-8']),
                'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_AsAFractionOfCount_Person_25To64Years':
                    (row['T_ED3_4']),
                'Count_Person_25To64Years_TertiaryEducation_AsAFractionOfCount_Person_25To64Years':
                    (row['T_ED5-8']),
                'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female':
                    (row['F_ED0-2']),
                'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_Female_AsAFractionOfCount_Person_25To64Years_Female':
                    (row['F_ED3-8']),
                'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female':
                    (row['F_ED3_4']),
                'Count_Person_25To64Years_TertiaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female':
                    (row['F_ED5-8']),
                'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male':
                    (row['M_ED0-2']),
                'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_Male_AsAFractionOfCount_Person_25To64Years_Male':
                    (row['M_ED3-8']),
                'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male':
                    (row['M_ED3_4']),
                'Count_Person_25To64Years_TertiaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male':
                    (row['M_ED5-8']),
            })


def get_template_mcf(output_columns):
    # Automate Template MCF generation since there are many Statistical Variables.
    TEMPLATE_MCF_TEMPLATE = """
  Node: E:EurostatsNUTS2_Education_Attainment->E{index}
  typeOf: dcs:StatVarObservation
  variableMeasured: dcs:{stat_var}
  observationAbout: C:EurostatsNUTS2_Education_Attainment->GeoId
  observationDate: C:EurostatsNUTS2_Education_Attainment->Date
  value: C:EurostatsNUTS2_Education_Attainment->{stat_var}
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
    preprocess(translate_wide_to_long(_DATA_URL), _CLEANED_CSV)
    get_template_mcf(_OUTPUT_COLUMNS)
