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

CREATE TABLE NodeEmbedding (
  subject_id STRING(1024) NOT NULL,
  embedding_content STRING(MAX),
  types ARRAY<STRING(1024)>,
  embeddings ARRAY<FLOAT64>(vector_length=>768)
) PRIMARY KEY(subject_id),
INTERLEAVE IN PARENT Node ON DELETE CASCADE;

CREATE VECTOR INDEX NodeEmbeddingIndex
ON NodeEmbedding(embeddings)
WHERE embeddings IS NOT NULL
OPTIONS (
  distance_type = 'COSINE',
  flat_index = true
);

CREATE MODEL NodeEmbeddingModel
INPUT(
  content STRING(MAX),
  task_type STRING(MAX),
)
OUTPUT(
  embeddings
    STRUCT<
      statistics STRUCT<truncated BOOL, token_count FLOAT64>,
      values ARRAY<FLOAT64>>
)
REMOTE OPTIONS (
  endpoint = '{{ embeddings_endpoint }}'
);
