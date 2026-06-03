import functions_framework
from spanner_client import SpannerClient
from storage_client import StorageClient
from embedding_utils import get_latest_lock_timestamp, get_updated_nodes, filter_and_convert_nodes, generate_embeddings_partitioned
import logging
import os
from absl import flags
import import_utils
from flask import jsonify
from aggregation_utils import AggregationUtils

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
flags.DEFINE_integer(
    'timeout', int(os.environ.get('TIMEOUT', 1700)),
    'Timeout in seconds for spanner client to execute queries')

if not FLAGS.is_parsed():
    FLAGS(['ingestion_helper'])


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

    action_type = request_json['actionType']
    spanner = SpannerClient(FLAGS.spanner_project_id,
                            FLAGS.spanner_instance_id,
                            FLAGS.spanner_database_id,
                            graph_database_id=FLAGS.spanner_graph_database_id,
                            location=FLAGS.location,
                            model_id=os.environ.get('EMBEDDING_MODEL_ID',
                                                    'text-embedding-005'))
    storage = StorageClient(FLAGS.gcs_bucket_id)

    if action_type == 'get_import_info':
        # Gets the details of imports that are ready for ingestion.
        # Input:
        #   importList: list of import names to ingest (optional)
        import_list = request_json.get('importList', [])
        import_info = spanner.get_import_info(import_list)
        return jsonify(import_info)

    elif action_type == 'acquire_ingestion_lock':
        # Attempts to acquire the global lock for ingestion.
        # Input:
        #   workflowId: ID of the workflow acquiring the lock
        #   timeout: lock duration in seconds
        validation_error = _validate_params(request_json,
                                            ['workflowId', 'timeout'])
        if validation_error:
            return (validation_error, 400)
        workflow = request_json['workflowId']
        timeout = request_json['timeout']
        status = spanner.acquire_lock(workflow, timeout)
        if not status:
            return ('Failed to acquire lock', 500)
        return ('OK', 200)

    elif action_type == 'release_ingestion_lock':
        # Releases the global ingestion lock.
        # Input:
        #   workflowId: ID of the workflow releasing the lock
        validation_error = _validate_params(request_json, ['workflowId'])
        if validation_error:
            return (validation_error, 400)
        workflow = request_json['workflowId']
        status = spanner.release_lock(workflow)
        if not status:
            return ('Failed to release lock', 500)
        return ('OK', 200)

    elif action_type == 'update_ingestion_status':
        # Updates the status of imports after ingestion.
        # Input:
        #   importList: list of import names
        #   workflowId: ID of the workflow
        #   status: import status
        #   jobId: Dataflow job ID
        validation_error = _validate_params(
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

    elif action_type == 'update_import_status':
        # Updates the status of a specific import job.
        # Input:
        #   importName: name of the import
        #   status: new status
        #   jobId: Batch job ID (optional)
        #   executionTime: execution time in seconds (optional)
        #   dataVolume: data volume in bytes (optional)
        #   latestVersion: latest version string (optional)
        #   graphPath: graph path regex (optional)
        #   nextRefresh: next refresh timestamp (optional)
        validation_error = _validate_params(request_json,
                                            ['importName', 'status'])
        if validation_error:
            return (validation_error, 400)
        import_name = request_json['importName']
        status = request_json['status']
        logging.info(f'Updating import {import_name} to status {status}')
        params = import_utils.get_import_params(request_json)
        next_refresh = None
        if FLAGS.is_base_dc:
            next_refresh = import_utils.get_next_refresh(FLAGS.project_id, FLAGS.location, import_name)

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

    elif action_type == 'update_import_version':
        # Updates the version and status of an import.
        # Input:
        #   importName: name of the import
        #   version: version string
        #   comment: audit log comment
        #   override: override status check (optional)
        #   triggerIngestion: trigger ingestion workflow (optional)
        validation_error = _validate_params(
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

    elif action_type == 'initialize_database':
        # Initializes the database by creating all required tables and proto bundles.
        logging.info("Action: initialize_database")
        spanner.initialize_database()
        return ('OK', 200)
    elif action_type == 'seed_database':
        # Seeds the database with base empty nodes.
        logging.info("Action: seed_database")
        spanner.seed_database()
        return ('OK', 200)
    elif action_type == 'embedding_ingestion':

        logging.info("Action: embedding_ingestion")
        enable_embeddings = request_json.get('enableEmbeddings',
                                             FLAGS.enable_embeddings)
        if not enable_embeddings:
            logging.info("Embeddings not enabled, skipping.")
            return ('Invalid request on embedding ingestion.', 400)
            
        node_types = FLAGS.node_types
        try:
            logging.info(f"Job started. Fetching all nodes for types: {node_types}")
            timestamp = get_latest_lock_timestamp(spanner.database)
            nodes = get_updated_nodes(spanner.database, timestamp, node_types, timeout=FLAGS.timeout)
            converted_nodes = filter_and_convert_nodes(nodes)
            affected_rows = generate_embeddings_partitioned(spanner.database, converted_nodes, timeout=FLAGS.timeout)
            return (f"OK [Affected rows: {affected_rows}]", 200)
        except Exception as e:
            logging.error(f"Embedding ingestion failed: {e}")
            return (f"Error: {e}", 500)
    elif action_type == 'run_aggregation':
        # Runs aggregation logic for the specified imports.
        # Input:
        #   importList: list of imports to aggregate
        import_list = request_json.get('importList', [])
        
        # Validate required flags are not empty or None
        missing_flags = []
        if not FLAGS.spanner_connection_id:
            missing_flags.append('spanner_connection_id (BQ_SPANNER_CONN_ID)')
        if not FLAGS.spanner_project_id:
            missing_flags.append('spanner_project_id (SPANNER_PROJECT_ID)')
        if not FLAGS.spanner_instance_id:
            missing_flags.append('spanner_instance_id (SPANNER_INSTANCE_ID)')
        if not FLAGS.spanner_graph_database_id:
            missing_flags.append('spanner_graph_database_id (SPANNER_GRAPH_DATABASE_ID)')
            
        if missing_flags:
            error_msg = f"Missing required configuration flags/env-vars: {', '.join(missing_flags)}"
            logging.error(error_msg)
            return (error_msg, 400)

        aggregation = AggregationUtils(
            connection_id=FLAGS.spanner_connection_id,
            project_id=FLAGS.spanner_project_id,
            instance_id=FLAGS.spanner_instance_id,
            database_id=FLAGS.spanner_graph_database_id,
            location=FLAGS.location,
            is_base_dc=FLAGS.is_base_dc,
        )
        try:
            if aggregation.run_aggregation(import_list):
                return ('OK', 200)
            else:
                return ('Aggregation failed', 500)
        except Exception as e:
            return (f"Aggregation failed: {str(e)}", 500)

    elif action_type == 'clear_redis_cache':
        logging.info("Action: clear_redis_cache")
        redis_host = os.environ.get("REDIS_HOST")
        redis_port = os.environ.get("REDIS_PORT", "6379")
        if redis_host:
            try:
                import redis
                r = redis.Redis(host=redis_host, port=int(redis_port))
                r.flushall(asynchronous=True)
                logging.info(f"Redis cache at {redis_host}:{redis_port} flushed successfully (async).")
                return jsonify({'status': 'SUCCESS', 'message': 'Cache cleared'}), 200
            except Exception as e:
                logging.error(f"Failed to flush Redis cache: {e}")
                return jsonify({'status': 'ERROR', 'message': str(e)}), 500
        else:
            logging.warning("REDIS_HOST not set, skipping cache flush.")
            return jsonify({'status': 'SKIPPED', 'message': 'REDIS_HOST not set'}), 200

    else:
        return (f'Unknown actionType: {action_type}', 400)
