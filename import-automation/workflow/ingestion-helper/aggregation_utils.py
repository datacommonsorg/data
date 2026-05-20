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
            self.client = bigquery.Client(project=self.project_id)
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


class PrecomputedEdgeIngester:
    """Computes and ingests pre-computed edges (e.g., transitive closures) into Spanner for faster lookup."""
    def __init__(self, executor: BigQueryExecutor) -> None:
        self.executor = executor

    def run_all(self, import_names: List[str] = None) -> None:
        """Runs all global aggregations in sequence."""
        if not import_names:
            logging.info("No imports specified. Skipping global aggregations.")
            return

        logging.info(f"Running global aggregations for imports: {import_names}")
        
        # TODO: Run these methods in parallel to speed up execution since they are independent.
        self.run_linked_contained_in_place(import_names)
        self.run_linked_member_of(import_names)
        self.run_linked_member(import_names)


    def run_linked_contained_in_place(self, import_names: List[str] = None) -> None:
        """Expands place containment hierarchies."""
        if not import_names:
            return

        dest = self.executor.get_spanner_destination_uri()
        provenances = [f"'dc/base/{name}'" for name in import_names]
        provenance_filter = f" AND provenance IN ({', '.join(provenances)})"
        
        query = f"""
        -- Pull base edges needed for containedInPlace aggregation
        CREATE OR REPLACE TEMPORARY TABLE `temp_base_contained_in_place` AS
        SELECT * FROM EXTERNAL_QUERY("{self.executor.connection_id}", 
          "SELECT subject_id, predicate, object_id FROM Edge WHERE predicate = 'containedInPlace'{provenance_filter}");

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

    def run_linked_member_of(self, import_names: List[str] = None) -> None:
        """Expands membership hierarchies using memberOf and specializationOf."""
        if not import_names:
            return

        dest = self.executor.get_spanner_destination_uri()
        provenances = [f"'dc/base/{name}'" for name in import_names]
        provenance_filter = f" AND provenance IN ({', '.join(provenances)})"

        query = f"""
        -- Pull base edges needed for memberOf aggregation
        CREATE OR REPLACE TEMPORARY TABLE `temp_base_member_of` AS
        SELECT * FROM EXTERNAL_QUERY("{self.executor.connection_id}", 
          "SELECT subject_id, predicate, object_id FROM Edge WHERE predicate IN ('memberOf', 'specializationOf'){provenance_filter}");

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

    def run_linked_member(self, import_names: List[str] = None) -> None:
        """Expands topic/SVGP descendants to identify leaf members."""
        if not import_names:
            return

        dest = self.executor.get_spanner_destination_uri()
        provenances = [f"'dc/base/{name}'" for name in import_names]
        provenance_filter = f" AND provenance IN ({', '.join(provenances)})"

        query = f"""
        -- Pull base edges needed for member aggregation
        CREATE OR REPLACE TEMPORARY TABLE `temp_base_member` AS
        SELECT * FROM EXTERNAL_QUERY("{self.executor.connection_id}", 
          "SELECT subject_id, predicate, object_id FROM Edge WHERE predicate IN ('relevantVariable', 'member'){provenance_filter}");

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


class CacheAggregator:
    """Contains the SQL queries for Cache table aggregations."""
    def __init__(self, executor: BigQueryExecutor) -> None:
        self.executor = executor

    def run_all(self, import_names: List[str]) -> None:
        """Runs all cache aggregations in sequence."""
        if not import_names:
            logging.info("No imports specified. Skipping cache aggregations.")
            return

        logging.info(f"Running cache aggregations for imports: {import_names}")
        self.run_provenance_summary_aggregation(import_names)

    def run_provenance_summary_aggregation(self, import_names: List[str]) -> None:
        """Calculates ProvenanceSummary for all variables and populates the Cache table."""
        if not import_names:
            return

        dest = self.executor.get_spanner_destination_uri()
        connection_id = self.executor.connection_id
        
        # Format import names for the SQL IN clause
        imports_str = ", ".join([f"'{name}'" for name in import_names])
        
        query = f"""
        -- Step 1: Fetch Observation rows for the specific import
        -- We cast 'observations' to STRING to avoid the PROTO error.
        CREATE OR REPLACE TEMPORARY TABLE `temp_obs_raw` AS
        SELECT 
          variable_measured, 
          observation_about, 
          facet_id, 
          import_name,
          observation_period,
          measurement_method,
          unit,
          scaling_factor,
          is_dc_aggregate,
          observations_json
        FROM EXTERNAL_QUERY("{connection_id}", 
          '''SELECT 
               variable_measured, 
               observation_about, 
               facet_id, 
               import_name,
               observation_period,
               measurement_method,
               unit,
               scaling_factor,
               is_dc_aggregate,
               CAST(observations AS STRING) as observations_json
             FROM Observation
             WHERE import_name IN ({imports_str}) ''');

        -- Step 2: Fetch ALL Node names (Narrow selection to reduce data transfer)
        CREATE OR REPLACE TEMPORARY TABLE `temp_node_names` AS
        SELECT subject_id, name 
        FROM EXTERNAL_QUERY("{connection_id}",
          "SELECT subject_id, name FROM Node WHERE name IS NOT NULL");

        -- Step 3: Fetch ALL typeOf edges (Narrow selection)
        CREATE OR REPLACE TEMPORARY TABLE `temp_type_edges` AS
        SELECT subject_id, object_id as place_type
        FROM EXTERNAL_QUERY("{connection_id}", 
          "SELECT subject_id, object_id FROM Edge WHERE predicate = 'typeOf'");

        -- Step 4: Join and Flatten in BigQuery
        CREATE OR REPLACE TEMPORARY TABLE `temp_prepared` AS
        SELECT 
          raw.variable_measured,
          raw.observation_about,
          raw.facet_id,
          raw.import_name,
          raw.observation_period,
          raw.measurement_method,
          raw.unit,
          raw.scaling_factor,
          raw.is_dc_aggregate,
          JSON_VALUE(v, '$.key') as date_val,
          SAFE_CAST(JSON_VALUE(v, '$.value') AS FLOAT64) as value_num,
          CONCAT('dc/base/', raw.import_name) as provenance_dcid,
          nodes.name as place_name,
          edges.place_type
        FROM `temp_obs_raw` raw
        CROSS JOIN UNNEST(JSON_EXTRACT_ARRAY(SAFE.PARSE_JSON(observations_json), '$.values')) as v
        LEFT JOIN `temp_node_names` nodes ON raw.observation_about = nodes.subject_id
        LEFT JOIN `temp_type_edges` edges ON raw.observation_about = edges.subject_id;

        -- Step 5: Aggregate Place Type Summaries
        CREATE OR REPLACE TEMPORARY TABLE `temp_place_type_summary` AS
        SELECT
          variable_measured,
          provenance_dcid,
          facet_id,
          place_type,
          COUNT(DISTINCT observation_about) as place_count,
          MIN(value_num) as min_val,
          MAX(value_num) as max_val,
          ARRAY_AGG(
            STRUCT(observation_about as dcid, place_name as name)
            ORDER BY observation_about LIMIT 3
          ) as top_places
        FROM `temp_prepared`
        WHERE place_type IS NOT NULL
        GROUP BY variable_measured, provenance_dcid, facet_id, place_type;

        -- Step 6: Final aggregation and export to Cache
        EXPORT DATA
          OPTIONS( uri="{dest}",
            format='CLOUD_SPANNER',
            spanner_options = '{{"table": "Cache"}}' ) AS
        WITH facet_base AS (
          SELECT 
            variable_measured, provenance_dcid, facet_id,
            ANY_VALUE(import_name) as import_name,
            ANY_VALUE(measurement_method) as measurement_method,
            ANY_VALUE(observation_period) as observation_period,
            ANY_VALUE(unit) as unit,
            ANY_VALUE(scaling_factor) as scaling_factor,
            ANY_VALUE(is_dc_aggregate) as is_dc_aggregate,
            MIN(date_val) as min_date,
            MAX(date_val) as max_date,
            MIN(value_num) as facet_min,
            MAX(value_num) as facet_max,
            COUNT(*) as facet_obs_count,
            COUNT(DISTINCT observation_about) as facet_ts_count
          FROM `temp_prepared`
          GROUP BY variable_measured, provenance_dcid, facet_id
        ),
        facet_summaries AS (
          SELECT 
            fb.variable_measured,
            fb.provenance_dcid,
            fb.facet_id,
            fb.import_name,
            fb.measurement_method,
            fb.observation_period,
            fb.unit,
            fb.scaling_factor,
            fb.is_dc_aggregate,
            fb.min_date,
            fb.max_date,
            fb.facet_min,
            fb.facet_max,
            fb.facet_obs_count,
            fb.facet_ts_count,
            ARRAY_AGG(STRUCT(pts.place_type, pts.place_count, pts.min_val, pts.max_val, pts.top_places)) as pt_summaries
          FROM facet_base fb
          LEFT JOIN `temp_place_type_summary` pts USING (variable_measured, provenance_dcid, facet_id)
          GROUP BY 
            variable_measured, provenance_dcid, facet_id, import_name, measurement_method,
            observation_period, unit, scaling_factor, is_dc_aggregate, min_date, max_date,
            facet_min, facet_max, facet_obs_count, facet_ts_count
        )
        SELECT
          'ProvenanceSummary' as type,
          variable_measured as key,
          provenance_dcid as provenance,
          JSON_OBJECT(
            'import_name', ANY_VALUE(import_name),
            'observation_count', CAST(SUM(facet_obs_count) AS FLOAT64),
            'time_series_count', CAST(SUM(facet_ts_count) AS FLOAT64),
            'series_summary', ARRAY_AGG(
              JSON_OBJECT(
                'series_key', JSON_OBJECT(
                  'measurement_method', measurement_method,
                  'observation_period', observation_period,
                  'unit', unit,
                  'scaling_factor', scaling_factor,
                  'is_dc_aggregate', COALESCE(is_dc_aggregate, false)
                ),
                'earliest_date', min_date,
                'latest_date', max_date,
                'min_value', facet_min,
                'max_value', facet_max,
                'observation_count', CAST(facet_obs_count AS FLOAT64),
                'time_series_count', CAST(facet_ts_count AS FLOAT64),
                'place_type_summary', (
                  SELECT JSON_OBJECT(
                    ARRAY_AGG(place_type),
                    ARRAY_AGG(JSON_OBJECT(
                      'place_count', place_count,
                      'min_value', min_val,
                      'max_value', max_val,
                      'top_places', (
                        SELECT ARRAY_AGG(JSON_OBJECT('dcid', tp.dcid, 'name', tp.name))
                        FROM UNNEST(top_places) tp
                      )
                    ))
                  )
                  FROM UNNEST(pt_summaries)
                  WHERE place_type IS NOT NULL
                )
              )
            )
          ) as value
        FROM facet_summaries
        GROUP BY variable_measured, provenance_dcid;
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
        database_id = os.environ.get('SPANNER_GRAPH_DATABASE_ID', 'dc_graph_2025_11_07')

        self.executor = BigQueryExecutor(
            connection_id=connection_id,
            project_id=project_id,
            instance_id=instance_id,
            database_id=database_id
        )
        self.precomputed_edge_ingester = PrecomputedEdgeIngester(self.executor)
        self.cache_aggregator = CacheAggregator(self.executor)

    def run_aggregation(self, import_list: List[Dict[str, Any]]) -> bool:
        """
        Orchestrates standard per-import aggregations and global aggregations.
        """
        logging.info(f"Received request for importList: {import_list}")
        
        try:
            import_names = []
            # 1. Run standard per-import aggregations
            for import_item in import_list:
                import_name = import_item.get('importName')
                if import_name:
                    import_names.append(import_name)
                    query = "SELECT @import_name as import_name, CURRENT_TIMESTAMP() as execution_time"
                    job_config = bigquery.QueryJobConfig(query_parameters=[
                        bigquery.ScalarQueryParameter("import_name", "STRING", import_name),
                    ])
                    self.executor.execute(query, job_config=job_config)
                else:
                    logging.info('Skipping aggregation logic for empty importName')

            # 2. Run global aggregations
            self.precomputed_edge_ingester.run_all(import_names)
            self.cache_aggregator.run_all(import_names)
            
            return True

        except Exception as e:
            logging.error(f"Aggregation failed: {e}")
            raise e
