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
SELECT distinct * from(
SELECT 
  statvar, 
  SUBSTR(observation_about,0,8) as observation_about,
  observation_date, 
  CONCAT('dcAggregate/',measurement_method) as measurement_method,
  population_statvar,
  SUM(CAST(pop_count AS FLOAT64))*100/SUM(CAST(population AS FLOAT64)) as percent
FROM 
(
  SELECT
    SVO1.variable_measured as statvar,
    SVO1.observation_about as observation_about,
    SVO1.observation_date as observation_date,
    SVO1.value as percent,
    SVO1.measurement_method as measurement_method,
    SVO2.variable_measured as population_statvar,
    SVO2.value as population,
    CAST(SVO2.value AS FLOAT64) * CAST(SVO1.value AS FLOAT64) / 100 as pop_count
  FROM `datcom-store.dc_kg_latest.StatVarObservation` as SVO1
  JOIN `datcom-store.dc_kg_latest.StatVarObservation` as SVO2 ON TRUE
  JOIN (
    # Get the statvars and corresponding population statvar
    # with ‘Percent_’ replaced with ‘Count_’ and
    # dropping the non-age, non-gender constraints.
    SELECT
      SVO.variable_measured as CDC500,
      CONCAT('Count_', REGEXP_SUBSTR(SVO.variable_measured, '(Person_.*ale|Person_.*Years|Person)')) as pop_statvar
      FROM `datcom-store.dc_kg_latest.StatVarObservation` as SVO
    WHERE
      SVO.prov_id = 'dc/base/CDC500'
      AND SVO.variable_measured like 'Percent_%'
      GROUP BY CDC500, pop_statvar
   ) AS CDC_SV ON TRUE
  WHERE
    SVO1.prov_id = 'dc/base/CDC500'
    AND SVO1.variable_measured LIKE 'Percent%'
    AND SVO1.observation_about = SVO2.observation_about
    AND SVO1.observation_date = SVO2.observation_date
    AND SVO1.variable_measured = CDC_SV.CDC500
    AND SVO2.variable_measured = CDC_SV.pop_statvar
    AND SVO1.observation_about like "geoId/%"
) group by 1,2,3,4,5
)
"""

client = bigquery.Client(project='datcom-store')
try:
    logging.info("Running the query")
    query_job = client.query(query)
except Exception as e:
    logging.fatal(f"Error faced while running the query {e}")

logging.info("Converting to dataframe")
results = query_job.to_dataframe()

logging.info("Writing output to CSV")
output_file = os.path.join(_OUTPUT_FILE_PATH + "/CDC500State_Output.csv")
results.to_csv(output_file, index=False)
