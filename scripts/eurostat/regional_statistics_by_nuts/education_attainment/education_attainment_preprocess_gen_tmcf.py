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

# _DATA_URL = "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/edat_lfse_04.tsv.gz"

_CLEANED_CSV = "./Eurostats_NUTS2_Edat.csv"
_TMCF = "./Eurostats_NUTS2_Edat.tmcf"
_SOURCE_TSV = "./edat_lfse_04.tsv"
_SOURCE_CSV_LONG = "./edat_lfse_04.csv"

_OUTPUT_CLOUMNS = [
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


def translate_wide_to_long(source_tsv, source_csv_long):
    df = pd.read_csv(source_tsv, delimiter='\t')
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

    df.to_csv(source_csv_long, index=False)


def preprocess(cleaned_csv, source_csv_long, output_columns):
    with open(cleaned_csv, 'w', newline='') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=output_columns,
                                lineterminator='\n')
        with open(source_csv_long) as response:
            reader = csv.DictReader(response)

            writer.writeheader()
            for row_dict in reader:
                assert not row_dict['F_ED0-2'].isdigit()
                assert not row_dict['F_ED3-8'].isdigit()
                assert not row_dict['F_ED3_4'].isdigit()
                assert not row_dict['F_ED5-8'].isdigit()
                assert not row_dict['M_ED0-2'].isdigit()
                assert not row_dict['M_ED3-8'].isdigit()
                assert not row_dict['M_ED3_4'].isdigit()
                assert not row_dict['M_ED5-8'].isdigit()
                assert not row_dict['T_ED0-2'].isdigit()
                assert not row_dict['T_ED3-8'].isdigit()
                assert not row_dict['T_ED3_4'].isdigit()
                assert not row_dict['T_ED5-8'].isdigit()
                assert not row_dict['time'].isdigit()
                processed_dict = {
                    'Date':
                        '%s' % (row_dict['time'][:4]),
                    'GeoId':
                        'dcid:nuts/%s' % row_dict['geo'],
                    'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_AsAFractionOfCount_Person_25To64Years':
                        (row_dict['T_ED0-2']),
                    'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_AsAFractionOfCount_Person_25To64Years':
                        (row_dict['T_ED3-8']),
                    'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_AsAFractionOfCount_Person_25To64Years':
                        (row_dict['T_ED3_4']),
                    'Count_Person_25To64Years_TertiaryEducation_AsAFractionOfCount_Person_25To64Years':
                        (row_dict['T_ED5-8']),
                    'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female':
                        (row_dict['F_ED0-2']),
                    'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_Female_AsAFractionOfCount_Person_25To64Years_Female':
                        (row_dict['F_ED3-8']),
                    'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female':
                        (row_dict['F_ED3_4']),
                    'Count_Person_25To64Years_TertiaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female':
                        (row_dict['F_ED5-8']),
                    'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male':
                        (row_dict['M_ED0-2']),
                    'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_Male_AsAFractionOfCount_Person_25To64Years_Male':
                        (row_dict['M_ED3-8']),
                    'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male':
                        (row_dict['M_ED3_4']),
                    'Count_Person_25To64Years_TertiaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male':
                        (row_dict['M_ED5-8']),
                }

        writer.writerow(processed_dict)


def get_template_mcf(tmcf, output_columns):
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
    with open(tmcf, 'w', newline='') as f_out:
        for i in range(len(stat_vars)):
            f_out.write(
                TEMPLATE_MCF_TEMPLATE.format_map({
                    'index': i,
                    'stat_var': output_columns[2:][i]
                }))


if __name__ == "__main__":
    translate_wide_to_long(_SOURCE_TSV, _SOURCE_CSV_LONG)
    preprocess(_CLEANED_CSV, _SOURCE_CSV_LONG, _OUTPUT_CLOUMNS)
    get_template_mcf(_TMCF, _OUTPUT_CLOUMNS)
