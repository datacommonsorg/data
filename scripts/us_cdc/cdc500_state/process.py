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

_FLAGS = flags.FLAGS
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_OUTPUT_DIR = os.path.join(_MODULE_DIR, 'CDC500State_Output')
DEFAULT_BQ_TIMEOUT_SECONDS = 600

flags.DEFINE_string('output_dir', _DEFAULT_OUTPUT_DIR,
                    'Directory to write output CSV.')
flags.DEFINE_string(
    'project', None,
    'GCP project ID for BigQuery. Defaults to ambient environment if omitted.')
flags.DEFINE_integer('timeout', DEFAULT_BQ_TIMEOUT_SECONDS,
                     'Timeout in seconds for BigQuery query and download.')

QUERY = """
WITH cdc_sv AS (
  SELECT
    variable_measured AS cdc500,
    CASE
      WHEN REGEXP_CONTAINS(
        variable_measured, r'65OrMoreYears.*Female'
      ) THEN 'Count_Person_65OrMoreYears_Female'
      WHEN REGEXP_CONTAINS(
        variable_measured, r'65OrMoreYears.*Male'
      ) THEN 'Count_Person_65OrMoreYears_Male'
      WHEN variable_measured LIKE '%65OrMoreYears%' THEN 'Count_Person_65OrMoreYears'
      WHEN variable_measured LIKE '%18To64Years%' THEN 'Count_Person_18To64Years'
      WHEN variable_measured LIKE '%18OrMoreYears%' THEN 'Count_Person_18OrMoreYears'
      ELSE 'Count_Person'
    END AS pop_statvar
  FROM `datcom-store.spanner_dc_graph_prod_DEFAULT.TimeSeries`
  WHERE provenance = 'dc/base/CDC500'
    AND variable_measured LIKE 'Percent_%'
    AND variable_measured NOT IN (
      'Percent_Person_50To74Years_Female_ReceivedMammography',
      'Percent_Person_21To65Years_Female_ReceivedCervicalCancerScreening',
      'Percent_Person_21To65Years_Female_ReceivedPapSmearTest',
      'Percent_Person_50To75Years_ReceivedColorectalCancerScreening'
    )
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
  INNER JOIN cdc_sv
    ON O.variable_measured = cdc_sv.cdc500
  WHERE O.entity1 LIKE 'geoId/%'
    AND (
      LENGTH(O.entity1) = 13
      OR (
        O.entity1 = 'geoId/15003'
        AND (
          O.date <= '2016'
          OR (
            O.date = '2017'
            AND NOT REGEXP_CONTAINS(
              O.variable_measured, r'HighBloodPressure|Cholesterol'
            )
          )
        )
      )
    )
    AND SAFE_CAST(O.value AS FLOAT64) IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY O.variable_measured, O.entity1, O.date, T.measurement_method
    ORDER BY O.last_update_timestamp DESC, O.facet_id DESC
  ) = 1
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
    AND (LENGTH(O.entity1) = 13 OR O.entity1 = 'geoId/15003')
    AND SAFE_CAST(O.value AS FLOAT64) IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY O.variable_measured, O.entity1, O.date
    ORDER BY O.last_update_timestamp DESC, O.facet_id DESC
  ) = 1
)

SELECT
  p.statvar,
  SUBSTR(p.observation_about, 1, 8) AS observation_about,
  p.observation_date,
  COALESCE(
    'dcAggregate/' || NULLIF(TRIM(p.measurement_method), ''), 'dcAggregate'
  ) AS measurement_method,
  SAFE_DIVIDE(
    SUM(SAFE_CAST(c.population AS FLOAT64) * SAFE_CAST(p.percent AS FLOAT64)),
    SUM(SAFE_CAST(c.population AS FLOAT64))
  ) AS percent
FROM svo_percent AS p
INNER JOIN svo_count AS c
  ON p.observation_about = c.observation_about
  AND p.observation_date = c.observation_date
  AND p.pop_statvar = c.population_statvar
GROUP BY 1, 2, 3, 4
HAVING percent IS NOT NULL
"""


def run_process(client: bigquery.Client,
                output_file: str,
                timeout: int = DEFAULT_BQ_TIMEOUT_SECONDS) -> bool:
    """Executes the BigQuery query and writes the resulting DataFrame to output_file."""
    logging.info("Running BigQuery aggregation query on project %s...",
                 client.project)
    query_job = client.query(QUERY, timeout=timeout)
    logging.info("BigQuery job started with ID: %s", query_job.job_id)

    logging.info("Fetching query results into dataframe...")
    df = query_job.to_dataframe(timeout=timeout)

    if df.empty:
        logging.error("BigQuery query returned 0 rows.")
        raise RuntimeError("BigQuery query returned 0 rows.")

    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    logging.info("Writing %d rows to %s", len(df), output_file)
    temp_file = output_file + ".tmp"
    try:
        df.to_csv(temp_file, index=False)
        if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
            logging.error("Output file %s was created empty or missing.",
                          temp_file)
            raise RuntimeError(
                f"Output file {temp_file} was created empty or missing.")
        os.replace(temp_file, output_file)
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    return True


def main(argv):
    """Main entry point for the CDC 500 state aggregation script."""
    del argv  # Unused.
    client = bigquery.Client(project=_FLAGS.project)
    output_file = os.path.join(_FLAGS.output_dir, 'CDC500State_Output.csv')
    try:
        run_process(client, output_file, timeout=_FLAGS.timeout)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.fatal("CDC 500 state aggregation failed: %s", e, exc_info=True)


if __name__ == '__main__':
    app.run(main)
