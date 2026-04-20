import os
import logging
from google.cloud import spanner
from embedding_utils import get_updated_nodes, filter_and_convert_nodes, generate_embeddings_partitioned

logging.basicConfig(level=logging.INFO)

def main():
    # Read configuration from environment variables
    instance_id = os.environ.get("SPANNER_INSTANCE")
    database_id = os.environ.get("SPANNER_DATABASE")
    project_id = os.environ.get("SPANNER_PROJECT")
    
    if not instance_id or not database_id:
        logging.error("SPANNER_INSTANCE or SPANNER_DATABASE environment variables not set.")
        exit(1)
        
    logging.info(f"Connecting to Spanner instance: {instance_id}, database: {database_id}, project: {project_id}")
    
    spanner_client = spanner.Client(project=project_id)
    instance = spanner_client.instance(instance_id)
    database = instance.database(database_id)

    node_types = ["StatisticalVariable", "Topic"]
    
    try:
        logging.info(f"Job started. Fetching all nodes for types: {node_types}")
        nodes = get_updated_nodes(database, None, node_types)
        
        converted_nodes = filter_and_convert_nodes(nodes)
        
        affected_rows = generate_embeddings_partitioned(database, converted_nodes)
        
        logging.info(f"Job completed successfully. Total affected rows: {affected_rows}")
    except Exception as e:
        logging.error(f"Job failed with error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
