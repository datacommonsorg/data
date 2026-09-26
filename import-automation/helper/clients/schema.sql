-- Copyright 2026 Google LLC
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--      http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.{history_table}` (
  ImportName STRING NOT NULL,
  Version STRING,
  Status STRING NOT NULL,
  JobId STRING,
  ExecutionTime INT64,
  DataVolume INT64,
  UpdateTimestamp TIMESTAMP NOT NULL,
  NextRefreshTimestamp TIMESTAMP,
  Comment STRING
)
PARTITION BY DATE(UpdateTimestamp)
CLUSTER BY ImportName;

CREATE OR REPLACE VIEW `{project_id}.{dataset_id}.{summary_view}` AS
SELECT
  ImportName,
  Version AS LatestVersion,
  Status AS State,
  JobId,
  ExecutionTime,
  DataVolume,
  MAX(IF(Status = 'STAGING', UpdateTimestamp, NULL)) OVER (
    PARTITION BY ImportName
  ) AS DataImportTimestamp,
  UpdateTimestamp AS StatusUpdateTimestamp,
  NextRefreshTimestamp
FROM `{project_id}.{dataset_id}.{history_table}`
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY ImportName
  ORDER BY UpdateTimestamp DESC
) = 1;
