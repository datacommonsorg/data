# Deploy Executor to GKE

Import-automation executor can be deployed to Google Kubernetes Engine
(GKE).

## (One Time) Setup IAP

Import Automation tool use [Identity-Aware Proxy
(IAP)](https://cloud.google.com/iap) to guard access. Non public instances are
guarded by IAP.

### Configure the OAuth consent screen

Follow
[documentation](https://cloud.google.com/iap/docs/enabling-kubernetes-howto#oauth-configure).

### Create OAuth credential

Follow
[documentation](https://cloud.google.com/iap/docs/enabling-kubernetes-howto#oauth-credentials).

### Setup IAP access

Follow
[documentation](https://cloud.google.com/iap/docs/enabling-kubernetes-howto#iap-access).

## (One Time) Setup GKE

1. Update the PROJECT_ID in "gke/configure_gke.sh", if needed.

2. Update OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET in "gke/configure_gke.sh".

3. Run `./gke/configure_gke.sh`.

## Deployment

After committing new changes, please do the following to deploy.

1. Make sure the local repo is clean without pending changes.

2. From repo root, run: `cd import-automation/executor`.

3. build and push image: `./gke/push_image.sh`. This build a new docker image
   with tag `prod` and the current git commit hash.

4. Update GKE with the following command (replace GCP_PROJECT with actual
   project id):

```sh
export PROJECT_ID=<GCP_PROJECT>

gcloud container clusters get-credentials datacommons-us-central1 \
  --region us-central1 --project $PROJECT_ID

kubectl apply -f gke/deployment.yaml
```
