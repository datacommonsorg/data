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

from google.cloud import bigquery
import logging

class PlaceAggregator:
    def __init__(self, bq_client: bigquery.Client, connection_id: str = "429015563165.us.dc_graph_2026_01_27_no_parallel"):
        self.bq_client = bq_client
        self.connection_id = connection_id

    def _run_external_query(self, query: str):
        """Helper method to run a query against Spanner via BigQuery External Query."""
        sql = f"""
            SELECT * FROM EXTERNAL_QUERY(
              "{self.connection_id}",
              '''
              {query}
              '''
            );
        """
        return self.bq_client.query(sql).result()

    def aggregate_states_to_country(self, parent_place="geoId/06", date="2020"):
        """
        Aggregates population data for a specific parent place and date.
        This is typically used for State to Country aggregation.
        """
        logging.info(f"Running place aggregation for {parent_place} on {date}")
        
        query = f"""
            SELECT 
                e.object_id AS parent_place, 
                ts.variable_measured, 
                svo.date, 
                SUM(CAST(svo.value AS FLOAT64)) AS aggregated_value 
            FROM StatVarObservation svo 
            JOIN TimeSeries ts ON svo.id = ts.id 
            JOIN TimeSeriesAttribute tsa_place ON ts.id = tsa_place.id AND tsa_place.property = 'observationAbout' 
            JOIN Edge e ON tsa_place.value = e.subject_id AND e.predicate = 'containedInPlace' 
            LEFT JOIN TimeSeriesAttribute tsa_method ON ts.id = tsa_method.id AND tsa_method.property = 'measurementMethod' 
            WHERE ts.variable_measured = 'Count_Person' 
              AND e.object_id = '{parent_place}' 
              AND LENGTH(tsa_place.value) = 11 
              AND svo.date = '{date}' 
              AND tsa_method.value = 'USDecennialCensus' 
            GROUP BY e.object_id, ts.variable_measured, svo.date
        """
        
        try:
            results = self._run_external_query(query)
            
            output = []
            for row in results:
                output.append(dict(row))
            return output
            
        except Exception as e:
            logging.error(f"Failed to run state to country aggregation: {e}")
            raise e

    def aggregate_counties_to_state(self, parent_place="geoId/06", date="2020", method="CensusACS5yrSurvey"):
        """
        Aggregates county population data to a state using an optimized multi-step approach.
        """
        logging.info(f"Running optimized County-to-State aggregation for {parent_place} on {date}")
        
        try:
            # Step 1: Fetch child IDs (Counties)
            logging.info("Step 1: Fetching County IDs...")
            step1_sql = f"""
                SELECT e.subject_id
                FROM Edge e
                JOIN Node n ON e.subject_id = n.subject_id
                WHERE e.predicate = 'containedInPlace'
                  AND e.object_id = '{parent_place}'
                  AND 'County' IN UNNEST(n.types)
            """
            child_ids = [row.subject_id for row in self._run_external_query(step1_sql)]
            
            if not child_ids:
                logging.warning(f"No counties found for state {parent_place}")
                return []

            # Step 2: Fetch TimeSeries IDs
            logging.info(f"Step 2: Fetching TimeSeries IDs for {len(child_ids)} counties...")
            ids_str = ",".join([f"'{i}'" for i in child_ids])
            step2_sql = f"""
                SELECT tsa1.id 
                FROM TimeSeriesAttribute tsa1 
                JOIN TimeSeriesAttribute tsa2 ON tsa1.id = tsa2.id 
                JOIN TimeSeries ts ON tsa1.id = ts.id 
                WHERE tsa1.property = 'observationAbout' 
                  AND tsa1.value IN ({ids_str})
                  AND tsa2.property = 'measurementMethod' 
                  AND tsa2.value = '{method}' 
                  AND ts.variable_measured = 'Count_Person'
            """
            ts_ids = [row.id for row in self._run_external_query(step2_sql)]
            
            if not ts_ids:
                logging.warning("No TimeSeries IDs found for counties.")
                return []

            # Step 3: Final Aggregation
            logging.info(f"Step 3: Calculating aggregated value for {len(ts_ids)} TimeSeries...")
            ts_ids_str = ",".join([f"'{i}'" for i in ts_ids])
            step3_sql = f"""
                SELECT 
                    '{parent_place}' AS parent_place, 
                    'Count_Person' AS variable_measured,
                    date, 
                    SUM(CAST(value AS FLOAT64)) AS aggregated_value 
                FROM StatVarObservation 
                WHERE id IN ({ts_ids_str})
                  AND date = '{date}' 
                GROUP BY date
            """
            
            results = self._run_external_query(step3_sql)
            
            output = []
            for row in results:
                output.append(dict(row))
            return output
            
        except Exception as e:
            logging.error(f"Failed to run County-to-State aggregation: {e}")
            raise e
