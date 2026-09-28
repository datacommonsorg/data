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

CREATE TABLE ImportSummary (
  ImportName STRING(MAX) NOT NULL,
  LatestVersion STRING(MAX),
  GraphPath STRING(MAX),
  State STRING(1024) NOT NULL,
  JobId STRING(1024),
  WorkflowId STRING(1024),
  ExecutionTime INT64,
  DataVolume INT64,
  DataImportTimestamp TIMESTAMP OPTIONS ( allow_commit_timestamp = TRUE ),
  StatusUpdateTimestamp TIMESTAMP OPTIONS ( allow_commit_timestamp = TRUE ),
  NextRefreshTimestamp TIMESTAMP,
) PRIMARY KEY(ImportName);

CREATE TABLE ImportHistory (
  ImportName STRING(MAX) NOT NULL,
  Version STRING(MAX) NOT NULL,
  UpdateTimestamp TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
  WorkflowExecutionID STRING(1024),
  JobId STRING(1024),
  Status STRING(1024),
  ExecutionTime INT64,
  DataVolume INT64,
  Comment STRING(MAX),
) PRIMARY KEY (ImportName, UpdateTimestamp DESC);
