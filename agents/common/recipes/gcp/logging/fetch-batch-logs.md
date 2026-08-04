# Fetch bounded Batch logs

Recipe ID: `gcp.logging.fetch-batch-logs`

## Use when

Structured pipeline stage/status evidence is required for a known Batch job.

## Required inputs

Logging project, row limit, and optional filter clauses when available: Batch
job UID (`<JOB_UID>`), UTC start/end timestamps (`<START>`/`<END>`), and an
optional text/payload search term (`<QUERY_TERM>`).

## Clarify when

The job UID is unverified or an unbounded query returns too many results.

## Read-only operation

```bash
# Structured stage/status events (default)
gcloud logging read \
  'logName="projects/<PROJECT>/logs/batch_task_logs" AND labels.job_uid="<JOB_UID>" AND timestamp>="<START>" AND timestamp<="<END>" AND (jsonPayload.log_type="auto-import-job-stage" OR jsonPayload.log_type="auto-import-job-status")' \
  --project=<PROJECT> \
  --order=desc \
  --limit=<LIMIT_PLUS_ONE> \
  --format='json(timestamp,severity,labels.job_uid,
                 jsonPayload.log_type,jsonPayload.import_name,
                 jsonPayload.stage_name,jsonPayload.status,
                 jsonPayload.latency_secs,jsonPayload.data_bytes)'

# With optional query term (retains textPayload for system/startup logs)
gcloud logging read \
  'logName="projects/<PROJECT>/logs/batch_task_logs" AND labels.job_uid="<JOB_UID>" AND timestamp>="<START>" AND timestamp<="<END>" AND "<QUERY_TERM>"' \
  --project=<PROJECT> \
  --order=desc \
  --limit=<LIMIT_PLUS_ONE> \
  --format=json
```

Include `<JOB_UID>`, `<START>`/`<END>`, and `<QUERY_TERM>` as optional filter
clauses when available. When searching with `<QUERY_TERM>`, use `--format=json`
so that `textPayload` (such as container image pull logs) is preserved.

## Preferred invocation

Run only for a selected job when structured pipeline stage or status events
are required beyond job-level state and summary evidence. Request one more row
than the display limit to detect truncation, then return at most the requested
limit in chronological order.

If zero matching logs are returned, relax or widen the timestamp window
(`<START>`/`<END>`) or remove optional query terms (`<QUERY_TERM>`).

## Expected output

Allowlisted structured stage/status fields (or matching JSON/text payload when
using `<QUERY_TERM>`) and explicit truncation.

## Required bounds

Filter by exact log name, job UID when known, structured log types or query
term, explicit UTC window when available, and result limit. Return at most 500
records.

## Evidence to retain

Log name, timestamp, severity, job UID, structured fields used, and truncation.
Never retain `message`, `textPayload`, or unrecognized payload fields unless
explicitly matching `<QUERY_TERM>`.

## Common failures

Expired logs, private-log permission, wrong UID, no structured events, no
matching logs (relax timestamp window or query terms if zero results are
returned), or truncation.

## Related repository sources

`import-automation/executor/app/executor/import_executor.py` constants
`AUTO_IMPORT_JOB_STAGE`, `AUTO_IMPORT_JOB_STATUS`, and `log_import_status()`.
