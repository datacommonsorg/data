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

import logging
import os
import time
from typing import Any, Dict, List, Optional

from google.cloud import bigquery

logging.getLogger().setLevel(logging.INFO)

class BigQueryExecutor:
    """Handles BigQuery client initialization and query execution."""
    def __init__(self,
                 connection_id: Optional[str] = None,
                 project_id: Optional[str] = None,
                 instance_id: Optional[str] = None,
                 database_id: Optional[str] = None) -> None:
        self.connection_id = connection_id
        self.project_id = project_id
        self.instance_id = instance_id
        self.database_id = database_id
        try:
            self.client = bigquery.Client()
        except Exception as e:
            logging.warning(f"Failed to initialize BigQuery client: {e}")
            self.client = None

    def get_spanner_destination_uri(self) -> str:
        """Returns the Spanner destination URI for EXPORT DATA."""
        return f"https://spanner.googleapis.com/projects/{self.project_id}/instances/{self.instance_id}/databases/{self.database_id}"

    def execute(self, query: str, job_config: Optional[bigquery.QueryJobConfig] = None) -> bigquery.table.RowIterator:
        """Executes a query and returns the result."""
        if not self.client:
             logging.error("BigQuery client not initialized")
             raise RuntimeError("BigQuery client not initialized")
             
        start_time = time.time()
        logging.info(f"Executing query (first 100 chars): {query.strip()[:100]}...")
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            result = query_job.result()
            duration = time.time() - start_time
            logging.info(f"Query completed in {duration:.2f}s. Job ID: {query_job.job_id}")
            return result
        except Exception as e:
            logging.error(f"Query execution failed after {time.time() - start_time:.2f}s: {e}")
            raise


