# GCS operations

- [List recent import versions](#list-recent-import-versions)
- [Read one import version summary](#read-one-import-version-summary)
- [Find the last successful import version](#find-the-last-successful-import-version)
- [List artifacts for one import version](#list-artifacts-for-one-import-version)

## List recent import versions

### Use when

Up to five recent versions that produced `import_summary.json`, together with
their Batch job IDs, are needed for one exact import.

### Required inputs

Exact absolute import name; GCS project and bucket from the effective
environment; result limit from 1 through 5.

### Clarify when

The import identity or GCS resource is unresolved.

### Read-only operation

```bash
./agents/common/run_python.sh \
  agents/common/scripts/list_import_summaries.py \
  --absolute_import_name='<DIRECTORY>:<IMPORT_NAME>' \
  --gcs_project='<PROJECT>' \
  --gcs_bucket='<BUCKET>' \
  --limit='<1_TO_5>'
```

### Preferred invocation

Use the helper once. It orders timestamp-version names newest first, downloads
only the selected summaries to validate `import_name` and extract `job_id`, and
reports skipped non-timestamp names. If `scan_truncated=true`, use no returned
history and do not replace it with a broader bucket, Workflow, or Batch search.

Reverse lexicographic ordering intentionally trusts folder names and can
misorder versions within the repeated Pacific hour at DST fall-back.

### Expected output

Top-level identity, requested and scan limits, scanned/returned counts,
truncation, skipped override count, and bounded issues. Each result contains
`version`, date derived from the version name, the exact `gcs_version_uri`
without a trailing slash, and `batch_job_id`. Append `/import_summary.json` to
the version URI only when the exact summary is needed.

### Required bounds

Scan up to 1000 matching summary object names plus one overflow sentinel (1001
names maximum). Return at most five timestamp-named versions and download at
most those five summaries.

### Evidence to retain

Exact import prefix and GCS resource, requested bounds, truncation, returned
version fields, and issues.

### Common failures

Permission denied, missing credentials, scan-limit overflow, invalid JSON,
summary identity mismatch, missing Batch job ID, or only non-timestamp names.
A Batch failure before summary creation is intentionally absent: this is
version history, not complete attempt history.

### Related repository sources

[Artifact layout](../../../common/references/import-automation/artifact-layout.md),
[import evidence flow](import-evidence-flow.md),
and the [summary-list helper](../../../common/scripts/list_import_summaries.py).

## Read one import version summary

### Use when

Candidate classification, Batch job ID, or summary statistics are needed for
an already selected version.

### Required inputs

GCS project and bucket from the effective environment; exact import identity
and version; expected simple import name; and, when already known, the expected
Batch job ID.

### Clarify when

The import identity or version is ambiguous. Accept an exact version supplied
by the user or obtained from the current status, last-successful-version, or
bounded recent-version operation. Keep the read scoped to the selected import's
GCS prefix.

### Read-only operation

```bash
gcloud storage cat \
  'gs://<BUCKET>/<IMPORT_PREFIX>/<VERSION>/import_summary.json' \
  --project=<PROJECT> | \
jq '{import_name,job_id,status,latest_version,graph_path,next_refresh,
     execution_time,data_volume,import_stats}'
```

### Preferred invocation

Read `import_summary.json` for one exact version and require `import_name` to
match the selected import before using any status or statistics. When a Batch
job ID is already known, also require `job_id` to match. Otherwise retain the
summary's `job_id` as a discovered identifier and follow only that exact ID.
When an exact version is supplied independently, construct its URI using the
[import evidence flow](import-evidence-flow.md); do not run the summary-list
helper first.

### Expected output

Allowlisted summary identity, status, version/path, timing, volume, and import
statistics.

### Required bounds

Read one exact summary. Do not list artifacts or other summaries.

### Evidence to retain

Exact summary URI, import/job identity match, status, and fields used in the
answer.

### Common failures

Attempt or Batch failure before summary creation, identity mismatch, invalid
JSON, missing object, or permission denied. A missing summary is not proof that
no attempt occurred.

### Related repository sources

The [import executor](../../../../import-automation/executor/app/executor/import_executor.py)
defines `ImportStatusSummary` and `_update_latest_version()`.

## Find the last successful import version

### Use when

The last successful or accepted ET version must be identified.

### Required inputs

GCS project and bucket from the effective environment, plus the exact import
identity.

### Clarify when

A required project, bucket, or import identity is missing, or the import prefix
cannot be constructed from the exact import identity.

### Read-only operation

```bash
gcloud storage cat \
  'gs://<BUCKET>/<IMPORT_PREFIX>/latest_version.txt' \
  --project=<PROJECT>
```

### Preferred invocation

Read `latest_version.txt` for the last successful version accepted as the
current ET output. To determine whether a selected version is the last
successful version, compare it exactly with this value. This does not prove
loader completion or serving availability.

### Expected output

One version string from one exact object, labeled as the last successful
version.

### Required bounds

Read one exact object. Never list the import prefix to discover pointer names.

### Evidence to retain

Exact object URI, returned version, and observation time.

### Common failures

Failure before summary creation, missing accepted version, wrong bucket/prefix,
permission denied, or a stale value.

### Related repository sources

[Import environment defaults](../../../common/config/import-environments.yaml)
and [artifact layout](../../../common/references/import-automation/artifact-layout.md).

## List artifacts for one import version

### Use when

Artifact metadata for input, output, MCF, validation, or differ files is needed
for one selected run.

### Required inputs

GCS project and bucket from the effective environment, exact import identity,
exact version, and result limit.

### Clarify when

The version is unknown or the requested artifact category is ambiguous.

### Read-only operation

```bash
gcloud storage objects list \
  'gs://<BUCKET>/<IMPORT_PREFIX>/<VERSION>/**' \
  --project=<PROJECT> \
  --limit=<LIMIT_PLUS_ONE> \
  --format='json(name,bucket,size,updateTime,generation)'
```

### Preferred invocation

List metadata under one selected version. Filter returned names to the requested
artifact category; do not download data or MCF contents by default.

### Expected output

Bounded object URIs, sizes, update times, generations, and truncation.

Object presence confirms that an artifact was retained for the selected
version. If an expected artifact is absent, use the
[manifest reference](../../../common/references/import-automation/manifest.md)
and [artifact layout](../../../common/references/import-automation/artifact-layout.md)
to interpret whether it was selected for upload.

### Required bounds

Use one exact version and an explicit result limit. Request one extra object to
detect truncation.

### Evidence to retain

Exact version URI, requested category, object metadata used, limit, and
truncation.

### Common failures

Wrong version, deleted objects, permission denied, or more objects than the
selected limit.

### Related repository sources

The [import executor](../../../../import-automation/executor/app/executor/import_executor.py)
and [artifact layout](../../../common/references/import-automation/artifact-layout.md).
