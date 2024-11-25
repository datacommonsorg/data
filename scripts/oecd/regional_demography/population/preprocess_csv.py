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

import os
import sys
import csv
import json
import pandas as pd
import logging
from absl import flags
from absl import app

_FLAGS = flags.FLAGS
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
flags.DEFINE_string('mode', '', 'Options: download or process')

logging.basicConfig(level=logging.INFO)

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(1, os.path.join(_MODULE_DIR, '../'))
from utils import multi_index_to_single_index
from download import download_data_to_file_and_df


def process_data(df, output_file_path):
    logging.info("Processing the input file")
    logging.info("Filtering the required columns")
    df = df[df['UNIT_MEASURE'] == "PS"]
    # df = df[['TL', 'REG_ID', 'Region', 'VAR', 'SEX', 'Year', 'Value']]
    df = df[[
        'TERRITORIAL_LEVEL', 'REF_AREA', 'Reference area', 'AGE', 'SEX',
        'TIME_PERIOD', 'OBS_VALUE'
    ]]
    # First remove geos with names that we don't have mappings to dcid for.
    regid_file = "scripts/oecd/regional_demography/regid2dcid.json"
    with open(regid_file, 'r') as f:
        regid2dcid = dict(json.loads(f.read()))
    logging.info("Resolving places")
    df = df[df['REF_AREA'].isin(regid2dcid.keys())]
    # Second, replace the names with dcids
    #print(df.head())
    df['Reference area'] = df.apply(lambda row: regid2dcid[row['REF_AREA']],
                                    axis=1)

    df['TIME_PERIOD'] = '"' + df['TIME_PERIOD'].astype(str) + '"'

    df_cleaned = df.pivot_table(
        values='OBS_VALUE',
        index=['REF_AREA', 'Reference area', 'TIME_PERIOD'],
        columns=['AGE', 'SEX'])
    df_cleaned = multi_index_to_single_index(df_cleaned)

    VAR_to_statsvars = {
        '_T_T': 'Count_Person',
        'Y_LT5_T': 'Count_Person_Upto4Years',
        'Y5T9_T': 'Count_Person_5To9Years',
        'Y10T14_T': 'Count_Person_10To14Years',
        'Y15T19_T': 'Count_Person_15To19Years',
        'Y20T24_T': 'Count_Person_20To24Years',
        'Y25T29_T': 'Count_Person_25To29Years',
        'Y30T34_T': 'Count_Person_30To34Years',
        'Y35T39_T': 'Count_Person_35To39Years',
        'Y40T44_T': 'Count_Person_40To44Years',
        'Y45T49_T': 'Count_Person_45To49Years',
        'Y50T54_T': 'Count_Person_50To54Years',
        'Y55T59_T': 'Count_Person_55To59Years',
        'Y60T64_T': 'Count_Person_60To64Years',
        'Y65T69_T': 'Count_Person_65To69Years',
        'Y70T74_T': 'Count_Person_70To74Years',
        'Y75T79_T': 'Count_Person_75To79Years',
        'Y_GE80_T': 'Count_Person_80OrMoreYears',
        'Y_LT15_T': 'Count_Person_Upto14Years',
        'Y15T64_T': 'Count_Person_15To64Years',
        'Y_GE65_T': 'Count_Person_65OrMoreYears',
        '_TM': 'Count_Person_Male',
        'Y_LT5M': 'Count_Person_Upto4Years_Male',
        'Y5T9M': 'Count_Person_5To9Years_Male',
        'Y10T14M': 'Count_Person_10To14Years_Male',
        'Y15T19M': 'Count_Person_15To19Years_Male',
        'Y20T24M': 'Count_Person_20To24Years_Male',
        'Y25T29M': 'Count_Person_25To29Years_Male',
        'Y30T34M': 'Count_Person_30To34Years_Male',
        'Y35T39M': 'Count_Person_35To39Years_Male',
        'Y40T44M': 'Count_Person_40To44Years_Male',
        'Y45T49M': 'Count_Person_45To49Years_Male',
        'Y50T54M': 'Count_Person_50To54Years_Male',
        'Y55T59M': 'Count_Person_55To59Years_Male',
        'Y60T64M': 'Count_Person_60To64Years_Male',
        'Y65T69M': 'Count_Person_65To69Years_Male',
        'Y70T74M': 'Count_Person_70To74Years_Male',
        'Y75T79M': 'Count_Person_75To79Years_Male',
        'Y_GE80M': 'Count_Person_80OrMoreYears_Male',
        'Y_LT15M': 'Count_Person_Upto14Years_Male',
        'Y15T64M': 'Count_Person_15To64Years_Male',
        'Y_GE65M': 'Count_Person_65OrMoreYears_Male',
        '_TF': 'Count_Person_Female',
        'Y_LT5F': 'Count_Person_Upto4Years_Female',
        'Y5T9F': 'Count_Person_5To9Years_Female',
        'Y10T14F': 'Count_Person_10To14Years_Female',
        'Y15T19F': 'Count_Person_15To19Years_Female',
        'Y20T24F': 'Count_Person_20To24Years_Female',
        'Y25T29F': 'Count_Person_25To29Years_Female',
        'Y30T34F': 'Count_Person_30To34Years_Female',
        'Y35T39F': 'Count_Person_35To39Years_Female',
        'Y40T44F': 'Count_Person_40To44Years_Female',
        'Y45T49F': 'Count_Person_45To49Years_Female',
        'Y50T54F': 'Count_Person_50To54Years_Female',
        'Y55T59F': 'Count_Person_55To59Years_Female',
        'Y60T64F': 'Count_Person_60To64Years_Female',
        'Y65T69F': 'Count_Person_65To69Years_Female',
        'Y70T74F': 'Count_Person_70To74Years_Female',
        'Y75T79F': 'Count_Person_75To79Years_Female',
        'Y_GE80F': 'Count_Person_80OrMoreYears_Female',
        'Y_LT15F': 'Count_Person_Upto14Years_Female',
        'Y15T64F': 'Count_Person_15To64Years_Female',
        'Y_GE65F': 'Count_Person_65OrMoreYears_Female',
    }

    df_cleaned.rename(columns=VAR_to_statsvars, inplace=True)

    # Drop columns that are not related with populations.
    drop_cols = []
    csv_columns = {'REF_AREA', 'Reference area', 'TIME_PERIOD'}
    csv_columns.update(VAR_to_statsvars.values())
    for col in df_cleaned.columns:
        if col not in csv_columns:
            drop_cols.append(col)
    df_cleaned.drop(columns=drop_cols, axis=0, inplace=True)
    logging.info("Writing output to %s",output_file_path)
    df_cleaned.to_csv(output_file_path, index=False, quoting=csv.QUOTE_NONE)
    return df_cleaned


