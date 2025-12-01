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
from absl import flags, logging
from absl import app
from columns import *

_FLAGS = flags.FLAGS
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(_MODULE_DIR)
flags.DEFINE_string('mode', '', 'Options: download or process')

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
    df1.loc[:, "AGE"] = df1["UNIT_MEASURE"] + "_" + df1["AGE"] + df1["SEX"]

    # First remove geos with names that we don't have mappings to dcid for.
    try:
        regid_file = os.path.join(parent_dir, "regid2dcid.json")
        with open(regid_file, 'r') as f:
            regid2dcid = dict(json.loads(f.read()))
        logging.info(f"Resolving places from {regid_file}")
        df2 = df1[~df1['REF_AREA'].isin(regid2dcid.keys())]
        unmapped = len(df2["REF_AREA"].unique())
        logging.info(f"{unmapped} places have not been resolved")
        df1 = df1[df1['REF_AREA'].isin(regid2dcid.keys())]
        mapped = len(df1["REF_AREA"].unique())
        logging.info(f"{mapped} places have been resolved")
        # Second, replace the names with dcids
        df1['Reference area'] = df1.apply(
            lambda row: regid2dcid[row['REF_AREA']], axis=1)
    except Exception as e:
        logging.fatal(f"Error processing regid2dcid.json: {e}")
        return None  # Indicate failure

    df1['TIME_PERIOD'] = '"' + df1['TIME_PERIOD'].astype(str) + '"'

    temp = df1[['Reference area', 'AGE', 'SEX', 'TIME_PERIOD', 'OBS_VALUE']]
    try:
        temp_multi_index = temp.pivot_table(
            values='OBS_VALUE',
            index=['Reference area', 'TIME_PERIOD'],
            columns=['AGE', 'SEX'])
        df_cleaned = multi_index_to_single_index(temp_multi_index)
    except Exception as e:
        logging.fatal(
            f"Unable to pivot the dataframe and retain the columns:{e}")
        return None
    # Renaming column headers to their SVs
    df_cleaned.rename(columns=VAR_to_statsvars, inplace=True)
    # Filtering the reuired columns
    df_cleaned_reset = df_cleaned.reindex(columns=reindex_columns)
    logging.info("Writing output to %s", output_file_path)
    df_cleaned_reset.to_csv(output_file_path,
                            index=False,
                            quoting=csv.QUOTE_NONE)

    return df_cleaned_reset


def generate_tmcf(df_cleaned_reset, filepath):
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

    stat_vars = df_cleaned_reset.columns[2:]
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
        filepath = os.path.join(_MODULE_DIR, "OECD_deaths_cleaned.tmcf")
        generate_tmcf(df_cleaned, filepath)


if __name__ == "__main__":
    app.run(main)
