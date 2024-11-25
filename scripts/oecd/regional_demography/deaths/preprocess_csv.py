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

import sys
import os
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
    df1 = df[(df['TERRITORIAL_LEVEL'] == "TL3")]
    df1 = df[[
        'TERRITORIAL_LEVEL', 'REF_AREA', 'Reference area', 'AGE', 'SEX',
        'TIME_PERIOD', 'OBS_VALUE', 'UNIT_MEASURE'
    ]]
    df1["AGE"] = df1["UNIT_MEASURE"] + "_" + df1["AGE"] + df1["SEX"]

    # First remove geos with names that we don't have mappings to dcid for.
    # regid2dcid = dict(json.loads(open('../regid2dcid.json').read()))
    regid_file = "scripts/oecd/regional_demography/regid2dcid.json"
    with open(regid_file, 'r') as f:
        regid2dcid = dict(json.loads(f.read()))
    logging.info("Resolving places")
    df1 = df1[df1['REF_AREA'].isin(regid2dcid.keys())]

    # Second, replace the names with dcids
    df1['Reference area'] = df1.apply(lambda row: regid2dcid[row['REF_AREA']],
                                      axis=1)

    df1['TIME_PERIOD'] = '"' + df1['TIME_PERIOD'].astype(str) + '"'

    temp = df1[[
        'REF_AREA', 'Reference area', 'AGE', 'SEX', 'TIME_PERIOD', 'OBS_VALUE'
    ]]
    temp_multi_index = temp.pivot_table(
        values='OBS_VALUE',
        index=['REF_AREA', 'Reference area', 'TIME_PERIOD'],
        columns=['AGE', 'SEX'])
    df_cleaned = multi_index_to_single_index(temp_multi_index)

    VAR_to_statsvars = {
        'DT__T_T_T': 'Count_Death',
        # 'D_Y0_4T': 'Count_Death_Upto4Years',
        'DT_Y_LT5_T_T': 'Count_Death_Upto4Years',
        'DT_Y5T9_T_T': 'Count_Death_5To9Years',
        'DT_Y10T14_T_T': 'Count_Death_10To14Years',
        'DT_Y15T19_T_T': 'Count_Death_15To19Years',
        'DT_Y20T24_T_T': 'Count_Death_20To24Years',
        'DT_Y25T29_T_T': 'Count_Death_25To29Years',
        'DT_Y30T34_T_T': 'Count_Death_30To34Years',
        'DT_Y35T39_T_T': 'Count_Death_35To39Years',
        'DT_Y40T44_T_T': 'Count_Death_40To44Years',
        'DT_Y45T49_T_T': 'Count_Death_45To49Years',
        'DT_Y50T54_T_T': 'Count_Death_50To54Years',
        'DT_Y55T59_T_T': 'Count_Death_55To59Years',
        'DT_Y60T64_T_T': 'Count_Death_60To64Years',
        'DT_Y65T69_T_T': 'Count_Death_65To69Years',
        'DT_Y70T74_T_T': 'Count_Death_70To74Years',
        'DT_Y75T79_T_T': 'Count_Death_75To79Years',
        'DT_Y_GE80_T_T': 'Count_Death_80OrMoreYears',
        # 'D_Y0_14T': 'Count_Death_Upto14Years',
        'DT_Y_LT15_T_T': 'Count_Death_Upto14Years',
        'DT_Y15T64_T_T': 'Count_Death_15To64Years',
        'DT_Y_GE65_T_T': 'Count_Death_65OrMoreYears',
        'DT__TMM': 'Count_Death_Male',
        # 'D_Y0_4MM': 'Count_Death_Upto4Years_Male',
        'DT_Y_LT5MM': 'Count_Death_Upto4Years_Male',
        'DT_Y5T9MM': 'Count_Death_5To9Years_Male',
        'DT_Y10T14MM': 'Count_Death_10To14Years_Male',
        'DT_Y15T19MM': 'Count_Death_15To19Years_Male',
        'DT_Y20T24MM': 'Count_Death_20To24Years_Male',
        'DT_Y25T29MM': 'Count_Death_25To29Years_Male',
        'DT_Y30T34MM': 'Count_Death_30To34Years_Male',
        'DT_Y35T39MM': 'Count_Death_35To39Years_Male',
        'DT_Y40T44MM': 'Count_Death_40To44Years_Male',
        'DT_Y45T49MM': 'Count_Death_45To49Years_Male',
        'DT_Y50T54MM': 'Count_Death_50To54Years_Male',
        'DT_Y55T59MM': 'Count_Death_55To59Years_Male',
        'DT_Y60T64MM': 'Count_Death_60To64Years_Male',
        'DT_Y65T69MM': 'Count_Death_65To69Years_Male',
        'DT_Y70T74MM': 'Count_Death_70To74Years_Male',
        'DT_Y75T79MM': 'Count_Death_75To79Years_Male',
        'DT_Y_GE80MM': 'Count_Death_80OrMoreYears_Male',
        # 'D_Y0_14MM': 'Count_Death_Upto14Years_Male',
        'DT_Y_LT15MM': 'Count_Death_Upto14Years_Male',
        'DT_Y15T64MM': 'Count_Death_15To64Years_Male',
        'DT_Y_GE65MM': 'Count_Death_65OrMoreYears_Male',
        'DT__TFF': 'Count_Death_Female',
        # 'D_Y0_4FF': 'Count_Death_Upto4Years_Female',
        'DT_Y_LT5FF': 'Count_Death_Upto4Years_Female',
        'DT_Y5T9FF': 'Count_Death_5To9Years_Female',
        'DT_Y10T14FF': 'Count_Death_10To14Years_Female',
        'DT_Y15T19FF': 'Count_Death_15To19Years_Female',
        'DT_Y20T24FF': 'Count_Death_20To24Years_Female',
        'DT_Y25T29FF': 'Count_Death_25To29Years_Female',
        'DT_Y30T34FF': 'Count_Death_30To34Years_Female',
        'DT_Y35T39FF': 'Count_Death_35To39Years_Female',
        'DT_Y40T44FF': 'Count_Death_40To44Years_Female',
        'DT_Y45T49FF': 'Count_Death_45To49Years_Female',
        'DT_Y50T54FF': 'Count_Death_50To54Years_Female',
        'DT_Y55T59FF': 'Count_Death_55To59Years_Female',
        'DT_Y60T64FF': 'Count_Death_60To64Years_Female',
        'DT_Y65T69FF': 'Count_Death_65To69Years_Female',
        'DT_Y70T74FF': 'Count_Death_70To74Years_Female',
        'DT_Y75T79FF': 'Count_Death_75To79Years_Female',
        'DT_Y_GE80FF': 'Count_Death_80OrMoreYears_Female',
        # 'D_Y0_14FF': 'Count_Death_Upto14Years_Female',
        'DT_Y_LT15FF': 'Count_Death_Upto14Years_Female',
        'DT_Y15T64FF': 'Count_Death_15To64Years_Female',
        'DT_Y_GE65FF': 'Count_Death_65OrMoreYears_Female',
    }

    df_cleaned.rename(columns=VAR_to_statsvars, inplace=True)
    columns_to_drop = [
        '10P3HB_Y_LT15_T_T', '10P3HB__TFF', '10P3HB__TMM', '10P3HB__T_T_T'
    ]

    # Drop columns if they exist
    for col in columns_to_drop:
        if col in df_cleaned.columns:
            df_cleaned.drop(col, axis=1, inplace=True)
    logging.info("Writing output to %s", output_file_path)
    df_cleaned.to_csv(output_file_path, index=False, quoting=csv.QUOTE_NONE)

    return df_cleaned