def generate_tmcf(df_cleaned, filepath):
    # Automate Template MCF generation since there are many Statitical Variables.
    TEMPLATE_MCF_TEMPLATE = """
    Node: E:OECD_population_cleaned->E{index}
    typeOf: dcs:StatVarObservation
    variableMeasured: dcs:{stat_var}
    measurementMethod: dcs:OECDRegionalStatistics
    observationAbout: C:OECD_population_cleaned->Reference area
    observationDate: C:OECD_population_cleaned->TIME_PERIOD
    observationPeriod: "P1Y"
    value: C:OECD_population_cleaned->{stat_var}
    """

    stat_vars = df_cleaned.columns[3:]
    with open(filepath, 'w', newline='') as f_out:
        for i in range(len(stat_vars)):
            f_out.write(
                TEMPLATE_MCF_TEMPLATE.format_map({
                    'index': i + 1,
                    'stat_var': stat_vars[i]
                }))


def main(_):
    mode = _FLAGS.mode
    url = "https://sdmx.oecd.org/public/rest/data/OECD.CFE.EDS,DSD_REG_DEMO@DF_POP_5Y,2.0/all?dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
    filename = os.path.join(_MODULE_DIR, "REGION_DEMOGR_population.csv")

    if mode == "" or mode == "download":
        download_data_to_file_and_df(url, filename, is_download_required=True,csv_filepath=None)
    if mode == "" or mode == "process":
        df = pd.read_csv(filename)
        csv_filepath = os.path.join(_MODULE_DIR, "OECD_population_cleaned.csv")
        df_cleaned = process_data(df, csv_filepath)
        tmcf_filepath = os.path.join(_MODULE_DIR, "OECD_population.tmcf")
        generate_tmcf(df_cleaned, tmcf_filepath)

if __name__=="__main__":
    app.run(main)
