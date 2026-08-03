# Describe the ingestion helper

Recipe ID: `gcp.cloud-run.describe-ingestion-helper`

## Use when

Inspecting the configured ingestion-helper deployment when the user asks about
it or another live resource reports an infrastructure mismatch.

## Required inputs

Cloud Run project, region, and exact helper service name from the effective
environment.

## Clarify when

A required effective coordinate is missing or explicit prompt values conflict.

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
Do not use this recipe merely to discover GCS or Spanner coordinates; obtain
those from the effective environment. Do not retain the raw service response or
any other environment variable.

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

The runtime environment file and, when implementation details are requested,
an optional sibling ingestion-helper checkout.
