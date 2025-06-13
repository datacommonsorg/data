# Copyright 2024 Google LLC
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
""" Utility to generate a dataset diff for import analysis."""

import os
import pandas as pd
import random
import sys
import time
from enum import Enum

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

import differ_utils

_SAMPLE_COUNT = 3
_GROUPBY_COLUMNS = 'variableMeasured,observationAbout,observationDate,observationPeriod,measurementMethod,unit,scalingFactor'
_VALUE_COLUMNS = 'value'
_TMP_LOCATION = '/tmp'

Diff = Enum('Diff', [
    ('ADDED', 1),
    ('DELETED', 2),
    ('MODIFIED', 3),
])

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'current_data', '', 'Path to the current data \
  (wildcard on local/GCS supported).')
flags.DEFINE_string(
    'previous_data', '', 'Path to the previous data \
  (wildcard on local/GCS supported).')
flags.DEFINE_string('output_location', 'results', \
  'Path (local/GCS) to the output data folder.')
flags.DEFINE_string('differ_jar_location', '', \
  'Path to the differ tool jar (local runner mode).')
flags.DEFINE_string('file_format', 'mcf',
                    'Format of the input data (mcf,tfrecord)')
flags.DEFINE_string('runner_mode', 'native', 'Runner mode (native/local/cloud)')
flags.DEFINE_string('project_id', '', 'GCP project id for the dataflow job.')
flags.DEFINE_string('job_name', 'differ', 'Name of the differ dataflow job.')


