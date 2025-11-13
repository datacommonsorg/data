import functions_framework
from spanner_client import SpannerClient
from flask import jsonify

_PROJECT_ID = 'datcom-store'
_SPANNER_INSTANCE_ID = 'dc-kg-test'
_SPANNER_DATABASE_ID = 'dc_graph_stable'


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
    spanner = SpannerClient(_PROJECT_ID, _SPANNER_INSTANCE_ID,
                            _SPANNER_DATABASE_ID)
    if actionType == 'get_import_list':
        imports = spanner.get_import_list()
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
        result = spanner.update_ingestion_status(import_list, workflow_id)
        if not result:
            return ('Failed to update ingestion status', 500)
        return ('Updated ingestion status', 200)
    elif actionType == 'update_import_status':
        validation_error = _validate_params(request_json, [
            'importName', 'jobId', 'status', 'schedule', 'duration', 'version'
        ])
        if validation_error:
            return (validation_error, 400)
        import_name = request_json['importName']
        status = request_json['status']
        job_id = request_json['jobId']
        duration = request_json['duration']
        version = request_json['version']
        schedule = request_json['schedule']
        result = spanner.update_import_status(import_name, status, job_id,
                                              duration, version, schedule)
        if not result:
            return ('Failed to update import status', 500)
        return ('Updated import status', 200)
    else:
        return (f'Unknown actionType: {actionType}', 400)
