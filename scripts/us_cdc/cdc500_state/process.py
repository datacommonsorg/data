# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from absl import logging
from google.cloud import bigquery

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_OUTPUT_FILE_PATH = os.path.join(_MODULE_DIR + '/CDC500State_Output')
if not os.path.exists(_OUTPUT_FILE_PATH):
    os.mkdir(_OUTPUT_FILE_PATH)

query = """
WITH cdc_sv AS (
  SELECT
    variable_measured AS cdc500,
    CONCAT('Count_', REGEXP_SUBSTR(variable_measured, '(Person_.*ale|Person_.*Years|Person)')) AS pop_statvar
  FROM `datcom-store.spanner_dc_graph_prod_DEFAULT.TimeSeries`
  WHERE provenance = 'dc/base/CDC500'
    AND variable_measured LIKE 'Percent_%'
  GROUP BY cdc500, pop_statvar
),
svo_percent AS (
  SELECT
    O.variable_measured AS statvar,
    O.entity1 AS observation_about,
    O.date AS observation_date,
    O.value AS percent,
    T.measurement_method AS measurement_method,
    cdc_sv.pop_statvar
  FROM `datcom-store.spanner_dc_graph_prod_DEFAULT.Observation` AS O
  JOIN `datcom-store.spanner_dc_graph_prod_DEFAULT.TimeSeries` AS T
    ON O.variable_measured = T.variable_measured
    AND O.entity1 = T.entity1
    AND O.facet_id = T.facet_id
  JOIN cdc_sv ON O.variable_measured = cdc_sv.cdc500
  WHERE O.entity1 LIKE 'geoId/%'
),
svo_count AS (
  SELECT
    variable_measured AS population_statvar,
    entity1 AS observation_about,
    date AS observation_date,
    value AS population
  FROM `datcom-store.spanner_dc_graph_prod_DEFAULT.Observation`
  WHERE entity1 LIKE 'geoId/%'
    AND variable_measured IN (SELECT DISTINCT pop_statvar FROM cdc_sv)
)
SELECT DISTINCT * FROM (
  SELECT 
    statvar, 
    SUBSTR(observation_about, 0, 8) AS observation_about,
    observation_date, 
    CONCAT('dcAggregate/', measurement_method) AS measurement_method,
    population_statvar,
    SUM(CAST(pop_count AS FLOAT64)) * 100 / SUM(CAST(population AS FLOAT64)) AS percent
  FROM (
    SELECT
      p.statvar,
      p.observation_about,
      p.observation_date,
      p.percent,
      p.measurement_method,
      c.population_statvar,
      c.population,
      CAST(c.population AS FLOAT64) * CAST(p.percent AS FLOAT64) / 100 AS pop_count
    FROM svo_percent AS p
    JOIN svo_count AS c
      ON p.observation_about = c.observation_about
      AND p.observation_date = c.observation_date
      AND p.pop_statvar = c.population_statvar
  )
  GROUP BY 1, 2, 3, 4, 5
)
"""

client = bigquery.Client()
try:
    logging.info("Running the query")
    query_job = client.query(query)
except Exception as e:
    logging.fatal(f"Error faced while running the query {e}")
try:
    logging.info("Converting to dataframe")
    results = query_job.to_dataframe()
except Exception as e:
    logging.info(f"Error faced while fetching results: {e}")

logging.info("Writing output to CSV")
output_file = os.path.join(_OUTPUT_FILE_PATH + "/CDC500State_Output.csv")
results.to_csv(output_file, index=False)
