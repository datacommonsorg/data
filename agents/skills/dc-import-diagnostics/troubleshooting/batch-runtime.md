# Cloud Batch runtime issues

Use this guide when a selected Cloud Batch job failed, stopped making progress,
or has a suspected runtime cause.

For an unclassified Batch problem, inspect the exact job and use task events or
bounded logs as needed to test the hypotheses below.

## Hypotheses

| Hypothesis | Consider first when | Section |
|---|---|
| Out of memory | The job terminates unexpectedly, a task is killed, exit code 137 appears, or memory exhaustion is suspected | [Out of memory](#out-of-memory) |
| Java GC thrashing | Java remains active but makes little useful import progress | [Java GC thrashing](#java-gc-thrashing) |

## Out of memory

### Confirm or reject

Confirm only when task events or bounded logs explicitly report memory
exhaustion, such as `OutOfMemoryError`, `OOMKilled`, `oom-kill`,
`out of memory`, or a memory-limit failure. Inspect task events first, then use
bounded Batch logs when task evidence is insufficient.

Exit code 137, SIGKILL, high memory use, or abrupt termination alone does not
confirm OOM. Missing evidence means unknown, not refuted. Do not use monitoring
evidence until the skill has a supported monitoring operation.

### Mitigation when confirmed

When confirmed, recommend increasing `resource_limits.memory` for the affected
import specification. Preserve its existing CPU and disk settings, state the
current and proposed memory values in GiB, and recommend rerunning the import
after the manifest change.

## Java GC thrashing

### Confirm or reject

Confirm only when bounded runtime evidence shows repeated Java garbage
collection and bounded stage or status evidence shows little useful import
progress. Long runtime or high CPU alone is insufficient. Missing runtime
evidence means unknown, not refuted.

### Mitigation when confirmed

For the Data Commons import-tool path, Java heap sizing scales with the
container's available memory. Increasing `resource_limits.memory` therefore
increases the heap available to Java. When GC thrashing is confirmed, recommend
increasing `resource_limits.memory` for the affected import specification,
preserving its existing CPU and disk settings, and rerunning the import after
the manifest change.

## When no hypothesis matches

Report the Batch runtime problem as unclassified and return to the parent
troubleshooting fallback. Do not force a memory diagnosis.
