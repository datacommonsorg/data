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
    def __init__(self, bq_client: bigquery.Client):
        self.bq_client = bq_client
        self.connection_id = "429015563165.us.dc_graph_2026_01_27_no_parallel"

    def aggregate_population(self, parent_place="geoId/06", date="2020"):
        """
        Aggregates population data for a specific parent place and date.
        """
        logging.info(f"Running place aggregation for {parent_place} on {date}")
        
        query = f"""
            SELECT * FROM EXTERNAL_QUERY(
              "{self.connection_id}",
              '''
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
              '''
            );
        """
        
        try:
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            output = []
            for row in results:
                output.append(dict(row))
            return output
            
        except Exception as e:
            logging.error(f"Failed to run place aggregation: {e}")
            raise e
