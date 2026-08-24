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
"""Cloud Batch job configuration shared by the container-command DAG."""

import hashlib
from collections.abc import Mapping

MACHINE_TYPE = 'e2-standard-4'
CPU_MILLI = 4000
MEMORY_MIB = 16384
MAX_RUN_DURATION = '3600s'

PROJECT_ID_ENV = 'GCP_PROJECT_ID'
REGION_ENV = 'CLOUD_BATCH_REGION'
SERVICE_ACCOUNT_ENV = 'CLOUD_BATCH_SERVICE_ACCOUNT'


def get_required_environment(environ: Mapping[str, str], name: str) -> str:
    """Returns a non-empty deployment environment value."""
    value = environ.get(name, '').strip()
    if not value:
        raise ValueError(f'Missing required environment variable: {name}')
    return value


def make_batch_job_id(run_id: str, try_number: int) -> str:
    """Returns a valid, deterministic Batch job ID for one task attempt."""
    if not run_id:
        raise ValueError('run_id must not be empty')
    if try_number < 1:
        raise ValueError('try_number must be positive')

    identity = f'{run_id}:{try_number}'.encode('utf-8')
    digest = hashlib.sha256(identity).hexdigest()[:32]
    return f'airflow-{digest}'


def build_job(image_uri: str, command: str, service_account_email: str) -> dict:
    """Builds the Cloud Batch job submitted by the Airflow operator."""
    return {
        'task_groups': [{
            'task_count': 1,
            'task_spec': {
                'runnables': [{
                    'container': {
                        'image_uri': image_uri,
                        'entrypoint': '/bin/sh',
                        'commands': ['-c', command],
                    },
                }],
                'compute_resource': {
                    'cpu_milli': CPU_MILLI,
                    'memory_mib': MEMORY_MIB,
                },
                'max_retry_count': 0,
                'max_run_duration': MAX_RUN_DURATION,
            },
        }],
        'allocation_policy': {
            'instances': [{
                'policy': {
                    'machine_type': MACHINE_TYPE,
                    'provisioning_model': 'STANDARD',
                },
            }],
            'service_account': {
                'email': service_account_email,
            },
        },
        'logs_policy': {
            'destination': 'CLOUD_LOGGING',
        },
        'labels': {
            'source': 'airflow',
            'workflow': 'container-command',
        },
    }
