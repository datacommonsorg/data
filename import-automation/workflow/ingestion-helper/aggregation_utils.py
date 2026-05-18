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
from google.cloud import bigquery

logging.getLogger().setLevel(logging.INFO)

class BigQueryExecutor:
    """Handles low-level BigQuery client initialization and query execution."""
    def __init__(self):
        try:
            self.client = bigquery.Client()
        except Exception as e:
            logging.warning(f"Failed to initialize BigQuery client: {e}")
            self.client = None

    def execute(self, query, job_config=None):
        """Executes a query and waits for the result."""
        if not self.client:
             logging.error("BigQuery client not initialized")
             raise Exception("BigQuery client not initialized")
             
        logging.info(f"Executing query (first 100 chars): {query.strip()[:100]}...")
        query_job = self.client.query(query, job_config=job_config)
        return query_job.result()


class GraphAggregator:
    """Contains the specific business logic and SQL for graph-related recursive queries."""
    def __init__(self, executor: BigQueryExecutor):
        self.executor = executor

    def run_linked_contained_in_place(self):
        """Expands place containment hierarchies."""
        query = """
        CREATE OR REPLACE TEMPORARY TABLE `temp_cip` AS
        SELECT subject_id, object_id
        FROM `dc_graph_stable.Edge` 
        WHERE predicate = 'containedInPlace';

        EXPORT DATA
          OPTIONS( uri="https://spanner.googleapis.com/projects/datcom-store/instances/dc-kg-test/databases/dc_graph_2026_01_27",
            format='CLOUD_SPANNER',
            spanner_options = '{"table": "Edge"}' ) AS
        with RECURSIVE Ancestors AS (
          SELECT
            subject_id,
            object_id AS ancestor_place,
            1 AS level
          FROM
            temp_cip
          UNION ALL

          SELECT
            a.subject_id,
            t.object_id AS ancestor_place,
            a.level + 1
          FROM
            Ancestors AS a
          JOIN
            temp_cip AS t
            ON a.ancestor_place = t.subject_id
          WHERE
            a.level <= 10 -- Limit to 10 levels
        )
        SELECT DISTINCT
          subject_id,
          'linkedContainedInPlace' as predicate,
          ancestor_place as object_id,
          'dc/base/GeneratedGraphs' as provenance
        FROM
          Ancestors
        """
        self.executor.execute(query)

    def run_linked_member_of(self):
        """Expands membership hierarchies using memberOf and specializationOf."""
        query = """
        CREATE OR REPLACE TEMPORARY TABLE `temp_hierarchy` AS
        SELECT DISTINCT subject_id, predicate, object_id
        FROM `dc_graph_2026_01_27.Edge`
        WHERE predicate IN ('memberOf', 'specializationOf');

        EXPORT DATA
          OPTIONS( uri="https://spanner.googleapis.com/projects/datcom-store/instances/dc-kg-test/databases/dc_graph_2026_01_27",
            format='CLOUD_SPANNER',
            spanner_options = '{"table": "Edge"}' ) AS
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
        )
        SELECT DISTINCT
          subject_id,
          'linkedMemberOf' as predicate,
          ancestor as object_id,
          'dc/base/GeneratedGraphs' as provenance
        FROM
          Ancestors
        """
        self.executor.execute(query)

    def run_linked_member(self):
        """Expands topic/SVGP descendants to identify leaf members."""
        query = """
        CREATE OR REPLACE TEMPORARY TABLE `temp_topic_hierarchy` AS
        SELECT DISTINCT subject_id, object_id
        FROM `dc_graph_2026_01_27.Edge`
        WHERE predicate IN ('relevantVariable', 'member')
        AND (subject_id LIKE 'dc/topic%' OR subject_id LIKE 'dc/svpg%');

        EXPORT DATA
          OPTIONS( uri="https://spanner.googleapis.com/projects/datcom-store/instances/dc-kg-test/databases/dc_graph_2026_01_27",
            format='CLOUD_SPANNER',
            spanner_options = '{"table": "Edge"}' ) AS
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
        )
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
        """
        self.executor.execute(query)


class AggregationUtils:
    """Orchestrates the overall aggregation workflow."""
    def __init__(self):
        self.executor = BigQueryExecutor()
        self.graph_aggregator = GraphAggregator(self.executor)

    def run_aggregation(self, import_list):
        """
        Orchestrates standard per-import aggregations and custom modular aggregations.
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

            # 2. Run custom modular aggregations
            custom_aggregations = [
                self.graph_aggregator.run_linked_contained_in_place,
                self.graph_aggregator.run_linked_member_of,
                self.graph_aggregator.run_linked_member,
            ]
            
            for agg_func in custom_aggregations:
                logging.info(f"Running custom aggregation: {agg_func.__name__}")
                agg_func()
            
            return True

        except Exception as e:
            logging.error(f"Aggregation failed: {e}")
            raise e