class ImportDiffer:
    """
  Utility to generate a diff (point and series analysis) 
  of two versions of the same dataset for import analysis. 

  Usage:
  $ python import_differ.py --current_data=<path> --previous_data=<path> --output_location=<path> \
    --file_format=<mcf/tfrecord> --runner_mode=<native/local/cloud> --project_id=<id> --job_name=<name> 

  Summary output generated is of the form below showing 
  counts of differences for each variable.  

  variableMeasured   ADDED  DELETED  MODIFIED
  0   dcid:var1       1      0       0
  1   dcid:var2       0      2       1
  2   dcid:var3       0      0       1
  3   dcid:var4       0      2       0

  Detailed diff output is written to files for further analysis.
  - point_analysis_summary.csv: diff summry for point analysis
  - point_analysis_results.csv: detailed results for point analysis
  - series_analysis_summary.csv: diff summry for series analysisq
  - series_analysis_results.csv: detailed results for series analysis

  """

    def __init__(self,
                 current_data,
                 previous_data,
                 output_location,
                 differ_tool,
                 project_id,
                 job_name,
                 file_format,
                 runner_mode,
                 groupby_columns=_GROUPBY_COLUMNS,
                 value_columns=_VALUE_COLUMNS):
        self.current_data = current_data
        self.previous_data = previous_data
        self.output_path = output_location
        self.tmp_path = os.path.join(_TMP_LOCATION, job_name)
        self.differ_tool = differ_tool
        self.project_id = project_id
        self.job_name = job_name
        self.file_format = file_format
        self.runner_mode = runner_mode
        self.groupby_columns = groupby_columns.split(',')
        self.value_columns = value_columns.split(',')
        self.variable_column = self.groupby_columns[0]
        self.place_column = self.groupby_columns[1]
        self.time_column = self.groupby_columns[2]
        self.diff_column = 'diff_result'

    def _cleanup_data(self, df: pd.DataFrame):
        for column in Diff:
            df[column.name] = df[
                column.name] if column.name in df.columns else 0
            df[column.name] = df[column.name].fillna(0).astype(int)

    def _get_samples(self, row):
        years = sorted(row[self.time_column])
        if len(years) > _SAMPLE_COUNT:
            return [years[0]] + random.sample(years[1:-1],
                                              _SAMPLE_COUNT - 2) + [years[-1]]
        else:
            return years

    # Processes two dataset files to identify changes.
    def generate_diff(self, previous_df: pd.DataFrame,
                      current_df: pd.DataFrame) -> pd.DataFrame:
        """
        Process previous and current datasets to generate
        the intermediate data for point and series analysis.
        Args:
          current_df: dataframe with current (new) data
          previous_df: dataframe with previous (old) data
        Returns:
          intermediate merged data for analysis
        """
        for column in self.groupby_columns:
            if column not in current_df.columns.values.tolist():
                current_df[column] = ''
            if column not in previous_df.columns.values.tolist():
                previous_df[column] = ''
        df1 = previous_df.loc[:, self.groupby_columns + self.value_columns]
        df2 = current_df.loc[:, self.groupby_columns + self.value_columns]
        df1 = df1.reindex(columns=self.groupby_columns + self.value_columns)
        df2 = df2.reindex(columns=self.groupby_columns + self.value_columns)
        df1['_value_combined'] = df1[self.value_columns]\
          .apply(lambda row: '_'.join(row.values.astype(str)), axis=1)
        df2['_value_combined'] = df2[self.value_columns]\
          .apply(lambda row: '_'.join(row.values.astype(str)), axis=1)
        df1.drop(columns=self.value_columns, inplace=True)
        df2.drop(columns=self.value_columns, inplace=True)
        # Perform outer join operation to identify differences.
        result = pd.merge(df1,
                          df2,
                          on=self.groupby_columns,
                          how='outer',
                          indicator=self.diff_column)
        result[self.diff_column] = result.apply(
          lambda row: 'ADDED' if row[self.diff_column] == 'right_only' \
          else 'DELETED' if row[self.diff_column] == 'left_only' \
          else 'MODIFIED' if row['_value_combined_x'] != row['_value_combined_y'] \
          else 'UNMODIFIED', axis=1)
        result = result[result[self.diff_column] != 'UNMODIFIED']
        result.sort_values(by=[self.diff_column], inplace=True)
        result.reset_index(drop=True, inplace=True)
        return result

    def process_data(self) -> pd.DataFrame:
        """ 
        Runs job to process two datasets to identify changes.
        """
        if self.runner_mode == 'native':
            # Runs native Python differ.
            logging.info('Loading data...')
            current_dir = os.path.join(self.tmp_path, 'current')
            previous_dir = os.path.join(self.tmp_path, 'previous')
            current_df = differ_utils.load_data(self.current_data, current_dir)
            previous_df = differ_utils.load_data(self.previous_data,
                                                 previous_dir)
            logging.info('Generating diff...')
            in_data = self.generate_diff(previous_df, current_df)
            return in_data
        elif self.runner_mode == 'local':
            # Runs dataflow job in the local mode.
            args = {
                'currentData': self.current_data,
                'previousData': self.previous_data,
                'outputLocation': os.path.join(self.output_path, 'diff'),
            }
            if self.file_format == 'tfrecord':
                args['useOptimizedGraphFormat'] = 'true'
            logging.info("Running local dataflow job")
            cmd = f'java -jar {self.differ_tool}'
            for k, v in args.items():
                cmd += f' --{k}={v}'
            logging.info(cmd)
            status = os.system(cmd)
            if status > 0:
                raise ExecutionError(
                    'Dataflow job failed to process input data')
            diff_path = os.path.join(self.output_path, 'diff*')
            logging.info("Loading diff data from: %s", diff_path)
            diff = differ_utils.load_csv_data(diff_path, self.tmp_path)
        else:  # cloud runner
            # Runs dataflow job in GCP.
            logging.info('Launching dataflow job for processing data...')
            url = differ_utils.launch_dataflow_job(
                self.project_id, self.job_name, self.current_data,
                self.previous_data, self.file_format, self.output_path)
            logging.info('Dataflow job url: %s', url)
            status = 'JOB_STATE_UNKNONW'
            while (status != 'JOB_STATE_DONE' and status != 'JOB_STATE_FAILED'):
                logging.info(
                    f'Waiting for job {self.job_name} to complete. Status:{status}'
                )
                status = differ_utils.get_job_status(self.project_id,
                                                     self.job_name)
                time.sleep(60)
            if status == 'JOB_STATE_FAILED':
                raise ExectionError('Dataflow job failed to process input data')

            diff_path = os.path.join(self.output_path, 'diff*')
            logging.info("Loading diff data from: %s", diff_path)
            diff = differ_utils.load_csv_data(diff_path, self.tmp_path)

    def point_analysis(self,
                       diff: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
        """ 
        Performs point diff analysis to identify data point changes.

        Returns:
          summary and results from the analysis
        """
        if diff.empty:
            return pd.DataFrame(
                columns=['variableMeasured', 'ADDED', 'DELETED', 'MODIFIED'
                        ]), pd.DataFrame(columns=[
                            'variableMeasured', 'diff_result',
                            'observationAbout', 'observationDate', 'size'
                        ])

        column_list = [
            self.variable_column, self.place_column, self.time_column,
            self.diff_column
        ]
        result = diff.loc[:, column_list]
        result = result.groupby(
            [self.variable_column, self.diff_column],
            observed=True,
            as_index=False)[[self.place_column,
                             self.time_column]].agg(lambda x: x.tolist())
        result['size'] = result.apply(lambda row: len(row[self.place_column]),
                                      axis=1)
        result[self.place_column] = result.apply(lambda row: random.sample(
            row[self.place_column],
            min(_SAMPLE_COUNT, len(row[self.place_column]))),
                                                 axis=1)
        result[self.time_column] = result.apply(self._get_samples, axis=1)
        summary = result.pivot(
          index=self.variable_column, columns=self.diff_column, values='size')\
          .reset_index().rename_axis(None, axis=1)
        self._cleanup_data(summary)
        result.sort_values(by=[self.diff_column, self.variable_column],
                           inplace=True)
        return summary, result

    def series_analysis(self,
                        diff: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
        """ 
        Performs series diff analysis to identify time series changes.

        Returns:
          summary and results from the analysis
        """
        if diff.empty:
            return pd.DataFrame(columns=[
                'variableMeasured', 'observationAbout', 'ADDED', 'DELETED',
                'MODIFIED'
            ]), pd.DataFrame(columns=[
                'variableMeasured', 'observationAbout', 'diff_result',
                'observationDate', 'size'
            ])

        column_list = [
            self.variable_column, self.place_column, self.time_column,
            self.diff_column
        ]
        result = diff.loc[:, column_list]
        column_list = [
            self.variable_column, self.place_column, self.diff_column
        ]
        result = result.groupby(column_list,
                                as_index=False)[[self.time_column
                                                ]].agg(lambda x: x.tolist())
        result['size'] = result.apply(lambda row: len(row[self.time_column]),
                                      axis=1)
        summary = result.pivot(
          index=[self.variable_column, self.place_column], columns=self.diff_column, values='size')\
          .reset_index().rename_axis(None, axis=1)
        result[self.time_column] = result.apply(self._get_samples, axis=1)
        self._cleanup_data(summary)
        result.sort_values(by=[self.diff_column, self.variable_column],
                           inplace=True)
        return summary, result

    def run_differ(self):
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        if not os.path.exists(self.tmp_path):
            os.makedirs(self.tmp_path)

        logging.info('Processing input data...')
        diff = self.process_data()
        print(diff.head(10))

        logging.info('Point analysis:')
        summary, result = self.point_analysis(diff)
        print(summary.head(10))
        print(result.head(10))
        differ_utils.write_csv_data(summary, self.output_path,
                                    'point_analysis_summary.csv', self.tmp_path)
        differ_utils.write_csv_data(result, self.output_path,
                                    'point_analysis_results.csv', self.tmp_path)

        logging.info('Series analysis:')
        summary, result = self.series_analysis(diff)
        print(summary.head(10))
        print(result.head(10))
        differ_utils.write_csv_data(summary, self.output_path,
                                    'series_analysis_summary.csv',
                                    self.tmp_path)
        differ_utils.write_csv_data(result, self.output_path,
                                    'series_analysis_results.csv',
                                    self.tmp_path)

        logging.info('Differ output written to %s', self.output_path)


def main(_):
    '''Runs the differ.'''
    differ = ImportDiffer(_FLAGS.current_data, _FLAGS.previous_data,
                          _FLAGS.output_location, _FLAGS.differ_jar_location,
                          _FLAGS.project_id, _FLAGS.job_name,
                          _FLAGS.file_format, _FLAGS.runner_mode)
    differ.run_differ()


if __name__ == '__main__':
    app.run(main)
