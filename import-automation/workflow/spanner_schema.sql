-- Copyright 2025 Google LLC
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

-- Spanner schema for ingestion workflow
-- gcloud spanner databases ddl update <database_id> --instance=<instance_id> --project <project_id> --ddl-file=./spanner_schema.sql

CREATE TABLE ImportStatus (
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

CREATE TABLE IngestionHistory (
  CompletionTimestamp TIMESTAMP NOT NULL OPTIONS ( allow_commit_timestamp = TRUE ),
  WorkflowExecutionID STRING(1024) NOT NULL,
  DataflowJobID STRING(1024),
  IngestedImports ARRAY<STRING(MAX)>,
  ExecutionTime INT64,
  NodeCount INT64,
  EdgeCount INT64,
  ObservationCount INT64,
) PRIMARY KEY(CompletionTimestamp DESC);

CREATE TABLE ImportVersionHistory (
  ImportName STRING(MAX) NOT NULL,
  Version STRING(MAX) NOT NULL,
  UpdateTimestamp TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
  Comment STRING(MAX),
) PRIMARY KEY (ImportName, UpdateTimestamp DESC);

CREATE TABLE IngestionLock (
  LockID STRING(1024) NOT NULL,
  LockOwner STRING(1024),
  AcquiredTimestamp TIMESTAMP OPTIONS ( allow_commit_timestamp = TRUE ),
) PRIMARY KEY(LockID);

-- Initialize the IngestionLock table with the global lock.
-- INSERT INTO IngestionLock (LockID) VALUES ('global_ingestion_lock');