class GraphAggregator:
    """Contains the SQL global aggregation queries."""
    def __init__(self, executor: BigQueryExecutor) -> None:
        self.executor = executor


    def run_linked_contained_in_place(self) -> None:
        """Expands place containment hierarchies."""
        dest = self.executor.get_spanner_destination_uri()
        
        query = f"""
        -- Pull base edges needed for containedInPlace aggregation
        CREATE OR REPLACE TEMPORARY TABLE `temp_base_contained_in_place` AS
        SELECT * FROM EXTERNAL_QUERY("{self.executor.connection_id}", 
          "SELECT subject_id, predicate, object_id FROM Edge WHERE predicate = 'containedInPlace'");

        -- Pull existing generated edges to filter them out later
        CREATE OR REPLACE TEMPORARY TABLE `temp_existing_linked_contained_in_place` AS
        SELECT * FROM EXTERNAL_QUERY("{self.executor.connection_id}", 
          "SELECT subject_id, predicate, object_id, provenance FROM Edge WHERE predicate = 'linkedContainedInPlace'");

        CREATE OR REPLACE TEMPORARY TABLE `temp_contained_in_place` AS
        SELECT subject_id, object_id
        FROM `temp_base_contained_in_place`;

        EXPORT DATA
          OPTIONS( uri="{dest}",
            format='CLOUD_SPANNER',
            spanner_options = '{{"table": "Edge"}}' ) AS
        with RECURSIVE Ancestors AS (
          SELECT
            subject_id,
            object_id AS ancestor_place,
            1 AS level
          FROM
            temp_contained_in_place
          UNION ALL

          SELECT
            a.subject_id,
            t.object_id AS ancestor_place,
            a.level + 1
          FROM
            Ancestors AS a
          JOIN
            temp_contained_in_place AS t
            ON a.ancestor_place = t.subject_id
          WHERE
            a.level <= 10 -- Limit to 10 levels
        ),
        NewEdges AS (
          SELECT DISTINCT
            subject_id,
            'linkedContainedInPlace' as predicate,
            ancestor_place as object_id,
            'dc/base/GeneratedGraphs' as provenance
          FROM
            Ancestors
        ),
        FilteredEdges AS (
          SELECT
            subject_id,
            predicate,
            object_id,
            provenance
          FROM
            NewEdges n
          WHERE NOT EXISTS (
            SELECT 1
            FROM `temp_existing_linked_contained_in_place` e
            WHERE n.subject_id = e.subject_id
              AND n.predicate = e.predicate
              AND n.object_id = e.object_id
              AND n.provenance = e.provenance
          )
        )
        SELECT
          subject_id,
          predicate,
          object_id,
          provenance
        FROM
          FilteredEdges
        """
        self.executor.execute(query)

    def run_linked_member_of(self) -> None:
        """Expands membership hierarchies using memberOf and specializationOf."""
        dest = self.executor.get_spanner_destination_uri()

        query = f"""
        -- Pull base edges needed for memberOf aggregation
        CREATE OR REPLACE TEMPORARY TABLE `temp_base_member_of` AS
        SELECT * FROM EXTERNAL_QUERY("{self.executor.connection_id}", 
          "SELECT subject_id, predicate, object_id FROM Edge WHERE predicate IN ('memberOf', 'specializationOf')");

        -- Pull existing generated edges to filter them out later
        CREATE OR REPLACE TEMPORARY TABLE `temp_existing_linked_member_of` AS
        SELECT * FROM EXTERNAL_QUERY("{self.executor.connection_id}", 
          "SELECT subject_id, predicate, object_id, provenance FROM Edge WHERE predicate = 'linkedMemberOf'");

        CREATE OR REPLACE TEMPORARY TABLE `temp_hierarchy` AS
        SELECT DISTINCT subject_id, predicate, object_id
        FROM `temp_base_member_of`;

        EXPORT DATA
          OPTIONS( uri="{dest}",
            format='CLOUD_SPANNER',
            spanner_options = '{{"table": "Edge"}}' ) AS
        WITH RECURSIVE Ancestors AS (
          SELECT
            subject_id,
            object_id AS ancestor,
            1 AS level
          FROM
            temp_hierarchy
          WHERE
            predicate = 'memberOf'
          UNION ALL

          SELECT
            a.subject_id,
            t.object_id AS ancestor,
            a.level + 1
          FROM
            Ancestors AS a
          JOIN
            temp_hierarchy AS t
            ON a.ancestor = t.subject_id
          WHERE
            a.level <= 20 -- Limit to 20 levels
            AND t.predicate = 'specializationOf'
        ),
        NewEdges AS (
          SELECT DISTINCT
            subject_id,
            'linkedMemberOf' as predicate,
            ancestor as object_id,
            'dc/base/GeneratedGraphs' as provenance
          FROM
            Ancestors
        ),
        FilteredEdges AS (
          SELECT
            subject_id,
            predicate,
            object_id,
            provenance
          FROM
            NewEdges n
          WHERE NOT EXISTS (
            SELECT 1
            FROM `temp_existing_linked_member_of` e
            WHERE n.subject_id = e.subject_id
              AND n.predicate = e.predicate
              AND n.object_id = e.object_id
              AND n.provenance = e.provenance
          )
        )
        SELECT
          subject_id,
          predicate,
          object_id,
          provenance
        FROM
          FilteredEdges
        """
        self.executor.execute(query)

    def run_linked_member(self) -> None:
        """Expands topic/SVGP descendants to identify leaf members."""
        dest = self.executor.get_spanner_destination_uri()

        query = f"""
        -- Pull base edges needed for member aggregation
        CREATE OR REPLACE TEMPORARY TABLE `temp_base_member` AS
        SELECT * FROM EXTERNAL_QUERY("{self.executor.connection_id}", 
          "SELECT subject_id, predicate, object_id FROM Edge WHERE predicate IN ('relevantVariable', 'member')");

        -- Pull existing generated edges to filter them out later
        CREATE OR REPLACE TEMPORARY TABLE `temp_existing_linked_member` AS
        SELECT * FROM EXTERNAL_QUERY("{self.executor.connection_id}", 
          "SELECT subject_id, predicate, object_id, provenance FROM Edge WHERE predicate = 'linkedMember'");

        CREATE OR REPLACE TEMPORARY TABLE `temp_topic_hierarchy` AS
        SELECT DISTINCT subject_id, object_id
        FROM `temp_base_member`
        WHERE (subject_id LIKE 'dc/topic%' OR subject_id LIKE 'dc/svpg%');

        EXPORT DATA
          OPTIONS( uri="{dest}",
            format='CLOUD_SPANNER',
            spanner_options = '{{"table": "Edge"}}' ) AS
        WITH RECURSIVE Descendants AS (
          SELECT
            subject_id,
            object_id AS descendant,
            1 AS level
          FROM
            temp_topic_hierarchy
          UNION ALL

          SELECT
            d.subject_id,
            t.object_id AS descendant,
            d.level + 1
          FROM
            Descendants AS d
          JOIN
            temp_topic_hierarchy AS t
            ON d.descendant = t.subject_id
          WHERE
            d.level <= 20 -- Limit to 20 levels
        ),
        NewEdges AS (
          SELECT DISTINCT
            descendant as subject_id,
            'linkedMember' as predicate,
            subject_id as object_id,
            'dc/base/GeneratedGraphs' as provenance
          FROM
            Descendants
          WHERE subject_id LIKE 'dc/topic%'
          AND descendant NOT LIKE 'dc/topic%'
          AND descendant NOT LIKE 'dc/svpg%'
        ),
        FilteredEdges AS (
          SELECT
            subject_id,
            predicate,
            object_id,
            provenance
          FROM
            NewEdges n
          WHERE NOT EXISTS (
            SELECT 1
            FROM `temp_existing_linked_member` e
            WHERE n.subject_id = e.subject_id
              AND n.predicate = e.predicate
              AND n.object_id = e.object_id
              AND n.provenance = e.provenance
          )
        )
        SELECT
          subject_id,
          predicate,
          object_id,
          provenance
        FROM
          FilteredEdges
        """
        self.executor.execute(query)


