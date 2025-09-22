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
import random
import sys
import time
from enum import Enum

import numpy as np
import pandas as pd
from absl import app
from absl import flags
from absl import logging
from googleapiclient.discovery import build

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

from differ_utils import StorageClient

_SAMPLE_COUNT = 3

_DATAFLOW_TEMPLATE_URL = 'gs://datcom-templates/templates/flex/differ.json'


class Diff(str, Enum):
  ADDED = 'ADDED'
  DELETED = 'DELETED'
  MODIFIED = 'MODIFIED'
  UNMODIFIED = 'UNMODIFIED'


class Column(str, Enum):
  VARIABLE_MEASURED = 'variableMeasured'
  OBSERVATION_DATE = 'observationDate'
  VALUE = 'value'
  TYPE_OF = 'typeOf'
  DCID = 'dcid'
  DIFF_TYPE = 'diff_type'
  DIFF_SIZE = 'diff_size'
  OBSERVATION_ABOUT = 'observationAbout'
  KEY_COMBINED = 'key_combined'
  VALUE_COMBINED = 'value_combined'
  OBSERVATION_PERIOD = 'observationPeriod'
  MEASUREMENT_METHOD = 'measurementMethod'
  UNIT = 'unit'
  SCALING_FACTOR = 'scalingFactor'
  NODE = 'Node'


_OBS_KEY_COLUMNS = [
    Column.VARIABLE_MEASURED,
    Column.OBSERVATION_ABOUT,
    Column.OBSERVATION_DATE,
    Column.OBSERVATION_PERIOD,
    Column.MEASUREMENT_METHOD,
    Column.UNIT,
    Column.SCALING_FACTOR,
]
_OBS_VALUE_COLUMN = Column.VALUE

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'current_data',
    '',
    'Path to the current data (wildcard on local/GCS supported).',
)
flags.DEFINE_string(
    'previous_data',
    '',
    'Path to the previous data (wildcard on local/GCS supported).',
)
flags.DEFINE_string(
    'output_location', 'results', 'Path (local/GCS) to the output data folder.'
)
flags.DEFINE_string(
    'file_format', 'mcf', 'Format of the input data (mcf,tfrecord)'
)
flags.DEFINE_string('runner_mode', 'local', 'Runner mode (local/cloud)')
flags.DEFINE_string('job_name', 'differ', 'Name of the differ job.')
flags.DEFINE_string('project_id', '', 'GCP project id for the dataflow job.')


class DataflowRunner:
  """Handles the execution and monitoring of a Dataflow job."""

  def __init__(self, project_id: str):
    self.project_id = project_id

  def run(
      self,
      job_name: str,
      current_data: str,
      previous_data: str,
      file_format: str,
      output_location: str,
  ) -> str:
    logging.info('Launching differ dataflow job %s', job_name)
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
    dataflow = build('dataflow', 'v1b3')
    request = (
        dataflow.projects()
        .locations()
        .flexTemplates()
        .launch(
            projectId=self.project_id,
            location='us-central1',
            body={
                'launchParameter': {
                    'jobName': job_name,
                    'containerSpecGcsPath': template,
                    'parameters': parameters,
                },
            },
        )
    )
    response = request.execute()
    job_id = response['job']['id']
    url = f'https://pantheon.corp.google.com/dataflow/jobs/{job_id}?project={self.project_id}'
    logging.info('Dataflow job url: %s', url)
    status = 'JOB_STATE_UNKNOWN'
    dataflow = build('dataflow', 'v1b3')
    request = (
        dataflow.projects()
        .locations()
        .jobs()
        .list(projectId=self.project_id, location='us-central1', name=job_id)
    )
    while (
        status != 'JOB_STATE_DONE'
        and status != 'JOB_STATE_FAILED'
        and status != 'JOB_STATE_CANCELLED'
    ):
      logging.info('Waiting for job %s to complete. Status: %s', job_name, status)
      time.sleep(60)
      response = request.execute()
      status = response['jobs'][0]['currentState']

    logging.info(
        'Finished differ dataflow job %s with status %s.', job_name, status
    )
    return status


