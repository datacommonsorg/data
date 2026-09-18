# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""DAG that runs a parameterized container command as a Cloud Batch job."""

import datetime
import os

from airflow.providers.google.cloud.operators import cloud_batch
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.hitl import HITLBranchOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sdk import DAG
from airflow.sdk import Param

from datacommons_airflow.cloud_batch_job import build_job
from datacommons_airflow.cloud_batch_job import get_required_environment
from datacommons_airflow.cloud_batch_job import make_batch_job_id
from datacommons_airflow.cloud_batch_job import PROJECT_ID_ENV
from datacommons_airflow.cloud_batch_job import REGION_ENV
from datacommons_airflow.cloud_batch_job import SERVICE_ACCOUNT_ENV

PROJECT_ID = get_required_environment(os.environ, PROJECT_ID_ENV)
REGION = get_required_environment(os.environ, REGION_ENV)
SERVICE_ACCOUNT_EMAIL = get_required_environment(os.environ,
                                                 SERVICE_ACCOUNT_ENV)

DAG_ID = 'cloud_batch_container_command'
IMPORT_NAME_TEMPLATE = '{{ params.import_name }}'
IMAGE_URI_TEMPLATE = '{{ params.image_uri }}'
COMMAND_TEMPLATE = '{{ params.command }}'
JOB_ID_TEMPLATE = '{{ batch_job_id(run_id, ti.try_number, params.import_name) }}'

IMPORT_NAME_PARAM = Param(
    default='custom-import',
    type='string',
    minLength=1,
    maxLength=100,
    title='Import name',
    description='Descriptive name for the import workload (used in Batch job IDs and logs).',
)
IMAGE_URI_PARAM = Param(
    type='string',
    minLength=1,
    maxLength=2000,
    title='Container image URI',
    description='Image containing /bin/sh and command dependencies.',
)
COMMAND_PARAM = Param(
    type='string',
    minLength=1,
    maxLength=10000,
    title='Shell command',
    description='Command executed by /bin/sh -c inside the container.',
)
DAG_PARAMS = {
    'import_name': IMPORT_NAME_PARAM,
    'image_uri': IMAGE_URI_PARAM,
    'command': COMMAND_PARAM,
}

with DAG(
        dag_id=DAG_ID,
        description='Run a parameterized container command on Cloud Batch.',
        schedule=None,
        start_date=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        catchup=False,
        default_args={
            'owner': 'data-imports',
            'retries': 0,
        },
        params=DAG_PARAMS,
        user_defined_macros={'batch_job_id': make_batch_job_id},
        tags=['import-automation', 'cloud-batch'],
) as dag:
    run_container_command = cloud_batch.CloudBatchSubmitJobOperator(
        task_id='run_container_command',
        project_id=PROJECT_ID,
        region=REGION,
        job_name=JOB_ID_TEMPLATE,
        job=build_job(
            image_uri=IMAGE_URI_TEMPLATE,
            command=COMMAND_TEMPLATE,
            service_account_email=SERVICE_ACCOUNT_EMAIL,
        ),
        gcp_conn_id='google_cloud_default',
        deferrable=True,
        polling_period_seconds=30,
    )

    review_batch_result = HITLBranchOperator(
        task_id='review_batch_result',
        subject='Review the Cloud Batch result',
        body='Choose whether to run the Cloud Batch step again or continue.',
        options=['Run again', 'Continue'],
        options_mapping={
            'Run again': 'rerun_container_command',
            'Continue': 'continue_workflow',
        },
    )

    rerun_container_command = TriggerDagRunOperator(
        task_id='rerun_container_command',
        trigger_dag_id=DAG_ID,
        trigger_run_id=(
            '{{ params.import_name }}__{{ macros.datetime.now().strftime("%Y%m%dT%H%M%S") }}'
            '__retry_{{ ti.try_number }}'
        ),
        conf={
            'import_name': IMPORT_NAME_TEMPLATE,
            'image_uri': IMAGE_URI_TEMPLATE,
            'command': COMMAND_TEMPLATE,
        },
        wait_for_completion=False,
    )

    continue_workflow = EmptyOperator(task_id='continue_workflow')

    run_container_command >> review_batch_result >> [
        rerun_container_command,
        continue_workflow,
    ]
