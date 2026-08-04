# Trace a Batch job to source-commit evidence

Recipe ID: `gcp.batch.trace-batch-job-source-commit`

## Use when

Trace one exact Batch job to runtime-image or source-commit evidence. Use the
recorded image reference first, then use a local time candidate as the default
fallback. Query Artifact Registry only when exact provenance is required or an
exact digest must be correlated with its attached tags.

## Required inputs

Exact Batch job resource, its recorded container `imageUri` and `createTime`,
the local `data` repository root, and a local Git reference (default `HEAD`) for
the time heuristic. Artifact Registry project, location, repository, image
name, and digest are required only for an exact-image lookup.

## Clarify when

The Batch job is not exact, the requested local Git ref is ambiguous, exact
provenance is required but immutable digest evidence is absent, or more than
one repository commit-shaped tag is attached to an exact image.

## Read-only operation

First follow [Describe Batch job](describe-job.md) for one exact job. Retain
only its `createTime` and requested container `imageUri`, then classify the
image reference.

### Commit tag already recorded

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

### Exact digest recorded or resolved

An image digest has the form `sha256:<64 lowercase hexadecimal characters>`.
Throughout this recipe, `<DIGEST>` means that complete value, including the
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

### Mutable or unusable image tag

For `stable`, `latest`, a missing image URI, or a tag that cannot be resolved,
report `runtime_source_commit: unknown`. When exact provenance is not required,
find the nearest commit on the selected local ref before the Batch job's
validated RFC3339 `createTime`:

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

## Preferred invocation

Use the smallest applicable branch:

```text
Batch image has commit tag -> local verification
Batch image has digest     -> one exact DockerImage read -> tags[] -> Git
Batch image has other tag  -> exact digest -> one exact DockerImage read
Batch image is mutable      -> exact commit unknown; default time candidate
```

Never query Cloud Build, search builds or images by time, add a Python helper,
fetch Git history, pull or run the image, or change the local checkout.

## Expected output

Batch job and `createTime`, requested image URI, immutable digest when known,
commit-shaped tags attached to that digest, locally verified Git commit, any
separate time candidate, `correlation_method`, `artifact_registry_lookups`, and
one confidence result:

- Exact digest identity: `exact`.
- Unique digest-attached Git tag or recorded commit tag: `strongly_correlated`.
- Nearest commit before Batch creation: `heuristic`.
- Mutable tag, no commit-shaped tag, or missing local commit: `unknown`.
- Multiple commit-shaped tags: `ambiguous`.

## Required bounds

Describe one exact Batch job. Use zero Artifact Registry requests for a
recorded commit tag, one exact `DockerImage` request for a known digest, or at
most two exact requests for another tag. Never list packages, versions, tags,
repositories, builds, or nearby images.

## Evidence to retain

Batch job resource and `createTime`, recorded image URI, digest and exact
`DockerImage` URI when used, returned `tags[]`, selected Git SHA, local Git ref
and verification, lookup count, correlation method, confidence, and unresolved
or ambiguous conditions.

## Common failures

Mutable `stable` or `latest`, missing or expired Batch job, invalid image URI or
digest, deleted image, permission denied (including CBA restrictions causing a
`401 Unauthorized` on `print-access-token`; fall back to Application Default
Credentials with `gcloud auth application-default print-access-token`),
returned digest mismatch, no or multiple commit-shaped tags, missing local
commit, or an unavailable local time candidate.

## Related repository sources

`import-automation/executor/cloudbuild.yaml` documents how the executor image
is tagged with Cloud Build's `COMMIT_SHA`, `latest`, and `stable`. Google Cloud
documents the Batch [`imageUri` and `createTime`](https://docs.cloud.google.com/batch/docs/reference/rest/v1/projects.locations.jobs),
Artifact Registry [`DockerImage.tags[]`](https://docs.cloud.google.com/artifact-registry/docs/reference/rest/v1/projects.locations.repositories.dockerImages),
and [Cloud Build substitutions](https://docs.cloud.google.com/build/docs/configuring-builds/substitute-variable-values).
