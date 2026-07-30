# Resolve runtime provenance

Recipe ID: `gcp.cloud-build.resolve-runtime-provenance`

## Use when

Identifying the Workflow revision, image/build source, or data commit used by a
historical run.

## Required inputs

Workflow execution/revision, Batch image URI, task start time, image/build
project, and local repository commit.

## Clarify when

The image project/region cannot be parsed or multiple builds remain plausible.

## Read-only operation

```bash
gcloud builds list \
  --project=<PROJECT> --region=<REGION> \
  --filter='status="SUCCESS" AND finishTime<"<TASK_START>"' \
  --sort-by='~finishTime' --limit=<LIMIT> --format=json
```

## Preferred invocation

Use `collect_provenance.py`, which filters candidates by image/tag/digest and
retains only allowlisted source-provenance fields.

## Expected output

Workflow revision, requested image, digest/build candidates, Cloud Build
source commit, embedded data commit when recorded, local commit, confidence,
and evidence.

## Required bounds

Use the task time and a small build-result limit. Never list all builds or pull
and run the image.

## Evidence to retain

Immutable resource IDs, timestamps, image names/digests, commit fields, and the
reason for the selected confidence.

## Common failures

Mutable `stable` tag, image/build project mismatch, expired build history,
separate unpinned `/data` clone, or multiple same-time builds.

## Related repository sources

`import-automation/executor/cloudbuild.yaml` and the executor Dockerfile.
