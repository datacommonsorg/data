import logging
import os
from flask import jsonify
from absl import flags
from .helpers import import_utils
from .utils import validate_params

FLAGS = flags.FLAGS

def handle_get_import_info(spanner, request_json):
    """Gets the details of imports that are ready for ingestion."""
    import_list = request_json.get('importList', [])
    import_info = spanner.get_import_info(import_list)
    return jsonify(import_info)

def handle_update_ingestion_status(spanner, request_json):
    """Updates the status of imports after ingestion."""
    validation_error = validate_params(
        request_json, ['importList', 'workflowId', 'jobId', 'status'])
    if validation_error:
        return (validation_error, 400)
        
    import_list = request_json['importList']
    workflow_id = request_json['workflowId']
    status = request_json['status']
    job_id = request_json['jobId']
    ingested_imports = [item['importName'] for item in import_list]

    spanner.update_ingestion_status(ingested_imports, workflow_id, status)
    metrics = import_utils.get_ingestion_metrics(FLAGS.project_id,
                                                 FLAGS.location, job_id)
    spanner.update_ingestion_history(workflow_id, job_id, ingested_imports,
                                     metrics)
    if status == 'SUCCESS':
        spanner.update_import_version_history(import_list, workflow_id)
    return ('OK', 200)

def handle_update_import_status(spanner, storage, request_json):
    """Updates the status of a specific import job."""
    validation_error = validate_params(request_json,
                                        ['importName', 'status'])
    if validation_error:
        return (validation_error, 400)
        
    import_name = request_json['importName']
    status = request_json['status']
    logging.info(f'Updating import {import_name} to status {status}')
    params = import_utils.get_import_params(request_json)
    next_refresh = import_utils.get_next_refresh(FLAGS.project_id,
                                                 FLAGS.location,
                                                 import_name)
    if next_refresh:
        params['next_refresh'] = next_refresh
    if status == 'STAGING':
        version = os.path.basename(request_json.get('latestVersion', ''))
        if not version:
            return (f'Empty version for import {import_name}', 500)
        storage.update_version_file(import_name, version, is_staging=True)
        storage.update_provenance_file(import_name, version)
        storage.update_import_summary(params)
        storage.update_version_file(import_name, version, is_staging=False)
        comment = f"import-workflow:{request_json.get('jobId','')}"
        spanner.update_version_history(import_name, version, comment)
    spanner.update_import_status(params)
    return ('OK', 200)

def handle_update_import_version(spanner, storage, request, request_json):
    """Updates the version and status of an import."""
    validation_error = validate_params(
        request_json, ['importName', 'version', 'comment'])
    if validation_error:
        return (validation_error, 400)
        
    import_name = request_json['importName']
    version = request_json['version']
    comment = request_json['comment']
    logging.info(
        f"Updating import {import_name} to version {version} comment:{comment}"
    )
    override = request_json.get('override', False)
    if version == 'STAGING':
        version = storage.get_staging_version(import_name)
    summary = storage.get_import_summary(import_name, version)
    params = import_utils.get_import_params(summary)
    if override:
        params['status'] = 'STAGING'
        caller = import_utils.get_caller_identity(request)
        comment = f'version-override:{caller} {comment}'
    if params['status'] == 'STAGING':
        storage.update_provenance_file(import_name, version)
        storage.update_version_file(import_name, version, is_staging=False)
        spanner.update_version_history(import_name, version, comment)
        logging.info(f"Updated import {import_name} to version {version}")
    else:
        logging.info(f"Skipping {import_name} version update")
    spanner.update_import_status(params)
    return (
        f"OK [Import: {import_name} Version: {version} Status: {params['status']}]",
        200)
