# Copyright 2021 Google LLC
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
"""process module to generate the csv/tmcf and csv for S2408"""
import os
import sys
import json
from zipfile import ZipFile

import numpy as np
import pandas as pd

import os
import sys
import json

from absl import app, flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../common'))  # for col_map_generator, data_loader

from generate_col_map import process_zip_file
from data_loader import SubjectTableDataLoaderBase
from resolve_geo_id import convert_to_place_dcid

FLAGS = flags.FLAGS
flags.DEFINE_string(
    'option', 'all',
    'Specify how to run the process, colmap -- generates column map, process -- runs processing, all -- runs colmap first and then proessing'
)
flags.DEFINE_string(
    'table_prefix', None,
    '[for processing]Subject Table ID as a prefix for output files, eg: S2702')
flags.DEFINE_string('spec_path', None, 'Path to the JSON spec [mandatory]')
flags.DEFINE_string(
    'input_path', None,
    'Path to input directory with (current support only for zip files)')
flags.DEFINE_string('output_dir', './', 'Path to the output directory')
flags.DEFINE_boolean(
    'has_percent', False,
    '[for processing]Specify the datasets has percentage values that needs to be convered to counts'
)
flags.DEFINE_boolean(
    'debug', False,
    '[for processing]set the flag to add additional columns to debug')


def process_subject_tables(table_prefix='',
                           input_path='./',
                           output_dir='./',
                           column_map_path=None,
                           spec_path=None,
                           debug=False,
                           delimiter='!!',
                           has_percent=False,
                           decimal_places=3,
                           header_row=1,
                           estimate_period=5):
    ## create a data loader object with base parameters
    data_loader = S2408SubjectTableLoader(table_id=table_prefix,
                                          col_delimiter=delimiter,
                                          has_percent=has_percent,
                                          debug=debug,
                                          output_path_dir=output_dir,
                                          json_spec=spec_path,
                                          column_map_path=column_map_path,
                                          decimal_places=decimal_places,
                                          estimate_period=estimate_period,
                                          header_row=header_row)

    ## if input_path is a file, select csv/zip processing methods
    _, file_extension = os.path.splitext(input_path)
    if file_extension == '.zip':
        data_loader._process_zip_file(input_path)

    elif file_extension == '.csv':
        data_loader._process_csv_file(input_path)

    else:
        data_loader._process_dir(input_path)


