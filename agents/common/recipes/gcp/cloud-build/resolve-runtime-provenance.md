# Resolve runtime provenance

Recipe ID: `gcp.cloud-build.resolve-runtime-provenance`

## Use when

The user asks which Workflow revision, image, build, or source commit ran.

## Required inputs

Workflow execution/revision, Batch image URI, earliest task start time, image or
build project/region, result limit, and local repository commit.

## Clarify when

The image project/region cannot be parsed or multiple builds remain plausible.

## Read-only operation

```bash
gcloud builds list \
  --project=<PROJECT> \
  --region=<REGION> \
  --filter='status="SUCCESS" AND finishTime<"<TASK_START>"' \
  --sort-by='~finishTime' \
  --limit=<LIMIT> \
  --format='json(id,status,createTime,startTime,finishTime,images,
                 results.images.name,results.images.digest,
                 source.repoSource.commitSha,
                 sourceProvenance.resolvedRepoSource.commitSha,
                 substitutions.COMMIT_SHA)'
```

## Preferred invocation

Run only after Batch supplied the image URI and a runtime time bound. Compare
the small candidate set by image repository/tag/digest and return unknown when
more than one candidate remains.

## Expected output

Workflow revision, requested image, bounded build candidates, immutable digest
when available, source commit, local commit, and confidence.

## Required bounds

Use the task time and a small explicit result limit. Never list all builds,
print all substitutions, or pull and run the image.

## Evidence to retain

Immutable resource IDs, timestamps, image names/digests, commit fields, limit,
and the reason for the selected confidence.

## Common failures

Mutable `stable` tag, image/build project mismatch, expired history, separate
unpinned `/data` clone, or multiple same-time builds.

## Related repository sources

`import-automation/executor/cloudbuild.yaml`, executor image build definitions,
and the runtime-provenance reference.
