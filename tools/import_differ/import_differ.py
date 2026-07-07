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

import csv
import glob
import json
import os
import pandas as pd
import random
import subprocess
import sys
import time
from collections import defaultdict
from enum import Enum

from absl import app
from absl import flags
from absl import logging
from googleapiclient.discovery import build

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

import differ_utils

_DATAFLOW_TEMPLATE_URL = 'gs://datcom-templates/templates/flex/differ.json'

_GROUPBY_KEYS = [
    'variableMeasured', 'observationAbout', 'observationDate',
    'observationPeriod', 'measurementMethod', 'unit', 'scalingFactor'
]

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
    ('key_combined', 7),
    ('value_combined', 8),
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
flags.DEFINE_string('runner_mode', 'native',
                    'Runner mode (native/direct/cloud)')
flags.DEFINE_string('job_name', 'differ', 'Name of the differ job.')
flags.DEFINE_string('project_id', '', 'GCP project id for the dataflow job.')


def val_str(value) -> str:
    if isinstance(value, list):
        return ",".join([val_str(v) for v in value])
    if value and isinstance(value, str) and " " in value and value[0].isalpha():
        return '"' + value + '"'
    return str(value)


class ImportDiffer:
    """
  Utility to generate a diff of two versions of a dataset for import analysis. 

  Usage:
  $ python import_differ.py --current_data=<path> --previous_data=<path> --output_location=<path> \
    --file_format=<mcf/tfrecord> --runner_mode=<native/direct/cloud> --project_id=<id> --job_name=<name> 

  Runner Modes:
  - native: Runs the differ using native Python (Pandas) locally.
  - direct: Runs the differ using the Apache Beam DirectRunner (Java jar) locally.
  - cloud: Runs the differ as a Dataflow job in GCP.

  Summary output generated is of the form below showing 
  counts of differences for each variable.  

  variableMeasured   ADDED  DELETED  MODIFIED
  0   dcid:var1       1      0       0
  1   dcid:var2       0      2       1
  2   dcid:var3       0      0       1
  3   dcid:var4       0      2       0

  Detailed diff output is written to files for further analysis.
  - nodes-added.mcf: MCF nodes added in the current version
  - nodes-deleted.mcf: MCF nodes deleted in the current version
  - nodes-modified.mcf: MCF nodes modified in the current version
  - differ_summary.json: consolidated diff statistics 

  """

    def __init__(self,
                 current_data,
                 previous_data,
                 output_location,
                 project_id='',
                 job_name='differ',
                 file_format='mcf',
                 runner_mode='native'):
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
                Column.value_combined.name + '_y', Column.diff_type.name
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
                Column.value_combined.name + '_y', Column.diff_type.name
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
                value_keys = [Column.value.name]
                for key in _GROUPBY_KEYS:
                    keys_to_combine.append(str(node.get(key, "")))
                for key in value_keys:
                    values_to_combine.append(str(node.get(key, "")))

                key_combined = ";".join(keys_to_combine)
                value_combined = ";".join(values_to_combine)

                obs_list.append({
                    Column.key_combined.name: key_combined,
                    Column.value_combined.name: value_combined,
                    'Node': node.get('Node', ''),
                    'dcid': node.get('dcid', '')
                })
            else:
                node_id_key = str(node.get('Node', ""))
                node_id_key = str(node.get(Column.dcid.name, node_id_key))
                if not node_id_key:
                    logging.error(f'Skipping node as dcid is missing {node}.')
                    continue
                values_to_combine = []
                keys_to_combine = [node_id_key]
                node.pop(Column.dcid.name, None)
                node.pop('Node', None)
                value_keys = sorted(node.keys())
                for key in value_keys:
                    values_to_combine.append(key + ":" +
                                             val_str(node.get(key, "")))
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

    def convert_diff_to_mcf_nodes(self,
                                  diff_df: pd.DataFrame,
                                  is_obs: bool,
                                  diff_type: str = None) -> list:
        """
        Converts the diff dataframe back to MCF format nodes.
        """
        all_nodes = []
        diff_types = [diff_type] if diff_type else [
            Diff.ADDED.name, Diff.DELETED.name, Diff.MODIFIED.name
        ]
        for d_type in diff_types:
            df_type = diff_df[diff_df[Column.diff_type.name] == d_type]
            if df_type.empty:
                continue

            for _, row in df_type.iterrows():
                node = {}
                key_combined = str(row[Column.key_combined.name])

                # Determine which column to use for values and node IDs
                suffix = '_x' if d_type == Diff.DELETED.name else '_y'

                # Helper to get value from row, handles cases with or without suffix
                def get_val(base_name):
                    col_name = base_name + suffix
                    if col_name in row:
                        return str(row[col_name])
                    return str(row.get(base_name, ''))

                value_combined = get_val(Column.value_combined.name)

                if is_obs:
                    node_id = get_val('Node')
                    dcid_id = get_val('dcid')
                    if node_id and node_id != 'nan':
                        node['Node'] = node_id
                    if dcid_id and dcid_id != 'nan':
                        node['dcid'] = dcid_id

                    # Reconstruct observation node
                    keys = key_combined.split(';')
                    for i, key in enumerate(_GROUPBY_KEYS):
                        if i < len(keys) and keys[i] and keys[i] != "nan":
                            node[key] = keys[i]

                    values = value_combined.split(';')
                    if values and values[0] and values[0] != "nan":
                        node['value'] = values[0]

                    node['typeOf'] = 'StatVarObservation'
                else:
                    # Reconstruct schema node
                    # key_combined is node_id_key
                    if key_combined.startswith('dcid:'):
                        node['dcid'] = key_combined[len('dcid:'):]
                    else:
                        node['Node'] = key_combined

                    for kv in value_combined.split(';'):
                        if ':' in kv:
                            k, v = kv.split(':', 1)
                            node[k] = v

                all_nodes.append(node)
        return all_nodes

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

    def run_direct_job(self, current_data: str, previous_data: str,
                       file_format: str, output_location: str) -> str:
        logging.info(f'Launching differ direct job {self.job_name}')
        jar_path = os.path.join(_SCRIPT_DIR, 'differ-bundled-0.1-SNAPSHOT.jar')
        if not os.path.exists(jar_path):
            logging.error(f'Dataflow jar not found: {jar_path}')
            return 'JOB_STATE_FAILED'

        cmd = [
            'java', '-jar', jar_path, f'--currentData={current_data}',
            f'--previousData={previous_data}',
            f'--outputLocation={output_location}', '--runner=DirectRunner'
        ]
        if file_format == 'tfrecord':
            logging.info('Using tfrecord file format')
            cmd.append('--useOptimizedGraphFormat=true')
        else:
            logging.info('Using mcf file format')

        logging.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(
                f"Direct job failed with return code {result.returncode}")
            logging.error(f"Stdout: {result.stdout}")
            logging.error(f"Stderr: {result.stderr}")
            return 'JOB_STATE_FAILED'

        logging.info(f'Finished differ direct job {self.job_name}.')
        return 'JOB_STATE_DONE'

    def run_differ(self):
        os.makedirs(self.output_path, exist_ok=True)
        tmp_path = os.path.join(self.output_path, self.job_name)
        os.makedirs(tmp_path, exist_ok=True)

        logging.info('Processing input data to generate diff...')
        differ_summary = {}
        if self.runner_mode == 'cloud':
            # Runs dataflow job in GCP.
            logging.info("Invoking dataflow mode for differ")
            status = self.run_dataflow_job(self.project_id, self.job_name,
                                           self.current_data,
                                           self.previous_data, self.file_format,
                                           self.output_path)
            if status == 'JOB_STATE_FAILED':
                raise RuntimeError(f'Dataflow job {self.job_name} failed.')
        elif self.runner_mode == 'direct':
            # Runs dataflow jar directly.
            logging.info("Invoking direct mode for differ")
            status = self.run_direct_job(self.current_data, self.previous_data,
                                         self.file_format, self.output_path)
            if status == 'JOB_STATE_FAILED':
                raise RuntimeError(f'Direct job {self.job_name} failed.')

            return
        else:
            # Runs native Python differ.
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

            logging.info('Writing diff to MCF files...')
            for d_type, filename in [
                (Diff.ADDED.name, 'nodes-added.mcf'),
                (Diff.DELETED.name, 'nodes-deleted.mcf'),
                (Diff.MODIFIED.name, 'nodes-modified.mcf'),
            ]:
                obs_nodes = self.convert_diff_to_mcf_nodes(
                    obs_diff, True, d_type)
                schema_nodes = self.convert_diff_to_mcf_nodes(
                    schema_diff, False, d_type)
                type_nodes = obs_nodes + schema_nodes
                if type_nodes:
                    differ_utils.write_mcf_nodes(type_nodes, self.output_path,
                                                 filename, tmp_path)

            obs_stats = obs_diff[Column.diff_type.name].value_counts().to_dict()
            schema_stats = schema_diff[
                Column.diff_type.name].value_counts().to_dict()

            differ_summary = {
                'current_version':
                    self.current_data,
                'previous_version':
                    self.previous_data,
                'current_obs_count':
                    int(current_df_obs.shape[0]),
                'previous_obs_count':
                    int(previous_df_obs.shape[0]),
                'current_schema_count':
                    int(current_df_schema.shape[0]),
                'previous_schema_count':
                    int(previous_df_schema.shape[0]),
                'added_obs_count':
                    int(obs_stats.get(Diff.ADDED.name, 0)),
                'deleted_obs_count':
                    int(obs_stats.get(Diff.DELETED.name, 0)),
                'modified_obs_count':
                    int(obs_stats.get(Diff.MODIFIED.name, 0)),
                'added_schema_count':
                    int(schema_stats.get(Diff.ADDED.name, 0)),
                'deleted_schema_count':
                    int(schema_stats.get(Diff.DELETED.name, 0)),
                'modified_schema_count':
                    int(schema_stats.get(Diff.MODIFIED.name, 0)),
                'obs_diff_count':
                    int(obs_diff.shape[0]),
                'schema_diff_count':
                    int(schema_diff.shape[0])
            }
            logging.info(
                f'Generated observation diff of size {obs_diff.shape[0]}')
            logging.info(
                f'Generated schema diff of size {schema_diff.shape[0]}')
            differ_utils.write_json_data(differ_summary, self.output_path,
                                         'differ_summary.json', tmp_path)
        logging.info(f'Differ summary: {differ_summary}')
        logging.info(f'Differ output written to {self.output_path}')
        return differ_summary


def main(_):
    '''Runs the differ.'''
    differ = ImportDiffer(_FLAGS.current_data, _FLAGS.previous_data,
                          _FLAGS.output_location, _FLAGS.project_id,
                          _FLAGS.job_name, _FLAGS.file_format,
                          _FLAGS.runner_mode)
    differ.run_differ()


if __name__ == '__main__':
    app.run(main)