class S2408SubjectTableLoader(SubjectTableDataLoaderBase):

    def _process_dataframe(self, df, filename):
        """processes a dataframe read from a csv file"""
        df = self._replace_ignore_values_with_nan(
            df)  #handle the values to be ignored
        year = filename.split(f'ACSST{self.estimate_period}Y')[1][:4]
        print(f"Processing: {filename}", end=" |  ", flush=True)
        # if has_percent is set, convert percentages to counts. Convert
        # percentage to count only for years from 2010 - 2014.
        percent_years = ['2010', '2011', '2012', '2013', '2014']
        if self.has_percent and year in percent_years:
            print(f"Converting percent to counts", end=" |  ", flush=True)
            df = self._convert_percent_to_numbers(df)

        # if column map is not available generate, will rarely be False
        column_map = self.column_map[year]

        # add stats to dict_counter for current year
        self.counter_dict[year] = {
            "filename":
                filename,
            "number of columns in dataset":
                df.shape[1],
            "number of rows in dataset":
                df.shape[0],
            "number of statVars generated for columns":
                len(list(column_map.keys())),
            "number of observations":
                0,
            "number of unique StatVars with observations":
                0,
        }

        csv_file = open(self.clean_csv_path, 'a')
        place_geoIds = df['id'].apply(convert_to_place_dcid)

        # update the clean csv
        for column in df.columns.tolist():
            if column in column_map:
                obs_df = pd.DataFrame(columns=self.csv_columns)
                obs_df['Place'] = place_geoIds
                obs_df['StatVar'] = column_map[column]['Node']
                # obs_df['Quantity'] = df[column].values.tolist()

                # Clean the quantity values by removing commas, dashes, and any non-numeric characters like '+'
                obs_df['Quantity'] = df[column].apply(lambda x: str(x).replace(
                    ',', '').replace('-', '').replace('+', '')).astype(
                        float).tolist()

                # add unit to the csv
                try:
                    unit = column_map[column]['unit']
                    del column_map[column]['unit']
                except KeyError:
                    unit = np.nan
                obs_df['Unit'] = unit

                # add scaling factor to the csv
                try:
                    scalingFactor = column_map[column]['scalingFactor']
                    del column_map[column]['scalingFactor']
                except KeyError:
                    scalingFactor = np.nan
                obs_df['ScalingFactor'] = scalingFactor

                # if StatVar not in mcf_dict, add dcid
                dcid = column_map[column]['Node']

                if dcid not in self.mcf_dict:
                    ## key --> node dcid
                    self.mcf_dict[dcid] = {}
                    ## add pvs to dict
                    for key, value in column_map[column].items():
                        if key != 'Node':
                            self.mcf_dict[dcid][key] = value

                obs_df['Year'] = year
                obs_df['Column'] = column

                # Replace empty places (unresolved geoIds) as null values
                obs_df['Place'].replace('', np.nan, inplace=True)

                # Drop rows with observations for empty (null) values
                obs_df.dropna(subset=['Place', 'Quantity'],
                              axis=0,
                              inplace=True)

                # Write the processed observations to the clean_csv
                if self.year_count == 0:
                    obs_df.to_csv(csv_file, header=True, index=False, mode='w')
                else:
                    obs_df.to_csv(csv_file, header=False, index=False, mode='a')
                self.year_count += 1

                # update stats for the year:
                self.counter_dict[year]["number of unique geos"] = len(
                    obs_df['Place'].unique())
                self.counter_dict[year][
                    "number of observations"] += obs_df.shape[0]
                self.counter_dict[year][
                    "number of unique StatVars with observations"] += len(
                        obs_df['StatVar'].unique())
                self.counter_dict[year]["number of StatVars in mcf_dict"] = len(
                    list(self.mcf_dict.keys()))
        csv_file.close()
        print(
            f"""Completed with { self.counter_dict[year]['number of observations'] }
            observation for { self.counter_dict[year]['number of unique StatVars with observations'] }
            StatVars at { self.counter_dict[year]['number of unique geos'] } places.
            """,
            flush=True)


def set_column_map(input_path, spec_path, output_dir):
    generated_col_map = process_zip_file(input_path,
                                         spec_path,
                                         write_output=False)
    f = open(os.path.join(output_dir, 'column_map.json'), 'w')
    json.dump(generated_col_map, f, indent=4)
    f.close()


def main(argv):
    ## get inputs from flags
    option = FLAGS.option.lower()
    table_prefix = FLAGS.table_prefix
    spec_path = FLAGS.spec_path
    input_path = FLAGS.input_path
    output_dir = FLAGS.output_dir
    has_percent = FLAGS.has_percent
    debug = FLAGS.debug

    _, file_extension = os.path.splitext(input_path)

    if file_extension == '.zip':
        if option == 'colmap':
            set_column_map(input_path, spec_path, output_dir)
        if option == 'process':
            process_subject_tables(table_prefix=table_prefix,
                                   input_path=input_path,
                                   output_dir=output_dir,
                                   column_map_path=os.path.join(
                                       output_dir, 'column_map.json'),
                                   spec_path=spec_path,
                                   debug=debug,
                                   delimiter='!!',
                                   has_percent=has_percent)

        if option == 'all':
            set_column_map(input_path, spec_path, output_dir)
            process_subject_tables(table_prefix=table_prefix,
                                   input_path=input_path,
                                   output_dir=output_dir,
                                   column_map_path=os.path.join(
                                       output_dir, 'column_map.json'),
                                   spec_path=spec_path,
                                   debug=debug,
                                   delimiter='!!',
                                   has_percent=has_percent)
    else:
        print("At the moment, we support only zip files.")


if __name__ == '__main__':
    flags.mark_flags_as_required(
        ['table_prefix', 'spec_path', 'input_path', 'output_dir'])
    app.run(main)
