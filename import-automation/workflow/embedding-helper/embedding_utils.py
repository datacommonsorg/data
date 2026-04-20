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

"""Helper utilities for embedding workflows."""

import logging
import time
from datetime import datetime
from google.cloud.spanner_v1.param_types import TIMESTAMP, STRING, Array, Struct, StructField


def get_latest_lock_timestamp(database):
    """Gets the latest AcquiredTimestamp from IngestionLock table.
    
    Args:
        database: google.cloud.spanner.Database object.
        
    Returns:
        The latest AcquiredTimestamp as a datetime object, or None if no entries exist.
    """
    time_lock_sql = "SELECT MAX(AcquiredTimestamp) FROM IngestionLock"
    try:
        with database.snapshot() as snapshot:
            results = snapshot.execute_sql(time_lock_sql)
            for row in results:
                return row[0]
    except Exception as e:
        logging.error(f"Error fetching latest lock timestamp: {e}")
        raise
    return None

def get_updated_nodes(database, timestamp, node_types):
    """Gets subject_ids and names from Node table where update_timestamp > timestamp.
    
    Args:
        database: google.cloud.spanner.Database object.
        timestamp: datetime object to filter by.
        node_types: A list of strings representing the node types to filter by.
        
    Returns:
        A list of dictionaries containing subject_id and name.
    """
    if not timestamp:
        logging.info("No timestamp provided, reading all nodes.")
        updated_node_sql = """
            SELECT subject_id, name FROM Node 
            WHERE name IS NOT NULL
              AND EXISTS (
                SELECT 1 FROM UNNEST(types) AS t WHERE t IN UNNEST(@node_types)
              )
        """
        params = {"node_types": node_types}
        param_types = {"node_types": Array(STRING)}
    else:
        logging.info(f"Filtering nodes updated after {timestamp}")
        updated_node_sql = """
            SELECT subject_id, name FROM Node 
            WHERE update_timestamp > @timestamp
              AND name IS NOT NULL
              AND EXISTS (
                SELECT 1 FROM UNNEST(types) AS t WHERE t IN UNNEST(@node_types)
              )
        """
        params = {"timestamp": timestamp, "node_types": node_types}
        param_types = {"timestamp": TIMESTAMP, "node_types": Array(STRING)}
    
    nodes = []
    try:
        with database.snapshot() as snapshot:
            results = snapshot.execute_sql(updated_node_sql, params=params, param_types=param_types)
            fields = None
            for row in results:
                if fields is None:
                    fields = [field.name for field in results.fields]
                nodes.append(dict(zip(fields, row)))
    except Exception as e:
        logging.error(f"Error fetching updated nodes: {e}")
        raise
    return nodes


def filter_and_convert_nodes(nodes):
    """Filters out nodes without a name and converts dictionaries to tuples.
    Reads 'name' from input and maps it to output tuple.

    Args:
        nodes: A list of dictionaries containing subject_id and name.

    Returns:
        A list of tuples (subject_id, embedding_content).
    """
    valid_tuples = [
        (node.get("subject_id"), node.get("name"))
        for node in nodes
        if node.get("name")
    ]
    return valid_tuples


def generate_embeddings_partitioned(database, nodes):
    """Generates embeddings in batches using standard transactions.
    Processes nodes in chunks of 500 to avoid transaction size limits.
    
    Args:
        database: google.cloud.spanner.Database object.
        nodes: A list of tuples containing (subject_id, embedding_content).
        
    Returns:
        The number of affected rows.
    """
    if not nodes:
        logging.info("No nodes to update.")
        return 0

    BATCH_SIZE = 500
    total_rows_affected = 0

    logging.info(f"Generating embeddings for {len(nodes)} nodes in batches of {BATCH_SIZE}.")

    embeddings_sql = """
        INSERT OR UPDATE INTO NodeEmbeddings (subject_id, embedding_content, embeddings)
        SELECT subject_id, content, embeddings.values
        FROM ML.PREDICT(
            MODEL text_embeddings,
            (SELECT subject_id, embedding_content AS content, "RETRIEVAL_QUERY" AS task_type FROM UNNEST(@nodes))
        )
    """

    struct_type = Struct([
        StructField("subject_id", STRING),
        StructField("embedding_content", STRING)
    ])

    for i in range(0, len(nodes), BATCH_SIZE):
        batch = nodes[i : i + BATCH_SIZE]

        params = {"nodes": batch}
        param_types = {"nodes": Array(struct_type)}

        def _execute_dml(transaction):
            return transaction.execute_update(embeddings_sql, params=params, param_types=param_types, timeout=300)

        try:
            row_count = database.run_in_transaction(_execute_dml)
            total_rows_affected += row_count
            logging.info(f"Processed batch of {len(batch)} nodes. Affected {row_count} rows.")
            time.sleep(0.5)
        except Exception as e:
            logging.error(f"Error executing batch transaction: {e}")
            raise

    logging.info(f"Completed batch processing. Total affected rows: {total_rows_affected}")
    return total_rows_affected





