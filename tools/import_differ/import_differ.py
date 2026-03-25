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

_DATAFLOW_TEMPLATE_URL = 'gs://datcom-templates/templates/flex/differ.json'

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
    ('dcid', 5),
    ('diff_type', 6),
    ('diff_size', 7),
    ('observationAbout', 8),
    ('key_combined', 9),
    ('value_combined', 10),
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
  - obs_diff_summary.csv: diff summary for observation analysis
  - obs_diff_samples.csv: sample diff for observation analysis
  - obs_diff_log.csv: diff log for observations
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
            df[column.name] = df.get(column.name, 0)
            df[column.name] = df[column.name].fillna(0).astype(int)

    def _get_samples(self, row):
        years = sorted(row[Column.observationDate.name])
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
        the diff data for identifying changes.
        Args:
          current_df: dataframe with current (new) data
          previous_df: dataframe with previous (old) data
        Returns:
          intermediate diff data for analysis
        """
        if current_df.empty and not previous_df.empty:
            result = previous_df.copy()
            result[Column.diff_type.name] = Diff.DELETED.name
            return result
        elif previous_df.empty and not current_df.empty:
            result = current_df.copy()
            result[Column.diff_type.name] = Diff.ADDED.name
            return result
        elif previous_df.empty and current_df.empty:
            column_list = [
                Column.key_combined.name, Column.value_combined.name + '_x',
                Column.value_combined.name + '_y' + Column.diff_type.name
            ]
            return pd.DataFrame(columns=column_list)
        result = pd.merge(previous_df,
                          current_df,
                          on=Column.key_combined.name,
                          how='outer',
                          indicator=Column.diff_type.name)
        result[Column.diff_type.name] = result.apply(
          lambda row: Diff.ADDED.name if row[Column.diff_type.name] == 'right_only' \
          else Diff.DELETED.name if row[Column.diff_type.name] == 'left_only' \
          else Diff.MODIFIED.name if row[Column.value_combined.name + '_x'] != row[Column.value_combined.name + '_y'] \
          else Diff.UNMODIFIED.name, axis=1)
        result.drop(
            result[result[Column.diff_type.name] == Diff.UNMODIFIED.name].index,
            inplace=True)
        # result.sort_values(by=[Column.diff_type.name], inplace=True)
        result.reset_index(drop=True, inplace=True)
        if result.empty:
            column_list = [
                Column.key_combined.name, Column.value_combined.name + '_x',
                Column.value_combined.name + '_y' + Column.diff_type.name
            ]
            return pd.DataFrame(columns=column_list)

        return result

    def split_data(self, mcf_nodes: list) -> (pd.DataFrame, pd.DataFrame):
        """ 
        Split mcf nodes into observation and schema nodes based on typeOf property.

        Returns:
          Dataframes containing observation and schema nodes 
        """
        obs_list = []
        schema_list = []
        for node in mcf_nodes:
            if 'StatVarObservation' in node.get(Column.typeOf.name):
                values_to_combine = []
                keys_to_combine = []
                groupby_keys = [
                    'variableMeasured', 'observationAbout', 'observationDate',
                    'observationPeriod', 'measurementMethod', 'unit',
                    'scalingFactor'
                ]
                value_keys = [Column.value.name]
                for key in groupby_keys:
                    keys_to_combine.append(str(node.get(key, "")))
                for key in value_keys:
                    values_to_combine.append(str(node.get(key, "")))

                key_combined = ";".join(keys_to_combine)
                value_combined = ";".join(values_to_combine)

                obs_list.append({
                    Column.key_combined.name: key_combined,
                    Column.value_combined.name: value_combined
                })
            else:
                node_id_key = str(node.get('Node', ""))
                node_id_key = str(node.get(Column.dcid.name, node_id_key))
                if not node_id_key:
                    logging.error(f'Skipping node as dcid is missing {node}.')
                    continue
                values_to_combine = []
                keys_to_combine = [node_id_key]
                node.pop(Column.dcid.name)
                node.pop('Node', None)
                value_keys = sorted(node.keys())
                for key in value_keys:
                    values_to_combine.append(key + ":" + str(node.get(key, "")))
                key_combined = ";".join(keys_to_combine)
                value_combined = ";".join(values_to_combine)
                schema_list.append({
                    Column.key_combined.name: key_combined,
                    Column.value_combined.name: value_combined
                })

        schema_df = pd.DataFrame(schema_list)
        schema_df.drop_duplicates(inplace=True)
        obs_df = pd.DataFrame(obs_list)
        return obs_df, schema_df

    def observation_diff_analysis(
            self, diff: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
        """ 
        Performs observation diff analysis to identify data point changes.

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

        split_df = diff[Column.key_combined.name].str.split(';', expand=True)
        diff[Column.variableMeasured.name] = split_df[0]
        diff[Column.observationAbout.name] = split_df[1]
        diff[Column.observationDate.name] = split_df[2]

        samples = diff.groupby(
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

    def schema_diff_analysis(self, diff: pd.DataFrame) -> pd.DataFrame:
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

        template = _DATAFLOW_TEMPLATE_URL
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
        status = 'JOB_STATE_UNKNOWN'
        dataflow = build("dataflow", "v1b3")
        request = (dataflow.projects().locations().jobs().list(
            projectId=project, location='us-central1', name=job_id))
        while (status != 'JOB_STATE_DONE' and status != 'JOB_STATE_FAILED' and
               status != 'JOB_STATE_CANCELLED'):
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
            obs_diff = self.generate_diff(previous_df_obs, current_df_obs)
            logging.info('Generating schema diff...')
            schema_diff = self.generate_diff(previous_df_schema,
                                             current_df_schema)
            differ_utils.write_csv_data(obs_diff, self.output_path,
                                        'obs_diff_log.csv', tmp_path)
            differ_utils.write_csv_data(schema_diff, self.output_path,
                                        'schema_diff_log.csv', tmp_path)
            differ_summary = {
                'current_version': self.current_data,
                'previous_version': self.previous_data,
                'current_obs_size': current_df_obs.shape[0],
                'previous_obs_size': previous_df_obs.shape[0],
                'current_schema_size': current_df_schema.shape[0],
                'previous_schema_size': previous_df_schema.shape[0],
                'obs_diff_size': obs_diff.shape[0],
                'schema_diff_size': schema_diff.shape[0]
            }
            differ_utils.write_json_data(differ_summary, self.output_path,
                                         'differ_summary.json', tmp_path)

        logging.info(f'Generated observation diff of size {obs_diff.shape[0]}')
        logging.info(f'Generated schema diff of size {schema_diff.shape[0]}')
        logging.info(f'Differ summary: {differ_summary}')

        logging.info(f'Performing schema diff analysis')
        schema_diff_summary = self.schema_diff_analysis(schema_diff)
        logging.info('Performing observation diff analysis...')
        obs_diff_summary, obs_diff_samples = self.observation_diff_analysis(
            obs_diff)

        logging.info(f'Writing differ output to {self.output_path}')
        differ_utils.write_csv_data(schema_diff_summary, self.output_path,
                                    'schema_diff_summary.csv', tmp_path)
        differ_utils.write_csv_data(obs_diff_summary, self.output_path,
                                    'obs_diff_summary.csv', tmp_path)
        differ_utils.write_csv_data(obs_diff_samples, self.output_path,
                                    'obs_diff_samples.csv', tmp_path)
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
