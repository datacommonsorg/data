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
from googleapiclient.discovery import build

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

import differ_utils

_SAMPLE_COUNT = 3
_OBS_COLUMNS = 'variableMeasured,observationAbout,observationDate,observationPeriod,measurementMethod,unit,scalingFactor,value'
_NODE_COLUMNS = 'Node,typeOf,populationType'

Diff = Enum('Diff', [
    ('ADDED', 1),
    ('DELETED', 2),
    ('MODIFIED', 3),
    ('UNMODIFIED', 4),
])

Column = Enum('Column', [
    ('variableMeasured', 1),
    ('observationDate', 2),
    ('value', 3),
    ('typeOf', 4),
    ('Node', 5),
    ('diff_type', 6),
    ('diff_size', 7),
    ('observationAbout', 8),
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
flags.DEFINE_string('file_format', 'mcf',
                    'Format of the input data (mcf,tfrecord)')
flags.DEFINE_string('runner_mode', 'local', 'Runner mode (local/cloud)')
flags.DEFINE_string('job_name', 'differ', 'Name of the differ job.')
flags.DEFINE_string('project_id', '', 'GCP project id for the dataflow job.')


class ImportDiffer:
    """
  Utility to generate a diff of two versions of a dataset for import analysis. 

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
  - svobs_diff_summary.csv: diff summary for observation analysis
  - svobs_diff_samples.csv: sample diff for observation analysis
  - svobs_diff_log.csv: diff log for observations
  - schema_diff_summary.csv: diff summary for schema analysis
  - schema_diff_log.csv: diff log for schema nodes 

  """

    def __init__(self,
                 current_data,
                 previous_data,
                 output_location,
                 project_id='',
                 job_name='differ',
                 file_format='mcf',
                 runner_mode='local'):
        self.current_data = current_data
        self.previous_data = previous_data
        self.output_path = output_location
        self.project_id = project_id
        self.job_name = job_name
        self.file_format = file_format
        self.runner_mode = runner_mode

    def _cleanup_data(self, df: pd.DataFrame):
        for column in [Diff.ADDED, Diff.DELETED, Diff.MODIFIED]:
            df[column.name] = df[
                column.name] if column.name in df.columns else 0
            df[column.name] = df[column.name].fillna(0).astype(int)

    def _get_samples(self, row):
        years = sorted(row[Column.observationDate.name])
        if len(years) > _SAMPLE_COUNT:
            return [years[0]] + random.sample(years[1:-1],
                                              _SAMPLE_COUNT - 2) + [years[-1]]
        else:
            return years

    # Processes two dataset files to identify changes.
    def generate_diff(self, previous_df: pd.DataFrame, current_df: pd.DataFrame,
                      isObs: bool) -> pd.DataFrame:
        """
        Process previous and current datasets to generate
        the diff data for identifying changes.
        Args:
          current_df: dataframe with current (new) data
          previous_df: dataframe with previous (old) data
        Returns:
          intermediate diff data for analysis
        """
        if isObs:
            column_set = _OBS_COLUMNS.split(',')
            column_set.remove(Column.value.name)
            groupby_columns = column_set
            value_columns = [Column.value.name]
        else:
            column_set = current_df.columns.tolist()
            groupby_columns = [Column.Node.name]
            column_set.remove(Column.Node.name)
            value_columns = list(column_set)

        if current_df.empty and not previous_df.empty:
            result = previous_df
            result[Column.diff_type.name] = Diff.DELETED.name
            return result
        elif previous_df.empty and not current_df.empty:
            result = current_df
            result[Column.diff_type.name] = Diff.ADDED.name
            return result
        elif previous_df.empty and current_df.empty:
            column_list = groupby_columns + value_columns + [
                Column.diff_type.name
            ]
            return pd.DataFrame(columns=column_list)

        for column in groupby_columns:
            if column not in current_df.columns.values.tolist():
                current_df[column] = ''
            if column not in previous_df.columns.values.tolist():
                previous_df[column] = ''
        df_p = previous_df.loc[:, groupby_columns + value_columns]
        df_c = current_df.loc[:, groupby_columns + value_columns]
        df_p = df_p.reindex(columns=groupby_columns + value_columns)
        df_c = df_c.reindex(columns=groupby_columns + value_columns)
        df_p['_value_combined'] = df_p[value_columns]\
          .apply(lambda row: '_'.join(row.values.astype(str)), axis=1)
        df_c['_value_combined'] = df_c[value_columns]\
          .apply(lambda row: '_'.join(row.values.astype(str)), axis=1)
        df_p.drop(columns=value_columns, inplace=True)
        df_c.drop(columns=value_columns, inplace=True)
        # Perform outer join operation to identify differences.
        result = pd.merge(df_p,
                          df_c,
                          on=groupby_columns,
                          how='outer',
                          indicator=Column.diff_type.name)
        result[Column.diff_type.name] = result.apply(
          lambda row: Diff.ADDED.name if row[Column.diff_type.name] == 'right_only' \
          else Diff.DELETED.name if row[Column.diff_type.name] == 'left_only' \
          else Diff.MODIFIED.name if row['_value_combined_x'] != row['_value_combined_y'] \
          else Diff.UNMODIFIED.name, axis=1)
        result = result[result[Column.diff_type.name] != Diff.UNMODIFIED.name]
        # result.sort_values(by=[Column.diff_type.name], inplace=True)
        result.reset_index(drop=True, inplace=True)
        if result.empty:
            column_list = groupby_columns + value_columns + [
                Column.diff_type.name
            ]
            return pd.DataFrame(columns=column_list)

        return result

    def split_data(self, mcf_nodes: list) -> (pd.DataFrame, pd.DataFrame):
        observations = [
            node for node in mcf_nodes
            if node.get('typeOf') == 'dcid:StatVarObservation'
        ]
        schema = [
            node for node in mcf_nodes
            if node.get('typeOf') != 'dcid:StatVarObservation'
        ]
        if observations:
            pd_obsevartions = pd.DataFrame(observations)
        else:
            logging.info("Empty observations dataframe")
            pd_obsevartions = pd.DataFrame(columns=_OBS_COLUMNS.split(','))

        if schema:
            pd_schema = pd.DataFrame(schema)
        else:
            logging.info("Empty schema dataframe")
            pd_schema = pd.DataFrame(columns=_NODE_COLUMNS.split(','))

        return pd_obsevartions, pd_schema

    def point_analysis(self,
                       diff: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
        """ 
        Performs point diff analysis to identify data point changes.

        Returns:
          summary and results from the analysis
        """
        if diff.empty:
            return pd.DataFrame(columns=[
                Column.variableMeasured.name, Diff.ADDED.name,
                Diff.DELETED.name, Diff.MODIFIED.name
            ]), pd.DataFrame(columns=[
                Column.variableMeasured.name, Column.diff_type.name,
                Column.observationAbout.name, Column.observationDate.name,
                Column.diff_size.name
            ])

        column_list = [
            Column.variableMeasured.name, Column.observationAbout.name,
            Column.observationDate.name, Column.diff_type.name
        ]
        in_df = diff.loc[:, column_list]
        samples = in_df.groupby(
            [Column.variableMeasured.name, Column.diff_type.name],
            observed=True,
            as_index=False)[[
                Column.observationAbout.name, Column.observationDate.name
            ]].agg(lambda x: x.tolist())
        samples[Column.diff_size.name] = samples.apply(
            lambda row: len(row[Column.observationAbout.name]), axis=1)
        samples[Column.observationAbout.name] = samples.apply(
            lambda row: random.sample(
                row[Column.observationAbout.name],
                min(_SAMPLE_COUNT, len(row[Column.observationAbout.name]))),
            axis=1)
        samples[Column.observationDate.name] = samples.apply(self._get_samples,
                                                             axis=1)
        summary = samples.pivot(
          index=Column.variableMeasured.name, columns=Column.diff_type.name, values=Column.diff_size.name)\
          .reset_index().rename_axis(None, axis=1)
        self._cleanup_data(summary)
        samples.sort_values(
            by=[Column.diff_type.name, Column.variableMeasured.name],
            inplace=True)
        return summary, samples

    def series_analysis(self,
                        diff: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
        """ 
        Performs series diff analysis to identify time series changes.

        Returns:
          summary and results from the analysis
        """
        if diff.empty:
            return pd.DataFrame(columns=[
                Column.variableMeasured.name, Column.observationAbout.name,
                Diff.ADDED.name, Diff.DELETED.name, Diff.MODIFIED.name
            ]), pd.DataFrame(columns=[
                Column.variableMeasured.name, Column.observationAbout.name,
                Column.diff_type.name, Column.observationDate.name,
                Column.diff_size.name
            ])

        column_list = [
            Column.variableMeasured.name, Column.observationAbout.name,
            Column.observationDate.name, Column.diff_type.name
        ]
        in_df = diff.loc[:, column_list]
        column_list = [
            Column.variableMeasured.name, Column.observationAbout.name,
            Column.diff_type.name
        ]
        samples = in_df.groupby(column_list,
                                as_index=False)[[Column.observationDate.name
                                                ]].agg(lambda x: x.tolist())
        samples[Column.diff_size.name] = samples.apply(
            lambda row: len(row[Column.observationDate.name]), axis=1)
        summary = samples.pivot(
          index=[Column.variableMeasured.name, Column.observationAbout.name],
          columns=Column.diff_type.name, values=Column.diff_size.name)\
          .reset_index().rename_axis(None, axis=1)
        samples[Column.observationDate.name] = samples.apply(self._get_samples,
                                                             axis=1)
        self._cleanup_data(summary)
        samples.sort_values(
            by=[Column.diff_type.name, Column.variableMeasured.name],
            inplace=True)
        return summary, samples

    def schema_analysis(self, diff: pd.DataFrame) -> pd.DataFrame:
        """ 
        Performs variable diff analysis to identify statvar changes.

        Returns:
          summary from the analysis
        """
        if diff.empty:
            return pd.DataFrame(columns=[
                Column.diff_type.name, Diff.ADDED.name, Diff.DELETED.name,
                Diff.MODIFIED.name
            ])

        result = diff[Column.diff_type.name].value_counts().reset_index()
        summary = result.set_index(
            Column.diff_type.name).transpose().rename_axis(
                None, axis=1).reset_index(drop=True)
        self._cleanup_data(summary)
        return summary

    def run_dataflow_job(self, project: str, job: str, current_data: str,
                         previous_data: str, file_format: str,
                         output_location: str) -> str:
        logging.info('Launching differ dataflow job {self.job_name}')
        parameters = {
            'currentData': current_data,
            'previousData': previous_data,
            'outputLocation': output_location,
        }
        if file_format == 'tfrecord':
            logging.info('Using tfrecord file format')
            parameters['useOptimizedGraphFormat'] = 'true'
        else:
            logging.info('Using mcf file format')

        template = 'gs://vishg-dataflow/templates/flex/differ.json'
        dataflow = build("dataflow", "v1b3")
        request = (dataflow.projects().locations().flexTemplates().launch(
            projectId=project,
            location='us-central1',
            body={
                "launchParameter": {
                    "jobName": job,
                    "containerSpecGcsPath": template,
                    "parameters": parameters,
                },
            },
        ))
        response = request.execute()
        job_id = response['job']['id']
        url = f'https://pantheon.corp.google.com/dataflow/jobs/{job_id}?project={project}'
        logging.info('Dataflow job url: %s', url)
        status = 'JOB_STATE_UNKNONW'
        dataflow = build("dataflow", "v1b3")
        request = (dataflow.projects().jobs().list(projectId=project,
                                                   name=job_id))
        while (status != 'JOB_STATE_DONE' and status != 'JOB_STATE_FAILED'):
            logging.info(
                f'Waiting for job {self.job_name} to complete. Status:{status}')
            time.sleep(60)
            response = request.execute()
            status = response['jobs'][0]['currentState']

        logging.info(
            f'Finished differ dataflow job {self.job_name} with status {status}.'
        )
        return status

    def run_differ(self):
        os.makedirs(self.output_path, exist_ok=True)
        tmp_path = os.path.join(self.output_path, self.job_name)
        os.makedirs(tmp_path, exist_ok=True)

        logging.info('Processing input data to generate diff...')
        if self.runner_mode == 'cloud':
            # Runs dataflow job in GCP.
            logging.info("Invoking dataflow mode for differ")
            status = self.run_dataflow_job(self.project_id, self.job_name,
                                           self.current_data,
                                           self.previous_data, self.file_format,
                                           self.output_path)
            if status == 'JOB_STATE_FAILED':
                raise ExectionError(f'Dataflow job {job_name} failed.')
            diff_path = os.path.join(self.output_path, 'obs-diff*')
            logging.info("Loading obs diff data from: %s", diff_path)
            obs_diff = differ_utils.load_csv_data(diff_path, tmp_path)
            diff_path = os.path.join(self.output_path, 'schema-diff*')
            logging.info("Loading schema diff data from: %s", diff_path)
            schema_diff = differ_utils.load_csv_data(diff_path, tmp_path)
        else:
            # Runs local Python differ.
            current_dir = os.path.join(tmp_path, 'current')
            previous_dir = os.path.join(tmp_path, 'previous')
            logging.info(f'Loading current data from {self.current_data}')
            mcf_nodes = differ_utils.load_data(self.current_data, current_dir)
            current_df_obs, current_df_schema = self.split_data(mcf_nodes)
            logging.info(
                f'Loaded current data with {current_df_obs.shape[0]} observations and {current_df_schema.shape[0]} nodes.'
            )
            logging.info(f'Loading previous data from {self.previous_data}')
            mcf_nodes = differ_utils.load_data(self.previous_data, previous_dir)
            previous_df_obs, previous_df_schema = self.split_data(mcf_nodes)
            logging.info(
                f'Loaded previous data with {previous_df_obs.shape[0]} observations and {previous_df_schema.shape[0]} nodes.'
            )
            logging.info('Generating observation diff...')
            obs_diff = self.generate_diff(previous_df_obs, current_df_obs, True)
            logging.info('Generating schema diff...')
            schema_diff = self.generate_diff(previous_df_schema,
                                             current_df_schema, False)
            differ_utils.write_csv_data(obs_diff, self.output_path,
                                        'svobs_diff_log.csv', tmp_path)
            differ_utils.write_csv_data(schema_diff, self.output_path,
                                        'schema_diff_log.csv', tmp_path)

        logging.info(f'Generated observation diff of size {obs_diff.shape[0]}')
        logging.info(f'Generated schema diff of size {schema_diff.shape[0]}')

        logging.info(f'Performing schema diff analysis')
        schema_diff_summary = self.schema_analysis(schema_diff)
        logging.info(f'Schema diff summary size {schema_diff_summary.shape[0]}')

        logging.info('Performing obs diff...')
        obs_diff_summary, obs_diff_samples = self.point_analysis(obs_diff)
        logging.info(f'Obs point diff summary size {obs_diff_summary.shape[0]}')

        logging.info(f'Writing differ output to {self.output_path}')
        differ_utils.write_csv_data(schema_diff_summary, self.output_path,
                                    'schema_diff_summary.csv', tmp_path)
        # TODO: remove this file once validation script is updated.
        differ_utils.write_csv_data(obs_diff_summary, self.output_path,
                                    'point_analysis_summary.csv', tmp_path)
        differ_utils.write_csv_data(obs_diff_summary, self.output_path,
                                    'svobs_diff_summary.csv', tmp_path)
        differ_utils.write_csv_data(obs_diff_samples, self.output_path,
                                    'svobs_diff_samples.csv', tmp_path)
        logging.info(f'Differ output written to {self.output_path}')


def main(_):
    '''Runs the differ.'''
    differ = ImportDiffer(_FLAGS.current_data, _FLAGS.previous_data,
                          _FLAGS.output_location, _FLAGS.project_id,
                          _FLAGS.job_name, _FLAGS.file_format,
                          _FLAGS.runner_mode)
    differ.run_differ()


if __name__ == '__main__':
    app.run(main)
