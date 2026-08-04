# Fetch bounded Batch logs

Recipe ID: `gcp.logging.fetch-batch-logs`

## Use when

Structured pipeline stage/status evidence is required for a known Batch job.

## Required inputs

Logging project, Batch job UID, UTC start/end, and row limit.

## Clarify when

The job UID is unverified or the requested window is unbounded.

## Read-only operation

```bash
gcloud logging read \
  'logName="projects/<PROJECT>/logs/batch_task_logs" AND labels.job_uid="<JOB_UID>" AND timestamp>="<START>" AND timestamp<="<END>" AND (jsonPayload.log_type="auto-import-job-stage" OR jsonPayload.log_type="auto-import-job-status")' \
  --project=<PROJECT> \
  --order=desc \
  --limit=<LIMIT_PLUS_ONE> \
  --format='json(timestamp,severity,labels.job_uid,
                 jsonPayload.log_type,jsonPayload.import_name,
                 jsonPayload.stage_name,jsonPayload.status,
                 jsonPayload.latency_secs,jsonPayload.data_bytes)'
```

## Preferred invocation

Run only for a selected job when structured pipeline stage or status events
are required beyond job-level state and summary evidence. Request one more row
than the display limit to detect truncation, then return at most the requested
limit in chronological order.

## Expected output

Allowlisted structured stage/status fields and explicit truncation.

## Required bounds

Filter by exact log name, job UID, structured log types, explicit UTC window,
and result limit. Return at most 500 records.

## Evidence to retain

Log name, timestamp, severity, job UID, structured fields used, and truncation.
Never retain `message`, `textPayload`, or unrecognized payload fields.

## Common failures

Expired logs, private-log permission, wrong UID, no structured events, or
truncation.

## Related repository sources

`import-automation/executor/app/executor/import_executor.py` constants
`AUTO_IMPORT_JOB_STAGE`, `AUTO_IMPORT_JOB_STATUS`, and `log_import_status()`.
