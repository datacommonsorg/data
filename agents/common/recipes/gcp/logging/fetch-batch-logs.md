# Fetch bounded Batch logs

Recipe ID: `gcp.logging.fetch-batch-logs`

## Use when

Structured pipeline stage/status evidence is required for a known Batch job.

## Required inputs

Logging project, verified Batch job UID (`<JOB_UID>`), inclusive UTC start
timestamp (`<START>`), exclusive UTC end timestamp (`<END>`), and row limit. A
text/payload search term (`<QUERY_TERM>`) is optional.

## Clarify when

The job UID is unverified, either timestamp is unavailable, the start is not
before the end, or the bounded query returns too many results.

## Read-only operation

Follow the [shared Cloud Logging parameters](../../../references/gcp/logging.md)
with one of these Batch-specific parameter sets.

```text
# Structured stage/status events (default)
FILTER =
  logName="projects/<PROJECT>/logs/batch_task_logs"
  AND labels.job_uid="<JOB_UID>"
  AND (jsonPayload.log_type="auto-import-job-stage"
       OR jsonPayload.log_type="auto-import-job-status")
  AND timestamp >= "<START>" AND timestamp < "<END>"
PROJECT = <PROJECT>
ORDER = desc
LIMIT = <LIMIT_PLUS_ONE>
FORMAT = json(timestamp,severity,labels.job_uid,
              jsonPayload.log_type,jsonPayload.import_name,
              jsonPayload.stage_name,jsonPayload.status,
              jsonPayload.latency_secs,jsonPayload.data_bytes)

# Optional text/payload search for system or startup logs
FILTER =
  logName="projects/<PROJECT>/logs/batch_task_logs"
  AND labels.job_uid="<JOB_UID>"
  AND timestamp >= "<START>" AND timestamp < "<END>"
  AND "<QUERY_TERM>"
PROJECT = <PROJECT>
ORDER = desc
LIMIT = <LIMIT_PLUS_ONE>
FORMAT = json
```

The query-term mode uses JSON so that matching `textPayload`, such as container
image pull logs, is preserved.

## Preferred invocation

Run only for a selected job when structured pipeline stage or status events
are required beyond job-level state and summary evidence. Request one more row
than the display limit to detect truncation, then return at most the requested
limit in chronological order.

If zero matching logs are returned, verify or widen the timestamp window
(`<START>`/`<END>`) or remove optional query terms (`<QUERY_TERM>`).

## Expected output

Allowlisted structured stage/status fields (or matching JSON/text payload when
using `<QUERY_TERM>`) and explicit truncation.

## Required bounds

Filter by exact log name and verified job UID, plus structured log types or a
query term. Always use the inclusive UTC start and exclusive UTC end. Request
one extra record for truncation detection and return at most 500 records.

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