class DiffAnalyzer:
  """Analyzes diff DataFrames to produce summaries and samples."""

  def _cleanup_data(self, df: pd.DataFrame):
    for column in [Diff.ADDED, Diff.DELETED, Diff.MODIFIED]:
      df[column.value] = df.get(column.value, 0)
      df[column.value] = df[column.value].fillna(0).astype(int)

  def _get_samples(self, row):
    years = sorted(row[Column.OBSERVATION_DATE])
    if len(years) > _SAMPLE_COUNT:
      return (
          [years[0]]
          + random.sample(years[1:-1], _SAMPLE_COUNT - 2)
          + [years[-1]]
      )
    else:
      return years

  def analyze_observation_diff(
      self, diff: pd.DataFrame
  ) -> (pd.DataFrame, pd.DataFrame):
    """
    Performs observation diff analysis to identify data point changes.

    Returns:
      A tuple containing the summary and samples DataFrames.
    """
    if diff.empty:
      return pd.DataFrame(
          columns=[
              Column.VARIABLE_MEASURED,
              Diff.ADDED.value,
              Diff.DELETED.value,
              Diff.MODIFIED.value,
          ]
      ), pd.DataFrame(
          columns=[
              Column.VARIABLE_MEASURED,
              Column.DIFF_TYPE,
              Column.OBSERVATION_ABOUT,
              Column.OBSERVATION_DATE,
              Column.DIFF_SIZE,
          ]
      )

    samples = diff.groupby(
        [Column.VARIABLE_MEASURED, Column.DIFF_TYPE],
        observed=True,
        as_index=False,
    )[[Column.OBSERVATION_ABOUT, Column.OBSERVATION_DATE]].agg(list)
    samples[Column.DIFF_SIZE] = samples[Column.OBSERVATION_ABOUT].str.len()
    samples[Column.OBSERVATION_ABOUT] = samples[
        Column.OBSERVATION_ABOUT
    ].apply(lambda x: random.sample(x, min(_SAMPLE_COUNT, len(x))))
    samples[Column.OBSERVATION_DATE] = samples.apply(self._get_samples, axis=1)
    summary = (
        samples.pivot(
            index=Column.VARIABLE_MEASURED,
            columns=Column.DIFF_TYPE,
            values=Column.DIFF_SIZE,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    self._cleanup_data(summary)
    samples.sort_values(
        by=[Column.DIFF_TYPE, Column.VARIABLE_MEASURED], inplace=True
    )
    return summary, samples

  def analyze_schema_diff(self, diff: pd.DataFrame) -> pd.DataFrame:
    """
    Performs variable diff analysis to identify statvar changes.

    Returns:
      A summary DataFrame from the analysis.
    """
    if diff.empty:
      return pd.DataFrame(
          columns=[
              Column.DIFF_TYPE,
              Diff.ADDED.value,
              Diff.DELETED.value,
              Diff.MODIFIED.value,
          ]
      )

    result = diff[Column.DIFF_TYPE].value_counts().reset_index()
    summary = (
        result.set_index(Column.DIFF_TYPE)
        .transpose()
        .rename_axis(None, axis=1)
        .reset_index(drop=True)
    )
    self._cleanup_data(summary)
    return summary


class ImportDiffer:
  """
  Utility to generate a diff of two versions of a dataset for import analysis.
  """

  def __init__(
      self,
      current_data,
      previous_data,
      output_location,
      project_id='',
      job_name='differ',
      file_format='mcf',
      runner_mode='local',
  ):
    self.current_data = current_data
    self.previous_data = previous_data
    self.output_path = output_location
    self.project_id = project_id
    self.job_name = job_name
    self.file_format = file_format
    self.runner_mode = runner_mode
    self.analyzer = DiffAnalyzer()

  def _process_observation_node(self, node: dict) -> dict:
    obs_node = {}
    for key in _OBS_KEY_COLUMNS:
      obs_node[key] = node.get(key)
    obs_node[_OBS_VALUE_COLUMN] = node.get(_OBS_VALUE_COLUMN)
    return obs_node

  def _process_schema_node(self, node: dict) -> dict:
    node_id_key = str(node.get(Column.NODE, ''))
    node_id_key = str(node.get(Column.DCID, node_id_key))
    if not node_id_key:
      logging.error('Skipping node as dcid is missing %s.', node)
      return None
    values_to_combine = []
    keys_to_combine = [node_id_key]
    node.pop(Column.DCID, None)
    node.pop(Column.NODE, None)
    value_keys = sorted(node.keys())
    for key in value_keys:
      values_to_combine.append(f'{key}:{node.get(key, "")}')
    key_combined = ';'.join(keys_to_combine)
    value_combined = ';'.join(values_to_combine)
    return {
        Column.KEY_COMBINED: key_combined,
        Column.VALUE_COMBINED: value_combined,
    }

  def generate_diff(
      self,
      previous_df: pd.DataFrame,
      current_df: pd.DataFrame,
      key_columns: list[str],
      value_column: str = None,
  ) -> pd.DataFrame:
    """
    Process previous and current datasets to generate
    the diff data for identifying changes.
    Args:
      current_df: dataframe with current (new) data
      previous_df: dataframe with previous (old) data
      key_columns: list of columns that uniquely identify a row
      value_column: column whose value is being compared
    Returns:
      intermediate diff data for analysis
    """
    if value_column is None:
      value_column = Column.VALUE_COMBINED

    if current_df.empty and not previous_df.empty:
      result = previous_df.copy()
      result[Column.DIFF_TYPE] = Diff.DELETED
      return result
    elif previous_df.empty and not current_df.empty:
      result = current_df.copy()
      result[Column.DIFF_TYPE] = Diff.ADDED
      return result
    elif previous_df.empty and current_df.empty:
      return pd.DataFrame()

    result = pd.merge(
        previous_df,
        current_df,
        on=key_columns,
        how='outer',
        indicator=Column.DIFF_TYPE,
    )

    value_x = f'{value_column}_x'
    value_y = f'{value_column}_y'

    conditions = [
        result[Column.DIFF_TYPE] == 'right_only',
        result[Column.DIFF_TYPE] == 'left_only',
        result[value_x] != result[value_y],
    ]
    choices = [Diff.ADDED, Diff.DELETED, Diff.MODIFIED]
    result[Column.DIFF_TYPE] = np.select(
        conditions, choices, default=Diff.UNMODIFIED
    )

    return result[result[Column.DIFF_TYPE] != Diff.UNMODIFIED].reset_index(
        drop=True
    )

  def split_data(
      self, mcf_nodes: list[dict]
  ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split mcf nodes into observation and schema nodes based on typeOf property.

    Returns:
      Dataframes containing observation and schema nodes
    """
    obs_list = []
    schema_list = []
    for node in mcf_nodes:
      if 'StatVarObservation' in node.get(Column.TYPE_OF, ''):
        obs_list.append(self._process_observation_node(node))
      else:
        schema_node = self._process_schema_node(node)
        if schema_node:
          schema_list.append(schema_node)

    obs_df = pd.DataFrame(obs_list).fillna('')
    obs_df.drop_duplicates(subset=_OBS_KEY_COLUMNS, inplace=True)
    schema_df = pd.DataFrame(schema_list)
    schema_df.drop_duplicates(inplace=True)
    return obs_df, schema_df

  def _load_and_split_data(
      self, client: StorageClient
  ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Loads data from a client and splits it into observation and schema DataFrames."""
    logging.info('Loading data from %s', client._strategy._path)
    mcf_nodes = client.load_mcf_nodes()
    df_obs, df_schema = self.split_data(mcf_nodes)
    logging.info(
        'Loaded data with %s observations and %s nodes.',
        df_obs.shape[0],
        df_schema.shape[0],
    )
    return df_obs, df_schema

  def _run_local_differ(
      self, tmp_path: str, output_client: StorageClient
  ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Runs the differ process locally."""
    current_client = StorageClient(
        self.current_data, tmp_dir=os.path.join(tmp_path, 'current')
    )
    previous_client = StorageClient(
        self.previous_data, tmp_dir=os.path.join(tmp_path, 'previous')
    )

    current_df_obs, current_df_schema = self._load_and_split_data(current_client)
    previous_df_obs, previous_df_schema = self._load_and_split_data(
        previous_client
    )

    logging.info('Generating observation diff...')
    obs_diff = self.generate_diff(
        previous_df_obs,
        current_df_obs,
        key_columns=_OBS_KEY_COLUMNS,
        value_column=_OBS_VALUE_COLUMN,
    )
    logging.info('Generating schema diff...')
    schema_diff = self.generate_diff(
        previous_df_schema,
        current_df_schema,
        key_columns=[Column.KEY_COMBINED],
    )
    output_client.write_csv(obs_diff, 'obs_diff_log.csv')
    output_client.write_csv(schema_diff, 'schema_diff_log.csv')
    return obs_diff, schema_diff

  def _run_cloud_differ(
      self, tmp_path: str, output_client: StorageClient
  ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Runs the differ process on Dataflow."""
    logging.info('Invoking dataflow mode for differ')
    runner = DataflowRunner(self.project_id)
    status = runner.run(
        self.job_name,
        self.current_data,
        self.previous_data,
        self.file_format,
        self.output_path,
    )
    if status == 'JOB_STATE_FAILED':
      raise RuntimeError(f'Dataflow job {self.job_name} failed.')

    logging.info('Loading obs diff data from: %s', self.output_path)
    obs_diff = output_client.load_csv('obs-diff*')
    logging.info('Loading schema diff data from: %s', self.output_path)
    schema_diff = output_client.load_csv('schema-diff*')
    return obs_diff, schema_diff

  def _analyze_and_write_results(
      self,
      obs_diff: pd.DataFrame,
      schema_diff: pd.DataFrame,
      output_client: StorageClient,
  ) -> None:
    """Analyzes the diff DataFrames and writes the results to CSV files."""
    logging.info('Generated observation diff of size %s', obs_diff.shape[0])
    logging.info('Generated schema diff of size %s', schema_diff.shape[0])

    logging.info('Performing schema diff analysis')
    schema_diff_summary = self.analyzer.analyze_schema_diff(schema_diff)
    logging.info('Performing observation diff analysis...')
    (
        obs_diff_summary,
        obs_diff_samples,
    ) = self.analyzer.analyze_observation_diff(obs_diff)

    logging.info('Writing differ output to %s', self.output_path)
    output_client.write_csv(schema_diff_summary, 'schema_diff_summary.csv')
    output_client.write_csv(obs_diff_summary, 'obs_diff_summary.csv')
    output_client.write_csv(obs_diff_samples, 'obs_diff_samples.csv')
    logging.info('Differ output written to %s', self.output_path)

  def run(self) -> None:
    os.makedirs(self.output_path, exist_ok=True)
    tmp_path = os.path.join(self.output_path, self.job_name)
    os.makedirs(tmp_path, exist_ok=True)
    output_client = StorageClient(self.output_path, tmp_dir=tmp_path)

    logging.info('Processing input data to generate diff...')
    if self.runner_mode == 'cloud':
      obs_diff, schema_diff = self._run_cloud_differ(tmp_path, output_client)
    else:
      obs_diff, schema_diff = self._run_local_differ(tmp_path, output_client)

    self._analyze_and_write_results(obs_diff, schema_diff, output_client)


def main(_):
  '''Runs the differ.'''
  differ = ImportDiffer(
      _FLAGS.current_data,
      _FLAGS.previous_data,
      _FLAGS.output_location,
      _FLAGS.project_id,
      _FLAGS.job_name,
      _FLAGS.file_format,
      _FLAGS.runner_mode,
  )
  differ.run()


if __name__ == '__main__':
  app.run(main)
