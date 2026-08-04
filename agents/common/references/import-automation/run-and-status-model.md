# Run and status model

One Workflow execution is one logical extract-and-transform (ET) attempt. A
checkpointed ET run is a version recorded in Spanner version metadata. The
correlation path joins it to its exact GCS summary when available. Checkpointed
runs are fast to query, but they are not an exhaustive attempt ledger because
an attempt can fail before creating those records.

## Status dimensions

Keep these dimensions separate:

| Dimension | Meaning |
|---|---|
| Scheduler | Delivery and deployed configuration, not run completion |
| Workflow | Orchestration state and historical revision |
| Batch/task | Compute allocation and container execution |
| Pipeline | Executor summary such as `STAGING`, `VALIDATION`, or `SKIP` |
| Semantic validation | Whether generated data passed import validation |
| Current (accepted) ET output | Whether a candidate became the selected ET result |

A Workflow and Batch job can succeed while the pipeline result is `VALIDATION`
or `SKIP`.

## Candidate classification and acceptance

- `STAGING`: a new version completed and is eligible to become the accepted ET
  output.
- `VALIDATION`: compute completed but semantic validation failed. Classify the
  refresh as failed.
- `SKIP`: ET completed with no data change. It is neither a new accepted version
  nor a failure.
- Failure before summary: rely on Workflow, Batch, task, and logs; no GCS
  summary or version event may exist.

A `STAGING` summary proves eligibility, not acceptance. Define the latest
checkpointed successful refresh as the newest correlated version with an exact
`STAGING` summary and an unambiguous ET acceptance checkpoint. For the current
ET output, read the configured current-output pointer and that version's exact
summary. A historical checkpoint does not by itself prove that the version is
still current.

When queried summary, pointer, or checkpoint evidence is missing or conflicts,
return the individual states and an overall status of `unknown`. If bounded
evidence has no success, mark the result incomplete rather than claiming the
import never succeeded.

## Evidence sources and lookup order

- Workflow executions: retained ET attempts, including failures before output.
- Batch jobs/tasks: retained compute attempts.
- GCS summaries: candidate classification and output details.
- GCS current-output pointer: which accepted ET output is current at read time.
- `ImportVersionHistory`: queryable version-event checkpoint history. Use
  bounded correlation to select relevant ET evidence; do not treat every event
  as an ET attempt or automated acceptance.

For routine single-import history and status, start with bounded correlated
checkpoint history. This limitation does not justify listing Workflow
executions merely because some attempts may be absent. Query Workflow only when
the request requires running attempts, failures before checkpointing, complete
attempt history, multiple-import status, or another fact that structured
correlation cannot provide. When correlation returns a Workflow execution ID,
describe that exact execution instead of listing Workflow history.

If correlation returns no record and the request still requires an attempt-level
answer, use bounded Workflow history. Otherwise report
`No checkpointed ET run found` for the queried bounds. Do not translate that
result into `No ET attempt occurred`.

## Status across multiple imports

For a query across multiple imports, default to production, the previous 24
hours, and at most 100 returned Workflow executions. The single-import
checkpoint path is not a multiple-import index. List FULL-view executions once
without an exact-import filter, apply an optional case-insensitive import-name
filter locally, and report a compact table before row details.

- `failed`: Workflow or Batch technical failure, or pipeline `VALIDATION` or
  failure.
- `running`: Workflow or Batch is active, queued, or running.
- `succeeded`: pipeline `STAGING` and accepted-output evidence are both
  observed.
- `skipped`: pipeline `SKIP`.
- `unknown`: required semantic evidence is missing, conflicting, ambiguous, or
  truncated.

Read semantic evidence only for technically successful candidate runs whose
requested classification needs it. For a consecutive-failure query, inspect
terminal runs newest to oldest and measure the current streak against the
requested minimum. Every status other than `failed` breaks the streak.

Always state the queried time window, result/page limits, and truncation.
