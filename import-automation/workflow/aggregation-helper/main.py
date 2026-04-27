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

import functions_framework
from google.cloud import bigquery
import logging
from flask import jsonify
import os
from place_aggregator import PlaceAggregator

logging.getLogger().setLevel(logging.INFO)

# Initialize BigQuery Client
try:
    bq_client = bigquery.Client()
except Exception as e:
    logging.warning(f"Failed to initialize BigQuery client: {e}")
    bq_client = None

BQ_DATASET_ID = os.environ.get('BQ_DATASET_ID')
SPANNER_PROJECT_ID = os.environ.get('SPANNER_PROJECT_ID')
SPANNER_INSTANCE_ID = os.environ.get('SPANNER_INSTANCE_ID')
SPANNER_DATABASE_ID = os.environ.get('SPANNER_DATABASE_ID')
GCS_BUCKET_ID = os.environ.get('GCS_BUCKET_ID')


@functions_framework.http
def aggregation_helper(request):
    """
    HTTP Cloud Function that takes importName and runs a BQ query.
    """
    request_json = request.get_json(silent=True)
    import_list = request_json.get('importList', [])
    logging.info(f"Received request for importList: {import_list}")
    results = []
    try:
        # Initialize PlaceAggregator
        place_aggregator = PlaceAggregator(bq_client)
        
        for import_item in import_list:
            import_name = import_item.get('importName')

            # Scaffolding: Run place aggregation for a specific import or just as a test
            if import_name == 'CDCMortality': # Using the example from legacy doc
                logging.info(f"Triggering place aggregation for {import_name}")
                # Defaulting to California and 2020 for scaffolding
                agg_results = place_aggregator.aggregate_population(parent_place="geoId/06", date="2020")
                results.extend(agg_results)
            else:
                logging.info(f"Skipping aggregation logic for {import_name}")
                continue

        return jsonify({"status": "success", "results": results}), 200

    except Exception as e:
        logging.error(f"Aggregation failed: {e}")
        return (f"Aggregation failed: {str(e)}", 500)
