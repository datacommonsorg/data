# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Script to generate events from source data.
It is a pipeline with the following steps:
  1. get_source_data: Download data from source, incrementally with any source specific processing
  2. generate_gridded_csv: Process source data into CSV with S2 cells.
  3. generate_events: Generate events and related stats from the csv data.
"""

import os
import re
import sys
import time

from absl import app
from absl import flags
from absl import logging

flags.DEFINE_string('pipeline_config', '',
                    'Config for the pipeline as a py dictionary of json')
flags.DEFINE_string(
    'pipeline_state', '',
    'File with state for the pipeline processing as a python dictionary.'
    'Used to resume processing for new incremental data.')
flags.DEFINE_list('run_stages', [],
                  'List of stages to run. If empty, all stages are run.')

_FLAGS = flags.FLAGS

_SCRIPTS_DIR = os.path.dirname(__file__)
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), 'util'))

import common_flags
import earthengine_image
import file_util
import raster_to_csv
import process_events
import utils

from counters import Counters
from config_map import ConfigMap
from download_util import request_url
from google.cloud import bigquery

_DEBUG = False

# Default configuration settings.
# Includes static settings for each stage of processing.
_DEFAULT_CONFIG = {
    'defaults': {
        # Change to import specific name
        'import_name': 'import',

        # Date from which to process files.
        'start_date': '',
        'time_period': 'P1M',

        # GCS folder setting for generated images
        # output will be in: gs://<gcs_bucket>/<gcs_folder>/*.tif
        'gcs_project': '',
        'gcs_bucket': 'datcom-prod-imports',
        'gcs_folder': '{import_name}',
    },
    # sequence of stages with configs.
    'stages': [
        # Settings to fetch geotiff from earth engine
        # See earthentine_image.py:EE_DEFAULT_CONFIG for config parameters
        {
            'stage': 'earthengine',

            # Date from which to process files.
            'start_date': '',
            'time_period': 'P1M',

            # GCS folder setting for generated images
            # output will be in: gs://<gcs_bucket>/<gcs_folder>/*.tif
            'gcs_project': '',
            'gcs_bucket': '',
            'gcs_folder': '',

            # Wait for EE tasks to complete
            'ee_wait_task': True,
            'skip_existing_output': True,
        },

        # Settings to download source data
        {
            'stage':
                'download',
            # List of URLs to download
            'url': [],

            # URL parameters
            'url_params': {},
            'http_method':
                'GET',

            # Look for lines with date in the response.
            'successful_response_regex':
                ',[0-9]{4}-[0-9]{2}-[0-9]{2},',

            # Dates to download files
            'start_date':
                '',
            'time_period':
                'P1D',

            # Retry settings.
            'timeout':
                60,
            'retry_count':
                10,
            'retry_interval':
                60,

            # GCS folder setting for downloaded files
            # output will be in: gs://<gcs_bucket>/<gcs_folder>/*.csv
            'gcs_project':
                '',
            'gcs_bucket':
                '',
            'gcs_folder':
                '',
            'output_file':
                'gs://{gcs_bucket}/{gcs_folder}/{stage_name}/{import_name}-{stage_name}-{start_date}-{time_period}.csv',
            'skip_existing_output':
                True,
        },

        # Settings to convert source input data to csv
        # See raster_to_csv.py:_DEFAULT_CONFIG for config settings
        {
            'stage':
                'raster_csv',
            'skip_existing_output':
                True,
            's2_level':
                10,
            'output_file':
                'gs://{gcs_bucket}/{gcs_folder}/input_csv/{year}/{import_name}-{stage_name}-{start_date}-{time_period}.csv'
        },
        # Settings to process data into events
        # See process_events.py:_DEFAULT_CONFIG for config settings.
        {
            'stage':
                'events',
            'output_dir':
                'gs://{gcs_bucket}/{gcs_folder}/events/{year}/data.{file_extension}'
        },
    ],

    # File with the latest state for the pipeline
    'pipeline_state_file': ''
}

# Processing state persisted to a file
# Includes dynamic parameter values for each stage of processing.
_PROCESS_STATE = {
    # Last date for which input was processed in YYYY-MM-DD format
    'last_input_date': '',
}

_DEBUG = False


class StageRunner:
    '''Class to run a single stage of the pipeline.
    Create a derived class with run() method calling necessary processing.
    Example:
      class MyStage(StageRunner):
        def __init__(self,
                     config_dicts: list = [],
                     state: dict = {},
                     counters=None):
          self.setUp('My-Stage', configs, state, counters)

        def run(self,
            input_files: list = None,
            config: dict = {},
            counters: Counters = None) -> list:
          outputs = []
          for file in input_files:
            outputs.append(my_process(file, config, counters))
          return outputs

    '''

    def __init__(self,
                 config_dicts: list = [],
                 state: dict = {},
                 counters=None):
        self.setUp('runner', config_dicts, state, counters)

    def run(self,
            input_files: list = None,
            config: dict = {},
            counters: Counters = None) -> list:
        '''Override in child class.
       Returns the output files generated after running processing for this stage
       on the input_files.

       Args:
         input_files: List of files to process
           they are outputs from previous stage along with any files
           matching config['input_files'].
          config: dictionary of configuration settings for this stage.
          counters: global counters for the task.
       Returns:
         list if output files that are passed on to the next stage as inputs.
        '''
        logging.fatal(
            f'run() not implemented in {self.__class__}. Use a class with run() overridden.'
        )
        return []

    def setUp(self,
              name: str,
              config_dicts: list = [],
              state: dict = {},
              counters=None):
        '''Called by derived classes to set up configs and state in the base class.'''
        self.name = name
        # Dynamic state with parameters to be updated after run.
        self.state = state
        # Set config as a merged dict
        self.config = _merge_dicts(config_dicts)
        self.config['stage_name'] = name
        # Counters for this stage.
        self.counters = counters
        if counters is None:
            self.counters = Counters()
        self.set_config_dates()
        self.set_output_dir()
        logging.info(
            f'Created stage: {name} with config: {self.config} from configs: {config_dicts}'
        )

    def get_name(self):
        return self.name

    def run_stage(self, input_files: list) -> list:
        '''Returns the output files after running the stage.'''
        # Get input files from args or config.
        input_files = self.get_inputs(input_files)

        # Get resolved config for running stage.
        self.config.update(self.state)
        config = _get_resolved_dict(self.config)

        # Run the stage
        logging.info(
            f'Running stage: {self.name} with {len(input_files)} inputs: {input_files} and config: {config}'
        )
        output_files = self.run(input_files, config, self.counters)
        logging.info(f'Got output for {self.name}: {output_files}')

        # Set the state for the stage
        stage_state = self.get_state(self.name, {})
        stage_state['input'] = ','.join(input_files)
        if output_files:
            if isinstance(output_files, list):
                stage_state['output'] = ','.join(output_files)
            else:
                stage_state['output'] = output_files
        self.set_state(self.name, stage_state)
        return output_files

    def get_inputs(self, inputs: list = []) -> list:
        '''Return a set of files macthing input config.'''
        input_list = inputs
        config_inputs = self.get_config('input_files', '')
        if config_inputs:
            input_list.append(config_inputs)
        # Replace any reference to other config parameters.
        input_pat = _format(','.join(input_list), self.config)
        return file_util.file_get_matching(input_pat)

    def set_output_dir(self) -> str:
        '''Sets the output directory in the config if not set.'''
        if not self.get_config('output_dir', ''):
            import_dir = self.get_config('import_dir', '')
            output_dir = os.path.join(import_dir, self.name)
            self.set_config('output_dir', output_dir)

    def get_output_dir(self) -> str:
        return self.get_config('output_dir', '')

    def get_output_filename(self,
                            input_filename: str = '',
                            config_dict: dict = {},
                            file_ext: str = '.csv') -> str:
        '''Returns the file name from the config.'''
        filename = self.config.get('output_file', '')
        if not filename:
            filename = self.get_config('output_file', '')
        if not filename:
            # Create filename from GCS settings.
            output_dir = self.get_output_dir()
            stage_name = self.get_name()
            if not output_dir:
                gcs_bucket = self.get_config('gcs_bucket', '')
                gcs_folder = self.get_config('gcs_folder', '')
                if gcs_bucket and gcs_folder:
                    output_dir = f'gs://{gcs_bucket}/{gcs_folder}/{stage_name}'
            if output_dir:
                if input_filename:
                    filename = file_util.file_get_name(os.path.join(
                        output_dir, os.path.basename(input_filename)),
                                                       suffix=f'-{stage_name}')
                else:
                    filename = f'{output_dir}/{import_name}-{stage_name}-{start_date}-{time_period}{file_ext}'

        return _format(filename, self.config)

    def should_skip_existing_output(self, filename: str) -> bool:
        '''Returns True if the filename exists and skip_existing_output is True.'''
        if self.get_config('skip_existing_output', True):
            existing_file = file_util.file_get_matching(filename)
            if existing_file:
                return True
        return False

    def get_config(self,
                   param: str,
                   default_value: str = '',
                   config_dict: dict = {}) -> str:
        '''Returns the resolved config value from config_dict or object's config.'''
        if config_dict:
            value = config_dict.get(param, None)
            if value:
                return _format(value, config_dict)
        value = self.config.get(param, default_value)
        return _format(value, self.config)

    def set_config(self, param: str, value: str) -> str:
        '''Set the config parameter.'''
        self.config[param] = value
        return value

    def get_configs(self) -> dict:
        return _get_resolved_dict(self.config)

    def get_state(self, key: str, default_value: str = '') -> str:
        '''Returns the value for the key from the processing state dict.'''
        return self.state.get(key, default_value)

    def set_state(self, key: str, value: str):
        '''Sets the value of the pipeline state.'''
        self.state[key] = value
        return value

    def set_config_dates(self, start_date: str = ''):
        '''Set the dates in the config based on processing state.'''
        # Set start_date to be the next date from the last input date
        if start_date:
            self.set_config('start_date', start_date)
        start_date = self.get_config('start_date', '')
        if not start_date:
            # Set the start_date to the last processed date.
            last_input_date = self.get_state('last_input_date', '')
            if last_input_date:
                start_date = utils.date_advance_by_period(
                    self.get_state('last_input_date', ''),
                    self.get_config('time_period', 'P1M'))
                logging.info(
                    f'Setting start_date to {start_date} from last_input_date: {last_input_date}'
                )
            if not start_date:
                # No date set, set to start of year.
                start_date = utils.date_today('%Y-01-01')
                logging.info(
                    f'Setting start_date to start of year: {start_date}')
            if start_date:
                self.set_config('start_date', start_date)
        self.set_config('year', start_date[:4])
        self.set_config('month', start_date[5:7])
        self.set_config('day', start_date[8:10])


class EarthEngineRunner(StageRunner):
    '''Class to generate geoTif images from earth engine.'''

    def __init__(self,
                 config_dicts: list = [],
                 state: dict = {},
                 counters=None):
        configs = [earthengine_image.EE_DEFAULT_CONFIG]
        configs.extend(config_dicts)
        self.setUp('earthengine', configs, state, counters)

    def run(self,
            input_files: list = None,
            config_dict: dict = {},
            counters: Counters = None) -> list:
        logging.info(f'Processing earth engine config: {config_dict}')
        # Generate ee images
        ee_tasks = earthengine_image.ee_process(config_dict)
        if not ee_tasks:
            return None
        # Return the list of output files.
        image_files = []
        for status in ee_tasks:
            output_file = status.get('output_file', '')
            if output_file:
                image_files.append(output_file)
        return image_files


class DownloadRunner(StageRunner):
    '''Class to download data files from source.'''

    def __init__(self,
                 config_dicts: list = [],
                 state: dict = {},
                 counters=None):
        self.setUp('download', config_dicts, state, counters)

    def run(self,
            input_files: list = None,
            config_dict: dict = {},
            counters: Counters = None) -> list:
        # Download data from start_date up to end_date
        # advancing date by the time_period.
        start_date = self.get_config('start_date', '', config_dict)
        end_date = self.get_config('end_date', '', config_dict)
        if not end_date:
            end_date = utils.date_yesterday()
        data_files = []
        while start_date and start_date <= end_date:
            # Download data for the start_date
            download_files = self.download_file_with_config(self.get_configs())
            if download_files:
                data_files.extend(download_files)

            # Advance start_date to the next date.
            start_date = utils.date_advance_by_period(
                start_date, self.get_config('time_period', 'P1M', config_dict))
            if start_date:
                self.set_config_dates(start_date=start_date)
        return data_files

    def download_file_with_config(self, config_dict: dict = {}) -> list:
        '''Returns list of files downloaded for config.'''
        logging.info(f'Downloading data for config: {config_dict}')
        downloaded_files = []
        urls = config_dict.get('url', [])
        if not isinstance(urls, list):
            urls = [urls]
        for url in urls:
            if not url:
                continue
            url_params = config_dict.get('url_params', {})
            filename = self.get_output_filename(config_dict=config_dict)
            if self.should_skip_existing_output(filename):
                logging.info(f'Skipping download for existing file: {filename}')
                continue

            # Download the URL with retries.
            download_content = ''
            retry_count = 0
            retries = config_dict.get('retry_count', 5)
            retry_secs = config_dict.get('retry_interval', 5)
            while not download_content and retry_count < retries:
                download_content = request_url(
                    url,
                    params=url_params,
                    method=config_dict.get('http_method', 'GET'),
                    output=config_dict.get('response_type', 'text'),
                    timeout=config_dict.get('timeout', 60),
                    retries=config_dict.get('retry_count', 3),
                    retry_secs=retry_secs)
                if download_content:
                    # Check if the downloaded content matches the regex.
                    regex = config_dict.get('successful_response_regex', '')
                    if regex:
                        match = re.search(regex, download_content)
                        if not match:
                            download_content = ''
                            retry_count += 1
                            logging.info(
                                f'Downloaded content for {url} does not match {regex}'
                            )
                            if retry_count < retries:
                                logging.info(
                                    f'retrying {url} #{retry_count} after {retry_secs}'
                                )
                                time.sleep(retry_secs)
            if not download_content:
                logging.error(
                    f'Failed to download {url} after {retries} retries')
                return None

            # Save downloaded content to file.
            with file_util.FileIO(filename, mode='w') as file:
                file.write(download_content)
            logging.info(
                f'Downloaded {len(download_content)} bytes from {url} into file: {filename}'
            )
            downloaded_files.append(filename)

        return downloaded_files


class BigQueryExportRunner(StageRunner):
    '''Class to download data from BigQuery tables using SQL.
    Data is exported on GCS as csv.
    '''

    # SQL statement to export query output.
    _EXPORT_SQL_QUERY = '''
    EXPORT DATA
      OPTIONS (
        uri = '{output}',
        format = 'CSV',
        overwrite = true,
        header = true,
        field_delimiter = ',')
    AS (
        {query}
    )'''

    def __init__(self,
                 config_dicts: list = [],
                 state: dict = {},
                 counters=None):
        self.setUp('bq_export', config_dicts, state, counters)

    def run(self,
            input_files: list = None,
            config_dict: dict = {},
            counters: Counters = None) -> list:
        '''Returns the list of csv files exported from BigQuery.'''
        # Get the query
        query = self.get_bq_query(config_dict)
        if not query:
            logging.error(
                f'No SQL query set for BigQueryExportRunner in {self.config.get_configs()}.'
            )
            return []

        # Setup query to export to output files as csv.
        project_id = self.get_config('gcs_project', None, config_dict)
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
        bq_client = bigquery.Client(project=project_id)
        output = self.get_output_filename(config_dict=config_dict,
                                          file_ext='-*.csv')
        if not query.lower().startswith('export'):
            query = self._EXPORT_SQL_QUERY.format(query=query, output=output)
        else:
            query_output = self.get_query_export_uri(query)
            if query_output:
                output = query_output
            else:
                logging.fatal(f'No export uri in BQ query: {query}')

        # Run the BQ query.
        logging.info(f'Running query: {query}')
        result = bq_client.query(query)
        while (result.state == 'RUNNING'):
            time.sleep(1)
        logging.info(
            f'Got response: {result}, state: {result.state}, errors: {result.errors} for query: {query}'
        )
        if result.errors:
            logging.fatal(
                f'Failed to run query:{query}, Error: {result.errors}')
            return []

        # Get the output files.
        output_files = file_util.file_get_matching(output)
        logging.info(f'Got output: "{output_files}" for query: {query}')
        return output_files

    def get_bq_query(self, config_dict: dict = {}) -> str:
        '''Returns the query to select data to export.'''
        query = self.get_config('bq_query', '', config_dict).strip()
        if not query:
            # No query in config. Export the whole table is specified.
            table = config_dict.get('bq_table')
            if table:
                query = f'SELECT * from {table}'
        return query

    def get_query_export_uri(self, query: str) -> str:
        '''Returns the output URI from the export query.'''
        _EXPORT_OUTPUT_REGEX = r'url *= *[\'"](?P<output>[^\'"]*)[\'"]'
        matche = re.search(_EXPORT_OUTPUT_REGEX, query)
        if match:
            return match.groupdict().get('output', '')


class RasterCSVRunner(StageRunner):
    '''Class to generate CSV per input geoTif or CSV with lat/long.'''

    def __init__(self,
                 config_dicts: list = [],
                 state: dict = {},
                 counters=None):
        self.setUp('raster_csv', config_dicts, state, counters)

    def run(self,
            input_files: list = None,
            config_dict: dict = {},
            counters: Counters = None) -> list:
        '''Returns the csv files with data per geo point generated from the input files.
      The input geoTif files are converted to data per-s2 cell grid.
      Input csvs with lat,longs are also converted to data per grid point.
      '''
        output_files = []

        for filename in file_util.file_get_matching(input_files):
            output_filename = self.get_output_filename(input_filename=filename)
            if self.should_skip_existing_output(output_filename):
                logging.info(
                    f'Skip processing {filename} for existing file: {output_filename}'
                )
                continue
            filebase, ext = os.path.splitext(filename)
            input_geotif = ''
            input_csv = ''
            if ext == '.csv':
                input_csv = filename
            else:
                input_geotif = filename
                # Get date from geoTif filename as bands may not have the
                # date.
                output_date = earthengine_image.get_date_from_filename(
                    filename, self.get_config('time_period', 'P1D',
                                              config_dict))
                if output_date:
                    self.set_config('output_date', output_date)
            raster_to_csv.process(input_geotif, input_csv, output_filename,
                                  ConfigMap(config_dict=config_dict),
                                  self.counters)
            output_files.append(output_filename)
        return output_files


class EventsRunner(StageRunner):
    '''Class to generate CSV per input geoTif or CSV weith lat/long.'''

    def __init__(self,
                 config_dicts: list = [],
                 state: dict = {},
                 counters=None):
        configs = [process_events._DEFAULT_CONFIG]
        configs.extend(config_dicts)
        self.setUp('events', configs, state, counters)

    def run(self,
            input_files: list = None,
            config_dict: dict = {},
            counters: Counters = None) -> list:
        '''Process data for places into events.'''
        config = ConfigMap(config_dict=config_dict)
        output_path = self.get_output_dir()
        process_events.process(csv_files=input_files,
                               output_path=output_path,
                               config=config)


_STAGE_RUNNERS = {
    'earthengine': EarthEngineRunner,
    'download': DownloadRunner,
    'bq_export': BigQueryExportRunner,
    'raster_csv': RasterCSVRunner,
    'events': EventsRunner,
}


class EventPipeline(StageRunner):
    '''Class to generate events from source data.
    Runs a series of pipelines as per the config.
    '''

    def __init__(self, config: ConfigMap, counters: Counters = None):
        self._config = config
        if not config:
            self._config = ConfigMap()
        self._pipeline_state = {}
        self.load_pipeline_state()
        config_dicts = [self._config.get('defaults', {})]
        config_dicts.append(self._config.get_configs())
        self.setUp('event_pipeline', config_dicts, self._pipeline_state,
                   counters)
        self.setup_stages()

    def __del__(self):
        # Save the pipeline state into the file.
        if self._pipeline_state:
            pipeline_state_file = self.get_config('pipeline_state_file', '')
            if pipeline_state_file:
                return file_util.file_write_py_dict(self._pipeline_state,
                                                    pipeline_state_file)

    def load_pipeline_state(self) -> dict:
        pipeline_state_file = self._config.get('pipeline_state_file', '')
        if pipeline_state_file:
            self._pipeline_state = file_util.file_load_py_dict(
                pipeline_state_file)
            logging.info(
                f'Loaded pipeline state: {self._pipeline_state} from {pipeline_state_file}'
            )
        return self._pipeline_state

    def set_pipeline_state(self, key: str, value: str):
        '''Sets the value of the pipeline state.'''
        self._pipeline_state[key] = value

    def setup_stages(self):
        '''Create the runners for each stage of the pipeline.'''
        self.stage_runners = []
        stage_names = []
        default_config = self._config.get('defaults', {})
        if not default_config:
            default_config = dict(self._config.get_configs())
            if 'stages' in default_config:
                default_config.remove('stages')
        for stage_config in self._config.get('stages', []):
            stage = stage_config.get('stage', '')
            if stage not in _STAGE_RUNNERS:
                logging.fatal(f'Unknown stage: {stage} in {stage_config}')
            runner = _STAGE_RUNNERS[stage]
            configs = [default_config, stage_config]
            self.stage_runners.append(
                runner(configs, self._pipeline_state, self.counters))
            stage_names.append(stage)
        logging.info(
            f'Created pipeline with {len(self.stage_runners)} stages: {stage_names}'
        )

    def run(self, run_stages: list = []):
        '''Run all the stages in the pipeline.'''
        stage_count = 0
        output_files = []
        for stage_runner in self.stage_runners:
            stage_count += 1
            stage_name = stage_runner.get_name()
            if not run_stages or stage_name in run_stages:
                self.counters.set_prefix(f'S{stage_count}:{stage_name}:')
                output_files = stage_runner.run_stage(output_files)
            else:
                output_files = []

        if output_files:
            # Update the process state
            self.set_pipeline_state('last_input_date', utils.date_yesterday())


def _merge_dicts(config_dicts: list) -> dict:
    config = {}
    if not isinstance(config_dicts, list):
        config_dicts = [config_dicts]
    for d in config_dicts:
        config.update(d)
    return config


def _get_resolved_dict(config: dict) -> dict:
    '''Resolve format string references in the values of the config dict.'''
    resolved_config = {}
    for param in config.keys():
        value = config[param]
        if value and isinstance(value, str):
            # Resolve string value.
            resolved_config[param] = _format(value, config)
        else:
            resolved_config[param] = value
    return resolved_config


def _format(string: str, params: dict) -> str:
    '''Returns the string with format patterns replaced.'''
    formatted_str = string
    try:
        if isinstance(string, str):
            formatted_str = string.format(**params)
        elif isinstance(string, list):
            formatted_str = [_format(s, params) for s in string]
    except (KeyError, IndexError) as e:
        logging.error(f'Format error for {string} with {params}')
    return formatted_str


def main(_):
    config_dict = file_util.file_load_py_dict(_FLAGS.pipeline_config)
    if _FLAGS.pipeline_state:
        config_dict['pipeline_state_file'] = _FLAGS.pipeline_state
    config = ConfigMap(config_dict=config_dict)
    if _FLAGS.debug or config.get('debug', False):
        config.set_config('debug', True)
    pipeline = EventPipeline(config=config)
    pipeline.run(run_stages=_FLAGS.run_stages)


if __name__ == '__main__':
    app.run(main)
