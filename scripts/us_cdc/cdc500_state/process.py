# Copyright 2026 Google LLC
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
"""Processes CDC 500 cities data into aggregated state-level health indicators."""

import os
from absl import app
from absl import flags
from absl import logging
from google.cloud import bigquery
import pandas as pd

_FLAGS = flags.FLAGS
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_OUTPUT_DIR = os.path.join(_MODULE_DIR, 'CDC500State_Output')

flags.DEFINE_string('output_dir', _DEFAULT_OUTPUT_DIR,
                    'Directory to write output CSV.')

QUERY = """
WITH cdc_sv AS (
  SELECT
    variable_measured AS cdc500,
    CASE
      WHEN variable_measured LIKE '%Female_50To74Years%' OR variable_measured LIKE '%50To74Years_Female%' THEN 'Count_Person_Female_50To74Years'
      WHEN variable_measured LIKE '%Female_21To65Years%' OR variable_measured LIKE '%21To65Years_Female%' THEN 'Count_Person_Female_21To65Years'
      WHEN variable_measured LIKE '%Female_65OrMoreYears%' OR variable_measured LIKE '%65OrMoreYears_Female%' THEN 'Count_Person_Female_65OrMoreYears'
      WHEN variable_measured LIKE '%Male_65OrMoreYears%' OR variable_measured LIKE '%65OrMoreYears_Male%' THEN 'Count_Person_Male_65OrMoreYears'
      WHEN variable_measured LIKE '%65OrMoreYears%' THEN 'Count_Person_65OrMoreYears'
      WHEN variable_measured LIKE '%18To64Years%' THEN 'Count_Person_18To64Years'
      WHEN variable_measured LIKE '%18OrMoreYears%' THEN 'Count_Person_18OrMoreYears'
      ELSE 'Count_Person'
    END AS pop_statvar
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
  INNER JOIN `datcom-store.spanner_dc_graph_prod_DEFAULT.TimeSeries` AS T
    ON O.variable_measured = T.variable_measured
    AND O.entity1 = T.entity1
    AND O.facet_id = T.facet_id
    AND T.provenance = 'dc/base/CDC500'
    AND T.variable_measured LIKE 'Percent_%'
  INNER JOIN cdc_sv
    ON O.variable_measured = cdc_sv.cdc500
  WHERE O.entity1 LIKE 'geoId/%'
    AND O.variable_measured LIKE 'Percent_%'
),

svo_count AS (
  SELECT
    O.variable_measured AS population_statvar,
    O.entity1 AS observation_about,
    O.date AS observation_date,
    O.value AS population
  FROM `datcom-store.spanner_dc_graph_prod_DEFAULT.Observation` AS O
  INNER JOIN `datcom-store.spanner_dc_graph_prod_DEFAULT.TimeSeries` AS T
    ON O.variable_measured = T.variable_measured
    AND O.entity1 = T.entity1
    AND O.facet_id = T.facet_id
    AND T.provenance = 'dc/base/CensusACS5YearSurvey'
  INNER JOIN (
    SELECT DISTINCT pop_statvar
    FROM cdc_sv
  ) AS pop
    ON O.variable_measured = pop.pop_statvar
  WHERE O.entity1 LIKE 'geoId/%'
)

SELECT 
  p.statvar, 
  SUBSTR(p.observation_about, 1, 8) AS observation_about,
  p.observation_date, 
  CONCAT('dcAggregate/', p.measurement_method) AS measurement_method,
  p.pop_statvar AS population_statvar,
  SAFE_DIVIDE(
    SUM(CAST(c.population AS FLOAT64) * CAST(p.percent AS FLOAT64)),
    SUM(CAST(c.population AS FLOAT64))
  ) AS percent
FROM svo_percent AS p
INNER JOIN svo_count AS c
  ON p.observation_about = c.observation_about
  AND p.observation_date = c.observation_date
  AND p.pop_statvar = c.population_statvar
GROUP BY 1, 2, 3, 4, 5
"""

def run_process(client: bigquery.Client, output_file: str) -> None:
    """Executes the BigQuery query and writes the resulting DataFrame to output_file."""
    logging.info("Running BigQuery aggregation query...")
    try:
        query_job = client.query(QUERY)
    except Exception as e:
        logging.error("Failed to submit BigQuery query: %s", e)
        raise

    logging.info("Fetching query results into dataframe...")
    try:
        df = query_job.to_dataframe()
    except Exception as e:
        logging.error("Failed to fetch query results into dataframe: %s", e)
        raise

    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    logging.info("Writing %d rows to %s", len(df), output_file)
    df.to_csv(output_file, index=False)

def main(argv):
    del argv  # Unused.
    client = bigquery.Client()
    output_file = os.path.join(_FLAGS.output_dir, 'CDC500State_Output.csv')
    run_process(client, output_file)

if __name__ == '__main__':
    app.run(main)
