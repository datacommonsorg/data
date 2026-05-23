import logging
from absl import flags
from .helpers.embedding_utils import get_latest_lock_timestamp, get_updated_nodes, filter_and_convert_nodes, generate_embeddings_partitioned

FLAGS = flags.FLAGS

def handle_embedding_ingestion(spanner, request_json):
    """Handles embedding ingestion."""
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
        nodes = get_updated_nodes(spanner.database, timestamp, node_types)
        converted_nodes = filter_and_convert_nodes(nodes)
        affected_rows = generate_embeddings_partitioned(spanner.database, converted_nodes)
        return (f"OK [Affected rows: {affected_rows}]", 200)
    except Exception as e:
        logging.error(f"Embedding ingestion failed: {e}")
        return (f"Error: {e}", 500)
