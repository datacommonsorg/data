import functions_framework
from spanner_client import SpannerClient
from storage_client import StorageClient
from flask import jsonify
import logging
import import_utils

logging.getLogger().setLevel(logging.INFO)

_PROJECT_ID = 'datcom-import-automation-prod'
_SPANNER_PROJECT_ID = 'datcom-store'
_SPANNER_INSTANCE_ID = 'dc-kg-test'
_SPANNER_DATABASE_ID = 'dc_graph_import'
_GCS_BUCKET_ID = 'datcom-prod-imports'
_LOCATION = 'us-central1'


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
    spanner = SpannerClient(_SPANNER_PROJECT_ID, _SPANNER_INSTANCE_ID,
                            _SPANNER_DATABASE_ID)
    storage = StorageClient(_GCS_BUCKET_ID)

    if actionType == 'get_import_list':
        import_list = request_json.get('importList', [])
        imports = spanner.get_import_list(import_list)
        return jsonify(imports)
    elif actionType == 'acquire_ingestion_lock':
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
        validation_error = _validate_params(request_json, ['workflowId'])
        if validation_error:
            return (validation_error, 400)
        workflow = request_json['workflowId']
        status = spanner.release_lock(workflow)
        if not status:
            return ('Failed to release lock', 500)
        return ('Lock released', 200)
    elif actionType == 'update_ingestion_status':
        validation_error = _validate_params(request_json,
                                            ['importList', 'workflowId'])
        if validation_error:
            return (validation_error, 400)
        import_list = request_json['importList']
        workflow_id = request_json['workflowId']
        job_id = request_json['jobId']
        metrics = import_utils.get_ingestion_metrics(_PROJECT_ID, _LOCATION,
                                                     job_id)
        spanner.update_ingestion_status(import_list, workflow_id, job_id,
                                        metrics)
        return ('Updated ingestion status', 200)
    elif actionType == 'update_import_status':
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
