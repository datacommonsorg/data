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
    column_rename = {
        'TERRITORIAL_LEVEL': 'TL',
        'REF_AREA': 'REG_ID',
        'Reference area': 'Region',
        'MEASURE': 'VAR',
        'TIME_PERIOD': 'Year',
        'OBS_VALUE': 'Value'
    }
    df = df.rename(columns=column_rename)
    df = df[df['UNIT_MEASURE'] == "PS_KM2"]
    logging.info("Filtering the required columns")
    df = df[['TL', 'REG_ID', 'Region', 'VAR', 'SEX', 'Year', 'Value']]
    # First remove geos with names that we don't have mappings to dcid for.
    regid_file = "scripts/oecd/regional_demography/regid2dcid.json"
    with open(regid_file, 'r') as f:
        regid2dcid = dict(json.loads(f.read()))
    logging.info("Resolving places")
    df = df[df['REG_ID'].isin(regid2dcid.keys())]
    # Second, replace the names with dcids
    df['Region'] = df.apply(lambda row: regid2dcid[row['REG_ID']], axis=1)

    df['Year'] = '"' + df['Year'].astype(str) + '"'
    temp = df[['REG_ID', 'Region', 'VAR', 'Year', 'Value']]
    temp_multi_index = temp.pivot_table(values='Value',
                                        index=['REG_ID', 'Region', 'Year'],
                                        columns=['VAR'])
    df_cleaned = multi_index_to_single_index(temp_multi_index)[[
        'REG_ID', 'Region', 'Year', 'POP'
    ]]

    VAR_to_statsvars = {
        'POP': 'Count_Person_PerArea'
        # 'SURF': 'Area',
    }

    df_cleaned.rename(columns=VAR_to_statsvars, inplace=True)
    logging.info("Writing output to %s",output_file_path)
    df_cleaned.to_csv(output_file_path, index=False, quoting=csv.QUOTE_NONE)


def main(_):
    mode = _FLAGS.mode
    url = "https://sdmx.oecd.org/public/rest/data/OECD.CFE.EDS,DSD_REG_DEMO@DF_DENSITY,2.0/all?dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
    filename = os.path.join(_MODULE_DIR, "REGION_DEMOGR_pop_density.csv")

    if mode == "" or mode == "download":
        download_data_to_file_and_df(url, filename, is_download_required=True,csv_filepath=None)
    if mode == "" or mode == "process":
        df = pd.read_csv(filename)
        output_file_path = os.path.join(_MODULE_DIR, "OECD_pop_density_cleaned.csv")
        process_data(df, output_file_path)

if __name__ == "__main__":
    app.run(main)
