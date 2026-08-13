# Cloud Batch runtime issues

Use this guide when a selected Cloud Batch job:

- failed;
- stopped making progress; or
- has a suspected runtime cause.

For an unclassified Batch problem:

- Inspect the exact job.
- Use task events or bounded logs as needed to test the hypotheses below.

## Hypotheses

| Hypothesis | Consider first when | Section |
|---|---|---|
| Out of memory | Unexpected termination, a killed task, exit code 137, or suspected memory exhaustion | [Out of memory](#out-of-memory) |
| Java GC thrashing | Java remains active but makes little useful import progress | [Java GC thrashing](#java-gc-thrashing) |

## Out of memory

### Confirm or reject

- Confirm OOM only when task events or bounded logs explicitly report memory
  exhaustion.
- Accept signals such as `OutOfMemoryError`, `OOMKilled`, `oom-kill`,
  `out of memory`, or a memory-limit failure.
- Inspect task events first.
- Use bounded Batch logs when task evidence is insufficient.
- Do not confirm OOM from exit code 137, SIGKILL, high memory use, or abrupt
  termination alone.
- Treat missing evidence as unknown, not refuted.
- Do not use monitoring evidence until the skill has a supported monitoring
  operation.

### Mitigation when confirmed

When OOM is confirmed:

- Recommend increasing `resource_limits.memory` for the affected import
  specification.
- Preserve its existing CPU and disk settings.
- State the current and proposed memory values in GiB.
- Recommend rerunning the import after the manifest change.

## Java GC thrashing

### Confirm or reject

- Confirm GC thrashing only when bounded runtime evidence shows repeated Java
  garbage collection and bounded stage or status evidence shows little useful
  import progress.
- Treat long runtime or high CPU alone as insufficient.
- Treat missing runtime evidence as unknown, not refuted.

### Mitigation when confirmed

For the Data Commons import-tool path, Java heap sizing scales with the
container's available memory. Increasing `resource_limits.memory` therefore
increases the heap available to Java.

When GC thrashing is confirmed:

- Recommend increasing `resource_limits.memory` for the affected import
  specification.
- Preserve its existing CPU and disk settings.
- Recommend rerunning the import after the manifest change.

## When no hypothesis matches

- Report the Batch runtime problem as unclassified.
- Return to the parent troubleshooting fallback.
- Do not force a memory diagnosis.
