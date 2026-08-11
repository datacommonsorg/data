# Cloud Batch runtime issues

Use this guide when a selected Cloud Batch job failed or stopped making
progress.

## Select the issue

| Observed behavior | Section |
|---|---|
| The task terminates with explicit out-of-memory or memory-limit evidence | [Out of memory](#out-of-memory) |
| The Java process remains active but repeatedly performs garbage collection with little import progress | [Java GC thrashing](#java-gc-thrashing) |

If neither pattern matches, report the Batch runtime issue as unclassified and
return to the parent troubleshooting fallback. Do not force a memory diagnosis.

## Out of memory

Confirm out of memory only when task events or logs explicitly identify an
out-of-memory or memory-limit failure. A nonzero exit code without supporting
memory evidence is not sufficient.

When confirmed, recommend increasing `resource_limits.memory` for the affected
import specification. Preserve its existing CPU and disk settings, state the
current and proposed memory values in GiB, and recommend rerunning the import
after the manifest change.

## Java GC thrashing

Confirm Java garbage-collection thrashing only when Java runtime evidence shows
repeated garbage collection with little useful import progress. A long-running
job or high CPU usage without GC evidence is not sufficient.

Increasing the Cloud Batch memory limit gives processes in the container,
including Java processes, a larger available memory budget. When GC thrashing
is confirmed, recommend increasing `resource_limits.memory` for the affected
import specification, preserving its existing CPU and disk settings, and
rerunning the import after the manifest change.

## Report the diagnosis

Report the issue classification, supporting Batch and runtime evidence, current
and proposed memory values, remaining unknowns, and the recommended rerun. If
the evidence is inconclusive, label memory pressure as suspected and do not
present the memory increase as a confirmed fix.
