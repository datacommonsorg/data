# Describe the ingestion helper

Recipe ID: `gcp.cloud-run.describe-ingestion-helper`

## Use when

Resolving GCS or Spanner coordinates required by a selected recipe.

## Required inputs

Cloud Run project, region, and exact helper service name derived from the live
Workflow.

## Clarify when

The Workflow does not identify a unique helper or user/live scopes conflict.

## Read-only operation

```bash
gcloud run services describe <SERVICE> \
  --project=<PROJECT> \
  --region=<REGION> \
  --format=json | \
jq '{name: .metadata.name,
     url: .status.url,
     latest_ready_revision: .status.latestReadyRevisionName,
     service_account: .spec.template.spec.serviceAccountName,
     coordinates:
       ([.spec.template.spec.containers[].env[]?
         | select(.name == "GCS_BUCKET_ID"
                  or .name == "SPANNER_PROJECT_ID"
                  or .name == "SPANNER_INSTANCE_ID"
                  or .name == "SPANNER_DATABASE_ID")
         | {key: .name, value: .value}] | from_entries)}'
```

## Preferred invocation

Describe one exact service and immediately project only allowlisted coordinates.
Do not retain the raw service response or any other environment variable.

## Expected output

Service resource, URL, revision/service account, and allowlisted GCS or Spanner
coordinates.

## Required bounds

Describe one exact service. Do not list services or print complete environments.

## Evidence to retain

Resource name, revision, observation time, and origin of each allowlisted
coordinate.

## Common failures

Service rename, wrong API generation, missing permission, allowed variable
absent, or a coordinate provided indirectly through a secret reference.

## Related repository sources

The live Workflow source and a supplied sibling ingestion-helper deployment.
