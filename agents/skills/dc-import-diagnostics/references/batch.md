# Cloud Batch operations

- [Describe one Batch job](#describe-one-batch-job)
- [List tasks for one Batch job](#list-tasks-for-one-batch-job)
- [Fetch bounded Batch logs](#fetch-bounded-batch-logs)
- [Trace a Batch job to source-commit evidence](#trace-a-batch-job-to-source-commit-evidence)

## Describe one Batch job

### Use when

Job-level evidence is needed for an exact Batch job identified by current
`ImportStatus.JobId` or a validated GCS summary `job_id`.

### Required inputs

Exact Batch job ID, its evidence source, project, and location.

### Clarify when

The job ID was inferred from a name prefix instead of recorded evidence.

### Read-only operation

```bash
gcloud batch jobs describe <JOB_ID> \
  --project=<PROJECT> \
  --location=<LOCATION> \
  --format=json | \
jq '{name, uid, createTime, updateTime,
     status:
       {state: .status.state,
        events: [.status.statusEvents[]?
                 | {type, eventTime, taskState}]},
     import_identity:
       (([.taskGroups[]?.taskSpec.runnables[]?.environment.variables.IMPORT_NAME
          | select(. != null)]
         + [.taskGroups[]?.taskSpec.runnables[]?.container.commands[]?
            | select(startswith("--import_name="))
            | sub("^--import_name="; "")]) | first),
     compute_resources:
       [.taskGroups[]?.taskSpec.computeResource],
     image_uris:
       [.taskGroups[]?.taskSpec.runnables[]?.container.imageUri
        | select(. != null)]}'
```

### Preferred invocation

Describe the exact job once. The projection extracts only the runnable import
identity and never prints complete commands, environments, secret references,
or task specifications.

### Expected output

Job resource/UID, import identity, allowlisted state events, timestamps, compute
resources, and container image URI.

### Required bounds

Describe one exact job. Do not list candidate jobs when no exact ID is known.

### Evidence to retain

Full job resource, UID, exact import match, state, timestamps, resources, image
URI, and the `ImportStatus` or summary job-ID correlation.

### Common failures

Permission denied or an attempt that failed before an exact Batch job ID was
recorded.

Batch automatically deletes completed jobs after 60 days and may delete them
earlier on request. If the exact job is not found, verify its project, location,
and ID once; do not search for or guess another job. Use the
[bounded Batch logs operation](#fetch-bounded-batch-logs) only when a verified
job UID and time range are available. Otherwise report the Batch evidence as
unavailable.

### Related repository sources

`import-automation/executor/app/executor/cloud_batch.py`.

## List tasks for one Batch job

### Use when

Task-level state, exit status, or runtime start time is required for a selected
Batch job.

### Required inputs

Exact Batch job ID, project, location, and task limit.

### Clarify when

The job ID or required result limit is missing.

### Read-only operation

```bash
gcloud batch tasks list \
  --job=<JOB_ID> \
  --project=<PROJECT> \
  --location=<LOCATION> \
  --limit=<LIMIT_PLUS_ONE> \
  --format=json | \
jq --argjson limit '<LIMIT>' '
  {truncated: (length > $limit),
   tasks:
     [.[0:$limit][] |
      {name,
       status:
         {state: .status.state,
          events: [.status.statusEvents[]?
                   | {type, eventTime, taskState,
                      exitCode: .taskExecution.exitCode}]}}]}'
```

### Preferred invocation

Run only when job-level evidence does not answer the task-level state or
runtime-start question.

### Expected output

Bounded task resources, states, status events, task-execution exit codes when
present, and explicit truncation.

### Required bounds

Use one exact job and an explicit limit. Request `LIMIT_PLUS_ONE`, return at
most `LIMIT` tasks, and report whether the extra task exists.

### Evidence to retain

Task resource, state, status events used, task-execution exit code when present,
result limit, and truncation.

### Common failures

Expired tasks, permission denied, wrong location, or more tasks than the
selected limit.

### Related repository sources

`import-automation/executor/app/executor/cloud_batch.py`.

## Fetch bounded Batch logs

### Use when

Structured pipeline stage/status evidence is required for a known Batch job.

### Required inputs

Logging project, verified Batch job UID (`<JOB_UID>`), inclusive UTC start
timestamp (`<START>`), exclusive UTC end timestamp (`<END>`), and row limit. A
text/payload search term (`<QUERY_TERM>`) is optional.

### Clarify when

The job UID is unverified, either timestamp is unavailable, the start is not
before the end, or the bounded query returns too many results.

### Read-only operation

Follow the [shared Cloud Logging parameters](../../../common/references/gcp/logging.md)
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

### Preferred invocation

Run only for a selected job when structured pipeline stage or status events
are required beyond job-level state and summary evidence. Request one more row
than the display limit to detect truncation, then return at most the requested
limit in chronological order.

If zero matching logs are returned, verify or widen the timestamp window
(`<START>`/`<END>`) or remove optional query terms (`<QUERY_TERM>`).

### Expected output

Allowlisted structured stage/status fields (or matching JSON/text payload when
using `<QUERY_TERM>`) and explicit truncation.

### Required bounds

Filter by exact log name and verified job UID, plus structured log types or a
query term. Always use the inclusive UTC start and exclusive UTC end. Request
one extra record for truncation detection and return at most 500 records.

### Evidence to retain

Log name, timestamp, severity, job UID, structured fields used, and truncation.
Never retain `message`, `textPayload`, or unrecognized payload fields unless
explicitly matching `<QUERY_TERM>`.

### Common failures

Expired logs, private-log permission, wrong UID, no structured events, no
matching logs (relax timestamp window or query terms if zero results are
returned), or truncation.

### Related repository sources

`import-automation/executor/app/executor/import_executor.py` constants
`AUTO_IMPORT_JOB_STAGE`, `AUTO_IMPORT_JOB_STATUS`, and `log_import_status()`.

## Trace a Batch job to source-commit evidence

### Use when

Trace one exact Batch job to runtime-image or source-commit evidence. Use the
recorded image reference first, then use a local time candidate as the default
fallback. Query Artifact Registry only when exact provenance is required or an
exact digest must be correlated with its attached tags.

### Required inputs

Exact Batch job resource, its recorded container `imageUri` and `createTime`,
the local `data` repository root, and a local Git reference (default `HEAD`) for
the time heuristic. Artifact Registry project, location, repository, image
name, and digest are required only for an exact-image lookup.

### Clarify when

The Batch job is not exact, the requested local Git ref is ambiguous, exact
provenance is required but immutable digest evidence is absent, or more than
one repository commit-shaped tag is attached to an exact image.

### Read-only operation

First follow [Describe Batch job](#describe-one-batch-job) for one exact job.
Retain only its `createTime` and requested container `imageUri`, then classify
the image reference.

#### Commit tag already recorded

When the image tag matches the repository's current commit-tag convention,
verify it locally without an Artifact Registry request:

```text
^[0-9a-f]{40}$
```

```bash
git -C <DATA_REPOSITORY_ROOT> cat-file -e '<GIT_SHA>^{commit}'
git -C <DATA_REPOSITORY_ROOT> show --no-patch --format=fuller '<GIT_SHA>'
```

Report `correlation_method: image_sha_tag` and
`artifact_registry_lookups: 0`. This establishes the requested commit tag. A
tag is not immutable image identity unless the repository's immutable-tag
setting or other immutable provenance proves that property.

#### Exact digest recorded or resolved

An image digest has the form `sha256:<64 lowercase hexadecimal characters>`.
Throughout this operation, `<DIGEST>` means that complete value, including the
`sha256:` prefix. If the Batch image URI already contains the digest, do not
describe it again. If the URI contains another exact tag, resolve only that tag
to its digest:

```bash
gcloud artifacts docker images describe '<IMAGE_URI>' \
  --project=<PROJECT> \
  --format='value(image_summary.fully_qualified_digest)'
```

Treat the command result as `<RESOLVED_IMAGE_AT_DIGEST>` in the exact form
`<IMAGE>@<DIGEST>`. Require `<IMAGE>` to equal the requested image name, then
retain the suffix after `@` as `<DIGEST>`.

Do not resolve `stable` or `latest` with this command. Their current values do
not establish which image an older Batch job pulled.

For the known digest, read the exact Artifact Registry `DockerImage` resource.
Percent-encode `<IMAGE>@<DIGEST>` as one path component to obtain
`<URL_ENCODED_IMAGE_AT_DIGEST>`. Feed the access token to `curl` through
standard input; never print or persist it:

```bash
(gcloud auth application-default print-access-token 2>/dev/null || gcloud auth print-access-token) | \
  sed -e 's/^/header = "Authorization: Bearer /' -e 's/$/"/' | \
  curl --config - \
    --fail-with-body \
    --silent \
    --show-error \
    --url \
    'https://artifactregistry.googleapis.com/v1/projects/<PROJECT>/locations/<LOCATION>/repositories/<REPOSITORY>/dockerImages/<URL_ENCODED_IMAGE_AT_DIGEST>' | \
  jq '{uri, tags, uploadTime, buildTime}'
```

Require the returned `uri` to contain the requested digest. Inspect only that
resource's `tags[]`; never list repository, package, version, or tag resources.
Accept a source tag only when exactly one tag basename matches
`^[0-9a-f]{40}$`, then verify that commit locally with the commands above.

An already-known digest requires one Artifact Registry request. Another exact
tag requires at most two: resolve the tag, then read the exact digest resource.

#### Mutable tag with log-resolved digest

When the Batch image URI uses `stable` or `latest`, do not immediately report
`unknown`. First inspect the job's startup logs using
[Fetch bounded Batch logs](#fetch-bounded-batch-logs):

- Set `<JOB_UID>` to the exact Batch job UID.
- Set `<START>` to `<BATCH_CREATE_TIME>` and `<END>` to 5 minutes after launch.
- Set `<QUERY_TERM>` to `"sha256"` and use `--format=json`.

If a container pull event containing `sha256:<64 lowercase hexadecimal characters>`
is returned in `textPayload`, use that digest in the Artifact Registry
`DockerImage` read operation above to identify the attached `^[0-9a-f]{40}$` Git
tag. Report `correlation_method: log_resolved_digest_tag` and
`confidence: strongly_correlated`.

#### Unresolvable tag or missing log digest (heuristic fallback)

For a missing image URI, a tag that cannot be resolved, or when mutable-tag log
evidence is absent or expired, report `runtime_source_commit: unknown`. When
exact provenance is not required, find the nearest commit on the selected
local ref before the Batch job's validated RFC3339 `createTime`:

```bash
git -C <DATA_REPOSITORY_ROOT> log \
  -1 \
  --before='<BATCH_CREATE_TIME>' \
  --format=fuller \
  '<LOCAL_REF>'
```

Report that result separately as `nearest_local_commit_before_launch`, with
`correlation_method: heuristic_by_time`. Never call it the commit that ran.
The image may have been built earlier, from another ref, or from Git history
that is absent or stale locally. When exact provenance is required, do not
substitute this time candidate for missing digest evidence.

### Preferred invocation

Use the smallest applicable branch:

```text
Batch image has commit tag -> local verification
Batch image has digest     -> one exact DockerImage read -> tags[] -> Git
Batch image has other tag  -> exact digest -> one exact DockerImage read
Batch image is mutable      -> check Batch logs for pulled digest -> one exact DockerImage read
Log digest unavailable     -> exact commit unknown; default time candidate
```

Never query Cloud Build, search builds or images by time, add a Python helper,
fetch Git history, pull or run the image, or change the local checkout.

### Expected output

Batch job and `createTime`, requested image URI, immutable digest when known,
commit-shaped tags attached to that digest, locally verified Git commit, any
separate time candidate, `correlation_method`, `artifact_registry_lookups`, and
one confidence result:

- Exact digest identity: `exact`.
- Unique digest-attached Git tag, recorded commit tag, or log-resolved digest tag: `strongly_correlated`.
- Nearest commit before Batch creation: `heuristic`.
- Mutable tag without log digest, no commit-shaped tag, or missing local commit: `unknown`.
- Multiple commit-shaped tags: `ambiguous`.

### Required bounds

Describe one exact Batch job. Use zero Artifact Registry requests for a
recorded commit tag, one exact `DockerImage` request for a known digest or a
log-resolved digest, or at most two exact requests for another tag. Never list
packages, versions, tags, repositories, builds, or nearby images.

### Evidence to retain

Batch job resource and `createTime`, recorded image URI, digest and exact
`DockerImage` URI when used, returned `tags[]`, selected Git SHA, local Git ref
and verification, lookup count, correlation method (`image_digest_tag`,
`log_resolved_digest_tag`, or `heuristic_by_time`), confidence, and unresolved
or ambiguous conditions.

### Common failures

Mutable `stable` or `latest` with expired/missing logs, missing or expired Batch
job, invalid image URI or digest, deleted image, permission denied (including
CBA restrictions causing a `401 Unauthorized` on `print-access-token`; fall
back to Application Default Credentials with
`gcloud auth application-default print-access-token`), returned digest
mismatch, no or multiple commit-shaped tags, missing local commit, or an
unavailable local time candidate.

### Related repository sources

`import-automation/executor/cloudbuild.yaml` documents how the executor image
is tagged with Cloud Build's `COMMIT_SHA`, `latest`, and `stable`. Google Cloud
documents the Batch [`imageUri` and `createTime`](https://docs.cloud.google.com/batch/docs/reference/rest/v1/projects.locations.jobs),
Artifact Registry [`DockerImage.tags[]`](https://docs.cloud.google.com/artifact-registry/docs/reference/rest/v1/projects.locations.repositories.dockerImages),
and [Cloud Build substitutions](https://docs.cloud.google.com/build/docs/configuring-builds/substitute-variable-values).
