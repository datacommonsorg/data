# Run and status model

One Workflow execution is one logical refresh run. Keep the following status
dimensions separate:

| Dimension | Meaning |
|---|---|
| Scheduler | Delivery/configuration state, not run completion |
| Workflow | Orchestration state and historical revision |
| Batch/task | Compute allocation and container execution |
| Pipeline | Executor summary such as `STAGING`, `VALIDATION`, or `SKIP` |
| Semantic validation | Whether generated data passed import validation |
| Publication | Whether an accepted version was recorded |
| Downstream ingestion | Whether the accepted graph was ingested |

A Workflow and Batch job can succeed while the pipeline result is
`VALIDATION` or `SKIP`.

- `STAGING`: a new version completed and is eligible for publication.
- `VALIDATION`: the refresh completed technically but failed semantic
  validation. Treat it as a failed refresh.
- `SKIP`: the refresh completed with no data change. Report it separately; it
  is neither a new accepted version nor a failure.
- Failure before summary: rely on Workflow, Batch, task, and logs; no GCS
  summary or version event may exist.

Define latest successful refresh as the newest run with `STAGING` plus an
observed publication update. When either signal is missing or conflicts, return
the component states and composite `unknown`. Resolve it from returned runs and
accepted `ImportVersionHistory` rows tied to `import-workflow:<execution-id>`.
If bounded evidence contains no success, mark the result incomplete rather than
claiming the import has never succeeded.

## History sources

- Workflow executions: retained refresh attempts, including failures.
- Batch jobs/tasks: retained compute attempts.
- `ImportStatus`: one mutable current row, not an attempt ledger.
- `ImportVersionHistory`: accepted/version transition events; failed and
  skipped attempts may be absent.
- `IngestionHistory`: downstream ingestion/Dataflow history, not upstream
  refresh history.

Always state the queried time window, result/page limits, and truncation.
For consecutive failures, every status other than `failed` breaks the streak.