class AggregationUtils:
    """Orchestrates the overall aggregation workflow."""
    def __init__(self, 
                 connection_id: Optional[str] = None) -> None:
        # Default connection ID
        if not connection_id:
            connection_id = os.environ.get(
                'SPANNER_CONNECTION_ID',
                "429015563165.us.dc_graph_2026_01_27_no_parallel"
            )

        # Spanner metadata
        project_id = os.environ.get('SPANNER_PROJECT_ID', 'datcom-store')
        instance_id = os.environ.get('SPANNER_INSTANCE_ID', 'dc-kg-test')
        database_id = os.environ.get('SPANNER_GRAPH_DATABASE_ID', 'dc_graph_2026_01_27')

        self.executor = BigQueryExecutor(
            connection_id=connection_id,
            project_id=project_id,
            instance_id=instance_id,
            database_id=database_id
        )
        self.graph_aggregator = GraphAggregator(self.executor)

    def run_aggregation(self, import_list: List[Dict[str, Any]]) -> bool:
        """
        Orchestrates standard per-import aggregations and global aggregations.
        """
        logging.info(f"Received request for importList: {import_list}")
        
        try:
            # 1. Run standard per-import aggregations
            for import_item in import_list:
                import_name = import_item.get('importName')
                if import_name:
                    query = "SELECT @import_name as import_name, CURRENT_TIMESTAMP() as execution_time"
                    job_config = bigquery.QueryJobConfig(query_parameters=[
                        bigquery.ScalarQueryParameter("import_name", "STRING", import_name),
                    ])
                    self.executor.execute(query, job_config=job_config)
                else:
                    logging.info('Skipping aggregation logic for empty importName')

            # 2. Run global aggregations
            global_aggregations = [
                self.graph_aggregator.run_linked_contained_in_place,
                self.graph_aggregator.run_linked_member_of,
                self.graph_aggregator.run_linked_member,
            ]
            
            for agg_func in global_aggregations:
                logging.info(f"Running global aggregation: {agg_func.__name__}")
                agg_func()
            
            return True

        except Exception as e:
            logging.error(f"Aggregation failed: {e}")
            raise e