def generate_tmcf(df_cleaned, filepath):
    # Automate Template MCF generation since there are many Statistical Variables.
    TEMPLATE_MCF_TEMPLATE = """
    Node: E:OECD_deaths_cleaned->E{index}
    typeOf: dcs:StatVarObservation
    variableMeasured: dcs:{stat_var}
    measurementMethod: dcs:OECDRegionalStatistics
    observationAbout: C:OECD_deaths_cleaned->Reference area
    observationDate: C:OECD_deaths_cleaned->TIME_PERIOD
    observationPeriod: "P1Y"
    value: C:OECD_deaths_cleaned->{stat_var}
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
    url = "https://sdmx.oecd.org/public/rest/data/OECD.CFE.EDS,DSD_REG_DEMO@DF_DEATH_5Y,2.0/all?dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
    filename = os.path.join(_MODULE_DIR, "REGION_DEMOGR_death_5Y.csv")

    if mode == "" or mode == "download":
        download_data_to_file_and_df(url,
                                     filename,
                                     is_download_required=True,
                                     csv_filepath=None)
    if mode == "" or mode == "process":
        df = pd.read_csv(filename)
        output_file_path = os.path.join(_MODULE_DIR, "OECD_deaths_cleaned.csv")
        df_cleaned = process_data(df, output_file_path)
        filepath = os.path.join(_MODULE_DIR, "OECD_deaths.tmcf")
        generate_tmcf(df_cleaned, filepath)


if __name__ == "__main__":
    app.run(main)
