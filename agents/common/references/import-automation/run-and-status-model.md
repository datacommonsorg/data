# Run and status model

Use each source only for the state it actually records. This skill supports a
current mutable snapshot and bounded finalized-version evidence; it does not
provide complete ET-attempt history.

## Evidence roles

| Source | What it represents | What it does not prove |
|---|---|---|
| `ImportStatus` | One import's latest mutable database snapshot, including raw state, recorded version, ET Batch job ID, and update time | Historical state changes, every ET attempt, or a finalized version |
| GCS `import_summary.json` | One candidate that reached finalization, including classification, Batch job ID, and metrics | That the attempt is the latest attempt or that the candidate became current |
| `staging_version.txt` | Most recent candidate that reached summary creation | Most recent ET attempt if a later attempt failed earlier |
| Current-output pointer, normally `latest_version.txt` | Version selected as the current ET output at read time | Loader execution or serving-system state |
| Exact Batch job/task | Technical compute state for one already-known Batch ID | Import history or semantic ET outcome |

`ImportStatus` is mutable and shared with the separate loader pipeline. Return
its `State` without reinterpretation as `current_status`. Its `JobId` is the ET
Batch identifier and may seed exact Batch inspection. Its `WorkflowId` is
loader-owned, can belong to an earlier run, and is not an ET Workflow execution
ID; never select, return, or follow it in this skill.

## Finalized versions are not attempt history

The bounded GCS helper finds version directories that contain
`import_summary.json`. Those are finalized candidates, not all Workflow or
Batch attempts. A technical failure can stop before a version or summary is
complete, so it will not appear in GCS summary history. For the current import,
`ImportStatus` may still expose that failure and its Batch job ID. Older
pre-summary failures are unsupported because this skill does not list Workflow
executions or Batch jobs.

The helper uses reverse lexicographic timestamp-folder order, scans no more than
100 summary names, skips non-timestamp override names, returns at most five
versions with their exact GCS version URIs, and reads only those selected
summaries for their Batch job IDs. This ordering is an intentional operational
approximation: Pacific timestamps can misorder versions within the repeated
hour at DST fall-back. If the scan exceeds 100, the helper returns no history
rather than mislabeling the oldest scanned results as the newest.

## Keep status fields separate

| Report field | Evidence |
|---|---|
| `current_status` | Raw `ImportStatus.State` |
| `summary_status` | Exact GCS summary, such as `STAGING`, `VALIDATION`, or `SKIP` |
| `is_current` | Selected version compared with the current-output pointer |
| `batch_state` | Exact Batch description for a known Batch job ID |

Do not create an overall status. These values describe different stages and
can legitimately differ.

## Candidate classification and acceptance

- `STAGING`: changed output passed ET checks and is eligible for acceptance.
- `VALIDATION`: output was generated but validation failed; it is not eligible.
- `SKIP`: ET completed but found no meaningful change; there is no new output
  to accept.
- Technical failure: compute can stop before a complete candidate or summary
  exists.

Acceptance is the ET-only action that promotes an eligible `STAGING` candidate
to the current ET output. It advances the current-output pointer and makes that
version eligible for the separate loader pipeline. It does not mean a human
approved the data, the loader ran, or serving data changed.

## Choose the smallest evidence path

| Question | Start with |
|---|---|
| Current recorded state, job ID, or version for one import | Exact `ImportStatus` query |
| Imports currently in a selected state and recently updated | Bounded across-import `ImportStatus` query |
| Up to five recent finalized versions for one import | GCS summary-list helper |
| Classification or metrics for one selected version | Exact GCS summary |
| Whether a selected version is the current ET output | Exact current-output pointer |
| Technical state, task, or logs for a known job ID | Exact Batch recipe |

Compose only when the question needs multiple facts:

1. Use `ImportStatus` for the current snapshot or GCS for a finalized version.
2. Follow only `ImportStatus.JobId` or a validated summary `job_id` to Batch.
3. Read the selected version's exact summary for `summary_status` or metrics.
4. Read the current-output pointer only when currentness or acceptance matters.

Never list Workflow executions or Batch jobs to fill a missing identifier.

## Across-import current-state queries

A query such as “all failing imports in the last week” means:

```text
current ImportStatus.State = FAILURE
and StatusUpdateTimestamp is within the requested week
```

It does not mean every failure event that occurred during that week. A row that
failed and later changed state no longer matches; an older failure whose current
row was not updated in the window also does not match.

Unless the user supplies bounds, use production, the previous seven days, and
at most 100 returned current rows. Query one extra row to detect truncation.
Always report the UTC window, requested limit, and whether results were
truncated.

## Missing or conflicting evidence

Return known fields and use `unknown` only for the fact the evidence cannot
establish. Common partial states include:

- `ImportStatus` reports a failure and Batch ID, but no summary exists because
  the attempt failed before finalization;
- a GCS summary exists, but the current-output pointer names an older version;
- `ImportStatus.LatestVersion` and a pointer differ because they have different
  update semantics;
- an exact Batch resource has expired or cannot be read;
- the GCS summary-name scan exceeds 100;
- a version uses a non-timestamp override name and is skipped by the bounded
  history helper.

Do not broaden the search or infer that a missing record means no attempt
occurred.
