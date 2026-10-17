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
"""Process data from Census ACS 5-Year Subject Table S2303."""

import json
import os
import sys

from absl import app
from absl import flags
from absl import logging
import numpy as np
import pandas as pd

# pylint: disable=wrong-import-position
# pylint: disable=import-error
_CODEDIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(_CODEDIR, '..', 'common'))

from data_loader import SubjectTableDataLoaderBase
from generate_col_map import process_zip_file
from resolve_geo_id import convert_to_place_dcid
# pylint: enable=wrong-import-position
# pylint: enable=import-error

FLAGS = flags.FLAGS


class S2303SubjectTableDataLoader(SubjectTableDataLoaderBase):
    """Data loader for Census ACS 5-Year Subject Table S2303."""

    def _process_dataframe(self, df, filename):
        """Processes a dataframe read from a CSV file."""
        df = self._replace_ignore_values_with_nan(df)
        year = filename.split(f'ACSST{self.estimate_period}Y')[1][:4]
        logging.info(f'Processing: {filename}')

        # Only convert percentages to counts for 2010-2014 (2015+ report counts directly).
        percent_years = self.json_spec.get(
            'percent_years', ['2014', '2013', '2012', '2011', '2010'])
        if self.has_percent and year in percent_years:
            logging.info(f'Converting percent to numbers for {year}')
            df = self._convert_percent_to_numbers(df)

        column_map = self.column_map[year]

        # Add stats to counter_dict for current year.
        self.counter_dict[year] = {
            'filename':
                filename,
            'number of columns in dataset':
                df.shape[1],
            'number of rows in dataset':
                df.shape[0],
            'number of statVars generated for columns':
                len(list(column_map.keys())),
            'number of observations':
                0,
            'number of unique StatVars with observations':
                0,
        }

        if 'id' in df.columns:
            place_geo_ids = df['id'].apply(convert_to_place_dcid)
        else:
            place_geo_ids = df['Geography'].apply(convert_to_place_dcid)

        with open(self.clean_csv_path, 'a') as csv_file:
            for column in df.columns.tolist():
                if column in column_map:
                    obs_df = pd.DataFrame(columns=self.csv_columns)
                    obs_df['Place'] = place_geo_ids
                    obs_df['StatVar'] = column_map[column]['Node']
                    obs_df['Quantity'] = df[column].values.tolist()

                    try:
                        unit = column_map[column]['unit']
                        del column_map[column]['unit']
                    except KeyError:
                        unit = np.nan
                    obs_df['Unit'] = unit

                    try:
                        scaling_factor = column_map[column]['scalingFactor']
                        del column_map[column]['scalingFactor']
                    except KeyError:
                        scaling_factor = np.nan
                    obs_df['ScalingFactor'] = scaling_factor

                    dcid = column_map[column]['Node']
                    if dcid not in self.mcf_dict:
                        self.mcf_dict[dcid] = {}
                        for key, value in column_map[column].items():
                            if key != 'Node':
                                self.mcf_dict[dcid][key] = value

                    obs_df['Year'] = year
                    obs_df['Column'] = column

                    # Replace empty places (unresolved geoIds) as null values.
                    obs_df['Place'] = obs_df['Place'].replace('', np.nan)

                    # Drop rows with observations for empty (null) values.
                    obs_df.dropna(subset=['Place', 'Quantity'],
                                  axis=0,
                                  inplace=True)

                    if self.year_count == 0:
                        obs_df.to_csv(csv_file,
                                      header=True,
                                      index=False,
                                      mode='w')
                    else:
                        obs_df.to_csv(csv_file,
                                      header=False,
                                      index=False,
                                      mode='a')
                    self.year_count += 1

                    self.counter_dict[year]['number of unique geos'] = len(
                        obs_df['Place'].unique())
                    self.counter_dict[year][
                        'number of observations'] += obs_df.shape[0]
                    self.counter_dict[year][
                        'number of unique StatVars with observations'] += len(
                            obs_df['StatVar'].unique())
                    self.counter_dict[year][
                        'number of StatVars in mcf_dict'] = len(
                            list(self.mcf_dict.keys()))

        n_obs = self.counter_dict[year]['number of observations']
        n_sv = self.counter_dict[year][
            'number of unique StatVars with observations']
        n_geos = self.counter_dict[year]['number of unique geos']
        logging.info(
            f'Completed with {n_obs} observations for {n_sv} StatVars at '
            f'{n_geos} places.')


def process_subject_tables(table_prefix,
                           input_path,
                           column_map_path,
                           spec_path,
                           output_dir='./',
                           has_percent=False,
                           debug=False,
                           estimate_period=5,
                           delimiter='!!',
                           decimal_places=3,
                           header_row=1):
    """Processes S2303 zip/directory/csv inputs into cleaned CSV, MCF, and TMCF."""
    data_loader = S2303SubjectTableDataLoader(table_id=table_prefix,
                                              col_delimiter=delimiter,
                                              has_percent=has_percent,
                                              debug=debug,
                                              output_path_dir=output_dir,
                                              json_spec=spec_path,
                                              column_map_path=column_map_path,
                                              decimal_places=decimal_places,
                                              estimate_period=estimate_period,
                                              header_row=header_row)

    if os.path.isdir(input_path):
        data_loader._process_dir(input_path)
    else:
        _, file_extension = os.path.splitext(input_path)
        if file_extension == '.zip':
            data_loader._process_zip_file(input_path)
        elif file_extension == '.csv':
            data_loader._process_csv_file(input_path)


def set_column_map(input_path, spec_path, output_dir):
    generated_col_map = process_zip_file(input_path,
                                         spec_path,
                                         write_output=False)
    with open(os.path.join(output_dir, 'column_map.json'), 'w') as f:
        json.dump(generated_col_map, f, indent=4)


def main(argv):
    del argv
    option = FLAGS.option.lower()
    if option not in ('colmap', 'process', 'all'):
        logging.fatal(
            f"Invalid --option '{FLAGS.option}'. Must be one of: 'colmap', "
            "'process', 'all'.")
    table_prefix = FLAGS.table_prefix
    spec_path = FLAGS.spec_path
    input_path = FLAGS.input_path
    output_dir = FLAGS.output_dir
    has_percent = FLAGS.has_percent
    debug = FLAGS.debug

    _, file_extension = os.path.splitext(input_path)

    if file_extension == '.zip':
        if option in ('colmap', 'all'):
            set_column_map(input_path, spec_path, output_dir)
        if option in ('process', 'all'):
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
        logging.fatal('At the moment, we support only zip files.')


if __name__ == '__main__':
    flags.DEFINE_string(
        'option', 'all',
        'Specify how to run the process, colmap -- generates column map, '
        'process -- runs processing, all -- runs colmap first and then '
        'processing')
    flags.DEFINE_string(
        'table_prefix', None,
        '[for processing] Subject Table ID as a prefix for output files, '
        'eg: S2303')
    flags.DEFINE_string('spec_path', None, 'Path to the JSON spec [mandatory]')
    flags.DEFINE_string(
        'input_path', None,
        'Path to input directory with (current support only for zip files)')
    flags.DEFINE_string('output_dir', './', 'Path to the output directory')
    flags.DEFINE_boolean(
        'has_percent', False,
        '[for processing] Specify if the dataset has percentage values that '
        'need to be converted to counts')
    flags.DEFINE_boolean(
        'debug', False,
        '[for processing] Set the flag to add additional columns to debug')
    flags.mark_flags_as_required(
        ['table_prefix', 'spec_path', 'input_path', 'output_dir'])
    app.run(main)
