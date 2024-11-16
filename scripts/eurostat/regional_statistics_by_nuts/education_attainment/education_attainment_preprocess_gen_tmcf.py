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
    'Count_Person_20To24Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_AsAFractionOfCount_Person_20To24Years',
    'Count_Person_30To34Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_AsAFractionOfCount_Person_30To34Years',
    'Count_Person_25To34Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_AsAFractionOfCount_Person_25To34Years',
    'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_AsAFractionOfCount_Person_25To64Years',
    'Count_Person_20To24Years_UpperSecondaryEducationOrHigher_AsAFractionOfCount_Person_20To24Years',
    'Count_Person_30To34Years_UpperSecondaryEducationOrHigher_AsAFractionOfCount_Person_30To34Years',
    'Count_Person_25To34Years_UpperSecondaryEducationOrHigher_AsAFractionOfCount_Person_25To34Years',
    'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_AsAFractionOfCount_Person_25To64Years',
    'Count_Person_20To24Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_AsAFractionOfCount_Person_20To24Years',
    'Count_Person_30To34Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_AsAFractionOfCount_Person_30To34Years',
    'Count_Person_25To34Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_AsAFractionOf_Count_Person_25To34Years',
    'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_AsAFractionOfCount_Person_25To64Years',
    'Count_Person_20To24Years_EducationalAttainmentTertiaryEducation_AsAFractionOf_Count_Person_20To24Years',
    'Count_Person_30To34Years_EducationalAttainmentTertiaryEducation_AsAFractionOf_Count_Person_30To34Years',
    'Count_Person_25To34Years_TertiaryEducation_AsAFractionOf_Count_Person_25To34Years',
    'Count_Person_25To64Years_TertiaryEducation_AsAFractionOfCount_Person_25To64Years',
    'Count_Person_20To24Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Female_AsAFractionOfCount_Person_20To24Years_Female',
    'Count_Person_30To34Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Female_AsAFractionOfCount_Person_30To34Years_Female',
    'Count_Person_25To34Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Female_AsAFractionOfCount_Person_25To34Years_Female',
    'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female',
    'Count_Person_20To24Years_UpperSecondaryEducationOrHigher_Female_AsAFractionOfCount_Person_20To24Years_Female',
    'Count_Person_30To34Years_UpperSecondaryEducationOrHigher_Female_AsAFractionOfCount_Person_30To34Years_Female',
    'Count_Person_25To34Years_UpperSecondaryEducationOrHigher_Female_AsAFractionOfCount_Person_25To34Years_Female',
    'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_Female_AsAFractionOfCount_Person_25To64Years_Female',
    'Count_Person_20To24Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Female_AsAFractionOfCount_Person_20To24Years_Female',
    'Count_Person_30To34Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Female_AsAFractionOfCount_Person_30To34Years_Female',
    'Count_Person_25To34Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Female_AsAFractionOf_Count_Person_25To34Years_Female',
    'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female',
    'Count_Person_20To24Years_EducationalAttainmentTertiaryEducation_Female_AsAFractionOf_Count_Person_20To24Years_Female',
    'Count_Person_30To34Years_EducationalAttainmentTertiaryEducation_Female_AsAFractionOf_Count_Person_30To34Years_Female',
    'Count_Person_25To34Years_TertiaryEducation_Female_AsAFractionOf_Count_Person_25To34Years_Female',
    'Count_Person_25To64Years_TertiaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female',
    'Count_Person_20To24Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Male_AsAFractionOfCount_Person_20To24Years_Male',
    'Count_Person_30To34Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Male_AsAFractionOfCount_Person_30To34Years_Male',
    'Count_Person_25To34Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Male_AsAFractionOfCount_Person_25To34Years_Male',
    'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male',
    'Count_Person_20To24Years_UpperSecondaryEducationOrHigher_Male_AsAFractionOfCount_Person_20To24Years_Male',
    'Count_Person_30To34Years_UpperSecondaryEducationOrHigher_Male_AsAFractionOfCount_Person_30To34Years_Male',
    'Count_Person_25To34Years_UpperSecondaryEducationOrHigher_Male_AsAFractionOfCount_Person_25To34Years_Male',
    'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_Male_AsAFractionOfCount_Person_25To64Years_Male',
    'Count_Person_20To24Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Male_AsAFractionOfCount_Person_20To24Years_Male',
    'Count_Person_30To34Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Male_AsAFractionOfCount_Person_30To34Years_Male',
    'Count_Person_25To34Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Male_AsAFractionOf_Count_Person_25To34Years_Male',
    'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male',
    'Count_Person_20To24Years_TertiaryEducation_Male_AsAFractionOfCount_Person_20To24Years_Male',
    'Count_Person_30To34Years_TertiaryEducation_Male_AsAFractionOfCount_Person_30To34Years_Male',
    'Count_Person_25To34Years_TertiaryEducation_Male_AsAFractionOf_Count_Person_25To34Years_Male',
    'Count_Person_25To64Years_TertiaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male',
]


