# Runtime provenance

Recover provenance in this order:

```text
Workflow execution
  -> historical Workflow revision
  -> Batch job/task and requested image URI
  -> Artifact Registry digest or Cloud Build result
  -> Cloud Build source commit
  -> embedded /data commit when explicitly recorded
  -> local checkout commit for comparison
```

Record evidence and one confidence value:

- `exact`: an immutable identifier directly records the runtime source.
- `strongly_correlated`: multiple independent time/image/build signals agree.
- `ambiguous`: more than one candidate remains.
- `unknown`: evidence is absent or expired.

Bound Cloud Build candidates using the earliest Batch task `RUNNING` status
event. Fall back to Batch job creation time, then Workflow start time, and
record the selected `time_basis`.

The current image build tags the executor with the Cloud Build commit and later
promotes it to mutable `stable`. The cloud Dockerfile separately clones the
Data Commons `data` repository without pinning a commit. Therefore the Cloud
Build source commit does not prove the embedded `/data` commit, and a current
`stable` digest does not necessarily identify a historical task image.

Do not run or pull a production container merely to inspect it. Use Batch,
Workflow, Artifact Registry, Cloud Build, structured startup logs, and image
metadata that are already available. Return `unknown` when the embedded commit
was not recorded.
