import logging
import os
from absl import flags
from .helpers.aggregation_utils import AggregationUtils

FLAGS = flags.FLAGS

def handle_run_aggregation(request_json):
    """Runs aggregation logic for the specified imports."""
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
    )
    try:
        if aggregation.run_aggregation(import_list):
            return ('OK', 200)
        else:
            return ('Aggregation failed', 500)
    except Exception as e:
        return (f"Aggregation failed: {str(e)}", 500)