def download_data(download_link):
    """Downloads raw data from Eurostat website and stores it in instance
    data frame.
    """

    urllib.request.urlretrieve(download_link, "edat_lfse_04.tsv.gz")
    raw_df = pd.read_table("edat_lfse_04.tsv.gz")
    raw_df = raw_df.rename(columns=({
        'freq,sex,isced11,age,unit,geo\TIME_PERIOD':
            'sex,isced11,age,unit,geo\\time'
    }))
    raw_df['sex,isced11,age,unit,geo\\time'] = raw_df[
        'sex,isced11,age,unit,geo\\time'].str.slice(2)
    return raw_df


def translate_wide_to_long(data_url, is_download_required=False, df_input=None):
    # df = pd.read_csv(data_url, delimiter='\t')
    if is_download_required:
        df = download_data(data_url)
    else:
        df = df_input
    # df = raw_df
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

    df["sex-level"] = df["sex"] + "_" + df["level"] + "_" + df["age"]

    # Assuming NUTS1_CODES_NAMES and COUNTRY_MAP are already defined

    df['geo'] = df['geo'].apply(lambda geo: f'nuts/{geo}' if any(
        char.isdigit() for char in geo) or ('nuts/' + geo in NUTS1_CODES_NAMES)
                                else COUNTRY_MAP.get(geo, f'{geo}'))

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
                    '%s' % (row['geo']),
                'Count_Person_20To24Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_AsAFractionOfCount_Person_20To24Years':
                    (row['T_ED0-2_Y20-24']),
                'Count_Person_30To34Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_AsAFractionOfCount_Person_30To34Years':
                    (row['T_ED0-2_Y30-34']),
                'Count_Person_25To34Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_AsAFractionOfCount_Person_25To34Years':
                    (row['T_ED0-2_Y25-34']),
                'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_AsAFractionOfCount_Person_25To64Years':
                    (row['T_ED0-2_Y25-64']),
                'Count_Person_20To24Years_UpperSecondaryEducationOrHigher_AsAFractionOfCount_Person_20To24Years':
                    (row['T_ED3-8_Y20-24']),
                'Count_Person_30To34Years_UpperSecondaryEducationOrHigher_AsAFractionOfCount_Person_30To34Years':
                    (row['T_ED3-8_Y30-34']),
                'Count_Person_25To34Years_UpperSecondaryEducationOrHigher_AsAFractionOfCount_Person_25To34Years':
                    (row['T_ED3-8_Y25-34']),
                'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_AsAFractionOfCount_Person_25To64Years':
                    (row['T_ED3-8_Y25-64']),
                'Count_Person_20To24Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_AsAFractionOfCount_Person_20To24Years':
                    (row['T_ED3_4_Y20-24']),
                'Count_Person_30To34Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_AsAFractionOfCount_Person_30To34Years':
                    (row['T_ED3_4_Y30-34']),
                'Count_Person_25To34Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_AsAFractionOf_Count_Person_25To34Years':
                    (row['T_ED3_4_Y25-34']),
                'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_AsAFractionOfCount_Person_25To64Years':
                    (row['T_ED3_4_Y25-64']),
                'Count_Person_20To24Years_EducationalAttainmentTertiaryEducation_AsAFractionOf_Count_Person_20To24Years':
                    (row['T_ED5-8_Y20-24']),
                'Count_Person_30To34Years_EducationalAttainmentTertiaryEducation_AsAFractionOf_Count_Person_30To34Years':
                    (row['T_ED5-8_Y30-34']),
                'Count_Person_25To34Years_TertiaryEducation_AsAFractionOf_Count_Person_25To34Years':
                    (row['T_ED5-8_Y25-34']),
                'Count_Person_25To64Years_TertiaryEducation_AsAFractionOfCount_Person_25To64Years':
                    (row['T_ED5-8_Y25-64']),
                'Count_Person_20To24Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Female_AsAFractionOfCount_Person_20To24Years_Female':
                    (row['F_ED0-2_Y20-24']),
                'Count_Person_30To34Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Female_AsAFractionOfCount_Person_30To34Years_Female':
                    (row['F_ED0-2_Y30-34']),
                'Count_Person_25To34Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Female_AsAFractionOfCount_Person_25To34Years_Female':
                    (row['F_ED0-2_Y25-34']),
                'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female':
                    (row['F_ED0-2_Y25-64']),
                'Count_Person_20To24Years_UpperSecondaryEducationOrHigher_Female_AsAFractionOfCount_Person_20To24Years_Female':
                    (row['F_ED3-8_Y20-24']),
                'Count_Person_30To34Years_UpperSecondaryEducationOrHigher_Female_AsAFractionOfCount_Person_30To34Years_Female':
                    (row['F_ED3-8_Y30-34']),
                'Count_Person_25To34Years_UpperSecondaryEducationOrHigher_Female_AsAFractionOfCount_Person_25To34Years_Female':
                    (row['F_ED3-8_Y25-34']),
                'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_Female_AsAFractionOfCount_Person_25To64Years_Female':
                    (row['F_ED3-8_Y25-64']),
                'Count_Person_20To24Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Female_AsAFractionOfCount_Person_20To24Years_Female':
                    (row['F_ED3_4_Y20-24']),
                'Count_Person_30To34Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Female_AsAFractionOfCount_Person_30To34Years_Female':
                    (row['F_ED3_4_Y30-34']),
                'Count_Person_25To34Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Female_AsAFractionOf_Count_Person_25To34Years_Female':
                    (row['F_ED3_4_Y25-34']),
                'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female':
                    (row['F_ED3_4_Y25-64']),
                'Count_Person_20To24Years_EducationalAttainmentTertiaryEducation_Female_AsAFractionOf_Count_Person_20To24Years_Female':
                    (row['F_ED5-8_Y20-24']),
                'Count_Person_30To34Years_EducationalAttainmentTertiaryEducation_Female_AsAFractionOf_Count_Person_30To34Years_Female':
                    (row['F_ED5-8_Y30-34']),
                'Count_Person_25To34Years_TertiaryEducation_Female_AsAFractionOf_Count_Person_25To34Years_Female':
                    (row['F_ED5-8_Y25-34']),
                'Count_Person_25To64Years_TertiaryEducation_Female_AsAFractionOfCount_Person_25To64Years_Female':
                    (row['F_ED5-8_Y25-64']),
                'Count_Person_20To24Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Male_AsAFractionOfCount_Person_20To24Years_Male':
                    (row['M_ED0-2_Y20-24']),
                'Count_Person_30To34Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Male_AsAFractionOfCount_Person_30To34Years_Male':
                    (row['M_ED0-2_Y30-34']),
                'Count_Person_25To34Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Male_AsAFractionOfCount_Person_25To34Years_Male':
                    (row['M_ED0-2_Y25-34']),
                'Count_Person_25To64Years_LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male':
                    (row['M_ED0-2_Y25-64']),
                'Count_Person_20To24Years_UpperSecondaryEducationOrHigher_Male_AsAFractionOfCount_Person_20To24Years_Male':
                    (row['M_ED3-8_Y20-24']),
                'Count_Person_30To34Years_UpperSecondaryEducationOrHigher_Male_AsAFractionOfCount_Person_30To34Years_Male':
                    (row['M_ED3-8_Y30-34']),
                'Count_Person_25To34Years_UpperSecondaryEducationOrHigher_Male_AsAFractionOfCount_Person_25To34Years_Male':
                    (row['M_ED3-8_Y25-34']),
                'Count_Person_25To64Years_UpperSecondaryEducationOrHigher_Male_AsAFractionOfCount_Person_25To64Years_Male':
                    (row['M_ED3-8_Y25-64']),
                'Count_Person_20To24Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Male_AsAFractionOfCount_Person_20To24Years_Male':
                    (row['M_ED3_4_Y20-24']),
                'Count_Person_30To34Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Male_AsAFractionOfCount_Person_30To34Years_Male':
                    (row['M_ED3_4_Y30-34']),
                'Count_Person_25To34Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Male_AsAFractionOf_Count_Person_25To34Years_Male':
                    (row['M_ED3_4_Y25-34']),
                'Count_Person_25To64Years_UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male':
                    (row['M_ED3_4_Y25-64']),
                'Count_Person_20To24Years_TertiaryEducation_Male_AsAFractionOfCount_Person_20To24Years_Male':
                    (row['M_ED5-8_Y20-24']),
                'Count_Person_30To34Years_TertiaryEducation_Male_AsAFractionOfCount_Person_30To34Years_Male':
                    (row['M_ED5-8_Y30-34']),
                'Count_Person_25To34Years_TertiaryEducation_Male_AsAFractionOf_Count_Person_25To34Years_Male':
                    (row['M_ED5-8_Y25-34']),
                'Count_Person_25To64Years_TertiaryEducation_Male_AsAFractionOfCount_Person_25To64Years_Male':
                    (row['M_ED5-8_Y25-64']),
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
    _DATA_URL = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/edat_lfse_04/?format=TSV&compressed=true"
    _CLEANED_CSV = "./Eurostats_NUTS2_Edat.csv"
    _TMCF = "./Eurostats_NUTS2_Edat.tmcf"

    preprocess(translate_wide_to_long(_DATA_URL, is_download_required=True),
               _CLEANED_CSV)
    get_template_mcf(_OUTPUT_COLUMNS)
