# Deploy Executor to GKE

Import-automation executor can also be deployed to Google Kubernetes Engine
(GKE). After committing new changes, please do the following to deploy.

1. Make sure the local repo is clean without pending changes.

1. From repo root, run: `cd import-automation/executor`.

1. build and push image: `./gke/push_image.sh`. This build a new docker image
   with tag `prod` and the current git commit hash.

1. Update GKE with the following command (replace GCP_PROJECT with actual
   project id):

```sh
export PROJECT_ID=<GCP_PROJECT>

gcloud container clusters get-credentials datacommons-us-central1 \
  --region us-central1 --project $PROJECT_ID

kubectl apply -f gke/deployment.yaml
```
