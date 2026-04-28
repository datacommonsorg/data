# Copyright 2026 Google LLC
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

import os
import logging
from google.cloud import spanner
from embedding_utils import get_latest_lock_timestamp, get_updated_nodes, filter_and_convert_nodes, generate_embeddings_partitioned

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
        timestamp = get_latest_lock_timestamp(database)
        nodes = get_updated_nodes(database, timestamp, node_types)
        
        converted_nodes = filter_and_convert_nodes(nodes)
        
        affected_rows = generate_embeddings_partitioned(database, converted_nodes)
        
        logging.info(f"Job completed successfully. Total affected rows: {affected_rows}")
    except Exception as e:
        logging.error(f"Job failed with error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
