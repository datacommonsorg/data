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
"""Common data processing module for ACS Subject Tables"""
import os
import sys
import numpy as np
import pandas as pd
# TODO: Consider using logs for logging warning messages for debug at a later
# date
#
# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(_SCRIPT_PATH, '../common'))  # for resolve_geo_id
from data_loader import SubjectTableDataLoaderBase
from resolve_geo_id import convert_to_place_dcid

_IGNORED_VALUES = set(['-', '*', '**', '***', '*****', 'N', '(X)', 'null'])


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
    """
    Wrapper method for invoking the data processing module, maps files with the
    corresponding processing function based on input format (*.zip/*.csv),
    output files are saved in the specified output directory.

    NOTE: This module does not generate the column_map, you will need to run the
  `generate_col_map.py` module before running this module in standalone mode.

  NOTE: If the path for column_map is not specified this module will exit with
  an error, stating that the column_map is a required input.

  Args:
  table_prefix: string prefix that will be added to differentiate outputs
  input_path: path to the input file(s). The module supports inputs as either
    a zip file or a csv file or a directory with zip/ csv files
  output_dir: path to the output directory
  column_map_path: path to the column_map generated with `generate_col_map.py`
  spec_path: path to the JSON specification for the subject table
  debug: if set, adds additional columns to output csv for debugging (default: False)
  delimiter: String denoting the delimiter character in dataset (default: '!!')
  has_percent: if set, converts percent to count values (default: False)
  decimal_places: specifies the number of digits after decimal place (default: 3)
  estimate_period: specifies the duration of the subject period estimate (default: 5)
                : since we use the 5 year subject table estimate
    header_row: specifies the row index to be considered as the dataframe's
    header for column name assignment. For subject tables, the second row (row index = 1)
    has a human readable column header. (default: 1)
  header_row: specifies the row index to be considered as the dataframe's header
  for column name assignment. For subject tables, the second row (row index = 1)
  has a human readable column header. (default: 1)

  Outputs:
  The module will write the following files to the specified output directory
  <table_prefix>_cleaned.csv:
    csv file with StatVarObservations i.e. quantity measured for a stat_var at a particular place and date.
    It also has additional columns like units, and scalingFactor if they are specified in the JSON spec.
  <table_prefix>_output.mcf:
    file in mcf format with all the StatVars generated in the column map
  <table_prefix>_output.tmcf:
    template mcf file used in combination with the csv file for data import
  <table_prefix>_summary.json:
    summary stats of data processing year-wise

  If debug=True, additional output files are written to the output directory
  column_to_dcid.csv:
    maps the stat var dcid associated to each column of the data file
  column_to_statvar_map.json:
    a json file with column mapped to the complete stat-var node
  <table_prefix>_cleaned.csv will have an additional column containing the name of column in the dataset for which each StatVarObservation was recorded
  """
    ## create a data loader object with base parameters
    data_loader = S2409SubjectTableDataLoaderBase(
        table_id=table_prefix,
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


class S2409SubjectTableDataLoaderBase(SubjectTableDataLoaderBase):
    """
    A common module that has a collection of methods for subject table S2409 data processing
    inheriting from class SubjectTableDataLoaderBase

    """

    def __init__(self, table_id, col_delimiter, has_percent, debug,
                 output_path_dir, json_spec, column_map_path, decimal_places,
                 estimate_period, header_row):
        super().__init__(table_id, col_delimiter, has_percent, debug,
                         output_path_dir, json_spec, column_map_path,
                         decimal_places, estimate_period, header_row)

    def _process_dataframe(self, df, filename):
        """processes a dataframe read from a csv file"""
        df = self._replace_ignore_values_with_nan(
            df)  #handle the values to be ignored
        year = filename.split(f'ACSST{self.estimate_period}Y')[1][:4]
        print(f"Processing: {filename}", end=" |  ", flush=True)

        percent_years = ['2010', '2011', '2012', '2013', '2014']
        # if has_percent is set, convert percentages to counts. Requires the
        # 'denominators' key to be specified in the spec
        #if self.has_percent:
        if self.has_percent and year in percent_years:
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
                obs_df['Quantity'] = df[column].values.tolist()
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
