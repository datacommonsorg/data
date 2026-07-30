# Describe the ingestion helper

Recipe ID: `gcp.cloud-run.describe-ingestion-helper`

## Use when

Resolving the GCS and Spanner coordinates used by the deployed Workflow.

## Required inputs

Cloud Run project, region, and helper service name derived from the live
Workflow.

## Clarify when

The Workflow does not identify a unique helper or user/live scopes conflict.

## Read-only operation

```bash
gcloud run services describe <SERVICE> \
  --project=<PROJECT> --region=<REGION> --format=json
```

## Preferred invocation

Use the snapshot collector and retain only allowlisted non-secret environment
coordinates such as GCS bucket and Spanner project/instance/database.

## Expected output

Full service resource, URL, revision/service account, and allowlisted
infrastructure coordinates.

## Required bounds

Describe one exact service; do not list or print all service environments.

## Evidence to retain

Resource name, revision, observation time, and origin of each allowlisted
coordinate.

## Common failures

Service rename, missing permission, environment variable absent, or secrets
referenced indirectly.

## Related repository sources

The live Workflow source and a supplied sibling ingestion-helper deployment.
