# Copyright 2025 Google LLC
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
from spanner_client import SpannerClient
from storage_client import StorageClient
from flask import jsonify
import logging
import import_utils
import os
import sys
from absl import flags

logging.getLogger().setLevel(logging.INFO)

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'project_id', os.environ.get('PROJECT_ID', 'datcom-import-automation-prod'),
    'GCP Project ID')
flags.DEFINE_string('spanner_project_id',
                    os.environ.get('SPANNER_PROJECT_ID', 'datcom-store'),
                    'Spanner Project ID')
flags.DEFINE_string('spanner_instance_id',
                    os.environ.get('SPANNER_INSTANCE_ID', 'dc-kg-test'),
                    'Spanner Instance ID')
flags.DEFINE_string('spanner_database_id',
                    os.environ.get('SPANNER_DATABASE_ID', 'dc_graph_import'),
                    'Spanner Database ID')
flags.DEFINE_string('gcs_bucket_id',
                    os.environ.get('GCS_BUCKET_ID', 'datcom-prod-imports'),
                    'GCS Bucket ID')
flags.DEFINE_string('location', os.environ.get('LOCATION', 'us-central1'),
                    'GCP Location')


def _validate_params(request_json, required_params):
    for param in required_params:
        if param not in request_json:
            return f"'{param}' parameter is missing"
    return None


@functions_framework.http
def ingestion_helper(request):
    """
    HTTP Cloud Function with helper routines for Spanner ingestion workflow.
    """
    request_json = request.get_json(silent=True)
    if not request_json:
        return ('Request is not a valid JSON', 400)

    validation_error = _validate_params(request_json, ['actionType'])
    if validation_error:
        return (validation_error, 400)

    actionType = request_json['actionType']
    spanner = SpannerClient(FLAGS.spanner_project_id, FLAGS.spanner_instance_id,
                            FLAGS.spanner_database_id)
    storage = StorageClient(FLAGS.gcs_bucket_id)

    if actionType == 'get_import_list':
        # Gets the list of imports that are ready for ingestion.
        import_list = request_json.get('importList', [])
        imports = spanner.get_import_list(import_list)
        return jsonify(imports)
    elif actionType == 'acquire_ingestion_lock':
        # Attempts to acquire the global lock for ingestion.
        validation_error = _validate_params(request_json,
                                            ['workflowId', 'timeout'])
        if validation_error:
            return (validation_error, 400)
        workflow = request_json['workflowId']
        timeout = request_json['timeout']
        status = spanner.acquire_lock(workflow, timeout)
        if not status:
            return ('Failed to acquire lock', 500)
        return ('Lock acquired', 200)
    elif actionType == 'release_ingestion_lock':
        # Releases the global ingestion lock.
        validation_error = _validate_params(request_json, ['workflowId'])
        if validation_error:
            return (validation_error, 400)
        workflow = request_json['workflowId']
        status = spanner.release_lock(workflow)
        if not status:
            return ('Failed to release lock', 500)
        return ('Lock released', 200)
    elif actionType == 'update_ingestion_status':
        # Updates the status of imports after ingestion.
        validation_error = _validate_params(request_json,
                                            ['importList', 'workflowId'])
        if validation_error:
            return (validation_error, 400)
        import_list = request_json['importList']
        workflow_id = request_json['workflowId']
        job_id = request_json['jobId']
        metrics = import_utils.get_ingestion_metrics(FLAGS.project_id,
                                                     FLAGS.location, job_id)
        spanner.update_ingestion_status(import_list, workflow_id, job_id,
                                        metrics)
        return ('Updated ingestion status', 200)
    elif actionType == 'update_import_status':
        # Updates the status of a specific import job.
        validation_error = _validate_params(request_json,
                                            ['importName', 'status'])
        if validation_error:
            return (validation_error, 400)
        import_name = request_json['importName']
        status = request_json['status']
        logging.info(f'Updating {import_name} {status}')
        params = import_utils.get_import_params(request_json)
        spanner.update_import_status(params)
        return (f"Updated import {import_name} to status {params['status']}",
                200)
    elif actionType == 'update_import_version':
        # Updates the version of an import and marks it as READY.
        validation_error = _validate_params(request_json,
                                            ['importName', 'version', 'reason'])
        if validation_error:
            return (validation_error, 400)
        import_name = request_json['importName']
        version = request_json['version']
        reason = request_json['reason']
        caller = import_utils.get_caller_identity(request)
        logging.info(
            f"[ImportVersionAuditLog] Import {import_name} version {version} caller: {caller} reason: {reason}"
        )
        if version == 'staging':
            version = storage.get_staging_version(import_name)
        summary = storage.get_import_summary(import_name, version)
        params = import_utils.create_import_params(summary)
        params['status'] = 'READY'
        storage.update_version_file(import_name, version)
        spanner.update_import_status(params)
        return (f'Updated import {import_name} to version {version}', 200)
    else:
        return (f'Unknown actionType: {actionType}', 400)
