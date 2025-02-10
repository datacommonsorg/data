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
import json
from zipfile import ZipFile

import numpy as np
import pandas as pd

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(_SCRIPT_PATH, '.'))  # for resolve_geo_id
from resolve_geo_id import convert_to_place_dcid

_IGNORED_VALUES = set(['-', '*', '**', '***', '*****', 'N', '(X)', 'null'])

# TODO: Consider using logs for logging warning messages for debug at a later
# date


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
    data_loader = SubjectTableDataLoaderBase(table_id=table_prefix,
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


class SubjectTableDataLoaderBase:
    """
    A common module that has a collection of methods for subject table data processing.


  Attributes:
  table_prefix: string prefix that will be added to differentiate outputs
  input_path: path to the input file(s). The module supports inputs as either
    a zip file or a csv file or a directory with zip/ csv files
  output_dir: path to the output directory
  column_map_path: path to the column_map generated with `generate_col_map.py`
  spec_path: path to the JSON specification for the subject table
  debug: if set, adds additional columns to output csv for debugging (default: False)
  col_delimiter: String denoting the delimiter character in dataset (default: '!!')
  has_percent: if set, converts percent to count values (default: False)
  decimal_places: specifies the number of digits after decimal place (default: 3)
  estimate_period: specifies the duration of the subject period estimate (default: 5)
                : since we use the 5 year subject table estimate
  header_row: specifies the row index to be considered as the dataframe's header
  for column name assignment. For subject tables, the second row (row index = 1)
  has a human readable column header. (default: 1)

  """

    def __init__(self,
                 table_id='',
                 col_delimiter='!!',
                 has_percent=False,
                 debug=False,
                 output_path_dir='./',
                 json_spec='./',
                 column_map_path='./',
                 decimal_places=3,
                 estimate_period=5,
                 header_row=1):
        """module init"""
        ## static inputs
        self.table_id = table_id
        self.has_percent = has_percent
        self.debug = debug
        self.decimal_places = decimal_places
        self.delimiter = col_delimiter
        self.estimate_period = estimate_period
        self.header_row = header_row

        ## set the output path, if not exists, make directory
        if not os.path.exists(output_path_dir):
            os.mkdir(output_path_dir)
        self.output_path_dir = output_path_dir
        self.base_tmcf_path = os.path.join(_SCRIPT_PATH,
                                           './subject_table_base.tmcf')

        ## get the content of JSON spec
        try:
            f = open(json_spec, 'r')
            self.json_spec = json.load(f)
            f.close()
        except:
            print("Please ensure that the path to the JSON spec is correct.")
            exit(1)

        ## get the content from Column map
        try:
            f = open(column_map_path, 'r')
            self.column_map = json.load(f)
            f.close()
        except:
            # TODO: If the module is called from `process.py`, the message needs
            # to be to run with --option=colmap. So rephrasing this message will help.
            print(
                """To run this module in standalone mode, ensure the column map
                is generated by running `generate_col_map` module.""")
            exit(1)

        ## initialize other class variables
        self.mcf_dict = {}

        # initialize a dictionary of counters
        # TODO: Add a means to fill the git commit SHA
        self.counter_dict = {
            "summary": {
                "column map generator commit SHA": "",
                "data processing script commit SHA": "",
                "total StatVarObservations": 0,
            },
        }

        # initialize the StatVarObservation csv
        self.csv_columns = [
            'Year', 'Place', 'StatVar', 'Quantity', 'Unit', 'ScalingFactor',
            'Column'
        ]  #optional: Unit, ScalingFactor
        self.clean_csv_path = os.path.join(output_path_dir,
                                           f'./{table_id}_cleaned.csv')
        self.year_count = 0
        if os.path.exists(self.clean_csv_path):
            os.remove(self.clean_csv_path)

    def _convert_percent_to_numbers(self, df):
        """utility to convert percent to numbers"""
        # TODO: Currently this function expects full names for function, which
        # makes the spec long, perhaps we can add support for tokens
        df_columns = df.columns.tolist()
        for count_col, percent_col_list in self.json_spec['denominators'].items(
        ):
            # TODO: add a warning message
            if count_col in df_columns:
                for col in percent_col_list:
                    if col in df_columns:
                        df[col] = df[col].astype(float)
                        df[count_col] = df[count_col].astype(float)
                        df[col] = (df[col] / 100) * df[count_col]
                        df[col] = df[col].round(
                            3
                        )  # TODO: replace with parameter self.decimal_places
        return df

    def _get_summary(self):
        """
        method returns the total number of columns, stat vars and other stats
        from the column_map and csv.
        """
        for key, count_dict in self.counter_dict.items():
            if key != 'summary':
                self.counter_dict['summary'][
                    "total StatVarObservations"] += count_dict[
                        "number of observations"]
        return self.counter_dict

    def _replace_ignore_values_with_nan(self, df):
        """
        Replaces cells of the dataframe by column with nan if cell has values in
        _IGNORED_VALUES.
        """
        for col in df.columns.tolist():
            df[col] = df[col].apply(lambda row: np.nan
                                    if row in _IGNORED_VALUES else row)
        return df

    def _process_dataframe(self, df, filename):
        """processes a dataframe read from a csv file"""
        df = self._replace_ignore_values_with_nan(
            df)  #handle the values to be ignored
        year = filename.split(f'ACSST{self.estimate_period}Y')[1][:4]
        print(f"Processing: {filename}", end=" |  ", flush=True)
        # if has_percent is set, convert percentages to counts. Requires the
        # 'denominators' key to be specified in the spec
        if self.has_percent:
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
                obs_df['Place'] = obs_df['Place'].replace('', np.nan)

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

    def _generate_mcf_from_column_map(self):
        """
        uses column_map to generate a mcf file with all the stat_vars nodes that
        are created.
        """

        #get cleaned column map
        final_mcf = ""

        for column, stat_var in self.mcf_dict.items():
            col_stat_var = []
            # TODO: Add 'Node:' as the first element of col_stat_var, and append
            # all the stat-var node information to col_stat_var
            dcid = 'Node: ' + column + '\n'

            for p, v in stat_var.items():
                if p != 'unit' or p != 'scalingFactor':
                    col_stat_var.append(f"{p}: {v}")
            # TODO: Replace the next two lines with final_mcf = final_mcf + '\n'.join(col_stat_var) + '\n\n'
            col_stat_var = dcid + '\n'.join(col_stat_var)
            final_mcf = final_mcf + col_stat_var + "\n\n"
        return final_mcf

    def _generate_tmcf_from_clean_csv(self):
        """update the base tmcf template based on the clean_csv"""
        clean_csv = pd.read_csv(self.clean_csv_path, low_memory=False)
        empty_cols = [
            col for col in clean_csv.columns if clean_csv[col].isnull().all()
        ]

        f = open(self.base_tmcf_path, 'r')
        tmcf_contents = f.read().splitlines()
        f.close()

        ## modify the tmcf file content
        for col in empty_cols:
            for index, line in enumerate(tmcf_contents):
                if col in line:
                    del tmcf_contents[index]

        ## write into the output tmcf
        tmcf_contents = '\n'.join(tmcf_contents)
        if not self.debug:
            clean_csv.drop(columns=['Column'], inplace=True)

        ## update the csv by dropping empty column
        clean_csv.drop(columns=empty_cols, inplace=True)
        clean_csv.to_csv(self.clean_csv_path, index=False)
        return tmcf_contents

    def _get_outputs(self):
        """aggregated method which stores tmcf and clean_csv to output directory"""
        ### write to mcf
        final_mcf = self._generate_mcf_from_column_map()
        f = open(
            os.path.join(self.output_path_dir, f'./{self.table_id}_output.mcf'),
            'w')
        f.write(final_mcf)
        f.close()

        ## write to tmcf
        final_tmcf = self._generate_tmcf_from_clean_csv()
        f = open(
            os.path.join(self.output_path_dir,
                         f'./{self.table_id}_output.tmcf'), 'w')
        f.write(final_tmcf)
        f.close()

        ## write all stat_vars from column map to file for debugging
        if self.debug:
            debug_df = pd.DataFrame(columns=['Year', 'Column', 'StatVarID'])
            for year, val in self.column_map.items():
                for column, stat_var in val.items():
                    debug_df = debug_df.append(
                        {
                            'Year': year,
                            'Column': column,
                            'StatVarID': stat_var['Node']
                        },
                        ignore_index=True)
            debug_df.to_csv(os.path.join(self.output_path_dir,
                                         './column_to_dcid.csv'),
                            index=False)
            f = open(
                os.path.join(self.output_path_dir,
                             './column_to_statvar_map.json'), 'w')
            json.dump(self.column_map, f, indent=4)
            f.close()

        ## write summary dict of counters
        counter_dict = self._get_summary()
        summary_path = os.path.join(self.output_path_dir,
                                    f'{self.table_id}_summary.json')
        f = open(summary_path, 'w')
        json.dump(counter_dict, f, indent=4)
        f.close()
        print(f"""processing of subject table is complete: the summary of the
            process is available at {summary_path} along with the generated
            output files.""")

    def _process_zip_file(self, zip_file_path):
        """processes each dataset in a zip file to make the clean csv of StatVarObs"""
        zf = ZipFile(zip_file_path)
        for filename in zf.namelist():
            if 'data_with_overlays' in filename:
                df = pd.read_csv(zf.open(filename, 'r'),
                                 header=self.header_row,
                                 low_memory=False)
                self._process_dataframe(df, filename)
        zf.close()
        self._get_outputs()

    def _process_dir(self, input_dir_path):
        """specify the folder_path with data files to generate StatVarObs csv"""
        try:
            for filename in os.listdir(input_dir_path):
                ## if zip file is present in directory, try _process_zip_file()
                if os.path.splitext(filename)[1] == 'zip':
                    self._process_zip_file(
                        os.path.join(input_dir_path, filename))
                ## if input_directory has csv files, process them
                if 'data_with_overlays' in filename:
                    input_path = os.path.join(input_dir_path, filename)
                    df = pd.read_csv(input_path,
                                     header=self.header_row,
                                     low_memory=False)
                    self._process_dataframe(df, filename)
            self._get_outputs()
        except:
            print("""ensure input path is that of directory with dataset files,
                a zip file or a csv file""")

    def _process_csv_file(self, input_path):
        df = pd.read_csv(input_path, header=self.header_row, low_memory=False)
        self._process_dataframe(df, input_path)
        self._get_outputs()
