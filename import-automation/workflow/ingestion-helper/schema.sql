-- Copyright 2026 Google LLC
--
-- Licensed under the Apache License, Version 2.0 (the "License")
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

CREATE PROTO BUNDLE (
  `org.datacommons.Observations`
);

CREATE TABLE Node (
  subject_id STRING(1024) NOT NULL,
  value STRING(MAX),
  bytes BYTES(MAX),
  name STRING(MAX),
  types ARRAY<STRING(1024)>,
  last_update_timestamp TIMESTAMP OPTIONS (allow_commit_timestamp=true),
  name_tokenlist TOKENLIST AS (TOKENIZE_FULLTEXT(name)) HIDDEN,
) PRIMARY KEY(subject_id);

CREATE TABLE Edge (
  subject_id STRING(1024) NOT NULL,
  predicate STRING(1024) NOT NULL,
  object_id STRING(1024) NOT NULL,
  provenance STRING(1024) NOT NULL,
) PRIMARY KEY(subject_id, predicate, object_id, provenance),
INTERLEAVE IN Node;

CREATE TABLE Observation (
  observation_about STRING(1024) NOT NULL,
  variable_measured STRING(1024) NOT NULL,
  facet_id STRING(1024) NOT NULL,
  observation_period STRING(1024),
  measurement_method STRING(1024),
  unit STRING(1024),
  scaling_factor STRING(1024),
  observations org.datacommons.Observations,
  import_name STRING(1024),
  provenance_url STRING(1024),
  is_dc_aggregate BOOL,
) PRIMARY KEY(observation_about, variable_measured, facet_id);

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
  IngestionFailure Bool NOT NULL,
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

CREATE PROPERTY GRAPH DCGraph
  NODE TABLES(
    Node
      KEY(subject_id)
      LABEL Node PROPERTIES(
        bytes,
        name,
        subject_id,
        types,
        value)
  )
  EDGE TABLES(
    Edge
      KEY(subject_id, predicate, object_id, provenance)
      SOURCE KEY(subject_id) REFERENCES Node(subject_id)
      DESTINATION KEY(object_id) REFERENCES Node(subject_id)
      LABEL Edge PROPERTIES(
        object_id,
        predicate,
        provenance,
        subject_id)
  );
