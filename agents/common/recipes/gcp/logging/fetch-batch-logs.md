# Fetch bounded Batch logs

Recipe ID: `gcp.logging.fetch-batch-logs`

## Use when

Pipeline stage/status evidence is required for a known Batch job.

## Required inputs

Logging project, Batch job UID, UTC start/end, and row limit.

## Clarify when

The job UID is not verified or the requested window is unbounded.

## Read-only operation

```bash
gcloud logging read \
  'logName="projects/<PROJECT>/logs/batch_task_logs" AND labels.job_uid="<JOB_UID>" AND timestamp>="<START>" AND timestamp<="<END>" AND (jsonPayload.log_type="auto-import-job-stage" OR jsonPayload.log_type="auto-import-job-status")' \
  --project=<PROJECT> --order=desc --limit=<LIMIT_PLUS_ONE> --format=json
```

## Preferred invocation

Use the snapshot collector. Prefer structured `jsonPayload` fields including
`log_type`, `import_name`, `stage_name`, `status`, `latency_secs`, and
`data_bytes`. Do not retain `message`, `textPayload`, or unrecognized payload
fields.

## Expected output

The newest bounded structured stage/status records in chronological display
order, plus an explicit truncation flag.

## Required bounds

Filter by exact log name, job UID, structured log types, and explicit UTC
timestamps. Request the configured limit plus one to detect truncation; return
at most 500 entries.

## Evidence to retain

Log name, timestamp, severity, job UID, structured stage/status fields, and
truncation. Raw message text belongs in the debugging skill after a separate
sanitization policy exists.

## Common failures

Expired logs, private-log permission, wrong UID, no structured events, or
truncation.

## Related repository sources

`import_executor.py` constants `AUTO_IMPORT_JOB_STAGE` and
`AUTO_IMPORT_JOB_STATUS` and `log_import_status()`.
