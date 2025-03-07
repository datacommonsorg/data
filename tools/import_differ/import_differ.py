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
_GROUPBY_COLUMNS = 'variableMeasured,observationAbout,observationDate,measurementMethod,unit,observationPeriod'
_VALUE_COLUMNS = 'value,scalingFactor'
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
flags.DEFINE_string('runner_mode', 'local', 'Dataflow runner mode(local/cloud)')
flags.DEFINE_string('project_id', '', 'GCP project id for the dataflow job.')
flags.DEFINE_string('job_name', 'differ', 'Name of the differ dataflow job.')


class ImportDiffer:
    """
  Utility to generate a diff (point and series analysis) 
  of two versions of the same dataset for import analysis. 

  Usage:
  $ python import_differ.py --current_data=<path> --previous_data=<path> --output_location=<path> \
    --file_format=<mcf/tfrecord> --runner_mode=<local/cloud> --project_id=<id> --job_name=<name> 

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
        self.output_path = os.path.join(output_location, job_name)
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

    def run_pipeline(self):
        """ 
        Runs dataflow job to process two datasets to identify changes.
        """
        if self.runner_mode == 'local':
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
            return os.system(cmd)
        else:  # cloud runner
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
                logging.error('Dataflow job failed to process input data')
                return 1
            else:
                return 0

    def process_data(self, diff_path: str) -> pd.DataFrame:
        column_list = self.groupby_columns + [
            '_value_combined_x', '_value_combined_y', 'diff_result'
        ]
        logging.info("Loading data from: %s", diff_path)
        diff = differ_utils.load_csv_data(diff_path, column_list, self.tmp_path)
        return diff

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

        logging.info('Running dataflow pipeline...')
        status = self.run_pipeline()
        if status > 0:
            logging.error('Dataflow pipeline run failed.')
            return

        logging.info('Processing diff data...')
        diff = self.process_data(os.path.join(self.output_path, 'diff*'))

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
