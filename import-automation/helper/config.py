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

import os

PROJECT_ID = os.environ.get('PROJECT_ID')
LOCATION = os.environ.get('LOCATION') or os.environ.get('REGION')
PROJECT_NUMBER = os.environ.get('PROJECT_NUMBER')
GCS_BUCKET_ID = os.environ.get('GCS_BUCKET_ID')

SPANNER_DATABASE_PATH = os.environ.get('SPANNER_DATABASE_PATH')
if SPANNER_DATABASE_PATH and len(SPANNER_DATABASE_PATH.split('/')) >= 6:
    _parts = SPANNER_DATABASE_PATH.split('/')
    SPANNER_PROJECT_ID = _parts[1]
    SPANNER_INSTANCE_ID = _parts[3]
    SPANNER_DATABASE_ID = _parts[5]
else:
    SPANNER_PROJECT_ID = os.environ.get('SPANNER_PROJECT_ID')
    SPANNER_INSTANCE_ID = os.environ.get('SPANNER_INSTANCE_ID')
    SPANNER_DATABASE_ID = os.environ.get('SPANNER_DATABASE_ID')

SPANNER_EMULATOR_HOST = os.environ.get('SPANNER_EMULATOR_HOST')
IS_BASE_DC = os.environ.get('IS_BASE_DC', 'true').lower() == 'true'
GCS_OUTPUT_PREFIX = os.environ.get('GCS_OUTPUT_PREFIX', '')

INGESTION_HELPER_SERVICE = os.environ.get('INGESTION_HELPER_SERVICE', 'ingestion-helper-service')
INGESTION_HELPER_URL = f"https://{INGESTION_HELPER_SERVICE}-{PROJECT_NUMBER}.{LOCATION}.run.app" if PROJECT_NUMBER and LOCATION else ""
SPANNER_INGESTION_WORKFLOW_ID = os.environ.get('SPANNER_INGESTION_WORKFLOW_NAME', 'spanner-ingestion-workflow')
IMPORT_AUTOMATION_WORKFLOW_ID = os.environ.get('IMPORT_AUTOMATION_WORKFLOW_NAME', 'import-automation-workflow')
AIRFLOW_WEB_SERVER_URL = os.environ.get('AIRFLOW_WEB_SERVER_URL', '')
AIRFLOW_DEFAULT_DAG_ID = os.environ.get(
    'AIRFLOW_DEFAULT_DAG_ID',
    'manual_refresh'
)
AIRFLOW_IAP_CLIENT_ID = os.environ.get('AIRFLOW_IAP_CLIENT_ID', '')
