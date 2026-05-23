import functions_framework
from spanner_client import SpannerClient
from storage_client import StorageClient

import logging
import os
from absl import flags

from flask import jsonify


logging.getLogger().setLevel(logging.INFO)

FLAGS = flags.FLAGS

flags.DEFINE_string('project_id', os.environ.get('PROJECT_ID'),
                    'GCP Project ID')
flags.DEFINE_string('spanner_project_id', os.environ.get('SPANNER_PROJECT_ID'),
                    'Spanner Project ID')
flags.DEFINE_string('spanner_instance_id',
                    os.environ.get('SPANNER_INSTANCE_ID'),
                    'Spanner Instance ID')
# Separate spanner DB for metadata and graph tables
# (to be merged into a single DB after testing).
flags.DEFINE_string('spanner_database_id',
                    os.environ.get('SPANNER_DATABASE_ID'),
                    'Spanner Database ID')
flags.DEFINE_string('spanner_graph_database_id',
                    os.environ.get('SPANNER_GRAPH_DATABASE_ID'),
                    'Spanner Graph Database ID')
flags.DEFINE_string('spanner_connection_id',
                    os.environ.get('BQ_SPANNER_CONN_ID'),
                    'BigQuery Connection ID to access Cloud Spanner')
flags.DEFINE_string('gcs_bucket_id', os.environ.get('GCS_BUCKET_ID'),
                    'GCS Bucket ID')
flags.DEFINE_string('location', os.environ.get('LOCATION') or os.environ.get('REGION'), 'Location')
flags.DEFINE_bool(
    'enable_embeddings',
    os.environ.get('ENABLE_EMBEDDINGS', 'false').lower() == 'true',
    'Enable embeddings')
flags.DEFINE_list(
    'node_types', ['StatisticalVariable', 'Topic'],
    'Node types to generate embeddings for')
flags.DEFINE_bool(
    'is_base_dc',
    os.environ.get('IS_BASE_DC', 'true').lower() == 'true',
    'Is base DC')

if not FLAGS.is_parsed():
    FLAGS(['ingestion_helper'])


def _validate_params(request_json, required_params):
    for param in required_params:
        if param not in request_json:
            return f"'{param}' parameter is missing"
    return None

_spanner_client = None
_storage_client = None

def _get_spanner_client():
    global _spanner_client
    if _spanner_client is None:
        _spanner_client = SpannerClient(
            FLAGS.spanner_project_id,
            FLAGS.spanner_instance_id,
            FLAGS.spanner_database_id,
            graph_database_id=FLAGS.spanner_graph_database_id,
            location=FLAGS.location,
            model_id=os.environ.get('EMBEDDING_MODEL_ID', 'text-embedding-005')
        )
    return _spanner_client

def _get_storage_client():
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient(FLAGS.gcs_bucket_id)
    return _storage_client


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

    action_type = request_json['actionType']
    spanner = _get_spanner_client()
    storage = _get_storage_client()

    if action_type == 'get_import_info':
        from handlers.imports import handle_get_import_info
        return handle_get_import_info(spanner, request_json)

    elif action_type == 'acquire_ingestion_lock':
        from handlers.lock import handle_acquire_lock
        return handle_acquire_lock(spanner, request_json)

    elif action_type == 'release_ingestion_lock':
        from handlers.lock import handle_release_lock
        return handle_release_lock(spanner, request_json)

    elif action_type == 'update_ingestion_status':
        from handlers.imports import handle_update_ingestion_status
        return handle_update_ingestion_status(spanner, request_json)

    elif action_type == 'update_import_status':
        from handlers.imports import handle_update_import_status
        return handle_update_import_status(spanner, storage, request_json)

    elif action_type == 'update_import_version':
        from handlers.imports import handle_update_import_version
        return handle_update_import_version(spanner, storage, request, request_json)

    elif action_type == 'initialize_database':
        from handlers.database import handle_initialize_database
        return handle_initialize_database(spanner, request_json)
    elif action_type == 'seed_database':
        from handlers.database import handle_seed_database
        return handle_seed_database(spanner)
    elif action_type == 'embedding_ingestion':
        from handlers.embeddings import handle_embedding_ingestion
        return handle_embedding_ingestion(spanner, request_json)
    elif action_type == 'run_aggregation':
        from handlers.aggregation import handle_run_aggregation
        return handle_run_aggregation(request_json)

    elif action_type == 'clear_redis_cache':
        from handlers.cache import handle_clear_redis_cache
        return handle_clear_redis_cache(request_json)

    else:
        return (f'Unknown actionType: {action_type}', 400)
