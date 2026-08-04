# Resolve an exact runtime image to local Git evidence

Recipe ID: `gcp.artifact-registry.resolve-runtime-image`

## Use when

An ET debugging task starts from one exact Batch job and needs the strongest
available runtime-image and source-commit evidence. This is not a routine
`dc-import-info` operation.

## Required inputs

Exact Batch job resource, its recorded container `imageUri`, Artifact Registry
project/location/repository/package parsed from that URI, a tag-result limit,
and the local `data` repository root.

## Clarify when

The Batch job or image URI is not exact, the image is outside Artifact Registry,
or more than one full Git-SHA tag is attached to the resolved image version.

## Read-only operation

First describe the exact Batch job with the Batch recipe and retain its
requested container `imageUri`.

If the URI ends in `:stable` or `:latest`, report historical source provenance
as `unknown` and stop. Do not resolve the current value of either mutable tag.

For an immutable digest or any other exact tag, resolve only that identifier:

```bash
gcloud artifacts docker images describe '<IMAGE_URI>' \
  --project=<PROJECT> \
  --format='json(image_summary.digest,
                 image_summary.fully_qualified_digest)'
```

Retain the returned digest as `<DIGEST>`. Resolve its exact Artifact Registry
version resource without listing versions:

```bash
gcloud artifacts versions describe '<DIGEST>' \
  --package='<IMAGE_PACKAGE>' \
  --repository=<REPOSITORY> \
  --location=<LOCATION> \
  --project=<PROJECT> \
  --format='value(name)'
```

Treat that output as `<VERSION_RESOURCE>` and remove its final
`/versions/<DIGEST>` segment to obtain `<PACKAGE_RESOURCE>`. The installed
package-level `gcloud` tag-list command eagerly follows all pages before
applying its output limit, so use one authenticated REST page to enforce both
the exact server-side filter and the total bound. Feed the access token to
`curl` through standard input; never print or persist it:

```bash
gcloud auth print-access-token | \
  sed -e 's/^/header = "Authorization: Bearer /' -e 's/$/"/' | \
  curl --config - \
    --fail-with-body \
    --silent \
    --show-error \
    --get \
    --data-urlencode 'filter=version="<VERSION_RESOURCE>"' \
    --data-urlencode 'pageSize=<TAG_LIMIT_PLUS_ONE>' \
    --url 'https://artifactregistry.googleapis.com/v1/<PACKAGE_RESOURCE>/tags'
```

Require every returned `version` to equal `<VERSION_RESOURCE>`. If more than
`<TAG_LIMIT>` rows are returned or `nextPageToken` is non-empty, mark tag
evidence truncated and stop. From the remaining tag-name basenames, accept a
source tag only when exactly one matches:

```text
^[0-9a-f]{40}$
```

Verify that commit in the existing local checkout without changing it:

```bash
git -C <DATA_REPOSITORY_ROOT> cat-file -e '<GIT_SHA>^{commit}'
git -C <DATA_REPOSITORY_ROOT> show --no-patch --format=fuller <GIT_SHA>
```

## Preferred invocation

Use the exact evidence chain:

```text
Batch job -> recorded imageUri -> exact Artifact Registry digest/version
          -> exact-version bounded tag result -> unique full Git SHA
          -> existing local commit
```

Never query Cloud Build, search builds or images by time, add a Python helper,
fetch Git history, pull or run the image, or change the local checkout.

## Expected output

Exact Batch image URI, resolved immutable digest and version resource, bounded
exact-version tag evidence, unique full Git SHA when present, local commit
metadata when available, and one result:

- Image digest identity: `exact`.
- Git commit: `strongly_correlated` unless immutable provenance explicitly
  records the commit.
- Mutable tag, no full-SHA tag, multiple plausible SHA tags, truncated tags, or
  missing local commit: `unknown` or `ambiguous` with the reason.

## Required bounds

Describe one exact Batch job, one exact Docker tag/digest, and the one resolved
version. Request one tag page for only that exact version with
`pageSize=<TAG_LIMIT_PLUS_ONE>`. Do not follow a page token or list packages,
versions, repositories, builds, or nearby images.

## Evidence to retain

Batch job resource, recorded image URI, Artifact Registry digest and version
resource, exact tag filter and limits, selected full-SHA tag, local Git
verification, confidence, and unresolved or ambiguous conditions.

## Common failures

Mutable `stable` or `latest`, missing/expired Batch job, deleted image version,
permission denied, tag-result truncation, no full-SHA tag, multiple full-SHA
tags, or the commit being absent from the local checkout.

## Related repository sources

`import-automation/executor/cloudbuild.yaml` documents the image tags attached
during the build. The exact Batch record and Artifact Registry metadata remain
runtime truth.
