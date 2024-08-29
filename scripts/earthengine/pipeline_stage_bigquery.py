# Copyright 2023 Google LLC
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
"""Class to run the events pipeline stage to export data from BigQuery.
"""

import os
import sys

from absl import logging
from google.cloud import bigquery

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), 'util'))

from counters import Counters
from pipeline_stage_runner import StageRunner, register_stage_runner


class BigQueryExportRunner(StageRunner):
    '''Class to download data from BigQuery tables using SQL.
    Data is exported on GCS as csv.
    '''

    # SQL statement template to export query output to GCS.
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
        self.set_up('bq_export', config_dicts, state, counters)

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


# Register the EventsRunner
register_stage_runner('bigquery', BigQueryExportRunner)
