# Describe one Batch job

Recipe ID: `gcp.batch.describe-job`

## Use when

Job-level evidence is needed for an exact Batch job identified by current
`ImportStatus.JobId` or a validated GCS summary `job_id`.

## Required inputs

Exact Batch job ID, its evidence source, project, and location.

## Clarify when

The job ID was inferred from a name prefix instead of recorded evidence.

## Read-only operation

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

## Preferred invocation

Describe the exact job once. The projection extracts only the runnable import
identity and never prints complete commands, environments, secret references,
or task specifications.

## Expected output

Job resource/UID, import identity, allowlisted state events, timestamps, compute
resources, and container image URI.

## Required bounds

Describe one exact job. Do not list candidate jobs when no exact ID is known.

## Evidence to retain

Full job resource, UID, exact import match, state, timestamps, resources, image
URI, and the `ImportStatus` or summary job-ID correlation.

## Common failures

Expired job, permission denied, wrong project/location, or an attempt that
failed before an exact Batch job ID was recorded.

## Related repository sources

`import-automation/executor/app/executor/cloud_batch.py`.
