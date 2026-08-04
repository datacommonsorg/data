# Run and status model

One Workflow execution is one logical extract-and-transform (ET) attempt. Keep
these status dimensions separate:

| Dimension | Meaning |
|---|---|
| Scheduler | Delivery and deployed configuration, not run completion |
| Workflow | Orchestration state and historical revision |
| Batch/task | Compute allocation and container execution |
| Pipeline | Executor summary such as `STAGING`, `VALIDATION`, or `SKIP` |
| Semantic validation | Whether generated data passed import validation |
| Accepted ET output | Whether the selected ET version became the accepted result |

A Workflow and Batch job can succeed while the pipeline result is `VALIDATION`
or `SKIP`.

- `STAGING`: a new version completed and is eligible to become the accepted ET
  output.
- `VALIDATION`: compute completed but semantic validation failed. Classify the
  refresh as failed.
- `SKIP`: ET completed with no data change. It is neither a new accepted version
  nor a failure.
- Failure before summary: rely on Workflow, Batch, task, and logs; no GCS
  summary or version event may exist.

Define the latest successful refresh as the newest run with a `STAGING` summary
plus either the configured accepted pointer referencing that same version or an
accepted `ImportVersionHistory` event tied to
`import-workflow:<execution-id>`. When either signal is missing or conflicts,
return the individual states and an overall status of `unknown`. If bounded
evidence has no success, mark the result incomplete rather than claiming the
import never succeeded.

## History sources

- Workflow executions: retained ET attempts, including failures before output.
- Batch jobs/tasks: retained compute attempts.
- GCS pointers and exact summaries: pipeline status and current accepted-output
  evidence.
- `ImportVersionHistory`: accepted version/output events; failed and skipped
  attempts may be absent. Use only through bounded correlation.

Correlation history does not replace Workflow execution history.

## Status across multiple imports

For a query across multiple imports, default to production, the previous 24
hours, and at most 100 returned Workflow executions. List FULL-view executions
once without an exact-import filter, apply an optional case-insensitive
import-name filter locally, and report a compact table before row details.

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
