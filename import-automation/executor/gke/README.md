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

1. Set the PROJECT_ID, OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET environment variables in "gke/configure_gke.sh", e.g.
```
export PROJECT_ID=<GCP_PROJECT>
export OAUTH_CLIENT_ID=<OAUTH_CLIENT_ID>
export OAUTH_CLIENT_SECRET=<OAUTH_CLIENT_SECRET>
```

2. Run `./gke/configure_gke.sh`. The script will error out if the environment variables in (1) are not set.

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
