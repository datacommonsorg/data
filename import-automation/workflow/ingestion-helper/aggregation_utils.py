# Copyright 2026 Google LLC
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

import logging
import os
from google.cloud import bigquery

logging.getLogger().setLevel(logging.INFO)

class AggregationUtils:
    def __init__(self):
        # Initialize BigQuery Client
        try:
            self.bq_client = bigquery.Client()
        except Exception as e:
            logging.warning(f"Failed to initialize BigQuery client: {e}")
            self.bq_client = None

        self.bq_dataset_id = os.environ.get('BQ_DATASET_ID')

    def run_aggregation(self, import_list):
        """
        Runs a BQ query for each import in the import_list.
        """
        logging.info(f"Received request for importList: {import_list}")
        results = []
        if not self.bq_client:
             logging.error("BigQuery client not initialized")
             return False

        try:
            for import_item in import_list:
                import_name = import_item.get('importName')

                query = None
                # Define specific queries based on importName
                if import_name:
                    query = """
                        SELECT @import_name as import_name, CURRENT_TIMESTAMP() as execution_time
                     """
                else:
                    logging.info('Skipping aggregation logic')
                    continue

                if query:
                    job_config = bigquery.QueryJobConfig(query_parameters=[
                        bigquery.ScalarQueryParameter("import_name", "STRING",
                                                      import_name),
                    ])
                    query_job = self.bq_client.query(query, job_config=job_config)
                    query_results = query_job.result()
                    for row in query_results:
                        results.append(dict(row))
            return True

        except Exception as e:
            logging.error(f"Aggregation failed: {e}")
            raise e
